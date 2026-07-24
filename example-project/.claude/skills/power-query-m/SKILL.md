---
name: power-query-m
description: >
  Expert at Power Query and the M language — the ETL layer that shapes, cleans, and
  combines data before it lands in the Power BI (or Excel) model. Use this skill whenever
  the user connects Power BI to a SharePoint list or file, imports and transforms/cleans
  source data, needs a query to fold for faster refresh, unpivots or pivots, merges or
  appends queries, expands a lookup/person/choice column, parameterizes a source, writes a
  custom M function, or sets up incremental refresh. Trigger on "Power Query", "M code",
  "connect Power BI to SharePoint list", "SharePoint.Tables / SharePoint.Contents",
  "query folding", "View Native Query", "unpivot", "merge queries", "append", "expand
  column", "the query is slow to refresh", "reduce refresh time", "Table.SelectRows",
  "RangeStart / RangeEnd", or a pasted `let … in` expression. Implicit signals: a report
  refresh takes forever, a lookup column shows `[Record]` or `[Table]`, column internal
  names differ from display names, or data arrives tall-and-narrow and needs reshaping.
  Boundaries — for calculations, measures, and columns computed AFTER the data loads
  (DAX / the model) use power-bi-dax; for designing the source list's schema, columns,
  and content types use sharepoint-list-architecture; for JSON column/view formatting use
  sharepoint-column-formatting; for reaching the data programmatically as an alternative
  to the connector use graph-api-integration. Power Fx is a different language entirely —
  for it use power-fx-development, power-fx-review, or power-apps-components.
---

# Power Query / M Skill

You shape data with Power Query and the M language so that a clean, correctly-typed,
minimal table lands in the model — and you do it in a way that **folds** back to the
source so refreshes stay fast. Lead with the answer, state your assumptions (source,
refresh mode, volume) up front, and prefer the smallest correct change to an applied-step
chain.

## Core principles

1. **Fold as much as possible.** Query folding is when Power Query translates your steps
   into a single native request the source executes (SQL, OData, SharePoint REST). Folded
   work happens *at the source* over the full dataset; unfolded work pulls everything down
   and grinds through it in the mashup engine. Folding is the single biggest lever on
   refresh time. Preserve it.
2. **Shape early.** Foldable, payload-reducing steps go first: filter rows, remove
   columns, then set types. Anything that breaks folding goes last, so the maximum amount
   of work still folds ahead of it.
3. **Types first, and explicitly.** Set the right data type on every column you keep. Many
   transforms and type-specific filters are only available on correctly-typed columns, and
   a wrong type discovered at row 201 (Power Query infers from the first 200 rows) is a
   silent data bug.
4. **M is case-sensitive and functional.** `Table.SelectRows` ≠ `table.selectrows`;
   `RangeStart` ≠ `rangestart`. Every step is an immutable expression bound to a name in a
   `let … in` block; there is no mutation, only new tables derived from prior ones. Never
   invent function names — if unsure a function exists, say so.

---

## First — clarify before shaping

Ask **one** targeted question when any of these is unknown; the answer changes the whole approach:

| Unknown | Ask | Why it matters |
|---|---|---|
| Source | "Where does the data live — a SharePoint list, files in a library, a database, an API?" | Picks the connector and whether folding is even possible |
| Refresh mode | "Import, DirectQuery, or Dual?" | DirectQuery/Dual **require** folding; Import merely benefits from it |
| Volume & growth | "Roughly how many rows, and does it grow daily?" | Large + growing → design for folding and consider incremental refresh |
| Grain / reshape | "Is the data already one-row-per-fact, or does it need unpivoting/grouping?" | Decides unpivot / group / pivot steps |
| Model shape | "One flat table, or a star schema of fact + dimension queries?" | Affects merges, references, and what hands off to the model |

State assumptions at the top:
```
// Source: SharePoint Online list "Projects" on the Delivery site; Import mode; ~40k rows, grows daily
```

---

## Connecting to SharePoint

### Pick the connector — and use the SITE url, not the list url

