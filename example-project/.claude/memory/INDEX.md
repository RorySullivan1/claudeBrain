# MEMORY INDEX  ·  keep ≤ ~80 lines

<!-- Showcase sample. Illustrative content for the example-project consumer — it
     shows what a populated INDEX looks like under the session-memory pattern,
     not live history. -->

## State            (rewrite in place — current truth only, ≤ ~10 lines)
- VSTO Excel add-in (C#) + Python tooling + end-user/developer docs.
- `.claude/` layout adopted; domain skills + stack briefs populated.
- Skill families now cover VSTO, Python, and **VBA** (dev/review/maintenance/distribution).
- Memory tracked here via the `session-memory` skill (replaced the old DECISIONS.md).

## Decisions        (append-only; supersede, never delete)
- [2026-02-02] Adopt the typed `.claude/` layout; stack briefs in `context/`, not inline in CLAUDE.md — keeps every session lean — sessions/2026-02-02-1000-adopt-claude-layout.md
- [2026-06-21] VBA gets a full lifecycle skill family mirroring VSTO, distilled from the existing vba-development.md brief; siblings cross-defer and defer to VSTO-development for .NET — sessions/2026-06-21-1500-vba-skill-family.md

## Threads          (open items; remove when closed)
- Fill `hooks/`, `commands/`, `agents/`, `workflows/` when a concrete need appears.
- Offered next on VBA: open a PR; add a VBA developer agent orchestrating the skills.

## Log              (append-only pointers)
- 2026-02-02 1000 | Adopt the .claude/ layout | sessions/2026-02-02-1000-adopt-claude-layout.md
- 2026-06-21 1500 | Author VBA skill family | sessions/2026-06-21-1500-vba-skill-family.md
