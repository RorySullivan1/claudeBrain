<!-- guide: TITLE is an imperative, specific unit of work ("Add the verification-surface context doc"), never a topic ("Verification"). This template is the default for a sub-issue of an epic. -->
Part of #{{parent}}

<!-- guide: Delete the "Part of" line for a standalone task. -->

## Goal

{{goal}}

<!-- guide: One or two sentences: what this issue delivers, and why it matters to the parent's outcome. -->

## Context

{{context}}

<!-- guide: What someone picking this up cold needs: the relevant files or docs, the current behaviour, and what has already been decided. Link rather than paste. -->

## Scope

{{scope}}

<!-- guide: Two short lists, "In:" and "Out:". "Out" is what stops a sub-issue from quietly absorbing its siblings' work. -->

## Acceptance

{{acceptance}}

<!-- guide: Checkable `- [ ]` lines. Each one names a test to run, a file or behaviour to inspect, or a decision recorded in a named place. "Works well" is not checkable. -->

## Depends on

{{depends_on}}

<!-- guide: `#N` references to issues that must land first, or "None". Epic children are filed in dependency order, so every number here already exists. -->

## Done when

A PR into the default branch merges with this line in its description:

```
Closes #{{self}}
```

<sub>GitHub closing keywords work only from a PR description or a commit message, and only when the PR targets the default branch. One keyword per issue: `Closes #1, closes #2`.</sub>
