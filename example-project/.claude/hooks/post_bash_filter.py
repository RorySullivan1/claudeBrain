#!/usr/bin/env python3
"""PostToolUse(Bash) filter: keep verbose command output out of the main context.

The command already ran; this only changes what the MODEL sees, via `updatedToolOutput`.
It strips ANSI color codes and, if the output is long, keeps the first HEAD and last TAIL
lines with an elision marker noting how much was cut. Short, clean output passes through
untouched.

Fails safe: if the tool_response shape is unexpected or anything errors, it emits nothing
(exit 0) and the original output is shown. The exact Bash tool_response shape can vary by
Claude Code version — verify with `claude --debug` if truncation isn't firing; the
extraction below handles a plain string or a dict with stdout/stderr/output/content.
"""
from __future__ import annotations
import json
import re
import sys

HEAD = 80
TAIL = 40
MAX_LINES = 200
MAX_CHARS = 12_000
ANSI = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")


def extract_text(resp) -> str | None:
    if isinstance(resp, str):
        return resp
    if isinstance(resp, dict):
        parts = []
        for key in ("stdout", "output", "content", "result", "stderr"):
            val = resp.get(key)
            if isinstance(val, str) and val:
                parts.append(val)
        if parts:
            return "\n".join(parts)
    return None


def main() -> int:
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except (json.JSONDecodeError, ValueError):
        return 0
    if data.get("tool_name") != "Bash":
        return 0
    text = extract_text(data.get("tool_response"))
    if text is None:
        return 0

    cleaned = ANSI.sub("", text)
    lines = cleaned.splitlines()
    had_ansi = cleaned != text
    too_long = len(lines) > MAX_LINES or len(cleaned) > MAX_CHARS

    if not too_long:
        # Only rewrite if we actually cleaned something; otherwise pass through.
        if had_ansi:
            print(json.dumps({"hookSpecificOutput": {
                "hookEventName": "PostToolUse", "updatedToolOutput": cleaned}}))
        return 0

    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PostToolUse", "updatedToolOutput": shorten(cleaned, lines)}}))
    return 0


def shorten(cleaned: str, lines: list[str]) -> str:
    """Elide the middle by lines, then by characters, so the result is always smaller.

    Line elision alone can't bound size: with few-but-wide lines (or one minified line) the
    head and tail windows overlap, and joining them would repeat the output. So lines are
    only elided when there are more than HEAD + TAIL of them, and whatever remains is then
    capped at MAX_CHARS by keeping its first and last characters.
    """
    out = cleaned
    if len(lines) > HEAD + TAIL:
        elided = len(lines) - HEAD - TAIL
        marker = (f"... [{elided} lines elided to save context — full output ran in the "
                  f"tool; re-run narrowed (grep/tail/--quiet) if you need the middle] ...")
        out = "\n".join([*lines[:HEAD], "", marker, "", *lines[-TAIL:]])
    if len(out) > MAX_CHARS:
        keep_head, keep_tail = MAX_CHARS * 2 // 3, MAX_CHARS // 3
        cut = len(out) - keep_head - keep_tail
        marker = (f"... [{cut} characters elided to save context — full output ran in the "
                  f"tool; re-run narrowed (grep/cut/--quiet) if you need the middle] ...")
        out = f"{out[:keep_head]}\n\n{marker}\n\n{out[-keep_tail:]}"
    return out


if __name__ == "__main__":
    raise SystemExit(main())
