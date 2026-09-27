# Studying a New Encoder/Decoder Pair

The workflow for taking on an encoder/decoder relationship not yet studied here. “New pair” names
the relationship, not two new components: an existing encoder paired with a new decoder is still a
new pair. Split out of [encoder-decoder-method.md](encoder-decoder-method.md), which is read every
session and so holds only the labelled rules; this is read once per pair. Those rules still apply
throughout — T8 in particular — and are not repeated here.

Follow the process used for `js-confuser` ([js-confuser.md](js-confuser/js-confuser.md) as a worked
example). T8 applies throughout and is not repeated.

## Transform-document acceptance

Read [doc-conventions.md](doc-conventions.md) before writing a transform page. Its numbered layout
defines where each kind of claim belongs; the acceptance rule here defines how much explanation is
enough. **A transform page is a reconstruction contract, not a source-location receipt.** A reader
who does not have the implementation open must be able to recover the mechanism's decisions and
then use the citations to verify them.

### Engineer: analyze before writing

Do not begin by expanding the existing prose or assigning one page per source file. Read the
implementation to derive algorithm boundaries and information dependencies first; file layout and
line count do not define either one. For each candidate transform, build a working record with these
fields before deciding that it has a page:

| Analysis field | Question the source must answer |
| --- | --- |
| Target and discriminator | What exact input shape is recognized, and which invariant separates it from a near-neighbor or a safe decline? |
| Input and output | What AST shape, state, or intermediate representation enters, and what exact representation leaves? |
| Ordered algorithm | Which phases run, where do they branch or repeat, and what information crosses each boundary? |
| State and invariants | Which values evolve, which facts must remain true, and what terminates a loop or fixpoint? |
| Implementation ownership | Which functions, tables, data structures, AST mutations, and generated helpers own each phase? |
| Source ownership | Which cited spans implement this transform, which coordinate several transforms, and which are helpers delegated to another page? |
| Dependencies | What does an earlier pass establish, why can this pass not run before it, and what does the next pass consume? |
| Failure and safety | Which conditions decline, throw, fall back, execute recovered code, touch host state, or rely on a sample-specific role? |
| Evidence boundary | Which claims come from source inspection, a retained exact example, transfer, or another named empirical cell? |

Trace from the transform's entry point through the callees that change those fields. Follow both the
success path and every material exit, catch, fallback, recursion guard, and work bound. A list of
symbols is not the result: connect each symbol to the algorithmic decision it implements. Use the
source to distinguish a parameter variation from a different solution-level algorithm; the former
stays in item 3, while the latter receives another transform page under
[doc-conventions.md](doc-conventions.md)'s layout rule.

Classify each cited source span as **owned algorithm**, **shared coordinator**, or **delegated
helper** before using it as the page's coverage boundary. An owned span accounts for every material
branch. A coordinator span accounts here only for the decisions that schedule or gate this
transform; its other branches name their owning pages. A delegated helper names the page that
explains it, or an explicit documentation gap when none does. Without those labels, two reviewers
can legitimately disagree about what the reverse source check was supposed to cover.

Before writing prose, order the transforms by information dependency and reconcile the working
records at their edges: every output consumed by another page has one producer, and every required
input either names that producer or is an explicit external assumption. Unowned state, a diagram
edge with no source operation, or two pages claiming the same mutation is an analysis defect, not
something prose should smooth over.

### Engineer: write the reconstruction contract

A page is complete only when a cold reader can:

1. identify the accepted input shape, the output or intermediate representation, and the invariants
   that distinguish the target from a near-neighbor;
2. replay the solution-level algorithm in order, including loops, branches, fixpoints, fallbacks,
   and the state carried from one phase to the next;
3. map those phases to concrete functions, data structures, AST shapes, mutations, and ownership
   boundaries in the source rather than receiving a flat symbol inventory;
4. explain why each pipeline dependency exists, what an earlier pass supplies, and what a later
   pass is allowed to assume; and
5. locate every fail-closed condition, execution or side-effect boundary, sample-specific
   assumption, evidence label, and generality limit without confusing documentary detail with
   empirical qualification.

