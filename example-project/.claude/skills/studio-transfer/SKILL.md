---
name: studio-transfer
description: >
  Expert at moving canvas Power App source between Power Apps Studio (on a locked-down work
  machine) and a git repo across a manual clipboard air gap — the authored→audited→landed
  lifecycle and the code-view mechanics that make it work. Use this skill whenever the task
  involves getting Power Fx / control YAML into or out of Studio by hand: "paste this into
  Studio", "copy the control code", "why won't my YAML paste", "the paste created Gallery1_1",
  "how do I get App.OnStart in", "is the repo in sync with the live app", "log this paste",
  "did this land". Trigger on the mechanics of the transfer channel — code view (View code /
  Ctrl+C / Ctrl+V), the App-object formula-bar exception, paste-time validation, rename-and-log
  after paste, clipboard permission for make.powerapps.com, .pa.yaml vs code-view YAML,
  `pac canvas download`, the round-trip test. Implicit signals: any uncertainty about whether
  the repo matches the running app, a rejected paste, a control that landed with a suffixed
  name, or a request to author formulas that will later be pasted. Boundaries: the *content* of
  the formulas — delegation, column-type policy, Person patching — is power-fx-development;
  auditing authored Power Fx before a paste is the pre-paste-review agent; the list schema is
  sharepoint-list-architecture. This skill owns the *transfer channel and its discipline*, not
  what the code says.
---

# Studio Transfer Skill

**When to reach for this skill:** a team is building a canvas app whose source lives in a git
repo, but the repo and Power Apps Studio are on **different machines with no pipeline between
them** — no connector, MCP server, tenant auth, CI, or linter. Studio runs on a locked-down work
machine; the repo lives somewhere the work machine cannot reach. This is common in corporate
environments where automated ALM is not permitted.

In that situation **the only channel is the clipboard, moved by a human, one paste at a time —
and it runs ONE WAY: repo → Studio.** Nothing comes back but the human's binary "it worked / it
didn't." Your job is to make each crossing deliberate, small enough to diagnose, and recorded —
the repo is the **authoritative source**, not a mirror of a Studio you cannot query. Lead with
the mechanics that matter for the crossing in front of you.

For the model itself and its consequences, see the **`air-gap`** context brief; this skill is the
*how-to*.

## Core principles (these are rules)

1. **The gap is ONE-WAY: repo → Studio.** The model — why the repo is the authoritative
   source, what "nothing comes back" implies, why Studio edits are invisible drift — is the
   **`air-gap`** brief's to state, not this skill's. Operate on its two consequences: author
   in the repo and treat its files as the truth, and expect no return signal beyond the
   human's binary **"it works / it doesn't."**
2. **No round-trip, so resolve unknowns yourself — don't defer to a pull that can't happen.**
   Resolve unknown paste tokens from **public sources** or ship a **grounded fallback**; a
   wrong guess is a failed paste you revise blind, so **maximise first-try correctness**.
3. **Every paste costs human effort.** Few large *correct* pastes beat many small
   speculative ones. Get the formula right (and audited — see the pre-paste-review agent)
   *before* asking a human to paste it.
4. **Studio's paste-time validation is the only check that exists.** Keep each paste small
   enough that a rejection points at an obvious cause. A 400-line screen that won't paste
   tells you nothing; one control at a time tells you exactly what broke.
5. **Record every crossing in a paste log.** An unlogged paste is a drift you can't
   reconstruct. The log — a plain file in the repo, e.g. `paste-log.md` — is how a future
   session knows what actually landed and under what name.

## No round-trip test — the channel is one-way

A round-trip test (copy a control out of Studio, commit it, paste it back) is **impossible under
a one-way gap**: Studio's output cannot reach the repo. Do not instruct the human to "View code
and drop the sample into a `pulled/` directory" — that assumes a return channel that does not
exist.

Instead, establish paste-readiness *before* the human ever pastes:

1. **Ground every token from public sources.** Control names/versions, gallery `Variant`
   values, and enum members come from an `.msapp` you can obtain offline, MS Learn, or the
   `microsoft/PowerApps-Tooling` schema — not from a pull. The evidence ladder and the
   `.msapp` enum-recovery technique (`References/Templates.json` holds the enum tables — the
   strongest evidence in an air-gapped setup) are **owned by `powerapp-canvas-controls`**;
   apply them from there rather than a restated copy. **Check an `.msapp` you already have
   BEFORE declaring a value ungroundable.**
2. **For anything still uncertain, author the grounded fallback**, and keep the risky-but-nicer
   variant documented as an alternative to try if the first paste is rejected.
3. **The human's feedback is binary** — "it pasted / it didn't." Design each paste so a failure
   is cheap to recover: small units, one control-group at a time, with the fallback ready.
4. **A "didn't work" can be a STALE STUDIO, not a bad paste.** Studio's editor can keep showing
   an old component definition after its properties or body have changed — the app behaves as if
   the edit never happened. **Ask for a browser refresh before believing any failure report.**
   Across a one-way gap a false negative is expensive: it looks like an authoring bug, and the
   revise-blind loop that follows rewrites correct code.

## What survives the paste — the two transfer-side layout facts

Two layout facts change how you author for the crossing. Both are **owned elsewhere** — the
container's tokens, YAML shape, and still-inferred properties by **`powerapp-canvas-controls`**,
the freeze mechanics and the geometry consequences by **`powerapp-canvas-design`** (§ *layout
formulas do not survive the paste*). What this skill adds is their transfer meaning:

1. **Auto-layout containers are the one layout that survives the gap intact.** Children of a
   `GroupContainer`/`AutoLayout` carry no X/Y — and X/Y are exactly what Studio freezes at
   paste time, so everything inside a container is immune to that failure mode. Prefer a
   container over absolute positions for anything that stacks.
2. **Every layout formula lands as a frozen constant** — the value it evaluated to at the
   instant of the paste. So at *authoring-for-paste* time: plain integers for X/Y/Width/Height
   unless genuine responsiveness is wanted, never position one control off another, and tell
   the human that fixing a frozen value means editing it in Studio's formula bar — re-pasting
   just re-freezes it.

## The channel — code view mechanics

Code view (GA **17 Mar 2025**) is the interactive channel. Grounded on Microsoft Learn
*Use code view for canvas app controls*:

- **Turn on the Power Fx formula bar** (app **Settings**) or View code isn't available.
- **Pull:** right-click a control (tree view or canvas) → **View code**; copy via the menu,
  **Ctrl+C**, or the **Copy code** button. Code view shows the selected control **and all its
  child controls** — copying a container brings its subtree.
- **Land:** paste via the menu or **Ctrl+V**. Pasting **creates a new control** after
  validation — it is **never** an in-place patch. Use the exact **YAML Studio generated**;
  it is validated before the control is created, so hand-edited shapes get rejected.
- **Paste assigns a suffixed name** (`Gallery1` → `Gallery1_1`). **Rename immediately** to the
  intended name and **log both** the intended name and the suffix Studio gave, so later work
  reconciles.
- **Browser clipboard permission** is required. The first paste prompts; if it fails, allow
  **`https://make.powerapps.com`** for clipboard access in the browser (Edge: add it to the
  allowed sites).

### Two hard limitations — design around them (official *Known limitations*)

- **The App Object has no code view.** `App.OnStart`, `App.Formulas`, and named formulas
  **cannot** be copied or pasted through code view. They go through the **formula bar only** —
  paste the body into the formula bar by hand. Treat App-level code as a separate,
  formula-bar-only transfer path, kept in its own place in the repo (e.g. an
  `src/patches/` directory) rather than mixed in with pasteable control YAML.
- **The code-view pane is not editable.** You cannot edit code inside code view — pasting
  creates, it never patches. To change a control, author the new YAML in the repo, paste to
  create, rename, and delete the old one (or patch its properties in the formula bar).

## Two artifacts, one is read-only — don't confuse them

There are two YAML surfaces and they are **not** interchangeable. Grounded on Microsoft Learn
*View source code files for canvas apps* and *Source control for canvas apps*:

| Surface | What it is | Can you paste it into Studio? |
|---|---|---|
| **Code-view YAML** | What **View code / Copy code / Paste code** produce and consume, interactively, per control | **Yes** — this is the interactive create channel. Use Studio's own output verbatim. |
| **`*.pa.yaml` source** | The single **active** source-control schema, in the `\Src` of an exported `.msapp` (or a Git-integration repo). **Read-only** — "not used when an app is loading"; changes to the file are ignored/lost. Editing, merging, conflict resolution supported **only in Power Platform Git Integration**, and only after you **publish**. | **No** — it's a *review* artifact, not a paste source. Don't try to paste `.pa.yaml` through code view. |

Consequences when you're on the repo side of the gap:
- The **code-view dialect** is what you author toward for control paste. Ground it from an
  `.msapp` you can open offline, MS Learn, or the `microsoft/PowerApps-Tooling` schema — **not**
  from a pull (there is none). The modern versioned form (`Control: Type@version`) is what
  current Studio uses; the retired `pac canvas unpack` inline (`Name As type:`) format is **not**
  the target — do not author to it.
- The `\Src\*.pa.yaml` inside an exported `.msapp` is a useful **read-only reference** for
  *reasoning* about a whole app, but it is **not** a paste source. Producing one requires
  `pac canvas download` (PAC CLI, tenant-authenticated) run on the machine that has that auth —
  the Studio side. Under a one-way gap **you never receive one**, so any `.msapp` you hold is a
  sample you brought in, never the live app's state.

## The authored → landed lifecycle

1. **Authored** — the change, written in the repo in the paste dialect. Keep pasteable control
   YAML in your authored-source directory (e.g. `src/authored/`) and App-object bodies in a
   separate formula-bar directory (e.g. `src/patches/`). The repo is the source of record;
   formula *content* follows `power-fx-development`.
2. **Audited** — run the **pre-paste-review agent** on the authored change. It returns a
   paste / do-not-paste verdict. Do not hand a human a paste that hasn't passed.
3. **Landed** — a human pastes it into Studio; it validates and creates the control; they
   rename it and tell you **whether it worked** (the only signal that returns). You **record the
   crossing** (date, target, intended name, Studio's suffix, outcome) in the paste log. Only now
   is it real.

There is no "pulled" stage before and no "reconciled" stage after — nothing flows back. An
authored file that has not landed is **not** in the app. Studio-only edits are drift you will
never see; never describe the app as if authored-but-unlanded work is live.

## Watch Out

1. **Waiting on a pull/round-trip that can't happen.** Nothing returns from Studio but a binary
   "worked/didn't." Don't defer a decision to "confirm on the next pull" — resolve it from public
   sources or ship a fallback now.
2. **Big speculative pastes.** A large paste that Studio rejects wastes a human's effort and
   hides the cause — and you only learn "it didn't work." Author small, audited units; let
   validation point at one thing; keep a fallback ready.
3. **Forgetting the App-object exception.** Trying to paste `App.OnStart` through code view
   fails silently to exist — there's no App code view. It's formula-bar-only.
4. **Losing the rename.** Paste names collide-suffix (`_1`). If you don't rename and log
   immediately, the tree fills with `Control_1` noise you can't map back.
5. **Pasting `.pa.yaml`.** It's read-only review output, not a paste source. Imitate the
   **code-view** dialect for anything you intend to land.
6. **Rewriting code on an unrefreshed failure report.** Before diagnosing, confirm Studio was
   refreshed after the edit. A stale editor reports a working unit as broken, and each blind
   rewrite that follows costs a full round trip and can damage code that was already correct.

## Out of scope — defer

- **The air-gap model itself** (what's true about the channel, why the repo is golden source) →
  the **`air-gap`** context brief.
- **Formula *content*** — delegation, column-type policy, Person/Claims patching, aggregation
  rules → **power-fx-development** (matrix in its `delegation.md`).
- **Auditing an authored change before paste** (non-delegable expressions, schema violations,
  paste/do-not-paste verdict) → the **pre-paste-review** agent.
- **The list schema and internal names** the formulas bind to → **sharepoint-list-architecture**
  (plus whatever list-schema brief your project keeps in `context/`).
- **Orchestrating a whole change** (ground → author → audit → hand off → record) → the
  **change-end-to-end** workflow, which invokes this skill for the transfer steps.
