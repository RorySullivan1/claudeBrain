# claude-skills-library

A library of reusable Claude Code assets — skills, reference context, and the
templates needed to bootstrap the same infrastructure pattern in other projects.
This repo is **not an application**; it has no `src/`. Its job is to hold
well-factored, copy-pasteable building blocks.

## What's here

```
.claude/
├── skills/      ← 10 skill bundles (the core deliverable)
├── context/     ← 5 CLAUDE.md-style project-instruction docs (per language/stack)
├── hooks/       ← scaffold (empty — lifecycle enforcement scripts go here)
├── commands/    ← scaffold (empty — single-shot prompt templates)
├── agents/      ← scaffold (empty — isolated subagent definitions)
├── workflows/   ← scaffold (empty — multi-step orchestrations)
├── settings.json
├── README.md    ← the .claude taxonomy + composability stack, explained
└── DECISIONS.md ← log of structural decisions
templates/
├── CLAUDE.md.template        ← starter that teaches the infrastructure pattern
└── CLAUDE.local.md.template  ← starter for personal, gitignored notes
```

## The skills

Each skill is a self-contained bundle at `.claude/skills/<name>/SKILL.md`. The
folder name always equals the skill's `name:` frontmatter value.

| Skill | Purpose |
|---|---|
| `VSTO-development` | Write/architect/debug VSTO Office add-ins (C#/VB.NET) |
| `VSTO-distribution` | Package & deploy VSTO add-ins (ClickOnce, MSI/WiX, GPO) |
| `VSTO-maintenance` | Troubleshoot & maintain deployed VSTO add-ins |
| `VSTO-review` | Review VSTO code (COM lifecycle, event hygiene, threading) |
| `python-development` | Write new Python code |
| `python-review` | Review Python code for bugs/security/design |
| `python-maintenance` | Debug, refactor, modernize existing Python |
| `python-deployment` | Package, containerize, ship Python to production |
| `technical-documentation-drafter` | Developer-facing docs (`docs/` folder) |
| `user-guide-drafter` | End-user, non-technical documentation |

## The context docs

`.claude/context/` holds five longer-form, CLAUDE.md-style system prompts — one
per language/stack — that predate the skill split. They are reference material:
drop one into a project's `CLAUDE.md` (or `.claude/context/`) to give Claude a
full operating brief for that stack. See `.claude/context/README.md`.

## Conventions

- **Skill folder = `name:` frontmatter.** Renaming a skill means renaming both.
- **Context docs are kebab-case** (`c-csharp-project-instructions.md`).
- **Contents are authoritative as-is.** When updating a skill, edit its `SKILL.md`
  in place; don't fork copies at the root.

## Using an asset elsewhere

- **A skill:** copy the whole `.claude/skills/<name>/` folder into the target
  project's `.claude/skills/`.
- **A context doc:** copy the file into the target's `.claude/context/`, or paste
  its body into that project's `CLAUDE.md`.
- **The whole pattern:** start from `templates/CLAUDE.md.template` and the scaffold
  READMEs under `.claude/` — see `.claude/README.md` for what each layer is for.
