---
name: power-fx-development
description: >
  Expert Power Fx developer for writing, architecting, and debugging formulas in
  canvas Power Apps backed by a SharePoint list. Use this skill whenever the user
  asks to author or fix Power Fx: "write a Power Fx formula", "Patch this to
  SharePoint", "how do I set a variable / collection in Power Apps", "SubmitForm
  isn't saving", "Navigate to a screen and pass context", "my gallery only shows
  500 rows", "why is my app slow", or pastes a formula and asks to make it work.
  Trigger especially on delegation questions — "delegation warning", "blue
  underline under my Filter", "StartsWith vs Search", "in operator won't
  delegate", "should I raise the data row limit to 2000", "ForAll to write many
  records", "ClearCollect to cache my list", "Set vs UpdateContext vs With",
  "App.Formulas vs OnStart". Also fire on implicit signals: the user mentions a
  gallery/form/screen returning wrong or partial results, aggregates
  (Sum/CountRows) over a big list, or IfError/Notify error handling in an app.
  This skill WRITES and architects formulas. For auditing/reviewing existing Power
  Fx for delegation and performance defer to power-fx-review; for building reusable
  UI components and HtmlText rich content defer to power-apps-components; for
  designing the list schema, indexing, and view-threshold strategy defer to
  sharepoint-list-architecture; for programmatic (non-in-app) data access defer to
  graph-api-integration. DAX belongs to power-bi-dax and Power Query/M to
  power-query-m — this skill is canvas Power Fx only.
---

# Power Fx Development Skill

You write Power Fx the way it wants to be written: **declarative, delegable, and
Excel-minded** — not procedural code with loops bolted on. Every formula runs against a
SharePoint list that can grow past the local limit, so *delegation is the first thing you
reason about, not the last.* Lead with the answer, state your assumptions, and prefer the
smallest correct formula over a clever one.

## Core principles (these are rules, not suggestions)

1. **Think in expressions, not steps.** Power Fx has no classic `for`/`while`. You don't
   mutate state in a loop — you describe a result. Reach for `ForAll`/`Sequence` only when
   you genuinely need per-row work; a `Filter`/`LookUp`/`AddColumns` almost always beats a
   loop and (crucially) can delegate.
2. **Delegable-first.** Before writing any `Filter`, `LookUp`, `Sort`, or `Search`, ask
   "does this translate to a SharePoint query?" If not, rewrite it so it does. See the full
   matrix in **`delegation.md`** (this folder). A blue wavy underline in the editor means
   *this clause won't delegate* — never ship past it on a list that can exceed the limit.
3. **Minimize recompute.** A control property re-evaluates whenever anything it references
   changes. Don't put a `Filter` over a data source directly in ten control properties —
   compute once (a variable, a collection, or a named formula) and reference that.
4. **Name state by its scope.** Global (`Set`), screen (`UpdateContext`), inline (`With`),
   and cached tables (`Collect`) are four different tools — pick the narrowest that works.
5. **Errors are values, not crashes.** Wrap risky work in `IfError`, surface it with
   `Notify`, and centralize the safety net in `App.OnError`. Never let a Patch fail silently.

---

## First — clarify before coding

Ask **one** targeted question only if the answer changes the formula:

| Unknown | Ask |
|---|---|
| List size / growth | "Roughly how many items — under 500, or will it grow past 2000?" (decides how hard delegation matters) |
| Column types | "Is that a Choice/Lookup/Person column or plain text?" (changes what delegates) |
| Where the formula lives | "Is this a gallery `Items`, a button `OnSelect`, a form, or `App.OnStart`?" |
| Read vs write | "Reading/filtering, or writing back with Patch/SubmitForm?" |
| Backend certainty | Default to a **SharePoint list**; confirm only if Dataverse/SQL is possible (delegation rules differ) |

State assumptions at the top of your answer, e.g. *"Assuming `Projects` is a SharePoint list
that can exceed 2000 items; `Status` is a Choice column."*

---

## State & variables — pick the narrowest scope

| Tool | Scope | Use for | Read/clear |
|---|---|---|---|
| `Set(gVar, value)` | **Global** (whole app) | Current user, selected record shared across screens | `gVar`; `Set(gVar, Blank())` |
| `UpdateContext({cVar: value})` | **Screen** (one screen) | UI state local to a screen (dialog open, edit mode) | `cVar`; also settable via `Navigate` |
| `With({x: expr}, formula)` | **Inline** (one formula) | Naming a subexpression to avoid recomputing it | scoped to the `With` body |
| `Collect`/`ClearCollect` | **Collection** (in-memory table) | Caching a list, staging rows before a bulk write | `MyColl`; `Clear(MyColl)` |
| `App.Formulas` (named formula) | **App, declarative** | A reusable *value/definition* that recomputes automatically | reference by name |

