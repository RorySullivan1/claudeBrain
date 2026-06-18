# 2026-06-18 22:00 · single-source-operational-assets

**Goal:** Symlink operational assets to one canonical copy in example-project; kill factory/consumer drift

## What happened
- Third efficiency review, lens = factory↔consumer duplication. Three Explore agents
  mapped it. Smoking gun: `example-project`'s `memory.py` was **stale** — never got the
  PR #7 per-session Stop-hook dedupe. The showcase was shipping an inferior copy.
- Fix (user chose "symlink to one copy"): canonical copy of each drift-prone operational
  asset now lives in `example-project/.claude/` (already "the thing you copy"); the
  factory `.claude/` holds **9 relative symlinks** into it:
  - dirs: `skills/session-memory`, `skills/agent-finder`
  - files: `hooks/build-hooks.py` + the 6 shared `*.json` fragments
- First synced the canonical `example-project` `memory.py` to the factory's good version
  (so the surviving copy is the correct one), THEN symlinked.
- Docs: recorded the single-source rule in `CLAUDE.md` (Conventions), `.claude/skills/README.md`
  (operational-skills section), `.claude/hooks/README.md`.

## Gotchas & dead ends
- Why symlinks are safe: every script resolves paths from `${CLAUDE_PROJECT_DIR}`, not
  its own location — so the factory's hooks run the example-project script body but
  operate on the FACTORY's `.claude/hooks/` + `.claude/memory/` (CLAUDE_PROJECT_DIR=repo
  root). Verified `build-hooks.py --check`, `memory.py stop-hook` dedupe, `agents.py list`
  all work through the symlinks; `settings.json` unchanged.
- Liftability preserved: nothing under `example-project/` is a symlink, so `cp -rL`
  (or any copy) of a module yields real, self-contained files. Verified.
- Direction matters: real files MUST be in example-project (the lifted side); factory
  symlinks point inward. Symlinking the other way would hand consumers dangling links.
- NOT symlinked (correctly divergent by role): `settings.json` (broad vs minimal perms),
  per-layer `README.md`s (authoring vs usage), `.claude/memory/` (factory's own log).
- Windows caveat: cloning the FACTORY repo on Windows needs core.symlinks; consumers are
  unaffected (they get real files).

## State at end
- Branch `claude/optimize-factory-model` (PR #8). Symlinks committed; runtime verified.
- Operational assets now single-sourced; editing one place is impossible to drift.

## Open threads
- Planned meta-skills unwritten: `skill-authoring`, `context-vs-skill`.
- Planned commands: `/validate-asset`, `/add-context`.
