# `.claude/` — project infrastructure

This directory holds the typed building blocks Claude Code uses for a project.
Each subdirectory is a distinct *layer* with a distinct job. The layers compose.

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
- **DECISIONS.md** — Log of structural/architecture decisions and their rationale.

## Status in this repo

`skills/` and `context/` are populated. `hooks/`, `commands/`, `agents/`, and
`workflows/` are intentional **scaffolds** — each has a README describing what it's
for, ready to fill when a concrete need appears. No example content is fabricated.
