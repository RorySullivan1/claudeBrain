# commands/ — authoring commands (factory scope)

The **factory** `commands/` layer. Single-shot prompt templates for **authoring**
assets — the saved prompts we'd otherwise retype when building a new skill, hook,
or context brief. Invoked as `/<name>`.

## What goes here

The **`add-*` family** — one scaffolder per asset layer. Each takes a name (and an
optional target `.claude/` dir), consults the relevant meta-skill or layer README,
scaffolds the file(s) with correct frontmatter/structure, and confirms placement
(factory vs. a consumer like `example-project/`):

- `/add-skill` — scaffold a `skills/<name>/SKILL.md`. **(built)**
- `/add-agent` — scaffold an `agents/<name>.md` (uses the `*-agent-authoring` skills). **(built)**
- `/add-command` — scaffold a `commands/<name>.md`. **(built)**
- `/add-hook` — scaffold a `hooks/<name>` script and wire it into `settings.json`. **(built)**
- `/add-workflow` — scaffold a `workflows/<name>.md`. **(built)**

Future additions could include `/validate-asset` (check one asset against the
conventions) and `/add-context` (scaffold a context brief).

## Format

One markdown file per command: `<name>.md` (the filename is the command name). The
body is the prompt; use `$ARGUMENTS` / `$1`, `$2`, … for parameters. Optional
frontmatter (`description`, `argument-hint`) makes the command self-documenting.

## Status

**The `add-*` scaffolder family is built** (`add-skill`, `add-agent`, `add-command`,
`add-hook`, `add-workflow`). Validation/other authoring commands are not written yet.
