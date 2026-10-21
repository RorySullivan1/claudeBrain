#!/usr/bin/env python3
"""Match a usage.py report against the spend-levers catalog and rank what would save most. Stdlib only.

One rule per lever in `../references/spend-levers.md`, by the same id (#62, #64). A rule reads
the report's measured tokens, prices the change from `../references/pricing.json`, and returns
a finding with its evidence, the change, an estimated saving and a confidence. It proposes and
never applies: nothing here writes a file.

Usage:
  audit.py [--logs DIR | --transcript FILE] [--session ID | --session current] [--command /NAME]
           [--since DATE] [--last N] [--json]
  audit.py --report FILE.json [--json]     # a saved `usage.py report --price --json`

Every dollar is an estimate at API list price, labelled as such: token counts are measured, the
arithmetic is the catalog's, and an assumption a rule makes is stated in its finding. A finding
is material at MATERIAL_SHARE of the profile's estimated spend and at least MATERIAL_MIN_USD.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import usage  # noqa: E402

LABEL = "estimate (API list price, model-based)"
MATERIAL_SHARE = 0.03
MATERIAL_MIN_USD = 0.50
MAX_FINDINGS = 5
MAX_LINES = 40              # the rendered report's cap
TOP_RESULTS = 25            # tool results and rebuilds asked of usage.py
SUMMARY_TOKENS = 20_000     # idle-rebuild: assumed size of a compaction summary
CONTEXT_TARGET = 150_000    # long-context: context per call the estimate holds a session to
LONG_SESSION_CALLS = 50
PREFIX_TRIM = 0.10          # standing-context: share of the prefix the estimate trims
LARGE_RESULT_CHARS = 20_000
BASH_CAP_CHARS = 12_400     # post_bash_filter MAX_CHARS plus its elision marker
READ_GUARD_CHARS = 60_000   # pre_read_guard THRESHOLD_BYTES
OUTPUT_SHARE_HIGH = 0.30
EFFORT_CUT = 0.25
FANOUT_SHARE_HIGH = 0.40
FAMILY_STEPS = (("opus", "sonnet"), ("sonnet", "haiku"))
SOURCE = "references/spend-levers.md"

RULES: dict = {}


def rule(lever: str):
    def register(fn):
        RULES[lever] = fn
        return fn
    return register


def usd(x: float) -> str:
    return f"${x:,.2f}"


def tok(n: float) -> str:
    return usage.h(n)


class Profile:
    """The report plus the prices, with the few derived numbers several rules share."""

    def __init__(self, report: dict, prices: dict):
        self.r, self.prices = report, prices
        main = [m for m in report["by_model"] if m["scope"] == "main"]
        self.main = max(main, key=lambda m: m["calls"]) if main else None
        self.main_model = self.main["model"] if self.main else None
        self.rate = usage.rate_for(prices, self.main_model) if self.main_model else None
        self.total = report.get("total_usd") or report.get("log_usd") or 0.0
        self.threshold = max(MATERIAL_MIN_USD, MATERIAL_SHARE * self.total)
        self.sessions = report.get("cache_by_session") or []
        self.calls_in = {s["session"]: s["main_calls"] for s in self.sessions}

    def rate_of(self, model: str | None) -> dict | None:
        return usage.rate_for(self.prices, model) if model else None

    def write_rate(self, ttl: str, rate: dict | None = None) -> float:
        r = rate or self.rate or {}
        return r.get("cache_write_1h" if ttl == "1h" else "cache_write_5m", 0.0)


def finding(lever, title, evidence, change, saving, confidence, assumption=None) -> dict:
    return {"lever": lever, "title": title, "evidence": evidence, "change": change,
            "saving_usd": round(saving, 2), "confidence": confidence, "assumption": assumption}


def check(lever, text) -> dict:
    return {"lever": lever, "check": text}


# --------------------------------------------------------------------------- the rules
@rule("idle-rebuild")
def idle_rebuild(p: Profile) -> list:
    hit = [s for s in p.sessions if s["rebuilds"]["idle"]]
    if not hit or not p.rate:
        return [check("idle-rebuild", "no rebuild after an idle gap past the TTL")]
    count = sum(s["rebuilds"]["idle"] for s in hit)
    written = sum(s["rebuilds"]["idle_tokens"] for s in hit)
    saving = 0.0
    for s in hit:
        n, k = s["rebuilds"]["idle_tokens"], s["rebuilds"]["idle"]
        w = p.write_rate(s["main_ttl"])
        now = n * w
        compacted = n * p.rate["cache_read"] + k * SUMMARY_TOKENS * (p.rate["output"] + w)
        saving += max(0.0, now - compacted) / 1e6
    worst = max(hit, key=lambda s: s["rebuilds"]["idle_tokens"])
    ev = [f"{count} rebuild(s) after a gap past the TTL rewrote {tok(written)} tokens at the write rate",
          f"session {worst['session']}: {worst['rebuilds']['idle']} of them, {tok(worst['rebuilds']['idle_tokens'])} "
          f"tokens ({worst['main_ttl']} TTL)"]
    return [finding("idle-rebuild", "Context rebuilt after idle breaks", ev,
                    "/compact at a natural break before stepping away, /clear when the next task is "
                    "unrelated; idle /goal check-ins and scheduled tasks resume with the whole context",
                    saving, "high", f"a compaction summary of {SUMMARY_TOKENS:,} tokens")]


@rule("cache-ttl-main")
def cache_ttl_main(p: Profile) -> list:
    if not p.main or not p.rate:
        return [check("cache-ttl-main", "no main-conversation calls")]
    w1, w5 = p.main["cache_write_1h"], p.main["cache_write_5m"]
    paused = sum(s["pauses_between_ttls"]["tokens"] for s in p.sessions)
    premium = w1 * (p.rate["cache_write_1h"] - p.rate["cache_write_5m"]) / 1e6
    benefit = paused * (p.rate["cache_write_5m"] - p.rate["cache_read"]) / 1e6
    if w1 >= w5:
        if premium > benefit:
            return [finding("cache-ttl-main", "The 1-hour main TTL costs more than it saves",
                            [f"1h writes {tok(w1)} tokens: premium over 5m {usd(premium)}",
                             f"pauses of 5-60 min carried {tok(paused)} tokens: {usd(benefit)} to rebuild at 5m"],
                            "set promptCacheTtl (or CLAUDE_CODE_PROMPT_CACHE_TTL) to 5m",
                            premium - benefit, "medium")]
        return [check("cache-ttl-main", f"1h TTL earns its {usd(premium)} premium: a 5m TTL would add "
                                        f"{usd(benefit)} of rebuilds at the measured pauses")]
    gain = paused * (p.rate["cache_write_5m"] - p.rate["cache_read"]) / 1e6
    cost = w5 * (p.rate["cache_write_1h"] - p.rate["cache_write_5m"]) / 1e6
    if gain > cost:
        return [finding("cache-ttl-main", "Pauses rebuild a 5-minute cache that a 1-hour one would keep",
                        [f"pauses of 5-60 min carried {tok(paused)} tokens, rebuilt at 5m: {usd(gain)}",
                         f"a 1h TTL would add {usd(cost)} of write premium on {tok(w5)} tokens"],
                        "set promptCacheTtl (or CLAUDE_CODE_PROMPT_CACHE_TTL) to 1h", gain - cost, "medium")]
    return [check("cache-ttl-main", f"5m TTL is the cheaper one here ({usd(cost)} premium against "
                                    f"{usd(gain)} of pause rebuilds)")]


@rule("cache-ttl-subagent")
def cache_ttl_subagent(p: Profile) -> list:
    out = []
    for m in p.r["by_model"]:
        if m["scope"] != "subagent" or not m["cache_write_1h"]:
            continue
        rate = p.rate_of(m["model"])
        if not rate:
            continue
        premium = m["cache_write_1h"] * (rate["cache_write_1h"] - rate["cache_write_5m"]) / 1e6
        out.append(finding("cache-ttl-subagent", f"Subagents on {m['model']} write the 1-hour cache",
                           [f"{tok(m['cache_write_1h'])} subagent cache-write tokens at the 1h rate"],
                           "unset ENABLE_PROMPT_CACHING_1H, or set subagentPromptCacheTtl to 5m",
                           premium, "high"))
    return out or [check("cache-ttl-subagent", "subagent cache writes are 5m")]


@rule("mid-session-switch")
def mid_session_switch(p: Profile) -> list:
    rebuilt = [r for r in p.r.get("top_rebuilds") or [] if r["cause"] == "model_switch"]
    count = sum(s["rebuilds"]["model_switch"] for s in p.sessions)
    if not count:
        return [check("mid-session-switch", "no rebuild after a model switch")]
    tokens = sum(r["cache_write"] for r in rebuilt)
    saving = sum(r["cache_write"] * p.write_rate("1h", p.rate_of(r["model"])) for r in rebuilt) / 1e6
    return [finding("mid-session-switch", "Model switches rebuilt the cache",
                    [f"{count} rebuild(s) right after a model switch; the largest wrote {tok(tokens)} tokens"],
                    "set the model and effort before the first prompt, or switch at a /clear",
                    saving, "high", "priced at the 1h write rate")]


@rule("always-loaded-edits")
def always_loaded_edits(p: Profile) -> list:
    edits = sum(s["always_loaded_edits"] for s in p.sessions)
    broke = sum(s["rebuilds_after_edit"] for s in p.sessions)
    if broke:
        return [check("always-loaded-edits", f"{broke} rebuild(s) followed an edit to CLAUDE.md or memory, "
                                             "which the docs say keeps the cache: look for another cause "
                                             "(tool definitions, the model, an expired TTL)")]
    return [check("always-loaded-edits", f"{edits} mid-session edit(s) to always-loaded files, none followed by "
                                         "a rebuild (the docs say they keep the cache)")]


@rule("long-context")
def long_context(p: Profile) -> list:
    hit = [s for s in p.sessions
           if s["context_per_call"] > CONTEXT_TARGET and s["main_calls"] >= LONG_SESSION_CALLS]
    if not hit or not p.rate:
        return [check("long-context", f"no session averaged over {tok(CONTEXT_TARGET)} tokens a call")]
    excess = sum((s["context_per_call"] - CONTEXT_TARGET) * s["main_calls"] for s in hit)
    saving = excess * p.rate["cache_read"] / 1e6
    worst = max(hit, key=lambda s: s["context_per_call"] * s["main_calls"])
    return [finding("long-context", "Long sessions carry a large context on every call",
                    [f"{len(hit)} session(s) averaged over {tok(CONTEXT_TARGET)} tokens a call",
                     f"session {worst['session']}: {tok(worst['context_per_call'])} a call over "
                     f"{worst['main_calls']:,} calls"],
                    "/clear between unrelated tasks, /compact at natural breaks, one session per task",
                    saving, "medium", f"context held to {CONTEXT_TARGET:,} tokens a call")]


@rule("standing-context")
def standing_context(p: Profile) -> list:
    prefixes = [s["prefix_tokens"] for s in p.sessions if s["main_calls"]]
    if not prefixes or not p.rate:
        return [check("standing-context", "no main calls to measure")]
    median = statistics.median(prefixes)
    calls = sum(s["main_calls"] for s in p.sessions)
    saving = median * PREFIX_TRIM * calls * p.rate["cache_read"] / 1e6
    f = finding("standing-context", "The standing prefix rides in every call",
                [f"median standing prefix {tok(median)} tokens over {calls:,} main calls"],
                "trim CLAUDE.md and the memory INDEX, move workflow detail into skills, prune unused "
                "skills and MCP servers", saving, "medium",
                f"trimming {PREFIX_TRIM:.0%} of the prefix; most of it is Claude Code's own")
    f["check_text"] = f"median standing prefix {tok(median)} tokens"
    return [f]


def results(p: Profile, tool: str | None, over: int) -> list:
    return [t for t in p.r.get("top_tool_results") or []
            if t["context"] == "main" and t["chars"] > over and (tool is None or t["tool"] == tool)]


def reread_usd(p: Profile, rows: list, keep: int = 0) -> float:
    """What the part of each result over `keep` chars costs, re-read on half the session's calls."""
    if not p.rate:
        return 0.0
    tokens = sum(max(0, t["chars"] - keep) / 4 * p.calls_in.get(t["session"], 0) / 2 for t in rows)
    return tokens * p.rate["cache_read"] / 1e6


