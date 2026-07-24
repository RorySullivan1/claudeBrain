---
name: power-apps-components
description: >
  Expert at building reusable Power Apps canvas components and UI elements — the
  control/layout/rich-content layer of a canvas app. Use this skill whenever the
  user wants to create a reusable component, build or publish a component library,
  add a custom Input/Output/Behavior/Function property, design a responsive screen
  with containers, build a theme/design-system, lay out galleries or forms as UI,
  or render formatted HTML with the HtmlText control. Trigger on "create a reusable
  component", "component library", "custom input/output property", "make a header
  component", "reusable card", "render HTML in Power Apps", "HtmlText control",
  "build an HTML table/badge in Power Fx", "responsive layout", "horizontal/vertical
  container", "Parent.Width", "fill portions", "theme component", "named formulas",
  "propagate a component update". Implicit signals: repeated copy-pasted control
  clusters, absolute X/Y that break on resize, a screen that needs the same
  header/nav on every page, or a request to show a table/badge/rich text that a
  Label can't format. Boundary: core formula logic, data operations, and delegation
  belong to power-fx-development; auditing existing formulas belongs to
  power-fx-review; HTML rendering of SharePoint *list cells or views* (a different
  surface entirely) belongs to sharepoint-column-formatting — this skill owns HTML
  rendered *inside the app* via HtmlText. Data-source/backend design belongs to
  sharepoint-list-architecture; Graph calls to graph-api-integration.
---

# Power Apps Components Skill

You build reusable UI elements for canvas Power Apps: components that define their
contract with typed custom properties, screens that lay out with containers instead
of absolute coordinates, and rich content rendered through the HtmlText control's
restricted HTML subset. Lead with the answer, state assumptions, and keep formula
*logic* out of this layer — it belongs in `power-fx-development`.

## Core principles

- **A component is a contract, not a copy.** Its only inputs/outputs are its custom
  properties; nothing inside reaches out to app globals. That boundary is what makes
  it reusable across screens and (via a library) across apps.
- **Size and position with formulas, never dragging.** `Parent.Width`/`Parent.Height`
  and containers, not constant X/Y. Once a control's X/Y/Width/Height is a formula,
  dragging it in the editor silently overwrites the formula with constants.
- **Match the property *type* to intent** — Data vs. Function vs. Behavior/Action vs.
  Event. Picking wrong (e.g. a Data output where you needed a Behavior action) is the
  usual reason a component "can't do" something.
- **Prefer native controls; reach for HtmlText only when no control formats it.**
  HtmlText renders a *restricted* HTML subset (no script/style/object), so use it for
  tables, badges, and inline-styled rich text — not as a general web view.

## First — clarify before building

| Unknown | Ask |
|---|---|
| Element type | "A reusable component, a responsive screen layout, a gallery, or rich HTML content?" |
| Reuse scope | "Reused within one app, or across apps? (across apps ⇒ component library)" |
| Contract | "What does it take in and hand back — which inputs, and what state should the app read out?" |
| Behavior | "Does the app need to *trigger* something on it (Reset, Save), or does *it* raise events to the app?" |
| HTML need | "Can a native control format this, or does it truly need HtmlText (a table/badge/mixed inline styling)?" |
| Responsiveness | "Fixed tablet/phone size, or must it reflow across screen sizes?" |

---

## Custom properties — the component's contract

Four property kinds. Choose by what crosses the boundary and in which direction. Data
properties are the *only* ones that participate in app data flow.

| Property type | Direction | Purpose | Can chain side-effects? | Example |
|---|---|---|---|---|
| **Data** | Input | App → component value | no | `HeaderColor` (Color), `Items` (Table) |
| **Data** | Output | Component → app value/state | no | `SelectedItem` (Record) |
| **Function** | Input / Output | Pure logic, args in → value out | no | `FormatName(first, last)` |
| **Behavior / Action** | Output | App calls it to *do* something in the component | **yes** | `ResetFilters()`, `Save()` |
| **Event** | Input | Component calls app-defined logic on an event | **yes** | `OnItemSelected` |

Key rules grounded in the docs:

- **Function properties can't touch variables or other component properties** and
  don't trigger data flow — everything they need is passed as arguments. Use them for
  pure transforms only.
- **Behavior/Action and Event properties** are the enhanced-component-properties
  feature; enable it in **Settings → Upcoming features** if the option to add them
  isn't shown. They allow chained/side-effecting formulas (`Set`, `Collect`, `Reset`).
- Give a Data-of-type-Table/Record property a **default value** that shows the expected
  schema (e.g. `Table({Title:"", Subtitle:""})`) so consumers know the shape to pass.

### Worked example — a reusable `StatCard` component

A KPI card reused across dashboards. Inputs style + data; outputs the last tap; the app
can reset its pressed state.

