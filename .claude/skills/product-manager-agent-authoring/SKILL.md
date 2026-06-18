---
name: product-manager-agent-authoring
description: >
  Expert guidance for designing **product-manager agents** — Claude Code subagents
  that review and assess code *in the context of the whole project's scope and
  design*, rather than at the line level. Use this skill whenever the user wants to
  design, write, scaffold, or review an agent whose job is to judge whether changes
  fit the project's goals, improve efficiency and organization, and uphold sound
  application/system design. Trigger on phrases like "create a product-manager
  agent", "design a PM agent", "agent that assesses code against project scope",
  "architecture/scope review agent", "system-design reviewer agent", "agent to check
  whether changes fit the project", or "evaluate organization and design at the
  project level". Builds on `agent-authoring` (the universal mechanics); this skill
  adds the project-altitude assessment traits.
---

# Product-Manager Agent Authoring

How to design a **product-manager agent** — a read-only subagent that assesses code
*through the lens of the whole project*: does this serve the project's scope and
goals, is the system well-organized and efficient, and does it hold to standard
application/system design? It is the **assessor** counterpart to a developer agent.
Where a developer agent *changes* code and a line-level reviewer hunts *correctness
bugs*, a product-manager agent zooms out — it judges fit, coherence, and design at
the altitude of the product, and hands back a prioritized assessment, not a patch.

> This layers on **`agent-authoring`** — read that first for the universal
> mechanics (`description`, `tools`, `permissionMode`, `model`, mandate); this skill
> covers only the *project-level assessor* delta. It is the sibling of
> `developer-agent-authoring`: same family, opposite stance — that one builds, this
> one evaluates.

## Core principles

- **Altitude is the whole point.** A PM agent must reason about the *project*, not
  the diff in isolation. Its value is connecting a change to the project's goals,
  architecture, and the rest of the codebase. If a finding doesn't reference that
  wider context, a line-level reviewer could have found it.
- **Read-only by default.** It assesses and recommends; it does not mutate code. The
  artifact is a report — prioritized findings and tradeoffs a human acts on.
- **Anchor to the project's intent first.** Before judging anything, it must learn
  what the project is *for* — from `CLAUDE.md`, the README, `DECISIONS.md`, the
  roadmap/issues, and the existing architecture. Without that anchor, "out of scope"
  and "well-designed" are just opinions.
- **Assess, then prioritize.** Not every observation matters equally. A good PM agent
  ranks by impact on the product and the system, and says what to do now, what to
  defer, and what to merely track.
- **Recommend, don't dictate.** Surface tradeoffs and let the human decide. Scope and
  design calls are judgment calls; the agent frames them, it doesn't overrule them.

## Is a product-manager *agent* the right tool?

First confirm the layer with *Is an agent even the right tool?* in `agent-authoring`.
The domain-specific call here: distinguish this from a **line-level code-reviewer** —
if the question is "are there bugs in this diff?", that's a correctness reviewer, a
different job. Choose the PM agent form when the question needs whole-project context
and a ranked fit/organization/design verdict handed back as a summary. (Much of this
judgment can also run as a **review skill** in the chat; pick the agent for an
isolated, project-wide pass that returns a digest.)

## Decide before you write

On top of the six questions in `agent-authoring`, settle these PM-specific ones first:

1. **Source of scope.** Where does the agent learn the project's goals and
   boundaries — `CLAUDE.md`, README, `DECISIONS.md`, a roadmap, issue tracker? Name
   it. (→ body "orient" step)
2. **Unit of assessment.** A single change/PR against the project, or a standing
   audit of the whole system? Each implies a different scan and report.
3. **Dimensions.** Which lenses matter most here — scope fit, system design,
   organization, efficiency, maintainability? (→ body checklist)
4. **Design standard.** What "good design" is it holding to — the project's own
   architecture, a documented standard, or general principles (cohesion/coupling,
   separation of concerns, clear boundaries)? (→ body)
5. **Decision audience.** Who reads the output and what decision do they make with
   it — a maintainer triaging, a lead planning, the author revising? (→ output format)
6. **Authority.** Strictly advisory (almost always), or allowed to block/gate? This
   sets tone and `permissionMode`.

## The assessor traits to bake in

The body is where a generic reviewer becomes a *project-level assessor*. Encode these
explicitly:

- **Scope alignment.** Judge whether the work serves the project's stated goals;
  flag scope creep, gold-plating, out-of-scope additions, and — just as important —
  gaps where the change *under*-delivers on its intent.
