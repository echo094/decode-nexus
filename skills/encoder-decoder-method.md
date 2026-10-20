# Encoder/Decoder Method

How to plan, diagnose, fix and measure a decoder for an obfuscating encoder. It applies to every
encoder/decoder pair here and names no single project ([Project Independence](doc-conventions.md#project-boundaries)).

**Each rule opens with one bold line: the rule itself.** The paragraphs beneath it explain how to
apply it. The real bug or wrong plan behind each rule is in
[encoder-decoder-incidents.md](encoder-decoder-incidents.md) under the same label. Read an incident
when someone questions the rule, not every session.

## The rules

| Label | Rule |
|---|---|
| [P1](#p1-work-in-reverse-encoder-stage-order-each-stage-placed-by-its-last-write) | Work in reverse encoder stage order, each stage placed by its last write: fix the last stage first and peel the outermost first; a later stage silently breaks earlier matchers. |
| [P2](#p2-attribute-era-boundaries-outward-from-a-closed-version) | Attribute era boundaries outward from one fully closed version, nearest boundary first. |
| [P3](#p3-each-decoder-removes-only-its-own-additions-by-its-own-encoders-facts) | Each decoder removes only what its own layer or stage added, using only what that encoder used; an addition whose deciding fact only a later decoder can read stays in place as a suspect, read past by every decoder in between and settled by the owner's own rule once that decoder has run. |
| [P4](#p4-every-work-item-names-its-output-measure) | Every work item names the decoded-output measure it should move. |
| [D1](#d1-read-the-tree-and-its-docs-before-you-probe-or-propose) | Read the tree and its owning docs before you probe or propose; what already works or is already decided beats any experiment. |
| [D2](#d2-verify-claims-before-acting-on-them) | A comment, doc, status or spec is a claim; verify it before you act on it. |
| [D3](#d3-instrument-one-real-failure) | Instrument one real failure; never root-cause from reading alone. |
| [D4](#d4-fix-the-producer-not-the-consumer) | Fix the operation that produced the bad shape, not the consumer that tripped on it. |
| [D5](#d5-use-what-earlier-steps-established) | Use what earlier steps established: a proved fact narrows and serves as reference for every later step; never re-derive it from defaults or spelling. |
| [F1](#f1-select-what-the-program-cannot-run-without) | Select what the program cannot run without, never how it is spelled: names, declarators, layout, statement shape, distances and allocated values are spelling; a location is identity to whatever jumps to it. |
| [F2](#f2-resolve-completely-or-not-at-all) | Resolve a matched structure completely or leave it untouched. |
| [F3](#f3-keep-tree-and-derived-state-consistent) | After a pass, derived state must equal what a fresh parse of its output gives. |
| [F4](#f4-keep-a-guard-only-where-a-real-case-needs-it) | Keep a refusal guard or fallback only where an encoder-produced case reaches it. |
| [F5](#f5-one-fix-is-never-the-whole-fix) | Grep for the defect's shape everywhere, and turn the audit into a harness assertion. |
| [F6](#f6-revise-the-owning-rule-never-patch-beside-it) | Revise the rule that owns the behaviour; a special case beside it is a patch the next variant pays again. |
| [F7](#f7-a-shared-pass-needs-off-path-cases) | A pass shared by several decoders needs hand-built cases off every encoder's path that the source language can express, and its normal form must reach both sides of every comparison. |
| [M1](#m1-judge-an-output-by-how-it-reads-against-its-source) | Judge an output by how it reads against its source: a passing run proves nothing, and neither does a changed output, or a count of them, until it is read. |
| [M2](#m2-measure-residue-what-an-encoder-stage-added-and-the-decode-left) | Measure residue, what an encoder stage added and the decode left: size ratios, characteristic construct counts, leftover helpers. |
| [M3](#m3-freeze-the-corpus) | Freeze the corpus before comparing; encoder output is random. |
| [M4](#m4-a-control-must-reach-its-mechanism) | A control proves something only if it reaches the mechanism it names. |

## Why decoders fail silently

Every decoder here **fails closed**: a pass that cannot recognise its shape leaves the input
untouched and moves on. That is right, because a half-rewritten program is worse than an
obfuscated one. But a broken decoder and a working one produce the same runtime behaviour; they
differ only in the shape of the output. A declining pass emits no error, no log line and correct
output. So runtime correctness cannot tell you whether anything decoded ([M1](#m1-judge-an-output-by-how-it-reads-against-its-source)); coupling between
passes is invisible, because the bail-out conditions are the dependency graph ([F4](#f4-keep-a-guard-only-where-a-real-case-needs-it)); and the first
failure hides every cascading one, so the symptom sits several layers from its cause ([D3](#d3-instrument-one-real-failure)).

This method fails the same way. Follow it to a wrong conclusion and there is no error either: a
plausible fix, a green suite, and the real defect one pass upstream. Most signals below read
output, which is only half of what a pass owns; the other half is [F3](#f3-keep-tree-and-derived-state-consistent).

## Find the rule from the symptom

| What you are looking at | Go to |
|---|---|
| Correct-running output, and you don't know whether anything decoded | [M1](#m1-judge-an-output-by-how-it-reads-against-its-source), then [M2](#m2-measure-residue-what-an-encoder-stage-added-and-the-decode-left) |
| A residual obfuscated shape in correct-running output | [D3](#d3-instrument-one-real-failure), bail-out breadcrumb |
| A `TypeError` or `ReferenceError` thrown by the decoded program | [D3](#d3-instrument-one-real-failure), output diff |
| A pass that fires on nothing, or suddenly stopped firing | [P1](#p1-work-in-reverse-encoder-stage-order-each-stage-placed-by-its-last-write) (a later stage rewrote its input), [D3](#d3-instrument-one-real-failure) (the caller's gate) |
| A pass that fails on input our own earlier pass or layer produced | [D4](#d4-fix-the-producer-not-the-consumer), then [P3](#p3-each-decoder-removes-only-its-own-additions-by-its-own-encoders-facts) |
| A guard rejecting something that looks like it should pass | [F4](#f4-keep-a-guard-only-where-a-real-case-needs-it) |
| An "exactly one" gate failing where the encoder makes variants | [F4](#f4-keep-a-guard-only-where-a-real-case-needs-it) |
| A later step guessing what an earlier step already proved | [D5](#d5-use-what-earlier-steps-established) |
| Deciding what to work on next | [P1](#p1-work-in-reverse-encoder-stage-order-each-stage-placed-by-its-last-write) for the stage, [P2](#p2-attribute-era-boundaries-outward-from-a-closed-version) for the era, [P4](#p4-every-work-item-names-its-output-measure) for the measure |
| A version boundary where several era axes turn at once | [P2](#p2-attribute-era-boundaries-outward-from-a-closed-version), then [D3](#d3-instrument-one-real-failure)'s step 5 |
| Several open bugs in one subsystem | [F6](#f6-revise-the-owning-rule-never-patch-beside-it) |
| A gap under a preset but under no single-transform test | [D3](#d3-instrument-one-real-failure), combo isolation |
| A sample that looks obfuscated again after a decode | [P1](#p1-work-in-reverse-encoder-stage-order-each-stage-placed-by-its-last-write) |
| Output that runs, reads clean on every residue axis, and is still wrong | [F2](#f2-resolve-completely-or-not-at-all), [M4](#m4-a-control-must-reach-its-mechanism) |
| A doc, comment or status you are about to rely on | [D2](#d2-verify-claims-before-acting-on-them) |
| A matcher that accepts a fresh parse and rejects your pipeline's tree | [F3](#f3-keep-tree-and-derived-state-consistent) |
| A fix that works and you cannot say why, or only in one position | [D4](#d4-fix-the-producer-not-the-consumer) |
| A change to a pass shared by several decoders | [F7](#f7-a-shared-pass-needs-off-path-cases), then [F6](#f6-revise-the-owning-rule-never-patch-beside-it) |
| A comment telling the caller to do something afterwards | [D2](#d2-verify-claims-before-acting-on-them): count the callers |
| An encoder/decoder pair not yet studied here | [encoder-decoder-newpair.md](encoder-decoder-newpair.md) |

## P — Plan the order

None of these needs a run. They are read from the encoder's stage order and the decoder's own
source, and reaching for a probe to settle one is a mistake in itself.

### P1. Work in reverse encoder stage order, each stage placed by its last write

**Work in reverse encoder stage order, each stage placed by its last write: fix the last stage first and peel the outermost first; a later stage silently breaks earlier matchers.**

Map the encoder's stage order against the decoder's pipeline and fix the last encoder stage first,
asking of each stage what its matcher needs its input to look like. The reason is that anything
later in the encoder's order can invalidate an earlier matcher's assumptions. The failure is silent
and total: a late stage's rewrite preserves semantics and changes only the shape, so the matcher
declines on every application at once. Confirmed forms are a late renaming stage and a late
minifier.

The same order runs the decode. A second encode is a later stage over the whole of the first
encode's output, machinery included, so every fingerprint of the inner layer fails for the same
reason. What makes it tractable is derived, not observed: a second encode cannot change what
existing code does, only add wraps.

- **A defect's size in the output says nothing about where it starts.** A defect contributing
  almost nothing can hold a large one shut. Byte share measures a symptom. This is an order of
  dependency, not of priority: every open shape blocks release, and the order only keeps a stage
  from being worked while a later stage owns its input.
- **Don't troubleshoot a pass whose input still carries a later stage's residue.** Remove that
  residue first; the symptom may not survive it. In a loop (next point but one) the residue's owner
  cannot decide all of it yet: what it cannot decide arrives as published suspects, and the pass
  is troubleshot on its input read past them.
- **Our own pipeline position never sets the order.** "Our pass X runs before Y" is not the
  encoder's stage order and does not mean X's input is clean. Nor does the order the encoder
  invokes its passes in: a stage sits where its last write lands (next point).
- **A stage sits where its last write lands, and one stage can straddle another.** An encoder pass
  can leave a value open for a later step to finish: a label operand carrying an encoding function
  that final address resolution applies, say. Its structure is inner to every stage run in
  between; its finished value is outer to all of them. That is a loop: a stage in between needs a
  fact only the straddling stage's decoder can read, and that decoder sits under the stage in
  between. The inverse splits around it: the stage in between decides what it can and passes the
  rest on, the straddling stage's decoder recovers the fact, and the owner settles the rest
  ([P3](#p3-each-decoder-removes-only-its-own-additions-by-its-own-encoders-facts)).
- **Confirm residue is the encoder's before filing it under an encoder stage.** A decoder pass
  emits shapes too; [D3](#d3-instrument-one-real-failure)'s per-stage replay settles which.
- **Do not probe for the ordering.** A probe cannot beat the order enum, and a misread one
  manufactures confidence.
- **Stage order sets the order between stages, not the units within one.** A stage of several
  transformers is one work unit unless its parts form a decode dependency chain, where one cannot
  be resolved until another has; then it splits along that chain, basis first. A basis unit is
  inert, not broken, on samples whose remaining part belongs to the layer above it. Write the chain
  down next to the unit list, or the split is re-argued at the boundary stage order cannot explain.
- **Documentation follows a different order.** Specifications are written basis first (container
  and grammar before the semantics using them); fixes run in reverse encoder order. Specifying an
  earlier stage first never licenses decoding through a later shape nobody has proved.
- **Encoder option gating does not mean the decoder detects options.** The reversal needs the
  shape, not the option: each pass fires where its shape is present. One fixed composition run to a
  fixpoint has driven every residue axis to zero at every era and option profile here, with no
  per-option branching. Ask whether a unit's passes can be scheduled once, not which options they
  must detect.
- **Layers stack rather than merge.** Once the outer layer is gone, what remains is exactly what
  the inner encode emitted, and every single-layer claim applies unchanged.
- **The loop belongs above any single decoder,** because layers need not come from one encoder.
  Each decoder reports one of three outcomes: clean, a layer remains that is not mine, or mine and
  unreadable. Collapsing those three makes a nested sample undiagnosable. Stop on a round that
  removes nothing.
- **An evaluating reversal is not exempt.** An inner prelude is not runnable alone, since its own
  literals are outer-encoded calls. Repeated encoding therefore costs every strategy a loop and
  decides nothing between them.

Two limits. Runtime equivalence across a peel is not a free oracle, because a wrap can suppress or
kill what the inner layer does (silenced console output, a guard that stops termination). And the
invariant binds the encoder, not us: our normalization re-spells the recovered layer and can trip
that layer's own anti-tamper guard. One option breaks the invariant outright: property renaming
renames properties the program does not own, so the emitted program can simply die. Exclude it from
corpora for that reason.

### P2. Attribute era boundaries outward from a closed version

**Attribute era boundaries outward from one fully closed version, nearest boundary first.**

An encoder has two independent axes. [P1](#p1-work-in-reverse-encoder-stage-order-each-stage-placed-by-its-last-write) orders work along the stage axis; [P2](#p2-attribute-era-boundaries-outward-from-a-closed-version) orders it along the
version axis, deciding which era boundary to attribute first. Close one version end to end first;
it is the **spine** that every comparison is read against. For a new pair the spine is the
encoder's current release ([encoder-decoder-newpair.md](encoder-decoder-newpair.md)).

- **Attribute the nearest boundary before crossing the next.** Data may be gathered in any order;
  reading may not. An unattributed difference at the nearest boundary is inherited by every
  comparison beyond it, so a distant version showing eleven differences may be ten new plus one
  carried down. The nearest boundary is also the cheapest, since one era change separates the pair.
- **Difference count is not signal strength.** Starting where most cells differ is [P1](#p1-work-in-reverse-encoder-stage-order-each-stage-placed-by-its-last-write)'s byte-share
  error on the version axis.
- **"Nearest" means nearest era boundary**, not nearest version number. With no sample between two
  versions you have a bracket, not a boundary, and adding the version that separates candidates is
  itself the experiment.
- **Run the reference version first,** and **fix a known defect in your own pipeline before
  attributing anything past it.** Readings are usually taken by removing a pass and watching what
  breaks, so your own bug can be the thing being measured.
- **When several era axes turn at one boundary, compare which option sets moved.** A transform's
  own axis flips only the sets enabling it; a shared subsystem's change flips every set that reads
  it. Prefer a per-feature set, because a maximal profile is often already failing for another
  reason.
- **A maximal option profile decides pass order, not coverage.** Every lesser profile is the
  all-on dependency graph with nodes removed, so the order derived there generalizes. Shapes do
  not: options interact, and one all-on cell emitted no string-array subsystem at all.
- **Two eras collapse for decoding only if one's reversal is the spine's minus a pass, with the
  surviving passes' order and levels unchanged.** Removing a node can merge two levels or reorder
  survivors inside one, so check the order separately. Collapse is a result of the study, never an
  input read off a pipeline signature (a shape change is invisible to the dependency graph). It
  licenses no coverage reduction (confirm a shape at both ends of its claimed range), no re-encode
  of a frozen corpus, and no significance marking in the era registry.
- **A phase that leaps from the spine to a far version skips every boundary between.** If the leap
  is taken anyway, the skipped range is a prerequisite for reading its failures, not follow-up work.

### P3. Each decoder removes only its own additions, by its own encoder's facts

**Each decoder removes only what its own layer or stage added, using only what that encoder used. An addition whose deciding fact only a later decoder can read stays in place as a suspect: every decoder in between reads past it, and the owner's own rule settles it once that decoder has run, never by guess or reachability.**

- **Each layer's decoder reads and rewrites only its own layer.** Mutating still-encoded inner
  machinery corrupts it, and corruption is silent where a decline leaves countable residue.
- **A stage inside one encode peels the same way.** A stage's decoder returns what the stage
  received, minus what the stage added. Earlier stages' code passing through is not its concern: it
  neither keeps nor restores it, and losing some of it (dead code, say) as a by-product of removing
  its own additions is acceptable when that takes no code of its own. A later consumer that reads
  such code depends on a fact no stage promises; that consumer is the defect
  ([D4](#d4-fix-the-producer-not-the-consumer)), and teaching the stage decoder an earlier stage's
  shapes couples the two.
- **A stage's decoder uses only what its encoder used.** Read the stage's source for what it
  consumes (widths, labels, operands, a cipher) and decode with exactly that; a fact it never used
  (register meaning, jump targets, another stage's proof) is another stage's to decide. Reachability
  decides nothing in the inverse of a transform that does not sense it: a transform that treats
  reachable and unreachable code alike is inverted alike, and recognizes what it injected from its
  own placement facts. Reachability is decided once, over the recovered canonical program. Where
  those facts leave an addition ambiguous, find the encoder fact that bounds it (what a block can
  start with, say) before reaching for another stage's knowledge. If only a later decoder can
  read that fact, the addition is a suspect (next point), not a guess.
- **A suspect waits for its fact.** The stage that cannot decide keeps the entry in place and passes
  it on by address, carried through every later address map. The decoders in between read past
  it through that published set, never by recognizing its shape or reading its layout
  ([F1](#f1-select-what-the-program-cannot-run-without),
  [D4](#d4-fix-the-producer-not-the-consumer)); right after the
  decoder that recovers the fact, the owner's own rule runs again with it and removes what it now
  proves. A suspect is never removed early and never charged as residue
  ([M2](#m2-measure-residue-what-an-encoder-stage-added-and-the-decode-left)). Readable now means
  decide now: a fact the stage can recover by its own encoder's rules (a direct jump target, say)
  leaves nothing to defer.
- **The coordinator owns layer ordering; the input contract owns normalization.** Before inner
  recognition, normalize the producer leftovers a matcher that selects what the program cannot run
  without ([F1](#f1-select-what-the-program-cannot-run-without)) still cannot read, such as computed
  literal keys, into the ordinary JavaScript forms that consumer requires. Hoisted declarations
  are not such a leftover: the defining write is read directly. A consumer
  plugin can run pre-operation visitors from a separate internal file. Their suitability is
  established for that consumer; another plugin needs its own input-contract and test assessment,
  not an assumed universal normalization pipeline. Never teach the inner recognizer an
  outer-specific dialect; that couples two decoders and is paid again for every outer encoder.
- **A pipeline-wide behaviour-neutral rewrite is not a layer crossing.** Deleting `debugger`, say,
  applies to every layer. The inner recognizer matches modulo such rewrites rather than asking the
  outer pass to skip them.

### P4. Every work item names its output measure

**Every work item names the decoded-output measure it should move.**

Before a work item starts, name the [M2](#m2-measure-residue-what-an-encoder-stage-added-and-the-decode-left) measure it should change on real samples (a residue count
falling, a size ratio shrinking, a helper disappearing) and the samples it is read on. The item is
done when that measure moves and every other output it changes has been read against its source ([M1](#m1-judge-an-output-by-how-it-reads-against-its-source)). Proofs, refusal controls, qualification runs
and harnesses support a decode; they are not progress on their own, and a plan whose items name no
output measure cannot show that the output is getting better.

## D — Diagnose

### D1. Read the tree and its docs before you probe or propose

**Read the tree, its owning docs and the encoder stage that added the shape before you probe or propose; what already works or is already decided beats any experiment.**

Validate a plan in this order. First, grep the packages and the decoder for the subject: a matcher
that already does the job correctly is free, stronger than a probe, and also answers who owns the
reversal ([D4](#d4-fix-the-producer-not-the-consumer)). An open item may already be answered in a doc the same study wrote. Before
proposing a remedy, read the contract of the component it would change: a recommendation that
contradicts a recorded decision reverses that decision, which only the user may do. Read the
encoder stage that added the shape as well, its doc first, then its source: what the stage
guarantees about its addition (a field it writes that nothing reads, say) usually decides the
remedy. Remove that addition first ([P1](#p1-work-in-reverse-encoder-stage-order-each-stage-placed-by-its-last-write)):
left in place, it stays in every later decoding step's input, together with what later encoder
stages did to it, and each of those shapes needs its own treatment (a decoy store a minifier later
moved and whose parameter it reused, read through by a flow analysis across both stages). Then run a
throwaway probe: reading and probing find different kinds of thing, so budget for both, and keep
the recipe rather than the script, since a kept script silently stops matching the current code.
Whichever way the probe reads, suspect the sample and the oracle before the code: check the
denominator ([M3](#m3-freeze-the-corpus)), and check the oracle measures liveness rather than presence.

### D2. Verify claims before acting on them

**A comment, doc, status or spec is a claim; verify it before you act on it.**

A comment, a doc or a "covered" status described intent when it was written; its target can
change under it silently. Never document a mechanism from memory or inference.

- **Distrust most a guard comment saying something is impossible.** "By design" describes the
  operation the guard was written for, never everything it now blocks ([F4](#f4-keep-a-guard-only-where-a-real-case-needs-it)). Copying one into a
  skill doc turns a hypothesis into a documented limit.
- **A comment stating a caller obligation is a defect report.** "Reload afterwards", "call this
  before X": it is almost always a repair the pass declined to do. Count the callers; the ones not
  paying it are the finding.
- **A claimed necessity is a claim to measure.** A comment saying an order is load-bearing is the
  same object as a guard saying a shape is impossible. Write the measurement beside the claim or
  do not make it.
- **A status is only as strong as its criterion.** Anything closed on runtime correctness alone was
  closed on nothing ([M1](#m1-judge-an-output-by-how-it-reads-against-its-source)).
- **A specification is not validated until something runs against it.** Reading confirms only
  that it is internally coherent. For an encoder doc, a decode attempt against real stacked output
  is the verification ([`SKILL.md` gate 4](../SKILL.md#gates) applies this to a pin).
- **Missing evidence is unqualified, not disproven.** Do not turn a gap, or a result our own defect
  could explain, into a verdict about the encoder. Find our defect first ([D4](#d4-fix-the-producer-not-the-consumer)), then decide.

### D3. Instrument one real failure

**Instrument one real failure; never root-cause from reading alone.**

Every cause found here so far was found by breadcrumbing a real failure, none by an isolation
matrix. A residual shape proves that something failed, never what. Pick the instrument by what the
failure looks like:

| Question | Instrument | Note |
|---|---|---|
| Which guard rejected this shape? | Bail-out breadcrumb | Tag every `return null` with its own source line |
| Which stage made the output look like this? | Replay the pipeline stage by stage on one real sample, printing size and a structural count ([M2](#m2-measure-residue-what-an-encoder-stage-added-and-the-decode-left)) | A stage that should shrink and reads `+0` never fired; a stage that grows the output is a finding. Build it before reading any matcher |
| Is this residue ours or the encoder's? | The same per-stage replay | Never input-vs-output counting: it fails while an outer layer still hides the construct |
| Did the fix even run? | The breadcrumb, asked of the caller | A correct fix that never executes gives byte-identical output |
| The pass ran and the output is wrong | Before/after diff at the site the error names | A guard counter cannot see this |
| Two mechanisms could explain one symptom | Differential diagnosis, below | The plausible one wins by default unless tested |
| Is my reading of optimized output right? | Re-encode the same source, options and seed without the final optimizer | Same allocations, the encoder's own comments intact: a truth oracle, valid only when the optimizer runs last and draws no randomness |

**Differential diagnosis.** Each step removes a candidate; the earliest can end the search.

1. **Run the artifact untouched.** If it already misbehaves alone, nothing downstream is implicated.
2. **Test that the accused shape is present,** with a positive control that carries it.
3. **Bisect your own operations** one at a time from none applied.
4. **Hold the rival explanation constant** and vary only the suspect.
5. **Sweep the axis to bound the range, and read the bound as a candidate.** A bound landing
   exactly on a known boundary feels like an answer and is not, because boundaries cluster. Your
   bound is only as tight as your sample spacing. Sweep every axis, not only the family the
   subsystem makes salient. Then diff the source between the two versions, since a component nobody
   swept has no axis to report. When several candidates share a bound, switch axes: find a version
   or option where one moved and the others did not. Until then the verdict is "confounded", which
   is not "unexplained". Only a full sweep plus an empty source diff earns "something undocumented".

**Combo gaps.** When a gap appears under a preset but under no single-transform test and there is
no failing site to breadcrumb, isolate it empirically. Fix one small source and a base combo known
to decode cleanly; add one candidate transform at a time at full strength (`1`/`true`, never a
probability), judge each by [M2](#m2-measure-residue-what-an-encoder-stage-added-and-the-decode-left) over three or more runs; the addition that flips the verdict is the
trigger; then shrink the reproducing combo one transform at a time. Read encoder source only after
that. A cause can need a second transform present, which a one-at-a-time matrix never reaches.

**Five ways the instrument lies.**

| Lie | Correction |
|---|---|
| A bail tally measures the pipeline's interior, not its output | A decline is not a defect until an output census says so; a declining gate can be load-bearing |
| A tally names the gate, never the thing | Print one offending candidate's bindings before writing a cause down |
| A pass with no candidates looks like one that resolved everything | Census inside the pass first; establish the population is non-zero |
| A breadcrumb filtered by name inverts its answer | Dump every call with its resolved binding's location ([F1](#f1-select-what-the-program-cannot-run-without)) |
| A guard counter cannot see a failure after a successful match | Instrument the catch blocks; a caught exception reads as a clean pass |

### D4. Fix the producer, not the consumer

**Fix the operation that produced the bad shape, not the consumer that tripped on it.**

When a pass cannot match what an earlier pass or layer left, the reflex is to teach the matcher in
front of you to tolerate it. That is the last option, because it is the same fix paid again at
every consumer. Diagnose first:

| Case | Remedy |
|---|---|
| 1. The producing operation emits a wrong shape | Fix that operation |
| 2. The input does not exist yet, but will | Reschedule the pass, possibly to run twice; in a loop, the owner runs again after the decoder that recovers its fact |
| 3. The producer is correct but lacks a fact | Route the fact to the pass that owns the reversal and call it directly |
| 4. None of the above | Tolerate it in the consumer, knowing you will pay again |

Empirically the cause has always been case 1 or 2: a shape one of our own passes emitted, never a
matcher merely too narrow. So a failure at one of our own handoffs, including a layer handoff ([P3](#p3-each-decoder-removes-only-its-own-additions-by-its-own-encoders-facts)),
is our defect until shown otherwise. Diagnose the producer before anything else; a qualification
run or a widened consumer is not an answer to it.

- **"The producer" is the operation that mutates, never the composition that schedules it.** Every
  defect originates at a mutation of the tree or of its derived state. A file that only schedules
  cannot be the origin. The one-second check: open the file you are about to edit and find the
  operation that causes the defect; if it is not there, you are at the wrong level.
- **Separate case 1 from case 2 explicitly.** Case 1 is a wrong operation, fixed at that operation.
  Case 2 is a right operation at the wrong time, and is the only case a scheduler-level fix is
  correct for. Establish the operation is sound before reaching for the scheduler.
- **A loop is case 2, not case 4.** When a stage's deciding fact is recovered only by a later
  decoder ([P1](#p1-work-in-reverse-encoder-stage-order-each-stage-placed-by-its-last-write)'s
  straddling stage), the owner publishes what it cannot decide and runs its rule again after that
  decoder. The decoders in between read past the published suspects
  ([P3](#p3-each-decoder-removes-only-its-own-additions-by-its-own-encoders-facts)): that is reading the producer's contract, not tolerating a bad shape, as long
  as each reads the published set and none recognizes the shape on its own.
- **Separate case 1 from case 3 too.** The tell is whether the upstream pass is wrong or merely
  stopped. Case 3 creates a direct call dependency and mutates before the calling matcher has
  confirmed its own match; decide what happens to that mutation if the match then fails.
- **A shape the producer's documented contract emits is not a bad shape.** When a contract defines
  the form its consumers must read, the consumer that cannot read it is the defect; check the
  contract before naming the producer.
- **A producer can be wrong while its output is right.** It can leave derived state inconsistent
  with the tree it rewrote ([F3](#f3-keep-tree-and-derived-state-consistent)). Ask what a pass leaves behind besides its output before ruling
  out case 1.
- **A fix you cannot explain is a defect report.** A repair that works only in one position is
  probably compensating for something upstream. A repair at a composition is the trap: it greens
  the suite and is perfectly explicable, so prefer the one-second check to the outcome.
- **Case 4 is right only for a re-spelling the encoder emits,** where there is no producer of ours
  to fix. It stays bounded because the encoder's set is closed and readable from source: enumerate
  what it can emit before widening.
- **Your instrument's resolution bounds the answer.** A per-pass probe can only accuse a pass;
  descend to the operation before attributing ([probes.md](decode-js/probes.md)).

### D5. Use what earlier steps established

**Use what earlier steps established: a proved fact narrows and serves as reference for every later step; never re-derive it from defaults or spelling.**

A fact an earlier step has proved (an identified role, a matched table, a resolved index) is an
input to every later step. It narrows the unknown population, since what is left is what remains to
identify, and it is the reference the rest is identified against. A later step that guesses the
same fact again from a default or a spelling is [D4](#d4-fix-the-producer-not-the-consumer)'s case
3 seen from the consumer: the fact exists and was never routed. So identify the cheapest certain
members first, then let them constrain the rest, and check that every consumer reads the
established fact rather than its default.

## F — Fix

### F1. Select what the program cannot run without

**Select what the program cannot run without, never how it is spelled: names, declarators, layout, statement shape, distances and allocated values are spelling; a location is identity to whatever jumps to it.**

Every encoder stage, a later layer's included, adds complexity and keeps the program's behaviour in a
production environment, so behaviour is the only invariant; a debug-only statement and a check that
always passes in a normal environment are not behaviour either. A role is identified by the
conditions whose violation would break the program: a binding written exactly once, before any
read, whose value has the role's shape and is used where the role is used.
A control merge is the block every continuing path must pass, not the block nearest both arms.
Name text, declaration form, initializer placement, braces, member spelling, block order and block
distances are spellings an encoder, a later layer or our own passes can vary; matching on them
makes a valid program decline or pick a wrong structure. Read the defining write, not the
declarator; the postdominator, not the distance.

The audit is a grep, not a review ([F5](#f5-one-fix-is-never-the-whole-fix)). Seven traps survive knowing the rule:

- **A name a matcher resolved is still a name.** Holding the target as a string resolves nothing;
  every same-named identifier in reach answers to it. Compare the binding object.
- **Declaration sites are not references.** A declarator id, a function name and a nested
  parameter are bindings, not uses. Counting references without `isReferencedIdentifier()` reads
  all three as uses and fails closed everywhere in scope.
- **Source positions are the same trap.** Earlier passes reparse bodies and synthesize statements,
  so `node.start`/`node.end` are often absent or fragment-relative. Ask the path ancestry.
- **Cached scope state can point at a detached node** that still prints identically to the live
  one, so identity comparisons fail silently. The tell: it accepts every hand-built case and rejects
  every real one, or accepts a re-parsed tree and rejects the live one. Ask the live tree a
  structural question instead ([F3](#f3-keep-tree-and-derived-state-consistent)).
- **A value the encoder allocates is spelling.** Opcode numbers, label values, their ranges,
  contiguity and allocation order can all be randomized; identify a role by what its code does,
  never by where its value falls.
- **After a whole-program optimizer, statement shape is spelling.** The optimizer rewrites each
  function on its own and folds or keeps locals by their content, so two bodies cut from one
  template diverge. Compare effects, not statements: reads as ordered slots, locals as carriers.
- **An address is spelling to a matcher and identity to a jump.** Never select a role by where it
  sits, and never renumber or drop a location unless every reference to it is rewritten, including
  encoded or computed ones the current stage cannot read. "Nothing visible jumps here" proves
  nothing. Keep the encoder's final address as each instruction's identity, translate every
  reference through it, and make a reference to a removed location refuse instead of landing on
  the next one.

### F2. Resolve completely or not at all

**Resolve a matched structure completely or leave it untouched.**

If the input for part of a match is missing, schedule a second visit for when it exists. Leaving
the structure alone is cheap and safe; a half-way state is neither. Half-resolution manufactures two
entities from one: downstream matchers key on spelling, so one storage slot spelled two ways becomes
two slots, and a later pass treats them as unrelated. This is [P1](#p1-work-in-reverse-encoder-stage-order-each-stage-placed-by-its-last-write)'s failure with the agency
reversed, our own pass changing a spelling under our own later pass, and it looks like progress on
every residue measure ([M4](#m4-a-control-must-reach-its-mechanism) has the checks that catch it). Define the unit of atomicity for every
transform ([doc-conventions.md](doc-conventions.md)).

### F3. Keep tree and derived state consistent

**After a pass, derived state must equal what a fresh parse of its output gives.**

A pass rewrites the tree and the derived state kept beside it: cached paths, scope bindings,
reference sets. Leave that state stale and the text is perfect while every later pass decides
against a program that no longer exists. Output checks are structurally blind to this, and "output
unchanged" is not "nothing happened".

- **Scope the check by who reads the state.** State no later pass consults needs no assertion.
- **The cheap checks lie.** A detached reference reports `removed === false` and its cached parent
  chain still reaches a Program path. Ask whether its node is reachable from the live program.
- **A serialize→parse boundary repairs this class silently,** so a measurement taken across one is
  evidence about a different program.
- **The repair belongs to the operation that breaks the invariant** ([D4](#d4-fix-the-producer-not-the-consumer)), and the check belongs in
  the shared test harness ([F5](#f5-one-fix-is-never-the-whole-fix)).

### F4. Keep a guard only where a real case needs it

**Keep a refusal guard or fallback only where an encoder-produced case reaches it.**

Ask two questions of every early `return null`: what upstream state makes it fire, and what is it
protecting, and is that what I am doing? A fail-closed rule outlives the operation it was written
for: it goes on blocking a different operation that needs none of its protection, and gets misread
from the other side as proof that a shape cannot be resolved. A comment asserting a constraint is
the same object as a guard ([D2](#d2-verify-claims-before-acting-on-them)).

Place guards at the boundary they protect. For an owned decoder chain, recognize the source by its
distinctive structure and required parts, then trust the records our own stages build: test those
stages and the end-to-end output rather than revalidating every record at every handoff. Keep checks
that decide whether source semantics are supported, whether analysis covers the admitted input and
whether emission is complete. Keep a refusal guard only when an encoder-produced source reaches it
through the normal entry and a test pins that. A hand-edited source no encoder can emit, or a mutated
private record, does not justify a guard, and neither does a reviewer's request for completeness.
A separately supplied model crosses a new boundary and needs its own contract.

A uniqueness requirement is a guard too, and it fails on populations the encoder grows by cloning:
the original and its variants all fit. Before requiring exactly one, ask whether the encoder emits
variants; prefer the most general member, and treat behaviourally equal members as one. A fallback
route is a guard's twin: before removing one, disable it on a scratch copy and rerun the census and
fixtures with a reach log. Only what still decides through it needs covering first.

Reading guards this way is the only way coupling between passes gets written down, since docs
describe what a pass does when it succeeds. It also shows which passes cannot be measured until an
earlier gap is fixed, and so which experiments not to run yet.

### F5. One fix is never the whole fix

**Grep for the defect's shape everywhere, and turn the audit into a harness assertion.**

A defect's shape almost never occurs once. Grep for the shape across the pipeline before closing
the item. Where the condition is computable, make the audit an assertion in the shared test helper
every case runs through: a grep is one-time and only as good as its pattern, while a harness
assertion audits the whole suite and everything added later. Where a defect is invisible in output
([F3](#f3-keep-tree-and-derived-state-consistent)), build that detector before the fix: then it demonstrates the defect, where built afterwards it
can only ratify a fix already chosen.

### F6. Revise the owning rule, never patch beside it

**Revise the rule that owns the behaviour; a special case beside it is a patch the next variant pays again.**

A single defect is already the first member of a cluster. A special case for the shape in front of
you (a straight-line handler, a loop's exit test) fixes that shape and leaves the rule that
mis-decided it in place for the next one; revising the rule (a try statement as one unit, merges at
the immediate postdominator) fixes the class. When bugs do cluster, price one refactor against all
the patches.

Ask what a cluster shares in how the code represents something, not in what the bugs do. Each patch
is cheap, which is exactly why the shared cause never gets priced. A workaround repeated across
several consumers of one pass is the same cluster in disguise: each consumer works, so the cause is
never nominated. Count the consumers paying it and the ones silently not paying. "They already work
around it" reads N copies of a fix as evidence the fix belongs there, which inverts this rule. When
every member consumes one half-reversed shape, [D4](#d4-fix-the-producer-not-the-consumer) beats a refactor: fix the producer and the
cluster disappears.

### F7. A shared pass needs off-path cases

**A pass shared by several decoders needs hand-built cases off every encoder's path that the
source language can express, and its normal form must reach both sides of every comparison.**

A matcher validated only on an isolated single-transform fixture is not proven against combined
output, which adds exactly the later stages that break it. And a matcher validated on one encoder's
whole corpus is not proven sound once another decoder shares it: that encoder's regularities are
invisible from inside, its gaps are the inputs it cannot produce, so every census reads clean.
Judge a shared pass on hand-built cases that leave the encoder's path, chiefly where it would
corrupt or throw instead of declining. A case must be a shape some producer of the source language
could emit: one the language cannot express (a catch entered from outside its try, a try statement
with a second normal completion) is no case, and a test pinning it designs the pass for an input
no producer emits. Before changing a shared pass, enumerate its consumers and
read what each already does to work around it ([F6](#f6-revise-the-owning-rule-never-patch-beside-it)). Field reports are evidence no corpus replaces.

A normal form belongs to the comparison, not to one side. A canonicalizing step in a shared pass
must reach both sides of every comparison its consumers make (templates, forms a consumer builds
after its own substitution), or it manufactures the differences it was meant to remove.

## M — Measure readability

**A decode is worth how well its output reads against the source.** Every measure below serves
that question and none replaces reading the output. They are cheap measurements answering "did
this decode, or did it just not break?" — usable before there is a trustworthy expected output. All of [M2](#m2-measure-residue-what-an-encoder-stage-added-and-the-decode-left) measures residue; [F2](#f2-resolve-completely-or-not-at-all) and [M4](#m4-a-control-must-reach-its-mechanism) cover the case where a decode
is wrong with no residue, and [F3](#f3-keep-tree-and-derived-state-consistent) covers what output cannot show.

### M1. Judge an output by how it reads against its source

**Judge an output by how it reads against its source: a passing run proves nothing, and neither does a changed output, or a count of them, until it is read.**

Passthrough always runs correctly, so a green behaviour check cannot tell "decoded" from "safely
didn't decode". Judge by [M2](#m2-measure-residue-what-an-encoder-stage-added-and-the-decode-left). Runtime equality is still a real regression guard after a fix.

The converse holds too. A changed, even worse-looking, output is a finding, not a regression: group
the changes by structural signature, read one diff per group against the source, and run the
behaviour oracle before judging. A merge rule that restored the source's guard clauses changed 39
fixture outputs, every one an improvement; byte-identity would have flagged all of them.

**Nor does a count of changes value a design.** Choosing between candidate rules comes down to one
question: does the output's readability deteriorate? Read each changed output against its source,
grouped by structural signature, with the readability metrics beside it. A tally of the fixtures
each candidate breaks or keeps adds up unread changes, and can charge one candidate for a defect in
another rule it leans on. So a design change lands with its fixture regression: encoder-built
fixtures, committed failing before the change, that assert the decision the rule makes ([M4](#m4-a-control-must-reach-its-mechanism)) and
pin the readable form it produces.

### M2. Measure residue: what an encoder stage added and the decode left

**Measure residue, what an encoder stage added and the decode left: size ratios, characteristic construct counts, leftover helpers.**

- **Residue is what an encoder stage added.** Against a no-option baseline, count what is extra;
  earlier-stage code a stage decoder dropped as a by-product ([P3](#p3-each-decoder-removes-only-its-own-additions-by-its-own-encoders-facts)) is missing, not residue.
  An addition no stage can decide yet is a suspect, not residue, until its owner's rule settles it.
- **Size ratios.** Decoded size over pre-obfuscation source: a multiple in the hundreds means whole
  mechanisms were never reversed (some growth from renaming or injected dead code is legitimate).
  Decoded size over obfuscated input: if decoding barely shrinks the file, little was reversed; this
  one needs no source, so it works on real-world samples. Take the calibration pair from the run in
  front of you. Keep `<name>.src.js` beside each fixture so the first ratio stays computable. A
  ratio compares only within one frozen corpus.
- **Characteristic construct counts,** before and after: `switch` and `while` for control-flow
  flattening; sequence expressions for dispatchers; bracket-member reads and array-index lookups for
  string concealing; `Function(` and `eval(` for packers. Never a regex for a partial decode's
  residue, which reads "clean" both when a decode finished and when it never started. Pick a count
  that can move before the fix is finished, and switch axes once a count saturates.
- **Leftover helpers.** A runtime helper the decoder should consume must end with zero references
  and be gone. Unreferenced does not mean missed: obfuscators emit dead helpers, so check whether it
  was ever live in the input. But the same zero-reference helper is what a cleanup sweep leaves when
  its deletion gate keys on a spelling an earlier pass stopped emitting; when a matcher moves to
  resolving by binding, audit that pass's deletion gates in the same change. Referenced does not
  mean live either: every reference can sit inside another undecoded layer, so chase the residue
  holding it alive.
- **Structure against the source.** For recovered control, count what the source wrote against
  what the output wrote: loops, guard clauses against `if`/`else`, sibling against nested
  statements, synthetic labels and leftover dispatch loops. An output can keep behaviour with
  every residue at zero and still read worse.

### M3. Freeze the corpus

**Freeze the corpus before comparing; encoder output is random.**

Names, state vectors, keys and case order regenerate per run, and many transforms are
probability-gated, so a transform at full strength may still not fire on a given source. Use three
to five runs per side for any verdict you will act on. Two fresh encodes are not comparable at all.
A case encoded afresh inside a throwaway command is not frozen even when the encoder draws no
randomness: nothing records it, so no figure from it reproduces. Save the case and its generation
record before comparing.
This compounds across an isolation matrix: a grid reading clean may only mean every short run missed
the payload.

### M4. A control must reach its mechanism

**A control proves something only if it reaches the mechanism it names.**

A positive control, a case built to make something fail, can silently miss in two ways: its damage
is of a kind the named check is blind to, so a different check takes the credit while the status
reads as expected; or the probe's own scaffolding changes the property under test. So assert the
diagnostic, not the outcome, and prove that assertion can fail by feeding it a case that should not
match. A probe reporting the answer you wanted needs this most, because nothing prompts the question.
A case checked only for success can be passed by a different change in the same build; assert the
decision of the rule it was built for.

An evaluating reversal that misses one component of the machinery it runs is wrong with no residue:
extract a string array's holder and accessor but miss the rotator, and every call returns a real
string, the wrong one. Three checks catch it on real samples with no expected output:

- **Self-validating machinery proves its own extraction.** A component that searches until a
  checksum matches cannot terminate on wrong data, so non-termination means incomplete extraction.
  That is why timeouts are mandatory. This reading outranks "anti-tamper detected re-spelled code",
  which is always available and wins on reputation; run [D3](#d3-instrument-one-real-failure)'s differential diagnosis rather than
  arguing it.
- **Count entities, not fragments.** A collector that hollows each match to mark it consumed but
  iterates per reference emits the same entity twice, whole and hollow. A gate counting collected
  pieces reads the duplicate as abundance.
- **A decoded string in computed-member-key position must be a valid identifier,** since the
  encoder put a real property name there.

## Former labels

| Former | Now | Former | Now | Former | Now |
|---|---|---|---|---|---|
| T1 · W4 | P1 | T8 | D1, D2, M4 | S1, S2, S3 | M2 |
| W1 | P1 | T6, T5 | D3 | S4 | M1 |
| V1 | P2 | T9 | D4 | S5 | M3 |
| W6 | P3 | T2 | F1, F2 | S6 | F3, D4 |
| T3 · W2 | F4 | W5 | F2, M4 | T7 | F5 |
| T4 · W3 | F6 | W7 | F7 | | |
