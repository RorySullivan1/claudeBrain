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
   pattern is a bulk `Patch` of a shaped table:
   Two documented shapes exist (MS Learn, *Patch function* + *Create or update bulk records*),
   and which one you want depends on whether the save mixes creates with updates:

   **Updates only → one bulk call.** `Patch( DataSource, Collection )` is the documented bulk
   form — records shaped to match the source, each carrying its primary key. ForAll only
   SHAPES here; the single Patch is the only write:
   ```power
   Patch( Source,
       ForAll( Filter(Gallery.AllItems, ID > 0) As row,
           { ID: row.ID, Field: row.txtField.Text } ) );
   ```
   (The pairwise 3-arg form — `Patch(DS, BaseRecordsTable, ChangeRecordTable)`, tables matched
   one-for-one — is the other documented bulk shape, including bulk *creates* via a base table
   of `Defaults(DS)` records.)

   **Mixed update + create harvested from controls → one Patch per row inside ForAll.** This
   is the pattern MS Learn itself gives for joining control values to source records:
   ```power
   ForAll( Gallery.AllItems As row,
       If( row.ID > 0,
           Patch(Source, LookUp(Source, ID = row.ID), { Field: row.txtField.Text }),
           Patch(Source, Defaults(Source), { Field: row.txtField.Text })
       )
   );
   ```
   It fires one request per row — accept that cost for the mixed case, or split the save into
   a bulk-update call plus a bulk-create call if the grid is large.

   Two shape facts both prior versions of this section got wrong at least once: with `As row`,
   **the alias IS the record** — read `row.ID` / `row.txtField.Text`; there is no `.ThisItem`
   member on an `AllItems` row. And tables are perfectly valid Patch arguments — both bulk
   forms take them — so don't avoid the bulk shapes for that reason; what you must not do is
   wrap per-row *writes* (3-arg Patches) inside another Patch, which double-writes.
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
    // One bulk write: shape the checked rows into ID-keyed records, Patch the table once.
    Patch( Training,
        ForAll(
            Filter(Gallery2.AllItems, Toggle1.Value = true) As r,
            { ID: r.ID, Status: {Value: "Complete"}, CompletedOn: Today() }
        )
    ),
    Notify("Some rows failed to save: " & FirstError.Message, NotificationType.Error),
    Notify("Saved.", NotificationType.Success)
);
ClearCollect(colTraining, Filter(Training, AssignedTo.Email = gUserEmail))
```

The shaped records carry `ID`, so the single `Patch` updates the **existing** rows (an ID-keyed
record targets its source record; no `Defaults` merge), and the whole checked set goes out in
one call.

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
- **The source list's columns, keys, and indexing** → `sharepoint-list-architecture`. (On a
  SharePoint backend, keys come from the built-in `ID` assigned on insert — there is no atomic
  increment, so a client-generated key needs a second write.)
