# 2026-09-22 18:50 · epic-issue-commands

**Goal:** Build /epic and /issue: no-code planning filed on the remote as templated epics/sub-issues with auto-close

## What happened
- The user asked whether commands existed for filing epics and issues on the remote. None did.
  The know-how existed (the `github-issues` skill and the `github-operator` agent) but
  nothing could be invoked directly. **Decision (user): keep epics SEPARATE from
  `.meta/roadmap/`.** GitHub is not a mirror of the roadmap. A one-way link can be added
  later if doing it by hand becomes a chore.
- Built in `example-project/.claude/` as the canonical copy, with factory symlinks:
  - `commands/epic.md` and `commands/issue.md`. These are procedure only. The standard
    comes from the skill.
  - `skills/github-issues/`, which gained:
    - `references/templates/{epic,task,bug,feature}.md`. The epic template follows Epic #48's
      house shape: Problem, Outcome, ordered Sub-issues, Acceptance, Non-goals, Closing.
    - `scripts/issue_body.py`, which runs render, `check --allow-self`, `fill-self`, then
      `check`.
    - `references/mechanics.md`: the call order, the `gh` fallback, and the traps.
    - `assets/epic-autoclose.yml`, plus a probe for it.
  - The SKILL.md's inline bug template moved out to `bug.md`.
- Ledger went from 96 to 100 rows: closing keywords, sub-issue limits and id-vs-number, the
  GITHUB_TOKEN no-recursion rule, and the auto-close probe.

## Gotchas & dead ends
- **`sub_issue_id` is the issue's database id, not its #number.** Both the REST docs and the
  MCP schema say so. The fix is to avoid the call entirely: `issue_write` create accepts
  `parent_issue_number` and links in the same call.
- **GitHub's docs don't say that a parent closes when its sub-issues do.** So we ship a
  workflow rather than a claim.
- **Events caused by GITHUB_TOKEN start no new runs**, so the parent → grandparent cascade has
  to happen inside one run. A re-trigger design would stop silently one level up.
- **Check-the-check caught a vacuous gate.** The first `issue_body.py check` searched the
  whole body for a closing keyword, and the template's own footnote example
  (`Closes #1, closes #2`) satisfied it. It now reads only the fenced line under Done when.
- The auto-close script uses curl against `github.api_url`, not `gh api`, so the probe can
  point it at a local fake and treat 404 ("no parent") as distinct from other errors,
  which fail loudly. Five deliberate breaks were each caught by the probe.
- Issue types: `/orgs/{org}/issue-types` is organization-scoped, and the docs don't say
  personal repos lack types. The commands call `list_issue_types` and fall back to an
  `epic` label.

## State at end
- Built, structurally checked (asset_integrity clean, and it reported a missing reference when
  one was injected), probe 14/14, catalogs regenerated in both trees. Nothing filed on the
  remote. The commands have never been run end to end against GitHub.

## Open threads
- First real `/epic` run is the live test: body pipeline + parented creates + read-back.
- `epic-autoclose.yml` is NOT installed in this repo's `.github/workflows/`. Offered, not done.
  Its first live close is the confirming event (check the Actions log).
