---
name: power-bi-dax
description: >
  Expert at DAX for Power BI — measures, evaluation context, and model
  calculations over a star-schema semantic model. Use this skill whenever the
  user needs to write or fix a DAX measure, build time intelligence (YoY,
  year-to-date, running total), compute a % of total or ranking, understand why
  a subtotal or grand total comes out wrong, reason about CALCULATE and filter
  context, or decide between a measure and a calculated column. Trigger on
  phrases like "write a DAX measure", "year over year in Power BI", "running
  total", "% of total", "CALCULATE", "why is my total wrong", "context
  transition", "measure vs calculated column", "ALL / ALLEXCEPT / ALLSELECTED",
  "SAMEPERIODLASTYEAR", or "my time intelligence returns blank". Implicit signals:
  the user pastes a measure that gives the right leaf value but a wrong total,
  asks why a number doesn't respond (or over-responds) to a slicer, or wants a
  calculation that compares periods. Boundary — this skill is the model layer
  only. Shaping, loading, merging, or cleaning data BEFORE it reaches the model
  is power-query-m; designing the source SharePoint list is
  sharepoint-list-architecture; Power Fx app formulas are a DIFFERENT language,
  use power-fx-development (and power-fx-review to review them). Canvas UI is
  power-apps-components; Graph calls are graph-api-integration.
---

# Power BI DAX Skill

You write DAX that is correct at every level of a report — not just the leaf
rows, but every subtotal and the grand total — and that stays fast on a real
model. Lead with the measure, state the model assumptions you're making, and
explain *why* a formula behaves the way it does, because in DAX the "why" is the
whole game.

**Baseline assumption:** a **star schema** — fact tables (Sales, Orders)
surrounded by dimension tables (Date, Product, Customer) joined on single-column
relationships, filters flowing from the one-side dimensions to the many-side
facts. If the user's model isn't shaped this way, say so early: most DAX pain is
really a modeling problem, and the fix is upstream (`power-query-m`), not a
cleverer measure.

## Core principles

1. **Default to a measure.** A measure is evaluated in the report's filter
   context at query time, aggregates dynamically, and costs no storage. Reach
   for a calculated column only for the narrow cases below.
2. **Understand the context before you write a line.** Every DAX value is
   produced in a context. Get the context wrong and the formula still returns a
   number — just the wrong one, usually visible only in totals. Name the context
   out loud before writing the expression.
3. **Prefer clearing/shaping filters over materializing rows.** `CALCULATE` with
   filter modifiers is almost always cheaper and more correct than iterating a
   physical table or storing a column.
4. **Make intent explicit with variables.** `VAR`/`RETURN` is not just tidy — it
   *freezes* a value in the context where it's declared, which is often the
   actual fix for a broken measure.

## First — clarify before writing

Ask **one** targeted question when any of these is unknown; a wrong assumption
here produces a confidently wrong measure.

| Unknown | Ask |
|---|---|
| Grain of the fact | "Is each row a line item, an order, or a daily snapshot?" — sets whether you sum a column or iterate |
| Date table | "Do you have a dedicated Date table marked as a date table?" — time intelligence is impossible without one |
| Desired filter behavior | "Should this respond to the slicers, or ignore some of them?" — decides which filters to keep vs. remove |
| Total behavior | "What should the grand total show?" — a ratio-of-sums vs. sum-of-ratios choice |
| Measure vs. column | "Does this need to slice dynamically (measure), or is it a fixed per-row attribute you'll group/filter by (column)?" |

State assumptions at the top of a measure:

```dax
// Assumes: star schema, 'Date' marked as a date table, Sales at line-item grain,
// [Total Sales] := SUM ( Sales[SalesAmount] ) already exists
```

---

## Measure vs. calculated column vs. calculated table

Default to a **measure**. Use the others only when their specific property is
required.

| You need… | Use | Why |
|---|---|---|
| A number that reacts to slicers, rows, filters | **Measure** | Evaluated in filter context at query time; no storage |
| A fixed per-row value you'll **slice by, filter on, or put on an axis** | **Calculated column** | Materialized per row, computed at refresh; can be a dimension key |
| A **derived table** (a bespoke Date table, a disconnected parameter table, a bridge) | **Calculated table** | Produces a whole table in the model |

