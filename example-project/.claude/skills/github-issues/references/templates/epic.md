<!-- guide: TITLE is "Epic: <the outcome, in plain words>". Name the result, not the activity ("Epic: close the gaps between doctrine and enforcement", not "Epic: doctrine work"). -->
## Problem

{{problem}}

<!-- guide: Who is affected, what is broken or missing, and the evidence. Every factual claim is checked against the tree or the docs BEFORE filing, and the body says so. Numbered gaps are fine; each one should map to at least one sub-issue. -->

## Outcome

{{outcome}}

<!-- guide: One or two sentences on what is true once this epic is done. This is the sentence a reviewer checks the finished work against. -->

## Sub-issues (in dependency order)

{{breakdown}}

<!-- guide: One numbered line per child: `1. #N — <title>` plus `(depends on #M)` where it applies. Before the children exist, write titles only. /epic rewrites this list with the real numbers once they are filed. GitHub's sub-issue panel tracks progress. This list records ORDER and DEPENDENCIES, which the panel does not. -->

## Acceptance

{{acceptance}}

<!-- guide: Checkable, EPIC-level criteria as `- [ ]` lines: what must hold across the children together. Don't restate each child's own acceptance. -->

## Non-goals

{{non_goals}}

<!-- guide: What this epic deliberately does not do, and where that work belongs if it matters. A follow-up that is worth doing but not now goes here with "file it then, not now". -->

## Risks and open questions

{{risks}}

<!-- guide: OPTIONAL. Delete the whole section, heading included, if there are none. Never leave it empty. -->

## Closing

This epic closes when its last sub-issue closes. The `epic-autoclose` workflow does this if the repo has it installed. Otherwise close it by hand with a pointer to the last PR. Sub-issue PRs close their own issue only. None of them should carry a closing keyword for this epic.

---
<sub>Filed with `/epic` — planning only, no code. Dedupe: {{dedupe}}</sub>
