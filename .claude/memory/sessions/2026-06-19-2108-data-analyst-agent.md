# 2026-06-19 21:08 · data-analyst-agent

**Goal:** Build data-analyst agent: objective explore/visualize/conclude method, language-agnostic, defers subjective how

## What happened
- Built `example-project/.claude/agents/data-analyst.md` — a conceptual agent that owns the
  **objective** analysis method (frame → explore → visualize → conclude → hand off) and is
  deliberately language/tool-agnostic. Its spine is an explicit **objective/subjective
  boundary**: objective (question framing, EDA goals, purpose-driven viz specs, inference +
  uncertainty) is its job; subjective (which language/library, the actual code, domain calls
  data can't settle) is specified and delegated to a developer agent / language skill.
- Frontmatter: tools Read/Grep/Glob/Bash, `permissionMode: plan` (read-only — investigates +
  reasons, never mutates or runs the pipeline), `model: opus` (inference/uncertainty/fallacy
  work). Authored per the agent-authoring discipline (sharp description w/ triggers + "not
  for" boundaries; tight role/method/guardrails/output body).
- Positioned as the **objective counterpart** to `finance-quantitative-developer` (the
  subjective hands-on executor) — data-analyst writes the spec, the developer agent runs it.
- Docs: example-project CLAUDE.md "Agents available" + agents/README "Defined".

## Gotchas & dead ends
- Placement: consumer **showcase agent, real in example-project, NOT symlinked** into the
  factory — same as finance-quantitative-developer. The factory never analyzes data, so it
  wouldn't dogfood it (no settings.json/hook change). Distinct from operational agents like
  token-manager, which IS symlinked because the factory uses it.
- The "conceptual/objective" read of the brief drove read-only `plan` mode: it inspects data
  read-only to *orient* (sample/schema/size) but does not write/run the analysis — that's the
  subjective layer. If the user wants it hands-on, flip to acceptEdits + Edit/Write/Bash.
- Verified discovery via agent-finder `agents.py show data-analyst` (name/scope/tools/model/
  description/body all parse; name == filename).

## State at end
- Branch `claude/data-analyst-agent` off merged main (#8–#12; #13 version-labeling still open).
  Independent of #13 (different files). Committed + pushed; PR opened.

## Open threads
- Possible future sibling meta-skill `analyst-agent-authoring` (how to author objective
  analyst agents) — not built; the existing agent-authoring base sufficed here.
- Planned meta-skills still unwritten: `skill-authoring`, `context-vs-skill`.
