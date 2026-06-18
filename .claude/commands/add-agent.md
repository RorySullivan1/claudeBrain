---
description: Scaffold a new subagent (.claude/agents/<name>.md) following the agent-authoring conventions.
argument-hint: <agent-name> [target .claude/ dir] [— one-line purpose]
---

You are scaffolding a new **subagent** named `$1`.

## 1. Load the authoring expertise

Invoke the **agent-authoring** skill — it owns the rules for the triggering
`description`, the least-privilege `tools` allowlist, `permissionMode`, `model`, and
the system-prompt mandate. If `$1` is a specialized flavor, also use the matching
meta-skill:

- a language/stack code-writing agent → **developer-agent-authoring**
- a project-scope / system-design assessor → **product-manager-agent-authoring**
- a knowledge-base curator / retriever → **knowledge-agent-authoring**

The meta-skill (plus any built agent as a model) is the format spec — do **not**
spawn Explore/research agents to re-derive conventions or re-read example bundles.
For a request that needs several assets, follow the `author-asset` workflow and
batch them.

## 2. Confirm placement

Determine the target `.claude/agents/` directory from `$ARGUMENTS`. If it isn't given,
ask: a **factory** meta-asset (`./.claude/agents/`) or a **product** for a consumer
(`example-project/.claude/agents/` or another project path)? Default to the factory layer.

## 3. Decide before writing

Settle the six questions from agent-authoring — mandate, trigger, tools, permissions,
model, return value. Ask the user only for what you can't infer from `$ARGUMENTS`.

## 4. Scaffold

Create `<target>/.claude/agents/$1.md` with:

- **frontmatter** — `name: $1`, a triggering `description`, a least-privilege `tools`
  allowlist, the weakest workable `permissionMode`, and a fitting `model`.
- **body** — the agent's complete system prompt: a role line, a numbered workflow, and
  an explicit *concise-summary* output format (the agent starts fresh, so restate any
  constraint it must know).

## 5. Verify

Run the agent-authoring checklist. Report the path created and how to invoke it
(`@agent-$1`).
