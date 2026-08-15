---
name: vba-excel-object-model
description: >
  Expert on driving Excel's object model from VBA — the worksheet-shaped surface that
  general VBA guidance doesn't cover. Use this skill whenever the task touches Excel
  Tables/`ListObject`s (create, read, append rows, address a column by name, structured
  references), PivotTables (`PivotCaches.Create` → `CreatePivotTable`, fields, refresh),
  charts (`ChartObjects.Add`, `SetSourceData`, series), writing formulas from code
  (`.Formula` vs `.Formula2` vs `.FormulaR1C1`, the implicit-intersection `@`), reading
  cell values correctly (`.Value2` vs `.Value` vs `.Text`), or locating data on a sheet
  (`UsedRange`, `End(xlUp)`, `SpecialCells`, `AutoFilter` + visible cells). Trigger on
  "add a row to the table", "loop the ListObject", "why is DataBodyRange Nothing",
  "create a pivot table in VBA", "refresh the pivot", "build a chart from this range",
  "write this formula from code", "R1C1", "my formula got an @ in it", "find the last
  row", "copy only the visible rows", "read the cell value without the format".
  Boundaries: general VBA mechanics — error handling, the performance wrapper, the
  Range⇄array round-trip, binding, naming — are vba-development, and this skill defers
  to it rather than restating it; dialogs are vba-userforms; reviewing existing code is
  vba-review; SQL/ADO/DAO against a database is vba-data-access; packaging is
  vba-addin-building / vba-distribution. This skill owns *Excel's own objects*.
---

# VBA — the Excel Object Model

`vba-development` teaches how to write VBA. This skill teaches what to write it *against*:
the Excel-specific objects that carry the data. Assume its rules are already in force —
`Option Explicit`, the structured error handler, the performance wrapper, and above all
**read once, write once** through the Range⇄array round-trip. Everything here is layered
on top of that; do not restate it.

Two rules govern this whole surface:

1. **Address structure, not coordinates.** A `ListObject` column resolved by name survives
   a user inserting a column; `Range("D2:D500")` does not. Prefer the named object at every
   level — table, column, pivot field, chart series.
2. **Every accessor here can return `Nothing` or empty.** `DataBodyRange`, `SpecialCells`,
   `HeaderRowRange`, `TotalsRowRange`, `ChartObjects(…)` — the empty case is the normal
   case on a freshly built sheet, and it is the single biggest source of run-time 91 and
   1004 in Excel VBA. Guard it before you dereference it.

---

## Tables (`ListObject`) — the structural unit

A Table is the right container for tabular data written or read by code: it grows on
append, its columns are addressable by name, and its range references stay correct.

```vba
Dim ws As Worksheet, lo As ListObject
Set ws = ThisWorkbook.Worksheets("Data")
Set lo = ws.ListObjects("tblOrders")          ' by NAME — never ListObjects(1)
```

### The anatomy — and which part you actually want

| Property | What it covers | Empty-table behaviour |
|---|---|---|
| `.Range` | header + body + totals | always a range |
| `.HeaderRowRange` | the header row only | `Nothing` if `ShowHeaders = False` |
| `.DataBodyRange` | **the data rows only** | **`Nothing` when the table has no data rows** |
| `.TotalsRowRange` | the totals row only | `Nothing` if `ShowTotals = False` |
| `.ListColumns("X").DataBodyRange` | one column's data cells | `Nothing` on an empty table |

`DataBodyRange` returning `Nothing` on a table with no data rows is documented, and it is
the trap: a table with a header row and *no* rows still looks populated in the UI. Never
write `lo.DataBodyRange.Rows.Count` unguarded.

```vba
Dim data As Variant
If lo.DataBodyRange Is Nothing Then
    ' zero rows — not an error, just nothing to do
Else
    data = lo.DataBodyRange.Value2         ' one read, per vba-development
End If
```

### Creating a table

```vba
Set lo = ws.ListObjects.Add( _
             SourceType:=xlSrcRange, _
             Source:=ws.Range("A1").CurrentRegion, _
             XlListObjectHasHeaders:=xlYes, _
             TableStyleName:="TableStyleLight1")
lo.Name = "tblOrders"                       ' name it immediately; the default is Table1, Table2, …
```

