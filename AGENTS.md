# Codex Bootloader

Read `SKILL.md` completely before taking any task action. It is the single copy of this
repository's skills and operational directives, all of which apply to Codex work here:
Standing Rules decide how a session is run, and Commit Conventions carry the commit format,
sign-off and identity rules. This bootloader owns Codex-specific launch policy and tool mappings;
shared role, ownership and acceptance rules live in [orchestration.md](skills/orchestration.md).

**Default session shape: delegate suitable work to preserve Main context.** Before dispatching,
read [orchestration.md](skills/orchestration.md) and follow its Main operating sequence. Assign
substantial investigation or implementation before loading all its sources into Main. Keep small
changes and tightly connected sequential work directly when a handoff offers little benefit.
Architectural difficulty can justify a more capable architect; it is not a reason to keep all
judgment with Main. Avoidable context loss, rather than token cost or dispatch count, guides the choice.

**Subagent concurrency budget: `N = 3`.** Apply the wave limit defined in
`skills/orchestration.md`; `N` counts active subagents and excludes the main agent.

## Model and effort policy

- **Main agent / product manager: `gpt-6-luna` · `max`.** It owns the user conversation,
  checkpoint, task decomposition, acceptance coordination, and Git operations. Assign technical
  integration to its engineer or architect owner; Main does not have to reconstruct their reasoning.
- **Engineer: `gpt-6-luna` · `xhigh`.** Spawn workers with a concise task brief and a context-free fork so
  the explicit model and effort apply.
- **Architect: `gpt-6-sol` · `high`.** Use this on-demand role only for the cross-cutting
  decisions and review gates defined by `skills/orchestration.md` or the active checkpoint. A delivery
  architect owns the assigned authoritative edits and their validation; an advisory/review architect
  returns findings. Main coordinates ownership and acceptance rather than translating a memo. The
  architect does not become a second product manager or edit `checkpoint.md`.

Depart from these defaults only when the user requests another configuration or a task packet
establishes a concrete need for one. A model named here is a launch policy: the session launcher
must select the Main-agent model, and each delegated task must set its role's model and effort
explicitly.

**Model and effort are immutable for an agent's lifetime.** Never switch either one after creating
a Main session or subagent; doing so invalidates the serving-cache assumptions behind this policy.
When work needs a different pair, start a fresh context-free subagent with that pair. Changing the
Main pair requires a fresh Main session. A follow-up may reuse an agent only with the exact model
and effort it was created with.

## Ordinary dispatch

Use the role and write-ownership contract in [orchestration.md](skills/orchestration.md). Record the
task brief and child ID returned by the harness; let the owner edit its assigned repository scope and
validate the deliverable. Starting sources do not form a read allowlist. Main records acceptance
and keeps the checkpoint current. Rely on native history without locating or exporting transcripts
as part of dispatch. Export is a separate task when requested.

Native history does not guarantee permanent retention or exact reproduction. Follow the task-record
and empirical-evidence rules in the orchestration guideline.
