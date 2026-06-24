---
name: vba-code-test-writing
description: >
  Expert at writing tests for VBA (Excel/Word/Outlook/PowerPoint macros and add-ins),
  where the test runner lives *inside* the host Office app and there is no real
  headless CI. Use this skill whenever the user wants to write, structure, or run VBA
  unit tests: adding test coverage to a macro/`.xlam`, setting up Rubberduck test
  modules (annotations, the Assert object, Fakes for built-ins like MsgBox/Now), a
  no-add-in fallback harness (Immediate-window runner, `Debug.Assert`, a hand-rolled
  assert module), making untestable object-model-bound code testable, or automating a
  test run by driving the host via COM. Trigger on "write tests for this macro",
  "unit test this VBA", "set up Rubberduck", "how do I test a UDF", "test without
  Excel open", "make this testable", "CI for VBA", "mock MsgBox/Now in a test". Builds
  on vba-development (write the code) and pairs with vba-review (which flags what to
  test); this skill owns *authoring the tests* and the in-host verification strategy.
---

# VBA Test-Writing Skill

VBA testing is unusual: **the test runner is the host Office application itself.** There
is no `pytest`, no headless CI you can trust, and no compile step outside the VBE. That
single fact drives every decision here. Your job is to make VBA code *provable* anyway —
first by designing it so it *can* be tested, then by writing tests in the right harness,
and finally by being honest about what can and can't be automated.

## First — Clarify

| Unknown | Ask |
|---|---|
| Tooling allowed | "Is **Rubberduck** installed/permitted, or must tests be plain VBA (no add-in)?" |
| What's under test | "Pure logic (parsing, math, formatting), or code that drives the worksheet/host?" |
| Run context | "Run by hand in the VBE, or does this need to run unattended (CI)?" |
| Platform | "Windows only, or must this work on Mac?" (Mac changes everything — see the gap) |

---

## Pillar 1 — Make It Testable First (the real work)

Most "I can't test this" is a *design* problem, not a tooling one. Code fused to the
Office object model cannot be unit-tested; pure logic can. Before writing a single test,
separate the two — this is the highest-leverage step and usually the bulk of the effort.

```vba
' UNTESTABLE: reaches into the host, takes a Range, mutates the sheet — needs live Excel
Public Sub MarkOverdue()
    Dim r As Long
    For r = 2 To ActiveSheet.UsedRange.Rows.Count
        If ActiveSheet.Cells(r, 3).Value < Date Then ActiveSheet.Cells(r, 4).Value = "OVERDUE"
    Next r
End Sub

' TESTABLE: pure function over values; the host boundary is a thin, separate shell
Public Function OverdueFlags(ByVal dueDates As Variant, ByVal asOf As Date) As Variant
    Dim out() As String, i As Long
    ReDim out(LBound(dueDates) To UBound(dueDates))
    For i = LBound(dueDates) To UBound(dueDates)
        out(i) = IIf(IsDate(dueDates(i)) And dueDates(i) < asOf, "OVERDUE", "")
    Next i
    OverdueFlags = out
End Function
```

Rules that make VBA testable:
- **Take values, return values.** Read a `Range` into a `Variant` array at the boundary,
  compute on the array, write back — don't pass `Range` objects into logic.
- **Inject the host, don't reach for it.** Pass `Worksheet`/`Workbook` as parameters;
  never read `ActiveSheet`/`Selection`/globals inside logic.
- **Pass `asOf`/config in.** Don't read `Now`/`Date`/`Environ` deep inside a function —
  take them as arguments so a test can pin them (or fake them; Pillar 2).
- **Seam external effects behind an interface.** File IO, HTTP, and the like go behind a
  class you `Implements`, so a test can substitute a fake. (See `vba-development` for the
  `Implements`/`Init` patterns.)

A reviewer (`vba-review`) flags object-model coupling; this skill is where you actually
extract the pure function and test it.

---

## Pillar 2 — Rubberduck (the real test framework)

