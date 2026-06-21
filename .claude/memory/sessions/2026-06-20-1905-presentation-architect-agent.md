# 2026-06-20 19:05 · presentation-architect-agent

**Goal:** Add presentation-architect agent (objective presentation-flow brain) to example-project

## What happened
- Built `example-project/.claude/agents/presentation-architect.md` — a new member of the
  objective / defer-the-how agent family (sibling of `data-analyst` + `software-architect`).
- It designs the *flow* of communication artifacts (decks, brochures, one-pagers, reports):
  audience+goal, narrative arc, message hierarchy, ordered per-unit content spec, reading
  path, CTA placement. Format- and tool-agnostic; defers the subjective *how* (visual design,
  final copy, authoring tool) to a design/content executor or skill.
- Frontmatter matches siblings: `tools: Read, Grep, Glob, Bash`, `permissionMode: plan`,
  `model: opus`. Same body shape (objective/subjective boundary → Method → Guardrails → Output).
- Registered in `example-project/.claude/agents/README.md` and `example-project/CLAUDE.md`.
- User chose name `presentation-architect` (over narrative-architect / communication-designer)
  and the defer-the-how scope (over flow+final-copy) via AskUserQuestion.
- Opened PR #16. Then (same session) built the two executor skills the agent defers to,
  completing the pipeline: `presentation-architect` (objective flow) → `presentation-design`
  (subjective visual + copy design *how*, format-spanning, tool-agnostic; emits a design spec)
  → `deck-builder` (execution: assemble a real deck file in a tool — pptx/python-pptx, Google
  Slides, Beamer, Marp/reveal.js — verified). Mirrors data-analyst → viz skill → developer agent.
- Registered both skills in `example-project/CLAUDE.md`; pointed the agent's hand-off line at
  them; widened PR #16 title/body to cover the agent + both skills.

## Gotchas & dead ends
- Branch `claude/presentation-flow-agent-ml1wuq` already existed; just checked it out.
- I'd phrased the follow-up as "`presentation-design`/`deck-builder`" (an *or*); user read it
  as two skills and asked for both. Built both — clean three-tier split with no overlap.

- Then added the **format-specific build tier** below `presentation-design`: `one-pager-builder`
  (flat page; bleed/print-vs-screen), `brochure-builder` (folded sheet; fold imposition — panels
  print in fold-position order, tuck-in panel narrower), `pamphlet-builder` (booklet; pages ×4,
  author-in-reader-order + tool imposes, gutter/creep). User chose **three separate skills** via
  AskUserQuestion (over one consolidated builder or a folded/flat split) — accepted overlap for
  specificity. Differentiated each by its real format-specific build concern. Generalized
  `presentation-design` downstream refs + the agent hand-off to the whole builder family.
- Subscribed to PR #16 activity (CI + reviews) at user's request.

## State at end
- **PR #16 MERGED** — full presentation pipeline now on `main`. Session auto-unsubscribed.
- Pipeline complete: presentation-architect → presentation-design → {deck,one-pager,brochure,pamphlet}-builder.
- Repo has no CI workflows (get_check_runs = 0); no review comments. `send_later` not available this session.

## Open threads
- Possible future: a `report-builder` (long-form/multi-section document) if reports need a build
  tier distinct from pamphlet-builder; `presentation-design` already covers report *design*.
- Offered to open a PR / watch CI — awaiting user.
</content>
