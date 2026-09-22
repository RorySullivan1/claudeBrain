---
name: github-issues
description: >
  Expert at handling GitHub issues — writing, triaging, organizing, and closing them
  well. Use this skill whenever the user wants to create, file, triage, label, assign,
  link, break down, or close issues: writing a clear bug report or feature request,
  applying labels/types/milestones, planning an epic and splitting it into sub-issues,
  linking issues to PRs so merges auto-close them, searching/deduplicating existing
  issues, or curating a backlog. Ships fill-in templates (epic, task, bug, feature), a
  render/check script, and an epic auto-close GitHub Actions workflow; the `/epic` and
  `/issue` commands drive it. Trigger on "open an issue", "file a bug", "write a feature
  request", "plan this as an epic", "triage these issues", "label this", "break this
  into sub-issues", "is there a duplicate", "close issue #N", "link this issue to the
  PR". Prefers the GitHub MCP tools (`issue_write`,
  `issue_read`, `list_issues`, `search_issues`, `sub_issue_write`) where present, else
  the `gh` CLI. Pairs with github-pull-requests (the PR that closes the issue) and
  github-comments (discussion on the issue). Be frugal — don't file noise.
---

# GitHub Issues Skill

A good issue is a unit of work someone can pick up cold: it states the problem, the
evidence, and what "done" looks like. Your job is to make issues precise, findable, and
non-duplicative — and to close the loop when work lands.

## Before filing — search first
**Always check for an existing issue before opening a new one.** Use `search_issues` /
`gh issue list --search` on the key terms and error text. Duplicates fragment
discussion and annoy maintainers. If you find one, comment/upvote there (see
github-comments) instead of filing again; if filing a genuine near-duplicate, link it
("Related to #45").

## Templates — the repo's first, then these
Check `.github/ISSUE_TEMPLATE/` for forms (`*.yml`) or markdown templates and fill the
matching one (bug vs. feature vs. question). If the repo uses **issue types** or a
required-fields config, set them. A template's headings are the maintainer's expected
shape — match them.

Where the repo has none, use this skill's own, in `references/templates/`:

| Kind | Template | Use for |
|---|---|---|
| `epic` | `epic.md` | A parent: Problem, Outcome, ordered Sub-issues, Acceptance, Non-goals |
| `task` | `task.md` | A unit of work, the default sub-issue: Goal, Context, Scope in/out, Acceptance, Depends on |
| `bug` | `bug.md` | What happened, Steps, Expected, Environment, Evidence, regression Acceptance |
| `feature` | `feature.md` | Problem before Proposal, Acceptance, Non-goals |

Every non-epic template ends in **Done when** with a ready-to-paste `Closes #N` line.
Fill templates through `scripts/issue_body.py` (`render` → `check --allow-self` → file
→ `fill-self` → `check`), never by hand: the script refuses missing values, leftover
`{{placeholders}}`, guidance comments, and empty sections. Call order, the `gh`
fallback, and the traps are in `references/mechanics.md`.

## Writing a bug report
Lead with what's broken and how to see it (`references/templates/bug.md` is the shape).

- **Title = the symptom**, specific and searchable: "Upload retries forever on 503",
  not "bug in uploader".
- One bug per issue. Reproduction steps and expected-vs-actual are the parts
  maintainers most often have to ask for — include them up front.

## Writing a feature request
State the problem before the solution: **who** needs **what** and **why**, then a
proposed approach (clearly marked as a proposal), acceptance criteria, and scope/non-goals.
A feature framed as a problem invites better solutions than one framed as a demand.

## Triage — make the backlog navigable
- **Labels:** apply the repo's existing taxonomy (`bug`, `enhancement`,
  `good first issue`, area/priority labels). Read the label list first; don't invent
  labels that overlap existing ones. Use `get_label` / `gh label list`.
- **Type / milestone / assignee:** set where the project uses them.
- **Deduplicate:** close duplicates with a pointer to the canonical issue.
- **Clarify:** if an issue is unactionable, ask the one question that unblocks it
  rather than letting it rot.

## Break big work into sub-issues
An epic is a parent issue whose children are real sub-issues. Each child should be
independently shippable and pass the same "can someone pick this up cold?" bar.
- **Plan before filing.** Settle the breakdown and its dependency order first, then file
  the children **in that order** so each `Depends on #M` already exists.
- **Parent at creation.** `issue_write` with `parent_issue_number` creates and links in
  one call. The standalone link (`sub_issue_write`) takes the child's **id, not its
  number** — the most common way to link the wrong issue.
- **The epic body records order and dependencies**; GitHub's sub-issue panel records
  progress. Keep both: the panel can't say "#50 depends on #49".
- **Limits:** 100 sub-issues per parent, 8 levels deep. An epic nearing either is two
  epics.
- Where sub-issues aren't available, fall back to a list of `#N` lines in the body.

## Linking and closing
- **Link to the PR that fixes it:** the PR body's `Closes #N` (see
  github-pull-requests) auto-closes the issue on merge — prefer that over manual closing.
  It fires only for a PR into the **default branch**; one keyword per issue.
- **Epics close from their children, not from a PR.** Never put the epic's number in a
  child's closing line (the first merge would close the epic). Install
  `assets/epic-autoclose.yml` as `.github/workflows/epic-autoclose.yml` to close the
  parent when its last child closes and reopen it when a child reopens; without it,
  close the epic by hand with a pointer to the last PR.
- **Close with a reason and a pointer:** "Fixed in #210" or "Closing as won't-fix
  because …". Never close silently — the next person needs the trail.
- **Reopen** rather than file a fresh issue when a regression recurs.

## Watch Out
1. **Search before you file.** A duplicate is worse than no issue — it splits the
   conversation.
2. **No reproduction = no bug report.** Steps + expected-vs-actual + evidence are the
   difference between an actionable issue and a help-desk message.
3. **Don't invent labels.** Match the repo's taxonomy; overlapping labels make triage
   harder, not easier.
4. **Close the loop.** An issue fixed by a merged PR but left open, or closed with no
   explanation, both erode trust in the tracker.
5. **Be frugal.** File issues that capture real, actionable work — not every passing
   thought.
