---
name: vba-userforms
description: >
  Expert on building VBA UserForms — the dialog/GUI layer of Excel/Word/Outlook/
  PowerPoint macros. Use this skill whenever the user wants to create, lay out,
  style, or wire up a UserForm or its controls: designing a settings/input/wizard
  dialog, adding and arranging TextBox/ComboBox/ListBox/CheckBox/OptionButton/Frame/
  MultiPage/CommandButton controls, handling control events (Click, Change,
  BeforeUpdate, KeyPress), input validation, populating combos/lists from a range,
  showing a form modal vs. modeless, building controls dynamically at runtime, form
  resizing/tab order/accelerator keys, or replacing repeated InputBox/MsgBox prompts
  with a real dialog. Trigger on "create a UserForm", "build a dialog/form in VBA",
  "add a dropdown/listbox to my form", "validate form input", "show a settings
  window", "make a wizard", "populate this combobox", "userform won't close".
  Builds on vba-development (general VBA mechanics, error handling, binding) — defer
  non-UI logic there; this skill owns the form/control/event layer.
---

# VBA UserForms Skill

You build VBA dialogs that are clean to use and clean to maintain: forms whose
code-behind only handles UI, that validate before they commit, and that hand real
work off to standard modules. Lead with the answer and state assumptions up front.

## First — Clarify Before Building

| Unknown | Ask |
|---|---|
| Purpose | "Input/settings dialog, a pick-from-list, or a multi-step wizard?" |
| Modality | "Should the user be blocked until they close it (modal), or work alongside it (modeless)?" |
| Data source | "Where do the choices come from — a hardcoded list, a worksheet range, or a query?" |
| Result handoff | "On OK, what consumes the values — a macro, cells, a config store?" |
| Layout authoring | "Drag-and-drop in the VBA editor, or generated in code?" (see below) |

> **Authoring reality:** a `.frm` is laid out visually in the VBA editor; you can't
> drag controls from here. So **describe the layout precisely** (control names, types,
> positions, the property grid settings) for the user to build, *or* generate the form
> and its controls **entirely in code** (the `Add` approach below). Pick one and say which.

---

## Architecture — Keep the Form Thin

The form module is for **UI only**. Treat it like a VSTO/event module: wire events,
read/write controls, validate, then delegate.

```vba
' frmSettings (code-behind) — UI only
Option Explicit

Private m_confirmed As Boolean       ' result flag the caller reads

Public Property Get Confirmed() As Boolean
    Confirmed = m_confirmed
End Property

Public Property Get Threshold() As Double
    Threshold = CDbl(Me.txtThreshold.Value)   ' typed accessor, not raw control reads by caller
End Property

Private Sub btnOk_Click()
    If Not ValidateInput() Then Exit Sub       ' validate before committing
    m_confirmed = True
    Me.Hide                                     ' Hide, not Unload — so the caller can read values
End Sub

Private Sub btnCancel_Click()
    m_confirmed = False
    Me.Hide
End Sub
```

```vba
' modMain — the caller owns the lifecycle: create → show → read → unload
Public Sub RunWithSettings()
    Dim f As frmSettings
    Set f = New frmSettings                     ' explicit instance, not the default global
    f.Show vbModal                              ' blocks here until Hide
    If f.Confirmed Then modWork.Process f.Threshold
    Unload f                                     ' destroy only after reading results
    Set f = Nothing
End Sub
```

**Rules:**
- `OK`/`Cancel` call `Me.Hide`, **not** `Unload Me` — unloading destroys the controls before the caller can read them. The caller `Unload`s after reading.
- Always create an explicit instance (`New frmSettings`) rather than relying on the implicit default instance — the global is a frequent source of stale-state bugs.
- Expose results as typed `Property Get`s; don't let callers reach into `.Controls`.
- Non-UI logic (calculations, I/O, sheet writes) lives in standard modules, called from the handlers.

---

## Creating a Form (visual vs. code)

### Visual (the normal path) — describe it to build
When specifying a form for the user to draw in the editor, give a control table:

| Name | Type | Caption / role | Key properties |
|---|---|---|---|
| `frmSettings` | UserForm | dialog | `Caption="Settings"`, `StartUpPosition=1` (center owner) |
| `lblThreshold` | Label | "Threshold:" | — |
| `txtThreshold` | TextBox | numeric input | `TabIndex=0` |
| `cboMode` | ComboBox | mode picker | `Style=2` (dropdown list, no free text), `TabIndex=1` |
| `chkVerbose` | CheckBox | "Verbose log" | `TabIndex=2` |
| `btnOk` | CommandButton | "OK" | `Default=True`, `TabIndex=3` |
| `btnCancel` | CommandButton | "Cancel" | `Cancel=True`, `TabIndex=4` |

Always specify **names** (never ship `TextBox1`), **tab order**, and the **Default/Cancel**
buttons — those make Enter/Esc work.

### Code (dynamic / generated forms)
Build controls at runtime when the layout depends on data (e.g. one row per item):

