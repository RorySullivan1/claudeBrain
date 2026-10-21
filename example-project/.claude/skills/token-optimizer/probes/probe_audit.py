#!/usr/bin/env python3
"""Probe audit.py (#64) and the spend-levers catalog (#63) on planted profiles, then on real logs.

    python3 probe_audit.py --selftest   # planted signals, a clean control, the cap, drift, breaks
    python3 probe_audit.py --real [--logs DIR]   # audit this project's own logs (needs ~/.claude)

The fixtures plant each signal a rule claims to see: rebuilds after idle gaps, a rebuild after
a model switch, an edit to CLAUDE.md that keeps the cache, a Bash result past the filter's cap,
and report-level profiles for the TTL, model, effort and fan-out rules. The control is a clean
session that must report no material finding. Each break disables one mechanism and must turn
a check red: a break that stays green means the check cannot see what it claims.
"""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import json
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
import audit  # noqa: E402
import usage  # noqa: E402

CATALOG = HERE.parent / "references" / "spend-levers.md"
AGENT = HERE.parents[2] / "agents" / "spend-auditor.md"
COMMAND = HERE.parents[2] / "commands" / "spend-audit.md"
OPUS, SONNET = "claude-opus-5-5", "claude-sonnet-5-5"
SID = "aaaaaaaa-0000-0000-0000-000000000001"
T0 = dt.datetime(2026, 10, 1, 9, 0, tzinfo=dt.timezone.utc)
FIELDS = ("Signal", "Mechanism", "Source", "Direction", "Trade-off", "Apply", "Measured")


def ts(seconds: float) -> str:
    return (T0 + dt.timedelta(seconds=seconds)).isoformat().replace("+00:00", "Z")


class Log:
    """A main-session transcript built call by call, with the context growing as it would."""

    def __init__(self, ttl: str = "5m"):
        self.lines, self.t, self.n, self.ttl, self.context = [], 0.0, 0, ttl, 0

    def prompt(self, text: str = "do the next thing", gap: float = 20):
        self.t += gap
        self.lines.append({"type": "user", "uuid": f"u{len(self.lines)}", "sessionId": SID,
                           "timestamp": ts(self.t), "message": {"role": "user", "content": text}})

    def call(self, new: int = 600, gap: float = 20, model: str = OPUS, rebuild: bool = False,
             tools: tuple = (), out: int = 300, prefix: int = 30_000):
        """One API call: reads the cached context and writes `new`, or rewrites it all on a rebuild."""
        self.t += gap
        self.n += 1
        if self.context == 0:
            write, read = prefix, 0
        elif rebuild:
            write, read = self.context - prefix + new, prefix
        else:
            write, read = new, self.context
        self.context = read + write
        w5 = write if self.ttl == "5m" else 0
        self.lines.append({"type": "assistant", "sessionId": SID, "timestamp": ts(self.t), "uuid": f"a{self.n}",
                           "message": {"id": f"msg_{self.n}", "model": model, "content": list(tools),
                                       "usage": {"input_tokens": 2, "cache_creation_input_tokens": write,
                                                 "cache_read_input_tokens": read, "output_tokens": out,
                                                 "cache_creation": {"ephemeral_5m_input_tokens": w5,
                                                                    "ephemeral_1h_input_tokens": write - w5}}}})

    def result(self, tool_id: str, chars: int):
        self.lines.append({"type": "user", "sessionId": SID, "timestamp": ts(self.t), "uuid": f"r{tool_id}",
                           "message": {"role": "user", "content": [
                               {"type": "tool_result", "tool_use_id": tool_id, "content": "x" * chars}]}})

    def report(self, tmp: Path, name: str) -> dict:
        d = tmp / name
        d.mkdir()
        (d / f"{SID}.jsonl").write_text("\n".join(json.dumps(x) for x in self.lines) + "\n", encoding="utf-8")
        corpus = usage.load(usage.discover(d))
        return usage.build_report(corpus, usage.select(corpus), audit.TOP_RESULTS, usage.load_prices())


def clean(ttl: str = "5m", calls: int = 120, new: int = 600, model: str = OPUS) -> Log:
    log = Log(ttl)
    log.prompt()
    for i in range(calls):
        if i % 10 == 9:
            log.prompt()
        log.call(new=new, model=model)
    return log


