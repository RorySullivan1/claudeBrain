# 2026-06-17 · hook-fragments

**Goal:** Store hooks as independent files instead of a growing inline block in
`settings.json`.

## What happened
- Adopted a **fragment + generator** model. Each hook is its own `*.json` in
  `.claude/hooks/` (`session-start`, `pre-compact`, `stop`, `user-prompt-submit`),
  a partial hooks object keyed by event. `build-hooks.py` merges all `*.json`
  fragments (filename order; same-event arrays concatenate) into the `hooks` block of
  `.claude/settings.json`. `--check` mode exits 1 if settings.json is stale.
- Fragments are the source of truth; `settings.json`'s hooks block is a generated
  artifact — don't hand-edit it. The hooks/README.md is the fragment index + rebuild
  instructions.
- Applied to both the factory and example-project (generator vendored into each, like
  `memory.py`; project root from `$CLAUDE_PROJECT_DIR`).

## Gotchas & dead ends
- **Claude Code cannot load hook definitions from external files** (verified via
  claude-code-guide against current docs): no `$include`/`$ref`/`extends`, no
  `settings.d`, and `.claude/hooks/*.json` is NOT auto-discovered. The `hooks` block
  must be inline in a settings file. So bare fragment files would be inert — hence the
  generator that compiles them into settings.json.
- The ONLY native way to keep hooks out of settings.json is a **plugin**
  (`hooks/hooks.json`), but that's a single file (not per-hook), adds plugin
  scaffolding + a marketplace entry, and needs a one-time `claude plugin install` per
  machine — friction vs. today's zero-setup committed settings. Rejected for that.
- Tradeoff accepted: settings.json is the same byte size (still holds the merged
  block), but it's no longer hand-maintained. "Don't hand-edit a big file," not
  "small file."

## State at end
- Hooks authored as fragments; `build-hooks.py --check` green in both projects.

## Open threads
- `settings.json` can drift if a fragment is edited without rerunning the generator.
  Mitigation exists (`--check`); could wire it as a PreToolUse guard or CI step later.
