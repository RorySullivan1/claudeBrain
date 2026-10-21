---
description: Review what Claude Code sessions spent and get a ranked list of changes that would cut it — dispatches the read-only spend-auditor agent and relays its capped report.
argument-hint: [session [ID] | command <name> | last N | all]  (default: session, this one)
---

You are running a spend review. The procedure lives in the `spend-auditor` agent and the
script it runs (`token-optimizer/scripts/audit.py`). This command picks the scope, hands it
over, and relays the answer. **It changes nothing:** a finding is a proposal.

The request: $ARGUMENTS

## 1. Map the argument to a filter

| Argument | Filter passed to `audit.py` |
|---|---|
| *(none)* or `session` | `--session current` (the newest session log, which is this one) |
| `session <ID>` | `--session <ID>` (an ID prefix is enough) |
| `command <name>` | `--command /<name>` (prompts that ran that slash command) |
| `last <N>` | `--last <N>` (the N most recent prompts) |
| `all` | no filter: every session in this project's logs |

Anything else: say which forms are accepted and stop. A `command` or `last` filter scopes to
prompts, so background requests drop out of the total and the report says so.

## 2. Dispatch

Delegate to the `spend-auditor` agent with the filter from step 1. Tell it to return its
report as specified (at most 30 lines, every number from the script). Don't run the audit
in the main thread: the point of the agent is that the profile and the catalog never enter
this context.

## 3. Relay

Show the agent's report as it returned it. Don't add findings, re-rank them or restate the
savings as anything but estimates. If it says "No material finding.", say that and stop.

Then offer, once, to file accepted findings as issues: the user picks which, and each
becomes one `/issue` with the evidence numbers and the lever's catalog section as its
context. File nothing without that choice.