Choose the representation from the relationship being explained, not from a formatting quota:

| Relationship | Smallest useful form |
| --- | --- |
| A linear sequence whose order carries information | Numbered algorithm or implementation steps |
| Repeated fields, opcode/shape variants, phase-to-symbol ownership, or input/output schemas | Table with one row per case so omissions remain visible |
| Three or more dependent transforms, a branch/fallback decision, a fixpoint, or state that changes across a non-trivial flow | Mermaid flowchart or state diagram with every edge traceable to source |
| One invariant, tradeoff, or bounded caveat | Prose beside the step it constrains |

A plugin composed of three or more transforms therefore carries one end-to-end Mermaid dependency
diagram at its root. A transform page adds its own diagram when its internal control or data flow is
non-linear; a linear page uses ordered steps instead. Do not add decorative charts, duplicate the
same sequence in prose and a diagram, or force every page to contain every form. Conversely, a
paragraph that merely names several functions is not an algorithm, and a `## Source` section with a
broad line range does not make the claims above source-traceable. Attach citations closely enough
that a reviewer can check each non-obvious phase, edge, invariant, and failure boundary.

**Line count is a diagnostic, never the gate.** A large implementation may contain repetition and
need a short page; a small function may encode a dense state transition and need more. Judge depth
by distinct decisions, representations, and failure paths. A `source-inspection only` label narrows
the evidence claim, not the implementation detail owed.

The review is a cold reconstruction followed by a source check: first derive pseudocode, state/IR
schemas, dependencies, and decline behavior from the page alone; then open the pinned source and
verify that every derived relationship is present and every material source branch has an owner in
the explanation. A page that passes only the second half is an index, not accepted transform
documentation.

Before handoff, the engineer performs both halves and reports any claim that could not be made
source-traceable. The handoff names the pages written, the analysis records they cover, the checks
run, and what was not inspected or executed. It does not ask Main to infer completeness from the
amount of prose.

### Main: evaluate and decide acceptance

Main owns the verdict even when an independent reviewer performs one pass. Evaluate in this order;
an earlier failure stops acceptance because later source fidelity cannot rescue an unreadable or
mis-scoped contract.

1. **Contract and boundary check.** Confirm the numbered layout, `## Source`, `## Fixtures`, evidence
   label, project boundary, and plugin/transform ownership. Reject any page that widens source
   inspection into execution, transfer, or production coverage.
2. **Cold reconstruction.** Without source open, derive the transform's pseudocode, input/output
   schemas, evolving state, dependency order, success result, and every named decline/fallback or
   execution edge. Record the first point that requires guessing. A material guess is a rejection,
   even if the missing fact can later be found in source. Persist this reconstruction before source
   access and record an immutable ordering witness such as its digest and write time. A reviewer who
   already opened the implementation cannot manufacture the cold half afterwards; use a fresh
   reviewer or reject that evidence.
3. **Source-fidelity check.** Open the pinned source and trace every non-obvious algorithm step,
   diagram edge, implementation row, invariant, and failure boundary. Check the reverse direction
   too: every material branch in the owned source range must appear in the page or be explicitly
   delegated to another page. A broad permalink that merely contains the symbol does not prove the
   relationship attributed to it.
4. **Package-integration check.** Reconcile the plugin diagram, transform order, cross-page data
   edges, source map, navigation, evidence labels, and safety boundaries. Run the repository's link,
   language, layout, and source-coverage checks. A page can be correct alone and still conflict with
   the package's order or ownership. Record each exact command, its expected success/zero condition,
   and its observed result. An unavailable check is stated as unavailable rather than silently
   omitted, and it blocks acceptance whenever the contract depends on that check.

Use three verdicts only:

| Verdict | Meaning |
| --- | --- |
| `rejected` | The algorithm cannot be reconstructed; a transform boundary or dependency is wrong; a material source path is missing; a diagram edge is invented; or the evidence/safety boundary is widened or hidden. Re-scope or rewrite before integration. |
| `accepted with required corrections` | The mechanism and boundary survive cold and source review, but localized citation, naming, navigation, or metadata defects must be corrected and rechecked before integration. |
| `accepted` | Cold reconstruction is complete, every claimed relationship and owned material branch is source-accounted, package checks pass, and required corrections are closed. Only this verdict unlocks a dependent task. |

