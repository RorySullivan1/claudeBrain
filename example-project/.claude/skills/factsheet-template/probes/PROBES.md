# Probe kit — factsheet-template

| Artifact | Role |
|---|---|
| `sample-context.json` | A complete, contract-valid context for a fictional volatility-carry index. The worked example, and the regression fixture. |
| `sample-performance.svg` | matplotlib chart at `figsize=(7.087, 2.56)` inches — 180mm wide, matching the text column exactly, with `svg.fonttype='path'` so its text is outlines. |

## Run log — 2026-09-15, WeasyPrint 69.0, Jinja2 3.1.6, matplotlib 3.11.2

**Contract gate, with discrimination proved on four bad contexts.** The valid sample passes
with 0 errors and 4 warnings (3 `PLACEHOLDER` blocks + absent optional logo), exit 1. Each
deliberate defect was caught with a specific message and exit 2:

| Injected defect | Caught as |
|---|---|
| `as_of_date` removed | required field missing |
| `as_of_date` set to 2027-12-31 | in the future — the figures cannot exist |
| `period` set to `"last month"` | not one of the closed period list |
| `return_pct` given as `"+2.41%"` | must be a number; formatting is the template's job |
| disclaimer prose in `disclaimer_blocks` | looks like prose, not a filename |
| `disclaimer_text` authored by hand | derived field must not be authored |

**Full pipeline.** Staged render directory → Jinja2 with `StrictUndefined` and
`autoescape=True` → lint **clean, exit 0** → render **2 pages**. Page 1 carried the masthead,
Strategy, Key facts, the chart, Period returns and Risk statistics; page 2 carried Methodology,
Composition, Notes and Important information. The running footer appeared on **both** pages
with the audience label, the identifier and "Page N of 2".

**The font slot behaves as designed.** With `fonts/` empty the render reported exactly four
warnings — one per `@font-face` — in the `fonts` bucket at exit 1. Loud, not silent.

**One QA iteration was needed, and it found a real layout defect.** The first render produced
**3** pages: page 1 overflowed by the risk table, which took a page of its own and pushed
Methodology to page 3. Fixed by pairing returns and risk in a two-column row; re-rendered at 2
pages. This is the loop working as specified, and it is why `layout-spec.md` records the
side-by-side arrangement as a necessity rather than a preference.

**Two linter false positives surfaced here, not in the fixtures.** Linting the real factsheet
reported E003 (no `@page`) and W004 (`var(--family-display)` has no face) on a correct
template. The linter was following `<link rel="stylesheet">` but not `@import`, and reading a
`var()` reference as a family name. Both fixed at source in
`../weasyprint-print-html/scripts/lint_print_html.py`, and the engine's three controls
re-verified afterwards.

## Not verified

`snapshot.py` was never run against this PDF: poppler is a system binary and was unavailable
in the build sandbox, so **no page image of this factsheet has been looked at.** Page count,
section distribution and footer text were read from the PDF's text layer instead. Run
`snapshot.py --check-tools`, then a real snapshot, on the first factsheet in the target
environment and record it here — the layout is *plausible*, not *seen*.