A calculated column is justified when the value is genuinely a **row attribute** —
a bucket/segment used as a slicer, a concatenated key, a sort-order column — and
must exist independent of any report context. It is **not** justified for "a
number I want to show in a visual": that's a measure. Calculated columns cost
memory and refresh time and don't respond to the report, so an aggregation stored
as a column is almost always a mistake.

If the value could be produced upstream during data load, prefer a **Power Query**
column over a calculated column — it compresses better and keeps the model lean.
That's `power-query-m` territory.

---

## Evaluation context — the one thing to get right

DAX evaluates in two contexts that stack:

- **Row context** — "the current row." Exists automatically inside a calculated
  column and inside every **iterator** (`SUMX`, `FILTER`, …). Row context lets
  you read column values for *this* row. It does **not**, by itself, filter other
  tables or perform aggregation.
- **Filter context** — "the set of filters currently applied." Comes from the
  visual (rows, columns, slicers, the filter pane) and from `CALCULATE`. Filter
  context is what an aggregation like `SUM` actually sees.

The two are independent: a calculated column has row context but the *whole
table's* filter context, which is why `= SUM ( Sales[Amount] )` in a column
returns the grand total on every row — the row context does not filter the SUM.

### Context transition — the crux of CALCULATE

**`CALCULATE` turns the current row context into an equivalent filter context.**
This is *context transition*. It's why this calculated column works:

```dax
// Customer[LifetimeValue] — a calculated column
LifetimeValue = CALCULATE ( SUM ( Sales[SalesAmount] ) )
// CALCULATE transitions the current customer row into a filter,
// so the SUM sees only THIS customer's sales.
```

Two rules that resolve most confusion:

1. Inside an iterator, a bare aggregation (`SUM`) sees the **outer** filter
   context, ignoring the row being iterated. Wrap it in `CALCULATE` (or call a
   **measure** — measures carry an *automatic* context transition) to make it
   respect the current row.
2. Referencing a **measure** anywhere already implies `CALCULATE` around it.
   `[Total Sales]` inside `SUMX` is really `CALCULATE ( [Total Sales] )` per row.
   This is the single most useful fact about DAX.

---

## CALCULATE and filter modifiers

`CALCULATE ( <expression>, <filter1>, <filter2>, … )` evaluates the expression in
a filter context modified by each filter argument. Semantics that matter:

- A filter on a column **not** already in context is **added**. A filter on a
  column **already** in context **overwrites** it (unless wrapped in
  `KEEPFILTERS`).

| Modifier | Effect | Reach for it when |
|---|---|---|
| `ALL ( Table )` / `ALL ( Col )` | Remove filters from that table/column | Denominator for a % of total; ignore a slicer |
| `REMOVEFILTERS ( … )` | Same as ALL used as a modifier, clearer intent | Modern replacement for `ALL` when you only mean "clear filters" |
| `ALLEXCEPT ( Table, KeepCol… )` | Remove all filters on the table **except** the named columns | "Total within each category" — keep category, drop the rest |
| `ALLSELECTED ( … )` | Ignore filters from *inside* the visual, but **keep** outer slicers/filters | % of the **visible** total (respects slicers, ignores the axis) |
| `KEEPFILTERS ( <filter> )` | Add a filter **intersecting** the existing one instead of overwriting | Apply a condition without wiping the user's slicer on that column |
| `USERELATIONSHIP ( c1, c2 )` | Activate an **inactive** relationship for this evaluation | Ship-date vs. order-date analysis on the same Date table |

`ALL` vs. `ALLSELECTED` is the classic % choice: `ALL ( Product )` gives % of the
**grand** total (every product, always); `ALLSELECTED ( Product )` gives % of what
the user has **selected/filtered** — the total across the rows currently visible.

---

## Iterators — when a plain aggregate isn't enough

Aggregators (`SUM`, `AVERAGE`, `MAX`) take a single column. Use an **iterator**
(`SUMX`, `AVERAGEX`, `MAXX`, `MINX`, `COUNTX`) when the per-row value is an
**expression** that must be computed before aggregating.

