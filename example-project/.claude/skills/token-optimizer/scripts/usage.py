#!/usr/bin/env python3
"""Measure what Claude Code sessions actually spent, from their own logs. Stdlib only.

`tokens.py` estimates tokens before work runs; this measures them afterwards. It follows
the rules in `../references/usage-sources.md`, which were settled by probe (#58):

1. One API call spans several log lines: deduplicate by `message.id` across every file,
   and attribute by the line's `sessionId`, never by filename.
2. Subagent input and cache tokens come from `<session>/subagents/agent-*.jsonl`. Their
   output counts are placeholders, so subagent output is the parent's tool-result figure,
   which covers the subagent's LAST call only, and is marked partial.
3. Background requests appear in no log. They are reported as harness minus log, over the
   windows between two `cost-state` records of the same process.
4. Reconcile only inside such a window; outside one there is nothing to compare against.

A segment is everything from one real user prompt to the next. Meta lines, tool results,
compact summaries and local-command output do not open a segment. A prompt that starts with
`<command-name>/x</command-name>` makes its segment a `/x` command segment.

Usage:
  usage.py report    [--logs DIR | --transcript FILE] [--session ID] [--command /NAME]
                     [--since DATE] [--last N] [--top N] [--price] [--json] [--strict]
  usage.py reconcile [--logs DIR | --transcript FILE] [--session ID] [--json]

`--logs` defaults to this project's `~/.claude/projects/<slug>`. `--last N` keeps the N most
recent prompts. `--price` adds USD from `../references/pricing.json`, always labelled
"estimate (API list price)": the harness's own figures are client-side estimates too, and
billing truth is the Console or the Usage and Cost API. An unknown log record shape is
reported, never skipped; `--strict` turns that report into exit code 3.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

FIELDS = ("input", "cache_write", "cache_read", "output")
LOG_KEYS = {"input": "input_tokens", "cache_write": "cache_creation_input_tokens",
            "cache_read": "cache_read_input_tokens", "output": "output_tokens"}
HARNESS_KEYS = {"input": "inputTokens", "cache_write": "cacheCreationInputTokens",
                "cache_read": "cacheReadInputTokens", "output": "outputTokens"}
KNOWN_TYPES = frozenset({
    "assistant", "user", "system", "attachment", "cost-state", "last-prompt", "atis-latch",
    "mode", "custom-title", "queue-operation", "summary", "file-history-snapshot"})
KNOWN_USAGE_KEYS = frozenset({
    "input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens",
    "cache_creation", "output_tokens_details", "server_tool_use", "service_tier",
    "inference_geo", "iterations", "speed", "fallback_credit"})
NOT_A_PROMPT = ("<local-command-stdout>", "<local-command-stderr>", "<local-command-caveat>")
COMMAND_RE = re.compile(r"<command-name>\s*/?([^<\s]+)\s*</command-name>")
PRICING = Path(__file__).resolve().parent.parent / "references" / "pricing.json"
PRICE_LABEL = "estimate (API list price)"


def model_key(model: str | None) -> str:
    """`claude-haiku-4-5-20251001` and `claude-opus-5-5[1m]` -> their undated family id."""
    m = re.sub(r"\[.*?\]$", "", model or "?")
    return re.sub(r"-\d{8}$", "", m)


def zero() -> dict:
    return dict.fromkeys(FIELDS, 0)


def add(into: dict, more: dict) -> None:
    for k in FIELDS:
        into[k] += more.get(k) or 0


def parse_ts(s: str | None) -> dt.datetime | None:
    if not s:
        return None
    try:
        t = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None
    return t if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)


@dataclass
class Call:
    mid: str
    session: str
    model: str
    ts: str
    tokens: dict           # FIELDS plus cache_write_5m / cache_write_1h
    segment: str
    agent: str | None = None
    speed: str | None = None
    geo: str | None = None
    web_search: int = 0


@dataclass
class Segment:
    key: str
    session: str
    ts: str
    prompt: str
    command: str | None
    calls: list = field(default_factory=list)


@dataclass
class Agent:
    id: str
    agent_type: str
    session: str
    segment: str
    last_output: int | None
    calls: list = field(default_factory=list)


@dataclass
class Window:
    """The span between two cost-state records of one process (same startTime)."""
    file: str
    session: str
    before: dict
    after: dict
    mids: list = field(default_factory=list)


@dataclass
class Corpus:
    files: list = field(default_factory=list)
    calls: dict = field(default_factory=dict)
    segments: dict = field(default_factory=dict)
    agents: dict = field(default_factory=dict)
    tool_results: dict = field(default_factory=dict)
    windows: list = field(default_factory=list)
    cost_states: dict = field(default_factory=dict)  # session -> latest record
    unknown: collections.Counter = field(default_factory=collections.Counter)
    usage_lines: int = 0
    naive: dict = field(default_factory=zero)
    synthetic: int = 0


# --------------------------------------------------------------------------- loading
def default_logs() -> Path:
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()).resolve()
    return Path.home() / ".claude" / "projects" / ("-" + str(root).strip("/").replace("/", "-"))


def rows(path: Path, corpus: Corpus):
    with path.open(encoding="utf-8", errors="replace") as fh:
        for n, line in enumerate(fh, 1):
            if not line.strip():
                continue
            try:
                d = json.loads(line)
            except ValueError:
                corpus.unknown[f"non-JSON line ({path.name}:{n})"] += 1
                continue
            if not isinstance(d, dict):
                corpus.unknown["non-object line"] += 1
                continue
            yield n, d


def prompt_text(d: dict) -> str | None:
    """The text of a real user prompt, or None for meta, tool-result and local-command lines."""
    if d.get("isMeta") or d.get("isCompactSummary") or d.get("isSidechain"):
        return None
    content = (d.get("message") or {}).get("content")
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        blocks = [b for b in content if isinstance(b, dict)]
        if any(b.get("type") == "tool_result" for b in blocks):
            return None
        text = "".join(b.get("text") or "" for b in blocks if b.get("type") == "text")
    else:
        return None
    text = text.strip()
    if not text or text.startswith(NOT_A_PROMPT):
        return None
    return text


def result_chars(block: dict) -> int:
    c = block.get("content")
    if isinstance(c, str):
        return len(c)
    if isinstance(c, list):
        return sum(len(b.get("text") or "") for b in c if isinstance(b, dict))
    return 0


def usage_tokens(u: dict, corpus: Corpus) -> dict:
    t = {k: int(u.get(v) or 0) for k, v in LOG_KEYS.items()}
    cc = u.get("cache_creation") if isinstance(u.get("cache_creation"), dict) else {}
    t["cache_write_5m"] = int(cc.get("ephemeral_5m_input_tokens") or 0)
    t["cache_write_1h"] = int(cc.get("ephemeral_1h_input_tokens") or 0)
    for k in set(u) - KNOWN_USAGE_KEYS:
        corpus.unknown[f"usage key {k!r}"] += 1
    for it in u.get("iterations") or []:
        if isinstance(it, dict) and it.get("type") not in (None, "message"):
            corpus.unknown[f"usage.iterations type {it.get('type')!r}"] += 1
    return t


def read_assistant(d: dict, corpus: Corpus, where: str) -> tuple[str, dict] | None:
    """(message.id, usage tokens) for a usage-bearing assistant line; reports odd shapes."""
    m = d.get("message")
    if not isinstance(m, dict) or not isinstance(m.get("usage"), dict):
        corpus.unknown[f"assistant line without message.usage ({where})"] += 1
        return None
    if m.get("model") == "<synthetic>":
        corpus.synthetic += 1  # a client-made message (an API error, say): no API call
        return None
    if not m.get("id"):
        corpus.unknown[f"assistant usage without message.id ({where})"] += 1
        return None
    t = usage_tokens(m["usage"], corpus)
    corpus.usage_lines += 1
    add(corpus.naive, t)
    return m["id"], t


def make_call(corpus: Corpus, mid: str, d: dict, t: dict, segment: str, agent: str | None) -> Call:
    m, u = d["message"], d["message"]["usage"]
    if mid in corpus.calls:
        old = corpus.calls[mid].tokens
        if any(old[k] != t[k] for k in FIELDS if k != "output") or (agent is None and old["output"] != t["output"]):
            corpus.unknown["duplicate lines of one call disagree on usage"] += 1
        return corpus.calls[mid]
    stu = u.get("server_tool_use") if isinstance(u.get("server_tool_use"), dict) else {}
    c = Call(mid=mid, session=str(d.get("sessionId") or "?"), model=str(m.get("model") or "?"),
             ts=str(d.get("timestamp") or ""), tokens=t, segment=segment, agent=agent,
             speed=u.get("speed"), geo=u.get("inference_geo"),
             web_search=int(stu.get("web_search_requests") or 0))
    corpus.calls[mid] = c
    corpus.segments[segment].calls.append(mid)
    return c


def ensure_segment(corpus: Corpus, key: str, session: str, ts: str, prompt: str, command: str | None) -> str:
    if key not in corpus.segments:
        corpus.segments[key] = Segment(key, session, ts, prompt, command)
    return key


def read_main(corpus: Corpus, path: Path, tool_seg: dict, tool_win: dict, tool_name: dict,
              last_output: dict) -> None:
    seg = None
    prev = None              # previous cost-state in this file
    win_mids, win_tools = [], []
    seen = set()
    for n, d in rows(path, corpus):
        t = d.get("type")
        if t not in KNOWN_TYPES:
            corpus.unknown[f"record type {t!r}"] += 1
            continue
        sid = str(d.get("sessionId") or "?")
        if t == "user":
            text = prompt_text(d)
            if text is not None:
                m = COMMAND_RE.search(text[:400])
                seg = ensure_segment(corpus, str(d.get("uuid") or f"{path.name}:{n}"), sid,
                                     str(d.get("timestamp") or ""), " ".join(text.split())[:70],
                                     m.group(1) if m and text.startswith("<command-") else None)
            content = (d.get("message") or {}).get("content")
            for b in content if isinstance(content, list) else []:
                if isinstance(b, dict) and b.get("type") == "tool_result" and b.get("tool_use_id"):
                    corpus.tool_results.setdefault(b["tool_use_id"], {
                        "chars": result_chars(b), "tool": tool_name.get(b["tool_use_id"], "?"),
                        "session": sid, "segment": seg, "context": "main"})
            r = d.get("toolUseResult")
            if isinstance(r, dict) and r.get("agentId") and isinstance(r.get("usage"), dict):
                last_output[r["agentId"]] = r["usage"].get("output_tokens")
        elif t == "assistant":
            got = read_assistant(d, corpus, path.name)
            if got is None:
                continue
            mid, tok = got
            if seg is None:
                seg = ensure_segment(corpus, f"(before first prompt):{path.name}", sid,
                                     str(d.get("timestamp") or ""), "(before first prompt)", None)
            make_call(corpus, mid, d, tok, seg, None)
            for b in d["message"].get("content") or []:
                if isinstance(b, dict) and b.get("type") == "tool_use" and b.get("id"):
                    tool_name[b["id"]] = b.get("name") or "?"
                    tool_seg.setdefault(b["id"], seg)
                    win_tools.append(b["id"])
            if mid not in seen:
                seen.add(mid)
                win_mids.append(mid)
        elif t == "cost-state":
            corpus.cost_states[sid] = d
            if prev is not None and prev.get("startTime") == d.get("startTime"):
                corpus.windows.append(Window(path.name, sid, prev, d, win_mids))
                for tid in win_tools:
                    tool_win[tid] = len(corpus.windows) - 1
            prev, win_mids, win_tools = d, [], []


def read_agent(corpus: Corpus, path: Path, tool_seg: dict, tool_win: dict, tool_name: dict,
               last_output: dict) -> None:
    aid = path.stem[len("agent-"):]
    meta_path = path.with_name(path.stem + ".meta.json")
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    except ValueError:
        corpus.unknown[f"unreadable subagent meta ({meta_path.name})"] += 1
        meta = {}
    agent = None
    for n, d in rows(path, corpus):
        t = d.get("type")
        if t not in KNOWN_TYPES:
            corpus.unknown[f"record type {t!r} (subagent)"] += 1
            continue
        if t == "user":
            content = (d.get("message") or {}).get("content")
            for b in content if isinstance(content, list) else []:
                if isinstance(b, dict) and b.get("type") == "tool_result" and b.get("tool_use_id"):
                    corpus.tool_results.setdefault(b["tool_use_id"], {
                        "chars": result_chars(b), "tool": tool_name.get(b["tool_use_id"], "?"),
                        "session": str(d.get("sessionId") or "?"),
                        "segment": agent.segment if agent else None,
                        "context": f"subagent:{meta.get('agentType') or '?'}"})
            continue
        if t != "assistant":
            continue
        got = read_assistant(d, corpus, path.name)
        if got is None:
            continue
        mid, tok = got
        if agent is None:
            sid = str(d.get("sessionId") or "?")
            seg = tool_seg.get(meta.get("toolUseId")) or ensure_segment(
                corpus, f"(unattributed subagents):{sid}", sid, str(d.get("timestamp") or ""),
                "(subagent with no parent tool call found)", None)
            agent = corpus.agents[aid] = Agent(aid, str(meta.get("agentType") or "?"), sid, seg,
                                               last_output.get(aid))
        for b in d["message"].get("content") or []:
            if isinstance(b, dict) and b.get("type") == "tool_use" and b.get("id"):
                tool_name[b["id"]] = b.get("name") or "?"
        tok = dict(tok, output_logged=tok["output"], output=0)  # placeholders: never summed
        if mid not in corpus.calls:
            agent.calls.append(mid)
        make_call(corpus, mid, d, tok, agent.segment, aid)
        w = tool_win.get(meta.get("toolUseId"))
        if w is not None and mid not in corpus.windows[w].mids:
            corpus.windows[w].mids.append(mid)


def discover(logs: Path | None = None, transcript: Path | None = None) -> list[Path]:
    if transcript:
        return [transcript] if transcript.is_file() else []
    d = logs or default_logs()
    return sorted(d.glob("*.jsonl"), key=lambda p: p.stat().st_mtime) if d.is_dir() else []


def load(files: list[Path], extra_agents: list[Path] = ()) -> Corpus:
    """Read main logs oldest first (so copied history keeps its original prompt), then subagents."""
    corpus = Corpus(files=[p.name for p in files])
    tool_seg, tool_win, tool_name, last_output = {}, {}, {}, {}
    for p in files:
        read_main(corpus, p, tool_seg, tool_win, tool_name, last_output)
    subs = [s for p in files for s in sorted((p.parent / p.stem / "subagents").glob("agent-*.jsonl"))]
    subs += [Path(x) for x in extra_agents if Path(x).is_file() and Path(x).resolve() not in {s.resolve() for s in subs}]
    for sub in subs:
        read_agent(corpus, sub, tool_seg, tool_win, tool_name, last_output)
    for a in corpus.agents.values():  # a parent result written after its subagent's file was read
        if a.last_output is None:
            a.last_output = last_output.get(a.id)
    return corpus


# --------------------------------------------------------------------------- pricing (#60)
def load_prices(path: Path = PRICING) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def rate_for(prices: dict, model: str) -> dict | None:
    return (prices.get("models") or {}).get(model_key(model))


def price(rate: dict, t: dict, speed: str | None = None, geo: str | None = None, web: int = 0,
          mods: dict | None = None) -> float:
    """USD for one token bundle at list price. Cache writes split by TTL; an unsplit remainder
    is priced as a 1-hour write, which is what Claude Code's main loop requests."""
    r = rate
    prompt = t.get("input", 0) + t.get("cache_write", 0) + t.get("cache_read", 0)
    if r.get("over_100k") and prompt > 100_000:
        r = dict(r, **r["over_100k"])
    scale, out_rate = 1.0, r["output"]
    if speed == "fast" and r.get("fast"):
        scale, out_rate = r["fast"]["input"] / r["input"], r["fast"]["output"]
    w5 = t.get("cache_write_5m", 0)
    w1 = t.get("cache_write", 0) - w5
    usd = (t.get("input", 0) * r["input"] + w5 * r["cache_write_5m"] + w1 * r["cache_write_1h"]
           + t.get("cache_read", 0) * r["cache_read"]) * scale + t.get("output", 0) * out_rate
    usd /= 1e6
    mods = mods or {}
    if geo == "us":
        usd *= mods.get("inference_geo_us", 1.1)
    return usd + web * mods.get("web_search_per_request", 0.01)


