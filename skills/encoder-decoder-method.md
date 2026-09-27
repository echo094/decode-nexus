# Encoder/Decoder Method — cross-project notes

Working method for studying an obfuscator and for building/debugging its decoder — one
discipline, not two (T8). Applies to any encoder/decoder submodule pair here, not to one
obfuscator's transforms. Kept separate per `SKILL.md`'s Project Independence rule.

**Rules here, evidence next door.** Every rule was paid for by a real bug or a wrong plan; those
narratives live in [encoder-decoder-incidents.md](encoder-decoder-incidents.md) under the same
labels. Read that file when a rule is being questioned or extended — the incident is what makes a
rule survive a plausible argument against it. Read this one every session, which is why it is
terse.

**Labels are stable identifiers, not positions.** Other docs cite `T1`, `W1`, `S3` by name, so a
label keeps its content permanently; only grouping and order change. A merged rule carries both
labels. Cite by label, never by tier or position. Tiers rank by how often a session needs the
rule, not by how interesting the incident was. Per `SKILL.md`'s Revise by Evolution, a new
incident sharpens an existing rule rather than adding one.

**Splitting is the counterpart of merging: a merge fuses labels always read together, a split is
owed once they are not.** No label may change meaning — each keeps the text it was being cited for,
which is what makes a split safe — and the citing docs are repointed in the same change, including
any that deep-link a *heading* anchor, since renaming a heading breaks those silently.

## Background: why decoders fail silently

Every decoder here **fails closed**: a pass that cannot recognise its shape leaves the input
untouched and moves on. That is right — a half-rewritten program is worse than an obfuscated
one — but:

> A completely broken decoder and a perfectly working one produce the same *runtime behaviour*.
> They differ only in the *shape* of the output.

A declining pass emits no error, no log line, and correct output. So: runtime correctness cannot
tell you whether anything decoded (S4); coupling between passes is invisible, because the bail-out
conditions *are* the dependency graph (W2); and the first failure hides every cascading one, so
the symptom sits several layers from its cause (T6).

**This method fails the same way**, which is why rules here get re-learned: follow it to a wrong
conclusion and there is no error either — a plausible fix, a green suite, and the real defect one
pass upstream. Every signal below reads **output**, which is only half of what a pass is
responsible for; the other half is S6.

## Find the rule from the symptom

