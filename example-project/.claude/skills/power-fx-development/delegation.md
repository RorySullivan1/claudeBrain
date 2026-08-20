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
| `IsBlank` inside a predicate | **No** on Text/Complex | `Filter(l, IsBlank(x))` → `Filter(l, x = Blank())` delegates for `=` **on simple columns only** (Text/Number/Date/Bool); a Person/Lookup/Choice root does **not** — flag those with a maintained Boolean. |
| `EndsWith` | **No** | No SharePoint equivalent. |
| `in` / `exactin` | **No** | `exactin` is documented as non-delegable everywhere; `in` is *absent from* SharePoint's delegable-operations table rather than explicitly excluded (omission, checked 2026-08-15) — treat as non-delegable. Rewrite to `Or`/`=` chain or `StartsWith`. |
| `Sum` `Average` `Min` `Max` `StdevP` `VarP` | **No** | Aggregates don't delegate to SharePoint → wrong totals past the limit. |
| `CountRows` `CountIf` | **No** | Only counts what was pulled locally (≤ limit). |
| `Concat` `GroupBy` `Distinct` `Ungroup` | **No** | Operate locally on the pulled page. |
| `FirstN` `Last` `LastN` | **No** | Pull the local page first. |
| `First` | **Delegable** (per source) | MS Learn lists `First` among the delegable filter functions; SharePoint-specific behaviour is undocumented, so verify before relying on it at scale. |
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
| Blank check (simple column) | `Filter(l, IsBlank(DueDate))` | `Filter(l, DueDate = Blank())` — `= Blank()` delegates on Text/Number/Date/Bool (MS Learn states the rewrite; the simple-vs-complex restriction is *field-observed*, not doc-stated — checked 2026-08-15). **A Person/Lookup/Choice column does NOT** — maintain a Boolean flag (see the row below). |
| "Is not blank" | `Filter(l, !IsBlank(Owner))` | No delegable form via `<>`; add/maintain a Boolean flag column, or filter locally on a pre-narrowed set. |
| Top N newest | `FirstN(Sort(l, Created, Descending), 20)` | `FirstN(...)` is local, but `Sort(...)` on a DateTime **delegates** — so the sort runs server-side and `FirstN` trims the returned page. Keep the delegable sort inside. |
| Ordering on a Text column | `Sort(l, Title)` then `<`/`>` filters | Sort on Text delegates; the relational **filter** on Text does not. Filter on a Number/DateTime column instead, or narrow server-side then refine locally. |
| "Children of MY parents" (fan-out) | `Filter(children, parent_id.Id in colMyParents.ID)` | **`in` against a collection does not delegate — it caps at the row limit and UNDERCOUNTS SILENTLY.** Run one delegable round trip per parent instead: `Sum( ForAll(colMyParents As p, CountRows(Filter(children, parent_id.Id = p.ID))), Value )` — the single-value ForAll result is a one-column table named `Value` (MS Learn). Cost scales with the number of parents, not the child list — check that trade first. |
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

## 6. When reasoning runs out: LIVE MONITOR is the positive test

§5's warning is a **one-way signal** and Microsoft says so outright:

> A delegation warning often appears in the formula bar as a yellow triangle when Power Apps
> can't push a formula operation to the data source, **but not every nondelegable case shows
> this warning.**
> — MS Learn, *Understand data sources for canvas apps*

So "no underline" is not evidence of delegation, and on a small list it is nearly meaningless.
The documented tool for exactly this is **Live Monitor**:

> To troubleshoot delegation issues that aren't flagged, use Live Monitor under **Advanced
> tools** to inspect the queries Power Apps sends and the data returned from each data source.

**The procedure — the only way to actually settle a delegation question, and the only one
that yields evidence someone else can read back in a sentence:**

1. Studio → **Advanced tools** → **Monitor**. Play the app; events stream live.
2. Do the one thing under test (open the screen, type in the search box).
3. Find the **`getRows`** event for the list. Select it to see the data source, timing, result
   and the formula that caused it.
4. **Delegated:** a small number of `getRows`, each returning a page of already-filtered rows.
   **Not delegated:** *repeated* `getRows` walking the list, then filtering on the client —
   "look for repeated `getRows` calls; these calls might indicate a nondelegable formula."

Pair it with **Settings → General → Data row limit = 1** when you want the failure to be
loud: anything non-delegable then returns a single record, which is impossible to miss.

**Ask for the `getRows` count, not for "did it work".** A non-delegable query looks completely
correct on a small list — that is the entire danger — so "it works" is not an answer to a
delegation question, and neither is a screenshot of the gallery.

### A Monitor-verified result: composing over a named formula folds

**Nesting a `Filter` over a named formula that is itself a `Filter` DOES fold into one server
query.** Verified by Live Monitor on `Filter(ActiveProjects, StartsWith(project_name, …))`,
where `ActiveProjects` is an `App.Formulas` filter over the list — one `getRows`, returning
already-filtered rows. So a named formula is a safe place to put a shared predicate.

Two caveats the verification does **not** cover:

- It proved **one** level of composition. A named formula defined over another named formula
  is two, and is not evidence-backed — write the predicate out rather than layering.
- It says nothing about which queries *should* use a shared set. A query already scoped to one
  parent usually should not: it is bounded anyway, and the shared filter can hide rows the
  caller needs. The worst version is a maintenance routine that must read *every* child,
  including the ones it is about to change — filtering there makes it skip exactly its own
  work.
