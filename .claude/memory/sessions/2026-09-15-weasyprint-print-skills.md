# 2026-09-15 · weasyprint-print-skills

**Goal:** Build the WeasyPrint print-HTML skill + factsheet-template skill from the build
brief; defer the `print-qa` subagent to phase 2.

## What happened

Built both skills into `example-project/.claude/skills/`. Phase 2's `print-qa` subagent was
**not** built — the brief gates it on the QA loop actually crowding main-session context, and
that has not happened yet.

Three of the brief's open questions were confirmed with the user before writing CSS: **A4
default with a Letter override**, **`fonts/` ships empty with a fallback stack** (no
unlicensed font in the repo), and **full factsheet skill with placeholder compliance copy
only** (safe to keep here; real copy and faces go to the internal repo).

The build sandbox turned out to be far more capable than expected, which changed the quality
of the work: **WeasyPrint 69.0 installs from PyPI wheels with no system libraries**, so the
whole write → lint → render loop ran for real instead of being reasoned about. matplotlib and
jinja2 installed too, so the factsheet rendered end to end from a real SVG chart. Only poppler
was unavailable — it is a system binary — so `snapshot.py` is the one surface never exercised.

Ledger 91 → 96. Five surface rows added to `context/verification-surface.md`.

## Gotchas & dead ends

Everything below was found by **running** something. None of it was visible from reading.

- **`FatalURLFetchingError` subclasses `BaseException`, not `Exception`.** The worker's
  `except Exception` therefore could not catch the one error `--fail-on-fetch-error` exists to
  raise: it died with a traceback, empty stdout, and `render.py` reported "unknown error".
  Same defect family as the repo's durable lesson — the handler for the gate couldn't handle
  the gate.
- **`--strict-fetch` alone is not a gate.** It contains the fetch, but WeasyPrint logs the
  refusal and finishes, so the default outcome of the security flag is a PDF quietly missing an
  asset. For a factsheet that is shipping without a logo. Hence the separate hard-fail flag.
- **`base_url` does double duty** — relative-path root *and* strict-fetch root. Widening it to
  reach a sibling `assets/` dir breaks the template's own paths, so a sandboxable bundle must
  be self-contained under one directory. Learned by trying the obvious fix and watching the
  stylesheet 404.
- **The linter's `@page` check was satisfiable by a comment.** The negative-control fixture's
  own header comment said "@page" and silenced E003. Comment bodies are now blanked (newlines
  preserved) before every check.
- **The linter had two false positives that only a real template exposed**: it followed
  `<link rel=stylesheet>` but not `@import` (so E003 — an *error* — fired on a correct
  factsheet whose `@page` was in the imported base sheet), and it read
  `font-family: var(--family-display)` as a family name. The fixtures never caught either.
- **`transform` is supported; `aspect-ratio` is not.** The first draft of the unsupported list
  had this backwards for `transform`, which would have cost design range for nothing. Measured
  all 33 properties instead: there are **three** outcomes, not two — supported, *dropped*
  (parser rejects, logs "unknown property"), and *inert* (parses, logs nothing, does nothing).
  `animation`/`transition`/`will-change`/`scroll-behavior` are inert, so they became a separate
  lint rule (W007); one rule covering both groups described the second wrongly.
- **The factsheet's first render was 3 pages, not 2.** Page 1 overflowed by the risk table,
  which took a page of its own and pushed Methodology to page 3. Fixed in one iteration by
  pairing returns and risk side by side — recorded in `layout-spec.md` as a necessity rather
  than a preference, so nobody "tidies" it back.
- **`@page { size: var(--page-size) }` does not work.** WeasyPrint resolves `@page` descriptors
  before custom properties, so the A4/Letter switch restates `size` while the mm variables
  carry the rest.

## State at end

Both skills complete and probed. Engine: 4 scripts, `print-base.css`, 3 references, 3 fixtures
+ a drift probe, DECISIONS.md, PROBES.md. Factsheet: Jinja2 layout, brand CSS, empty fonts slot,
placeholder compliance, contract validator (`--print-contract` is the authoritative field list),
2 references, sample context + chart, DECISIONS.md, PROBES.md. `asset_integrity` clean in both
trees; CATALOG regenerated; `memory.py check` within budget after relocating four older
decisions to ARCHIVE-2026.md.

Verified live: 2-page factsheet with the running footer on both pages; lint clean; 6 injected
contract defects each caught; 33-row CSS table with both controls passing and no drift; repeating
`<thead>` across a 59-row table split 27/32.

## Addendum — 2026-09-16, fixture trimmed after review

The user challenged the sample: these are assets, not a product. Correct on the part that
mattered. The linter's controls (3.8KB of fixtures) are instruments and match the repo's
existing probe-kit convention, but the factsheet sample had drifted into a *product sample* —
a 58KB matplotlib render plus realistic invented returns ("+61.40% since inception", "Sharpe
1.12") inside a compliance-sensitive template bound for an internal repo. That is the hazard
the compliance placeholders exist to prevent, arriving through the numbers instead.

Trimmed rather than deleted: the chart is now a 1.6KB shapes-only stand-in with the **same
footprint** (510×184pt = 180mm×65mm), so pagination is still regression-tested against real
geometry; figures are round (1/2/5/10/20/50); identity is "Example Systematic Index"; and a
new `_sample` marker makes the validator always say the data is synthetic. Re-verified: lint
clean, 2 pages, same section split, footer on both pages, all engine controls unchanged.
Factsheet bundle 172K → 120K.

**The generalizable lesson is about what gets committed, not what gets built.** The realistic
render earned its keep — it is what exposed the @import/E003 false positive, the `var()` W004
false positive, and the 3-page overflow, none of which the small fixtures caught. A realistic
render is a good scratch artifact and a poor repository fixture.

## Open threads

- **No page image has ever been looked at.** poppler is absent here, so `snapshot.py`'s
  rasterise and live `pdffonts` paths are untested and the factsheet layout is *plausible, not
  seen*. First job in the target environment: `snapshot.py --check-tools`, then a real snapshot,
  then record it in both PROBES.md files.
- Pending from the user: licensed brand font files, approved compliance copy, and the
  internal-repo copy of `factsheet-template` (with its two content directories replaced).
- Still unanswered from the brief's open questions: where Claude Code will run these (affects
  whether `render.py` needs `$WEASYPRINT_PYTHON` set), and the page-1 section order for the
  first *real* factsheet — the current order is the brief's proposal, verified only against the
  fictional sample.
- `print-qa` subagent: build when the QA loop crowds context, not before.
