# MEMORY INDEX  ·  keep ≤ ~80 lines

## State            (rewrite in place — current truth only, ≤ ~10 lines)
- claudeBrain is a **factory** for Claude Code assets: `.claude/` authors meta-tooling; `example-project/` showcases a produced `.claude/`.
- Meta-skills built: `agent-authoring` + the three specialized siblings `developer-`, `product-manager-`, `knowledge-agent-authoring`.
- Operational skills built: `session-memory` and `agent-finder` (subagent selection/delegation, engine `scripts/agents.py`).
- Authoring commands built: the `add-*` family (`add-skill/agent/command/hook/workflow`).
- **Memory:** `session-memory` skill + `.claude/memory/` now replace the old `DECISIONS.md` workflow; four lifecycle hooks (SessionStart/PreCompact/Stop/UserPromptSubmit).
- **Hooks** are authored as per-hook `*.json` fragments in `.claude/hooks/` and compiled into `settings.json` by `build-hooks.py`; self-maintaining via a PostToolUse auto-rebuild + a SessionStart staleness warning.

## Decisions        (append-only; supersede, never delete)
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
- Planned meta-skills not yet written: `skill-authoring`, `context-vs-skill`.
- Planned commands: `/validate-asset`, `/add-context`.
- Possible future agent siblings: a line-level code-reviewer; an orchestrator/coordinator.
- `/add-skill` references `skill-authoring` (planned); it falls back to README + `agent-authoring` until that lands.

## Log              (append-only pointers)
- 2026-06-17 | Add agent-finder skill + grant Bash permission | sessions/2026-06-17-agent-finder.md
- 2026-06-17 | Hook drift guard + coding-standards → Python/C# | sessions/2026-06-17-hook-guard-and-csharp.md
- 2026-06-17 | Hooks as fragments + build-hooks.py generator | sessions/2026-06-17-hook-fragments.md
- 2026-06-17 | Adopt session-memory; migrate DECISIONS.md | sessions/2026-06-17-adopt-session-memory.md
- (pre-2026-06-17) | Full prior decision history (8 entries) | sessions/2026-archive-decisions.md
