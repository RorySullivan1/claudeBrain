# skills/ — meta-skills (authoring scope)

This is the **factory** `skills/` layer. It does **not** hold domain skills — those
ship in `../../example-project/.claude/skills/`. This layer holds *meta-skills*:
expertise on **how to author assets well**.

## What goes here

Skills that guide the construction of other assets, e.g.:

- `agent-authoring` — how to design and write a Claude Code subagent
  (`.claude/agents/<name>.md`): triggering `description`, tools allowlist, default
  permissions, model, and the system-prompt mandate. **(built)**
- A `skill-authoring` skill — how to scope a skill, write a triggering
  `description:`, structure `SKILL.md`, and keep the folder name == `name:`.
- A `context-vs-skill` skill — deciding when knowledge belongs in a skill, a
  context brief, a command, or a hook.

## Format

Same as any skill: one folder per skill containing `SKILL.md`, folder name equal to
the `name:` frontmatter value.

## Status

**One meta-skill built:** `agent-authoring/`. The others above (`skill-authoring`,
`context-vs-skill`, …) are not written yet — add them as we codify each authoring
playbook.
