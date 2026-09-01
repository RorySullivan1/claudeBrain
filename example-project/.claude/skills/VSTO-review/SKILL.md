---
name: VSTO-review
description: >
  Expert VSTO code reviewer for Office add-ins written in C# or VB.NET. Use this
  skill whenever the user pastes VSTO code and asks for a review, audit, feedback,
  or help improving it. Also trigger when the user reports a bug, memory leak, crash,
  performance problem, or unexpected Office behavior and shares code as context —
  even if they don't explicitly say "review". Trigger on phrases like "what's wrong
  with this", "can you check this", "is this correct", "why does this crash", "review
  my add-in", or any paste of VSTO/Office interop code followed by a question.
  Prioritize correctness over style. Always check COM release, event hygiene, and
  thread safety before anything else.
---

# VSTO Code Review Skill

## Review Priority Order

Always evaluate in this sequence. Stop and flag critical issues before moving to style:

1. **COM object lifecycle** — leaks, missing releases, two-dot violations
2. **Event handler hygiene** — subscriptions without matching unsubscriptions
3. **Thread safety** — Office calls off the UI thread
4. **Exception handling** — bare catches, swallowed errors, missing finally blocks
5. **Office API correctness** — wrong properties, version-specific pitfalls, deprecated members
6. **Architecture** — business logic in Office entry points, testability, separation of concerns
7. **Code style** — naming, readability, redundancy

Never skip to style feedback when a correctness issue exists.

---

## What to Ask For (if not provided)

Before reviewing, request the following if absent:

- **Office application and version** (Excel 2019? Outlook 365?)
- **.NET target framework** (4.7.2? 4.8?)
- **Add-in type** (application-level or document-level?)
- **Error message verbatim**, if reviewing a bug report
- **Stack trace**, if reviewing a crash

---

## Review Checklist

### 1. COM Object Lifecycle

Check every Office object reference for these issues:

