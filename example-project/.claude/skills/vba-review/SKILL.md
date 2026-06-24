---
name: vba-review
description: >
  Expert VBA code reviewer for Excel/Word/Outlook/PowerPoint macros and add-ins.
  Use this skill whenever the user pastes VBA and asks for a review, audit, feedback,
  or help improving it. Also trigger when the user reports a bug, a slow macro, a
  wrong UDF result, a workbook that won't close, or unexpected Office behavior and
  shares VBA as context — even without the word "review". Trigger on phrases like
  "what's wrong with this macro", "can you check this VBA", "is this correct", "why
  is this slow", "review my macro", or any paste of VBA followed by a question.
  Prioritize correctness over style: check Option Explicit, declaration bugs,
  error handling, range/array performance, and application-state hygiene before
  anything cosmetic. Because VBA has no external CI, a review must also say how to
  *verify* a fix inside the host Office app. For C#/VB.NET Office add-ins use
  VSTO-review instead; to author the tests a review asks for, use vba-code-test-writing.
---

# VBA Code Review Skill

You review VBA for the defects that actually bite: silent `Variant` bugs, swallowed
errors, cell-by-cell loops, and left-behind application state. Lead with the most
severe issue. Present findings grouped by severity, not in the order you found them.

## Review Priority Order

Evaluate in this sequence. Never skip to style while a correctness issue stands:

1. **`Option Explicit` + declaration bugs** — missing `Option Explicit`; grouped `Dim` that silently makes `Variant`s; `Integer` where overflow is possible
2. **Error handling** — bare `On Error Resume Next`, swallowed errors, UDFs that raise instead of returning `CVErr`
3. **Performance** — cell-by-cell range loops instead of array round-tripping; unnecessary `Application.Volatile`
4. **Application-state hygiene** — `Calculation`/`EnableEvents`/`ScreenUpdating` not saved-and-restored (or hardcoded back to `True`)
5. **Binding consistency** — half-converted late/early binding; references the user must set manually
6. **Object-reference correctness** — `.Select`/`.Activate`/`ActiveSheet`; unqualified `Sheets(...)`; hardcoded sheet indices
7. **Architecture & API surface** — work in sheet/event modules instead of standard modules; oversized public surface
8. **Style** — naming, dead code, magic numbers

## What to Ask For (if absent)

- **Host application and version** (Excel 2016? Outlook 365?)
- **Deliverable** — `.xlsm` macro, `.xlam` add-in, or worksheet UDF? (the rules differ)
- **The error message verbatim** and which line, if reviewing a bug
- **What "slow" means** — how many rows / how long, if reviewing performance

---

## Review Checklist

### 1. Option Explicit & Declarations

```vba
' BUG: only k is Long; i and j are Variant — slow, and silently coerces types
Dim i, j, k As Long
' FIX
Dim i As Long, j As Long, k As Long
```
Flag a missing `Option Explicit` as the first thing you say — without it, a typo'd variable
name is a silent new `Variant`, not a compile error. Flag `Integer` counters that can exceed
32,767 (e.g. `UsedRange` row counts).

### 2. Error Handling

```vba
' BUG: masks every error in the whole procedure
On Error Resume Next
DoRiskyThing
' ... 40 more lines, all errors swallowed ...

' FIX: scope it to the one statement that can legitimately fail, then turn it off
On Error Resume Next
Set ws = ThisWorkbook.Worksheets("Maybe")
On Error GoTo 0
If ws Is Nothing Then ' handle the missing-sheet case explicitly
```

```vba
' BUG: a UDF that raises shows #VALUE! with no diagnostic and may halt calc
Public Function Foo(x As Range) As Double
    Foo = 1 / x.Value            ' raises on 0 or text
End Function
' FIX: return a CVErr so the cell shows #VALUE! deliberately
Public Function Foo(x As Range) As Variant
    On Error GoTo Fail
    Foo = 1 / x.Value
    Exit Function
Fail:
    Foo = CVErr(xlErrValue)
End Function
```
Flag any `catch`-equivalent that swallows silently, and any public procedure with no labelled
handler. Error messages should name the procedure they came from.

### 3. Performance — Range/Array

```vba
' BUG: one COM round-trip per cell — minutes on large ranges
Dim r As Long
For r = 1 To rng.Rows.Count
    rng.Cells(r, 1).Value = UCase$(rng.Cells(r, 1).Value)
Next r

' FIX: read once, process in memory, write once
Dim arr As Variant: arr = rng.Value
For r = 1 To UBound(arr, 1)
    arr(r, 1) = UCase$(CStr(arr(r, 1)))
Next r
rng.Value = arr
```
Also flag `WorksheetFunction.VLookup`/`Match` *inside* loops (use `Application.Match` over an
array once) and `Application.Volatile` in UDFs that don't need it — it recalcs on every change.