@rule("tool-output-size")
def tool_output_size(p: Profile) -> list:
    guarded = {"Bash": BASH_CAP_CHARS, "Read": READ_GUARD_CHARS}  # their own rules report those
    rows = [t for t in results(p, None, LARGE_RESULT_CHARS) if t["chars"] <= guarded.get(t["tool"], t["chars"])]
    if not rows:
        return [check("tool-output-size", f"no main-context tool result over {LARGE_RESULT_CHARS:,} chars")]
    tools = sorted({t["tool"] for t in rows})
    return [finding("tool-output-size", "Large tool results stay in the main context",
                    [f"{len(rows)} main-context result(s) over {LARGE_RESULT_CHARS:,} chars "
                     f"(largest {rows[0]['chars']:,}, from {rows[0]['tool']}); tools: {', '.join(tools)}"],
                    "send bulk reads, test runs and fetches to token-manager or Explore; page with offset/limit",
                    reread_usd(p, rows, LARGE_RESULT_CHARS), "medium",
                    "each result re-read on half its session's main calls")]


@rule("bash-filter")
def bash_filter(p: Profile) -> list:
    rows = results(p, "Bash", BASH_CAP_CHARS)
    if not rows:
        return [check("bash-filter", f"post_bash_filter holds: no Bash result over {BASH_CAP_CHARS:,} chars "
                                     "reached the main context")]
    return [finding("bash-filter", "Bash output passed the filter's cap",
                    [f"{len(rows)} Bash result(s) over {BASH_CAP_CHARS:,} chars in the main context "
                     f"(largest {rows[0]['chars']:,})"],
                    "wire post-tool-use-bash-filter.json into settings.json through build-hooks.py",
                    reread_usd(p, rows, BASH_CAP_CHARS), "high",
                    "each result re-read on half its session's main calls")]


