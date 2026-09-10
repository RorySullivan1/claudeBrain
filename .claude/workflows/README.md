# workflows/ — authoring pipelines (factory scope)

The **factory** `workflows/` layer. Multi-step orchestrations for **producing
assets** end to end — where a command is one shot, a workflow runs the whole build.

Most workflows here are factory **authoring** pipelines (real files). The exception is
`ship-version`, an **operational** workflow the factory dogfoods and consumers lift, so it
is a **symlink** to the canonical copy in `example-project/.claude/workflows/` — edit it
there, never replace the symlink. (Mirrors how `skills/` mixes real meta-skills with
symlinked operational ones.)

## What goes here

- `author-asset` — **(built)** the default build path for any "make me a skill /
  agent / set of assets" request: scope → load conventions once (no re-exploration)
  → scaffold via the `add-*` commands → batch the wiring → verify structurally.
- `ship-version` — **(built, operational/symlinked)** label a unit of work as a semver
  version with its goals in `.meta/version`, then name and ship the PR from those goals
  (via `/version-set` + `/version-ship`).
- `init-project` — **(built)** the adoption path: brief → objective, build `.claude/` by
  selection from the portable core, choose skill families from `CATALOG.md` (recording the
  exclusions), run `establish-verification`, seed `.meta/roadmap/` and one `.meta/version`
  cursor, then green the tree.
- `establish-verification` — **(built, operational/symlinked)** answer per surface whether the
  agent can confirm it or a human must, prove each candidate check can fail, and write
  `context/verification-surface.md`.
- `verify-claims` — **(built, operational/symlinked)** the truth gate for an asset that
  asserts facts about an external system: extract the claims, tier each by what would
  settle it, ground them against docs or a local probe, and label what stayed unverified.
  Engine: the `claim-grounding` skill, which owns the shape/performance/truth split.
- `author-skill` — scaffold → draft `SKILL.md` → audit against conventions → place
  the finished bundle into `example-project/.claude/skills/` (or a downstream repo).
- `harvest-context` — turn a stack brief into a context doc, validate, file it.

## Format

One markdown file per workflow: `<name>.md` — ordered steps, the agents/commands
each step invokes (reference `../agents/` and `../commands/`), inputs/outputs, and
stop conditions.

## Status

**`author-asset`, `init-project`, `ship-version`, `verify-claims` and `establish-verification`
built** (the last three are operational, symlinked from example-project). `author-skill` and
`harvest-context` remain planned.
