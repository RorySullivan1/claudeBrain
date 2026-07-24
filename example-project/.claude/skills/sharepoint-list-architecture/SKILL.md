---
name: sharepoint-list-architecture
description: >
  Expert at designing SharePoint lists as an application backend — the schema,
  column types, indexing, and relationship model behind a Power App or Power
  Automate flow, engineered so queries stay correct and fast at scale. Use this
  skill whenever the user is designing the data layer behind a Power App
  ("list schema for my PowerApp", "SharePoint as a database"), choosing between
  column types ("choice vs lookup column", "person column vs text"), fighting the
  size ceiling ("5000 item limit", "list view threshold", "the number of items in
  this list exceeds"), planning for growth ("index a column", "my list is getting
  slow", "delegation warning"), modeling relationships between lists (one-to-many,
  parent/child, cascade delete), or deciding whether SharePoint is even the right
  store ("SharePoint list vs Dataverse", "should this be a list or a document
  library"). Also trigger on implicit signals: a maker sketching columns for a new
  app, someone whose app "works with 200 rows but breaks at 6000", questions about
  internal vs display column names or a rename that broke a formula, item-level
  "show only mine" permission design, or content types on a list. Boundary — this
  skill designs the STORE, not the app on top of it: for writing the Power Fx that
  queries the list (Filter/LookUp/Search, delegation-safe formulas) use
  power-fx-development, and to review existing Power Fx use power-fx-review; for the
  reusable canvas UI over the data use power-apps-components; for the declarative
  JSON that changes how a column or view *looks* (colors, pills, layout) use
  sharepoint-column-formatting; for reaching the list programmatically over REST use
  graph-api-integration; for analytics over the data use power-bi-dax and
  power-query-m. This skill owns the list design; those own what runs against it.
---

# SharePoint List Architecture Skill

You design SharePoint lists that behave like a dependable application backend, not
like the ad-hoc spreadsheets they superficially resemble. Your job is to make the
schema decisions — column types, indexes, relationships, permissions — that keep an
app's queries correct and fast when the list grows from 200 rows to 200,000. Lead
with the design, state the assumptions that drive it, and prefer the schema that
survives scale over the one that's fastest to click together today.

## Core Principles — a SharePoint list is NOT a relational database

Internalize these before proposing any schema. Every trap below flows from ignoring one.

- **It's a throttled SQL table you don't control.** Every list lives in a shared
  SQL Server database. Microsoft protects that database with the **list view
  threshold: 5,000 items**. This is not the list's capacity (a list holds up to
  **30 million items**) — it's the maximum number of rows a *single query* may
  scan or return at once. Design is the art of never asking a question that scans
  more than 5,000 rows.
- **There are no real joins.** Lookup columns *look* relational but each one is a
  costly join, and a view/query may use at most **12 joins (lookup, Person/Group,
  and Managed Metadata columns all count)** before it's blocked. There is no
  foreign-key engine enforcing integrity for you.
- **Denormalize deliberately.** In a relational DB you normalize by default. In
  SharePoint you often do the opposite — copy a value into the child list — because
  a stored string costs nothing to read while a lookup costs a join against the
  threshold.
- **The client (Power Apps) has its own ceiling.** Power Fx only returns all
  matching rows when the query is *delegable*; a non-delegable query silently
  processes just the first **500 rows (raisable to 2,000)**. Schema choices decide
  which columns can be filtered delegably, so list design and app correctness are
  the same problem. (The formulas themselves live in power-fx-development.)
- **Names are frozen at creation.** A column's **internal name** is set once, when
  the column is created, and never changes — renaming the column only changes its
  display name. Every formula, view, and API call binds to the internal name.

---

## First — Clarify Before Designing

Never design a schema blind. Ask **one or two** targeted questions when these are unknown:

