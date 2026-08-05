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
  the dialect corrections teams doing this have paid for in failed pastes. Boundaries: WHICH control
  to use and what it returns is powerapp-canvas-controls; geometry, spacing and responsive
  layout are powerapp-canvas-design; delegation strategy and SharePoint column policy are
  power-fx-development; auditing before a paste is the pre-paste-review agent; moving the file
  into Studio is studio-transfer. This skill owns *the file and the formulas in it*.
---

# Canvas Development — pa-yaml v3.0 and the Power Fx inside it

Schema: the pa-yaml v3.0 schema vendored from `microsoft/PowerApps-Tooling` (e.g.
`tools/pa.schema.v3.0.yaml`). Run your validator (e.g. `python tools/validate_pa_yaml.py`)
before every hand-off. **The schema alone is
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
  asset_library:
    Type: Table
EditorState:
  ScreensOrder: [scrHome, scrAssets]
```

`Children` is an **array of single-key maps**, ordered by z-index: **first = bottom, last =
top**. There is no `ZIndex` property. Anything that must float — a dropdown's results, a modal,
an app bar — is declared LAST.

## Formula rules that have actually bitten

**`IfError` requires ALL arguments to be type-compatible.** MS Learn prints
`IfError(Patch(…), Notify(…))` and then notes that *currently* every argument's type must
match. `Patch` returns a record, `Notify` a boolean → *"expecting a record"*. Make every arm a
`Set`:

```powerapps
IfError( Set(gTmp, Patch(list, rec, {…})), Set(gErr, FirstError.Message) );
If( Len(gErr) > 0, Notify("Couldn't save: " & gErr, NotificationType.Error) )
```

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

## YAML traps specific to Power Fx

A plain YAML scalar **cannot contain `: `** — and Power Fx is full of it (record literals,
connector parameters). Emit those as block scalars:

```yaml
Items: |
  =Office365Users.SearchUserV2({ searchTerm: txtSearch.Text, top: 8 }).value
```

Same for anything multi-line, anything containing ` #`, and anything ending in `:`.

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

1. Read the golden source — your list-schema file (e.g. `schema/schema.yaml`) — for every column
   token you intend to write; **never invent a column name**.
2. Ground every control token (powerapp-canvas-controls) before typing it.
3. Author into your authored-source directory (e.g. `src/authored/`) for controls, and the
   separate App-object-bodies directory (e.g. `src/patches/`) for formula-bar-only code.
4. Run the validator — schema, tokens, icons, `IfError` typing, gallery `OnSelect`, cross-file
   component contracts.
5. Hand to the **pre-paste-review** agent for a paste/do-not-paste verdict.
6. Cross the gap per studio-transfer, then record the outcome in the paste log.
