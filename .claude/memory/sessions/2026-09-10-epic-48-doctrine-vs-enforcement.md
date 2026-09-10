# 2026-09-10 — Epic #48: the three gaps between doctrine and enforced behavior

**Request:** review an uploaded brief ("issue behavior reinforcement") and open a GitHub
epic with the enhancements it implies.

## Verified before filing (a proposal gets the same gate as a skill)

All three of the brief's claims held against the tree:
1. **No project-level verification asset.** Nothing named or referencing
   `verification-surface`; `air-gap.md` scopes itself to canvas apps in its first sentence.
2. **No cold start.** Neither `workflows/` tree has an init/adoption/bootstrap workflow.
3. **Single-cursor state.** The only `worktree` hit is token-optimizer's search-recall
   advice; `.meta/version` is one file/one cursor; INDEX § State is literally "rewrite in
   place"; `roadmap_guard.py` extracts a single `cursor`. Two worktrees collide on all three
   — so a `/worktree-start` command BEFORE fixing that would corrupt state silently.

Dedupe (the brief asked): **zero open issues** at filing time — #43/#44 closed, #46 merged.

## Filed

- **Epic #48** with the verified evidence per claim, acceptance, non-goals (portfolio
  consolidation excluded; no new enforcement floor yet — the SessionStart/Stop hook question
  is a follow-up once the doc has proven its shape), and dependency order.
- **#49** `establish-verification` workflow + `verification-surface.md` (fold `air-gap.md`
  into the general model as its canvas instance; consumers point at the doc instead of
  re-deriving what they can verify).
- **#50** `init-project` workflow — brief → scaffold → select families from CATALOG →
  establish-verification → seeded roadmap; regression: re-run the taskmaster init brief.
- **#51** single-cursor state: per-branch cursor OR documented constraint — with a probe that
  demonstrates the collision before the fix and its absence after. Precondition for any
  worktree command.

## Out-of-band merges discovered and reconciled

- **#46 merged** (WCAG AA + prose reach + prose-auditor).
- **#47 merged** — another session RAN THE EXCEL PROBE KIT (#43): SpecialCells-1004
  CONFIRMED, pivot-rename collision CONFIRMED (1004 "Unable to set the Name…"), and
  **`UsedRange` REFUTED** — it shrank immediately after `.Clear`/`.ClearContents` and stayed
  shrunk across save/reopen; the over-report is driven by residual FORMATTING outliving data.
  Skill corrected at the source with dated Excel-16.0 labels; three ledger rows upgraded in
  place to `probe:` grounding (count stays 86). **The first live-probe refutation in the
  library — the kit produced exactly the outcome it existed to allow.**
- #43 closed on the Excel half alone; the **five Outlook claims remain field-settled** with
  coverage-gap row 78 standing → filed **#52** (narrow follow-up, not a reopen).
