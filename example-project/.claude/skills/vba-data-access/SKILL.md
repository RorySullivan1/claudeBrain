---
name: vba-data-access
description: >
  Expert on getting data into and out of external stores from VBA — SQL Server, Access/
  ACE, ODBC sources, and other workbooks — via ADO and DAO. Use this skill whenever the
  task involves a connection string, a `Recordset`, a `Command`, running SQL from a macro,
  **parameterised queries**, writing query results onto a sheet with `CopyFromRecordset`,
  bulk-inserting sheet data into a table, transactions, connection lifetime/pooling, or
  reading another workbook as a data source without opening it. Trigger on "query the
  database from Excel", "connect to SQL Server in VBA", "ADO recordset", "DAO", "run this
  SQL from a macro", "connection string", "Provider=", "Microsoft.ACE.OLEDB", "insert
  these rows into the database", "why is my query returning nulls", "escape the
  apostrophe in this query", "parameterise this SQL", "ODBC call failed",
  "CopyFromRecordset". Boundaries: reading and writing the *worksheet* — tables, pivots,
  charts, ranges, formulas — is vba-excel-object-model; general VBA mechanics (error
  handling, binding, the performance wrapper) are vba-development; HTTP/REST/JSON
  integration stays in vba-development; reviewing existing code is vba-review; packaging
  and driver deployment onto user machines is vba-distribution. This skill owns
  *the connection, the query, and the round trip*.
---

# VBA Data Access — ADO, DAO, and SQL from a macro

You move data between VBA and an external store. Three things decide whether the result is
production code or a liability: **the query is parameterised**, **the connection is
closed**, and **the round trip is bulk, not per-row**. Everything below serves those.

`vba-development`'s rules are assumed in force — `Option Explicit`, the structured error
handler, explicit types. Sheet-side reading and writing belongs to
`vba-excel-object-model`; this skill hands data to it and takes data from it.

---

## Rule zero — never build SQL by concatenating values

This is the defect that matters most in VBA data code, and it is nearly universal in the
wild. Concatenated SQL is broken in three ways at once, and only one of them is security:

```vba
' WRONG — three separate failure modes in one line
sql = "SELECT * FROM Orders WHERE Customer = '" & txt & "' AND Due < #" & dt & "#"
```

1. **Correctness.** A customer named `O'Brien` produces a syntax error. Doubling the
   apostrophe patches that one case and nothing else.
2. **Locale.** `dt` is stringified by VBA using the *machine's* regional settings; the
   same macro sends `03/04/2026` from one desk and means a different day on another.
   Numbers hit the same problem via the decimal separator.
3. **Injection.** Anything typed into that cell reaches the server as SQL. In an Excel
   front end the "attacker" is usually just a colleague pasting an odd value into a filter
   box — the damage is accidental and the mechanism is identical.

Parameters fix all three, because the value never becomes text: types are transmitted as
types.

### The parameterised form

A parameterised query needs a `Command` object. `Connection.Execute` and `Recordset.Open`
take a string only — they cannot carry parameters:

```vba
Dim cn As Object, cmd As Object, rs As Object
Set cn = CreateObject("ADODB.Connection")
cn.Open connString

Set cmd = CreateObject("ADODB.Command")
Set cmd.ActiveConnection = cn
cmd.CommandType = adCmdText                      ' declare it; ADO won't have to guess
cmd.CommandText = "SELECT OrderID, Amount FROM Orders " & _
                  "WHERE Customer = ? AND Due < ?"

cmd.Parameters.Append cmd.CreateParameter("@cust", adVarWChar, adParamInput, 100, txt)
cmd.Parameters.Append cmd.CreateParameter("@due", adDBTimeStamp, adParamInput, , dt)

Set rs = cmd.Execute
```

Four documented constraints on `CreateParameter(Name, Type, Direction, Size, Value)`:

- **It does not append.** It returns a detached `Parameter`; you must `Append` it. That
  two-step exists so you can set extra properties before ADO validates on append.
- **A variable-length type requires `Size`.** `adVarChar`, `adVarWChar`, `adVarBinary` and
  friends error on append without a `Size` greater than zero. Fixed-width types don't need
  it — that's why the timestamp above passes an empty `Size`.
