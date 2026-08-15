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

## Addendum 2 — verify-claims run on Power Platform + VBA (item 1)

First real exercise of the truth gate. 11 parallel verifiers (7 Power Platform, 4 VBA),
~190 load-bearing claims graded against Microsoft Learn; a citation counted only when the
fetched text stated the claim. Two verifiers died on a session limit and were relaunched,
seeded with the specific claims their predecessors were mid-check on.

**8 corrections:** `First` wrongly listed non-delegable (power-fx-review + delegation.md —
Learn names it delegable; highest impact, it would make a reviewer flag correct code);
JoinKind enumerated 6 of 8 values; enhanced-component-properties toggle moved to
Settings>Updates>New (on by default for new apps); setTimeouts "defaults unbounded" false
(only resolveTimeout is infinite; 60/30/30 for the rest); Graph per-site roles are
read/write/manage/fullcontrol (not "owner"); delegated Sites.Selected does NOT need admin
consent; MacroOptions reuses an existing Category rather than throwing; add-in procedures
are reference-free only for UDFs/Application.Run, not cross-project VBA calls.

**18 experience-settled labels** — kept and labeled, never deleted or laundered, per the
skill's "omission means unconfirmed, not unsupported" rule. Biggest: the Graph `Prefer:
HonorNonIndexedQueries...` header asserted as required in 5 places but absent from the
official reference; HtmlText's strip list (documented for a DIFFERENT control); the
.frm/.frx export pair (never named on current Learn); DAX "Power Query columns compress
better" (community lore Learn argues against — rationale replaced).

**1 contested:** SharePoint's ≤20,000-item ceiling for adding/removing an index. The
current support article says M365 allows indexing a list of ANY size; a live Learn
troubleshooting page still states the 20,000 limit. Recorded as drift rather than resolved
— exactly the contract-drift stop the skill prescribes.

Judgments recorded in `skills/claim-grounding/reviews/ledger.jsonl` (27 rows: identity,
verdict, rationale, grounded_by, date). Ledger schema worked as designed; `count` captured
multi-site claims (Prefer header = 5).

**Method notes for next time:** the pre-grounded skip rule fired zero times — nothing in
either family carried dated grounding, which is itself the finding. Verifiers reliably
self-limited to ~15-23 claims each; that granularity felt right. Rubberduck-specific claims
in vba-code-test-writing are out of Learn's scope entirely and need a different source.

## Addendum 3 — verify-claims pass 2 (VSTO, coding-standards, Python, quant)

10 more verifiers in two batches of five (smaller batches after pass 1's session-limit
deaths). Totals across both passes: **21 verifiers, ~390 claims, 22 skills, 63 ledger rows
(40 corrected, 22 experience-settled, 1 contested).**

**VSTO was by far the worst family: 22 errors.** The LoadBehavior registry table was wrong
in TWO files and differently wrong in each — `2` called load-on-demand when it is the
post-failure error state, `0` called a crash symptom when it is a deliberate setting, `9`
and `16` both mislabeled. Anyone debugging a failed load would read the registry backwards.
Also: the WiX Manifest value was missing the required `file:///` prefix (an MSI from that
template would not load), the mage.exe signing order was inverted, `|vstolocal` appeared on
a ClickOnce URL where it opts out of the very cache being described, and GPO
computer-assigned packages were said to install at logon rather than startup.

**The highest-yield finding class across the whole exercise: review skills teaching
inverted rules.** Three independent instances —
- VSTO-review flagged `FinalReleaseComObject` as high-severity; Microsoft's warning is about
  `ReleaseComObject`, and it recommends FinalRelease for deterministic release.
- python-review's late-binding example (`lambda i: i`) was the documented FIX, not the bug —
  its parameter shadows the loop variable. The real bug is the parameterless `lambda: i`.
- financial-timeseries told readers to hunt look-ahead leakage in `ewm`, which has no
  `center` parameter and is provably causal (verified by perturbation).
Each one would make a reviewer flag correct code and miss the actual defect. Worth a
standing rule: **when a skill teaches "spot X", verify the example IS X.**

**Second class: freshness decay, not authoring error.** The Semi-Annual Enterprise Channel
advice was true when written; the July 2026 (2606) release unified SAEC into Monthly
Enterprise, so it silently stopped working. Different failure mode, different fix (a
dated caveat rather than a correction).

