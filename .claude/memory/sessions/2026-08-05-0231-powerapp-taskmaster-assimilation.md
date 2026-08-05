# 2026-08-05 02:31 · powerapp-taskmaster-assimilation

**Goal:** Pull useful Claude assets from powerapp-taskmaster into claudeBrain (blocked on repo access)

## What happened
- Shipped earlier this session: PR #27 (vba-addin-building skill) → merged; PR #28
  (Power Platform skill family, 8 skills + 2 sidecars) → merged; PR #29 (VBA skill example
  correctness fixes) → merged; PR #30 (4 fixes across vba-addin-building, vba-code-test-writing,
  goal-auditor, roadmap_guard) → open.
- New request: review `powerapp-taskmaster` repo, extract/normalize/assimilate its Claude assets
  into claudeBrain. **Could not start — repo is unreachable from this session.**

## Gotchas & dead ends
- Session GitHub scope is HARD-LOCKED to `rorysullivan1/claudebrain`. `mcp__github__get_file_contents`
  on `RorySullivan1/powerapp-taskmaster` → "Access denied: repository is not configured for this session."
- `add_repo` (Claude_Code_Remote) that would attach another repo is NO LONGER available this session.
- `add_repo` earlier returned "not found / no access" for `rorysullivan1/powerapp-taskmaster` — the
  exact owner/name spelling is also unconfirmed.
- Verified-wrong review finding worth remembering: `Table.StopFolding` IS a real Power Query M
  function (Microsoft Learn) — do not "fix" power-query-m to remove it.

## State at end
- Blocked awaiting user to either (a) add `RorySullivan1/powerapp-taskmaster` to this session's
  allowed repos (and confirm exact name), or (b) upload/paste its `.claude/` tree.

## Open threads
- **When access lands, run this plan:** inventory & triage assets (drop project-specific glue) →
  review each vs house authoring standards (skill-authoring/agent-authoring) + fact-check Power
  Platform claims vs Microsoft Learn → normalize (folder==name frontmatter, description
  trigger/boundary lines, sidecars over context docs, kebab-case) → ASSIMILATE not duplicate
  (fold Power Fx/SharePoint/Graph overlaps into existing `power-fx-development`,
  `sharepoint-list-architecture`, `graph-api-integration`, etc.; net-new only where nothing
  covers it) → land on a fresh branch off main with a PR.
- Existing Power Platform family to reconcile against: power-fx-development (+delegation.md),
  power-apps-components, power-fx-review, sharepoint-list-architecture, sharepoint-column-formatting,
  graph-api-integration (+endpoints.md), power-bi-dax, power-query-m.