- **`adNumeric` / `adDecimal` additionally require `Precision` and `NumericScale`.** Set
  them on the `Parameter` object before appending.
- **Order matters with `?` placeholders.** OLE DB positional markers bind by append order,
  not by the name you gave them — the names are for your benefit. Appending out of order
  silently swaps the values.

Declaring the parameters yourself, rather than touching `cmd.Parameters` and letting ADO
call `Refresh` implicitly, saves a round trip to the provider for metadata — and some
providers don't support `Refresh` at all and will error.

**Late binding vs. early.** The example uses `CreateObject`, which means the `ad*` constants
are not defined. Either add a reference to *Microsoft ActiveX Data Objects* and declare the
objects as `ADODB.Connection` etc., or declare the handful of constants you use yourself
(`Const adVarWChar As Long = 202`). Do not silently rely on undeclared constants: without
`Option Explicit` they evaluate to `Empty` (0) and the parameter takes the wrong type.
`vba-development`'s binding guidance applies — early binding while developing, late binding
for distribution across mixed Office versions.

---

## Connections

### Shape of a connection string

```vba
' SQL Server, Windows auth — the default for a corporate fleet
"Provider=MSOLEDBSQL19;Data Source=SQLPROD01;Initial Catalog=Sales;" & _
"Integrated Security=SSPI;DataTypeCompatibility=80;"

' Access / ACE
"Provider=Microsoft.ACE.OLEDB.12.0;Data Source=C:\data\Sales.accdb;" & _
"Persist Security Info=False;"

' Another Excel workbook, read as a database — no need to open it
"Provider=Microsoft.ACE.OLEDB.12.0;Data Source=C:\data\Book.xlsx;" & _
"Extended Properties=""Excel 12.0 Xml;HDR=YES"";"
```

Points that cause real support calls:

- **ADO against the modern SQL Server driver needs `DataTypeCompatibility=80`.** Microsoft
  states both `Provider=MSOLEDBSQL19` (or `MSOLEDBSQL`) *and* `DataTypeCompatibility=80` are
  required for an ADO application to use the OLE DB Driver for SQL Server. Omitting it is
  the classic "works in the UDL tester, fails in VBA".
- **Encryption defaults to `Mandatory` on the v19 driver.** `Use Encryption for Data` is
  `Mandatory` by default, so a server without a certificate the client trusts refuses the
  connection. Fix the certificate; only reach for `Use Encryption for Data=Optional` when
  someone with authority over that server has decided so.
- **Integrated security beats a stored password.** A password in a connection string in a
  `.bas` file is in source control, in the `.xlsm` any user can open, and in every backup.
  If the store can't do Windows auth, keep the credential outside the workbook and say so
  explicitly to the user — don't quietly hardcode it.
- **The provider must be installed and must match Office's bitness.** A 64-bit Excel cannot
  load a 32-bit ACE provider and vice versa. This is a *deployment* fact, not a code fact —
  route it to `vba-distribution`, but flag it, because it is the usual reason a macro works
  on the developer's machine and nowhere else.
- **`Extended Properties` needs escaped inner quotes** (doubled in VBA, as above) and is not
  optional for the Excel provider.

### Reading a workbook or CSV through ACE — the type-guessing trap

The Excel provider **infers each column's type from the first 8 rows** (the `TypeGuessRows`
registry value). A column whose first 8 rows are numeric and whose 9th is text imports that
text as `NULL` — silently. This is the single most common "why is my query returning
nulls" cause.

Mitigations, best first:

1. Don't route Excel-to-Excel data through a SQL provider at all — read the range directly
   (`vba-excel-object-model`). This is usually the right answer.
2. Add `IMEX=1` to `Extended Properties`, which tells the driver to read intermixed columns
   as text: `Extended Properties="Excel 12.0 Xml;HDR=YES;IMEX=1";`. Microsoft notes this may
   also require a registry change to be fully reliable — so it is a mitigation, not a fix.
3. Format the source column as Text before it is read.

`HDR=YES` means the first row is column names, not data. Sheet names in the SQL are
`[Sheet1$]`; a named range is `[MyRange]`.

### Lifetime

Open late, close early, and close in the error path too:

