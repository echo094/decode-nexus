#!/usr/bin/env python3
"""One orchestration-log row per dispatched task, extracted from Codex transcripts.

    tools/measure-codex.py <sessions-dir> [agent-path-prefix ...]

The metrics are defined in skills/orchestration.md, the invariants every extractor must honour
in skills/orchestration-log.md, and how to write the finished row in the former's "Recording the
dispatch". What is specific to this harness is here, beside the code that acts on it.

Where the child's own phase begins
    Codex records exact per-request usage in the child transcript's token_count events, but a
    full-history fork can copy the parent's into that same JSONL. Aggregation therefore starts
    only after the agent_message addressed to the child's own agent_path; the first positive
    usage past that boundary is the startup request, and its non-cached part is `first fresh`.

Per-request arithmetic
    cached_input_tokens is a subset of input_tokens, so a request's non-cached input is the
    difference — summed into `total fresh`. reasoning_output_tokens is likewise already a subset
    of output_tokens and is never added again. `peak context` keeps cached input, since it still
    occupies the window even when it costs nothing to process.

Completion
    A finished child has a task_complete event; an incomplete transcript prints no row rather
    than a row of zeros. A resumed child emits another task_complete whose duration covers that
    turn, so wall time is the sum of every completion duration in the one dispatch record.
    `evidence read` is main-side and prints as a placeholder, along with the two ratios resting on
    it.
"""
import glob
import json
import os
import sys


def records(path):
    with open(path, encoding="utf-8", errors="replace") as stream:
        for line in stream:
            try:
                yield json.loads(line)
            except ValueError:
                continue


def row(path):
    meta = context = None
    total_fresh = output = report = 0
    window = peak = 0
    complete = None
    duration = 0
    started = False
    first_fresh = None
    previous_total = previous_cached = None
    regressions = replay = compactions = 0
    for record in records(path):
        payload = record.get("payload", {})
        if record.get("type") == "session_meta" and meta is None:
            meta = payload
        elif record.get("type") == "turn_context":
            context = payload
        elif (meta and record.get("type") == "response_item"
              and payload.get("type") == "agent_message"
              and payload.get("recipient") == meta.get("agent_path")):
            started = True
        elif not started:
            continue
        elif record.get("type") == "compacted":
            compactions += 1
        elif record.get("type") == "event_msg" and payload.get("type") == "token_count":
            info = payload.get("info") or {}
            usage = info.get("last_token_usage") or {}
            total_input = usage.get("input_tokens", 0)
            cached_input = usage.get("cached_input_tokens", 0)
            if not total_input:
                continue
            turn_fresh = total_input - cached_input
            if first_fresh is None:
                first_fresh = turn_fresh
            if (previous_total is not None and total_input >= previous_total
                    and cached_input < previous_cached):
                regressions += 1
                replay += previous_cached - cached_input
            previous_total = total_input
            previous_cached = cached_input
            total_fresh += turn_fresh                       # total fresh: the cache misses
            turn = usage.get("output_tokens", 0)
            output += turn                                  # output: every turn
            peak = max(peak, total_input + turn)             # cached input still occupies context
            if turn:
                report = turn                               # report: the last one wins
            window = info.get("model_context_window", window)
        elif record.get("type") == "event_msg" and payload.get("type") == "task_complete":
            complete = payload
            turn_duration = payload.get("duration_ms")
            if isinstance(turn_duration, (int, float)):
                duration += turn_duration

    if (not meta or meta.get("thread_source") != "subagent"
            or first_fresh is None or not total_fresh or not report or not complete):
        return None                                         # never a row of zeros
    spawn = (((meta.get("source") or {}).get("subagent") or {}).get("thread_spawn") or {})
    agent_path = spawn.get("agent_path", "?")
    workload = total_fresh - first_fresh + output
    if workload <= 0:
        return None

    timestamp = meta.get("timestamp", "")
    date = timestamp[:10]
    wall = f"{round(duration / 60000)}m" if duration else "?"
    model = (context or {}).get("model", "?")
    effort = (context or {}).get("effort", "?")
    transcript = str(meta.get("id", "?"))[-8:]
    k = lambda number: f"{number / 1000:.2f}k"
    return (agent_path, f"| {date}.<n> | <task> | {transcript} | {model} · {effort} | "
            f"{k(window)} | {k(peak)} | {k(first_fresh)} | "
            f"<pred workload> | {k(total_fresh)} | {k(output)} | "
            f"{k(report)} | {k(workload)} | "
            f"<evidence read> | <delegation efficiency> | <main-context compression> | "
            f"{regressions} / {k(replay)} | {compactions} | {wall} |")


root = sys.argv[1] if len(sys.argv) > 1 else "."
prefixes = sys.argv[2:] or [""]
paths = sorted(glob.glob(os.path.join(root, "**", "*.jsonl"), recursive=True))
for path in paths:
    result = row(path)
    if result and any(result[0].startswith(prefix) for prefix in prefixes):
        print(result[1])