def price_call(prices: dict, c: Call) -> float | None:
    rate = rate_for(prices, c.model)
    if rate is None:
        return None
    return price(rate, c.tokens, c.speed, c.geo, c.web_search, prices.get("modifiers"))


# --------------------------------------------------------------------------- selection
def select(corpus: Corpus, session: str | None = None, command: str | None = None,
           since: str | None = None, last: int | None = None) -> list[Segment]:
    segs = sorted(corpus.segments.values(), key=lambda s: s.ts)
    if session:
        segs = [s for s in segs if s.session.startswith(session)]
    if command:
        segs = [s for s in segs if s.command == command.lstrip("/")]
    if since:
        floor = parse_ts(since if "T" in since else since + "T00:00:00+00:00")
        segs = [s for s in segs if (parse_ts(s.ts) or floor) >= floor]
    if last:
        segs = [s for s in segs if s.calls][-last:]
    return segs


# --------------------------------------------------------------------------- reporting
def background(corpus: Corpus, sessions: set) -> dict:
    """Harness minus log, per model, over every cost-state window of the given sessions."""
    out: dict = {}
    for w in corpus.windows:
        if w.session not in sessions:
            continue
        for model, row in window_rows(corpus, w).items():
            if model not in out:
                out[model] = dict(zero(), windows=0)
            out[model]["windows"] += 1
            for k in FIELDS:
                out[model][k] += max(0, row["gap"][k])
    return out


