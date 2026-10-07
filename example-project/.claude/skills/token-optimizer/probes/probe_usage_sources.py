#!/usr/bin/env python3
"""Probe what each Claude Code usage source counts, so the spend parser is built on
measured behaviour rather than on assumptions (RorySullivan1/claudebrain#58).

    python3 probe_usage_sources.py [LOGS_DIR]   # default: this project's ~/.claude/projects/<slug>
    python3 probe_usage_sources.py --selftest   # prove each detector fires on a synthetic log set

Reads only. It reports five things about a real log directory:

1. Duplicate lines: one API call spread over several log lines (deduplicate by message.id).
2. Copied history: the same call in more than one session file, kept under its original
   sessionId. Summing files double-counts it.
3. Harness windows: between consecutive `cost-state` records with the same startTime, the
   deduplicated log usage against the change in the harness's per-model totals. Output
   should match (final counts); a positive cache/input gap means calls the log never saw.
4. Resumes: whether a new startTime begins from zero (spend not carried) or the total keeps
   growing across SessionStart:resume.
5. Subagents: each subagents/agent-*.jsonl call's output_tokens, against the real final-call
   usage the parent records in its Agent tool result. A large shortfall means placeholders.

The self-test builds logs with every one of those shapes planted, including controls that
must NOT be flagged, so a detector that has gone blind fails loudly.
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import sys
import tempfile
from pathlib import Path

TOK = ("input_tokens", "output_tokens", "cache_read_input_tokens", "cache_creation_input_tokens")
HARNESS = ("inputTokens", "outputTokens", "cacheReadInputTokens", "cacheCreationInputTokens")


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    for n, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if line.strip():
            try:
                rows.append(json.loads(line))
            except ValueError:
                print(f"  ! {path.name}:{n} is not JSON (reported, not skipped silently)")
    return rows


def calls(rows: list[dict]) -> list[tuple[str, dict]]:
    """(message.id, row) for every assistant line that carries usage, in file order."""
    out = []
    for d in rows:
        m = d.get("message")
        if d.get("type") == "assistant" and isinstance(m, dict) and m.get("usage") and m.get("id"):
            out.append((m["id"], d))
    return out


def check_duplicates(files: dict[str, list[dict]]) -> dict:
    lines = ids = 0
    conflicting = []
    for name, rows in files.items():
        seen: dict[str, dict] = {}
        for mid, d in calls(rows):
            lines += 1
            u = {k: d["message"]["usage"].get(k) for k in TOK}
            if mid in seen and seen[mid] != u:
                conflicting.append((name, mid))
            seen.setdefault(mid, u)
        ids += len(seen)
    return {"usage_lines": lines, "unique_calls": ids, "conflicting_duplicates": conflicting}


def check_copies(files: dict[str, list[dict]]) -> dict:
    where = collections.defaultdict(set)
    sid_of = {}
    for name, rows in files.items():
        for mid, d in calls(rows):
            where[mid].add(name)
            sid_of[mid] = d.get("sessionId")
    shared = {m for m, fs in where.items() if len(fs) > 1}
    return {"calls_in_multiple_files": len(shared),
            "their_sessionIds": sorted({str(sid_of[m])[:8] for m in shared})}


def check_harness(rows: list[dict]) -> dict:
    """Per window between cost-state records: log usage vs harness delta (main model)."""
    windows, resets, carries = [], 0, 0
    seen, win = set(), collections.Counter()
    prev = None  # (start, per-model totals)
    resumes_since = 0
    for d in rows:
        if d.get("type") == "attachment" and "SessionStart:resume" in json.dumps(d)[:4000]:
            resumes_since += 1
        m = d.get("message")
        if d.get("type") == "assistant" and isinstance(m, dict) and m.get("usage") and m.get("id") not in seen:
            seen.add(m["id"])
            win[m.get("model")] += 0  # keep model keys
            for a, b in zip(HARNESS, TOK):
                win[(m.get("model"), a)] += m["usage"].get(b) or 0
        if d.get("type") != "cost-state":
            continue
        cur = {k: v for k, v in (d.get("modelUsage") or {}).items()}
        start = d.get("startTime")
        if prev is not None:
            if start != prev[0]:
                resets += 1
            elif resumes_since:
                carries += 1
            if start == prev[0]:
                for model, now in cur.items():
                    before = prev[1].get(model, {})
                    logm = [k for k in win if isinstance(k, str) and k.startswith(model.split("-202")[0][:16])]
                    log = {a: sum(win[(lm, a)] for lm in logm) for a in HARNESS}
                    delta = {a: (now.get(a) or 0) - (before.get(a) or 0) for a in HARNESS}
                    if any(delta.values()) or any(log.values()):
                        windows.append({"model": model, "log": log, "harness_delta": delta})
        prev = (start, cur)
        win, resumes_since = collections.Counter(), 0
    return {"windows": windows, "new_start_without_carry": resets, "resumes_carried": carries}


def check_subagents(session_dir: Path, parent_rows: list[dict]) -> list[dict]:
    real = {}
    for d in parent_rows:
        r = d.get("toolUseResult")
        if isinstance(r, dict) and r.get("agentId") and isinstance(r.get("usage"), dict):
            real[r["agentId"]] = r["usage"].get("output_tokens")
    out = []
    for log in sorted((session_dir / "subagents").glob("agent-*.jsonl")) if session_dir.is_dir() else []:
        aid = log.stem.removeprefix("agent-")
        rows = read_jsonl(log)
        last_out, seen = None, {}
        for mid, d in calls(rows):
            seen[mid] = d["message"]["usage"].get("output_tokens") or 0
            last_out = seen[mid]
        meta = log.with_suffix("").with_suffix(".meta.json")
        model = json.loads(meta.read_text()).get("model") if meta.exists() else None
        in_parent = any(d.get("isSidechain") for d in parent_rows)
        out.append({"agent": aid, "model": model, "calls": len(seen), "log_last_output": last_out,
                    "parent_last_output": real.get(aid), "sidechain_lines_in_parent": in_parent})
    return out


def probe(logs: Path) -> dict:
    files = {p.name: read_jsonl(p) for p in sorted(logs.glob("*.jsonl"))}
    report = {"files": {k: len(v) for k, v in files.items()},
              "duplicates": check_duplicates(files),
              "copies": check_copies(files),
              "sessions": {}}
    for name, rows in files.items():
        report["sessions"][name] = {"harness": check_harness(rows),
                                    "subagents": check_subagents(logs / Path(name).stem, rows)}
    return report


def verdicts(r: dict) -> list[str]:
    v = []
    d = r["duplicates"]
    v.append(f"[1] {d['usage_lines']} usage lines = {d['unique_calls']} calls; "
             f"{'duplicates disagree!' if d['conflicting_duplicates'] else 'duplicates carry identical usage'}")
    c = r["copies"]
    v.append(f"[2] {c['calls_in_multiple_files']} calls appear in more than one file "
             f"(sessionIds {c['their_sessionIds']}): dedupe across files, attribute by sessionId")
    for name, s in r["sessions"].items():
        h = s["harness"]
        for w in h["windows"]:
            gap = {a.replace("InputTokens", "").replace("Tokens", ""): w["harness_delta"][a] - w["log"][a] for a in HARNESS}
            v.append(f"[3] {name[:8]} {w['model'][:22]}: harness - log = {gap}")
        v.append(f"[4] {name[:8]}: {h['resumes_carried']} cost records carried totals across a resume; "
                 f"{h['new_start_without_carry']} began a new startTime from zero")
        for a in s["subagents"]:
            v.append(f"[5] subagent {a['agent'][:10]} ({a['model']}): log says last call output "
                     f"{a['log_last_output']}, parent's tool result says {a['parent_last_output']}; "
                     f"sidechain lines in parent log: {a['sidechain_lines_in_parent']}")
    return v


# --------------------------------------------------------------------------- self-test
def _asst(mid, sid, model, u, side=False, agent=None):
    d = {"type": "assistant", "sessionId": sid, "isSidechain": side,
         "message": {"id": mid, "model": model, "usage": dict(zip(TOK, u)), "content": []}}
    if agent:
        d["agentId"] = agent
    return d


def _cost(start, model, u):
    return {"type": "cost-state", "startTime": start, "totalCostUSD": 1.0,
            "modelUsage": {model: dict(zip(HARNESS, u))}}


def selftest() -> int:
    tmp = Path(tempfile.mkdtemp())
    M, H = "claude-main-model", "claude-haiku-x"
    resume = {"type": "attachment", "attachment": {"content": "SessionStart:resume hook success"}}
    old = [_asst("m1", "OLD", M, (1, 100, 1000, 10)), _asst("m1", "OLD", M, (1, 100, 1000, 10))]
    new = old + [  # copied history, kept under the OLD sessionId
        _cost(1, M, (0, 0, 0, 0)),
        _asst("m2", "NEW", M, (2, 50, 2000, 5)), _asst("m2", "NEW", M, (2, 50, 2000, 5)),
        _cost(1, M, (2 + 500, 50 + 10, 2000 + 4000, 5)),      # one hidden helper call
        resume,
        _asst("m3", "NEW", M, (3, 70, 3000, 7)),
        _cost(1, M, (505 + 3, 60 + 70, 6000 + 3000, 12)),     # control: exact match, carried
        _cost(2, M, (1, 1, 1, 1)),                            # new startTime: began from zero
        {"type": "user", "toolUseResult": {"agentId": "abc", "usage": {"output_tokens": 142}}},
    ]
    (tmp / "OLD.jsonl").write_text("\n".join(json.dumps(x) for x in old))
    (tmp / "NEW.jsonl").write_text("\n".join(json.dumps(x) for x in new))
    sub = tmp / "NEW" / "subagents"
    sub.mkdir(parents=True)
    (sub / "agent-abc.jsonl").write_text(json.dumps(_asst("s1", "NEW", H, (1, 3, 0, 9), True, "abc")))
    (sub / "agent-abc.meta.json").write_text(json.dumps({"model": "haiku"}))

    r = probe(tmp)
    s = r["sessions"]["NEW.jsonl"]
    w = s["harness"]["windows"]
    checks = {
        "duplicates collapse to calls": r["duplicates"]["usage_lines"] == 7 and r["duplicates"]["unique_calls"] == 4,
        "copied history found under its original sessionId": r["copies"]["calls_in_multiple_files"] == 1
            and r["copies"]["their_sessionIds"] == ["OLD"],
        "hidden call shows as a harness-minus-log gap": len(w) >= 1
            and w[0]["harness_delta"]["cacheReadInputTokens"] - w[0]["log"]["cacheReadInputTokens"] == 4000,
        "output matches when nothing is hidden [control]": len(w) >= 2
            and w[1]["harness_delta"]["outputTokens"] == w[1]["log"]["outputTokens"],
        "carry across a resume is detected": s["harness"]["resumes_carried"] == 1,
        "a new startTime from zero is detected": s["harness"]["new_start_without_carry"] == 1,
        "subagent placeholder vs parent's real output": s["subagents"]
            and s["subagents"][0]["log_last_output"] == 3 and s["subagents"][0]["parent_last_output"] == 142,
        "no subagent flagged where none exists [control]": r["sessions"]["OLD.jsonl"]["subagents"] == [],
    }
    for name, ok in checks.items():
        print(f"{'PASS' if ok else 'FAIL'}  {name}")
    failed = sum(not ok for ok in checks.values())
    print(f"\n{len(checks) - failed}/{len(checks)} passed")
    return 1 if failed else 0


def default_logs() -> Path:
    slug = "-" + str(Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()).resolve()).strip("/").replace("/", "-")
    return Path.home() / ".claude" / "projects" / slug


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("logs", nargs="?", type=Path)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    logs = a.logs or default_logs()
    if not logs.is_dir():
        print(f"no log directory at {logs}")
        return 2
    r = probe(logs)
    print(json.dumps(r, indent=1) if a.json else "\n".join(verdicts(r)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
