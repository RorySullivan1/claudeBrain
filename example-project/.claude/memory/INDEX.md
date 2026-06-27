# MEMORY INDEX  ·  keep ≤ ~80 lines

<!-- Showcase sample. Illustrative content for the example-project consumer — it
     shows what a populated INDEX looks like under the session-memory pattern,
     not live history. -->

## State            (rewrite in place — current truth only, ≤ ~10 lines)
- VSTO Excel add-in (C#) + Python tooling + end-user/developer docs.
- `.claude/` layout adopted; domain skills + stack briefs populated.
- Skill families cover VSTO, **VBA** (full lifecycle + tests), Python, quant, docs, and **GitHub**.
- **Developer agents** pair with the families: `python-developer`, `vsto-developer`,
  `finance-quantitative-developer`, `vba-developer`; plus the `github-operator`. Factory has
  **7 meta-skills** (skill/agent×4/workflow/context-vs-skill) + the `add-context` scaffolder.
- **Roadmap → orchestration** layer drives plan-based iterative dev (`development-mapping`,
  `advance-roadmap-step`, `goal-auditor`, `roadmap_status`+`roadmap_guard` hooks) atop the
  `.meta/version` + ship-version spine; `.meta/roadmap/` is a labeled showcase sample.
- Memory via `session-memory`. #22/#23/#24/#26 merged; #25 (roadmap) merging into main now.

## Decisions        (append-only; supersede, never delete)
- [2026-02-02] Adopt the typed `.claude/` layout; stack briefs in `context/`, not inline in CLAUDE.md — keeps every session lean — sessions/2026-02-02-1000-adopt-claude-layout.md
- [2026-06-21] VBA gets a full lifecycle skill family mirroring VSTO, distilled from the existing vba-development.md brief; siblings cross-defer and defer to VSTO-development for .NET — sessions/2026-06-21-1500-vba-skill-family.md
- [2026-06-27] Orchestration = a workflow (advance-roadmap-step), not an agent; the planner = a skill+command. Roadmap is the route, `.meta/version` the cursor; the orchestrator reuses ship-version — sessions/2026-06-27-2138-github-and-roadmap-assets.md
- [2026-06-27] Sample runtime state in example-project (`.meta/roadmap/`, `.meta/version`, memory) carries a "showcase sample" banner — teaching examples live with the skill, not as live plans — sessions/2026-06-27-2138-github-and-roadmap-assets.md
- [2026-06-27] Build assessed enhancements via one-file-per-agent fan-out; integrate shared files (catalogs/READMEs) sequentially. Context briefs point to skills (skills own how-to) — sessions/2026-06-27-2209-code-review-and-enhancements.md

## Threads          (open items; remove when closed)
- Remaining authoring gap: a `command-authoring` meta-skill.
- Sample-state convention settled on banner-all (.meta/version, .meta/roadmap, memory/INDEX).

## Log              (append-only pointers)
- 2026-02-02 1000 | Adopt the .claude/ layout | sessions/2026-02-02-1000-adopt-claude-layout.md
- 2026-06-21 1500 | Author VBA skill family | sessions/2026-06-21-1500-vba-skill-family.md
- 2026-06-27 2138 | GitHub skills+operator & roadmap/orchestration layer | sessions/2026-06-27-2138-github-and-roadmap-assets.md
- 2026-06-27 2209 | Code review + build all enhancements (PRs #25/#26) | sessions/2026-06-27-2209-code-review-and-enhancements.md