### 4. Application-State Hygiene

```vba
' BUG: leaves the user's calc on Manual and events off if the body errors
Application.Calculation = xlCalculationManual
Application.ScreenUpdating = False
DoWork
Application.Calculation = xlCalculationAutomatic   ' wrong: hardcoded, and skipped on error
Application.ScreenUpdating = True
```
Require: capture previous values, restore them in a `Cleanup:` label reached on error too,
and restore the *previous* value rather than hardcoding `True`/`xlCalculationAutomatic`.

### 5. Binding Consistency

Flag a class whose field is `As Object` (late) but whose property/parameter is
`As Scripting.Dictionary` (early) — it reintroduces the manual-reference dependency. Flag any
hard reference to a non-host library (`Scripting`, `MSXML2`, FSO) that a late-bound
`CreateObject` would remove from the deployment burden.

### 6. Object-Reference Correctness

```vba
' BUG: depends on what's active; fragile and slow
Sheets("Data").Select
Range("A1").Value = 1

' FIX: address directly, qualified to the workbook
ThisWorkbook.Worksheets("Data").Range("A1").Value = 1
```
Flag `.Select`/`.Activate`/`ActiveSheet`/`ActiveCell` outside genuine event handlers, unqualified
`Sheets(...)` (depends on `ActiveWorkbook`), and `Worksheets(1)` index access (breaks when a user
reorders tabs).

### 7. Architecture & API Surface

| Problem | Recommendation |
|---|---|
| Real logic living in a `Sheet`/`ThisWorkbook` module | Move to a standard module; keep event modules to event wiring |
| Everything `Public` | Make internal helpers `Private`; expose a minimal surface |
| Magic numbers / sheet names inline | Promote to `Const` / a `modConfig` accessor |
| File opened `For Input` with no `Close` on the error path | Add a cleanup label that closes the handle |

---

## Review Output Format

### Critical (fix before shipping)
Silent data corruption, swallowed errors, left-behind application state, UDFs that mutate or raise.

### Important (fix soon)
Cell-by-cell performance, half-converted binding, fragile `ActiveSheet`/index references.

### Minor (nice to fix)
Naming, dead code, magic numbers, oversized public surface.

### Summary
One paragraph: overall quality and the single most important thing to fix first.

---

## Verifying — There Is No CI

A VBA review is only half-done if it stops at "here's the bug." VBA cannot be linted,
compiled, or run outside its host Office app on Windows — there is no `pytest`/`ruff`
to invoke, no headless CI. So **never claim a fix is verified from reading alone**, and
hand the user a concrete way to confirm it. For each correctness fix you propose:

1. **Trace the failure paths explicitly** — empty range, a single cell (scalar, not a
   2D array), a missing sheet, an error/blank cell value, an HTTP non-200. These are
   where VBA actually breaks, and where a "looks fine" review goes wrong.
2. **Give a runnable check.** Prefer a tiny test `Sub` the user runs from the
   Immediate window (`?FunctionUnderTest(args)` or a `RunTests` sub), or a
   `Debug.Assert` they can drop in. State the inputs and the expected result.
3. **Assess testability while you review.** If the logic is fused to the object model
   (reads `ActiveSheet`, takes `Range` instead of values), flag it: it *can't* be unit
   tested as written. Recommend extracting the pure logic — and route the actual test
   authoring to the `vba-code-test-writing` skill.
4. **State the environment caveat** when relevant: results can only be fully confirmed
   in the host app, and on a Mac or a locked-down machine even that may be constrained.

```vba
' Minimal verification a reviewer can hand back — run NormalizeName_Tests from the Immediate window
Public Sub NormalizeName_Tests()
    Debug.Assert NormalizeName("  ab ") = "Ab"        ' trims + title-cases
    Debug.Assert NormalizeName("") = ""               ' empty stays empty (no error)
    Debug.Print "NormalizeName: all asserts passed"
End Sub
```

---

## Watch Out

1. **"It works on my 100-row sheet" hides O(n) COM overhead.** The same cell-by-cell loop is minutes on the real 200k-row workbook. Judge performance by the loop shape, not the demo.
2. **A swallowed error is worse than a crash.** `On Error Resume Next` over a whole procedure turns a clear failure into a silently wrong result the user trusts. Always flag it.
3. **Leftover Manual calculation is a support ticket waiting to happen.** A macro that errors out without restoring `Application.Calculation` leaves every later edit not recalculating — and the user blames Excel, not the macro.
