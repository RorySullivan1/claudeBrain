---
description: Scaffold a new multi-step workflow (.claude/workflows/<name>.md).
argument-hint: <workflow-name> [target .claude/ dir] [— what it orchestrates]
---

You are scaffolding a new **workflow** named `$1`.

## 1. Conventions

Follow `.claude/workflows/README.md`: one markdown file per workflow; the body lays out
the ordered steps, the agents/commands each step invokes, the inputs and outputs, and
the success/stop conditions. Reference `../agents/` and `../commands/` rather than
re-describing them.

## 2. Confirm placement

Determine the target `.claude/workflows/` directory from `$ARGUMENTS`. If it isn't
given, ask: a **factory** authoring pipeline (`./.claude/workflows/`) or a **product**
workflow for a consumer (`example-project/.claude/workflows/` or another project path)?
Default to the factory layer.

## 3. Scaffold

Create `<target>/.claude/workflows/$1.md` describing:

- **purpose and inputs** — what it produces and what it needs to start.
- **ordered steps** — each naming the agent or command it invokes and the output it
  passes on.
- **control flow** — any branch/loop logic, and explicit **stop / success conditions**.

## 4. Verify

Confirm every referenced agent and command exists (or is flagged as still to be
created). Report the path created.
