# The verification surface — who can confirm this worked

The project's answer, per surface, to one question: **can the agent confirm this itself, or
must a human — and why?** Every workflow that ends in "done" reads this file instead of
re-deriving what it can check, and every human gate in this repo traces back to a row here.

Produced and refreshed by the **`establish-verification`** workflow. This file is a *project*
record: the table below describes **example-project**, and a project adopting the factory
replaces the rows with its own. The model above the table travels unchanged.

## Why this file exists

This repo's recurring defect is **verification steps that cannot verify** — an audit that runs
in plan mode and can't run the check, a probe bound early so it fails to compile on the version
it was meant to test, an advisory wrapper that crashes instead of advising. Each one *looked*
like verification from the outside. The fix is not more checks; it is a written, per-surface
answer that cannot be satisfied by a check that doesn't run.

The `claim-grounding` skill answers this for an **asset's factual claims**. This file answers it
for the **project's own work** — the C# that has to build, the HTML that has to render, the
formula that has to paste.

## The three tiers

| Tier | Means | Requires |
|---|---|---|
| `agent-runnable` | A command the agent can execute here, whose result is the verdict | The exact command, and evidence it has been seen to **fail** |
| `human-gated` | Confirmation needs something the agent cannot reach | The blocker, and what the human is asked to report back |
| `unverified` | Nobody has a check yet | An owner and a next action — this tier is a debt marker, not a resting state |

### Rules that make the tiers mean something

- **Name the command, not the capability.** "The tooling is tested" is not a check; `pytest -q
  tools/` is. If the *check* column holds nothing you could paste into a shell, the row is
  `unverified` wearing a disguise.
- **A check that cannot fail is not a check.** Before a row may be marked `agent-runnable`, the
  command must have been observed to fail on deliberately broken input at least once — the same
  controls discipline `claim-grounding` requires of a probe. Record that in *last-run*.
- **`human-gated` is a real answer, not a failure.** It is what lets a workflow place an
  honest gate instead of reporting success it cannot see. What makes the row useful is the
  **reason** (so nobody re-litigates it) and the **report contract** (what the human returns —
  often just a binary "worked / didn't", which is all an air gap can carry).
- **Split a surface rather than calling it "mixed".** If part of a surface is machine-checkable
  and part isn't, that is two rows. "Mixed" hides which half is actually covered.
- **A stale `agent-runnable` row is a claim about the past.** *last-run* is what distinguishes a
  check that works from one that used to.
- **Say whether the check gates or only reports.** Several of this repo's checks are advisory by
  contract — `asset_integrity.py` never vetoes a commit, and `contrast.py` exits 0 on a failing
  pair and puts the verdict in its output. A caller that reads exit status alone will record a
  pass that never happened. Where the two differ, the *check* column says which to read.
- **Never promote a tier to close a gap.** Downgrading is free; upgrading needs a command and a
  failure. Reporting `unverified` is always cheaper than a wrong "verified".

## The surface table — example-project

| Surface | Check | Tier | Reason | Last run |
|---|---|---|---|---|
| Python tooling (`tools/`) | `pytest -q tools/` | `agent-runnable` | Process-isolated from Office; no Excel in the loop (`notes/addin-tooling-data-flow.md`) | — |
| Python style | the project's configured formatter/linter (CLAUDE.md § Conventions) | `agent-runnable` | Pure source analysis | — |
| VSTO add-in build (`src/AddIn/`) | `msbuild` on the add-in project | `human-gated` | Needs Windows, a licensed Office install and the VSTO runtime | — |
| VSTO add-in behaviour in Excel | manual load + exercise the Ribbon | `human-gated` | Needs a running Excel host; human reports which commands loaded and what failed | — |
| ClickOnce deployment | install from the staged payload on a target machine | `human-gated` | Needs a signed manifest and a managed end-user machine | — |
| VBA against the Excel object model | `skills/vba-excel-object-model/probes/probe_claims.bas` (controls-gated) | `human-gated` | Needs a real Excel host; authored here, **run** by a human who returns the log | 2026-09-02 — controls PASSed; one claim REFUTED |
| Canvas app source (`src/authored/`) | none — one-way clipboard to Studio | `human-gated` | The air gap (`air-gap.md`); only inbound signal is a binary "worked / didn't" | per `paste-log.md` |
| Canvas paste readiness | spawn `../agents/pre-paste-review.md` → PASTE / DO-NOT-PASTE | `agent-runnable` | Consistency against the repo's own records needs no return channel | — |
| Outlook HTML — structure | parse-validate the file (`../agents/outlook-html-designer.md` step 11) + balance `<!--[if` / `<![endif]-->` | `agent-runnable` | Parsing is local; malformed markup fails here | 2026-09-10 — probe kit A+B clean, conditionals balanced; control (one deleted `</td>`) caught |
| Outlook HTML — contrast | `skills/branding/references/contrast.py "#FG on #BG"` — **read the verdict line; it exits 0 either way** | `agent-runnable` | WCAG AA is computable from the colour values | 2026-09-10 — self-test PASS (incl. #767676/#777777 boundary); discriminates 4.54 vs 4.48 |
| Outlook HTML — rendering | open in the Word-engine client and look | `human-gated` | No Outlook renderer is reachable from a session (five claims unprobed, #52) | — |
| Asset shape (`.claude/`) | `asset_integrity.py` fed a git-commit hook payload — **advisory: reports, never vetoes** | `agent-runnable` | Pure file-shape analysis | 2026-09-10 — silent on the real tree; caught a deliberate `name:`/folder mismatch |
| Parallel-state model (`.meta/`, `memory/`) | `python3 .claude/hooks/probes/probe_parallel_state.py` | `agent-runnable` | Reproduces the two-worktree collision locally with git; four controls gate the run | 2026-09-10 — controls PASSed; 2 of 3 claims REFUTED |
| Docs (`docs/`) | none | `unverified` | No link-check or build step exists. Owner: docs maintainer; next: add a link checker | — |

**Reading `—` in *last-run*.** It means the tier is **claimed, not proved** — nobody has yet
watched that command fail on broken input. Treat such a row as `unverified` until a run stamps
it. Most rows above carry `—` on purpose: `example-project` is a showcase whose `tools/`,
`src/AddIn/` and `docs/` trees are illustrative, so their checks have never been run. The two
dated `agent-runnable` rows are the ones backed by real controls (ledger:
`skills/claim-grounding/reviews/ledger.jsonl`) and are what a fully-worked row looks like.

## How the rest of the repo uses this

- **Workflows** consult it instead of restating what they can check: `establish-verification`
  writes it; `advance-roadmap-step` reads it to know which of a version's surfaces its review
  loop can actually close; `change-end-to-end` and `screen-build` place their human gates from it.
- **Agents** name their row rather than re-deriving their reach — `../agents/pre-paste-review.md`,
  `../agents/outlook-html-designer.md`.
- **`air-gap.md`** is the canvas *instance* of the `human-gated` tier, in depth: what a one-way
  channel implies for how work is done. This file records *that* the gate exists; that brief
  records what living behind it costs. Neither restates the other.

## See also

- **`establish-verification`** workflow — how the rows get produced and refreshed.
- **`air-gap.md`** — the canvas one-way transfer model.
- **`claim-grounding`** skill — the same question asked of an asset's *claims* rather than the
  project's *work*.
