#!/usr/bin/env python3
"""Plan, apply, revert and record one spend change for the optimize-spend loop. Stdlib only.

The changing half of the loop (#66, #68, #69); `benchmark.py` measures and `audit.py` proposes.
Only a finding that carries a machine edit (a frontmatter key in one file) and a benchmark task
that exercises it can be planned. Everything else stops at `plan` with the reason.

Usage:
  optimize.py plan --audit AUDIT.json [--tasks FILE] [--out PLAN.json]
  optimize.py apply --plan PLAN.json --state STATE.json [--root DIR]
  optimize.py revert --state STATE.json        # the file goes back byte for byte, or this refuses
  optimize.py keep --state STATE.json
  optimize.py record --plan PLAN.json --decision DECISION.json [--date YYYY-MM-DD]
                     [--catalog FILE] [--ledger FILE]

`apply` stores the file's original bytes in the state file; `revert` restores them and checks the
hash. If the file changed after `apply`, both `revert` and `keep` refuse instead of guessing.
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TASKS = HERE.parent / "references" / "benchmark-tasks.json"
CATALOG = HERE.parent / "references" / "spend-levers.md"
LEDGER = HERE.parents[1] / "claim-grounding" / "reviews" / "ledger.jsonl"
ROOT = HERE.parents[3]                  # the project: scripts, token-optimizer, skills, .claude, then it
CATALOG_SOURCE = "skills/token-optimizer/references/spend-levers.md"
NO_FINDING, NOT_APPLICABLE, REFUSED = 3, 3, 5
OUTCOME = re.compile(r"^  - `\d{4}-\d{2}-\d{2}` ")    # one recorded run under a lever's Measured field


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------- plan
def plan(audit: dict, tasks: list) -> tuple[dict | None, list]:
    """The first finding, in the audit's rank order, that has an edit and a task to measure it."""
    skipped = []
    for f in audit.get("findings") or []:
        key = f"{f['lever']}:{f.get('target')}"
        if not f.get("edit"):
            skipped.append(f"{f['lever']}: no machine edit, apply it by hand ({f['change']})")
            continue
        ids = [t["id"] for t in tasks if key in t.get("targets", [])]
        if not ids:
            skipped.append(f"{key}: no benchmark task exercises it")
            continue
        return {"lever": f["lever"], "target": f.get("target"), "title": f["title"], "change": f["change"],
                "edit": f["edit"], "estimate_usd": f["saving_usd"], "confidence": f["confidence"],
                "evidence": f["evidence"], "tasks": ids}, skipped
    return None, skipped


# --------------------------------------------------------------------------- the edit
def set_frontmatter(text: str, key: str, value: str) -> str:
    m = re.match(r"(---\r?\n)(.*?)(\r?\n---\r?\n)", text, re.S)
    if not m:
        raise ValueError("the file has no YAML frontmatter")
    head, body, tail = m.group(1), m.group(2), m.group(3)
    nl = "\r\n" if "\r\n" in head else "\n"
    line = re.compile(rf"^{re.escape(key)}:.*$", re.M)
    body = line.sub(f"{key}: {value}", body, count=1) if line.search(body) else f"{body}{nl}{key}: {value}"
    return head + body + tail + text[m.end():]


def apply(p: dict, state: Path, root: Path) -> int:
    if state.exists():
        print(f"a change is already in flight ({state}); keep or revert it first")
        return REFUSED
    target = (root / p["edit"]["file"]).resolve()
    if root.resolve() not in target.parents or not target.is_file():
        print(f"edit target is not a file inside the project: {p['edit']['file']}")
        return REFUSED
    original = target.read_bytes()
    changed = set_frontmatter(original.decode("utf-8"), p["edit"]["key"], p["edit"]["value"]).encode("utf-8")
    if changed == original:
        print(f"{p['edit']['file']} already has {p['edit']['key']}: {p['edit']['value']}; nothing to measure")
        return NOT_APPLICABLE
    target.write_bytes(changed)
    write_json(state, {"file": str(target), "original_b64": base64.b64encode(original).decode(),
                       "original_sha256": sha(original), "applied_sha256": sha(changed), "plan": p})
    print(f"applied: {p['edit']['file']} {p['edit']['key']}: {p['edit']['value']}")
    return 0


def revert(state: Path) -> int:
    s = load_json(state)
    target, original = Path(s["file"]), base64.b64decode(s["original_b64"])
    now = sha(target.read_bytes())
    if now == s["original_sha256"]:
        state.unlink()
        print(f"already as before: {target}")
        return 0
    if now != s["applied_sha256"]:
        print(f"{target} changed after the edit was applied; not overwriting it. Restore it from {state} by hand.")
        return REFUSED
    target.write_bytes(original)
    if sha(target.read_bytes()) != s["original_sha256"]:
        print(f"restore of {target} does not match the original hash")
        return REFUSED
    state.unlink()
    print(f"reverted: {target} is byte-identical to before the change")
    return 0


