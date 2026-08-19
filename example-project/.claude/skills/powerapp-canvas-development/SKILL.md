---
name: powerapp-canvas-development
description: >
  Authoring canvas-app source in pa-yaml v3.0 — the file structure itself and the Power Fx
  that lives inside it. Use this skill when writing or fixing a `.pa.yaml` file: "add a screen",
  "what goes in the App section", "how do I declare a data source", "why won't this YAML
  parse", "where does EditorState go", "write the OnSelect for this", "this formula is
  rejected by Studio", "IfError is complaining", "expecting an identifier name". Covers the
  five root sections (App / Screens / ComponentDefinitions / DataSources / EditorState), the
  control mapping shape, property vs behaviour formulas, YAML-vs-Power-Fx quoting traps, and
  the dialect corrections this project has paid for in failed pastes. Boundaries: WHICH control
  to use and what it returns is powerapp-canvas-controls; geometry, spacing and responsive
  layout are powerapp-canvas-design; delegation strategy and SharePoint column policy are
  power-fx-development; auditing before a paste is the pre-paste-review agent; moving the file
  into Studio is studio-transfer. This skill owns *the file and the formulas in it*.
---

# Canvas Development — pa-yaml v3.0 and the Power Fx inside it

> **Docs source (meaning, not tokens):** the authoritative control/property/layout reference is
> `github.com/MicrosoftDocs/powerapps-docs` (e.g. `controls/reference-properties.md`). See
> `.claude/context/powerapps-docs-source.md` for paths + fetch methods. It grounds SEMANTICS; the
> pa-yaml token/version still comes from a Studio code-view (`tools/studio-enums.json`).

Schema: `tools/pa.schema.v3.0.yaml`, vendored from `microsoft/PowerApps-Tooling`.
Validate with `python tools/validate_pa_yaml.py` before every hand-off. **The schema alone is
not enough** — it declares `Control:` as `true` (anything) and `Variant:` as any string, so a
placeholder validates perfectly and still cannot work. That is why the validator has a second
token pass.

---

## Root structure

```yaml
App:
  Properties:
    StartScreen: =scrHome
Screens:
  scrHome:
    Properties:
      Fill: =Theme.Color.Bg
      OnVisible: |
        =Set(gFoo, 1)
    Children:
      - lblTitle:
          Control: Label@2.5.1
          Properties:
            Text: ="Hello"
ComponentDefinitions:
  cmpThing:
    DefinitionType: CanvasComponent
    CustomProperties: { … }
    Properties: { … }
    Children: [ … ]
DataSources:
  taskmaster_projects:
    Type: Table
EditorState:
  ScreensOrder: [scrHome, scrProjects]
```

`Children` is an **array of single-key maps**, ordered by z-index: **first = bottom, last =
top**. There is no `ZIndex` property. Anything that must float — a dropdown's results, a modal,
an app bar — is declared LAST.

## Formula rules that have actually bitten

**`SetFocus` is unusable almost everywhere in a real app — check the target's ANCESTRY before
writing it.** MS Learn (`function-setfocus#limitations`) excludes four containers outright:

> You cannot set the focus to controls that are within a **Gallery**, **Edit form**, or
> **Component**. […] You cannot set the focus to controls that are within a **Container**.

Plus: the target must be a Button / Icon / Image / Label / TextInput, on the **same screen** as
the formula, not `DisplayMode.Disabled`, and the call must be in a behaviour formula. In this
repo that leaves almost nothing — every screen below its header is auto-layout containers, and
every dialog is a component. **Studio rejected `SetFocus(txtPkSearch)` inside `cmpPicker`'s
`OnReset` on 2026-08-12**; `Reset(txtPkSearch)` on the line above was fine, because `Reset`
carries none of these restrictions. If one of a pair throws and the other doesn't, that
asymmetry is the tell.

The consequence is not fixable in Power Fx: **a modal dialog cannot auto-focus its own search
box**, so the user must click into it. The only documented route is a PCF code component with
an `InputEvent` property driven by `"SetFocus" & Text(Rand())`. Say that plainly rather than
reaching for a formula that cannot exist.

> Beware the plausible wrong diagnosis. The first guess here was a *timing* one — that the
> control was not yet visible when `OnReset` ran. It reads well, it is unfalsifiable across a
> one-way gap, and it is wrong: the restriction is categorical and documented. **When a
> function is rejected, read its Limitations section before theorising about evaluation order.**

**`IfError` requires ALL arguments to be type-compatible.** MS Learn prints
`IfError(Patch(…), Notify(…))` and then notes that *currently* every argument's type must
match. `Patch` returns a record, `Notify` a boolean → *"expecting a record"*. Make every arm a
`Set`:

```powerapps
IfError( Set(gTmp, Patch(list, rec, {…})), Set(gErr, FirstError.Message) );
If( Len(gErr) > 0, Notify("Couldn't save: " & gErr, NotificationType.Error) )
```

**Every call site needs its OWN scrap name.** A global's type unifies across every `Set`, so one
`gTmp` holding a record from one `Patch` and a table from a `Remove` is a type conflict that
reports far from its cause. A cascade that removes three lists needs three scrap names.
`Remove`/`RemoveIf`/`ForAll` return **tables**, not records, so they cannot share a scrap with a
`Patch` either.

`FirstError` is only in scope *inside* the replacement, so stash it and act afterwards. Inside
`ForAll` — where `Set` is unsafe because iteration order is not guaranteed — force the arms to
text instead: `IfError( Text(Patch(…).ID), FirstError.Message, "" )`.