**Custom properties**

| Name | Type | Definition | Data type | Default |
|---|---|---|---|---|
| `Label` | Data | Input | Text | `"Metric"` |
| `Value` | Data | Input | Number | `0` |
| `AccentColor` | Data | Input | Color | `RGBA(0,120,212,1)` |
| `Trend` | Data | Input | Number | `0` (±% change) |
| `Selected` | Data | Output | Boolean | `false` |
| `OnCardSelect` | Event (Input fn) | — | — | (app supplies) |

**Inside the component** (controls size to the component, never the screen):

```power
// Root container: Fill = StatCard.AccentColor tinted
ColorFade(StatCard.AccentColor, 0.85)

// lblValue.Text
Text(StatCard.Value, "[$-en-US]#,##0")

// lblTrend.Text  — arrow + percent, colored by sign
If(StatCard.Trend >= 0, "▲ ", "▼ ") & Text(Abs(StatCard.Trend), "0.0%")

// lblTrend.Color
If(StatCard.Trend >= 0, Color.Green, Color.Red)

// Button (invisible overlay) OnSelect  — set output state AND raise the event
Set(gLastCard, StatCard.Label); StatCard.OnCardSelect()
```

Set the component's **`Selected`** output property formula to the internal button's
pressed flag (a component-scoped variable), so the app can read `StatCard_1.Selected`.

**On the screen** (the consuming app):

```power
// Instance property assignments
StatCard_1.Label       = "Revenue"
StatCard_1.Value       = Sum(Sales, Amount)
StatCard_1.AccentColor = Theme.Primary          // named formula, see Theming
StatCard_1.Trend       = varRevenueTrend
StatCard_1.OnCardSelect = Navigate(DetailScreen, ScreenTransition.Cover)
```

Because the app supplies `OnCardSelect`, each instance decides what a tap does — the
component stays generic. Keep the actual formula logic (the `Sum`, the trend math) in
the app / a helper, per `power-fx-development`; the component only presents it.

---

## Component libraries — reuse across apps

A single component lives in one app. To share it across apps, put it in a **component
library** (a first-class container of components):

1. **Create** the library (Power Apps home → **+ New → Component library**), author the
   component there, and **Publish** the library.
2. **Consume** it: in another app, **Insert → Get more components → Library**, pick the
   components. Instances reference the published definition.
3. **Update propagation:** edit + **Publish** the library again. Consuming apps get an
   **"Update available"** banner; the maker chooses to pull the new version. Updates are
   *not* silent/forced — treat a library like a versioned dependency and note breaking
   property changes.

Library limitations to design around: **Power Automate flows aren't supported inside a
component library**, and you **can't save data sources** (or controls bound to them,
like Forms/data tables) in a component — pass data *in* through Input properties instead.

---

## Component scope & the reset pattern

- **Components are isolated.** Inside, `UpdateContext` is **not** supported. Use `Set()` —
  its variables are **scoped to the component instance** and invisible to the app unless
  you surface them through an **Output** property.
- **Resetting an instance:** define the component's **`OnReset`** behavior to clear its
  state, then either the app calls `Reset(StatCard_1)`, or — for the common "reset when
  the bound record changes" case — check **"Raise OnReset when value changes"** on the
  relevant Input property so a new input auto-fires `OnReset`.

```power
// Component OnReset
Set(varPressed, false); Reset(galInner)

// Default of an inner input, so it re-seeds cleanly on reset
If(IsBlank(varPressed), StatCard.Value, varPressed)
```

- **Cross-instance caveat:** you can't wire one instance's Input custom property to
  another instance's Output custom property (circular-reference warning). Route through
  an app variable/collection instead.

---

## Responsive layout — containers over coordinates

Absolute X/Y is the #1 cause of layouts that break on resize. Prefer, in order:

1. **Auto-layout containers** — **Horizontal container** / **Vertical container**. They
   position children automatically (you never set child X/Y) and distribute space.
2. **Relative formulas** on X/Y/Width/Height when a container doesn't fit.

**Enable true responsiveness first:** Settings → Display → turn **off** *Scale to fit*
(also *Lock aspect ratio* / *Lock orientation*). "Scale to fit" only zooms a fixed
layout; it is not responsiveness.

**Top-level container fills the screen:**

```power
X = 0   Y = 0   Width = Parent.Width   Height = Parent.Height
```

**Split space with `FillPortions`.** On children of a container, `FillPortions`
distributes leftover space by ratio (like CSS flex-grow). Left rail 1, body 3:

```power
// LeftRail.FillPortions  = 1
// BodyPanel.FillPortions = 3    → rail gets 1/4, body gets 3/4
```

Set the container's **Align** to `Stretch` to fill the cross-axis, and use
`Wrap = true` + `Overflow = Scroll` on flexible-height/width containers so narrow
screens reflow instead of clipping.

