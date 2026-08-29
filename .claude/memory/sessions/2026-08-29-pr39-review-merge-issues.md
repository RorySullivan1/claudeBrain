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