The **SharePoint Online list** connector is backed by two M functions. Both take the
**site** URL (`https://contoso.sharepoint.com/sites/Delivery`) — *not* the list's own
page URL. Pasting the list URL is the most common connection mistake.

| Need | Function | Notes |
|---|---|---|
| Rows of a SharePoint **list** | `SharePoint.Tables(siteUrl, options)` | The list connector. Returns a table of the site's lists; drill into the one you want. |
| Navigate a site's folders/files | `SharePoint.Contents(siteUrl, options)` | Folder-style navigation of documents. |
| Flat view of **files** in a library | `SharePoint.Files(siteUrl, options)` | Every file under the site; for combining workbooks/CSVs, not list rows. |

For list data, prefer `SharePoint.Tables`. Key options (a record passed as the 2nd arg):

- `[Implementation = "2.0"]` — use the **v2.0** connector. It has improved APIs and better
  usability and has been GA since 2022; prefer it for new work. (It isn't backwards
  compatible with 1.0, so don't flip it on an existing query without re-checking columns.)
- `[ViewMode = "All"]` vs `"Default"` — **v2.0 only.** `"All"` returns every user and
  system column; `"Default"` returns only what the list's default view shows. (Beware: if
  the default view is Calendar or Board, SharePoint returns only that view's columns even
  under `"All"`.)
- `[ApiVersion = "Auto"]` — needed for some sites; non-English sites require API version 15.

```m
let
    Source   = SharePoint.Tables("https://contoso.sharepoint.com/sites/Delivery",
                   [Implementation = "2.0", ViewMode = "All"]),
    Projects = Source{[Title = "Projects"]}[Items]   // drill into the list by name
in
    Projects
```

### The internal-name and lookup-column traps

- **Internal names ≠ display names.** SharePoint stores fields under internal names
  (`Title`, `OData__x0020_Owner`, `field_3`) that differ from the friendly display name.
  The v2.0 connector surfaces display names better, but when a column reference errors,
  suspect an internal name. Rename to a stable friendly name in an early step and reference
  *that* downstream.
- **Lookup / Person / Managed-metadata columns arrive as nested `[Record]` or `[Table]`
  values,** not scalars — that's why a column shows `[Record]` instead of a name. You must
  **expand** them to pull out the scalar you want (`.Title` / `.Value` / `.lookupValue`
  depending on column kind):

```m
    // Owner is a Person column → expand the nested record, keep just the display name
    Expanded = Table.ExpandRecordColumn(Projects, "Owner", {"Title"}, {"OwnerName"})
```

Reduce columns **before** expanding — expanding a wide lookup pulls extra fields you'll
only discard.

---

## Query folding — what it is and how to keep it

**Why it matters:** a fully-folded query sends one native request and the source returns
only the filtered, trimmed result. An unfolded step forces Power Query to download the
whole table and process it locally — the usual cause of "the query is slow to refresh."

**How to check it:**
- **View Native Query** — right-click the last applied step. If it's enabled, the query
  folds up to that step; the dialog shows the exact native request. If it's greyed out on a
  source that normally supports it, that step broke folding.
- **Query folding indicators** on the applied-steps pane, and the **Query plan** dialog.
  In the plan, only `Value.NativeQuery` and data-source nodes are "folded (remote)"; every
  other node ran locally. Fewer local nodes = better.

**How to preserve it — step order is the lever:**

| Do early (folds, shrinks payload) | Do late (often breaks folding) |
|---|---|
| Filter rows (`Table.SelectRows`) | Add custom columns with complex M / `Table.AddColumn` |
| Remove/choose columns (`Table.SelectColumns`) | Anything invoking a custom function per row |
| Set data types | Merges against non-foldable sources; certain fuzzy/pivot ops |
| Rename columns | Steps after the first non-folding step (folding stops there for good) |

Put the folding-breaker as late as you can, so everything upstream still folds. Power
Query's engine may reorder steps to maximize folding, but don't rely on it — sequence
deliberately.

