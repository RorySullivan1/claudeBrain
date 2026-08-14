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
- `verify-claims` — the **truth gate**: extract an asset's factual claims, tier each by what
  would settle it, ground them against docs or a probe, and label what stayed unverified.
  Run before shipping anything that asserts facts about an external system. Independent of
  `skill-creator`'s eval loop, which is the *performance* gate.
