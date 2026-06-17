# Decisions (archived)

> **Frozen archive.** This is the former `.claude/DECISIONS.md`, migrated into the
> `session-memory` system on 2026-06-17 when it replaced the DECISIONS workflow. It
> is now an append-only log: kept for full rationale, never rewritten. New decisions
> go to `.claude/memory/INDEX.md` (Decisions section) and new session logs alongside
> this file. The one-line summaries in INDEX point back here.

A running log of structural decisions for this repo. Newest first.

## 2026-06-17 — Factory authoring commands: the `add-*` family

**Context.** The factory `commands/` layer was an empty stub. Scaffolding a new asset
meant retyping the same setup each time (correct path, frontmatter, structure). We
wanted one-shot scaffolders, one per asset layer.

**Decision.** Shipped five authoring commands in `.claude/commands/`: `add-skill`,
`add-agent`, `add-command`, `add-hook`, `add-workflow`. Each is a single-shot prompt
template (`<name>.md`, filename == command name) with lightweight frontmatter
(`description`, `argument-hint`) and a body that: (1) loads the relevant authoring
expertise — `add-agent` invokes `agent-authoring` and points to the specialized
`developer-`/`product-manager-`/`knowledge-agent-authoring` skills; the others cite
their layer README; (2) **confirms placement** — factory meta-asset
(`./.claude/<layer>/`) vs. a product for a consumer (`example-project/.claude/<layer>/`
or another path), defaulting to the factory; (3) scaffolds the file(s) with correct
frontmatter/structure; (4) verifies against the conventions.

**Scope.** Scaffolders only — no `/validate-asset` or `/add-context` yet (noted as
future). Commands delegate authoring depth to the meta-skills/READMEs rather than
duplicating it, so guidance stays single-sourced.

## 2026-06-17 — Fourth factory meta-skill: `knowledge-agent-authoring`

**Context.** The agent-family meta-skills covered building (`developer`) and assessing
(`product-manager`) code, but not the third common stance: agents that *own knowledge*
— maintaining context/knowledge bases and retrieving from them. We added a playbook
for that.

**Decision.** Shipped `.claude/skills/knowledge-agent-authoring/SKILL.md`, a meta-skill
for designing **knowledge agents**: subagents that curate a corpus (docs, notes,
memory, a vector store) and/or answer queries from it with grounded, ranked,
context-efficient results. It **layers on top of** `agent-authoring` and is the third
sibling alongside `developer-` and `product-manager-agent-authoring`. Distinctively, it
**spans two modes** — retrieval-only (`tools` read-only, `permissionMode: plan`) and
curation (`Edit`/`Write`, `acceptEdits` with scope limited to the corpus) — and the
frontmatter guidance branches on mode. It establishes the trait set (source grounding
& citation, honest gaps, multi-strategy ranked retrieval, query understanding, KB
organization, freshness/lifecycle, dedup/coherence, provenance/trust, context
efficiency, faithful synthesis), an orient→retrieve / orient→curate mandate shape
anchored to the corpus index and entry schema, a checklist, anti-patterns, a template,
and a worked `docs-retriever` example.

**Scope.** Meta-skill only. It does not build retrieval infrastructure (vector DB /
index — an MCP-server job the agent *uses*), is not for developer or product-manager
agents, and does not curate the corpus or answer queries itself.

## 2026-06-16 — Third factory meta-skill: `product-manager-agent-authoring`

**Context.** With `developer-agent-authoring` covering agents that *write* code, we
wanted its assessor counterpart: a playbook for agents that evaluate code at the
**project altitude** — scope fit, system/application design, organization, and
efficiency — rather than line-level correctness.

**Decision.** Shipped `.claude/skills/product-manager-agent-authoring/SKILL.md`, a
meta-skill for designing **product-manager agents**: read-only subagents that assess
changes against the whole project's scope and design and return a prioritized report.
It **layers on top of** `agent-authoring` (defers the universal mechanics) and is the
deliberate sibling of `developer-agent-authoring` — same structure, opposite stance
(build vs. assess). It establishes assessor defaults (`tools` read-only,
`permissionMode: plan`, `model: opus`), the trait set (scope alignment, system
design, organization, system-level efficiency, coherence, maintainability,
prioritization, tradeoff framing), an orient→assess→prioritize mandate shape anchored
to project intent (`CLAUDE.md`/README/`DECISIONS.md`/roadmap), a checklist,
anti-patterns, a template, and a worked `architecture-scope-reviewer` example.

