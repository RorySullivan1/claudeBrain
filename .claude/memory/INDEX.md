# MEMORY INDEX  ·  keep ≤ ~80 lines, ≤ ~200 chars per line

## State            (rewrite in place — current truth only, ≤ ~10 lines)
- claudeBrain = a **factory** for Claude Code assets: `.claude/` authors meta-tooling; `example-project/` is the produced consumer. Inventory: its `.claude/CATALOG.md` — never re-list here.
- Consumer families: Power Platform + canvas, VBA (9), VSTO, Python, quant, docs, branding→presentation, Outlook HTML, GitHub. Meta: *-authoring skills + `add-*` scaffolders.
- Single-sourcing: operational assets canonical in `example-project/.claude/`; the factory holds symlinks — edit the canonical copy. `settings.json` + per-layer READMEs stay per-tree.
- Hooks: `*.json` fragments compiled by `build-hooks.py` (drift-guarded); `git_guards.py` dispatcher; `catalog.py` → CATALOG.md; `asset_integrity.py` shape checks. Probes: `hooks/probes/`.
- Verification, two altitudes: `claim-grounding`/`verify-claims` gate an ASSET's claims (ledger 91 rows); `establish-verification` + `context/verification-surface.md` gate a PROJECT's own work.
- Adoption: `init-project` — brief → `.claude/` by SELECTION (never copy-then-strip) → families from CATALOG → establish-verification → roadmap + ONE cursor (settled, not accidental).
- Prose (#39): coding-standards scope table; `prose_budget.py` hook+library (opt-in, advisory); memory BUDGETS via `memory.py check`; skill-wins rule.
- Memory: this INDEX (budgeted) + append-only `sessions/*.md`. Version flow: `.meta/version` + `/version-set` + `/version-ship`; roadmap in `.meta/roadmap/`.
- Durable lesson: the recurring defect class is **verification steps that cannot verify** (inverted rules, plan-mode auditors, early-bound probes, crashing advisory wrappers). Check the check.

## Decisions        (append-only; supersede, never delete)
- [2026-08-29] PR #39 (pyHermes prose-discipline port) reviewed mechanically and merged; issues #40–#44 filed from findings + standing gaps. Review record on the PR —
  sessions/2026-08-29-pr39-review-merge-issues.md
- [2026-09-02] **First live-probe REFUTATION** (PR #47, another session ran the #43 Excel kit): `UsedRange`
  does shrink after `.Clear`/`.ClearContents`, incl. across save/reopen; it over-reports only while
  FORMATTING outlives data. Skill corrected at source; SpecialCells-1004 and pivot-rename CONFIRMED.
  Proof the probe discipline yields corrections, not just confirmations — sessions/2026-09-10-epic-48-doctrine-vs-enforcement.md
- [2026-09-03] **WCAG 2.2 Level AA is the library's accessibility bar** (issue #44): 4.5:1 normal text,
  3:1 large text and UI/graphics; AAA named as the stricter tier. `branding` is canonical and ships
  `references/contrast.py` (boundary-controlled) so the bar is COMPUTED; presentation-design, the
  Outlook skill and its agent point at it rather than restating. Naming numbers here does NOT
  contradict #39's "no line counts in a cross-project standard" — an external published standard
  travels; a per-codebase length cap does not — sessions/2026-09-03-wcag-aa-contrast-bar.md
- [2026-09-10] **Single-cursor state stays; the constraint is stated, not engineered away** (#51,
  shipped in PR #53). Probed first (`example-project/.claude/hooks/probes/`, 4 controls PASSed) and the
  filing was 2/3 wrong: `roadmap_guard` is ALREADY per-version (its `cursor` was dead code — removed),
  worktrees have their own checkouts, and "append-only sections merge" is false — git has no notion of
  append-only. Nothing is silently corrupted; collisions are LOUD merges preserving both sides. The real
  constraint: the two hunks need OPPOSITE resolutions — append-only keep both; State rewrite from both,
  NEVER take a side — sessions/2026-09-10-1131-epic-48-build.md
- [2026-08-15] **A verifying agent must not carry `permissionMode: plan`** — its value is running the real check; read-only comes from omitting Edit/Write. Codified in agent-authoring; all 12 agents
  swept clean — sessions/2026-08-15-0100-xlflow-verification-layer-and-review.md
- [2026-08-15] One-way air-gap doctrine wins the freshness conflict: pre-paste-review grounds against the repo's records, never demands a freshness pull; canvas workflows name project state by ROLE
  — sessions/2026-08-15-0100-xlflow-verification-layer-and-review.md
- [2026-08-05] powerapp_taskmaster assimilated via plain clone (public repo; no scope needed). Most of its `.claude/` was claudeBrain's own output; only self-grown assets were net-new (7 skills, 2
  agents, 3 workflows, air-gap brief) — sessions/2026-08-05-0231-powerapp-taskmaster-assimilation.md
- [2026-07-24] 8-skill Power Platform family, clustered for a future per-use-case plugin split; reference tables as in-folder sidecars for portability; authored by 8 parallel agents + independent
  doc-verification — sessions/2026-07-24-1338-power-platform-skill-family.md
- [≤2026-06-21] Earlier decisions (factory/consumer split, symlink single-sourcing, hooks-as-fragments, capability catalog, permission tuning, the meta-skill series, presentation tier builds) —
  sessions/ARCHIVE-2026.md

## Threads          (open items; remove when closed)
- **No open PRs.** #46, #47 and #53 (Epic #48) merged; branch restarted from main. After a merge,
  follow-ups are a NEW PR, never stacked onto merged history.
- **Epic #48 SHIPPED** (PR #53; #48–#51 closed). Two follow-ups deliberately not built: the
  verification-surface check as a `SessionStart`/`Stop` hook (decide after a real adoption proves the
  doc's shape), and `/worktree-start` — now unblocked, but its first step must be "refuse if another
  cursor is in flight".
- **#52 open** — run the Outlook probe kit; human-gated (needs classic Outlook). Kit parse-verified; row 78 stands.
- verify-claims has run over every family (~390 claims; 91 ledger rows, 8 probe-grounded). The ledger is
  the record; re-argue nothing it settles.
- Possible future agent sibling: an orchestrator/coordinator. (The line-level reviewer is realized as
  `prose-auditor` + `/prose-review`.)

## Log              (append-only pointers)
- 2026-09-10 | PR #53 merged: Epic #48 shipped, #48–#51 closed; #52 stays open (human-gated) | sessions/2026-09-10-1131-epic-48-build.md
- 2026-09-10 | Epic #48 built end to end (#49 verification surface, #51 single-cursor probe+decision, #50 init-project); ledger 86→90 | sessions/2026-09-10-1131-epic-48-build.md
- 2026-09-10 | Epic #48 (+#49/#50/#51) filed from the reinforcement brief, claims verified against the tree; #47 reconciled (UsedRange REFUTED); #52 for Outlook probes |
  sessions/2026-09-10-epic-48-doctrine-vs-enforcement.md
- 2026-09-03 | WCAG 2.2 AA adopted as contrast bar (#44) + branding/references/contrast.py with boundary control; PR #46 | sessions/2026-09-03-wcag-aa-contrast-bar.md
- 2026-08-29 | PR #39 reviewed+merged; issues #40–#44 filed; then #40 fixes (IndexError, catch widening, run-slug keys, attribute qualnames) + #41 INDEX compaction |
  sessions/2026-08-29-pr39-review-merge-issues.md
- 2026-08-20 | Outlook HTML pair: outlook-html-specifications skill + outlook-html-designer agent; gated at authoring, ledger 78→83 | sessions/2026-08-20-outlook-html-asset-pair.md
- 2026-08-15 | taskmaster re-review distilled into 14 assets; disputes settled vs MS Learn | sessions/2026-08-15-0100-xlflow-verification-layer-and-review.md
- 2026-08-15 | xlflow → verification layer (claim-grounding + verify-claims + integrity/git-guard hooks); 8-angle review of PR #31, 19 findings fixed |
  sessions/2026-08-15-0100-xlflow-verification-layer-and-review.md
- 2026-08-05 | powerapp_taskmaster assimilation | sessions/2026-08-05-0231-powerapp-taskmaster-assimilation.md
- ≤2026-06-21 | June build-out (memory adoption, hooks/catalog systems, token economy, agent family, presentation pipeline, quant layer) + pre-June history | sessions/ARCHIVE-2026.md
