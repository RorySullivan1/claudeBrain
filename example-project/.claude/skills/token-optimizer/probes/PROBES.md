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
