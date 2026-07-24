---
name: power-fx-review
description: >
  Expert Power Fx code reviewer for Power Apps canvas apps — delegation, performance,
  and correctness. Use this skill whenever the user pastes Power Fx and asks for a
  review, audit, or help improving it, or reports a bug, a slow app, or wrong results
  and shares formulas as context — even without the word "review". Trigger on phrases
  like "review my Power Fx", "why is this slow", "is this correct", "what's wrong with
  this app", "delegation warning", "why doesn't it show all my records", or any paste
  of Power Fx (a Filter/LookUp/ForAll/Patch formula, a gallery Items, an OnStart)
  followed by a question. The implicit signal is a paste of Power Fx followed by a
  question — treat that as a review request. Prioritize delegation and correctness
  over style: check for non-delegable queries that silently truncate at 500 records,
  per-row lookups inside galleries, and blank/error handling before anything cosmetic.
  To write new formulas from scratch use power-fx-development; to build reusable canvas
  UI components use power-apps-components; when the delegation issue is really a data
  model problem, hand the backend design to sharepoint-list-architecture.
---

# Power Fx Code Review Skill

You review Power Fx for the defects that actually bite a canvas app in production:
queries that silently return only the first 500 rows, galleries that fire a network
call per row, and formulas that break on a blank or an error. Lead with the most
severe issue. Present findings grouped by severity, not in the order you found them.
A Power Fx review is **delegation-first**: a formula that looks correct on the maker's
50-row test list can be silently wrong against the real 20,000-row source.

## Review Priority Order

Evaluate in this sequence. Never skip to style while a delegation or correctness issue stands:

1. **Delegation correctness** — non-delegable `Filter`/`LookUp`/`Search`/`Sort`/aggregation that Power Apps runs locally over only the first 500 records (2,000 max), returning incomplete or wrong results against a large source
2. **Performance** — N+1 lookups inside a gallery, repeated `Filter`/`LookUp` per row, `Patch`-in-`ForAll` instead of bulk `Patch`, uncached repeated data calls, `OnStart` bloat, controls that recompute an expensive expression on every dependency change
3. **Correctness** — blank/error handling (`IsBlank` vs `IsEmpty`, `Coalesce`, `IfError`), type coercion, `Patch` vs `SubmitForm` on a form, race conditions with async calls
4. **Maintainability** — naming, magic values, hardcoded list GUIDs/URLs, screen-to-screen context passing, dead `OnStart` code

## What to Ask For (if absent)

You cannot judge delegation without knowing the data source. If the paste doesn't make these clear, ask:

- **The data source(s)** behind each `Filter`/`LookUp`/gallery — SharePoint, Dataverse, SQL, or a local collection? Delegation support differs sharply (Dataverse delegates the most; SharePoint the least; a collection is always local so delegation never applies)
- **The Data row limit setting** (Settings → General → Data row limit, 1–2,000) and the **row count** of the real source — a non-delegable query is only a bug when the source exceeds that limit
- **Target form factor / screen sizes** if reviewing layout-coupled performance, and **what "slow" means** — screen load, a gallery scroll, a save? how many rows?
- **The symptom verbatim** if reviewing a bug — "only shows 500 rows", a `#Error`, a blank where a value should be

---

## Review Checklist

### 1. Delegation (do this first)

The single most important check. When a query can't be delegated, Power Apps pulls only the
first **500 records** (raisable to **2,000** max in app settings) to the device and runs the
operation locally. At authoring time this shows as a blue wavy underline and a yellow-triangle
warning — but **at runtime it fails silently**: the user just never sees record 501+.

```
// BUG: Search is not delegable to SharePoint. Against a 20,000-item list this
// scans only the first 500 items — matches past row 500 silently vanish.
Gallery.Items = Search(Projects, TextBox.Text, "Title")

// FIX: StartsWith and Filter with = are delegable to SharePoint.
Gallery.Items = Filter(Projects, StartsWith(Title, TextBox.Text))
```

Flag these delegation traps specifically:

- **Non-delegable functions inside a query** — `Search`, `First`/`Last`, `CountRows`/`CountIf` (SharePoint), `Sum`/`Average`/`Max`/`Min` over a large source, `in` on SharePoint. If any part of the expression is non-delegable, **the whole query is non-delegable**.
- **Non-delegable predicates** — `Filter(list, IsBlank(Owner))` does **not** delegate; `Filter(list, Owner = Blank())` **does** (they differ on the empty string, but the delegable form is usually what you want). Same for many string ops depending on source.
- **Column-order and operator quirks** — `StartsWith(Title, x)` delegates but `StartsWith(x, Title)` doesn't; `"a" in Column` delegates on SQL where `Column in "a"` doesn't.
- **Sorting and aggregation** — `Sort`/`SortByColumns` delegate on most sources, but a `Sort` wrapped around a non-delegable inner expression inherits its locality; aggregates like `Average(BigList, Amount)` silently average only 500 rows.
- **`ForAll`/`UpdateIf`/`RemoveIf`** — these simulate delegation only up to the 500/2,000 cache; don't treat them as full-table operations.

Rule of thumb to hand back: **set the Data row limit to 1 while testing** — any non-delegable
formula then returns a single record, making the problem impossible to miss.

### 2. Performance — N+1 and repeated calls

```
// BUG: N+1. This LookUp runs once PER ROW the gallery renders — one network
// round-trip each. A 200-row gallery = 200 calls just to show a name.
Gallery.Items = Projects
Label_Owner.Text = LookUp(Users, ID = ThisItem.OwnerId, FullName)

// FIX: pre-join once into a collection at screen load, then read locally.
Screen.OnVisible =
  ClearCollect(
    colProjects,
    AddColumns(
      Projects,
      OwnerName, LookUp(Users, ID = OwnerId, FullName)
    )
  );
Gallery.Items = colProjects
Label_Owner.Text = ThisItem.OwnerName
```

Also flag:

- **`Patch` inside `ForAll`** for bulk writes — `ForAll(items, Patch(Source, ...))` issues one call per item. Prefer a **single bulk `Patch(Source, table_of_records)`**, which sends one request. (`ForAll` is for producing a table, not for driving side effects row by row.)
- **Uncached repeated data calls** — the same `Filter`/`LookUp` evaluated in several control properties re-queries each time. Compute once into a collection or a context/global variable and reuse.
- **`OnStart` bloat** — heavy `ClearCollect`s in `App.OnStart` delay app launch for every user, every start. Move data that a screen needs into that screen's `OnVisible`; reserve `OnStart` for genuinely global, cheap setup.
- **Expensive expressions in high-churn properties** — a `Filter`/`CountRows` in a property that recomputes on every keystroke or timer tick. Debounce or cache.

### 3. Correctness — blank, error, and forms

```
// BUG: IsBlank on a collection is ALWAYS false — a collection exists even when
// it has zero rows. This branch never fires.
If(IsBlank(colCart), Notify("Cart is empty"))

// FIX: IsEmpty tests a table for zero records.
If(IsEmpty(colCart), Notify("Cart is empty"))
```

- **`IsBlank` vs `IsEmpty`** — `IsBlank` tests a *value* for blank or empty string; `IsEmpty` tests a *table* for zero records. Never `IsBlank` a collection/table to check emptiness.
- **`Coalesce` for fallbacks** — `Coalesce(value, fallback)` returns the first non-blank, non-empty-string argument in one pass; prefer it over `If(!IsBlank(x), x, y)`, which evaluates `x` twice.
- **Error handling** — wrap fallible data operations in `IfError`; use `IsBlankOrError` where a formula must treat errors and blanks alike. Note that `Patch`/`Collect` return *blank* (not the record) on failure — check it, and read `Errors(Source)` for the reason.
- **`Patch` vs `SubmitForm`** — if the screen has an `Edit form`, saving with a raw `Patch` bypasses the form's validation, `Error`/`OnFailure` handling, and `Unsaved`/`Updates` machinery. Use `SubmitForm(Form)` and handle `OnSuccess`/`OnFailure`; reserve `Patch` for when there is no form.
- **Race conditions** — assuming a value is set immediately after an async call, or chaining operations across `;` that depend on a network write having completed. Sequence with `OnSuccess`/`IfError`, not by hoping.

### 4. Maintainability