**Method notes:**
- Empirical grounding beat citation-hunting on Python/quant — catastrophic cancellation vs
  np.var's two-pass implementation, `freq="B"` including July 4th, ewm causality by
  perturbation, sqrt-of-time by simulation. For runtime behaviour, run it.
- Standards/review skills are ~80% judgment by design; verifiers correctly extracted only
  the checkable minority. That ratio is healthy, not a defect.
- Egress: docs.python.org, peps.python.org, docs.pydantic.dev, numpy.org,
  pandas.pydata.org and docs.scipy.org are ALL blocked by the proxy. Only
  learn.microsoft.com and raw.githubusercontent.com are reliably reachable. The OSS
  template now says so.
- Two skills came back with ZERO errors: coding-standards (21/22 confirmed) and
  backtesting-validation + quant-code-review. Both are heavily judgment-based, which is
  itself the pattern: the more falsifiable a skill, the more it decays.

## Addendum 4 — the agent-authoring verifying-agent rule (the last open item)

Codified the defect that shipped twice: `agent-authoring` now has a dedicated subsection
("If the agent VERIFIES, `plan` is the wrong posture") plus a checklist line and an
anti-pattern entry.

Deliberate framing choice: the rule argues from the **mandate**, not from harness
mechanics. I did not assert what plan mode blocks at the tool level — that is a falsifiable
claim about a moving target, and this session was largely about not making those. The
tension holds regardless: `plan` exists to propose rather than act, an auditor's value is
running the check and citing output, and combining them yields a verdict inferred rather
than proven. Stated that way the rule survives harness changes and needs no dated caveat.

Prescribed shape: `default` + `Read, Grep, Glob, Bash`. Read-only behaviour comes from
OMITTING Edit/Write, not from `plan` — you keep non-mutating while staying able to prove
what you claim.

Conformance swept across all 12 example-project agents: **clean.** The three `plan` agents
are genuine propose-only design agents (data-analyst, presentation-architect,
software-architect) with zero verify-signals; both original offenders were already fixed in
review. So this codifies a fix rather than exposing new violations — which is the point of
promoting a twice-seen defect into an authoring rule.

## Addendum 5 — light sweep of presentation/docs (pass 3, completes the gate)

4 verifiers over 10 skills, grouped by where checkable content plausibly lived rather than
one-per-file. Brief said explicitly: **an empty array is a success, don't grade opinions,
name what you skipped.** That instruction did real work — two groups returned near-zero and
said so cleanly instead of padding.

**~23 claims, 3 errors.** Thin, as predicted from the pass-2 observation that the most
judgment-heavy skills return zero.

- `report-builder` had Word's broken-cross-reference string as "Error! Reference not found";
  the real string is **"Error! Reference source not found."** Severity is higher than its
  size: it sat in a VERIFY step, so an agent grepping the literal would match nothing in a
  genuinely broken document and report it clean. Third variant of the session's recurring
  theme — a verification step that cannot verify. Added "Error! Bookmark not defined." too.
- `brochure-builder` listed the LaTeX `ticket` class as a brochure tool. It makes visiting
  cards/labels/stickers and is a package, not a class. `leaflet` (also listed) is correct
  and genuinely does two-fold imposition, so the row now names it alone.
- `technical-documentation-drafter` said GitHub surfaces CONTRIBUTING.md "in PR templates" —
  it links on the PR-creation page, a different feature from PULL_REQUEST_TEMPLATE.md.

