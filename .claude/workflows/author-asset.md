# author-asset

Produce one or more `.claude/` assets (skill, agent, command, hook, context,
workflow) end to end — efficiently, without re-deriving formats. This is the
default path for any "build me a skill / agent / a set of assets" request.

**Inputs:** the asset type(s) wanted, a name/purpose for each, and the target
`.claude/` (this factory, or a consumer like `example-project/`).
**Output:** the finished asset file(s), wired into the consumer's catalog, passing
the structural check.

## Steps

1. **Scope the build.** List every asset the request implies and its layer
   (skill / agent / command / hook / context / workflow), and confirm placement:
   factory (`./.claude/`) vs. a consumer (`example-project/.claude/` or another
   project). Settle this once, up front, for all assets.

2. **Load conventions once — do not re-explore.** Read the matching meta-skill or
   layer README a single time:
   - skill → `skill-authoring` if present, else `.claude/skills/README.md` + a
     built skill as a model.
   - agent → `agent-authoring` (+ `developer-`/`product-manager-`/
     `knowledge-agent-authoring` for that flavor).
   - command / hook / context / workflow → the layer's `README.md`.

   **Guardrail (the whole point of this workflow):** the meta-skill and the named
   built reference assets ARE the format spec. **Do not spawn Explore/research
   agents to re-derive conventions or re-read example bundles** — that is the
   redundant work this workflow exists to eliminate. Read the one authoritative
   source and proceed.

3. **Scaffold + fill, per asset.** Follow the matching `/add-*` command
   (`/add-skill`, `/add-agent`, `/add-command`, `/add-hook`, `/add-workflow`) to
   create each file with correct frontmatter and a complete body. Reuse the
   conventions loaded in step 2; don't reload them per asset.

4. **Batch the wiring (multi-asset runs).** When building several assets, decide
   them all first, scaffold in one pass, then do the shared wiring **once** — set
   cross-references between the new assets, and update the consumer's `CLAUDE.md`
   catalog (and any layer `README.md` status) in a single edit, not per asset.

5. **Verify structurally.** Confirm each skill folder name equals its `name:`
   frontmatter and each agent `name:` equals its filename; frontmatter parses;
   cross-references resolve; descriptions name real triggers. Markdown assets need
   no code execution. If a hook *fragment* changed, run
   `python .claude/hooks/build-hooks.py` and confirm `--check` is green.

## Stop conditions

- All requested assets exist, are wired into the catalog, and pass the structural
  check → done; report the paths and how to invoke each.
- A genuine design choice is the caller's (stack, scope, which assets) → ask via
  the decision tools, then resume. Do **not** open-endedly explore.

## Invokes
- Commands: the `add-*` family (`../commands/add-*.md`).
- Skills: the `*-agent-authoring` meta-skills; `skill-authoring` when it lands.
