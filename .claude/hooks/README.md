# hooks/

**Lifecycle enforcement layer.** Deterministic shell scripts the harness runs on
events — the model cannot skip them. This is the floor underneath the whole prompt
stack. Use hooks for anything that must *always* execute.

## Format

- One executable script per hook (`.sh`, or any interpreter via shebang).
- Wired up in `../settings.json` under the `hooks` key, keyed by event
  (`PreToolUse`, `PostToolUse`, `SessionStart`, `Stop`, …) with an optional matcher.
- A `PreToolUse` hook that exits non-zero **vetoes** the tool call.

## Typical uses

- `PreToolUse` → block writes to protected paths/endpoints.
- `PostToolUse` → auto-format edited files (e.g. `black` + `flake8`).
- `SessionStart` → warm caches, refresh tokens.
- `PreToolUse` → guard branch names / reject commits to `main`.

## Status

**Empty scaffold.** No hooks defined yet. Add a script here and register it in
`settings.json` when a need appears.
