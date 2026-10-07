#!/usr/bin/env python3
"""Run epic-autoclose.yml's real `run:` script against a fake GitHub REST API.

The script is pulled out of the workflow file, not copied, so the probe can't drift from
what ships. It runs under real bash, curl, and jq against a local HTTP server that serves
the sub-issue endpoints from an in-memory issue table. Each case sets the table, fires
one event, and asserts the exit code and the exact writes. The negative controls (no
write expected) guard against a script that "passes" by closing everything.

    python3 probe_epic_autoclose.py        # exit 0 = every case passed
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import yaml

WORKFLOW = Path(__file__).resolve().parent.parent / "assets" / "epic-autoclose.yml"
REPO = "Owner/Repo"


class Fake:
    issues: dict[int, dict] = {}
    writes: list[tuple] = []
    fail: set[str] = set()
    base = ""
    comments: dict[int, list[dict]] = {}
    next_id = 100


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code: int, body) -> None:
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _issue_json(self, n: int) -> dict:
        i = Fake.issues[n]
        return {"number": n, "state": i["state"], "state_reason": i.get("reason"),
                "repository_url": f"{Fake.base}/repos/{i.get('repo', REPO)}"}

    def _route(self, method: str):
        path, _, query = self.path.partition("?")
        if path in Fake.fail:
            return self._send(500, {"message": "injected failure"})
        d = re.fullmatch(r"/repos/Owner/Repo/issues/comments/(\d+)", path)
        if d and method == "DELETE":
            Fake.writes.append(("DELETE", int(d.group(1))))
            return self._send(204, {})
        m = re.fullmatch(r"/repos/Owner/Repo/issues/(\d+)(/parent|/sub_issues|/comments)?", path)
        if not m or int(m.group(1)) not in Fake.issues:
            return self._send(404, {"message": "Not Found"})
        n, tail = int(m.group(1)), m.group(2)
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        if method == "GET" and tail == "/parent":
            p = Fake.issues[n].get("parent")
            return self._send(404, {"message": "Not Found"}) if p is None else self._send(200, self._issue_json(p))
        if method == "GET" and tail == "/sub_issues":
            kids = [k for k, v in Fake.issues.items() if v.get("parent") == n]
            return self._send(200, [self._issue_json(k) for k in kids])
        if method == "PATCH" and tail is None:
            Fake.issues[n]["state"] = body["state"]
            Fake.issues[n]["reason"] = body.get("state_reason")
            Fake.writes.append(("PATCH", n, body["state"], body.get("state_reason")))
            return self._send(200, self._issue_json(n))
        if method == "POST" and tail == "/comments":
            Fake.writes.append(("COMMENT", n))
            Fake.next_id += 1
            c = {"id": Fake.next_id, "body": body["body"], "updated_at": "2099-01-01T00:00:00Z"}
            Fake.comments.setdefault(n, []).append(c)
            return self._send(201, c)
        if method == "GET" and tail == "/comments":
            since = dict(q.split("=", 1) for q in query.split("&") if "=" in q).get("since", "")
            return self._send(200, [c for c in Fake.comments.get(n, []) if c["updated_at"] >= since])
        return self._send(405, {"message": "unexpected call"})

    def do_GET(self):
        self._route("GET")

    def do_PATCH(self):
        self._route("PATCH")

    def do_POST(self):
        self._route("POST")

    def do_DELETE(self):
        self._route("DELETE")


def extract_script() -> str:
    wf = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    return wf["jobs"]["sync-parent"]["steps"][0]["run"]


def fire(script: str, issue: int, action: str, api: str = "") -> subprocess.CompletedProcess:
    env = dict(os.environ, GH_TOKEN="fake", API=api or Fake.base, REPO=REPO, ISSUE=str(issue), ACTION=action)
    for var in ("HTTPS_PROXY", "HTTP_PROXY", "https_proxy", "http_proxy"):
        env.pop(var, None)  # the fake API is local; a sandbox proxy would intercept it
    return subprocess.run(["bash", "-c", script], env=env, capture_output=True, text=True, timeout=30)


def I(state="open", parent=None, reason=None, repo=REPO) -> dict:
    return {"state": state, "parent": parent, "reason": reason, "repo": repo}


# (name, issue table, event issue, action, expected exit, expected writes)
CASES = [
    ("sibling still open -> parent untouched [control]",
     {1: I(), 2: I("closed", 1, "completed"), 3: I(parent=1)}, 2, "closed", 0, []),
    ("last child completed -> parent closed completed",
     {1: I(), 2: I("closed", 1, "completed"), 3: I("closed", 1, "completed")}, 3, "closed", 0,
     [("PATCH", 1, "closed", "completed"), ("COMMENT", 1)]),
    ("mixed completed + not_planned -> completed",
     {1: I(), 2: I("closed", 1, "not_planned"), 3: I("closed", 1, "completed")}, 2, "closed", 0,
     [("PATCH", 1, "closed", "completed"), ("COMMENT", 1)]),
    ("all children not_planned -> parent not_planned",
     {1: I(), 2: I("closed", 1, "not_planned"), 3: I("closed", 1, "not_planned")}, 3, "closed", 0,
     [("PATCH", 1, "closed", "not_planned"), ("COMMENT", 1)]),
    ("nested: grandchild closes -> parent AND grandparent close in one run",
     {1: I(), 2: I(parent=1), 3: I("closed", 2, "completed")}, 3, "closed", 0,
     [("PATCH", 2, "closed", "completed"), ("COMMENT", 2), ("PATCH", 1, "closed", "completed"), ("COMMENT", 1)]),
    ("nested: cascade stops where an uncle is still open",
     {1: I(), 2: I(parent=1), 4: I(parent=1), 3: I("closed", 2, "completed")}, 3, "closed", 0,
     [("PATCH", 2, "closed", "completed"), ("COMMENT", 2)]),
    ("reopen child -> closed parent and grandparent reopen",
     {1: I("closed", None, "completed"), 2: I("closed", 1, "completed"), 3: I("open", 2)}, 3, "reopened", 0,
     [("PATCH", 2, "open", None), ("COMMENT", 2), ("PATCH", 1, "open", None), ("COMMENT", 1)]),
    ("reopen child under an open parent -> no write [control]",
     {1: I(), 2: I(parent=1)}, 2, "reopened", 0, []),
    ("no parent (404) -> no write, success [control]",
     {5: I("closed", None, "completed")}, 5, "closed", 0, []),
    ("parent already closed by hand -> no write [control]",
     {1: I("closed", None, "not_planned"), 2: I("closed", 1, "completed")}, 2, "closed", 0, []),
    ("parent in another repo -> left alone",
     {1: I(repo="Owner/Other"), 2: I("closed", 1, "completed")}, 2, "closed", 0, []),
    ("repo casing differs -> still treated as same repo",
     {1: I(repo="owner/repo"), 2: I("closed", 1, "completed")}, 2, "closed", 0,
     [("PATCH", 1, "closed", "completed"), ("COMMENT", 1)]),
]

FAULTS = [
    # (name, table, event issue, failing path) -> must exit non-zero with no close.
    ("parent lookup 500 -> fails loudly, not 'no parent'",
     {1: I(), 2: I("closed", 1, "completed")}, 2, "/repos/Owner/Repo/issues/2/parent"),
    ("sub-issue list 500 -> fails loudly, no close",
     {1: I(), 2: I("closed", 1, "completed")}, 2, "/repos/Owner/Repo/issues/1/sub_issues"),
]


RACER = "Closed automatically (completed): all 2 sub-issues are closed; the last was #2."
# (name, table, event issue, existing comments on #1, expected writes). Two runs can both
# pass the "parent is open" check; each posts, then all but the lowest-id comment go.
RACES = [
    ("racing run already commented -> own duplicate deleted",
     {1: I(), 2: I("closed", 1, "completed"), 3: I("closed", 1, "completed")}, 3,
     [{"id": 50, "body": RACER, "updated_at": "2099-01-01T00:00:00Z"}],
     [("PATCH", 1, "closed", "completed"), ("COMMENT", 1), ("DELETE", 101)]),
    ("old auto-close comment from an earlier cycle -> kept, no delete [control]",
     {1: I(), 2: I("closed", 1, "completed"), 3: I("closed", 1, "completed")}, 3,
     [{"id": 50, "body": RACER, "updated_at": "2001-01-01T00:00:00Z"}],
     [("PATCH", 1, "closed", "completed"), ("COMMENT", 1)]),
]


def main() -> int:
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    Fake.base = f"http://127.0.0.1:{server.server_address[1]}"
    threading.Thread(target=server.serve_forever, daemon=True).start()
    script = extract_script()
    failed = 0

    for name, table, issue, action, want_rc, want_writes in CASES:
        Fake.issues, Fake.writes, Fake.fail = {k: dict(v) for k, v in table.items()}, [], set()
        Fake.comments, Fake.next_id = {}, 100
        r = fire(script, issue, action)
        ok = r.returncode == want_rc and Fake.writes == want_writes
        failed += not ok
        print(f"{'PASS' if ok else 'FAIL'}  {name}")
        if not ok:
            print(f"      rc={r.returncode} writes={Fake.writes}\n      stdout={r.stdout!r}\n      stderr={r.stderr!r}")

    for name, table, issue, existing, want_writes in RACES:
        Fake.issues, Fake.writes, Fake.fail = {k: dict(v) for k, v in table.items()}, [], set()
        Fake.comments, Fake.next_id = {1: [dict(c) for c in existing]}, 100
        r = fire(script, issue, "closed")
        ok = r.returncode == 0 and Fake.writes == want_writes
        failed += not ok
        print(f"{'PASS' if ok else 'FAIL'}  {name}")
        if not ok:
            print(f"      rc={r.returncode} writes={Fake.writes}\n      stdout={r.stdout!r}\n      stderr={r.stderr!r}")

    # Transport failure (nothing listening): curl itself fails, and the run must still
    # fail with an ::error:: annotation rather than dying silently under `set -e`.
    Fake.issues, Fake.writes, Fake.fail = {1: I(), 2: I("closed", 1, "completed")}, [], set()
    r = fire(script, 2, "closed", api="http://127.0.0.1:9")
    ok = r.returncode != 0 and "::error::" in r.stdout
    failed += not ok
    print(f"{'PASS' if ok else 'FAIL'}  transport failure -> fails loudly with ::error::")
    if not ok:
        print(f"      rc={r.returncode}\n      stdout={r.stdout!r}\n      stderr={r.stderr!r}")

    for name, table, issue, path in FAULTS:
        Fake.issues, Fake.writes, Fake.fail = {k: dict(v) for k, v in table.items()}, [], {path}
        Fake.comments, Fake.next_id = {}, 100
        r = fire(script, issue, "closed")
        ok = r.returncode != 0 and not any(w[0] == "PATCH" for w in Fake.writes) and "::error::" in r.stdout
        failed += not ok
        print(f"{'PASS' if ok else 'FAIL'}  {name}")
        if not ok:
            print(f"      rc={r.returncode} writes={Fake.writes}\n      stdout={r.stdout!r}\n      stderr={r.stderr!r}")

    server.shutdown()
    total = len(CASES) + len(RACES) + 1 + len(FAULTS)
    print(f"\n{total - failed}/{total} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