@rule("read-guard")
def read_guard(p: Profile) -> list:
    rows = results(p, "Read", READ_GUARD_CHARS)
    if not rows:
        return [check("read-guard", f"pre_read_guard holds: no Read result over {READ_GUARD_CHARS:,} chars "
                                    "reached the main context")]
    return [finding("read-guard", "A whole large file was read into the main context",
                    [f"{len(rows)} Read result(s) over {READ_GUARD_CHARS:,} chars (largest {rows[0]['chars']:,})"],
                    "wire pre-tool-use-read-guard.json through build-hooks.py; read a slice with offset/limit",
                    reread_usd(p, rows, READ_GUARD_CHARS), "medium",
                    "each result re-read on half its session's main calls; a paged or exempt read also shows")]


def cheaper(p: Profile, model: str) -> str | None:
    for big, small in FAMILY_STEPS:
        if f"-{big}-" in model:
            candidate = model.replace(f"-{big}-", f"-{small}-")
            if p.rate_of(candidate):
                return candidate
    return None


BUILT_IN_AGENTS = frozenset({"general-purpose", "Explore", "Plan", "statusline-setup", "claude-code-guide"})


def model_change(agent: str, target: str) -> str:
    """Where to set the cheaper model: a built-in agent has no file to edit."""
    alias = target.split("-")[1]
    if agent in BUILT_IN_AGENTS:
        return f"pass model: {alias} when dispatching {agent}, or set CLAUDE_CODE_SUBAGENT_MODEL"
    return f"set model: {alias} in .claude/agents/{agent}.md"