Three documented constraints on `ListObjects.Add`:

- **`LinkSource` is invalid when `SourceType` is `xlSrcRange`** and raises an error *if
  supplied at all* — omit it entirely, don't pass `False`.
- **`Destination` is ignored when `SourceType` is `xlSrcRange`** (it's required, and only
  meaningful, for `xlSrcExternal`).
- **Header cells get converted to Text**, using the cell's *visible* text — so a
  locale-dependent date format in the header row produces a locale-dependent column name.
  Duplicate visible header texts get an incremental integer appended to disambiguate.
  Write literal string headers before calling `Add` and this never bites you.

Pass `XlListObjectHasHeaders:=xlYes` explicitly. The default is `xlGuess`, and a guess is
not a contract.

### Appending rows

```vba
Dim lr As ListRow
Set lr = lo.ListRows.Add                     ' omit Position → appended at the bottom
lr.Range(1, lo.ListColumns("Order ID").Index).Value2 = 4711
```

`ListRows.Add(Position, AlwaysInsert)` returns the new `ListRow`; omitting `Position`
appends. Adding rows one at a time is a per-row round trip into Excel — for anything
bulk, size the table once and write the block:

```vba
lo.Resize lo.Range.Resize(1 + UBound(data, 1), lo.ListColumns.Count)
lo.DataBodyRange.Value2 = data               ' one write
```

`Resize` has three documented constraints: the header must stay in the **same row**, the new
range must **overlap** the original, and the result must contain a header row **and at least
one row of data**. Hence the `1 +` — and hence the fact that you cannot resize a table down
to zero data rows. No cells are inserted or moved, so anything below the table is
overwritten, not pushed down. Add another row for a totals row if `ShowTotals` is on, or turn
it off, resize, and turn it back on.

### Structured references in code

`.Formula` accepts structured references as text — they are the durable way to point at a
table from a formula you generate:

```vba
lo.ListColumns("Total").DataBodyRange.Formula = "=[@Qty]*[@[Unit Price]]"
```

Note the doubled brackets: a column name containing a space must be wrapped
(`[@[Unit Price]]`), and `@` here is the structured-reference *this row* marker — unrelated
to the dynamic-array `@` below.

---

## Reading values: `.Value2`, `.Value`, `.Text`

Microsoft's own performance guidance ranks these, and the ranking is not intuitive:

- **`.Value2` — fast, and does not alter the data.** The default choice for reading.
- **`.Value` — slow.** For a cell formatted as Date or Currency it returns a VBA `Date` or
  `Currency`, which loses precision and can break calls into worksheet functions.
- **`.Text` — slow, lossy, and layout-dependent.** It returns the *formatted* string, so it
  can return `###` purely because of the current column width or zoom.

The cost of `.Value2` is that dates arrive as serial numbers. That is a feature when you're
computing and a nuisance when you're displaying; convert explicitly with `CDate` at the
point of display rather than paying `.Value` on the whole block.

**Never use `.Text` to decide anything.** If code branches on `.Text`, it branches on
formatting — the same data renders differently on another user's machine.

---

## Writing formulas from code

Three properties, and picking the wrong one silently changes what the formula computes.

| Property | Evaluation | Can spill? |
|---|---|---|
| `.Formula` | implicit intersection (the pre-dynamic-array dialect) | never |
| `.Formula2` | array evaluation (the dynamic-array dialect) | yes |
| `.FormulaR1C1` | same as `.Formula`, R1C1 notation | never |

Excel translates between the two dialects on read, and the translation is visible: setting
`.Formula = "=SQRT(A1:A4)"` and then reading `.Formula2` gives `"=SQRT(@A1:A4)"` — the `@`
marks where implicit intersection *would* occur. Reading `.Formula` on a formula that was
set with `.Formula2` strips `@`s that would be applied silently anyway. So an unexpected
`@` appearing in your formula is not corruption; it is the round trip telling you the
formula was written in the other dialect.

Microsoft's stated rule:

- Targeting dynamic-array Excel only → **use `.Formula2`**.
- Targeting both pre- and post-dynamic-array Excel → **use `.Formula`**, unless you need
  tight control over what the user sees in the formula bar, in which case detect whether
  `.Formula2` is supported and fall back.

