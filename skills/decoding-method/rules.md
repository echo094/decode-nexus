# Decoding Rules

How to plan, diagnose, fix and measure a decoder, whatever is known about the encoder. It names no
single project ([Project Independence](../doc-conventions.md#project-boundaries)). Rules that need
the encoder are in [with-encoder.md](with-encoder.md); rules for a target with no encoder available
are in [without-encoder.md](without-encoder.md).

**Each rule opens with one bold line: the rule itself.** The paragraphs beneath it explain how to
apply it. The real bug or wrong plan behind each rule is in
[incidents.md](incidents.md) under the same label. Read an incident
when someone questions the rule, not every session.

A rule enters once it is restated without the encoder, or proved to hold without one,
together with every rule it references.

## P — Plan the order

### P1

**Before a work item starts, name the decoded-output measure it should move and the samples it is read on.**

Before a work item starts, name the [M2](#m2) measure it should change on real samples (a residue count
falling, a size ratio shrinking, a helper disappearing) and the samples it is read on. The item is
done when that measure moves and every other output it changes has been read ([M1](#m1)). Proofs, refusal controls, qualification runs
and harnesses support a decode; they are not progress on their own, and a plan whose items name no
output measure cannot show that the output is getting better.

### P2

**When you budget a unit, count the questions it must answer, not the code it should produce; a unit can close with no new code.**

Two units closed with no new code and still cost a doc of what they reverse, a census and
fixtures. Don't read a unit's value off its diff.

## D — Diagnose

### D1

**Read the decoder's code and its owning docs before you probe or propose; what already works or is already decided beats any experiment.**

Validate a plan in this order. First, grep the packages and the decoder for the subject: a matcher
that already does the job correctly is free, stronger than a probe, and also answers who owns the
reversal. An open item may already be answered in a doc the same study wrote. Before proposing a
remedy, read the contract of the component it would change: a recommendation that contradicts a
recorded decision reverses that decision, which only the user may do. Then run a throwaway probe:
reading and probing find different kinds of thing, so budget for both, and keep the recipe rather
than the script, since a kept script silently stops matching the current code. Whichever way the
probe reads, suspect the sample and the oracle before the code: check the denominator, and check
the oracle measures liveness rather than presence.

Only normalization independent of any one obfuscator transfers between decoders: operator-to-statement, sequence splitting, re-bracing. Reversal specific to one does not, so
never generalize this into "search the repo for prior art"; one plugin of about 1,300 lines has
about 350 lines of such normalization and the rest has no analogue next door.

### D2

**A comment, doc, status or spec is a claim; verify it before you act on it.**

A comment, a doc or a "covered" status described intent when it was written; its target can
change under it silently. Never document a mechanism from memory or inference.

- **Distrust most a guard comment saying something is impossible.** "By design" describes the
  operation the guard was written for, never everything it now blocks. Copying one into a
  skill doc turns a hypothesis into a documented limit.
- **A comment stating a caller obligation is a defect report.** "Reload afterwards", "call this
  before X": it is almost always a repair the pass declined to do. Count the callers; the ones not
  paying it are the finding.
- **A claimed necessity is a claim to measure.** A comment saying an order is load-bearing is the
  same object as a guard saying a shape is impossible. Write the measurement beside the claim or
  do not make it.
- **A status is only as strong as its criterion.** Anything closed on runtime correctness alone was
  closed on nothing.
- **A specification is not validated until something runs against it.** Reading confirms only
  that it is internally coherent.
- **Missing evidence is unqualified, not disproven.** Do not turn a gap, or a result our own defect
  could explain, into a verdict about the target. Find our defect first, then decide.
- **Documenting a mechanism, showing a borrowed algorithm works here, and reproducing a result are
  separate claims;** never infer one from another. Code or notes may graduate as prior art, citing
  their provenance and limits, once those are clear; that neither grants decoder coverage nor
  opens implementation.

### D3

**When you look for the cause of a failure, instrument one real failure; never root-cause from reading alone.**

Every cause found here so far was found by breadcrumbing a real failure, none by an isolation
matrix. A residual shape proves that something failed, never what. Pick the instrument by what the
failure looks like:

| Question | Instrument | Note |
|---|---|---|
| Which guard rejected this shape? | Bail-out breadcrumb | Tag every `return null` with its own source line |
| Which stage made the output look like this? | Replay the pipeline stage by stage on one real sample, printing size and a structural count | A stage that should shrink and reads `+0` never fired; a stage that grows the output is a finding. Build it before reading any matcher |
| Is this residue ours or the input's? | The same per-stage replay | Never input-vs-output counting: it fails while an outer layer still hides the construct |
| Did the fix even run? | The breadcrumb, asked of the caller | A correct fix that never executes gives byte-identical output |
| The pass ran and the output is wrong | Before/after diff at the site the error names | A guard counter cannot see this |
| Two mechanisms could explain one symptom | Differential diagnosis, below | The plausible one wins by default unless tested |

**Differential diagnosis.** Each step removes a candidate; the earliest can end the search.

1. **Run the artifact untouched.** If it already misbehaves alone, nothing downstream is implicated.
2. **Test that the accused shape is present,** with a positive control that carries it.
3. **Bisect your own operations** one at a time from none applied.
4. **Hold the rival explanation constant** and vary only the suspect.

**Five ways the instrument lies.**

| Lie | Correction |
|---|---|
| A bail tally measures the pipeline's interior, not its output | A decline is not a defect until an output census says so; a declining gate can be load-bearing |
| A tally names the gate, never the thing | Print one offending candidate's bindings before writing a cause down |
| A pass with no candidates looks like one that resolved everything | Census inside the pass first; establish the population is non-zero |
| A breadcrumb filtered by name inverts its answer | Dump every call with its resolved binding's location |
| A guard counter cannot see a failure after a successful match | Instrument the catch blocks; a caught exception reads as a clean pass |

### D4

**When a pass cannot read the shape it receives, find our own operation that produced that shape and fix it there, not in the consumer.**

When a pass cannot match what an earlier pass or layer left, the reflex is to teach the matcher in
front of you to tolerate it. That is the last option, because it is the same fix paid again at
every consumer. Diagnose first:

| Case | Remedy |
|---|---|
| 1. The producing operation emits a wrong shape | Fix that operation |
| 2. The input does not exist yet, but will | Reschedule the pass, possibly to run twice |
| 3. The producer is correct but lacks a fact | Route the fact to the pass that owns the reversal and call it directly |
| 4. None of the above | Tolerate it in the consumer, knowing you will pay again |

Empirically the cause has always been case 1 or 2: a shape one of our own passes emitted, never a
matcher merely too narrow. So a failure at one of our own handoffs, including a layer handoff,
is our defect until shown otherwise. Diagnose the producer before anything else; a qualification
run or a widened consumer is not an answer to it.

- **"The producer" is the operation that made the shape a consumer receives:** one of our own
  passes' mutations or, for a shape the input itself carries, whatever made the input. Cases 1–3
  act only on our own; a shape the input carries is case 4. Our producer is the operation that
  mutates, never the composition that schedules it. Every defect originates at a mutation of the syntax tree or of its derived state. A file that only schedules
  cannot be the origin. The one-second check: open the file you are about to edit and find the
  operation that causes the defect; if it is not there, you are at the wrong level.
- **Separate case 1 from case 2 explicitly.** Case 1 is a wrong operation, fixed at that operation.
  Case 2 is a right operation at the wrong time, and is the only case a scheduler-level fix is
  correct for. Establish the operation is sound before reaching for the scheduler.
- **Separate case 1 from case 3 too.** The tell is whether the upstream pass is wrong or merely
  stopped. Case 3 creates a direct call dependency and mutates before the calling matcher has
  confirmed its own match; decide what happens to that mutation if the match then fails.
- **A shape the producer's documented contract emits is not a bad shape.** When a contract defines
  the form its consumers must read, the consumer that cannot read it is the defect; check the
  contract before naming the producer.
- **A producer can be wrong while its output is right.** It can leave derived state inconsistent
  with the syntax tree it rewrote. Ask what a pass leaves behind besides its output before ruling
  out case 1.
- **Reading a pass's guards writes down its coupling.** Docs describe what a pass does when it
  succeeds; its refusals show which earlier passes it depends on, and so which passes cannot be
  measured until an earlier gap is fixed.
- **A fix you cannot explain is a defect report.** A repair that works only in one position is
  probably compensating for something upstream. A repair at a composition is the trap: it greens
  the suite and is perfectly explicable, so prefer the one-second check to the outcome.
- **Case 4 is right only for a re-spelling the input itself carries,** where there is no producer
  of ours to fix.
- **Your instrument's resolution bounds the answer.** A per-pass probe can only accuse a pass;
  descend to the operation before attributing ([probes.md](../decode-js/probes.md)).

### D5

**When a later step needs a fact an earlier step proved, use the proved fact; never re-derive it from a default or from how the code is written (names, layout, statement shape).**

A proved fact narrows the unknown population and is the reference for the rest. A fact an earlier
step has proved (an identified role, a matched table, a resolved index) is an input to every later
step. It narrows the unknown population, since what is left is what remains to
identify, and it is the reference the rest is identified against. A later step that guesses the
same fact again from a default or a spelling is [D4](#d4)'s case
3 seen from the consumer: the fact exists and was never routed. So identify the cheapest certain
members first, then let them constrain the rest, and check that every consumer reads the
established fact rather than its default.

## F — Fix

### F1

**When a pass matches a structure, resolve it completely or leave it untouched.**

If the input for part of a match is missing, schedule a second visit for when it exists. Leaving
the structure alone is cheap and safe; a half-way state is neither. Half-resolution manufactures two
entities from one: downstream matchers key on spelling, so one storage slot spelled two ways becomes
two slots, and a later pass treats them as unrelated. This is the failure of a later stage rewriting what an earlier
matcher reads, with the agency reversed: our own pass changing how a slot is written under our
own later pass, and it looks like progress on
every residue measure ([M3](#m3) has the checks that catch it). Define the unit of atomicity for every
transform ([doc-conventions.md](../doc-conventions.md)).

### F2

**When you fix a defect, grep for its shape everywhere, and turn the audit into a harness assertion.**

A defect's shape almost never occurs once. Grep for the shape across the pipeline before closing
the item. Where the condition is computable, make the audit an assertion in the shared test helper
every case runs through: a grep is one-time and only as good as its pattern, while a harness
assertion audits the whole suite and everything added later. Where a defect is invisible in output
([F3](#f3)), build that detector before the fix: then it demonstrates the defect, where built afterwards it
can only ratify a fix already chosen.

### F3

**After a pass rewrites the syntax tree, its derived state (cached paths, scope bindings, reference sets) must equal what a fresh parse of its output gives.**

A pass rewrites the syntax tree and the derived state kept beside it: cached paths, scope bindings,
reference sets. Leave that state stale and the text is perfect while every later pass decides
against a program that no longer exists. Output checks are structurally blind to this, and "output
unchanged" is not "nothing happened".

- **Scope the check by who reads the state.** State no later pass consults needs no assertion.
- **The cheap checks lie.** A detached reference reports `removed === false` and its cached parent
  chain still reaches a Program path. Ask whether its node is reachable from the live program.
- **A serialize→parse boundary repairs this class silently,** so a measurement taken across one is
  evidence about a different program.
- **The repair belongs to the operation that breaks the invariant** ([D4](#d4)), and the check belongs in
  the shared test harness ([F2](#f2)).

### F4

**When a matcher picks out a role or structure, select it by what the program cannot run without, never by how the code is written (names, declarations, layout, statement shape, distances, allocated values); a location is identity to whatever jumps to it.**

Every obfuscating stage, a later layer's included, adds complexity and keeps the program's behaviour in a
production environment, so behaviour is the only invariant; a debug-only statement and a check that
always passes in a normal environment are not behaviour either. A role is identified by the
conditions whose violation would break the program: a binding written exactly once, before any
read, whose value has the role's shape and is used where the role is used.
A control merge is the block every continuing path must pass, not the block nearest both arms.
Name text, declaration form, initializer placement, braces, member spelling, block order and block
distances are spellings whatever produced the input, a later layer or our own passes can vary; matching on them
makes a valid program decline or pick a wrong structure. Read the defining write, not the
declarator; the postdominator, not the distance.

The audit is a grep, not a review ([F2](#f2)). Seven traps survive knowing the rule:

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
  structural question instead ([F3](#f3)).
- **A value the input's producer allocates is spelling.** Opcode numbers, label values, their ranges,
  contiguity and allocation order can all be randomized; identify a role by what its code does,
  never by where its value falls.
- **After a whole-program optimizer, statement shape is spelling.** The optimizer rewrites each
  function on its own and folds or keeps locals by their content, so two bodies cut from one
  template diverge. Compare effects, not statements: reads as ordered slots, locals as carriers.
- **An address is spelling to a matcher and identity to a jump.** Never select a role by where it
  sits, and never renumber or drop a location unless every reference to it is rewritten, including
  concealed or computed ones the current stage cannot read. "Nothing visible jumps here" proves
  nothing. Keep the input's final address as each instruction's identity, translate every
  reference through it, and make a reference to a removed location refuse instead of landing on
  the next one.

### F5

**When a defect shows our decoder deciding wrongly, revise the code that owns that decision; a special case beside it is a patch the next variant pays again.**

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
every member consumes one half-reversed shape, [D4](#d4) beats a refactor: fix the producer and the
cluster disappears.

### F6

**When a pass is shared by several decoders, test it on hand-built cases off every decoder's input path, each a shape its producer could hand it from real input; its normal form must reach both sides of every comparison.**

A matcher validated only on an isolated single-transform fixture is not proven against combined
output, which adds exactly the later stages that break it. And a matcher validated on one input population's
whole corpus is not proven sound once another decoder shares it: that population's regularities are
invisible from inside, its gaps are the inputs it never contains, so every census reads clean.
Judge a shared pass on hand-built cases that leave every population's path, chiefly where it would
corrupt or throw instead of declining. A case must be a shape its producer could hand it from real
input: behind a conversion, the conversion is the producer and the origin is still real
input. One the source language cannot express (a catch entered from outside its try, a try
statement with a second normal completion) is no case, and a test pinning it designs the pass for an input
no producer emits. Before changing a shared pass, enumerate its consumers and
read what each already does to work around it ([F5](#f5)). Field reports are evidence no corpus replaces.

A normal form belongs to the comparison, not to one side. A canonicalizing step in a shared pass
must reach both sides of every comparison its consumers make (templates, forms a consumer builds
after its own substitution), or it manufactures the differences it was meant to remove.

## M — Measure readability

### M1

**When you judge a decode or a design change, read the outputs: a passing run proves nothing, and neither does a changed output, or a count of them, until it is read.**

Passthrough always runs correctly, so a green behaviour check cannot tell "decoded" from "safely
didn't decode". Judge by reading the output. Runtime equality is still a real regression guard
after a fix.

The converse holds too. A changed, even worse-looking, output is a finding, not a regression: group
the changes by structural signature, read one diff per group, and run the behaviour oracle before
judging.

**Nor does a count of changes value a design.** Choosing between candidate designs comes down to
one question: does the output's readability deteriorate? Read each changed output, grouped by
structural signature, with the readability metrics beside it. A tally of the fixtures each
candidate breaks or keeps adds up unread changes, and can charge one candidate for a defect in
another rule it leans on.

### M2

**When you measure what a decode removed, count what the obfuscation left that a decoder can tell apart (characteristic constructs, leftover helpers) and compare decoded size with the input's; what no decoder can tell apart and what changes nothing the program does is how the code is written, not residue.**

- **Residue is what the obfuscation added and a decoder can tell apart.** An addition no
  decoder's facts can ever tell from code an earlier stage could emit, and that changes nothing the
  program does, is how the code is written ([F4](#f4)), not residue: a jump a flattening decode
  leaves where it split a block is one more `JUMP`, like the compiler's own. It is left as is,
  remapped like any code passing through and never counted, and no decoder removes it by a guess.
- **Size ratio.** Decoded size over obfuscated input: if decoding barely shrinks the file, little
  was reversed; this one needs no source, so it works on real-world samples. It assumes the
  obfuscation inflated the code; a mechanism whose decode expands compact data into statements (a
  VM's bytecode, say) can raise it while the decode improves. A ratio compares only within one
  frozen corpus.
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

### M3

**When you build a control or check, make sure it reaches the mechanism it names; one that misses still reads as expected.**

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
  which is always available and wins on reputation; run [D3](#d3)'s differential diagnosis rather than
  arguing it.
- **Count entities, not fragments.** A collector that hollows each match to mark it consumed but
  iterates per reference emits the same entity twice, whole and hollow. A gate counting collected
  pieces reads the duplicate as abundance.
- **A decoded string in computed-member-key position must be a valid identifier,** since a real
  property name stood there before the obfuscation.
