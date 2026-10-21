# Probes — token-optimizer

## `probe_usage_sources.py`: what each usage source counts (RorySullivan1/claudebrain#58)

```
python3 probe_usage_sources.py --selftest   # 8 cases on planted logs, including 2 controls
python3 probe_usage_sources.py [LOGS_DIR]    # this project's ~/.claude/projects/<slug> by default
```

It reads only. The findings live in `../references/usage-sources.md`, which is the table `usage.py` must follow.

**Self-test, 8/8.** It plants every shape the probe claims to detect: duplicate lines, history
copied under another `sessionId`, a hidden call in a harness window, a carry across a resume, a
fresh `startTime`, and a subagent placeholder. It also plants two controls that must not be
flagged (an exact-match window, and a session with no subagents). **Three deliberate breaks**
(no dedupe, blindness to a fresh start, a window that double-counts) each turned one case red.

**First real run, 2026-10-07**, on this repo's cloud-session logs (2 files, 1,446 usage lines,
676 calls). It reproduced the hand analysis exactly:
- every duplicate carries identical usage;
- 51 calls sit in both files under the earlier session's id;
- the six Opus windows show a harness-minus-log gap of 506 input, 6–19 output, and a cache read
  the size of the context per hidden call (one window exact);
- every Haiku token is harness-only;
- 4 records carried totals across a resume, and 1 began from zero;
- the subagent logged output 2 for a call the parent records as 142.

**Not covered:**
- Whether `cost-state` includes subagent spend: the docs say yes, and it's pending the next
  record (see `usage-sources.md`).
- A Haiku-as-main-model session.
- Local (non-cloud) installs, where the log location or the exit behaviour may differ. Re-run
  the probe there before trusting the table.

## `probe_usage.py`: the parser and its prices (RorySullivan1/claudebrain#59, #60)

```
python3 probe_usage.py --selftest   # 26 checks on planted fixture logs
python3 probe_usage.py --real       # reconcile this project's own logs
```

**Self-test, 26/26.** The fixtures plant:
- one call split over three lines, and the same call copied into a later session's file;
- meta, tool-result, compact-summary and local-command lines;
- a `/cmd` prompt followed by a plain prompt that spawns a subagent;
- placeholder subagent output;
- a hidden background call inside a harness window, and a new process (new `startTime`).

The odd-shape fixture adds an unknown record type, an unknown usage key, and an unknown model.

The controls must stay quiet:
- a naive line sum must *disagree* with the parser;
- a clean log reports no unknown shapes;
- a window holding the subagent's calls shows no false background;
- a new `startTime` opens no window.

The #60 cases are:
- hand-computed prices for 5m/1h writes, the Opus 5.5 cache-read rate, fast mode, US-only
  inference, web search, and the Haiku 5.5 over-100K tier;
- the table matching the fixture harness;
- the "estimate (API list price)" label, with tokens leading;
- an unknown model showing as UNPRICED, never $0.

**Breaks, each caught (2026-10-07):** no dedupe, meta lines opening a segment, a command segment
that never ends, unknown types skipped silently, subagent placeholders summed, an unpriced model
as $0, windows spanning two processes, a wrong price row, and a log that exceeds the harness. Two
of these first came back green: the placeholder sum (the by-model row overwrote it) and the
cross-process window (no fixture had a second process). The checks were tightened until both went red.

**Real run, 2026-10-07:** 12 window/model rows, 0 failures. The table equals the harness
`costUSD` in every row (max difference 3e-14). The log never exceeds the harness. Each gap is
named: background, plus subagent output in the one window that ran a subagent.

## `probe_audit.py`: the spend audit and its catalog (RorySullivan1/claudebrain#63, #64)

```
python3 probe_audit.py --selftest              # 39 checks on planted profiles
python3 probe_audit.py --real [--logs DIR]     # audit this project's own logs
```

**Self-test, 39/39.** The fixtures plant each signal a rule claims to see:
- three rebuilds after two-hour gaps on a 1-hour TTL;
- a rebuild after a Sonnet-to-Opus switch;
- an Edit to `CLAUDE.md` with no rebuild after it;
- a 40,000-character Bash result in the main context;
- report-level profiles for the TTL, model, effort and fan-out rules.

