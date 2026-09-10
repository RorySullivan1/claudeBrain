# Probe kit — parallel state (issue #51)

**Question:** the factory's state files are written as if exactly one unit of work is ever in
flight. Before reshaping them to permit parallel worktrees, does the collision actually happen —
and in the shape the issue described?

Run: `python3 example-project/.claude/hooks/probes/probe_parallel_state.py`

## How to read a run

Four controls gate the run: the guard must stay **silent** when cursor and map agree and **warn**
when they drift (otherwise a silent result proves nothing), and the merge harness must produce a
**clean** merge on disjoint regions and a **conflict** on the same line (otherwise a "clean"
result proves nothing). A control FAIL prints STOP-THE-LINE and everything below it is discarded.

## Run log — 2026-09-10

All four controls PASSed. Findings, against the three claims as filed:

| Claim | Verdict | What the run showed |
|---|---|---|
| C1 `roadmap_guard.py` can only see one cursor | **REFUTED** | With two in-flight versions against one shared roadmap INDEX, the guard was correctly silent in worktree A and produced the correct, specific warning in worktree B. It is already **per-version**, not per-cursor. |
| C2 `.meta/version` collides between worktrees | **CONFIRMED, reshaped** | Not at runtime — each worktree has its own checkout, so each guard reads its own file. The collision is at **merge**, and it is a loud conflict, not a silent overwrite. |
| C3 State is lost on merge; append-only sections merge | **CONFIRMED / REFUTED** | State conflicts as predicted. But the append-only sections do **not** merge cleanly: two appends at the same insertion point conflict too. Git has no notion of append-only. |

### Why C1 read as true from the source

`parse_index()` computes a `cursor` — and `check()` throws it away (`statuses, _cursor = …`).
Every comparison it makes is keyed off *this* worktree's own `version:` label looked up in the
shared table, which is exactly the branch-safe shape. The dead variable is what made the function
look single-cursor to a reader. It is now removed, so the code reads the way it behaves.

### The finding that matters

**Nothing is silently corrupted.** Every collision surfaces as a git conflict with **both sides
preserved** in the conflict region. The risk is not data loss; it is the **resolution**, and in a
realistic run (each session rewrites State and appends to the Log) the two hunks need *opposite*
resolutions:

- **Log / Decisions hunk → keep both**, in date order. The conflict is an artifact of two appends
  landing on the same line; both entries are true and both belong.
- **State hunk → rewrite from both.** Neither side alone is correct: each describes a different
  unit of work that is genuinely in flight. Taking one side is the only real loss available here,
  and it is a human choice, not something git does.

That asymmetry is the whole constraint, and it is why the decision (recorded in
`.claude/memory/INDEX.md`) was to **state the constraint** rather than reshape three assets to
solve a corruption that does not occur.

## Closing the loop

A CONFIRMED claim is fixed at the source, and a REFUTED one is corrected there too — never
softened to save the claim. C1's refutation removed the dead `_cursor`; C3's refutation replaced
"the append-only sections merge" with the resolution rule above, in `session-memory`'s SKILL.md.
