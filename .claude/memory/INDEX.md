# MEMORY INDEX  ·  keep ≤ ~80 lines

## State            (rewrite in place — current truth only, ≤ ~10 lines)
- claudeBrain is a **factory** for Claude Code assets: `.claude/` authors meta-tooling; `example-project/` showcases a produced `.claude/`.
- **example-project** now carries its first real agent (`finance-quantitative-developer`, Python quant) + a Quant skill set (`quantitative-finance`, `financial-timeseries-analysis`, `backtesting-validation`, `quant-code-review`) — `agents/` is no longer an empty scaffold.
- Meta-skills built: `agent-authoring` (the single source of truth for layer-choice + the authoring checklist) + three specialized siblings `developer-`/`product-manager-`/`knowledge-agent-authoring`, now trimmed to a clean **delta** that points back to the base instead of restating it.
- Operational skills built: `session-memory`, `agent-finder`, `knowledge-router` (reference-notes tier via `scripts/context.py`), and `token-optimizer` (work-placement judgment; engine `scripts/tokens.py`). Operational **agent**: `token-manager` (verbose work → capped summary). Context-economy **guard hooks**: `post_bash_filter.py` (PostToolUse·Bash) + `pre_read_guard.py` (PreToolUse·Read). **Single-sourced:** canonical copies in `example-project/.claude/`; the factory `.claude/` holds symlinks (skills, the agent, hook scripts + fragments, `build-hooks.py`) — edit in `example-project/`, never copy.
- Authoring commands built: the `add-*` family (`add-skill/agent/command/hook/workflow`).
- **Memory:** `session-memory` skill + `.claude/memory/` now replace the old `DECISIONS.md` workflow; four lifecycle hooks (SessionStart/PreCompact/Stop/UserPromptSubmit).
- **Hooks** are authored as per-hook `*.json` fragments in `.claude/hooks/` and compiled into `settings.json` by `build-hooks.py`; self-maintaining via a PostToolUse auto-rebuild + a SessionStart staleness warning.
- **Factory efficiency:** Stop hook nudges at most once per session (per-`session_id` temp marker); `author-asset` workflow + `add-*` guardrails forbid re-deriving formats via Explore agents.

