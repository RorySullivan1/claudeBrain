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

1. **The gap is ONE-WAY: repo → Studio. The repo is the authoritative source; Studio is the
   downstream apply-target.** Authored source flows out (a human pastes it); **nothing comes
   back** — no pull, no export, no code-view sample. The only return signal is the human's
   binary **"it works / it doesn't."** Anything edited directly in Studio is invisible drift,
   lost to the repo forever — so author in the repo and treat its files as the truth.
2. **No round-trip, so resolve unknowns yourself — don't defer to a pull that can't happen.**
   Unknown paste tokens or dialect can't be confirmed by a returned sample. Resolve them from
   **public sources** (MS Learn, the `microsoft/PowerApps-Tooling` repo, public `.msapp`
   exports), or ship a **grounded fallback**. A wrong guess is a failed manual paste the human
   reports only as "didn't work," after which you revise blind — so **maximise first-try
   correctness** and prefer grounded constructs over nicer-but-unverified ones.
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

1. **Ground every token from public sources.** Control names/versions and gallery `Variant`
   values come from an `.msapp` you can obtain offline, MS Learn, or the
   `microsoft/PowerApps-Tooling` schema — not from a pull. (Version suffixes are optional;
   Studio uses the current version if omitted, so only the control *name* and `Variant` matter.)

   **An `.msapp` carries the ENUM TABLES, and that is the strongest evidence available in an
   air-gapped setup.** MS Learn documents properties like `Icon` and never lists their values.
   But an `.msapp` is a zip, and `References/Templates.json` inside it holds the enums as
   pipe-delimited runs:

   ```bash
   unzip -o app.msapp -d /tmp/app                       # note: backslash paths, ignore the warning
   grep -oE '[A-Za-z0-9_]+(\|[A-Za-z0-9_]+){20,}' /tmp/app/References/Templates.json
   ```

   That recovers the complete **180-value classic `Icon` enum** — and immediately exposes
   invented names (`Icon.Back`, `Icon.Documents`, `Icon.Table` are not in it). Extract the list
   once into a checked-in data file (e.g. `tools/studio-enums.json`) and have your validator
   check against it. **Check an `.msapp` you already have BEFORE declaring a value ungroundable.**
2. **For anything still uncertain, author the grounded fallback**, and keep the risky-but-nicer
   variant documented as an alternative to try if the first paste is rejected.
3. **The human's feedback is binary** — "it pasted / it didn't." Design each paste so a failure
   is cheap to recover: small units, one control-group at a time, with the fallback ready.
4. **A "didn't work" can be a STALE STUDIO, not a bad paste.** Studio's editor can keep showing
   an old component definition after its properties or body have changed — the app behaves as if
   the edit never happened. **Ask for a browser refresh before believing any failure report.**
   Across a one-way gap a false negative is expensive: it looks like an authoring bug, and the
   revise-blind loop that follows rewrites correct code.

## The auto-layout container

`GroupContainer@1.5.0` with `Variant: AutoLayout`, read straight off Studio's code view. This is
the control the Insert pane calls *Horizontal container* / *Vertical container* — one control,
direction chosen by a property.

```yaml
- Container3:
    Control: GroupContainer@1.5.0
    Variant: AutoLayout
    Properties:
      LayoutDirection:  =LayoutDirection.Horizontal    # or .Vertical
      LayoutAlignItems: =LayoutAlignItems.Center
      PaddingTop: =8
      PaddingBottom: =8
      PaddingLeft: =8
      PaddingRight: =8
    Children:
      - Rectangle2:
          Control: Rectangle@2.3.0
          Properties:
            LayoutMinWidth:  =16      # child-side layout properties
            LayoutMinHeight: =16
```

**Children carry no X/Y** — the container positions them. That matters more here than it looks:
X/Y are exactly the properties Studio freezes on paste, so **anything inside an auto-layout
container is immune to that whole failure mode**. It is the one layout that survives the gap
intact.

**A SCROLLING COLUMN — every property below confirmed from Studio's own code view:**

```yaml
- frmScroll:
    Control: GroupContainer@1.5.0
    Variant: AutoLayout
    Properties:
      LayoutDirection:  =LayoutDirection.Vertical
      LayoutAlignItems: =LayoutAlignItems.Center
      LayoutGap:        =8
      LayoutOverflowX:  =LayoutOverflow.Scroll
      LayoutOverflowY:  =LayoutOverflow.Scroll
      PaddingTop: =8   PaddingBottom: =8   PaddingLeft: =8   PaddingRight: =8
```

Still inferred (never observed non-default, so Studio never printed them):
`LayoutJustifyContent`, `LayoutWrap`, `FillPortions`.

**A hidden child takes no space**, so a results gallery placed inline after its search box
expands the column when it opens and collapses when it closes — no overlay, no z-order, no
one-picker-at-a-time gate. In a scrolling form that replaces the whole absolute-overlay pattern.

## LAYOUT FORMULAS DO NOT SURVIVE THE PASTE

First-party, from *Create responsive layouts in canvas apps*:

> After you write formulas for the **X**, **Y**, **Width** and **Height** properties of a control,
> your formulas will be overwritten with constant values if you subsequently drag the control in
> the canvas editor.

Studio does that positioning as part of a paste, so **every layout formula lands as a frozen
constant** — the value the formula happened to evaluate to *at the instant of the paste*.

Three consequences, all of which bite in practice:

1. **A layout formula that references another control freezes to a transient value.** If the
   referenced control isn't yet at its final position when the paste evaluates, the wrong number
   is baked in permanently — e.g. a gallery positioned off a filter row lands at the row's
   mid-paste `Y` and covers it. **Never position off another control** — the value must be
   self-contained.
2. **The landed app is not responsive.** `Width: =Parent.Width - 48` becomes `1318`. Fine for a
   fixed-size tablet app, but it means a Theme change will never propagate to layout: re-pasting
   is the only way, and re-pasting re-freezes.
3. **Fixing a frozen value means editing that property in Studio**, not re-pasting — the paste
   will just freeze it again. Set the number in the formula bar.

**Authoring rule:** prefer plain integers for X/Y/Width/Height whenever the value is static
anyway, so what lands equals what was authored and there is no evaluation-order dependency at
all. Keep a formula only where genuine responsiveness is wanted, and tell the human not to drag
that control.

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
