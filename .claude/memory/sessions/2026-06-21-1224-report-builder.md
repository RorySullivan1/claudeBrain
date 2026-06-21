# 2026-06-21 12:24 · report-builder

**Goal:** Add report-builder skill (long-form document build tier)

## What happened
- Built `example-project/.claude/skills/report-builder/SKILL.md` — fifth member of the
  format-specific build tier (after deck/one-pager/brochure/pamphlet). Long-form multi-page
  documents: research reports, whitepapers, annual reports, proposals, manuals.
- Format-specific concerns: generated ToC/numbering/cross-refs/lists/index, long text flow
  (headers/footers, page numbers, section breaks, widow/orphan, footnotes, citations/bibliography),
  tooling (Word/python-docx, LaTeX, Typst, Quarto/Pandoc, HTML→PDF/WeasyPrint, Google Docs).
- Per the earlier agent-vs-skill discussion: kept it a **skill**; the one high-volume risk (big
  builds) is handled by an explicit "delegate the verbose build to `token-manager`" section, not by
  making the asset an agent.
- Defers structure→presentation-architect, design+prose→presentation-design, identity→branding.
- Registered in CLAUDE.md Presentation line + agent hand-off. Branch off main; opened **PR #18**.

## Decisions
- Agent vs skill → **skill** (symmetry with builder family; renders upstream-provided content, so
  not inherently context-flooding; per-job verbosity handled via token-manager delegation).
- User first named it `long-form-report-building`, then asked to **rename for consistency** → renamed
  to `report-builder` (folder + `name:` + title) to match the `*-builder` family.

## Gotchas & dead ends
- Branch name is `claude/long-form-report-building` (created before the rename); skill is
  `report-builder`. Harmless mismatch; PR #18 title/refs use report-builder.
- Branched off main (PR #17 branding not merged), so this PR doesn't touch presentation-design —
  avoids conflicts with #17. presentation-design's downstream builder list still omits report-builder;
  append it whenever #17/#18 land (minor).

## State at end
- All committed + pushed to `claude/long-form-report-building`; PR #18 open. PR #17 (branding) still open.

## Open threads
- After #17 + #18 merge: add `report-builder` to presentation-design's "Defer downstream" list (minor).
- Possible future: web/email/social builders if those channels come in-scope (branding already feeds all).
</content>