```vba
Public Function FetchOrders(ByVal cutoff As Date) As Variant
    Dim cn As Object, cmd As Object, rs As Object
    On Error GoTo Fail

    Set cn = CreateObject("ADODB.Connection")
    cn.ConnectionTimeout = 15
    cn.Open ConnString()
    ' … build cmd, execute …

Done:
    On Error Resume Next
    If Not rs Is Nothing Then If rs.State <> 0 Then rs.Close
    If Not cn Is Nothing Then If cn.State <> 0 Then cn.Close
    Set rs = Nothing: Set cmd = Nothing: Set cn = Nothing
    Exit Function
Fail:
    ' report per vba-development's handler, then fall through
    Resume Done
End Function
```

Test `.State <> 0` (`adStateClosed` is 0) rather than assuming — closing an already-closed
connection raises. A connection left open holds a server-side session and, for ACE, a lock
file next to the database that blocks other users.

**Reuse one `Connection` for multiple recordsets.** ADO will create a *new* connection per
`Recordset` if you pass a connection string instead of the object variable — even when the
string is identical. Open one `Connection`, pass the object.

---

## Recordsets

### Getting rows onto a sheet

`CopyFromRecordset` is the bulk path and it is the right default:

```vba
Dim target As Range
Set target = ws.Range("A2")                  ' hold it in a variable — see below
target.CopyFromRecordset rs
```

Four documented behaviours:

- **It fails outright if any field holds an OLE object.** Project those columns out of the
  `SELECT` rather than discovering it at run time.
- **It copies from the recordset's *current row*.** If you already looped to inspect the
  first record, you will silently copy everything after it. `rs.MoveFirst` first, or don't
  peek.
- **After it returns, `rs.EOF` is `True`.** The recordset is spent; re-`Open` to reuse.
- **Microsoft recommends assigning the destination to an object variable** rather than
  calling it on an inline expression — doing otherwise "may cause generic automation
  errors depending on the recordset and the range."

It does **not** write headers. Emit them yourself from `rs.Fields(i).Name` before the copy.

`GetRows` is the alternative when you want the data in VBA rather than on a sheet — it
returns a **transposed** 2D array (field, record), the opposite orientation from
`Range.Value2`. Know which one you have before you index it.

### Cursors and locks — pick, don't default

`rs.Open Source, Connection, CursorType, LockType`:

- **`adOpenForwardOnly` + `adLockReadOnly`** — the default and the fastest. One pass, no
  `RecordCount`. Use it for everything you're just reading.
- **`adOpenStatic` + client-side cursor** (`cn.CursorLocation = adUseClient`) — gives a real
  `RecordCount` and lets you disconnect the recordset from the connection. Note that with
  `adUseClient` the `UnderlyingValue` property on `Field` objects is unavailable.
- **`adOpenKeyset` / `adOpenDynamic` with `adLockOptimistic`** — only when you genuinely
  intend to update through the recordset.

`RecordCount` returns `-1` on a forward-only cursor — the actual count only for static or
keyset, and either for dynamic depending on the data source. Code that branches on
`rs.RecordCount > 0` is a bug waiting for the cursor type to change; test
`rs.EOF And rs.BOF` for emptiness instead — both are `True` when there are no records, and
both are `False` immediately after a successful open.

(Microsoft's own pages disagree on one corner: the `RecordCount` reference says `-1` for
forward-only unconditionally, while "Limits of a Recordset" says an *empty* recordset
reports `0` for every cursor except dynamic. Don't resolve it — the `BOF And EOF` test is
correct under either reading, which is the reason to use it.)

The `Parameters` collection of a `Recordset` goes out of scope when the recordset closes —
read anything you need out of it first.

---

## Writing back

### Bulk insert, not a row-at-a-time loop

Each `Execute` is a network round trip. A 5,000-row loop of single `INSERT`s is minutes;
the same rows sent in batches are seconds. In rough order of preference:

1. **A stored procedure** taking a table-valued parameter or a delimited payload — the
   store owns the validation.
2. **One `Command`, parameters re-bound per row inside a transaction.** The parse plan is
   reused; the parameters keep it safe:

