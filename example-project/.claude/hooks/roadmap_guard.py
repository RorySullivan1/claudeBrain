#!/usr/bin/env python3
"""PreToolUse(Bash) guard: warn when the version cursor has drifted from the roadmap.

Opt-in BY PRESENCE: silent unless the project has BOTH a `.meta/roadmap/INDEX.md` (it has
adopted the development-map flow) and a `.meta/version` with a label. It only speaks up at
`git push` time, and only when the cursor (`.meta/version`) and the map (`.meta/roadmap/`)
disagree — e.g. shipping a version the roadmap doesn't list, or one the INDEX still marks
`planned`, or while the INDEX shows a different version as the in-progress cursor.

Like `version_guard.py` it NEVER blocks: it emits `permissionDecision: allow` plus an
`additionalContext` nudge, so the push proceeds and the model just learns the map needs a
status update (`/roadmap-status` to reconcile, `/roadmap-set` to re-slice). Fails safe: on
any unexpected shape or error it prints nothing and the push proceeds.
"""
import json
import os
import re
import sys
from pathlib import Path

PUSH_RE = re.compile(r"\bgit\s+push\b")
# A roadmap INDEX "Versions" table row: | vX.Y.Z | stage | goal | status |
ROW_RE = re.compile(r"^\|\s*(v\d[\w.\-]*)\s*\|.*\|\s*([^|]+?)\s*\|\s*$")


def meta_dir() -> Path:
    root = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    return Path(root) / ".meta"


def current_version(text: str) -> str:
    for line in text.splitlines():
        m = re.match(r"^#?\s*version:\s*(\S+)", line.strip(), re.IGNORECASE)
        if m and m.group(1) not in ("", "<label>"):
            return m.group(1)
    return ""


def current_status(text: str) -> str:
    for line in text.splitlines():
        m = re.match(r"^status:\s*(\S+)", line.strip(), re.IGNORECASE)
        if m:
            return m.group(1).lower()
    return ""


def parse_index(text: str) -> tuple[dict, str]:
    """Return ({version: status_text}, cursor_version) from the INDEX versions table."""
    statuses: dict[str, str] = {}
    cursor = ""
    for line in text.splitlines():
        m = ROW_RE.match(line.strip())
        if not m:
            continue
        version, status = m.group(1), m.group(2).strip()
        low = status.lower()
        if "version" in low and "status" in low:  # header row leaked through — skip
            continue
        statuses[version] = status
        if "cursor" in low or "in-progress" in low or "in progress" in low:
            cursor = cursor or version
    return statuses, cursor


def main() -> int:
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except (json.JSONDecodeError, ValueError):
        return 0
    if data.get("tool_name") != "Bash":
        return 0
    command = (data.get("tool_input") or {}).get("command") or ""
    if not PUSH_RE.search(command):
        return 0

    index_path = meta_dir() / "roadmap" / "INDEX.md"
    version_path = meta_dir() / "version"
    if not index_path.is_file() or not version_path.is_file():
        return 0  # roadmap flow not adopted (or no cursor) — stay silent

    try:
        index_text = index_path.read_text(encoding="utf-8", errors="replace")
        version_text = version_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return 0

    current = current_version(version_text)
    if not current:
        return 0
    status = current_status(version_text)
    statuses, _cursor = parse_index(index_text)
    if not statuses:
        return 0  # couldn't parse the table — say nothing rather than guess

    # Only flag UNAMBIGUOUS drift, keyed off the version's own status, so the normal
    # between-versions state (last-shipped version + a different next-planned cursor)
    # does NOT false-positive.
    warning = ""
    index_status = statuses.get(current, "").lower()
    if current not in statuses:
        warning = (f"`.meta/version` is {current}, but that version isn't listed on the "
                   f"roadmap INDEX (`.meta/roadmap/INDEX.md`). Add it to the map or re-slice "
                   f"with `/roadmap-set`.")
    elif status == "shipped" and "shipped" not in index_status:
        warning = (f"`.meta/version` marks {current} as shipped, but the roadmap INDEX still "
                   f"lists it as `{statuses[current]}`. Flip its row to `shipped` so the map "
                   f"tracks reality (`/roadmap-status` to reconcile).")
    elif status == "in-progress" and "planned" in index_status:
        warning = (f"You're shipping in-progress work for {current}, but the roadmap INDEX "
                   f"still lists it as `planned`. Mark its row `in-progress`.")
    if not warning:
        return 0  # status and map agree — nothing to say

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "permissionDecisionReason": "Roadmap cursor drift (advisory)",
            "additionalContext": warning,
        }
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
