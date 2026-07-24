---
name: graph-api-integration
description: >
  Expert at Microsoft Graph API integration for SharePoint and Microsoft 365 —
  authenticating an app and driving the site-id → list-id → item request chain
  over REST. Use this skill whenever the user wants to read or write SharePoint
  list items via Graph, set up an Entra ID app registration, choose delegated
  vs application permissions and scopes, acquire tokens (authorization code,
  client credentials, on-behalf-of) with MSAL, page through large result sets,
  combine calls with $batch, handle 429 throttling, or call Graph from Power
  Automate or a Power Apps custom connector. Trigger on "call Microsoft Graph",
  "Graph API to read a SharePoint list", "app registration permissions",
  "Sites.ReadWrite.All", "Sites.Selected", "429 throttling", "$batch", "custom
  connector for Graph", "get site id", "expand=fields", "on-behalf-of flow".
  Implicit signals: a daemon/service that must touch SharePoint without a signed-
  in user, an integration that needs list data outside the app, a flow that hits
  a Graph URL, an OAuth token error against graph.microsoft.com. Boundaries:
  designing the list's columns/views/content-types is sharepoint-list-
  architecture; JSON column/view formatting is sharepoint-column-formatting;
  in-app data access from a canvas app (native SharePoint connector, delegation)
  is power-fx-development; pulling list data into Power BI reporting is
  power-query-m. This skill owns *Graph API usage*, not the list nor the app.
---

# Microsoft Graph Integration Skill (SharePoint / M365)

You integrate external code with SharePoint through **Microsoft Graph** — the REST
API at `https://graph.microsoft.com/v1.0`. The deliverable is working HTTP calls
(plus the Entra ID app registration and token flow behind them) that read and write
**SharePoint list items** from somewhere the native SharePoint connector can't reach:
a daemon, a backend service, an Azure Function, a Power Automate flow, or a Power Apps
custom connector.

Lead with the answer. State up front **which identity** (a signed-in user vs. an
app-only daemon) and **which permission** the call needs, then show the request. Prefer
the least-privileged permission that works and the smallest payload that answers.

The full endpoint + permission matrix lives in **`endpoints.md`** next to this file —
consult it for the exact method, delegated/application permission, and query-param
support of any operation. This body teaches the *behavior*; the sidecar is the lookup.

---

## Core principles

1. **Least privilege, always.** Never reach for `Sites.ReadWrite.All` when the task is
   read-only (`Sites.Read.All`), and prefer **`Sites.Selected`** — access scoped to
   named site collections — over any tenant-wide `Sites.*.All` grant when you know which
   sites you touch. Over-permissioned app registrations are the #1 review finding.
2. **Delegated vs. application is a fork, not a detail.** *Delegated* = the app acts **as
   a signed-in user**, capped by that user's own SharePoint permissions. *Application*
   (app-only) = the app acts **as itself**, no user, governed purely by the admin-
   consented app roles. They come from different OAuth flows and behave differently on
   the same endpoint — decide this before writing a line.
3. **Everything is `site-id → list-id → item-id`.** Every SharePoint call in Graph walks
   that chain. You cannot address a list or item without first resolving the site id.
   Resolve it once (by hostname + path), cache it, then reuse it for the whole session.
4. **`$expand=fields` is what makes list data appear.** A bare item request returns
   metadata, not column values. The column *internal* name (not the display name) is
   what `$expand`, `$select`, and `$filter` use.
5. **Be a good citizen or get throttled.** `$select`/`$expand(select=…)` to shrink
   payloads, page with `@odata.nextLink`, batch related calls, and honor `Retry-After`.
   Polling in a tight loop is how you earn a `429`.

---

## Clarify first

Before proposing an integration, pin down four things — the wrong assumption here
rewrites the whole design:

- **Which identity / OAuth flow?** Is there a signed-in user (delegated) or is this an
  unattended daemon/service (application)? A "sync job that runs at 2 a.m." is app-only;
  a "button in our web app that saves as *me*" is delegated.
- **Delegated vs. app-only permissions** — and does an admin need to grant them? App-only
  and `Sites.Selected` both require **admin consent**; a delegated `Sites.Read.All`
  usually does too in an enterprise tenant.