def window_rows(corpus: Corpus, w: Window) -> dict:
    """Per model in one window: harness delta, deduplicated log tokens, and their gap."""
    log: dict = collections.defaultdict(lambda: dict(zero(), cache_write_5m=0, calls=0, subagent_calls=0))
    for mid in w.mids:
        c = corpus.calls[mid]
        row = log[model_key(c.model)]
        add(row, c.tokens)
        row["cache_write_5m"] += c.tokens.get("cache_write_5m", 0)
        row["calls"] += 1
        row["subagent_calls"] += c.agent is not None
    before, after = w.before.get("modelUsage") or {}, w.after.get("modelUsage") or {}
    out = {}
    for model in sorted(set(after) | {m for m in log}, key=str):
        hk = next((k for k in after if model_key(k) == model_key(model)), model)
        now, was = after.get(hk) or {}, before.get(hk) or {}
        delta = {k: (now.get(v) or 0) - (was.get(v) or 0) for k, v in HARNESS_KEYS.items()}
        delta_usd = (now.get("costUSD") or 0) - (was.get("costUSD") or 0)
        delta_web = (now.get("webSearchRequests") or 0) - (was.get("webSearchRequests") or 0)
        lg = log.get(model_key(model)) or dict(zero(), cache_write_5m=0, calls=0, subagent_calls=0)
        if not any(delta.values()) and not lg["calls"]:
            continue
        out[model_key(model)] = {"harness": delta, "harness_usd": delta_usd, "harness_web": delta_web,
                                 "log": {k: lg[k] for k in FIELDS}, "log_cache_write_5m": lg["cache_write_5m"],
                                 "log_calls": lg["calls"], "subagent_calls": lg["subagent_calls"],
                                 "gap": {k: delta[k] - lg[k] for k in FIELDS}}
    return out


