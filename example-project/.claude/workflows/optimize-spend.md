# optimize-spend

Take the spend audit's top proposal, apply it only with approval, measure it against a
benchmark whose noise floor is known, and keep it only if the saving beats that floor and every
task's check still passes. Otherwise revert it. Either way, record the outcome in the levers
catalog. A recommended change is a hypothesis until this loop has measured it.

Run it when the user asks to "optimize spend", "prove that saving", "try the auditor's
suggestion", or "is the cheaper model good enough", and after `/spend-audit` proposes a change
the user wants tested. It is not the audit itself (`/spend-audit`) and never runs unattended:
it stops for approval before it changes anything.

**Inputs:** this project's session logs, and a machine where `claude -p` runs with tools (step 1 checks).
**Output:** the change kept or reverted, with the tree as the decision left it; one outcome line under
the lever's **Measured** field in `spend-levers.md`; one ledger row; and a report with the numbers.

Runtime state for one run lives in `.meta/optimize/<date>-<lever>-<target>/`: `audit.json`,
`plan.json`, `state.json`, `results.jsonl` and `decision.json`. That makes a run resumable, and
it is per-project state that isn't committed. Paths below are from the project root; `S` is that
directory and `T` is `.claude/skills/token-optimizer/scripts`.

## Steps

1. **Check the bench.** Unless `benchmark.py probe` has passed on this machine before, run
   `python3 T/benchmark.py probe` (four tiny runs, under $0.30). It must show `claude -p` running,
   tools running, and the budget cap stopping a run. If any fails, **stop** and say this machine
   can't run the loop: run it locally. If only `subagents_run` is false, levers that act through a
   subagent can't be measured here; say so and carry on only with a task that needs no agent.
2. **Audit.** Run **`/spend-audit`** (`../commands/spend-audit.md`, which dispatches
   `../agents/spend-auditor.md`) for the human-readable report. Then save the machine form with
   `python3 T/audit.py --json [same filter] > S/audit.json`.
3. **Plan.** `python3 T/optimize.py plan --audit S/audit.json --out S/plan.json` picks the first
   finding, in the audit's order, that carries a machine edit and has a benchmark task in
   `../skills/token-optimizer/references/benchmark-tasks.json` that exercises it. It prints what
   it skipped, and why.
4. **Gate: approval.** Show the plan: the finding and its evidence, the exact edit (file, key,
   value), the tasks, the repeat count (default 3), and the spend cap, which is at most
   tasks × repeat × 2 × each task's `run_cap`. Ask the user to approve it, using AskUserQuestion.
   Nothing has changed yet.
5. **Baseline.** Run `python3 T/benchmark.py run --label baseline --repeat 3 --task ID … --cap-usd X
   --out S/results.jsonl`, using half the approved cap. Then run `benchmark.py floor --results
   S/results.jsonl` to get each task's noise floor.
6. **Apply.** `python3 T/optimize.py apply --plan S/plan.json --state S/state.json`. The state file
   holds the original bytes.
7. **Candidate.** Run the same tasks with `--label candidate`, the same repeat, and the other half
   of the cap, into the same results file.
8. **Decide.** `python3 T/benchmark.py decide --results S/results.jsonl > S/decision.json` returns
   `keep`, `reject` or `invalid`, with the reason.
9. **Keep or revert.** On `keep`, run `optimize.py keep --state S/state.json`. On anything else,
   run `optimize.py revert --state S/state.json`, which checks that the file is byte-identical to
   before.
10. **Record.** On `keep` or `reject`, run `optimize.py record --plan S/plan.json --decision
    S/decision.json`. It writes the outcome line under the lever's Measured field, which
    `audit.py` then ranks by, and appends a `measured-outcome` row to
    `../skills/claim-grounding/reviews/ledger.jsonl`. Don't record an `invalid` run: it measured
    nothing.
11. **Report.** Give the verdict and reason, the baseline and candidate means per task, the floor,
    the measured share against the audit's estimate, what the benchmark itself spent, and the
    file's final state. If the change was kept, say that it is uncommitted and offer a commit;
    committing is the user's call.

## Control flow / STOP conditions

- **No material finding** (`plan` prints "No material finding.", exit 3) → **stop** after step 3.
  Nothing has changed, so report the audit and end.
- **No finding the loop can apply** (`plan` exit 3, "no material finding the loop can apply and
  measure") → **stop**. Relay the skipped reasons: a finding without a machine edit is applied by
  hand, and one without a task needs a task added to `benchmark-tasks.json` first. Nothing has
  changed.
- **Approval declined** at step 4 → **stop**. Nothing has changed, and nothing is recorded:
  declining isn't evidence about the lever.
- **The baseline fails its own check, or a baseline run fails** at step 5 → **stop** before
  step 6. The benchmark is broken, not the lever. Nothing was applied.
- **The cap is reached** (`run` exit 4) → if it happens after step 6, run
  `optimize.py revert`. Report the partial spend, and record nothing.
- **Saving within the noise floor** (`decide`: reject, "saving within the noise floor") → revert,
  record it as rejected, report.
- **The quality guard fails** (`decide`: reject, "quality guard failed on …") → revert, record it as
  rejected, report. Cheaper and worse is not a saving.
- **The candidate costs more** → revert, record it as rejected, report.
- **Any error after step 6** → run `optimize.py revert` first, then report. If revert refuses
  because the file changed after apply, **stop** and say so: never overwrite someone else's edit.
- **Keep** (saving above the floor, every check held) → `optimize.py keep`, record it as kept, report.
- **Gate:** step 6 never runs without the step 4 approval, and the loop never commits.

## Invokes

- Commands: `../commands/spend-audit.md`.
- Agents: `../agents/spend-auditor.md`; the agent under test, for example `../agents/python-developer.md`.
- Scripts: `../skills/token-optimizer/scripts/audit.py`, `benchmark.py`, `optimize.py` (same folder).
- References: `../skills/token-optimizer/references/spend-levers.md`, `benchmark-tasks.json`.
- Ledger: `../skills/claim-grounding/reviews/ledger.jsonl`.
- Probes: `../skills/token-optimizer/probes/probe_optimize.py` (the loop's guards), `probe_audit.py`.
- Tools: AskUserQuestion (the step 4 gate).
