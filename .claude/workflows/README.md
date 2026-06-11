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

## Status

**Empty scaffold.** No workflows defined yet. Add a `<name>.md` describing the
sequence to create one.
