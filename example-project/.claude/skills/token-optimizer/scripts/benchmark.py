#!/usr/bin/env python3
"""Run fixed tasks through `claude -p`, record each run's spend, and tell a saving from noise. Stdlib only.

The measuring half of the optimize-spend loop (#66, #67). Each task in
`../references/benchmark-tasks.json` runs in a throwaway copy of the project, with the project's
own CLAUDE.md, skills, agents and hooks loaded (no `--bare`), read-only tools, write tools denied,
and no session log written. A run's spend is the `total_cost_usd` the CLI reports, cross-checked
against `../references/pricing.json` through usage.py. A task's own check judges the answer, so a
cheaper run that answers worse fails rather than counting as a saving.

Usage:
  benchmark.py probe [--claude PATH]               # can this machine run claude -p, with tools, under a cap?
  benchmark.py selfcheck [--tasks FILE]            # each check passes its good sample and fails its broken one
  benchmark.py run --label baseline|candidate --repeat N --cap-usd X --out FILE.jsonl
                   [--task ID ...] [--tasks FILE] [--root DIR] [--claude PATH]
  benchmark.py floor --results FILE.jsonl [--label baseline]
  benchmark.py decide --results FILE.jsonl

Spend is capped twice: every run gets `--max-budget-usd` set to what is left of the cap (the
CLI's own stop, which `probe` shows working), and the runner starts no run once less than
MIN_RUN_USD is left. A run can overshoot its budget by the call in flight; the runner counts
what the CLI reports, so the total says what was really spent.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import usage  # noqa: E402

TASKS = HERE.parent / "references" / "benchmark-tasks.json"
ROOT = HERE.parents[3]                  # the project: scripts, token-optimizer, skills, .claude, then it
WRITE_TOOLS = "Edit,Write,NotebookEdit,MultiEdit"
SCRUB_ENV = ("CLAUDE_CODE_SESSION_ID", "CLAUDE_CODE_REMOTE_SESSION_ID")  # else the child reports this session's id
COPY_IGNORE = (".git", "__pycache__", ".venv", "node_modules", ".meta")
DEFAULT_MODEL = "haiku"
DEFAULT_RUN_CAP = 0.50
MIN_RUN_USD = 0.01
MIN_REPEAT = 2
TIMEOUT_S = 900
RESULT_KEEP = 4000                      # characters of each answer kept in the results file
PRICE_TOLERANCE = 0.005                 # harness cost vs pricing.json, either side of the 5m..1h band


# --------------------------------------------------------------------------- tasks and checks
def load_tasks(path: Path = TASKS) -> dict:
    tasks = json.loads(path.read_text(encoding="utf-8"))["tasks"]
    return {t["id"]: t for t in tasks}


def judge(task: dict, result: str, agents: list, changed: list, subtype: str) -> tuple[bool, str]:
    """The task's quality guard: (passed, why). Every condition must hold."""
    c = task["check"]
    if subtype != "success":
        return False, f"the run did not finish ({subtype})"
    if changed:
        return False, f"the run changed files: {', '.join(changed[:5])}"
    for pat in c.get("all", []):
        if not re.search(pat, result, re.I):
            return False, f"answer lacks /{pat}/"
    for pat in c.get("none", []):
        if re.search(pat, result, re.I):
            return False, f"answer contains /{pat}/"
    for agent in c.get("agents", []):
        if agent not in agents:
            return False, f"the {agent} agent did not run"
    return True, "check passed"


def selfcheck(tasks: dict) -> int:
    rows = []
    for t in tasks.values():
        s, need = t["samples"], t["check"].get("agents", [])
        rows.append((f"{t['id']}: good sample passes", judge(t, s["pass"], need, [], "success")[0]))
        rows.append((f"{t['id']}: broken sample fails", not judge(t, s["fail"], need, [], "success")[0]))
        rows.append((f"{t['id']}: a run that edits a file fails", not judge(t, s["pass"], need, ["x.md"], "success")[0]))
        rows.append((f"{t['id']}: a run stopped by the cap fails",
                     not judge(t, s["pass"], need, [], "error_max_budget_usd")[0]))
        if need:
            rows.append((f"{t['id']}: the answer without the agent fails", not judge(t, s["pass"], [], [], "success")[0]))
    width = max(len(n) for n, _ in rows)
    for name, ok in rows:
        print(f"{'PASS' if ok else 'FAIL'}  {name.ljust(width)}")
    passed = sum(ok for _, ok in rows)
    print(f"\n{passed}/{len(rows)} passed")
    return 0 if passed == len(rows) else 1


# --------------------------------------------------------------------------- one run
def tree_digest(root: Path) -> dict:
    out = {}
    for p in sorted(root.rglob("*")):
        if p.is_file() and not p.is_symlink():
            out[str(p.relative_to(root))] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def changed_files(before: dict, after: dict) -> list:
    return sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))