def build_report(corpus: Corpus, segs: list, top: int = 5, prices: dict | None = None,
                 filtered: bool = False) -> dict:
    keys = {s.key for s in segs}
    calls = [c for c in corpus.calls.values() if c.segment in keys]
    agents = [a for a in corpus.agents.values() if a.segment in keys]
    unpriced: set = set()

    def usd(cs) -> dict:
        """USD for some calls, or None when nothing is priced: an unknown model is never $0."""
        if prices is None:
            return {"usd": None}
        total, missing = 0.0, 0
        for c in cs:
            p = price_call(prices, c)
            if p is None:
                unpriced.add(model_key(c.model))
                missing += 1
            else:
                total += p
        return {"usd": None if missing == len(cs) else total, "unpriced_calls": missing}

    def tokens(cs) -> dict:
        t = zero()
        for c in cs:
            add(t, c.tokens)
        return t

    by_model: dict = {}
    for c in calls:
        key = (model_key(c.model), "subagent" if c.agent else "main")
        by_model.setdefault(key, []).append(c)
    model_rows = []
    for (model, scope), cs in sorted(by_model.items(), key=lambda kv: -sum(tokens(kv[1]).values())):
        t = tokens(cs)
        row = {"model": model, "scope": scope, "calls": len(cs), "tokens": t, **usd(cs)}
        if scope == "subagent":
            part = sum(a.last_output or 0 for a in agents if any(corpus.calls[m].model == cs[0].model for m in a.calls))
            t["output"] = part
            row["output_partial"] = True
            rate = rate_for(prices, model) if prices else None
            if row["usd"] is not None and rate:
                row["usd"] += part * rate["output"] / 1e6
        model_rows.append(row)
    total = zero()
    for r in model_rows:
        add(total, r["tokens"])
    input_side = total["input"] + total["cache_write"] + total["cache_read"]

    def group(label_of) -> list:
        g: dict = collections.defaultdict(list)
        for s in segs:
            if s.calls:
                g[label_of(s)].extend(corpus.calls[m] for m in s.calls)
        return [{"key": k, "prompts": sum(1 for s in segs if s.calls and label_of(s) == k),
                 "calls": len(v), "tokens": tokens(v), **usd(v)}
                for k, v in sorted(g.items(), key=lambda kv: -sum(tokens(kv[1]).values()))]

    turn_rows = []
    for s in segs:
        if not s.calls:
            continue
        cs = [corpus.calls[m] for m in s.calls]
        t = tokens(cs)
        turn_rows.append({"ts": s.ts, "session": s.session[:8], "command": s.command,
                          "prompt": s.prompt, "calls": len(cs), "tokens": t, **usd(cs),
                          "processed": sum(t.values())})
    turn_rows.sort(key=lambda r: -(r["usd"] if r["usd"] is not None else r["processed"]))

    agent_rows: dict = {}
    for a in agents:
        row = agent_rows.setdefault(a.agent_type, {"key": a.agent_type, "runs": 0, "calls": 0,
                                                   "tokens": zero(), "usd": 0.0 if prices else None})
        cs = [corpus.calls[m] for m in a.calls]
        row["runs"] += 1
        row["calls"] += len(cs)
        add(row["tokens"], tokens(cs))
        row["tokens"]["output"] += a.last_output or 0
        if prices is not None:
            row["usd"] += usd(cs)["usd"] or 0
            rate = rate_for(prices, cs[0].model) if cs else None
            if rate:
                row["usd"] += (a.last_output or 0) * rate["output"] / 1e6

    results = [dict(r, tool_use_id=k) for k, r in corpus.tool_results.items() if r["segment"] in keys]
    results.sort(key=lambda r: -r["chars"])
    sessions = {s.session for s in segs}
    report = {
        "files": corpus.files,
        "counts": {"sessions": len(sessions), "prompts": sum(1 for s in segs if s.calls),
                   "calls": len(calls), "usage_lines": corpus.usage_lines, "subagent_runs": len(agents)},
        "naive_line_sum": corpus.naive,
        "by_model": model_rows,
        "totals": total,
        "cache_read_share": total["cache_read"] / input_side if input_side else 0.0,
        "by_session": group(lambda s: s.session[:8]),
        "by_command": group(lambda s: "/" + s.command if s.command else "(plain prompt)"),
        "by_subagent_type": sorted(agent_rows.values(), key=lambda r: -sum(r["tokens"].values())),
        "top_prompts": turn_rows[:top],
        "top_tool_results": [{"chars": r["chars"], "approx_tokens": r["chars"] // 4, "tool": r["tool"],
                              "context": r["context"], "session": r["session"][:8]} for r in results[:top]],
        "unknown_shapes": dict(corpus.unknown),
        "synthetic_messages": corpus.synthetic,
    }
    if filtered:
        report["background"] = None
    else:
        bg = background(corpus, sessions)
        if prices is not None:
            for model, row in bg.items():
                rate = rate_for(prices, model)
                row["usd"] = price(rate, row) if rate else None
                if rate is None:
                    unpriced.add(model)
        report["background"] = bg
    if prices is not None:
        report["pricing"] = {"label": PRICE_LABEL, "source": prices.get("source"),
                             "checked": prices.get("checked"), "unpriced_models": sorted(unpriced)}
        report["log_usd"] = sum(r["usd"] or 0 for r in model_rows)
        report["total_usd"] = report["log_usd"] + sum(
            (r.get("usd") or 0) for r in (report["background"] or {}).values())
    return report


