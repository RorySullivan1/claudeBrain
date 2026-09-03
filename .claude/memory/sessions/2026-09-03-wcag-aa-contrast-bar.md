# 2026-09-03 — Issue #44: adopt WCAG AA as the contrast bar

**Request:** "adopt WCAG AA — build out and open a PR." Closes the standing gap where
`branding` told readers to verify contrast but never said what passes.

## Grounded first (the gate applies to ADDED claims too)

Filling this gap means *adding* claims, which is why it was left open in the
verification passes rather than fixed unilaterally. So it went through the authority
before any writing: `curl` reached **w3.org** (a useful egress finding — earlier sessions
mapped most non-Microsoft domains as proxy-blocked; W3C is NOT). Quoted normative text
from **WCAG 2.2, W3C Recommendation 12 December 2024**:
- SC 1.4.3 (AA): 4.5:1 normal text, 3:1 large text; SC 1.4.6 (AAA): 7:1 / 4.5:1
- SC 1.4.11 (AA): 3:1 UI components + graphical objects — **and no AAA counterpart exists**
- large scale = **>=18pt or >=14pt bold** (points are normative; 24px/18.7px is a CSS
  1pt=4/3px derivation, labelled as derived rather than laundered into the standard)
- ratio formula, sRGB relative luminance (incl. the post-May-2021 0.04045 threshold)
- the three exemptions — **logotypes** foremost: a branding skill omitting that would
  send people repainting wordmarks to chase a ratio.

## Built

- **`branding` § Contrast** — the canonical section: the AA/AAA table, the large-text
  definition, the exemptions, and the "record verified pairings as token facts with their
  measured ratios" rule. Where the palette can't reach the bar, the palette changes.
- **`branding/references/contrast.py`** — the bar made COMPUTABLE. `--self-test` carries a
  **boundary control**: `#767676` on white passes AA (4.54) and `#777777` fails (4.48),
  because a wrong luminance curve still gets black/white=21:1 right — extremes alone prove
  nothing. Verdicts never round a near-miss up (WCAG states a minimum). Clean against the
  prose budget at shipped defaults (dogfooding the discipline shipped days earlier).
- **Downstream pointers, not restatements** (skill-wins rule): `presentation-design`
  (+ a projector-washout note: AA is the floor, not the target), `outlook-html-specifications`
  and `outlook-html-designer`. The Outlook pair carries the wrinkle only it can state:
  **you author one palette but ship two renderings, and the dark one is the client's** —
  measuring your source checks half the product; measure the inverted screenshot too.
  Coherence cross-check: the dark-mode pair it already recommended (#1A1A1A on #F5F5F5)
  measures 15.96:1, clearing AA and AAA.

## The integrity hook earned its keep

After the downstream edits, `asset_integrity` flagged that presentation-design and the
Outlook skill "cite `references/contrast.py` but that file does not exist" — the prose said
"its `references/…`" which reads as a *local* sidecar. Genuinely ambiguous for a human
reader too. Fixed by qualifying to `branding/references/contrast.py`. A structural check
catching a real cross-reference defect the semantic pass had missed.

Ledger 84 → 86 (one doc-settled row for the standard, one probe row for the checker).
