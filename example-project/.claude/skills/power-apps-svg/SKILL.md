---
name: power-apps-svg
description: >
  Expert at rendering dynamic SVG inside a canvas Power App — vector charts, KPI rings,
  gauges, progress bars, sparklines, badges, and custom icons drawn with Power Fx and
  shown in an Image control via a data URI. Use this skill whenever the user wants a
  chart or visual that native controls and Power BI don't give them: "progress ring",
  "donut/gauge in Power Apps", "draw a chart without Power BI", "custom icon that changes
  colour by value", "SVG in Power Apps", "data:image/svg+xml", "EncodeUrl an SVG",
  "thermometer/battery indicator", "spark line in a gallery", or a KPI visual for users
  who have no Power BI licence. Trigger on implicit signals too: someone building native
  dashboard visuals, a status indicator that must scale crisply, or a gallery cell that
  needs a tiny inline chart. Boundary: this skill owns SVG rendered *in the app* through
  the Image control's data URI. Rich HTML text/tables/badges via the HtmlText control are
  power-apps-components; declarative JSON that styles a SharePoint *list cell/view* is
  sharepoint-column-formatting; the Power Fx data/aggregation feeding the visual is
  power-fx-development; DAX/Power BI visuals are power-bi-dax. This skill is the in-app
  vector-graphics layer only.
---

# Power Apps SVG Skill

You draw vector graphics inside a canvas app by building an **SVG string in Power Fx** and
handing it to an **Image control** as a **data URI**. This is the escape hatch for visuals the
platform doesn't ship — progress rings, gauges, thermometers, sparklines, value-driven icons —
with **no image assets, no PCF, and no Power BI licence**. Lead with the smallest SVG that
works, keep the *data* math in Power Fx (not baked into the string), and always encode.

Grounded on Microsoft Learn: the Image control's `Image` property **accepts the data URI
scheme** (official — *Data types → Text, Hyperlink, Image, and Media*); `EncodeUrl` is the
documented URL encoder; image/URI strings have **no preset length limit**.

## Core principles

1. **Two encodings — pick by whether it's dynamic.**
   - **Dynamic (interpolate Power Fx):** `"data:image/svg+xml," & EncodeUrl("<svg …>" & value & "…</svg>")`.
     `EncodeUrl` makes the raw SVG safe in a URI, and because you concatenate Power Fx into the
     string, the picture reacts to data. **This is the workhorse.**
   - **Static:** `"data:image/svg+xml;base64," & <base64>` — fine for a fixed logo/icon, but you
     can't easily interpolate values, so don't use it for anything that changes.
2. **Keep the data in Power Fx, the shape in SVG.** Compute the percentage / colour / count as a
   variable, then drop it into the SVG. Don't encode business logic inside the markup.
3. **Always encode.** Wrap the whole SVG in `EncodeUrl`. Wrap any *user/data-sourced text* you
   place inside the SVG in `EncodeHTML` first — a stray `<` or `&` breaks the XML (and is an
   injection vector).
4. **Set `width`, `height`, and `viewBox`** on the `<svg>` so it scales predictably; set the
   Image control's `ImagePosition = Fit`. Avoid embedded `<style>`/classes — use inline
   `style=`/attributes (embedded styles can leak between SVGs).
5. **Vector, not raster.** SVG scales crisply at any DPI and is tiny — prefer it over PNG icons
   for anything that must recolour or resize by state.

## When to reach for this (and when not)

| Want | Use |
|---|---|
| A ring/gauge/bar/sparkline/thermometer, or an icon that recolours by value | **this skill** (SVG in Image) |
| A formatted table / badge / rich text block | `power-apps-components` (HtmlText) |
| A colour pill on a SharePoint **list** column/view | `sharepoint-column-formatting` |
| A real analytical chart over the whole dataset | `power-bi-dax` (Power BI) |

## The method

1. **State the inputs** — the value(s) the visual encodes (a percent, a count, a status) and
   where they come from (a named formula / variable). Compute them in Power Fx first.
2. **Build the SVG string** — smallest markup that draws it; parameterise only what changes.
3. **Encode + assign** — `Image = "data:image/svg+xml," & EncodeUrl(<string>)`.
4. **Verify at two states** — e.g. 0% and 100%, and an empty/blank value — so the guard math is
   right (division by zero, negative, over-100 clamp).