def child_env() -> dict:
    return {k: v for k, v in os.environ.items() if k not in SCRUB_ENV}


def parse_stream(stdout: str) -> tuple[dict, str]:
    """The stream's result object, and every main-thread assistant text joined.

    The answer is judged on all of the main thread's text, not the final message alone: a
    project Stop hook can add a turn after the answer, and that reply becomes `result`.
    """
    result, texts = {}, []
    for line in stdout.strip().splitlines():
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if not isinstance(d, dict):
            continue
        if d.get("type") == "result":
            result = d
        elif d.get("type") == "assistant" and not d.get("parent_tool_use_id"):
            for block in (d.get("message") or {}).get("content") or []:
                if isinstance(block, dict) and block.get("type") == "text":
                    texts.append(block.get("text", ""))
    texts.append(str(result.get("result") or ""))
    return result, "\n".join(t for t in texts if t)


def priced_band(model_usage: dict, prices: dict) -> tuple[float, float, list]:
    """The list-price range the reported tokens allow, and the models pricing.json lacks.

    `modelUsage` sums a whole run, so it can't say which calls passed 100K and took the
    long-context rate. The low end prices every call at the base rate with 5m writes; the high
    end lets the long-context rate apply when the run's total prompt passes 100K, with 1h writes.
    """
    lo = hi = 0.0
    unpriced = []
    for model, u in (model_usage or {}).items():
        rate = usage.rate_for(prices, model)
        if not rate:
            unpriced.append(model)
            continue
        t = {"input": u.get("inputTokens", 0), "output": u.get("outputTokens", 0),
             "cache_read": u.get("cacheReadInputTokens", 0), "cache_write": u.get("cacheCreationInputTokens", 0)}
        base = {k: v for k, v in rate.items() if k != "over_100k"}
        lo += usage.price(base, dict(t, cache_write_5m=t["cache_write"]))
        hi += usage.price(rate, t)
    return lo, hi, unpriced


def agents_run(d: dict) -> list:
    by_type = ((d.get("subagent_stats") or {}).get("by_type")) or {}
    return sorted(by_type) if isinstance(by_type, dict) else sorted(map(str, by_type))


def run_one(task: dict, budget: float, root: Path, claude: str, prices: dict) -> dict:
    with tempfile.TemporaryDirectory(prefix="bench-") as t:
        work = Path(t) / "project"
        shutil.copytree(root, work, symlinks=True, ignore=shutil.ignore_patterns(*COPY_IGNORE))
        before = tree_digest(work)
        cmd = [claude, "-p", task["prompt"], "--output-format", "stream-json", "--verbose",
               "--model", task.get("model", DEFAULT_MODEL), "--max-budget-usd", f"{budget:.4f}",
               "--no-session-persistence", "--allowedTools", ",".join(task["tools"]),
               "--disallowedTools", WRITE_TOOLS]
        try:
            proc = subprocess.run(cmd, cwd=work, env=child_env(), capture_output=True, text=True,
                                  timeout=task.get("timeout", TIMEOUT_S))
            d, answer = parse_stream(proc.stdout)
            err = None if d else (proc.stderr.strip()[-500:] or f"exit {proc.returncode}, no JSON result")
        except subprocess.TimeoutExpired:
            d, answer, err = {}, "", f"timed out after {task.get('timeout', TIMEOUT_S)}s"
        changed = changed_files(before, tree_digest(work))
    cost = float(d.get("total_cost_usd") or 0.0)
    result = str(d.get("result") or "")
    subtype = d.get("subtype") or ("error" if err else "unknown")
    agents = agents_run(d)
    passed, why = judge(task, answer, agents, changed, subtype) if not err else (False, err)
    lo, hi, unpriced = priced_band(d.get("modelUsage"), prices)
    reconciled = None if unpriced or not d else (lo * (1 - PRICE_TOLERANCE) <= cost <= hi * (1 + PRICE_TOLERANCE))
    return {"task": task["id"], "cost_usd": round(cost, 6), "budget_usd": round(budget, 4),
            "overshoot_usd": round(max(0.0, cost - budget), 6), "subtype": subtype,
            "is_error": bool(d.get("is_error")) or bool(err), "passed": passed, "why": why,
            "num_turns": d.get("num_turns"), "duration_ms": d.get("duration_ms"),
            "models": {m: round(u.get("costUSD", 0.0), 6) for m, u in (d.get("modelUsage") or {}).items()},
            "model_usage": d.get("modelUsage") or {}, "usage": {k: v for k, v in (d.get("usage") or {}).items()
                                                                if k != "iterations"},
            "agents": agents, "changed": changed, "priced_band_usd": [round(lo, 6), round(hi, 6)],
            "reconciled": reconciled, "unpriced": unpriced, "result": result[:RESULT_KEEP],
            "answer": answer[:RESULT_KEEP]}


