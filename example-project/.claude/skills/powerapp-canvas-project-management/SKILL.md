---
name: powerapp-canvas-project-management
description: >
  Running a canvas-app project as a repo — source control, provisioning, hand-off discipline
  and the records that make a one-way gap survivable. Use this skill for any question about
  process rather than code: "what's the state of the app", "what's left to build", "how do I
  get the source out of Studio", "pac canvas download", "what's in an .msapp", "update the
  build book", "log this paste", "the lists are provisioned", "what should I do next", "did
  this land". Covers: the golden-source inversion (repo defines, SharePoint applies), the
  authored→landed lifecycle and the four records that support it (a golden-source schema file,
  a build book, a paste/transfer log, a decisions ledger), provisioning verification, `.msapp`
  structure and the CLI, and the diagnostic discipline for reports that arrive as one sentence.
  Boundaries: the clipboard mechanics themselves are studio-transfer; formulas are
  powerapp-canvas-development; schema column design is sharepoint-list-architecture; durable
  decisions are session-memory. This skill owns *the project's state and its paper trail*.
---

# Canvas Project Management — the paper trail is the product

Nothing here is bureaucracy. Across a one-way gap, the records ARE the feedback loop: they are
the only thing that distinguishes "authored" from "actually working", and the only defence
against re-deciding something already settled.

---

## The four records, and what each is for

Four **roles**, not four filenames. The paths below are the conventional names used in this
example; a project may call them anything, but it must have all four, pick the names **once**,
and state them in its `CLAUDE.md` so every session finds the same paper trail.

| Record (example path) | Answers | Rule |
|---|---|---|
| **Golden-source schema** — e.g. `schema/schema.yaml` | what the backend IS | **Golden source.** The repo defines; SharePoint applies. Never edited to match reality — reality is changed to match it. |
| **Build book** — `BUILD-BOOK.md` or equivalent | what to do next, in order | The linear runbook for the human. Contracts inlined so nobody flips between files while typing. |
| **Paste / transfer log** — e.g. `paste-log.md` | what actually landed | One row per crossing. **Claude maintains it** from chat reports, because the human works on a machine that cannot write to this repo. |
| **Decisions ledger** — e.g. `.claude/memory/INDEX.md` (the `session-memory` skill) | what was decided and why | Append-only. Committed, because the session environment is ephemeral. |

A unit is **authored** until a human pastes it and confirms. The paste log is the only place
that distinction is recorded — if it is not in the log, it is not in the app.

## The golden-source inversion

Normally a repo mirrors the system of record. Here it is the reverse: **the repo defines the
backend and the app; the tenant merely applies them.** Nothing reads SharePoint or Studio back,
so there is no reconciliation step and no drift detection — only what the repo says and what a
human reports. Two consequences drive everything else:

- **Never edit a record to match observed reality.** If the deployed list disagrees with the
  schema file, the *list* is wrong; re-provision it. Editing the schema to match launders a
  defect into the golden source.
- **Anything changed only in the tenant is invisible.** Edits made directly in Studio or in the
  SharePoint UI are drift the repo will never see. Author here, apply there.

## Provisioning verification

The schema file defines the lists; nothing reads SharePoint back. So a mismatch is **silent
until a screen errors**. Four things drift, ordered by how loudly they fail:

1. **Arity** — mark `multi:` on every Person and Managed Metadata column. A multi column returns
   a TABLE: the read errors (`Coalesce(<table>, "")` → *"expecting a Table"*) and the write fails
   too. This is the most common provisioning defect; check it first.
2. **Internal names**, frozen at creation. A column created as "Project Manager" is internally
   `Project_x0020_Manager` and every token that assumes the display name misses.
3. **Choice values**, including case. A `Patch` of an unlisted value fails; a `Filter` on one
   silently returns nothing — the quiet one.
4. **Indexed columns.** No error at all; a delegable `Filter` just becomes a threshold failure
   once the list grows past the delegation limit.

Verify these against the schema file whenever the human reports "the lists are provisioned" —
that report is a claim, not a confirmation.

## Getting source out of Studio

```powershell
pac canvas list
pac canvas download --name "MyApp" --extract-to-directory "C:\dest"
Expand-Archive -Path app.msapp -DestinationPath C:\dest    # an .msapp IS a zip
```

Inside: `\src\App.pa.yaml`, `\src\<Screen>.pa.yaml`, `\src\Component\<Name>.pa.yaml`. Only
`\src` is meant for source control; the JSON files are not stable.

**`References/Templates.json` is the hidden prize** — it carries the enum tables as
pipe-delimited runs. That is where the complete 180-value classic `Icon` enum comes from, and
it is the strongest grounding evidence available without a round trip. Always look there
before declaring a token ungroundable.

**`pac` cannot author component custom properties** (`PA3004`). Component contracts are typed
by hand in Studio; only bodies paste. Plan any component work as three phases: properties →
body → the phase-3 formulas that reference child controls.

## Diagnosing a one-sentence report

The human's whole return channel is a sentence. Extract the most from it:

1. **Ask whether Studio was refreshed.** A stale editor reports working code as broken. This
   failure mode has cost entire rewrites of components that were already correct. Make it the
   first question, always.
2. **Ask for a photo of code view** when a token or a number is in doubt. A single screenshot
   can pin a gallery `Variant`, a container token, and the whole modern control set at once. It
   carries vastly more than "it worked / it didn't".
3. **Compare the numbers.** If they report `Y=193` and the source says `220`, they are on a
   stale copy — a much shorter conversation than a debugging session.
4. **When one instance of a repeated formula fails and its siblings do not, suspect the DATA.**
   Two byte-identical formulas that differ only in the column they bind to will diverge on
   column arity or internal name, not on syntax.
5. **Sweep the class the same day.** Fixing only the reported instance leaves the rest to be
   found one painful round trip at a time. One dead gallery usually means every gallery built
   from the same template is dead too.

## Workflow: a change, end to end

1. **Decide** — check the decisions ledger first; do not relitigate a settled call.
2. **Schema first** — if the change touches data, edit the golden-source schema file before any
   app code, and note whether SharePoint needs re-provisioning.
3. **Author** into the repo's authored-source area (e.g. `src/authored/` for control YAML,
   `src/patches/` for App-object bodies that go through the formula bar), grounding every
   token first.
4. **Validate** — run the repo's YAML/Power Fx validator (in this example,
   `python tools/validate_pa_yaml.py`). Add a lint for any new failure class; a bug found twice
   should have been a lint after the first time.
5. **Audit** — the `pre-paste-review` agent, for a paste / do-not-paste verdict.
6. **Update the build book** with anything the human must type by hand (component custom
   properties, connections, list settings).
7. **Hand off** — say plainly what to paste, in what order, and what to report back.
8. **Record** — a paste-log row on the report; a decision in the ledger if it settles something.
9. **Commit and push.**

The `change-end-to-end` workflow orchestrates these steps; `studio-transfer` owns the crossing
itself (steps 7–8).

## When to stop and ask

Ask when the answer changes the work and cannot be derived: which of two provisioning fixes to
apply, whether a design constraint is real, an ungroundable token. Do **not** ask for things
that are checkable — read the schema, unzip the `.msapp`, compute the geometry.
