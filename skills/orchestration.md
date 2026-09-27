# Orchestration

Delegate suitable work to preserve useful context and continuity. Main keeps the user's intent,
constraints, accepted decisions and task dependencies; subagents carry substantial investigation,
implementation and review in their own context windows. Avoidable compaction can lose details that
still matter. Token cost and dispatch count are not the objective, and zero compactions is not a
requirement.

The bootloader sets the default session shape and available models. Main coordinates delivery;
the agent assigned the technical work owns the reasoning and its implementation. A more capable
architect must not depend on Main translating a memo into technically correct changes.

## Main's operating sequence

1. Define the result, constraints and observable acceptance criteria. Keep small or tightly sequential
   work directly when a handoff would add little value.
2. Delegate a coherent task before reading its entire source surface. Supply enough context and
   starting locations for the worker to investigate independently.
3. Assign exclusive write ownership, the appropriate engineer or architect, and any execution or
   review-order constraints. Record the assignment and the child ID returned by the harness.
4. Let the owner investigate, edit and validate the deliverable. Answer scope questions and coordinate
   ownership changes; do not repeat the investigation merely to supervise it.
5. Check the delivered result against the agreed acceptance criteria. Use independent technical
   review when needed. Main need not rederive architectural reasoning or manually apply changes.
6. Integrate accepted work, run the relevant combined checks, and update
   [checkpoint.md](checkpoint-format.md)'s restart state. Rely on native history for operation logs.

## Roles and write authority

| Role | Accountable for | Normal write authority |
|---|---|---|
| Main | User conversation, objective, dependencies, assignments, acceptance and delivery | Checkpoint, coordination records and explicitly owned integration work; Git branches, commits and pin operations |
| Engineer | A coherent investigation or implementation, including relevant tests and local documentation | Assigned repository components and its own working artifacts |
| Architect | Architectural decisions, consistency and implementation of the assigned architectural change | Assigned specifications, guidelines, interfaces or code, including affected references and semantic integration |

Main owns delivery coordination. The architect owns architectural correctness within its assignment.
Main checks scope, user constraints, evidence and outstanding issues. When a technical question
exceeds Main's confidence, request a focused architect review rather than reconstructing or overruling
the reasoning without evidence. Confidence or model capability alone is never acceptance evidence.

### Engineer

Give the engineer a component or coherent change, with explicit exclusions and shared-file boundaries.
It may edit that component directly, add supporting tests or documentation, run permitted checks and
correct its own changes. Do not require a complete filename list or a draft tree that Main must copy
into the repository. Use an isolated checkout when the task requires one; it does not remove the need
to plan semantic integration.

If a needed change crosses ownership, the engineer proposes the change and Main expands, transfers
or sequences ownership. Continue useful independent work while that decision is pending. Discovering
another relevant source is ordinary investigation; adopting a separate objective is scope expansion.

### Architect

Choose the assignment explicitly:

- **Deliver a change:** investigate, decide, edit the authoritative files, reconcile affected
  references and validate the result. Return a concise explanation of the delivered decisions and
  remaining issues. The memo is supporting material, not a mandatory intermediate deliverable.
- **Advise or independently review:** return a decision or review record with evidence, alternatives
  where relevant, and required corrections. Do not silently edit the implementation being reviewed.

An architect may own semantic integration across engineer deliverables. Main first hands over the
necessary files and stops competing writes. The architect resolves interface and design conflicts,
updates the affected implementation or documentation, and validates the combined result. Main then
coordinates acceptance and Git operations. Scheduling writers and executing Git commands does not
make Main responsible for translating the architectural design.

## Ownership and discovery

One active writer owns each file in a shared checkout. Shared registries and indexes have one named
owner during a wave. Main alone edits the checkpoint and manages branches, commits and pins under
`SKILL.md`. Encoder and evidence-corpus read-only rules bind every role.

Ownership is recorded before work starts and may change explicitly during the task. A role does not
confer unrestricted repository writes. Where two tasks need the same file, sequence them, assign an
integration owner, or have one return a proposed patch.

Starting sources are entry points, not a read allowlist. Workers may search and follow relevant
repository dependencies without asking Main to prepare each input. Read narrowly, persist findings
and broaden as the question requires. Reading code does not authorize executing it; execution must
respect the assignment and repository safety boundaries.

Use stable revisions or snapshots for inputs that another worker is changing or whose exact bytes
matter to the result. Cold reviews may impose a specific reading order to protect independence.
These are explicit methodological constraints, not reasons to freeze every exploration input.