def reconcile(corpus: Corpus, sessions: set | None = None, prices: dict | None = None) -> dict:
    """Per cost-state window and model: does the log stay within the harness, and does the
    price table reproduce the harness's own costUSD from the harness's own tokens?"""
    out, failures = [], 0
    tol = (prices or {}).get("reconcile_tolerance_usd", 0.001)
    for i, w in enumerate(corpus.windows):
        if sessions and w.session not in sessions:
            continue
        for model, r in window_rows(corpus, w).items():
            over = [k for k in FIELDS if r["gap"][k] < 0]
            row = {"window": i, "session": w.session[:8], "model": model, "log_calls": r["log_calls"],
                   "subagent_calls": r["subagent_calls"], "harness": r["harness"], "log": r["log"],
                   "gap": r["gap"], "log_exceeds_harness": over}
            gap_names = []
            if any(r["gap"][k] > 0 for k in FIELDS):
                gap_names.append("background requests (in no log)")
                if r["subagent_calls"]:
                    gap_names.append("subagent output beyond placeholders")
            row["gap_named"] = gap_names
            if prices is not None:
                rate = rate_for(prices, model)
                row["harness_usd"] = r["harness_usd"]
                if rate is None:
                    row["table_usd"] = row["log_usd"] = None
                    row["table_matches_harness"] = None
                else:
                    h = dict(r["harness"], cache_write_5m=min(r["log_cache_write_5m"], r["harness"]["cache_write"]))
                    row["table_usd"] = price(rate, h, web=r["harness_web"], mods=prices.get("modifiers"))
                    row["log_usd"] = sum(price_call(prices, corpus.calls[m]) or 0 for m in w.mids
                                         if model_key(corpus.calls[m].model) == model)
                    row["table_matches_harness"] = abs(row["table_usd"] - r["harness_usd"]) <= tol
                    failures += not row["table_matches_harness"]
            failures += bool(over)
            out.append(row)
    return {"windows": out, "failures": failures, "tolerance": {
        "tokens": "the log may never exceed the harness on any field; a positive gap is named",
        "usd": tol}}


