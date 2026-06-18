# 2026-06-18 21:40 · optimize-agent-authoring-family

**Goal:** Dedupe agent-authoring skill family + trim eager descriptions

## What happened
- Second factory-efficiency review (after PR #7 merged). Three Explore agents audited
  skills / commands+workflows / hooks. Most findings were either negligible micro-perf
  or collided with design — scoped down to the two real levers.
- **Sibling dedup (Moderate, user-chosen):** in `developer-`, `product-manager-`, and
  `knowledge-agent-authoring`, replaced each re-derived "Is a [domain] agent the right
  tool?" table with a short pointer to `agent-authoring`'s *Is an agent even the right
  tool?* (keeping only the one domain distinction); replaced the inlined base-checklist
  re-listing with "Passes the base `agent-authoring` checklist."; compressed the
  "Start with agent-authoring" intro block to one sentence.
- **Description trim (careful, user-chosen):** all 4 agent-authoring descriptions —
  cut trailing disclaimers already covered by each skill's Out-of-scope; kept every
  "Trigger on phrases like…" list intact (triggering preserved). Descriptions load
  eagerly into every session, so this is a recurring per-session context saving.
- **Trivial:** removed the double `merge_fragments()` call in `build-hooks.py:mode_build`
  (factory + example-project copies kept byte-identical).
- Net −37 lines; settings.json unchanged; all cross-refs resolve.

## Gotchas & dead ends
- Deliberately did NOT "fix" several agent-flagged items: example-project script
  duplication (intentional — it's a copyable showcase), hook micro-perf (runs once per
  lifecycle event), and command placement boilerplate (factoring to README adds a
  read-indirection; inlining ~4 lines is cheaper).
- The base `agent-authoring/SKILL.md` is the single source of truth — its body was NOT
  changed structurally; siblings now point to it instead of restating.

## State at end
- Branch `claude/optimize-factory-model` (re-cut from merged main). Changes committed
  + pushed. No PR opened yet.
- agent-authoring family is now base + clean delta; the authoring checklist exists in
  exactly one place (the base).

## Open threads
- Planned meta-skills still unwritten: `skill-authoring`, `context-vs-skill`.
- Planned commands: `/validate-asset`, `/add-context`.