Detection has to be **late-bound**, and that is the part people get wrong. `.Formula2` is
resolved against the referenced Excel type library at *compile* time — so a project that
mentions `rng.Formula2` anywhere fails to compile on an Excel whose type library predates
it, and the fallback never runs. Route the probe *and* the write through an `Object`
variable so neither is compiled against the member:

```vba
Private Function Formula2Supported(ByVal target As Range) As Boolean
    Dim obj As Object, probe As Variant
    Set obj = target                       ' Object-typed → late bound, no compile-time member
    On Error Resume Next
    probe = obj.Formula2
    Formula2Supported = (Err.Number = 0)
    On Error GoTo 0
End Function

Private Sub SetFormula(ByVal target As Range, ByVal f As String)
    Dim obj As Object
    Set obj = target
    If Formula2Supported(target) Then obj.Formula2 = f Else target.Formula = f
End Sub
```

`.FormulaR1C1` earns its place when you're writing the *same relative* formula down a
column — `"=RC[-2]*RC[-1]"` is one string for every row, where A1 notation needs one per
row. Write the whole column in a single assignment either way; setting a formula on a
multi-cell range fills every cell in it.

---

## PivotTables

Two steps, always: build a cache, then build the table on it.

```vba
Dim pc As PivotCache, pt As PivotTable
Set pc = ThisWorkbook.PivotCaches.Create( _
             SourceType:=xlDatabase, _
             SourceData:="tblOrders")            ' a STRING — see below
Set pt = pc.CreatePivotTable( _
             TableDestination:=wsOut.Range("A3"), _
             TableName:="ptSummary")

With pt
    .PivotFields("Region").Orientation = xlRowField
    .PivotFields("Month").Orientation = xlColumnField
    With .PivotFields("Amount")
        .Orientation = xlDataField
        .Function = xlSum
        .NumberFormat = "#,##0.00"
        .Name = "Total Amount"                   ' must differ from the source field name
    End With
End With
```

Three documented traps:

- **Pass `SourceData` as a string, not a `Range` object.** Microsoft explicitly recommends
  a string naming the workbook/worksheet/range, or a defined name — "passing a `Range`
  object may cause 'type mismatch' errors unexpectedly." A table name works and is the most
  durable form.
- **`SourceData` is required unless `SourceType` is `xlExternal`.** For `xlExternal` it
  takes a `WorkbookConnection`, not a range.
- **Never pass `xlPivotTableVersionCurrent` as `Version`** — it is explicitly disallowed and
  raises a run-time error. Omit `Version` (you get `xlPivotTableVersion12`) or name a real
  version constant.

Renaming a data field to the source field's own name raises an error — that is why the
example sets `.Name = "Total Amount"` rather than `"Amount"`. *(Field-observed; the
`PivotField.Name` reference doesn't state it. `PivotField.SourceName` is the documented way
to recover the original name after a rename.)*

Refreshing: `pt.RefreshTable` refreshes one table; `pc.Refresh` refreshes every table
sharing that cache. Two pivots built from one `PivotCaches.Create` call share a cache, and
that is usually what you want — separate caches double the memory and can drift out of
sync. `ChangePivotCache` only works on worksheet-sourced pivots; it errors on a pivot bound
to an external source.

---

## Charts

For an embedded chart on a worksheet, `ChartObjects.Add(Left, Top, Width, Height)` — all
four are required, all in **points**, measured from the top-left of cell A1:

```vba
Dim co As ChartObject
Set co = ws.ChartObjects.Add(Left:=300, Top:=20, Width:=400, Height:=250)
With co.Chart
    .ChartType = xlColumnClustered
    .SetSourceData Source:=lo.Range, PlotBy:=xlColumns
    .HasTitle = True
    .ChartTitle.Text = "Orders by Region"
End With
co.Name = "chtOrders"
```

Anchor to the grid rather than to absolute points when the sheet's geometry can change:

```vba
With ws.Range("F2:M16")
    Set co = ws.ChartObjects.Add(.Left, .Top, .Width, .Height)
End With
co.Placement = xlMoveAndSize                 ' or xlFreeFloating to survive row deletes
```