**Where folding breaks against SharePoint:** the SharePoint list connector supports only
**partial** folding — it can push some filters and column selections to the SharePoint
REST/OData endpoint, but many transforms (and often **View Native Query** itself) aren't
available. Don't assume a SharePoint query folds the way a SQL one does; lean on the
**folding indicators** and keep filters/column-removal as the very first steps to push down
what you can. For the fullest control, reduce with `[ViewMode="Default"]` or a
purpose-built list view at the source.

> `Table.Buffer` reads a table fully into memory and **stops all downstream folding** —
> use it only to isolate data from change or to force a one-time read, never as a reflex.
> If you merely want to stop folding (e.g. to pin a plan) without the memory cost, use
> `Table.StopFolding`.

---

## The transform workflow

Order your applied steps to fold first and reshape last:

1. **Source** — connect (site URL, right connector/options).
2. **Filter rows early** — drop rows you'll never use (`Table.SelectRows`). Filtering
   early both folds and shrinks every downstream step.
3. **Remove columns early** — keep only what the model needs (`Table.SelectColumns` /
   "Choose Columns"). Retrieving all columns is an anti-pattern; trimming early lets the
   source avoid extracting data only to discard it.
4. **Set data types** — one `Table.TransformColumnTypes` covering every kept column.
5. **Expand** lookup/person records now that the table is narrow.
6. **Reshape** — unpivot (`Table.UnpivotOtherColumns` for a dynamic column set), pivot,
   or group (`Table.Group`).
7. **Combine** — merge or append (below).
8. **Rename** to model-friendly names as the last cosmetic step.

### Merge (join) vs. append (stack)

- **Merge** = a **join**: add columns from another query by matching key(s), then expand
  the resulting nested table column. Use for lookups and star-schema keys.

  ```m
    Merged   = Table.NestedJoin(Fact, {"OwnerId"}, DimPeople, {"Id"}, "People", JoinKind.LeftOuter),
    AddName  = Table.ExpandTableColumn(Merged, "People", {"FullName"}, {"OwnerName"})
  ```

  `JoinKind` values: `Inner`, `LeftOuter`, `RightOuter`, `FullOuter`, `LeftAnti`,
  `RightAnti`. Default (omit the arg) is `LeftOuter`.

- **Append** = a **union**: stack rows of queries with the same shape
  (`Table.Combine({Q1, Q2})`). Use to concatenate this-year + last-year, or many identical
  files. Mismatched column names produce nulls, not errors — align names first.

> Sorting is **not preserved** through `Table.Group`, `Table.NestedJoin`, or
> `Table.Distinct`. If you need the top row per group, rank or sort *inside* the grouped
> table — don't sort upstream and hope it survives.

### Parameters and custom functions

- **Parameters** externalize values that change per environment (a site URL, an
  environment name) — define once via Manage Parameters, reference by name. This keeps a
  query portable between dev and prod without editing steps.
- **Custom M functions** factor a repeated transform. A function is just a `let` that
  returns `(x) => …`; invoke it per file when combining a folder, or per row via
  `Table.AddColumn`. Note that a per-row custom function usually **breaks folding** — keep
  it after the foldable steps.

---

## Worked examples

### 1. Connect to a list and expand a Person lookup — fold-friendly order

```m
let
    Source    = SharePoint.Tables(
                    "https://contoso.sharepoint.com/sites/Delivery",
                    [Implementation = "2.0", ViewMode = "All"]),
    Projects  = Source{[Title = "Projects"]}[Items],

    // 1) filter early (pushes down where SharePoint allows)
    Active    = Table.SelectRows(Projects, each [Status] <> "Archived"),

    // 2) remove columns early — narrow the payload before expanding
    Kept      = Table.SelectColumns(Active,
                    {"Title", "Status", "DueDate", "Owner", "Region"}),

    // 3) types
    Typed     = Table.TransformColumnTypes(Kept, {
                    {"Title", type text}, {"Status", type text},
                    {"DueDate", type date}, {"Region", type text}}),

    // 4) expand the Person column's nested record → scalar display name
    Expanded  = Table.ExpandRecordColumn(Typed, "Owner", {"Title"}, {"OwnerName"}),

    // 5) final rename for the model
    Renamed   = Table.RenameColumns(Expanded, {{"Title", "ProjectName"}})
in
    Renamed
```

