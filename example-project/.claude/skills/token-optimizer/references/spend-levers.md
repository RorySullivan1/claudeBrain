# Spend levers: from a measured signal to the change that addresses it

The catalog `../scripts/audit.py` matches against (RorySullivan1/claudebrain#62, #63). Each
lever names the `usage.py report --json` field it reads, the mechanism with its source, which
way the change moves spend, what it costs you, and where to apply it. Every mechanism was read
on its source page on 2026-10-21 and has a row in `claim-grounding/reviews/ledger.jsonl`.

`audit.py` has one rule per lever below, by the same id, and `../probes/probe_audit.py` fails if
the two lists drift. A rule turns a signal into an **estimated** saving: the token counts are
measured, the dollars are API list price from `pricing.json`, and any assumption is stated in
the finding. On a subscription the limit is plan usage, not dollars, but the token arithmetic
is the same. A finding is **material** when its estimate is at least 3% of the profile's
estimated spend and at least $0.50. Below that, the audit says "no material finding".

Each lever's **Measured** field is written by the `optimize-spend` workflow (#66), never by hand.
One line per run records the change, the saving per benchmark run against its noise floor,
whether every task's check held, and whether the change was kept or rejected. A rejected change
stays recorded, because a lever that failed is evidence too. Where a lever has a measured
outcome for a finding's target, `audit.py` ranks the finding by the measured cut instead of the
estimate, and turns a rejected one into a check that names the run.

Three facts most levers rest on:
- **Claude Code re-sends the whole context on every request**, and the cache serves the
  unchanged prefix at the cache-read rate. So every token kept in context is paid for again on
  every later call ([costs: why usage climbs](https://code.claude.com/docs/en/costs#why-usage-climbs-in-a-long-session)).
- **The cache is an exact prefix match**: "a change anywhere in the prefix recomputes everything
  after it" ([prompt caching](https://code.claude.com/docs/en/prompt-caching#how-the-cache-is-organized)).
- **Writes cost more than reads**: a 5-minute write is 1.25x the input price, a 1-hour write 2x,
  a read 0.1x or less ([API pricing](https://platform.claude.com/docs/en/build-with-claude/prompt-caching#pricing)).
  Opus 5.5's reads are 0.05x, which `pricing.json` carries per model.

## Cache lifetime and rebuilds

### `idle-rebuild`
- **Signal:** `cache_by_session[].rebuilds.idle` and `.idle_tokens`, with `top_rebuilds[]` where `cause` is `idle`: a main call after the session's first that writes at least 20,000 tokens, reads less than it writes, and comes after a gap at least as long as the session's TTL.
- **Mechanism:** a cached prefix expires after a period of inactivity, and "the first message after a break longer than the cache lifetime misses the cache and reprocesses your full context" at the write rate. Compacting while the cache is warm reads the prefix at the read rate, and after a break the turn rebuilds only the shorter summary.
- **Source:** https://code.claude.com/docs/en/prompt-caching#cache-lifetime ; https://code.claude.com/docs/en/prompt-caching#compacting-the-conversation ; https://code.claude.com/docs/en/costs#why-usage-climbs-in-a-long-session ; measured by `probe_audit.py --real` (2026-10-21: 45 such rebuilds rewrote 18.0M tokens in one session).
- **Direction:** down. Each break costs a summary-sized write instead of a context-sized one.
- **Trade-off:** compaction drops detail from the conversation, and `/clear` drops all of it. The estimate assumes a 20,000-token summary.
- **Apply:** run `/compact` at a natural break before stepping away, or `/clear` when the next task is unrelated. In a terminal session leave `idleCompaction` on (the default). A `/goal` check-in, a scheduled task or a cross-session message resumes an idle session with its whole context too; `CLAUDE_CODE_GOAL_CHECKIN_MINUTES=0` stops goal check-ins.
- **Measured:** none yet.

### `cache-ttl-main`
- **Signal:** `by_model[]` main-scope `cache_write_1h` and `cache_write_5m`, against `cache_by_session[].pauses_between_ttls.tokens`: the context carried across every gap of 5 to 60 minutes, which survives a 1-hour TTL and expires under a 5-minute one.
- **Mechanism:** the 1-hour TTL "keeps the cache warm through longer breaks but charges a higher rate for cache writes" (2x the input price against 1.25x). Claude Code requests the hour for the main conversation only on a subscription within plan usage, and five minutes on usage credits, an API key or a cloud provider.
- **Source:** https://code.claude.com/docs/en/prompt-caching#which-ttl-each-request-gets ; https://code.claude.com/docs/en/prompt-caching#choose-the-ttl-yourself ; https://platform.claude.com/docs/en/build-with-claude/prompt-caching#pricing
- **Direction:** either way. The rule prices the 1-hour premium on every main write against the rebuilds a 5-minute TTL would add at the measured pauses, and recommends the cheaper TTL, or reports that the current one earns its cost.
- **Trade-off:** 5 minutes makes every pause past five minutes a full rebuild. 1 hour charges more for every write, which bursts of work that never pause waste.
- **Apply:** the `promptCacheTtl` setting or `CLAUDE_CODE_PROMPT_CACHE_TTL`, `5m` or `1h` (Claude Code v2.1.242+). `FORCE_PROMPT_CACHING_5M=1` overrides both buckets.
- **Measured:** none yet.

### `cache-ttl-subagent`
- **Signal:** `by_model[]` subagent-scope `cache_write_1h`.
- **Mechanism:** subagents sit in the "everything else" TTL bucket and get five minutes even on a subscription unless someone chose longer. A 1-hour write costs 2x the input price against 1.25x, and a subagent's cache is its own: "Its first request doesn't read the parent's cache".
- **Source:** https://code.claude.com/docs/en/prompt-caching#subagents-and-the-cache ; https://code.claude.com/docs/en/prompt-caching#choose-the-ttl-yourself ; https://platform.claude.com/docs/en/build-with-claude/prompt-caching#pricing
- **Direction:** down, by the 1-hour premium on subagent writes.
- **Trade-off:** a long-running subagent that pauses more than five minutes between its own calls would rebuild. Most runs are minutes long.
- **Apply:** remove `ENABLE_PROMPT_CACHING_1H`, and set `subagentPromptCacheTtl` or `CLAUDE_CODE_SUBAGENT_PROMPT_CACHE_TTL` to `5m`, or drop an agent's `experimental` `cacheTtl`.
- **Measured:** none yet.

### `mid-session-switch`
- **Signal:** `cache_by_session[].rebuilds.model_switch`, with `top_rebuilds[]` where `cause` is `model_switch`.
- **Mechanism:** "Each model has its own cache. Switching with `/model` means the next request reads the entire conversation history with no cache hits." On most models a mid-session effort change does the same (not on Opus 5.5, Sonnet 5.5, Haiku 5.5 or Fable 5.1 with an API key or a subscription), and so does a skill whose frontmatter names another model.
- **Source:** https://code.claude.com/docs/en/prompt-caching#switching-models ; https://code.claude.com/docs/en/prompt-caching#changing-effort-level
- **Direction:** down, by the rebuild writes.
- **Trade-off:** none in cost. Pick the model and effort at the start of the session, or switch at a `/clear`.
- **Apply:** set the model and effort before the first prompt; avoid `opusplan` toggling in a long session; check skill and command `model:` frontmatter.
- **Measured:** none yet.

### `always-loaded-edits`
- **Signal:** `cache_by_session[].always_loaded_edits` and `.rebuilds_after_edit`: an Edit or Write to `CLAUDE.md`, `CLAUDE.local.md`, `MEMORY.md` or the session-memory `INDEX.md`, and whether a rebuild followed before the next call.
- **Mechanism:** this is a lever that should **not** fire. The project-root and user `CLAUDE.md` "are read once at session start and held in memory. Editing them mid-session does not invalidate the cache, but the edit also doesn't apply" until `/clear`, `/compact` or a restart. A rebuild right after such an edit therefore has another cause: tool definitions, the model, or an expired TTL.
- **Source:** https://code.claude.com/docs/en/prompt-caching#editing-claude-md-mid-session ; measured by `probe_audit.py --real` (2026-10-21: no mid-session edit to these files in this repo's logs; the one mid-session `settings.json` edit, which the signal doesn't count, was followed by a call that read 281,664 and wrote 219).
- **Direction:** none. The rule reports a contradiction when a rebuild follows an edit, and otherwise confirms the docs.
- **Trade-off:** the edit doesn't reach the running session, so a rule change made mid-session isn't in force until the next `/clear` or `/compact`.
- **Apply:** nothing to change for cost. To make an edit take effect, `/compact` or start a new session.
- **Measured:** none yet.

## Context carried per call

### `long-context`
- **Signal:** `cache_by_session[].context_per_call` (input-side tokens per main call) and `.main_calls`.
- **Mechanism:** "Claude Code sends your full conversation with every request", re-read at the cached rate, so "a one-line question in a session that has been open all day still draws usage for the whole conversation". "Stale context wastes tokens on every subsequent message."
- **Source:** https://code.claude.com/docs/en/costs#why-usage-climbs-in-a-long-session ; https://code.claude.com/docs/en/costs#manage-context-proactively
- **Direction:** down. The estimate prices the context above 150,000 tokens per call at the cache-read rate.
- **Trade-off:** clearing or compacting loses conversation detail, and `/compact` on a large context is itself a large request. The 150,000 target is an assumption.
- **Apply:** `/clear` between unrelated tasks (`/rename` first, `/resume` to return); `/compact` with instructions at natural breaks; one session per task.
- **Measured:** none yet.

### `standing-context`
- **Signal:** `cache_by_session[].prefix_tokens`: the smallest input side of any main call in the session, which no call can go below. Its median across sessions is the standing prefix: system prompt, tool definitions, `CLAUDE.md`, memory and the skill listing.
- **Mechanism:** the project-context layer (`CLAUDE.md`, auto memory, unscoped rules) loads at session start and rides in every request. "Move instructions from CLAUDE.md to skills" because skills "load on-demand only when invoked"; "Aim to keep CLAUDE.md under 200 lines". MCP tool definitions are deferred by default.
- **Source:** https://code.claude.com/docs/en/prompt-caching#how-the-cache-is-organized ; https://code.claude.com/docs/en/costs#move-instructions-from-claudemd-to-skills ; https://code.claude.com/docs/en/costs#reduce-mcp-server-overhead
- **Direction:** down. The estimate prices trimming 10% of the median prefix over every main call, at the cache-read rate.
- **Trade-off:** most of the prefix is Claude Code's own system prompt and tools, which no project can trim. The 10% is an assumption, and only `CLAUDE.md`, memory, skills and MCP servers are yours to cut.
- **Apply:** trim `CLAUDE.md` and the memory INDEX; move workflow detail into skills; prune unused skills (or set `disable-model-invocation: true`); disable unused MCP servers in `/mcp`. Measure files with `tokens.py estimate`.
- **Measured:** none yet.

### `tool-output-size`
- **Signal:** `top_tool_results[]` with `context` `main` and `chars` over 20,000, and the session's `main_calls`.
- **Mechanism:** a tool result appends to the conversation and is re-sent with every later request. "Delegate these to subagents so the verbose output stays in the subagent's context while only a summary returns."
- **Source:** https://code.claude.com/docs/en/costs#delegate-verbose-operations-to-subagents ; https://code.claude.com/docs/en/costs#why-usage-climbs-in-a-long-session
- **Direction:** down. The estimate assumes a result is re-read on half the session's later main calls.
- **Trade-off:** a delegated read returns a summary, so a detail the summary drops costs a second look.
- **Apply:** send bulk reads, test runs and fetches to the `token-manager` agent or Explore; page large files with `offset`/`limit`; narrow MCP queries.
- **Measured:** none yet.

### `bash-filter`
- **Signal:** `top_tool_results[]` with `tool` `Bash`, `context` `main` and `chars` over 12,400: the shipped `post_bash_filter` hook caps output at 12,000 characters plus its elision marker.
- **Mechanism:** the `PostToolUse` hook replaces long Bash output with its head, tail and an elision marker (`hooks/post_bash_filter.py`: `MAX_LINES = 200`, `MAX_CHARS = 12_000`). A longer result in the main context means the hook isn't installed or didn't run. Preprocessing in a hook is the docs' own example of cutting context.
- **Source:** `hooks/post_bash_filter.py` ; https://code.claude.com/docs/en/costs#offload-processing-to-hooks-and-skills
- **Direction:** down, by the oversize part re-read on later calls.
- **Trade-off:** the elided middle is gone from context. Rerun with a narrower command to see it.
- **Apply:** wire `post-tool-use-bash-filter.json` into `settings.json` through `build-hooks.py`.
- **Measured:** none yet.

### `read-guard`
- **Signal:** `top_tool_results[]` with `tool` `Read`, `context` `main` and `chars` over 60,000: the shipped `pre_read_guard` hook's threshold.
- **Mechanism:** the `PreToolUse` hook limits an unpaged Read of a file over 60,000 bytes to its first 1,500 lines (`hooks/pre_read_guard.py`). A larger Read result in the main context means the hook is absent, the read was paged on purpose, or the file sits in `EXEMPT_DIRS`.
- **Source:** `hooks/pre_read_guard.py` ; https://code.claude.com/docs/en/costs#why-usage-climbs-in-a-long-session
- **Direction:** down, by the oversize part re-read on later calls.
- **Trade-off:** a capped read is incomplete. The hook says so, and the model can page the rest.
- **Apply:** wire `pre-tool-use-read-guard.json` through `build-hooks.py`; read a slice with `offset`/`limit`.
- **Measured:** none yet.

## Models and output

### `model-per-agent`
- **Signal:** `by_subagent_type[].models` and `.usd`, repriced at the next cheaper model of the same family generation in `pricing.json` (Opus to Sonnet, Sonnet to Haiku).
- **Mechanism:** a subagent's `model` field takes `sonnet`, `opus`, `haiku`, `fable`, a full model ID or `inherit`, and "For simple subagent tasks, specify `model: haiku`". A subagent that inherits runs on the session's model, which a switch to Opus raises for every inheriting agent.
- **Source:** https://code.claude.com/docs/en/sub-agents#choose-a-model ; https://code.claude.com/docs/en/costs#choose-the-right-model
- **Direction:** down, by the price difference on the same tokens. Subagent output is the last call's only, so the estimate understates it.
- **Trade-off:** a cheaper model may do the job worse. Confidence is low until one run on the cheaper model is compared.
- **Apply:** set `model:` in `.claude/agents/<name>.md`; for a built-in agent, which has no file, pass `model` when dispatching it or set `CLAUDE_CODE_SUBAGENT_MODEL` as the default.
- **Measured:** 1 optimize-spend run, newest last.
  - `2026-10-21` `python-developer` model → haiku: saving $0.0448 a run (82.4%), noise floor $0.0415; quality held; **kept**

### `effort-level`
- **Signal:** main-scope output tokens (`by_model[].tokens.output`, which includes thinking) priced as a share of the main conversation's estimated spend.
- **Mechanism:** "Thinking tokens are billed as output tokens, and the default budget can be tens of thousands of tokens per request". Lower effort with `/effort`, `--effort`, `CLAUDE_CODE_EFFORT_LEVEL` or `effortLevel`, or per skill or subagent with an `effort` key in its frontmatter.
- **Source:** https://code.claude.com/docs/en/costs#adjust-extended-thinking ; https://code.claude.com/docs/en/model-config#adjust-effort-level ; https://code.claude.com/docs/en/prompt-caching#changing-effort-level
- **Direction:** down. The rule fires when output is at least 30% of main spend, and the estimate assumes a 25% cut in output.
- **Trade-off:** less reasoning on hard tasks. On most models a mid-session change also rebuilds the cache; Opus 5.5, Sonnet 5.5, Haiku 5.5 and Fable 5.1 keep it.
- **Apply:** pick the effort level at the start of a session for the kind of work, rather than leaving it high by default; give a mechanical skill or subagent a lower `effort` in its frontmatter.
- **Measured:** none yet.

### `subagent-fanout`
- **Signal:** the subagent scope's share of estimated log spend (`by_model[]` rows with `scope` `subagent`), and `by_subagent_type[].runs` and `.tokens.cache_write`.
- **Mechanism:** "every subagent ... sends its own requests on top of the main conversation's", and a subagent's "first request doesn't read the parent's cache", so each run builds its own context from scratch.
- **Source:** https://code.claude.com/docs/en/costs#why-usage-climbs-in-a-long-session ; https://code.claude.com/docs/en/prompt-caching#subagents-and-the-cache
- **Direction:** down. The rule fires when subagents carry at least 40% of log spend, and the estimate assumes half the runs could be merged or done inline, saving their context build.
- **Trade-off:** isolation is why the subagents exist. Fewer runs means more of their output lands in the main context, which `long-context` then charges for.
- **Apply:** cap fan-out and tell each worker what to return; merge small sibling tasks into one run; keep trivial tasks inline.
- **Measured:** none yet.
