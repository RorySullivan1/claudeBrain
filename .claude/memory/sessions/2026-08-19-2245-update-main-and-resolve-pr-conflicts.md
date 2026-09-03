# 2026-08-19 22:45 · update-main-and-resolve-pr-conflicts

**Goal:** Update main and resolve conflicts in PRs #35/#36

## What happened
- Diagnosed: local `main` was **29 commits behind** `origin/main` (local HEAD = f577bdd, merge of #30; origin/main = c094ed5, merge of #34). Clean-FF ancestor — no divergent local commits.
- The "uncommitted items" were minor edits on that stale base, already superseded by origin/main's 29 commits (e.g. origin added the "verifying agents shouldn't use `plan`" section to agent-authoring/SKILL.md). Plus one untracked, novel session log `2026-08-10-1954-asset-audit-fixes.md`.
- Per user choice ("Discard everything, FF"): created safety branch `backup/pre-update-main-f577bdd`, then `git reset --hard origin/main` + `git clean -fd`. **main is now updated, clean, 0/0 vs origin/main.**
- PRs #35 & #36 are DUPLICATE ports ("Port ... back from powerapp_taskmaster"), both branched from the same stale f577bdd. That work already landed + was refined on origin/main via: `08bb56d` Assimilate Studio air-gap, `34ef8a9` Assimilate canvas-source pair, `bdca771` apply 19 findings from 8-angle review, `4d40892` re-sync canvas family vs powerapp_taskmaster HEAD. Nearly all conflicts are add/add.
- Launched 2 background agents (per user choice "Investigate, then recommend") to do per-file verdicts: main-dominates / PR-has-newer / mixed. Await results before any merge/close.

## Gotchas & dead ends
- `git rev-list --left-right --count origin/main...HEAD` = `29 0` → origin is AHEAD; don't misread as local ahead.
- PR #36 tip commit is dated TODAY (Aug 19), newer than main's Aug-15 re-sync — may carry newer upstream content (e.g. studio-transfer gains a bidirectional "pull the app / pac canvas download" lifecycle main's one-way version lacks). So main does NOT strictly dominate #36 — verify per-file.
- Local refs `pr-35`, `pr-36` fetched from refs/pull/*/head for comparison.

## Resolution (complete)
- Both agents returned **CLOSE BUT CHERRY-PICK**. The "#36 bidirectional-pull" premise did NOT hold — both PRs describe the same one-way gap; main is the refined/generalized version and merging either would revert doc corrections (Graph `manage` not `owner`, debunked DAX compression lore, wrong Power Query `JoinKind` list missing LeftSemi/RightSemi, re-added `permissionMode: plan`).
- Salvaged **7** genuinely net-new nuggets (deduped; #35's only nugget = the delegation Live-Monitor section, also in #36) onto main's versions on branch `claude/salvage-port-nuggets` → **PR #37**:
  1. delegation.md — Live Monitor / getRows positive delegation test
  2. power-fx SKILL.md — optional filter = no-op StartsWith/Coalesce predicate
  3. pre_read_guard.py — EXEMPT_DIRS never-truncate-golden-source guard
  4. sharepoint-list-architecture — conditional-required rules live in the app
  5. powerapp-canvas-development — SetFocus limits, hidden-control Select(), block-scalar # trap + lints
  6. powerapp-canvas-design — screen-scope paste can drop X (survival is control-scope only)
  7. powerapp-canvas-controls — grounded per-control modern versions + TriggerOutput/FocusOut/AccessibleLabel
- Applied additive-only (no PR reverts/path re-hardcoding). Commit 37b4044 (+282/-14, 7 files).
- **Closed #35 and #36** as superseded with comment pointing at #37.

## State at end
- main = origin/main (c094ed5), clean. PR #37 open (salvage). #35/#36 closed. pr-35/pr-36 local refs deleted.
- Backup branch `backup/pre-update-main-f577bdd` still exists (holds the discarded pre-update state) — safe to delete once #37 lands.

## Caveat / open thread
- Item 7's modern-control version tokens (`@1.1.1`/`@1.0.2`/etc.) were grounded on the PR side and NOT re-verifiable against powerapp_taskmaster HEAD from here; a wrong token silently fails a whole paste. Flagged in the #37 body — spot-check against live Studio before relying.