[Rubberduck](https://rubberduckvba.com) is the open-source VBE add-in that gives VBA a
real unit-test framework, run from a **Test Explorer** toolwindow inside the host app.
Tests live in a standard module marked with annotation comments.

**Annotations** (exact spellings — `'@` marker comments):
- `'@TestModule` — in the module's declarations section.
- `'@TestMethod("Category")` — before each test `Sub` (the category string is optional).
- `'@ModuleInitialize` / `'@ModuleCleanup` — run once per module.
- `'@TestInitialize` / `'@TestCleanup` — run before/after every test.

Test methods and lifecycle subs are `Public`, parameterless `Sub`s.

**The `Assert` object** — declare `Private Assert As New Rubberduck.AssertClass`. Methods:
`AreEqual`, `AreNotEqual`, `AreSame`, `AreNotSame`, `IsTrue`, `IsFalse`, `IsNothing`,
`IsNotNothing`, `Fail`, `Succeed`, `Inconclusive`, `SequenceEquals`, `NotSequenceEquals` —
each takes an optional trailing message string. `Rubberduck.PermissiveAssertClass` is the
same surface with VBA-style loose equality (type coercion, looser string compare) instead
of the default strict equality; swap the declared type to choose.

```vba
'@TestModule
Option Explicit
Private Assert As New Rubberduck.AssertClass

'@TestMethod("Overdue")
Public Sub OverdueFlags_FlagsPastDatesOnly()
    On Error GoTo TestFail
    Dim due As Variant: due = Array(#1/1/2020#, #1/1/2999#, "not a date")
    Dim got As Variant: got = OverdueFlags(due, #6/1/2026#)
    Assert.AreEqual "OVERDUE", got(0)
    Assert.AreEqual "", got(1)
    Assert.AreEqual "", got(2), "non-dates must not raise"
TestExit:
    Exit Sub
TestFail:
    Assert.Fail "Err #" & Err.Number & " - " & Err.Description
End Sub
```

Every test wraps its body in `On Error GoTo TestFail` and turns an error into
`Assert.Fail` — an unhandled error otherwise aborts the run.

**Fakes — for nondeterminism and UI built-ins.** Rubberduck can intercept VBA built-in
functions so a test neither blocks on a dialog nor depends on the clock. Confirmed
targets include `MsgBox`, `InputBox`, `Now`, `Date`, `Time`, `Timer`, `Environ`,
`Shell`, `Kill`, `Dir`, `Rnd`, `DoEvents` (the live list is Rubberduck issue #2891).
Use the injected `Fakes` provider: set a return, run the code, then `Verify` the call.

```vba
'@TestMethod("Dialog")
Public Sub Prompt_ReturnsYes_WhenUserClicksYes()
    Fakes.MsgBox.Returns vbYes               ' don't actually pop a dialog
    Assert.IsTrue UserConfirmed()            ' code under test calls MsgBox internally
    Fakes.MsgBox.Verify.Once                 ' assert it was shown exactly once
End Sub
```

Prefer faking a built-in (`Now`, `MsgBox`) only when you can't inject the value as a
parameter — injection (Pillar 1) is simpler and add-in-independent. **Always offer the
non-Rubberduck fallback too** (Pillar 3): Rubberduck is Windows-only and may not be
installed or permitted on a locked-down machine, so tests that *require* it aren't
portable.

---

## Pillar 3 — No-Add-In Fallback Harness

When Rubberduck isn't available, write plain-VBA tests: a runner `Sub` plus a tiny assert
module that tallies results and prints a summary. Run it by typing the runner's name in
the **Immediate window** (Ctrl+G), or wire it to a button.

```vba
' modTestRunner — run by typing  RunAllTests  in the Immediate window
Public PassCount As Long, FailCount As Long

Public Sub RunAllTests()
    PassCount = 0: FailCount = 0
    Test_OverdueFlags                      ' call each test sub
    Debug.Print "---- " & PassCount & " passed, " & FailCount & " failed ----"
End Sub

Public Sub AssertEqual(ByVal actual As Variant, ByVal expected As Variant, ByVal name As String)
    If actual = expected Then
        PassCount = PassCount + 1
    Else
        FailCount = FailCount + 1
        Debug.Print "FAIL: " & name & " — expected <" & expected & "> got <" & actual & ">"
    End If
End Sub

Private Sub Test_OverdueFlags()
    Dim got As Variant: got = OverdueFlags(Array(#1/1/2020#, #1/1/2999#), #6/1/2026#)
    AssertEqual got(0), "OVERDUE", "past date flagged"
    AssertEqual got(1), "", "future date not flagged"
End Sub
```

- `Debug.Assert <cond>` is the lightest check — it **breaks into the IDE** at that line
  when the condition is false (Windows VBE only; no message, no effect when run
  unattended). Good for a quick inline guard, not for a reportable suite.
- `Debug.Print` writes to the Immediate window — your only "test output" without an add-in.
- Keep tests in their own `modTests_*` modules, excluded from the shipped build (or
  stripped during the round-trip build — see `vba-distribution`).

---

## Pillar 4 — The CI / Headless Reality (be honest)

VBA tests run **inside an interactive host on Windows.** There is no supported headless
mode. You *can* automate by driving the host via COM and calling the runner:

```powershell
# Windows, interactive logged-in session, macros pre-trusted
$xl = New-Object -ComObject Excel.Application
$wb = $xl.Workbooks.Open("C:\build\Tests.xlsm")
$xl.Run("RunAllTests")          # your Pillar-3 runner; read results from a cell/file it writes
$wb.Close($false); $xl.Quit()
```

State these limits plainly rather than promising green CI:
- **Microsoft does not support server-side/unattended Office automation** (KB257757). On a
  non-interactive session, *any* modal dialog — a macro-security prompt, an unexpected
  error popup — hangs the process indefinitely. Practical runs need a real logged-in
  desktop (a self-hosted runner with autologon), with macro trust pre-configured.
- Have the runner **write results to a cell or a text file**, not just the Immediate
  window, so the external script can read pass/fail and set an exit code.
- **macOS is a hard gap:** Rubberduck is Windows-only and COM automation isn't available —
  Mac VBA can only be tested by hand in the VBE. Say so; don't pretend otherwise.

---

## Output

When you deliver tests, give:
- The **testable refactor** (if the code was object-model-bound) plus the pure function(s).
- The **test module** — Rubberduck if available, else the fallback harness — covering the
  happy path and the failure paths a `vba-review` would flag (empty, single-cell scalar
  vs. 2D array, bad/blank input, error path).
- **Exactly how to run it** (Test Explorer, or `RunAllTests` in the Immediate window) and
  the expected output.
- An honest note on **what can't be automated** in the user's environment.

## Watch Out

1. **You can't test your way out of object-model coupling.** If the answer to "how do I
   test this" is "open Excel and watch," the code needs extracting first (Pillar 1), not a
   cleverer test. Fix the design, then test the pure part.
2. **A test that needs Rubberduck isn't portable.** It won't run on a machine without the
   add-in or on a Mac. Offer the plain-VBA fallback so the suite survives the environment.
3. **`Debug.Assert` does nothing useful unattended.** It only breaks the IDE on Windows;
   under COM automation it's silent. Use a real assert harness for anything you need to
   report.
4. **Don't claim CI green you didn't see.** "Server-side Office automation is unsupported"
   is the literal Microsoft position — if you wire up a runner, verify it on an interactive
   session and report honestly, including the modal-dialog hang risk.
