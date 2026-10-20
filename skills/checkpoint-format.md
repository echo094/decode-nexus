# Checkpoint Format

`checkpoint.md` at the hub root is **scratch state**: the restart interface between sessions, and
between a main agent and whatever replaces it after a compaction. A fresh reader who has read
`SKILL.md` must be able to resume from it without reconstructing finished work. It is not a skill
doc, a history archive or a notebook, and never the only copy of a fact
([doc-conventions.md](doc-conventions.md#where-facts-live)). It holds no rules either: a rule that
matters goes into a skill doc with the user's approval ([`SKILL.md` gate 6](../SKILL.md#gates)).

**One file, one objective: the one that outlives the session.** Rewrite the file when the objective
changes; never append a second one. Work opened and closed inside one session leaves its record in
its artifacts and commits, not here.

## Layout

Ordered by importance, never by chronology: the file answers *what do I do next* and *what was
already decided*, so both sit at the top.

```md
# Checkpoint — <the concrete objective>

<two or three lines: what this objective is, and what is deliberately not in it>

## Resume here
- Current state: <the last accepted result>
- Next action: <one exact task or command>
- Why next: <the dependency that makes it next>

## Definition of done
## Constraints and decisions
## Plan
## Validation
## Repository state
## Open questions
## Assets
## Decisions not to re-make
```

A section with nothing to say is deleted, not left as a placeholder. The preamble states the
objective and what is out of scope; it never restates this specification.

| Section | Holds |
|---|---|
| Constraints and decisions | Live constraints and settled decisions, each with its reason and the skill doc that now owns it. A decision reversed rather than wrong says so. The user's current instructions, one entry each, latest wording only. |
| Plan | Remaining work in the order it unblocks, each step saying what it unblocks. Direct work lists steps; delegated work uses the task graph below; never both. The order lives in the table a reader scans, never in prose beside it; say which positions no dependency sets. Re-derive a step's order and diagnosis from source before implementing it. |
| Validation | Checks run, latest result per check, and checks still owed. |
| Repository state | Branches, which dirt is intentional, untracked assets that must survive, any commit constraint in force. |
| Open questions | Only items that can still change the plan. A design gap, design change or unexpected result waiting on the user sits here with its options and recommendation ([`SKILL.md` gate 1](../SKILL.md#gates)). |
| Assets | Corpora, instruments, fixtures and pipelines a later step will use, and what must not be deleted and why. |
| Decisions not to re-make | Corrections that were believed, acted on and wrong, kept only while they would otherwise be re-made. |

### The task graph

| ID | Deliverable | Dependencies | Owner | Write scope | Status | Evidence |
|---|---|---|---|---|---|---|

IDs are stable and shared with the task brief ([orchestration.md](orchestration.md)). Status is
`pending`, `in_progress`, `blocked` or `completed`; `completed` means Main checked the acceptance
evidence, not that a subagent's turn ended. Owner and write scope are recorded before a task starts.

## How to update

Every update is an edit of the whole file's state, not an addition to it. Follow these steps each
time:

1. **Rewrite `Resume here` from scratch.** Three bullets: the last accepted result, one exact next
   action, why it is next. Never append to the old bullets.
2. **Replace, never accumulate.**
   - A new user instruction replaces the one it supersedes, in place. Never narrate a sequence
     ("the user resumed…, then later asked…").
   - A new result for a check replaces that check's previous result.
   - A finished plan step shrinks to one line, or is deleted once nothing depends on it.
3. **Delete what this step made obsolete**, in the same edit: answered questions, superseded plans
   and alternatives, failures that are resolved, history.
4. **Graduate settled facts.** A fact that is now settled moves to the skill doc that owns it, and
   the scratch copy is deleted in the same change.
5. **Ask the gate question.** Did this step hit a design gap, a design change or an unexpected
   result? If yes, record it under Open questions with options and a recommendation, and make the
   next action "ask the user" ([`SKILL.md` gate 1](../SKILL.md#gates)).
6. **Read the file once, top to bottom.** If two sections repeat or contradict each other, or a
   status appears in one place but not another, rewrite the file whole; that rewrite is real work
   and earns its own commit. A status lives in several
   places (a table row, a summary, a next action); update every one
   ([doc-conventions.md](doc-conventions.md#marking-something-done)).

**When to update:** after each step, not at each milestone. A step is anything whose loss to a
compaction would cost real work: a refactor, a matcher, a settled sub-question. Also update when a
task is dispatched, accepted, rejected or blocked; when evidence changes a dependency, constraint or
decision; before a handoff; and after integration and final verification.

## What never goes in

- **Commit SHAs from this repository or an editable submodule.** Unpushed history is rebuilt, so
  such a SHA silently stops resolving; describe the change instead. Submodule pins and the tag a
  finding was read at are permanent and allowed.
- **Any fact that has a durable home.** Once settled it moves to its skill doc (step 4 above).
- **Raw evidence or a path outside Git.** Long logs, full diffs, generated corpora and intermediate
  measurements are not resumable. Link skill docs, committed tests and tools only.
- **A measured figure without its date and command.** Figures may live here rather than in a skill
  doc, but a bare value is unusable once the corpus regenerates.
- **An answered question, a completed narrative or a superseded plan.** An answered question reads
  exactly like an open one and gets re-opened at full price. Keep only enough finished state to
  explain what the remaining work depends on.
- **A rule.** Rules live in skill docs ([`SKILL.md` gate 6](../SKILL.md#gates)).

## Handing off

A chat message is not a handoff. Update the file first, then report the same state to the user:
outcomes, changed files or commits, checks run, live risks, unfinished work and the exact resume
point. Describe accepted state, not activity: not commands that merely ran, not investigations that
decided nothing, not a subagent claim nobody checked. **Never round partial work up to
`completed`:** record the last verified boundary, why it is partial, and the next exact command.
