# Studying a New Encoder/Decoder Pair

The workflow for an encoder/decoder relationship not yet studied here. "New pair" names the
relationship, not two new components: an existing encoder with a new decoder is still a new pair.
Read it once per pair. The [decoding rules](../SKILL.md#decoding-rules) apply throughout, [D2](encoder-decoder-method.md#d2-verify-claims-before-acting-on-them) especially; the
incidents behind this workflow are in
[encoder-decoder-incidents.md](encoder-decoder-incidents.md#studying-a-new-encoderdecoder-pair).

## Transform-document acceptance

Read [doc-conventions.md](doc-conventions.md) before writing a transform page. **A transform page is
a reconstruction contract, not a source-location receipt:** a reader without the implementation open
must recover the mechanism's decisions, then use the citations to verify them.

### Engineer: analyze before writing

Do not start by expanding existing prose or assigning one page per source file. Read the
implementation to derive algorithm boundaries and information dependencies first. For each
candidate transform, build a working record before deciding it has a page:

| Field | Question the source must answer |
| --- | --- |
| Target and discriminator | What exact input shape is recognized, and which invariant separates it from a near-neighbour or a safe decline? |
| Input and output | What AST shape, state or representation enters, and what leaves? |
| Ordered algorithm | Which phases run, where do they branch or repeat, what crosses each boundary? |
| State and invariants | Which values evolve, which facts must hold, what terminates a loop or fixpoint? |
| Implementation ownership | Which functions, tables, structures, mutations and generated helpers own each phase? |
| Source ownership | Which spans implement this transform, which coordinate several, which are helpers owned elsewhere? |
| Dependencies | What an earlier pass establishes, why this pass cannot run first, what the next pass consumes |
| Failure and safety | Which conditions decline, throw, fall back, execute recovered code, touch host state, or rely on a sample-specific role? |
| Evidence boundary | Which claims come from source inspection, a committed example, transfer or another named empirical cell? |

Trace from the entry point through every callee that changes those fields, following the success
path and every material exit, catch, fallback, recursion guard and work bound. Connect each symbol to
the decision it implements; a symbol list is not a result. A parameter variation stays in item 3; a
different solution-level algorithm gets its own page.

Classify each cited span as **owned algorithm** (accounts for every material branch), **shared
coordinator** (accounts here only for the decisions that schedule or gate this transform) or
**delegated helper** (names the page that explains it, or an explicit gap). Without these labels two
reviewers can disagree about what the reverse source check covers.

Before writing prose, order the transforms by information dependency and reconcile the records at
their edges: every consumed output has one producer, and every required input names its producer or
is an explicit external assumption. Unowned state, a diagram edge with no source operation, or two
pages claiming one mutation is an analysis defect.

### Engineer: write the reconstruction contract

A page is complete when a cold reader can:

1. identify the accepted input shape, the output representation, and the invariants that separate
   the target from a near-neighbour;
2. replay the algorithm in order, including loops, branches, fixpoints, fallbacks and carried state;
3. map phases to functions, structures, AST shapes, mutations and ownership boundaries;
4. explain why each pipeline dependency exists, what an earlier pass supplies and what a later one
   may assume; and
5. locate every fail-closed condition, execution or side-effect boundary, sample-specific
   assumption, evidence label and generality limit.

| Relationship | Smallest useful form |
| --- | --- |
| A linear sequence whose order matters | Numbered steps |
| Repeated fields, variants, phase-to-symbol ownership, schemas | Table, one row per case |
| Three or more dependent transforms, a branch, a fixpoint or non-trivial state flow | Mermaid diagram, every edge traceable to source |
| One invariant, trade-off or caveat | Prose beside the step it constrains |

A plugin of three or more transforms carries one end-to-end Mermaid dependency diagram at its root;
a transform page adds one only for non-linear internal flow. No decorative charts or duplicated
sequences. Cite closely enough that a reviewer can check each non-obvious phase, edge, invariant and
failure boundary; a broad line range does not make a claim traceable. Line count is a diagnostic,
never the gate: judge depth by distinct decisions, representations and failure paths. A
`source-inspection only` label narrows the evidence claim, not the detail owed.

Before handoff, the engineer performs both halves of the review below and reports any claim that
could not be made traceable, naming the pages, records covered, checks run, and what was not
inspected or executed.

### Main: evaluate and decide acceptance

Main owns the verdict even when a reviewer runs a pass. Evaluate in order; an earlier failure stops
acceptance.

1. **Contract and boundary.** Numbered layout, `## Source`, `## Fixtures`, evidence label, project
   boundary, ownership. Reject a page that widens source inspection into execution, transfer or
   production coverage.
2. **Cold reconstruction.** Without source open, derive the pseudocode, schemas, evolving state,
   dependency order, result and every decline, fallback or execution edge. Record the first point
   that needs guessing; a material guess rejects the page. Write this reconstruction down before
   opening source; a reviewer who already opened it cannot produce the cold half afterwards.
3. **Source fidelity.** Open the pinned source and trace every non-obvious step, edge, row, invariant
   and failure boundary, and the reverse: every material branch in the owned range appears in the
   page or is delegated.
4. **Package integration.** Reconcile the plugin diagram, transform order, cross-page edges, source
   map, navigation, labels and safety boundaries. Run the link, language, layout and source-coverage
   checks, recording each command, its success condition and its result. An unavailable check is
   stated, and blocks acceptance if the contract depends on it.

| Verdict | Meaning |
| --- | --- |
| `rejected` | Not reconstructable; a wrong boundary or dependency; a missing source path; an invented edge; a widened or hidden evidence or safety boundary |
| `accepted with required corrections` | Survives cold and source review; localized citation, naming, navigation or metadata defects must be fixed and rechecked |
| `accepted` | Complete cold reconstruction, every relationship and owned branch accounted, package checks pass. Only this unlocks a dependent task |

Length, diagram count, file count and the engineer's confidence are never acceptance evidence.
Main records the reconstruction and source checks it performed and their exclusions; `completed`
in the task graph means those checks passed, not that a draft arrived.

## Pair workflow

### Preserve evidence and run the unit loop

- **Graduate source-backed knowledge as you go,** independently of qualification and execution.
  Documentation, transfer qualification and reproduction are separate claims; never infer one from
  another. Code or notes may graduate as provenance-cited `documented/incomplete` prior art once
  their source and limits are clear. That neither grants decoder coverage nor opens implementation.
- **Go from unit to combo,** letting whoever is driving pick the next piece. Single-transform
  coverage is a first phase: this project's closed bugs are almost all combo bugs. The unit loop:
  1. if a decoder file already reuses a shared visitor, stop: keep-or-fork is a decision ([F7](encoder-decoder-method.md#f7-a-shared-pass-needs-off-path-cases));
  2. document the encoder side;
  3. write the decoder pass;
  4. document the decoder side;
  5. build fixtures from the encoder's own test cases, and mine them as a measurement: encode every
     upstream fixture for the stage and compare the decoded structure with its source, which has
     twice found a missing reversal on units whose censuses and suites read clean;
  6. pause for review;
  7. commit, then clear context.

### Set the reference version and phases

- **Pin the encoder at its current release; that is the reference cell and the spine ([P2](encoder-decoder-method.md#p2-attribute-era-boundaries-outward-from-a-closed-version)).** Walking
  back into older releases is a later decision driven by prevalence, not completeness. The one
  exception is auditing an incumbent decoder's claimed range, which opens at the newest release
  inside that range.
- **With many versions, cut phases as era slices taken end to end:** study the encoder, verify any
  incumbent, write the decoder. A phase boundary is what the decoder claims, never a kind of work.
  Splitting by behaviour (document all, then verify all, then build) fails three ways: each part
  alone is unfalsifiable (an encoder doc is a hypothesis until a decode inverts it, [D2](encoder-decoder-method.md#d2-verify-claims-before-acting-on-them); a
  verification rests on a residue census, [M1](encoder-decoder-method.md#m1-judge-an-output-by-how-it-reads-against-its-source); a fixture pins a claim, so fixtures before claims are a
  name list); a census written before the encoder study is defined by the thing under test; and one
  late finding forces rewriting a large body of docs.
- **Take the incumbent's claimed range first,** so a failure there is not version drift and later
  failures read as version findings.
- **An incumbent's boundary set is evidence of prevalence,** built from real user-submitted samples
  over years. Era granularity follows prevalence (an era earns a strategy by being met); prevalence
  predicts which refusals fire; whether to cover a range is a prevalence question, asked before
  enlarging a corpus; and "no samples seen" is never recorded as "no change occurred".

### Budget and compose each unit

- **Budget a unit by the questions it must answer,** not by whether code falls out. Two units closed
  with no new code and still cost an encoder doc, an era axis per tag, a census and fixtures. Don't
  read a unit's value off its diff.
- **Budget for composition; the finding is usually there.** Passes clean on their own censuses
  routinely reveal a dependency once run as one pipeline.

### Use incumbent and preset evidence

- **With an incumbent decoder, add three steps between documenting the encoder and writing code, in
  this order:** (a) define this unit's residue census from the encoder side just documented, never
  from the incumbent's description; (b) run the incumbent on the cells exercising this unit and
  record the verdict; (c) read how the incumbent inverts the shape before designing your own.
  - Borrow its algorithms, never its pass order: a unit list taken from an incumbent's order, then
    citing that incumbent as corroboration, had to be re-derived from the encoder's stage order and
    gained a missing unit.
  - The exit is this unit's census reading zero on its own cells plus a fixture-pinned pass; a green
    incumbent run is an input, never an exit.
- **Climb the shipped presets as the combo ladder,** smallest first, largest for final integration.
  A smaller tier can be a distinct shape, so verify the relationship before treating one tier's
  coverage as implying another's.
- **Only encoder-agnostic normalization transfers between decoders:** operator-to-statement,
  sequence splitting, re-bracing. Encoder-specific reversal does not, so never generalize this into
  "search the repo for prior art"; one plugin of about 1,300 lines has about 350 lines of such
  normalization and the rest has no analogue next door.

### Close the package surface

- **Summarize the test suite** in a `tests.md`: framework, structure, directory breakdown.
- **Cross-reference upstream docs, and verify them.** Confirm a shipped `docs/` page matches the
  pinned commit; note, never silently drop, upstream docs describing features the pin lacks.