# --------------------------------------------------------------------------- spend log (#61)
def spend_records(corpus: Corpus, session: str, prices: dict | None = None, event: str | None = None) -> list:
    """What `.claude/spend/log.jsonl` keeps: one compact line for the session and one per
    subagent run, keyed by (kind, id). Token counts and command names only, no prompt text."""
    segs = [s for s in select(corpus, session=session) if s.session == session]
    rep = build_report(corpus, segs, top=0, prices=prices)
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    stamps = sorted(corpus.calls[m].ts for s in segs for m in s.calls if corpus.calls[m].ts)
    cs = corpus.cost_states.get(session) or {}
    rec = {"kind": "session", "id": session, "updated": now, "event": event,
           "first": stamps[0] if stamps else None, "last": stamps[-1] if stamps else None,
           "prompts": rep["counts"]["prompts"], "calls": rep["counts"]["calls"],
           "subagent_runs": rep["counts"]["subagent_runs"], "tokens": rep["totals"],
           "by_model": {m["model"] + (" (subagent)" if m["scope"] == "subagent" else ""): dict(m["tokens"], calls=m["calls"])
                        for m in rep["by_model"]},
           "commands": {g["key"]: g["prompts"] for g in rep["by_command"] if g["key"] != "(plain prompt)"},
           "background": {m: {k: b[k] for k in FIELDS} for m, b in (rep["background"] or {}).items()},
           "harness_usd_at_last_idle": cs.get("totalCostUSD"),
           "unknown_shapes": sum(rep["unknown_shapes"].values())}
    if prices is not None:
        rec.update(est_usd=round(rep["total_usd"], 4), usd_label=PRICE_LABEL,
                   unpriced=rep["pricing"]["unpriced_models"])
    out = [rec]
    for a in corpus.agents.values():
        if a.session != session:
            continue
        calls = [corpus.calls[m] for m in a.calls]
        t = zero()
        for c in calls:
            add(t, c.tokens)
        t["output"] = a.last_output
        row = {"kind": "subagent", "id": a.id, "session": session, "updated": now, "event": event,
               "agent_type": a.agent_type, "model": model_key(calls[0].model) if calls else None,
               "calls": len(calls), "tokens": t,
               "output_note": "last call only; subagent logs hold placeholders" if a.last_output is not None
               else "pending: the parent records it when the subagent returns"}
        if prices is not None and calls:
            rate = rate_for(prices, calls[0].model)
            row["est_usd"] = None if rate is None else round(
                sum(price_call(prices, c) or 0 for c in calls) + (a.last_output or 0) * rate["output"] / 1e6, 4)
        out.append(row)
    return out