**Column names are IDENTIFIERS, not strings**, since Power Apps 3.24042 (Apr 2024):
`Ungroup(t, v)`, `ShowColumns(x, Label, Path)`, `AddColumns(t, wgt, …)`. Existing apps were
auto-migrated; anything authored from scratch against an older example is wrong.

**`Errors()` returns a TABLE**, so `IsError(Errors(…))` never fires. Use `IsEmpty(Errors(…))`
or the `IfError`-plus-variable pattern above.

**`IsMatch` defaults to `MatchOptions.Complete`** — it already anchors, so adding `^`/`$`
double-anchors and never matches.

**A gallery's `Items` is write-only.** `CountRows(gal.Items)` is invalid. `Self.AllItems` is
readable but *latches*: a hidden gallery's rows are never realised, so a `Visible` computed
from it can never turn back on. Ask the source data instead.

**A gallery's own `OnSelect` does not reliably fire** when the click lands on a child control.
Put the action on a transparent full-template `Classic/Button` declared LAST in the row:

```yaml
- rowHit:
    Control: Classic/Button@2.2.0
    Properties:
      Text: =""
      Fill: =RGBA(0, 0, 0, 0)
      BorderThickness: =0
      X: =0
      Y: =0
      Width: =Parent.TemplateWidth
      Height: =Parent.TemplateHeight
      OnSelect: =Select(Parent); Set(gSel, ThisItem); Navigate(scrDetail)
```

The validator rejects any gallery that still carries its own `OnSelect`.

## Reusing a behaviour block: a hidden control, invoked with `Select()`

Power Fx cannot name a behaviour block. There is no procedure to call, so logic needed in more
than one place gets copied — and copies of a block that WRITES are how a screen ends up with two
writers of the same column that quietly disagree.

**A control's `OnSelect` is the one reusable behaviour unit the language offers**, and `Select()`
invokes it. The control can be hidden: `Select()` fires on a control with `Visible: =false` —
confirmed in Studio 2026-08-18 (`tests/scrProbeRerun`, scoring a visible, a 1×1 transparent and a
hidden button identically against a passing positive control). The common folklore that it
no-ops on an invisible control is false here. Do not smuggle the worker in as a 1×1 transparent
button; hide it.

```yaml
- btnRecompute:
    Control: Classic/Button@2.2.0
    Properties:
      Visible: =false
      Width: =1
      Height: =1
      OnSelect: |
        =Set( gDerivedA, … );
         Set( gDerivedB, … )
```

`OnVisible` calls `Select( btnRecompute )`; so does every handler that invalidates those values.
One copy, several callers.

`Navigate( <the current screen> )` also re-runs `OnVisible` — also confirmed, also undocumented,
MS Learn defines `Navigate` in terms of "the NEW screen". Prefer the worker anyway: no screen
transition, no pushing a screen onto its own history, and `Select( btnRecompute )` says at each
call site what it actually does.

## YAML traps specific to Power Fx

A plain YAML scalar **cannot contain `: `** — and Power Fx is full of it (record literals,
connector parameters). Emit those as block scalars:

```yaml
Items: |
  =Office365Users.SearchUserV2({ searchTerm: txtSearch.Text, top: 8 }).value
```

Same for anything multi-line, anything containing ` #`, and anything ending in `:`.

**And the inverse, which is worse because nothing complains.** Inside a block scalar a `#` is
**content, not a comment** — YAML only treats it as a comment outside one. So a comment that
drifts into a `|` block becomes part of the formula, and **Power Fx has no `#` comment at all**
(it uses `//` and `/* */`), which means Studio rejects the paste. The file still parses, the
schema still validates, and the damage is visible only by reading the value back. This happened
here by appending to a file whose last line was inside a block scalar and which had no trailing
newline, so a comment banner glued onto the end of an `OnSelect`.

Two rules fall out, both now enforced by `tools/validate_pa_yaml.py`:

- **No `#` outside a string literal in an `=`-prefixed value** (`stray_hash_errors`).
- **No comment at column 0 once the document has started** (`stray_comment_indent`) — in a file
  nested 30+ columns deep that is always a multi-line edit that lost its indentation.

Scripted edits are where both arise. Guarantee the trailing newline before appending, and indent
*every* line of a multi-line comment, not just the first.

## Behaviour vs property formulas

Property formulas compute a value and must be side-effect free. Behaviour formulas (`OnSelect`,
`OnVisible`, `OnChange`) chain with `;`. A behaviour formula returns its **last expression** —
which is how a component Action declaring `ReturnType: Boolean` ends up type-mismatched if it
finishes on `Collect`/`Patch` (both return values). End such a formula with `; true`.

## State

- `Set` — global, app-wide. The default here.
- `UpdateContext` — screen-scoped.
- `Collect`/`ClearCollect` — collections, for staging rows before a write.

Prefer **named formulas in `App.Formulas`** over `OnStart` for anything derivable: they always
have a value, have no timing dependency, and cannot be overwritten from elsewhere. Note the
App object has **no code view** — its body is typed into the formula bar (see studio-transfer).

## Workflow: authoring a change

1. Read the golden source (`schema/schema.yaml`) for every column token you intend to write —
   **never invent a column name**.
2. Ground every control token (powerapp-canvas-controls) before typing it.
3. Author into `src/Screens/` (controls) or `src/` (App object bodies).
4. `python tools/validate_pa_yaml.py` — schema, tokens, icons, `IfError` typing, gallery
   `OnSelect`, cross-file component contracts.
5. Hand to the **pre-paste-review** agent for a paste/do-not-paste verdict.
6. Cross the gap per studio-transfer, then record the outcome in `docs/build-history.md`.