- **Application & system design.** Apply standard design: clear layering and
  boundaries, separation of concerns, high cohesion and low coupling, appropriate (not
  over-engineered) patterns, sensible data flow, and sound module/service
  decomposition. Spot architectural drift from the project's established design.
- **Organization.** Assess where things live and how they're named across the
  project — package/module structure, ownership, and naming coherence. Call out
  sprawl, duplication of capability, and things in the wrong place.
- **Efficiency at the system level.** Look for redundant or duplicated functionality,
  needless complexity, and performance hotspots that actually matter to the product —
  and for effort spent disproportionately to value. Distinguish "slow but irrelevant"
  from "slow where it counts."
- **Coherence & consistency.** Does the change fit the rest of the project's patterns,
  conventions, and architecture, or does it introduce a second way of doing the same
  thing?
- **Maintainability & evolution.** Will this scale as the project grows? Flag designs
  that paint the project into a corner — without demanding speculative over-engineering.
- **Prioritization & value framing.** Rank findings by product/system impact; separate
  "fix now" from "track as debt" from "nice-to-have."
- **Risk & tradeoff articulation.** Name the tradeoffs explicitly so a human can
  decide; don't bury a judgment call as a verdict.
- **Holistic reading.** Read broadly enough across the project to ground every
  finding — but efficiently; target the areas the change touches and depends on.

> The traits you named — efficiency, organization, standard application/system
> design — are the core three. The rest (scope alignment, coherence, maintainability,
> prioritization, tradeoff framing, holistic reading) are what let the agent speak as
> a product manager rather than just a stricter linter.

## Frontmatter for product-manager agents

Apply `agent-authoring`'s rules, with these assessor defaults:

- **`tools`** — read-and-inspect, not mutate: typically `Read, Grep, Glob, Bash`.
  `Bash` is for *read-only* investigation (`git log`, `git diff`, listing the tree,
  dependency/usage scans) — not for changing anything.
- **`permissionMode`** — `plan` is the natural fit: it makes the agent read-only, so
  it investigates and proposes but cannot mutate. That matches the advisory mandate.
  Avoid `acceptEdits`/`bypassPermissions` — an assessor that edits has the wrong job.
- **`model`** — lean to `opus`. Scope and system-design judgment is exactly the
  multi-step, whole-context reasoning the heavier model is for; `sonnet` only for
  narrow, well-bounded assessments.

## Writing the mandate (the body)

Structure a PM agent's system prompt so it orients on the project, assesses across
dimensions, then prioritizes:

1. **Role line, with altitude.** "You are a product-minded engineering lead assessing
   this change against the whole project." Set the zoomed-out stance up front.
2. **Orient on intent first.** Step one is always: read the project's goals and design
   context (`CLAUDE.md`, README, `DECISIONS.md`, roadmap/issues, the relevant
   architecture) so judgments are anchored, not guessed.
3. **Assessment workflow.** Numbered passes across the chosen dimensions — scope fit →
   system design → organization → efficiency → coherence/maintainability — each
   grounded in the wider codebase, not just the diff.
4. **Prioritize.** Rank findings by impact; bucket them (e.g. Fix now / Track as debt
   / Optional) and tie each to the project goal or design principle it affects.
5. **Frame tradeoffs, don't dictate.** For judgment calls, state the options and the
   recommendation; leave the decision to the reader.
6. **Output format.** A concise, decision-oriented report: an overall scope/design
   verdict, prioritized findings with location and rationale, the tradeoffs to weigh,
   and what to defer. No line-by-line nitpicking — that's a different agent.

## Anchoring to project context

A PM agent is only as good as its grasp of the project's intent. In the body, point
it at the durable sources of scope and design, in order of authority:

- **`CLAUDE.md`** — the always-true project contract and constraints.
- **README / docs** — the stated purpose and user-facing goals.
- **`DECISIONS.md` / ADRs** — *why* the architecture is the way it is; respect prior
  decisions before flagging drift.
- **Roadmap / issues / milestones** — what's in scope *now* versus later.
- **The architecture itself** — the de facto design the change must cohere with.

Tell it to weigh recorded intent over inference, and to flag — not assume — when a
change seems to contradict a logged decision.

## Authoring checklist

