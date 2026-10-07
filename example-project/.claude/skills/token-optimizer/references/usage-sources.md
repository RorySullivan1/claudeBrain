# Usage sources: which one to trust for each number

This table is what `usage.py` (RorySullivan1/claudebrain#59) must follow. Every row was
settled by `../probes/probe_usage_sources.py` against real logs on 2026-10-07 (Claude Code
cloud session, `claude-opus-5-5` main model, one Haiku subagent), or by the docs where it says so.
Re-run the probe after a Claude Code upgrade, because the log format is internal and undocumented.

## The table

| Number | Authoritative source | Fallback | Known gap |
|---|---|---|---|
| Main-session calls, input and cache tokens | Session log `~/.claude/projects/<slug>/<session>.jsonl`, assistant lines, **deduplicated by `message.id`** | none | Omits background requests (see the "Background" row) |
| Main-session output tokens | The same log. Interactive per-call `output_tokens` **are final** (they matched the harness to within the hidden calls' own output: 10, 10, 19, 17, 0 and 6 tokens across six windows) | `cost-state` delta | Same background requests |
| Subagent calls, input and cache tokens | `<session>/subagents/agent-<agentId>.jsonl`, deduplicated by `message.id`. `agent-<id>.meta.json` gives `agentType`, `model` and the parent's `toolUseId` | none | **The parent log holds none of it**: no sidechain lines and no subagent usage |
| Subagent output tokens | `cost-state`, which includes subagent spend (confirmed 2026-10-07: see "Settled since") | The parent's Agent tool result, `toolUseResult.usage.output_tokens`, which covers **only the subagent's last call** | Subagent-log `output_tokens` **are placeholders** (3 and 2 logged, 142 real), matching the docs' warning. Output from non-final calls is unrecoverable from logs |
| Background (auxiliary) requests | `cost-state` `modelUsage` | OpenTelemetry `claude_code.token.usage` with `query_source="auxiliary"` (docs) | **In no log file.** Two kinds were seen: every Haiku call (all Haiku usage was harness-only), and main-model calls of about 506 uncached input, 6–19 output, and a cache read the size of the whole context, 0–2 per prompt. They added 0–20% to a window's cache reads |
| Session total, estimated USD | `cost-state` `totalCostUSD`, a client-side estimate (docs) | Log tokens × `pricing.json` (`usage.py --price`) | See "When cost-state exists". The table reproduces the harness's per-model `costUSD` exactly (see "Settled since") |
| Which session a call belongs to | The `sessionId` field on each line | none | **Not the filename.** A continued session's file carries its predecessor's calls under their original `sessionId` (51 calls, seen in two files) |
| Authoritative billing | Usage and Cost API, or the Console (docs) | none | Out of scope for #57 |

## When `cost-state` exists, and what it covers

- **It's written when the process goes idle or exits normally**, after the Stop hook and the
  last prompt, and not after every turn. A window with no normal exit has no record.
- **It carries over across resumes of the same session id.** `startTime` stayed fixed, and the
  total kept growing across five resumes ($1.92 → $36.11).
- **A session continued under a new id starts from zero.** The new process began at $1.92
  and the predecessor's $3.49 wasn't carried, though its messages were copied into the new file.
- **Spend from a process that never exited normally is in no record:** 61 calls (62K output
  tokens) before the first record of the new process. A log file can also reach back months
  before its first `cost-state`. The harness total is a lower bound for the file, not its total.

## Rules this sets for `usage.py`

1. Deduplicate by `message.id` **across every file**, and attribute by `sessionId`, never by filename.
2. Read `subagents/agent-*.jsonl` for subagent input and cache tokens. Take subagent output from the
   harness, or mark it "partial (last call only)". Never sum subagent-log `output_tokens`.
3. Report background requests as a separate line, "in harness, not in logs": the harness's
   per-model total minus the log total, over windows that `cost-state` covers.
4. Reconcile only within a `cost-state` window (same `startTime`, between two records). Outside
   one there is nothing to reconcile against, so say so instead of reporting a match.

## Reconciliation tolerance (what "matches" means)

Inside one `cost-state` window, per model:
- **Tokens:** the log may never exceed the harness on any field. Tolerance on that side is 0,
  because an excess means the parser double-counted. A positive gap is expected and must be
  named: background requests, plus subagent output beyond the placeholders when the window ran a
  subagent. For the main model the output gap has been 0–19 tokens per window.
- **Dollars:** pricing the harness's *own* tokens with `pricing.json` must land within $0.001
  of its `costUSD`. That checks the table, not the parser.

`usage.py reconcile` applies both rules and exits 1 on any breach.

## Settled since #58

- **`cost-state` includes subagent spend.** Once the subagent log's calls are put in the window
  of the parent's Agent call, the Haiku input and cache gap is exactly 0. The subagent's 26,431
  cache-write tokens and 24,823 cache-read tokens are in the harness delta. Only its non-final
  output (placeholders in the log) stays as a gap. Run: `usage.py reconcile`, window 13, 2026-10-07.
- **The price table reproduces the harness.** In all 12 window/model rows on this repo's logs
  (Opus 5.5 and Haiku 4.5), the table priced the harness's tokens to its `costUSD` exactly: the
  largest difference was 3e-14 dollars, which is float rounding. Two things fell out of that match:
  - Claude Code's main loop writes the **1-hour** cache. The rows only match at the 1h rate. The
    subagent's writes were 5-minute ones, and the log's per-call `cache_creation` split shows it.
  - The harness's `outputTokens` **already includes** `thinkingTokens`. Pricing output alone matched.

## Pending

- **Does the per-model match still hold for Haiku as a main model?** Every main-session call
  here was Opus, so the "output is final" row is proven for one main model.
- **Opus 5, Fable 5 and Fable 5.1 are priced from the page, not reconciled.** Their sessions had no
  complete `cost-state` window here. The first window that includes one confirms or refutes the row.
- **Haiku 5.5 is priced per prompt length** (over 100,000 tokens costs more). `usage.py` applies the
  tier per call, but a reconcile window only has aggregate harness tokens, so a Haiku 5.5 window
  may report TABLE != HARNESS when nothing is wrong. That failure would be loud, not silent; fix it
  when the first Haiku 5.5 window appears.
- **Does `SessionEnd` fire when a cloud container is reclaimed?** Untested. The spend hook
  updates on every `Stop` so it doesn't depend on the answer (see `hooks/spend_record.py`).
