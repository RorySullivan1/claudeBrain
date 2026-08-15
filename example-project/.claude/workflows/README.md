# workflows/

**Multi-step autonomous orchestration.** Claude executes a scripted sequence that
can loop, branch, and spawn agents — designed to run largely unattended. Where a
command is one shot, a workflow is a whole pipeline.

## Format

- One markdown file per workflow: `<name>.md`.
- The body lays out the ordered steps, the agents/commands each step invokes, the
  inputs and outputs, and the success/stop conditions.
- Reference `../agents/` and `../commands/` rather than re-describing them.

## Typical uses

- A scheduled report: gather data → score/analyze → draft → deliver.
- A triage pipeline: read items → prioritize → assign → post a digest.
- A refresh job: fetch source data → recompute → write outputs → flag anomalies.

## Defined here

- `advance-roadmap-step` — graduate the roadmap's cursor card into `.meta/version`, then
  drive implement → review → reiterate → assess, stop for approval, and ship.
- `ship-version` — label a unit of work with its goals in `.meta/version`, then name and
  ship the PR from those goals (`/version-set` + `/version-ship`).
- `verify-claims` — the **truth gate** for assets that assert facts about an external
  system (engine: the `claim-grounding` skill; independent of `skill-creator`'s
  performance evals).
- `change-end-to-end` — one canvas-app change from intent to landed-in-Studio across the
  clipboard air gap: ground → author → audit → human paste gate → record.
- `screen-build` — build one canvas screen end to end: ground data + controls, plan
  layout, author, geometry-check, validate, audit, hand off, record.
- `control-grounding` — ground an unknown control/property/enum token before it is
  authored, then propagate the grounding to every catalogue surface.

To add one, create a `<name>.md` describing the sequence (see Format above); the
auto-generated `../CATALOG.md` is the always-current inventory.
