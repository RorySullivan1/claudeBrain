---
name: VSTO-development
description: >
  Expert VSTO (Visual Studio Tools for Office) development assistant for writing,
  architecting, and debugging Office add-ins in C# or VB.NET. Use this skill whenever
  the user asks to write, scaffold, or fix VSTO code — including Ribbon XML/Designer,
  Custom Task Panes, Office object model interactions, COM interop patterns, event
  handlers, or ThisAddIn entry point logic. Also trigger for questions about project
  structure, add-in architecture, Excel/Word/Outlook/PowerPoint object models, or any
  task that involves producing working VSTO code. If the user says "how do I..." or
  "write me..." in the context of Office add-ins, use this skill.
---

# VSTO Development Skill

## First — Clarify Before Coding

Never assume. Ask **one** targeted question if any of these are unknown:

| Unknown | Ask |
|---|---|
| Office application | "Which Office app — Excel, Word, Outlook, or PowerPoint?" |
| Add-in scope | "Is this application-level or document-level?" |
| UI surface | "Ribbon button, Task Pane, or context menu?" |
| Language | Default to C#; ask only if user signals VB.NET |
| Office version | "Which Office version is the minimum target?" |

State all assumptions explicitly in a comment at the top of every code block:
```csharp
// Targets: Excel 2016+, .NET Framework 4.7.2, VSTO 4, application-level add-in
```

---

## Code Standards

### Required in Every Code Example
- All relevant `using` statements included at the top
- `try/finally` blocks around every COM object that must be released
- `Marshal.ReleaseComObject` called explicitly — never rely on GC
- Null checks before dereferencing Office objects
- XML doc comments (`/// <summary>`) on all public methods in teaching examples
- PascalCase for public members, camelCase for locals, `_` prefix for private fields

### COM Release Pattern — Always Use This

```csharp
// CORRECT: Explicit release in finally block
Excel.Range range = null;
try
{
    range = worksheet.Cells[1, 1] as Excel.Range;
    range.Value2 = "Hello";
}
finally
{
    if (range != null)
    {
        Marshal.ReleaseComObject(range);
        range = null;
    }
}
```

### The Two-Dot Rule — Call Out Every Violation

Never chain COM property accesses. Each `.` is a hidden COM object that won't be released:

```csharp
// WRONG — creates an unreleased intermediate Worksheets COM object
var name = _application.Workbooks[1].Worksheets[1].Name;

// CORRECT — capture every intermediate object
Excel.Workbooks workbooks = null;
Excel.Workbook workbook = null;
Excel.Worksheets sheets = null;
Excel.Worksheet sheet = null;
try
{
    workbooks = _application.Workbooks;
    workbook  = workbooks[1];
    sheets    = workbook.Worksheets;
    sheet     = sheets[1] as Excel.Worksheet;
    var name  = sheet.Name;
}
finally
{
    if (sheet     != null) Marshal.ReleaseComObject(sheet);
    if (sheets    != null) Marshal.ReleaseComObject(sheets);
    if (workbook  != null) Marshal.ReleaseComObject(workbook);
    if (workbooks != null) Marshal.ReleaseComObject(workbooks);
}
```

---

## Project Structure

Recommend this layout for all new VSTO projects:

```
MyAddIn/
├── MyAddIn/                    # Main VSTO project
│   ├── ThisAddIn.cs            # Entry point — keep thin
│   ├── Ribbon/
│   │   ├── MainRibbon.xml      # Ribbon XML (preferred over designer)
│   │   └── RibbonCallbacks.cs  # One callback file per ribbon
│   ├── TaskPanes/
│   │   └── MainTaskPane.cs     # UserControl subclass
│   ├── Services/               # Business logic — no Office references here
│   ├── Models/                 # Plain data classes
│   ├── Helpers/
│   │   └── ComHelper.cs        # Shared COM release utilities
│   └── Resources/
├── MyAddIn.Tests/              # Unit tests — mock Office interop
├── MyAddIn.Setup/              # WiX or ClickOnce setup project
└── docs/
    ├── deployment.md
    └── changelog.md
```

**Key rules:**
- `ThisAddIn.cs` wires events and initializes services only — no business logic
- `Services/` must not reference `Microsoft.Office.Interop.*` — keeps logic testable
- One `ComHelper.cs` with a static `SafeRelease<T>()` utility method used everywhere

---

## Key Code Recipes

### ThisAddIn Entry Point

```csharp
public partial class ThisAddIn
{
    private MyService _service;

    private void ThisAddIn_Startup(object sender, EventArgs e)
    {
        _service = new MyService();
        // Subscribe to application events here
        this.Application.WorkbookOpen += Application_WorkbookOpen;
    }

    private void ThisAddIn_Shutdown(object sender, EventArgs e)
    {
        // Always unsubscribe events on shutdown
        this.Application.WorkbookOpen -= Application_WorkbookOpen;
        _service?.Dispose();
    }

    private void Application_WorkbookOpen(Excel.Workbook wb)
    {
        // Handle event — do not store wb without releasing later
    }
}
```