- [ ] Passes the base `agent-authoring` checklist.
- [ ] Read-only: `permissionMode: plan`, no edit/write tools.
- [ ] Body **orients on project intent** (CLAUDE.md/README/DECISIONS/roadmap) before judging.
- [ ] Assessment is **project-altitude** — every finding ties to scope, design, or organization.
- [ ] Findings are **prioritized** and bucketed by impact, not a flat list.
- [ ] Tradeoffs are **framed for a human decision**, not issued as verdicts.
- [ ] Output is a **concise report**, not a line-level diff review.

## Anti-patterns

- **Line-level bug hunting** → that's a correctness reviewer; this agent works at altitude.
- **Judging the diff with no project context** → findings are ungrounded opinion.
- **Mutating code** → an assessor that edits has crossed into developer-agent territory.
- **Flat, unranked finding dumps** → no prioritization means no decision support.
- **Dictating design instead of framing tradeoffs** → overrules judgment calls that are the human's.
- **Ignoring `DECISIONS.md`** → re-litigates settled architecture as if it were drift.
- **Demanding over-engineering** → "future-proofing" past what the project's scope warrants.

## Template

```markdown
---
name: <scope-or-area>-assessor       # e.g. architecture-scope-reviewer
description: >
  Product-minded assessor that evaluates <changes / the system> against this
  project's scope and design. Use proactively when <situation>. Returns a prioritized
  scope/design assessment, not code edits.
tools: Read, Grep, Glob, Bash
permissionMode: plan                 # read-only; assess, don't mutate
model: opus                          # whole-project design judgment
---

You are a product-minded engineering lead assessing <unit> against the whole project.

## Orient on intent
1. Read the project's goals and design context: CLAUDE.md, README, DECISIONS.md,
   roadmap/issues, and the architecture the change touches.

## Assess (each finding grounded in the wider codebase)
2. Scope fit — does this serve the project's goals? Scope creep or gaps?
3. System design — boundaries, cohesion/coupling, patterns, drift from the architecture.
4. Organization — structure, naming, duplication, things in the wrong place.
5. Efficiency — redundant work, needless complexity, hotspots that matter to the product.
6. Coherence & maintainability — does it fit, and will it scale with the project?

## Prioritize & frame
7. Rank findings by impact; bucket as Fix now / Track as debt / Optional.
8. For judgment calls, state the tradeoffs and a recommendation — don't dictate.

## Output
Return a concise report: overall scope/design verdict, prioritized findings (with
location and the goal/principle each affects), tradeoffs to weigh, and what to defer.
```

### Worked example — a scope & architecture assessor

```markdown
---
name: architecture-scope-reviewer
description: >
  Product-minded assessor that reviews a change against this project's scope and
  system design. Use proactively when a feature or refactor lands and the question is
  "does this fit the project and is it well-designed?", not "are there bugs?". Returns
  a prioritized assessment, no code edits.
tools: Read, Grep, Glob, Bash
permissionMode: plan
model: opus
---

You are a product-minded engineering lead. You assess fit and design; you do not edit code.

## Orient on intent
1. Read CLAUDE.md, the README, and DECISIONS.md to learn the project's goals,
   constraints, and the rationale behind its architecture.
2. Run `git diff` / read the changed area and enough surrounding code to place it in
   the system.

## Assess
3. Scope: does the change serve a stated goal? Flag scope creep, gold-plating, or gaps.
4. Design: check boundaries, cohesion/coupling, and patterns against the existing
   architecture; flag drift and second-way-of-doing-things duplication.
5. Organization & efficiency: structure, naming, duplicated capability, and complexity
   or hotspots that matter to the product.

## Prioritize & frame
6. Rank findings by product/system impact; bucket as Fix now / Track as debt / Optional.
7. For each judgment call, give the tradeoff and a recommendation; leave the decision open.

## Output
Return a concise report: an overall verdict on scope-fit and design health, prioritized
findings (each tied to a project goal or design principle, with location), the key
tradeoffs, and what to defer. No line-by-line nitpicking.
```

## Out of scope

- **The universal agent mechanics** — `description`/`tools`/`permissionMode`/`model`
  rules live in `agent-authoring`; this skill assumes them.
- **Line-level correctness review** — bug/security/regression hunting on a diff is a
  code-reviewer's job, not a product-manager agent's.
- **Developer agents** — agents that *write* code are `developer-agent-authoring`.
- **Doing the PM work** — this skill designs the assessor; it doesn't set the
  roadmap, write the scope, or perform the assessment the agent is for.
