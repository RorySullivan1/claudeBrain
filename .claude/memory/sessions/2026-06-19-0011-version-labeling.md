# 2026-06-19 00:11 · version-labeling

**Goal:** Add version-labeling flow: ship-version workflow + version-set/ship commands + .meta/version guard hook

## What happened
- Built a 3-layer version-labeling flow (user named "workflow/command/hook"), single-sourced
  (canonical in example-project, factory symlinks):
  - `workflows/ship-version.md` — orchestrates define → work → ship.
  - `commands/version-set.md` — write/update `.meta/version` (semver label + Goals/Objectives).
  - `commands/version-ship.md` — derive branch + PR title/body from the goals, commit, push,
    open PR via `mcp__github__create_pull_request`, record PR URL back into `.meta/version`.
  - `hooks/version_guard.py` + `pre-tool-use-version-guard.json` (PreToolUse·Bash).
- `.meta/version` lives at project root (sibling to `.claude/`), per-project runtime state like
  `.claude/memory/`. Committed a filled SAMPLE at `example-project/.meta/version` (showcase).
- Rebuilt both settings.json (11 fragments; PreToolUse now has Read-guard + Bash version-guard).
- Semver labeling (user choice); prospective (goals) vs memory's retrospective — no overlap.

## Gotchas & dead ends
- **Guard is opt-in BY PRESENCE + warn-only:** silent if `.meta/version` absent (so the factory's
  own pushes — repo root has no `.meta/version` — are never nagged); warns (allow +
  additionalContext, never blocks) only when the file exists but lacks a `version:` or any goal.
  Verified all 5 cases incl. fail-safe on malformed stdin. Tunable to hard `deny` later.
- First **single-sourced workflow + commands** (prior `author-asset`/`add-*` are factory-only
  real). example-project/.claude/{workflows,commands}/ already existed (READMEs); added canonical
  files + factory symlinks. Mirrors skills/ mixing real meta + symlinked operational.
- Commands are model-driven prose (read .meta/version, run git, call the MCP PR tool) — no script
  needed; only the guard hook has a script.
- This work itself was NOT shipped via the new flow (no factory .meta/version) — used the normal
  claude/<slug> branch; the flow is the deliverable + showcased in example-project.

## State at end
- Branch `claude/version-labeling` off merged main (#8–#12 in). Committed + pushed; PR opened.
- Asset taxonomy now exercises all layers: skills, agents, commands, workflows, hooks, context, memory.

## Open threads
- Planned meta-skills still unwritten: `skill-authoring`, `context-vs-skill`.
- Planned commands: `/validate-asset`, `/add-context`.
- version_guard ships warn-only; could offer a hard-deny variant if a project wants enforcement.
