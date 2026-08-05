---
name: powerapp-canvas-controls
description: >
  The grounded control catalogue for canvas-app YAML — which `Control:` tokens, `Variant:`
  values, enum members and OUTPUT properties actually exist, and which are guesses. Use this
  skill whenever a control is being chosen, added, or swapped: "which control should I use",
  "what's the token for a dropdown / date picker / container", "is Icon.Table real", "what
  does a combobox return", "convert this to a modern control", "why did the paste fail on
  this control", "add a text input / gallery / tab list". Also use before writing ANY new
  control into your authored-source directory (e.g. `src/authored/`) — an ungrounded token fails
  the whole paste and comes back only as "it didn't work". Covers: classic vs modern control
  families, version suffixes, gallery
  `BrowseLayout_*` variants, the 180-value classic `Icon` enum, `GroupContainer` auto-layout,
  the `Classic/` prefix rule, the five single-select controls and how each is seeded, forms and
  data cards, toggles, ratings, sliders, radio groups and the rich text editor, and the output
  property of every control in use (`.Text`, `.Value`, `.Selected.Value`, `.SelectedDate`,
  `.HtmlText`). Boundaries: the FORMULAS inside a control's properties are
  powerapp-canvas-development and power-fx-development; screen layout and geometry are
  powerapp-canvas-design; getting the YAML into Studio is studio-transfer; reusable component
  contracts are power-apps-components. This skill owns *what a control is called and what it
  gives back*.
---

# Canvas Controls — the grounded catalogue

**The single rule: never author a control token you cannot point at evidence for.**

An unknown `Control:` or `Variant:` fails the *entire* paste. Across a one-way gap that returns
as "it didn't work" with no detail, and you then revise blind. Every token below is either
grounded (read off a real Studio artefact) or explicitly marked as a guess.

Keep a machine-readable copy of the grounded tokens next to a validator that enforces them
(e.g. `tools/studio-enums.json` + `tools/validate_pa_yaml.py`).

---

## The generic docs will get you rejected

Microsoft's YAML guidance lists control types as `Label`, `Button`, `TextInput`, `Container`,
`Dropdown`. **Studio's code view does not emit those names.** It emits versioned, sometimes
prefixed tokens:

| Generic doc says | Studio actually writes |
|---|---|
| `Button` | `Classic/Button@2.2.0` or `ModernButton@1.0.0` |
| `TextInput` | `Classic/TextInput@2.3.2` or `ModernTextInput@1.0.0` |
| `Container` | `GroupContainer@1.5.0` + `Variant: AutoLayout` |
| `Dropdown` / `Combobox` | `ModernCombobox@1.0.0` |
| `DatePicker` | `ModernDatePicker@1.0.0` |
| `Timer` | `Timer` — no prefix, no version |

Treat the generic docs as a guide to *structure*, never to *tokens*.

## Grounded tokens

**Classic family** — `Label@2.5.1`, `Rectangle@2.3.0`, `Classic/Icon@2.5.0`,
`Classic/TextInput@2.3.2`, `Classic/Button@2.2.0`, `Gallery@2.15.0`, `Image@2.2.3`,
`HtmlViewer@2.1.0`, `Timer`, `CanvasComponent`.

`Classic/ComboBox@2.4.0`, `Classic/DropDown@2.3.1`, `ListBox@2.2.0`, `Form@2.4.4`
(`Variant: Classic`), `TypedDataCard@1.0.7` (`Variant: ClassicTextualEdit`),
`Classic/Toggle@2.1.0`, `RichTextEditor@2.7.0`, `Rating@2.1.0`, `Classic/Slider@2.1.0`,
`Classic/Radio@2.3.0`.

### The `Classic/` prefix has a rule — but it only predicts

Across every token grounded so far the prefix appears on **exactly those names a modern Fluent
control also uses**, and is absent where no modern namesake exists:

| Prefixed (a modern namesake exists) | Bare (none exists) |
|---|---|
| `Classic/Icon`, `Classic/TextInput`, `Classic/Button`, `Classic/ComboBox`, `Classic/DropDown`, `Classic/Toggle`, `Classic/Slider`, `Classic/Radio` | `Timer`, `ListBox`, `RichTextEditor`, `Rating`, `Gallery`, `Image`, `HtmlViewer`, `Label`, `Rectangle`, `Form`, `TypedDataCard`, `GroupContainer` |

Use it to *guess which form to ask for* — never to author an ungrounded token. A wrong guess
still fails the whole paste. **Casing stays per-token**: `DropDown` has a capital D mid-word,
`ComboBox` a capital B, `RichTextEditor` neither.

**Modern family** — `ModernTextInput@1.0.0`, `ModernNumberInput@1.0.0`, `ModernCombobox@1.0.0`,
`ModernDatePicker@1.0.0`, `ModernTabList@1.0.0`, `ModernButton@1.0.0`,
`GroupContainer@1.5.0` (`Variant: AutoLayout`).

**`Classic/ComboBox@2.4.0` and `ModernCombobox@1.0.0` are different controls.** Studio generates
the classic one inside data cards; the modern one is what you insert by hand today. The classic
adds `Chevron*` styling properties and takes `DefaultSelectedItems` to seed the selection —
which is how a card wires it up:

```yaml
Items: =Choices([@asset_library].'asset_owner')
DefaultSelectedItems: =Parent.Default
SelectMultiple: =false
DisplayMode: =Parent.DisplayMode
PaddingLeft: =If(Self.DisplayMode = DisplayMode.Edit, 5, 0)
```

Version suffixes are optional — Studio uses the current version if omitted — so a version
mismatch is not a failure mode. **Only the control name and the `Variant` matter.**

## Output properties — get these wrong and every formula breaks

| Control | Read it as | Note |
|---|---|---|
| `ModernTextInput` | `.Text` | **Unchanged from classic** — converting inputs is a property rename only |
| `ModernNumberInput` | `.Value` | a real number; `TriggerOutput` was removed from this control |
| `ModernCombobox` | `.Selected.Value` | with `SelectMultiple: =false`, `Selected` is a record |
| `ModernDatePicker` | `.SelectedDate` | `Blank()` when unset |
| `ModernTabList` | `.Selected.Value` | the tab label |
| `Gallery` | `.AllItems`, `.Selected` | **`.Items` is WRITE-ONLY** — reading it is an error |
| `Classic/Toggle` | `.Value` | a boolean; seeded by `Default` |
| `Rating` | `.Value` | a number, `0` when unrated; seeded by `Default` |
| `RichTextEditor` | `.HtmlText` | **in and out are different names** — `Default` in, `.HtmlText` out |
| `Classic/Slider` | `.Value` | a number; seeded by `Default`, bounded by `Min`/`Max` |
| `ModernSlider` | `.Value` | **read-only** — the input is `Default`, not `Value` (it was `Value` before the revision) |
| `Classic/Radio` | `.Selected.Value` | `SelectedText` is deprecated; display column via `Items.Value` |

`RichTextEditor` is the one control whose in and out properties don't match, and its output is
**markup, not text**. So the SharePoint column receiving it must be *Multiple lines of text →
Enhanced rich text*, or the tags get stored literally; and it reads back into an
`HtmlViewer@2.1.0`, never a `Label`.

## Gallery variants

Not `Vertical` / `Horizontal`. The real shape is `BrowseLayout_<Orientation>_<Template>_ver5.0`:

- `BrowseLayout_Vertical_TwoTextOneImageVariant_ver5.0` — confirmed from Studio
- `BrowseLayout_Horizontal_TwoTextOneImageVariant_ver5.0`
- `BrowseLayout_Vertical_OneTextVariant_ver5.0`
- `BrowseLayout_Flexible_SocialFeed_ver5.0`

The template part only picks the default child layout, which pasted children replace — so any
vertical variant works. An unrecognised variant renders the gallery as a black block.

## Icons

