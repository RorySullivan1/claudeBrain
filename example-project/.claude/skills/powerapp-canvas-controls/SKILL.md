---
name: powerapp-canvas-controls
description: >
  The grounded control catalogue for canvas-app YAML — which `Control:` tokens, `Variant:`
  values, enum members and OUTPUT properties actually exist, and which are guesses. Use this
  skill whenever a control is being chosen, added, or swapped: "which control should I use",
  "what's the token for a dropdown / date picker / container", "is Icon.Table real", "what
  does a combobox return", "convert this to a modern control", "why did the paste fail on
  this control", "add a text input / gallery / tab list". Also use before writing ANY new
  control into `src/Screens/` — an ungrounded token fails the whole paste and comes back only
  as "it didn't work". Covers: classic vs modern control families, version suffixes, gallery
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

> **Docs source (meaning, not tokens):** the authoritative control/layout reference is
> `github.com/MicrosoftDocs/powerapps-docs`. See `.claude/context/powerapps-docs-source.md` for the
> paths and how to fetch it (raw GitHub, `gh`, or the connected MS Learn MCP). Ground a control's
> SEMANTICS there; ground the pa-yaml TOKEN in `tools/studio-enums.json` (Studio code-view).

**The single rule: never author a control token you cannot point at evidence for.**

An unknown `Control:` or `Variant:` fails the *entire* paste. Across a one-way gap that returns
as "it didn't work" with no detail, and you then revise blind. Every token below is either
grounded (read off a real Studio artefact) or explicitly marked as a guess.

`tools/studio-enums.json` is the machine-readable copy; `tools/validate_pa_yaml.py` enforces it.

---

## The generic docs will get you rejected

Microsoft's YAML guidance lists control types as `Label`, `Button`, `TextInput`, `Container`,
`Dropdown`. **Studio's code view does not emit those names.** It emits versioned, sometimes
prefixed tokens:

| Generic doc says | Studio actually writes |
|---|---|
| `Button` | `Classic/Button@2.2.0` — modern button version UNKNOWN, so classic |
| `TextInput` | `ModernTextInput@1.1.1` or `Classic/TextInput@2.3.2` |
| `Container` | `GroupContainer@1.5.0` + `Variant: AutoLayout` (or `GridLayout` — see below, container shape not yet grounded) |
| `Dropdown` / `Combobox` | `ModernCombobox@1.1.1` (or `Classic/ComboBox@2.4.0`) |
| `DatePicker` | `ModernDatePicker@1.0.1` |
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

**Modern family IN USE** — `ModernTextInput@1.1.1`, `ModernCombobox@1.1.1`,
`ModernDatePicker@1.0.1`, `GroupContainer@1.5.0` (`Variant: AutoLayout`). Version-confirmed
but unused: `ModernDropdown@1.0.2`, `ModernRadio@1.0.1`, `ModernDataGrid@1.5.0`,
`ModernCard@1.3.0` (2026-08-10, same photo as `GridLayout`).

**Version UNKNOWN, so NOT used** — `ModernButton`, `ModernNumberInput`, `ModernTabList`,
`ModernSlider`. Author the classic control for these; see the standing rule below.

**`Classic/ComboBox@2.4.0` and `ModernCombobox@1.1.1` are different controls.** The classic
adds `Chevron*` styling properties and takes `DefaultSelectedItems` to seed the selection —
which is how a card wires it up:

```yaml
Items: =Choices([@asset_library].'asset_owner')
DefaultSelectedItems: =Parent.Default
SelectMultiple: =false
DisplayMode: =Parent.DisplayMode
PaddingLeft: =If(Self.DisplayMode = DisplayMode.Edit, 5, 0)
```

Version suffixes are optional on the CLASSIC family — Studio uses the current version if
omitted. On the modern family they are not decoration; see below.

### MODERN VERSIONS ARE PER-CONTROL — read them, never infer them

Read off the live Studio controls by the user, **2026-08-07**:

| Modern control | pa-yaml token |
|---|---|
| Text input | `ModernTextInput@1.1.1` |
| Combo box | `ModernCombobox@1.1.1` |
| Dropdown | `ModernDropdown@1.0.2` |
| Date picker | `ModernDatePicker@1.0.1` |
| Radio | `ModernRadio@1.0.1` |
| Data grid | `ModernDataGrid@1.5.0` |

**Nothing in that table is `@1.0.0`, and no two entries share a version.** This repo
carried `@1.0.0` on every modern token for days purely because the first few happened to
ground that way — a pattern that was never real. A version cannot be inferred from a
sibling control, from the family, or from a number in MS Learn's sample code.

