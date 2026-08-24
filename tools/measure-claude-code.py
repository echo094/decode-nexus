#!/usr/bin/env python3
"""One orchestration-log row per dispatched task, extracted from Claude Code transcripts.

    tools/measure-claude-code.py <session-dir> [--window 1000000] [transcript-id-prefix ...]

The metrics are defined in skills/orchestration.md, the invariants every extractor must honour
in skills/orchestration-log.md, and how to write the finished row in the former's "Recording the
dispatch". What is specific to this harness is here, beside the code that acts on it.

Where the transcripts are
    A dispatched task is  <project-slug>/<session-id>/subagents/agent-<transcript-id>.jsonl
    under ~/.claude/projects. Point this at the *session* directory, never the project: a whole
    project mixes waves from unrelated sessions into one table. The file is a sidechain with its
    own agentId and no inherited parent usage, so the child's phase is the whole file.

One request spans several records
    Claude Code writes a record per content block — thinking, text, each tool call — all under
    one requestId. Input fields repeat identically across them while output_tokens climbs to its
    final value, so records are folded by requestId and the last snapshot wins. Summing records
    instead doubles every input total, and reports no error while doing it.

Per-request arithmetic
    cache miss   input_tokens + cache_creation_input_tokens. Never cache_read_input_tokens,
                 which repeats the prefix on every request.
    first fresh  the first request's cache miss.
    total fresh  every request's, summed.
    peak context max over requests of input + cache_creation + cache_read + output_tokens —
                 cached input included, since it still occupies the window.
    compactions  records of type "system", subtype "compact_boundary".

Two figures are not in the child transcript
    Window capacity is never recorded; pass --window from the row's own model. In Claude Code on
    a paid plan Sonnet 5, Fable 5, Opus 5 and Opus 4.6-4.8 are 1M (the default below) and the
    rest 200K, some needing usage credits enabled:
    https://support.claude.com/en/articles/8606394-how-large-is-the-context-window-on-paid-claude-plans
    `evidence read` is main-side, taken from the parent session's own transcript at
    ~/.claude/projects/<project-slug>/<session-id>.jsonl by matching each artifact-reading call
    to its result and counting the characters returned, over four. Printed as a placeholder
    here, along with the two ratios resting on it.
"""
import json, sys, glob, os, datetime

def name(path):                                                # agent-<transcript-id>.jsonl
    return os.path.basename(path).split(".")[0].removeprefix("agent-")

def requests(path):
    """One entry per API request, plus the child's compaction count.

    Claude Code repeats a request's usage on every content-block record it writes,
    so records are folded by requestId and the last snapshot taken: input fields are
    identical across them and output_tokens grows to its final value.
    """
    order, usage, meta, compactions = [], {}, {}, 0
    for line in open(path, encoding="utf-8", errors="replace"):
        try: o = json.loads(line)
        except ValueError: continue
        if o.get("type") == "system" and o.get("subtype") == "compact_boundary":
            compactions += 1                                   # the explicit harness record
        m = o.get("message") if isinstance(o.get("message"), dict) else {}
        u = m.get("usage")
        if not isinstance(u, dict): continue
        key = o.get("requestId") or o.get("uuid")
        if key not in usage: order.append(key)
        usage[key] = u
        meta[key] = (o.get("timestamp"), m.get("model"), o.get("effort"))
    return [(usage[k], meta[k]) for k in order], compactions

def row(path, window):
    reqs, compactions = requests(path)
    if not reqs: return None                                   # never a row of zeros
    total_fresh = output = report = peak = regressions = replay = 0
    first_fresh = prev_total = prev_read = None
    model = effort = "?"
    t0 = t1 = None
    for u, (ts, mdl, eff) in reqs:
        fresh = (u.get("input_tokens", 0)                      # fresh: the cache misses,
                 + u.get("cache_creation_input_tokens", 0))    # never cache_read
        read = u.get("cache_read_input_tokens", 0)
        turn = u.get("output_tokens", 0)
        if first_fresh is None: first_fresh = fresh            # the launch request
        total_fresh += fresh
        output += turn                                         # output: every request
        if turn: report = turn                                 # report: the last one wins
        peak = max(peak, fresh + read + turn)                  # cached input still occupies
        if prev_total is not None and fresh + read >= prev_total and read < prev_read:
            regressions += 1                                   # cache-prefix regression:
            replay += prev_read - read                         # a replay lower bound
        prev_total, prev_read = fresh + read, read
        if ts: t0, t1 = (t0 or ts), ts
        if mdl: model = mdl
        if eff: effort = str(eff)
    workload = total_fresh - first_fresh + output
    if workload <= 0: return None
    date, wall = "", ""
    if t0:
        date = t0[:10]
        try:
            d = (datetime.datetime.fromisoformat(t1.replace("Z", "+00:00"))
                 - datetime.datetime.fromisoformat(t0.replace("Z", "+00:00")))
            wall = f"{round(d.total_seconds() / 60)}m"
        except ValueError: pass
    k = lambda n: f"{n/1000:.2f}k"
    return (f"| {date}.<n> | <task> | {name(path)[:8]} | {model} · {effort} | "
            f"{k(window)} | {k(peak)} | {k(first_fresh)} | <pred workload> | "
            f"{k(total_fresh)} | {k(output)} | {k(report)} | {k(workload)} | "
            f"<evidence read> | <delegation efficiency> | <main-context compression> | "
            f"{regressions} / {k(replay)} | {compactions} | {wall} |")

args = sys.argv[1:]
window = 1_000_000
if "--window" in args:
    i = args.index("--window"); window = int(args[i + 1]); del args[i:i + 2]
d = args[0] if args else "."
pre = args[1:] or [""]
for p in sorted(glob.glob(os.path.join(d, "**", "agent-*.jsonl"), recursive=True)):
    if any(name(p).startswith(x) for x in pre):
        r = row(p, window)
        if r: print(r)
