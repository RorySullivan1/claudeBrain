# 2026-06-21 13:20 · readme-architecture-update

**Goal:** Update root + consumer READMEs for new architecture (capabilities + catalog)

## What happened
- Root `README.md`: added "What the example demonstrates" (objective agent family +
  branding→presentation pipeline + operational infra) and "Discovering capabilities (the
  catalog)" (auto-load by description; `.claude/CATALOG.md` via catalog.py; `/reindex`).
- `example-project/.claude/README.md`: added CATALOG.md to Supporting files; rewrote the stale
  Status section (had claimed commands/agents/workflows were empty scaffolds + "11 domain
  bundles" — all seven layers now populated). Points to CATALOG.md for the current per-layer list.
- Docs-only; READMEs are excluded from the catalog scan so CATALOG.md unaffected. PR #20.

## Gotchas & dead ends
- "the README" was ambiguous (root vs consumer .claude/README); updated both since both were
  architecture-relevant and the consumer one was stale.

## State at end
- Committed + pushed to `claude/readme-architecture-update`; PR #20 open. (PRs #19 catalog, #17/#18
  presentation already merged or open.)

## Open threads
- PR #19 (capability catalog) and PR #20 (readme) open, not yet merged.
