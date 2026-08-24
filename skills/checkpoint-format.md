# Checkpoint Format

`checkpoint.md` at the hub root is the repository's **scratch state**: the restart interface between
sessions, and between a main agent and whatever replaces it after a compaction. A fresh reader who
has loaded `SKILL.md` should be able to resume from it without reconstructing finished work.

It is **not** a skill doc, a history archive, or a notebook, and never the only copy of a fact
(`SKILL.md`'s Revise by Evolution).

**One file, one objective — the one that outlives the session**, rewritten when that objective
changes rather than appended to. Work opened and closed inside a single session leaves its record in
its artifacts and the commits it earns: it has no restart to interface with, and letting it displace
a live multi-session plan trades the only copy of that plan for a copy of something disposable. Work
that turns out to outlive the session becomes the objective at that moment, and the file is
rewritten around it.

**The file does not restate this specification.** Its preamble says what the current objective is
and what is deliberately out of scope, nothing more.

## Ordering: important-first, history last

The file is read to answer two questions — *what do I do next* and *what was already decided* — so
it is ordered by importance, never by chronology. Both answers sit at the top; findings, assets and
superseded reasoning sit at the bottom.

**Never let a status note accrete pass by pass.** One "Last updated" line here grew into a 123-line
nested parenthetical that was the first thing anyone read and the least useful part of the file, and
the same rewrite found three doc-layout sections at three heading depths contradicting each other.
When the file goes patchy, **rewrite it whole rather than patching a fifth time** — that rewrite is
real work and earns its own commit.

## The layout

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
## Assets                <- what earlier phases leave behind that is still in use
## Decisions not to re-make
```

Sections are required **when they apply**, and a section with nothing to say is deleted rather than
left holding a placeholder — an empty template read back as a plan is how planning gets skipped.
Longer sections may be numbered and subdivided, provided the order above holds.

What each section carries, where the name is not self-evident:

- **Constraints and decisions** — live constraints and settled decisions, each with its reason and,
  where one exists, the durable doc that now owns it. A decision that was *reversed rather than
  wrong* says so; that distinction is the reason it will not be re-litigated.
- **Plan** — the remaining work in the order it unblocks. It takes one of two shapes and never
  both: direct work lists the steps, each saying what it unblocks; orchestrated work uses the task
  graph below. A step whose only justification is that it comes next is not a plan entry — say what
  makes it next, since that is what a resumption re-derives otherwise. **The order lives in the
  structure a reader scans, never in prose beside it**: a sequence explained in a paragraph under a
  table is not ordered work, so give each row its position and say plainly which positions no
  dependency sets, or the next session reads one in. And **re-derive a recorded item's order from
  source before implementing it, along with its own diagnosis** — doing that here found an item
  whose target had zero population at the pass, so it could never have worked.
- **Validation** — checks already run, and checks still owed. The second half is the one that gets
  dropped and is the reason the section exists.
- **Repository state** — branches, which dirt is intentional, untracked assets that must survive,
  and any commit constraint currently in force.
- **Open questions** — only items that can still change the plan.
- **Assets** — corpora, instruments, fixtures and pipelines a later phase will use, plus what must
  not be deleted and why. This is not history: it is inventory the next session depends on.
- **Decisions not to re-make** — the bottom of the file. Corrections that were believed, acted on,
  and wrong, kept only while they would otherwise be re-made.

### The task graph

| ID | Deliverable | Dependencies | Owner | Write scope | Status | Evidence |
|---|---|---|---|---|---|---|

IDs are stable and shared with the task packet and its artifact directory
([orchestration.md](orchestration.md)). Status is `pending`, `in_progress`, `blocked` or
`completed`, and **`completed` means the main agent checked the acceptance evidence** — not that a
subagent's turn ended. Owner and write scope are recorded before a task starts, not after a
collision.

## When to update

**After each step, not at each milestone.** A step is a refactor, a matcher, a settled sub-question
— anything whose loss to a compaction would cost real work. Beyond that, always update when a task
is dispatched, accepted, rejected or blocked; when evidence changes a dependency, constraint or
decision; before handing work to another session; and after integration and final verification.

Marking something done means re-reading every place that names it — a status lives in a table, a
summary line and a next-action at once, and updating the one in front of you leaves the others
asserting the opposite ([doc-conventions.md](doc-conventions.md), "Marking something done").

## What never goes in

- **Commit SHAs from this repository or an editable submodule.** Unpushed history gets rebuilt, so
  such a SHA is a reference that silently stops resolving; describe the change, not the commit.
  **Submodule SHAs are the exception and are permanent** — an encoder pin, or the tag a finding was
  read at.
- **Any fact that has a durable home.** Once it is settled it goes to the skill doc that owns it and
  the scratch copy is pruned *in the same change*, or the two drift and the stale one is
  indistinguishable from the fresh one.
- **Raw evidence.** Long logs, full diffs, generated corpora and intermediate measurements live in
  task artifacts; the checkpoint links them.
- **A measured figure without its date and command.** Figures belong here rather than in a skill doc
  (`SKILL.md`'s Measured Figures Are Diary), but a bare value here is just as unusable — a corpus
  regenerates and voids it with nothing to notice.
- **An answered question.** It reads exactly like an unanswered one and gets re-opened at full
  price. The same applies to completed narratives, superseded plans and obsolete alternatives:
  keep only enough finished state to explain what the remaining work depends on.

## Handing off

A chat message is not a handoff. Update the file first, then report the same state to the user:
outcomes, changed files or commits, checks run, live risks, unfinished work, and the exact resume
point. Rewrite `Resume here` so it names the last accepted result, one exact next action, and why
that action is next.

Describe accepted state, not activity — not commands that merely ran, not investigations that
produced no decision, not a subagent claim nobody validated. **Never round partial work up to
`completed` for a cleaner handoff**: record the last verified boundary, its artifact paths, why it
is partial, and the next exact command.