> **THE STANDING RULE: if you are unsure of a modern control's version, author the CLASSIC
> control instead.** A wrong version rejects the *whole* paste and returns as "it didn't
> work". `ModernButton` and `ModernNumberInput` were converted to `Classic/Button@2.2.0`
> and `Classic/TextInput@2.3.2` on 2026-08-07 for exactly that reason — their versions are
> unknown, and a working classic control beats a guessed modern one every time.

Converting a button means dropping `Appearance` (modern-only) and carrying the look on
`Fill` / `Color` / `BorderColor` / `BorderThickness`. Converting a number input means
dropping `Min` / `Step` / `Precision` and reading it as `Value(ctl.Text)` rather than
`ctl.Value`, because a classic text input outputs text.

### Sibling modern controls do NOT share property names

Two property errors on one screen, both from assuming a neighbour's spelling:

| Control | Right | Wrong — and what it belongs to |
|---|---|---|
| `ModernTextInput` | `Type: =TextInputType.Multiline` | `Mode: =TextMode.MultiLine` — the **classic** text input |
| `ModernTextInput` | `TriggerOutput: =TriggerOutput.Delayed` | `DelayOutput: =true` — the **combo box** |

`TriggerOutput` takes `Keypress` (default) / `FocusOut` / `Delayed`. The combo box is the
control that renamed `TriggerOutput` to `DelayOutput`; the text input did **not**.

> **`FocusOut` does NOT fire on Enter — confirmed in Studio 2026-08-11.** It means only what
> it says: the output commits when the control *loses focus*. Both pickers were authored with
> `FocusOut` on the assumption that a single-line input commits on Enter, and the result was a
> search box where Enter did nothing and results appeared only when you clicked away.
>
> **There is no keypress or Enter event on a canvas text input at all**, so no formula can bind
> Enter to an action. The two real options are `Delayed` (debounce — fires once typing stops,
> which is what this repo uses in all eight places) or an explicit button beside the box. If a
> spec asks for "press Enter to search", say up front that it cannot be built.

### `AccessibleLabel` is a MODERN-ONLY property

**`AccessibleLabel` does not exist on `Classic/*` controls — confirmed 2026-08-12.** Writing it
on a `Classic/Button`, `Classic/Icon` or `Classic/TextInput` fails the paste. It is valid on
modern controls (`ModernTextInput` and its siblings), which is the whole reason the mistake is
easy to make: the property is real, it is just not on the family you reached for.

The classic equivalent is **`Tooltip`**, which is grounded and used throughout this repo — but
it is a hover hint, not a name, so it does not solve the same problem. Where a classic control
carries no visible text (a transparent full-row hit target, a scrim), **there is no property
that names it**, and a screen reader announces it as a bare "button". Say so plainly rather
than reaching for a label property that does not exist; the only real fix is converting that
control to a modern one, which is a separate change with its own paste risk.

### Modern controls still get REVISED — the revision renames properties

The revision is real even though the token doesn't move. The combo box's current shape:

| Old | Current |
|---|---|
| `TriggerOutput` | `DelayOutput` (boolean) |
| `Fields = ["Col"]` | `ItemDisplayText = ThisItem.Col` |
| `SelectMultiple` default `false` | default **`true`** — set it explicitly |
| `Appearance` / `ValidationState` as strings | typed enums |
| `FontColor` / `FontSize` / `BorderRadius` | `Color` / `Size` / `Radius{TopLeft,…}` |

So a sample found online is version-specific in its PROPERTIES as well as its token — check
both. `ModernSlider` was revised the same way (`Value`→`Default`, `Layout`→`LayoutDirection`).

**The two combo boxes name their display column differently, and it is not optional.**
`ModernCombobox@1.1.1` takes `ItemDisplayText: =ThisItem.Value`. `Classic/ComboBox@2.4.0` takes
string arrays — `DisplayFields: =["Value"]` **and** `SearchFields: =["Value"]`. Crossing them
renders **blank rows** rather than erroring. `Items` built by `Distinct()`, by a `["a","b"]`
literal, or by `Choices()` all expose a single column named **`Value`**, so `ThisItem.Value` is
right for every combo box in this repo.

`IsSearchable` and `SelectMultiple` both `=false` gives plain dropdown behaviour on either
control.

**There is no `Reset` PROPERTY on the modern combo box.** Classic `ListBox` has one, which is
where the idea comes from; authoring it here fails the paste. The `Reset()` *function* works
fine — and on the current control it now clears `SearchText` as well as the selection.

### `Default` on a tab list is an ITEM, on a dropdown it is a VALUE

`ModernTabList` (version UNKNOWN — see the standing rule) — **`Default: ="Tasks"` errors.** A string-array `Items` yields
*records* with a `Value` column (which is why the output is `.Selected.Value`), and MS Learn
says `Default` "must match an item from the Items source" — an item, not something equal to
one. Author `=First(["Tasks", "Transactions", "Issues"])`, or
`=LookUp([...], Value = "Tasks")` when it is not the first tab.

