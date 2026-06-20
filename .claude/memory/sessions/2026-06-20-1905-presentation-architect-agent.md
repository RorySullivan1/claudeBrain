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

## Gotchas & dead ends
- Branch `claude/presentation-flow-agent-ml1wuq` already existed; just checked it out.

## State at end
- Committed + pushed to `claude/presentation-flow-agent-ml1wuq`. No PR opened (not requested).

## Open threads
- No companion executor exists yet for the hand-off target. Natural follow-up: a
  `presentation-design`/`deck-builder` **skill** that owns the visual/copy *how*.
- Offered to open a PR / watch CI — awaiting user.
</content>
