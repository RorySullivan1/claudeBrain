#!/usr/bin/env python3
"""Render, check, and number issue bodies from the github-issues templates.

    issue_body.py render <kind> <values.json> [--out FILE]
    issue_body.py check  <file> [--allow-self]
    issue_body.py fill-self <file> <number> [--out FILE]

<kind> is a template name under ../references/templates/ (epic, task, bug, feature).
values.json maps each placeholder to its markdown. Two keys are special:

- `parent`: omit it or set it to null to drop the "Part of #…" line.
- An OPTIONAL section (see OPTIONAL) whose value is null is removed, heading included.

`{{self}}` is never rendered. The issue's own number exists only after creation, so
`fill-self` patches it in afterwards. `check --allow-self` is the pre-filing gate and
plain `check` is the post-filing one. Exit status: 0 = clean, 2 = defects, listed on stderr.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

TEMPLATES = Path(__file__).resolve().parent.parent / "references" / "templates"
PLACEHOLDER = re.compile(r"\{\{\s*([a-z_]+)\s*\}\}")
GUIDE = re.compile(r"<!--\s*guide:.*?-->\n?", re.S)
HEADING = re.compile(r"^## (.+)$", re.M)
CLOSING = re.compile(r"\b(close[sd]?|fix(e[sd])?|resolve[sd]?) #\d+\b", re.I)
OPTIONAL = {"risks": "Risks and open questions"}


def _fail(defects: list[str]) -> int:
    for d in defects:
        print(f"issue_body: {d}", file=sys.stderr)
    return 2


def _drop_section(text: str, heading: str) -> str:
    return re.sub(rf"^## {re.escape(heading)}\n.*?(?=^## |\Z)", "", text, flags=re.M | re.S)


def render(kind: str, values: dict) -> tuple[str, list[str]]:
    path = TEMPLATES / f"{kind}.md"
    if not path.is_file():
        known = sorted(p.stem for p in TEMPLATES.glob("*.md"))
        return "", [f"unknown template {kind!r}; known: {', '.join(known)}"]
    text = GUIDE.sub("", path.read_text(encoding="utf-8"))

    if values.get("parent") in (None, ""):
        text = re.sub(r"^Part of #\{\{parent\}\}\n\n?", "", text, flags=re.M)
    for key, heading in OPTIONAL.items():
        if key in values and values[key] is None:
            text = _drop_section(text, heading)

    wanted = {m for m in PLACEHOLDER.findall(text)} - {"self"}
    missing = sorted(k for k in wanted if values.get(k) in (None, ""))
    if missing:
        return "", [f"missing value for: {', '.join(missing)}"]

    def sub(m: re.Match) -> str:
        key = m.group(1)
        return m.group(0) if key == "self" else str(values[key]).strip()

    text = PLACEHOLDER.sub(sub, text)
    return re.sub(r"\n{3,}", "\n\n", text).strip() + "\n", []


def check(text: str, allow_self: bool) -> list[str]:
    defects = []
    for key in PLACEHOLDER.findall(text):
        if not (allow_self and key == "self"):
            defects.append(f"unfilled placeholder {{{{{key}}}}}")
    if "<!-- guide:" in text:
        defects.append("template guidance comment left in the body")
    parts = HEADING.split(text)
    sections = dict(zip(parts[1::2], parts[2::2]))
    for heading, body in sections.items():
        if not body.strip():
            defects.append(f"empty section: ## {heading}")
    # Search the fenced line only: the footnote's own example keywords must not satisfy this.
    done = re.search(r"```\n(.*?)\n```", sections.get("Done when", ""), re.S)
    if "Done when" in sections and not allow_self and not (done and CLOSING.search(done.group(1))):
        defects.append("'Done when' has no numbered closing keyword (run fill-self)")
    return defects


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("render")
    r.add_argument("kind")
    r.add_argument("values")
    r.add_argument("--out")
    c = sub.add_parser("check")
    c.add_argument("file")
    c.add_argument("--allow-self", action="store_true")
    f = sub.add_parser("fill-self")
    f.add_argument("file")
    f.add_argument("number", type=int)
    f.add_argument("--out")
    args = ap.parse_args(argv)

    if args.cmd == "render":
        values = json.loads(Path(args.values).read_text(encoding="utf-8"))
        text, defects = render(args.kind, values)
        defects = defects or check(text, allow_self=True)
        if defects:
            return _fail(defects)
    elif args.cmd == "check":
        defects = check(Path(args.file).read_text(encoding="utf-8"), args.allow_self)
        if defects:
            return _fail(defects)
        print("issue_body: clean")
        return 0
    else:
        text = Path(args.file).read_text(encoding="utf-8")
        if "{{self}}" not in text:
            return _fail(["no {{self}} placeholder to fill"])
        text = text.replace("{{self}}", str(args.number))

    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
