---
description: Scaffold a new context doc (.claude/context/<name>.md) — a whole-stack brief or a reference note.
argument-hint: <context-name|topic> [target .claude/ dir] [— what it documents]
---

You are scaffolding a new **context doc** for `$1`.

## 1. Load the authoring conventions

If a **context-vs-skill** meta-skill exists, use it first to confirm this knowledge
belongs in **context** (reference Claude deep-reads on demand) and not in a **skill**
(how Claude should *think/behave*). Until then, follow `example-project/.claude/context/README.md`
and the Context row of the taxonomy table in `CLAUDE.md`: context docs are kebab-case
plain markdown with **no YAML frontmatter** (unlike skills/agents), listed in the
context manifest.

That README plus an existing brief is the format spec — do **not** spawn
Explore/research agents to re-derive conventions. For a request that needs several
assets, follow the `author-asset` workflow and batch them.

## 2. Pick the tier

`context/` has two tiers — decide which `$1` is:

- a whole-stack/topic **brief** — a longer operating doc, one per language/stack
  (`context/<kebab-name>.md`); continue here.
- a small **reference note** — a declarative card (a concept, an external-system fact,
  a schema, a system map) catalogued in `context/INDEX.md`. **Don't hand-write notes** —
  defer to the **knowledge-router** skill / its `context.py` engine, which creates the
  note and regenerates the catalog so it can't drift. Hand off and stop.

## 3. Confirm placement

Determine the target `.claude/context/` directory from `$ARGUMENTS`. If it isn't given,
ask: a **factory** authoring brief (`./.claude/context/`, e.g. authoring standards) or a
**product** brief for a consumer (`example-project/.claude/context/` or another project
path)? Default to the factory layer.

## 4. Scaffold (kebab-case, NO frontmatter)

Create `<target>/.claude/context/<kebab-name>.md` as plain markdown — **no YAML
frontmatter**. Give it a starter skeleton: a top `# <Title>` heading, then the sections
the brief warrants (purpose/scope, the stack/architecture, conventions and constraints,
key workflows, gotchas). Mirror an existing brief like
`example-project/.claude/context/python-project-instructions.md` for depth and tone.

## 5. Register and verify

Add the new file to the context manifest — the **Manifest** table in
`<target>/.claude/context/README.md` — with a one-line "what it's for" (a note instead
goes to `context/INDEX.md` via the knowledge-router flow). Confirm the filename is
kebab-case and the doc carries no frontmatter. Report the path created and that the
manifest was updated.