# --------------------------------------------------------------------------- the runner
def read_results(path: Path) -> list:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def run(tasks: dict, ids: list, label: str, repeat: int, cap: float, out: Path, root: Path,
        claude: str) -> int:
    if label == "baseline" and repeat < MIN_REPEAT:
        print(f"a baseline needs at least {MIN_REPEAT} runs a task to measure its noise floor")
        return 2
    unknown = [i for i in ids if i not in tasks]
    if unknown:
        print(f"unknown task(s): {', '.join(unknown)}")
        return 2
    prices = usage.load_prices()
    spent, done, stopped = 0.0, 0, None
    for rep in range(1, repeat + 1):
        for tid in ids:
            left = cap - spent
            if left < MIN_RUN_USD:
                stopped = f"cap reached: ${spent:.4f} of ${cap:.2f} spent, {done} run(s) done"
                break
            budget = min(tasks[tid].get("run_cap", DEFAULT_RUN_CAP), left)
            rec = run_one(tasks[tid], budget, root, claude, prices)
            rec.update(label=label, rep=rep)
            with out.open("a", encoding="utf-8") as f:
                f.write(json.dumps(rec) + "\n")
            spent += rec["cost_usd"]
            done += 1
            print(f"{label} {tid} #{rep}: ${rec['cost_usd']:.4f} (budget ${budget:.4f}) "
                  f"{'pass' if rec['passed'] else 'FAIL: ' + rec['why']}")
        if stopped:
            break
    total = sum(r["cost_usd"] for r in read_results(out))
    print(f"{label}: {done} run(s), ${spent:.4f} this invocation (cap ${cap:.2f}); "
          f"${total:.4f} across {out.name}")
    if stopped:
        print(stopped)
        return 4
    return 0


def stats(records: list, label: str) -> dict:
    by_task: dict = {}
    for r in records:
        if r.get("label") == label:
            by_task.setdefault(r["task"], []).append(r)
    out = {}
    for tid, rs in by_task.items():
        costs = [r["cost_usd"] for r in rs]
        mean = statistics.fmean(costs)
        floor = noise_floor(costs)
        out[tid] = {"n": len(costs), "mean_usd": round(mean, 6), "min_usd": min(costs), "max_usd": max(costs),
                    "floor_usd": None if floor is None else round(floor, 6),
                    "floor_share": round(floor / mean, 4) if mean and floor is not None else None,
                    "passed": sum(r["passed"] for r in rs), "failed": [r["why"] for r in rs if not r["passed"]]}
    return out


def noise_floor(costs: list) -> float | None:
    """The spread of repeated runs of one task: a difference inside it is indistinguishable from noise."""
    return max(costs) - min(costs) if len(costs) >= MIN_REPEAT else None


def decide(records: list) -> dict:
    base, cand = stats(records, "baseline"), stats(records, "candidate")
    rows, reasons = [], []
    for tid, b in base.items():
        c = cand.get(tid)
        if b["n"] < MIN_REPEAT:
            reasons.append(f"{tid}: {b['n']} baseline run(s), the floor needs {MIN_REPEAT}")
        if b["failed"]:
            reasons.append(f"{tid}: the baseline fails its own check ({b['failed'][0]}), so the benchmark is broken")
        if not c:
            reasons.append(f"{tid}: no candidate runs")
            continue
        floor = max(b["floor_usd"] or 0.0, c["floor_usd"] or 0.0)
        rows.append({"task": tid, "baseline_mean_usd": b["mean_usd"], "candidate_mean_usd": c["mean_usd"],
                     "saving_usd": round(b["mean_usd"] - c["mean_usd"], 6), "floor_usd": round(floor, 6),
                     "quality_held": not c["failed"], "candidate_failures": c["failed"]})
    if reasons:
        return {"verdict": "invalid", "reason": "; ".join(reasons), "tasks": rows}
    saving = sum(r["saving_usd"] for r in rows)
    floor = sum(r["floor_usd"] for r in rows)
    base_total = sum(r["baseline_mean_usd"] for r in rows)
    broke = [r for r in rows if not r["quality_held"]]
    if broke:
        verdict, reason = "reject", (f"quality guard failed on {broke[0]['task']}: "
                                     f"{broke[0]['candidate_failures'][0]}")
    elif saving <= 0:
        verdict, reason = "reject", "the candidate costs more"
    elif saving <= floor:
        verdict, reason = "reject", "saving within the noise floor"
    else:
        verdict, reason = "keep", "saving exceeds the noise floor and every check passed"
    return {"verdict": verdict, "reason": reason, "saving_usd_per_pass": round(saving, 6),
            "floor_usd": round(floor, 6), "share": round(saving / base_total, 4) if base_total else None,
            "runs": sum(1 for r in records if r.get("label") in ("baseline", "candidate")),
            "unreconciled_runs": sum(1 for r in records if r.get("reconciled") is False),
            "spent_usd": round(sum(r["cost_usd"] for r in records), 6), "tasks": rows}


