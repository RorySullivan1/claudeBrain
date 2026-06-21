---
name: vba-maintenance
description: >
  Expert VBA maintenance, debugging, and modernization specialist for existing
  Excel/Word/Outlook/PowerPoint macros and add-ins. Use this skill whenever the
  user has VBA that already runs (or used to) and needs to change: debugging a
  runtime error (1004, 91, 13, 438), fixing a macro that broke after an Office
  update or file move, refactoring legacy code toward modern conventions, making a
  slow macro fast, eliminating a "compile error", recovering a corrupted/locked
  VBAProject, migrating across Office versions or 32-vs-64-bit (PtrSafe / Declare),
  or setting up Git-friendly source export. Trigger on "my macro stopped working",
  "it worked before the update", "why is this so slow", "Run-time error 1004",
  "modernize this old macro", "compile error", "fix this VBA". Distinct from new
  development (use vba-development) and from reviewing code you won't change (vba-review).
---

# VBA Maintenance Skill

You debug, refactor, and modernize VBA that already exists. Make **targeted** edits,
not opportunistic rewrites — fix the reported issue everywhere it occurs and leave
working code alone unless you flag a change and explain why.

## Triage First — Get the Facts

Before diagnosing, collect:

| Information | How to get it |
|---|---|
| **Exact error** | Number + message + the highlighted line (`Run-time error '1004'`, `'91'`, `'13'`, `'438'`) |
| **When it broke** | After an Office update? A file move/rename? A new machine? A reference change? |
| **Host + version + bitness** | File → Account → About (shows 32-bit / 64-bit) |
| **Deliverable** | `.xlsm` workbook, `.xlam` add-in, or exported `.bas`/`.cls` source |
| **References** | Tools → References — any marked **MISSING**? |
| **Reproducibility** | Every run, or intermittent? On every machine, or one? |

---

## Common Runtime Errors — Decode Table

| Error | Usual meaning | First thing to check |
|---|---|---|
| `1004` "Application-defined or object-defined" | Bad range/sheet reference, or write to a protected/missing object | Is the sheet name right and qualified? Is the sheet protected? Is `ActiveWorkbook` not what you assumed? |
| `91` "Object variable not set" | Used an object before `Set`, or a `Find`/`ActiveX` returned `Nothing` | Guard the result of `.Find`, `ActiveExplorer`, `ActiveInspector` for `Nothing` before use |
| `13` "Type mismatch" | Reading a cell error/empty into a typed var; passing a single cell where a 2D array was assumed | Handle the single-cell scalar vs. 2D-array case; check for `IsError(cell.Value)` |
| `438` "Object doesn't support this property/method" | Wrong object type, or a late-bound member that doesn't exist in this version | Confirm the member in the Object Browser; check the actual runtime type |
| `9` "Subscript out of range" | Sheet/name/array index that doesn't exist | Hardcoded `Worksheets("X")` or `Worksheets(1)` after a rename/reorder |
| Compile: "Can't find project or library" | A referenced library is **MISSING** | Tools → References; reattach or convert that dependency to late binding |

---

## Diagnostic Flow — "It Worked Before"

1. **Tools → References — look for MISSING.** A moved/upgraded machine is the #1 cause. The durable fix is to convert the dependency to **late binding** (`CreateObject`) so no reference is needed at all — see the refactor below.
2. **Did the file move?** Unqualified `Sheets(...)`, `ActiveWorkbook`, or a hardcoded path now resolves differently. Re-qualify to `ThisWorkbook` and resolve paths relative to `ThisWorkbook.Path`.
3. **Office update?** A behavior you relied on (event order, `Application.FileDialog`, an Outlook security prompt) may have shifted. Reproduce on the prior channel if available; pin critical users to Semi-Annual.
4. **32-vs-64-bit?** Any `Declare` to a Win32 DLL needs `PtrSafe` and `LongPtr` on 64-bit Office — see migration below.
5. **Macro/Trusted-Location issue?** If the macro doesn't even run, the file may be in Protected View or its location de-trusted. That's a distribution/trust problem — hand off to `vba-distribution`.

