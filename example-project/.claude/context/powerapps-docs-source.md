# powerapps-docs — the authoritative control & layout source

`github.com/MicrosoftDocs/powerapps-docs` (branch `main`) is the **source markdown** behind
`learn.microsoft.com/power-apps`. It is the most comprehensive, greppable reference for what
canvas-app **controls, layouts and properties do**. Consult it whenever grounding a control's
semantics, a layout behaviour, or the meaning of a property.

## How to read it — fetch on demand, no clone

- **Rendered + searchable (fastest first stop):** the Microsoft Learn MCP server, where
  connected — `microsoft_docs_search` then `microsoft_docs_fetch`. Same content, chunked
  for search.
- **Raw source file (WebFetch):**
  `https://raw.githubusercontent.com/MicrosoftDocs/powerapps-docs/main/<path>`
- **Browse / list a folder:** `gh api repos/MicrosoftDocs/powerapps-docs/contents/<path>` —
  list a folder, then fetch the `control-*.md` you need. This is how you grep the whole
  control set.

## The paths that matter

The docs root is the `powerapps-docs/` folder inside the repo. Canvas-app material:

- **Classic controls** — `powerapps-docs/maker/canvas-apps/controls/control-*.md`
  (~50 files: `control-button.md`, `control-combo-box.md`, `control-grid-container.md`, …)
- **Modern (Fluent) controls** — `.../controls/modern-controls/modern-control-*.md`
- **All-properties reference** — `.../controls/reference-properties.md`
- **Layout / responsive** — `.../canvas-apps/create-responsive-layout.md`,
  `.../canvas-apps/build-responsive-apps.md`
- **Scale / performance** — `.../canvas-apps/working-with-large-apps.md`

## What it grounds — and the hard limit (READ THIS)

These docs ground **semantics and DISPLAY-property names**: what a control is, what it does,
what a property means. They do **NOT** give the pa-yaml `Control:` token, its `@version`, the
`Variant:` string, or the property TOKENS — the dialect renames on the way into code view (the
container's "Gap" → `LayoutGap`, "Direction" → `LayoutDirection`). So this source answers
*"what is this control and what are its properties?"*; the exact pasteable token still comes
from a **Studio code-view sample**, per the air-gap model. **Ground meaning here; ground tokens
against the project's enum catalogue** (e.g. `tools/studio-enums.json`).

One more calibration, learned in the field: **an omission in these docs means UNCONFIRMED, not
unsupported.** Per-property "Applies to" lists are incomplete — a property absent from a
control's list has been observed working (e.g. `HoverFill` on the classic Icon). Absence is a
reason to probe, never a reason to declare a token impossible.

## Relation to the other sources

- The project's **enum catalogue** (e.g. `tools/studio-enums.json`) — the grounded pa-yaml
  tokens, with Studio code-view / photo provenance. Authoritative for *what to type*.
- The **`powerapp-canvas-*` skills** — the distilled behaviour and dialect rules.
- This repo (powerapps-docs) — the **meaning** layer: control catalogue, property semantics,
  layout behaviour.
