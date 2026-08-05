# control-grounding

Ground an unknown control, property or enum token **before** you type it, then propagate the
grounding so it never has to be re-derived. Run this the moment you want a token you cannot
cite evidence for — it is always cheaper than a failed paste, which returns across the one-way
gap as nothing but "it didn't work". A token grounded once must never need grounding twice.

**Inputs:** an uncertain `Control:` / `Variant:` / enum member / output-property token needed
for an authored change.
**Output:** either the token grounded with its provenance and recorded in every catalogue
surface, or a **grounded fallback** built from proven tokens with the open question noted in
the file header.

## Steps

1. **Check the catalogue first.** Look the token up in `powerapp-canvas-controls`, then in
   `tools/studio-enums.json` and the validator's allow-list. Already grounded → **stop, done**;
   don't re-derive what a previous session settled. → hand-off: the token, or a confirmed gap.

2. **Walk the evidence ladder.** Apply the **`powerapp-canvas-controls`** skill — it owns the
   ordered, costed ladder (an `.msapp` in the repo is a zip: `References/Templates.json` holds
   the enum tables; then a human-supplied code-view sample; then MS Learn for output properties
   and enum semantics). Do not restate the technique here; the skill is the source of truth.
   Note that Studio prints only NON-DEFAULT properties, so a sample request must say which
   property to change first. → hand-off: a grounded token + its provenance, or exhaustion.

3. **Ship a fallback if it stays unknown.** Build the thing from proven tokens (three
   Rectangles instead of an unverified icon) and note in the file header what the nicer version
   would be, so it can be swapped once grounded. **Never author a guess.** → hand-off: a
   paste-safe construct plus a recorded open question.

4. **Record it in all four places, once.** The propagation is the point of the workflow:
   - the validator's allow-list, with a dated comment — **the only copy that gates a paste**;
   - `tools/studio-enums.json` — the token, its properties, its OUTPUT property, the Studio
     defaults seen in the sample, and its provenance;
   - `powerapp-canvas-controls`' grounded-token list, output-property table, and a short YAML
     example when the wiring isn't obvious — **a skill is how the next session finds this**; a
     token that lives only in the allow-list is grounding nobody will look for;
   - `paste-log.md` (the crossing) and, via **`session-memory`**, the decision if it corrects a
     previous belief.

5. **Verify the propagation.** Run `python tools/validate_pa_yaml.py` — it audits the copies
   against each other and flags any allow-listed token missing from the enums file or the
   skill. A warning there means step 4 is unfinished. → hand-off: a clean cross-check.

6. **Check downstream.** If the newly grounded control writes to the backing list, decide
   whether the COLUMN must change too (a rich-text editor emits markup; a toggle cannot produce
   `Blank()`, so a Yes/No column can never mean "unanswered"). That decision belongs to
   **`sharepoint-list-architecture`** — route it there, don't settle it here. → done.

## Control flow / stop conditions

- **Short-circuit:** step 1 finds the token already catalogued → **done immediately**.
- **Loop (the ladder):** step 2 repeats one rung at a time, cheapest first. Terminal state:
  grounded with provenance → step 4; all rungs exhausted → step 3 (fallback). Never a guess.
- **Gate (human at Studio):** a code-view sample is a request across the one-way gap, not a
  pull. Ask for it, keep descending the ladder meanwhile, and never block the change on it —
  the fallback in step 3 is the escape.
- **Bail:** the token cannot be grounded *and* no fallback can be built from proven tokens →
  **stop** and surface the uncertainty; do not hand a human a paste that rests on a guess.
- **Success:** the token (or its fallback) is in use, and step 5's cross-check is clean → done;
  report the token, its provenance, and where it was recorded.
- **Incomplete:** grounded but not propagated (step 5 warns) → not done; finish step 4 first.

## Invokes
- Skills: `powerapp-canvas-controls` (the evidence ladder and the catalogue it owns),
  `studio-transfer` (paste-dialect shape), `sharepoint-list-architecture` (step 6),
  `session-memory` (the decision record).
- Workflows: called by `screen-build` (step 2) and `change-end-to-end` (step 1).
- State: `tools/studio-enums.json`, the validator allow-list, `paste-log.md`,
  `.claude/memory/INDEX.md`.
- Tools: `python tools/validate_pa_yaml.py` (cross-checks the catalogue copies).
