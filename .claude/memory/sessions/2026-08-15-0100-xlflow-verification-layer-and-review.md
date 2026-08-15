# 2026-08-15 · xlflow → verification layer, then an 8-angle review of PR #31

## What happened
1. **Distilled harumiWeb/xlflow** (Excel-VBA dev harness with unusually mature agent tooling)
   into a verification layer for the factory. The gap it fills: the authoring path checked
   *shape* (skill-authoring) and *performance* (skill-creator's evals) but nothing checked
   whether an asset's factual claims are *true*.
   - New (single-sourced in example-project, symlinked into factory): `claim-grounding` skill
     (+ `references/ledger-schema.md`), `verify-claims` workflow, `asset_integrity.py` hook.
   - Folded (not spawned): search economy → token-optimizer; why-vs-what + keep/discard →
     knowledge-router; mode routing + name-the-authority + post-authoring gates →
     skill-authoring; non-mutating/fail-safe/opt-in/advisory/cap rules → hooks README.
2. **PR handling:** branch already carried the canvas assimilation (8 commits) and PR #31 was
   already open from it — pushed onto it and rewrote the PR body as two parts. PR #30 was
   found already merged into main.
3. **8-angle code review** (`/code-review`, "enhancements, conflicts, efficiencies"). Mid-run
   the `/model` switch killed 3 finders and ate 2 completion notifications — recovered the 2
   finished reports from subagent transcripts, relaunched the 3 dead angles verbatim.
   Deduped ~37 candidates → **19 findings (16 CONFIRMED, 3 PLAUSIBLE)**, reported via
   ReportFindings, then applied all fixes.

## Key findings → fixes (all on PR #31)
- `asset_integrity.py`: SKIP_DIRS matched *ancestor* dirs (hook silently dead under
  `/build/…`) → filter below root; symlink dedup was a string-keyed no-op → resolve()-keyed
  first-visit; parser/dead-code cleanup (one `frontmatter()`, shared `check_frontmatter`).
- Hook economy: 3 per-Bash-call Python spawns → one `git_guards.py` dispatcher fragment;
  guards expose `check(command, root)`, stay standalone-runnable.
- Doctrine conflict (4 angles): pre-paste-review demanded "freshness" the one-way model says
  cannot exist → rewritten to ground-against-repo-records; delegation list now defers to
  delegation.md as authority.
- Truth defects in "grounded" content: invalid one-line Padding YAML in canvas-controls +
  studio-transfer (yaml.safe_load fails; claimed "confirmed from code view");
  editable-table's `row.ThisItem.ID` + double-write flagship snippet → ID-keyed shaped
  records, single bulk Patch.
- Canvas workflows hard-coded taskmaster paths (`tools/validate_pa_yaml.py`,
  `schema/schema.yaml`…) unreachable in example-project → role-based naming + `e.g.` paths +
  missing-roles stop conditions; screen-build steps 1–2 marked parallel; audit consumes the
  validator output instead of re-running it.
- Stale records: workflows README omitted the 3 canvas workflows; memory INDEX claimed PR #30
  open + misattributed the reused branch; knowledge-router's recurrence bullet had no
  destination → routed to reference notes `--type lesson` (context.py help updated).
- Dedup passes: triplicated grounded facts, 4× change lifecycle, air-gap↔studio-transfer
  mutual restatement, 6× shape/performance/truth taxonomy, description trims (canvas family).

## Gotchas worth remembering
- A `/model` switch mid-session kills in-flight subagents and can swallow completion
  notifications — finished results are recoverable from
  `~/.claude/projects/<proj>/<session>/subagents/agent-<id>.jsonl` (last assistant text).
- GitHub allows one open PR per head/base — pushing to a branch with an open PR lands in it;
  update the body rather than trying to open a second.
- `build-hooks.py --check` under an exported `CLAUDE_PROJECT_DIR` checks the wrong tree in
  subshells — run with `env -u CLAUDE_PROJECT_DIR` per tree.

## Open
- Run `verify-claims` against Power Platform + VBA + canvas families (claims preserved, not
  re-verified — now the factory's own review demonstrated why that matters).
- agent-authoring: add the "validating agent must not carry `permissionMode: plan`" check
  (defect seen twice: goal-auditor #30, pre-paste-review).

## Addendum — taskmaster re-review (same session, later)

Re-reviewed powerapp_taskmaster at HEAD (2026-08-14; 9 days of field use since the Aug-5
assimilation) and distilled everything new/corrected into claudeBrain:

- **THE FREEZE RULE WAS FALSE.** taskmaster probed it (tests/scrProbe-layout-freeze.pa.yaml,
  Studio 2026-08-13): layout formulas SURVIVE a code-view paste and stay live; only direct
  manipulation (drag, resize handles, position/size boxes) writes back constants. The MS Learn
  quote always said "drag". Rewrote canvas-design §4/§5 + studio-transfer; the real paste
  hazard is suffixed-name reference resolution. We had consolidated the false claim as the
  owned fact THE SAME DAY the field falsified it — the strongest possible case for the
  verify-claims follow-up.
- **Aug-9 corrections sweep ported** (12 files corrected downstream 4 days AFTER we imported
  them): Graph `Prefer: HonorNonIndexedQueriesWarningMayFailRandomly` + HTTP 400 + eq is
  case-INSENSITIVE; 8-join wall (boundaries doc: nominal 12/query, blocked above 8 — verified);
  TOTALYTD year-end is the 4th arg; ALL('Date') whole-table for running totals; IsBlank→=Blank()
  delegates on simple columns only; Table.ExpandTableColumn for multi-value Person/Lookup;
  pac download -d vs Expand-Archive are alternatives; ModernNumberInput version ungrounded.
- **Bulk-Patch dispute settled vs MS Learn**: taskmaster's "a table is not a valid base record"
  rationale is wrong (Patch(DS, Collection) and Patch(DS, Base, Changes) both take tables), but
  ForAll+Patch is the documented pattern for control-harvest joins. editable-table now teaches
  both forms with their conditions.
- **New content**: SVG data-driven charts (Concat generator, Sequence+Index positions, running
  totals, Mod-positive dashoffset, allow-list+Other categories, integer-viewBox locale rule,
  can/cannot table); App.OnStart comment trap (= and // failures, expand-the-formula-bar,
  IntelliSense diagnostic); GridLayout variant (partially grounded, honestly labeled);
  scale-to-fit vs lock-aspect divergence; theme-blank "squished and black" diagnosis;
  gTheme-not-Theme collision; Set(x,Filter()) kills delegation; component-in-gallery ban;
  per-parent delegable aggregation row in delegation.md; pre-paste-review golden-source-only
  token resolution; context/powerapps-docs-source.md (semantics vs tokens split; "omission
  means unconfirmed, not unsupported").
- Their Aug-9 pre-paste-review freshness fix CONVERGED with ours independently — kept ours
  (role-based), folded their golden-source nuance.
