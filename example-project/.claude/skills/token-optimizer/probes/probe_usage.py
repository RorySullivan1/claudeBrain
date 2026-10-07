#!/usr/bin/env python3
"""Probe usage.py (#59) and its pricing (#60) on planted fixture logs, then on real ones.

    python3 probe_usage.py --selftest   # every rule on fixtures, with negative controls
    python3 probe_usage.py --real       # reconcile this project's own logs (needs ~/.claude)

The fixtures plant each shape the parser claims to handle: split lines of one call, copied
history, meta / tool-result / compact / local-command lines, a slash command followed by a
plain prompt, a subagent with placeholder output, a hidden background call inside a harness
window, an unknown record type and usage key, and an unpriced model. Controls are cases that
must NOT trip: a clean log reports no unknown shapes, an exact window shows no gap, a correct
table matches. A break that keeps a check green means the check cannot see what it claims.
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import usage  # noqa: E402

OPUS, HAIKU = "claude-opus-5-5", "claude-haiku-4-5-20251001"


def asst(mid, sid, model, u, ts, tools=(), cc5=0, **extra):
    inp, wr, rd, out = u
    d = {"type": "assistant", "sessionId": sid, "timestamp": ts, "uuid": f"a-{mid}-{ts}",
         "message": {"id": mid, "model": model, "content": [
             {"type": "tool_use", "id": t, "name": n} for t, n in tools],
             "usage": {"input_tokens": inp, "cache_creation_input_tokens": wr,
                       "cache_read_input_tokens": rd, "output_tokens": out,
                       "cache_creation": {"ephemeral_5m_input_tokens": cc5,
                                          "ephemeral_1h_input_tokens": wr - cc5},
                       "speed": "standard", "inference_geo": "not_available"}}}
    d["message"]["usage"].update(extra)
    return d


def user(uuid, sid, text, ts, **flags):
    return dict({"type": "user", "uuid": uuid, "sessionId": sid, "timestamp": ts,
                 "message": {"role": "user", "content": text}}, **flags)


def result(sid, tool_id, chars, ts, agent=None, out=None):
    d = {"type": "user", "sessionId": sid, "timestamp": ts, "uuid": f"r-{tool_id}",
         "message": {"role": "user", "content": [
             {"type": "tool_result", "tool_use_id": tool_id, "content": "x" * chars}]}}
    if agent:
        d["toolUseResult"] = {"agentId": agent, "usage": {"output_tokens": out}}
    return d


def cost(start, per_model):
    return {"type": "cost-state", "startTime": start, "sessionId": "NEW",
            "totalCostUSD": sum(v[4] if len(v) > 4 else 0 for v in per_model.values()),
            "modelUsage": {m: {"inputTokens": v[0], "cacheCreationInputTokens": v[1],
                               "cacheReadInputTokens": v[2], "outputTokens": v[3],
                               "costUSD": v[4] if len(v) > 4 else 0, "webSearchRequests": 0}
                           for m, v in per_model.items()}}


def opus_usd(i, w, r, o, w5=0):
    return (i * 4 + w5 * 5 + (w - w5) * 8 + r * 0.2 + o * 20) / 1e6


def haiku_usd(i, w, r, o, w5=0):
    return (i * 1 + w5 * 1.25 + (w - w5) * 2 + r * 0.1 + o * 5) / 1e6


def build(tmp: Path, extra_lines=(), break_harness=False) -> Path:
    """OLD: one prompt, one call split over 3 lines. NEW: copied OLD history, then /cmd, a plain
    prompt that spawns a subagent, and two harness windows (one with a hidden call)."""
    old = [user("p0", "OLD", "first question", "2026-10-01T10:00:00Z"),
           asst("m0", "OLD", OPUS, (5, 1000, 0, 50), "2026-10-01T10:00:01Z"),
           asst("m0", "OLD", OPUS, (5, 1000, 0, 50), "2026-10-01T10:00:01Z"),
           asst("m0", "OLD", OPUS, (5, 1000, 0, 50), "2026-10-01T10:00:01Z")]
    # window 1 (after record A): /cmd + its tool loop, plus one hidden background call
    w1 = [(2, 100, 2000, 40), (1, 50, 3000, 30)]
    hidden = (506, 0, 3000, 10)
    # window 2: plain prompt with an Agent call; the subagent's calls belong here too
    w2 = [(3, 200, 4000, 60)]
    sub = [(1, 300, 0, 3), (1, 0, 300, 2)]   # output placeholders: 3 and 2
    real_last_sub_out = 142
    sub_real_out = 90 + real_last_sub_out     # harness sees the real output of both calls

    def tot(rows):
        return tuple(sum(r[k] for r in rows) for k in range(4))

    o1 = tot(w1 + [hidden])
    o2 = tot(w2)
    s2 = tot(sub)
    harness_a = {OPUS: (0, 0, 0, 0, 0.0)}
    harness_b = {OPUS: o1 + (opus_usd(*o1),)}
    o12 = tuple(a + b for a, b in zip(o1, o2))
    if break_harness:  # a harness that saw LESS than the log: the parser must flag it
        o12 = (o12[0], o12[1], o12[2] - 1000, o12[3])
    s_harness = (s2[0], s2[1], s2[2], sub_real_out)
    harness_c = {OPUS: o12 + (opus_usd(*o12),),
                 HAIKU: s_harness + (haiku_usd(*s_harness, w5=300),)}
    new = old + [
        user("p1", "NEW", "<command-name>/cmd</command-name>\n<command-args>go</command-args>", "2026-10-02T09:00:00Z"),
        cost(1, harness_a),
        asst("m1", "NEW", OPUS, w1[0], "2026-10-02T09:00:01Z", tools=[("t1", "Bash")]),
        asst("m1", "NEW", OPUS, w1[0], "2026-10-02T09:00:01Z", tools=[("t1", "Bash")]),
        result("NEW", "t1", 8000, "2026-10-02T09:00:02Z"),
        user("meta1", "NEW", "Stop hook feedback: keep going", "2026-10-02T09:00:03Z", isMeta=True),
        user("loc1", "NEW", "<local-command-stdout>ok</local-command-stdout>", "2026-10-02T09:00:03Z"),
        user("cmp1", "NEW", "This session is being continued...", "2026-10-02T09:00:03Z", isCompactSummary=True),
        asst("m2", "NEW", OPUS, w1[1], "2026-10-02T09:00:04Z"),
        cost(1, harness_b),
        user("p2", "NEW", "now a plain prompt", "2026-10-02T09:05:00Z"),
        asst("m3", "NEW", OPUS, w2[0], "2026-10-02T09:05:01Z", tools=[("tA", "Agent")]),
        result("NEW", "tA", 500, "2026-10-02T09:05:30Z", agent="sub1", out=real_last_sub_out),
        cost(1, harness_c),
        cost(2, {OPUS: (1, 0, 0, 1, opus_usd(1, 0, 0, 1))}),  # a new process: no window spans it
        *extra_lines,
    ]
    for name, lines in (("OLD.jsonl", old), ("NEW.jsonl", new)):
        (tmp / name).write_text("\n".join(json.dumps(x) for x in lines) + "\n")
    import os
    os.utime(tmp / "OLD.jsonl", (1, 1))  # oldest first: copied history keeps its original prompt
    sd = tmp / "NEW" / "subagents"
    sd.mkdir(parents=True, exist_ok=True)
    (sd / "agent-sub1.jsonl").write_text("\n".join(json.dumps(dict(
        asst(f"s{i}", "NEW", HAIKU, u, f"2026-10-02T09:05:1{i}Z", cc5=u[1]), isSidechain=True, agentId="sub1"))
        for i, u in enumerate(sub)) + "\n")
    (sd / "agent-sub1.meta.json").write_text(json.dumps({"agentType": "Explore", "toolUseId": "tA", "model": "haiku"}))
    return tmp


def header_order(text: str) -> bool:
    head = next((ln for ln in text.splitlines() if ln.startswith("model ")), "")
    cols = [head.find(c) for c in ("input", "cache wr", "cache rd", "output", "est. USD")]
    return -1 not in cols and cols == sorted(cols)


def run(tmp: Path, *args) -> tuple[int, str]:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = usage.main(list(args) + ["--logs", str(tmp)])
    return code, buf.getvalue()


def selftest() -> int:
    checks = {}
    with tempfile.TemporaryDirectory() as t:
        tmp = build(Path(t))
        c = usage.load(usage.discover(tmp))
        rep = usage.build_report(c, usage.select(c), top=10)
        naive_out = c.naive["output"]
        # --- #59: deduplication, with the naive line sum as the negative control
        checks["split lines of one call count once (4 main + 2 subagent calls)"] = (
            rep["counts"]["calls"] == 6 and sum(p["calls"] for p in rep["top_prompts"]) == 6
            and rep["totals"]["cache_write"] == 1000 + 100 + 50 + 200 + 300)
        checks["[control] a naive line sum disagrees with the parser"] = (
            c.usage_lines == 12 and naive_out != rep["totals"]["output"])
        checks["copied history is attributed by sessionId, not filename"] = (
            c.calls["m0"].session == "OLD" and {g["key"] for g in rep["by_session"]} == {"OLD", "NEW"})
        # --- segments
        by_cmd = {g["key"]: g for g in rep["by_command"]}
        checks["meta, tool-result, compact and local-command lines open no segment"] = (
            sorted(s.key for s in c.segments.values()) == ["p0", "p1", "p2"])
        checks["a slash-command segment ends at the next real prompt"] = (
            by_cmd.get("/cmd", {}).get("calls") == 2 and c.calls["m3"].segment == "p2")
        checks["the subagent belongs to the prompt that spawned it"] = c.agents["sub1"].segment == "p2"
        # --- subagent output: placeholders never summed, partial last-call output used
        sub_row = next(r for r in rep["by_model"] if r["scope"] == "subagent")
        checks["subagent output is the parent's last-call figure, not placeholder sums"] = (
            sub_row["tokens"]["output"] == 142 and sub_row.get("output_partial")
            and rep["by_subagent_type"][0]["tokens"]["output"] == 142
            and rep["totals"]["output"] == 50 + 40 + 30 + 60 + 142)
        checks["[control] a new startTime opens no window (2 windows, not 3)"] = len(c.windows) == 2
        # --- background: harness minus log inside windows, subagent calls included
        bg = rep["background"]
        checks["a hidden call shows as background, in no log"] = (
            bg.get("claude-opus-5-5", {}).get("cache_read") == 3000 and bg["claude-opus-5-5"]["input"] == 506)
        checks["[control] subagent input and cache are in the window: no false background"] = (
            bg.get("claude-haiku-4-5", {}).get("cache_write") == 0 and bg["claude-haiku-4-5"]["cache_read"] == 0)
        checks["the largest tool result is reported with its tool name"] = (
            rep["top_tool_results"][0]["tool"] == "Bash" and rep["top_tool_results"][0]["chars"] == 8000)
        checks["[control] a clean log reports no unknown shapes"] = rep["unknown_shapes"] == {}
        # --- filters
        checks["--command keeps only that command's prompts"] = (
            usage.build_report(c, usage.select(c, command="/cmd"))["counts"]["calls"] == 2)
        checks["--last 1 keeps the most recent prompt (with its subagent)"] = (
            usage.build_report(c, usage.select(c, last=1))["counts"]["calls"] == 3)

        # --- #60: pricing and reconciliation
        prices = usage.load_prices()
        rec = usage.reconcile(c, prices=prices)
        checks["the table reproduces the harness's costUSD in every window"] = (
            rec["windows"] and all(w["table_matches_harness"] for w in rec["windows"]) and rec["failures"] == 0)
        bad = json.loads(json.dumps(prices))
        bad["models"]["claude-opus-5-5"]["cache_read"] = 0.5
        checks["[break] a wrong price row fails reconciliation"] = usage.reconcile(c, prices=bad)["failures"] > 0
        r = prices["models"]["claude-opus-5-5"]
        checks["price: 1M uncached input on Opus 5.5 is $4"] = abs(usage.price(r, {"input": 10**6}) - 4) < 1e-9
        checks["price: cache writes split 5m/1h; 1M cache reads on Opus 5.5 = $0.20"] = abs(usage.price(
            r, {"cache_write": 2 * 10**6, "cache_write_5m": 10**6, "cache_read": 10**6}) - (5 + 8 + 0.2)) < 1e-9
        checks["price: fast mode scales input-side and swaps output rate"] = abs(usage.price(
            r, {"input": 10**6, "output": 10**6}, speed="fast") - (8 + 40)) < 1e-9
        checks["price: inference_geo us is 1.1x; a web search is $0.01"] = abs(usage.price(
            r, {"input": 10**6}, geo="us", web=1, mods=prices["modifiers"]) - (4.4 + 0.01)) < 1e-9
        hk = prices["models"]["claude-haiku-5-5"]
        checks["price: Haiku 5.5 over 100K prompt tokens uses the higher tier"] = (
            abs(usage.price(hk, {"input": 200_000}) - 0.1) < 1e-9 and abs(usage.price(hk, {"input": 100_000}) - 0.01) < 1e-9)
        code, text = run(tmp, "report", "--price")
        checks["dollars are labelled 'estimate (API list price)' and tokens come first"] = (
            "estimate (API list price)" in text and header_order(text))

    with tempfile.TemporaryDirectory() as t:
        odd = [{"type": "brand-new-record", "sessionId": "NEW"},
               asst("m9", "NEW", "claude-unknown-9", (1, 0, 0, 1), "2026-10-02T10:00:00Z", new_token_kind=5)]
        tmp = build(Path(t), extra_lines=odd)
        c = usage.load(usage.discover(tmp))
        rep = usage.build_report(c, usage.select(c), prices=usage.load_prices())
        checks["an unknown record type and usage key are reported, not skipped"] = (
            "record type 'brand-new-record'" in rep["unknown_shapes"] and "usage key 'new_token_kind'" in rep["unknown_shapes"])
        checks["--strict turns unknown shapes into exit 3"] = run(tmp, "report", "--strict")[0] == 3
        unk = next(r for r in rep["by_model"] if r["model"] == "claude-unknown-9")
        checks["an unknown model is UNPRICED, never $0"] = (
            unk["usd"] is None and unk["unpriced_calls"] == 1 and "claude-unknown-9" in rep["pricing"]["unpriced_models"]
            and "UNPRICED" in usage.render(rep))

    with tempfile.TemporaryDirectory() as t:
        tmp = build(Path(t), break_harness=True)
        rec = usage.reconcile(usage.load(usage.discover(tmp)), prices=usage.load_prices())
        checks["[break] a log that exceeds the harness is flagged, not hidden"] = any(
            w["log_exceeds_harness"] for w in rec["windows"]) and rec["failures"] > 0

    for name, ok in checks.items():
        print(f"{'PASS' if ok else 'FAIL'}  {name}")
    failed = sum(not ok for ok in checks.values())
    print(f"\n{len(checks) - failed}/{len(checks)} passed")
    return 1 if failed else 0


def real() -> int:
    files = usage.discover()
    if not files:
        print(f"no logs at {usage.default_logs()}")
        return 2
    c = usage.load(files)
    rec = usage.reconcile(c, prices=usage.load_prices())
    print(usage.render_reconcile(rec))
    print(f"unknown shapes: {dict(c.unknown) or 'none'}")
    return 1 if rec["failures"] else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--real", action="store_true")
    return selftest() if ap.parse_args().selftest else real()


if __name__ == "__main__":
    sys.exit(main())
