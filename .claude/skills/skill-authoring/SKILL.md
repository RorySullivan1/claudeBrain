---
name: skill-authoring
description: >
  Expert guidance for authoring Claude Code skills — the skill bundles that live in a
  project's .claude/skills/<name>/SKILL.md. Use this skill whenever the user wants to
  design, write, scaffold, review, or fix a skill: deciding whether a task even warrants
  a skill (vs an agent, command, context brief, or hook), writing a description that
  triggers reliably, naming the skill and matching the folder, and structuring the
  SKILL.md body so it teaches Claude how to think and behave. Trigger on phrases like
  "write a skill", "create a skill", "author a SKILL.md", "draft a .claude/skills file",
  "skill frontmatter", "fix my skill's description", "why isn't my skill triggering",
  "is this a skill or an agent / a context doc", or "should this be a skill". For
  authoring agents use agent-authoring; this skill is only about skill definitions.
---

# Skill Authoring

How to design and write a good Claude Code **skill** — the bundles that live in
`.claude/skills/<name>/SKILL.md`. Use this when building a new skill, reviewing an
existing one, or diagnosing why a skill never gets loaded. This is the skills
analogue of `agent-authoring`.

## Core principles

- **A skill is in-session expertise.** Its value is teaching Claude *how to think and
  behave* for a recurring task type, applied **in the main conversation** — no separate
  context window, no summary handoff. If the work is really a noisy side task you won't
  reread, that's an agent, not a skill.
- **The `description` is the trigger.** The harness loads a skill by reading its
  `description` and matching the user's request. A vague description means the skill
  never fires — or worse, collides with a sibling and both under-fire. This field earns
  the most care.
- **Teach behavior, not a doc dump.** A good `SKILL.md` body is a *method* — principles,
  a workflow, worked examples, gotchas. Reference material that Claude only sometimes
  needs belongs in a context brief or a sidecar file the skill points to, not inline.
- **One coherent job.** A skill that "helps with the codebase" triggers poorly and
  teaches nothing well. Scope it to a single nameable discipline.
- **Fold before you fork.** Before creating a skill, check whether an existing one
  should be *extended* instead. Skill proliferation makes triggering worse, because
  overlapping descriptions collide.

## Is a skill even the right layer?

Confirm the layer before writing anything. The universal layer-choice mechanics live in
`agent-authoring`'s *Is an agent even the right tool?* — read that for the full table.
The skill-specific calls:

| Pick a… | when the thing is… | not a skill because… |
|---|---|---|
| **Skill** | reusable expertise/procedure that should run *in* this conversation | — |
| **Agent** | a self-contained side task whose output you won't reread; you want a summary back | it needs an isolated context window |
| **Command** | a quick one-shot prompt you'd retype, with no standing expertise | a skill is loaded by trigger, not typed each time |
| **Context brief** | reference knowledge Claude deep-reads on demand (schemas, stack briefs) | a skill teaches *how to act*, not *what the facts are* |
| **Hook** | something that must *always* fire on a lifecycle event | a skill is advisory; the model can ignore it |

Quick test: *Is this know-how I want applied whenever a certain kind of task comes up,
in the main thread?* → skill. *Is it mostly facts I'll look up?* → context brief
(the planned `context-vs-skill` skill owns that boundary in depth). *Must it fire
deterministically?* → hook.

## Fold-first: should this skill exist at all?

Skills are permanent context cost — every skill's `description` sits in the routing
surface forever. Before authoring, run the `skill-distiller` discipline:

1. **Significance gate** — the material must clear all three: **recurrence** (it'll come
   up again), **non-obviousness** (it encodes procedure/gotchas you wouldn't reliably
   reproduce), and **generality** (it transfers beyond this instance). Fail any → it's a
   memory note or a one-off, not a skill.
2. **Redundancy check** — compare against existing skills (`skills.py similar "<desc>"`).
   If an existing skill covers it → **extend that skill's SKILL.md**, don't spawn a
   sibling. Only author net-new when nothing is close. The default on real overlap is
   "extend," not "create."

If it survives both gates, proceed. If it's borderline, enqueue it and wait for one more
occurrence rather than authoring a half-useful skill.

