# Orchestration

How several agents of **ordinary capability, each with a limited context window**, finish work that
would otherwise need one agent to hold everything at once. Read it whenever the session will
delegate — the default for some bootloaders and a departure for others, decided by `SKILL.md`'s
Orchestration Gate rather than here. A session working directly does not need this file.

**The constraint being solved is context, not capability.** A subagent is not smarter than the main
agent and is usually a smaller model; what it has is an empty window. Everything below follows: the
filesystem is the shared memory, the **task packet** is what an engineer gets instead of the
conversation, and `checkpoint.md` is what a fresh main agent gets instead of the session
([checkpoint-format.md](checkpoint-format.md)).

**The corollary is the rule people skip:** work whose difficulty is *judgment* rather than volume
does not decompose, and delegating it buys a round trip and a re-derivation for nothing. Design
decisions, doctrine, a diagnosis where each step names the next probe — those stay with the main
agent however large they are.

## Delegate, or take a compaction instead

The alternative to dispatching is not "run out of room" — it is **carry on and compact**. Both spend
context, differently, so this is an estimate rather than a reflex.

**Eleven base and derived quantities, defined here and recorded in the log. Each is named for what
it is** — a single-letter scheme reads fine while it is being defined and is unreadable in a row six
months later, so the names below are the ones the log's columns and every extractor use. **A
definition says what a quantity counts; it never says which fields carry it.** That arithmetic is
harness-specific and belongs beside the script that performs it, in each agent's own bootloader —
kept here, a borrowed formula turns into a silent error the moment a harness names its cache fields
the other way round.

- **`first fresh`** — the non-cached input of the child's first request: the uncached parts of
  system and developer instructions, tool schemas, inherited conversation, harness framing and the
  task packet. The framing dominates the packet, so it is measured at the child, never estimated
  from what the packet cost to write.
- **`total fresh`** — the engineer's cumulative **cache-miss input**: input actually processed
  across its requests, cache-hit prefixes excluded.
- **`output`** — its cumulative generation across those requests; reasoning tokens are already
  included where the harness reports them as a subset.
- **`peak context`** — the largest single request's whole input plus its output. **Cached input
  counts**, since cache reuse changes what a request costs to process, not what it occupies.
- **`compactions`** — explicit harness compaction records within the child's own phase. Cache misses
  and cache-prefix regressions do not imply one.
- **`cache regressions` / `replay lower bound`** — consecutive requests whose total input did not
  shrink while the cached prefix fell: how many such falls, and their sum, which lower-bounds the
  input processed a second time. A diagnostic *on* `total fresh`, never a component of it — that
  processing is already counted — and never evidence of a compaction.
- **`report`** — the last output-bearing turn, what comes back to the main agent. It is already part
  of `output` as child generation and counts again as main input in `delegation cost`, because it
  crosses a context boundary.
- **`evidence read`** — task-artifact content the main agent actually loads to accept or integrate
  the result, never the size of an artifact merely named by the report; `~` marks a
  character-derived estimate.
- **`workload` = `total fresh` − `first fresh` + `output`** — processing performed after launch,
  plus all generation.
- **`main intake` = `report` + `evidence read`** — what the main agent receives to understand and
  validate the result.
- **`delegation cost` = `total fresh` + `output` + `report` + `evidence read`** — measurable worker
  processing and generation, plus the returned context the main agent processes. Integration
  reasoning cannot be isolated and is an explicit omission, never an estimate.

The report crossing that boundary is why it appears twice — once as child generation, once as main
input — which is intentional, not double-counting within one context. Four tests follow, all strong
negatives and weak positives, and all context-workload measures rather than currency:

- **Is `workload` large in absolute terms?** The dispatch converts `workload` of main context into a
  worker run plus main intake, so a `workload` of a few thousand saves nothing and still costs
  minutes to dispatch and validate.
- **Is `workload` / `delegation cost` high?** This is measurable delegation efficiency: useful work
  kept out of the main agent divided by the worker and main-intake cost incurred to do so. **Read
  `first fresh` beside it**, because a cold serving cache inflates the denominator without the
  dispatch being any worse — that part is infrastructure, and the main agent's own window pays it
  too, so a low score is only evidence about the task once cache state is accounted for.
- **Is `workload` / `main intake` high?** This is main-context compression: how much work stayed
  outside the main window for each token the main had to receive. A low multiple means the engineer
  relayed rather than concluded — the case a compaction serves better.