def keep(state: Path) -> int:
    s = load_json(state)
    if sha(Path(s["file"]).read_bytes()) != s["applied_sha256"]:
        print(f"{s['file']} is not as the change left it; not marking it kept")
        return REFUSED
    state.unlink()
    print(f"kept: {s['file']}")
    return 0


# --------------------------------------------------------------------------- record
def outcome_line(p: dict, d: dict, date: str) -> str:
    kept = d["verdict"] == "keep"
    quality = "held" if all(t["quality_held"] for t in d["tasks"]) else "failed"
    share = (d.get("share") or 0.0) * 100
    line = (f"  - `{date}` `{p['target']}` {p['edit']['key']} → {p['edit']['value']}: "
            f"saving ${d['saving_usd_per_pass']:.4f} a run ({share:.1f}%), noise floor ${d['floor_usd']:.4f}; "
            f"quality {quality}; **{'kept' if kept else 'rejected'}**")
    return line if kept else f"{line}: {d['reason']}"


def record_catalog(catalog: Path, lever: str, line: str) -> None:
    text = catalog.read_text(encoding="utf-8")
    m = re.search(rf"^### `{re.escape(lever)}`\n(.*?)(?=^### |^## |\Z)", text, re.M | re.S)
    if not m:
        raise ValueError(f"lever {lever} is not in {catalog}")
    lines = m.group(0).split("\n")
    i = next((k for k, s in enumerate(lines) if s.startswith("- **Measured:**")), None)
    if i is None:
        raise ValueError(f"lever {lever} has no Measured field")
    j = i + 1
    while j < len(lines) and OUTCOME.match(lines[j]):
        j += 1
    outcomes = lines[i + 1:j] + [line]
    n = len(outcomes)
    lines[i:j] = [f"- **Measured:** {n} optimize-spend run{'s' if n > 1 else ''}, newest last."] + outcomes
    catalog.write_text(text[:m.start()] + "\n".join(lines) + text[m.end():], encoding="utf-8")


def ledger_row(p: dict, d: dict, date: str) -> dict:
    kept = d["verdict"] == "keep"
    return {"id": {"source": CATALOG_SOURCE,
                   "symbol": f"{p['lever']} {p['target']}: {p['edit']['key']} → {p['edit']['value']} saves spend "
                             "without losing quality",
                   "rule": "measured-outcome", "severity": "info"},
            "verdict": "confirmed" if kept else "refuted", "count": d.get("runs", 0),
            "rationale": (f"Benchmark tasks {', '.join(p['tasks'])}: saving ${d['saving_usd_per_pass']:.4f} a pass "
                          f"against a noise floor of ${d['floor_usd']:.4f}; {d['reason']}. The audit estimated "
                          f"~${p['estimate_usd']:.2f} from logs ({p['confidence']} confidence)."),
            "grounded_by": "probe:token-optimizer/scripts/benchmark.py decide", "checked": date}


def record(p: dict, d: dict, date: str, catalog: Path, ledger: Path) -> int:
    if d["verdict"] not in ("keep", "reject"):
        print(f"decision is {d['verdict']} ({d.get('reason')}): not an outcome, nothing recorded")
        return REFUSED
    line = outcome_line(p, d, date)
    record_catalog(catalog, p["lever"], line)
    with ledger.open("a", encoding="utf-8") as f:
        f.write(json.dumps(ledger_row(p, d, date)) + "\n")
    print(f"recorded in {catalog.name} and {ledger.name}:\n{line}")
    return 0


def main(argv: list | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("plan")
    s.add_argument("--audit", type=Path, required=True)
    s.add_argument("--tasks", type=Path, default=TASKS)
    s.add_argument("--out", type=Path)
    s = sub.add_parser("apply")
    s.add_argument("--plan", type=Path, required=True)
    s.add_argument("--state", type=Path, required=True)
    s.add_argument("--root", type=Path, default=ROOT)
    for name in ("revert", "keep"):
        s = sub.add_parser(name)
        s.add_argument("--state", type=Path, required=True)
    s = sub.add_parser("record")
    s.add_argument("--plan", type=Path, required=True)
    s.add_argument("--decision", type=Path, required=True)
    s.add_argument("--date", default=dt.date.today().isoformat())
    s.add_argument("--catalog", type=Path, default=CATALOG)
    s.add_argument("--ledger", type=Path, default=LEDGER)
    a = ap.parse_args(argv)
    if a.cmd == "plan":
        audit = load_json(a.audit)
        if not audit.get("findings"):
            print("No material finding.")
            return NO_FINDING
        p, skipped = plan(audit, load_json(a.tasks)["tasks"])
        for line in skipped:
            print(f"skipped: {line}")
        if not p:
            print("no material finding the loop can apply and measure")
            return NOT_APPLICABLE
        if a.out:
            write_json(a.out, p)
        print(json.dumps(p, indent=1))
        return 0
    if a.cmd == "apply":
        return apply(load_json(a.plan), a.state, a.root)
    if a.cmd == "revert":
        return revert(a.state)
    if a.cmd == "keep":
        return keep(a.state)
    return record(load_json(a.plan), load_json(a.decision), a.date, a.catalog, a.ledger)


if __name__ == "__main__":
    sys.exit(main())