**Print geometry was the one place I guessed right.** Fold arithmetic verified by
computation, not citation: US Letter tri-fold 3.6875+3.6875+3.625=11.000in exactly (tuck
panel 1.59mm narrower — inside the 1/16-1/8in trade range the skill's "~2-3mm" brackets);
A4 gate-fold 74.25+148.5+74.25=297.0; Z-fold 297/3=99.0 equal; saddle-stitch pages=4x
sheets; spine pairs sum to n+1. All sound.

**Three predictions wrong, worth remembering.** I seeded the brief with WCAG contrast
ratios, python-pptx/python-docx APIs, and Diatraxis as likely targets. None exist anywhere
in these families: branding/presentation-design reference contrast only as an instruction
to CHECK (never a threshold), the builders name libraries only as tools to PICK (no
signatures), and neither drafter uses Diataxis at all. In judgment-heavy families the
falsifiable surface is thinner AND differently placed than it looks from outside — guess
the location badly and a sweep finds nothing while looking thorough.

**Zero-yield coverage rows added to the ledger** for branding/presentation-design and the
verified fold geometry. Without them a future pass cannot distinguish "examined and
genuinely empty" from "never looked at" — the same absence-means-unreviewed logic the
ledger schema already applies to findings.

**Observation, not acted on:** `branding` tells the reader to verify contrast but never says
what passes. That is a content GAP, and filling it means ADDING claims — out of scope for a
verification pass. Flagged for a human decision rather than fixed unilaterally.

---

## Addendum 6 — VBA family gap: two new skills, gated at authoring

**The probe, not the intuition.** Asked whether the VBA family had gaps, I grepped all 7
VBA skills plus the global `vba-developer` for the obvious Excel surfaces. **Zero hits** for
`ListObject`/Tables, PivotTables, Charts, `.Formula`/R1C1, ADO/DAO/`Recordset`/SQL, and
Regex. `vba-development`'s whole host coverage was **four bullets** for Excel+Word+Outlook+
PowerPoint combined, against a description promising "Office object-model automation across
Excel, Word, Outlook, and PowerPoint" — a promise/delivery mismatch at the coverage level,
which is a different defect class from a wrong claim and is only visible by measuring the
description against the body.

**Built (user chose 2 of 4 candidates, and chose to gate them):**
- **`vba-excel-object-model`** — Tables/`ListObject`, PivotTables, charts, `.Formula` vs
  `.Formula2` vs R1C1, `.Value2`/`.Value`/`.Text`, `UsedRange`/`End(xlUp)`/`SpecialCells`/
  `AutoFilter`. Defers the Range⇄array round-trip to `vba-development` rather than restating.
- **`vba-data-access`** — ADO/DAO, connection strings, cursors/locks, `CopyFromRecordset`,
  transactions. **Rule zero: never concatenate values into SQL** — the family said nothing
  about it, and it's the standard VBA data defect.

Both carry explicit `Boundaries:` lines (the VBA family had none — the Power Platform family
does; this closes that inconsistency). Cross-links added into `vba-development` (two
pointers) and `vba-review` (data-access safety inserted as priority **3**, above performance,
because it is a correctness bug and a security bug simultaneously).

### The truth gate found real defects — in my own draft, before shipping

Running `verify-claims` at authoring time (rather than after) caught three things that would
have shipped:

1. **A feature-detect that cannot detect.** My `Formula2` support probe was both nonsense
   (`Application.WorksheetFunction.Parent.Range("A1")`) and *early-bound* — naming
   `.Formula2` anywhere makes the project fail to **compile** on an older Excel, so the
   fallback path can never run. Fixed with an `Object`-typed late-bound probe **and** a
   late-bound write. This is the fourth-plus instance of the session's highest-yield class:
   **verification steps that cannot verify.** It now has a sibling: *a compatibility fallback
   that the compiler kills before it executes.*
2. **An incomplete connection string.** `Provider=MSOLEDBSQL;…SSPI` omits
   `DataTypeCompatibility=80`, which Microsoft states ADO *requires* for the OLE DB Driver.
   Classic works-in-the-UDL-tester/fails-in-VBA. Added, plus the v19 `Use Encryption for
   Data=Mandatory` default.
3. **Missing preconditions on `ListObject.Resize`** — header must stay in the same row, new
   range must overlap the original, and the result needs a header **and ≥1 data row**, so a
   table cannot be resized to zero rows. No cells are inserted, so content below is
   overwritten, not pushed down.

**Contract drift reported, not resolved.** Two Microsoft pages disagree on `RecordCount` for
an *empty* forward-only recordset (`-1` per the property reference; `0` per "Limits of a
Recordset"). Per `verify-claims`' stop condition I did not pick the convenient source — I
recorded the conflict and noted that the skill's actual advice (`rs.EOF And rs.BOF`) is
correct under either reading, which is the argument for using it.

**Three claims labelled experience-settled rather than deleted or laundered:**
`SpecialCells` raising 1004 on no match, the PivotTable data-field rename collision, and
`UsedRange` over-reporting. All three are true in practice and absent from the references.

**Honest gap (recorded as a ledger row, not omitted):** step 4 of `verify-claims` —
grounding against a *live* authority — could not run. There is no Windows/Office host here.
Everything in both skills is doc-settled or explicitly labelled; **nothing was confirmed by
executing VBA.** The three experience-settled rows are precisely what a live probe would
settle.

Ledger: **69 → 78 rows** (3 corrected, 1 confirmed-before-shipping, 1 contested, 4
experience-settled incl. the coverage gap).
