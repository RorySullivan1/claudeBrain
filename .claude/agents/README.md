# agents/ — authoring subagents (factory scope)

The **factory** `agents/` layer. Not domain agents — these are isolated subagents
for **authoring jobs**: focused workers that help build assets and return only a
summary, keeping the main authoring session clean.

## What goes here

- A `draft-skill` agent — takes a task description, returns a first-pass `SKILL.md`.
- An `asset-auditor` agent — reads a skill/hook/workflow and reports convention
  violations without bleeding the whole file into context.

## Format

One markdown file per agent: `<name>.md`. Frontmatter (`name`, `description`, and
optionally `tools`, `model`); the body is the agent's mandate.

## Operational agents (exceptions)

Not authoring agents — general workers the factory *dogfoods* during any session. Like the
operational skills, their canonical copy lives in `example-project/.claude/agents/` and this
layer holds a **symlink**; edit them in `example-project/`, never replace the symlink with a copy.

- `token-manager` — a context-economy worker: does verbose/high-volume work (test runs, log
  processing, large-file analysis, fetches) in its own isolated context and returns only a
  capped summary. The delegation target of the `token-optimizer` skill.

## Status

**No authoring agents defined yet** (the `draft-skill` / `asset-auditor` ideas above are still
stubs). One operational agent is wired: `token-manager` (symlinked from example-project).
