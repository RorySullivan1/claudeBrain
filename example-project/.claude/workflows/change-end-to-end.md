# change-end-to-end

Take one canvas-app change from intent to landed-in-Studio across the clipboard air gap,
safely: ground what you can't cite, author, audit, choose the transfer mechanism, hand off to a
human for the paste, and record what landed. Use it for "take this change through to Studio",
"author and paste this", or any question about how a change gets from the repo into the live
app. The orchestration is the value — the work lives in the skills and agents it invokes.

**Inputs:** a described change to the app. (No "current baseline" precondition — the gap is
**one-way** per `../context/air-gap.md`, the repo *is* the source; there is nothing to be stale
against.)
**Output:** an authored, audited change either **landed** in Studio and recorded in the paste
log, or **stopped** before a wasted paste — with the reason and the next step.

## Steps

1. **Ground the paste, don't confirm freshness.** There is no pull and no baseline to check —
   the repo is authoritative. Instead, resolve any uncertain paste token, `Variant:` or dialect
   detail before you type it — run the **`control-grounding`** workflow, which resolves from
   public evidence or ships a grounded fallback per `powerapp-canvas-controls` and
   `studio-transfer`. Grounding first is always cheaper than a failed paste. → hand-off: a
   paste approach you can defend without a return sample.

2. **Author the change.** Apply the **`power-fx-development`** skill to write the formulas and
   the **`studio-transfer`** skill for the paste-dialect shape; put control YAML in
   `src/authored/` and any App-object body in `src/patches/`. Bind every column to an internal
   name that resolves in `schema/schema.yaml` (the golden source) — never invent one. For a
   substantial build, delegate to **`../agents/powerapp-canvas-developer.md`** instead of
   authoring inline. → hand-off: authored files.

3. **Audit before paste.** Spawn the **`../agents/pre-paste-review.md`** agent on the authored
   files. It returns findings + a **PASTE / DO-NOT-PASTE** verdict (schema + delegation +
   paste-shape + grounding). → hand-off: the verdict.

4. **Choose the transfer mechanism.** Per `studio-transfer`: control(s) → **code view**
   (paste creates a new control, validated); App-object code (`App.OnStart`/`App.Formulas`/
   named formulas) → **formula bar only** (no App code view). Keep each unit small enough that
   a rejection localizes. → hand-off: a paste plan (which unit, which channel, target screen).

5. **Hand off for paste (human gate).** Present the audited YAML and the paste plan to the
   human to paste into Studio. This is the air gap — you cannot paste. Ask them to confirm it
   validated, then **rename** the suffixed control (`_1`) to its intended name. → hand-off:
   the landed name + Studio's suffix + outcome.

6. **Record.** Append the crossing to `paste-log.md` (date, target screen, intended name,
   Studio suffix, outcome). If the change carried a decision worth keeping, log it via
   **`session-memory`**. → done.

## Control flow / stop conditions

- **Bail (unverifiable token):** step 1 can't ground a paste token and has no safe fallback →
  **stop**; surface the uncertainty rather than shipping a blind guess a failed paste can't
  diagnose. (There is no pull to request — the gap is one-way.)
- **Loop (audit):** step 3 returns **DO-NOT-PASTE** → return to step 2 with the agent's fixes;
  re-audit. Repeat until PASTE. Never hand a human a paste that hasn't passed. Terminal state:
  a PASTE verdict (or the human explicitly overrides, recorded).
- **Gate (paste):** step 5 is a human action across the air gap — the workflow **pauses** for
  it and does not proceed until the human confirms the outcome. Never claim a change is live
  before the human confirms it validated.
- **Success:** the change validated in Studio, was renamed, and is recorded in `paste-log.md` →
  done; report what landed and under what name.
- **Partial:** authored + audited PASTE but not yet pasted (human unavailable) → stop and
  report it as *authored, not landed*; it is **not** in the app until step 5 completes.

## Invokes
- Skills: `studio-transfer`, `power-fx-development` (+ `power-fx-review` when reviewing an
  existing formula), `powerapp-canvas-controls` (token grounding),
  `sharepoint-list-architecture` (when the change needs a schema decision), `session-memory`.
- Agents: `../agents/pre-paste-review.md`, `../agents/powerapp-canvas-developer.md`.
- Workflows: `control-grounding` (step 1), `screen-build` (when the unit is a whole screen).
- Context: `../context/air-gap.md` (the one-way transfer model).
- State: `schema/schema.yaml` (golden source for column names), `paste-log.md` (what landed).
