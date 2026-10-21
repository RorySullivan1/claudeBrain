#!/usr/bin/env python3
"""Probe the optimize-spend loop (#66): benchmark.py against a stub `claude`, and optimize.py's edits.

    python3 probe_optimize.py --selftest    # no network, no spend: a stub stands in for claude -p

The stub answers each `claude -p` call from a scripted list and logs the argv, the cwd and the
environment it saw, so the probe can check what the runner really passes: the budget, the
denied write tools, the throwaway copy, the scrubbed session id. Decisions run on planted
results whose right answer is known. Each break disables one guard and must turn a check red.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import os
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
import audit  # noqa: E402
import benchmark  # noqa: E402
import optimize  # noqa: E402
import usage  # noqa: E402

WORKFLOW = HERE.parents[2] / "workflows" / "optimize-spend.md"
FACTORY_LINK = HERE.parents[4] / ".claude" / "workflows" / "optimize-spend.md"
HAIKU = "claude-haiku-5-5"

STUB = r'''#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
plan = json.loads(Path(os.environ["STUB_PLAN"]).read_text())
n_file = Path(os.environ["STUB_PLAN"] + ".n")
n = int(n_file.read_text()) if n_file.exists() else 0
n_file.write_text(str(n + 1))
r = plan["responses"][min(n, len(plan["responses"]) - 1)]
argv = sys.argv[1:]
budget = float(argv[argv.index("--max-budget-usd") + 1])
with open(plan["log"], "a") as f:
    f.write(json.dumps({"argv": argv, "cwd": os.getcwd(),
                        "session_env": "CLAUDE_CODE_SESSION_ID" in os.environ}) + "\n")
if r.get("touch"):
    Path(r["touch"]).write_text("edited by the run\n")
cost, subtype = r["cost"], r.get("subtype", "success")
if cost > budget:
    cost, subtype = budget + 0.001, "error_max_budget_usd"
tokens = r.get("tokens", {"inputTokens": 0, "outputTokens": 0, "cacheReadInputTokens": 0,
                          "cacheCreationInputTokens": 0})
for text, parent in r.get("stream", []):
    print(json.dumps({"type": "assistant", "parent_tool_use_id": parent,
                      "message": {"content": [{"type": "text", "text": text}]}}))
print(json.dumps({"type": "result", "subtype": subtype, "is_error": subtype != "success",
                  "total_cost_usd": cost, "result": r.get("result", ""), "num_turns": 3,
                  "modelUsage": {r.get("model", "claude-haiku-5-5"): dict(tokens, costUSD=cost)},
                  "subagent_stats": {"by_type": {a: 1 for a in r.get("agents", [])}}}))
'''

GOOD = {t["id"]: t["samples"]["pass"] for t in benchmark.load_tasks().values()}
BAD = {t["id"]: t["samples"]["fail"] for t in benchmark.load_tasks().values()}


def digest(root: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(root.rglob("*")):
        if p.is_file():
            h.update(str(p.relative_to(root)).encode() + p.read_bytes())
    return h.hexdigest()


def quiet(fn, *a, **k):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = fn(*a, **k)
    return code, buf.getvalue()


def project(tmp: Path, name: str, agent_text: str = "---\nname: python-developer\nmodel: sonnet\n---\nbody\n") -> Path:
    root = tmp / name
    (root / ".claude" / "agents").mkdir(parents=True)
    (root / ".claude" / "agents" / "python-developer.md").write_bytes(agent_text.encode())
    (root / "CLAUDE.md").write_text("# a project\n", encoding="utf-8")
    return root


class Stub:
    def __init__(self, tmp: Path, name: str):
        self.dir = tmp / f"stub-{name}"
        self.dir.mkdir()
        self.bin = self.dir / "claude"
        self.bin.write_text(STUB, encoding="utf-8")
        self.bin.chmod(0o755)
        self.plan, self.log = self.dir / "plan.json", self.dir / "calls.jsonl"

    def script(self, responses: list):
        self.plan.write_text(json.dumps({"responses": responses, "log": str(self.log)}), encoding="utf-8")
        os.environ["STUB_PLAN"] = str(self.plan)

    def calls(self) -> list:
        return [json.loads(x) for x in self.log.read_text().splitlines()] if self.log.exists() else []


def rec(label, task, cost, passed=True, why="check passed"):
    return {"label": label, "task": task, "cost_usd": cost, "passed": passed, "why": why}


def planted(base: list, cand: list, cand_pass=True, base_pass=True, task="agent-python-developer") -> list:
    return ([rec("baseline", task, c, base_pass, "check passed" if base_pass else "answer lacks /x/") for c in base]
            + [rec("candidate", task, c, cand_pass, "check passed" if cand_pass else "answer lacks /top_rebuilds/")
               for c in cand])


def audit_with(findings: list) -> dict:
    return {"findings": findings, "checks": [], "caveats": []}


def mpa_finding(edit=True):
    return {"lever": "model-per-agent", "title": "python-developer runs on claude-sonnet-5-5",
            "evidence": ["python-developer: 7 run(s), $26.17 on claude-sonnet-5-5"], "saving_usd": 19.63,
            "change": "set model: haiku in .claude/agents/python-developer.md", "confidence": "low",
            "target": "python-developer", "base_usd": 26.17,
            "edit": {"file": ".claude/agents/python-developer.md", "key": "model", "value": "haiku"} if edit else None}


def selftest() -> int:
    checks: dict = {}
    tasks = benchmark.load_tasks()
    os.environ["CLAUDE_CODE_SESSION_ID"] = "parent-session"   # the runner must not pass it on
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        root = project(tmp, "proj")
        before = digest(root)
        stub = Stub(tmp, "a")
        out = tmp / "results.jsonl"

        # the default root is the project, so a run sees its CLAUDE.md, agents and skills
        checks["the default root is the project: it holds CLAUDE.md and .claude/agents"] = all(
            (r / "CLAUDE.md").is_file() and (r / ".claude" / "agents").is_dir()
            for r in (benchmark.ROOT, optimize.ROOT))

        # the runner refuses a baseline that cannot measure a floor
        code, _ = quiet(benchmark.run, tasks, ["lever-ids"], "baseline", 1, 1.0, out, root, str(stub.bin))
        checks["a one-run baseline is refused (the floor needs two)"] = code == 2 and not out.exists()

        # a baseline of two tasks, twice each
        stub.script([{"cost": c, "result": GOOD[tid]} for c, tid in
                     ((0.10, "lever-ids"), (0.20, "hook-cap"), (0.11, "lever-ids"), (0.22, "hook-cap"))])
        code, text = quiet(benchmark.run, tasks, ["lever-ids", "hook-cap"], "baseline", 2, 5.0, out, root,
                           str(stub.bin))
        rs = benchmark.read_results(out)
        calls = stub.calls()
        checks["a baseline of 2 tasks x 2 runs records 4 runs, all passing"] = (
            code == 0 and len(rs) == 4 and all(r["passed"] for r in rs))
        floor = benchmark.stats(rs, "baseline")
        checks["the noise floor is each task's spread: $0.01 and $0.02"] = (
            floor["lever-ids"]["floor_usd"] == 0.01 and floor["hook-cap"]["floor_usd"] == 0.02)
        argv = [c["argv"] for c in calls]
        checks["every run passes -p, a streamed format and --no-session-persistence, never --bare"] = all(
            "-p" in a and a[a.index("--output-format") + 1] == "stream-json" and "--verbose" in a
            and "--no-session-persistence" in a and "--bare" not in a for a in argv)
        checks["every run denies Edit and Write and names its allowed tools"] = all(
            "Edit" in a[a.index("--disallowedTools") + 1] and "Write" in a[a.index("--disallowedTools") + 1]
            and a[a.index("--allowedTools") + 1] == "Read,Grep,Glob" for a in argv)
        checks["every run carries a --max-budget-usd"] = all("--max-budget-usd" in a for a in argv)
        checks["no run sees this session's CLAUDE_CODE_SESSION_ID"] = not any(c["session_env"] for c in calls)
        checks["every run works in a throwaway copy, not the project itself"] = all(
            Path(c["cwd"]).resolve() != root.resolve() and "bench-" in c["cwd"] for c in calls)

        # the cap: three runs at $0.10 against a $0.25 cap
        stub2, out2 = Stub(tmp, "cap"), tmp / "cap.jsonl"
        stub2.script([{"cost": 0.10, "result": GOOD["lever-ids"]}])
        code, text = quiet(benchmark.run, tasks, ["lever-ids"], "baseline", 5, 0.25, out2, root, str(stub2.bin))
        rs2 = benchmark.read_results(out2)
        budgets = [float(c["argv"][c["argv"].index("--max-budget-usd") + 1]) for c in stub2.calls()]
        spent = sum(r["cost_usd"] for r in rs2)
        checks["the cap stops the runner: exit 4, 3 of 5 runs, the last budget is what was left"] = (
            code == 4 and len(rs2) == 3 and abs(budgets[-1] - 0.05) < 1e-9 and "cap reached" in text)
        checks["spend stays within the cap plus one call's overshoot"] = spent <= 0.25 + 0.001 + 1e-9
        checks["a run the CLI stopped on its budget fails its check"] = (
            not rs2[-1]["passed"] and rs2[-1]["subtype"] == "error_max_budget_usd")

        # a run that edits a file fails, and the real project is untouched
        stub3, out3 = Stub(tmp, "edit"), tmp / "edit.jsonl"
        stub3.script([{"cost": 0.05, "result": GOOD["hook-cap"], "touch": "CLAUDE.md"}])
        quiet(benchmark.run, tasks, ["hook-cap"], "candidate", 1, 1.0, out3, root, str(stub3.bin))
        r3 = benchmark.read_results(out3)[0]
        checks["a run that edits a file fails its check, naming the file"] = (
            not r3["passed"] and r3["changed"] == ["CLAUDE.md"])
        checks["the project itself is byte-identical after every run"] = digest(root) == before

        # a wrong answer and a missing agent fail the guard
        stub4, out4 = Stub(tmp, "bad"), tmp / "bad.jsonl"
        stub4.script([{"cost": 0.05, "result": BAD["lever-ids"]},
                      {"cost": 0.05, "result": GOOD["agent-python-developer"], "agents": []},
                      {"cost": 0.05, "result": GOOD["agent-python-developer"], "agents": ["python-developer"]}])
        quiet(benchmark.run, tasks, ["lever-ids", "agent-python-developer"], "candidate", 1, 1.0, out4, root,
              str(stub4.bin))
        quiet(benchmark.run, tasks, ["agent-python-developer"], "candidate", 1, 1.0, out4, root, str(stub4.bin))
        r4 = benchmark.read_results(out4)
        checks["a wrong answer fails; the right answer without the agent fails; with it, passes"] = (
            [r["passed"] for r in r4] == [False, False, True] and "did not run" in r4[1]["why"])

        # a Stop hook's extra turn replaces `result`; the answer earlier in the main thread still counts
        stub8, out8 = Stub(tmp, "hook"), tmp / "hook.jsonl"
        hook_reply = "Nothing from this session needs logging."
        stub8.script([{"cost": 0.05, "result": hook_reply, "agents": ["python-developer"],
                       "stream": [[GOOD["agent-python-developer"], None], [hook_reply, None]]},
                      {"cost": 0.05, "result": hook_reply, "agents": ["python-developer"],
                       "stream": [[GOOD["agent-python-developer"], "toolu_sub"], [hook_reply, None]]}])
        quiet(benchmark.run, tasks, ["agent-python-developer"], "candidate", 2, 1.0, out8, root, str(stub8.bin))
        r8 = benchmark.read_results(out8)
        checks["an answer before a Stop hook's extra turn passes"] = r8[0]["passed"]
        checks["an answer only the subagent gave, never relayed, fails"] = not r8[1]["passed"]

        # the harness cost reconciles with pricing.json through usage.py
        toks = {"inputTokens": 1176, "outputTokens": 20, "cacheReadInputTokens": 25829,
                "cacheCreationInputTokens": 12025}
        stub5, out5 = Stub(tmp, "price"), tmp / "price.jsonl"
        stub5.script([{"cost": 0.00279089, "result": GOOD["hook-cap"], "tokens": toks, "model": HAIKU},
                      {"cost": 0.0100, "result": GOOD["hook-cap"], "tokens": toks, "model": HAIKU}])
        quiet(benchmark.run, tasks, ["hook-cap"], "candidate", 2, 1.0, out5, root, str(stub5.bin))
        r5 = benchmark.read_results(out5)
        checks["a cost that matches pricing.json reconciles (the first real probe run's numbers)"] = r5[0]["reconciled"]
        checks["a cost that doesn't match is flagged, not trusted"] = r5[1]["reconciled"] is False
        run_total = {HAIKU: {"inputTokens": 1211, "outputTokens": 318, "cacheReadInputTokens": 142065,
                             "cacheCreationInputTokens": 18996}}   # a real subagent run: 162K summed, no call over 100K
        lo, hi, _ = benchmark.priced_band(run_total, usage.load_prices())
        checks["a run whose summed prompt passes 100K still reconciles (the real $0.004849)"] = lo <= 0.004849 <= hi

        # decisions on planted results
        d = {k: benchmark.decide(v) for k, v in {
            "keep": planted([0.10, 0.11, 0.10], [0.05, 0.06, 0.05]),
            "noise": planted([0.10, 0.11, 0.10], [0.098, 0.104, 0.101]),
            "worse": planted([0.10, 0.11, 0.10], [0.05, 0.06, 0.05], cand_pass=False),
            "dearer": planted([0.10, 0.11, 0.10], [0.13, 0.14, 0.13]),
            "broken": planted([0.10, 0.11, 0.10], [0.05, 0.06, 0.05], base_pass=False),
            "thin": planted([0.10], [0.05, 0.06]),
        }.items()}
        checks["a saving past the floor with every check held is kept"] = d["keep"]["verdict"] == "keep"
        checks["a saving inside the noise floor is rejected"] = (
            d["noise"]["verdict"] == "reject" and "noise floor" in d["noise"]["reason"])
        checks["cheaper but worse is rejected by the quality guard"] = (
            d["worse"]["verdict"] == "reject" and "quality guard" in d["worse"]["reason"])
        checks["a dearer candidate is rejected"] = d["dearer"]["verdict"] == "reject"
        checks["a baseline that fails its own check makes the run invalid, not a verdict"] = (
            d["broken"]["verdict"] == "invalid" and "broken" in d["broken"]["reason"])
        checks["a one-run baseline makes the run invalid"] = d["thin"]["verdict"] == "invalid"

        # optimize.py: plan
        aj = tmp / "audit.json"
        aj.write_text(json.dumps(audit_with([mpa_finding()])), encoding="utf-8")
        code, text = quiet(optimize.main, ["plan", "--audit", str(aj), "--out", str(tmp / "plan.json")])
        pl = json.loads((tmp / "plan.json").read_text())
        checks["plan picks the model-per-agent finding and the task that exercises its agent"] = (
            code == 0 and pl["tasks"] == ["agent-python-developer"] and pl["edit"]["value"] == "haiku")
        aj.write_text(json.dumps(audit_with([mpa_finding(edit=False)])), encoding="utf-8")
        code, text = quiet(optimize.main, ["plan", "--audit", str(aj)])
        checks["a finding with no machine edit stops plan, with the reason"] = code == 3 and "by hand" in text
        aj.write_text(json.dumps(audit_with([])), encoding="utf-8")
        code, text = quiet(optimize.main, ["plan", "--audit", str(aj)])
        checks["no material finding stops plan"] = code == 3 and "No material finding." in text

        # optimize.py: apply, revert, keep
        variants = {"lf": "---\nname: python-developer\nmodel: sonnet\n---\nbody\n",
                    "crlf": "---\r\nname: python-developer\r\nmodel: sonnet\r\n---\r\nbody",
                    "no-model": "---\nname: python-developer\ntools: Read\n---\nbody\n"}
        identical = []
        for name, text0 in variants.items():
            r = project(tmp, f"v-{name}", text0)
            agent = r / ".claude" / "agents" / "python-developer.md"
            st = tmp / f"state-{name}.json"
            code_a, _ = quiet(optimize.apply, pl, st, r)
            applied = agent.read_text(encoding="utf-8")
            code_r, _ = quiet(optimize.revert, st)
            identical.append(code_a == 0 and "model: haiku" in applied and code_r == 0
                             and agent.read_bytes() == text0.encode() and not st.exists())
        checks["apply then revert leaves the file byte-identical (LF, CRLF, no model key)"] = all(identical)
        r = project(tmp, "keep")
        st = tmp / "state-keep.json"
        quiet(optimize.apply, pl, st, r)
        code_twice, _ = quiet(optimize.apply, pl, st, r)
        code_k, _ = quiet(optimize.keep, st)
        checks["a second apply while one is in flight is refused; keep then clears it"] = (
            code_twice == optimize.REFUSED and code_k == 0 and not st.exists()
            and "model: haiku" in (r / ".claude" / "agents" / "python-developer.md").read_text())
        r = project(tmp, "drift")
        st = tmp / "state-drift.json"
        quiet(optimize.apply, pl, st, r)
        agent = r / ".claude" / "agents" / "python-developer.md"
        agent.write_text(agent.read_text() + "someone else's edit\n")
        code_r, _ = quiet(optimize.revert, st)
        checks["revert refuses to overwrite a file changed after apply"] = (
            code_r == optimize.REFUSED and "someone else's edit" in agent.read_text() and st.exists())

        # optimize.py: record, and the audit reads it back
        cat = tmp / "levers.md"
        cat.write_text(re.sub(r"^- \*\*Measured:\*\*.*\n(?:  - `.*\n)*", "- **Measured:** none yet.\n",
                              audit.CATALOG.read_text(encoding="utf-8"), flags=re.M), encoding="utf-8")
        led = tmp / "ledger.jsonl"
        dk, dr = tmp / "keep.json", tmp / "reject.json"
        dk.write_text(json.dumps(d["keep"]))
        dr.write_text(json.dumps(d["noise"]))
        quiet(optimize.record, pl, d["keep"], "2026-10-21", cat, led)
        first = audit.measured_outcomes(cat).get(("model-per-agent", "python-developer"))
        quiet(optimize.record, pl, d["noise"], "2026-10-22", cat, led)
        latest = audit.measured_outcomes(cat).get(("model-per-agent", "python-developer"))
        text = cat.read_text(encoding="utf-8")
        rows = [json.loads(x) for x in led.read_text().splitlines()]
        checks["record writes a Measured line the audit parses as kept, with its share"] = (
            bool(first) and first["verdict"] == "kept" and float(first["share"]) > 0)
        checks["a second run keeps the first line: both recorded, the newest wins"] = (
            "2 optimize-spend runs, newest last." in text and text.count("`python-developer` model") == 2
            and latest["verdict"] == "rejected" and "noise floor" in latest["reason"])
        checks["the catalog still parses with every lever's seven fields after recording"] = (
            len(re.findall(r"^- \*\*Measured:\*\*", text, re.M)) == len(audit.RULES))
        checks["each outcome adds a ledger row: kept confirms, rejected refutes"] = (
            [r["verdict"] for r in rows] == ["confirmed", "refuted"]
            and all(r["id"]["rule"] == "measured-outcome" and r["rationale"] for r in rows))
        code, _ = quiet(optimize.record, pl, d["broken"], "2026-10-23", cat, led)
        checks["an invalid decision records nothing"] = (
            code == optimize.REFUSED and len(led.read_text().splitlines()) == 2)

        # the workflow names every stop path
        if WORKFLOW.is_file():
            body = WORKFLOW.read_text(encoding="utf-8")
            checks["the workflow names each stop: no finding, declined, noise floor, quality guard"] = all(
                k in body for k in ("No material finding", "declined", "noise floor", "quality guard"))
            checks["the workflow reverts on every stop after apply"] = "optimize.py revert" in body
            checks["the workflow gates apply behind approval"] = re.search(r"approv", body, re.I) is not None
        checks["the factory links the workflow to its canonical copy"] = (
            FACTORY_LINK.is_symlink() and FACTORY_LINK.resolve() == WORKFLOW.resolve())

        # breaks: each disables one guard, and the check that relies on it must go red
        saved = benchmark.noise_floor
        benchmark.noise_floor = lambda costs: 0.0
        checks["[break] with no noise floor, noise is kept as a saving"] = benchmark.decide(
            planted([0.10, 0.11, 0.10], [0.098, 0.104, 0.101]))["verdict"] == "keep"
        benchmark.noise_floor = saved
        saved = benchmark.judge
        benchmark.judge = lambda *a, **k: (True, "no guard")
        stub6, out6 = Stub(tmp, "noguard"), tmp / "noguard.jsonl"
        stub6.script([{"cost": 0.05, "result": BAD["lever-ids"]}])
        quiet(benchmark.run, tasks, ["lever-ids"], "candidate", 1, 1.0, out6, root, str(stub6.bin))
        benchmark.judge = saved
        checks["[break] with no quality guard, a wrong answer passes"] = benchmark.read_results(out6)[0]["passed"]
        saved = benchmark.SCRUB_ENV
        benchmark.SCRUB_ENV = ()
        stub7, out7 = Stub(tmp, "noscrub"), tmp / "noscrub.jsonl"
        stub7.script([{"cost": 0.05, "result": GOOD["hook-cap"]}])
        quiet(benchmark.run, tasks, ["hook-cap"], "candidate", 1, 1.0, out7, root, str(stub7.bin))
        benchmark.SCRUB_ENV = saved
        checks["[break] without the scrub the child sees this session's id"] = stub7.calls()[0]["session_env"]
        saved = optimize.sha
        optimize.sha = lambda b: "same"
        r = project(tmp, "blind")
        st = tmp / "state-blind.json"
        quiet(optimize.apply, pl, st, r)
        agent = r / ".claude" / "agents" / "python-developer.md"
        agent.write_text("clobbered\n")
        code_r, _ = quiet(optimize.revert, st)
        optimize.sha = saved
        checks["[break] a revert that can't tell bytes apart claims success on a clobbered file"] = (
            code_r == 0 and agent.read_text() == "clobbered\n")

    width = max(map(len, checks))
    for name, ok in checks.items():
        print(f"{'PASS' if ok else 'FAIL'}  {name.ljust(width)}")
    passed = sum(bool(v) for v in checks.values())
    print(f"\n{passed}/{len(checks)} passed")
    return 0 if passed == len(checks) else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
