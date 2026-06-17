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

## Status in this project

`skills/` (11 domain bundles plus the operational `session-memory` and `agent-finder`
skills) and `context/` (5 stack briefs) are populated, and `memory/` is active with the lifecycle hooks wired in
`settings.json`. `commands/`, `agents/`, and `workflows/` remain intentional
**scaffolds** — each has a README describing what it's for, ready to fill when a
concrete need appears.
