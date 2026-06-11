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

**Empty scaffold.** No agents defined yet. Add a `<name>.md` with frontmatter to
define one.
