# 2026-06-19 21:23 · software-architect-agent

**Goal:** Build software-architect agent: objective project structure/conventions design, defers subjective stack

## What happened
- Built `example-project/.claude/agents/software-architect.md` — second member of the
  objective/conceptual agent family (after `data-analyst`). Owns the **objective** design of
  a project's STRUCTURE in service of its objective: architecture (components/boundaries/
  layering, separation of concerns), placement (where each kind of element lives), naming
  conventions (dirs/files/modules/symbols), and file/module organization conventions.
- Same spine as data-analyst: an explicit **objective/subjective boundary**. Objective =
  structure + placement + naming + conventions + coherence/fit-to-objective. Subjective
  (specify + defer) = the actual code & framework idioms, AND the product scope/roadmap
  (the objective is an *input* it designs toward, not one it sets).
- Frontmatter: tools Read/Grep/Glob/Bash, `permissionMode: plan` (read-only — produces the
  blueprint + conventions or assesses an existing tree; never scaffolds/moves/edits files —
  defers that), `model: opus` (design judgment). Authored per agent-authoring discipline.
- Method: anchor & survey (read objective + existing conventions read-only) → design
  architecture fit-to-objective → define placement → define naming/file conventions → check
  coherence & fit → hand off blueprint/targeted moves to a developer agent/skill.
- Docs: example-project CLAUDE.md "Agents available" + agents/README "Defined".

## Gotchas & dead ends
- Placement: consumer **showcase agent, real in example-project, NOT symlinked** — same as
  data-analyst / finance-quantitative-developer. NOTE: the factory IS convention-heavy, so it
  *could* dogfood this (symlink into factory) — left as consumer-only for now; offered to the
  user. (token-manager is the only symlinked agent because the factory actively runs it.)
- Distinctness: vs data-analyst (analyzes data) — this designs code structure. vs a product-
  manager/assessor — architect is prescriptive about structure/placement/naming and takes
  scope as an input, rather than judging scope-fit/roadmap. Boundary stated in the body.
- Read it as conceptual/read-only (matching data-analyst + the "within scope of the
  objective" framing). If the user wants it hands-on (scaffold dirs / move files), flip to
  acceptEdits + Edit/Write.
- Verified discovery via agent-finder `agents.py show software-architect`.

## State at end
- Branch `claude/software-architect-agent` off merged main (#14 in). Committed + pushed; PR opened.
- Objective-agent family now: data-analyst (analysis) + software-architect (structure).

## Open threads
- Possible family meta-skill later (e.g. authoring objective/conceptual agents); not built.
- If the user wants the factory to dogfood software-architect, symlink it into `.claude/agents/`.
- Planned meta-skills still unwritten: `skill-authoring`, `context-vs-skill`.
