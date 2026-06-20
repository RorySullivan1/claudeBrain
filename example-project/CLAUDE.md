<!--
  This is the example-project showcase from the claudeBrain factory.
  It plays the part of a real downstream repo so you can see a populated .claude/
  in context. Copy this file (and the .claude/ next to it) into your own project
  and replace the contents with your real specifics. Keep CLAUDE.md short — it
  loads on EVERY session, so it should hold only what's true every time, and point
  into .claude/context/ for detail.
-->

# example-project

A demonstration project that ships an Office productivity tool: a **VSTO Excel
add-in** (C#) backed by a set of **Python** data and packaging scripts, with
end-user and developer **documentation**. It exists to show what a real consumer
of the `claudeBrain` factory looks like once the assets are in place.

## Architecture
- **Add-in** (`src/AddIn/`): VSTO Excel add-in, C# — Ribbon UI + task panes.
- **Tooling** (`tools/`): Python scripts for data prep and build/packaging.
- **Docs** (`docs/`): developer docs (contributors) and user guides (the desk).

## Constraints
- Corporate-managed Windows; no admin rights on end-user machines.
- Office is Click-to-Run (Microsoft 365); add-in deploys via ClickOnce.
- Python tooling targets the pinned interpreter in `tools/.python-version`.

## Skills available
This project's `.claude/skills/` carries task-scoped expertise. Claude picks the
right one from its `description:`; you don't invoke them by hand.
- **VSTO:** `VSTO-development`, `VSTO-review`, `VSTO-distribution`, `VSTO-maintenance`
- **Python:** `python-development`, `python-review`, `python-maintenance`, `python-deployment`
- **Quant:** `quantitative-finance`, `financial-timeseries-analysis`, `backtesting-validation`, `quant-code-review`
- **Docs:** `technical-documentation-drafter`, `user-guide-drafter`
- **Knowledge:** `knowledge-router` — routes durable knowledge to the right home and owns the `.claude/context/` reference-notes tier.
- **Efficiency:** `token-optimizer` — decides where high-volume work runs to keep the main context lean (pairs with the output-guard hooks and the `token-manager` agent).
- **Authoring:** `skill-distiller` — decides whether freshly-derived know-how should become a skill (significance + redundancy gate), then hands authoring to `/add-skill`.

## Agents available
`.claude/agents/` holds isolated subagents Claude delegates to (auto via their
`description:`, or `@agent-<name>`):
- **`finance-quantitative-developer`** — senior Python quant engineer for the
  `tools/` analytics layer (pricing, risk, signals, time-series). Writes and
  verifies quantitative code; draws on the Quant skills above.
- **`data-analyst`** — the *objective* analysis brain: frames the question, plans the
  exploration, specifies what to visualize and why, and reasons to defensible
  conclusions — language- and tool-agnostic. Hands the subjective *how* (the code, the
  stack) to a developer agent like `finance-quantitative-developer` or a language skill.
- **`software-architect`** — the *objective* structure brain: designs the project's
  architecture to fit its objective and sets the conventions (module boundaries, where
  things live, naming, file organization). Stack-agnostic — produces the blueprint and
  hands the implementation to a developer agent / language skill.
- **`presentation-architect`** — the *objective* presentation-flow brain: designs how a
  communication artifact (deck, brochure, one-pager, report) is structured to land its
  message — audience + goal, narrative arc, message hierarchy, per-unit content spec,
  reading path, and CTA placement. Format- and tool-agnostic — produces the flow blueprint
  and hands the subjective *how* (visual design, final copy, authoring tool) to a
  design/content executor or skill.
- **`token-manager`** — context-economy worker: runs verbose/high-volume tasks in
  isolation and returns only a capped summary (keeps bulk out of the main context).

## Reference Docs
See `.claude/context/README.md` for two tiers of reference: whole-stack operating briefs
and on-demand reference notes.
- VSTO specialist brief — `vsto-project-instructions.md`
- Python full-lifecycle brief — `python-project-instructions.md`
- C/C# brief — `c-csharp-project-instructions.md`
- (also: C++ and VBA briefs)
- **Reference notes** — small declarative cards in `context/notes/`, catalogued in the
  always-loaded `context/INDEX.md` (managed by `knowledge-router`).

## Memory & decisions
State and decisions carry across sessions via the `session-memory` skill:
`.claude/memory/INDEX.md` (auto-loaded) plus append-only `sessions/*.md` logs.

## Versioning
The current unit of work is labeled in `.meta/version` (a semver label + its goals). The
`ship-version` workflow names and ships the PR from those goals: `/version-set` records the
label + goals; `/version-ship` derives the branch + PR title/body from them. `.meta/version`
is prospective ("what this version is for") and complements memory's retrospective log.

## Conventions
- Branch per change; conventional-commit-style messages.
- Python formatted with the project's configured formatter/linter before commit.
- Skill folder name always equals the skill's `name:` frontmatter.

## Compact Instructions
On compaction, preserve: the ClickOnce deployment constraint, the no-admin-rights
limit, the pinned Python version, and which skills cover VSTO vs. Python vs. docs.