| what you are looking at | go to |
|---|---|
| correct-running output, and you don't know whether anything decoded | S4, then S1 · S2 · S3 |
| a residual obfuscated shape in correct-running output | T6 — bail-out breadcrumb |
| a `TypeError`/`ReferenceError` thrown by the decoded program | T6 — output diff |
| a pass that fires on nothing, or suddenly stopped firing | W1 (a later encoder stage rewrote its input), T6 (the caller's gate) |
| an earlier pass left a shape your matcher can't handle | T9 |
| a guard rejecting something that looks like it should pass | T3 |
| deciding what to work on next | T1 — and nothing else decides it |
| **deciding which era boundary to attribute first**, or planning a phase that skips versions | **V1** — the version axis, independent of T1 |
| a version boundary where several era axes turn at once | V1, then T6's step 5 — coincidence is a candidate, not an attribution |
| several open bugs in one subsystem | T4 |
| a gap that appears under a preset but under no single-transform test | T5 |
| a sample that looks obfuscated *again* after a decode, or a pass that corrupts rather than declines | W6 |
| output that runs, reads clean on every residue axis, and is still wrong | W5 |
| a doc, comment, or worklist status you are about to rely on | T8 |
| **a matcher that accepts a freshly parsed tree and rejects the one your pipeline produced** | **S6** — derived state went stale; the defect is not in the output |
| **a fix that works and you cannot say why**, or that only works in one position | **T9** — an unexplained fix is a defect report; it is probably at the wrong level |
| **you are about to change a pass shared by several decoders** | **W7**, then T4 · W3 — count the consumers *and* their existing workarounds before deciding where the fix goes |
| **a comment telling the caller to do something afterwards** | **T8** — count the callers who honour it; the ones who don't are the finding |
| an encoder/decoder relationship not yet studied here | [encoder-decoder-newpair.md](encoder-decoder-newpair.md) |

## Tier 1 — every session

### T8. Validate a premise before implementing against it — in-tree first, then a probe

**Verify against source, always.** A comment, a doc, or a "Covered" status describes intent when
written; the decoder's target can change under it silently. Never document a mechanism from memory
or inference.

- **Distrust most a guard comment asserting something is impossible.** "By design", "cannot be
  resolved" describe the operation the guard was written for, never the set it now blocks (T3).
  Repeating one into a skill doc launders a hypothesis into a documented limit.
- **A comment stating a *caller obligation* is a defect report, and the validation is counting the
  callers.** "The code must be reloaded afterwards", "call this before X" — it reads as a contract
  the callers accepted, and is almost always a repair the pass declined to do, taxing every
  consumer present and future. **Count them; the ones silently not paying are the finding.**
- **Claiming a necessity is a claim to measure, and it fails in the constructive direction too.** A
  comment saying an ordering is load-bearing is the same object as a guard saying a shape is
  impossible. Two such comments were written in one unit here — a prelude's ordering and a removal
  order — and reversing each changed no result. **A false constraint is either trusted forever or
  moved blindly, and neither reader can tell what broke**, so write the measurement beside the claim
  or do not make the claim.
- **A status is only as strong as the criterion it was recorded under** — anything closed before
  the decode-quality signals existed was judged on runtime correctness, which S4 says is nothing.
- **Treat a decode attempt as the verification step for an encoder claim.** A mechanism documented
  from reading is a hypothesis; inverting it against real, adversarially-stacked output is what
  proves it complete. Don't mark an encoder-side transform doc settled before something has tried.
  `SKILL.md`'s Encoder Pin Gate is this rule applied to a pin.
- **Do not turn an evidence gap or our own defect into a verdict about the encoder's mechanism.**
  A source-inspection observation with no transfer cell is unqualified, not disproven. If a current
  decoder or harness success, decline, or apparent gap may be caused by a defect introduced on our
  side—including a producer/decoder configuration mismatch—quarantine that comparison until the
  defect is localized and the baseline is re-verified.
  Preserve the source-backed knowledge and make the next task a bounded baseline audit or
  qualification; only that evidence can support an adopt, defer, or reject decision.

Then validate the plan, in this order: **look for a matcher that already does it correctly**
(free, stronger than a probe, and it also answers T9's "who already owns this reversal"); **then a
throwaway probe** — reading and probing find different classes of thing, so budget for both, and
**keep the recipe, not the script**; **suspect the sample and the oracle before the code, whichever
way the probe reads** — check the denominator (S5), then check the oracle measures *liveness*
rather than presence.

**A specification is not validated until it has been executed.** Reading a table of options, a
stage list or a set of definitions confirms only that it is internally coherent. Three defects in
one option matrix here survived every reading and were found the first time something ran against
it — so where a spec drives work, run it once against the thing it describes before trusting it.

**A probe reporting the answer you wanted needs that same treatment, and it is the harder direction
because nothing prompts the question.** It bites hardest on a **positive control** — a case built
to make something fail — which is a control only while its input can still reach the mechanism it
names. Two ways it silently cannot: the damage is of a kind the named check is blind to, so a
*different* check takes the credit while the status reads exactly as expected; or the probe's own
scaffolding perturbs the property under test. So **assert the mechanism, not the outcome** — have
the case name the diagnostic it expects — and prove that assertion can fail by feeding it one that
should never match.

[Incidents](encoder-decoder-incidents.md#t8--validate-a-premise-before-implementing-against-it)

### T6. Instrument the failure; don't root-cause from reading alone

**Every cause found in this project so far was found by breadcrumbing a real failure, and none by
an isolation matrix.** Budget accordingly. **A residual shape proves *something* failed, never
*what*.** The tell for which instrument to reach for is what the failure looks like, not where you
suspect it is.

| question | instrument | notes |
|---|---|---|
| Which guard rejected this shape? | bail-out breadcrumb | tag every `return null` with its own source line, so it survives a rewrite |
| Which *stage* made the output look like this? | replay the pipeline stage by stage on one real sample, printing size + a structural count (S2) | a stage that should shrink and reports `+0` never fired; also catches a stage that *grows* output. Build it before reading any matcher |
| Is this residue ours or the encoder's? | the same per-stage run | **never** input-vs-output counting: that is valid only when the construct is visible in both, and it silently is not while an outer layer still hides it |
| Did the fix even run? | the breadcrumb, asked of the **caller** | a correct fix that never executes measures as *byte-identical* output. Instrument the gate *above* the code you are writing |
| The pass ran and the output is wrong | before/after **diff** of decoded output at the site the error names | a guard counter cannot see this — it is not a decline, so the tally actively reassures |
| **Two mechanisms could explain this one symptom** | **differential diagnosis** — the five steps below | the plausible mechanism wins by default and is never tested, so the cost is paid in sessions rather than in a wrong line of code |

**Differential diagnosis, when a symptom has more than one available explanation.** The steps are
cheap, they are ordered so the earliest can end it, and each one *removes* a candidate rather than
supporting one:

1. **Run the artifact untouched.** If the sample already does this alone, nothing downstream is
   implicated — the behavioural twin of "ours or the encoder's", and the step most often skipped
   because the answer feels obvious.
2. **Test that the accused shape is even present**, with a positive control — a sample that does
   carry it — so a zero is visibly not a blind probe.
3. **Bisect your own operations**, one at a time, from none applied. "Present with none applied"
   ends the search immediately; anything else names the operation.
4. **Hold the rival explanation constant and vary only the suspect.** Same regenerated text, one
   difference — that is what turns two plausible stories into one measured one.
5. **Sweep the axis to bound the range** — and read the bound as a *candidate*, never as the
   answer. A bound falling between known boundaries is plainly still an observation. The trap is
   the other case: a bound landing *exactly* on a boundary the code already has feels like an
   explanation, and is only a candidate, because **boundaries cluster**. Four rules, each of which
   was paid for in one sitting:
   - **Your bound is only as tight as your sample spacing.** With no sample between two versions
     you have a *bracket*, not a boundary — and narrowing the bracket is itself the experiment,
     because the version you add is the one that can separate candidates.
   - **Count how many things move at that bound, sweeping *every* axis rather than the ones the
     subsystem makes salient.** Checking only the family you already suspect finds a coinciding
     boundary and stops, confidently.
   - **Then diff the source between the two versions, because a registry cannot report a component
     nobody has swept.** An axis list is sound but incomplete by construction, so the candidate
     that explains the symptom may have no row yet, and only the diff shows it.
   - **When several candidates share a bound, version sweeping is exhausted — switch axes.** Find a
     *sample* where one moved and the others did not: another version if one exists, otherwise an
     **option** that varies one without the others. Until such a sample exists the honest verdict
     is "confounded", which is a different claim from "unexplained" and must not be written as one.

   **Only when a full axis sweep and a source diff both come up empty is "something undocumented is
   happening" earned** — and even then the first move is to derive the missing axis, not to treat
   the symptom as novel.

**Five ways the instrument itself lies:**

| lie | correction |
|---|---|
| a bail tally measures the pipeline's interior, not its output | a decline is not a defect until an output census says so. **A gate that declines can be load-bearing** |
| a tally names the gate, never the thing | print one offending candidate's own bindings before writing a cause down |
| a pass with no candidates looks identical to one that resolved everything | census *inside* the pass against the encoder's variant matrix. **Establish the population is non-zero before working an item** |
| a breadcrumb filtered by name inverts the answer | T2's name trap applies to instruments too — dump every call with its resolved binding's location |
| a guard counter is blind to a failure *after* a successful match | a caught exception reads as a clean pass. Instrument the catch blocks, and prefer what the pass already reports |

[Incidents](encoder-decoder-incidents.md#t6--instrument-the-failure)

### T7. One fix is never the whole fix — and where the audit lives decides how long it lasts

A defect's shape almost never occurs once. Grep for the *shape* across the pipeline before closing
the item — the audit is a grep, not a review. S4's regression value is what makes verifying the
broadened fix cheap.

**Where the condition is computable, the audit is an assertion in the shared test harness, not a
grep.** A grep is one-time and only as good as the pattern you thought of; an assertion in the
helper every case already runs through audits the whole suite at once and keeps auditing what is
added later. The cost is one function.

**Then it goes in before the fix.** This inverts the order the rest of this file assumes, and only
where a defect is invisible to output (S6): there the detector is not a regression guard, it is the
only thing making the defect *observable*, so building it first demonstrates the defect rather than
inferring it. Built afterwards it can only ratify a fix already chosen — which is how a symptom
patch at the wrong level gets certified.

## Tier 2 — deciding what to fix, and in what order

Readable from the encoder's stage order and the decoder's own source. **None of them needs a
run**, and reaching for tier 1's instruments to settle one is the mistake T1 and T9 record.
Measurement still earns its place wherever the stage order is silent — whether a matcher is
correct, which guard fired, whether a fix regressed anything.

### T1 · W4. Order the work from the stage order — not by byte share, and not by probing

Map the encoder's stage order against the decoder's pipeline order and fix in **reverse encoder
order**, asking of each stage what its matcher needs its input to already look like.

**Stage order sets the order *between* stages and says nothing about granularity *within* one.**
A stage holding several transformers is one work unit unless its components form a **decode
dependency chain** — one that cannot be resolved until another already has — in which case it
splits along that chain, basis first. Transformer count does not decide it: a stage with a dozen
independent transformers is correctly one unit, while a stage with three can be two. Two
consequences worth stating because both look like defects from outside: a basis unit is **inert**,
not broken, on the samples whose remaining component belongs to the layer above it; and the
distinction between "mine, readable, and the layer that owns the rest is not built yet" and "mine
and unreadable" has to exist in the interface for as long as the chain is unfinished. **Write the
chain down next to the unit list** — a list justified only by stage order reads as arbitrary at
exactly the boundaries stage order cannot explain, and it will be re-litigated.

**W4 — a defect's size in the output says nothing about where it originates.** A defect
contributing almost nothing can be holding a large one shut. Byte attribution measures a
*symptom's* size. **It is a dependency order, not a priority order**: every open shape is
release-blocking, and sequencing only keeps a stage from being worked while a later one owns its
input. "Measure the prize first" is W4 in the costume of diligence, and it predicts badly.
Three corollaries:

- **Don't troubleshoot a decoder whose input still carries a later encoder stage's residue.**
  Remove the residue first — the symptom may not survive.
- **Our own pipeline position never sets priority.** "Our pass X runs before our pass Y" is not
  the stage order and does not imply X's input is clean.
- **Confirm the residue is the encoder's before filing it under an encoder stage**, and name the
  specific stage only from its source. A decoder pass emits shapes too. T6's instrument table owns
  how to settle it and why input-vs-output counting cannot.

**Do not probe for the ordering.** A probe cannot beat the order enum, and a misread one
manufactures confidence.

**This rule is about the *stage* axis. The version axis has its own, and it is independent of this
one: V1.** Neither implies the other — stage order decides which transform to reverse first,
V1 decides which *era boundary* to attribute first, and a project doing one correctly can still do
the other backwards.

**Encoder-side option gating does not imply decoder-side option detection.** An encoder guards a
transform behind an option; the reversal does not need the option, only the shape — each pass fires
where its shape is present and declines where it is not. Measured across four units here, one fixed
composition run to a fixpoint drove every residue axis to zero at **every era and every option
profile**, with no per-(version × option) branching anywhere, even though several of the
transformers involved are option-gated. So the question to ask of a new unit is whether its passes
can be scheduled once, not which options they must detect.

[Incidents](encoder-decoder-incidents.md#t1--w4--order-the-work-from-the-stage-order)

### V1. Work the era axis outward from the version you have closed

**An encoder has two independent axes and this is the second one.** T1 · W4 orders work along the
*stage* axis — which transform to reverse first. V1 orders it along the *version* axis — which era
boundary to attribute first — and the two answer different questions. A study that has closed one
version end to end (call it the **spine**) then owes the rest of its range an attribution per
boundary, and the order that takes is not free.

**Work outward from the spine, one boundary at a time, and attribute each before crossing the
next.** The comparisons are independent, so their *data* may be gathered in any order; their
*reading* may not.

- **An unattributed difference at the nearest boundary is inherited by every comparison beyond
  it**, where it silently inflates the next one. A distant version showing eleven differences
  against the spine may be ten new plus one carried down, and counting eleven is how a boundary
  gets attributed to the wrong thing.
- **The nearest boundary is the cheapest**, because exactly one era change separates the pair. A
  distant one is separated by several at once and attributes none of them — which is the same
  failure a decoder has when its input still carries a later stage's residue (W4's first
  corollary), one axis over.
- **W4 arrives here in costume.** The temptation is to start where the most cells differ, because
  the signal looks strongest there. Difference *count* is a symptom's size and says nothing about
  where the cause is. Take the nearest boundary however small it looks.
- **The reference version runs first**, for the same reason everything is compared against it; a
  sweep that schedules it last has to be re-run.
- **A pending fix invalidates the map.** These readings are usually taken by sabotage — removing a
  pass and seeing what breaks — so a known defect in *your own* pipeline can be the thing being
  measured. Fix it before attributing anything beyond it, or the groups you are attributing may
  not survive the fix.

**Close one cell end to end before attributing anything — that is what makes it the spine.** Not
"study it first" in the sense of priority: a reference the comparisons are read against has to
exist, and until one does there is nothing for a difference to be a difference *from*. Which cell
is a separate question, and for a pair with no package here yet the answer is the encoder's current
release ([encoder-decoder-newpair.md](encoder-decoder-newpair.md)).

**Each other era is then tested as "the spine's decode minus a pass" — and that test has a guard
which is not pedantry.** Two eras collapse into one for decode purposes when the other era's
reversal is the spine's minus a pass **with the surviving passes' relative order and level
boundaries unchanged**. Deleting a node from a dependency graph can merge two levels, and it can
also **reorder two survivors inside a level** without changing any level count — so a matching set
of load-bearing passes is not by itself proof of collapse, and the ordering has to be checked
separately.

- **Collapse is an output of the study, never an input read off a pipeline-order signature.** A
  shape change is invisible to the dependency graph by construction: the graph records ordering
  *requirements*, not data flow. The recorded case is an encoder whose largest emitted-shape change
  in its whole history sits **mid-era** on both source-derived axes, which are correctly silent
  there.
- **Three things collapse does not license.** Not a coverage reduction — confirm a shape at **both
  ends** of its claimed range. Not a re-encode, because the freeze rule stands. And not a
  significance marking in the registry: which eras matter is what the study produces, not what it
  starts from.

**A maximal option profile dominates on pass *order* and not on *coverage*, and conflating the two
is expensive.** Every options-off profile is the all-on dependency graph with nodes deleted and the
sort re-run, so one derivation at the maximal profile really does generate the others — that is a
statement about the ordering graph. It is **not** a statement about which shapes appear: options
interact, so turning everything on can turn something off. The measured case is an encoder whose
all-options-on cell at one version emits **no string-array subsystem at all**, less coverage than a
lesser profile at the same version. Reading the graph result as a coverage result is what makes a
study skip the per-feature sets, which the saturation paragraph below is the other half of.

**Two versions can be adjacent in the release list and far apart on the axis that matters**, so
"nearest" means nearest *era boundary*, not nearest version number. Sample spacing bounds the
resolution: with no version between two samples you have a **bracket**, not a boundary, and
narrowing it is itself an experiment — the version you add is the one able to separate candidates
(T6's step 5 owns the rest of that).

**When several era axes turn at one boundary, the discriminator is often already in hand: compare
which *option sets* move.** An axis belonging to one transform flips only the sets enabling it,
while a shape change under a shared subsystem flips every set that reads it. Prefer a
**per-feature** set — a maximal profile is frequently failing for another reason already and cannot
show the contribution of one more, which is T5's saturation one axis over.

**Consequence for planning, and it is the expensive one:** a phase that jumps from the spine to a
far version *skips* every boundary between, so its result is uninterpretable in the same way. If
that leap is taken for an unrelated reason — a pinned commit, a different toolchain — then the
range it skipped is a **prerequisite for attributing its failures**, not optional follow-up work,
and scheduling it afterwards inverts the dependency.

[Incidents](encoder-decoder-incidents.md#v1--work-the-era-axis-outward)

### W1. A later stage invalidates an earlier matcher's assumptions

**Anything later in the encoder's stage order can invalidate an earlier matcher's assumptions.**
The failure is silent *and total*, because a late stage's rewrites are semantics-preserving: only
the shape the matcher was written against changes, so the pass declines on every application at
once. Confirmed forms: a late **renaming** stage, and a late **minifier**.

This is *why* T1 works in reverse stage order, but it is what you reach for when a working pass
stops, where T1 is for choosing what to work on. Three subjects extend it: its limiting case, a
second encode (**W6**); what it means for a validation set, names being unreliable by design rather
than convention (**W7**); and the same failure with the agency reversed, one of *our* passes
changing the spelling under our own later pass (**W5**).

[Incidents](encoder-decoder-incidents.md#w1--a-later-stage-invalidates-an-earlier-matchers-assumptions)

### W6. Repeated encoding — layers stack, so peel outermost-first

A second encode is a later stage over the *entire* pipeline: the whole of the first pass's output,
machinery included, is input to the second, so every fingerprint on the inner layer fails for the
ordinary W1 reason.

**The invariant that makes it tractable: a second encode cannot change what the existing code
does — it can only add wraps.** **Derived, not observed**, forced by the per-transform
behaviour-preservation claims a package already records — so a nested sample needs no corpus to
establish the rule. Four consequences:

- **Layers stack rather than merge, so peel outermost-first.** Once the outer layer is gone what
  remains is exactly what the first pass emitted, so every single-encode claim applies unchanged.
- **Crossing a layer boundary is always a defect.** Inner machinery is *encoded by* the outer
  layer, so membership is decidable by readability, not by shape. The failure is **fail-open**:
  mutating a still-encoded construct corrupts it, where failing to match leaves legible residue.
  Residue is countable; corruption is not, and is loud only when it throws.
- **An evaluating reversal is not exempt.** An inner prelude is not runnable standalone — its own
  literals are outer-encoded calls. **So repeated encoding is neutral between reversal
  strategies**: it costs each a loop and nothing else, and decides nothing about which to build.
- **Terminate on a round that removes nothing.** Each peel strictly reduces. But **the layers need
  not come from the same encoder**, so the loop belongs *above* any single decoder: one pass can
  only report *clean* / *a layer remains that is not mine* / *mine and unreadable*, and collapsing
  those three is what makes a nested sample undiagnosable.

Two qualifications, since the invariant is about the inner code's logic and not the program's
observable output: **a wrap can suppress or kill what the inner layer does** (an outer
`disableConsoleOutput` silences it; `selfDefending` can stop it terminating), so **runtime
equivalence across a peel is not a free oracle**; and **the invariant binds the encoder, not us** —
our own normalization re-spells the recovered layer, which can trip that layer's own anti-tamper
guard. **One genuine exception:** an option that is not semantics-preserving at all — renaming
*properties* renames ones the program does not own, so the emitted program can simply die. Worth
excluding from a corpus for that reason.

[Incidents](encoder-decoder-incidents.md#w6--repeated-encoding)

### W7. What a validation set cannot show — at either end of its size

Two corollaries, and the second is the one that decides whether a change to *shared* code is safe:

- a matcher validated only against an isolated single-transform fixture is not proven robust to
  real combined output, since that fixture omits exactly the later stages that would break it;
- **and a matcher validated only against one encoder's whole corpus is not proven sound either,
  once it is shared with a decoder for a different encoder.** One encoder's output is a narrow
  slice of the shapes a pass will meet, and its regularities are invisible from inside: the gaps
  are exactly the inputs that encoder *cannot* produce, so every census reads clean, every sample
  decodes, and the pass looks proven. A shared pass therefore has to be judged on hand-built cases
  that go off the encoder's path — and the ones worth building are the ones where it **corrupts or
  throws instead of declining**, since a decline costs legible residue and the other two are
  silent. Field reports are the only evidence a corpus cannot substitute for here.

**Read in the other direction, before changing a shared pass:** a green corpus is evidence about
*your* encoder and says nothing about the other consumers. Enumerate them, and read what each
already does to work around the pass (T4 · W3).

[Incidents](encoder-decoder-incidents.md#w7--what-a-validation-set-cannot-show)

### T9. When an earlier pass leaves a shape you can't match, find out why before adapting

The reflex — teach the matcher in front of you to tolerate it — is the **last** of four options,
because it is the same fix re-paid at every consumer. Nothing about the residue tells the cases
apart, so diagnose first.

| case | remedy |
|---|---|
| 1. the producing pass emits a genuinely wrong shape | **fix the producer** — and "producer" is the *operation* that emits it, never the composition that schedules it (S6). Every downstream matcher tripping over it is a symptom; this inverts what T4 would recommend |
| 2. the input does not exist yet, but will | **reschedule the pass** — possibly to run twice. If the residue survives that decode by design, moving it changes nothing |
| 3. the producing pass is correct but *uninformed* | **route the fact to the pass that owns the reversal** and drive it directly. The information exists, just not where the pass can see it |
| 4. none of the above | tolerate it in the consumer, knowing you will pay again |

**Empirically the cause was always case 1 or 2** — a shape one of our own passes emitted, never a
matcher merely too narrow. So when the reflex says "widen it", the prior is that something upstream
is wrong or mistimed, and **a pass's schedule is part of its correctness**.

**Separating 1 from 2 is what decides the level**, and it is worth doing explicitly rather than by
feel: case 1 is a wrong operation and is fixed at that operation; case 2 is a right operation at the
wrong time and is the only case a scheduler-level fix is correct for. Reaching for the scheduler
without establishing the operation is sound is how a compensating repair gets certified.

**Every case above is keyed on emitted shape, which is a false-negative machine.** A producer can be
wrong while its output is right — leaving *derived state* inconsistent with the tree it just
rewrote. The text round-trips, so "the shape it emits is correct" is true and rules out nothing.
Ask what a pass leaves behind **besides** its output before concluding it is not case 1 (S6).

**A fix you cannot explain is a defect report, not an open question.** A repair that only works in
one position is most likely at the wrong level, the position load-bearing because it compensates
for something upstream. Recording it as "measured, don't tidy" protects the patch and retires the
search. Hunt the producer; if the fix then becomes unnecessary, that *was* the explanation.

**The one recorded exception is case 4, and only for a re-spelling the *encoder* emits** — there is
no producer of ours to fix and nothing later to wait for. What keeps it bounded rather than
open-ended: **the accepted set is closed and readable from source.** Enumerate what the encoder can
emit before widening, and the tolerance list is finite.

**Distinguishing 1 from 3 gets skipped**; the tell is whether the upstream pass is *wrong* or
merely *stopped*, and a guard comment claiming the shape is unresolvable is not evidence of case 1
(T3). **Cost of case 3:** it creates a direct call dependency a scheduled pipeline does not have,
and it mutates before the calling matcher has confirmed its own match — decide explicitly what
happens to that mutation when the match then fails.

[Incidents](encoder-decoder-incidents.md#t9--find-out-why-before-adapting)

### T3 · W2. Ask what a guard protects, and whether that is what you are doing

Two questions of every early `return null`: **"what upstream state makes this fire?"** and
**"what is this guard protecting, and is that what I am doing?"** The second gets skipped, and it
is a correctness rule rather than a planning one — **a fail-closed rule outlives the operation it
was written for**, going on to block a different operation that needs none of its protections, and
to be misread from the other side as proof something is inherently unresolvable.

**A comment asserting a constraint is the same object as a guard** — an assertion about the world
that nobody re-checked — whether it claims a shape is impossible, an ordering is load-bearing, or a
caller owes a repair. Validating those is T8's subject, and it is where the counting rules live.

**This is source reading, not measurement**, and it is the only way inter-pass coupling ever gets
written down: documentation describes what a pass does when it *succeeds*, and a declining pass is
indistinguishable from a working one. The planning payoff is knowing which passes are
**unmeasurable** until an earlier gap is fixed, and therefore which experiments not to run yet.

[Incidents](encoder-decoder-incidents.md#t3--w2--ask-what-a-guard-protects)

### T2 · W5. Hold matchers to two contracts — shape-keyed, and all-or-nothing

**Key on AST shape, or on a binding captured when the pass first resolves it — never on name
text.** The audit form is a grep, not a review (T7). Three traps that survive knowing the rule:

- **A name a matcher resolved is still a name.** Holding the target as a string resolves nothing;
  every same-named identifier in reach answers to it. Compare the binding object.
- **Declaration sites are not references.** A `var x` declarator id, a `function x(…)` name and a
  nested parameter `x` are bindings, not uses — counting "references" without
  `isReferencedIdentifier()` reads all three as the target being used, which fail-closed kills
  every application in scope.
- **Source positions are the same trap one level down.** Earlier passes reparse bodies and
  synthesise statements, so `node.start`/`node.end` are routinely absent or fragment-relative. Ask
  the path ancestry, which is current whatever rebuilt the tree.
- **So is any cached scope state, and this one inverts a fix that looks right.** A resolved binding
  records the path as of the last crawl, so it can point at a detached node that still *prints*
  identically to the live one, and identity comparisons fail silently. Two tells: it accepts every
  hand-built case and rejects every real one — hand-built trees being the only ones nothing has
  rewritten — and, more common in a pipeline, it accepts a *re-parsed* tree and rejects the live
  one. Prefer a structural question asked of the live tree over a lookup computed earlier.
  Detection, and whose job the repair is, are S6.

**Resolve a matched structure completely or leave it entirely alone**, scheduling a second visit
for when the missing input exists. "Leave it alone" is cheap and always safe; the half-way state is
neither.

**W5 — half-resolution manufactures two entities from one.** Downstream matchers key on how a
construct is *spelled*, so one entity appears as two and a later pass treats them as unrelated.
**This is W1 with the agency reversed** — there a later *encoder* stage changes the spelling, here
a decoder pass changes it under its own later pass. Partial decoding looks like progress on exactly
the signals tier 3 recommends, so S1/S2 cannot catch it.

**An *evaluating* reversal fails this way whenever it misses one component of the machinery it
runs.** Extract a string array's holder and accessor but miss the rotator and every call site
returns a real string — the wrong one. Output parses, runs, and drives every residue axis to zero.
Two checks catch it with no expected output, so they work on a real sample:

- **Self-validating machinery proves its own extraction.** A component that searches until a
  checksum over the data matches cannot terminate on wrong data. Non-termination then means
  incomplete extraction rather than a hostile sample — which is why timeouts are mandatory rather
  than defensive. **This reading outranks the anti-tamper one**, which gets reached for
  first: a guard built to loop forever on re-spelled code produces the identical symptom, and an
  evaluating reversal does re-spell before evaluating — so that story is always available and wins
  on reputation rather than evidence. It is T6's two-mechanisms case; run the differential
  diagnosis rather than arguing it.
- **Marking a match consumed by emptying it manufactures a duplicate, not a variant.** A collector
  that hollows each match but iterates once per *reference* rather than per entity emits the same
  entity twice, whole and hollow, and whichever resolves last wins. **A sufficiency gate counting
  collected pieces cannot see this** — it reads the duplicate as having found more. Count entities,
  not fragments.
- **A decoded string in computed-member-key position must be a valid identifier**, because the
  encoder put a real property name there. Under a per-item-keyed encoding the same miss also yields
  non-ASCII bytes — louder, but encoding-specific.

Once a structure cannot be partially resolved, the only question left is *when* enough information
exists — T1 for the ordering, T9 for the remedy.

[Incidents](encoder-decoder-incidents.md#t2--w5--shape-keyed-and-all-or-nothing)

### T4 · W3. When bugs cluster, price the refactor against *all* of them

Ask what a cluster shares in how the code **represents** something, not in what the bugs do.
Symptoms with one address look like independent bugs precisely because each patch is cheap, so the
shared cause never gets priced. The honest comparison is refactor-versus-all-the-patches.
**Exception:** when the members are all *consumers* of one half-reversed shape, T9's case 1 beats
this — fix the producer and the cluster evaporates.

**A workaround repeated per consumer is the same cluster in disguise, and it prices the root fix
rather than arguing against it.** The members never look like bugs — each consumer *works* — so the
shared cause is never nominated. The tell is one remedy appearing independently in several callers
of one pass. Count them, and count the ones **not** paying: a consumer silently skipping the
workaround is carrying the defect unrepaired. "They already work around it, so leave the producer
alone" reads N copies of a fix as evidence the fix belongs there, which is this rule inverted.

[Incidents](encoder-decoder-incidents.md#t4--w3--price-the-refactor-against-all-of-them)

## Tier 3 — judging whether a decode worked

Cheap measurements answering "did this actually decode, or did it just not break?" — what you use
*before* a gap is fixed, when there is no trustworthy expected output to diff against. Read S4
first; it rules out the signal everyone reaches for. Read W5 before trusting a clean reading:
S1–S3 all measure **residue**, and an evaluating reversal can be wrong with none. Read S6 before
concluding a pass is correct: S1–S4 all read output, which is half its contract.

### S4. Runtime-correctness is not a decode-quality signal

Passthrough always runs correctly, so a green check at diagnosis time cannot tell "decoded" from
"safely didn't decode". Judge by S1/S2/S3. Its value as a **regression guard** after a fix is real
(T7) — a property of a fixed decoder, not a diagnostic for a broken one.

### S6. A pass's contract is (output, derived state) — verify both halves

S4 rules out runtime and sends you to the output. **S6 says the output is only half the contract.**
A pass rewrites the tree *and* the derived state the framework keeps beside it — cached paths,
scope bindings, reference sets. Leave that inconsistent and the emitted text is perfect byte for
byte, while every later pass consulting it decides against a program that no longer exists. This
is not a blind spot in output-checking; it is output-checking being **structurally incomplete**.

**The invariant, and it needs no knowledge of which bug you are hunting: after a pass, its derived
state should equal what a fresh parse of its own output would produce.** That is mechanically
checkable, it is the second half every case should assert, and *"output unchanged" is not "nothing
happened"* — a pass that removes and rebuilds can round-trip the text perfectly.

- **Scope it by who reads it.** The state worth an invariant is the state a later pass consults;
  derived state nobody consumes needs no assertion. Ask what reads it next and whether that reader
  could tell it was stale.
- **The cheap checks lie**, so for detached references use reachability: a stale one reports
  `removed === false` and its ancestry still reaches *a* Program path, because the cached parent
  chain survives. Ask whether its node is still reachable from the live program.
- **The tell before you have an oracle:** a matcher that accepts a freshly parsed tree and rejects
  every tree a pipeline has touched. A re-parse rebuilds derived state from text, so it repairs
  this class silently — which also makes any measurement taken across a serialize→parse boundary
  evidence about a *different* program.
- **The repair belongs to the pass that breaks the invariant**, not to whichever consumer noticed.
  A consumer-side repair has a placement question; that question is an artifact of the wrong level,
  not a fact about the pipeline (T9). At the producer there is one placement and no mystery.
- **"The pass" means the operation that mutates, and a composition is never it.** Passes compose,
  so the pipeline's units are not the units where defects originate: **every defect originates at a
  mutation** — of the tree, or of the derived state beside it, which is why both halves of this
  rule's own contract are in scope. A file that only schedules performs no mutation and therefore
  cannot be the origin, however clearly the symptom first appears at its boundary. Keep descending
  until you reach an operation.
  - **The check is one second long: open the file you are about to edit and find the operation that
    causes the defect. If it is not in there, you are at the wrong level.**
  - **A repair at a composition works, and that is the trap rather than the reassurance.** Repairing
    where the damage has accumulated fixes the symptom and greens the suite, so nothing prompts the
    question — T9's "a fix you cannot explain" never fires, because a compensating repair is
    perfectly explicable. Prefer the tell above to the outcome.
  - **The one legitimate exception is T9's case 2**: a mutation that is correct and merely
    *mistimed* is fixed at the scheduler, because there is nothing wrong with the operation itself.
    Establish that the operation is correct before accepting this, or it is the same misplacement
    wearing a licence.
  - **Your instrument's resolution bounds the answer**, and its finest unit will be read as a leaf.
    A per-pass probe can only ever accuse a pass. Descend before attributing (probes.md).
- **The oracle belongs in the shared harness, not a probe** (T7).

[Incidents](encoder-decoder-incidents.md#s6--a-passs-contract-is-output-derived-state)

### S1. Size ratio — two of them, and the second works in production

- **decoded ÷ pre-obfuscation source.** The higher the multiple, the more went unreversed. Some
  growth is legitimate — renaming, object extraction and injected dead code leave residue no
  decoder can remove — but a multi-hundred-x ratio means whole mechanisms were never reversed.
  **Take the calibration pair from the run in front of you**, never from remembered numbers.
- **decoded ÷ obfuscated input.** If decoding barely shrinks the file, little was reversed. Needs
  no pre-obfuscation source, so it is the one available on a real-world sample — the production
  case.

Keeping the source beside every fixture (`<name>.src.js`) keeps the first ratio computable. A ratio
is only comparable within one frozen corpus.

### S2. Count the obfuscation-characteristic constructs, before vs. after

A decode should drive them toward zero. **Not** a regex for the residue a partial decode leaves: a
signature regex looks for the wreckage of a decode that ran and didn't finish, so it reports
"clean" both when a decode finished and when it never started.

| family | count |
|---|---|
| control-flow flattening | `switch`, `while` |
| dispatchers / goto encoding | sequence (comma) expressions |
| string concealing | bracket-member reads, array-index lookups |
| packers | `Function(`, `eval(` |

**Pick a count that *can* move before the fix is finished** — one whose subject is only removed by
the last step reads flat through every intermediate step, indistinguishable from no progress. **A
saturated count stops discriminating**; switch to whatever axis is still open rather than building
a second scoreboard for the closed one.

### S3. Zero-reference bindings left in the output

Any runtime helper the decoder was supposed to consume should end at zero references *and* be gone.
Two caveats run in opposite directions, which is why the reference count must be read before either
conclusion:

- **Unreferenced does not mean missed** — obfuscators emit dead helpers of their own, so check
  whether it was ever live in the input. This also bounds use-site-driven decoding: a helper with no
  live references has no use site to be discovered from. **But run that check, because the answer
  routinely inverts:** the same zero-reference helper is what a cleanup sweep leaves when one of its
  gates keys on a spelling an earlier pass stopped emitting. A declining matcher leaves the shape
  intact and is countable by a breadcrumb; a sweep whose deletion gate reads false deletes nothing
  and logs nothing. **Whenever a matcher is taught to resolve through a binding instead of a
  declaration form, audit that pass's deletion gates in the same change.**
- **Referenced does not mean live work either** — every reference can sit inside a *different*
  undecoded layer. An undeleted helper is a symptom to attribute, not a cleanup bug to fix: chase
  the residue holding it alive.

### S5. Obfuscator output is randomized by design

Names, state vectors, key strings and case ordering regenerate per run, and many transforms are
probability-gated — so a transform requested at full strength may still not fire on a given source.
Three to five runs per side on any verdict you intend to act on. Two fresh encodes are not
comparable at all, so **freeze a corpus before A/B-ing anything.** This compounds across an
isolation matrix (T5): a grid that reads clean in isolation may only mean every short run missed
the payload.

[Incidents: S1](encoder-decoder-incidents.md#s1--size-ratio) ·
[S2](encoder-decoder-incidents.md#s2--count-the-characteristic-constructs) ·
[S3](encoder-decoder-incidents.md#s3--zero-reference-bindings) ·
[S5](encoder-decoder-incidents.md#s5--output-is-randomized-by-design)

## Tier 4 — situational

### T5. Isolate a combo gap empirically, then read only what is left

**Reach for this only when a breadcrumb cannot be placed** — the gap appears under a preset or
multi-transform sample, under no single-transform test, and there is no failing site to instrument.
Where a real failing sample exists T6 is strictly better. S5 bounds what this can conclude.

1. Fix one small source shape and a base combo already known to decode cleanly.
2. Obfuscate with base + one candidate transform at a time, forced to full strength (`1`/`true`,
   never a probability), decode, and judge against a structural count (S2). Three-plus runs each.
3. Whichever single addition flips the verdict is the trigger.
4. Shrink the reproducing combo itself — drop one transform at a time, 3–5 runs each. This usually
   shrinks the *sample* dramatically too, which matters for reading residue and for fixture size.

**Read encoder source only after that.** Reading is for explaining a known-minimal reproduction,
not for searching. A cause has needed a *second* transform present to reproduce at all, so a matrix
varying one at a time could not have reached it.

[Incidents: T5](encoder-decoder-incidents.md#t5--isolate-a-combo-gap)
