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
engine). Both are **symlinks** to the canonical copies under
`example-project/.claude/skills/` — the factory dogfoods the same produced asset a
consumer lifts, so there is one source of truth and no drift. **Edit them in
`example-project/`; never replace the symlink with a copy.**

- `session-memory` — the *factory's own* persistent memory (`.claude/memory/`: an
  auto-loaded `INDEX.md` + append-only `sessions/*.md`), replacing the old `DECISIONS.md`
  workflow. Engine: `scripts/memory.py`, driven by the lifecycle hooks in `settings.json`.
  **(built)**
- `agent-finder` — sharpens subagent selection/delegation: inventory → match → choose
  topology → delegate, keeping verbose work out of the main context. Engine:
  `scripts/agents.py` (`list`/`search`/`show` over `.claude/agents/` + the built-ins).
  **(built)**
- `knowledge-router` — the front door for capturing durable knowledge: classifies an item
  and routes it to the right home (skill / `session-memory` / `CLAUDE.md` / a reference
  note), defaulting to *drop*. Owns the `.claude/context/` reference-notes tier (an
  always-loaded `INDEX.md` + on-demand `notes/*.md`). Engine: `scripts/context.py`
  (`new`/`list`/`search`/`reindex`/`index`), with `index` driven by a SessionStart hook.
  **(built)**
- `token-optimizer` — the judgment layer for keeping a session token-efficient: estimate a
  high-volume operation, then place it (delegate to `Explore` or the `token-manager` agent,
  slice a large read, or flush state to memory). Pairs with the `post_bash_filter` /
  `pre_read_guard` hooks (which trim output automatically) and the `token-manager` agent
  (which absorbs the bulk). Engine: `scripts/tokens.py` (`estimate`). **(built)**

## Format

Same as any skill: one folder per skill containing `SKILL.md`, folder name equal to
the `name:` frontmatter value.

## Status

**Four meta-skills built:** `agent-authoring/`, `developer-agent-authoring/`,
`product-manager-agent-authoring/`, and `knowledge-agent-authoring/`, plus two
operational skills (`session-memory/`, `agent-finder/`). The others above
(`skill-authoring`, `context-vs-skill`, …) are not written yet — add them as we codify
each authoring playbook.