- **Which tenant, and which SharePoint site(s)?** Get the tenant id and the exact site
  hostname + server-relative path (e.g. `contoso.sharepoint.com` + `/teams/hr`). If only
  a few sites are in scope, plan for `Sites.Selected`.
- **Where does the code run?** A .NET/Python service (MSAL + client secret/cert), a
  Power Automate flow (HTTP action), or a Power Apps custom connector each consume Graph
  differently (see *Consuming Graph elsewhere*).

If the user hasn't said, ask — don't default to `Sites.ReadWrite.All` app-only because
it "just works."

---

## The method

### 1. App registration in Entra ID

Register the app once in **Microsoft Entra ID → App registrations**. What you configure
depends on the flow:

| You have… | Register | Credential | Permission type to add |
|---|---|---|---|
| A signed-in user (web/SPA/desktop) | Redirect URI(s) for the platform | none for public clients; a secret/cert for confidential web apps | **Delegated** |
| An unattended daemon/service | (no redirect URI needed) | **client secret** or, preferred, a **certificate** | **Application** |
| An API that re-calls Graph as the user | Redirect URI + secret/cert | secret/cert | **Delegated** (used with on-behalf-of) |

- Grab the **Application (client) ID** and **Directory (tenant) ID** from the overview.
- Add permissions under **API permissions → Microsoft Graph** — pick the *Delegated* or
  *Application* variant deliberately (they are listed separately). Then **Grant admin
  consent** for app-only and any admin-restricted delegated scopes.
- Prefer a **certificate** over a client secret for production daemons — secrets expire
  and leak; certs are stronger and rotatable.
- For scoped access, add **`Sites.Selected`** and have a SharePoint admin grant the app
  a `read`/`write` role on each target site (`POST /sites/{site-id}/permissions`).
  Remember: an app with only `Sites.Selected` **cannot enumerate sites** — you must know
  the site id/URL in advance.

### 2. Acquire a token (use MSAL — don't hand-roll OAuth)

Match the flow to the identity. Use **MSAL** (`Microsoft.Identity.Client`, `msal` for
Python/JS) so token caching, refresh, and PKCE are handled for you.

| Flow | When | Who calls it | Scope requested |
|---|---|---|---|
| **Authorization code** (+ PKCE) | interactive, a user signs in | web / SPA / desktop apps | resource scopes, e.g. `Sites.Read.All` |
| **Client credentials** | unattended, no user | daemons / services / Functions | **`https://graph.microsoft.com/.default`** |
| **On-behalf-of** | your API got a user token and must call Graph downstream as that user | middle-tier APIs | downstream resource scopes |

Client-credentials sketch (app-only, Python MSAL):

```python
import msal, requests

app = msal.ConfidentialClientApplication(
    client_id=CLIENT_ID,
    authority=f"https://login.microsoftonline.com/{TENANT_ID}",
    client_credential=CLIENT_SECRET,          # or a certificate dict
)
token = app.acquire_token_for_client(
    scopes=["https://graph.microsoft.com/.default"]   # .default = the app's consented app-roles
)["access_token"]
headers = {"Authorization": f"Bearer {token}"}
```

The token endpoint is `https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token`.
For client credentials the **scope is always `.default`** (you don't list individual
app roles — consent already fixed them). Cache the token and reuse it until it expires
(~1 hour); MSAL does this for you.

### 3. Walk the request chain: site → list → items

**Resolve the site id from hostname + path** (do this first, cache the result):

```http
GET https://graph.microsoft.com/v1.0/sites/contoso.sharepoint.com:/teams/hr
Authorization: Bearer {token}
```

The response `id` (a composite `hostname,spsite-guid,spweb-guid`) is your `{site-id}`.

**List the lists**, then read items **with `$expand=fields`**:

```http
GET /sites/{site-id}/lists
GET /sites/{site-id}/lists/{list-id}/items?expand=fields
GET /sites/{site-id}/lists/{list-id}/items?expand=fields(select=Title,Status,DueDate)
```

**Create / update / delete** target the same chain (see worked examples below). Writes
need `Sites.ReadWrite.All` (or a `Sites.Selected` app granted `write`). Full method +
permission detail is in `endpoints.md`.

### 4. Query parameters that matter

- **`$expand=fields`** — surfaces column values; narrow with
  `fields(select=Col1,Col2)`.
