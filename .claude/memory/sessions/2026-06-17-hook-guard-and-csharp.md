# 2026-06-17 · hook-guard-and-csharp

**Goal:** Close the three open items — wire a drift guard for the generated
settings.json, decide/repoint the coding-standards skill's languages, and commit the
backlog in logical splits.

## What happened
- **Drift guard (item 3).** Added two more hook fragments that keep the generated
  `settings.json` in sync automatically:
  - `post-tool-use-build.json` → `build-hooks.py --on-edit`: PostToolUse (Edit/Write/
    MultiEdit) regenerates settings.json whenever Claude edits a `*.json` fragment.
  - `session-start-hooks-check.json` → `build-hooks.py --warn-if-stale`: SessionStart
    prints an in-context warning if settings.json is stale (catches manual/IDE edits),
    never blocks.
  - `build-hooks.py` gained `--warn-if-stale` and `--on-edit` modes; `--check` stays
    for CI. Applied to factory + example-project.
- **coding-standards (item 1).** Decided **Python + C#** (example-project's real
  VSTO/.NET + Python stack); replaced all TypeScript examples with idiomatic C#
  (records + `with`, `Task.WhenAll`, nullable reference types, DataAnnotations, XML
  doc comments, `Lazy<T>`/`yield`, xUnit `[Fact]`/`[Theory]`, pattern-matching guard
  clauses).
- **Commits (item 2).** Split the backlog into logical commits on a new branch.

## Gotchas & dead ends
- **`is_fragment` path equality was brittle.** Comparing `Path(file_path).resolve().parent`
  to `hooks_dir().resolve()` by `==` failed across path formats (MSYS `/c/Users/…` vs
  Windows `C:\Users\…`) in testing. Switched to **`os.path.samefile(p.parent, hooks_dir())`**
  — OS file identity, immune to drive-letter/slash/case differences. Production passes
  consistent Windows paths, but samefile is the robust choice regardless.
- **New hooks only load at session start.** Adding the two guard fragments this session
  doesn't activate them until next session, so the rebuild had to be run manually now.

## State at end
- Hooks self-maintaining (auto-rebuild on Claude edits + staleness warn). Both
  projects' settings.json in sync (`--check` green). coding-standards is Python + C#.

## Open threads
- None new. Drift is now guarded; the TS-vs-stack question is resolved.
