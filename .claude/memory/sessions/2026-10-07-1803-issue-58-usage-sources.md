# 2026-10-07 · issue-58-usage-sources

**Goal:** Settle by probe which usage source is authoritative for each spend number (#58)

## What happened
- Built `token-optimizer/probes/probe_usage_sources.py`. It reads only; its self-test is 8/8 with
  2 controls, and three deliberate breaks each turned a case red. Ran it on this repo's two
  cloud-session logs.
- Wrote `token-optimizer/references/usage-sources.md`: the source-of-truth table plus the four
  rules `usage.py` (#59) must follow. Ledger 107 → 112.
- Spawned one tiny Haiku Explore subagent on purpose. No session had run one, and the subagent
  question can only be answered by a real run.

## Findings: all four #58 observations settled
1. **Duplicates:** confirmed and benign. They always carry identical usage, so deduplicate by
   `message.id`. NEW: a continued session's file also carries its predecessor's calls under the
   original `sessionId` (51 calls in two files), so attribute by `sessionId`, not filename.
2. **"cost-state resets on resume": refuted.** It carries across same-id resumes ($1.92 → $36.11
   over 5 resumes). The 12.7M-vs-287M gap was scope: the file predates the first record by
   weeks. But a session continued under a NEW id starts from zero, it's written only at
   idle/exit, and 61 calls with no normal exit are in no record. It's a lower bound.
3. **Background calls are in no log.** That's all Haiku, plus main-model calls of about 506
   input, 6–19 output and a full-context cache read, 0–2 per prompt (0–20% of a window's cache
   reads). Only cost-state or OTel sees them.
4. **Output placeholders: both readings were right.** Main-session output is FINAL (it matched
   the harness to within the hidden calls' own output). Subagent-log output IS placeholder (2–3
   logged against 142 real), and the parent log holds no subagent usage at all.
   `toolUseResult.usage` covers the subagent's last call only.

## Gotchas
- `cost-state` isn't per turn; it's written when the session goes idle. So "does it include the
  subagent" can't be confirmed within the turn that ran the subagent. It's left as a named
  pending check: the next record should show Haiku output above 3,250 + 142.

## Open threads
- Pending: re-run the probe after this session idles, to confirm cost-state includes subagent spend.
- Next in the epic: #59 (`usage.py`), then #60 and #61.
