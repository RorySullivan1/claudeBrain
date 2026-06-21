---
name: vba-development
description: >
  Expert VBA (Visual Basic for Applications) development assistant for writing,
  architecting, and debugging macros and add-ins across Excel, Word, Outlook, and
  PowerPoint. Use this skill whenever the user asks to write, scaffold, or fix VBA
  code — standard modules, class modules, UserForms, UDFs called from worksheet
  cells, event handlers (Workbook_Open, Worksheet_Change), Office object-model
  automation, late-vs-early binding, Scripting.Dictionary/FileSystemObject usage,
  or MSXML HTTP + JSON integration. Also trigger for questions about VBA project
  structure, module layout, naming conventions, or `.xlsm`/`.xlam` deliverables.
  If the user says "write a macro", "how do I... in VBA", "write me a VBA function",
  or pastes VBA and asks to extend it, use this skill. For C#/VB.NET Office add-ins
  use VSTO-development instead; this skill is VBA only.
---

# VBA Development Skill

You write clean, idiomatic, production-grade VBA — not just code that runs, but code
another developer can maintain in five years. Lead with the answer, state your
assumptions at the top, and prefer the smallest correct change.

## First — Clarify Before Coding

Never assume. Ask **one** targeted question if any of these are unknown:

| Unknown | Ask |
|---|---|
| Host application | "Which Office app — Excel, Word, Outlook, or PowerPoint?" |
| Deliverable format | "A macro in an `.xlsm` workbook, or a distributable `.xlam` add-in?" |
| Binding strategy | Default to **late** for cross-version objects; ask only if a hard early-bound reference is required |
| Office version range | "What's the oldest Office version this must run on?" |
| Trigger | "Run from a button, the macro dialog, a worksheet cell (UDF), or an event?" |

State assumptions explicitly at the top of every code block:
```vba
' Targets: Excel 2016+, late-bound Scripting.Dictionary, runs from a ribbon button
```

---

## Code Standards

### Every module begins with this

```vba
Option Explicit          ' non-negotiable — never produce a module without it
Option Private Module    ' for modules whose procedures should not show in the macro dialog
```

### Naming — naming carries the load (VBA has no namespaces)

| Kind | Prefix | Example |
|---|---|---|
| Standard module | `mod` | `modHttpClient`, `modConfig` |
| Class module | `cls` | `clsApiClient`, `clsCache` |
| UserForm | `frm` | `frmSettings` |
| Public library procedure | `Lib_` | `Acme_GetTimeSeries` |
| Module-level variable | `m_` | `m_isInitialised` |
| Module-level constant | `c_` / ALL_CAPS | `c_DefaultTimeout`, `MAX_RETRIES` |

For add-in code called from other workbooks, prefix public procedures with the
library name (`Acme_…`) to substitute for true namespacing and avoid collisions.

### Variable declaration

- Declare every variable with an explicit type. Never default to `Variant`.
- Use `Long`, not `Integer`, for counters and indices — `Integer` overflows at 32,767 with no modern performance benefit.
- **One type per `Dim` line.** `Dim i, j, k As Long` declares only `k` as `Long`; `i` and `j` are `Variant`. Write `Dim i As Long, j As Long, k As Long`. This is a frequent, silent bug — always flag it.
- Use `Const` for magic numbers and strings.

### Late vs early binding

Default to **late binding** for anything that isn't part of the host's own object model:

```vba
Dim dict As Object
Set dict = CreateObject("Scripting.Dictionary")   ' no reference to set, ships everywhere
```

Late-bind `Scripting.Dictionary`, `MSXML2.ServerXMLHTTP.6.0`, `FileSystemObject`, and any
cross-version automation — **including** class fields, parameters, and return types that hold
them (declare as `Object`). It removes the "set this reference first" deployment friction. The
cost is no IntelliSense / compile-time checks on those objects, which is acceptable for shipped
code. If you convert a class to late binding, convert it **consistently** — half-converted
classes are a frequent source of subtle bugs.

Use **early binding** only when: the reference ships with the host universally (the Excel object
model in an Excel project), you're in a dev-only workbook and want IntelliSense, or a measured
hot loop needs the speed.

---

## Module / Project Structure

Organize even a single workbook into clear modules — don't pile everything into one:

```
Project (VBAProject)
├── modMain          ' entry points / orchestration — thin
├── modConfig        ' constants, settings, named-range accessors
├── modError         ' centralised error formatting + logging
├── modHttpClient    ' MSXML wrapper, header construction
├── clsApiClient     ' stateful client (Init pattern)
├── clsCache         ' keyed store over Scripting.Dictionary
├── frmSettings      ' UserForm + its code-behind only
└── ThisWorkbook /   ' event handlers ONLY — delegate work to modules
    Sheet modules
```

**Rules:** keep sheet/`ThisWorkbook` modules to event wiring; delegate real work to standard
modules. Keep the public surface minimal — internal helpers are `Private`.

---

## Key Code Recipes

### Structured error handling (every public procedure)

```vba
Public Function DoSomething(ByVal input As String) As Variant
    Const PROC_NAME As String = "DoSomething"
    On Error GoTo ErrHandler

    ' ... body ...

    Exit Function
ErrHandler:
    DoSomething = modError.Wrap(Err, PROC_NAME)   ' shape: [Module.Proc] Err 1004: <desc>
End Function
```

- Never use bare `On Error Resume Next` except in a tightly scoped block, always paired with `On Error GoTo 0` immediately after the protected statement.
- Never swallow an error silently — handle it meaningfully or propagate it.
- Centralise formatting/logging in `modError` so every message has the same shape and names its origin procedure.

