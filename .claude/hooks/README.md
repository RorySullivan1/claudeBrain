# hooks/ — authoring guardrails (factory scope)

The **factory** `hooks/` layer. Deterministic scripts the harness runs *while we
author assets in this repo* — the enforcement floor for the factory itself, not
hooks shipped to a consumer project. The model cannot skip them.

## What goes here

Checks that must always run when editing assets here, e.g.:

- `PostToolUse` → validate that a skill folder name matches its `name:` frontmatter.
- `PostToolUse` → lint/format authored markdown.
- `PreToolUse` → guard the branch name / block stray writes.

It also holds **memory lifecycle hooks** — the deterministic moments that drive the
`session-memory` system (load on start, persist before context is lost, recall on
"continue") — and **context-economy guard hooks**: `post_bash_filter.py`
(PostToolUse·Bash — ANSI-strips and head/tail-elides long command output) and
`pre_read_guard.py` (PreToolUse·Read — caps an unpaged whole-file slurp of a huge file).
Both fail safe and pair with the `token-optimizer` skill. These are not authoring
guardrails, but they live here because they are the other thing the harness must run
*for us* while we work in this repo. (Like the scripts, these hook files are symlinks to
the canonical copies in `example-project/.claude/hooks/`.)

## Storage — one fragment file per hook (this is the source of truth)

Claude Code can't load hook definitions from external files — the `hooks` block must
live inline in `settings.json`. To keep that file from becoming a large, hand-edited
blob, we store each hook as its own small `*.json` **fragment** here and **generate**
`../settings.json` from them with `build-hooks.py`. Edit the fragments; never
hand-edit the `hooks` block in `settings.json` (it's a derived artifact).

A fragment is a partial hooks object keyed by event name. Prefer **exec-form**
(`command` + `args`) over shell-form on Windows, where `cat`/`$VAR` hooks are fragile:

```json
{ "SessionStart": [ { "matcher": "...", "hooks": [ { "type": "command", "command": "python", "args": [ "..." ] } ] } ] }
```

Every `*.json` in this folder is treated as a fragment (the README and `build-hooks.py`
are ignored). Fragments merge in filename order; multiple fragments targeting the same
event concatenate.

> **`build-hooks.py` and the shared fragments are symlinks** to the canonical copies in
> `example-project/.claude/hooks/` — single source of truth, no drift. Edit them in
> `example-project/`. A factory-only hook can still be added as a new *real* `*.json`
> here alongside the symlinks; `build-hooks.py` globs every `*.json` regardless.
> `README.md` and `settings.json` stay independent per tree (they differ by role).

### Rebuild after editing a fragment

```bash
python .claude/hooks/build-hooks.py          # regenerate ../settings.json
python .claude/hooks/build-hooks.py --check   # CI/guard: exit 1 if settings.json is stale
```

(`python3` on macOS/Linux.)

## Fragment index — memory lifecycle hooks (wired)

These four call `session-memory`'s `scripts/memory.py` (it lives under the skill, not
here) so the model uses memory at the right moments:

| Fragment | Event | Matcher | Subcommand | Effect |
|---|---|---|---|---|
| `session-start.json` | `SessionStart` | `startup\|resume\|clear\|compact` | `index` | Prints `INDEX.md` into context — memory is always loaded. |
| `pre-compact.json` | `PreCompact` | `auto\|manual` | `precompact-hook` | Reminds the model to persist state before compaction summarizes it away. |
| `stop.json` | `Stop` | — | `stop-hook` | Once-guarded (`stop_hook_active`) reminder to log a substantial session before stopping. |
| `user-prompt-submit.json` | `UserPromptSubmit` | — | `prompt-hook` | On "continue"/"last time"-style prompts, points at `INDEX.md` + `memory.py search`. |

To add a hook: drop a new `<event>.json` fragment here, add a row above, and run
`build-hooks.py`. A non-zero `PreToolUse` fragment would veto the matched tool call.

## Self-maintaining (the drift guard)

Because `settings.json` is generated, it can fall out of sync if a fragment changes
without a rebuild. Two fragments close that gap automatically — so in practice you
edit a fragment and never think about the rebuild:

| Fragment | Event | Calls | Effect |
|---|---|---|---|
| `post-tool-use-build.json` | `PostToolUse` (Edit/Write/MultiEdit) | `build-hooks.py --on-edit` | When Claude edits a `*.json` fragment here, regenerates `settings.json` immediately. |
| `session-start-hooks-check.json` | `SessionStart` | `build-hooks.py --warn-if-stale` | Catches edits the harness can't (manual/IDE): warns in-context at session start if `settings.json` is stale. Never blocks. |

`--check` (exit 1 when stale) remains for CI or a pre-commit guard.

## Status

**Memory lifecycle hooks are wired** (the four fragments above), compiled into
`settings.json` by `build-hooks.py`. Authoring guardrail hooks (skill-name/frontmatter
validation, markdown lint, branch guards) are not written yet — add them as fragments.
