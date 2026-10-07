# MEMORY INDEX  ·  keep ≤ ~80 lines, ≤ ~200 chars per line

## State            (rewrite in place — current truth only, ≤ ~10 lines)
- claudeBrain = a **factory**: `.claude/` authors meta-tooling; `example-project/` is the produced consumer. Inventory: its `CATALOG.md`, never here.
- Families: Power Platform + canvas, VBA (9), VSTO, Python, quant, docs, branding→presentation, Outlook HTML, GitHub, print-PDF pair. Meta: *-authoring + `add-*`.
- GitHub: `/epic`+`/issue` → issue templates (epics SEPARATE from roadmap); PR + issue templates in `.github/`; `installs.json` copies drift-checked.
- Single-sourcing: operational assets canonical in `example-project/.claude/`; factory holds symlinks. `settings.json` + per-layer READMEs stay per-tree.
- Hooks: `*.json` fragments compiled by `build-hooks.py` (drift-guarded); `git_guards.py` dispatcher; `catalog.py` → CATALOG.md; `asset_integrity.py` shape checks. Probes: `hooks/probes/`.
- Verification, two altitudes: `claim-grounding`/`verify-claims` gate an ASSET's claims (ledger 133 rows); `establish-verification` + `context/verification-surface.md` gate a PROJECT's own work.
- Adoption: `init-project` — brief → `.claude/` by SELECTION (never copy-then-strip) → families from CATALOG → establish-verification → roadmap + ONE cursor (settled, not accidental).
- Prose (#39): coding-standards scope table; `prose_budget.py` (opt-in, advisory); memory BUDGETS via `memory.py check`; skill-wins rule.
- Memory: this INDEX (budgeted) + append-only `sessions/*.md`. Versions: `.meta/version` + `/version-set`/`/version-ship`; roadmap `.meta/roadmap/`.
- Durable lesson: recurring defect = **verification steps that cannot verify** (inverted rules, plan-mode auditors, early-bound probes, fail-safes hiding failure). Check the check.

## Decisions        (append-only; supersede, never delete)
- [2026-10-07] **Factory records its spend** (#61): `.claude/spend/log.jsonl`, upserted per `Stop` — sessions/2026-10-07-1845-epic-57-spend.md
- [2026-09-15] **Print-to-PDF pair built** (`weasyprint-print-html` + `factsheet-template`): engine
  skill + branded layer, split by change cadence. Renderer SWAPPABLE — `render_worker.py` is the only
  file importing WeasyPrint. Three lessons generalize: (1) **a doc that IS a rule set must be
  probe-backed and drift-checked**; (2) **a security flag that only warns is not a gate** —
  `--strict-fetch` contained the fetch but the render finished, so `--fail-on-fetch-error` was added;
  (3) **a realistic render is a good SCRATCH artifact and a poor repo fixture** — it found 3 defects
  the small fixtures missed, but invented returns inside a factsheet template are the hazard the
  compliance slots exist to prevent; trimmed 2026-09-16 to a same-footprint stand-in, round figures,
  `_sample` marker. `print-qa` NOT built (phase 2) — sessions/2026-09-15-weasyprint-print-skills.md
- [2026-09-22] **Epics stay separate from the roadmap** (user); a roadmap→epic link waits until it's a chore.
  Epics close from their CHILDREN (`epic-autoclose`), never a PR keyword — sessions/2026-09-22-1850-epic-issue-commands.md
- [2026-08-29] PR #39 (prose-discipline port) merged; issues #40–#44 filed from findings —
  sessions/2026-08-29-pr39-review-merge-issues.md
- [2026-09-10] **Single-cursor state stays; the constraint is stated, not engineered away** (#51,
  shipped in PR #53). Probed first (`example-project/.claude/hooks/probes/`, 4 controls PASSed) and the
  filing was 2/3 wrong: `roadmap_guard` is ALREADY per-version (its `cursor` was dead code — removed),
  worktrees have their own checkouts, and "append-only sections merge" is false — git has no notion of
  append-only. Nothing is silently corrupted; collisions are LOUD merges preserving both sides. The real
  constraint: the two hunks need OPPOSITE resolutions — append-only keep both; State rewrite from both,
  NEVER take a side — sessions/2026-09-10-1131-epic-48-build.md
- [2026-09-02, 09-03] Archived: UsedRange REFUTED by live probe (#47); WCAG 2.2 AA is the contrast bar,
  computed by `branding/references/contrast.py` (#44). Both binding — sessions/ARCHIVE-2026.md
- [2026-07-24 → 2026-08-15] Archived: verifying-agent posture (no `permissionMode: plan`),
  one-way air-gap doctrine, taskmaster assimilation, the 8-skill Power Platform family. All four
  still binding — full text in sessions/ARCHIVE-2026.md
- [≤2026-06-21] Earlier decisions (factory/consumer split, symlink single-sourcing, hooks-as-fragments, capability catalog, permission tuning, the meta-skill series, presentation tier builds) —
  sessions/ARCHIVE-2026.md

## Threads          (open items; remove when closed)
- **AI-spend epics**: #57 done (PR #73). Next #62, then #66. Gaps: SessionEnd on reclaim; Opus 5/Fable unreconciled. No `epic` label (user's call).
- **Print pair: page images never seen** — poppler absent, so `snapshot.py`'s rasterise + live
  `pdffonts` are the one untested surface; run on the first real factsheet. Pending from the user:
  brand fonts (slot empty), approved compliance copy (placeholders), internal-repo copy.
- **#70 merged (PR #71)**; xlVizer can now drop its local patches and re-copy.
- **Epic #48 SHIPPED** (PR #53; #48–#51 closed). Two follow-ups deliberately not built: the
  verification-surface check as a `SessionStart`/`Stop` hook (decide after a real adoption proves the
  doc's shape), and `/worktree-start` — now unblocked, but its first step must be "refuse if another
  cursor is in flight".
- **#52 open** — run the Outlook probe kit; human-gated (needs classic Outlook). Kit parse-verified; row 78 stands.
- verify-claims has covered every family (~390 claims); the ledger is the record.
- Possible future agent sibling: an orchestrator/coordinator.

## Log              (append-only pointers)
- 2026-10-07 | PR #73 merged; epic #57 closed by epic-autoclose (1st real close) | sessions/2026-10-07-1845-epic-57-spend.md
- 2026-10-07 | Epic #57 built (#59–#61: usage.py, pricing, spend hook); ledger 112→133 | sessions/2026-10-07-1845-epic-57-spend.md
- 2026-10-07 | #58: usage sources settled by probe; main-log output final, subagent-log output placeholder | sessions/2026-10-07-1803-issue-58-usage-sources.md
- 2026-10-07 | #70: xlVizer fixes ported probe-first (17/17, 47/47); `**Routes to:**` check; tracker refs qualified | sessions/2026-10-07-1737-issue-70-xlvizer-fixes.md
- 2026-10-01 | Spend-audit proposal refined + filed as epics #57/#62/#66 (13 issues); usage-log traps verified | sessions/2026-10-01-1458-spend-epics.md
- 2026-09-23 | PR + issue templates in .github/ (issue ones = the skill's, slot format); installs.json drift check; ledger 101→104 | sessions/2026-09-23-1159-pr-template.md
- 2026-09-22 | /epic + /issue, issue templates, issue_body.py gate, epic-autoclose (14/14) | sessions/2026-09-22-1850-epic-issue-commands.md
- 2026-09-15 | WeasyPrint + factsheet skills built, probed live; ledger 91→96 | sessions/2026-09-15-weasyprint-print-skills.md
- 2026-09-10 | Epic #48 built (#49–#51, ledger 86→90) + shipped in PR #53; #52 stays open (human-gated) | sessions/2026-09-10-1131-epic-48-build.md
- 2026-09-10 | Epic #48 filed; #47 UsedRange REFUTED | sessions/2026-09-10-epic-48-doctrine-vs-enforcement.md
- 2026-09-03 | WCAG 2.2 AA contrast bar (#44, PR #46) | sessions/2026-09-03-wcag-aa-contrast-bar.md
- 2026-08-29 | PR #39 reviewed+merged; issues #40–#44 filed; then #40 fixes (IndexError, catch widening, run-slug keys, attribute qualnames) + #41 INDEX compaction |
  sessions/2026-08-29-pr39-review-merge-issues.md
- 2026-08-20 | Outlook HTML skill + designer agent; ledger 78→83 | sessions/2026-08-20-outlook-html-asset-pair.md
- 2026-08-05 → 08-15 | taskmaster assimilation + re-review; xlflow → verification layer (PR #31) | sessions/2026-08-15-0100-xlflow-verification-layer-and-review.md
- ≤2026-06-21 | June build-out (memory adoption, hooks/catalog systems, token economy, agent family, presentation pipeline, quant layer) + pre-June history | sessions/ARCHIVE-2026.md
