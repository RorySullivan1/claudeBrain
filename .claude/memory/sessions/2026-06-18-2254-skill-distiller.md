# 2026-06-18 22:54 · skill-distiller

**Goal:** Add skill-distiller skill (when to create/extend a skill) + plan-nudge hook; close knowledge-router loop

## What happened
- Incorporated the skill-distiller bundle (4 uploads) as an operational skill, single-sourced
  via symlink (canonical in example-project, factory symlink):
  - `SKILL.md` — the "should this become a skill?" decision: significance gate + redundancy
    check + candidate queue; prefers extending over creating.
  - `scripts/skills.py` — inventory / `similar` dedupe / candidate queue engine.
  - `scripts/plan_nudge.py` — PostToolUse·ExitPlanMode nudge (additionalContext).
  - `post-tool-use-plan-nudge.json` — exec-form fragment (not the uploaded shell-form hooks.json).
- Rebuilt both settings.json (10 fragments; new ExitPlanMode entry).
- **Closed the loop:** repointed knowledge-router's "procedure that will recur" bullet from
  `/add-skill`/`author-asset` back to **skill-distiller** (PR #10 had pointed it away because
  skill-distiller didn't exist yet). skill-distiller runs the gate, then authors via /add-skill.
- Docs: factory skills/README + hooks/README, example CLAUDE.md.

## Gotchas & dead ends
- Taxonomy adaptation (same pattern as before): SKILL hands authoring to a `skill-creator`
  skill that doesn't exist here → remapped to `/add-skill` + `author-asset` (+ planned
  `skill-authoring`). Also fixed the `skill-creator` string baked into skills.py's
  CANDIDATES.md header. Verified zero `skill-creator` refs remain.
- **Real bug found + fixed:** `Path.rglob` does NOT descend symlinked dirs, so from the
  factory root skills.py saw only the 5 real meta-skills and missed the 5 symlinked
  operational skills — a half-blind dedupe tool would emit false "net-new" verdicts (the
  exact proliferation failure it guards against). Switched discovery to
  `os.walk(followlinks=True)`; factory now inventories all 10. Consumer (real dirs) unaffected.
- Candidate queue (`.claude/skills/_candidates/CANDIDATES.md`) is per-project STATE (written
  at git-repo root), untracked like memory/ — tested round-trip then removed the test stub.
- Hook is exec-form per the standing convention; the uploaded shell-form hooks.json (python3
  "$VAR") not added verbatim (Windows-fragile + would break build-hooks).

## State at end
- Branch `claude/skill-distiller` off merged main (#8–#11 in). Committed + pushed; PR opened.
- Authoring stack now: skill-distiller (decide) → /add-skill (scaffold) → skill-authoring (planned depth).

## Open threads
- Planned meta-skills still unwritten: `skill-authoring`, `context-vs-skill`.
- skill-distiller references `/add-skill` (exists) + planned `skill-authoring`; fine until it lands.
