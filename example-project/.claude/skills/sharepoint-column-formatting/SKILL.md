---
name: sharepoint-column-formatting
description: >
  Expert at SharePoint column and view formatting — the declarative JSON that
  styles list cells and rows without code, using a restricted "HTML-in-JSON"
  element model (elmType/txtContent/style/attributes/children) and a runtime
  expression language. Use this skill whenever the user wants to color-code a
  status column, render a number as a data bar, apply conditional formatting to
  a list, show an icon by value, turn a field into a clickable hyperlink or
  mailto, add a button that launches a Power Automate Flow, or lay out a whole
  row/tile with a custom card. Trigger on "format a SharePoint column", "column
  formatting JSON", "view formatting", "conditional formatting in a list", "add
  a button to a list column", "color code status", "data bar", "status pill",
  "rowFormatter", "additionalRowClass", "customRowAction", or a pasted formatter
  JSON that won't render. Implicit signals: a screenshot of a plain SharePoint
  list they want to make readable, "@currentField", "[$InternalName]",
  "sp-field-severity", or "$schema … column-formatting.schema.json". Boundaries:
  designing the list's columns and data model themselves (column types,
  indexing, lookups, content types) is sharepoint-list-architecture; HTML
  rendered *inside a Power App* via the HtmlText control is a different surface —
  power-apps-components; changing formatting or list data *programmatically*
  through an API is graph-api-integration. This skill owns only the declarative
  visual formatter JSON.
---

# SharePoint Column & View Formatting Skill

You write the declarative JSON that changes how a SharePoint Online list *looks* —
not what it stores. This is **HTML-in-JSON**: a tiny, sandboxed element tree
(`elmType` → `txtContent`/`style`/`attributes`/`children`) that SharePoint renders
into DOM at view time. It is deliberately restricted — a fixed set of element types,
a whitelist of attributes, no `<script>`, no arbitrary HTML, no custom JS. Everything
dynamic is done with **expressions** evaluated per-row against field values.

Lead with the answer. State up front **which column or view** you're formatting and
**what condition** drives the styling, then hand over copy-paste JSON that starts with
the `$schema` line. Prefer the smallest formatter that works, and prefer a predefined
`sp-field-*` class over hand-rolled CSS.

The formatter changes presentation only. It never mutates data (except the explicit
`setValue`/`executeFlow` actions a user clicks), never runs on the server, and never
sees fields that aren't in the current view.

---

## Core principles

1. **Two schemas, two scopes.** *Column formatting* styles one field's cell; its root
   is a single element and it targets one column. *View formatting* styles the whole
   row (or card), via `rowFormatter`/`additionalRowClass` (List layout) or `formatter`
   (Gallery/Board). Same element grammar, different `$schema` and different entry point.
2. **Restricted element set.** `elmType` must be one of `div`, `span`, `a`, `img`,
   `svg`, `path`, `button`, `p`, `filepreview`. Anything else errors. No `<table>`, no
   `<input>`, no `<script>` — build layout from nested `div`/`span`.
3. **`style` is a flat CSS map.** `{"background-color": "...", "padding": "4px"}` —
   name/value pairs of CSS properties, not a stylesheet and not a `class` string.
   (Classes go in `attributes.class`.) `float` is no longer supported.
4. **`attributes` is a whitelist.** Only `href`, `rel`, `src`, `class`, `target`,
   `title`, `role`, `iconName`, `d`, `aria`, `data-interception`, `viewBox`,
   `preserveAspectRatio`, `draggable`. Any other attribute name errors.
5. **Every value can be an expression.** `txtContent`, any `style` value, and any
   `attributes` value may be a literal string or an expression evaluated per row.
6. **Fields by token or internal name.** `@currentField` is the column being formatted;
   `[$InternalName]` reaches sibling fields in the same view. Reference is by
   **internal name**, not display name (see the gotcha below).

---

## Clarify first

Column formatting is cheap to iterate but easy to aim at the wrong target. Before
writing JSON, pin down:

- **Column formatting or view formatting?** "Color the Status *cell*" → column. "Color
  the whole *row* red when overdue" or "show each item as a card" → view. If they want
  both cell chips *and* a row tint, do column formatting on the cell **plus**
  `additionalRowClass` on the view (they compose; `rowFormatter` does not).
- **Which field, and its internal name?** The display name may differ from the internal
  name. `[$Status]` works only if `Status` is the *internal* name. Ask, or tell them how
  to find it (below).
- **What is the field's type?** Text/choice/number render as `@currentField` directly;
  Person needs `@currentField.title`/`.email`, Lookup needs `.lookupValue`, Hyperlink
  needs `.desc` + the URL as `@currentField`, Date/Number/YesNo/Currency/Approval can use
  `.displayValue` for the locale-formatted string.
- **What conditions and buckets?** Enumerate the exact values ("Done / In Review /
  Blocked") and the color/icon each maps to. Vague "make it look nice" → propose a
  status-pill mapping and confirm.
- **Is every referenced field in the view?** `[$Other]` resolves to nothing if `Other`
  isn't a column in this view. Sibling references require the field be present.

---

## The method

### The element schema

Every formatter node is an object shaped like this (all but `elmType` optional):

```json
{
  "elmType": "div",
  "txtContent": "@currentField",
  "style":      { "css-property": "value-or-expression" },
  "attributes": { "class": "…", "iconName": "…", "href": "…", "target": "…" },
  "children":   [ /* nested element objects */ ],
  "customRowAction": { /* only on button/clickable elements */ }
}
```

Rules that bite:
- `txtContent` and `children` are mutually exclusive — **if `txtContent` is set, children
  are ignored.** A node either holds text or holds child nodes.
- The **root** of a *column* formatter is a single element object. The root of a *view*
  formatter is an object keyed by `rowFormatter` / `additionalRowClass` / `formatter`.
- Always emit the `$schema` line first — it's what turns on Monaco autocomplete/validation
  in the format pane and documents the target version:
  - Column (current, SP Online / SE 22H2+): `https://developer.microsoft.com/json-schemas/sp/v2/column-formatting.schema.json`
  - View: `https://developer.microsoft.com/json-schemas/sp/view-formatting.schema.json`
  - SharePoint 2019 / pre-22H2 column: the `v1/column-formatting.schema.json` variant.

### Expression syntax — two flavors

The same computation can be written two ways. Both evaluate per row.

**Excel-style** (SP Online & SE 22H2+): a string beginning with `=`. Readable, nestable.

```
"=if([$Sentiment] <= 0.3, 'sp-field-severity--blocked', if([$Sentiment] < 0.9, 'sp-field-severity--warning', 'sp-field-severity--good'))"
```

**Abstract-Object (AST)**: an `{ "operator": …, "operands": [ … ] }` object. Verbose but
works on **SharePoint 2019** too, where Excel-style is unavailable.

```json
{ "operator": "?",
  "operands": [
    { "operator": ">", "operands": ["@currentField", 40] },
    "100%",
    { "operator": "+", "operands": [
      { "operator": "toString()", "operands": [{ "operator": "*", "operands": ["@currentField", 2.5] }] },
      "%" ] }
  ] }
```

Operators available include arithmetic/comparison (`+ - * / % < > <= >= == != && ||`),
the ternary pair `? :`, and functions `if`, `toString()`, `Number()`, `Date()`,
`toLocaleString()`, `toLocaleDateString()`, `substring`, `indexOf`, `length`, `join`,
`toLowerCase`/`toUpperCase`, `floor`/`ceiling`/`abs`/`pow`, `startsWith`/`endsWith`,
`replace`/`replaceAll`, `getThumbnailImage`, `getUserImage`, `addDays`/`addMinutes`.
Prefer Excel-style unless you must support SP 2019.

**Field & context tokens.** `@currentField` (this column), `@currentField.title`/`.email`
(person), `.lookupValue` (lookup), `.desc` (hyperlink text), `.displayValue`
(locale-formatted). `[$InternalName]` = another field this row; `[!InternalName]` =
field metadata (`[!Status.DisplayName]`). `@me` = current user's email, `@now` = current
datetime, `@rowIndex` = 0-based render position, `@currentWeb` = site URL,
`@window.innerWidth`, `@lcid`, `@isSelected`, `@thumbnail.<size>`.

### Pattern catalog

- **Status pill / badge** — a colored `div` (predefined severity class) with an optional
  Fluent `iconName` span, mapping choice values to colors.
- **Conditional background color** — `style.background-color` driven by an `=if`.
- **Data bar** — a `div` whose `width` is a percentage expression of the number; class
  `sp-field-dataBars` gives the bar chrome.
- **Icon by value** — a `span` with `attributes.iconName` chosen per value (Fluent icon).
- **Clickable hyperlink / mailto** — an `a` with `href` (only `http(s)://`, `mailto:`,
  `tel:` allowed; add `data-interception:"on"` to stay in-tab).
- **Action button** — a `button` with `customRowAction` (`defaultClick`, `share`,
  `editProps`, `setValue`, `executeFlow`, …).
- **Date-relative coloring** — compare `[$DueDate]` against `@now` (millisecond math).
- **View: whole-row tint** — `additionalRowClass` on the view schema.
- **View: custom card** — a `rowFormatter` (List) or `formatter` (Gallery/Board) tree.

---

## Worked examples

### 1. Status pill (choice column → colored badge with icon)

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/sp/v2/column-formatting.schema.json",
  "elmType": "div",
  "attributes": {
    "class": "=if(@currentField == 'Done', 'sp-field-severity--good', if(@currentField == 'In Review', 'sp-field-severity--warning', if(@currentField == 'Blocked', 'sp-field-severity--blocked', 'sp-field-severity--low'))) + ' ms-fontColor-neutralSecondary'"
  },
  "children": [
    {
      "elmType": "span",
      "style": { "display": "inline-block", "padding": "0 4px" },
      "attributes": {
        "iconName": "=if(@currentField == 'Done', 'CheckMark', if(@currentField == 'Blocked', 'ErrorBadge', 'Info'))"
      }
    },
    { "elmType": "span", "txtContent": "@currentField" }
  ]
}
```

The `sp-field-severity--*` classes supply only the background color — the icon comes from
the `iconName` attribute (a Fluent UI icon name), not from the class.

### 2. Conditional background color (number threshold)

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/sp/v2/column-formatting.schema.json",
  "elmType": "div",
  "txtContent": "@currentField",
  "style": {
    "padding": "4px 8px",
    "background-color": "=if(@currentField < 40, '#ffdddd', if(@currentField < 70, '#fff4ce', '#dff6dd'))"
  }
}
```