**Threading — the documented failure is a REJECTED call, not a crash**
Background-thread object-model calls are *automatically marshaled* across the STA boundary;
they are not a hard "STA violation". What actually happens is that a busy Office app rejects
the call and COM interop surfaces it as a `COMException` ("The message filter indicated that
the application is busy" / `RPC_E_SERVERCALL_RETRYLATER`), and the thread blocks while the STA
is busy. So the review rule is: **every background-thread OM call needs `COMException`
handling with retry, or must be marshaled back to the UI thread** — flag the missing handling,
not the thread itself. *(Verified 2026-08-15.)*

**Unreleased intermediates (two-dot rule)**
```csharp
// BUG: intermediate Worksheets object never released
var name = workbook.Worksheets[1].Name;

// FIX: capture and release every intermediate
Excel.Worksheets sheets = null;
Excel.Worksheet sheet = null;
try
{
    sheets = workbook.Worksheets;
    sheet  = sheets[1] as Excel.Worksheet;
    var name = sheet.Name;
}
finally
{
    if (sheet  != null) Marshal.ReleaseComObject(sheet);
    if (sheets != null) Marshal.ReleaseComObject(sheets);
}
```

**Missing try/finally around COM operations**
```csharp
// BUG: exception between Activate and ReleaseComObject leaks the object
sheet.Activate();
DoSomethingRisky(); // throws
Marshal.ReleaseComObject(sheet); // never reached

// FIX: always use try/finally
try   { sheet.Activate(); DoSomethingRisky(); }
finally { Marshal.ReleaseComObject(sheet); }
```

**Explicit COM release — `ReleaseComObject` vs `FinalReleaseComObject`**
Neither is categorically "safe", and the docs' warning points the *opposite* way from the
folklore (verified 2026-08-15). Microsoft says to use `ReleaseComObject` "only if it is
absolutely required" because improper use "may cause your application to fail, or may cause
an access violation" — and that if you want a component released at a determined time, you
should "consider using the `FinalReleaseComObject` method instead."

So don't flag `FinalReleaseComObject` on sight. The reviewable defect is releasing an RCW
that **something else may still hold** — a singleton like `Application`, or an object the
caller passed in (an `ItemAdd` handler releasing the item it was handed is this bug). Flag
that; treat the choice between the two calls as secondary.

*(Tier note, checked 2026-08-15: the two-dot rule, the `foreach`-enumerator leak, and the
Outlook item-recycling rule below are long-standing VSTO practice and consistent with how RCWs
are documented to work, but Microsoft Learn does not state any of them outright. Keep applying
them — they are the safe direction — but treat them as **experience-settled**, and don't cite
a doc page for them in a review comment.)*

**`foreach` over Office collections**
```csharp
// BUG: foreach creates an enumerator COM object that is never released
foreach (Excel.Worksheet sheet in workbook.Worksheets) { ... }

// FIX: use indexed for loop, release each item
Excel.Worksheets sheets = null;
try
{
    sheets = workbook.Worksheets;
    for (int i = 1; i <= sheets.Count; i++)
    {
        Excel.Worksheet sheet = null;
        try
        {
            sheet = sheets[i] as Excel.Worksheet;
            // work with sheet
        }
        finally { if (sheet != null) Marshal.ReleaseComObject(sheet); }
    }
}
finally { if (sheets != null) Marshal.ReleaseComObject(sheets); }
```

---

### 2. Event Handler Hygiene

**Subscription without unsubscription**
```csharp
// BUG: event never unsubscribed — object graph stays alive, Excel won't close cleanly
private void ThisAddIn_Startup(object sender, EventArgs e)
{
    Application.WorkbookOpen += Application_WorkbookOpen;
}
// No corresponding -= anywhere

// FIX: mirror in Shutdown — but see the Outlook caveat below
private void ThisAddIn_Shutdown(object sender, EventArgs e)
{
    Application.WorkbookOpen -= Application_WorkbookOpen;
    // NB (Outlook): ThisAddIn_Shutdown is NOT raised when Outlook exits — only when the
    // user disables the add-in. Outlook cleanup belongs on Application.Quit / Explorer.Close.
}
```

**Storing Outlook items beyond event scope**
```csharp
// BUG: Outlook recycles MailItem references after the event returns
private MailItem _lastMail; // dangerous field

private void Items_ItemAdd(object item)
{
    _lastMail = item as MailItem; // item may be garbage collected/recycled
}

// FIX: extract needed data synchronously, don't store the item
private void Items_ItemAdd(object item)
{
    if (item is MailItem mail)
    {
        var subject = mail.Subject; // copy value types out
        ProcessSubject(subject);
        Marshal.ReleaseComObject(mail);
    }
}
```

---

### 3. Thread Safety

Flag any Office object model call that occurs off the UI thread:

```csharp
// BUG: unguarded Office call on a background thread (see note below)
Task.Run(() =>
{
    _worksheet.Cells[1, 1].Value2 = "result"; // marshaled across the STA — can be REJECTED
});

// FIX: marshal back to UI thread
Task.Run(() =>
{
    var result = ComputeResult();
    _syncContext.Post(_ =>
    {
        Excel.Range cell = null;
        try
        {
            cell = _worksheet.Cells[1, 1] as Excel.Range;
            cell.Value2 = result;
        }
        finally { if (cell != null) Marshal.ReleaseComObject(cell); }
    }, null);
});
```

---

### 4. Exception Handling

**Bare catch blocks that swallow errors**
```csharp
// BUG: swallows all exceptions including COM errors silently
try { DoOfficeWork(); }
catch { } // never acceptable

// FIX: catch specific exceptions, log, and re-throw or handle deliberately
try { DoOfficeWork(); }
catch (COMException ex)
{
    Logger.Error($"COM error {ex.ErrorCode}: {ex.Message}");
    throw; // or handle specifically
}
```

**Missing finally in COM-intensive methods**
Every method that acquires COM objects must have a `finally` block, even if a `using` pattern is not available. Flag methods longer than ~15 lines that contain COM objects and no `finally`.

---

### 5. Office API Correctness

**`Range.Value` vs `Range.Value2`**
`Range.Value` returns `Currency` and `DateTime` as their COM variants. `Range.Value2` is
typed `object` too — the *only* difference is that it never uses the Currency or Date types,
so a date-formatted cell comes back as an OADate `double`. It still returns `string` for
text, `bool` for booleans, and an error value for error cells, so keep type-checking the
result. Use `Value2` unless you specifically need Currency/Date coercion.

**`Items.ItemAdd` does not fire for bulk additions**
Documented behaviour: the event "does not run when a large number of items are added to the
folder at once." An add-in that relies on `ItemAdd` alone to see every new item will silently
miss batches (a move of many messages, a sync). Flag designs that assume completeness; a
periodic reconcile is the fix.

**`Application.ActiveWorkbook` / `ActiveSheet` without null checks**
These return `null` when no workbook is open. Always guard:
```csharp
var wb = Application.ActiveWorkbook;
if (wb == null) return;
```

**Outlook `Application.ActiveInspector()` without null check**
Returns `null` when no item is open in a compose window. Always check before using.

**`Workbook.Saved` property usage**
Setting `workbook.Saved = true` marks a workbook as saved without actually saving it. This is intentional for programmatic changes you don't want to prompt on. Flag if it looks accidental.

**Version-specific API calls**
If the code uses APIs introduced in a specific Office version (e.g., `Excel 2016`-specific APIs), note the minimum required version.

---

### 6. Architecture

Flag these structural problems with a recommendation, not a blocking issue:

| Problem | Recommendation |
|---|---|
| Business logic in `ThisAddIn.cs` | Move to `Services/` layer with no Office references |
| Direct Office object model calls in service classes | Inject an abstraction/interface for testability |
| Ribbon callbacks doing non-trivial work inline | Delegate to a service; keep callbacks as thin dispatchers |
| No `IDisposable` on classes that hold COM references | Implement `Dispose()` with COM release in it |
| Magic strings for range addresses | Use named constants or named ranges |

---

### 7. Code Style (lowest priority)

Only raise style issues after all correctness issues are addressed:

- Naming: PascalCase for public members, camelCase for locals, `_` prefix for private fields
- Remove dead/commented-out code
- `var` is fine for obvious types; avoid for COM interop types (prefer explicit for clarity)
- XML doc comments on public methods — and at the scope's budget: the ceiling table is
  `coding-standards` § *How much, by scope*; flag history-recounting docs and essay comment
  blocks, and route the displaced reasoning rather than deleting it

---

## Review Output Format

Structure every review as:

### Critical (fix before shipping)
Issues that will cause crashes, memory leaks, data corruption, or silent failures.

### Important (fix soon)
Issues that degrade reliability, prevent testability, or violate Office interop contracts.

### Minor (nice to fix)
Style, naming, and structural improvements with no correctness impact.

### Summary
One paragraph summarizing the overall quality and the single most important thing to address.

---

## Watch Out

1. **"It works in testing" ≠ correct COM release.** The GC may clean up leaks in short test sessions. The same code will cause Excel to hang or refuse to close after hours of use in production.
2. **VB.NET `For Each` on Office collections has the same leak problem as C# `foreach`.** Don't let the syntax fool you.
3. **Event handler memory leaks are cumulative.** A single leaked `WorkbookOpen` handler keeps the entire add-in object graph in memory for the lifetime of the Excel process.