- **Did `peak context` leave useful headroom, and were there no compactions?** Compare it with the
  model's context window. Low occupancy can justify keeping a similar task in the main agent or
  combining closely related tasks in one worker to amortize launch cost; a compaction shows that one
  peak did not contain the whole task. Window headroom never overrides dependency, ownership or
  acceptance boundaries.

**So compact instead** where the product *is* the material rather than a conclusion drawn from it;
where the main agent has already loaded the files, so an engineer re-reads them cold and charges a
round trip for it; where the work needs the main agent's judgment at each step; or where the result
must be reconciled against constraints only this session holds and the packet cannot carry.

**Confirm at the session's start that this environment reports per-request input, cache hits and
output.** `report` can be recovered from the parent conversation, but `first fresh`, `total fresh`
and `output` depend on the child harness: without cache-hit input, `total fresh` cannot distinguish
new work from a prefix re-read on every request; without output, `workload` is incomplete. Check
before the first dispatch, not after an unmeasured wave. **No threshold is quoted here** — a figure
lifted away from the rows that produced it outlives the harness behind them, so the numbers stay in
[orchestration-log.md](orchestration-log.md) and are read only when a sizing rule is set or
challenged.

## Roles

- **Main agent** — the user-facing owner of the result. Establishes the objective and the definition
  of done, cuts the dependency graph into waves, writes the packets, validates returned evidence,
  integrates, reports. The only agent that speaks to the user.
- **Engineer** — one bounded task, one deliverable, one report: read-heavy exploration, a focused
  repro, an isolated implementation, fixtures, a sweep.
- **Architect** — an on-demand role, not a layer. Use one where a wave turns on a cross-cutting
  decision: dependency ordering, a shared contract or abstraction, conflicting findings, a failure
  whose cause crosses task boundaries. It returns a decision memo — alternatives, tradeoffs, a
  recommendation, the tasks affected, the validation the decision now owes — and does not track
  status or edit shared files. With limited concurrency it **replaces** an engineer, so spend it on
  a decision, never on routine independent work.

## Who writes what

Concurrency is managed by ownership, not by care. **Two agents never hold the same file open for
writing in one wave** — if two tasks need one file, one owns it and the other returns a patch.

| Artifact | Writer | Why it is single-writer |
|---|---|---|
| `checkpoint.md` | main only | it is the restart interface; a second writer makes the restart state a merge conflict |
| skill docs, shared registries and indexes | main, or exactly one engineer named in the packet | a registry gains rows from several findings at once, and reconciling them is integration work |
| git — branches, commits, pin bumps | main only | `SKILL.md`'s Commit Conventions bind one concern per commit and one branch per submodule, neither visible to a task-local agent |
| a task's exclusive files | that engineer | declared in the packet before the task starts, never after a conflict |
| `/sandbox-tests/<task-id>/` | that engineer | one ignored directory per task, so nothing it writes can collide |
| encoder submodules | nobody | `SKILL.md`'s Read-Only Encoders binds subagents exactly as it binds here |

## The task packet

The packet replaces the conversation: give an engineer this and repository paths, not the session's
history. **A field that cannot be filled in concretely means the task is not ready to delegate** —
that is the whole atomicity test, which is why no separate checklist sits beside this table.

| Field | Required content |
|---|---|
| ID | stable identifier, shared by packet, checkpoint row, artifact directory and report |
| Objective | one question to settle or one artifact to produce |
| Dependencies | accepted task IDs or repository state required before starting |
| Required reads | the governing rules for this task's write scope, and only the sources it needs |
| Inputs | exact versions, fixtures, files, commands, failing samples |
| Write scope | exclusive files, or `read-only` plus the artifact directory |
| Method | the measurement, comparison or constraint that makes the result checkable |
| Predicted workload | `workload`, committed to **before** dispatch so the run can score whether its total workload was foreseen |
| Deliverable | the report, patch, fixtures or evidence expected back — **named for the task, not its genre** (`a3-notes.md`, never `findings.md`), since generic report filenames collide with harness write guards |
| Acceptance | what the main agent will check to accept it |
| Stop conditions | ambiguity, conflicting evidence, scope expansion, a shared file needed — **and any tool refusing an action this packet requires** |

### Required reads are a function of write scope

