# 2026-06-28 01:45 · remote-instance-pull-review

**Goal:** Review: is the layout compatible with a remote Claude instance pulling assets from this brain into another project?

## What happened
- Review-only session (no files changed). User clarified "exploring claude instances" = **a Claude session in another project pulling specific skills/agents/capabilities from this brain into that project** (the consumer-side of factory→consumer distribution).
- Verdict: **partially compatible** — discoverable, but the autonomous-pull path has real friction. Works today for a human copying one self-contained skill folder per `CLAUDE.md`; not yet smooth for a remote Claude to do safely.
- Three frictions that bite a remote puller:
  1. Canonical products live under `example-project/.claude/` (labeled "mock consumer"), not an obvious library; repo-root `.claude/` is authoring meta-tooling.
  2. Repo-root `.claude/` is a **symlink trap** — operational skills (session-memory, knowledge-router, token-optimizer, skill-distiller, agent-finder), hooks, and token-manager agent are symlinks into `../../example-project/`. Naive copy from repo-root → broken symlinks unless `cp -rL`/resolve to canonical.
  3. **No per-asset dependency/companion manifest** — skill→skill (presentation pipeline, quant family), agent→skill, skill→hook→settings.json. Partial pulls silently degrade (e.g. session-memory needs its lifecycle hooks + settings entries).
- Also: no machine-actionable pull interface (only human prose); showcase scoped names (`example-project:agent-finder`) need normalizing.

## Gotchas & dead ends
- Confirmed via `ls -l`: factory `.claude/{skills,hooks,agents}` are symlinks → example-project canonical (matches the single-sourcing decision). Reinforces the copy-trap point for external pullers.
- No existing install/pull/distribute/manifest doc anywhere (grep only hit asset *content* like vba-distribution skills).

## State at end
- Suggestions delivered (review only, NOT built), priority order: (1) machine-readable distribution manifest — root `LIBRARY.md`/`manifest.json` per shippable asset {canonical path, type, purpose, deps, companion hooks+settings, `cp -rL` recipe} — highest leverage; (2) agent-facing "pull-from-brain" procedure skill/doc; (3) per-asset `requires:` declaration; (4) signpost example-project/.claude as the canonical library, repo-root as authoring-only; (5) provenance/version stamp on pulled assets (ties to `.meta/version`); (6) optional fetch helper script.
- General-review gaps also surfaced (still open threads): `/validate-asset` + structural validator; tests/CI for the generators; `hook-authoring`/`context-authoring` meta-skills to complete the tier; code-reviewer + orchestrator agent siblings.

## Open threads
- User chose **review only** — nothing implemented. If picked up: the distribution manifest (#1) is the highest-value next build for the remote-pull use case. Branch in flight: `claude/repo-review-claude-instances-5tth8d`.

## Follow-up build (same session) — distribution/ layer
- User then asked to plan + execute. Approved plan: built the `distribution/` layer covering all 6 remote-pull suggestions.
- **Files added:** `distribution/registry.json` (curated overlay: category/portable/requires/hooks per asset), `distribution/build_library.py` (generator, mirrors `example-project/.claude/hooks/catalog.py` — parse_frontmatter + scan, `--check`/`--warn-if-stale`), `distribution/pull.py` (the pull helper), `distribution/README.md`, generated root `LIBRARY.md` + `distribution/library.json`.
- **Files edited:** root `README.md` (+ "Pulling assets into another project"), root `CLAUDE.md` (canonical-library statement in "Using an asset elsewhere" + `distribution/` in structure diagram), `.claude/memory/INDEX.md`.
- **Design keys:** (1) always copy from canonical `example-project/.claude/` (real files; repo-root `.claude/` is symlinked) and dereference symlinks → sidesteps the copy-trap; (2) `pull.py` transitively expands `requires`, brings companion hook fragments + any `.py` they reference (parsed from fragment JSON, generically catches loose `post_bash_filter.py`/`pre_read_guard.py`) + `build-hooks.py`; (3) registry is an overlay — name/desc read live from frontmatter (no drift); assets with no entry default to `category: other` and are flagged by `--check`; (4) provenance stamp `.brain-provenance.json` records `brain_version` (from `.meta/version` else git sha) for refresh decisions.
- **Verified end-to-end:** build_library.py `--check` green (55 assets, none uncategorized); dry-runs prove transitive deps (knowledge-router→session-memory+skill-distiller; deck-builder→presentation-design+branding; token-optimizer→token-manager+2 guards+loose scripts); real pull produced **regular files, zero symlinks**, bundled skill scripts + loose guard scripts + build-hooks.py all present, provenance written; the copied build-hooks.py compiled the pulled fragments into a valid settings.json (8 fragments, all events wired to pulled scripts).
- **Out of scope (deferred):** general gaps — `/validate-asset`, tests/CI for generators, `hook-authoring`/`context-authoring` meta-skills, code-reviewer/orchestrator agents.
- **Next:** commit + push to `claude/repo-review-claude-instances-5tth8d`. No PR unless asked. Optional future: wire `build_library.py --warn-if-stale` into a SessionStart hook so LIBRARY.md self-freshens like CATALOG.md.