| Unknown | Ask | Why it changes the design |
|---|---|---|
| Expected row count | "Roughly how many items — now and in two years?" | Under 2,000 → most rules relax. Over 5,000 → indexing + delegation drive everything. |
| Read/write pattern | "Who reads, who writes, and how many rows does a typical screen show?" | Decides which columns must be indexed and which views must be pre-filtered. |
| Query shape | "What will the app filter or sort on most?" | Those columns are your index candidates and must be delegation-friendly types. |
| Relationships | "Does a record belong to a parent, or reference another list?" | Drives lookup-vs-denormalize and the join budget. |
| Row-level privacy | "Does each user see only their own items?" | Item-level permissions have real performance cost; better designed in than bolted on. |
| Platform fit | "Is a list the right store, or is this really Dataverse/a document library?" | See the decision table below — sometimes the answer is 'not a list.' |

State assumptions at the top of any schema you propose, e.g.
`Assumes: ~50k items at maturity, Power Apps front end, users filter by Status + AssignedTo, each rep sees only their own records.`

---

## Choosing Column Types — the decision table

Pick the **most specific type that models the data**, then check its delegation
behavior in Power Apps. "Delegable" below means Power Fx can push a `Filter`/`Sort`
on that column to the server (correct results past 500/2,000); non-delegable columns
force local processing and quietly cap results.

| Data | Use | Not | Delegation / cost notes |
|---|---|---|---|
| Short text (name, ID, code) | **Single line of text** (≤255 chars) | Multiple lines | Delegable for `=`, `StartsWith`. **Indexable** — the workhorse filter column. |
| Long/notes/HTML | **Multiple lines of text** | Single line | **Not filterable, not indexable, not delegable.** Never filter on it; store keys elsewhere. |
| Small fixed set of values you own | **Choice** | Lookup | Delegable on `=`. No join cost. Best for Status/Category/Priority. Avoid "Fill-in" values — they wreck reporting. |
| A value that lives in and is maintained by another list | **Lookup** | Choice | Costs **1 join** (12-join view cap). Delegation is limited — filtering on lookup subfields is restricted. Use only for genuine shared reference data. |
| Enterprise taxonomy / cross-site tags | **Managed Metadata** | Choice | Central term store, but **counts as joins** and adds hidden columns; heavier than Choice. Reserve for true org-wide taxonomy. |
| A person or team | **Person or Group** | Text | Stores a directory reference (name, email, ID). **Counts as a join.** Delegation limited; filtering by `Email`/`current user` needs care. |
| A calendar date / timestamp | **Date and Time** | Text | Delegable for `<,>,=`. **Indexable** — index it if you filter by date range. Watch time-zone display. |
| Quantity / money | **Number** / **Currency** | Text | Delegable for comparisons. Currency adds formatting only; both indexable. |
| A true/false flag | **Yes/No** | Choice | Delegable, cheap, indexable. Default it explicitly. |
| A value derived from other columns | **Calculated** | (store it) | **Cannot be indexed, cannot be filtered delegably.** Fine for display; never a query key. |
| A link or image | **Hyperlink or Picture** | Text | Display only; not a filter/index target. Stored as two subfields (URL + description). |
| The record's own identity | **ID** (built-in) | a custom key | Auto, unique, **always indexed**. `LookUp(list, ID=n)` is the fastest possible query — the ideal way to fetch one record. |

Rules of thumb: **Choice beats Lookup** whenever the values are stable and owned by
this app (no join, delegable). **Lookup beats duplicating a whole related table**,
but each lookup spends join budget — cap yourself well under 12 per view. **Never
plan to filter or sort on** Multiple-lines, Calculated, or Hyperlink columns.

---

## The 5,000 Threshold & Indexing Playbook

The threshold blocks any query that would **scan** more than 5,000 items — even if
it returns two. An index changes what gets scanned. Work this playbook in order:

1. **Can the list stay under 5,000 by scoping?** Split by year, region, or
   business unit into separate lists, or archive closed records out. The cheapest
   large-list problem is the one you designed away.