"A subagent obeys every instruction governing its scope" and "a limited-context agent cannot absorb
the method docs" conflict only while the scope is vague. Narrow the write scope and the read set
collapses with it:

| The task writes | It must read |
|---|---|
| nothing — a survey, a sweep, a repro | the packet |
| a task artifact only | the packet |
| a skill doc | [doc-conventions.md](doc-conventions.md) and that package's root file |
| decoder code | that submodule's skill entry, plus the tier of [encoder-decoder-method.md](encoder-decoder-method.md) its work touches |
| a commit | nothing — commits are the main agent's, so no engineer reads the Commit Conventions |

Where a task needs one rule from a doc it has no other reason to open, **quote the rule — whole,
exceptions included — rather than sending an engineer to read 50KB for a paragraph.** A rule trimmed
to its demand is not a shorter rule but a different one, and an engineer with no other source
applies it literally and correctly, so the false findings return looking like its judgement failing:
the English-Only rule quoted without its "pre-existing non-English content stays as-is" clause
produced 21 findings the rule exempts, while the engineer given it whole reached the opposite, right
answer on the same evidence. Carve-outs that will not fit are the signal to cite the doc instead.
The quote is the main agent's to keep accurate; a stale one is its defect, not the engineer's. And
**quote rules, never paste fetched material** — pasted material is gathering already done, inflating
`first fresh` to hand over work the engineer is then asked to repeat.

### Predicting `workload`, and scoring the prediction

Every measured quantity arrives after dispatch, so the prediction is the one figure committed
beforehand — and an estimate from intuition scores nothing. For work on an encoder/decoder pair,
**derive it from the rules in
[encoder-decoder-method.md](encoder-decoder-method.md) that govern the task**, because what fills a
window is the method a task is forced to follow and that file is where the method is written down.
The rules name their own cost: **T8** is a ladder inside one rule — validate in-tree first, cheap,
and only then build a probe, and which rung is needed is most of the estimate; **T6** forces
instrumentation over reading; **T5** *lowers* the estimate by construction, isolating the combo
before reading what is left; **W6** multiplies by stacked layers, **V1** by era boundaries walked,
and **W7** sets the size a validation set must reach to show anything.

**The same file supplies the acceptance test, from Tier 3** — `S1` size ratio, `S2` characteristic
constructs before and after, `S3` zero-reference bindings, `S6` both halves of `(output, derived
state)`. **A task with no applicable Tier-3 rule has no cheap acceptance test, and that is the
finding**: it is not hard to *do*, it is hard to *accept*, and a task whose completion cannot be
checked independently is not ready to delegate.

**Two rules bear on the split itself.** Tier 2 is titled "deciding what to fix, and in what order" —
the main agent's own work by definition, so a task governed mainly by Tier 2 should not be handed
out. And **`S5`, obfuscator output is randomized by design**, means one engineer's one run can
report a coincidence as a property — how an option in this repository got recorded as doing the
opposite of what it does. Under `S5` the shape is not partition but **replication**: two engineers,
same task, disagreement is the finding.

**The delta is the finding, not the cost**: a window overrun against a low prediction is a
mis-assignment and the packet changes; against a high one the task was genuinely too big and the fix
is to split it. Whether a dispatch fit is **measured, not asked** — which is why the report contract
has no compaction field.

### Recording the dispatch

Everything needed to write a row is here. **The log accumulates without bound, so it is opened to
set or challenge a sizing rule, never to record one** — a session that dispatches reads this section
and appends.

**Every dispatched task gets a row**, including one that errored, stopped, hit a tool guard or was
abandoned: that row spent its cost for nothing, which makes it the most informative kind and the
easiest to omit. **Cost and outcome are two tables, not one row**, because whether a task fit and
whether its answer was trustworthy are independent, and forcing them together makes both unscannable.

**The key is `<date>.<index>`** — `2026-08-16.1`, the index ordering that day's dispatches — and it
is shared by the packet, the artifact directory, the checkpoint row and both tables. A session-local
label like `A1` cannot key an append-only file, since the next wave starts at `A1` too. **The
transcript ID gets its own column**, being what locates the origin data while that data still exists.

