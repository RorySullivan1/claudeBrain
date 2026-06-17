---
name: developer-agent-authoring
description: >
  Expert guidance for designing **developer agents** — Claude Code subagents
  specialized at writing and maintaining code in a specific language or stack. Use
  this skill whenever the user wants to design, write, scaffold, or review an agent
  whose job is to *develop software*: a language/stack specialist that implements
  features, structures projects, follows the codebase's conventions, keeps changes
  efficient and well-organized, and verifies its own work. Trigger on phrases like
  "create a developer agent", "build a Python/TypeScript/Go/Rust coding agent",
  "agent that writes <language> code", "language specialist subagent", "set up an
  agent to develop in <stack>", or "design a feature-dev agent". This builds on the
  general `agent-authoring` skill — use that for the universal mechanics
  (description, tools, permissions, model, mandate); use *this* for the
  developer-specific traits layered on top. It teaches how to author the agent; it
  does not write the agent's domain code itself.
---

# Developer Agent Authoring

How to design a **developer agent** — a subagent whose mandate is to *produce and
maintain code* in a given language or stack. A developer agent is the isolated,
summary-returning counterpart to an in-session development skill: you reach for it
when you want language-specialist work to run in its own context and hand back a
clean diff plus a short report, rather than narrate every edit into the main
session.

> **Start with `agent-authoring`.** That skill owns the universal anatomy —
> `description` as the trigger, the `tools` allowlist, `permissionMode`, `model`,
> and how to write a mandate. This skill assumes those basics and adds only what
> makes an agent a *good developer*. When the two seem to conflict, the general
> mechanics win; this layer specializes them.

## Core principles

- **A developer agent must change code, then prove it works.** Unlike a read-only
  reviewer, its whole point is to edit, build, and test. An agent that writes code
  but never runs it is half-built — verification is part of the mandate, not a bonus.
- **Specialize on one language/stack.** "A coding agent" is too broad to be good.
  Pin it to a language and toolchain (Python 3.12 + uv + ruff + pytest, or
  TypeScript strict + pnpm + vitest, …) so its idioms, layout, and tooling are
  concrete.
- **Fit the codebase before imposing on it.** The agent's first job in any real repo
  is to *discover* existing conventions (structure, naming, lint config, test
  patterns) and match them. New patterns are a last resort, not a default.
- **Small, reviewable, reversible changes.** Favor focused diffs over sweeping
  rewrites. A developer agent that refactors half the repo unprompted is a liability.
- **Efficiency is plural.** It means runtime performance *and* lean dependencies
  *and* a tight context budget — the agent should read what it needs, not the whole
  tree, and return a summary, not a transcript.

## Is a developer *agent* the right tool?

A lot of "developer expertise" is better delivered as a **skill** that runs in the
main conversation (like the `python-development` skill in `example-project/`). Choose
the agent form only when isolation pays off.

| Want | Use |
|---|---|
| Expertise applied *in* the current chat, with full back-and-forth | a development **skill** |
| A self-contained build/feature/fix that returns a diff + summary | a developer **agent** |
| A one-off "write me this function" prompt you'd retype | a **command** |
| Format/lint/typecheck that must *always* run on save/commit | a **hook** |

Quick test: *Will this dump a lot of exploration and tool output I won't reread, and
can it hand back just the diff and a short report?* → developer agent. Otherwise a
skill is lighter.

## Decide before you write

On top of the six questions in `agent-authoring`, settle these developer-specific
ones first:

1. **Language & version.** Which language/stack, pinned to a version? (→ role line)
2. **Mode of work.** Greenfield scaffolding, feature work in an existing repo, or
   maintenance/refactor? Each implies a different workflow and risk posture.
3. **Toolchain.** Formatter, linter, type checker, test runner, package/build tool —
   name them, because the agent must invoke them. (→ body + `tools`)
4. **Verification bar.** What must pass before the agent calls a task done — tests
   green? type check clean? lint clean? build succeeds? (→ body workflow)
5. **Change budget.** May it touch only the files in scope, or refactor neighbors?
   May it add dependencies, or must it ask first? (→ body guardrails)
6. **Autonomy.** Can it edit and run tests unattended (`acceptEdits`), or must it
   stop for review? (→ `permissionMode`)

## The developer traits to bake in

The body is where a generic agent becomes a *good engineer*. Encode these explicitly
— each maps to instructions or guardrails in the mandate:

- **Language mastery.** Idioms, standard library, modern syntax for the pinned
  version, and the patterns that language rewards (and the anti-patterns it punishes).
