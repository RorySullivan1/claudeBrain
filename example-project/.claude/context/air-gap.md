# The air gap — the one-way transfer model

A reference model for projects where a canvas Power App's source is kept in a git repo but
**Power Apps Studio is reachable only by hand**. It is common in corporate environments: Studio
runs on a locked-down, managed work machine, the repo lives elsewhere, and no automated pipeline
between them is permitted. When that describes the setup, this brief is the single most
load-bearing fact about how the repo relates to the running app, and it governs every authoring
and hand-off decision.

This brief records *what is true* under the model. The *how-to* of actually crossing the gap
(code view, the App-object formula-bar exception, rename-and-log after paste, paste-dialect
shape) is the **`studio-transfer`** skill — not repeated here.

## The model

Between the repo and Studio there is no connector, MCP server, tenant auth, CI, linter, or test
run — **only the clipboard, moved by a human, and it runs ONE WAY: repo → Studio.**

- **Authored source flows out.** A human copies YAML/Power Fx out of the repo and pastes it into
  Studio. That is the entire outbound channel.
- **Nothing comes back.** There is no pull, no `.msapp` export returned, no code-view sample, no
  reconcile. The **only** inbound signal is the human's **binary "it works / it doesn't."**
- **The repo is the authoritative source; Studio is the downstream apply-target.** Not the
  reverse. The tempting alternative framing — "Studio is the source of truth, the repo is a
  mirror" — is wrong here, because a mirror requires a return channel and there is none.
- **The repo can silently drift from the running app.** Anything edited directly in Studio is
  **invisible drift**: the repo never learns about it and it is lost from the repo's history
  forever. Someone who changes something in Studio must mirror it back by hand, or it is gone.

## What it means for how work is done

1. **No round-trip, so unknowns must be resolved up front.** An uncertain paste token or dialect
   detail cannot be confirmed by a returned sample. It is resolved from **public sources** — any
   `.msapp` obtainable offline, Microsoft Learn, the `microsoft/PowerApps-Tooling` schema — or a
   **grounded fallback** ships instead. "Confirm it on the next pull" is never available: there
   is no pull.
2. **First-try correctness is the currency.** A wrong guess becomes a failed manual paste that a
   human can only report as "didn't work," after which the next attempt is authored blind.
   Grounded constructs beat nicer-but-unverified ones; small pastes localise a rejection; a
   documented fallback shortens the recovery loop.
3. **Not every uncertainty gates a paste.** Only source that actually crosses the clipboard can
   fail at paste time. Canvas **components, for instance, are not code-view-pasted** — they are
   recreated by hand in Studio's component editor — so their tokens still matter as a real paste
   payload wherever they are referenced from pasted screens, while purely documentary tokens
   never gate anything. Version suffixes are optional (Studio uses the current version when one
   is omitted), so a control's *name* and `Variant` are what must be right.
4. **Facts that exist only on the Studio side are captured by hand.** True internal names created
   at provisioning time (e.g. SharePoint columns after `_x0020_` mangling) cannot be pulled back;
   whoever provisions records them manually into the project's schema reference.
5. **"Landed" is a human confirmation, then a log entry.** Nothing is in the app until a human
   pastes it, Studio validates it, and they confirm it worked — recorded in a paste/transfer log
   (e.g. `paste-log.md`) with the date, target, intended name, the suffix Studio assigned, and
   the outcome. An authored-but-unconfirmed file is **not** live, and must never be described as
   if it were.

## Consequences for repo layout and process

- **Any "pulled" / "snapshot" area is inert.** Directories that presuppose a return channel
  (`pulled/`, `pulled-src/`, `snapshots/`) hold nothing trustworthy under a one-way gap and must
  not be treated as a baseline. Prefer not to create them at all.
- **Reconcile steps are dead code.** A "pull and reconcile" command or workflow step has nothing
  to reconcile against; drop it rather than leaving it to mislead.
- **The first step of a change is *ground the paste*, not *confirm freshness*.** There is no
  baseline to be stale against — the repo *is* the source. See the **`change-end-to-end`**
  workflow.

## See also

- **`studio-transfer`** skill — the mechanics of every crossing.
- **`change-end-to-end`** workflow — the authored → audited → landed orchestration.
- **`pre-paste-review`** agent — the paste / do-not-paste verdict before a human is asked to act.