```vba
cn.BeginTrans
On Error GoTo Rollback
For r = 1 To UBound(data, 1)
    cmd.Parameters("@id").Value = data(r, 1)
    cmd.Parameters("@amt").Value = data(r, 2)
    cmd.Execute , , adExecuteNoRecords       ' 128 — don't build a Recordset we won't read
Next r
cn.CommitTrans
Exit Sub
Rollback:
    cn.RollbackTrans
    ' re-raise per vba-development's handler
```

3. **Multi-row `INSERT … VALUES (?,?),(?,?),…`** built with a *parameter per value* — the
   statement text is generated, the data never is.

`adExecuteNoRecords` on any statement that returns no rows is free performance; leaving it
off makes ADO construct and discard a `Recordset` every iteration.

Wrap multi-statement writes in `BeginTrans`/`CommitTrans`/`RollbackTrans` so a failure
halfway does not leave the store half-updated. An uncommitted transaction on a connection
you then close is rolled back — but be explicit rather than relying on it.

---

## DAO — when it's the right tool

DAO (`Microsoft DAO 3.6` / `Microsoft Office x.x Access Database Engine Object Library`) is
not legacy-by-default: against a local Access/ACE database it is faster than ADO and
exposes engine features ADO doesn't. Use it when the store *is* Access and the code lives
next to it. Use ADO for SQL Server, ODBC, and anything cross-provider.

The parameter discipline is the same, with different spelling:

```vba
Dim db As DAO.Database, qd As DAO.QueryDef, rs As DAO.Recordset
Set db = DBEngine.OpenDatabase("C:\data\Sales.accdb")
Set qd = db.CreateQueryDef("", "PARAMETERS pCust Text(100); " & _
                               "SELECT * FROM Orders WHERE Customer = pCust")
qd.Parameters("pCust").Value = txt
Set rs = qd.OpenRecordset(dbOpenSnapshot)
```

A zero-length name in `CreateQueryDef` makes a **temporary** querydef — anything else makes
a permanent one that is automatically appended to `QueryDefs` and saved to disk, and reusing
an existing name raises. Temporary querydefs are the documented way to run dynamic SQL
repeatedly without leaving objects behind. `dbOpenSnapshot` is the read-only, fastest option
— the DAO analogue of forward-only/read-only. A `QueryDef` is also Microsoft's stated
preferred vehicle for SQL pass-through against ODBC sources.

One structural difference from ADO: **DAO's `Parameters` collection cannot be appended to.**
It reports the parameters the SQL statement already declared (via the `PARAMETERS` clause),
so you *set* `qd.Parameters("pCust").Value` — you never create the parameter object.

**Don't mix the two libraries carelessly.** With both referenced, a bare
`Dim rs As Recordset` resolves by reference priority, not by intent. Always disambiguate:
`DAO.Recordset` / `ADODB.Recordset`.

---

## Watch Out

- **Concatenated SQL is the defect to look for first** — in new code and in anything you're
  asked to review or extend. Every value goes through a parameter, without exception. If a
  value genuinely cannot be parameterised (an *identifier* — a table or column name), it
  must be validated against an allow-list, never escaped.
- **`CreateParameter` doesn't append**, variable-length types need `Size`, decimals need
  `Precision`/`NumericScale`, and `?` parameters bind by append order.
- **`Connection.Execute` and `Recordset.Open` can't take parameters.** Reaching for them is
  what pushes people back to concatenation — use a `Command`.
- **`RecordCount` is `-1` on a forward-only cursor.** Test `rs.EOF And rs.BOF`.
- **`CopyFromRecordset` starts at the current row, ends at EOF, writes no headers, and
  fails on OLE-object fields.** Assign the destination range to a variable first.
- **`GetRows` is transposed** relative to `Range.Value2`.
- **The ACE Excel provider type-guesses from 8 rows** and turns the minority type into
  `NULL`. Prefer reading the range directly over querying a workbook.
- **The provider must match Office bitness and be installed on the user's machine** — the
  classic works-here-only failure. Deployment is `vba-distribution`'s.
- **Close in the error path, test `.State` before closing, reuse one `Connection`.**
- **Never hardcode a password.** Say so out loud when the design seems to want one.
- **Undeclared `ad*` constants evaluate to 0** under late binding — declare them or add the
  reference.
