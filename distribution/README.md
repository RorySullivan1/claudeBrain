# `distribution/` — pulling assets out of the brain

This layer lets a Claude instance working in **another project** pull specific skills, agents,
and other assets out of this brain — with their dependencies and companion hooks — instead of
hand-copying folders and silently missing the pieces that make an asset work.

It is a **factory capability** (about the brain exporting itself), not a pullable asset.

## Why this exists

The brain's shippable assets live canonically in `example-project/.claude/`. Three frictions made
a naive copy unreliable; this layer removes them:

1. **Canonical home.** The repo-root `.claude/` is authoring-only and holds **symlinks** into
   `example-project/`. Copy from it and you get broken links. The **real** files are in
   `example-project/.claude/` — `pull.py` always copies from there and dereferences symlinks.
2. **Dependencies.** Many assets need siblings (e.g. `presentation-design` needs `branding`;
   `knowledge-router` works with `session-memory` + `skill-distiller`). `pull.py` expands
   `requires` transitively.
3. **Companion hooks.** Operational skills are inert without their lifecycle hooks (e.g.
   `session-memory` needs 4 hook fragments; `token-optimizer` needs its two guards). `pull.py`
   brings the fragments, any scripts they invoke, and the `build-hooks.py` compiler.

## Files

| File | Role |
|---|---|
| `registry.json` | Hand-authored overlay: each asset's `category`, `portable`, `requires`, `hooks`. The dependency graph that can't be auto-derived. |
| `build_library.py` | Generator (like `.claude/hooks/catalog.py`). Scans `example-project/.claude/`, merges `registry.json`, writes `../LIBRARY.md` + `library.json`. |
| `library.json` | Generated machine manifest `pull.py` consumes. Do not hand-edit. |
| `pull.py` | The helper a consumer runs to pull asset(s) into a target `.claude/`. |
| `../LIBRARY.md` | Generated human/agent index of every pullable asset and its pull command. |

## Pull procedure (for a Claude instance in another repo)

1. **Find the asset.** Read `LIBRARY.md` (repo root) — assets are grouped by category, each with
   its dependencies, companion hooks, and exact pull command. `portable: no` marks
   stack/domain-specific assets (Office/VBA, quant) only useful with that stack.
2. **Pull it** into the target project's `.claude/`:
   ```
   python distribution/pull.py skills/knowledge-router --dest /path/to/target/.claude
   ```
   Pass several ids to pull them together. Add `--dry-run` to preview the full resolved set
   (assets + dependencies + hooks) without writing.
3. **Activate companion hooks** (only if the pull reported any). The pull copies the hook
   fragments and the `build-hooks.py` compiler; run it in the target to merge them into that
   project's `settings.json`:
   ```
   python /path/to/target/.claude/hooks/build-hooks.py
   ```
   (Or merge the printed fragments into `settings.json` by hand.)
4. **Done.** What was pulled, from which brain version, and when is recorded in
   `<target>/.claude/.brain-provenance.json`.

## Refreshing / updates

Pulls are copies — there is no live link back to the brain. `.brain-provenance.json` records the
`brain_version` each asset was pulled at, so a consumer can tell when an asset is behind and re-run
`pull.py` to refresh it.

## Maintaining the manifest (factory side)

`LIBRARY.md` + `library.json` are generated — regenerate after adding or changing an asset:

```
python distribution/build_library.py          # rebuild
python distribution/build_library.py --check   # CI: exit 1 if stale
```

When you add a new asset, give it an entry in `registry.json` (category + any `requires`/`hooks`).
Assets with no entry default to `category: other` and are flagged by `--check` so they don't slip
through uncategorized.