@rule("model-per-agent")
def model_per_agent(p: Profile) -> list:
    out = []
    for a in p.r.get("by_subagent_type") or []:
        if len(a.get("models") or []) != 1 or not a.get("usd"):
            continue
        model = a["models"][0]
        target = cheaper(p, model)
        if not target:
            continue
        repriced = usage.price(p.rate_of(target), dict(a["tokens"], cache_write_5m=a["tokens"]["cache_write"]))
        saving = a["usd"] - repriced
        out.append(finding("model-per-agent", f"{a['key']} runs on {model}",
                           [f"{a['key']}: {a['runs']} run(s), {usd(a['usd'])} on {model}; the same tokens on "
                            f"{target}: {usd(repriced)}"],
                           model_change(a["key"], target), saving, "low",
                           "the same tokens on the cheaper model; quality not measured"))
    return out or [check("model-per-agent", "no subagent type has a cheaper model of its family to try")]


@rule("effort-level")
def effort_level(p: Profile) -> list:
    if not p.main or not p.rate or not p.main.get("usd"):
        return [check("effort-level", "no priced main-conversation calls")]
    out_usd = p.main["tokens"]["output"] * p.rate["output"] / 1e6
    share = out_usd / p.main["usd"]
    if share < OUTPUT_SHARE_HIGH:
        return [check("effort-level", f"output (thinking included) is {share:.0%} of main spend")]
    return [finding("effort-level", "Output and thinking carry a large share of main spend",
                    [f"main output {tok(p.main['tokens']['output'])} tokens: {usd(out_usd)}, {share:.0%} of main spend"],
                    "pick a lower effort level for routine work at the start of a session (/effort)",
                    out_usd * EFFORT_CUT, "low", f"a {EFFORT_CUT:.0%} cut in output tokens")]