| Problem | Recommendation |
|---|---|
| Hardcoded list GUID / site URL / connection literal inline | Promote to a named data source or an `App.OnStart` global (`Set(gEnvUrl, ...)`) |
| Magic numbers / status strings repeated across screens | Centralize in a global variable or a small config collection set in `OnStart` |
| Screen-to-screen state via many globals | Pass with `Navigate(Screen, ScreenTransition.None, {record: ThisItem})` context where scoped |
| Cryptic names (`Gallery1`, `Var1`, `col2`) | Rename controls/variables to their role; galleries and collections especially |
| Dead `OnStart` code — collections built but never read | Remove; every `OnStart` line is startup latency for all users |

---

## Review Output Format

### Critical (fix before shipping)
Non-delegable queries against large sources (silent truncation), N+1 lookups in galleries, `Patch`-in-`ForAll` bulk writes, `IsBlank` used to test a table, raw `Patch` where a form's validation is required.

### Important (fix soon)
Uncached repeated data calls, `OnStart` bloat, missing error handling on data ops, avoidable delegation warnings, race conditions on async writes.

### Minor (nice to fix)
Naming, magic values, hardcoded URLs/GUIDs, dead code, screen-to-screen context hygiene.

### Summary
One paragraph: overall health, whether the app is delegation-safe at the real data volume, and the single most important thing to fix first.

---

## Worked Example — a delegation + N+1 fix together

A maker reports: *"My project list is slow and it's missing rows past a few hundred."* They paste:

```
// Gallery.Items
Sort(
    Filter(Projects, Status = "Active" && Search(Title, TextSearch.Text, "Title") ),
    Modified,
    Descending
)

// Label inside the gallery, per row
Label_Owner.Text = LookUp(Users, ID = ThisItem.OwnerId, DisplayName)
```

**Two defects, both severe.** (1) `Search` isn't delegable to SharePoint, so the *entire*
`Filter`/`Sort` runs locally over only the first 500 rows — that's the "missing rows." (2) The
per-row `LookUp(Users, ...)` is an N+1: one call per rendered row — that's the "slow."

```
// FIX 1 — make the query delegable: swap Search for StartsWith, keep Filter/Sort delegable
// FIX 2 — resolve the owner name once, at screen load, not per row

// Screen.OnVisible
ClearCollect(
    colProjects,
    AddColumns(
        Sort(
            Filter(
                Projects,
                Status = "Active" && StartsWith(Title, TextSearch.Text)
            ),
            Modified,
            Descending
        ),
        OwnerName, LookUp(Users, ID = OwnerId, DisplayName)
    )
);

// Gallery.Items
colProjects

// Label inside the gallery, per row — now a local field read, zero network calls
Label_Owner.Text = ThisItem.OwnerName
```

Now `Filter` + `StartsWith` + `Sort` all delegate to SharePoint, so every matching row is
returned regardless of list size, and the owner name is joined once instead of per row. Hand
back a way to confirm it: **set Data row limit to 1**, reload — if the gallery still shows all
active projects, delegation is working; if it collapses to one row, a non-delegable piece remains.

---

## Watch Out

1. **"It works on my test list" hides the 500-row cliff.** A non-delegable query is invisible on a 50-row source and silently wrong on the 20,000-row production list. Judge delegation by the formula and the *real* row count, never by the demo.
2. **A delegation warning is not just a lint nag.** The blue squiggle / yellow triangle is the app telling you it will return incomplete data at scale. Treat unresolved delegation warnings on a large source as a correctness bug, not a style note.
3. **`IsBlank` on a table is a silent no-op.** It is always `false` for a collection, even an empty one — the "is my cart empty" check never fires. Reach for `IsEmpty` on tables and `IsBlank`/`Coalesce` on values.
4. **`ForAll` is not a loop for side effects.** `ForAll(items, Patch(...))` fires a request per row and creates race and error-handling gaps; a single bulk `Patch(Source, items)` is one call and far faster.

## Out of Scope

- **Writing new formulas or architecting an app from scratch** — that's `power-fx-development`; this skill audits Power Fx that already exists.
- **Building reusable canvas UI components** (custom components, `HtmlText` rendering) — hand to `power-apps-components`.
- **Redesigning the backend data model** when a delegation problem is really a list-shape problem (wrong column types, list too wide, needs indexing) — that's `sharepoint-list-architecture`.
- **JSON column/view formatting** → `sharepoint-column-formatting`; **Microsoft Graph calls** → `graph-api-integration`; **DAX** → `power-bi-dax`; **Power Query / M** → `power-query-m`.