def idle(n_breaks: int = 3) -> Log:
    log = Log("1h")
    log.prompt()
    for i in range(150):
        if i in (40, 80, 120)[:n_breaks]:
            log.prompt(gap=2 * 3600)
            log.call(rebuild=True, new=3_000)
        else:
            log.call(new=3_000)
    return log


def switched() -> Log:
    log = clean(calls=120, new=1_500, model=SONNET)
    edit = {"type": "tool_use", "id": "t-edit", "name": "Edit",
            "input": {"file_path": "/repo/CLAUDE.md", "old_string": "a", "new_string": "b"}}
    log.call(tools=(edit,), model=SONNET)
    log.result("t-edit", 40)
    log.call(model=SONNET)                       # the docs: the edit keeps the cache
    log.prompt()
    log.call(model=OPUS, rebuild=True)           # a model switch rebuilds
    for _ in range(40):
        log.call()
    bash = {"type": "tool_use", "id": "t-bash", "name": "Bash", "input": {"command": "cat big.log"}}
    log.call(tools=(bash,))
    log.result("t-bash", 40_000)
    for _ in range(80):
        log.call()
    return log


def levers_of(a: dict) -> list:
    return [f["lever"] for f in a["findings"]]


def check_texts(a: dict, lever: str) -> list:
    return [c["check"] for c in a["checks"] if c["lever"] == lever]


def catalog_sections() -> dict:
    text = CATALOG.read_text(encoding="utf-8")
    out = {}
    for m in re.finditer(r"^### `([a-z0-9-]+)`\n(.*?)(?=^### |^## |\Z)", text, re.M | re.S):
        out[m.group(1)] = {f: (re.search(rf"^- \*\*{re.escape(f)}:\*\*\s*(.+)$", m.group(2), re.M) or [None, ""])[1]
                           for f in FIELDS}
    return out


def unmeasured(text: str) -> str:
    """The catalog with every Measured field reset, so a fixture plants exactly the outcomes it names."""
    return re.sub(r"^- \*\*Measured:\*\*.*\n(?:  - `.*\n)*", "- **Measured:** none yet.\n", text, flags=re.M)


def report_profile(base: dict, **patch) -> dict:
    r = copy.deepcopy(base)
    for k, v in patch.items():
        r[k] = v
    return r