`SetSourceData` takes a **`Range`** here (unlike `PivotCaches.Create`) — pointing it at a
`ListObject.Range` means the chart grows with the table. `Shapes.AddChart2(Style,
XlChartType, Left, Top, Width, Height, NewLayout)` is the modern alternative and is the one
to reach for when you want a specific built-in style; it returns a `Shape`, so the chart is
`shp.Chart`.

Address series by index only inside the loop that just created them. Anywhere else, name
them (`.SeriesCollection(1).Name = "=Data!$D$1"`) and look them up by name — series
indices reshuffle when the source range changes.

---

## Finding the data

**`UsedRange` is not the data.** It is Excel's bookkeeping of what has ever been touched,
including cleared cells and stray formatting, and it does not reliably shrink. Use it for
an upper bound, never for a row count. *(Field-observed — the reference documents what
`UsedRange` returns, not that it over-reports; treat the over-report as reliably true in
practice and never as a contract you can compute against.)*

The reliable idioms:

```vba
lastRow = ws.Cells(ws.Rows.Count, "A").End(xlUp).Row      ' bottom-up: immune to trailing junk
lastCol = ws.Cells(1, ws.Columns.Count).End(xlToLeft).Column
```

Bottom-up beats `End(xlDown)` from the top, which stops at the first blank cell inside the
block. Both are blind to blanks in the probed column — if column A can be empty mid-block,
probe a column that can't, or use the table's `DataBodyRange` and sidestep the question.

### `SpecialCells` raises when nothing matches

`SpecialCells` is the documented way to narrow a range before operating on it, and
Microsoft's performance guidance recommends it for exactly that. What the documentation
does *not* state — but is consistent field behaviour — is that **it raises run-time error
1004 ("No cells were found") instead of returning an empty range when nothing matches.**
Treat that as observed behaviour, not a contract, and guard it either way:

```vba
Dim vis As Range
On Error Resume Next
Set vis = lo.DataBodyRange.SpecialCells(xlCellTypeVisible)
On Error GoTo 0
If vis Is Nothing Then Exit Sub               ' filter matched nothing
```

The `On Error Resume Next` is scoped to the single statement and cleared immediately — this
is the one narrow exception to `vba-development`'s rule against resume-next; it is not
licence to wrap a block.

### Filtering

`AutoFilter` on a `ListObject` goes through `lo.Range.AutoFilter`. `Field:=` is documented as
"the integer offset of the field **from the left of the list**" — for a table, that means the
column's index **within the table**, not the worksheet column:

```vba
lo.Range.AutoFilter Field:=lo.ListColumns("Status").Index, Criteria1:="Open"
```

A filtered range still *contains* the hidden rows: `lo.DataBodyRange.Value2` returns
everything. Only the `xlCellTypeVisible` subset above is the filtered result — and copying
that subset gives you a multi-area range, so iterate `.Areas` rather than assuming one
contiguous block.

Clear filters with `lo.AutoFilter.ShowAllData` — but only when `lo.AutoFilter` is not
`Nothing` and `lo.AutoFilter.FilterMode` is `True`, or it raises.

---

## Watch Out

- **`DataBodyRange Is Nothing` is the empty table, not a bug.** Every read from a table
  needs the guard. Same for `HeaderRowRange` when `ShowHeaders` is off.
- **`ListObjects(1)` / `Worksheets(1)` / `SeriesCollection(1)`** — index-based access breaks
  the first time a user adds anything. Name everything, address by name.
- **`.Text` reflects formatting, not data.** Never branch on it, never write it to a store.
- **A stray `@` in a formula is a dialect translation, not corruption.** Decide `.Formula`
  vs `.Formula2` deliberately, and don't mix the two on one range.
- **`PivotCaches.Create` with a `Range` object throws type mismatch unpredictably** — pass
  a string. And never pass `xlPivotTableVersionCurrent`.
- **`SpecialCells` on no matches raises 1004.** Always the scoped guard.
- **`UsedRange` overstates.** It's a ceiling, not a count.
- **A per-row `ListRows.Add` loop is a per-row COM round trip.** `Resize` once and assign
  the block — the same read-once/write-once rule `vba-development` states for ranges.
- **`CopyFromRecordset` is the other bulk write into a sheet** — it belongs to
  `vba-data-access`, along with everything about where the recordset came from.
