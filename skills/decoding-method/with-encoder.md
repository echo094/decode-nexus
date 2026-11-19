# Decoding With an Encoder

How to plan, diagnose, fix and measure a decoder for an obfuscating encoder we can run: we encode
our own code with options we choose. An open encoder also shows its stages and their order in its
source; a closed one shows only its options. It applies to every encoder/decoder pair here and
names no single project ([Project Independence](../doc-conventions.md#project-boundaries)); the
general rules in [rules.md](rules.md) apply throughout.

**Each rule names what it needs** in the Needs column: *stages* (the encoder's stages and their
order, read from its source) or *options* (encoding our own code with chosen options and
versions). With a closed encoder, apply the *options* rules. A tag marked provisional is confirmed
when its rule is reviewed.

**Each rule opens with one bold line: the rule itself.** The paragraphs beneath it explain how to
apply it. The real bug or wrong plan behind each rule is in
[incidents.md](incidents.md) under the same label. Read an incident
when someone questions the rule, not every session.

## The rules

| Label | Needs | Rule |
|---|---|---|
| [P3](#p3) | stages | When you choose which encoder stage to work on, take them in reverse stage order, each placed by its last write: the last stage and the outermost layer first; a later stage silently breaks earlier matchers. |
| [P4](#p4) | options | When a decoder must cover several encoder versions, close one version end to end, then attribute era boundaries outward from it, nearest first. |
| [P5](#p5) | stages | When a stage's decoder removes additions, it removes only its own stage's, using only what that stage used; an addition it cannot decide yet stays in place as a suspect until the decoder that recovers its fact has run. |
| [P6](#p6) | options | When you can encode single transforms or options, cover each alone first, then their combinations, and budget for the combinations: passes clean on their own routinely fail together. |
| [P7](#p7) | stages | When you study a new encoder/decoder pair, run each unit through the loop, then climb the shipped presets smallest first. |
| [D6](#d6) | stages | Before you propose a remedy for a shape in the input, read the encoder stage that added it, its doc first, then its source: what the stage guarantees about its addition usually decides the remedy. |
| [D7](#d7) | options | When the samples in hand cannot settle a question, use the encoder to make input that can. |
| [D8](#d8) | stages | Before widening a consumer to tolerate a shape the input itself carries, enumerate from the encoder's source everything it can emit there. |
| [F7](#f7) | stages | In code built for one encoder, keep a refusal guard or fallback only where that encoder's output reaches it. |
| [F8](#f8) | options | Where the encoder provably changed a program's behaviour, either side is correct, so write the input's semantics in their native form; keep everything the source and the encoded program share. |
| [M4](#m4) | options | When you compare decodes of encoder output, freeze the corpus first; encoder output is random. |
| [M5](#m5) | options | When the source is known, read each output against its source, and land a design change with encoder-built fixtures committed failing before it. |
| [M6](#m6) | stages | When the encoder's stages are known, attribute residue to the stage that added it: count against a no-option baseline, treat what a stage decoder dropped as missing and an undecided addition as a suspect, never as residue. |

## P — Plan the order

None of these needs a run. They are read from the encoder's stage order and the decoder's own
source, and reaching for a probe to settle one is a mistake in itself.

### P3

**When you choose which encoder stage to work on, take them in reverse stage order, each placed by its last write: the last stage and the outermost layer first; a later stage silently breaks earlier matchers.**

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
  encoder's stage order and does not mean X's input is clean; neither does an incumbent decoder's order, so borrow its
  algorithms, never its pass order. Nor does the order the encoder
  invokes its passes in: a stage sits where its last write lands (next point).
- **A stage sits where its last write lands, and one stage can straddle another.** An encoder pass
  can leave a value open for a later step to finish: a label operand carrying an encoding function
  that final address resolution applies, say. Its structure is inner to every stage run in
  between; its finished value is outer to all of them. That is a loop: a stage in between needs a
  fact only the straddling stage's decoder can read, and that decoder sits under the stage in
  between. The inverse splits around it: the stage in between decides what it can and passes the
  rest on, the straddling stage's decoder recovers the fact, and the owner settles the rest
  ([P5](#p5)).
- **Confirm residue is the encoder's before filing it under an encoder stage.** A decoder pass
  emits shapes too; [D3](rules.md#d3)'s per-stage replay settles which.
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
  shape, not the option: each pass fires where its shape is present. Ask whether a unit's passes
  can be scheduled once, not which options they must detect.
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

### P4

**When a decoder must cover several encoder versions, close one version end to end, then attribute era boundaries outward from it, nearest first.**

An encoder has two independent axes. [P3](#p3) orders work along the stage axis; [P4](#p4) orders it along the
version axis, deciding which era boundary to attribute first. Close one version end to end first;
it is the **spine** that every comparison is read against.

- **The spine is the encoder's current release.** Walking back into older releases is a later
  decision driven by prevalence, not completeness. The one exception is auditing an incumbent
  decoder's claimed range: the study opens at the newest release inside that range, so a failure
  there is not version drift and later failures read as version findings.
- **With many versions, cut phases as era slices taken end to end:** study the encoder, verify any
  incumbent, write the decoder. A phase boundary is what the decoder claims, never a kind of work.
  Splitting by behaviour (document all, then verify all, then build) fails three ways: each part
  alone is unfalsifiable (an encoder doc is a hypothesis until a decode inverts it, [D2](rules.md#d2); a
  verification rests on a residue census, [M1](rules.md#m1); a fixture pins a claim, so fixtures before claims are a
  name list); a census written before the encoder study is defined by the thing under test; and one
  late finding forces rewriting a large body of docs.
- **An incumbent's boundary set is evidence of prevalence,** built from real user-submitted samples
  over years. Era granularity follows prevalence (an era earns a strategy by being met); prevalence
  predicts which refusals fire; whether to cover a range is a prevalence question, asked before
  enlarging a corpus; and "no samples seen" is never recorded as "no change occurred".
- **Attribute the nearest boundary before crossing the next.** Data may be gathered in any order;
  reading may not. An unattributed difference at the nearest boundary is inherited by every
  comparison beyond it, so a distant version showing eleven differences may be ten new plus one
  carried down. The nearest boundary is also the cheapest, since one era change separates the pair.
- **Difference count is not signal strength.** Starting where most cells differ is [P3](#p3)'s byte-share
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
- **A maximal option profile decides pass order, not coverage** (needs the stages). Every lesser profile is the
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

### P5

**When a stage's decoder removes additions, it removes only its own stage's, using only what that stage used; an addition it cannot decide yet stays in place as a suspect until the decoder that recovers its fact has run.**

- **Each layer's decoder reads and rewrites only its own layer.** Mutating still-encoded inner
  machinery corrupts it, and corruption is silent where a decline leaves countable residue.
- **A stage inside one encode peels the same way.** A stage's decoder returns what the stage
  received, minus what the stage added. Earlier stages' code passing through is not its concern: it
  neither keeps nor restores it, and losing some of it (dead code, say) as a by-product of removing
  its own additions is acceptable when that takes no code of its own. A later consumer that reads
  such code depends on a fact no stage promises; that consumer is the defect
  ([D4](rules.md#d4)), and teaching the stage decoder an earlier stage's
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
  ([F4](rules.md#f4);
  [D4](rules.md#d4): reschedule the owner, never tolerate the shape); right after the
  decoder that recovers the fact, the owner's own rule runs again with it and removes what it now
  proves. A suspect is never removed early and never charged as residue
  ([M6](#m6)). Readable now means
  decide now: a fact the stage can recover by its own encoder's rules (a direct jump target, say)
  leaves nothing to defer.
- **Equal output does not settle whose it is.** When two remedies give the same decoded output on
  every case, ownership still decides: ask whose addition the shape is, and reject the remedy that
  has another decoder recognize it, however little machinery it needs. That no case tells the
  remedies apart describes the cases, not the design.
- **The coordinator owns layer ordering; the input contract owns normalization.** Before inner
  recognition, normalize the producer leftovers a matcher that selects what the program cannot run
  without ([F4](rules.md#f4)) still cannot read, such as computed
  literal keys, into the ordinary JavaScript forms that consumer requires. Hoisted declarations
  are not such a leftover: the defining write is read directly. Never teach the inner recognizer an
  outer-specific dialect; that couples two decoders and is paid again for every outer encoder.
- **A pipeline-wide behaviour-neutral rewrite is not a layer crossing.** Deleting `debugger`, say,
  applies to every layer. The inner recognizer matches modulo such rewrites rather than asking the
  outer pass to skip them.

### P6

**When you can encode single transforms or options, cover each alone first, then their combinations, and budget for the combinations: passes clean on their own routinely fail together.**

Single-transform coverage is a first phase: most defects closed here so far were combination
defects. Passes clean on their own censuses routinely reveal a dependency once run as one
pipeline; the finding is usually there. Let whoever is driving pick the next piece. With a closed
encoder, the unit is an option, not a transform. A combination gap with no failing site to
breadcrumb is isolated by [D7](#d7).

### P7

**When you study a new encoder/decoder pair, run each unit through the loop, then climb the shipped presets smallest first.**

"New pair" names the relationship, not two new components: an existing encoder with a new decoder
is still a new pair. The loop:

1. if a decoder file already reuses a shared visitor, stop: keep-or-fork is a decision ([F6](rules.md#f6));
2. document the encoder side;
3. with an incumbent decoder: define this unit's residue census from the encoder side just
   documented, then run the incumbent on the cells exercising the unit and record its verdict,
   then read how it inverts the shape ([D1](rules.md#d1));
4. write the decoder pass;
5. document the decoder side;
6. build fixtures from the encoder's own test cases, and mine them as a measurement: encode every
   upstream fixture for the stage and compare the decoded structure with its source, which has
   twice found a missing reversal on units whose censuses and suites read clean;
7. pause for review;
8. commit, then clear context.

Climb the shipped presets as the combination ladder, smallest first, largest for final integration
([P6](#p6)). A smaller tier can be a distinct shape, so verify the relationship before treating one tier's
coverage as implying another's.

## D — Diagnose

### D6

**Before you propose a remedy for a shape in the input, read the encoder stage that added it, its doc first, then its source: what the stage guarantees about its addition usually decides the remedy.**

This completes [D1](rules.md#d1)
when the encoder can be read. A guarantee such as a field the stage writes that nothing reads
usually decides the remedy. What that decides is carried out by the rules that own it: the stage's
own decoder removes the addition
([P5](#p5)), in reverse
stage order ([P3](#p3)),
never by each later step tolerating it
([D4](rules.md#d4)).

An encoder doc read under this rule is itself a claim
([D2](rules.md#d2)): a decode attempt against real stacked output verifies it
([`SKILL.md` gate 4](../../SKILL.md#gates) applies this to a pin). Upstream docs shipped with the encoder are
claims too: confirm a shipped `docs/` page matches the pinned commit, and note, never silently
drop, upstream docs describing features the pin lacks.

### D7

**When the samples in hand cannot settle a question, use the encoder to make input that can.**

These extend [D3](rules.md#d3) where new input can be encoded on demand.

With a closed encoder, isolate options, not transforms: an option may switch on several stages or
none we can name. The re-encode without the final minifier and the source diff need the stages.

| Question | Instrument | Note |
|---|---|---|
| Is my reading of optimized output right? | Re-encode the same source, options and seed without the final optimizer | Same allocations, the encoder's own comments intact: a truth oracle, valid only when the optimizer runs last and draws no randomness |

**Differential diagnosis, step 5,** after D3's four steps. **Sweep the axis to bound the range, and read the bound as a candidate.** A bound landing
exactly on a known boundary feels like an answer and is not, because boundaries cluster. Your
bound is only as tight as your sample spacing. Sweep every axis, not only the family the
subsystem makes salient. Then diff the source between the two versions, since a component nobody
swept has no axis to report. When several candidates share a bound, switch axes: find a version
or option where one moved and the others did not. Until then the verdict is "confounded", which
is not "unexplained". Only a full sweep plus an empty source diff earns "something undocumented". Switching axes is the same technique
[P4](#p4) uses on era boundaries.

**Combo gaps.** When a gap appears under a preset but under no single-transform test and there is
no failing site to breadcrumb, isolate it empirically. Fix one small source and a base combo known
to decode cleanly; add one candidate transform at a time at full strength (`1`/`true`, never a
probability), judge each by [M2](rules.md#m2) over three or more runs; the addition that flips the verdict is the
trigger; then shrink the reproducing combo one transform at a time. Read encoder source only after
that. A cause can need a second transform present, which a one-at-a-time matrix never reaches.

### D8

**Before widening a consumer to tolerate a shape the input itself carries, enumerate from the encoder's source everything it can emit there.**

This bounds the last resort of [D4](rules.md#d4):
a shape the input itself carries has no operation of ours to fix, so the consumer tolerates it.
Where the encoder can be read, that tolerance stays bounded, because the encoder's set is closed
and readable from source: enumerate what it can emit before widening.

## F — Fix

### F7

**In code built for one encoder, keep a refusal guard or fallback only where that encoder's output reaches it.** A pass several decoders share is
[F6](rules.md#f6)'s.

Read the guard first: which one fired
([D3](rules.md#d3)), what upstream state makes it fire
([D4](rules.md#d4)), and whether it still protects
what it was written for ([D2](rules.md#d2)).

Place guards at the boundary they protect. For an owned decoder chain, recognize the source by its
distinctive structure and required parts, then trust the records our own stages build: test those
stages and the end-to-end output rather than revalidating every record at every handoff. Keep checks
that decide whether source semantics are supported, whether analysis covers the admitted input and
whether emission is complete. Keep a refusal guard only when an encoder-produced source reaches it
through the normal entry and a test pins that. A hand-edited source no encoder can emit, or a mutated
private record, does not justify a guard, and neither does a reviewer's request for completeness.

A uniqueness requirement is a guard too, and it fails on populations the encoder grows by cloning:
the original and its variants all fit. Before requiring exactly one, ask whether the encoder emits
variants; prefer the most general member, and treat behaviourally equal members as one. A fallback
route is a guard's twin: before removing one, disable it on a scratch copy and rerun the census and
fixtures with a reach log. Only what still decides through it needs covering first.

### F8

**Where the encoder provably changed a program's behaviour, either side is correct, so write the input's semantics in their native form; keep everything the source and the encoded program share.**

The decode is judged against its source ([M5](#m5)), but the encoded program is the decoder's only
witness of that source. Where an encoder carries less than the source (a dropped directive, a
handler that ignores a failure), the source's behaviour is gone from the input and cannot be
recovered in general, while the encoded program's version of it is the encoder's artifact:
reproducing it costs wrappers a reader takes for residue ([M2](rules.md#m2)). Neither side is owed there.

- **Name the limitation from the encoder's facts:** a quirk in the encoder package, proved by a
  reproducer whose source and encoded behaviour differ. An undocumented divergence is not free;
  until its quirk is written, keep the encoded behaviour.
- **Take the input in the semantics the encoder carries and write their native form:** the
  operator, the bare name, the plain call, not the encoder's handler step by step.
- **What the two share stays bound:** computed values, exceptions both raise, evaluation order,
  getter, setter and proxy effects. A statement that may throw keeps its evaluation when its result
  is unread.
- **The check:** the decoded program equals the source wherever the encoded program does, and
  elsewhere equals one of the two.

## M — Measure readability

**A decode is worth how well its output reads against the source.** Every measure below serves
that question and none replaces reading the output. They are cheap measurements answering "did
this decode, or did it just not break?" — usable before there is a trustworthy expected output. All of [M2](rules.md#m2) measures residue; [F1](rules.md#f1) and [M3](rules.md#m3) cover the case where a decode
is wrong with no residue, and [F3](rules.md#f3) covers what output cannot show.

### M4

**When you compare decodes of encoder output, freeze the corpus first; encoder output is random.**

Names, state vectors, keys and case order regenerate per run, and many transforms are
probability-gated, so a transform at full strength may still not fire on a given source. Use three
to five runs per side for any verdict you will act on. Two fresh encodes are not comparable at all.
A case encoded afresh inside a throwaway command is not frozen even when the encoder draws no
randomness: nothing records it, so no figure from it reproduces. Save the case and its generation
record before comparing.
This compounds across an isolation matrix: a grid reading clean may only mean every short run missed
the payload.

### M5

**When the source is known, read each output against its source, and land a design change with encoder-built fixtures committed failing before it.**

This extends [M1](rules.md#m1) where the input was encoded from our own code. Read one diff per
group of changes against the source, and each changed output against its source with the
readability metrics beside it. So a design change lands with its fixture regression: encoder-built
fixtures, committed failing before the change, that assert the decision the rule makes ([M3](rules.md#m3))
and pin the readable form it produces.

- **Size ratio over the source.** Decoded size over pre-obfuscation source: a multiple in the
  hundreds means whole mechanisms were never reversed (some growth from renaming or injected dead
  code is legitimate). Read it beside [M2](rules.md#m2)'s ratio over the input, the
  calibration pair from the run in front of you. Keep `<name>.src.js` beside each fixture so this
  ratio stays computable.
- **Structure against the source.** For recovered control, count what the source wrote against
  what the output wrote: loops, guard clauses against `if`/`else`, sibling against nested
  statements, synthetic labels and leftover dispatch loops. An output can keep behaviour with
  every residue at zero and still read worse.

### M6

**When the encoder's stages are known, attribute residue to the stage that added it: count against a no-option baseline, treat what a stage decoder dropped as missing and an undecided addition as a suspect, never as residue.**

This attributes [M2](rules.md#m2)'s residue where the stages are known; a closed encoder
attributes it to options instead, counting against the no-option baseline what each option adds.

- Against a no-option baseline, count what is extra; earlier-stage code a stage decoder dropped as
  a by-product ([P5](#p5)) is missing, not residue.
- An addition no stage can decide yet is a suspect, not residue, until its owner's rule settles it.
- A decoder whose own encoder's facts place an addition no other decoder can tell apart (a jump
  inside a run that encoder emits straight-line) reads it by those facts.