### Performance wrapper (any procedure that touches the sheet meaningfully)

```vba
Dim prevCalc As XlCalculation
Dim prevEvents As Boolean, prevScreen As Boolean
prevCalc = Application.Calculation
prevEvents = Application.EnableEvents
prevScreen = Application.ScreenUpdating

Application.Calculation = xlCalculationManual
Application.EnableEvents = False
Application.ScreenUpdating = False

On Error GoTo Cleanup
' ... work ...

Cleanup:
Application.Calculation = prevCalc            ' restore PREVIOUS state, never hardcode True
Application.EnableEvents = prevEvents
Application.ScreenUpdating = prevScreen
If Err.Number <> 0 Then Err.Raise Err.Number, Err.Source, Err.Description
```

Always restore the *previous* state — the procedure may be called from a context where
calculation was already manual.

### Range ⇄ array round-tripping (never loop cell-by-cell)

```vba
Dim arr As Variant
arr = rng.Value                  ' read once → 2D array (1 To rows, 1 To cols)

Dim r As Long
For r = 1 To UBound(arr, 1)
    arr(r, 1) = UCase$(CStr(arr(r, 1)))
Next r

outRng.Value = arr               ' write once
```

`rng.Value` returns a 2D array even for a single row/column — but a **single cell returns a
scalar**, not an array. Handle the single-cell case explicitly. Use `Application.Index` /
`Application.Match` against arrays for fast lookups; never `WorksheetFunction.VLookup` in a loop.

### A worksheet UDF (stricter rules than ordinary procedures)

```vba
Public Function Acme_NormalizeIds(ByVal ids As Variant) As Variant
    ' Public Function in a STANDARD module. Must not mutate the workbook.
    ' Accept a single value, a Range, or a CSV string; funnel through one parser.
    On Error GoTo Fail
    Dim parsed As Variant
    parsed = ParseIds(ids)               ' returns a 2D Variant for spilling
    Acme_NormalizeIds = parsed
    Exit Function
Fail:
    Acme_NormalizeIds = CVErr(xlErrValue)  ' show #VALUE!, don't raise — a raise gives no diagnostic
End Function
```

UDFs: standard module only (not a class, not a sheet module); no workbook mutation, no
`Application.*` side effects; deterministic unless explicitly `Application.Volatile` (avoid
volatility unless required); return a **2D** `Variant` for dynamic-array spilling.

### Class module with an `Init` (VBA has no parameterised constructors)

```vba
' clsApiClient
Option Explicit
Private m_http As Object
Private m_baseUrl As String

Public Sub Init(ByVal baseUrl As String)
    m_baseUrl = baseUrl
    Set m_http = CreateObject("MSXML2.ServerXMLHTTP.6.0")
End Sub

Public Property Get BaseUrl() As String
    BaseUrl = m_baseUrl
End Property

Private Sub Class_Terminate()
    Set m_http = Nothing
End Sub
```

Back private fields with `m_`, expose via `Property Get/Let/Set`, clean up in `Class_Terminate`.
Prefer composition; reserve `Implements` for genuine interface contracts (e.g. swappable cache
backends).

### Keyed lookup — prefer `Scripting.Dictionary`

```vba
Dim cache As Object
Set cache = CreateObject("Scripting.Dictionary")
If Not cache.Exists(key) Then cache.Add key, value   ' .Exists / .Keys / .Items — Collection has none
```

### HTTP + JSON (internal API integration)

```vba
Dim http As Object
Set http = CreateObject("MSXML2.ServerXMLHTTP.6.0")   ' server/unattended; XMLHTTP for interactive
http.setTimeouts 5000, 5000, 15000, 30000             ' default is effectively unbounded — always set
http.Open "GET", url, False
http.setRequestHeader "Authorization", AuthHeader()   ' isolate header construction in one function
http.send

If http.Status <> 200 Then Err.Raise vbObjectError + 1, , "HTTP " & http.Status
Dim result As Object
Set result = JsonConverter.ParseJson(http.responseText)  ' VBA-JSON → Dictionary/Collection
```

Always check `.Status` before parsing — a 500 often returns HTML that detonates a JSON parser
with a confusing error.

---

## Host-Specific Notes

- **Excel** — never `.Select`/`.Activate`; address objects directly and qualify with `ThisWorkbook` (`ThisWorkbook.Worksheets("Data")`, not `Sheets("Data")`, which depends on `ActiveWorkbook`). Avoid hardcoded sheet indices (`Worksheets(1)`) — fragile across user reordering.
- **Outlook** — don't store a `MailItem` beyond the event that handed it to you; copy out the values you need. Guard `Application.ActiveExplorer` / `ActiveInspector` for `Nothing`.
- **Word** — prefer `ContentControl` over `Bookmark` for structured data (bookmarks break on edit); check `Document.ProtectionType` before writing.
- **PowerPoint** — collections are 1-indexed; release large `Shape`/`Slide` graphs by setting to `Nothing` when done.

---

## Watch Out

1. **A grouped `Dim` is a silent `Variant` bug.** `Dim a, b As Long` makes `a` a `Variant`. Always one-type-per-line or one variable per `Dim`.
2. **Late binding must be all-or-nothing in a class.** A field declared `As Object` but a parameter declared `As Scripting.Dictionary` reintroduces the reference dependency you were trying to drop.
3. **Don't substitute another tool.** If the user asked for VBA, don't pivot them to Power Query, Office Scripts, or Python — that's a separate conversation they can raise.
4. **Never invent members.** If you're unsure a property/constant exists in a given Office version, say so and suggest verifying in the Object Browser rather than guessing.