# --------------------------------------------------------------------------- probe
def probe(claude: str) -> int:
    """Four tiny runs: text, a tool, the budget cap, a subagent. Each answers one question."""
    prices = usage.load_prices()
    token = base64.b32encode(os.urandom(5)).decode().lower()
    with tempfile.TemporaryDirectory(prefix="bench-probe-") as t:
        root = Path(t)
        (root / "probe.txt").write_text(f"{token}\n", encoding="utf-8")
        cases = [
            ("text", {"id": "probe-text", "prompt": "Reply with the single word OK.", "tools": ["Read"],
                      "check": {"all": [r"\bOK\b"]}}, 0.05),
            ("tools", {"id": "probe-tools", "prompt": "Read probe.txt and reply with the one word it holds.",
                       "tools": ["Read"], "check": {"all": [re.escape(token)]}}, 0.05),
            ("cap", {"id": "probe-cap", "prompt": "Read probe.txt, then list this directory with Glob, then read "
                     "probe.txt again, and reply with its word.", "tools": ["Read", "Glob"],
                     "check": {"all": [re.escape(token)]}}, 0.0001),
            ("subagent", {"id": "probe-agent", "prompt": "Use the Agent tool to have a general-purpose subagent "
                          "read probe.txt and report its word, then reply with that word.",
                          "tools": ["Agent", "Read"], "check": {"all": [re.escape(token)],
                                                                "agents": ["general-purpose"]}}, 0.20),
        ]
        out = {}
        for name, task, budget in cases:
            rec = run_one(task, budget, root, claude, prices)
            out[name] = rec
            print(f"{name}: subtype {rec['subtype']}, ${rec['cost_usd']:.4f} (budget ${budget}), "
                  f"{'pass' if rec['passed'] else rec['why']}; agents {rec['agents'] or 'none'}; "
                  f"priced band {rec['priced_band_usd']} reconciled {rec['reconciled']}; models {rec['models']}")
    print("subagent run, raw:", json.dumps({"modelUsage": out["subagent"]["model_usage"],
                                            "usage": out["subagent"]["usage"]}))
    cap = out["cap"]
    verdict = {
        "claude_p_runs": out["text"]["passed"],
        "tools_run": out["tools"]["passed"],
        "cap_stops_a_run": cap["subtype"] != "success" and not cap["passed"],
        "cap_overshoot_usd": cap["overshoot_usd"],
        "subagents_run": out["subagent"]["passed"],
        "cost_reconciles_with_pricing": all(r["reconciled"] for r in out.values() if r["reconciled"] is not None),
        "spent_usd": round(sum(r["cost_usd"] for r in out.values()), 6),
    }
    print(json.dumps(verdict, indent=1))
    return 0 if verdict["claude_p_runs"] and verdict["tools_run"] and verdict["cap_stops_a_run"] else 1


def main(argv: list | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("probe")
    p.add_argument("--claude", default="claude")
    p = sub.add_parser("selfcheck")
    p.add_argument("--tasks", type=Path, default=TASKS)
    p = sub.add_parser("run")
    p.add_argument("--label", required=True, choices=("baseline", "candidate"))
    p.add_argument("--repeat", type=int, default=3)
    p.add_argument("--cap-usd", type=float, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--task", action="append")
    p.add_argument("--tasks", type=Path, default=TASKS)
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--claude", default="claude")
    p = sub.add_parser("floor")
    p.add_argument("--results", type=Path, required=True)
    p.add_argument("--label", default="baseline")
    p = sub.add_parser("decide")
    p.add_argument("--results", type=Path, required=True)
    a = ap.parse_args(argv)
    if a.cmd == "probe":
        return probe(a.claude)
    if a.cmd == "selfcheck":
        return selfcheck(load_tasks(a.tasks))
    if a.cmd == "run":
        tasks = load_tasks(a.tasks)
        return run(tasks, a.task or list(tasks), a.label, a.repeat, a.cap_usd, a.out, a.root.resolve(), a.claude)
    records = read_results(a.results)
    if a.cmd == "floor":
        s = stats(records, a.label)
        print(json.dumps(s, indent=1))
        return 0 if s and all(v["n"] >= MIN_REPEAT for v in s.values()) else 1
    d = decide(records)
    print(json.dumps(d, indent=1))
    return {"keep": 0, "reject": 3, "invalid": 1}[d["verdict"]]


if __name__ == "__main__":
    sys.exit(main())