**Relative-formula patterns** (control `C`, no container). `Parent` is the screen or the
enclosing container/component:

| Goal | Property | Formula |
|---|---|---|
| Fill parent with margin `N` | `X` / `Width` | `N` / `Parent.Width - (N*2)` |
| Right-align to parent | `X` | `Parent.Width - (C.Width + N)` |
| Center horizontally | `X` | `(Parent.Width - C.Width) / 2` |
| Sit below sibling `D` | `Y` / `Height` | `D.Y + D.Height` / `Parent.Height - C.Y` |

Inside a **component**, these same formulas use `Parent.Width`/`Parent.Height` to mean
the *component's* size — that's what makes a component resize with its instance.

> Once X/Y/Width/Height is a formula, **stop dragging the control** — a drag overwrites
> your formula with frozen constants.

---

## Galleries & forms as UI elements

- **Gallery** = the repeater. Set **`Items`**; inside the template, refer to the current
  row with **`ThisItem`**; read the user's pick via the gallery's **`Selected`** output
  (`gal.Selected.Title`). Choose the template layout, and keep the template's inner
  controls positioned with `Parent.*` so rows reflow. **Nested galleries:** the inner
  gallery's `Items` is a table on the outer row, e.g. `ThisItem.LineItems`.
- **Constraint:** you **can't place a canvas component inside a gallery or a form** — so
  build a repeating card's row template from plain controls (or render it with HtmlText),
  and reserve components for screen-level building blocks (headers, nav, side panels).
- **Form** (Edit/Display) = the bound record editor — cards, `DataCardValue`, `SubmitForm`.
  Use a form when you're editing *one* record against a data source; use a gallery to
  browse many. Data-source binding and submit logic are `power-fx-development` territory.

---

## Theming — a design system with named formulas

Centralize color/typography so every component and screen reads one source. Prefer
**named formulas** in **`App.Formulas`** (computed, immutable, always current — no
`OnStart` ordering bugs):

```power
// App.Formulas
Theme = {
    Primary:    RGBA(0, 120, 212, 1),
    OnPrimary:  RGBA(255, 255, 255, 1),
    Surface:    RGBA(250, 250, 250, 1),
    Danger:     RGBA(196, 43, 28, 1),
    TextMain:   RGBA(32, 31, 30, 1)
};
Type = { H1: 28, H2: 20, Body: 14, Caption: 11 };
```

Then anywhere: `Fill = Theme.Surface`, `Color = Theme.TextMain`, `Size = Type.H2`.
Swapping a brand color is a one-line edit. (If named formulas aren't enabled, a
**theme component** exposing Output properties, or `Set()` in `App.OnStart`, is the
fallback — but named formulas avoid startup cost and staleness.) Feed the tokens into
components through their Input color/number properties, as `StatCard_1.AccentColor =
Theme.Primary` above.

---

## The HtmlText control — rendering rich content

`HtmlText` shows a string and interprets a **restricted** subset of HTML. Build the
string in Power Fx (interpolation `$"..."` or `Concatenate`) and assign it to the
control's **`HtmlText`** property. Reach for it when a Label/native control can't do the
formatting: **tables, badges, mixed inline styling, bulleted content from data**.

### What it supports — and what it strips

- **Stripped/ignored:** `<script>`, `<style>`, `<object>`, and unsupported elements/
  attributes are removed. There is **no JS, no external CSS, no `<link>`/`<style>`
  blocks** — style with **inline `style="..."`** only.
- **Default browser styling is dropped** for some elements — notably `<ul>`/`<ol>`: give
  them explicit inline styles (`list-style-type`, `margin`, `padding-inline-start`) or
  they render without bullets/indent.
- **Positioning:** HtmlText assumes relative positioning. For anything using
  `position:absolute` inside, wrap it in a relatively-positioned div:
  `"<div style='position:relative'>" & content & "</div>"`.
