#!/usr/bin/env python3
"""Stop / SubagentStop / SessionEnd hook: keep one spend line per session and per subagent run
in `.claude/spend/log.jsonl`, so spend history survives an ephemeral container (#61).

Opt-in BY PRESENCE: silent unless `.claude/spend/` exists, and silent if the token-optimizer
skill (whose `usage.py` does the measuring) is not installed. It never blocks and never
speaks: it prints nothing and always exits 0, whatever the payload or the state of the log.

Each run upserts by `(kind, id)`: the session's line, plus one line per subagent run of that
session (a `SubagentStop` writes only its own run). A line it can't parse is kept verbatim.
The file is rewritten to a temp file and swapped in with `os.replace`, so a crash mid-write
leaves the old log intact rather than a partial line. The normal commit flow carries the file.

Why `Stop` and not just `SessionEnd`: a cloud container is reclaimed after inactivity, and
nothing shows that `SessionEnd` fires then. `Stop` fires every turn, so the per-session line
is always at most one turn stale. `SessionEnd` is wired too, so where it does fire it costs
one idempotent rewrite. The harness's own total (`cost-state`) is written when the session
goes idle, after `Stop`, so `harness_usd_at_last_idle` lags by one turn.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path

USAGE = Path(".claude") / "skills" / "token-optimizer" / "scripts" / "usage.py"


def project_root() -> Path:
    return Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())


def load_usage(root: Path):
    path = root / USAGE
    if not path.is_file():
        return None
    spec = importlib.util.spec_from_file_location("spend_usage", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod  # dataclasses resolve string annotations through sys.modules
    spec.loader.exec_module(mod)
    return mod


def upsert(log: Path, records: list) -> None:
    """Replace the lines whose (kind, id) match a record, append the rest, swap in atomically."""
    fresh = {(r["kind"], r["id"]): r for r in records}
    lines = []
    if log.exists():
        for raw in log.read_text(encoding="utf-8", errors="replace").splitlines():
            if not raw.strip():
                continue
            try:
                old = json.loads(raw)
                key = (old.get("kind"), old.get("id")) if isinstance(old, dict) else None
            except ValueError:
                key = None
            if key in fresh:
                lines.append(json.dumps(fresh.pop(key), separators=(",", ":")))
            else:
                lines.append(raw)
    lines += [json.dumps(r, separators=(",", ":")) for r in fresh.values()]
    fd, tmp = tempfile.mkstemp(dir=log.parent, prefix=".log.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
        os.replace(tmp, log)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def locked(log: Path):
    """An exclusive lock where the platform has one: parallel subagents stop concurrently.
    The lock file lives in the temp dir, keyed by the log's path, so the repo gains no file."""
    try:
        import fcntl
    except ImportError:
        return None
    key = hashlib.sha1(str(log.resolve()).encode()).hexdigest()[:16]
    fh = open(Path(tempfile.gettempdir()) / f"spend-record-{key}.lock", "a")
    fcntl.flock(fh, fcntl.LOCK_EX)
    return fh


def record(data: dict, root: Path) -> None:
    spend = root / ".claude" / "spend"
    if not spend.is_dir():
        return
    usage = load_usage(root)
    if usage is None:
        return
    session = data.get("session_id")
    transcript = Path(data.get("transcript_path") or "")
    if not session or not transcript.is_file():
        return
    event = data.get("hook_event_name")
    agent_log = data.get("agent_transcript_path")
    corpus = usage.load([transcript], extra_agents=[agent_log] if agent_log else [])
    prices = usage.load_prices() if usage.PRICING.exists() else None
    records = usage.spend_records(corpus, session, prices, event)
    if event == "SubagentStop":
        records = [r for r in records if r["kind"] == "subagent" and r["id"] == data.get("agent_id")]
    if not records:
        return
    lock = locked(spend / "log.jsonl")
    try:
        upsert(spend / "log.jsonl", records)
    finally:
        if lock:
            lock.close()


def main() -> int:
    try:
        data = json.loads(sys.stdin.read() or "{}")
        if isinstance(data, dict):
            record(data, project_root())
    except Exception:  # fail safe: a spend log must never break the session it measures
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
