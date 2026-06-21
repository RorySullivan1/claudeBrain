# 2026-06-21 15:00 · vba-skill-family

**Goal:** Author VBA skill family (development/review/maintenance/distribution)

## What happened
- Added four worked-example skills under `example-project/.claude/skills/`:
  `vba-development`, `vba-review`, `vba-maintenance`, `vba-distribution`.
- Distilled them from the existing `context/vba-development.md` brief; matched
  the VSTO family's shape (clarify-first table → standards → recipes → "Watch Out";
  review uses severity-ordered Critical/Important/Minor).
- Cross-linked descriptions: siblings defer to each other, and to VSTO-development
  for C#/VB.NET so the two Office stacks don't trigger-collide.
- Regenerated `CATALOG.md` via `catalog.py`. Left `CLAUDE.md` untouched
  (its convention: don't enumerate assets, the catalog is the single source).
- Committed + pushed to branch `claude/vba-skills-jlhcsr`. No PR (not requested).

## Gotchas & dead ends
- None. Pattern was unambiguous once the VSTO family was read as the template.

## State at end
- Four VBA skills live and catalogued. Branch pushed, no PR opened yet.

## Open threads
- Offered (not yet done): open a PR; add a VBA developer *agent* that orchestrates
  these skills (à la finance-quantitative-developer). Awaiting user.
