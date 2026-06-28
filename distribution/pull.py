#!/usr/bin/env python
"""pull — copy an asset (and its dependencies + companion hooks) from this brain into a project.

This is the helper a Claude instance in another repo runs to pull a capability out of the brain.
It reads distribution/library.json, expands the requested asset(s) transitively (their `requires`),
and copies everything from the CANONICAL example-project/.claude tree — dereferencing symlinks, so
the consumer never inherits the brain's authoring-only symlinks.

What a pull brings:
  - the asset folder (skill) or file (agent/command/workflow), including any bundled scripts/;
  - every transitive dependency asset;
  - the companion hook fragments those assets need, plus any scripts those fragments reference
    (e.g. the loose hooks/post_bash_filter.py), plus hooks/build-hooks.py so the consumer can
    compile the fragments into their settings.json;
  - a .brain-provenance.json stamp recording what was pulled, from which brain version, when.

Usage:
    python distribution/pull.py skills/knowledge-router --dest ../myproj/.claude
    python distribution/pull.py agents/python-developer skills/branding --dest ../myproj/.claude
    python distribution/pull.py skills/token-optimizer --dest ../myproj/.claude --dry-run

After pulling assets that carry hooks, run the target project's hook compiler to activate them:
    python <target>/.claude/hooks/build-hooks.py
(or merge the printed fragments into <target>/.claude/settings.json by hand).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

CLAUDE_REL_RE = re.compile(r"\.claude/([A-Za-z0-9_./-]+\.py)")


def _force_utf8() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def brain_root() -> Path:
    return Path(__file__).resolve().parent.parent


def src_claude() -> Path:
    return brain_root() / "example-project" / ".claude"


def load_library() -> dict:
    path = brain_root() / "distribution" / "library.json"
    if not path.exists():
        sys.exit("error: distribution/library.json missing — run "
                 "`python distribution/build_library.py` first.")
    return json.loads(path.read_text(encoding="utf-8"))


def resolve(requested: list[str], assets: dict) -> tuple[list[str], dict[str, str]]:
    """Transitively expand requested ids via `requires`. Returns (ordered ids, origin map)."""
    origin: dict[str, str] = {}
    order: list[str] = []
    seen: set[str] = set()

    def visit(aid: str, how: str) -> None:
        if aid in seen:
            return
        if aid not in assets:
            sys.exit(f"error: unknown asset id '{aid}'. See LIBRARY.md for valid ids.")
        seen.add(aid)
        origin[aid] = how
        for dep in assets[aid].get("requires", []):
            visit(dep, "dependency")
        order.append(aid)

    for aid in requested:
        visit(aid, "requested")
    return order, origin


def collect_hooks(ids: list[str], assets: dict) -> list[str]:
    hooks: list[str] = []
    for aid in ids:
        for h in assets[aid].get("hooks", []):
            if h not in hooks:
                hooks.append(h)
    return hooks


def referenced_scripts(fragment_path: Path) -> list[str]:
    """Find .claude-relative .py paths a hook fragment invokes (so we copy them too)."""
    try:
        data = json.loads(fragment_path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return []
    rels: list[str] = []
    for arg in re.findall(r'"([^"]*)"', json.dumps(data)):
        m = CLAUDE_REL_RE.search(arg)
        if m and m.group(1) not in rels:
            rels.append(m.group(1))
    return rels


def brain_version() -> str:
    version_file = brain_root() / "example-project" / ".meta" / "version"
    if version_file.exists():
        for line in version_file.read_text(encoding="utf-8").splitlines():
            m = re.match(r"#\s*version:\s*(\S+)", line)
            if m:
                return m.group(1)
    try:
        sha = subprocess.run(["git", "-C", str(brain_root()), "rev-parse", "--short", "HEAD"],
                             capture_output=True, text=True, timeout=10)
        if sha.returncode == 0 and sha.stdout.strip():
            return sha.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return "unknown"


def copy_path(src: Path, dest: Path) -> None:
    """Copy a file or directory, dereferencing symlinks, creating parents, overwriting."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(src, dest, symlinks=False)
    else:
        shutil.copy2(src, dest)  # follows symlinks by default → copies the real file


def main(argv: list[str] | None = None) -> int:
    _force_utf8()
    parser = argparse.ArgumentParser(prog="pull.py")
    parser.add_argument("assets", nargs="+", help="asset id(s), e.g. skills/knowledge-router")
    parser.add_argument("--dest", required=True,
                        help="target project's .claude directory (created if missing)")
    parser.add_argument("--dry-run", action="store_true",
                        help="print the resolved plan without copying anything")
    args = parser.parse_args(argv)

    library = load_library()
    assets = library["assets"]
    dest = Path(args.dest).expanduser()

    ids, origin = resolve(args.assets, assets)
    hooks = collect_hooks(ids, assets)

    # Map each hook fragment to the extra scripts it references.
    hook_scripts: dict[str, list[str]] = {}
    for h in hooks:
        frag = src_claude() / "hooks" / h
        if not frag.exists():
            sys.exit(f"error: companion hook fragment '{h}' not found at {frag}")
        hook_scripts[h] = referenced_scripts(frag)

    print(f"Pull plan (source: {src_claude().relative_to(brain_root())}, dest: {dest}):\n")
    print("  Assets:")
    for aid in ids:
        tag = "" if origin[aid] == "requested" else f"  [{origin[aid]}]"
        print(f"    - {aid}{tag}")
    if hooks:
        print("\n  Companion hooks:")
        for h in hooks:
            extra = f"  (+ {', '.join(hook_scripts[h])})" if hook_scripts[h] else ""
            print(f"    - hooks/{h}{extra}")
        print("    - hooks/build-hooks.py  (compiler, to merge fragments into settings.json)")

    if args.dry_run:
        print("\n(dry run — nothing written)")
        return 0

    dest.mkdir(parents=True, exist_ok=True)

    # Copy assets.
    for aid in ids:
        rel = assets[aid]["path"]
        copy_path(src_claude() / rel, dest / rel)

    # Copy hook fragments + their referenced scripts + the compiler.
    copied_scripts: set[str] = set()
    for h in hooks:
        copy_path(src_claude() / "hooks" / h, dest / "hooks" / h)
        for rel in hook_scripts[h]:
            if rel not in copied_scripts:
                src_script = src_claude() / rel
                if src_script.exists():
                    copy_path(src_script, dest / rel)
                    copied_scripts.add(rel)
    if hooks:
        compiler = src_claude() / "hooks" / "build-hooks.py"
        if compiler.exists():
            copy_path(compiler, dest / "hooks" / "build-hooks.py")

    # Provenance stamp (append).
    stamp_path = dest / ".brain-provenance.json"
    stamp = {"source": "claudeBrain", "pulls": []}
    if stamp_path.exists():
        try:
            stamp = json.loads(stamp_path.read_text(encoding="utf-8"))
        except ValueError:
            pass
    version, when = brain_version(), datetime.now().isoformat(timespec="seconds")
    for aid in ids:
        stamp["pulls"].append({
            "asset": aid, "via": origin[aid], "brain_version": version, "pulled_at": when,
        })
    stamp_path.write_text(json.dumps(stamp, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"\nPulled {len(ids)} asset(s) into {dest} (brain version {version}).")
    if hooks:
        print("\nNext step — activate the companion hooks in the target project:")
        print(f"    python {dest}/hooks/build-hooks.py")
        print("  (or merge the fragments above into the target's .claude/settings.json by hand)")
    print("\nProvenance recorded in .brain-provenance.json.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