Length, diagram count, source-file count, and the engineer's confidence are never acceptance
evidence. Main records the concrete reconstruction and source checks it performed, plus exclusions;
`completed` in the task graph means those checks passed, not that a draft was delivered.

## Pair workflow

### Preserve evidence and establish the unit loop

- **Graduate source-backed knowledge continuously, independently of qualification and execution.**
  Keep documentary status, transfer qualification and reproduction status as separate claims;
  never infer one from another. Valuable code or notes may graduate as provenance-cited
  `documented/incomplete` prior art once their source and limits are clear, even when the current
  environment cannot run them or no same-configuration transfer is qualified. That status neither
  grants decoder coverage nor opens implementation without its own measured deficit and gate.
- **Go incrementally, from unit to combo**, letting whoever is driving pick the next piece rather
  than front-running unrequested sections. Single-transform coverage is a first phase, not a finish
  line: a decoder tested one transform at a time never sees the interactions a later stage's
  residue creates, and this project's closed bugs are almost entirely combo bugs. The unit loop
  that worked: **(1)** stop first if a decoder file already exists reusing a *shared* visitor —
  keep-or-fork is a decision, not a default; **(2)** document the encoder side; **(3)** write the
  decoder pass; **(4)** document the decoder side; **(5)** build fixtures from the *encoder's own*
  test cases, a free and authoritative case list — **and mine them as a measurement, not just as a
  source of cases**: encoding every upstream fixture for a stage and comparing the decoded
  structure against its source has twice found a reversal nobody had noticed was missing, on units
  whose own censuses, corpus and test suite all read clean, because none of them was asking that
  question; **(6)** pause for review; **(7)** commit, then
  clear context.

### Set the reference version and phase boundaries

- **Pin the encoder at its current release and make that your reference cell.** For a pair with no
  package here, that is the whole of the version decision — there are no prior claims to audit, so
  there is nothing to argue for opening anywhere else. Walking *backwards* into older releases is a
  later, separate decision, driven by prevalence rather than by completeness (below); it is not
  part of getting started. `V1` says why some reference has to be closed end to end before any
  comparison means anything.
  - **This project's own history is the exception rather than the pattern, and is easy to
    misread.** Its javascript-obfuscator study opened at `2.19.0` while the pin was `5.5.0`,
    because what it was auditing was an *incumbent decoder's claimed range*, and `2.19.0` was the
    newest release inside that range. Absent an incumbent making claims, that reasoning has no
    input.
- **Where the encoder has many versions, cut the work into phases, and make each phase an era
  slice taken *end to end*.** A phase is not a verification stage: it is one slice of era coverage
  carried all the way through — study the encoder, verify whatever incumbent exists, write the new
  decoder — and the boundary between phases is what the decoder *claims*, not what kind of work it
  contains. Splitting by behaviour instead (document everything, then verify everything, then
  build) fails three ways, and each has been paid for:
  - **Each behaviour alone is unfalsifiable.** An encoder doc written from reading is a hypothesis
    until something inverts it (T8). A verification verdict rests on the residue census, since S4
    rules out runtime correctness as a substitute. And a fixture pins *a claim*, so fixtures built
    before the claims exist are a name inventory.
  - **A census written before the encoder study is defined by the thing under test** — its subject
    list can only come from the decoder's own prose. This is the same trap the three-step incumbent
    loop below exists to avoid, one level up.
  - **Anything else forces a rewrite backwards**: a stage's output is provisional until the next
    stage tests it, so one late finding invalidates a large body of already-written docs.

  **Order the phases so a failure stays interpretable.** Take the range the incumbent already
  claims first: a failure there means the problem is *not* version drift, which is exactly what
  makes a later phase's failure readable as a version finding. `V1` governs the ordering *within* a
  phase's range and constrains which leaps between phases are interpretable at all.