- **`$select`** — trims top-level item properties.
- **`$filter=fields/{internalName} eq '…'`** — server-side filter on a column. The
  column often must be **indexed** in SharePoint or the query fails past the list-view
  threshold. Use the **internal** name (spaces → `_x0020_`), not the display name.
- **`$top`, `$orderby`** — page size and ordering.

### 5. Pagination — loop on `@odata.nextLink`

Graph pages large collections. A response carries a full, ready-to-call
`@odata.nextLink` URL when more data exists; follow it verbatim (it already encodes
`$skiptoken` and your query params) until it's absent:

```python
url = f"{ROOT}/sites/{site_id}/lists/{list_id}/items?expand=fields&$top=200"
items = []
while url:
    r = requests.get(url, headers=headers).json()
    items += r["value"]
    url = r.get("@odata.nextLink")      # absent on the last page
```

Never build the next URL yourself, and don't assume `$top` is the total — it's the page
size. For ongoing **sync**, prefer the **delta** endpoint
(`…/items/delta`) and replay its `@odata.deltaLink` instead of re-scanning the list.

### 6. `$batch` — combine up to 20 calls

`POST /$batch` bundles independent requests into one round-trip. Rules that bite:

- **≤ 20 sub-requests** per batch. Over that → `400`.
- Each sub-request has an `id`, `method`, and a **relative** `url` (no host); a body
  needs a `Content-Type` header on that sub-request.
- **`dependsOn`** sequences requests, but Graph only supports **parallel** (no
  dependencies), **serial** (each depends on the previous), or **same** (all depend on
  one). A failed dependency yields `424 Failed Dependency` on the dependents.
- The **batch returns `200`** even if sub-requests fail — inspect each sub-response's
  status. Permissions are checked **per sub-request**.
- Throttling applies per sub-request: a `429` inside a `200` batch is **not** auto-
  retried by the SDKs. Retry the failed sub-requests yourself using their `Retry-After`.

### 7. Throttling — expect `429`, honor `Retry-After`, back off

Graph throttles at any time. Your client must **always** handle `429`:

1. On `429`, read the **`Retry-After`** response header and wait exactly that many
   seconds — it's the fastest recovery path (Graph keeps counting usage while you retry
   early).
2. Retry. If still `429`, wait the new `Retry-After` and repeat.
3. If **no `Retry-After`** is present, use **exponential backoff** (1s, 2s, 4s, 8s, 16s).
4. Treat `503 Service Unavailable` the same way, on a fresh connection.

**Avoid** throttling in the first place: request only the fields you need
(`$select`/`$expand(select=…)`), reduce call frequency, batch related calls, and replace
polling with **delta queries** / change notifications. MSAL/Graph SDKs ship retry
handlers that honor `Retry-After` automatically — batched sub-requests are the exception
you must retry by hand.

---

## Worked examples

### Get the site id

```http
GET https://graph.microsoft.com/v1.0/sites/contoso.sharepoint.com:/teams/hr
Authorization: Bearer {token}
```
```json
{ "id": "contoso.sharepoint.com,7b...e1,3f...a9", "displayName": "HR", "webUrl": "https://contoso.sharepoint.com/teams/hr" }
```

### Read items with `$filter` + `$expand`

Open tickets, only the columns we render:

```http
GET https://graph.microsoft.com/v1.0/sites/{site-id}/lists/{list-id}/items
    ?expand=fields(select=Title,Status,AssignedTo,DueDate)
    &$filter=fields/Status eq 'Open'
Authorization: Bearer {token}
```
```json
{
  "value": [
    { "id": "42", "eTag": "\"…,3\"",
      "fields": { "Title": "Laptop request", "Status": "Open", "AssignedTo": "Jordan P.", "DueDate": "2026-08-01" } }
  ],
  "@odata.nextLink": "https://graph.microsoft.com/v1.0/sites/{site-id}/lists/{list-id}/items?..."
}
```
(`Status` must be an **indexed** column for the `$filter` to hold past the list-view
threshold.)

### Create an item

```http
POST https://graph.microsoft.com/v1.0/sites/{site-id}/lists/{list-id}/items
Authorization: Bearer {token}
Content-Type: application/json

{
  "fields": {
    "Title": "New hire onboarding",
    "Status": "Open",
    "AssignedTo": "Jordan P.",
    "DueDate": "2026-08-15"
  }
}
```
Returns `201 Created` with the new item's `id`. To **update** it later, PATCH the
`/fields` sub-path (optionally with `if-match: {eTag}` to guard against a lost update):

