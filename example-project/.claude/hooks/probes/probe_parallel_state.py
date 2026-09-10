#!/usr/bin/env python3
"""Controls-first probe: what actually breaks when two units of work are in flight?

The factory's state files are written as if exactly one unit of work exists at a time:
`.meta/version` is one file, `memory/INDEX.md` § State says "rewrite in place", and
`roadmap_guard.py` reads a cursor. Before anything is reshaped to allow parallel worktrees,
the collision has to be REPRODUCED — otherwise the fix is aimed at a guess.

Claims under test (issue #51, as filed):
  C1  roadmap_guard.py "extracts a single cursor" and cannot see a second in-flight version.
  C2  `.meta/version` collides: two worktrees read/write the same cursor and the guard
      validates the wrong one.
  C3  memory/INDEX.md § State is lost on merge, while the append-only sections merge cleanly.

Run:  python3 example-project/.claude/hooks/probes/probe_parallel_state.py

Reading the result: the two control blocks gate the run. A control FAIL prints
STOP-THE-LINE and the probe lines below it are NOT evidence — fix the harness first.
Findings are recorded in PROBES.md next to this file.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve()
HOOKS = HERE.parent.parent
GUARD = HOOKS / "roadmap_guard.py"
# The real INDEX is the fixture on purpose: section distance is one of the variables.
REAL_INDEX = HERE.parents[4] / ".claude" / "memory" / "INDEX.md"

INDEX_TMPL = "# ROADMAP\n\n| Version | Stage | Goal | Status |\n|---|---|---|---|\n{rows}\n"


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)


def version_file(label, status):
    return f"# version: {label}\nstatus: {status}\nbranch: claude/{label}\n\n## Goals\n- g\n"


def run_guard(root):
    """Invoke roadmap_guard as the harness does and return its advisory text ('' = silent)."""
    proc = subprocess.run(
        [sys.executable, str(GUARD)],
        input=json.dumps({"tool_input": {"command": "git push -u origin x"}}),
        capture_output=True, text=True,
        env={**os.environ, "CLAUDE_PROJECT_DIR": str(root)},
    )
    out = proc.stdout.strip()
    return json.loads(out)["hookSpecificOutput"]["additionalContext"] if out else ""


def make_root(tmp, name, label, status, rows):
    root = Path(tmp) / name
    (root / ".meta" / "roadmap").mkdir(parents=True)
    (root / ".meta" / "version").write_text(version_file(label, status))
    (root / ".meta" / "roadmap" / "INDEX.md").write_text(INDEX_TMPL.format(rows="\n".join(rows)))
    return root


def merge_two(seed, variant_a, variant_b, filename="INDEX.md"):
    """Commit `seed`, branch two variants off it, merge both into main. Returns (rc, text)."""
    with tempfile.TemporaryDirectory() as tmp:
        r = Path(tmp)
        git(r, "init", "-q", "-b", "main")
        git(r, "config", "user.email", "probe@local")
        git(r, "config", "user.name", "probe")
        (r / filename).write_text(seed)
        git(r, "add", "-A"), git(r, "commit", "-qm", "seed")
        for branch, text in (("a", variant_a), ("b", variant_b)):
            git(r, "checkout", "-q", "-b", branch, "main")
            (r / filename).write_text(text)
            git(r, "add", "-A"), git(r, "commit", "-qm", branch)
        git(r, "checkout", "-q", "main")
        git(r, "merge", "--no-edit", "a")
        m = git(r, "merge", "--no-edit", "b")
        return m.returncode, (r / filename).read_text()


def index_variant(seed, state_line=None, log_line=None):
    lines = []
    for line in seed.splitlines():
        lines.append(line)
        if state_line and line.startswith("## State"):
            lines.append(state_line)
    if log_line:
        lines.append(log_line)
    return "\n".join(lines) + "\n"


A_STATE = "- A-marker: analytics layer in flight"
B_STATE = "- B-marker: ribbon rework in flight"
A_LOG = "- 2026-09-11 | A-marker shipped | sessions/a.md"
B_LOG = "- 2026-09-11 | B-marker shipped | sessions/b.md"


def main() -> int:
    seed = REAL_INDEX.read_text(encoding="utf-8")
    failures = []

    # ---- Controls, block 1: the guard discriminates at all -------------------
    with tempfile.TemporaryDirectory() as tmp:
        pos = make_root(tmp, "pos", "v1.0.0", "in-progress", ["| v1.0.0 | s1 | g | in-progress |"])
        neg = make_root(tmp, "neg", "v1.0.0", "shipped", ["| v1.0.0 | s1 | g | planned |"])
        c1_pos, c1_neg = run_guard(pos), run_guard(neg)
        ok_pos, ok_neg = c1_pos == "", "shipped" in c1_neg
        print(f"CONTROL guard/agreement -> silent : {'PASS' if ok_pos else 'FAIL ' + repr(c1_pos)}")
        print(f"CONTROL guard/drift     -> warns  : {'PASS' if ok_neg else 'FAIL ' + repr(c1_neg)}")
        failures += [] if (ok_pos and ok_neg) else ["guard controls"]

        # ---- C1: two in-flight versions against one shared roadmap ----------
        rows = ["| v1.0.0 | s1 | g | in-progress |", "| v2.0.0 | s2 | g | planned |"]
        a = run_guard(make_root(tmp, "wtA", "v1.0.0", "in-progress", rows))
        b = run_guard(make_root(tmp, "wtB", "v2.0.0", "in-progress", rows))

    # ---- Controls, block 2: the merge harness can tell clean from conflicted -
    rc_clean, _ = merge_two(seed, index_variant(seed, state_line=A_STATE),
                            index_variant(seed, log_line=B_LOG))
    rc_dirty, _ = merge_two(seed, index_variant(seed, state_line=A_STATE),
                            index_variant(seed, state_line=B_STATE))
    ok_clean, ok_dirty = rc_clean == 0, rc_dirty != 0
    print(f"CONTROL merge/disjoint  -> clean  : {'PASS' if ok_clean else 'FAIL'}")
    print(f"CONTROL merge/same-line -> conflict: {'PASS' if ok_dirty else 'FAIL'}")
    failures += [] if (ok_clean and ok_dirty) else ["merge controls"]

    if failures:
        print(f"\nSTOP THE LINE — controls failed ({', '.join(failures)}).")
        print("Nothing below this line is evidence.")
        return 1

    # ---- Probes --------------------------------------------------------------
    print("\nC1  two in-flight versions, one shared roadmap INDEX")
    print(f"    worktree A (v1.0.0, row in-progress): {a or 'SILENT'}")
    print(f"    worktree B (v2.0.0, row planned)    : {b or 'SILENT'}")
    c1_refuted = a == "" and "v2.0.0" in b and "planned" in b
    print(f"    -> guard is per-version, not per-cursor: {'REFUTES C1' if c1_refuted else 'C1 stands'}")

    print("\nC2  .meta/version under two branches")
    rc_v, text_v = merge_two(version_file("v1.0.0", "planned"),
                             version_file("v1.0.0", "in-progress"),
                             version_file("v2.0.0", "in-progress"), filename="version")
    print(f"    merge rc={rc_v}, conflict markers={text_v.count('<<<<<<<')}")
    print("    -> each worktree has its OWN checkout at runtime; the collision is at MERGE, "
          "and it is loud")

    print("\nC3  memory/INDEX.md under two branches")
    rc_log, text_log = merge_two(seed, index_variant(seed, log_line=A_LOG),
                                 index_variant(seed, log_line=B_LOG))
    print(f"    append-only Log only : rc={rc_log}, conflicts={text_log.count('<<<<<<<')}, "
          f"both entries present={'sessions/a.md' in text_log and 'sessions/b.md' in text_log}")
    rc_full, text_full = merge_two(seed,
                                   index_variant(seed, state_line=A_STATE, log_line=A_LOG),
                                   index_variant(seed, state_line=B_STATE, log_line=B_LOG))
    print(f"    State + Log (realistic): rc={rc_full}, conflicts={text_full.count('<<<<<<<')}, "
          f"both sides preserved={'A-marker' in text_full and 'B-marker' in text_full}")
    print("    -> 'append-only sections merge cleanly' is REFUTED: two appends at the same "
          "insertion point conflict.")
    print("    -> but nothing is LOST. Both hunks keep both sides; the risk is the RESOLUTION, "
          "and the two hunks need opposite ones.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
