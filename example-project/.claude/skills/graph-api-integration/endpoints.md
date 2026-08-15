# Microsoft Graph endpoints — SharePoint lists & items (cheat-sheet)

Sidecar for the `graph-api-integration` skill. All paths are **relative to the
service root `https://graph.microsoft.com/v1.0`** and every request needs an
`Authorization: Bearer {token}` header. Permissions follow **least-privilege** —
the "least" column is what the API doc marks as least-privileged; the "higher"
column is the next step up only if you genuinely need it. Delegated and
Application permissions are listed separately because they are *different grants*
(see the skill body for which OAuth flow yields which).

Legend: **D** = Delegated (work/school; personal MSA is not supported for these
SharePoint APIs). **A** = Application (app-only / daemon).

---

## Resolve the site (everything starts here)

| Operation | Method + path | D (least) | A (least) | Query params |
|---|---|---|---|---|
| Site by hostname + server-relative path | `GET /sites/{hostname}:/{server-relative-path}` | Sites.Read.All | Sites.Read.All | `$select` |
| Site by composite id | `GET /sites/{hostname},{spsite-id},{spweb-id}` | Sites.Read.All | Sites.Read.All | `$select` |
| Tenant root site | `GET /sites/root` | Sites.Read.All | Sites.Read.All | `$select` |
| Group's team site | `GET /groups/{group-id}/sites/root` | Sites.Read.All | Sites.Read.All | `$select` |
| Search for sites by keyword | `GET /sites?search={query}` | Sites.Read.All | Sites.Read.All | free-text search; sort only by `createdDateTime`. **Not supported with `Sites.Selected`.** |

> The path form `{hostname}:/{path}` maps to an `SPWeb`. Chain another colon to
> jump back to the resource model, e.g.
> `/sites/contoso.sharepoint.com:/teams/hr:/lists`. The response's `id` is the
> `{site-id}` used by every path below — cache it.

## Lists

| Operation | Method + path | D (least) | A (least) | Query params |
|---|---|---|---|---|
| Enumerate lists on a site | `GET /sites/{site-id}/lists` | Sites.Read.All | Sites.Read.All | `$select`, `$filter`, `$expand=columns` |
| Get one list | `GET /sites/{site-id}/lists/{list-id}` | Sites.Read.All | Sites.Read.All | `$select`, `$expand=columns` |
| Get list by display name | `GET /sites/{site-id}/lists/{list-name}` | Sites.Read.All | Sites.Read.All | `list-id` may be the GUID **or** the list's display name |

## List items (the CRUD core)

| Operation | Method + path | D (least) | A (least) | Query params |
|---|---|---|---|---|
| List items | `GET /sites/{site-id}/lists/{list-id}/items` | Sites.Read.All | Sites.Read.All | `$expand=fields`, `$expand=fields(select=Col1,Col2)`, `$top`, `$orderby` |
| Get one item + fields | `GET /sites/{site-id}/lists/{list-id}/items/{item-id}?expand=fields` | Sites.Read.All | Sites.Read.All | `$expand=fields`, `$select` |
| **Filter** on a column | `GET /sites/{site-id}/lists/{list-id}/items?expand=fields&$filter=fields/Status eq 'Open'` | Sites.Read.All | Sites.Read.All | see the `$filter` note below |
| Create an item | `POST /sites/{site-id}/lists/{list-id}/items` | Sites.ReadWrite.All | Sites.ReadWrite.All | body: `{"fields": { … }}` |
| Update column values | `PATCH /sites/{site-id}/lists/{list-id}/items/{item-id}/fields` | Sites.ReadWrite.All | Sites.ReadWrite.All | body: a `fieldValueSet`; `if-match: {etag}` optional (→ `412` on mismatch) |
| Update item props | `PATCH /sites/{site-id}/lists/{list-id}/items/{item-id}` | Sites.ReadWrite.All | Sites.ReadWrite.All | `if-match: {etag}` optional |
| Delete an item | `DELETE /sites/{site-id}/lists/{list-id}/items/{item-id}` | Sites.ReadWrite.All | Sites.ReadWrite.All | returns `204 No Content` |
| Track changes (sync) | `GET /sites/{site-id}/lists/{list-id}/items/delta` | Sites.Read.All | Sites.Read.All | returns `@odata.deltaLink`; replay with `?token={deltaToken}` or `?token=latest` |

## Scoped access — `Sites.Selected`

| Concern | Detail |
|---|---|
| Identifiers | Application: `883ea226-0bf2-4a8f-9f9d-92c9162a727d` · Delegated: `f89c84ef-20d0-4b54-87e9-02e856d66d53` |
| What it does | Grants the app access to **only the specific site collections** an admin has assigned it in SharePoint — nothing tenant-wide. Preferred over `Sites.Read.All`/`Sites.ReadWrite.All` for a solution that touches a known handful of sites. |
| Granting per-site roles | An admin writes a permission entry per site (`POST /sites/{site-id}/permissions`) with `read` / `write` / `fullcontrol` / `owner` roles. Doing the grant itself requires `Sites.FullControl.All` (and, delegated, a site-collection admin). |
| Hard limitation | An app holding **only** `Sites.Selected` **cannot list or search sites** (`GET /sites?search=` fails) — you must already know the site id or URL. Resolve the id out-of-band or via the path addressing above. |

## Batch & service root

| Operation | Method + path | Notes |
|---|---|---|
| JSON batch | `POST /$batch` | Up to **20** sub-requests. Each sub-request needs `id`, `method`, `url` (relative, no host), optional `headers`/`body`. Permissions are evaluated **per sub-request** (each needs its own scope). |

---

## `$expand` / `$select` / `$filter` notes

- **`$expand=fields`** is what surfaces the actual column values (`Title`,
  custom columns). Without it you get item metadata (`id`, `createdDateTime`,
  `eTag`) but no field data. Narrow it with `fields(select=Col1,Col2)` to shrink
  the payload.
- **`$select`** trims the top-level `listItem` properties. Combine with the
  expand-select to fetch only what you render — the single biggest lever against
  throttling.
- **`$filter` on list items must target `fields/{internalName}`**, e.g.
  `$filter=fields/Status eq 'Open'`. Most field filters also require the request header
  **`Prefer: HonorNonIndexedQueriesWarningMayFailRandomly`** — without it, filtering a
  **non-indexed** column (or any list over the 5,000-item view threshold) returns
  **HTTP 400**. Indexing the column is the durable fix; the header is what lets the query
  run at all. String equality is **case-insensitive** (SharePoint text `eq` ignores case);
  use the column's **internal name**, not its display name.
- Column **internal names** differ from display names (spaces become `_x0020_`,
  a renamed column keeps its original internal name). Read them from
  `GET …/lists/{list-id}/columns` when a `$filter`/`$select` silently returns
  nothing.
