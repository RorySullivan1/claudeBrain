# Decisions

A running log of structural decisions for this repo. Newest first.

## 2026-06-11 — Adopt the `.claude/` infrastructure layout

**Context.** The repo was a flat collection of 15 markdown files at the root — 10
skills (with `name:`/`description:` frontmatter) and 5 CLAUDE.md-style
project-instruction docs — with no organizing structure, no `CLAUDE.md`, and no
`.gitignore`. We adopted the typed `.claude/` project-infrastructure pattern
(`context/`, `hooks/`, `skills/`, `commands/`, `agents/`, `workflows/`).

**Decisions.**

1. **Empty layers are scaffolded, not fabricated.** `hooks/`, `commands/`,
   `agents/`, and `workflows/` each get a README explaining the layer's purpose.
   No example content is invented — they stay empty until a real need appears.
2. **Project-instruction docs live in `.claude/context/`.** The 5 frontmatter-less
   CLAUDE.md-style stack briefs (VSTO, C/C#, C++, Python, VBA) are reference
   context, not skills, so they belong under `context/`.
3. **`CLAUDE.md` is a library guide; the reusable pattern lives in `templates/`.**
   This repo is a library, so its `CLAUDE.md` documents the library itself.
   `templates/CLAUDE.md.template` is the portable starter that teaches the
   infrastructure pattern for use in other projects.

**Mechanics.** Files were relocated with `git mv` to preserve history; their bodies
were left byte-for-byte unchanged. Skill folders are named after each skill's
`name:` frontmatter value. No `src/` directory — this is a pure asset library.