The classic `Icon` enum has exactly **180 values**, recovered from `References/Templates.json`
inside a real `.msapp`. `Icon.Back`, `Icon.Documents` and `Icon.Table` **do not exist** —
they are `Icon.BackArrow`, `Icon.Document`, `Icon.DetailList`. The validator checks every
`Icon.*` against the list and suggests the nearest real name.

`ModernButton`'s `Icon` is different: a **string** Fluent name (`Icon: ="Checkmark"`), not the
classic enum.

## Auto-layout container

```yaml
- frmScroll:
    Control: GroupContainer@1.5.0
    Variant: AutoLayout
    Properties:
      LayoutDirection:  =LayoutDirection.Vertical      # or .Horizontal
      LayoutAlignItems: =LayoutAlignItems.Center       # Start/End/Stretch per docs
      LayoutGap:        =8
      LayoutOverflowY:  =LayoutOverflow.Scroll         # or .Hide
      PaddingTop: =8   PaddingBottom: =8   PaddingLeft: =8   PaddingRight: =8
```

Children carry `LayoutMinWidth` / `LayoutMinHeight` and **no X/Y** — see
powerapp-canvas-design for why that is the most important property in the whole dialect.

Still inferred, never seen non-default: `LayoutJustifyContent`, `LayoutWrap`, `FillPortions`,
and the non-AutoLayout variant name.

## Selecting one thing: five controls, five contracts

| Control | Seed the selection with | Read it as | Reach for it when |
|---|---|---|---|
| `Classic/DropDown@2.3.1` | `Default` | `.Selected.<Column>` (`SelectedText` is deprecated) | many options, one line of space |
| `ListBox@2.2.0` | `Default` (one item only) | `.Selected`, `.SelectedItems` when `SelectMultiple` | multi-select in a fixed box |
| `ModernDropdown@1.0.0` | `Default` — a **value** | `.Selected.Value` | the modern single-select |
| `ModernCombobox@1.0.0` | `DefaultSelectedItems` — a **table** | `.Selected.Value` | searchable or multi-select |
| `Classic/Radio@2.3.0` | `Default` | `.Selected.Value` | **2–7 options that must all stay visible** |

The seeding property is where these differ most, and getting it wrong is silent: the control
renders, it just never shows the current value. `DefaultSelectedItems` "must be a table of
records from the Items data source" — so with `Items: =["A", "B"]`, the matching seed is
`=[gVar]`, not `=gVar`.

Classic `DropDown`, `ListBox` and `Radio` all name their display column with a **dotted
property key**:

```yaml
Items: =MyTable
Items.Value: =ColumnName     # not a typo — a qualified property name
```

Three controls now, so treat it as the **classic-family convention**, not a quirk of one
control. The modern family uses `ItemDisplayText: =ThisItem.ColumnName` instead.

A radio group costs vertical space per option and never collapses, which is the whole point —
the choices stay readable without a click. It is the right control at 2–7 options (MS's own
guidance, for the classic and modern versions alike) and the wrong one beyond that, where a
combo box wins. `LineHeight` sets the gap between options; `Layout` (`Layout.Vertical` /
`Layout.Horizontal`) sets the direction.

**No property in this catalogue is inferred any more.** `DefaultSelectedItems` was the last one,
and its own MS Learn page confirms it.

## Quoting a column inside a formula

Studio writes `Choices([@asset_library].'asset_owner')` — a **single-quoted identifier**. Quotes
are only *required* when the identifier needs escaping, so an unquoted snake_case form
is equally valid; Studio is just being defensive. Do not confuse this with a double-quoted
string, which since 3.24042 is wrong in `ShowColumns`, `Ungroup`, `AddColumns` and friends.

## Edit form and data cards

