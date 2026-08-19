---
name: powerapp-canvas-project-management
description: >
  Running a canvas-app project as a repo — source control, provisioning, hand-off discipline
  and the records that make a one-way gap survivable. Use this skill for any question about
  process rather than code: "what's the state of the app", "what's left to build", "how do I
  get the source out of Studio", "pac canvas download", "what's in an .msapp", "update the
  build book", "log this paste", "the lists are provisioned", "what should I do next", "did
  this land". Covers: the golden-source inversion (repo defines, SharePoint applies), the
  authored→landed lifecycle and its records (`docs/build-history.md`,
  `schema/schema.yaml`, `.claude/memory/`), provisioning verification, `.msapp` structure and
  the CLI, and the diagnostic discipline for reports that arrive as one sentence. Boundaries:
  the clipboard mechanics themselves are studio-transfer; formulas are
  powerapp-canvas-development; schema column design is sharepoint-list-architecture; durable
  decisions are session-memory. This skill owns *the project's state and its paper trail*.
---

# Canvas Project Management — the paper trail is the product

Nothing here is bureaucracy. Across a one-way gap, the records ARE the feedback loop: they are
the only thing that distinguishes "authored" from "actually working", and the only defence
against re-deciding something already settled.

---

## The four records, and what each is for

| File | Answers | Rule |
|---|---|---|
| `schema/schema.yaml` | what the backend IS | **Golden source.** The repo defines; SharePoint applies. Never edited to match reality — reality is changed to match it. |
| `docs/build-history.md` | what actually landed | One row per crossing. **Claude maintains it** from chat reports — the human cannot write to this repo. |
| `.claude/memory/INDEX.md` | what was decided and why | Append-only decisions ledger. Committed, because the environment is ephemeral. |

A unit is **authored** until a human pastes it and confirms. `docs/build-history.md` is the only place
that distinction is recorded — if it is not in the log, it is not in the app.

## Provisioning verification

`schema.yaml` defines the lists; nothing reads SharePoint back. So a mismatch is **silent until
a screen errors**. Four things drift, ordered by how loudly they fail:

1. **Arity** — `multi:` on every Person and Managed Metadata column. A multi column returns a
   TABLE: the read errors (`Coalesce(<table>, "")` → *"expecting a Table"*) and the write fails
   too. This has bitten three times.
2. **Internal names**, frozen at creation. A column created as "Project Manager" is internally
   `Project_x0020_Manager` and every token misses.
3. **Choice values**, including case. A `Patch` of an unlisted value fails; a `Filter` on one
   silently returns nothing — the quiet one.
4. **Indexed columns.** No error at all; a delegable `Filter` just becomes a threshold failure
   once the list grows.

## Getting source out of Studio

```powershell
pac canvas list
# EITHER extract the source tree directly (-d already unpacks — do NOT also Expand-Archive):
pac canvas download --name "MyApp" --extract-to-directory "C:\dest"
# OR download the raw .msapp and unzip it yourself (an .msapp IS a zip):
pac canvas download --name "MyApp" --file-name "C:\dest\MyApp.msapp"
Expand-Archive -Path "C:\dest\MyApp.msapp" -DestinationPath "C:\dest"
```
Those are **two alternatives**, not a sequence: `--extract-to-directory` (`-d`) already writes the
`\src` tree, so there is no `.msapp` left to `Expand-Archive`. Use the second pair only when you
want the raw `.msapp` in hand.

Inside: `\src\App.pa.yaml`, `\src\<Screen>.pa.yaml`, `\src\Component\<Name>.pa.yaml`. Only
`\src` is meant for source control; the JSON files are not stable.

**`References/Templates.json` is the hidden prize** — it carries the enum tables as
pipe-delimited runs. That is where the 180-value `Icon` enum came from. Always look there
before declaring a token ungroundable.

**`pac` cannot author component custom properties** (`PA3004`). Component contracts are typed
by hand in Studio; only bodies paste. Plan any component work as three phases: properties →
body → the phase-3 formulas that reference child controls.

## Diagnosing a one-sentence report

The user's whole channel is a sentence. Extract the most from it:

1. **Ask whether Studio was refreshed.** A stale editor reports working code as broken. This
   cost two full rewrites of a working component. It is now the first question, always.
2. **Ask for a photo of code view** when a token or a number is in doubt. A screenshot pinned
   the gallery `Variant`, the container token and the whole modern control set. It carries
   vastly more than "it worked / it didn't".
3. **Compare the numbers.** If they report `Y=193` and the source says 220, they are on a
   stale copy — a much shorter conversation than a debugging session.
4. **When one instance of a repeated formula fails and its siblings do not, suspect the DATA.**
   `gPrManager` and `gPrRequestor` were byte-identical; only the column differed.
5. **Sweep the class the same day.** Fixing only the reported instance leaves the rest to be
   found one painful round trip at a time. One dead gallery meant 24 more were dead.

## Workflow: a change, end to end

1. **Decide** — check `.claude/memory/INDEX.md` first; do not relitigate a settled call.
2. **Schema first** — if the change touches data, edit `schema/schema.yaml` before any app
   code, and note whether SharePoint needs re-provisioning.
3. **Author** into `src/Screens/` or `src/`, grounding every token first.
4. **Validate** — `python tools/validate_pa_yaml.py`. Add a lint for any new failure class;
   a bug found twice should have been a lint after the first time.
5. **Audit** — the pre-paste-review agent, for a paste/do-not-paste verdict.
6. **Say plainly what the human must do by hand in Studio** (component properties,
   connections, list settings).
7. **Hand off** — say plainly what to paste, in what order, and what to report back.
8. **Record** — `docs/build-history.md` row on the report; a decision in memory if it settles something.
9. **Commit and push.**

## When to stop and ask

Ask when the answer changes the work and cannot be derived: which of two provisioning fixes to
apply, whether a design constraint is real, an ungroundable token. Do **not** ask for things
that are checkable — read the schema, unzip the `.msapp`, compute the geometry.