- **An incumbent's boundary set is evidence, and it encodes prevalence.** Boundaries that
  accumulated from real user-submitted samples over years — with issue numbers in the source
  where shapes diverged — are not unverified claims. They carry a second signal free: **which
  versions people actually encounter.** Four consequences:
  - **Era granularity should follow prevalence.** An era earns a strategy by being *met*, not by
    existing.
  - **Prevalence predicts which refusals fire**, so uncovered eras determine the real-world refusal
    rate of a decoder that refuses rather than guessing.
  - **Whether to cover a range at all is a prevalence question, not a completeness one.** Do not
    enlarge a corpus before asking it.
  - **"No samples seen" and "no change occurred" are different findings** and must never be
    recorded as the same one.

### Budget and compose each unit

- **Budget a unit by the questions it has to answer, never by whether a pass falls out of it.**
  Two units here closed with **no new code** — one because a shared visitor imported unchanged
  already did the job, one because two passes an earlier unit had scheduled already performed the
  reversal — and each still cost an encoder doc, an era axis swept per tag, a census built twice,
  and fixtures. The work is establishing *that* nothing is needed, which is the same size as
  writing something. **Do not read a unit's value off the diff it lands**, and expect more of them
  as the pipeline fills in.
- **Budget for the composition step; it is where the finding usually is.** Passes that each read
  clean on their own census routinely surface a real dependency the moment they run as one
  pipeline — an earlier stage's reversal re-opening work a later one had finished, or a pass
  turning out to be another's precondition. Treating composition as a formality after the parts are
  green is how those arrive late. It is the same rule as "a stage's output is provisional until the
  next stage tests it", one level down.

### Use incumbent and preset evidence

- **Where a decoder for this encoder already exists, the loop gains three steps, and their order
  is the point.** Between documenting the encoder side and writing anything, insert: **(a)** define
  this unit's residue census *from the encoder side you just documented* — the construct list is
  encoder knowledge, never the incumbent's description of what it removes, or the census is defined
  by the thing under test; **(b)** run the incumbent over the cells that exercise this unit and
  record the verdict, which only means something once (a) exists; **(c)** read how the incumbent
  *inverts* this shape before designing your own, since a decoder that works is the cheapest
  account of how a shape inverts and beats any probe.
  - **That lends the incumbent's algorithms, never its pass order.** How it recognises and inverts
    a shape is prior art worth adopting; *when* it runs a pass is evidence of nothing. Taking the
    order from it is circular and has been paid for here — a unit list derived from an incumbent's
    pass order, then citing that incumbent as corroboration, had to be re-derived from the
    encoder's stage order and gained a whole missing unit.
  - **The exit criterion is the census reading zero on this unit's own cells, plus a pass that
    exists and is fixture-pinned.** A green run of the *incumbent* is an input to (c), never an
    exit.
- **Respect the preset order.** Climb the shipped tiers as the combo ladder instead of inventing
  one — smallest first, largest reserved for the final integration check. **Don't assume subset
  semantics**: a smaller tier can be a genuinely distinct shape, so verify the relationship before
  treating one tier's coverage as implying another's.
- **Only encoder-agnostic normalization transfers between decoders.** The reusable slice of an
  existing plugin is its *normalization prelude* — operator-to-statement, sequence splitting,
  re-bracing — which every obfuscator's output needs alike, and which is why the shared-visitor
  layer exists at all. Encoder-specific reversal does not transfer, so **do not generalize this
  into "search the repo for prior art"**: one plugin here is ~1325 lines of which ~350 are that
  prelude, and the rest is a keyed state machine with no analogue in the encoder next door. Mining
  it for a string array or a control-flow shape costs time and returns nothing.

### Close the package surface

- **Summarize the test suite** in a `tests.md` — framework, project structure, directory
  breakdown — so readers have somewhere to go when prose needs more precision.
- **Cross-reference upstream docs, but verify them too.** Confirm a shipped `docs/` page still
  matches the pinned commit; note, don't silently drop, any upstream doc describing a feature the
  pinned version lacks.

[Incidents](encoder-decoder-incidents.md#studying-a-new-encoderdecoder-pair)
