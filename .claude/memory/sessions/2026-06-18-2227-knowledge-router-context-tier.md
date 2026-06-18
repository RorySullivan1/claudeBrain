# 2026-06-18 22:27 · knowledge-router-context-tier

**Goal:** Add knowledge-router skill + .claude/context/ reference-notes tier (model contextualization)

## What happened
- User uploaded 3 files (context.py, knowledge-router/SKILL.md, hooks.json) to add a
  durable reference-notes tier that complements session-memory. Incorporated as a new
  **operational skill** following the PR #9 single-source pattern.
- Canonical real files in `example-project/.claude/skills/knowledge-router/`
  (SKILL.md + scripts/context.py); factory `.claude/skills/knowledge-router` is a symlink.
- New `.claude/context/` reference-notes tier: `context.py` manages `INDEX.md` (auto
  catalog) + `notes/*.md` (on-demand). Coexists with the existing flat briefs — INDEX
  catalogs `notes/`, not the briefs.
- SessionStart wiring: added `cmd_index` to context.py (prints INDEX, mirrors memory.py);
  new exec-form `context-start.json` fragment (real in example-project, symlink in factory);
  rebuilt BOTH settings.json (now 7 fragments each).
- Seeded one showcase note (`notes/addin-tooling-data-flow.md`, system-map) so INDEX is
  non-empty and the hook surfaces real content.
- Docs: context/README (two tiers), `.claude/skills/README.md` (operational section),
  example-project/CLAUDE.md (skills + reference docs), factory CLAUDE.md (context prose).

## Gotchas & dead ends
- Two confirmed adaptations to the uploaded SKILL.md (it was written for a different
  setup): `skill-distiller` → `author-asset`/`/add-skill`; `.claude/rules/*.md` →
  `CLAUDE.md` or a context note (claudeBrain has no rules/ tier). Verified no
  skill-distiller / .claude/rules refs remain.
- Hook: rejected the uploaded shell-form `cat` hook (factory bans cat/$VAR as
  Windows-fragile) in favor of exec-form + `context.py index`.
- Two SessionStart fragments now concatenate (memory index + context index) — build-hooks
  merges per-event arrays; both print at start.

## State at end
- Branch `claude/knowledge-router-context-tier`, stacked on PR #9's branch
  (claude/single-source-operational-assets) so it inherits the symlink convention. PR #9
  still open — this PR's diff includes #9 until #9 merges; cleanest to merge #9 first.
- Verified: context.py list/index/reindex; build-hooks --check green both trees;
  liftability (cp -rL → real files); factory entries mode 120000.

## Open threads
- PR for this branch opened against main (see chat). Merge PR #9 first for a clean diff.
- Planned meta-skills unwritten: `skill-authoring`, `context-vs-skill`.
- Factory's own `.claude/context/` is still a stub (no notes yet); INDEX created on demand.
