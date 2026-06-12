---
name: agent-authoring
description: >
  Expert guidance for authoring Claude Code subagents — the agent definitions that
  live in a project's .claude/agents/<name>.md. Use this skill whenever the user
  wants to design, write, scaffold, review, or fix a Claude Code agent / subagent:
  choosing whether a task even warrants an agent, writing a description that
  triggers reliable delegation, scoping the tools allowlist, setting its default
  permissions, picking a model, and writing the agent's system-prompt mandate.
  Trigger on phrases like "write an agent", "create a subagent", "draft a
  .claude/agents file", "agent frontmatter", "what tools/permissions/model should
  this agent have", "why isn't my agent being used", or "should this be an agent or
  a skill". This teaches how to author agents; it is not for authoring skills (that
  is skill-authoring) and not for doing the agent's own domain task.
---

# Agent Authoring

How to design and write a good Claude Code **subagent** — the agent definitions
that live in `.claude/agents/<name>.md`. Use this when building a new agent,
reviewing an existing one, or diagnosing why an agent never gets used.

## Core principles

- **An agent exists to isolate context.** Its real value is a *separate context
  window*: it does noisy, verbose, or error-prone work (searches, log-reading,
  multi-file analysis) and returns only a **summary**, so the main session stays
  clean. If a task won't flood context, it probably shouldn't be an agent.
- **The `description` is the trigger.** Claude decides whether to delegate by
  reading the `description`. A vague description means the agent is never invoked.
  This field earns the most care.
- **Least privilege, by default.** Give the agent only the tools it needs and the
  weakest permission posture that still lets it finish. Breadth is a liability.
- **One focused mandate.** An agent that "helps with the codebase" does nothing
  well. Scope it to a single, nameable job.
- **Agents start fresh.** A subagent does **not** inherit the conversation, and you
  should not assume it absorbs every CLAUDE.md rule. Anything it must know goes in
  its system-prompt body or its task input.

## Is an agent even the right tool?

Confirm the layer before writing anything. Pick the lightest thing that works.

| Layer | Use when | Context | Invocation |
|---|---|---|---|
| **Agent** | A self-contained side task produces output you won't reread; you want a summary back | Fresh, isolated | Auto (via `description`) or `@agent-<name>` |
| **Skill** | Reusable expertise/procedure that should run *in* the main conversation | Inline | Auto (via `description`) or `/<name>` |
| **Command** | A quick, one-shot prompt you'd otherwise retype | Inline | `/<name>` |
| **Hook** | Something that must *always* run on an event (format, guard, validate) | Inline | Automatic, event-triggered |

Quick test: *Does the task dump a lot of output I won't reference again, and can it
hand back a tidy summary?* → agent. *Is it knowledge or a procedure I want applied
in this conversation?* → skill. *Must it fire deterministically on an event?* →
hook.

## Decide before you write

Answer these first; they map directly onto the file:

1. **Mandate** — one sentence: what is this agent's job?
2. **Trigger** — what request/context should cause delegation? (→ `description`)
3. **Tools** — the minimum set it genuinely needs. (→ `tools`)
4. **Permissions** — can it act unattended, or must it stop and ask? (→ permissions)
5. **Model** — how much reasoning does the job warrant? (→ `model`)
6. **Return value** — what summary should it hand back? (→ body)

## Anatomy of an agent file

A subagent is a single markdown file with YAML frontmatter and a body:

- **Location.** `.claude/agents/<name>.md` for a project (checked in, shared with
  the team) or `~/.claude/agents/<name>.md` for personal, cross-project agents.
- **The body is the agent's *complete* system prompt** — not an addition to a
  default prompt. Write it as the agent's whole brief.

Document and reason about these **core, durable frontmatter fields** — the agent's
identity and trigger, plus the three operational levers (tools, permissions,
model):

| Field | Required | What it does |
|---|---|---|
| `name` | yes | Unique identifier; **must match the use intent and be unique**. |
| `description` | yes | Drives delegation — when Claude should hand the task off. |
| `tools` | no | Allowlist of tools the agent may use. Omit = inherit all. |
| `permissionMode` | no | The agent's default permission posture (see below). |
| `model` | no | Which model runs the agent (alias, full ID, or `inherit`). |

Other optional fields exist (e.g. `disallowedTools`, `color`). Don't memorize the
long tail — it shifts between versions. Browse and edit agents with the **`/agents`**
command, and confirm field names/values against the current **sub-agents docs**.

## Writing the `description` (the part that matters most)

This single field decides whether the agent is ever used. Write it for *delegation*,
not for documentation.

- **Lead with the use case, not the mechanism.** Not "a subagent for reviews" →
  "Expert code-review specialist. Use proactively right after code is written or
  changed."
- **Name concrete triggers.** List the phrases/situations that should invoke it,
  the way the skills in this repo do.
- **Use the "proactively" convention** when you want Claude to reach for it without
  being asked.
- **If it never triggers, the description is too generic** — make the use case
  sharper and more specific before touching anything else.

## Tools the agent can use (least privilege)

- **Omit `tools`** and the agent inherits every tool the parent has — convenient,
  but rarely what you want.
