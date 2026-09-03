# Live-host probes — vba-excel-object-model (issue #43)

> **Run log — 2026-09-02, Excel 16.0 (Windows 64-bit NT 10.00) / Microsoft 365.**
> Driven via Excel COM automation (module imported, `RunAllProbes` executed; output sink
> redirected from the Immediate window to a file, probe logic otherwise verbatim). Both
> controls PASSed. Results: `SpecialCells`-no-match **CONFIRMED** (raised 1004 "No cells
> were found."); pivot data-field rename collision **CONFIRMED** (raised 1004 "Unable to set
> the Name property of the PivotField class"; non-colliding rename succeeded); UsedRange
> "doesn't shrink after clear" **REFUTED** — it shrank after `.Clear` *and* `.ClearContents`,
> in-session and across save/reopen; the real over-report driver is residual formatting.
> Skill labels promoted/corrected; ledger rows updated (2026-09-02). See issue #43.


Three claims in `../SKILL.md` are labelled **experience-settled**: consistently observed in
the field, absent from the Microsoft references the skill cites. Only a run on a real
Excel/Windows host can promote or refute them. This folder is that run, packaged.

| Claim (as labelled in the skill) | Probe |
|---|---|
| `SpecialCells` raises 1004 on no match, not an empty range | `ProbeSpecialCellsNoMatch` |
| Renaming a pivot data field to the source field's name raises | `ProbePivotDataFieldRename` |
| `UsedRange` doesn't reliably shrink after cells are cleared | `ProbeUsedRangeAfterClear` |

## Running it (~2 minutes)

1. Open Excel on Windows with a **new, throwaway workbook**. The probes add and delete
   worksheets and build a small pivot; nothing touches other workbooks or files.
2. Alt+F11 → File → Import File… → `probe_claims.bas` (or paste into a new standard
   module). Macros must be enabled (a blank unsaved workbook is fine).
3. Open the Immediate window (Ctrl+G), click inside `RunAllProbes`, press **F5**.
4. Copy the entire Immediate-window block into issue #43, verbatim — including the
   header line with the Excel version. Do the optional `UsedRange` stage 2 (save,
   reopen, re-check) if you have another minute.

## Reading the output — the rules that make it evidence

- **Controls run first and gate everything.** `CONTROL positive` proves the API finds
  what genuinely exists; `CONTROL negative` proves the error-capture pattern captures a
  real error. If either says FAIL, the run prints STOP-THE-LINE and the probe lines are
  **not evidence** — report the control failure itself.
- The pivot probe carries its own inner control: a *non-colliding* rename must succeed
  before the colliding one means anything.
- Verdict words are deliberate: `CONFIRMED` / `REFUTED` / `PARTIAL` / `UNEXPECTED` /
  `INFRASTRUCTURE`. An UNEXPECTED or INFRASTRUCTURE line is a finding about the probe or
  the host, not about the claim.

## After the run — closing the loop

Per the `claim-grounding` skill (deliberate promotion, never silent):

- **CONFIRMED** → upgrade the claim's label in `../SKILL.md` from *field-settled* to
  probe-confirmed with the Excel version and date, and add a ledger row
  (`../../claim-grounding/reviews/ledger.jsonl`, shape per
  `../../claim-grounding/references/ledger-schema.md`) with
  `grounded_by: "probe:vba-excel-object-model/probes/probe_claims.bas"`.
- **REFUTED** → fix the claim **at the source** in `../SKILL.md` (the guidance built on
  it may still stand — e.g. the `SpecialCells` guard is worth keeping even if the raise
  doesn't reproduce — but the stated behavior must match the observation), and record
  the refutation as its own ledger row. Never soften the probe to save the claim.
- Either way, replace the standing "no live host" coverage-gap ledger row with one
  recording that the probe ran, on what host, with what results.
