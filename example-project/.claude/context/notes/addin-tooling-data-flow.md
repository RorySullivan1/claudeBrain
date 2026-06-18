# Add-in ↔ Python tooling data flow
type: system-map
status: current

## What it is
How the two halves of example-project hand work to each other: the VSTO Excel add-in
(`src/AddIn/`, C#) is the user-facing surface, and the Python scripts (`tools/`) do data
prep and build/packaging. They are separate processes — the add-in does not import Python;
it shells out to the pinned interpreter and exchanges data over files.

## Key points
- The add-in invokes `tools/` scripts as a subprocess using the interpreter pinned in
  `tools/.python-version`; it does not embed or call Python in-process.
- Hand-off is **file-based**: the add-in writes inputs to a temp workbook/CSV, the script
  reads them, writes results back, and the add-in reloads — no shared memory or RPC.
- Packaging is one-directional: `tools/` builds and stages the ClickOnce payload the
  add-in ships in; the add-in never writes back into `tools/`.
- Because it's process-isolated, the Python layer is testable on its own (`pt` shortcut)
  without Office in the loop.

## Where it shows up / pointers
- `src/AddIn/` — the C# add-in (Ribbon UI + task panes) that triggers tooling.
- `tools/` — the Python data-prep and packaging scripts; `tools/.python-version` pins the interpreter.
- CLAUDE.md → Architecture and Constraints (ClickOnce deploy, no admin, pinned Python).

## Source
- 2026-06-18 (project architecture; example reference note)