### Ribbon XML (preferred over Ribbon Designer)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<customUI xmlns="http://schemas.microsoft.com/office/2009/07/customui"
          onLoad="Ribbon_Load">
  <ribbon>
    <tabs>
      <tab id="tabMyAddIn" label="My Add-In">
        <group id="grpActions" label="Actions">
          <button id="btnRun"
                  label="Run"
                  imageMso="RunMacro"
                  size="large"
                  onAction="OnRunClicked" />
        </group>
      </tab>
    </tabs>
  </ribbon>
</customUI>
```

```csharp
// RibbonCallbacks.cs
public partial class ThisAddIn
{
    private Office.IRibbonUI _ribbon;

    public void Ribbon_Load(Office.IRibbonUI ribbonUI)
    {
        _ribbon = ribbonUI; // Cache for InvalidateControl calls
    }

    public void OnRunClicked(Office.IRibbonControl control)
    {
        // Called on the UI thread — safe to access Office objects here
        _service.Execute(this.Application.ActiveWorkbook);
    }
}
```

### Custom Task Pane Registration

```csharp
private CustomTaskPane _taskPane;

private void RegisterTaskPane()
{
    var control = new MainTaskPaneControl(); // Your UserControl
    _taskPane = this.CustomTaskPanes.Add(control, "My Panel");
    _taskPane.Width = 300;
    _taskPane.Visible = true;
    _taskPane.VisibleChanged += TaskPane_VisibleChanged;
}

private void TaskPane_VisibleChanged(object sender, EventArgs e)
{
    // Sync ribbon toggle button state if needed
    _ribbon?.InvalidateControl("btnTogglePane");
}
```

### ComHelper Utility

```csharp
public static class ComHelper
{
    /// <summary>
    /// Safely releases a COM object, suppressing null and non-COM-object errors.
    /// Always call this in finally blocks rather than Marshal.ReleaseComObject directly.
    /// </summary>
    public static void SafeRelease<T>(ref T comObject) where T : class
    {
        if (comObject == null) return;
        try
        {
            if (Marshal.IsComObject(comObject))
                Marshal.ReleaseComObject(comObject);
        }
        catch (Exception ex)
        {
            Debug.WriteLine($"SafeRelease failed for {typeof(T).Name}: {ex.Message}");
        }
        finally
        {
            comObject = null;
        }
    }
}
```

---

## Office Application-Specific Guidance

### Excel
- Use `Range.Value2` not `Range.Value` — avoids Currency/Date type coercion issues
- `Application.ScreenUpdating = false` around bulk operations; always restore in `finally`
- `Application.EnableEvents = false` when writing data that would trigger user event handlers
- Prefer `worksheet.Cells[row, col]` over `worksheet.Range["A1"]` for dynamic addressing

### Word
- Use `ContentControl` over `Bookmark` for structured data binding — bookmarks break on edit
- `Document.Saved` must be set to `true` after programmatic changes if you don't want a save prompt
- Always check `Document.ProtectionType` before writing to protected sections

### Outlook
- Never store `MailItem` beyond the current event scope — Outlook recycles items
- Use `Inspector.CurrentItem` over caching item references across events
- Always check `Application.ActiveExplorer()` for null before accessing `CurrentFolder`

### PowerPoint
- `Presentation.Slides` is 1-indexed, not 0-indexed (like all Office collections)
- Release `Shape` and `Slide` objects explicitly — large decks exhaust memory fast

---

## Threading Rules

Office is **Single-Threaded Apartment (STA)**. Enforce these rules without exception:

- All Office object model calls must happen on the UI thread
- Use `Control.Invoke()` or `SynchronizationContext` to marshal back from background threads
- Never pass Office COM objects to background threads, even as method arguments
- Background work (file I/O, HTTP, computation) is fine off-thread — Office calls are not

```csharp
// Correct: marshal Office call back to UI thread
Task.Run(() =>
{
    var result = _service.ComputeExpensiveThing();
    // Back to UI thread for Office interaction
    _syncContext.Post(_ =>
    {
        _worksheet.Cells[1, 1].Value2 = result;
    }, null);
});
```

---

## Watch Out

1. **GC.Collect() is not a fix.** If you're calling `GC.Collect(); GC.WaitForPendingFinalizers()` to make Excel close, you have unreleased COM objects. Fix the release pattern instead — GC is a workaround, not a solution.
2. **Office 32-bit vs. 64-bit.** Your compiled add-in bitness must match the installed Office bitness. Target `AnyCPU` with `Prefer 32-bit` unchecked, or explicitly target the right platform. Mismatch = silent load failure.
3. **Event handler leaks.** Always unsubscribe every event you subscribe to in `Startup`, inside `Shutdown`. A leaked event handler keeps object graphs alive indefinitely and causes Excel to fail to close.
