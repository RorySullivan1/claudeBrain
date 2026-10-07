# 2026-10-07 · issue-70-xlvizer-fixes

**Goal:** Port xlVizer's fixes for #70 and close its portability gaps

## What happened
- Attached RorySullivan1/xlVizer read-only and read fix commit `551f3f7`. Our pre-fix files
  were byte-identical to its base, so the patches applied cleanly with `git apply --directory`.
- **Probes before code.** Against the old code, exactly the 5 new regression cases failed and both
  controls passed. After the port: autoclose 17/17, issue_body 47/47, lint clean.
- **Items 1–6 (bugs, `/epic`, templates)** ported. The template note was generalised: xlVizer's
  "most PRs here target vX.Y.Z" is repo-specific.
- **Item 7:** new `**Routes to:**` line on all nine `vba-*` skills, generated from the whole
  SKILL.md (description boundaries count). `asset_integrity` checks it both ways: a declared
  sibling that isn't installed (a partial pull), and a named sibling that isn't declared (drift).
  The convention is documented in `skill-authoring` and the hooks README.
- **Item 8:** every tracker reference in vendored assets is qualified `RorySullivan1/claudebrain#N`.
  Found along the way: the Outlook probe kit said "paste into #43", but #43 is closed and #52
  tracks that run. Repointed.
- **Items 9–11:** a drift fallback in the docs when no hook is installed; `github-releases` and
  `github-operator` find the version constant and bump policy first, and confirm before tagging;
  `session-memory` gets a "copy the folder whole" rule with a `--help` subcommand self-check.

## Gotchas & dead ends
- **xlVizer's drift check was vacuous here.** It looked for `.github/` beside `.claude/`, which
  in claudeBrain is `example-project/`, so it compared nothing and passed. It now also checks
  the git root. Its first run caught 3 stale ISSUE_TEMPLATE copies.
- **The concurrency rationale in #70 is right only for the default.** GitHub now documents
  `queue: max` (up to 100 pending kept). comment_once was kept anyway: it needs no global
  serialization and has no cap.
- **The routes check caught its own bug:** VSTO-* skills are upper-case, and the pattern was not.
- `vba-build-forms` looked like a dangling skill reference, but it's a CLI tool. A hand-declared
  line beats text scanning for exactly this reason.

## State at end
- All of #70's acceptance criteria are met locally. PR opened to close #70.
- The memory commit for the spend epics, stranded off-main, was carried into this branch.

## Open threads
- xlVizer can drop its local patches and re-copy once this merges (per its own memory note).