```yaml
- Form1:
    Control: Form@2.4.4
    Variant: Classic
    Layout: Vertical                 # a top-level key, not a property
    Properties:
      DataSource: =asset_library
    Children:
      - asset_name_DataCard1:
          Control: TypedDataCard@1.0.7
          Variant: ClassicTextualEdit
          IsLocked: true             # Studio locks generated cards
          Properties:
            DataField: ="Title"                       # a STRING — the internal name
            Default: =ThisItem.asset_name             # value IN, from the form's Item
            Update: =DataCardValue1.Text              # value OUT, read by SubmitForm
            DisplayName: =DataSourceInfo([@asset_library], DataSourceInfo.DisplayName, 'Title')
            MaxLength:   =DataSourceInfo([@asset_library], DataSourceInfo.MaxLength, 'Title')
            Required: =false
          Children:
            - DataCardKey1:                # MetadataKey: FieldName    — the caption
            - DataCardValue1:              # MetadataKey: FieldValue   — the input
            - ErrorMessage1:               # MetadataKey: ErrorMessage — validation text
```

**The card is the contract.** `Default` is the way in, `Update` is the way out, and the
children bind back to the card through `Parent`:

```powerapps
Text:        =Parent.DisplayName
Default:     =Parent.Default
MaxLength:   =Parent.MaxLength
DisplayMode: =Parent.DisplayMode
BorderColor: =If(IsBlank(Parent.Error), Parent.BorderColor, Color.Red)
```

`MetadataKey` (`FieldName` / `FieldValue` / `ErrorMessage`) is what tells Studio which child
plays which role — swap the input control and keep the key. `Layout:`, `MetadataKey:` and
`IsLocked:` are all first-class pa-yaml keys, now confirmed in the wild.

Note `DataSourceInfo`'s column argument is a **single-quoted identifier** (`'Title'`), not a
double-quoted string — consistent with the 3.24042 identifier change.

**When a form is the right tool:** a straightforward CRUD screen over one list, where you want
`SubmitForm`, `Form.Error`, `Form.Unsaved` and per-field validation for free.

**When it is not:** anything needing a *guarded write per column*. An app that writes optional
Choice, expanded-user (Person) and expanded-taxonomy (Managed Metadata) columns puts each in a
separate `Patch` call so one bad field can't take the whole record down, and stages child rows
before the parent exists. A single `SubmitForm` cannot express that. Forms and hand-rolled
`Patch` screens are both legitimate — pick per screen, and say which you picked and why.

## Choosing between classic and modern

Prefer modern for anything a user types into or picks from — it removes hand-parsing:

- a date picker cannot produce an unparseable date, so `DateValue()` and its "⚠ not a date"
  echo label both disappear;
- a number input cannot produce a non-number, so `Value()` and its `IsError` guard disappear.

**Keep classic where the modern control can't do the job.** The transparent full-template
gallery hit target needs `Fill: =RGBA(0,0,0,0)` and `BorderThickness: =0`, which a Fluent
button does not expose — those stay `Classic/Button@2.2.0`.

## Boolean, rating and rich text

All three were read off Studio code view on 2026-08-05. Studio prints only NON-default
properties, so what follows is *its* default styling — copy the token and the properties you
actually need, not the whole block.

```yaml
- Toggle1:
    Control: Classic/Toggle@2.1.0
    Properties:
      Default:    =gEditAsset.asset_is_active       # boolean IN
      TrueText:   ="Active"                         # only shown when ShowLabel is true
      FalseText:  ="Inactive"
      TrueFill:   =RGBA(0, 120, 212, 1)             # Studio default
      FalseFill:  =RGBA(96, 94, 92, 1)
      OnChange:   =Set(gIsActive, Toggle1.Value)
```

`OnCheck` / `OnUncheck` fire on one transition each; `OnChange` fires on both — pick one, not
both, or the same work runs twice. A toggle is **two-state only**: a SharePoint Yes/No column
that must distinguish "not answered" from "no" needs a dropdown, because a toggle cannot
produce `Blank()`.

```yaml
- Rating1:
    Control: Rating@2.1.0
    Properties:
      Default:     =gEditAsset.asset_priority_score
      Max:         =5                               # defaults to 5 — set it if the scale differs
      ReadOnly:    =false
      RatingFill:  =RGBA(16, 110, 190, 1)           # Studio default
```

`Rating.Value` is a number and is `0`, not `Blank()`, when unrated — so a "must be rated"
guard is `Rating1.Value > 0`, and writing an unrated control to an optional Number column
stores a real 0. The **modern** Rating adds `Step` for half stars; the classic one is whole
stars only.

