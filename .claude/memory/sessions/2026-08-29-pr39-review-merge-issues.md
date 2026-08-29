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