**Naming convention:** prefix globals `g` (`gCurrentUser`), context vars `loc`/`c`
(`locShowDialog`), collections `col` (`colCart`). Consistency substitutes for Power Fx's
lack of a type system.

**`Set` vs `UpdateContext`:** default to **context** for anything one screen owns — a global
that only one screen uses is just leaked state. Use a global only when two screens must share it.

**Named formulas (`App.Formulas`) beat `App.OnStart`.** A named formula is a *definition*,
not an assignment: it's computed only when needed, always up to date, and never runs in a
slow startup chain.

```powerapps
// In App.Formulas — declarative, no ordering, recomputes when User() changes:
UserEmail = User().Email;
MyOpenTasks = Filter(Tasks, AssignedToEmail = UserEmail && Status.Value = "Open");
```

Prefer this over piling `Set()` calls into `App.OnStart` (which is sequential, runs once, and
delays the first screen). Reserve `OnStart` for true one-time imperative setup (e.g. an initial
`Navigate`), and keep it short.

---

## Delegation — the central skill

**One non-delegable clause poisons the entire query.** Power Apps then silently pulls only the
first *data-row-limit* records (default **500**, raise to max **2000** in Settings → General →
Data row limit) and evaluates locally — so a `Filter` over a 10,000-item list can miss the
record you need. `delegation.md` holds the full SharePoint matrix; the essentials:

**Delegates to SharePoint:** `Filter`, `LookUp`, `Sort`/`SortByColumns`, `StartsWith` (text),
`=` (all types), and relational `<` `<=` `<>` `>` `>=` on **Number/DateTime/Complex** columns.
`And`/`Or` (`&&`/`||`) delegate if both sides do.

**Does NOT delegate to SharePoint:** `Search`, `in`/`exactin`, `Not`/`!`, `<`/`>` on **Text**,
aggregates (`Sum`, `Average`, `Min`, `Max`, `CountRows`, `CountIf`), `Skip`, `First`/`FirstN`
bodies, `Distinct`, `GroupBy`, and `IsBlank()` inside a predicate.

**The three moves that fix most warnings:**

| Instead of | Write | Why |
|---|---|---|
| `Search(Tasks, box.Text, "Title")` | `Filter(Tasks, StartsWith(Title, box.Text))` | prefix match delegates; substring never does |
| `Filter(l, Status in myList)` | `Filter(l, Status="A" \|\| Status="B")` | explicit `Or` of `=` delegates |
| `Filter(l, IsBlank(Owner))` | `Filter(l, Owner = Blank())` | `= Blank()` delegates (for `=`, not `<>`) |

**Set the data row limit to 1 while developing.** Then any non-delegable formula returns a
single record and the bug is obvious immediately — far better than discovering it in production.

### Worked rewrite: a gallery "only showing 500 rows"

A gallery over a 6,000-item `Orders` list, filtered by a text search box, returns partial and
wrong results with a blue underline under `Search`:

```powerapps
// ❌ Non-delegable: Search() forces local eval → only first 500 rows scanned
Search(Orders, txtSearch.Text, "CustomerName")
```

Rewrite so SharePoint does the work:

```powerapps
// ✅ Delegable: StartsWith on a Text column translates to a SharePoint query.
// Guard the empty box so an empty search returns everything (sorted server-side).
Sort(
    Filter(
        Orders,
        IsBlank(txtSearch.Text) || StartsWith(CustomerName, txtSearch.Text)
    ),
    Created,
    SortOrder.Descending
)
```

Both `Filter`/`StartsWith` and the `Sort` on the `Created` DateTime delegate, so all 6,000 rows
are searched server-side and only matching pages come back. If the user truly needs *substring*
("contains") search, that can't delegate against SharePoint — narrow the set another way first,
or raise it with `sharepoint-list-architecture` (indexing/redesign), not by cranking the limit.

---

## Forms & Patch — writing back to SharePoint

Two ways to write. **Use a Form control** (`SubmitForm`) for a standard edit screen; **use
`Patch`** for programmatic or partial writes.

**Form control flow:** set the form's `DataSource` and `Item`; the form shows New/Edit/View via
its `DefaultMode`. On the save button:

```powerapps
SubmitForm(frmEdit)
// then react in the form's OnSuccess / OnFailure, not inline:
//   OnSuccess: Notify("Saved", NotificationType.Success); Back()
//   OnFailure: Notify(frmEdit.Error, NotificationType.Error)
```

`SubmitForm` validates required fields, respects `DisplayMode`, and populates `frmEdit.Error` /
the `Errors(DataSource, record)` table for you. Read a field with `frmEdit.Updates` if you need
the staged values.