### 2. Fold-preserving filter → remove-columns → typed sequence

Keep the payload-reducing, foldable steps first and contiguous, so the source does the
heavy lifting and *nothing local* runs before them:

```m
let
    Source   = Sql.Database("srv", "Sales"),
    Orders   = Source{[Schema = "dbo", Item = "Orders"]}[Data],
    Filtered = Table.SelectRows(Orders, each [OrderDate] >= #date(2024,1,1)),  // folds
    Trimmed  = Table.SelectColumns(Filtered, {"OrderId","OrderDate","CustomerId","Amount"}), // folds
    Typed    = Table.TransformColumnTypes(Trimmed, {
                   {"OrderId", Int64.Type}, {"OrderDate", type date},
                   {"CustomerId", Int64.Type}, {"Amount", Currency.Type}})       // folds
in
    Typed   // right-click this step → View Native Query should be enabled
```

### 3. Merge a fact query with a dimension, then expand

```m
let
    Fact    = #"Orders Typed",
    Dim     = #"Customers Typed",
    Joined  = Table.NestedJoin(Fact, {"CustomerId"}, Dim, {"CustomerId"},
                  "Cust", JoinKind.LeftOuter),
    WithSeg = Table.ExpandTableColumn(Joined, "Cust", {"Segment"}, {"CustomerSegment"})
in
    WithSeg
```

### 4. Incremental refresh skeleton (large, growing sources)

Create two reserved, **case-sensitive** Date/Time parameters `RangeStart` and `RangeEnd`,
then filter the date column against them in a single foldable step:

```m
    Filtered = Table.SelectRows(Source,
                   each [Modified] >= RangeStart and [Modified] < RangeEnd)
```

Put exactly one boundary as `>=`/`<` (not `<=` on both) so a row can't fall into two
partitions and duplicate. The filter **must fold in one query** or incremental refresh
degrades to a full pull — verify with the folding indicators before defining the policy.

---

## The hand-off to the model

Power Query's job ends when a clean, typed, minimal table lands in the model. From there
the **model** takes over: relationships between your fact and dimension queries, and
calculations. Do **not** try to compute cross-row business logic (running totals,
year-over-year, ranked measures) in M — that belongs in **DAX measures and calculated
columns after load** (`power-bi-dax`). A good rule: M reshapes and reduces *rows and
columns*; DAX computes *values over the loaded model*. Shape a star schema in Power Query;
calculate over it in DAX.

---

## Watch Out

1. **Site URL vs. list URL.** `SharePoint.Tables`/`SharePoint.Contents` take the **site**
   URL and you drill to the list. Pasting the list's page URL is the classic failure —
   the connector can't resolve it.
2. **`[Record]`/`[Table]` in a column means you didn't expand it.** Lookup, Person, and
   managed-metadata columns are nested. Expand to `.Title`/`.Value`; and trim columns
   *before* expanding so you don't pull fields you'll drop.
3. **One non-folding step poisons everything after it.** Once folding stops, every later
   step runs locally. Sequence deliberately (filter/remove/type first), and re-check **View
   Native Query** / the folding indicators after adding a step — especially on SharePoint,
   where folding is only partial.
4. **Case-sensitivity and reserved names.** M is case-sensitive; `RangeStart`/`RangeEnd`
   must be spelled exactly, be Date/Time, and be used with a single-sided equality — or
   incremental refresh duplicates rows or fails to fold.

---

## Out of scope — defer to the sibling skill

- **Calculations, measures, calculated columns — anything computed after the data loads** →
  `power-bi-dax`.
- **Designing the source list's schema, columns, content types, or views** →
  `sharepoint-list-architecture` (this skill *consumes* that list, it doesn't design it).
- **JSON column/view formatting on the list itself** → `sharepoint-column-formatting`.
- **Reaching the same data programmatically via the Graph API** (an alternative to the
  connector) → `graph-api-integration`.
- **Power Fx / canvas apps** — a different language and runtime → `power-fx-development`,
  `power-fx-review`, `power-apps-components`.