- **Not interactive/accessible by default:** the control has **no `TabIndex`** and can't
  be focused or act as a button; ARIA isn't applied automatically. `<a>` links work but
  need the app's **Simplified tab index** setting for correct tab order. If you need
  clicks, use a real Button — not an `onclick` in HtmlText (it won't run).
- **Images:** remote `<img src>` may be blocked by app connection rules; **data-URI**
  images (`src="data:image/png;base64,..."`) render reliably and travel with the app.
- **Encode untrusted text.** Wrap any user/data-sourced string you drop into markup with
  **`EncodeHTML(...)`** so a stray `<` or `&` can't break (or inject into) your HTML.

### Worked example — a status badge + detail table from a record

Given a record `rec` (`{Title, Owner, Status, Amount, DueDate}`), render a colored badge
and a two-column table:

```power
// HtmlText property of an HTML text control
With(
    {
        badgeColor:
            Switch(rec.Status,
                "Approved", "#107C10",
                "Pending",  "#986F0B",
                "Rejected", "#C42B1C",
                            "#605E5C")
    },
    $"<div style='font-family:Segoe UI, sans-serif; font-size:13px; color:#201F1E'>
        <span style='background:{badgeColor}; color:#fff; padding:2px 8px;
                     border-radius:10px; font-size:11px'>
            {EncodeHTML(rec.Status)}
        </span>
        <table style='border-collapse:collapse; margin-top:8px; width:100%'>
            <tr>
                <td style='padding:4px 8px; border:1px solid #EDEBE9; font-weight:600'>Owner</td>
                <td style='padding:4px 8px; border:1px solid #EDEBE9'>{EncodeHTML(rec.Owner)}</td>
            </tr>
            <tr>
                <td style='padding:4px 8px; border:1px solid #EDEBE9; font-weight:600'>Amount</td>
                <td style='padding:4px 8px; border:1px solid #EDEBE9'>{Text(rec.Amount, "[$-en-US]$#,##0")}</td>
            </tr>
            <tr>
                <td style='padding:4px 8px; border:1px solid #EDEBE9; font-weight:600'>Due</td>
                <td style='padding:4px 8px; border:1px solid #EDEBE9'>{Text(rec.DueDate, "yyyy-mm-dd")}</td>
            </tr>
        </table>
      </div>"
)
```

To render a **variable-length list**, build rows with `Concat` over a table, then wrap:

```power
"<ul style='list-style-type:disc; padding-inline-start:20px; margin:4px 0'>" &
Concat(colTasks, "<li style='margin:2px 0'>" & EncodeHTML(Title) & "</li>") &
"</ul>"
```

**When to prefer native controls instead:** if the content is a simple styled string,
use a **Label** (`Font`, `Size`, `Color`, `FontWeight`) — cheaper and accessible. If rows
are selectable or bound, use a **Gallery**. Use HtmlText specifically for static, richly
formatted, non-interactive markup a single control can't otherwise express.

---

## Performance

- **Reuse beats duplication.** Components de-duplicate controls and reduce app size;
  update once, all instances follow.
- **Keep `OnVisible`/`OnStart` light.** Don't load or compute heavy data there; prefer
  **named formulas** (computed lazily, cached) and load lists on demand. Heavy `OnStart`
  delays first paint of every screen.
- **Don't over-nest containers.** Deep container trees and many HtmlText controls cost
  layout time; collapse levels where a couple of relative formulas suffice.
- **Set `.List`/`Items` from one table**, not row-by-row appends, same as any Power Fx
  data-shaping (see `power-fx-development` for delegation-safe sourcing).

---

## Watch Out

1. **Wrong property type dead-ends you.** A **Data Output** can only *emit a value* — it
   can't run `Navigate`/`Set` for the app. To let the app trigger side-effects, use a
   **Behavior/Action** (Output) or **Event** (Input) property, and enable enhanced
   component properties if you don't see the option.
2. **`UpdateContext` silently unavailable in components.** Use `Set()` (component-scoped),
   and surface anything the app must read through an **Output** property — a context
   variable set inside is invisible outside.
3. **Dragging overwrites your responsive formulas.** After you write `Parent.Width`-based
   sizing, moving the control in the canvas replaces the formula with constants and the
   layout stops reflowing. Adjust via the formula bar.
4. **HtmlText is not a web view.** No `<script>`, no `<style>`/external CSS, no working
   `onclick`; inline styles only, `<ul>`/`<ol>` need explicit styling, and it can't take
   focus. If you need behavior or accessibility, use native controls.
5. **Unencoded data breaks (or injects into) HtmlText.** A `<` or `&` from a data source
   corrupts the markup — wrap interpolated strings in `EncodeHTML()`.
6. **A component library is a dependency, not a live link.** Consuming apps must *accept*
   an update; breaking a property contract strands them on the old version. Version
   deliberately.

---

## Out of scope — defer to a sibling skill

- **Core formula logic, data operations, delegation, error handling** — the `Sum`,
  `Filter`, `Patch`, `Collect`, and delegation warnings behind a component → **power-fx-development**.
- **Auditing/reviewing existing Power Fx** for correctness, delegation, or performance →
  **power-fx-review**.
- **HTML rendering of SharePoint *list columns / views*** — a completely different
  surface (declarative JSON formatting of list cells, not the app) → **sharepoint-column-formatting**.
- **Designing the SharePoint list/library backing the app** → **sharepoint-list-architecture**.
- **Microsoft Graph calls** (users, files, calendar) → **graph-api-integration**.
- **DAX / Power BI visuals** → **power-bi-dax**; **Power Query / M** data prep → **power-query-m**.
