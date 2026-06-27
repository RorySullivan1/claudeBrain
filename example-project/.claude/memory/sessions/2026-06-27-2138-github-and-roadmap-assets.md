# 2026-06-27 21:38 · github-and-roadmap-assets

**Goal:** Add GitHub workflow skills + operator agent, and a roadmap/orchestration layer
for plan-driven iterative development. (Continues the VBA work from earlier in the day.)

## What happened
Four open PRs produced this session, each on its own branch off `main`:
- **#22** `claude/vba-skills-jlhcsr` — `vba-developer` agent (sonnet, acceptEdits). Honest
  verification gate: VBA has no out-of-host lint/compile/test, so static self-review vs the
  vba-review checklist + a manual in-host test procedure, not a faked CI pass.
- **#23** `claude/vba-testing-skills` — new `vba-code-test-writing` skill + folded an
  "MSO verification, no CI" section into the existing `vba-review` (user chose fold over a
  duplicate `vba-code-review`). Grounded in researched Rubberduck specifics + KB257757.
- **#24** `claude/github-skills` — GitHub workflow skill family (`github-pull-requests`,
  `github-issues`, `github-releases`, `github-comments`) + `github-operator` agent
  (permissionMode default to gate public actions; curated mcp__github__ allowlist).
- **#25** `claude/roadmap-orchestration` — the roadmap → orchestration layer (below).

Roadmap layer (#25) wraps the existing version spine rather than replacing it:
- skill `development-mapping` (objective → stages → versions → milestones; PR-sized slicing;
  sequence by dependency/risk; checkable acceptance) + EXAMPLE.md worked map.
- commands `/roadmap-set`, `/roadmap-status`; artifact `.meta/roadmap/` (INDEX + stages/cards).
- workflow `advance-roadmap-step` (graduate cursor → implement → review→reiterate →
  goal-auditor → STOP for approval before PR → ship via ship-version → step cursor).
- agent `goal-auditor` (opus, read-only/plan) — acceptance gate vs the version card.
- hook `roadmap_status.py` + fragment — surface "you are here" at session start (opt-in by
  presence); settings.json rebuilt via build-hooks.py. CLAUDE.md documents the two altitudes.

## Gotchas & dead ends
- **Orchestrator is a workflow, not an agent.** User said "another agent"; deterministic
  multi-agent control flow is the workflow layer. Only the goal-auditor is a real agent.
- **Planner is a skill+command, not an isolated agent** — the "iterate until content" loop is
  conversational; an isolated subagent can only propose-once-return-summary. (User agreed.)
- **Roadmap-as-live-plan mistake (corrected):** first pass populated `.meta/roadmap/` as if it
  were example-project's real plan. Fix ("both"): moved the full worked example into the skill
  (EXAMPLE.md, generic URL-shortener) AND demoted `.meta/roadmap/` to a clearly-labeled
  SHOWCASE-SAMPLE banner (like memory/INDEX.md), trimmed to the active stage only.

## Decisions
- VBA `vba-code-review` request → folded into existing `vba-review`, not a new skill.
- GitHub PRs split into separate per-topic PRs (user prefers one PR per piece this session).
- Roadmap altitude sits ABOVE software-architect (structure) and ABOVE .meta/version (cursor);
  the orchestrator reuses /version-set + ship-version wholesale.

## State at end
- 4 PRs open (#22–#25), none merged yet. All branches pushed.
- example-project now showcases: VBA family (+agent, +testing), GitHub family (+operator),
  and the roadmap/orchestration layer.

## Open threads
- Watch/merge PRs #22–#25.
- Offered, not done: a broader cleanup to drop ALL sample runtime state from example-project
  (vs the current "showcase sample" convention for .meta/version, memory, .meta/roadmap).