`ModernDropdown@1.0.2` is the opposite: its `Default` takes a **value**. Two modern controls,
two contracts, same property name — check per control.

Its `Limitations` also warn that "very small or very large width and height values might not be
fully respected", so never lay out the band beneath a tab list from a height you *assumed* it
would take.

## Output properties — get these wrong and every formula breaks

| Control | Read it as | Note |
|---|---|---|
| `ModernTextInput` | `.Text` | **Unchanged from classic** — converting inputs is a property rename only |
| `ModernNumberInput` | `.Value` | *reference only* — version UNKNOWN, so this repo authors `Classic/TextInput@2.3.2` and reads `Value(ctl.Text)` instead (a real number; the modern control's `TriggerOutput` was removed) |
| `ModernCombobox` | `.Selected.Value` | with `SelectMultiple: =false`, `Selected` is a record; also `.SelectedItems`, `.SearchText` |
| `ModernDatePicker` | `.SelectedDate` | `Blank()` when unset |
| `ModernTabList` | `.Selected.Value` | the tab label — and `Default` must be an **item**, not a value; see below |
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

Still inferred, never seen non-default: `LayoutJustifyContent`, `LayoutWrap`, `FillPortions`.

## Grid container — WHY to adopt it, and how far it is grounded

A second container layout worth adopting: **CSS-grid** placement. You set the grid's columns,
rows and gap once, and each child names its cell instead of living in a nested row-of-columns.
**A 2×2 that today costs a row container + two col containers collapses to ONE grid
container** — which is the whole point: fewer controls, lower load. Responsive like the
auto-layout container (children keep their cells; their X/Y are ignored).
Insert ▸ **Layout ▸ Grid container**.

### Grounded 2026-08-10 — the Control token, the Variant, and the four child tokens

A Studio code-view photo settled what this section previously carried as inferred, including
"the non-AutoLayout variant name". **The grid SHARES the auto-layout container's token and
version**; only the `Variant:` differs.

```yaml
- Container1:
    Control: GroupContainer@1.5.0          # <- SAME token and version as AutoLayout
    Variant: GridLayout                    # <- the second variant, confirmed
    Properties:
      X: =40
      Y: =40
    Children:
      - Card1:
          Control: ModernCard@1.3.0        # <- new modern token, version 1.3.0
          Properties:
            X: =40
            Y: =40
      - Combobox1:
          Control: ModernCombobox@1.1.1
          Properties:
            LayoutGridColumnStart: =3      # <- how a child names its cell
            LayoutGridColumnEnd:   =5
            LayoutGridRowStart:    =1
            LayoutGridRowEnd:      =3
            X: =40
            Y: =40
```

The predicted `Layout*` renaming is exactly what happened: display-name *Column Start* is
`LayoutGridColumnStart`, and so on for the other three.

**Studio wrote `X`/`Y` on the grid child anyway**, alongside the four `LayoutGrid*` properties —
the same thing it does for auto-layout children whose X/Y are ignored. Never read the presence
of X/Y as evidence that absolute positioning is in play.

### Still ungrounded — and it is the half that blocks authoring

**Semantics** are grounded on MS Learn `controls/control-grid-container` (read 2026-08-10) —
container: `Gap`, `Columns`, `Rows`, `Padding`, `X/Y/Width/Height`, `Color`,
`Border{Style,Thickness,Color}`, `BorderRadius`, `DropShadow`, `Visible`; per-child:
`Column Start/End`, `Row Start/End`, `Align in Cell`. Those are **DISPLAY names**.

The four child placement tokens are now mapped. **No container property token is** — the sample's
grid container carried only `X`/`Y`, so whatever `Columns`, `Rows` and `Gap` become is still
unknown, as is `Align in Cell`.

Also **inferred, not observed**: that `Start`/`End` are CSS-grid style *line* indices rather than
cell indices. `ColumnStart 3 / ColumnEnd 5` spans two columns under the line reading and three
under the cell reading, and the sample does not distinguish them. Likewise 1-based indexing, and
whether a child with none of the four gets auto-placed.

> **So: FILL a grid Studio already made — the four child tokens are safe. Do NOT author a
> `GridLayout` container from scratch**, because placing children into a grid whose shape you
> cannot express is a guess, and a guess fails the whole paste. To close it, ask the human for a
> code-view of a grid container whose columns/rows/gap have been configured in the Studio pane.
> See `tools/studio-enums.json ▸ _gridContainerNotes`.

## Selecting one thing: five controls, five contracts

| Control | Seed the selection with | Read it as | Reach for it when |
|---|---|---|---|
| `Classic/DropDown@2.3.1` | `Default` | `.Selected.<Column>` (`SelectedText` is deprecated) | many options, one line of space |
| `ListBox@2.2.0` | `Default` (one item only) | `.Selected`, `.SelectedItems` when `SelectMultiple` | multi-select in a fixed box |
| `ModernDropdown@1.0.2` | `Default` — a **value** | `.Selected.Value` | the modern single-select |
| `ModernCombobox@1.1.1` | `DefaultSelectedItems` — a **table** | `.Selected.Value` | searchable, multi-select, or plain dropdown with both flags off |
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

**No property in this repo is inferred any more.** `DefaultSelectedItems` was the last one, and
its own MS Learn page confirms it.

## Quoting a column inside a formula

Studio writes `Choices([@asset_library].'asset_owner')` — a **single-quoted identifier**. Quotes
are only *required* when the identifier needs escaping, so this repo's unquoted snake_case form
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

**When it is not:** anything needing a *guarded write per column*. This app writes optional
Choice, expanded-user (Person) and expanded-taxonomy (Managed Metadata) columns in separate
`Patch` calls so one bad field can't take the whole record down, and it stages child rows
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
      Default:    =gEditProject.project_is_active   # boolean IN
      TrueText:   ="Active"                         # only shown when ShowLabel is true
      FalseText:  ="Inactive"
      TrueFill:   =RGBA(0, 120, 212, 1)             # Studio default
      FalseFill:  =RGBA(96, 94, 92, 1)
      OnChange:   =Set(gPrActive, Toggle1.Value)
```

`OnCheck` / `OnUncheck` fire on one transition each; `OnChange` fires on both — pick one, not
both, or the same work runs twice. A toggle is **two-state only**: a SharePoint Yes/No column
that must distinguish "not answered" from "no" needs a dropdown, because a toggle cannot
produce `Blank()`.

```yaml
- Rating1:
    Control: Rating@2.1.0
    Properties:
      Default:     =gEditTask.task_priority_score
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
      Default:          =gEditIssue.issue_description   # HTML in
      EnableSpellCheck: =true
      DisplayMode:      =If(gReadOnly, DisplayMode.View, DisplayMode.Edit)
```

Then `Patch(..., { issue_description: RichTextEditor1.HtmlText })` — **the out property is a
different name from the in property**, the only control in this catalogue where that is true.
It emits markup, so it pairs with an *Enhanced rich text* column and an `HtmlViewer@2.1.0` on
the read side. It is also a heavy control: one per screen, never inside a gallery template.

## Slider and radio

```yaml
- Slider1:
    Control: Classic/Slider@2.1.0
    Properties:
      Default:    =gPct        # no numeric column in this schema binds a slider today —
      Min:        =0           # a real Default must resolve to a name in schema/schema.yaml
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
      Items:       =Choices([@taskmaster_tasks].task_status)
      Items.Value: =Value                           # the display column, dotted key
      Default:     =gEditTask.task_status.Value
      Layout:      =Layout.Vertical
      LineHeight:  =28
      RadioSelectionFill: =RGBA(0, 120, 212, 1)
      OnChange:    =Set(gStatus, Radio1.Selected.Value)
```

**Two version traps on the modern slider.** `ModernSlider` (version UNKNOWN — author `Classic/Slider@2.1.0`) was revised: the input used to
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

Record whatever you learn in `tools/studio-enums.json` and the validator's allow-list, with
its provenance. A token grounded once should never need grounding twice.

## `Theme` is a BUILT-IN name — never use it for your own global (2026-08-12)

Enabling modern controls also enables **modern theming**, and that puts `Theme` in the app's
namespace. MS Learn, *Use modern themes in canvas apps*:

> Reference the currently active theme object by using **`App.Theme`**. Reference any theme
> loaded into the app **by its instance name**… **Theme Name** … must be **unique within the app**.

This repo used a named formula called `Theme` for months. **Studio tolerated it**, which is what
made it expensive: the collision never produced an error. It surfaced as colours resolving
inconsistently and a header control disappearing — a control whose `Height` came from
`Theme.Space.HeaderH`, so a wrong resolution silently became 0. Renamed to **`gTheme`** across 946
references.

**The general rule this bought:** a contested identifier does not have to be *rejected* to ruin
you. It only has to resolve to something other than what you meant, somewhere you were not
looking — and a theme object resolving instead of yours gives blanks, and blanks give black fills
and zero dimensions. **Prefix app-level globals (`g…`), the way this repo already does for
`gSelProject` / `gEditMode`, and the whole class disappears.**

Names to treat as taken in a modern-controls app: `Theme` and any theme instance name, plus the
usual `App`, `Self`, `Parent`, `ThisItem`, `ThisRecord`. When a name is generic enough that the
platform might want it, assume it does.