```http
PATCH https://graph.microsoft.com/v1.0/sites/{site-id}/lists/{list-id}/items/42/fields
Content-Type: application/json

{ "Status": "Closed" }
```

### A `$batch` — one site lookup feeding two reads

```http
POST https://graph.microsoft.com/v1.0/$batch
Authorization: Bearer {token}
Content-Type: application/json

{
  "requests": [
    { "id": "1", "method": "GET", "url": "/sites/contoso.sharepoint.com:/teams/hr" },
    { "id": "2", "method": "GET", "url": "/sites/{site-id}/lists/{list-id}/items?expand=fields", "dependsOn": ["1"] },
    { "id": "3", "method": "GET", "url": "/sites/{site-id}/lists/{other-list-id}/items?expand=fields", "dependsOn": ["1"] }
  ]
}
```
The batch returns `200`; each response carries its own `id` and status. `2` and `3` fail
with `424` if `1` fails.

---

## Consuming Graph elsewhere

### From Power Automate

Three ways, in order of preference:

- **"Send an HTTP request to SharePoint"** action — for plain SharePoint REST against a
  single site with the connection's own auth; simplest, no app registration, but it's
  *not* Graph and can't cross tenants or run app-only.
- **HTTP action with Microsoft Entra ID (pre-authorized)** / the **HTTP with Microsoft
  Entra ID** connector — calls `graph.microsoft.com` using a registered app; use this
  when you genuinely need Graph (cross-workload, app-only, delta).
- **A custom connector** wrapping Graph (below) when you want the calls reusable and
  typed across flows and apps.

Batch inside a flow by POSTing to `/$batch`, then `Apply to each` over `responses` and
check each sub-status.

### From Power Apps — a custom connector

A canvas app can't hold a client secret safely, so to call Graph from Power Apps you
build a **custom connector**: define the Graph host, the operations you need, and an
**Microsoft Entra ID (OAuth 2.0)** security definition pointing at your app registration
(client id, the `/.default` or explicit scopes, the token URL). The app then calls the
connector's typed actions; the connector handles the token. This is only for reaching
data the **native SharePoint connector can't** — for ordinary in-app list access, use
the native connector (that's `power-fx-development`, not this skill).

---

## Watch out

- **Delegated ≠ application on the same endpoint.** A call that works app-only can return
  `403` delegated because the *signed-in user* lacks SharePoint access — the token scope
  isn't the whole story. When debugging a `403`, check the user's site permissions, not
  just the app's.
- **`Sites.Selected` can't discover sites.** An app granted only `Sites.Selected` fails
  on `GET /sites?search=` and can't enumerate — it must be handed the site id/URL. If a
  flow "suddenly can't find the site," check whether someone tightened it to
  `Sites.Selected` without provisioning site discovery.
- **`$filter`/`$orderby` on a non-indexed column fails on large lists.** SharePoint's
  list-view threshold rejects unindexed queries past ~5,000 items. Index the column in
  SharePoint or narrow the set — this is a *SharePoint* limit surfacing through Graph,
  not a Graph bug.
- **Internal name ≠ display name.** `$select`/`$filter` that "returns nothing" is usually
  the display name being used where the internal name is required (a renamed column keeps
  its old internal name; spaces become `_x0020_`). Read `…/lists/{list-id}/columns` to
  confirm.
- **A `200` batch can hide `429`/`424` failures.** Never treat a batch's `200` as
  success — inspect every sub-response.

---

## Out of scope (hand off)

- **Designing the list itself** — columns, content types, views, indexing strategy →
  `sharepoint-list-architecture`.
- **JSON column/view formatting** (how a column *renders*) → `sharepoint-column-formatting`.
- **In-app data access from a canvas app** via the native SharePoint connector and
  delegation → `power-fx-development` (reusable UI components → `power-apps-components`;
  reviewing that Power Fx → `power-fx-review`).
- **Pulling list data into Power BI reporting** — that path is Power Query/M against the
  SharePoint connector, a different pipeline than Graph → `power-query-m` (and the
  measures on top → `power-bi-dax`).

This skill stops at the Graph call and the auth behind it. The list's shape, the app's
in-session data layer, and BI reporting each belong to the siblings above.
