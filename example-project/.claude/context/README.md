# context/

Reference docs Claude can deep-read when a task needs them. `CLAUDE.md` points
here so the main session stays lean — Claude only opens what's relevant.

This layer has **two tiers**:

1. **Project-instruction briefs** (flat `*.md` below) — longer-form, CLAUDE.md-style
   system prompts, one per language/stack. Each is a complete operating brief — drop one
   into a target project's `CLAUDE.md` (or its own `.claude/context/`) to give Claude a
   full stance for that stack. They predate the finer-grained skills in `../skills/` and
   overlap with them by design: the skills are task-scoped; these are whole-stack. Listed
   in the manual **Manifest** below.
2. **Reference notes** (`notes/*.md` + auto-generated `INDEX.md`) — small, declarative,
   read-on-demand reference cards (a concept, an external-system fact, a schema, a system
   map). `INDEX.md` is the always-loaded catalog (surfaced at SessionStart); each note is
   read only when its topic is relevant. The `knowledge-router` skill decides what earns a
   note, and its `context.py` engine creates notes and regenerates the catalog so it can't
   drift. Run `python ../skills/knowledge-router/scripts/context.py list` to see them.

## Manifest (project-instruction briefs)

| File | What it's for |
|---|---|
| `vsto-project-instructions.md` | Full VSTO specialist brief — dev, teaching, management, distribution across the Office add-in lifecycle. |
| `c-csharp-project-instructions.md` | C and C# coding-assistant brief — teaching, debugging, and producing idiomatic code. |
| `cpp-bot-instructions.md` | "Cero" C++ assistant brief — modern C++ (C++98→C++23) teaching, debugging, generation. |
| `python-project-instructions.md` | Python full-lifecycle brief — development, review, debugging, deployment standards. |
| `vba-development.md` | VBA engineering brief — production-grade VBA across Excel/Outlook/PowerPoint/Word. |

Reference notes are catalogued automatically in `INDEX.md` — not listed here.