@rule("subagent-fanout")
def subagent_fanout(p: Profile) -> list:
    sub = sum(m.get("usd") or 0 for m in p.r["by_model"] if m["scope"] == "subagent")
    log = p.r.get("log_usd") or 0
    share = sub / log if log else 0.0
    if share < FANOUT_SHARE_HIGH:
        return [check("subagent-fanout", f"subagents carry {share:.0%} of log spend")]
    build = 0.0
    for a in p.r.get("by_subagent_type") or []:
        rate = p.rate_of((a.get("models") or [None])[0])
        if rate:
            build += a["tokens"]["cache_write"] * rate["cache_write_5m"] / 1e6
    runs = sum(a["runs"] for a in p.r.get("by_subagent_type") or [])
    return [finding("subagent-fanout", "Subagents carry most of the spend",
                    [f"subagents {usd(sub)} of {usd(log)} log spend ({share:.0%}) over {runs} run(s)"],
                    "cap fan-out, merge small sibling tasks into one run, keep trivial tasks inline",
                    build / 2, "low", "half the runs merged, saving their context build")]


# --------------------------------------------------------------------------- the audit
def audit(report: dict, prices: dict) -> dict:
    p = Profile(report, prices)
    material, minor, checks = [], [], []
    for lever, fn in RULES.items():
        for item in fn(p):
            if "check" in item:
                checks.append(item)
            elif item["saving_usd"] >= p.threshold:
                material.append(item)
            else:
                minor.append(item)
                checks.append(check(lever, item.pop("check_text", None) or
                                    f"{item['evidence'][0]}: ~{usd(item['saving_usd'])}, below the threshold"))
    for f in material:
        f.pop("check_text", None)
    material.sort(key=lambda f: -f["saving_usd"])
    c = report["counts"]
    caveats = []
    unpriced = (report.get("pricing") or {}).get("unpriced_models")
    if unpriced:
        caveats.append(f"unpriced models are left out of every estimate: {', '.join(unpriced)}")
    if report.get("unknown_shapes"):
        caveats.append(f"{sum(report['unknown_shapes'].values())} log line(s) of an unknown shape were reported "
                       "by usage.py, not counted")
    if {"long-context", "idle-rebuild"} <= {f["lever"] for f in material}:
        caveats.append("long-context and idle-rebuild are both cut by compacting, so their savings overlap: "
                       "don't add them")
    if report.get("background") is None:
        caveats.append("a prompt-level filter leaves background requests out of the total")
    return {"label": LABEL, "catalog": SOURCE,
            "profile": {"sessions": c["sessions"], "prompts": c["prompts"], "calls": c["calls"],
                        "subagent_runs": c["subagent_runs"], "main_model": p.main_model,
                        "estimated_usd": round(p.total, 2), "cache_read_share": round(report["cache_read_share"], 3)},
            "material_threshold_usd": round(p.threshold, 2),
            "findings": material[:MAX_FINDINGS], "more_findings": max(0, len(material) - MAX_FINDINGS),
            "below_threshold": [{"lever": f["lever"], "saving_usd": f["saving_usd"]} for f in minor],
            "checks": checks, "caveats": caveats}


