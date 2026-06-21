# 2026-06-21 13:13 · capability-catalog

**Goal:** Slim example CLAUDE.md to category level + add catalog.py/CATALOG.md/reindex/hooks

## What happened
- **Slimmed `example-project/CLAUDE.md`**: replaced the enumerated "Skills available" +
  "Agents available" sections with one category-level **## Capabilities** section that points to
  `.claude/CATALOG.md` and states skills/agents auto-load by `description:`. ~36 enumerated lines
  → ~11. Kept Architecture/Constraints/Reference Docs/Memory/Versioning/Conventions/Compact.
- **Added a capability catalog system** (modeled on build-hooks.py + context.py):
  - `example-project/.claude/hooks/catalog.py` — mechanical generator (bare script in hooks/, NOT
    a skill — a SKILL.md would auto-inject a description every session, defeating the goal).
    Modes `build` / `--check` / `--warn-if-stale` / `--on-edit`. Scans 4 layers
    (skills/*/SKILL.md, agents|commands|workflows/*.md), preamble+marker like context.py.
  - `.claude/CATALOG.md` per tree — generated, **not symlinked** (content differs per tree, like
    settings.json).
  - `/reindex` command (`commands/reindex.md`).
  - Two hook fragments: `post-tool-use-catalog.json` (--on-edit) + `session-start-catalog-check.json`
    (--warn-if-stale; warn-only, catalog is on-demand, never printed every session).
  - Factory symlinks for catalog.py + 2 fragments + reindex.md; rebuilt settings.json in BOTH trees
    (13 fragments each).
  - Updated 4 READMEs (hooks ×2, commands ×2).

## Decisions
- User chose: on-demand catalog (not auto-loaded); bare script in hooks/ (not a skill — switched
  from initial "skill" pick once told a skill's description loads every session); full CLAUDE.md
  collapse; command name `/reindex`.
- Self-contained frontmatter parser duplicated from agents.py (~15 lines) rather than importing
  across skill bundles — coupling would break bundle portability. Noted in code comments "do not DRY".
- Skills scanned via `iterdir()` + `is_file()` (follows symlinks one level) instead of os.walk;
  `is_catalog_source` uses `os.path.samefile` so factory symlink paths resolve to canonical inode.

## Gotchas & dead ends
- workflows (author-asset, ship-version) have no `description:` frontmatter → catalog shows their
  H1 (the stem) as the description via the fallback. Acceptable; could add descriptions later.

## State at end
- Verified: catalog --check=0 both trees; --on-edit rebuilds on SKILL.md, no-ops on non-source;
  staleness → --check=1 + --warn-if-stale warns/0; factory catalog correctly lists symlinked
  operational assets + meta-skills (proves symlink traversal); build-hooks --check=0 both trees;
  settings.json valid JSON with catalog hooks merged. Branch `claude/capability-catalog` off main.

## Open threads
- Not yet committed/pushed/PR'd at time of writing (next step).
- Optional later: give author-asset/ship-version workflows a `description:` so the catalog line is
  meaningful; consider a one-line note in the factory root CLAUDE.md about the per-tree CATALOG.md.