### MISSING reference → late binding (the durable fix)

```vba
' BEFORE: early-bound, breaks if Microsoft Scripting Runtime is MISSING on the target
Dim dict As Scripting.Dictionary
Set dict = New Scripting.Dictionary

' AFTER: late-bound, no reference required anywhere
Dim dict As Object
Set dict = CreateObject("Scripting.Dictionary")
```
Convert **consistently** — fields, parameters, return types, and call sites. A half-converted
class (field `As Object` but parameter `As Scripting.Dictionary`) still carries the dependency.

### 32 ↔ 64-bit API declarations

```vba
' BEFORE: 32-bit only — compile error on 64-bit Office
Declare Function GetTickCount Lib "kernel32" () As Long

' AFTER: compiles on both; LongPtr for pointer/handle args
#If VBA7 Then
    Declare PtrSafe Function GetTickCount Lib "kernel32" () As Long
#Else
    Declare Function GetTickCount Lib "kernel32" () As Long
#End If
```

---

## Refactoring Legacy Code (toward the standards)

Apply these only where they fix the reported issue or where you flag them explicitly:

- **Add `Option Explicit`** to a module that lacks it, then resolve the variables it now flags — undeclared names are usually the latent bug.
- **Macro-recorder cleanup:** collapse `.Select` → `Selection.X` into direct object access; qualify bare `Sheets(...)` to `ThisWorkbook`.
- **Cell-by-cell → array round-trip** for any loop over a range (read `rng.Value` once, process the `Variant` array, write once).
- **Restore application state in a `Cleanup:` label** so an error doesn't leave `Calculation = Manual` or `EnableEvents = False`.
- **Centralise error handling** into a `modError.Wrap` so messages name their origin and you can trace failures.

Refactor in small, reviewable steps — change one module, confirm it still runs, then the next.
Don't restructure surrounding code under the guise of fixing one bug.

---

## Performance Fixing

When a macro is slow, in order:

1. **Wrap the work** — `Application.ScreenUpdating/Calculation/EnableEvents` off, restored after (saved values).
2. **Kill cell-by-cell loops** — array round-trip is usually 10–100×.
3. **Hoist invariant lookups** out of loops; replace in-loop `WorksheetFunction.VLookup` with one `Application.Match` over an array.
4. **Drop needless `Application.Volatile`** in UDFs — it forces recalc on every workbook change.
5. **Release external objects** (`Set obj = Nothing`) that hold resources, and `Close` file handles on every path.

Measure before and after with `Timer`; don't guess which step mattered.

---

## Version Control & Round-Trip Build

VBA lives inside a binary container, which fights Git. To make it diffable:

- **Export source as text:** standard modules `.bas`, classes `.cls`, forms `.frm` **plus** the binary `.frx` (commit the `.frx`).
- Prefer a **round-tripped build** — text source in Git, a build step that rebuilds the `.xlsm`/`.xlam` from those files — over committing the binary workbook. Treat the binary as an artifact, not source.
- For recovery of a locked/corrupted `VBAProject`, export every module you can reach to text first; that text is your backup before any repair attempt.

(Packaging the rebuilt `.xlam` and getting it onto machines is `vba-distribution`'s job.)

---

## Watch Out

1. **A MISSING reference breaks code that never changed.** The macro you're debugging may be fine — the target machine simply lacks a library the dev machine had. Check Tools → References before reading a single line, and prefer late binding so it can't recur.
2. **`On Error Resume Next` hides the real failure point.** When debugging, temporarily remove blanket error handling so the error surfaces on its actual line — then restore scoped handling once you've found it.
3. **An Office update can change behavior without changing your code.** "It worked last week" with no edits points at the environment: channel update, reference, bitness, or trust — not the VBA logic.
4. **Fix the bug, not the whole file.** The user reported one symptom; resist rewriting working procedures around it unless you call out the change and why.
