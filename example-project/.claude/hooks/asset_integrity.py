#!/usr/bin/env python3
"""PreToolUse(Bash) guard: report `.claude/` asset defects before a commit or push.

Checks the structural invariants that are cheap to break and expensive to notice later:
a skill folder that no longer matches its `name:` frontmatter, an asset missing `name:` or
`description:`, a `references/` file cited by a SKILL.md that isn't there, and broken
symlinks (this repo single-sources some assets, so a moved canonical file silently breaks
the link).

Opt-in BY PRESENCE: silent in a project with no `.claude/skills` or `.claude/agents`.

**Non-mutating by contract.** It reads, it reports, it never writes — no reformatting, no
renaming, no "helpful" fixes. A hook that edits files during a commit turns a review into a
moving target, and the diff you approved is not the diff you push. If something is wrong,
a human or the model fixes it deliberately.

It never blocks: it emits `permissionDecision: allow` plus an `additionalContext` warning,
so a commit is never vetoed — the model just learns what's broken. Fails safe: on any
unexpected shape or error it prints nothing and the command proceeds. Flip the decision to
`deny` if you want hard enforcement.
"""
import json
import os
import re
import sys
from pathlib import Path

GIT_RE = re.compile(r"\bgit\s+(commit|push)\b")
FM_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*(?:\n|\Z)", re.DOTALL)
REF_RE = re.compile(r"`(references/[A-Za-z0-9._/-]+)`")
SKIP_DIRS = {".git", "node_modules", "venv", ".venv", "__pycache__", "dist", "build"}
MAX_FINDINGS = 12


def project_root() -> Path:
    return Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())


def claude_dirs(root: Path) -> list[Path]:
    """`.claude` directories at depth <= 3, skipping vendor/VCS trees."""
    found = []
    for path in root.glob("*/.claude"):
        found.append(path)
    for path in root.glob("*/*/.claude"):
        found.append(path)
    if (root / ".claude").is_dir():
        found.insert(0, root / ".claude")
    return [p for p in found if p.is_dir() and not (SKIP_DIRS & set(p.parts))]


def frontmatter_keys(text: str) -> set[str] | None:
    """Top-level keys of the YAML frontmatter block, or None if there is no block."""
    m = FM_RE.match(text)
    if not m:
        return None
    keys = set()
    for line in m.group(1).splitlines():
        if line[:1].isspace():  # continuation of a folded/nested value
            continue
        k = re.match(r"^([A-Za-z0-9_-]+)\s*:", line)
        if k:
            keys.add(k.group(1))
    return keys


def frontmatter_name(text: str) -> str | None:
    m = FM_RE.match(text)
    if not m:
        return None
    for line in m.group(1).splitlines():
        k = re.match(r"^name\s*:\s*(\S+)", line)
        if k:
            return k.group(1).strip("\"'")
    return None


def read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def check_skill(folder: Path, rel: str, out: list[str]) -> None:
    skill = folder / "SKILL.md"
    if not skill.is_file():
        out.append(f"{rel}/ has no SKILL.md")
        return
    text = read(skill)
    if text is None:
        return
    keys = frontmatter_keys(text)
    if keys is None:
        out.append(f"{rel}/SKILL.md has no YAML frontmatter block")
        return
    for required in ("name", "description"):
        if required not in keys:
            out.append(f"{rel}/SKILL.md frontmatter is missing `{required}:`")
    name = frontmatter_name(text)
    if name and name != folder.name:
        out.append(f"{rel}/ folder name != frontmatter `name: {name}` (they must match)")
    for ref in set(REF_RE.findall(text)):
        if not (folder / ref).exists():
            out.append(f"{rel}/SKILL.md cites `{ref}` but that file does not exist")


def check_agent(path: Path, rel: str, out: list[str]) -> None:
    text = read(path)
    if text is None:
        return
    keys = frontmatter_keys(text)
    if keys is None:
        out.append(f"{rel} has no YAML frontmatter block")
        return
    for required in ("name", "description"):
        if required not in keys:
            out.append(f"{rel} frontmatter is missing `{required}:`")
    name = frontmatter_name(text)
    if name and name != path.stem:
        out.append(f"{rel} filename != frontmatter `name: {name}` (they must match)")


def scan(root: Path) -> list[str]:
    out: list[str] = []
    for cdir in claude_dirs(root):
        for link in cdir.rglob("*"):
            if link.is_symlink() and not link.exists():
                out.append(f"{link.relative_to(root)} is a broken symlink")
        skills = cdir / "skills"
        if skills.is_dir():
            for folder in sorted(skills.iterdir()):
                if folder.is_dir():
                    check_skill(folder, str(folder.relative_to(root)), out)
        agents = cdir / "agents"
        if agents.is_dir():
            for path in sorted(agents.glob("*.md")):
                if path.name != "README.md":
                    check_agent(path, str(path.relative_to(root)), out)
    # Symlinked trees are visited from both ends; report each defect once.
    return list(dict.fromkeys(out))


def main() -> int:
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except (json.JSONDecodeError, ValueError):
        return 0
    if data.get("tool_name") != "Bash":
        return 0
    command = (data.get("tool_input") or {}).get("command") or ""
    if not GIT_RE.search(command):
        return 0

    root = project_root()
    try:
        if not any((c / "skills").is_dir() or (c / "agents").is_dir() for c in claude_dirs(root)):
            return 0  # no assets here — nothing this guard can speak to
        findings = scan(root)
    except (OSError, RecursionError):
        return 0
    if not findings:
        return 0

    shown = findings[:MAX_FINDINGS]
    extra = len(findings) - len(shown)
    msg = (f"`.claude/` asset integrity — {len(findings)} issue(s) found:\n"
           + "\n".join(f"  - {f}" for f in shown)
           + (f"\n  … and {extra} more" if extra else "")
           + "\nThis check is advisory and non-mutating; fix these deliberately before shipping.")
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "permissionDecisionReason": "Asset integrity issues (advisory)",
            "additionalContext": msg,
        }
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