```yaml
- RichTextEditor1:
    Control: RichTextEditor@2.7.0
    Properties:
      Default:          =gEditAsset.asset_description   # HTML in
      EnableSpellCheck: =true
      DisplayMode:      =If(gReadOnly, DisplayMode.View, DisplayMode.Edit)
```

Then `Patch(..., { asset_description: RichTextEditor1.HtmlText })` — **the out property is a
different name from the in property**, the only control in this catalogue where that is true.
It emits markup, so it pairs with an *Enhanced rich text* column and an `HtmlViewer@2.1.0` on
the read side. It is also a heavy control: one per screen, never inside a gallery template.

## Slider and radio

```yaml
- Slider1:
    Control: Classic/Slider@2.1.0
    Properties:
      Default:    =gPct        # a slider must bind a real numeric column — the Default
      Min:        =0           # has to resolve to a name in your list schema, not a placeholder
      Max:        =100                              # the 0–100 default silently clamps a real scale
      Layout:     =Layout.Horizontal
      ShowValue:  =true
      ValueFill:  =RGBA(0, 120, 212, 1)             # the FILLED part, left of the handle
      RailFill:   =RGBA(184, 187, 184, 1)           # the EMPTY track, right of the handle
      OnChange:   =Set(gPct, Slider1.Value)
```

`ValueFill` and `RailFill` are easy to swap, and swapping them makes the slider read backwards
with no error. And a slider **always has a number** — it cannot express `Blank()`, so it cannot
represent an unset optional column; pair it with a "not set" checkbox or use a number input.

```yaml
- Radio1:
    Control: Classic/Radio@2.3.0
    Properties:
      Items:       =Choices([@asset_library].asset_status)
      Items.Value: =Value                           # the display column, dotted key
      Default:     =gEditAsset.asset_status.Value
      Layout:      =Layout.Vertical
      LineHeight:  =28
      RadioSelectionFill: =RGBA(0, 120, 212, 1)
      OnChange:    =Set(gStatus, Radio1.Selected.Value)
```

**Two version traps on the modern slider.** `ModernSlider@1.0.0` was revised: the input used to
be `Value` and is now `Default`, with `Value` demoted to a read-only output; and `Layout` became
`LayoutDirection`, taking a typed enum instead of the string `"Horizontal"`. Any sample found
online that assigns `Value:` predates the change and will not behave as written.

**And the orientation enum has no single name.** The modern Radio takes `Layout.Vertical`, the
modern Slider takes `LayoutDirection.Horizontal`, and a `GroupContainer` takes
`LayoutDirection.Vertical`. Same concept, two enum names, no rule — check per control.

The **modern radio group's token is not grounded**. Its semantics are on MS Learn (`Items`,
`ItemDisplayText`, `Default`, `Selected`, `Required`, `TriggerOutput`) but the page never names
the pa-yaml token, so do not author one — use `Classic/Radio@2.3.0`, which is grounded.

## How to ground a token you don't have

In order of cost:

1. **Unzip an `.msapp`** — it is a zip. `References/Templates.json` holds enum tables as
   pipe-delimited runs. This is how the 180-value Icon enum was recovered.
   ```bash
   unzip -o app.msapp -d /tmp/app
   grep -oE '[A-Za-z0-9_]+(\|[A-Za-z0-9_]+){20,}' /tmp/app/References/Templates.json
   ```
2. **Ask for a code-view photo or paste.** Insert the control in Studio, open code view,
   send it. Studio prints only NON-DEFAULT properties, so set the property you care about to
   something non-default first or it won't appear.
3. **MS Learn** for output properties and enum members — the docs describe those well even
   when they never name the token.
4. **Ship a grounded fallback** if none of the above lands. Drawing a hamburger from three
   Rectangles beats guessing `Icon.Hamburger`.

Record whatever you learn in your grounded-token file (e.g. `tools/studio-enums.json`) and the
validator's allow-list, with its provenance. A token grounded once should never need grounding
twice.
