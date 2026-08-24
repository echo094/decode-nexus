# Claude Bootloader

See @SKILL.md for complete repository skills and operational directives. It is the single
copy: Standing Rules decide how a session is run, and Commit Conventions carry the commit
format, sign-off and identity rules. The only thing this file owns is the one directive that
is agent-specific — the session's default shape, below.

**Default session shape: work directly.** Delegate to subagents only when the work will span
sessions or compactions, when it holds two or more independently verifiable tasks with disjoint
write scopes, or when the user asks — and then read `skills/orchestration.md` before the first
task packet.

## Measuring a dispatched task

Claude Code's extractor is [`tools/measure-claude-code.py`](tools/measure-claude-code.py), and
everything specific to this harness — where the transcripts are, why records fold by `requestId`,
which fields carry each metric, what the window has to be passed as — is documented in its own
header, beside the code that acts on it.

    tools/measure-claude-code.py <session-dir> [--window 1000000] [transcript-id-prefix ...]

**Run it; never read a subagent transcript into context**, since one will overflow the window it is
meant to be measuring. Writing the finished row is `skills/orchestration.md`'s "Recording the
dispatch"; the invariants behind the script are in `skills/orchestration-log.md`.