## Worked examples

### 1. Progress ring / donut (the canonical `stroke-dasharray` trick)

A percent-complete ring whose fill and colour react to a value. `pct` is any Power Fx number
0–100 (clamp it):

```power
With(
    { pct: Min(100, Max(0, RoundDown(ThisItem.PercentComplete, 0))),
      col: If(ThisItem.PercentComplete >= 100, "#107C10",
              If(ThisItem.PercentComplete >= 50, "#986F0B", "#C42B1C")) },
    "data:image/svg+xml," & EncodeUrl(
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 36 36'>" &
        "<circle cx='18' cy='18' r='15.9155' fill='none' stroke='#EDEBE9' stroke-width='3'/>" &
        "<circle cx='18' cy='18' r='15.9155' fill='none' stroke='" & col & "' stroke-width='3'" &
        " stroke-dasharray='" & pct & " " & (100 - pct) & "' stroke-dashoffset='25'" &
        " stroke-linecap='round' transform='rotate(-90 18 18)'/>" &
        "<text x='18' y='20.5' text-anchor='middle' font-size='8' fill='#201F1E'>" & pct & "%</text>" &
        "</svg>")
)
```

The whole ring is one `stroke-dasharray='<pct> <100-pct>'` on a circle of circumference ≈100
(`r=15.9155`). Colour comes from Power Fx, so the same control is a red/amber/green health ring.

### 2. Horizontal KPI bar (delegation-safe count → width)

For a status bar where the *number* comes from a **delegable-filtered, bounded** collection
(compute the count locally — `CountRows` doesn't delegate to SharePoint; filter server-side to a
small set first, then count in memory):

```power
With(
    { done: CountRows(Filter(colMyTasks, Status.Value = "Done")),
      total: Max(1, CountRows(colMyTasks)) },
    "data:image/svg+xml," & EncodeUrl(
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 12'>" &
        "<rect x='0' y='0' width='100' height='12' rx='6' fill='#EDEBE9'/>" &
        "<rect x='0' y='0' width='" & (done / total * 100) & "' height='12' rx='6' fill='#0F6CBD'/>" &
        "</svg>")
)
```

### 3. Value-driven icon colour

A dot that recolours by status (encode any data-sourced label with `EncodeHTML`):

```power
"data:image/svg+xml," & EncodeUrl(
    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 8 8'><circle cx='4' cy='4' r='4' fill='" &
    Switch(ThisItem.Health, "Green","#107C10","Amber","#986F0B","Red","#C42B1C","#605E5C") & "'/></svg>")
```

## Watch Out

1. **Forgetting `EncodeUrl` (or `xmlns`).** Without `EncodeUrl` the URI breaks on `#`, `<`,
   spaces; without `xmlns='http://www.w3.org/2000/svg'` the SVG may not render at all.
2. **Unclamped math.** A percent over 100 or a divide-by-zero produces a garbage ring. Clamp
   with `Min/Max` and guard denominators with `Max(1, …)`.
3. **Injecting raw data text.** Any `Title`/label you drop into the SVG must be `EncodeHTML`'d —
   a `<` or `&` from data corrupts the markup.
4. **Over-heavy SVG in a big gallery.** There's no length limit, but hundreds of complex SVGs
   still cost render time. Keep per-row SVGs small; reserve elaborate ones for single controls.
5. **Embedded `<style>`/classes.** They can leak across SVGs on a screen — use inline `style=`
   and attributes.
6. **It's a picture, not a control.** An Image can't take focus or fire per-element clicks. For
   interactivity, overlay a transparent Button, don't put handlers in the SVG.

## Out of scope — defer

- **The Power Fx that computes the value** (filters, delegable counts, aggregation) →
  `power-fx-development` (and `power-fx-review` to audit it).
- **HtmlText tables/badges/rich text** and **reusable components / responsive layout** →
  `power-apps-components`.
- **SharePoint list-cell/view formatting JSON** → `sharepoint-column-formatting`.
- **Real analytical charts over the whole dataset** → `power-bi-dax` (Power BI). This skill is
  the native, licence-free visual layer — useful precisely where Power BI isn't available.
