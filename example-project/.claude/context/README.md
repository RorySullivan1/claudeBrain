# context/

Reference docs Claude can deep-read when a task needs them. `CLAUDE.md` points
here so the main session stays lean — Claude only opens what's relevant.

This layer has **two tiers**:

1. **Project-instruction briefs** (flat `*.md` below) — longer-form, CLAUDE.md-style
   system prompts, one per language/stack. Each is a complete operating brief — drop one
   into a target project's `CLAUDE.md` (or its own `.claude/context/`) to give Claude a
   full stance for that stack. They predate the finer-grained skills in `../skills/` and
   overlap with them by design: the skills are task-scoped; these are whole-stack. Listed
   in the manual **Manifest** below — and see *When a skill and a brief cover the same
   ground* for how that overlap is resolved.
2. **Reference notes** (`notes/*.md` + auto-generated `INDEX.md`) — small, declarative,
   read-on-demand reference cards (a concept, an external-system fact, a schema, a system
   map). `INDEX.md` is the always-loaded catalog (surfaced at SessionStart); each note is
   read only when its topic is relevant. The `knowledge-router` skill decides what earns a
   note, and its `context.py` engine creates notes and regenerates the catalog so it can't
   drift. Run `python ../skills/knowledge-router/scripts/context.py list` to see them.

## When a skill and a brief cover the same ground, the skill wins

The two tiers overlap by design, but that does not license the same guidance in both
places — and left unstated it produces exactly that. Two rules settle it:

- **A skill is loaded by its own description when the task matches; a brief is loaded
  only if something points at it.** Reachability, not scope, is what makes a home
  canonical. Where both cover a topic, **the skill is canonical** and the brief must not
  restate it.
- **A brief earns its place only by what no skill carries** — a whole-stack stance a
  task-scoped skill cannot express — and it must be reachable: referenced from the
  installing project's `CLAUDE.md`, or it is dead weight. A brief nothing points at is
  not a fallback; it is a second copy that cannot be corrected because nobody reads it.

Measured downstream, in pyHermes: 71% of `python-project-instructions.md`'s substantive
lines echoed `python-development`, `python-review`, `python-deployment` or
`coding-standards` outright, every remaining line was carried by one of them, and nothing
referenced the file — that project's own copy of this README claimed `CLAUDE.md` pointed
there and it did not. Its Testing section was a strict *subset* of the skill's, which is
the shape to expect: **the unreachable copy is also the stale one.** pyHermes removed its
copy; whether the factory should keep shipping a brief per stack is a separate call, and
this rule is what makes it decidable rather than a matter of taste.

## Manifest (project-instruction briefs)

| File | What it's for |
|---|---|
| `vsto-project-instructions.md` | Full VSTO specialist brief — dev, teaching, management, distribution across the Office add-in lifecycle. |
| `c-csharp-project-instructions.md` | C and C# coding-assistant brief — teaching, debugging, and producing idiomatic code. |
| `cpp-bot-instructions.md` | "Cero" C++ assistant brief — modern C++ (C++98→C++23) teaching, debugging, generation. |
| `python-project-instructions.md` | Python full-lifecycle brief — development, review, debugging, deployment standards. |
| `vba-development.md` | VBA engineering brief — production-grade VBA across Excel/Outlook/PowerPoint/Word. |
| `air-gap.md` | The one-way clipboard air-gap model — repo as golden source, hand-pasted into Power Apps Studio, and the drift it implies. |
| `powerapps-docs-source.md` | The MicrosoftDocs/powerapps-docs repo as the grounding source for canvas-app control/layout SEMANTICS — paths, fetch methods, and the hard limit (it never gives pa-yaml tokens; omissions mean unconfirmed, not unsupported). |

Reference notes are catalogued automatically in `INDEX.md` — not listed here.
