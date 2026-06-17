---
description: Scaffold a new lifecycle hook script and wire it into settings.json.
argument-hint: <hook-name> [PreToolUse|PostToolUse|SessionStart|Stop|…] [target .claude/ dir]
---

You are scaffolding a new **hook** named `$1`.

## 1. Conventions

Follow `.claude/hooks/README.md`: one executable script per hook; it is wired in
`settings.json` under `hooks`, keyed by event (`PreToolUse`, `PostToolUse`,
`SessionStart`, `Stop`, …) with an optional matcher. A `PreToolUse` hook that exits
non-zero **vetoes** the tool call. Hooks run deterministically — the model cannot skip
them — so keep the script safe, fast, and side-effect-aware.

## 2. Confirm placement & event

Determine the target `.claude/hooks/` directory from `$ARGUMENTS`. If it isn't given,
ask: a **factory** guardrail (`./.claude/hooks/`) or a **product** hook for a consumer
(`example-project/.claude/hooks/` or another project path)? Default to the factory
layer. Confirm the lifecycle event and matcher if not provided.

## 3. Scaffold

- Create the script `<target>/.claude/hooks/$1.<ext>` with a shebang. Read hook input
  from stdin/environment; exit `0` to allow, and (for `PreToolUse`) non-zero to block,
  printing a reason to stderr. Make it executable.
- Register it in the target `.claude/settings.json` under `hooks` → the chosen event,
  with the matcher and the command path.

## 4. Verify

Show both the script and the `settings.json` entry, and confirm the event/matcher are
correct. Report the path created.