```dax
// Row-by-row multiply, THEN sum — cannot be done with SUM of one column
Total Revenue = SUMX ( Sales, Sales[Quantity] * Sales[UnitPrice] )
```

Iterators establish row context, so a measure referenced inside one gets the
per-row context transition automatically. Don't reach for an iterator when a
plain `SUM` over a single (possibly precomputed) column would do — iterating a
large fact when you didn't need to is a common performance own-goal.

---

## Time intelligence — a marked Date table is a prerequisite

Time intelligence functions **require a dedicated Date table** that is **marked as
a date table**, with a Date-typed column of **unique values** and a **contiguous
(gap-free) date range** covering every date in the data. Never point time
intelligence at a datetime column on the fact table. If the model has no such
table, the honest answer is "build the Date table first" — that's the fix, not a
workaround.

| Pattern | Formula |
|---|---|
| Year-to-date | `TOTALYTD ( [Total Sales], 'Date'[Date] )` |
| YTD dates as a set (compose in CALCULATE) | `CALCULATE ( [Total Sales], DATESYTD ( 'Date'[Date] ) )` |
| Same period last year | `CALCULATE ( [Total Sales], SAMEPERIODLASTYEAR ( 'Date'[Date] ) )` |
| Shift by N intervals | `CALCULATE ( [Total Sales], DATEADD ( 'Date'[Date], -1, YEAR ) )` |

`SAMEPERIODLASTYEAR ( 'Date'[Date] )` is exactly `DATEADD ( 'Date'[Date], -1, YEAR )`.
Use `DATEADD` when you need a different offset (a month, a quarter, N years). A
fiscal year-end is a third argument on `TOTALYTD` (e.g. `"6/30"`).

---

## Variables — readability and freezing context

`VAR` evaluates **once**, in the context where it's declared, and is immutable
thereafter. That gives two wins: the expression reads top-to-bottom, and a value
captured *before* a `CALCULATE` changes the context is preserved.

```dax
Sales YoY % =
VAR CurrentSales = [Total Sales]
VAR PriorSales   = CALCULATE ( [Total Sales], SAMEPERIODLASTYEAR ( 'Date'[Date] ) )
RETURN
    DIVIDE ( CurrentSales - PriorSales, PriorSales )
```

Because `CurrentSales` is frozen before the `CALCULATE`, there's no risk of the
prior-year filter leaking into it. Prefer variables over repeating a subexpression
— repetition risks the two copies being evaluated in different contexts.

---

## Worked examples

### % of grand total

```dax
% of Total Sales =
VAR SalesInContext = [Total Sales]
VAR AllProductsSales = CALCULATE ( [Total Sales], ALL ( Product ) )
RETURN
    DIVIDE ( SalesInContext, AllProductsSales )
```

The numerator respects the current row (e.g. one product); the denominator clears
the Product filter with `ALL`, so it's the total across every product. Swap
`ALL ( Product )` for `ALLSELECTED ( Product )` to make the denominator the total
of the **currently visible/selected** products instead of the absolute grand total.

### Year-over-year %

```dax
Sales YoY % =
VAR CurrentSales = [Total Sales]
VAR PriorSales =
    CALCULATE ( [Total Sales], SAMEPERIODLASTYEAR ( 'Date'[Date] ) )
RETURN
    DIVIDE ( CurrentSales - PriorSales, PriorSales )
```

Requires the marked Date table. `DIVIDE` returns `BLANK()` (not an error) for the
first period, where there is no prior year — so that period simply drops out of
the visual instead of showing `Infinity`.

### Correct running total (cumulative to date)

```dax
Running Total Sales =
VAR LastVisibleDate = MAX ( 'Date'[Date] )
RETURN
    CALCULATE (
        [Total Sales],
        FILTER (
            ALL ( 'Date'[Date] ),          // clear the axis, keep other filters
            'Date'[Date] <= LastVisibleDate // then re-apply "up to this date"
        )
    )
```

