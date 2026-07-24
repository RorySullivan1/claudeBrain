# 2026-07-24 13:38 · power-platform-skill-family

**Goal:** Add SharePoint + Power Fx + Graph skill family to example-project

## What happened
- Added `vba-addin-building` skill (uploaded) → example-project/.claude/skills/; PR #27 (branch claude/laughing-ride-pyhmzj).
- Then built a **Power Platform skill family** (8 skills) for a PowerApp + Power BI + SharePoint-lists-backend stack, modeled on the VBA family's decomposition. Clustered so each can later become its own plugin ("separate plugins by use case" per user):
  - **Power Apps/Fx:** `power-fx-development` (+ `delegation.md` sidecar), `power-apps-components` (incl. HtmlText), `power-fx-review`.
  - **SharePoint backend:** `sharepoint-list-architecture`, `sharepoint-column-formatting` (HTML-in-JSON).
  - **Graph:** `graph-api-integration` (+ `endpoints.md` sidecar).
  - **Power BI:** `power-bi-dax`, `power-query-m`.
- User decisions (AskUserQuestion): HTML surfaces = SharePoint formatting JSON + Power Apps HtmlText; Power BI = full skills; breadth = full family now.
- Authored via 8 parallel general-purpose agents (one per skill), each told to mirror the closest VBA exemplar + ground facts against Microsoft Learn MCP.
- Ran an independent **doc-verification pass**: pulled ground truth from Microsoft Learn (saved to scratchpad/ground-truth.md) and grep-checked every high-risk number/API against the drafts. All correct: 500/2000 delegation limit, 5,000 list-view threshold, 30M list capacity, 12-join lookup limit, 20,000 index limit, Sites.Read/ReadWrite/Selected/FullControl tiers, 20-request $batch cap, column-formatting v2 schema + customRowAction set, SharePoint.Tables site-URL/Implementation 2.0/partial folding.
- Regenerated example-project CATALOG.md (now lists all 8).

## Gotchas & dead ends
- `catalog.py` resolves its tree from `$CLAUDE_PROJECT_DIR` (fallback cwd). Running it from repo root regenerated the **factory** CATALOG (no-op), NOT example-project's. Must run `CLAUDE_PROJECT_DIR=.../example-project python .../catalog.py` to update example-project's catalog.
- Sidecars chosen over separate context/notes so each skill stays self-contained/portable (matters for the future per-use-case plugin split).

## State at end
- 8 skill dirs + example-project CATALOG.md staged/committed on branch claude/laughing-ride-pyhmzj (same branch as PR #27 → stacks on it; flagged to user, offered to split).
- All facts verified against live Microsoft Learn docs.

## Open threads
- Branch/PR placement: user interrupted the "new branch vs stack on PR #27" question. Landed on designated branch per standing instruction; may want a separate PR.
- Power BI cluster is only 2 skills (dax, query-m); no power-bi-modeling/report-design skill yet if deeper coverage wanted.
- Future: split the family into per-use-case plugins (`.claude-plugin/plugin.json` + marketplace).
