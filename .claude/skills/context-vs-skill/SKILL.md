---
name: context-vs-skill
description: >
  Decide WHERE a piece of durable knowledge belongs: a triggered skill, a passive
  context doc, CLAUDE.md, or a reference note. Use whenever you're authoring or
  curating factory assets and must place guidance — "should this be a skill or a
  context doc", "where does this knowledge go", "skill vs context", "is this a brief
  or a skill", "we have the same guidance in two places", "this overlaps an existing
  skill", or you're about to write a how-to into a context brief (or facts into a
  skill). Resolves duplication where a context brief and a skill teach the same
  thing. This is the focused skill-vs-context placement call; defer the broader
  routing across memory/CLAUDE.md/notes to knowledge-router, and the mechanics of
  writing a SKILL.md to skill-authoring.
---

# Context vs Skill

The placement decision: a given piece of durable knowledge has exactly **one** right
home. Get it wrong and you either bury behavior where it never fires, or duplicate the
same guidance in two files that then drift apart. This skill is the **skill-vs-context**
call specifically — the boundary that the VBA assets in this repo blur. For the wider
"where does any knowledge go" routing (memory, CLAUDE.md, a reference note, drop it),
that's `knowledge-router`; for how to actually write the `SKILL.md` once you've decided,
that's `skill-authoring`. This skill owns the seam between those two.

## The four homes (and what each one *is*)

| Home | What it is | Loaded | Holds |
|---|---|---|---|
| **Skill** | Triggered **behavior** — how to think/act for a recurring task | Auto, by `description:` when relevant (or `/<name>`) | Procedures, recipes, judgment, "do this / not that" |
| **Context doc** | Passive **reference** — a stack brief or a fact card | Deep-read on demand (or surfaced via `INDEX.md`) | Specs, tables, version facts, orientation, rationale |
| **CLAUDE.md** | The always-on **session contract** | Every session, always | Only what's true *every* session — short, universal rules |
| **Reference note** | A small declarative **card** in `context/notes/` | On demand; catalogued in always-loaded `INDEX.md` | One stable cross-cutting fact/concept/schema |

The line that matters most: a **skill is behavior** (it *fires* and changes how Claude
works), a **context doc is reference** (it *sits there* until something reads it). Same
words can be either — what differs is whether they're meant to *trigger and act* or to
*be looked up*.

## The decision procedure

Run these in order. The first clear "yes" places it.

1. **Is it true every single session?** → **CLAUDE.md.** (e.g. "Office is
   Click-to-Run"; "format with ruff before commit".) If it's only *sometimes*
   relevant, it doesn't belong in the always-on contract — keep going.
2. **Is it "how to *do* X" — a procedure, a recipe, judgment you want applied?**
   → **skill.** It needs to *fire by trigger* and shape the work in-session.
3. **Is it "facts *about* X" — a spec, a table, a version range, an orientation you'd
   *pull up while reading around a topic*?** → **context.** Then size it: a single
   stable cross-cutting card → **reference note** (`context/notes/` + INDEX); a longer
   whole-stack operating brief → a **flat `context/<name>.md` doc**.
4. **Still unsure between skill and context?** Ask: *would I want this to interrupt and
   guide me unprompted (skill), or only when I deliberately go looking (context)?*
   Behavior that should fire on its own is a skill; lookup material is context.

Two litmus phrasings that cut fast:
- **"how to" → skill; "facts about" → context.**
- **"fires by trigger" → skill; "pulled when reading around the topic" → context.**

## The failure mode: the same guidance in both

The trap this skill exists to prevent: putting the **same** how-to in a context brief
**and** a skill. This repo has a live example. Compare:

- `example-project/.claude/context/vba-development.md` — a context **brief**, and
- `example-project/.claude/skills/vba-development/SKILL.md` — a **skill**.

They overlap heavily: both carry the naming-prefix table, the `Option Explicit` rule,
the structured-error-handling pattern, the performance wrapper, the late-vs-early
binding guidance, the UDF discipline. That's the same *behavior* authored twice. Two
costs: (1) **drift** — fix the error-handling rule in one and the other now lies; (2)
**waste** — the brief carries behavior that the skill already fires on demand.

The brief *predates* the skill (the context tier was the original whole-stack stance;
the finer skills came later — see `context/README.md`). That's the usual origin story:
a how-to written into a brief before a skill existed, never moved when the skill was
born.

### The fix — split by kind, single-source the rest

The **skill owns the how-to.** The context doc keeps only what's genuinely *reference*
and *not* in the skill, plus a thin pointer. Concretely, for the VBA pair:

| Move to / keep in the **skill** (behavior) | Keep in the **context doc** (reference) |
|---|---|
| "Plan before you code", targeted-edits discipline | A one-paragraph orientation: *what this stack is, who it's for* |
| Naming conventions, error-handling pattern, perf wrapper | A pointer: **"For the how-to, the `vba-development` skill is authoritative."** |
| Late/early binding rules, UDF discipline, anti-patterns | Genuine reference the skill doesn't carry: Office **version-support tables**, trust-centre / Mark-of-the-Web **policy facts**, the `.frx`-is-binary packaging spec, file-format matrix |
| The review checklist (that's applied judgment) | Stable external facts and specs you'd *look up*, not *act on* |

After the split, no sentence of how-to lives in both files. The brief shrinks to
orientation + pointer + the few hard reference facts that aren't behavioral.

## When both legitimately coexist — and staying DRY

A skill and a context doc on the *same topic* are fine when they hold **different
kinds** of content: the skill = behavior, the doc = reference facts the behavior
doesn't encode (version matrices, schemas, policy tables, design rationale). Keep them
DRY:

- **Single-source every claim.** Each fact or rule lives in exactly one of the two. If
  you're tempted to repeat it "for convenience", don't — link instead.
- **The brief points to the skill, never re-teaches it.** One line:
  *"How-to lives in the `<name>` skill; this doc is reference only."*
- **When you edit one, check the other for an echo.** Drift starts as a helpful
  duplicate.
- **A pure-reference topic needs no skill; a pure-behavior topic needs no brief.** Only
  create the second home when it carries a genuinely different kind of content.

## Checklist

- [ ] Placed by **kind**: behavior → skill, reference → context, universal → CLAUDE.md,
  one stable card → reference note.
- [ ] No "how to" prose sitting in a context doc that a skill should own.
- [ ] No facts/specs/tables stuffed into a skill that should be reference.
- [ ] If both exist on one topic, each claim lives in exactly **one** of them.
- [ ] The context brief points to the skill for the how-to instead of repeating it.
- [ ] CLAUDE.md holds only what's true every session — nothing occasional.
- [ ] Sized right: a longer whole-stack stance is a flat `context/<name>.md` brief; a
  single cross-cutting fact is a `context/notes/` card in the INDEX.

## Watch Out

- **"It's helpful to have it in both" is how drift starts.** Duplication is a future
  bug, not a convenience. Single-source and link.
- **A brief that predates a skill is the classic duplication source.** When a skill is
  born for a topic that already has a brief, *move* the how-to out of the brief — don't
  leave a stale copy.
- **Behavior buried in a context doc rarely fires.** A how-to only triggers reliably as
  a skill (by `description:`); leaving it in a passive brief means it loads only if
  someone happens to deep-read that file.
- **Don't bloat CLAUDE.md with reference.** Occasional facts belong in an on-demand note
  or brief, not the always-loaded contract.
- **This is the skill-vs-context seam only.** For the full routing across
  memory/CLAUDE.md/notes/drop, use `knowledge-router`; for writing the `SKILL.md`
  itself, use `skill-authoring`. Don't re-derive either here.
