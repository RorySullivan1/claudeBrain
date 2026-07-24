# Power Fx → SharePoint delegation reference

The full matrix of what delegates to a **SharePoint list** data source, and how to
rewrite what doesn't. The `power-fx-development` SKILL.md teaches the method; this file
is the lookup table. Grounded on Microsoft Learn: *Connect to SharePoint from a canvas
app → Power Apps delegable functions and operations for SharePoint* and *Understand
delegation in a canvas app*.

> **The golden rule.** Delegation is **all-or-nothing per query.** If *any* part of a
> Filter/LookUp/Sort expression is non-delegable, Power Apps delegates **none** of it and
> falls back to pulling the first *data-row-limit* records (default **500**, max **2000**)
> to the device, then evaluating locally. One non-delegable clause poisons the whole query.

---

## 1. Operators — SharePoint

| Operator | Number | Text | Boolean | DateTime | Complex [c] |
|---|---|---|---|---|---|
| `=` | Yes | Yes | Yes | Yes | Yes |
| `<` `<=` `<>` `>` `>=` | Yes [id] | **No** | **No** | Yes | Yes |
| `&&` / `And`, `\|\|` / `Or` | delegable if both operands are | | | | |
| `!` / `Not` | **Never delegates** — rewrite to avoid | | | | |
| `in` (membership) | **Never delegates** to SharePoint | | | | |
| `exactin` | **Never delegates** | | | | |

- **[id]** A SharePoint **ID** column shows as a Number in Power Apps but is really Text.
  Only `=` delegates on ID; the relational operators (`<`, `>`, …) do **not**.
- **[c] Complex** = Choice, Lookup, Person, Managed Metadata. SharePoint defers the
  delegation decision to the **subfield** you touch — look that subfield's type up in this
  same table. For **Person**, only `Email` and `DisplayName` are delegable subfields.
- Text columns delegate **only `=`** — no `<`/`>` ordering, no `<>`.

## 2. Functions — SharePoint

| Function | Delegates? | Notes |
|---|---|---|
| `Filter` | **Yes** | …if its predicate is fully delegable (see operators + below). |
| `LookUp` | **Yes** | Same predicate rules as Filter; returns one record. |
| `Sort` / `SortByColumns` | **Yes** (Number/Text/Bool/DateTime) | **Not** on Complex-type columns. |
| `StartsWith` | **Yes** (Text) | **Not** on subfields of Choice/Lookup complex types. |
| `Search` | **No** | Substring/"contains" match — never delegates. See rewrite §4. |
| `IsBlank` inside a predicate | **No** on Text/Complex | `Filter(l, IsBlank(x))` → `Filter(l, x = Blank())` delegates (for `=` only, not `<>`). |
| `EndsWith` | **No** | No SharePoint equivalent. |
| `in` / `exactin` | **No** | Rewrite to `Or`/`=` chain or `StartsWith`. |
| `Sum` `Average` `Min` `Max` `StdevP` `VarP` | **No** | Aggregates don't delegate to SharePoint → wrong totals past the limit. |
| `CountRows` `CountIf` | **No** | Only counts what was pulled locally (≤ limit). |
| `Concat` `GroupBy` `Distinct` `Ungroup` | **No** | Operate locally on the pulled page. |
| `First` `FirstN` `Last` `LastN` | **No** | Pull the local page first. |
| `Skip` | **No** | Silently ignored on SharePoint — breaks pagination. |
| `AddColumns` `DropColumns` `ShowColumns` `RenameColumns` | pass-through | The inner Filter can delegate, but the **output** is still capped at the limit. |
| `UpdateIf` / `RemoveIf` | **Simulated** | Work locally but iterate in 500/2000 batches; correct only if the matching set fits. Prefer explicit `Patch`/`Remove` on known records. |

**System columns never delegate** — filtering/sorting on any of these forces local eval:
`ID`(relational only), `IsFolder`, `Thumbnail`, `Link`, `Name`, `FilenameWithExtension`,
`Path`, `FullPath`, `ModerationStatus`, `ModerationComment`, `ContentType`, `IsCheckedOut`,
`VersionNumber`.

## 3. The data-row-limit

| Setting | Value |
|---|---|
| Default non-delegable page size | **500** records |
| Max (Settings → General → **Data row limit**) | **2000** records |
| Recommended while testing | **1** — makes any silent non-delegation obvious immediately |

Raising the limit is a **band-aid, not a fix**: it slows the app (more rows over the wire,
worse on wide tables) and still fails the moment the list exceeds 2000. Fix delegation
instead. The limit only matters when a query is non-delegable *and* the list can grow past
it — small static lists (< 500) are safe with any formula.

## 4. Non-delegable → delegable rewrites

| Non-delegable intent | Don't write | Write instead |
|---|---|---|
| "Contains" text search | `Search(Tasks, txt.Text, "Title")` | `Filter(Tasks, StartsWith(Title, txt.Text))` — prefix match delegates. True substring can't delegate; index/redesign or accept prefix. |
| Match any of N values | `Filter(Orders, Status in tblStatuses)` | `Filter(Orders, Status = "New" \|\| Status = "Open" \|\| Status = "Held")` — explicit `Or` of `=` delegates. |
| "Not equal to X" on Text | `Filter(l, Category <> "Archived")` | Add a Boolean `IsArchived` column and `Filter(l, IsArchived = false)`. Text `<>` doesn't delegate. |
| Blank check | `Filter(l, IsBlank(Owner))` | `Filter(l, Owner = Blank())` — delegates for `=`. |
| "Is not blank" | `Filter(l, !IsBlank(Owner))` | No delegable form via `<>`; add/maintain a Boolean flag column, or filter locally on a pre-narrowed set. |
| Top N newest | `FirstN(Sort(l, Created, Descending), 20)` | `FirstN(...)` is local, but `Sort(...)` on a DateTime **delegates** — so the sort runs server-side and `FirstN` trims the returned page. Keep the delegable sort inside. |
| Ordering on a Text column | `Sort(l, Title)` then `<`/`>` filters | Sort on Text delegates; the relational **filter** on Text does not. Filter on a Number/DateTime column instead, or narrow server-side then refine locally. |
| Count of matches | `CountRows(Filter(BigList, Status="Open"))` | No delegable count on SharePoint. Maintain a rollup, use Daverse, or accept an approximate/capped count and label it as such. |

**Choice/Lookup columns:** filter on the delegable subfield with `=`, e.g.
`Filter(Projects, Status.Value = "Active")`. `StartsWith` on a Choice subfield does **not**
delegate — reserve `StartsWith` for plain Text columns.

## 5. How to read the editor's signal

- A **blue underline** (wavy) under part of a formula = "this won't delegate." Hover for
  the exact clause. The **App checker** (and a warning triangle) aggregates these.
- The warning fires only when the source *could* exceed the limit; a tiny list may not warn
  even though the formula is technically non-delegable. Don't rely on the absence of a
  warning — reason about the operator/function against §1–§2.
- Delegable **data sources** differ: Dataverse and SQL delegate more (e.g. `in` on SQL as
  `("val" in col)`, aggregates on Dataverse to 50k). This file is **SharePoint-specific** —
  moving the backend changes the matrix.
