---
description: Scaffold a new skill bundle (.claude/skills/<name>/SKILL.md) with correct frontmatter and structure.
argument-hint: <skill-name> [target .claude/ dir] [— one-line purpose]
---

You are scaffolding a new **skill** named `$1`.

## 1. Load the authoring conventions

If a **skill-authoring** meta-skill exists, use it. Until then, follow the conventions
in `.claude/skills/README.md` and model the structure on a built skill such as
`.claude/skills/agent-authoring/SKILL.md` (YAML frontmatter + a sectioned markdown body).

That README plus a built skill is the format spec — do **not** spawn
Explore/research agents to re-derive conventions or re-read example bundles. For a
request that needs several assets, follow the `author-asset` workflow and batch them.

## 2. Confirm placement

Determine the target `.claude/skills/` directory from `$ARGUMENTS`. If it isn't given,
ask: is this a **factory** meta-skill (`./.claude/skills/`, teaching how to author
assets) or a **domain/product** skill for a consumer (`example-project/.claude/skills/`
or another project path)? Default to the factory layer.

## 3. Scaffold (folder name MUST equal `name:`)

Create `<target>/.claude/skills/$1/SKILL.md` with:

- **frontmatter** — `name: $1` and a `description:` that leads with the use case and
  lists concrete trigger phrases. This field drives auto-invocation, so make it
  specific; a vague description means the skill never triggers.
- **body** — a title, then the sections the task warrants: core principles, the
  workflow / how-to, a checklist, anti-patterns, and an out-of-scope section.

## 4. Verify

Confirm the folder name equals the `name:` value and the description names real
triggers. Report the path created and how to invoke it (`/$1`), then offer to fill in
the body.
