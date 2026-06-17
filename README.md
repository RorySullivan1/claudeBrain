# claudeBrain

A factory for building reusable **Claude Code tooling** — skills, commands, agents,
hooks, and context briefs — that other projects copy in and run.

## The point

Author and refine `.claude/` assets in one place, then hand them off. This repo
*designs* how Claude should work inside a project — its "mental model." It is not an
application and has no `src/`.

## Structure

- **`.claude/`** — the factory's own design environment: meta-skills for *authoring*
  assets (e.g. `agent-authoring`), the `add-*` scaffolding commands, lifecycle hooks,
  and the `session-memory` system that tracks the repo's own decisions.
- **`example-project/`** — a mock consumer showing what a finished, populated `.claude/`
  looks like in a real repo: domain skills, stack briefs, and a layout to copy from.
- **`CLAUDE.md`** — the always-loaded guide to *what each kind of asset is, where it
  lives, and how to build it.*

To reuse an asset, copy the relevant folder from `example-project/.claude/` into your
target project.
