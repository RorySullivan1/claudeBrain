<!-- guide: TITLE is the symptom, specific and searchable ("Upload retries forever on 503"), never the area ("bug in uploader"). One bug per issue. -->
Part of #{{parent}}

<!-- guide: Delete the "Part of" line unless this bug belongs to an epic. -->

## What happened

{{what_happened}}

## Steps to reproduce

{{steps}}

<!-- guide: A numbered list that ends with "Observe: <the symptom>". If you can't reproduce it, say so and give the conditions under which it was seen. Don't invent steps. -->

## Expected

{{expected}}

## Environment

{{environment}}

<!-- guide: Version, commit or tag, runtime, and OS: whatever the bug could depend on. -->

## Evidence

{{evidence}}

<!-- guide: A log excerpt, stack trace, or failing test, in a fenced block. Trim it to the lines that matter. -->

## Acceptance

{{acceptance}}

<!-- guide: `- [ ]` lines. Include a regression test (or a named manual check) that fails before the fix and passes after it. -->

## Done when

A PR into the default branch merges with this line in its description:

```
Fixes #{{self}}
```

<sub>GitHub closing keywords work only from a PR description or a commit message, and only when the PR targets the default branch.</sub>