def selftest() -> int:
    checks: dict = {}
    prices = usage.load_prices()
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        r_clean = clean().report(tmp, "clean")
        r_idle = idle().report(tmp, "idle")
        r_switch = switched().report(tmp, "switch")
        a_clean, a_idle, a_switch = (audit.audit(r, prices) for r in (r_clean, r_idle, r_switch))

        checks["control: a clean session has no material finding"] = not a_clean["findings"]
        checks["control: its render says 'No material finding.'"] = "No material finding." in audit.render(a_clean)
        checks["control: every lever still reports a check on a clean profile"] = (
            {c["lever"] for c in a_clean["checks"]} == set(audit.RULES))
        checks["planted idle rebuilds name idle-rebuild, ranked first"] = levers_of(a_idle)[:1] == ["idle-rebuild"]
        checks["usage.py counts the 3 idle rebuilds, cause 'idle'"] = (
            r_idle["cache_by_session"][0]["rebuilds"]["idle"] == 3
            and {x["cause"] for x in r_idle["top_rebuilds"]} == {"idle"})
        checks["a rebuild after a model switch is cause 'model_switch', not idle"] = (
            r_switch["cache_by_session"][0]["rebuilds"]["model_switch"] == 1
            and r_switch["cache_by_session"][0]["rebuilds"]["idle"] == 0)
        checks["planted model switch names mid-session-switch"] = "mid-session-switch" in levers_of(a_switch)
        checks["an edit to CLAUDE.md is seen and, with no rebuild after it, confirms the docs"] = (
            r_switch["cache_by_session"][0]["always_loaded_edits"] == 1
            and "none followed by a rebuild" in " ".join(check_texts(a_switch, "always-loaded-edits")))
        checks["a Bash result past the filter's cap is named, not reported as holding"] = any(
            "Bash result(s) over" in c for c in check_texts(a_switch, "bash-filter") + [
                e for f in a_switch["findings"] if f["lever"] == "bash-filter" for e in f["evidence"]])
        checks["control: the clean session's bash-filter check holds"] = any(
            "holds" in c for c in check_texts(a_clean, "bash-filter"))
        idle_f = next(f for f in a_idle["findings"] if f["lever"] == "idle-rebuild")
        checks["a finding carries evidence, a change, a saving, a confidence and its assumption"] = all(
            idle_f[k] for k in ("evidence", "change", "saving_usd", "confidence", "assumption"))
        checks["every dollar is labelled an estimate"] = "estimate" in a_idle["label"] and \
            "estimate" in audit.render(a_idle)

        # report-level profiles for the rules a short transcript can't reach cheaply
        main_1h = clean("1h", calls=200, new=2_000).report(tmp, "clean1h")
        a_ttl = audit.audit(main_1h, prices)
        checks["1h writes with no pauses: cache-ttl-main recommends 5m"] = "cache-ttl-main" in levers_of(a_ttl) and \
            "5m" in next(f for f in a_ttl["findings"] if f["lever"] == "cache-ttl-main")["change"]
        paused = report_profile(main_1h, cache_by_session=[dict(main_1h["cache_by_session"][0],
                                pauses_between_ttls={"count": 30, "tokens": 30 * 80_000})])
        checks["...and with enough pauses it says the 1h TTL earns its premium"] = (
            "cache-ttl-main" not in levers_of(audit.audit(paused, prices))
            and "earns" in " ".join(check_texts(audit.audit(paused, prices), "cache-ttl-main")))
        heavy_agent = {"key": "worker", "runs": 6, "calls": 300, "models": [OPUS], "usd": 40.0,
                       "tokens": {"input": 600, "cache_write": 2_000_000, "cache_read": 60_000_000, "output": 30_000}}
        sub = report_profile(r_clean, by_subagent_type=[heavy_agent], log_usd=r_clean["log_usd"] + 40,
                             total_usd=r_clean["total_usd"] + 40, by_model=r_clean["by_model"] + [
                                 {"model": OPUS, "scope": "subagent", "calls": 300, "usd": 40.0,
                                  "tokens": heavy_agent["tokens"], "cache_write_5m": 0, "cache_write_1h": 2_000_000}])
        a_sub = audit.audit(sub, prices)
        checks["an Opus subagent type is repriced on Sonnet: model-per-agent"] = "model-per-agent" in levers_of(a_sub)
        builtin = audit.audit(report_profile(sub, by_subagent_type=[dict(heavy_agent, key="Explore")]), prices)
        changes = {f["change"] for a in (a_sub, builtin) for f in a["findings"] if f["lever"] == "model-per-agent"}
        checks["...naming the agent's file, or for a built-in the dispatch and env var"] = changes == {
            "set model: sonnet in .claude/agents/worker.md",
            "pass model: sonnet when dispatching Explore, or set CLAUDE_CODE_SUBAGENT_MODEL"}
        checks["subagent 1h writes name cache-ttl-subagent"] = "cache-ttl-subagent" in levers_of(a_sub)
        checks["subagents at most of the spend name subagent-fanout"] = "subagent-fanout" in levers_of(a_sub)
        talky = report_profile(r_clean, by_model=[dict(m, tokens=dict(m["tokens"], output=m["tokens"]["output"] * 40),
                                                       usd=(m["usd"] or 0) + m["tokens"]["output"] * 39 * 20 / 1e6)
                                                  for m in r_clean["by_model"]])
        talky["total_usd"] = talky["log_usd"] = sum(m["usd"] for m in talky["by_model"])
        checks["output past 30% of main spend names effort-level"] = "effort-level" in levers_of(audit.audit(talky, prices))

        # the cap: many material findings still render within MAX_LINES and MAX_FINDINGS
        crowd = report_profile(sub, by_subagent_type=[dict(heavy_agent, key=f"w{i}") for i in range(8)])
        a_crowd = audit.audit(crowd, prices)
        rendered = audit.render(a_crowd).splitlines()
        checks[f"the report stays within {audit.MAX_LINES} lines and {audit.MAX_FINDINGS} findings"] = (
            len(rendered) <= audit.MAX_LINES and len(a_crowd["findings"]) <= audit.MAX_FINDINGS
            and a_crowd["more_findings"] > 0)
        checks["every fixture's render stays within the cap"] = all(
            len(audit.render(a).splitlines()) <= audit.MAX_LINES for a in (a_clean, a_idle, a_switch, a_sub))

        # the catalog and the rules agree, and every lever is fully specified
        sections = catalog_sections()
        checks["catalog levers == audit.py rules, in the same order"] = list(sections) == list(audit.RULES)
        checks["every lever names its signal, mechanism, source, direction, trade-off, apply and measured"] = all(
            all(v.strip() for v in s.values()) for s in sections.values())
        checks["every signal names a usage.py report field"] = all(
            re.search(r"`(cache_by_session|by_model|by_subagent_type|top_tool_results|top_rebuilds)", s["Signal"])
            for s in sections.values())
        checks["every source is a doc URL or a named file or probe"] = all(
            re.search(r"https://|hooks/|probe_", s["Source"]) for s in sections.values())
        checks["cache claims cite the prompt-caching docs"] = all(
            "prompt-caching" in sections[k]["Source"] for k in sections if k.startswith(("cache-", "idle-")))

        # read-only: the auditor proposes and never applies
        src = (HERE.parent / "scripts" / "audit.py").read_text(encoding="utf-8")
        checks["audit.py writes no file"] = not re.search(r"write_text|write_bytes|open\([^)]*['\"][wa]", src)
        if AGENT.is_file():
            tools = re.search(r"^tools:\s*(.+)$", AGENT.read_text(encoding="utf-8"), re.M)
            checks["the spend-auditor agent has no Edit or Write tool"] = bool(tools) and not re.search(
                r"\b(Edit|Write|MultiEdit|NotebookEdit)\b", tools.group(1))
        if COMMAND.is_file():
            body = COMMAND.read_text(encoding="utf-8")
            checks["/spend-audit maps every argument form to a filter"] = all(
                k in body for k in ("--session", "--command", "--last", "all"))

        # measured outcomes (#69): the catalog's Measured lines outrank the estimate
        worker = next(f for f in a_sub["findings"] if f["lever"] == "model-per-agent")
        checks["a custom agent's finding carries its target and a machine edit; a built-in's has none"] = (
            worker["target"] == "worker"
            and worker["edit"] == {"file": ".claude/agents/worker.md", "key": "model", "value": "sonnet"}
            and next(f for f in builtin["findings"] if f["lever"] == "model-per-agent")["edit"] is None)
        base = unmeasured(CATALOG.read_text(encoding="utf-8"))
        marker = "### `model-per-agent`"
        head = base[base.index(marker):]
        measured_at = base.index(marker) + head.index("- **Measured:** none yet.")

        def with_outcome(line: str) -> Path:
            path = tmp / f"levers-{abs(hash(line))}.md"
            path.write_text(base[:measured_at] + "- **Measured:** 1 optimize-spend run, newest last.\n" + line
                            + base[measured_at + len("- **Measured:** none yet."):], encoding="utf-8")
            return path

        kept = with_outcome("  - `2026-10-21` `worker` model → sonnet: saving $0.0300 a run (25.0%), "
                            "noise floor $0.0040; quality held; **kept**")
        rejected = with_outcome("  - `2026-10-21` `worker` model → sonnet: saving $0.0010 a run (1.0%), "
                                "noise floor $0.0040; quality held; **rejected**: saving within the noise floor")
        saved = audit.CATALOG
        audit.CATALOG = kept
        a_kept = audit.audit(sub, prices)
        audit.CATALOG = rejected
        a_rej = audit.audit(sub, prices)
        audit.OUTCOME, saved_re = re.compile(r"(?!)"), audit.OUTCOME
        a_blind = audit.audit(sub, prices)
        audit.OUTCOME, audit.CATALOG = saved_re, saved
        kf = next((f for f in a_kept["findings"] if f["lever"] == "model-per-agent"), {})
        checks["a kept outcome re-prices the finding at the measured cut and labels it measured"] = (
            kf.get("basis") == "measured" and kf.get("saving_usd") == 10.0 and "(measured)" in audit.render(a_kept))
        checks["a rejected outcome drops the finding to a check that names the run"] = (
            "model-per-agent" not in levers_of(a_rej)
            and any("rejected" in c and "2026-10-21" in c for c in check_texts(a_rej, "model-per-agent")))
        checks["a target with no recorded outcome stays an estimate"] = worker["basis"] == "estimate"
        checks["[break] an outcome parser that matches nothing brings the rejected finding back"] = (
            "model-per-agent" in levers_of(a_blind))

        # breaks: disable one mechanism and the matching check must go red
        saved = usage.REBUILD_MIN_TOKENS
        usage.REBUILD_MIN_TOKENS = 10 ** 12
        broke = audit.audit(idle().report(tmp, "b1"), prices)
        usage.REBUILD_MIN_TOKENS = saved
        checks["[break] blind rebuild detection loses the planted idle finding"] = "idle-rebuild" not in levers_of(broke)
        saved = dict(usage.TTL_SECONDS)
        usage.TTL_SECONDS["1h"] = 10 ** 9
        broke = idle().report(tmp, "b2")
        usage.TTL_SECONDS.update(saved)
        checks["[break] a TTL that never expires turns idle rebuilds into 'other'"] = (
            broke["cache_by_session"][0]["rebuilds"]["idle"] == 0)
        saved = (audit.MATERIAL_SHARE, audit.MATERIAL_MIN_USD)
        audit.MATERIAL_SHARE, audit.MATERIAL_MIN_USD = 0.0, 0.0
        broke = audit.audit(r_clean, prices)
        audit.MATERIAL_SHARE, audit.MATERIAL_MIN_USD = saved
        checks["[break] with no materiality the control reports findings (it has teeth)"] = bool(broke["findings"])
        rule = audit.RULES.pop("read-guard")
        checks["[break] a rule missing from audit.py fails the drift check"] = list(catalog_sections()) != list(audit.RULES)
        audit.RULES["read-guard"] = rule
        audit.RULES = dict(sorted(audit.RULES.items(), key=lambda kv: list(catalog_sections()).index(kv[0])))
        saved = usage.ALWAYS_LOADED
        usage.ALWAYS_LOADED = ("NOTHING.md",)
        broke = switched().report(tmp, "b3")
        usage.ALWAYS_LOADED = saved
        checks["[break] an always-loaded list that misses CLAUDE.md sees no edit"] = (
            broke["cache_by_session"][0]["always_loaded_edits"] == 0)

    width = max(map(len, checks))
    for name, ok in checks.items():
        print(f"{'PASS' if ok else 'FAIL'}  {name.ljust(width)}")
    passed = sum(checks.values())
    print(f"\n{passed}/{len(checks)} passed")
    return 0 if passed == len(checks) else 1


def real(logs: Path | None = None) -> int:
    files = usage.discover(logs)
    if not files:
        print(f"no session logs at {logs or usage.default_logs()}")
        return 2
    corpus = usage.load(files)
    report = usage.build_report(corpus, usage.select(corpus), audit.TOP_RESULTS, usage.load_prices())
    rb = [s["rebuilds"] for s in report["cache_by_session"]]
    edits = sum(s["always_loaded_edits"] for s in report["cache_by_session"])
    print(f"{len(report['cache_by_session'])} session(s); rebuilds: {sum(r['count'] for r in rb)} "
          f"({sum(r['idle'] for r in rb)} idle, {sum(r['model_switch'] for r in rb)} model switch, "
          f"{sum(r['other'] for r in rb)} other); always-loaded edits: {edits}, followed by a rebuild: "
          f"{sum(s['rebuilds_after_edit'] for s in report['cache_by_session'])}")
    print(audit.render(audit.audit(report, usage.load_prices())))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--real", action="store_true")
    ap.add_argument("--logs", type=Path)
    a = ap.parse_args()
    if a.real:
        return real(a.logs)
    return selftest()


if __name__ == "__main__":
    sys.exit(main())
