# 2026-02-02 10:00 · adopt-claude-layout

> **Showcase sample.** This is an *example* session log (like the sample
> `CLAUDE.local.md`), not live history — it shows what a real `sessions/*.md` entry
> looks like under the `session-memory` pattern.

**Goal:** Decide how to structure Claude Code config for this project.

## What happened
- Adopted the typed `.claude/` layout: domain skills under `skills/`, whole-stack
  briefs under `context/`, and the four flexible layers (`hooks/`, `commands/`,
  `agents/`, `workflows/`) scaffolded for later. `CLAUDE.md` stays short and points
  into `context/`.

## Gotchas & dead ends
- Considered putting the stack briefs inline in `CLAUDE.md`; rejected — it would load
  on every session and blow the always-on token budget. They live in `context/` and
  are deep-read on demand instead.

## State at end
- `.claude/` layout in place; empty layers left as READMEs, not fabricated.

## Open threads
- Fill `hooks/`, `commands/`, `agents/`, `workflows/` when a concrete need appears.
