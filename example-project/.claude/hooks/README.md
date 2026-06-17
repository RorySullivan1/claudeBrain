# hooks/

**Lifecycle enforcement layer.** Deterministic shell scripts the harness runs on
events — the model cannot skip them. This is the floor underneath the whole prompt
stack. Use hooks for anything that must *always* execute.

## Storage — one fragment file per hook (the source of truth)

Claude Code can't load hook definitions from external files; the `hooks` block must be
inline in `settings.json`. To keep that file from becoming a large hand-edited blob,
each hook is stored as its own small `*.json` **fragment** here, and `../settings.json`
is **generated** from them by `build-hooks.py`. Edit the fragments, then rebuild — never
hand-edit the generated `hooks` block.

A fragment is a partial hooks object keyed by event name. Use **exec-form**
(`command` + `args`) for cross-platform reliability:

```json
{ "SessionStart": [ { "matcher": "...", "hooks": [ { "type": "command", "command": "python", "args": [ "..." ] } ] } ] }
```

Every `*.json` here is a fragment (README and `build-hooks.py` are ignored); fragments
merge in filename order, same-event arrays concatenate.

### Rebuild after editing a fragment

```bash
python .claude/hooks/build-hooks.py          # regenerate ../settings.json
python .claude/hooks/build-hooks.py --check   # exit 1 if settings.json is stale
```

(`python3` on macOS/Linux.)

## Fragments in this project (memory lifecycle hooks)

These drive the `session-memory` skill (load / persist / recall):

| Fragment | Event | Subcommand |
|---|---|---|
| `session-start.json` | `SessionStart` | `index` — load `INDEX.md` into context |
| `pre-compact.json` | `PreCompact` | `precompact-hook` — persist reminder before compaction |
| `stop.json` | `Stop` | `stop-hook` — once-guarded end-of-session write reminder |
| `user-prompt-submit.json` | `UserPromptSubmit` | `prompt-hook` — recall on "continue"-style prompts |

To add a hook: drop a `<event>.json` fragment here and run `build-hooks.py`. A
`PreToolUse` fragment that exits non-zero **vetoes** the tool call.

## Self-maintaining (the drift guard)

Two fragments keep `settings.json` in sync automatically, so you rarely run the
generator by hand:

| Fragment | Event | Calls | Effect |
|---|---|---|---|
| `post-tool-use-build.json` | `PostToolUse` (Edit/Write/MultiEdit) | `build-hooks.py --on-edit` | Auto-rebuilds `settings.json` when Claude edits a fragment here. |
| `session-start-hooks-check.json` | `SessionStart` | `build-hooks.py --warn-if-stale` | Warns in-context at session start if `settings.json` is stale (catches manual/IDE edits). |

`--check` (exit 1 when stale) remains for CI / a pre-commit guard.
