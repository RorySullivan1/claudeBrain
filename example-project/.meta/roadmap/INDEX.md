# Development Map — example-project

> Auto-surfaced at session start. Keep to ~one screen; detail lives in `stages/`.
> The cursor (`←`) is the next version to build. Statuses: planned · in-progress · shipped.

## Objective
Ship an Office productivity tool — a VSTO Excel add-in backed by Python tooling and docs —
that the desk can install and use under the corporate ClickOnce / no-admin constraints.

## Stages
1. **Foundation** — repo skeleton + ClickOnce build path + Python tooling base. *Milestone: the add-in builds and deploys, the tooling runs.*
2. **Analytics** — a verified quant surface the add-in can call without Office in the loop. *Milestone: pricing/risk analytics callable and validated.*
3. **Add-in UX** — ribbon + task pane wired to the analytics. *Milestone: the desk can run analytics from inside Excel.*
4. **Release & docs** — signed release + user/developer docs. *Milestone: v1.0 in the desk's hands.*

## Versions
| Version | Stage | Goal (one line)                                   | Status |
|---------|-------|---------------------------------------------------|--------|
| v0.1.0  | 01    | Project skeleton + ClickOnce build path           | shipped |
| v0.2.0  | 01    | Python tooling base (data prep + packaging)       | shipped |
| v0.3.0  | 02    | Pricing/risk analytics layer in `tools/`          | shipped |
| v0.4.0  | 03    | Ribbon UI + task pane calling the analytics       | planned ← cursor |
| v0.5.0  | 03    | User-facing error handling + diagnostics          | planned |
| v1.0.0  | 04    | Signed ClickOnce release + user & developer docs  | planned (sketch) |