**Scope.** Meta-skill only. It is not for line-level correctness review (a
code-reviewer's job), not for developer agents, and does not perform the assessment
itself.

## 2026-06-16 — Second factory meta-skill: `developer-agent-authoring`

**Context.** `agent-authoring` covers the universal mechanics of any subagent, but
designing an agent that *develops code well* in a given language needs more: project
structure, convention adherence, toolchain use, a verification gate, and dependency
hygiene. We wanted a dedicated playbook for that common case.

**Decision.** Shipped `.claude/skills/developer-agent-authoring/SKILL.md`, a
meta-skill for designing **developer agents** — language/stack-specialist subagents
that implement and maintain code. It explicitly **layers on top of** `agent-authoring`
(defers the universal `description`/`tools`/`permissionMode`/`model`/mandate rules to
it) and adds the developer specialization: when an agent beats an in-session
development skill, developer-specific frontmatter defaults (`Bash` in the allowlist,
`acceptEdits`), the trait set to bake in (language mastery, structure, conventions,
tooling, testing/verification, efficiency, dependency hygiene, readability, scope
discipline), a discover→implement→verify mandate shape, per-language tailoring
anchors, a checklist, anti-patterns, a template, and a worked `python-feature-dev`
example.

**Scope.** Meta-skill only. It teaches authoring the agent; it does not write the
agent's domain code, and it is not for non-developer agents (reviewers, researchers)
— those remain plain `agent-authoring` jobs.

## 2026-06-12 — First factory meta-skill: `agent-authoring`

**Context.** The factory `.claude/skills/` layer was a stub — meta-skills were
described but none existed. We needed the first one.

**Decision.** Shipped `.claude/skills/agent-authoring/SKILL.md`, a meta-skill that
teaches how to author Claude Code subagents (`.claude/agents/<name>.md`): writing a
triggering `description`, scoping the `tools` allowlist, choosing the default
permission posture (`permissionMode`), picking the `model`, and writing the
system-prompt mandate. It is grounded in the durable agent fields
(`name`/`description`/`tools`/`permissionMode`/`model`) and defers the volatile long
tail to `/agents` and the official sub-agents docs rather than hard-coding it.

**Scope.** Meta-skill only — no companion `draft-agent` authoring agent yet, and
no `skill-authoring` meta-skill yet (the new skill defers to it as future work).

## 2026-06-11 — Split into a factory (`.claude/`) and a mock consumer (`example-project/`)

**Context.** After adopting the `.claude/` layout (below), the domain skills and
context docs sat in the repo's *own* `.claude/`, implying this repo runs them. It
doesn't — they're *products*. The repo's real job is to **author** reusable Claude
Code assets for downstream projects. The single-`.claude/` framing conflated the
design environment with its output.

**Decisions.**

1. **The repo is a factory with two halves.** Root `.claude/` is the factory's
   **design environment** (meta-tooling for *authoring* assets); `example-project/`
   is a **mock consumer project** showing what a produced `.claude/` looks like.
2. **Domain assets move to `example-project/`.** The 10 skills and 5 context briefs
   (plus the taxonomy README and the four scaffold-layer READMEs — all
   consumer-oriented) relocate to `example-project/.claude/` via `git mv`. They are
   the canonical worked examples and the thing a developer copies.
3. **Root `.claude/` keeps the same layer taxonomy as stubs, re-scoped to
   authoring.** Each layer's README now describes the meta-tool it will hold
   (meta-skills, authoring commands/agents/workflows, authoring guardrail hooks,
   authoring standards in `context/`). No meta-tooling is fabricated yet.
4. **`templates/` is dissolved into `example-project/`.** The two template files
   "pop out" as the example project's real `CLAUDE.md` and `CLAUDE.local.md`, so the
   showcase is a faithful, copy-me repo skeleton rather than a separate templates
   folder.
5. **`example-project/CLAUDE.local.md` is tracked as a labeled sample.** By
   convention this file is gitignored/personal; here it is committed deliberately as
   a visible reference. Root `.gitignore` is anchored (`/CLAUDE.local.md`) so it only
   ignores the factory's own root-level personal file, not the example's.

**Mechanics.** All relocations used `git mv` (history preserved, bodies unchanged).
No `src/` directory — the consumer half is named `example-project/` per its role.

## 2026-06-11 — Adopt the `.claude/` infrastructure layout

**Context.** The repo was a flat collection of 15 markdown files at the root — 10
skills (with `name:`/`description:` frontmatter) and 5 CLAUDE.md-style
project-instruction docs — with no organizing structure, no `CLAUDE.md`, and no
`.gitignore`. We adopted the typed `.claude/` project-infrastructure pattern
(`context/`, `hooks/`, `skills/`, `commands/`, `agents/`, `workflows/`).

**Decisions.**

1. **Empty layers are scaffolded, not fabricated.** `hooks/`, `commands/`,
   `agents/`, and `workflows/` each get a README explaining the layer's purpose.
   No example content is invented — they stay empty until a real need appears.
2. **Project-instruction docs live in `.claude/context/`.** The 5 frontmatter-less
   CLAUDE.md-style stack briefs (VSTO, C/C#, C++, Python, VBA) are reference
   context, not skills, so they belong under `context/`.
3. **`CLAUDE.md` is a library guide; the reusable pattern lives in `templates/`.**
   This repo is a library, so its `CLAUDE.md` documents the library itself.
   `templates/CLAUDE.md.template` is the portable starter that teaches the
   infrastructure pattern for use in other projects.

**Mechanics.** Files were relocated with `git mv` to preserve history; their bodies
were left byte-for-byte unchanged. Skill folders are named after each skill's
`name:` frontmatter value. No `src/` directory — this is a pure asset library.
