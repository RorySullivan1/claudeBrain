# 2026-10-21 — Epic #62 built: spend measurements become a ranked review

**Issues:** #63 (spend-levers catalog), #64 (spend-auditor agent), #65 (/spend-audit). Epic #62 closes from them.

## What was built
- `token-optimizer/references/spend-levers.md` — 13 levers in catalog order, each with Signal, Mechanism,
  Source, Direction, Trade-off and Apply. Every cache mechanism cites code.claude.com/docs/en/prompt-caching.
- `usage.py` gains `cache_profile()`: `cache_by_session` (TTL, context per call, standing prefix, rebuilds by
  cause, pauses between the two TTLs, always-loaded edits) and `top_rebuilds`. A rebuild = a main call after
  the first writing ≥ 20,000 and reading less than it writes; cause = model switch, idle past TTL, or other.
- `scripts/audit.py` — deterministic matcher: one `@rule` per lever, in catalog order; a finding is material
  at max(3% of spend, $0.50); top 5 findings, 40-line render; below-threshold findings become checks.
- `probes/probe_audit.py` — 34/34: planted signals, clean controls, catalog drift, five breaks.
- `agents/spend-auditor.md` (Haiku, read-only, 30-line report) and `commands/spend-audit.md`; factory symlinks.
- Ledger 133 → 148: one row per catalog mechanism, plus the audit's acceptance run.

## Decisions and why
- **The analysis is a script, the agent only runs and relays it.** Determinism makes "finds the planted
  signal, stays silent on the control" testable; an agent's judgment isn't.
- **`always-loaded-edits` is a lever that should not fire.** The docs say a mid-session CLAUDE.md edit
  keeps the cache (and doesn't apply until /clear, /compact or restart). The rule reports a contradiction
  only if a rebuild follows such an edit. Real logs: none did.
- **long-context and idle-rebuild overlap** (compaction cuts both); the report says not to add them.
- **A built-in subagent has no file**: the model change names the dispatch `model` or the env var.

## Real numbers (this repo's logs, 2026-10-21, API list price)
- 24 sessions ~$728. Material: long-context ~$206, idle-rebuild ~$115 (45 rebuilds, 18.0M tokens, one session).
- The 1h main TTL earns its premium (~$93 against ~$254 of pause rebuilds a 5m TTL would add).
- Acceptance run (`--session current`, via a general-purpose agent carrying the spend-auditor body, since a
  new agent file only loads in a new session): 3 findings, every figure traced to the script.
  It surfaced one defect, fixed before shipping: the model change line named both remedies at once.

## Open
- #66 (optimize-spend loop that proves each saving) is next.
- The agent definition itself is unexercised as a registered agent until a fresh session loads it.