def render(a: dict) -> str:
    pr = a["profile"]
    lines = [f"Spend audit: {pr['sessions']} session(s), {pr['prompts']} prompt(s), {pr['calls']:,} calls, "
             f"{pr['subagent_runs']} subagent run(s); main model {pr['main_model']}.",
             f"Estimated spend {usd(pr['estimated_usd'])}; a finding is material at "
             f"{usd(a['material_threshold_usd'])}. Every $ is an {a['label']}."]
    if not a["findings"]:
        lines.append("No material finding.")
    for i, f in enumerate(a["findings"], 1):
        lines.append(f"{i}. [{f['lever']}] {f['title']}: save ~{usd(f['saving_usd'])} ({f['confidence']} confidence)")
        lines += [f"   - {e}" for e in f["evidence"]]
        lines.append(f"   change: {f['change']}")
        if f["assumption"]:
            lines.append(f"   assumes {f['assumption']}")
    if a["more_findings"]:
        lines.append(f"(+{a['more_findings']} more material finding(s) in --json)")
    lines.append("Checks:")
    lines += [f"  [{c['lever']}] {c['check']}" for c in a["checks"]]
    lines += [f"Caveat: {c}" for c in a["caveats"]]
    if len(lines) > MAX_LINES:
        lines = lines[:MAX_LINES - 1] + ["(checks truncated; --json has them all)"]
    return "\n".join(lines)


def main(argv: list | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group()
    src.add_argument("--logs", type=Path)
    src.add_argument("--transcript", type=Path)
    src.add_argument("--report", type=Path)
    ap.add_argument("--session")
    ap.add_argument("--command")
    ap.add_argument("--since")
    ap.add_argument("--last", type=int)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    prices = usage.load_prices()
    if a.report:
        report = json.loads(a.report.read_text(encoding="utf-8"))
    else:
        files = usage.discover(a.logs, a.transcript)
        if not files:
            print(f"no session logs at {a.transcript or a.logs or usage.default_logs()}")
            return 2
        corpus = usage.load(files)
        session = files[-1].stem if a.session == "current" else a.session  # newest log is this session
        segs = usage.select(corpus, session, a.command, a.since, a.last)
        report = usage.build_report(corpus, segs, TOP_RESULTS, prices,
                                    filtered=bool(a.command or a.since or a.last))
    result = audit(report, prices)
    print(json.dumps(result, indent=1) if a.json else render(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
