#!/usr/bin/env python3
"""Measuring an NeoPilot run from Claude Code session logs.

Answers the three questions it was written for:
  · what the run cost and who exactly spent it;
  · how much the contexts grew — the only quantity that can be controlled;
  · whether the rules that cannot be checked by reading the skill are kept.

Usage:
    python3 tools/measure-run.py <path to the project directory>
    python3 tools/measure-run.py ~/Documents/VScode/EDU/share

The logs directory is derived from the project path the same way Claude
Code does it: slashes are replaced with hyphens inside ~/.claude/projects/.

Cost normalization is relative to the input token:
    output ×5 · cache_write ×1.25 · cache_read ×0.1
These are proportions, not money: they exist to compare runs with each
other.
"""

import json
import os
import sys
import glob
from datetime import datetime
from collections import Counter

W_OUT, W_WRITE, W_READ = 5.0, 1.25, 0.1
IDLE_GAP_SEC = 300          # a longer pause is idle time, not work
CEILING_HINT = 120_000      # the ceiling from phases/5-subagents.md, for the "over" column


def logs_dir_for(project_path):
    p = os.path.abspath(os.path.expanduser(project_path))
    return os.path.join(os.path.expanduser("~/.claude/projects"), p.replace("/", "-"))


def parse_ts(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def load(path):
    rows = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return rows


def analyse(path, label):
    rows = load(path)
    ctx, tools = [], Counter()
    out = win = rin = cold = 0
    test_edits = code_edits = test_runs = 0
    stamps = []

    for r in rows:
        m = r.get("message") or {}
        ts = parse_ts(r.get("timestamp"))
        if ts:
            stamps.append(ts)
        if (m.get("role") or r.get("type")) != "assistant":
            continue
        u = m.get("usage") or {}
        if u:
            cr = u.get("cache_read_input_tokens", 0) or 0
            cw = u.get("cache_creation_input_tokens", 0) or 0
            ip = u.get("input_tokens", 0) or 0
            out += u.get("output_tokens", 0) or 0
            win += cw
            rin += cr
            if cw > 20_000:
                cold += 1
            if cr + cw + ip:
                ctx.append(cr + cw + ip)
        for c in m.get("content") or []:
            if not isinstance(c, dict) or c.get("type") != "tool_use":
                continue
            name, inp = c.get("name"), c.get("input", {})
            tools[name] += 1
            if name == "Bash":
                cmd = str(inp.get("command", ""))
                if any(k in cmd for k in ("pytest", "npm test", "go test", "cargo test", "unittest")):
                    test_runs += 1
            elif name in ("Edit", "Write", "NotebookEdit"):
                fp = str(inp.get("file_path", ""))
                base = os.path.basename(fp)
                if "/tests/" in fp or "/test/" in fp or base.startswith("test_") or ".test." in base:
                    test_edits += 1
                else:
                    code_edits += 1

    stamps.sort()
    active = idle = 0
    for a, b in zip(stamps, stamps[1:]):
        gap = (b - a).total_seconds()
        if gap <= IDLE_GAP_SEC:
            active += gap
        else:
            idle += gap

    return {
        "label": label, "steps": len(ctx),
        "avg_ctx": sum(ctx) / len(ctx) if ctx else 0,
        "max_ctx": max(ctx) if ctx else 0,
        "over": sum(1 for c in ctx if c > CEILING_HINT),
        "out": out, "write": win, "read": rin, "cold": cold,
        "norm": out * W_OUT + win * W_WRITE + rin * W_READ,
        "active": active, "idle": idle,
        "test_edits": test_edits, "code_edits": code_edits, "test_runs": test_runs,
    }


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    d = logs_dir_for(sys.argv[1])
    if not os.path.isdir(d):
        sys.exit(f"no logs: {d}")

    sessions = glob.glob(os.path.join(d, "*.jsonl"))
    if not sessions:
        sys.exit(f"no .jsonl in {d}")

    def weight(p):
        """An NeoPilot run is recognized by its subagents, not by recency:
        the latest session is usually the one where the result is viewed."""
        n = len(glob.glob(os.path.join(p[:-6], "subagents", "*.jsonl")))
        return (n, os.path.getsize(p))

    if len(sys.argv) > 2:                       # explicit choice: a session id
        picked = [p for p in sessions if sys.argv[2] in os.path.basename(p)]
        if not picked:
            sys.exit(f"session {sys.argv[2]} not found in {d}")
        main_log = picked[0]
    else:
        main_log = max(sessions, key=weight)

    if len(sessions) > 1:
        print(f"\nSessions in the directory: {len(sessions)}. Using {os.path.basename(main_log)[:8]}"
              f" ({len(glob.glob(os.path.join(main_log[:-6], 'subagents', '*.jsonl')))} subagents)."
              f"\nPick another with a second argument: measure-run.py <project> <session id>")
    sub_dir = main_log[:-6]

    metas = {}
    for mf in glob.glob(os.path.join(sub_dir, "subagents", "*.meta.json")):
        with open(mf) as f:
            metas[os.path.basename(mf)[:-10]] = json.load(f)

    results = [analyse(main_log, "Orchestrator")]
    for jf in sorted(glob.glob(os.path.join(sub_dir, "subagents", "*.jsonl"))):
        key = os.path.basename(jf)[:-6]
        results.append(analyse(jf, metas.get(key, {}).get("description", key)))
    results.sort(key=lambda r: -r["norm"])

    total = sum(r["norm"] for r in results) or 1
    print(f"\nRun: {sys.argv[1]}   contexts: {len(results)}\n")
    print(f"{'context':<38}{'steps':>7}{'avg.ctx':>9}{'max':>9}{'>120K':>7}{'norm.un':>11}{'share':>7}")
    print("-" * 88)
    for r in results:
        print(f"{r['label'][:37]:<38}{r['steps']:>7}{r['avg_ctx']/1000:>8.0f}K"
              f"{r['max_ctx']/1000:>8.0f}K{r['over']:>7}{r['norm']/1e6:>10.2f}M"
              f"{r['norm']/total*100:>6.1f}%")
    print("-" * 88)

    o = sum(r["out"] for r in results)
    w = sum(r["write"] for r in results)
    rd = sum(r["read"] for r in results)
    steps = sum(r["steps"] for r in results)
    print(f"{'TOTAL':<38}{steps:>7}{'':>9}{'':>9}{'':>7}{total/1e6:>10.2f}M\n")

    print("Spending breakdown")
    for name, val in (("cache reads", rd * W_READ), ("cache writes", w * W_WRITE), ("generation", o * W_OUT)):
        bar = "█" * round(val / total * 46)
        print(f"  {name:<14}{val/total*100:>5.1f}%  {bar}")
    print(f"\n  tokens read per token written: {(rd + w) / o:.0f}:1" if o else "")

    print("\nRule compliance")
    hot = [r for r in results if r["avg_ctx"] > CEILING_HINT * 1.5]
    print(f"  contexts above one-and-a-half ceiling: {len(hot)}"
          + (f" — {', '.join(r['label'][:24] for r in hot[:4])}" if hot else " — none"))
    te = sum(r["test_edits"] for r in results)
    ce = sum(r["code_edits"] for r in results)
    print(f"  test edits to code edits: {te}/{ce}"
          + (f" ({te/(te+ce)*100:.0f}%)" if te + ce else ""))
    print(f"  test runs: {sum(r['test_runs'] for r in results)}")
    cold_agents = [r for r in results if r["read"] and r["write"] / r["read"] > 0.10]
    print(f"  contexts with a stale cache (write/read > 10%): {len(cold_agents)}"
          + (f" — {', '.join(r['label'][:24] for r in cold_agents[:4])}" if cold_agents else " — none"))

    act = sum(r["active"] for r in results)
    idl = sum(r["idle"] for r in results)
    print(f"\nTime across all contexts: {act/60:.0f} min active · {idl/60:.0f} min idle"
          f" ({act/(act+idl)*100:.0f}% active)" if act + idl else "")


if __name__ == "__main__":
    main()
