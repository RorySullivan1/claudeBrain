# 2026-06-17 · permission-tuning

**Goal:** Stop the repeated "approve edit in .claude" prompts, and narrow the blanket
Bash permission to the command families actually used.

## What happened
- Set `permissions.defaultMode: "acceptEdits"` in committed `.claude/settings.json` —
  the bulletproof "never prompt for file edits" (hot-reloads immediately, repo-wide).
- Corrected the edit allow-rules to the **leading-slash** form
  `Edit(/.claude/**)` + `Edit(/example-project/.claude/**)` (kept as fallback/docs).
- Replaced blanket `Bash` with a focused allow-list: `python`, `python3`, `git`, `gh`,
  `cd`, `set`, `export`, `pwd`, `ls`, `cat`, `grep`, `wc`, `head`, `tail`, `echo`,
  `printf`, `mkdir`, `cp`. Deliberately omitted `rm` (destructive → still prompts).

## Gotchas & dead ends (the root cause)
- The user kept being prompted because **`/agents`-style "always allow" writes a narrow,
  per-directory rule to `~/.claude/settings.json`** (e.g. `Edit(/.claude/skills/agent-finder/**)`),
  so every *new* skill folder re-prompted. Those accumulated in USER settings.
- The broad project rule I'd first added used `Edit(.claude/**)` (no leading slash) and
  did **not** suppress the prompts. Claude Code's own canonical form uses a **leading
  slash** (`/.claude/...`, anchored to project root) — that's the empirical ground truth.
  `acceptEdits` mode sidesteps the glob question entirely for edits.
- Per claude-code-guide: permission changes **hot-reload mid-session** (no restart);
  `Shift+Tab` cycles modes in-session; a higher-precedence `deny` (user/managed) would
  shadow an allow.
- The user's `~/.claude/settings.json` still holds the now-redundant per-directory Edit
  rules — harmless; offered to clean them but left untouched (global/user scope).

## Decisions
- **Supersedes** the earlier "broad `Bash`" decision: Bash is now scoped to the families
  above; edits handled by `acceptEdits` + leading-slash `Edit(/.claude/**)` rules.

## State at end
- No edit prompts (acceptEdits); Bash scoped to session-used commands; settings hot-reloaded.

## Open threads
- Optional: clean redundant per-directory `Edit(...)` rules from `~/.claude/settings.json`.