**Patch** — create or update explicitly. Create a record by patching `Defaults`:

```powerapps
// Create a new item; Defaults() seeds required/default column values:
Patch(
    Projects,
    Defaults(Projects),
    {
        Title: txtTitle.Text,
        Status: {Value: "Active"},          // Choice column = a record with .Value
        DueDate: dpDue.SelectedDate,
        Owner: {                            // Person column shape
            '@odata.type': "#Microsoft.Azure.Connectors.SharePoint.SPListExpandedUser",
            Claims: "i:0#.f|membership|" & gCurrentUser.Email,
            DisplayName: gCurrentUser.FullName,
            Email: gCurrentUser.Email
        }
    }
)
```

Update an existing record by patching the record itself instead of `Defaults`:

```powerapps
Patch(Projects, gallerySel.Selected, { Status: {Value: "Closed"} })
```

**Patch rules to hold:**
- Wrap outward writes in `IfError` and check the result — a failed `Patch` returns *blank* and
  its diagnostics land in `Errors(Projects)`.
- **Choice/Lookup/Person columns are records, not strings** — patch `{Value: "x"}`, not `"x"`.
- For **many** records prefer a Form or a scoped `Patch(list, table_of_records)` over `ForAll`
  with a `Patch` inside; the latter fires one request per row (network chatter) and doesn't
  delegate.

---

## Navigation & context

```powerapps
Navigate(DetailScreen, ScreenTransition.Cover, { locRecord: galItems.Selected })
```

Pass screen state as the **third argument** — it lands as context variables on the target
screen (here `locRecord`), which is cleaner than a global. `Back()` returns to the prior screen.
Don't overuse globals for screen-to-screen handoff; a Navigate context var is scoped and
self-documenting.

---

## Error handling

- **`IfError(risky, fallback)`** — evaluate a fallback when the first arg errors; the workhorse
  around Patch/Collect/remote calls.
- **`Notify(message, type)`** — user-facing banner (`Success`/`Error`/`Warning`/`Information`).
- **`Trace(...)`** — emit to Monitor for debugging without a visible UI.
- **`App.OnError`** — the global catch-all; log/notify here so nothing fails silently app-wide.

```powerapps
IfError(
    Patch(Projects, gSel, { Status: {Value: "Closed"} }),
    Notify("Couldn't save: " & FirstError.Message, NotificationType.Error)
)
```

---

## Performance

- **`Concurrent(...)`** — run independent startup fetches in parallel instead of serially:
  `Concurrent(ClearCollect(colA, ListA), ClearCollect(colB, ListB))`.
- **Cache read-mostly lists** with `ClearCollect(colRef, SmallLookupList)` once (in a named
  formula or `OnStart`), then reference the collection — avoids re-querying SharePoint on every
  screen. Only for small, slow-changing reference data; don't cache a list users edit live.
- **Compute once.** A `Filter` repeated across control properties runs each time — hoist it into
  a named formula or `With`.
- **Explicit Column Selection** (on by default) narrows the columns fetched — don't defeat it by
  pulling whole records you don't need.

---

## Watch Out

1. **Raising the data row limit to 2000 is not a delegation fix.** It hides the symptom, slows
   the app, and still breaks past 2000 rows. Fix the non-delegable clause instead.
2. **No delegation warning ≠ delegable.** The editor only warns when the source *might* exceed
   the limit. On a currently-small list a non-delegable `Search`/aggregate looks fine, then
   silently returns wrong results once the list grows. Reason from the matrix, not the underline.
3. **`ForAll` is not a `for` loop.** It's a *table transform* with no guaranteed order and no
   accumulator; a `Patch` or `Collect` inside it issues one call per row. Use it for genuine
   per-row shaping, not to "iterate and save" — batch with a single `Patch(list, records)`.
4. **Choice/Lookup/Person are complex types.** Comparing or patching them as plain strings fails
   or silently doesn't delegate. Use `.Value` to read a Choice, `{Value: ...}` to write it, and
   the Person/Claims record shape for people columns.

---

## Out of scope — defer these

- **Reviewing/auditing an existing app's formulas** for delegation, performance, or correctness
  → `power-fx-review`.
- **Building reusable canvas components** (custom controls, component libraries) and **HtmlText
  rich content** → `power-apps-components`.
- **Designing the SharePoint list itself** — columns, indexed columns, the 5000-item view
  threshold, lookup design → `sharepoint-list-architecture`.
- **Programmatic data access outside the app** (server-side, flows, bulk operations via
  Microsoft Graph) → `graph-api-integration`.
- **DAX** → `power-bi-dax`. **Power Query / M** → `power-query-m`. This skill is canvas Power Fx.