## Decisions        (append-only; supersede, never delete)
- [2026-06-18] Added token/context-economy tooling (from uploads): `token-optimizer` skill (+`tokens.py`), `token-manager` agent (first operational agent), and two fail-safe guard hooks — `post_bash_filter.py` (elide long Bash output) + `pre_read_guard.py` (cap huge unpaged reads, first PreToolUse hook). Single-sourced via symlink; both settings.json rebuilt (9 fragments). Bundle was internally consistent → no taxonomy rewrites (only `python3`→`python` in SKILL examples) — sessions/2026-06-18-2239-token-economy-tooling.md
- [2026-06-18] Added `knowledge-router` operational skill + `.claude/context/` reference-notes tier (model contextualization, from user uploads): `context.py` manages `INDEX.md` + `notes/`; SessionStart surfaces the index via exec-form hook + new `context.py index` (mirrors memory.py). Single-sourced via symlink per PR #9. Adapted the SKILL's references (`skill-distiller`→`author-asset`/`add-skill`; `.claude/rules/`→`CLAUDE.md`/context note) to claudeBrain's real taxonomy — sessions/2026-06-18-2227-knowledge-router-context-tier.md
- [2026-06-18] Single-sourced the operational assets: canonical copies in `example-project/.claude/`, factory holds 9 relative symlinks (`skills/session-memory`, `skills/agent-finder`, `hooks/build-hooks.py` + 6 shared fragments). Kills factory↔consumer drift (caught `example-project` `memory.py` stale — missing the PR #7 Stop-hook dedupe). Liftability preserved (example-project files are real; `cp -rL` works). **Supersedes** the [2026-06-18] "left example-project script dup as intentional" stance for these specific assets. `settings.json` + per-layer READMEs stay independent — sessions/2026-06-18-2200-single-source-operational-assets.md
- [2026-06-18] Second efficiency pass: de-duped the agent-authoring family to base+delta (siblings now point to the base's *Is an agent the right tool?* + checklist instead of restating; "Start with agent-authoring" intro compressed) and trimmed all 4 eager descriptions (kept every trigger list). Deliberately left example-project script dup (intentional showcase), hook micro-perf, and command placement boilerplate alone. −37 lines, settings.json unchanged — sessions/2026-06-18-2140-optimize-agent-authoring-family.md
- [2026-06-18] Factory-efficiency pass: Stop hook deduped to once/session (temp marker keyed by session_id, supersedes block-every-Stop); new `author-asset` workflow + `add-agent`/`add-skill` guardrails ban re-deriving formats via Explore agents — sessions/2026-06-18-2059-optimize-factory-model.md
- [2026-06-17] First consumer agent + quant skill layer: `finance-quantitative-developer` (Python/numpy/scipy/pandas, verification-gated) + 4 skills in example-project; stack=Python (not C#/VSTO), built on `developer-agent-authoring` — sessions/2026-06-17-1753-finance-quant-dev-agent.md
- [2026-06-17] Permissions: `defaultMode: acceptEdits` (no edit prompts) + leading-slash `Edit(/.claude/**)`; Bash **scoped** to session-used families (supersedes the broad-Bash grant) — sessions/2026-06-17-permission-tuning.md
- [2026-06-17] Added `agent-finder` operational skill (subagent selection) + `agents.py`; granted broad `Bash` permission in committed settings.json per user request — sessions/2026-06-17-agent-finder.md
- [2026-06-17] Hook drift guard — PostToolUse auto-rebuilds settings.json on fragment edit + SessionStart warns if stale; `is_fragment` uses `os.path.samefile` for path-format robustness — sessions/2026-06-17-hook-guard-and-csharp.md
- [2026-06-17] example-project `coding-standards` skill uses Python + C# (its real VSTO/.NET stack); dropped TypeScript — sessions/2026-06-17-hook-guard-and-csharp.md
- [2026-06-17] Hooks stored as per-hook `*.json` fragments compiled into settings.json by `build-hooks.py` — Claude Code has no native external-hook loading; plugins (the only alternative) add install friction — sessions/2026-06-17-hook-fragments.md
- [2026-06-17] Adopt `session-memory`, retire `DECISIONS.md` — bounded decay + append-only logs beat a rewrite-in-place log — sessions/2026-06-17-adopt-session-memory.md
- [2026-06-17] Factory authoring commands: the `add-*` family — one-shot scaffolders per layer, delegate depth to meta-skills/READMEs — sessions/2026-archive-decisions.md
- [2026-06-17] Fourth meta-skill `knowledge-agent-authoring` — curator/retriever agents; spans read-only + curation modes — sessions/2026-archive-decisions.md
- [2026-06-16] Third meta-skill `product-manager-agent-authoring` — read-only project-altitude assessor sibling — sessions/2026-archive-decisions.md
- [2026-06-16] Second meta-skill `developer-agent-authoring` — language/stack code-writer with verification gate — sessions/2026-archive-decisions.md
- [2026-06-12] First meta-skill `agent-authoring` — grounded in durable agent fields, defers volatile long tail to docs — sessions/2026-archive-decisions.md
- [2026-06-11] Split into factory (`.claude/`) + mock consumer (`example-project/`) — design env vs. its output — sessions/2026-archive-decisions.md
- [2026-06-11] Adopt the typed `.claude/` layout; empty layers scaffolded, not fabricated — sessions/2026-archive-decisions.md

## Threads          (open items; remove when closed)
- PR #7 (first factory-efficiency pass) merged. `claude/optimize-factory-model` re-cut from main for the second efficiency pass (agent-authoring dedup); pushed, no new PR opened yet — open one if wanted.
- Planned meta-skills not yet written: `skill-authoring`, `context-vs-skill`.
- Planned commands: `/validate-asset`, `/add-context`.
- Possible future agent siblings: a line-level code-reviewer; an orchestrator/coordinator.
- `/add-skill` references `skill-authoring` (planned); it falls back to README + `agent-authoring` until that lands.

## Log              (append-only pointers)
- 2026-06-18 | token-economy tooling: token-optimizer skill + token-manager agent + guard hooks | sessions/2026-06-18-2239-token-economy-tooling.md
- 2026-06-18 | knowledge-router skill + .claude/context/ reference-notes tier | sessions/2026-06-18-2227-knowledge-router-context-tier.md
- 2026-06-18 | Single-source operational assets via symlink (kill factory↔consumer drift) | sessions/2026-06-18-2200-single-source-operational-assets.md
- 2026-06-18 | Dedupe agent-authoring family to base+delta + trim eager descriptions | sessions/2026-06-18-2140-optimize-agent-authoring-family.md
- 2026-06-18 | Factory efficiency: Stop-hook dedupe + author-asset workflow | sessions/2026-06-18-2059-optimize-factory-model.md
- 2026-06-17 | finance-quantitative-developer agent + 4 quant skills (consumer) | sessions/2026-06-17-1753-finance-quant-dev-agent.md
- 2026-06-17 | Permission tuning: acceptEdits + scoped Bash | sessions/2026-06-17-permission-tuning.md
- 2026-06-17 | Add agent-finder skill + grant Bash permission | sessions/2026-06-17-agent-finder.md
- 2026-06-17 | Hook drift guard + coding-standards → Python/C# | sessions/2026-06-17-hook-guard-and-csharp.md
- 2026-06-17 | Hooks as fragments + build-hooks.py generator | sessions/2026-06-17-hook-fragments.md
- 2026-06-17 | Adopt session-memory; migrate DECISIONS.md | sessions/2026-06-17-adopt-session-memory.md
- (pre-2026-06-17) | Full prior decision history (8 entries) | sessions/2026-archive-decisions.md
