# MEMORY INDEX  ·  keep ≤ ~80 lines

<!-- Showcase sample. Illustrative content for the example-project consumer — it
     shows what a populated INDEX looks like under the session-memory pattern,
     not live history. -->

## State            (rewrite in place — current truth only, ≤ ~10 lines)
- VSTO Excel add-in (C#) + Python tooling + end-user/developer docs.
- `.claude/` layout adopted; domain skills + stack briefs populated.
- Skill families cover VSTO, Python, **VBA** (+ `vba-developer` agent, `vba-code-test-writing`),
  and **GitHub** (`github-pull-requests`/`issues`/`releases`/`comments` + `github-operator` agent).
- **Roadmap/orchestration layer**: `development-mapping` skill, `/roadmap-set`+`/roadmap-status`,
  `advance-roadmap-step` workflow, `goal-auditor` agent, `roadmap_status` hook; `.meta/roadmap/`
  is a labeled showcase sample. Wraps the `.meta/version` + ship-version spine, doesn't replace it.
- 4 PRs open (#22 vba-developer · #23 VBA testing · #24 GitHub · #25 roadmap), none merged.

## Decisions        (append-only; supersede, never delete)
- [2026-02-02] Adopt the typed `.claude/` layout; stack briefs in `context/`, not inline in CLAUDE.md — keeps every session lean — sessions/2026-02-02-1000-adopt-claude-layout.md
- [2026-06-21] VBA gets a full lifecycle skill family mirroring VSTO, distilled from the existing vba-development.md brief; siblings cross-defer and defer to VSTO-development for .NET — sessions/2026-06-21-1500-vba-skill-family.md
- [2026-06-27] Orchestration of a dev step is a **workflow** (advance-roadmap-step), not an agent; the planner is a **skill+command** (conversational). Only goal-auditor is an agent — sessions/2026-06-27-2138-github-and-roadmap-assets.md
- [2026-06-27] Sample runtime state in example-project (`.meta/roadmap/`, `.meta/version`, memory) carries a "showcase sample" banner — teaching examples live with the skill, not as live plans — sessions/2026-06-27-2138-github-and-roadmap-assets.md

## Threads          (open items; remove when closed)
- Watch/merge PRs #22–#25.
- Possible follow-up: drop ALL sample runtime state from example-project vs the current "showcase sample" convention.

## Log              (append-only pointers)
- 2026-02-02 1000 | Adopt the .claude/ layout | sessions/2026-02-02-1000-adopt-claude-layout.md
- 2026-06-21 1500 | Author VBA skill family | sessions/2026-06-21-1500-vba-skill-family.md
- 2026-06-27 2138 | GitHub skills+operator & roadmap/orchestration layer | sessions/2026-06-27-2138-github-and-roadmap-assets.md
