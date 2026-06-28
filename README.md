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
  looks like in a real repo: domain skills, an objective *agent family*, stack briefs, and a
  layout to copy from (see below).
- **`CLAUDE.md`** — the always-loaded guide to *what each kind of asset is, where it
  lives, and how to build it.*

To reuse an asset, copy the relevant folder from `example-project/.claude/` into your
target project — or, from another project, **pull it** (see below).

## Pulling assets into another project

A Claude instance working in a different repo can pull a capability out of this brain — with its
dependencies and companion hooks resolved automatically — via the **`distribution/`** layer:

```
python distribution/pull.py skills/knowledge-router --dest /path/to/target/.claude
```

Browse **`LIBRARY.md`** (repo root, generated) for every pullable asset and its exact pull
command, and see `distribution/README.md` for the full procedure. The canonical, pullable files
live in `example-project/.claude/` — the repo-root `.claude/` is authoring-only and symlinked, so
never copy from it directly.

## What the example demonstrates

`example-project/` has grown into a worked example of a layered capability set:

- **An objective agent family** — `data-analyst`, `software-architect`, and
  `presentation-architect`: read-only "brains" that design the *what* and defer the
  subjective *how* to an executor.
- **A branding → presentation pipeline** of skills — `branding` (the durable identity,
  upstream of everything) → `presentation-design` (visual + copy) → format-specific
  **builders** (`deck-`, `one-pager-`, `brochure-`, `pamphlet-`, `report-builder`).
- **Operational infrastructure** — `session-memory`, `knowledge-router`, `token-optimizer`,
  and lifecycle hooks compiled from fragments by `build-hooks.py`.

## Discovering capabilities (the catalog)

Skills and agents auto-load into every session by their `description:`, so `CLAUDE.md`
stays lean and describes capabilities **by category**, not by enumerating them. The full,
always-current inventory lives in a generated **`.claude/CATALOG.md`** — every skill, agent,
command, and workflow with a one-line purpose. It's produced by `.claude/hooks/catalog.py`
(a mechanical generator like `build-hooks.py`), kept fresh automatically, and regenerated on
demand with the `/reindex` command. Read the catalog when you need the map; rely on
auto-loading to actually use an asset.
