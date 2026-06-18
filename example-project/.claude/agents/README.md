# agents/

**Isolated parallel workers.** Subagents spawned with a clean context that do
focused work and return only a summary — so they don't bleed context into the main
session. Good for noisy, error-prone, or narrowly-scoped jobs.

## Format

- One markdown file per agent: `<name>.md`.
- Frontmatter defines the agent: `name`, `description` (when to use it), and
  optionally `tools` (a restricted allowlist) and `model`.
- The body is the agent's system prompt — its focused mandate.

## Typical uses

- A data/fetcher agent that owns one external API and its quirks.
- An auth/worker agent that isolates token errors from the main session.
- A runner agent that executes a task and returns just the result summary.

## Status

**Defined:**
- `finance-quantitative-developer` — a senior Python quant engineer for the `tools/`
  analytics layer (pricing, risk, signals, time-series) that writes and verifies
  quantitative code.
- `token-manager` — a context-economy worker: runs verbose/high-volume tasks (test suites,
  log processing, large-file analysis, fetches) in isolation and returns only a capped
  summary. The delegation target of the `token-optimizer` skill.

Add more with a `<name>.md` + frontmatter.
