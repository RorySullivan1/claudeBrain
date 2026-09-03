# MEMORY INDEX  ·  keep ≤ ~80 lines, ≤ ~200 chars per line

## State            (rewrite in place — current truth only, ≤ ~10 lines)
- claudeBrain = a **factory** for Claude Code assets: `.claude/` authors meta-tooling; `example-project/` is the produced consumer. Inventory: its `.claude/CATALOG.md` — never re-list here.
- Consumer families: Power Platform + canvas authoring, VBA (9), VSTO, Python, quant, docs, branding→presentation tier, Outlook HTML pair, GitHub set. Meta: *-authoring skills + `add-*` scaffolders.
- Single-sourcing: operational assets canonical in `example-project/.claude/`; the factory holds symlinks — edit the canonical copy. `settings.json` + per-layer READMEs stay per-tree.
- Hooks: per-hook `*.json` fragments compiled by `build-hooks.py` (drift-guarded); `git_guards.py` dispatcher; `catalog.py` → CATALOG.md; `asset_integrity.py` shape checks.
- Verification: `claim-grounding` + `verify-claims` + evidence ledger (`claim-grounding/reviews/ledger.jsonl`, 83 rows). Every family gated; new assets gate at authoring.
- Prose discipline (#39): coding-standards scope table; `prose_budget.py` hook+library (opt-in via `prose-budget.json`, advisory); memory BUDGETS via `memory.py check`; skill-wins rule.
- Memory: this INDEX (budgeted) + append-only `sessions/*.md`. Version flow: `.meta/version` + `/version-set` + `/version-ship`; roadmap in `.meta/roadmap/`.
- Durable lesson: the recurring defect class is **verification steps that cannot verify** (inverted rules, plan-mode auditors, early-bound probes, crashing advisory wrappers). Check the check.

## Decisions        (append-only; supersede, never delete)
- [2026-08-29] PR #39 (pyHermes prose-discipline port) reviewed mechanically and merged; issues #40–#44 filed from findings + standing gaps. Review record on the PR —
  sessions/2026-08-29-pr39-review-merge-issues.md
- [2026-09-03] **WCAG 2.2 Level AA is the library's accessibility bar** (issue #44): 4.5:1 normal text,
  3:1 large text and UI/graphics; AAA named as the stricter tier. `branding` is canonical and ships
  `references/contrast.py` (boundary-controlled) so the bar is COMPUTED; presentation-design, the
  Outlook skill and its agent point at it rather than restating. Naming numbers here does NOT
  contradict #39's "no line counts in a cross-project standard" — an external published standard
  travels; a per-codebase length cap does not — sessions/2026-09-03-wcag-aa-contrast-bar.md
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
- **No open PRs.** #45 merged (c1b4786), auto-closing issues #40/#41/#42; branch restarted from
  main. After a merge, follow-ups are a NEW PR, never stacked onto merged history.
- **Issue #43 open, kit MERGED**: probes/ in vba-excel-object-model (controls-first .bas) +
  outlook-html-specifications (A/B perturbation emails). Awaits a ~10-min run on Windows/Office;
  results paste into #43, then PROBES.md turns them into label upgrades/fixes + ledger rows.
- **#44 DONE on branch** — WCAG 2.2 AA adopted as the library bar, grounded against the W3C
  Recommendation itself + a self-testing checker; closes on merge.
- verify-claims has run over every family (~390 claims; 83 ledger rows; worst offender VSTO with 22 errors). Ledger is the record; re-argue nothing it already settles.
- Possible future agent siblings: an orchestrator/coordinator. (The line-level-reviewer idea is
  partially realized: `prose-auditor` agent + `/prose-review` command own the prose dimension.)

## Log              (append-only pointers)
- 2026-08-29 | PR #39 reviewed+merged; issues #40–#44 filed; then #40 fixes (IndexError, catch widening, run-slug keys, attribute qualnames) + #41 INDEX compaction |
  sessions/2026-08-29-pr39-review-merge-issues.md
- 2026-08-20 | Outlook HTML pair: outlook-html-specifications skill + outlook-html-designer agent; gated at authoring, ledger 78→83 | sessions/2026-08-20-outlook-html-asset-pair.md
- 2026-08-15 | taskmaster re-review distilled into 14 assets; disputes settled vs MS Learn | sessions/2026-08-15-0100-xlflow-verification-layer-and-review.md
- 2026-08-15 | xlflow → verification layer (claim-grounding + verify-claims + integrity/git-guard hooks); 8-angle review of PR #31, 19 findings fixed |
  sessions/2026-08-15-0100-xlflow-verification-layer-and-review.md
- 2026-08-05 | powerapp_taskmaster assimilation | sessions/2026-08-05-0231-powerapp-taskmaster-assimilation.md
- ≤2026-06-21 | June build-out (memory adoption, hooks/catalog systems, token economy, agent family, presentation pipeline, quant layer) + pre-June history | sessions/ARCHIVE-2026.md
