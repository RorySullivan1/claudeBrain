# screen-build

Build or rebuild one screen end to end: ground the data, ground the controls, plan the layout,
author, check geometry, validate, audit, hand off for the paste, and record what landed. The
order is the value — **each step's output is the next step's input**, and skipping the early
ones is how you discover a wrong column name *after* the paste.

**Inputs:** a screen to build or rebuild and the behaviour it must support.
**Output:** authored, geometry-checked, validated, PASTE-audited screen source in
`src/authored/`, plus a hand-off note; a `paste-log.md` row once the human reports the outcome.

## Steps

1. **Ground the data (schema first).** Every column the screen reads or writes must resolve to
   a `name:` in `schema/schema.yaml`. Missing column → change the golden source *first* via
   **`sharepoint-list-architecture`**, and note whether the list needs re-provisioning. Check
   `multi:` on any Person / Managed Metadata column you touch — wrong arity breaks the read
   *and* the write. → hand-off: a resolved column list.

2. **Ground the controls.** List the control types the screen needs and check each against
   **`powerapp-canvas-controls`** / `tools/studio-enums.json`. Anything ungrounded → run the
   **`control-grounding`** workflow; **do not guess.** Prefer controls that remove hand-parsing
   (date picker, number input, combobox). → hand-off: a grounded token list.

3. **Plan the layout in bands.** Apply **`powerapp-canvas-design`**: resolve the band table and
   write it into the screen's header comment; decide absolute vs auto-layout container
   (container wins whenever content stacks — its children can't have positions frozen on
   paste); fixed furniture (header, action bar) stays absolute and OPAQUE. → hand-off: the band
   table + container decisions.

4. **Author.** Column tokens from step 1, control tokens from step 2. Apply
   **`powerapp-canvas-development`** (file structure) and **`power-fx-development`**
   (formulas), or delegate the whole build to **`../agents/powerapp-canvas-developer.md`**.
   Overlays and modals declared LAST; gallery rows get a transparent full-template hit button;
   multi-line and `: `-bearing formulas as block scalars. → hand-off: source in `src/authored/`.

5. **Check geometry.** Pairwise rectangle intersection over every control on the screen and
   inside every modal, per `powerapp-canvas-design`. Intentional overlaps only, and
   one-directional. → hand-off: a collision-free screen.

6. **Validate.** `python tools/validate_pa_yaml.py` — schema, tokens, icons, `IfError` typing,
   gallery `OnSelect`, cross-file component contracts, positioning-off-another-control. A new
   failure class earns a new lint **in the same change**. → hand-off: a green validator.

7. **Audit.** Spawn **`../agents/pre-paste-review.md`** for a **PASTE / DO-NOT-PASTE** verdict.
   → hand-off: the verdict.

8. **Hand off (human gate).** Per **`studio-transfer`**: update `BUILD-BOOK.md` with anything
   the human must type by hand in Studio, then state the paste order, the inferred tokens and
   their fallbacks, and what to report back. **STOP here** — you cannot paste; the gap is
   one-way (`../context/air-gap.md`). → hand-off: the human's outcome report.

9. **Record.** Write the `paste-log.md` row when the outcome comes back (target screen,
   intended name, Studio suffix, outcome), and log a decision via **`session-memory`** if it
   settles something. → done.

## Control flow / stop conditions

- **Ordering is a precondition, not a preference.** Don't start step N until step N−1's
  hand-off exists; a control grounded after authoring is a rebuild, not a fix.
- **Branch (step 1):** a column is missing → amend `schema/schema.yaml` and flag
  re-provisioning before any authoring; else → step 2.
- **Branch (step 2):** a token is ungrounded → `control-grounding`; terminal state is a
  grounded token or a proven-token fallback. Only then → step 3.
- **Loop (validate/audit):** step 6 red or step 7 **DO-NOT-PASTE** → back to step 4 with the
  findings; re-run 5–7. Terminal state: validator green **and** a PASTE verdict. Two passes
  with no progress → **stop and report** the blocker.
- **Gate (paste):** step 8 is a human action across the one-way gap. The workflow pauses; never
  claim the screen is live before the human confirms it validated, and never hand over source
  that hasn't passed step 7.
- **Success:** the screen validated in Studio, controls renamed off their `_1` suffixes, and
  the crossing recorded in `paste-log.md` → done; report what landed.
- **Partial:** authored + PASTE verdict but not yet pasted → report as *authored, not landed*.

## Invokes
- Skills: `sharepoint-list-architecture` (step 1), `powerapp-canvas-controls` (step 2),
  `powerapp-canvas-design` (steps 3, 5), `powerapp-canvas-development` +
  `power-fx-development` (step 4), `power-apps-components` (when the screen consumes a
  component), `studio-transfer` (step 8), `session-memory` (step 9).
- Agents: `../agents/powerapp-canvas-developer.md` (step 4),
  `../agents/pre-paste-review.md` (step 7).
- Workflows: `control-grounding` (step 2); `change-end-to-end` is the smaller single-change
  sibling of this pipeline.
- Context: `../context/air-gap.md` (why step 8 is a gate).
- State / tools: `schema/schema.yaml`, `tools/validate_pa_yaml.py`, `BUILD-BOOK.md`,
  `paste-log.md`.