### 3. Data bar (number as a proportional bar)

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/sp/v2/column-formatting.schema.json",
  "elmType": "div",
  "txtContent": "@currentField",
  "attributes": { "class": "sp-field-dataBars" },
  "style": {
    "padding": "0 2px",
    "width": "=if(@currentField > 20, '100%', (@currentField * 5) + '%')",
    "box-sizing": "border-box"
  }
}
```

`20` is the assumed max value and `* 5` scales it to fill the cell at that max — adjust
both to your data's range. `width` clamps to `100%` above the ceiling.

### 4. Icon by value (trending indicator comparing two fields)

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/sp/v2/column-formatting.schema.json",
  "elmType": "div",
  "children": [
    {
      "elmType": "span",
      "attributes": {
        "iconName": "=if([$After] > [$Before], 'StockUp', if([$After] < [$Before], 'StockDown', 'Forward'))",
        "class":    "=if([$After] > [$Before], 'sp-field-trending--up', if([$After] < [$Before], 'sp-field-trending--down', ''))"
      }
    },
    { "elmType": "span", "txtContent": "@currentField" }
  ]
}
```

### 5. Clickable hyperlink and mailto quick-action

Turn a text field into a link (here a stock ticker → Yahoo Finance):

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/sp/v2/column-formatting.schema.json",
  "elmType": "a",
  "txtContent": "@currentField",
  "attributes": {
    "target": "_blank",
    "href": "='https://finance.yahoo.com/quote/' + @currentField"
  }
}
```

A person column with a mail button beside the name (`@currentField` is the person object):

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/sp/v2/column-formatting.schema.json",
  "elmType": "div",
  "children": [
    { "elmType": "span", "txtContent": "@currentField.title" },
    {
      "elmType": "a",
      "attributes": {
        "class": "sp-field-quickActions",
        "iconName": "Mail",
        "title": "Email this person",
        "href": "='mailto:' + @currentField.email + '?subject=Re: ' + [$Title]"
      }
    }
  ]
}
```