- **Specify `tools`** as an *allowlist*: only those tools are available. Start
  minimal and add what the mandate demands.
  - Read-only analyzer: `Read, Grep, Glob` (add `Bash` only if it must run things).
  - Agent that edits: add `Edit`/`Write` deliberately.
- **`disallowedTools`** is the denylist counterpart — handy to subtract a few tools
  from an otherwise-inherited set.
- **MCP servers are configured separately**, not through `tools`. Don't list MCP
  tool names in `tools`.

Prefer an allowlist over a denylist: it fails safe as new tools appear.

## Default permissions the agent runs with

Tools control *what* is available; the **permission posture** controls *whether the
agent acts without stopping to ask*. Set it deliberately via `permissionMode`. The
common stances:

- **`default`** — prompts for permission as normal. Safe baseline.
- **`plan`** — read-only; the agent investigates and proposes but makes no
  mutations. Ideal for analysis/research agents.
- **`acceptEdits`** — auto-accepts file edits so the agent can work through changes
  unattended. Use only when edits are the whole point and the `tools`/scope are
  tight.
- **`bypassPermissions`** — runs without prompting at all. **High blast radius** —
  reserve it for trusted, narrowly-scoped automation, never as a convenience. When
  in doubt, don't.

Safe default: pair a **least-privilege `tools` allowlist** with the
**least-powerful `permissionMode`** the agent actually needs. Note that a stricter
*parent* posture wins — an agent can't grant itself more freedom than the session
allows. The exact, version-current list of modes lives in `/agents` and the
sub-agents docs; verify there rather than assuming.

## Which Anthropic model it uses

Set `model` to match the job's reasoning load:

- **`haiku`** — fast and cheap; great for read-only, mechanical, or high-volume work.
- **`sonnet`** — solid default for most agents.
- **`opus`** — complex reasoning, architecture, multi-step judgment.
- **`inherit`** — run on the parent session's model for consistency.

The field accepts a short alias or a full model ID. Lean cheaper for frequent,
shallow agents; reserve the heavier models for genuinely hard reasoning.

## Writing the mandate (the body)

The body is the agent's entire system prompt. Make it focused and self-contained:

1. **Open with the role.** "You are a senior code reviewer…" sets identity in one
   line.
2. **Give a workflow.** Numbered steps for how to approach the task end to end.
3. **Specify the output format.** State exactly what to return — and that it should
   be a **concise summary**, not a raw dump, since the point is to protect the main
   context.
4. **Restate what it needs.** The agent won't see the conversation and may not
   absorb every CLAUDE.md rule — repeat the few constraints that matter.
5. **Keep it tight.** Every line costs tokens; state what to do, skip the narration.

## Authoring checklist

- [ ] `name` is unique, kebab-case, and matches the agent's actual job.
- [ ] `description` leads with the use case and names concrete triggers.
- [ ] `tools` is a reviewed least-privilege allowlist (or a justified inherit).
- [ ] `permissionMode` is the least powerful posture that still completes the job.
- [ ] `model` fits the reasoning load.
- [ ] Body has a role line, a workflow, and an explicit summary output format.
- [ ] Tested: invoked via `@agent-<name>`, or inspected/edited through `/agents`.

## Anti-patterns

- **Generic description** ("a helpful agent") → never delegated.
- **No tool allowlist** → over-broad reach the mandate doesn't need.
- **`bypassPermissions` for convenience** → use the weakest mode that works instead.
- **Body assumes conversation/CLAUDE.md context** → the agent starts fresh; restate it.
- **Open-ended mandate with no exit criteria** → the agent wanders and never returns.
- **Duplicate `name`** → collisions are resolved unpredictably; keep names unique.

## Template

```markdown
---
name: <kebab-case-name>            # unique; matches the job
description: >
  <Use case first, then concrete triggers.> Use proactively when <situation>.
tools: Read, Grep, Glob            # least-privilege allowlist
permissionMode: plan               # weakest posture that still works
model: sonnet                      # alias, full ID, or inherit
---

You are a <role> focused on <single job>.

## When invoked
1. <first step>
2. <second step>
3. <verify / wrap up>

## Output
Return a concise summary: <exactly what the caller needs back>.
```

### Worked example — a read-only reviewer

```markdown
---
name: diff-reviewer
description: >
  Reviews the current diff for correctness and risk. Use proactively right after
  code is written or changed, or when the user asks "review this" / "any issues?".
tools: Read, Grep, Glob, Bash
permissionMode: plan
model: inherit
---

You are a senior reviewer. You do not modify code — you report.

## When invoked
1. Run `git diff` to see what changed.
2. Read the changed files and enough surrounding code to judge impact.
3. Check correctness, error handling, security, and obvious regressions.

## Output
Return findings grouped by severity — Critical / Warning / Suggestion — each with
file:line and a one-line fix. Keep it to the issues that matter; no narration.
```

## Out of scope

- **Authoring *skills*** — that's a separate concern (a future `skill-authoring`
  meta-skill); this skill is only about agent definitions.
- **Authoring hooks, commands, or workflows** — different layers, different rules.
- **Doing the agent's domain work** — this skill designs the agent; it doesn't
  perform the task the agent is for.
