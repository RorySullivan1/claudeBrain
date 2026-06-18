# 2026-06-18 22:39 · token-economy-tooling

**Goal:** Add token-optimizer skill + token-manager agent + Bash/Read guard hooks (context economy)

## What happened
- Incorporated 5 uploaded files as a context/token-economy capability, following the
  single-source pattern (canonical in example-project, symlinks in factory):
  - `token-optimizer` skill (+ `scripts/tokens.py` estimator) — the placement judgment layer.
  - `token-manager` agent — verbose work in isolation, returns a capped summary.
  - `post_bash_filter.py` (PostToolUse·Bash) — ANSI-strip + head/tail elide long output.
  - `pre_read_guard.py` (PreToolUse·Read) — cap an unpaged slurp of a huge file.
- 6 factory symlinks; 2 new hook fragments wired; rebuilt BOTH settings.json (9 fragments,
  now incl. PreToolUse). This is the first operational AGENT (token-manager) and first
  PreToolUse hook in the repo.
- Verified all three scripts via their stdin protocols (long→elide, short→passthrough,
  huge→cap-1500, explicit offset/limit→respected, small→noop); build-hooks --check green both trees.
- Docs: factory skills/README (token-optimizer), factory agents/README (new "Operational
  agents (exceptions)" section for token-manager), factory hooks/README (guard hooks),
  example agents/README + example CLAUDE.md (skill + agent).

## Gotchas & dead ends
- Unlike the knowledge-router upload, this bundle was internally consistent — all references
  (token-manager, Explore, session-memory, the two hooks) exist or are included, so NO
  taxonomy rewrites were needed. Only cosmetic change: SKILL.md `python3`→`python` examples
  to match repo convention (script shebangs kept as python3).
- Mid-implementation the harness briefly toggled plan mode; captured progress in the plan
  file, then continued on exit.
- Guard hooks fail safe (emit nothing on error/short output), so enabling them by default in
  both trees is safe. token-manager has Bash + WebFetch/WebSearch; left frontmatter as
  uploaded (model: inherit, maxTurns 20) — reasonable for a read-mostly worker.

## State at end
- Branch `claude/token-economy-tooling` off merged main (PRs #8/#9/#10 in). Not stacked.
- Committed + pushed; PR opened against main (see chat).

## Open threads
- Planned meta-skills unwritten: `skill-authoring`, `context-vs-skill`.
- Factory's own `.claude/agents/` now has one operational symlink (token-manager); still no
  authoring agents (`draft-skill`/`asset-auditor` remain ideas).
