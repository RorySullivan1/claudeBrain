# init-project

Take a fresh project from a **one-paragraph brief** to a **seeded roadmap** with no step
improvised: build its `.claude/` by selection, choose its skill families deliberately, establish
what can actually be verified, and set the first version cursor. This is the factory's adoption
path — the thing that used to be a one-off init document written from memory each time.

**Inputs:** a brief (what the project is, its stack(s), its constraints) and a target directory.
**Output:** a populated `.claude/` in the target, a `CLAUDE.md` written from the brief, a
`context/verification-surface.md`, a seeded `.meta/roadmap/`, one `.meta/version` cursor, and a
green run of `asset_integrity` + `catalog.py`.

## Steps

1. **Brief → objective.** Read the brief and extract four things: the **objective** (what the
   project is for), the **stacks**, the **constraints** that shape how work is done (managed
   machines, no admin rights, an air gap, a pinned runtime, a compliance bar), and the
   **surfaces** work will land on. Write them down; every later step consumes one of them. →
   hand-off: the four lists.

2. **Copy the portable core — by selection, not by stripping.** Create `<target>/.claude/` and
   copy in only the project-agnostic layer, in two tiers:

   - **The dogfooded floor.** `find .claude -type l` in this repo lists it exactly: every asset
     the factory single-sources because it runs it too — the operational skills, `token-manager`,
     the whole shared hooks layer, `/version-set`, `/version-ship`, `/reindex`, and the
     `ship-version`, `verify-claims` and `establish-verification` workflows. This is a *floor*,
     not the whole core: it can only contain what the factory itself uses.
   - **What the factory opts out of but a consumer wants.** The factory has no `.meta/` and no
     prose-budget config, so two project-agnostic tiers are absent from that symlink set and must
     be copied deliberately: the **roadmap** tier (`hooks/roadmap_guard.py`,
     `hooks/roadmap_status.py`, `hooks/session-start-roadmap.json`, `development-mapping`,
     `/roadmap-set`, `/roadmap-status`, `advance-roadmap-step`) and the **prose** tier
     (`hooks/prose_budget.py`, `hooks/post-tool-use-prose-budget.json`, `prose-auditor`,
     `/prose-review`). Every hook is opt-in by presence, so one that goes unconfigured is silent.

   Also take the per-layer `README.md`s, and seed an empty `memory/INDEX.md` with the four
   sections from `session-memory` — memory is core, but its *content* never is.

   Copy-and-then-strip is the wrong direction and this step deliberately inverts it: stripping
   fails *open* — whatever you forget to remove ships as if it were chosen — while selecting
   fails *closed*, and a missing asset announces itself the first time it is wanted.
   → hand-off: a `.claude/` skeleton with no domain content in it.

3. **Select the skill and agent families.** Read `example-project/.claude/CATALOG.md` — the
   always-current inventory — and match the brief's stacks to families. Copy the families you
   select, and **record the exclusions with their reasons** in the adoption note alongside the
   selections. The exclusions are the part nobody can reconstruct later: "we don't have the VBA
   family" is indistinguishable from "we decided against it" a month on. A stack with no family
   in the catalog is a branch, not a shrug — see *Control flow*. → hand-off: the selected tree
   plus the selection/exclusion record.

4. **Write `CLAUDE.md` from the brief.** Author it fresh against the shape in
   `example-project/CLAUDE.md` — architecture, constraints, capabilities *pointing at*
   `CATALOG.md` rather than enumerating assets, reference docs, memory, roadmap, conventions,
   compact instructions. Never adapt the showcase's copy: its architecture is fictional, and an
   edited fiction reads exactly like a fact. → hand-off: the session contract.

5. **Establish verification.** Run the **`establish-verification`** workflow (copied in step 2)
   against the surfaces from step 1. `context/verification-surface.md` is a *per-project* record
   like `settings.json` and `CATALOG.md` — it is produced here, never copied from the showcase. It produces `context/verification-surface.md` and proves each `agent-runnable` check
   can fail. → hand-off: the surface doc, and the standing `unverified` debt.

6. **Seed the roadmap and set one cursor.** Apply the **`development-mapping`** skill to turn the
   objective into `.meta/roadmap/` (INDEX + stage cards), then run **`/version-set`** for the
   first version. **One cursor:** `.meta/version` and `memory/INDEX.md` § State each name a
   single unit of work — a settled constraint, not an oversight (2026-09-10 decision; probe:
   `example-project/.claude/hooks/probes/`). Do not seed a second. → hand-off: a map with a
   cursor on it.

7. **Green the tree.** Run `hooks/build-hooks.py` to compile `settings.json` from the fragments,
   `hooks/catalog.py` to generate `CATALOG.md`, and `hooks/asset_integrity.py` to check asset
   shape. All three must come back clean before the tree is handed over. → hand-off: three green
   checks.

8. **Record the adoption.** Write the selection/exclusion record and the surface summary into the
   new project's memory via **`session-memory`** — its first Log entry and, for any consequential
   exclusion, a Decision. → done.

## Control flow / stop conditions

- **Bail (no objective):** the brief names a stack but not what the project is *for* → **stop and
  ask.** Every downstream step reads the objective; inventing one seeds a roadmap toward the
  wrong place, and roadmaps are believed.
- **Branch (uncovered stack):** step 3 finds a stack with no family in `CATALOG.md` → either
  author it now via the **`author-asset`** workflow, or record the gap explicitly in the
  exclusion list. Never substitute an adjacent family — a Python family aimed at a Go project
  is worse than no family, because it looks like coverage.
- **Gate (establish-verification bails):** step 5 stops on a surface nobody can classify → the
  adoption is **not** complete. Resolve the surface or record it `unverified` with an owner;
  don't proceed to a roadmap over a tree whose checkability is unknown.
- **Bail (target not empty):** `<target>/.claude/` already exists → **stop.** This workflow
  creates; it does not merge into a populated tree. Adopting into an existing `.claude/` is a
  different job and should be done asset by asset.
- **Idempotence:** steps 5–7 are safe to re-run and are the normal way to refresh an adopted
  tree. Steps 2–4 are not — they create.
- **Success:** `asset_integrity` and `catalog.py` clean, `verification-surface.md` populated,
  `.meta/roadmap/` seeded with exactly one cursor, `CLAUDE.md` pointing at the catalog → done;
  report the families selected, the families excluded and why, and the `unverified` surfaces as
  the project's opening debt.

## Invokes

- Workflows: `establish-verification` (step 5), `author-asset` (the uncovered-stack branch).
- Commands: `../commands/version-set.md` (step 6), `../commands/reindex.md` (step 7's catalog).
- Skills: `development-mapping` (step 6), `session-memory` (step 8), `context-vs-skill` (when
  step 3 turns up knowledge that needs placing rather than a family to copy).
- Hooks / scripts: `../hooks/build-hooks.py`, `../hooks/catalog.py`, `../hooks/asset_integrity.py`.
- Source of truth for what to copy: `example-project/` (the produced layout) and
  `example-project/.claude/CATALOG.md` (the inventory).
