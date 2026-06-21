# 2026-06-21 12:06 · branding-skill

**Goal:** Add upstream branding skill; presentation-design inherits the brand

## What happened
- Built `example-project/.claude/skills/branding/SKILL.md` — a **single** skill (not fragmented
  into logo/color/voice) covering the four pillars: strategy, verbal identity, visual identity,
  governance. Positioned **upstream** of the presentation pipeline as the durable, reusable identity
  that feeds *all* channels (decks, print, web, social, email, signage) — not folded into
  presentation-design.
- Wired the boundary: `presentation-design`'s "design system" section now **inherits** the brand
  (palette/type/logo/voice) when one exists, ad-hoc only as a fallback; updated its description +
  "where this sits" + input bullet. voice/tone: branding sets principles, presentation-design's
  copy craft applies them (explicit cross-ref, no dup).
- Registered under a new **Branding** line in `example-project/CLAUDE.md`.
- Branch `claude/branding-skill` off main; opened **PR #17**.

## Decisions
- User chose name `branding` (over `brand-identity`).
- One skill, not many: per skill-distiller de-dup logic, the four pillars are tightly coupled and
  defined/applied together; fragmenting would repeat triggers/bodies.
- Standalone, not inside presentation-design: a brand is reused across all channels, so it's a
  higher tier; presentation-design's per-artifact design-system inherits from it.

## Gotchas & dead ends
- presentation-design/INDEX/session files had been edited by user/linter before this session;
  read current state before editing, preserved their changes.

## State at end
- All committed + pushed to `claude/branding-skill`; PR #17 open (not yet watched).

## Open threads
- Possible future: extend `branding` reach to non-presentation channels via dedicated builders
  (web/email/social) if those get added; for now branding just feeds presentation-design + builders.
- Still open from prior: a `report-builder` for long-form docs.
</content>