# --------------------------------------------------------------------------- text output
def h(n: float | int | None) -> str:
    if n is None:
        return "-"
    n = float(n)
    for unit, size in (("B", 1e9), ("M", 1e6), ("K", 1e3)):
        if abs(n) >= size:
            return f"{n / size:.1f}{unit}"
    return f"{n:.0f}"


def money(x: float | None) -> str:
    return "-" if x is None else f"${x:,.2f}"


def table(headers: list, body: list) -> list:
    widths = [max(len(str(r[i])) for r in [headers] + body) for i in range(len(headers))]
    fmt = lambda r: "  ".join(str(c).ljust(widths[i]) if i == 0 else str(c).rjust(widths[i]) for i, c in enumerate(r))
    return [fmt(headers)] + [fmt(r) for r in body]


def render(r: dict) -> str:
    priced = "pricing" in r
    c = r["counts"]
    tok_head = ["input", "cache wr", "cache rd", "output"] + (["est. USD"] if priced else [])
    tk = lambda t, u=None, miss=0: [h(t["input"]), h(t["cache_write"]), h(t["cache_read"]), h(t["output"])] + (
        [("UNPRICED" if u is None else money(u) + ("+?" if miss else ""))] if priced else [])
    lines = [f"Spend from {len(r['files'])} log file(s): {c['sessions']} session(s), {c['prompts']} prompt(s), "
             f"{c['calls']} calls ({c['usage_lines']} usage lines, deduplicated by message.id), "
             f"{c['subagent_runs']} subagent run(s)."]
    if priced:
        p = r["pricing"]
        lines.append(f"Dollar figures are an {p['label']}, priced from {p['source']} (checked {p['checked']}).")
        if p["unpriced_models"]:
            lines.append(f"UNPRICED (not in the table, not counted as $0): {', '.join(p['unpriced_models'])}")
    if r["unknown_shapes"]:
        lines.append("UNKNOWN LOG SHAPES (reported, not skipped): " +
                     "; ".join(f"{k} x{v}" for k, v in sorted(r["unknown_shapes"].items())))
    lines += ["", "Tokens by model (logs)"]
    body = [[f"{m['model']} ({m['scope']})", m["calls"]] + tk(m["tokens"], m["usd"], m.get("unpriced_calls")) for m in r["by_model"]]
    body.append(["total", c["calls"]] + tk(r["totals"], r.get("log_usd"), r.get("pricing", {}).get("unpriced_models")))
    lines += table(["model", "calls"] + tok_head, body)
    if any(m.get("output_partial") for m in r["by_model"]):
        lines.append("  subagent output covers each run's LAST call only; subagent logs hold placeholders")
    lines.append(f"Cache-read share of input-side tokens: {r['cache_read_share']:.1%}")
    bg = r["background"]
    lines += ["", "Background requests: in the harness, in no log (cost-state windows only)"]
    if bg is None:
        lines.append("  n/a under a prompt-level filter (windows span whole idle-to-idle periods)")
    elif not bg:
        lines.append("  no complete cost-state window in scope, so nothing to compare against")
    else:
        lines += table(["model", "windows"] + tok_head,
                       [[m, b["windows"]] + tk(b, b.get("usd")) for m, b in bg.items()])
        if priced:
            lines.append(f"Estimated total, logs plus background: {money(r['total_usd'])}")
    for title, key, first in (("By session", "by_session", "session"), ("By command", "by_command", "command")):
        lines += ["", title]
        lines += table([first, "prompts", "calls"] + tok_head,
                       [[g["key"], g["prompts"], g["calls"]] + tk(g["tokens"], g["usd"], g.get("unpriced_calls")) for g in r[key]])
    if r["by_subagent_type"]:
        lines += ["", "By subagent type (output = last call only)"]
        lines += table(["agent type", "runs", "calls"] + tok_head,
                       [[g["key"], g["runs"], g["calls"]] + tk(g["tokens"], g["usd"]) for g in r["by_subagent_type"]])
    lines += ["", f"Most expensive prompts (by {'est. USD' if priced else 'tokens processed'})"]
    lines += table(["when", "session", "prompt", "calls"] + tok_head,
                   [[t["ts"][:16], t["session"], ("/" + t["command"]) if t["command"] else t["prompt"][:40],
                     t["calls"]] + tk(t["tokens"], t["usd"], t.get("unpriced_calls")) for t in r["top_prompts"]])
    lines += ["", "Largest tool results fed into context (~tokens = chars/4)"]
    lines += table(["tool", "context", "session", "chars", "~tokens"],
                   [[t["tool"], t["context"], t["session"], f"{t['chars']:,}", h(t["approx_tokens"])]
                    for t in r["top_tool_results"]])
    return "\n".join(lines)


