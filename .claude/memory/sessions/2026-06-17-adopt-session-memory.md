# 2026-06-17 · adopt-session-memory

**Goal:** Replace the factory's `DECISIONS.md` workflow with the `session-memory`
skill, wire lifecycle hooks that nudge the model to use it, and showcase the pattern
in `example-project/`.

## What happened
- Added the `session-memory` skill at `.claude/skills/session-memory/` (SKILL.md +
  `scripts/memory.py`). The skill text is the user-provided design; transcribed with
  corrected UTF-8 and `python` (not `python3`) for this Windows machine.
- Authored `memory.py` (stdlib only): `init`, `new`, `search`, `list`, `index`,
  `precompact-hook`, `stop-hook`, `prompt-hook`. It resolves the project root from
  `$CLAUDE_PROJECT_DIR` so the same script works in the factory and in example-project.
- Migrated `.claude/DECISIONS.md` → `.claude/memory/sessions/2026-archive-decisions.md`
  via `git mv` (history preserved); seeded `INDEX.md` with current State, one-line
  summaries of all 8 prior decisions (pointing at the archive), open Threads, and Log.
- Wired four hooks in `.claude/settings.json`: SessionStart (load INDEX),
  PreCompact (persist reminder), Stop (once-guarded write reminder),
  UserPromptSubmit (recall on "continue"-style prompts).
- Mirrored the skill + a sample memory store into `example-project/` and switched its
  showcase from DECISIONS.md to the memory pattern.

## Gotchas & dead ends
- **Windows stdout is cp1252**, so `print`/`write` of `≤`, `·`, `—`, or emoji raised
  `UnicodeEncodeError` and would have crashed the hooks in the real harness. Fix:
  `sys.stdout/stderr.reconfigure(encoding="utf-8")` at startup, and dropped emoji from
  reminder strings. `json.dumps` was already safe (ensure_ascii escapes to `\uXXXX`).
- `python3` does not exist on this machine (only `python`); hooks and skill examples
  use `python`. macOS/Linux users use `python3` (noted in the skill).
- Hooks use **exec-form** (`command` + `args`), not shell-form `cat "$VAR"`, because
  shell-form is fragile on Windows (Git Bash vs PowerShell fallback). Confirmed via
  claude-code-guide that `${CLAUDE_PROJECT_DIR}` is expanded and hook cwd is repo root.
- **Stop** hooks: exit-0 stdout is ignored by the harness; the only reliable nudge is
  JSON `{"decision":"block","reason":...}`, which loops (hard cap 8) unless guarded by
  the `stop_hook_active` flag. `stop-hook` checks that flag and blocks at most once.

## State at end
- Memory system live in the factory; DECISIONS.md workflow retired. Four hooks active.
- example-project showcases the same pattern with sample content.

## Open threads
- See INDEX Threads: planned `skill-authoring`/`context-vs-skill` meta-skills,
  `/validate-asset` + `/add-context` commands, possible reviewer/orchestrator agents.