2. **Index the columns you filter/sort on.** An indexed column lets SharePoint seek
   directly to the matching rows, so a filtered *result* under 5,000 succeeds even
   when the *list* is far larger. This is the core fix. Index your Status, date, and
   assignee columns — whatever the app's views and Power Fx filter on first.
   - **Facts to design around:** you can maintain only a **limited number of
     indexes per list (commonly documented as up to 20 in SharePoint Online)**, so
     spend them on real query columns, not "just in case."
   - You can **add or remove an index only while the list has ≤ 20,000 items** —
     past that the manual operation is throttled. Modern SharePoint **auto-indexes
     in the background** for lists that grow beyond ~20,000, but you should not rely
     on that timing; **create your indexes early, while the list is small.**
   - Multiple-lines and Calculated columns **cannot** be indexed — factor that into
     which column carries a query key.
3. **Make the *first* filter clause hit an indexed column.** SharePoint evaluates
   the leftmost condition against the index; if that clause alone narrows the set
   under 5,000, later conditions on unindexed columns are fine. A filter whose first
   clause is unindexed can still trip the threshold.
4. **Pre-filter every view.** A view with no filter tries to enumerate the whole
   list and throws *"The number of items in this list exceeds the list view
   threshold."* Give each view a filter on an indexed column (e.g. `Status = Active`,
   `Modified ≥ [Today]-30`) so it never asks for everything.
5. **Keep Power Apps delegable against the same columns.** The index keeps the
   *server* query legal; delegation keeps the *app* from silently truncating at
   500/2,000. They must agree: filter the app on indexed, delegation-friendly columns
   (text `=`/`StartsWith`, dates, numbers, Yes/No, Choice `=`). The Power Fx itself
   is power-fx-development's job — your part is guaranteeing the schema *can* be
   queried delegably.

---

## Relationships & Referential Integrity

SharePoint models one-to-many with a **Lookup** column on the child pointing at the
parent — but you own the trade-offs a real database would handle for you:

- **The 12-join wall.** Lookup, Person/Group, and Managed Metadata columns each cost
  a join, capped at 12 per view/query. A child list with several lookups plus a
  couple of people columns burns the budget fast. Count joins per *view*, and drop
  unused lookup columns from heavy views.
- **Projected (lookup) fields still count.** Pulling extra columns from the parent
  through a lookup ("also show the parent's Region and Owner") adds joins. Project
  only what a view actually shows.
- **Referential integrity is optional and limited.** A lookup can enforce
  **Restrict Delete** (block deleting a parent that has children) or **Cascade
  Delete** (delete the children too) — but only on **primary** lookup columns, and
  the cascade itself is throttled on large lists. Don't assume it's on; choose it
  deliberately.
- **Denormalize the hot path.** Because every lookup read is a join against the
  threshold, it is often *correct* to copy a stable parent value (e.g. the parent's
  `AccountName`) into the child as plain indexed text. You trade a little duplication
  for a delegable, join-free, indexable filter column. Reserve live lookups for data
  that genuinely changes and must stay consistent.
- **Content types** let one list hold several related record shapes (e.g. an
  `Incident` and a `Change` in one Tracker) sharing columns while adding their own.
  Useful for polymorphic backends — but they don't remove any threshold or join
  limit, so reach for them for modeling clarity, not scale.

---

## Worked Example — a Project Tracker backend (Power App)

Requirement: a canvas app tracking projects and their tasks; ~40k tasks at maturity;
managers see all, each contributor sees only tasks assigned to them; app filters
tasks by Status and DueDate and by parent Project.

**List 1 — `Projects`** (small, < 2,000 rows; reference/parent)

| Column (display) | Type | Indexed | Notes |
|---|---|---|---|
| `Title` | Single line of text | yes | Project name; the built-in Title column, repurposed. |
| `ProjectCode` | Single line of text | yes | Human key; unique by convention. |
| `Status` | Choice | – | `Planning / Active / Closed`. |
| `ProjectManager` | Person or Group | – | One join if referenced from a view. |

**List 2 — `Tasks`** (large, ~40k rows; child) — indexes chosen for the app's filters:

| Column (display) | Type | Indexed | Design reason |
|---|---|---|---|
| `Title` | Single line of text | – | Task summary. |
| `Status` | Choice | **yes** | Primary filter; Choice = delegable `=`, no join. |
| `DueDate` | Date and Time | **yes** | Range-filtered; indexed date keeps `DueDate ≤ …` under threshold. |
| `AssignedTo` | Person or Group | **yes** | Drives "only mine"; indexed so per-user queries stay legal. |
| `Project` | Lookup → Projects | – | The one real join; links child to parent. |
| `ProjectCodeText` | Single line of text | **yes** | **Denormalized** copy of the parent code — lets the app filter tasks by project *without* spending the lookup's join on a 40k-row view. |
| `Notes` | Multiple lines of text | – | Display only; never filtered. |

Why it holds at 40k: every screen filters first on an **indexed** column
(`Status`, `DueDate`, or `AssignedTo`), so no query scans the whole list; the parent
link is one lookup, and project-scoped views use the denormalized `ProjectCodeText`
so they stay join-cheap and delegable. Item-level permission "read items created by
the user" is set on `Tasks` for the contributor role (see Watch Out #3 on its cost).

---

## Watch Out

1. **The internal name is frozen — name columns right the first time.** If you create
   a column called "Status Code" the internal name becomes `Status_x0020_Code`
   forever; later renaming it to "Status" changes only the label. Worse, the *first*
   column you name "Title" and rename leaves `Title` as the internal name. Create
   columns with clean names (or create them named simply and rename in the UI once)
   so formulas and API calls bind to sane internal names. This bites Power Fx and
   Graph queries constantly.
2. **You can't index your way out after the fact, easily.** Adding an index is
   throttled once the list passes 20,000 items and auto-indexing is best-effort. A
   list designed without indexes that quietly grows past the threshold becomes a
   support incident. Add indexes while it's small.
3. **Item-level permissions ("show only mine") are not free.** Setting a list to
   "read/create items the user created" scopes rows per user, but every unique
   permission is a **security scope**, and lists degrade as scopes climb (tens of
   thousands hurt; over 100,000 items you can't even break inheritance). Prefer a
   single indexed `AssignedTo`/`Author` filter for "my items" over per-item unique
   permissions unless the data is genuinely confidential between users.
4. **A delegation warning is a data-loss bug, not a lint nit.** The blue Power Fx
   underline means the query fell back to 500/2,000 rows and may return *wrong*
   answers on a large list. Treat it as a schema signal: the column being filtered
   isn't delegable/indexed — change the type or add the index, don't just raise the
   row limit. (Fixing the formula is power-fx-development.)

---

## List vs Document Library vs Dataverse

| Choose | When | Because |
|---|---|---|
| **SharePoint list** | Structured records, ≤ a few hundred k rows, Microsoft 365 / Power Platform front end, no per-row licensing budget | Free with M365, native Power Apps/Automate integration, good enough with disciplined indexing. |
| **Document library** | The record *is* a file (contract, image, report) with metadata about it | A library is a list whose items are files; use it when the payload is a document, not columns. |
| **Dataverse** | Real relational integrity, > ~100k–millions of rows, rich role-based security, calculated/rollup server fields, broad delegation | It's a managed relational store; delegation and joins that SharePoint fakes are first-class. Costs premium licensing. |

Rule: reach for **Dataverse when you find yourself fighting SharePoint's limits by
design** — many lookups, referential integrity that must hold, security beyond
"mine vs all", or reliably large tables. If you're merely storing a few thousand
structured rows behind an app, a well-indexed list is the right, cheaper tool.

---

## Out of Scope — hand off to the sibling skill

- **Writing the Power Fx that queries the list** (`Filter`, `LookUp`, `Search`,
  delegation-safe formulas, collections) → **power-fx-development**; **reviewing**
  existing Power Fx → **power-fx-review**.
- **Reusable canvas UI over the data** (galleries, forms, custom components) →
  **power-apps-components**.
- **Declarative JSON that changes how a column or view looks** (color pills,
  conditional formatting, view layout) → **sharepoint-column-formatting**. This
  skill decides the columns *exist*; that one styles them.
- **Programmatic access to the list over REST** (create/read/update items, batch,
  app-only auth) → **graph-api-integration**.
- **Analytics and reporting over the list** → **power-bi-dax** (measures) and
  **power-query-m** (shaping/loading).
