---
name: power-apps-editable-table
description: >
  Expert at building an editable table / spreadsheet-style grid in a canvas Power App —
  a collection-backed gallery with per-row inputs, add/insert/delete rows, and a single
  bulk save back to the data source. Use this skill whenever the user wants users to edit
  many rows at once rather than one form at a time: "editable grid", "editable gallery",
  "spreadsheet in Power Apps", "bulk edit rows", "add a row / delete a row in a gallery",
  "enter multiple line items", "timesheet grid", "save all rows at once", "inline edit
  table", "data table but editable", or "Patch a whole gallery". Trigger on implicit
  signals: repeating line-item entry (order lines, timecard days, checklist), a DataTable
  that's read-only when they need edits, or a screen where a form-per-row is too slow.
  Boundary: this skill owns the editable-grid *pattern* — the staging collection, the
  per-row controls, and the bulk-write. The delegation rules and general Patch/Collect
  mechanics are power-fx-development (defer there for whether a query delegates); reusable
  component contracts, responsive layout, and non-editable gallery UI are
  power-apps-components; auditing an existing implementation is power-fx-review; the list
  schema behind it is sharepoint-list-architecture.
---

# Power Apps Editable Table Skill

Power Apps has **no native editable grid**. You build one from a **gallery bound to a staging
collection**: each row renders input controls, edits accumulate in the collection, and one
button writes the whole set back. Lead with the staging-collection design; keep every write
delegation-aware; and get the **`Defaults()` (new) vs `ThisRecord` (update)** distinction right —
it's the single most common bug in this pattern.

## Core principles

1. **Edit a collection, not the source.** Load a working copy into a collection, bind the gallery
   to *that*, and let users mutate it freely. The data source is touched only on **Save** — so
   there's no per-keystroke network chatter and edits are cancellable.
2. **The gallery is the grid; `ThisItem` is the row.** Per-row inputs default from
   `ThisItem.<field>`; the user's edits live in the input controls until you harvest them from
   `Gallery.AllItems` on save.
3. **One bulk write, not one-per-row.** Save with a single `Patch(Source, table)` where possible;
   a `ForAll(Gallery.AllItems, Patch(...))` fires **one request per row** — acceptable for modest
   counts, but never the default for large grids.
4. **`Defaults(Source)` creates; the record updates.** In a `Patch`, merge onto `Defaults(Source)`
   to **insert** a new row and onto the **existing record** to **update** it. Mixing these up
   either duplicates rows or fails silently.
5. **Delegation still applies to the load.** The initial `ClearCollect(col, Filter(Source, …))`
   must be delegable, or you stage only the first 500/2000 rows. (Delegation rules →
   `power-fx-development`.)

## The method

1. **Stage on screen entry.** `OnVisible`:
   ```power
   ClearCollect(colGrid, Filter(Source, ProjectId = gSel.ID));   // delegable load
   ```
   For a blank grid, `ClearCollect(colGrid, Blank()); Collect(colGrid, {TempId: 1, …defaults})`.
2. **Bind the gallery.** `Gallery.Items = colGrid`. In the template, per-column input controls
   `Default = ThisItem.<field>` (TextInput, Dropdown, DatePicker, etc.).
3. **Add / insert a row.** An add button `Collect(colGrid, { TempId: CountRows(colGrid)+1, …blank })`.
   Give new rows a client **TempId** so you can identify unsaved rows before they get a real `ID`.
4. **Delete a row.** A per-row trash icon `Remove(colGrid, ThisItem)`. If the row already exists
   in the source, also record it for deletion (a `colDeletes` collection) to remove on save.
5. **Harvest edits + save.** On Save, read the *current control values* per row. The robust
   pattern is a single `ForAll` pass with one `Patch` per row (update or create):
   ```power
   // Update existing + create new in one pass; split by whether the row has a real ID.
   // ForAll iterates and each row is written by its OWN Patch. Do NOT wrap this in an outer
   // Patch(Source, ForAll(...)) — ForAll returns a table, which is not a valid base record.
   // With `As row`, the alias IS the record: read columns/controls as row.ID / row.txtField.Text
   // (there is no `.ThisItem` on an AllItems row).
   ForAll( Gallery.AllItems As row,
       If( row.ID > 0,
           Patch(Source, LookUp(Source, ID = row.ID), { Field: row.txtField.Text }),
           // new row → merge onto Defaults(Source)
           Patch(Source, Defaults(Source), { Field: row.txtField.Text })
       )
   );
   ```
   Then reconcile deletes: `ForAll(colDeletes, Remove(Source, LookUp(Source, ID = ThisRecord.ID)))`,
   wrap in `IfError`, and `Notify` success/failure.
6. **Refresh + confirm.** Re-`ClearCollect` from the source so server-assigned `ID`s/keys appear,
   and surface the result.

## Worked example — a per-row toggle → bulk update

Update only the rows the user checked (April Dunnam's Required-Training pattern), one delegable
load, one write pass:

```power
// Gallery2.Items = colTraining  (loaded delegably in OnVisible)
// Each row: Toggle1 (Completed?), and displays ThisItem.CourseName

// Save button OnSelect:
IfError(
    ForAll(
        Filter(Gallery2.AllItems, Toggle1.Value = true) As r,
        Patch(Training, r, { Status: {Value: "Complete"}, CompletedOn: Today() })
    ),
    Notify("Some rows failed to save: " & FirstError.Message, NotificationType.Error),
    Notify("Saved.", NotificationType.Success)
);
ClearCollect(colTraining, Filter(Training, AssignedTo.Email = gUserEmail))
```

`Patch(Training, r, {...})` uses `r` — the gallery row bound by `As r` — directly as the base
record (there is no `.ThisItem` on an `AllItems` row; the alias *is* the record). It merges onto
the **existing** item, not `Defaults`, because these rows came from the source and carry their `ID`.

## Watch Out

1. **`Defaults()` vs `ThisRecord`.** Merging a *new* row onto the existing record (or an *update*
   onto `Defaults`) is the classic failure — duplicates or silent no-ops. Branch on `ID > 0`.
2. **`ForAll` is not a loop, and `Patch`-in-`ForAll` is one request per row.** For large grids
   this is slow and has no transaction — prefer a single `Patch(Source, tableOfRecords)` when the
   shape allows, and warn the user about partial-failure semantics.
3. **Reading stale values.** Harvest from the **control** (`row.txtField.Text`) or a
   two-way-bound collection — not from `ThisItem` alone if the input isn't writing back to the
   collection. Decide one source of truth per column.
4. **Non-delegable load.** If the `Filter` that stages the collection doesn't delegate, you edit
   only the first 500/2000 rows and silently drop the rest. Fix the load's delegation first.
5. **New rows have no `ID` until saved.** Use a client `TempId` to track/delete unsaved rows and
   to avoid `ID = Blank()` collisions; re-load after save to pick up real keys.
6. **Deletes need their own list.** `Remove` from the collection doesn't delete from the source —
   track removed existing rows and reconcile them on save.

## Out of scope — defer

- **Whether a query delegates**, and general `Patch`/`Collect`/`ForAll` mechanics →
  `power-fx-development` (matrix in its `delegation.md`); **auditing** an existing grid →
  `power-fx-review`.
- **Reusable component contracts, responsive layout, non-editable gallery/DataTable UI** →
  `power-apps-components`.
- **The source list's columns, keys, and indexing** → `sharepoint-list-architecture`. (On our
  SharePoint backend, keys come from the built-in `ID` in a second write — no atomic increment.)
