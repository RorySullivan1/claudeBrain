# 2026-06-18 20:59 · optimize-factory-model

**Goal:** Cut redundant/slow asset-production: dedupe Stop hook + add author-asset workflow & command guardrails

## What happened
- Diagnosed why the prior run (finance-quant-developer build) was slow/repetitive.
  Three causes; two factory-controlled, one not:
  1. **Stop-hook over-nagging** — `cmd_stop_hook` blocked on the first Stop of
     *every* turn (the `stop_hook_active` guard only breaks immediate retries, no
     cross-session dedup) → ~5 forced round-trips.
  2. **Redundant format re-derivation** — ~70k tokens of Explore agents re-reading
     example-project formats already encoded in the meta-skills / add-* commands.
  3. **Repeated plans** — mostly the harness re-entering plan mode on each
     "Continue"; NOT factory-controllable (flagged to user, set expectations).
- Fixes (branch `claude/optimize-factory-model`, commit 8bf5630):
  - `memory.py` `cmd_stop_hook`: per-`session_id` marker in `tempfile.gettempdir()`
    (`claude-session-memory-nudged-<id>.flag`); blocks at most once per session,
    silent thereafter. Fallback nudges once when session_id absent. Added
    `import tempfile`.
  - New `.claude/workflows/author-asset.md` — default build recipe (scope → load
    conventions ONCE, explicit "don't spawn Explore agents to re-derive formats"
    guardrail → scaffold via add-* → batch wiring → structural verify).
  - Guardrail lines added to `add-agent.md` / `add-skill.md`; `workflows/README.md`
    status flipped (author-asset built).
- User chose (AskUserQuestion): dedupe-once-per-session (not full non-block, not
  edit-gated); workflow + command guardrails (not guardrails-only, not a batch cmd).

## Gotchas & dead ends
- Stop hook payload key is `session_id` (Claude Code provides it on Stop).
- No hook *fragment* changed, so settings.json needs no rebuild — `build-hooks.py
  --check` stays green. The change is in the script the fragments call, not config.
- `py_compile` dropped a `__pycache__/` — excluded it from the commit.
- Verified behaviorally: 1st stop blocks, 2nd (same id) silent, stop_hook_active
  silent, no-id blocks once, marker created.

## State at end
- Committed + pushed to `claude/optimize-factory-model`. No PR opened (user didn't
  ask). PR #6 (quant agent) left untouched — separate branch by design.

## Open threads
- Optional follow-up: open a PR for `claude/optimize-factory-model` if wanted.
- Still planned: `skill-authoring`, `context-vs-skill` meta-skills; `author-skill`
  / `harvest-context` workflows; `/validate-asset`, `/add-context` commands.
