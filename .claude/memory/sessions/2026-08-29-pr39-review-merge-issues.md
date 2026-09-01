# 2026-08-29 — PR #39 review, merge, and the issue backlog

**Request:** review the open PR, assess the code, review the larger codebase, merge, file
additional items as issues. (#38, the Outlook pair, turned out to be already merged; the
open PR was **#39 "Bound the prose the library teaches, and check the bound"** — another
session's port from pyHermes: prose-budget hook + coding-standards scope table +
session-memory BUDGETS/check + knowledge-router code-as-destination + skill-wins rule.)

## Review method and results

Verified mechanically, not just read:
- `build-hooks.py --check` green on both trees (15 fragments example-project / 13 factory —
  factory's subset is intentional, no regen needed).
- **All four quadrants of the prose hook executed**: silent with no `prose-budget.json`;
  fires with one (positive control, 5-line docstring vs `function: 3`); baseline exempts by
  qualified name; exit 0 always. Self-scan against shipped defaults clean. Fragment matches
  house style (`"command": "python"`, all 15 consistent).
- **Confirmed defect**: `memory.py index_findings()` — `line.split()[1]` IndexErrors on a
  bare `## ` header and `index_warning()` catches only OSError → crashes the SessionStart
  hook. The exact fail-safe violation the file's own comment warns against. → #40.
- prose_budget nits (dead `text` var, O(n²) splitlines per token, ordinal-keyed comment
  runs vs the stable-key argument, attribute-key collision across classes) → #40.
- PR-body staleness: "4 wide lines" had grown to **103 lines / 28,403 chars / 39 wide** by
  merge time — the factory INDEX violates every budget the PR ships. Thesis, demonstrated.

Review submitted as a PR comment (GitHub refuses same-account APPROVE), then **merged**
(merge commit 211112d).

## Codebase sweep

Symlinks clean; PR-branch CATALOG fresh; `claude/optimize-factory-model` no longer exists
on origin (PR #8 merged it long ago — memory thread was stale, now closed).

## Issues filed (#40–#44)

- **#40** memory.py fail-safe fix + prose_budget hardening (the review's defects).
- **#41** compact the factory INDEX per the new budgets (State rewrite + ARCHIVE fold).
- **#42** decide: per-stack briefs vs the skill-wins rule (the PR's deliberate open call;
  six briefs, pyHermes' 71%-echo evidence, the measurement method sketched).
- **#43** live Office/Windows host for verify-claims step 4 — enumerates the 8 specific
  experience-settled claims (3 VBA, 5 Outlook) a probe would settle, and what done means.
- **#44** branding contrast bar (WCAG AA/AAA/deliberately-unquantified; ties to the
  Outlook skill's dark-mode "strong contrast" so the two state one number).

**Meta:** the review found the same defect class the gate keeps finding — a verifier that
cannot verify (an advisory whose crash path takes down the hook it advises from). And the
INDEX measurement is a live demonstration of why enforcement beats documentation: the cap
was written in this very file's header the whole time.

---

## Addendum — issues #40 and #41 worked

**#40 (fail-safe + hardening), all in the canonical example-project copies:**
- `memory.py`: `line.split()[1:2] == ["State"]` (bare `## ` header no longer crashes the
  SessionStart hook); `index_warning()` catch widened to `Exception` with a comment saying
  why broad is correct there; `cmd_check` wrapped so its "exit 0 regardless" docstring is
  actually true ("could not be measured; not a verdict" on failure).
- `prose_budget.py`: splitlines hoisted out of the tokenize loop (O(n²) → O(n)) and the dead
  `text` variable removed; comment runs now keyed `{scope}#{sha1(content)[:8]}` via
  `_run_slug` (stable across line moves and neighbouring-run insertion — churns only when
  the comment itself is rewritten; identical runs in one scope share a key, documented as
  acceptable); attribute keys qualified by enclosing scope (`A.limit` ≠ `B.limit`), module
  scope keeps the bare name. hooks/README baseline-key sentence updated.
- Verified by 6 probes: bare-header no-crash + State still counted; cmd_check exit-0;
  comment-run key identical before/after inserting a run above; class-qualified attribute
  keys; module bare-name back-compat; self-scan still clean on shipped defaults.

**#41 (INDEX compaction):** 107 lines / 28,624 chars / State 13 / 38 wide → **43 lines /
5,180 chars / State 8 / 0 wide — `memory.py check`: "INDEX.md is within budget."**
June-era Decisions (29 lines) and Log entries (23 lines) folded VERBATIM into
`sessions/ARCHIVE-2026.md` (extracted mechanically, not retyped) with pointer lines left;
State rewritten to 8 lines that point at CATALOG.md instead of enumerating; DONE/CLOSED
thread markers folded into the archive. Session logs untouched, per the never-rewrite rule.

One process note: the State budget counts PHYSICAL lines, so wrapping wide lines to satisfy
the width cap can push State over its line cap — the fix is condensing, not wrapping. The
first wrap pass produced State=16; the real fix was rewriting to 8 genuinely short lines.

---

## Addendum 2 — issues #42 and #43 worked

**#42 (briefs vs skill-wins) — executed by measurement, not taste.** Four parallel agents
audited each brief line-by-line against its skill family (the pyHermes method):
- **Python: REMOVED.** 99% echoed, 0 unique — worse than pyHermes' 71% copy. Its one
  non-echo was a stale contradiction (blanket "setup.py deprecated" vs the skill's dated
  correction). Nothing survived a trim.
- **VBA: REMOVED after fold.** 90% echoed; the single unique row (private helpers =
  unprefixed camelCase) folded into vba-development's naming table FIRST; its routing map
  omitted vba-addin-building/excel-object-model/data-access — actively misdirecting.
- **VSTO: TRIMMED.** 62% echoed — and the sharp finding: **five lines re-injected
  pre-correction claims the 2026-08-15 truth-gate fixed in the skills** (the
  FinalReleaseComObject inversion among them). Survives: persona, Teaching Mode, Response
  Formatting, Tone, management scraps, stack facts. Everything else → pointer to skills.
- **C/C#: KEPT, lightly trimmed.** 79% unique — the entire C half has no skill family.
  C# standards subsection replaced with 3 unique bullets + a defer that fixes the
  "IDisposable for all resources" error (RCWs aren't IDisposable). C89 default modernized.
- C++ (no skill overlap) and powerapps-docs-source (authority pointer) untouched.

Cross-references swept: vba-developer agent repointed off the dead brief; add-context's
exemplar → the trimmed VSTO brief; context-vs-skill's live example updated to record the
resolution (it now shows the trap AND its ending); CLAUDE.md Reference Docs; manifest.
The applied measurements are recorded in context/README under the rule, and as ledger row
84. **Generalized lesson: a brief restating a truth-gated skill re-injects the
pre-correction claims the gate removed.**

**#43 (live host probe) — advanced to its maximum without a host.** Built the probe kits:
- `vba-excel-object-model/probes/` — `probe_claims.bas` (controls-first: positive +
  negative controls gate the run, stop-the-line on failure; per-claim CONFIRMED/REFUTED/
  UNEXPECTED verdicts printed with the observation; the pivot probe carries its own inner
  negative control) + PROBES.md (run + ledger-recording procedure).
- `outlook-html-specifications/probes/` — a perturbation experiment: probe-a-baseline vs
  probe-b-mitigated, B GENERATED from A (3 deltas, 29 lines, both parse-verified clean),
  so observed differences attribute to specific mitigations. PROBES.md maps each of the 5
  claims to a section and observation.
The issue stays OPEN — the terminal state (claims promoted/refuted) needs a human run on
Windows/classic Outlook; the kit reduces that to ~10 minutes.

---

## Addendum 3 — prose-discipline reach assessment + closing the enforcement gaps

**Request:** assess the restrain-commentary arc (#39→#42) and propose/apply follow-ons.

**Coverage map (measured by grep, not intuition):** the scope table existed only inside
coding-standards — ZERO other assets referenced it. python-review carried the floor
("what-not-why") but no ceiling; VSTO-review floor-only; vba-review and the whole VBA
family said NOTHING about comments; the "emitted output" scope row had no consumer.

**Applied (folds, no new assets):**
1. python-review / VSTO-review / vba-review — one ceiling bullet each pointing at
   coding-standards § *How much, by scope* (DRY: pointer, no restatement) + "route
   displaced reasoning, don't delete it".
2. vba-development — a Comments subsection: VBA has no doc-comment form, so a 1–3 line
   `'` header on each public procedure IS the API doc; inline for traps/why only; no
   banner boxes or change-history headers (git owns history).
3. outlook-html-designer — build rule 10: a shipped email is *emitted output* (comments
   reach every recipient, cost bytes); keep assumptions block + MSO conditionals (code,
   not commentary), strip dev commentary; probes exempt (instruments). Fixed a step-
   numbering collision this introduced (verify steps renumbered 11–14).
4. prose_budget.py — opt-in `claude_md` budget (`{"lines": N, "chars": N}`): CLAUDE.md
   is the OTHER always-loaded prose and had no cap while the memory INDEX now does
   (pyHermes' 2,045-line CLAUDE.md is #39's own motivating evidence). Whole-file caps
   only (scope tables are for code); Finding gained a `unit` field so char findings
   print honestly. 8 probes: silent unadopted / silent without the key / fires with
   units / small file passes / baseline exempts / scan_tree picks up nested CLAUDE.mds /
   Python path regression-clean / self-scan clean. hooks/README documents the key.

**Proposed but deliberately NOT built** (the factory's no-fabrication-until-need rule):
- VBA/C# scanners for `_SCANNERS` — tractable (tokenizers, not regex) but no project
  currently runs the hook over VBA/C#; the silently-skip design is correct until one does.
- A SKILL.md line-counter — rejected on #39's own principle: a number in a cross-project
  standard is wrong for the next repo; skill-authoring already teaches economy by shape
  and skill-creator owns performance evals.
