---
name: workflow-authoring
description: >
  Expert guidance for authoring Claude Code workflows — the multi-step
  orchestration recipes that live in a project's .claude/workflows/<name>.md. Use
  this skill whenever the user wants to design, write, scaffold, review, or fix a
  workflow: deciding whether a task even warrants a workflow vs a command/agent/skill,
  laying out ordered steps that invoke existing commands/agents/skills, specifying
  inputs/outputs and the control-flow / STOP conditions people under-specify, placing
  approval gates on outward-facing actions, and keeping the recipe declarative and
  reference-based. Trigger on phrases like "write a workflow", "author a workflow",
  "should this be a workflow or a command/agent", "orchestrate these steps",
  "multi-step automation", "workflow stop conditions", or "loop/branch/spawn agents
  to do X". For authoring agents use agent-authoring; for skills, skill-authoring;
  this skill is only about workflow definitions.
---

# Workflow Authoring

How to design and write a good Claude Code **workflow** — the multi-step
orchestration recipes that live in `.claude/workflows/<name>.md`. Use this when
building a new workflow, reviewing an existing one, or diagnosing why one wanders,
loops forever, or fires an irreversible action without asking.

## Core principles

- **A workflow orchestrates; it doesn't do.** Its value is the *control flow* —
  the ordered steps, the branches, the loops, the agents it spawns — that strings
  existing assets into a pipeline. The actual work lives in the commands, agents,
  and skills it invokes. If there's no real sequencing, it isn't a workflow.
- **Reference, don't restate.** A step names the asset it invokes by path
  (`../commands/version-set.md`, `../agents/reviewer.md`) and the hand-off; it does
  **not** re-describe that asset's whole mandate. The asset is the single source of
  truth for what it does.
- **STOP conditions are the point.** The most under-specified part of every
  workflow is *when it ends and when it bails*. Every loop needs a terminal state;
  every step needs a success criterion and a failure/stop behavior. Spell them out.
- **Declarative recipe, not a script.** A workflow `.md` is the human-authored
  recipe the model follows — keep it declarative and reference-based. It is **not**
  the deterministic Workflow runtime/tool (scripted fan-out the harness executes);
  see *Prose `.md` vs the runtime* below.
- **Approval-gate the irreversible.** Anything outward-facing or hard to undo
  (opening a PR, posting, sending, deleting, deploying) gets an explicit gate —
  either a human checkpoint or a precondition that must hold — before it fires.

## Is a workflow even the right layer?

Confirm the layer before writing anything. Pick the lightest thing that works.

| Layer | Use when | Shape |
|---|---|---|
| **Workflow** | Deterministic *multi-step* control flow that loops/branches/spawns and runs largely unattended | Ordered steps invoking other assets |
| **Command** | A single one-shot prompt you'd otherwise retype | One `/<name>` prompt |
| **Agent** | A self-contained side task in an *isolated* context that returns a summary | One mandate, fresh context |
| **Skill** | Reusable expertise/procedure applied *in* the main conversation | In-session know-how |

Quick test: *Does this string together more than one step, with branch/loop/spawn
logic, mostly without me babysitting it?* → workflow. *One prompt, one shot?* →
command. *One noisy job whose output I won't reread?* → agent (use `agent-authoring`).
*Knowledge or a procedure to apply inline?* → skill (use `skill-authoring`).

If it's a single step — even a clever one — it's a command, not a workflow. A
workflow earns its keep only when the *orchestration* is the value.

## Decide before you write

Answer these first; they map directly onto the file:

1. **Goal** — one sentence: what does the whole pipeline produce?
2. **Trigger** — what request/context should cause it? (→ `description`)
3. **Inputs / Outputs** — what it needs to start; what exists when it's done.
4. **Steps** — the ordered actions, and which asset each one invokes.
5. **Control flow** — the branches and loops, with their terminal states.
6. **STOP conditions** — success (done), failure (bail), and gates (ask first).

## Anatomy of a workflow file

One markdown file, `.claude/workflows/<name>.md`, **no frontmatter required** for
the body itself — but lead with a strong purpose line and (when the workflow should
auto-trigger) a `description`. The body has these sections:

- **Purpose line** — a crisp sentence: what the workflow orchestrates and produces.
- **Inputs / Outputs** — one line each. What must exist to start; what exists at the end.
- **Steps** — numbered, ordered. Each step: the action, the **asset it invokes**
  (by path), and the **hand-off** (what it passes to the next step).
- **Control flow / STOP conditions** — the branches and loops, each loop's terminal
  state, each step's success criterion and failure/stop behavior, and approval gates.
- **Invokes** — a manifest listing every command / agent / skill / hook / tool the
  workflow uses, by path. References, not re-descriptions.

See `../../workflows/ship-version.md` and `../../workflows/author-asset.md` for the
canonical shape — note how their Steps name a command per step, the *Control flow /
stop conditions* section enumerates the done/bail/ask cases, and *Invokes* lists
assets by path rather than restating them.

## Writing the `description` (so it triggers)

If the workflow should auto-load, the `description` is what makes Claude reach for
it — same discipline as a skill or agent.

- **Lead with the use case, then name concrete triggers** ("ship this version",
  "run the release pipeline", "advance the roadmap step").
- **Distinguish it from the one-shot command** it may wrap — say *orchestrate /
  pipeline / end to end*, so it isn't confused with the single command inside it.
- If a workflow is only ever run by hand (`/<name>` or by name), a purpose line may
  be enough — but a sharp description never hurts.

## Writing the Steps (the orchestration)

Each step is an instruction to *invoke an existing asset*, plus the hand-off:

- **One asset per step where possible.** "Run `/version-set` to write `.meta/version`"
  beats inlining what `version-set` does. The command owns its own behavior.
- **State the hand-off.** What does this step produce that the next consumes? That
  chain is the workflow's spine.
- **Spawn a subagent when the work is noisy or needs isolation; call a skill inline
  when you want its expertise applied in the main context.** Reach for an agent to
  keep verbose output (searches, test runs, multi-file analysis) out of the main
  thread; reach for a skill when the procedure should shape the in-session work.
- **Don't re-derive conventions mid-workflow.** If a step needs a format or rule,
  point at the asset/brief that owns it; don't paste the rules into the step.

## Control flow / STOP conditions (the under-specified part)

This is where weak workflows fail. Be explicit about all three:

- **Success — when it's done.** The terminal state that means "stop, report." e.g.
  "PR open with a title/body matching the version's goals → done; report the URL."
- **Failure / bail — when it stops short.** The precondition that, if unmet, halts
  the workflow instead of guessing. e.g. "`.meta/version` has no goals → stop and
  run `/version-set` first; never invent goals."
- **Loops need a terminal state.** Any "repeat for each / until" must name what ends
  it — a counter, an empty queue, a condition. An unbounded loop with no exit is a bug.
- **Branches name their conditions.** "If X → step 4; else → step 5." No implicit forks.
- **Approval gates on outward-facing/irreversible steps.** Before a PR, post, send,
  delete, or deploy: either pause for a human OK or assert a precondition. Genuine
  scope/judgment calls belong to the caller — ask, don't guess.

## Orchestration design principles

- **Reuse, don't inline.** Every step should lean on an existing command/agent/skill.
  If a step's logic doesn't exist as an asset yet, that's a signal to author *that*
  asset first (via `author-asset`), not to bury its logic in the workflow.
- **Make each step's success and failure explicit.** A step with no "what good looks
  like" and no "what to do if it fails" is a gap.
- **Idempotence / resumability.** Prefer steps that are safe to re-run and a workflow
  that can resume from where it stopped (check "already done?" before acting). State
  that carries between runs lives in a file (`.meta/version`, memory), not in the chat.
- **Least surprise outward.** Keep irreversible actions late, gated, and few.

## Prose `.md` vs the deterministic runtime

Don't conflate two things that share the word "workflow":

- **The workflow `.md`** (this skill) — a *human-authored recipe* the model reads and
  follows, with judgment at each step. Declarative, reference-based, lives in
  `.claude/workflows/`.
- **The Workflow tool/runtime** — a *deterministic* harness mechanism that scripts
  fan-out/parallel execution with no model judgment between steps.

A workflow `.md` may *describe* spawning agents in parallel, but it remains a recipe,
not the executor. Author the recipe; keep it declarative; let the steps invoke assets.

## Authoring checklist