**Model, effort, window capacity and `peak context` belong on every row**: capacity is
model-specific and effort moves both request count and output length, so rows lacking them cannot be
compared. **A row carries one model and one effort by restriction, not by measurement** — a dispatch
here is never switched mid-run, so an extractor samples that metadata once and would miss a change
silently; note it on the row if one ever happens. **The predicted `workload` belongs on the row
too**, recorded at dispatch, or a row says what a task processed but not whether that was foreseen.
**A prediction never committed to is not backfilled**, since a retrofitted estimate scores perfectly
by construction and teaches nothing.

**Where the harness cannot report per-request input or cache hits, say so in the row** rather than
leaving a figure blank, and fall back to tool-use count and wall time — proxies that track
`workload` only loosely, so sizing reverts to being asserted.

**`evidence read` is filled after acceptance**, from the main side: an extractor cannot know what the
main will later load, so it prints that column and the two ratios resting on it as placeholders.

### Write through, don't report at the end

An engineer records findings into its artifact directory **as it produces them**, not from memory
once the task is done. A limited-context agent can be compacted mid-task; write-through makes that
cost the last step instead of the whole task, and leaves a stalled or stopped engineer still worth
something. The report is then largely a pointer to what is already on disk.

### The report

One page at most: the verdict, paths to the evidence, and **what the task did not check**. Not raw
logs, not a transcript of the investigation, not a plausible explanation dressed as a finding. The
omission line is the part the main agent cannot reconstruct from the artifacts, and it is what stops
an accepted result from being read as broader than it is.

**Work discovered but not done is reported as a proposal, in that same section.** An engineer that
trips over an independent, costly subtask neither takes it nor spawns anything to take it: it hands
back enough for the main agent to write a packet — what the task would settle, which files it would
touch, why it is independent of the one just finished. Less, and the discovery dies with the
engineer's window; more, and the engineer has quietly expanded its scope.

## Waves

- Parallelize only tasks whose dependencies are accepted and whose write scopes are disjoint. Prefer
  read-only parallelism; parallel writing costs more review than it saves unless ownership is
  genuinely non-overlapping.
- Let `N` be the active-subagent concurrency budget declared by the agent-specific bootloader.
  Start each wave with at most `N - 1` active subagents, reserving one slot for the main agent to
  packet and dispatch independent follow-up work an engineer discovers. The main agent alone may
  fill that reserve. Use the wave's slots only for genuinely independent work, and replace an
  engineer with an architect only where the wave needs a shared decision.
- **A finished turn is not an accepted task.** The main agent validates the evidence, not the
  subagent's authority: re-run the check, read the artifact, or reject and re-scope. Accepting a
  conclusion because it is confident is the failure this workflow exists to make visible. Accept a
  result before unlocking anything that depends on it.
- **Record the acceptance as data, not as prose.** Claims returned against claims accepted is the
  dispatch's *yield*, and every rejection is attributed to the `packet` or to the `engineer` —
  identical symptoms from the report alone, opposite fixes. Yield is independent of the cost ratios
  and is the only measure of whether a dispatch worked, so it is logged beside them
  ([orchestration-log.md](orchestration-log.md)). **Every dispatch is logged, including one that
  errored, stopped or was abandoned** — that row spent its cost for nothing and is the most
  informative kind.
- An engineer that hits a stop condition escalates and stops. It does not expand into neighbouring
  work, rewrite shared planning, edit the checkpoint, or delegate further — **subagents do not spawn
  subagents.** Three reasons, none of them tidiness: a child's result would land in its parent's
  window rather than the main agent's, putting context pressure exactly where the workflow was
  relieving it; the main agent cannot accept or reject evidence it never sees, so a conclusion would
  enter the record on a subagent's authority; and a spawning engineer cannot see the other tasks in
  flight, so it cannot know whether the write scope it hands out is already owned.
- Integrate shared files only after every accepted result that touches them, then run the
  repository's own checks — not merely each task's local check.

## Evaluating the workflow itself

An orchestrated session is evidence about these rules. Record in the checkpoint's evaluation slot
only what could change one — the concrete event, whether a rule prevented or caused it, the
candidate edit — and carry it out of scratch once acted on. The events worth catching are
task-boundary failures, duplicated investigation, main-context pollution, write conflicts, a
rejected subagent conclusion, a failed resumption, and an architect that did or did not earn its
slot. Per `SKILL.md`'s Revise by Evolution, accumulate evidence and then sharpen, merge or supersede
a rule; do not grow this file one incident at a time, and do not edit it while executing an
unrelated task.