- **Project structure & organization.** The conventional layout for the stack
  (`src/` package layout, module boundaries, entry points, where tests/config live),
  and clear separation of concerns — keep modules cohesive and loosely coupled.
- **Convention adherence.** Discover and follow the *existing* repo's style, naming,
  and patterns before writing; match surrounding code rather than importing personal
  taste.
- **Tooling fluency.** Run the formatter, linter, and type checker; use the project's
  package manager and build tool correctly; lean on the test runner.
- **Testing & verification discipline.** Write or update tests for new behavior, run
  them, and never report "done" on unverified code. Surface failures honestly with
  the actual output.
- **Efficiency.** Reasonable algorithmic choices and data structures; avoid needless
  allocation/IO; but don't micro-optimize past readability without cause. Also keep
  *its own* work efficient — read targeted files, not the whole repo.
- **Dependency & security hygiene.** Prefer the standard library; justify and pin new
  dependencies; never paste secrets; validate external input; follow least-privilege.
- **Readability & documentation.** Clear names, comments at the density of the
  surrounding code, docstrings/types where the stack expects them — code a teammate
  can maintain.
- **Error handling & edge cases.** Handle failure paths the language idiom prefers
  (exceptions, `Result`, error returns); don't swallow errors silently.
- **Scope discipline.** Stay inside the assigned change; flag tempting-but-unrelated
  fixes instead of doing them; stop and ask when a decision is genuinely the caller's.

> The first four are the traits you asked for (language, structure, efficiency,
> organization). The rest — conventions, tooling, testing, dependencies,
> readability, error handling, scope discipline — are the ones that, in practice,
> separate an agent that *compiles* from one you'd let touch a real codebase.

## Frontmatter for developer agents

Apply `agent-authoring`'s rules, with these developer defaults:

- **`tools`** — a developer agent mutates and runs code, so it needs more than a
  reader: typically `Read, Grep, Glob, Edit, Write, Bash`. `Bash` is what lets it
  format, build, and run tests — usually non-negotiable here. Still an allowlist: add
  only what the workflow demands.
- **`permissionMode`** — `acceptEdits` is the common fit so it can work through edits
  and run its toolchain unattended, *provided* `tools` and scope are tight. Use
  `default` when a human should approve each change; avoid `bypassPermissions` unless
  the automation is trusted and narrow.
- **`model`** — `sonnet` for routine feature/maintenance work; `opus` when the job
  involves architecture, tricky concurrency, or multi-file design judgment; `haiku`
  only for the most mechanical, high-volume edits.

## Writing the mandate (the body)

Structure a developer agent's system prompt so it discovers, builds, then verifies:

1. **Role line, with the stack.** "You are a senior Python 3.12 engineer working in
   this repository." Name the language and version up front.
2. **Orient before editing.** Step one is always: read the relevant code and config
   (`pyproject.toml`, `tsconfig.json`, lint config, nearby modules) and infer the
   conventions to follow. Forbid large speculative reads — target the task.
3. **Implementation workflow.** Numbered: understand the request → make the focused
   change matching existing patterns → keep the diff minimal → update/add tests.
4. **Verification gate.** Spell out the commands to run and the bar to clear (e.g.
   "run `ruff check`, `mypy`, and `pytest`; do not finish until they pass"). Require
   honest reporting of any failure with the real output.
5. **Guardrails.** State the change budget, dependency policy, and "stop and ask"
   conditions — the agent starts fresh and won't infer them from CLAUDE.md.
6. **Output format.** A concise summary: what changed and why, the files touched, the
   verification result (tests/lint/types), and anything deferred or needing a
   decision. The diff is the artifact; the summary is the report.

## Tailoring to a language

Keep the agent language-specific by baking the stack's concrete toolchain and layout
into the body. A few anchors (verify current tools per project):

- **Python** — `src/` layout, `pyproject.toml`; format/lint with `ruff` (or
  `black`+`flake8`), type-check with `mypy`/`pyright`, test with `pytest`; manage with
  `uv`/`poetry`/`pip`.
- **TypeScript/JS** — strict `tsconfig`; `eslint`+`prettier`; `vitest`/`jest`; package
  manager `pnpm`/`npm`; respect ESM/CJS and the framework's conventions.
- **Go** — standard project layout and modules; `gofmt`/`goimports`, `go vet`,
  `golangci-lint`, `go test ./...`; prefer the standard library.
