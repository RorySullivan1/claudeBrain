---
description: Scaffold a new slash command (.claude/commands/<name>.md).
argument-hint: <command-name> [target .claude/ dir] [— what it does]
---

You are scaffolding a new **command** `/$1`.

## 1. Conventions

Follow `.claude/commands/README.md`: one markdown file per command, filename equals the
command name; the body is the prompt; use `$ARGUMENTS` (or `$1`, `$2`, …) for
parameters. Keep each command focused on one repeatable action.

## 2. Confirm placement

Determine the target `.claude/commands/` directory from `$ARGUMENTS`. If it isn't given,
ask: a **factory** authoring command (`./.claude/commands/`) or a **product** command
for a consumer (`example-project/.claude/commands/` or another project path)? Default to
the factory layer.

## 3. Scaffold

Create `<target>/.claude/commands/$1.md` with:

- **optional frontmatter** — a `description` and an `argument-hint` so the command is
  self-documenting.
- **body** — a focused prompt for one repeatable action, parameterized with
  `$ARGUMENTS` / `$1`…. State the goal, the steps, and the expected output.

## 4. Verify

Confirm it does one thing well. Report the path created and how to invoke it (`/$1`).
