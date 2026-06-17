# 2026-06-17 · agent-finder

**Goal:** Add the `agent-finder` operational skill (enhances subagent selection) to
the factory and the example-project showcase; grant Bash permission per request.

## What happened
- Added `agent-finder` as a second **operational** skill (alongside `session-memory`)
  in both `.claude/skills/` and `example-project/.claude/skills/`. It guides delegation:
  inventory → match → choose topology → delegate, keeping verbose work out of main context.
- Authored its engine `scripts/agents.py` (stdlib only): `list` / `search` / `show` over
  `.claude/agents/*.md` + `~/.claude/agents/*.md` (project wins) plus the three built-ins
  (Explore/Plan/general-purpose). Includes a minimal YAML-frontmatter parser (handles
  folded `>-` description + inline `tools:`).
- Source skill was a paste with mojibake; transcribed to proper UTF-8 (— → …) and
  `python` (not `python3`), same adaptation as `session-memory`/`build-hooks.py`.
- Updated `.claude/skills/README.md` ("Operational skills" section now lists both) and
  the example-project README skills count.

## Gotchas & dead ends
- `.claude/agents/` holds only a README (no real agents yet), so `agents.py` skips files
  without a `name:` frontmatter — `list` currently shows just the three built-ins.
- Same Windows-stdout UTF-8 reconfigure as the other scripts (cp1252 would crash on …/—).

## Decisions
- Granted **broad `Bash`** permission in committed `.claude/settings.json` (alongside the
  `.claude/**` Edit/Write rules), at the user's request ("allow bash commands"). High
  blast radius but the user owns this repo and wants frictionless operation. Could be
  scoped or moved to `settings.local.json` later. Note: permission rules load at session
  start, so it activates next session.

## State at end
- Two operational skills built (`session-memory`, `agent-finder`). Bash allowed (committed).

## Open threads
- None.