- **Rust** — Cargo workspace; `cargo fmt`, `cargo clippy -D warnings`, `cargo test`;
  idiomatic `Result`/`?` error handling.

Don't hard-code volatile version numbers or tool flags as gospel — tell the agent to
confirm them against the repo's actual config.

## Authoring checklist

- [ ] Passes the base `agent-authoring` checklist (unique name, sharp description,
      least-privilege tools, right permission posture, fitting model, tight body).
- [ ] Specialized to **one** language/stack, pinned to a version.
- [ ] Body tells it to **discover and follow existing conventions** before writing.
- [ ] `tools` includes what it needs to **edit and run** code (usually `Bash`).
- [ ] Mandate has an explicit **verification gate** (tests/lint/types) it must clear.
- [ ] Guardrails state the **change budget** and **dependency policy**.
- [ ] Output format returns a **diff + concise report**, not a transcript.

## Anti-patterns

- **Writes code, never runs it** → no verification gate; ships unproven changes.
- **Language-agnostic "coding agent"** → too broad to develop anything idiomatically.
- **Ignores the repo's conventions** → produces correct-but-foreign code that fails review.
- **Unbounded refactors** → no change budget; touches far more than the task.
- **Adds heavy dependencies freely** → no dependency policy; bloats and risks the project.
- **Assumes a language version or tool** → breaks against the repo's actual config.
- **`bypassPermissions` for convenience** → use `acceptEdits` with tight scope instead.

## Template

```markdown
---
name: <lang>-<mode>-dev            # e.g. python-feature-dev
description: >
  Senior <language> engineer for <mode: feature work / maintenance / scaffolding> in
  this repo. Use proactively when <situation>. Returns a diff plus a verification report.
tools: Read, Grep, Glob, Edit, Write, Bash
permissionMode: acceptEdits        # tight scope; weakest posture that still works
model: sonnet                      # opus for architecture-heavy work
---

You are a senior <language> <version> engineer working in this repository.

## Orient first
1. Read the task-relevant code and config (<manifest>, lint/type config, nearby modules).
2. Infer and follow the existing conventions — match surrounding code; don't impose new patterns.

## Implement
3. Make the focused change; keep the diff minimal and within scope.
4. Add or update tests for the new behavior.

## Verify (do not finish until these pass)
5. Run <formatter>, <linter>, <type checker>, and <test runner>.
6. If anything fails, fix it or report it honestly with the real output.

## Guardrails
- Change budget: <which files may be touched>.
- Dependencies: <prefer stdlib; ask before adding>.
- Stop and ask when <a decision is the caller's>.

## Output
Return a concise report: what changed and why, files touched, the verification
result (tests/lint/types), and anything deferred or needing a decision.
```

### Worked example — a Python feature agent

```markdown
---
name: python-feature-dev
description: >
  Senior Python 3.12 engineer for feature work in this repo. Use proactively when the
  user asks to implement, add, or build a Python feature and wants it tested. Returns
  a diff and a verification report.
tools: Read, Grep, Glob, Edit, Write, Bash
permissionMode: acceptEdits
model: sonnet
---

You are a senior Python 3.12 engineer working in this repository.

## Orient first
1. Read `pyproject.toml`, the lint/type config, and the modules near the change to
   learn the layout, style, and test conventions.
2. Match what you find — naming, typing, structure. Do not introduce new patterns
   unless the task requires it.

## Implement
3. Write the feature as a minimal, focused diff that fits the existing package layout.
4. Add `pytest` tests covering the new behavior and important edge cases.

## Verify (do not finish until these pass)
5. Run `ruff check`, `mypy`, and `pytest`.
6. Fix failures; if something can't pass, report it with the real output, don't hide it.

## Guardrails
- Touch only the files needed for the feature; flag unrelated issues instead of fixing them.
- Prefer the standard library; ask before adding a dependency.

## Output
Return a concise report: the feature added, files touched, `ruff`/`mypy`/`pytest`
results, and anything deferred or needing a decision.
```

## Out of scope

- **The universal agent mechanics** — `description`/`tools`/`permissionMode`/`model`
  rules live in `agent-authoring`; this skill assumes them.
- **Non-developer agents** — reviewers, researchers, data-fetchers, and the like are
  plain agent-authoring jobs, not developer agents.
- **In-session development skills** — when the expertise should run in the main
  conversation, author a development *skill*, not an agent.
- **Doing the coding** — this skill designs the developer agent; it doesn't implement
  the feature the agent is for.
