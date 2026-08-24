# Codex Bootloader

Read `SKILL.md` completely before taking any task action. It is the single copy of this
repository's skills and operational directives, all of which apply to Codex work here:
Standing Rules decide how a session is run, and Commit Conventions carry the commit format,
sign-off and identity rules. The only thing this file owns is the one directive that is
agent-specific — the session's default shape, below. A rule binding every agent belongs in
`SKILL.md`; kept here it would be a second copy that drifts against `CLAUDE.md`.

**Default session shape: delegate to subagents.** Read `skills/orchestration.md` at the start
of the session and run the work through it. Take a task directly only when it is a small
change, a strongly sequential investigation, or work whose difficulty is judgment rather than
volume — that kind does not decompose, and delegating it costs a round trip to buy nothing.

**Subagent concurrency budget: `N = 3`.** Apply the wave limit defined in
`skills/orchestration.md`; `N` counts active subagents and excludes the main agent.

**Default subagent configuration: `gpt-5.6-luna` · `xhigh`.** Spawn packet-driven workers with
that model and reasoning effort, using a context-free fork so the explicit overrides apply. Depart
from this default only when the user requests another configuration or the task packet establishes
a concrete need for one.

## Measuring a dispatched task

Codex's extractor is [`tools/measure-codex.py`](tools/measure-codex.py), and everything specific to
this harness — where the child's own phase begins in a forked transcript, which usage fields are
subsets of which, what a completed child looks like — is documented in its own header, beside the
code that acts on it.

    tools/measure-codex.py <sessions-dir> [agent-path-prefix ...]

**Run it; never read a subagent transcript into context**, since one will overflow the window it is
meant to be measuring. Writing the finished row is `skills/orchestration.md`'s "Recording the
dispatch"; the invariants behind the script are in `skills/orchestration-log.md`.