Only `http://`, `https://`, `mailto:`, and `tel:` are permitted in `href`.

### 6a. Button — default click (open the item)

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/sp/v2/column-formatting.schema.json",
  "elmType": "button",
  "txtContent": "Open",
  "customRowAction": { "action": "defaultClick" }
}
```

`action` may also be `share`, `delete`, `editProps`, `openContextMenu`, or `setValue`
(the last writes field values in place via an `actionInput` map).

### 6b. Button — launch a Power Automate Flow

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/sp/v2/column-formatting.schema.json",
  "elmType": "button",
  "txtContent": "Request approval",
  "customRowAction": {
    "action": "executeFlow",
    "actionParams": "{\"id\": \"edf627d9-20f4-45ba-8bc9-4494bf2ff1be\", \"headerText\": \"Send for approval\", \"runFlowButtonText\": \"Run now\"}"
  }
}
```

`actionParams` is a **JSON string** (note the escaped quotes), not a nested object. `id`
is the Flow's identifier (Flow → See your flows → Export → Get flow identifier); only
`id` is required, `headerText`/`runFlowButtonText` customize the launch panel.

### 7. Date-relative coloring (overdue → red)

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/sp/v2/column-formatting.schema.json",
  "elmType": "div",
  "txtContent": "@currentField",
  "style": {
    "color": "=if([$DueDate] <= @now, '#a4262c', if([$DueDate] <= @now + 86400000, '#c19c00', ''))"
  }
}
```

Dates are milliseconds since epoch, so "within 24h" is `@now + 86400000`. To compare
against a fixed date, wrap a string in `Date('3/22/2027')`.

### 8. View formatting — tint the whole row by status

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/sp/view-formatting.schema.json",
  "additionalRowClass": "=if([$Status] == 'Blocked', 'sp-field-severity--blocked', if([$Status] == 'In Review', 'sp-field-severity--warning', if([$DueDate] <= @now, 'sp-field-severity--severeWarning', '')))"
}
```

`additionalRowClass` tints the row **and leaves individual column formatting intact** —
the two compose. Note this is *view* schema and it references `[$Status]` directly, not
`@currentField` (which resolves to Title in a view context — see Watch Out).

