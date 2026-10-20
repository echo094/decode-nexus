# Orchestration

How Main delegates to subagents. Read it before the first task brief; a session working directly
never opens it. The bootloader sets the default session shape, the available models and the
concurrency budget.

Delegation exists to keep useful context: Main holds the user's intent, constraints, accepted
decisions and task dependencies, while subagents carry substantial investigation, implementation
and review in their own windows. Token cost and dispatch count are not the objective, and a
compaction is a diagnostic, not a failure.

## Main's operating sequence

1. **Define** the result, constraints and observable acceptance criteria. Keep small or tightly
   sequential work direct when a handoff adds little.
2. **Delegate** a coherent task before reading its whole source surface, with enough context and
   starting locations for the worker to investigate alone.
3. **Assign** exclusive write ownership, the role, and any execution or review-order constraints.
   Record the assignment and the child ID the harness returns.
4. **Let the owner work.** Answer scope questions and coordinate ownership; do not repeat the
   investigation to supervise it.
5. **Check** the result against the acceptance criteria, with independent review where needed.
6. **Integrate** accepted work, run the combined checks, and update the checkpoint.

**Main takes every design gap, design change and unexpected result to the user** ([`SKILL.md`
gate 1](../SKILL.md#gates)). A worker escalates them to Main; Main does not settle them with a review. A review informs
the user's decision and never makes it.

## Roles

| Role | Accountable for | Writes |
|---|---|---|
| Main | User conversation, objective, dependencies, assignments, acceptance, delivery | Checkpoint, coordination records, explicitly owned integration; Git branches, commits and pins |
| Engineer | A coherent investigation or implementation, with its tests and local docs | Assigned components |
| Architect | Architectural decisions and consistency, and implementing the assigned architectural change | Assigned specifications, interfaces or code, including affected references |

- **Engineer:** gets a component or coherent change with explicit exclusions and shared-file
  boundaries. It may edit that component, add tests and docs, run permitted checks and correct its
  own changes. Do not require a complete filename list or a draft tree for Main to copy. An
  isolated checkout, where needed, does not remove the need to plan integration. If a change crosses ownership, it proposes the change and Main expands, transfers or
  sequences ownership. Discovering a relevant source is ordinary investigation; adopting a separate
  objective is scope expansion and goes to Main.
- **Architect:** is assigned either to **deliver** a change (investigate, decide within the
  approved design, edit the authoritative files, validate, and report decisions and remaining
  issues) or to **advise or review** (return findings with evidence and required corrections,
  without editing what it reviews). An architect may own integration across engineers' deliverables
  once Main hands over the files and stops competing writes. Main does not translate an
  architect's memo into changes.

When a technical question exceeds Main's confidence, request a focused architect review rather than
overruling the reasoning without evidence. Confidence or model capability is never acceptance
evidence. A review finding that adds a guard must cite an encoder-produced case ([F4](encoder-decoder-method.md#f4-keep-a-guard-only-where-a-real-case-needs-it)); a finding that
widens scope goes to the user.

## Ownership

One active writer owns each file in a shared checkout; shared registries and indexes have one
named owner during a wave. Main alone edits the checkpoint and runs Git. Ownership is recorded
before work starts and changes only explicitly. Where two tasks need one file, sequence them,
assign an integration owner, or have one return a patch. Read-only rules for encoders and the
evidence corpus bind every role.

Starting sources are entry points, not a read allowlist: workers follow relevant dependencies
without asking Main. Reading code does not authorize running it. Use a stable revision for inputs
another worker is changing. A cold review may impose a reading order to protect its independence. Prior session output is never a dependency: what a later task needs is
in skill docs, committed tests and tools.

## The task brief

| Field | Content |
|---|---|
| Identity and role | Task ID; engineer or architect; for an architect, deliver or review |
| Objective | The result, why it matters, and the decoded-output measure it should move ([P4](encoder-decoder-method.md#p4-every-work-item-names-its-output-measure)) |
| Context | Accepted decisions, dependencies and user constraints that affect the work |
| Starting sources | Governing instructions and useful source locations, with exact versions where material |
| Ownership | Writable components, shared-file exclusions, integration owner |
| Execution and method | Required checks, prohibited execution, review ordering or empirical protocol |
| Deliverable and acceptance | Final files or findings, observable success criteria, required evidence |
| Escalation | Objective changes, conflicting requirements, ownership transfers, blocked actions, and every design gap, design change or unexpected result: stop that line and report to Main |

Do not make Main read every source before assigning. Quote a narrow rule with its exceptions when
that saves unrelated reading; do not precompute the evidence the worker is meant to find.

## Task size

A useful task removes substantial source processing from Main's window and returns a compact,
checkable result. Keep connected reasoning together: splitting phases that share discoveries can
cost more rereading than one coherent task. Split only where each part is independently acceptable.
Workers write findings into their owning docs as they go, especially before a large new phase. Use
the bootloader's concurrency budget. **N − 1 wave rule:** start at most `N − 1` active subagents and
let Main fill the reserved slot with independent follow-up work. Do not create tasks to fill slots, and workers propose
follow-ups to Main rather than delegating further.

## Acceptance and reporting

A finished turn is not an accepted result. The owner reports what changed or was concluded and
where; the checks run and their results; limitations and unchecked behaviour; and independent work
found but not done. Main inspects the result, runs a meaningful check or gets an independent review,
and records accepted, needs correction or blocked, with the reason. Dependent tasks unlock only after
acceptance. Ownership holds until an explicit handoff, including during corrections.

## Records and evidence

Keep only what resuming and accepting needs: the brief, the child ID, the deliverable, the
validation result and open issues. The harness's native history is the operation log; ordinary
delegation never requires locating transcripts, copying logs, snapshotting inputs, hashing outputs
or assembling archives, and raw transcripts stay out of routine context. Native history does not
promise permanent retention or exact reproduction. An export or retrospective is a separate task
when the user asks for one: verify what was retained and state what is missing.

**Evidence is proportionate to the claim** ([`SKILL.md` gate 5](../SKILL.md#gates)). An empirical task states its inputs,
configuration, population, controls and oracle before running. Reproduction means pinned or pushed
commits, a recorded seed and a checked-in tool, with the toolchain stated; tracked inputs are
identified by commit and a clean `git status`, never by a stored digest
([doc-conventions.md](doc-conventions.md#where-facts-live)). What outlives the task is the
graduated finding and any fixture a maintained test needs. A harness, monitor or protocol that does
not move the decoded output needs the user's approval before it is built.

## Improving this workflow

Judge delegation by whether it kept decision context, produced correct deliverables and avoided
Main rereading or translating. Record only observations that would change this method, by evolving
an existing rule.