Raw transcripts stay outside routine model context. Prior session reports or archives are not
implicit dependencies: Main may supply relevant retained artifacts with provenance and a clear
purpose. Future work must not assume ignored staging paths survive. Graduate reusable findings into
tracked documentation or tests; access to retained archives requires an explicitly supplied archive.

## The task brief

The brief replaces a full conversation replay. Include what the worker needs to act independently:

| Field | Content |
|---|---|
| Identity and role | Task ID and engineer or architect; for architect, delivery or advisory/review assignment |
| Objective | Coherent result and why it matters |
| Context | Accepted decisions, dependencies and user constraints that affect the work |
| Starting sources | Governing instructions and useful source locations; exact versions where material |
| Ownership | Writable components, exclusive artifact location, shared-file exclusions and integration owner |
| Execution and method | Required checks, prohibited execution, cold-review ordering or empirical protocol where applicable |
| Deliverable and acceptance | Final files or findings, observable success criteria and required evidence |
| Escalation | Objective changes, conflicting requirements, needed ownership transfer or a blocked required action |

Do not make Main inspect every source before assignment. Workers read the instructions governing their
scope. Quote a narrow applicable rule with its exceptions when that avoids unrelated reading; do not
precompute the evidence the worker is assigned to discover.

## Context and task size

A useful task removes substantial source processing or implementation detail from Main's window and
returns a compact, checkable result. Delegate early enough to achieve that benefit. Keep connected
reasoning together; splitting phases that share discoveries and invariants can cause more rereading
and context loss than a single coherent assignment.

Workers write useful findings and intermediate state as they go, especially before a large new phase
or compaction. A compaction is a diagnostic, not task failure. Split work when each part has an
independently acceptable result; otherwise use a coherent staged task. Main should retain decisions
and references, not ingest every intermediate artifact.

Use the bootloader's concurrency budget. Start with at most `N - 1` active subagents and let Main
fill the reserved slot with independent follow-up work when useful. Do not create tasks merely to
fill slots. Workers propose independent follow-ups to Main rather than starting nested delegation.

## Acceptance and reporting

A completed turn is not an accepted result. The owner returns a compact report covering:

- What changed or was concluded, and where the final deliverable is.
- Checks performed and their results, with evidence sufficient to inspect them.
- Limitations, unchecked behavior and unresolved decisions.
- Independent work discovered but not undertaken.

Main checks the acceptance surface: inspect the relevant result, run a meaningful check or obtain
independent review. Main does not need to duplicate the entire investigation. Architectural changes
requiring specialist judgment can receive independent architect review; the delivery architect owns
corrections. Record accepted, needs correction or blocked, with the reason and any remaining action.
Unlock dependent tasks only after their required result is accepted.

After integration, run checks appropriate to the combined change. Preserve each agent's write
ownership until an explicit handoff, including during corrections.

## Task records and native history

Keep enough written state to resume and accept the work: the task brief, child ID returned by the
harness, deliverable, validation result and unresolved issues. Reuse the assignment, worker report
and Main acceptance record; do not create another summary that duplicates them. Update the checkpoint
with decisions and dependencies that must survive Main's compaction.

Rely on the harness's native history for the operation log. Ordinary dispatch does not require Main
or the worker to locate transcript files, copy logs, snapshot all inputs, hash outputs or assemble an
archive. Do not load raw transcripts into model context for routine supervision.

Native history is not a promise of permanent retention or exact reproduction. If the user requests
an export or retrospective analysis, handle it as a separate task, verify what was actually retained
and state any missing history. Do not make that work a prerequisite for ordinary delegation.
Preserve existing archives and partial evidence unless their cleanup is separately authorized.

### Evidence for empirical claims

An empirical task defines its evidence requirements in its acceptance criteria. Before execution,
specify the input and configuration boundary, population, controls, oracle and execution constraints.
Retain the inputs and results needed to substantiate that claim, with their provenance and relevant
versions. Exact reproduction requires exact supporting bytes; do not claim it from a transcript alone.
This does not require capturing every document an agent reads or archiving its entire working tree.

Ignored working artifacts are staging, not durable dependencies. Promote reusable findings into
tracked documentation or tests. Where a claim depends on retained evidence, preserve it in a verified
archive before cleanup and state its limitations. Later work requires that archive to be explicitly
supplied; it must not assume an old staging path still exists.

## Improving this workflow

Evaluate whether delegation preserved decision context, produced correct deliverables and avoided
unnecessary Main rereading or translation. Compactions, handoff failures and rework can identify a
problem; neither dispatch count nor exact token savings defines success. Record only observations
that could change the method and evolve the existing rule rather than accumulating incident rules.