`ALL ( 'Date'[Date] )` lifts the date filter the visual's axis imposes, then the
`FILTER` re-applies "every date on or before the current one." Capturing
`LastVisibleDate` in a variable *before* the `CALCULATE` is essential — inside the
`CALCULATE` the date context is gone. For a within-year reset, use
`DATESYTD ( 'Date'[Date] )` as the filter instead.

### Ranking

```dax
Product Rank =
RANKX ( ALL ( Product[ProductName] ), [Total Sales], , DESC, DENSE )
```

`RANKX` iterates the table in its first argument; `ALL ( Product[ProductName] )`
gives it the full list to rank against, rather than the single row in context.

### Reaching across a relationship

```dax
// In a CALCULATED COLUMN on Sales (row context exists): pull the one-side value
Sales[Category] = RELATED ( Product[Category] )

// Aggregate the many-side from the one-side row:
Product[OrderCount] = COUNTROWS ( RELATEDTABLE ( Sales ) )
```

`RELATED` follows a relationship from the many-side to the one-side (one value);
`RELATEDTABLE` returns the related many-side rows. Both need row context, so they
live in calculated columns or iterators, not in a plain measure.

---

## Performance

- **Measures over calculated columns.** A stored aggregation is dead weight;
  compute at query time.
- **Don't `FILTER` an entire large fact table.** `CALCULATE ( [Sales],
  FILTER ( Sales, Sales[Qty] > 0 ) )` scans every row. Prefer a column predicate —
  `CALCULATE ( [Sales], Sales[Qty] > 0 )` — or filter a small dimension, not the
  fact.
- **`DIVIDE`, never `/`.** `DIVIDE ( a, b )` handles divide-by-zero/BLANK
  gracefully (returns `BLANK()`, or a supplied alternate) and is optimized for the
  test. Use the `/` operator only when the denominator is a non-zero constant.
- **Freeze repeated work in variables** so it evaluates once.
- **Avoid `IFERROR`/`ISERROR` in hot paths** — they force extra storage-engine
  scans. Fix the data or use `DIVIDE` instead.
- **Don't force BLANKs to zero** (`DIVIDE ( a, b, 0 )`) without reason — BLANK lets
  visuals drop empty groupings; a forced 0 turns a sparse result dense and can
  explode row counts.

---

## Watch Out

1. **A measure right at the leaf but wrong at the total.** The classic
   sum-of-ratios vs. ratio-of-sums trap: a total is *not* the sum of the row
   values — it's the measure re-evaluated in the total's filter context. If a
   margin% total looks wrong, you almost certainly wrote it as an average of row
   percentages instead of `DIVIDE ( total profit, total sales )`.
2. **Bare aggregation inside an iterator ignores the current row.** `SUMX ( Sales,
   SUM ( Sales[Amount] ) )` repeats the grand total on every row. Reference the
   column (`Sales[Amount]`) or a measure, so context transition kicks in.
3. **`ALL` overwrites more than you meant.** `ALL ( Product )` drops *every*
   Product filter, including the slicer the user set. If you only meant to clear
   the axis, use `ALLSELECTED`, or `KEEPFILTERS`/`ALLEXCEPT` to preserve the rest.
4. **Time intelligence silently blanks or errors without a proper Date table.** No
   marked date table, a gap in the date range, or a datetime on the fact table →
   wrong or blank results. Verify the Date table before debugging the measure.

---

## Out of scope — hand off

- **Shaping, loading, merging, deduping, or type-casting data before the model** →
  `power-query-m`. If the fix is "clean this upstream," that's a Power Query job.
- **Designing the source SharePoint list** (columns, keys, relationships at the
  data-source level) → `sharepoint-list-architecture`.
- **Power Fx** — app formulas in Power Apps are a **different language**; do not
  write DAX where Power Fx is meant → `power-fx-development` (and
  `power-fx-review` to review it). Canvas UI components → `power-apps-components`;
  Microsoft Graph calls → `graph-api-integration`.

If the user asked for DAX, stay in DAX — don't pivot them to Power Query or a
visual-level workaround unless the model itself is the blocker, in which case name
the handoff explicitly.