- [ ] Filename `<name>.md` matches the workflow's job; lives in the right `.claude/workflows/`.
- [ ] Opens with a crisp purpose line (and a `description` if it should auto-trigger).
- [ ] **Inputs** and **Outputs** each stated in a line.
- [ ] Steps are numbered, ordered, and each names the **asset it invokes** + the hand-off.
- [ ] Steps reference assets by path — they do **not** restate those assets' mandates.
- [ ] Control flow names every branch condition and every loop's terminal state.
- [ ] STOP conditions cover success (done), failure (bail), and approval gates.
- [ ] Every outward-facing / irreversible step has an explicit gate.
- [ ] An **Invokes** manifest lists every command/agent/skill/hook/tool by path.
- [ ] Every referenced asset exists (or is flagged as still to be created).

## Anti-patterns

- **Restating an agent's/command's whole mandate inline** → the asset is the source
  of truth; name it and pass the hand-off, don't duplicate it.
- **Missing STOP conditions** → the workflow doesn't know when it's done or when to bail.
- **An unbounded loop with no terminal state** → it never ends; name the exit.
- **An outward-facing step (PR / post / send / deploy) with no approval gate** → blast
  radius with no checkpoint.
- **Inlining logic that should be its own asset** → author the command/agent/skill,
  then invoke it.
- **A single-step "workflow"** → that's a command; don't dress it up as orchestration.
- **State held only in the chat** → not resumable; persist cross-step state to a file.
- **Re-deriving conventions mid-step** → point at the brief/asset that owns them.

## Template

```markdown
# <workflow-name>

<One crisp sentence: what this workflow orchestrates and produces.>

**Inputs:** <what must exist to start>.
**Output:** <what exists when it's done>.

## Steps

1. **<Action>.** Run **`/<command>`** (or spawn `../agents/<agent>.md`) to <do X>;
   it produces <hand-off> for the next step.
2. **<Action>.** Invoke <asset by path> with <input>; on success → <hand-off>.
3. **<Gated action>.** Before <irreversible action>, confirm <precondition> /
   pause for OK, then <do it>.

## Control flow / STOP conditions

- <branch>: if <condition> → step N; else → step M.
- <loop>: repeat <step> for each <item> until <terminal state>.
- Success: <terminal state that means done> → report <what>.
- Bail: <precondition unmet> → **stop**; <what to do instead>. Never <guess X>.
- Gate: <outward-facing step> requires <approval/precondition> first.

## Invokes
- Commands: `../commands/<name>.md`, …
- Agents: `../agents/<name>.md`, …
- Skills: `<skill-name>`, …
- Hooks / Tools: `../hooks/<name>.py`, `mcp__…`, …
```

### Worked example — a release pipeline (sketch)

```markdown
# ship-release

Cut a release: verify the build, tag it, and open the release PR.

**Inputs:** a green main branch and a version label.
**Output:** a tag pushed and a release PR open, with the PR URL recorded.

## Steps
1. **Verify.** Spawn `../agents/build-verifier.md` to run the suite; it returns
   pass/fail + a summary (isolated, so logs stay out of the main context).
2. **Tag.** If pass → run **`/tag-version`** to create the tag from the label.
3. **Open the PR.** Gate: confirm the tag exists, then open the PR via
   `mcp__github__create_pull_request`; record the URL.

## Control flow / stop conditions
- Step 1 fails → **stop**; report the failures. Do not tag a red build.
- Tag already exists → skip step 2 (idempotent), proceed to step 3.
- PR open with the tag in its body → done; report the URL.
- Gate: never open the PR before the tag is confirmed present.

## Invokes
- Agents: `../agents/build-verifier.md`.
- Commands: `../commands/tag-version.md`.
- Tools: `mcp__github__create_pull_request`.
```

## Out of scope

- **Authoring agents / skills / commands / hooks / context** — different layers,
  different rules. Use `agent-authoring`, `skill-authoring`, and the matching layer
  README; this skill is only about workflow definitions.
- **Building the assets a step invokes** — if a step needs a command/agent/skill that
  doesn't exist yet, author it (e.g. via `author-asset`) and reference it here.
- **Doing the workflow's domain work** — this skill designs the recipe; it doesn't
  run the pipeline.
```