```vba
Private Sub UserForm_Initialize()
    Dim items As Variant: items = ThisWorkbook.Worksheets("Cfg").Range("Items").Value
    Dim top As Single: top = 6
    Dim r As Long
    For r = 1 To UBound(items, 1)
        Dim cb As MSForms.CheckBox
        Set cb = Me.Controls.Add("Forms.CheckBox.1", "chk_" & r, True)
        cb.Caption = CStr(items(r, 1))
        cb.Left = 6: cb.Top = top: cb.Width = 200
        top = top + 18
    Next r
    Me.Height = top + 60
End Sub
```
For event handling on dynamically added controls, use a small class with
`WithEvents As MSForms.CheckBox` and keep the instances in a `Collection`.

---

## Formatting & Layout

- **Center on open:** `StartUpPosition = 1` (CenterOwner). For multi-monitor correctness, set it relative to the host window.
- **Alignment over guesswork:** keep a consistent left margin and a fixed vertical rhythm (e.g. 18px row pitch). Group related controls in a `Frame`; use `MultiPage` for tabbed sections.
- **Sizing:** set `Width`/`Height` to fit content; for resizable forms, reposition controls in `UserForm_Resize` using `Me.InsideWidth`/`InsideHeight` (Anchoring isn't built in).
- **Readability:** consistent `Font`, right-align numeric `TextBox`es (`TextAlign=3`), and use `Label` `.Accelerator` (e.g. `&Threshold`) so Alt+T jumps to the field.
- **State affordances:** disable (`.Enabled = False`) rather than hide controls that are temporarily invalid, so the layout doesn't jump; gray out `btnOk` until input is valid if you prefer prevention over post-hoc validation.

---

## Populating Controls

```vba
' ComboBox/ListBox from a range — set .List once from an array, never .AddItem in a loop
Me.cboMode.List = ThisWorkbook.Worksheets("Cfg").Range("ModeList").Value

' Multi-column list (e.g. id + label), show the label, keep the id as BoundColumn
With Me.lstItems
    .ColumnCount = 2
    .ColumnWidths = "0;120"      ' hide the id column
    .BoundColumn = 1             ' .Value returns the id
    .List = arr2D
End With
```
Prefer `Style = 2` (dropdown list) on a ComboBox when only listed values are allowed —
it removes a whole class of free-text validation.

---

## Events & Validation

Common control events and what they're for:

| Event | Use for |
|---|---|
| `Click` / `Change` | buttons; reacting to a selection or toggle |
| `BeforeUpdate(ByVal Cancel As MSForms.ReturnBoolean)` | per-field validation — set `Cancel = True` to keep focus in the field |
| `KeyPress(ByVal KeyAscii As MSForms.ReturnInteger)` | restrict input (e.g. digits only: set `KeyAscii = 0` to reject) |
| `Enter` / `Exit` | field focus transitions |
| `UserForm_Initialize` | populate controls, set defaults — runs once on creation |
| `UserForm_QueryClose` | intercept the [X] (see below) |

```vba
' Validate on commit, report clearly, return focus to the offender
Private Function ValidateInput() As Boolean
    If Not IsNumeric(Me.txtThreshold.Value) Then
        MsgBox "Threshold must be a number.", vbExclamation, "Invalid input"
        Me.txtThreshold.SetFocus
        Exit Function          ' ValidateInput = False
    End If
    ValidateInput = True
End Function
```

```vba
' Treat the [X] like Cancel — don't leave the caller reading committed state
Private Sub UserForm_QueryClose(Cancel As Integer, CloseMode As Integer)
    If CloseMode = vbFormControlMenu Then
        m_confirmed = False
        ' Optionally: Cancel = True : Me.Hide  to keep the instance alive for the caller
    End If
End Sub
```

---

## Enabling / Showing the Form

- **Modal** (`f.Show vbModal`, the default): blocks code until `Hide`/`Unload`; use for input/settings the macro needs before continuing.
- **Modeless** (`f.Show vbModeless`): user keeps working in Excel; use for palettes/progress. The instance must stay in scope (a module-level variable), or it's destroyed immediately.
- **Trigger it** from a ribbon button, a worksheet shape/button (`Assign Macro`), or a macro — the launcher is just a `Sub` that runs the create→show→read→unload pattern above.
- **Conditional enabling:** enable/disable controls in `Initialize` and in `Change` handlers based on state; for whole-form gating, only `Show` it when preconditions hold and `MsgBox` the reason otherwise.

---

## Watch Out

1. **`Unload Me` in the OK button loses your data.** It destroys the controls before the caller reads them. Use `Me.Hide` in the form; let the caller `Unload` after reading the typed properties.
2. **The default instance bites.** `frmSettings.Show` (using the auto-global) keeps state between shows and breaks if shown re-entrantly. Always `New` an explicit instance.
3. **`.AddItem` in a loop is slow and flickers.** Assign `.List = array` once instead — same lesson as range round-tripping.
4. **A modeless form vanishes if it goes out of scope.** Hold it in a module-level variable, or it unloads the instant the launching `Sub` returns.
5. **The [X] isn't Cancel by default.** Without a `QueryClose` handler, closing via the title bar can leave `Confirmed`/result state ambiguous — handle `vbFormControlMenu` explicitly.
