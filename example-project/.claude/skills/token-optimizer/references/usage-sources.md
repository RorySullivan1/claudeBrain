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
| Subagent output tokens | `cost-state` (the docs say the harness total includes subagents; not yet confirmed here, see "Pending") | The parent's Agent tool result, `toolUseResult.usage.output_tokens`, which covers **only the subagent's last call** | Subagent-log `output_tokens` **are placeholders** (3 and 2 logged, 142 real), matching the docs' warning. Output from non-final calls is unrecoverable from logs |
| Background (auxiliary) requests | `cost-state` `modelUsage` | OpenTelemetry `claude_code.token.usage` with `query_source="auxiliary"` (docs) | **In no log file.** Two kinds were seen: every Haiku call (all Haiku usage was harness-only), and main-model calls of about 506 uncached input, 6–19 output, and a cache read the size of the whole context, 0–2 per prompt. They added 0–20% to a window's cache reads |
| Session total, estimated USD | `cost-state` `totalCostUSD`, a client-side estimate (docs) | Log tokens × a sourced price table (#60) | See "When cost-state exists" |
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

## Pending

- **Does `cost-state` include subagent spend?** The docs say yes. The probe's subagent ran after
  the last record, so the next record in this session's log should show Haiku output rise by
  at least 142 over the previous 3,250. Re-run the probe once the session has gone idle.
- **Does the per-model match still hold for Haiku as a main model?** Every main-session call
  here was Opus, so the "output is final" row is proven for one main model.