def render_reconcile(r: dict) -> str:
    lines = [f"Reconciliation over {len(r['windows'])} window/model row(s); "
             f"tolerance: {r['tolerance']['tokens']}; USD within ${r['tolerance']['usd']}."]
    for w in r["windows"]:
        g = w["gap"]
        status = "LOG EXCEEDS HARNESS on " + ",".join(w["log_exceeds_harness"]) if w["log_exceeds_harness"] else (
            "exact" if not any(g.values()) else "gap: " + " + ".join(w["gap_named"]))
        line = (f"[{w['window']:>2}] {w['session']} {w['model']:<22} calls {w['log_calls']:>3}  "
                f"harness-log  in {g['input']:>6} wr {g['cache_write']:>7} rd {g['cache_read']:>8} "
                f"out {g['output']:>5}  {status}")
        if "table_usd" in w:
            if w["table_usd"] is None:
                line += "  | UNPRICED model"
            else:
                ok = "table=harness" if w["table_matches_harness"] else "TABLE != HARNESS"
                line += (f"  | harness ${w['harness_usd']:.4f} table ${w['table_usd']:.4f} ({ok}); "
                         f"log ${w['log_usd']:.4f}")
        lines.append(line)
    lines.append(f"\n{r['failures']} failure(s).")
    return "\n".join(lines)


def main(argv: list | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=("report", "reconcile"))
    src = ap.add_mutually_exclusive_group()
    src.add_argument("--logs", type=Path)
    src.add_argument("--transcript", type=Path)
    ap.add_argument("--session")
    ap.add_argument("--command")
    ap.add_argument("--since")
    ap.add_argument("--last", type=int)
    ap.add_argument("--top", type=int, default=5)
    ap.add_argument("--price", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict", action="store_true")
    a = ap.parse_args(argv)
    files = discover(a.logs, a.transcript)
    if not files:
        print(f"no session logs at {a.transcript or a.logs or default_logs()}")
        return 2
    corpus = load(files)
    if a.cmd == "reconcile":
        sessions = {s for s in {c.session for c in corpus.calls.values()} if not a.session or s.startswith(a.session)}
        r = reconcile(corpus, sessions, load_prices() if PRICING.exists() else None)
        print(json.dumps(r, indent=1) if a.json else render_reconcile(r))
        return 1 if r["failures"] else 0
    segs = select(corpus, a.session, a.command, a.since, a.last)
    r = build_report(corpus, segs, a.top, load_prices() if a.price else None,
                     filtered=bool(a.command or a.since or a.last))
    print(json.dumps(r, indent=1) if a.json else render(r))
    return 3 if a.strict and r["unknown_shapes"] else 0


if __name__ == "__main__":
    sys.exit(main())
