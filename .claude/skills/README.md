# skills/ — meta-skills (authoring scope)

This is the **factory** `skills/` layer. It does **not** hold domain skills — those
ship in `../../example-project/.claude/skills/`. This layer holds *meta-skills*:
expertise on **how to author assets well**.

## What goes here

Skills that guide the construction of other assets, e.g.:

- `agent-authoring` — how to design and write a Claude Code subagent
  (`.claude/agents/<name>.md`): triggering `description`, tools allowlist, default
  permissions, model, and the system-prompt mandate. **(built)**
- `developer-agent-authoring` — how to design a *developer agent*: a subagent
  specialized at writing/maintaining code in a given language or stack — project
  structure, convention adherence, toolchain use, a verification gate, dependency
  hygiene, and efficiency. Layers on top of `agent-authoring`. **(built)**
- `product-manager-agent-authoring` — how to design a *product-manager agent*: a
  read-only subagent that assesses code against the whole project's scope and design —
  scope fit, system/application design, organization, and efficiency — and returns a
  prioritized report. The assessor sibling of `developer-agent-authoring`; layers on
  top of `agent-authoring`. **(built)**
- `knowledge-agent-authoring` — how to design a *knowledge agent*: a subagent that
  curates a corpus (docs, notes, memory, a vector store) and/or retrieves from it —
  grounded, cited, multi-strategy search, plus freshness, dedup, and provenance for
  curation. Spans read-only and curation modes; layers on top of `agent-authoring`.
  **(built)**
- A `skill-authoring` skill — how to scope a skill, write a triggering
  `description:`, structure `SKILL.md`, and keep the folder name == `name:`.
- A `context-vs-skill` skill — deciding when knowledge belongs in a skill, a
  context brief, a command, or a hook.

## Operational skills (exceptions)

These are **not** meta-skills — they run *during work* rather than teaching how to
author assets. They live here because each is a `SKILL.md` bundle (often with a script
engine):

- `session-memory` — the *factory's own* persistent memory (`.claude/memory/`: an
  auto-loaded `INDEX.md` + append-only `sessions/*.md`), replacing the old `DECISIONS.md`
  workflow. Engine: `scripts/memory.py`, driven by the lifecycle hooks in `settings.json`.
  **(built)**
- `agent-finder` — sharpens subagent selection/delegation: inventory → match → choose
  topology → delegate, keeping verbose work out of the main context. Engine:
  `scripts/agents.py` (`list`/`search`/`show` over `.claude/agents/` + the built-ins).
  **(built)**

## Format

Same as any skill: one folder per skill containing `SKILL.md`, folder name equal to
the `name:` frontmatter value.

## Status

**Four meta-skills built:** `agent-authoring/`, `developer-agent-authoring/`,
`product-manager-agent-authoring/`, and `knowledge-agent-authoring/`, plus two
operational skills (`session-memory/`, `agent-finder/`). The others above
(`skill-authoring`, `context-vs-skill`, …) are not written yet — add them as we codify
each authoring playbook.