## Decide before you write

Answer these first; they map directly onto the file:

1. **Job** — one sentence: what discipline does this skill teach?
2. **Trigger** — what requests/contexts should load it, and what should it *defer*? (→ `description`)
3. **Boundaries** — which sibling skills does it border, and how is the line drawn? (→ `description`)
4. **Method** — the core principles and workflow it imparts. (→ body)
5. **Examples** — the worked cases that make the method concrete. (→ body)
6. **Watch-outs** — the failure modes a practitioner must avoid. (→ body)

## Anatomy of a skill bundle

A skill is a **folder** containing a `SKILL.md` (plus any sidecar files it references):

- **Location.** `.claude/skills/<name>/SKILL.md` for a project (checked in, shared) or
  `~/.claude/skills/<name>/SKILL.md` for personal, cross-project skills.
- **Folder name == `name:`.** The folder name *must* equal the frontmatter `name`.
  Renaming a skill means renaming both. This is a hard convention.
- **Frontmatter is minimal:** just `name` and `description`. No `tools`/`model`/
  `permissions` — a skill is advice loaded into the conversation, not an isolated runner.

| Field | Required | What it does |
|---|---|---|
| `name` | yes | Unique identifier; **kebab-case**; **must equal the folder name**. |
| `description` | yes | Drives loading — when the harness should pull this skill in. |

The body is markdown with no fixed schema, but the **best skills converge on a shape**
(principles → method → examples → watch-outs) — see *Writing the body* below.

## Writing the `description` (the part that matters most)

This single field decides whether the skill is ever loaded. Write it for *triggering*,
not for documentation. The repo's strongest descriptions (see `vba-review`,
`python-development`, `skill-distiller`) all do the same things:

- **Lead with what it is, in one clause.** "Expert VBA code reviewer for Excel/Word/
  Outlook/PowerPoint macros…" — identity first, so a match is obvious.
- **Add an explicit "use when…" with concrete scenarios.** Spell out the situations:
  "whenever the user pastes VBA and asks for a review, audit, or help improving it."
  Generic intent under-fires; concrete scenarios fire.
- **List trigger phrases and synonyms.** Quote the things a user actually says —
  "what's wrong with this macro", "is this correct", "why is this slow". Cover the
  phrasings that *don't* contain the obvious keyword, too: `python-development` triggers
  on "implement" / "I need code that" even without the word "Python"; `skill-distiller`
  fires even when the user never says "skill".
- **Name the implicit-trigger case.** If the skill should fire on a *signal* rather than
  a keyword ("a freshly-derived reusable procedure is the signal"), say so — otherwise
  it only fires when explicitly invoked.
