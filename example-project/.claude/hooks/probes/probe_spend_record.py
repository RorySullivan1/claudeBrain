#!/usr/bin/env python3
"""Probe the spend_record hook (RorySullivan1/claudebrain#61) on planted projects.

    python3 example-project/.claude/hooks/probes/probe_spend_record.py

Each case runs the real hook as a subprocess, the way the harness does: a JSON payload on
stdin and CLAUDE_PROJECT_DIR set to a throwaway project. The project carries the real
token-optimizer skill (symlinked) and the fixture logs from `probe_usage.py`, so the hook
measures with the same code and the same planted shapes the usage probe already proved.

Controls: silence without `.claude/spend/` and without the skill must hold, or a "silent"
result elsewhere proves nothing; and an unchanged second run must not add lines.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HOOKS = Path(__file__).resolve().parent.parent
SKILL = HOOKS.parent / "skills" / "token-optimizer"
HOOK = HOOKS / "spend_record.py"
sys.path.insert(0, str(SKILL / "probes"))
import probe_usage  # noqa: E402  (fixture builder)


def project(tmp: Path, spend=True, skill=True) -> Path:
    root = tmp / "proj"
    (root / ".claude" / "skills").mkdir(parents=True)
    if skill:
        (root / ".claude" / "skills" / "token-optimizer").symlink_to(SKILL)
    if spend:
        (root / ".claude" / "spend").mkdir()
    logs = tmp / "logs"
    logs.mkdir()
    probe_usage.build(logs)
    return root


def hook(root: Path, payload) -> subprocess.CompletedProcess:
    body = payload if isinstance(payload, str) else json.dumps(payload)
    return subprocess.run([sys.executable, str(HOOK)], input=body, capture_output=True, text=True,
                          env=dict(os.environ, CLAUDE_PROJECT_DIR=str(root)), timeout=60)


def stop(tmp: Path, event="Stop", **extra) -> dict:
    return dict({"session_id": "NEW", "transcript_path": str(tmp / "logs" / "NEW.jsonl"),
                 "hook_event_name": event, "cwd": str(tmp)}, **extra)


def log_lines(root: Path) -> list:
    p = root / ".claude" / "spend" / "log.jsonl"
    return p.read_text().splitlines() if p.exists() else []


def keys(lines: list) -> list:
    out = []
    for ln in lines:
        try:
            d = json.loads(ln)
            out.append((d.get("kind"), d.get("id")))
        except ValueError:
            out.append(("unparsed", ln[:20]))
    return out


def quiet(p: subprocess.CompletedProcess) -> bool:
    return p.returncode == 0 and p.stdout == "" and p.stderr == ""


def main() -> int:
    checks = {}
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        root = project(tmp, spend=False)
        p = hook(root, stop(tmp))
        checks["[control] silent and writes nothing when .claude/spend/ is absent"] = (
            quiet(p) and not (root / ".claude" / "spend").exists())

    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        root = project(tmp, skill=False)
        p = hook(root, stop(tmp))
        checks["[control] silent and writes nothing when token-optimizer is absent"] = quiet(p) and log_lines(root) == []

    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        root = project(tmp)
        p = hook(root, stop(tmp))
        first = log_lines(root)
        checks["Stop writes one session line and one line per subagent run"] = (
            quiet(p) and keys(first) == [("session", "NEW"), ("subagent", "sub1")])
        rec = json.loads(first[0]) if first else {}
        checks["the session line counts only this session's calls (copied history excluded)"] = (
            rec.get("calls") == 5 and rec.get("prompts") == 2 and rec.get("commands") == {"/cmd": 1})
        checks["the line carries tokens, a labelled estimate, and no prompt text"] = (
            rec.get("usd_label") == "estimate (API list price)" and isinstance(rec.get("est_usd"), float)
            and "plain prompt" not in first[0] and "first question" not in first[0])
        sub = json.loads(first[1]) if len(first) > 1 else {}
        checks["the subagent line takes the parent's last-call output, never placeholders"] = (
            sub.get("tokens", {}).get("output") == 142 and sub.get("agent_type") == "Explore")
        hook(root, stop(tmp))
        checks["[control] a second Stop updates in place: still exactly one line per key"] = (
            keys(log_lines(root)) == keys(first))
        hook(root, stop(tmp, "SubagentStop", agent_id="sub1", agent_type="Explore",
                         agent_transcript_path=str(tmp / "logs" / "NEW" / "subagents" / "agent-sub1.jsonl")))
        mid = log_lines(root)
        hook(root, stop(tmp, "SessionEnd", reason="other"))
        after = log_lines(root)
        events = lambda ls: [json.loads(x).get("event") for x in ls]
        checks["SubagentStop rewrites only its own run; SessionEnd upserts both"] = (
            keys(mid) == keys(after) == keys(first)
            and events(mid) == ["Stop", "SubagentStop"] and events(after) == ["SessionEnd", "SessionEnd"])

    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        root = project(tmp)
        log = root / ".claude" / "spend" / "log.jsonl"
        log.write_text('{"kind":"session","id":"OTHER","calls":1}\nnot json at all\n[1,2]\n{"kind":"sess')
        p = hook(root, stop(tmp))
        text = log.read_text()
        lines = text.splitlines()
        checks["a malformed log causes no crash and keeps foreign lines verbatim"] = (
            quiet(p) and lines[:4] == ['{"kind":"session","id":"OTHER","calls":1}', "not json at all", "[1,2]", '{"kind":"sess'])
        checks["no partial line: the file ends in a newline and every new line parses"] = (
            text.endswith("\n") and keys(lines[4:]) == [("session", "NEW"), ("subagent", "sub1")])

    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        root = project(tmp)
        bad = ["{not json", "[]", json.dumps({"session_id": "NEW"}),
               json.dumps(stop(tmp, transcript_path=str(tmp))),          # a directory, not a file
               json.dumps(stop(tmp, transcript_path=str(tmp / "nope.jsonl")))]
        results = [hook(root, b) for b in bad]
        checks["never blocks: failing inputs exit 0 with no output and no log"] = (
            all(quiet(r) for r in results) and log_lines(root) == [])
        (root / ".claude" / "skills" / "token-optimizer").unlink()
        broken = root / ".claude" / "skills" / "token-optimizer" / "scripts"
        broken.mkdir(parents=True)
        (broken / "usage.py").write_text("raise RuntimeError('a broken measurer')\n")
        checks["never blocks: a measurer that raises still exits 0 silently"] = quiet(hook(root, stop(tmp)))

    with tempfile.TemporaryDirectory() as t:
        sys.path.insert(0, str(HOOKS))
        import spend_record
        log = Path(t) / "log.jsonl"
        log.write_text('{"kind":"session","id":"A","calls":1}\n')
        real_replace = os.replace
        os.replace = lambda *a: (_ for _ in ()).throw(OSError("disk full"))
        try:
            spend_record.upsert(log, [{"kind": "session", "id": "A", "calls": 2}])
            crashed = False
        except OSError:
            crashed = True
        finally:
            os.replace = real_replace
        checks["a crash mid-write leaves the old log intact and no temp file"] = (
            crashed and log.read_text() == '{"kind":"session","id":"A","calls":1}\n'
            and [p.name for p in Path(t).iterdir()] == ["log.jsonl"])

    for name, ok in checks.items():
        print(f"{'PASS' if ok else 'FAIL'}  {name}")
    failed = sum(not ok for ok in checks.values())
    print(f"\n{len(checks) - failed}/{len(checks)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
