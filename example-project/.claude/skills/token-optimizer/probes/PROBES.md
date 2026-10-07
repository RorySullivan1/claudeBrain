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