- **Draw the boundary lines.** End with deferral/collision clauses that keep it from
  fighting its neighbors: "For C#/VB.NET Office add-ins use VSTO-review instead; to
  author the tests a review asks for, use vba-code-test-writing." A crisp boundary is
  what stops two adjacent skills from both under-firing. Every authoring skill in this
  repo ends this way ("For authoring skills use skill-authoring; this skill is only
  about agent definitions").

If a skill never triggers, the description is too generic or collides with a sibling —
sharpen the use case and tighten the boundary before touching the body.

## Naming and the folder rule

- **`name` is kebab-case** and names the discipline (`vba-review`, `python-development`),
  not a vague helper label.
- **The folder must equal `name`.** `.claude/skills/vba-review/` ⇄ `name: vba-review`.
  A mismatch means the skill won't resolve. When you rename, rename both.
- **Keep names unique** across the skills tree; colliding names resolve unpredictably.

## Writing the body (teach how to think)

The body is the skill's whole teaching. Keep it about *behavior*, not reference. The
shape that works across the repo's best skills:

1. **One-line framing.** A sentence stating the job and its stance ("You review VBA for
   the defects that actually bite…"). Sets the altitude immediately.
2. **Core principles.** A short list of the opinions that govern the work — the
   judgment calls, stated as rules ("Correctness first, cleverness second").
3. **Clarify-first step, where relevant.** For skills where context changes the answer,
   tell Claude what to confirm before acting (`python-development`'s "what to ask before
   writing non-trivial code"; `vba-review`'s "what to ask for if absent"). Skip it for
   skills that act on whatever is in front of them.
4. **The method.** The core of the skill: an ordered workflow, a priority order, a
   checklist, or a standards section — whatever encodes *how to do the job well*. This
   is where a generic responder becomes a specialist.
5. **Worked examples.** Concrete cases — ideally a bug-and-fix or before/after pair —
   that show the method applied. Examples are load-bearing; they teach more than prose.
6. **A "Watch Out" section.** The 2–4 traps that separate a good outcome from a
   plausible-looking wrong one. Every strong skill here has one.
7. **Out of scope / deferrals.** Restate what this skill does *not* do and where that
   work goes — it reinforces the description's boundaries.

Keep it tight. If a chunk is reference material Claude needs only occasionally, move it
to a sidecar file or a context brief and point at it; don't bloat the always-considered
body. A skill that builds on a base skill should be written as a **delta** — say so up
front and cover only the difference (see `developer-agent-authoring`: "this layers on
`agent-authoring` — read that first; this skill covers only the delta").

## Authoring checklist

- [ ] Cleared the fold-first gates: significant, and net-new (not an extension of an existing skill).
- [ ] `name` is unique, kebab-case, and **equals the folder name**.
- [ ] `description` leads with identity, has a concrete "use when…", lists trigger phrases/synonyms.
- [ ] `description` names the implicit-trigger signal if the skill should fire without a keyword.
- [ ] `description` draws boundary/deferral lines against neighboring skills.
- [ ] Body teaches behavior: principles, a method, worked examples, a "Watch Out".
- [ ] Reference-only material is in a sidecar/context brief, not padding the body.
- [ ] Tested: a realistic request actually loads the skill, and adjacent requests don't mis-route.

## Anti-patterns

- **Generic description** ("helps with Python") → never loaded, or loaded for everything.
- **No boundary lines** → collides with a sibling skill; both under-fire.
- **Folder name ≠ `name`** → the skill doesn't resolve at all.
- **Body is a reference dump** → bloats context and buries the method; move facts to a brief.
- **Two loosely-related jobs in one skill** → triggers poorly; split or rescope.
- **A new skill where an existing one should be extended** → proliferation degrades all triggering.
- **Frontmatter borrowing agent fields** (`tools`, `model`) → skills don't take them; drop them.
- **Examples-free prose** → the method stays abstract; add a worked case.

## Template

```markdown
---
name: <kebab-case-name>            # unique; MUST equal the folder name
description: >
  <One-clause identity.> Use this skill whenever <concrete use-when scenarios>.
  Trigger on phrases like "<phrase>", "<synonym>", or <implicit signal>.
  <Boundary line: defer X to skill Y; for Z use W — this skill is only about …>.
---

# <Title>

<One-line framing: the job and its stance.>

## Core principles
- **<Opinion as a rule>.** <Why it governs the work.>
- **<Opinion as a rule>.** <…>

## <Clarify first — only if context changes the answer>
Confirm before acting: <the few things that change the approach>.

## <The method — workflow / priority order / standards>
1. <Step or priority>
2. <…>

## <Worked example>
<A bug-and-fix or before/after pair that shows the method applied.>

## Watch Out
1. **<Trap>.** <The plausible-looking wrong outcome it causes.>
2. **<Trap>.** <…>

## Out of scope
- <What this skill does not do, and where that work goes instead.>
```

## Out of scope

- **Authoring *agents*** — `description`/`tools`/`permissionMode`/`model` and the
  isolated-context mechanics live in `agent-authoring`; this skill is only about skill
  definitions.
- **Skill vs. context brief in depth** — when knowledge is reference rather than
  behavior, that boundary is the planned `context-vs-skill` skill's job.
- **Deciding *whether* something is skill-worthy** — the significance/redundancy gates
  are `skill-distiller`'s; this skill assumes the decision is made and teaches the writing.
- **Authoring hooks, commands, or workflows** — different layers, different rules.
- **Doing the skill's domain work** — this skill designs the skill; it doesn't perform
  the task the skill is for.
```