### 9. View formatting — a custom card (Gallery/tile layout)

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/sp/view-formatting.schema.json",
  "formatter": {
    "elmType": "div",
    "style": { "display": "flex", "flex-direction": "column", "padding": "12px", "border-radius": "6px", "box-shadow": "0 1.6px 3.6px rgba(0,0,0,0.13)" },
    "children": [
      { "elmType": "div", "txtContent": "[$Title]", "style": { "font-size": "16px", "font-weight": "600" } },
      { "elmType": "div", "txtContent": "[$Assigned_x0020_To.title]", "style": { "color": "#605e5c", "font-size": "12px" } },
      {
        "elmType": "div",
        "txtContent": "[$Status]",
        "attributes": { "class": "=if([$Status] == 'Done', 'sp-field-severity--good', 'sp-field-severity--warning')" },
        "style": { "margin-top": "8px", "padding": "2px 8px", "align-self": "flex-start", "border-radius": "10px" }
      }
    ]
  }
}
```

For a **List** layout instead of Gallery, put the same tree under `rowFormatter` (which
totally overrides row rendering) rather than `formatter`. `rowFormatter` and
`additionalRowClass` are mutually exclusive — a `rowFormatter` makes `additionalRowClass`
ignored.

Note the internal name `Assigned_x0020_To`: the space in "Assigned To" is encoded as
`_x0020_` (see the gotcha).

---

## `@currentField` vs `[$InternalName]` — and the internal-name gotcha

- **`@currentField`** = the value of the column this formatter is attached to. Use it in
  *column* formatting. Inside a **view** `rowFormatter`/`formatter`, `@currentField`
  **always resolves to the Title field** regardless of layout — so in view formatters
  always name fields explicitly with `[$InternalName]`.
- **`[$InternalName]`** = another field in the same row, by its **internal name**. This
  is the single most common source of "my formatter shows blank." The internal name is
  *not* the display name you see in the UI:
  - A column created as "Due Date" often has internal name `DueDate` or `Due_x0020_Date`.
  - **Spaces and specials are encoded**: space → `_x0020_`, so "Assigned To" →
    `Assigned_x0020_To`.
  - Renaming a column changes the display name but **not** the internal name.
  - Find it: open the column/list settings and read the `Field=` value in the settings
    URL, or check the list in **Site contents → Settings**. When in doubt, use `[!Field]`
    tooling or ask the user to confirm the internal name.
- The referenced field must be **present in the current view**, or the reference yields
  nothing — even if it exists on the list.

---

## Watch Out

- **`@currentField` becomes Title in view formatters.** Copying a column formatter into a
  `rowFormatter` and expecting `@currentField` to mean the status field is the classic
  trap. Rewrite every `@currentField` as `[$InternalName]` when moving to view scope.
- **Internal name ≠ display name.** `[$Due Date]` is invalid; it's `[$DueDate]` or
  `[$Due_x0020_Date]`. Silent blank output almost always means a wrong internal name or a
  field not in the view.
- **`actionParams` is an escaped JSON string, not an object.** `executeFlow` fails
  silently if you pass a nested object. The value must be a string with escaped quotes.
- **Attribute and elmType whitelists are hard walls.** An `onclick`, an `<input>`, a
  `<style>` element, or a stray attribute name doesn't degrade — it errors and the
  formatter won't save. Do interactivity through `customRowAction`, not script.
- **External images and embeds are blocked by default.** `img src` is allowed only from
  the tenant domain and a few Microsoft CDNs (`cdn.office.net`, `akamaihd.net`,
  `static2.sharepointonline.com`); other domains need a site-level allow-list setting.

---

## Debugging

- **Add `"debugMode": true`** at the formatter root — it logs warnings and evaluation
  errors to the browser console.
- **Blank / unstyled output** → almost always a bad `[$InternalName]` or a field missing
  from the view. Verify the internal name and add the field to the view.
- **Won't save / red squiggles** → schema violation: an illegal `elmType`, a non-whitelisted
  attribute, `txtContent` set alongside `children`, or malformed JSON. The Monaco editor in
  the format pane flags the line; `Ctrl+Space` gives valid completions.
- **Expression evaluates to the wrong branch** → check types. Comparisons on number
  columns need numeric operands; wrap with `Number(@currentField)` if a value arrives as
  text. Dates compare as milliseconds — don't compare a date to a bare string.
- **Iterate in the pane, not in prod.** Use **Preview** before **Save**; a saved formatter
  applies for everyone who views the list.
- **Start from a working sample.** The PnP `sp-dev-column-formatting` /
  `sp-dev-list-formatting` galleries and the PnP List Formatting helper tool
  (HTML/CSS → formatter JSON) are faster than authoring blind.

---

## Out of scope — hand off to a sibling skill

- **Designing the list's columns and data model** — column types, choices, lookups,
  indexing, content types, whether a field should even exist → **sharepoint-list-architecture**.
  This skill styles fields that already exist; it does not design them.
- **HTML rendered inside a Power App** (the canvas **HtmlText** control) — that's HTML in
  a *different* runtime with different rules → **power-apps-components**. Column formatting
  JSON does not run in a Power App.
- **Changing formatting or list data programmatically** — setting a view's
  `CustomFormatter` via API, bulk-updating items, provisioning → **graph-api-integration**
  (or the SharePoint REST/PnP APIs). This skill produces the JSON; pushing it via code is
  that skill's job.
- **Power Automate flow *authoring*** — this skill only wires a *button* to an existing
  Flow by ID; building the Flow itself is out of scope.
