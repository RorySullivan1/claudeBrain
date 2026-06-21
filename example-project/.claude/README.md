# `.claude/` — project infrastructure

This directory holds the typed building blocks Claude Code uses for a project.
Each subdirectory is a distinct *layer* with a distinct job. The layers compose.

> This is the **consumer-facing** view of the layers — what they mean in a project
> that *runs* them. (`example-project/` is the `claudeBrain` factory's
> showcase of a produced `.claude/`.) For the factory's *authoring* view of the
> same layers, see the repo-root `../../.claude/README.md`.

## The composability stack

```
hooks      ← enforcement, underneath everything (Claude cannot skip these)
─────────────────────────────────────────────────────────────────────────
workflows  ▸  commands  ▸  agents  ▸  skills
(orchestrate)  (one-shot)   (isolated)  (expertise)
```

- **hooks/** — Deterministic shell scripts run by the harness on lifecycle events
  (`PreToolUse`, `PostToolUse`, `SessionStart`, …). They are the enforcement layer
  *underneath* the prompt stack — the model cannot choose to skip them. Use for
  anything that must *always* happen: formatting, branch guards, write protection,
  cache warming. Configured in `settings.json`.
- **workflows/** — Multi-step autonomous orchestrations. Claude executes a scripted
  sequence that can loop, branch, and spawn agents. Each is a markdown file.
- **commands/** — Single-shot, stateless prompt templates — saved prompts you'd
  otherwise retype. One file per command (`/<name>`).
- **agents/** — Isolated subagents spawned with clean context. They do focused work
  and return only a summary, so they don't bleed context into the main session.
- **skills/** — Domain-expertise bundles that tell Claude *how to think and behave*
  for a task type. Applied within a session or an agent's context. One folder per
  skill containing `SKILL.md`; the folder name equals the skill's `name:` frontmatter.

## Supporting files

- **context/** — Reference docs (architecture notes, schemas, stack instructions).
  `CLAUDE.md` points here; Claude deep-reads only what's relevant to the task. See
  `context/README.md` for the manifest.
- **settings.json** — Permissions, model, and hook configuration.
- **memory/** — Cross-session state via the `session-memory` skill: an auto-loaded
  `INDEX.md` plus append-only `sessions/*.md` logs (loaded/persisted by the lifecycle
  hooks in `settings.json`). Replaces a static `DECISIONS.md` log.
- **CATALOG.md** — A generated, **on-demand** inventory of every skill, agent, command, and
  workflow with a one-line purpose. `CLAUDE.md` references it by path instead of enumerating
  assets (skills/agents already auto-load by their `description:`). Produced by
  `hooks/catalog.py` (a mechanical generator), kept fresh by a `PostToolUse` auto-rebuild +
  a `SessionStart` staleness warning, and regenerated with the `/reindex` command.

## Status in this project

All seven layers are populated:

- **skills/** — domain bundles across VSTO, Python, quant, and docs, a **branding →
  presentation** pipeline (`branding` → `presentation-design` → the `*-builder` family),
  plus operational skills (`session-memory`, `agent-finder`, `knowledge-router`,
  `token-optimizer`, `skill-distiller`).
- **agents/** — an objective agent family (`data-analyst`, `software-architect`,
  `presentation-architect`) alongside `finance-quantitative-developer` and the
  context-economy `token-manager`.
- **commands/** — `/version-set`, `/version-ship`, and `/reindex`.
- **workflows/** — `ship-version`.
- **hooks/** — memory + context lifecycle hooks, context-economy guards, and the
  `build-hooks.py` / `catalog.py` generators, compiled into `settings.json`.
- **context/** — stack briefs plus the reference-notes tier, and **memory/** is active.

For the full, current list of any layer, read **`CATALOG.md`** (regenerate with `/reindex`)
— this README describes the layers; the catalog enumerates them.
