# The air gap — the one-way transfer model

The single most load-bearing fact about how this repo relates to the running app. It governs
every authoring and hand-off decision. This brief records *what is true*; the *how-to* of
crossing the gap (code view, formula-bar exception, rename-and-log, paste-dialect shape) is the
**`studio-transfer`** skill — not repeated here.

## The model

Power Apps Studio runs on a **work machine**; this repo lives on a **personal machine**. Between
them there is no connector, MCP server, tenant auth, CI, linter, or test run — **only the
clipboard, moved by a human, and it runs ONE WAY: repo → Studio.**

- **Authored source flows out.** A human copies YAML/Power Fx from here and pastes it into
  Studio. That is the entire outbound channel.
- **Nothing comes back.** There is no pull, no `.msapp` export returned, no code-view sample, no
  reconcile. The **only** inbound signal is the human's **binary "it works / it doesn't."**
- **The repo is the authoritative source; Studio is the downstream apply-target.** (Not the
  reverse — the older "Studio is source of truth, repo is a mirror" framing was wrong.) Anything
  edited directly in Studio is **invisible drift, lost to the repo forever**. If you change
  something in Studio, mirror it back here by hand or it's gone.

## What it means for how we work

1. **No round-trip, so resolve unknowns yourself.** An uncertain paste token or dialect can't be
   confirmed by a returned sample. Resolve it from **public sources** — the `/example` `.msapp`
   already in the repo, Microsoft Learn, the `microsoft/PowerApps-Tooling` schema — or ship a
   **grounded fallback**. Never defer a decision to "confirm on the next pull": there is no pull.
2. **Maximise first-try correctness.** A wrong guess is a failed manual paste the human can only
   report as "didn't work," after which you revise blind. Prefer grounded constructs over
   nicer-but-unverified ones; keep each paste small so a rejection localises; keep a fallback
   ready. (Example: the screen nav is a `NavMenu`-driven gallery with the `Variant` resolved from
   public evidence, and a fully-grounded `Classic/Button` nav documented as the instant recovery.)
3. **Tokens that never gate a paste don't need chasing.** Canvas **components are not code-view-
   pasted** — they're recreated by hand in the Studio component editor. So a component's control
   tokens are a REAL paste payload (corrected 2026-08-03 — they were once assumed to be mere
   documentation, which cost two wrong tokens); only the
   tokens in the **screens** (which do paste) can actually fail. Version suffixes are optional —
   Studio uses the current version if omitted — so only a control's *name* and `Variant` matter.
4. **Provisioning names are captured by hand.** True internal column names (post `_x0020_`
   mangling) can't be pulled back — capture them manually into `schema.md` when you provision.
5. **"Landed" is confirmed by a human, then logged.** Nothing is in the app until a human pastes
   it, it validates, and they confirm it worked; record the crossing in `docs/build-history.md`. An
   authored-but-unconfirmed file is **not** live.

## Consequences for the repo layout

- **`studio/` (`pulled/`, `pulled-src/`, `snapshots/`) is inert** — it assumed a return channel
  that doesn't exist. Don't treat anything there as a baseline.
- **`/pull-reconcile` is deprecated** — there is no pull to reconcile.
- The **`change-end-to-end`** workflow's first step is *ground the paste*, not *confirm freshness*.

See also: `CLAUDE.md` "The air gap" (always loaded), the **`studio-transfer`** skill (mechanics),
and the one-way decision in `.claude/memory/INDEX.md` (dated, with reasoning).
