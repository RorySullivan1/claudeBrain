# workflows/ — authoring pipelines (factory scope)

The **factory** `workflows/` layer. Multi-step orchestrations for **producing
assets** end to end — where a command is one shot, a workflow runs the whole build.

## What goes here

- `author-asset` — **(built)** the default build path for any "make me a skill /
  agent / set of assets" request: scope → load conventions once (no re-exploration)
  → scaffold via the `add-*` commands → batch the wiring → verify structurally.
- `author-skill` — scaffold → draft `SKILL.md` → audit against conventions → place
  the finished bundle into `example-project/.claude/skills/` (or a downstream repo).
- `harvest-context` — turn a stack brief into a context doc, validate, file it.

## Format

One markdown file per workflow: `<name>.md` — ordered steps, the agents/commands
each step invokes (reference `../agents/` and `../commands/`), inputs/outputs, and
stop conditions.

## Status

**`author-asset` built.** `author-skill` and `harvest-context` remain planned.
