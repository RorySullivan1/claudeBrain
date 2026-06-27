# claudeBrain

A **factory for Claude Code tooling.** This repo is where reusable `.claude/`
assets — skills, context briefs, hooks, commands, agents, workflows — are
*designed*, then handed off to downstream projects that actually run them. It is
**not an application** and has no `src/`. It has two halves with two distinct jobs:

```
.claude/            ← the FACTORY's design environment (how we author assets)
example-project/    ← a MOCK consumer project (what a produced .claude/ looks like)
```

## The two halves

### `.claude/` — the design environment

The factory's own `.claude/` is tooling for *building* assets, not the assets
themselves. It mirrors the standard layer taxonomy (`skills/`, `context/`,
`hooks/`, `commands/`, `agents/`, `workflows/`), but each layer here is scoped to
**authoring** the matching downstream asset type — e.g. `skills/` will hold
meta-skills that guide how to write a good `SKILL.md`, `context/` will hold the
authoring standards and conventions. Today these layers are **stubs** (a README
per layer describing what it will become); no meta-tooling is fabricated until a
concrete need appears. See `.claude/README.md`.

### `example-project/` — the produced layout

A mock downstream repo that shows what the factory ships — the canonical **worked
examples** for every element type below. It's laid out exactly like a real project
a developer would copy:

```
example-project/
├── CLAUDE.md            ← the project's session contract
├── CLAUDE.local.md      ← sample personal notes (gitignored in a real repo)
└── .claude/
    ├── skills/          ← domain skill bundles (worked examples)
    ├── context/         ← stack-brief docs + manifest
    ├── memory/          ← session-memory: auto-loaded INDEX.md + sessions/ logs
    ├── hooks/ commands/ agents/ workflows/   ← scaffolds, ready to fill
    ├── settings.json · README.md
```

When you need to see a *finished* asset of any type, read its example here. See
`example-project/.claude/README.md` for what each layer means in a consumer.

## The asset taxonomy — pick the layer first

Before building anything, choose the right kind of asset. The layers compose:

```
hooks      ← enforcement floor, run by the harness (the model cannot skip them)
─────────────────────────────────────────────────────────────────────────
workflows  ▸  commands  ▸  agents  ▸  skills
(orchestrate)  (one-shot)  (isolated)  (expertise)
```

- **skill** — reach for it to teach Claude *how to think and behave* for a recurring
  task type (a domain or an authoring discipline). Loaded by trigger, in-session.
- **agent** — an isolated subagent with clean context that does focused work and
  returns only a summary. Use it for noisy or narrowly-scoped jobs.
- **command** — a saved single-shot prompt you'd otherwise retype, invoked `/<name>`.
- **workflow** — a multi-step orchestration that loops, branches, and spawns agents.
- **hook** — a deterministic script the harness runs on a lifecycle event; the
  enforcement layer *underneath* the prompt stack. Use it for what must *always* run.
- **context** — reference docs Claude deep-reads on demand (briefs, schemas, notes);
  `CLAUDE.md` points here so sessions stay lean. The `knowledge-router` skill curates a
  `context/notes/` reference-notes tier (an always-loaded `INDEX.md` catalog + on-demand
  notes, via `context.py`) on top of the flat briefs.

## Building an asset — the core brain

Every element follows a fixed where/named/formatted shape. Author the *meta-tooling*
under this repo's `.claude/<layer>/`; the matching path in a downstream project is
the same minus the meta- scoping.

| Element | Lives in | File / naming | Format shape | Author with |
|---|---|---|---|---|
| Skill | `.claude/skills/<name>/` | `SKILL.md`; folder == `name:` | YAML frontmatter (`name`, `description`) + markdown body | `skill-authoring` skill |
| Agent | `.claude/agents/` | `<name>.md` | YAML frontmatter (`name`, `description`, opt. `tools`, `model`) + system-prompt body | `agent-authoring` skill |
| Command | `.claude/commands/` | `<name>.md` (filename == command) | Prose prompt body; `$ARGUMENTS` / `$1…` params | `commands/README.md` |
| Workflow | `.claude/workflows/` | `<name>.md` | Prose: ordered steps, agents/commands invoked, inputs/outputs, stop conditions | `workflow-authoring` skill |
| Hook | `.claude/hooks/` | one script per event | Executable script; wired in `settings.json` by event | `hooks/README.md` |
| Context | `.claude/context/` | kebab-case `<name>.md` | Plain markdown, no frontmatter; listed in the `context/` manifest | `context/README.md` |

For the full format rules, open the matching `.claude/<layer>/README.md`; for skills,
agents, and workflows the meta-skills teach the how-to in depth (`agent-authoring`,
`skill-authoring`, `workflow-authoring`, and the `context-vs-skill` placement skill are
all built). For a finished example of any element, read its counterpart in
`example-project/.claude/`.

## Conventions

- **Skill folder = `name:` frontmatter.** Renaming a skill means renaming both.
- **Context docs are kebab-case** (`c-csharp-project-instructions.md`).
- **Contents are authoritative as-is.** When updating a skill, edit its `SKILL.md`
  in place; don't fork copies.
- **Factory vs. product.** Author the *how-to* (meta-tooling) under `.claude/`;
  the produced assets and their showcase live under `example-project/`.
- **Operational assets are single-sourced.** The assets the factory itself *runs*
  while dogfooding — the `session-memory` and `agent-finder` skills, `build-hooks.py`,
  and the shared hook fragments — are produced assets, so their canonical copy lives in
  `example-project/.claude/` and the factory's `.claude/` holds **symlinks** into it.
  Edit them in `example-project/`; never replace a symlink with a copy. (Role-divergent
  files — `settings.json`, the per-layer `README.md`s — stay independent per tree.)
- **Version labeling.** A project's current unit of work is named in a root `.meta/version`
  file (semver label + goals/objectives); the `ship-version` workflow (`/version-set` +
  `/version-ship`) names and ships the PR from those goals. `.meta/version` is per-project
  runtime state (like `.claude/memory/`), created on demand — not a shipped asset.

## Using an asset elsewhere

- **A skill:** copy `example-project/.claude/skills/<name>/` into the target
  project's `.claude/skills/`.
- **A context doc:** copy the file into the target's `.claude/context/`, or paste
  its body into that project's `CLAUDE.md`.
- **The whole pattern:** copy `example-project/` as a starting point — its
  `CLAUDE.md`, `CLAUDE.local.md`, and `.claude/` scaffold are a ready-to-fill repo
  skeleton. See `example-project/.claude/README.md` for what each layer is for.