The **control** is a clean session that must report "No material finding." The cap holds at
40 lines and 5 findings even with eight material findings. The catalog's lever ids must equal
`audit.py`'s rules, in order, and every lever must carry all seven fields with a source,
Measured included. A planted Measured line re-prices a finding at the measured cut when the
outcome was kept, and drops it to a check when it was rejected (#69). Six **breaks** each turned
a check red:
- blind rebuild detection;
- a TTL that never expires;
- no materiality floor, which makes the control report findings;
- a rule removed from `audit.py`;
- an always-loaded list that misses `CLAUDE.md`;
- an outcome parser that matches nothing, which brings a rejected finding back.

**First real run, 2026-10-21**, on the cloud-session logs (24 sessions, 5,499 calls). It found:
- 50 rebuilds: 45 after an idle gap past the 1-hour TTL, 0 after a model switch, 5 other;
- 0 mid-session edits to `CLAUDE.md` or memory;
- two material findings, long context and idle rebuilds, which overlap;
- that the 1-hour TTL earns its premium.

**Not covered:**
- Whether a 20,000-token compaction summary is typical. It's the stated assumption behind the
  `idle-rebuild` estimate.
- Any saving measured after a change. `probe_optimize.py` below covers that loop.

## `probe_optimize.py`: the optimize-spend loop (RorySullivan1/claudebrain#67, #68, #69)

```
python3 probe_optimize.py --selftest             # 45 checks; a stub stands in for claude -p
python3 ../scripts/benchmark.py selfcheck        # 13 checks: each task's guard can fail
python3 ../scripts/benchmark.py probe            # 4 real runs, about $0.01: text, tools, cap, subagent
```

**Self-test, 45/45.** A stub `claude` answers each call from a script and logs the argv, cwd
and environment it saw. That lets the probe check what the runner really passes:
- `--max-budget-usd`, `--no-session-persistence`, a streamed format and never `--bare`;
- Edit and Write denied;
- a throwaway copy as the working directory;
- no `CLAUDE_CODE_SESSION_ID`.

The rest of the checks:
- **The cap:** five runs at $0.10 against a $0.25 cap stop after three. The last budget is what
  was left, and a run the CLI stops on its budget fails its check.
- **The guard:** these fail their checks: a wrong answer, the right answer without the named
  agent, a run that edits a file, and an answer that only the subagent gave. An answer given
  before a Stop hook's extra turn still passes.
- **Decisions on planted results:** keep, noise, worse, dearer, a broken baseline, and a
  one-run baseline.
- **`optimize.py`:**
  - `plan` stops on no finding and on no machine edit;
  - apply then revert is byte-identical for LF, CRLF and a missing key;
  - a second apply is refused;
  - revert refuses a file someone changed after apply;
  - `record` writes Measured lines and ledger rows that `audit.py` reads back.

Four **breaks** each turned a check red:
- no noise floor, so noise is kept as a saving;
- no quality guard, so a wrong answer passes;
- no environment scrub, so the child sees this session's id;
- a hash that can't tell bytes apart, so revert claims success on a clobbered file.

**Real runs, 2026-10-21, in a cloud session.**

- **`probe`:** `claude -p` runs, tools run, and a subagent runs from the child. A $0.0001 budget
  stops a run with `error_max_budget_usd`, $0.000029 over. Every cost reconciles with
  `pricing.json`. It found one defect, fixed: `modelUsage` sums a whole run, so pricing it as one
  request wrongly applied the over-100K rate.
- **The end-to-end run,** with the user's approval: model-per-agent on `python-developer`,
  Sonnet to Haiku, task `agent-python-developer`, 3 runs before and 3 after.
  - Baseline $0.0277, $0.0663 and $0.0693 (floor $0.0415). Candidate $0.0085, $0.0101 and
    $0.0102. That is a saving of $0.0448 a run (82%), with every check held: **kept**.
  - The benchmark spent $0.19, plus $0.15 on two invalid baselines.
- **The quality guard stopped those two invalid baselines before anything was applied:**
  - The runner's default root pointed at `.claude/`, so runs saw no agents. Fixed, and a check
    now holds the default root to the project.
  - A Stop hook's extra turn replaced the final message. Fixed: the check now reads every
    main-thread message.
- **One run of six didn't reconcile:** Sonnet's `costUSD` was 1.8% under the base-rate floor. It
  is counted in `decide`'s `unreconciled_runs`, and the harness figure was used.

**Not covered:**
- A rejected outcome on real runs: the only real run was kept. The revert path is covered by
  the self-test, and the invalid baselines stopped before apply.
- Levers without a machine edit, which `plan` skips by design. `long-context` and
  `idle-rebuild`, the two largest findings, are session habits, not file edits.
- Noise across days or Claude Code versions: the floor is measured within one run.
