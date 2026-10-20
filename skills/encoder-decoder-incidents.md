# Encoder/Decoder Incidents — the evidence behind each rule

Companion to [encoder-decoder-method.md](encoder-decoder-method.md). Every rule there was paid for
by a real bug or a wrong plan; this file holds those payments so the rules stay short. **Nothing
here is a rule.** If a fact decides something, it belongs in the method's own text.

**Read this file when a rule is questioned, re-argued or extended.** The incident is what makes a
rule survive a plausible argument against it. Sections use the method's labels, in the same order.
Identifier names in the narratives are historical, not a live API reference.

A new incident sharpens or replaces an existing entry rather than appending a near-duplicate
([Revise by Evolution](doc-conventions.md#revising-a-doc)). An entry whose rule is settled can be dropped; an entry that has
twice stopped a wrong plan cannot.

---

## P1 — work in reverse encoder stage order, each stage placed by its last write

**A late renaming stage** (order 30, over flattening at 24). The flattening decoder identified the
obfuscator's own runtime helpers by literal name suffix; renaming reassigns every identifier,
internal helpers included, with zero functional effect. The lookup returned nothing and the
**entire** control-flow decode failed closed, silently, with correct runtime output.

**A late minifier** (order 28, again over 24). It strips the `BlockStatement` from a single-statement
loop body (`while(x)switch(y)`) and rewrites `a["k"]` to `a.k` for valid-identifier keys, breaking
body-shape matchers that hardcoded the unminified form.

**A one-element rejection wiped out a whole layer.** A literal-extraction array was matched
all-or-nothing, and a later minifier re-spelled exactly one element (`undefined` as `void 0`),
failing the whole array closed and leaving every indexed read, and the prelude they index,
undecoded.

**A later stage rewrote an earlier stage's reference sites.** Flattening at 24 over literal
extraction at 22 rewrote many already-placed reads to index through its own state array. Those are
unresolvable until the flattening decode runs, so the extraction decoder had to be scheduled twice
rather than improved.

**Measuring the prize predicted badly.** One fix measured a large win on the fixtures that motivated
it and a small negative on a full-preset corpus. Both numbers were irrelevant to whether it got done.

**Premature troubleshooting.** Flattening at 24 sits on top of variable masking at 20. Masking was
visibly not reversing its patterns and the tempting move was to breadcrumb its matcher, while its
input still carried flattening residue that survives the flattening decode by design.

**Residue misfiled under an encoder stage, three times.** A rest-masked population blamed on a
masking transform, when the flattening *decoder* gave every reconstructed function a rest param;
undecodable string wrappers blamed on a declaration-hoisting stage, when our own reversal of it left
each restored declaration shadowed; a destructuring spelling blamed on that same stage, which bailed
on non-identifier declarators outright, one guard readable before any measurement.

**Two runs were burned probing for the ordering**, one relocating a decode pass to see whether that
unblocked it. It changed nothing, which was readable from the order enum.

**A unit list justified only by stage order was re-argued at the boundary stage order cannot
explain.** Two units sat in one encoder stage, one the basis for the other, while another stage's
thirteen transformers formed a single unit. A reviewer concluded the boundary was drawn mid-reversal.
The units in fact split along a decode dependency chain that every artifact already behaved as if it
knew and that nobody had written down. The basis unit's inertness on the dependent samples, which
looked like the strongest evidence against the split, is the signature of a foundation.

**A documentation order read as a decode order.** A VM documentation rollout revised the canonical
grammar before the runtime representations, because those specs depend on it. As a fix order that
would have been wrong: a decoder reading grammar first still cannot decode through a minified runtime
shape no proof has admitted. The plan stated the two orders separately.

**The second-encode anchors.** A sample encoded twice where incomplete validation in the first
layer's decode processed second-layer content and threw; and a real decode procedure recorded as six
invocations across three decoders with a hand edit in the middle.

**An evaluating reversal was believed exempt from layer order, then measured not to be.** An inner
prelude extracted verbatim from a doubly-encoded sample throws a `ReferenceError` on the outer helper
it references, because its own literals are outer-encoded calls.

**A stage's junk rule waited on a later write.** A self-modifying VM stage plants junk after an
unconditional terminator and before the next label. A dispatcher stage, invoked earlier, leaves its
jump endpoints as label operands that final address resolution encodes after the self-modifying
pass, so some labels existed only as encoded endpoints the self-modifying decoder could not read.
Its junk rule removed real code before such a label, and a loop body lost a statement. Refusing
those runs was safe; keeping every undecided entry instead broke six later checks, some reading
every entry as program code, some reading layout adjacency. The stage order had been read by
invocation. By last write the endpoint encoding is outermost, so the junk can be decided only after
the dispatcher decoder has recovered the endpoints, and the decoders in between must read past it.

## P2 — attribute era boundaries outward

**A ten-version sweep was attributed from the wrong end.** A sabotage ladder split the versions into
three dependency profiles against the spine, at three boundaries. Work started at the boundary with
**eleven** differing cells rather than the one with **one**, because eleven looked stronger. Two axes
turning there had identical ranges, so nothing could separate them, and two attributions were made
and withdrawn before the confound was noticed.

The one-cell boundary was then attributed in a single reading of data already collected: three axes
turn there, but only one belongs to a single transform, and **only the option set enabling it
flipped**; a shared-subsystem change would have flipped all eight sets reading it. The maximal
profile carrying the same option did not flip, being saturated for other reasons. Reading that
boundary first would have shown the eleven as **ten new plus one carried down**.

**One of the eleven was not an era difference at all but a defect in the measuring decoder.** The
anti-tamper strip removed the *statement* holding its target, and the encoder's statement merging
had fused that target into one sequence with the program's own output calls, so the decoded program
computed everything and printed nothing. Both versions produced the same fused sequence; they
differed only in whether a randomized injection landed inside it. A seeded coin flip had been read
as an era boundary.

**A bound landing on a known boundary produced two confident wrong answers in one sitting.** A
boundary bracketed by two adjacent corpus columns was first attributed to the string-array scope
wrapper, whose era turns exactly there, found by checking only string-array axes. Sweeping all
twenty-one axes showed a second axis turning at the identical point. The second answer picked *that*
axis, on a comparison confounded with profile strength. Diffing encoder source across the two
versions found a third changed component with no axis at all; deriving it found one version where it
moved alone, and measuring there eliminated it. Two one-option siblings of the maximal profile then
attributed half the differing cells and left half explained by neither, which is "confounded", not a
finding.

## P3 — each decoder removes only its own additions, by its own encoder's facts

**The inner decoder was taught the outer decoder's leftovers.** A VM wrapped by an outer obfuscator
failed at the VM recognizer after the outer decode, because the outer decode left control-flow
residue: a hoisted `var` list with later assignments, named function expressions, computed literal
keys. Instead of normalizing that residue between the layers, an agent built a second "assigned"
dialect of the VM recognizer, hundreds of lines, and threaded a debugger-preserving flag back
through the outer decoder because the outer pass's `debugger` deletion emptied a VM handler the
recognizer required. Both coupled the two decoders, each from the other side. The flag was also
unnecessary: deleting `debugger` cannot change program behaviour, so the inner recognizer should
match modulo that rewrite. The work was dropped.

**A stage decoder was charged for the compiler's dead code.** A census compared each VM encoder
option's decoded model with the no-option model and counted every difference as residue. A
self-modifying stage's decoder, which then emitted only reached code, removed every encoder addition and,
with it, the compiler's unreachable return tails and try exits. The item was opened as residue, and
fixes were proposed that taught that decoder the compiler's dead-code shapes to keep a catch's
layout end, which a later consumer read from a dead try exit. The stage had added none of it.

**A stage decoder borrowed reachability and an inner stage's proof.** That self-modifying decoder
walked reachable code and, at each register jump, ran the anti-instrumentation register-flow proof
on the fragment it had reached, to prove finally targets. Under the dispatcher every branch is a
register jump, so the proof saw a few percent of the stream and declined on every full-option
sample. The encoder's own pass reads only widths, block labels, PATCH operands and its cipher, and
patches unreachable code as readily as reachable. Relaxing the anti proof to accept fragments was
proposed first and withdrawn, since it bent a correct inner stage to serve an outer one. The
rebuilt decoder sweeps linearly, removes its headers, decoys and decoy fillers by the encoder's
placement facts, and hands inner stages their addresses through a PC map.

## P4 — every work item names its output measure

**Four phases of work left the decoded output unchanged.** A plan defined "done" as source proofs,
refusal controls and qualification runs on fresh populations. It named no decoded-output measure.
Across four phases the decoder gained a real capability once and otherwise gained guards, censuses
and a native-execution harness of several thousand lines, while its output for a three-line program
stayed register-level code. Nothing in the plan could show that, because nothing measured the output.

## D1 — read the tree and its docs before you probe or propose

**Reading and probing found different kinds of thing on one plan.** Reading turned up a missed
matcher site and a hidden inter-pass dependency; a fifteen-minute probe turned up a semantic gap
neither had, the dead-helper case under [M2](encoder-decoder-method.md#m2-measure-residue-what-an-encoder-stage-added-and-the-decode-left).

**A kept probe inventory drifted into fiction.** Entries described scripts that no longer existed
while scripts on disk were described nowhere. A recipe for rebuilding a probe stays true; a preserved
script silently stops matching the current code.

**Both apparent probe failures were oracle artifacts.** One had a denominator problem: obfuscation
is shape-gated and several samples never exercised the feature ([M3](encoder-decoder-method.md#m3-freeze-the-corpus)). The other measured presence
where it needed liveness: a helper can be present yet transitively dead, and resolving it to nothing
is correct.

**Two items closed with no work once a census ran inside the pass.** The reversal was already in
production in a sibling pass, and the pass under investigation had no candidates.

**The encoder's own doc already held the deciding fact.** A residue axis was carried for several
sessions as "the emitter is unidentified, start by reading the encoder", while the package's own
transform doc named the emitter, called it ungated and quoted its character class. Later, a handler
locator kept a decoy parameter alive because minify had reused it as a local after class
obfuscation stored it into a fake field. Three remedies were proposed from general data-flow
analysis (source order, dominance, SSA versions) after reading only the decoder. The encoder's
transform doc already said the fake fields are never read; with that, the remedy was to remove the
stage's store first and let the existing dead-parameter rules decide, and the decoder's
spelling-based decoy rule turned out to accept real stores as decoys.

## D2 — verify claims before acting on them

**A guard comment laundered into a documented limit.** One session copied "an `UpdateExpression`
slot is marked invalid by design" from a source comment into a skill doc and defended it. The marking
was scoped to *value substitution*; the unmasking routine ignored the invalid list entirely.

**What reading alone could not surface.** A "linear execution order" that reading predicted needed
real branch points once something tried to reverse it; an inline comment was a fossil from an older
encoder version; a helper identified by name proved structurally unreliable under renaming. Each
surfaced only when a decode attempt ran against real combined output.

**Three defects in one option matrix survived every reading** and were found the first time
something ran against it.

**A self-created decoder defect was about to reject prior art.** An architecture memo ranked
source-inspected pages low because no transfer population was qualified, and treated the current
decoder's behaviour as evidence against them. The user caught the inversion: missing transfer work
is not a negative result, and a decoder result cannot settle an encoder mechanism while our own
defect could explain it. The pages were called unqualified, not rejected.

## D3 — instrument one real failure

**Two reading-based hypotheses about a minifier-interaction bug were both wrong**; breadcrumbs on
one real sample got the cause on the first attempt.

**A residual interpreter shape was attributed to an unbuilt in-place decoder** by matching it to the
nearest known-unbuilt feature: a wrong diagnosis, a wrong priority order and a nearly-started
refactor. The real cause was a bare `return;` three lines away.

**The per-stage table localized a whole undecoded layer to one stage on its first run**, and showed
a stage that *grows* the output, which is how an unguarded inlining pass was found.

**Input-vs-output counting silently inverted.** On a flattened sample a count read zero in the input
and non-zero in the output, scoring the residue as ours, for a shape that was the encoder's all along
and merely sealed inside the interpreter. A per-stage run showed it present from the first stage.

**"Did the fix even run?" three times, at a corpus run each.** A pass scheduled where its input did
not yet exist; a matcher whose caller gated on the very blindness the fix removed; a matcher and its
visitor both extended while the call-site filter above still rejected every site. Each measured as
byte-identical output.

**A diff named what four reading-based hypotheses could not.** Nested-pattern support in an
unmasking pass broke four samples: it rewrote an unpack line while references to the same slots,
inside a nested function declared above it, kept addressing a stack nothing populated.

**A load-bearing decline read as a gap.** One gate showed a large pile of declines that had cleared
every other gate, while the output census for that shape read zero: the population was entirely
intermediate. The fix was built anyway and reverted; it blew the corpus up by orders of magnitude,
because a later pass consumed the shape the gate was declining.

**A bucket split once an instance was printed.** A tally reading "reference, not a callee" was
entirely `new F(…)`, whose arity is readable; most of the population closed on one line.

**A name-filtered breadcrumb inverted its answer.** Gated on one identifier, it read zero hits and
the pass was declared unreached. It was reached repeatedly with that name, which a renaming stage
reuses across non-overlapping scopes.

**A fully breadcrumbed pass reported matches and no rejected site** while every match died in a
caught exception. The failures became countable only once the warnings were tallied.

**A combo cause needed a second transform present to reproduce at all**, so a matrix varying one
transform at a time could not reach it.

**A truth oracle for optimized output.** Identifications of minified handlers were checked by
re-encoding each case with the same seed and options minus the final optimizer: allocations match,
and the encoder's own handler comments name every case. All 160 checkable identifications agreed.

## D4 — fix the producer, not the consumer

**A handoff failure was answered with qualification instead of diagnosis.** A layer handoff declined,
and the write-up recorded that the decline "does not establish that the producing decoder is wrong".
Each later step built verification and harness work around the consumer while the producer was never
diagnosed. The producer, our own outer decode, was the cause ([P3](encoder-decoder-method.md#p3-each-decoder-removes-only-its-own-additions-by-its-own-encoders-facts)).

**Auditing the consumers of one half-reversed shape turned up dozens of candidate sites**, of which
two were ever live, and none needed changing once the producing pass stopped emitting the shape.

**Case 3's anchor.** An unmasking routine needs an exact parameter count and can read one only from
a truncation statement that one transform's entries never carry. Three callers now supply the count
and drive the reversal directly: the pass's own entry from the truncation statement, a function-length
pass from an unwrapped `fnLength(fn, length)` argument, and a dispatcher pass from the template's
zero declared params.

**Case 4's one right answer.** An obfuscator emits its helpers by re-running itself over each helper
template with a few forwarded options, so exactly those options bound how a helper can be re-spelled.
A matcher folding arithmetic and flattening sequences was complete against that set.

**An unresolvable slot documented as an inherent limit.** A fail-closed guard was built in the
consumer; the resolving routine existed all along and was simply unreachable.

**A repair at a composition, then at a consumer, before the operations.** A decode threw
`ReferenceError`: a control-flow storage declaration was deleted with one live reference left. The
consumer's completeness gate was correct but read a reference list inflated to 112 entries for 102
live nodes. Bisecting located the inflation after a normalization pass, and the repair was written
there; it worked. That pass rewrites nothing: its header says it is scheduling only, seven `traverse`
calls. The probe had per-pass resolution, so its finest unit was read as a leaf. Challenged, the fix
was moved to the consumer without measuring, which was also wrong: the consumer's own crawl repairs
some inflation. Measuring the seven visitors one at a time found four that inflate, three shared with
other plugins and untested. At the four operations the output was byte-identical, the shared visitors
became correct for every consumer, and the composition-level patch was deleted as redundant. Opening
the file first would have settled the level in one screen.

## D5 — use what earlier steps established

**A proved table that never reached its consumers.** One stage identified the VM's opcode meanings
by handler behaviour, but the readers of added opcodes partitioned handlers by the default
canonical values and failed once values were randomized. Identifying every canonical handler first,
then using them both to exclude (what is left is added) and as references, identified every added
handler across twelve encoder profiles.

## F1 — select what the program cannot run without

**Declarator spelling was taken for identity.** Packet A read every container role from
`var NAME = init`. The outer encoder's moved declarations split each into a declaration plus an
assignment, so normalization joined them back. That join then rewrote per-handler functions as well
and broke a class-template comparison (class obfuscation plus handler table). Selecting the single
top-level defining write instead recovered every case byte-identically with both normalizing passes
removed.

**A resolved name is still a name.** A pass received its target as `{ scopeName }` and reasoned that
it came from the interpreter's own shape, so it was not name matching. It held a string. The tell:
the "live keys" it reported were `indexOf`, `length`, `key`, `val`, members of an ordinary array.

**Source positions.** Earlier passes reparse function bodies and synthesize statements, so
`node.start`/`node.end` are absent or fragment-relative. A containment test built on them reported a
function's own local as an outside dependency and hoisted it out of scope.

**Cached scope state was stale, and the symptom pointed the wrong way.** A pass resolved two control
declarations through the scope's binding table, recorded at the last crawl. Earlier passes replaced
nodes, so the binding pointed at a detached node that printed identically, and identity comparison
failed silently. The pass accepted every hand-built case and rejected all real corpus blocks. A
sibling scan of the live tree fixed it.

**Opcode values read as roles.** Readers of a VM's added opcodes assumed those opcodes start one
past the canonical range, contiguous and in the order the encoder's stages created them. An option
that randomizes opcode values allocates them at random free values, and every reader declined
before reading a single handler body.

**Two bodies from one template.** An encoder bakes a literal operand into a copy of a handler; a
final whole-program optimizer then minified each handler function on its own. The copy came out as
one statement and the original as three, because the optimizer folds a local holding a literal but
keeps one holding a read whose order matters. Statement comparison matched 4 of 20 copies; comparing
effects (reads as ordered slots, locals as carriers) matched all 20.

**Positions were renumbered and the old ones dropped.** A VM decoder compacted the word stream at
every stage and forwarded each removed location to the next kept instruction, so an early stage
could delete what it took for junk after a terminator. A later stage decoded a jump target from an
encoded operand no earlier stage could read; it named one of the deleted instructions, the forward
moved it to the next one, and a loop lost its first statement while every check passed. Keeping the
encoder's address as each instruction's identity and giving removed locations no entry turned the
silent miscompile into a refusal.

## F2 — resolve completely or not at all

**Half-resolution manufactured two entities from one.** Resolving only the readable share of a
literal array left one slot written as `slot[-1]` at some sites and `slot[-literals[1]]` at others.
The masking decoder read two slots and split one object in two. Output was silently wrong on a
minority of samples, on a change where every size metric improved.

## F3 — keep tree and derived state consistent

**The incident that produced the rule.** A pass stripping anti-tamper helpers declined on every
sample combining debug protection with control-flow flattening, emitting code that threw. It had
been certified through a staged probe chain that re-parsed each stage's output; rebuilt on one AST
per cell, runtime equivalence fell from the whole corpus to 489 of 597. The reparse had silently
repaired the state the real pipeline carries.

**Fixed at the wrong end first.** A `traverse.cache.clear()` at the failing pass's entry restored the
corpus. Clearing between the pass's two phases did not, so the position was recorded as "measured, do
not tidy". There was nothing to explain: the repair was at a consumer, compensating for something
upstream.

**The producer had declared the defect in a comment.** The pass that detached the references said
`The code must be reloaded to update the references`, read as a contract its callers accepted. Of four
consuming plugins, three answered it with a full re-parse and the fourth did not answer it at all.

**The argument that nearly kept it there** was "three plugins already reload, so fixing the producer
makes them pay twice", which reads N workarounds as evidence the workaround belongs at the consumers.
A user objection, twice, overturned it. The fix was one `scope.crawl()` on the producer's
`Program.exit`, gated on having detached anything; the consumer's cache clear was then removed with
output byte-identical across all 597 cells.

## F4 — keep a guard only where a real case needs it

**One guard cluster, the same wrong inference, years apart.** Guards existed to make substituting a
*value* safe (rejecting nested scopes, `++` updates, reassigned aliases) and silently also blocked a
pure *rename*, which needs none of them. Later a slot rejected for a `++` update was written up as
unresolvable, when only value substitution was at stake; promoting the slot to a real local handles
`stk[3]++` as `_local++` perfectly well.

**Coupling no document recorded.** A later pass rejected any function body capturing outer variables,
which an *undecoded* interpreter body always does. That pass silently declined on exactly the
programs where an earlier pass had already failed.

**A reviewer's completeness request became a guard.** A review asked for a "complete dispatch label
domain proof", and a guard was added rejecting VM dispatch tables with duplicate or shadowing labels.
Every test fed it hand-edited sources no encoder emits. It protected nothing real and was dropped.

**"Exactly one handler per opcode" against cloned handlers.** A gate named a handler only if no
other handler fit the same template. The encoder's specialized copies fit too, so ten original
handlers went unnamed beside their own copies. The most general member (the one reading the most
operands) is the original; an identity-order alias behaves identically and shares its meaning.

**A fallback measured before it was removed.** Before deleting a runtime anchor and its routes, a
run with them disabled on a scratch copy showed two routes decided nothing on any input and a third
decided exactly four fixtures, which became the work to cover first.

## F5 — one fix is never the whole fix

**The detector came 26 minutes after the fix.** The reachability walk that made [F3](encoder-decoder-method.md#f3-keep-tree-and-derived-state-consistent)'s incident
provable, asserting no binding holds a reference to a node outside the tree, was written after the
fix it validated, so it could only ratify a repair already chosen, at the wrong level. Placed in the
shared test helper, it then audited every existing case for free, which is how the seventh case in
[F7](encoder-decoder-method.md#f7-a-shared-pass-needs-off-path-cases) was found to fail in one line.

## F6 — revise the owning rule, never patch beside it

**A workaround repeated across four consumers was read as evidence against fixing the producer**,
which inverts the rule; the consumer not paying it was the finding ([F3](encoder-decoder-method.md#f3-keep-tree-and-derived-state-consistent)).

**Three open issues, one address.** A rename-reliance failure, an unhandled member-chain state
accessor and a residual harness never cleaned up all came from storing identity as a name string in a
context object rather than as a binding or a NodePath. A string cannot represent `scope.a.b`, survive
renaming, or be revisited to clean up what it named. Each patch was cheap, so the shared cause stayed
unpriced.

## F7 — a shared pass needs off-path cases

**A corpus that could not test a shared visitor.** A control-flow pass used by three decoders reversed
every live block of one encoder's whole frozen corpus with the residue census at zero, and its
keep-or-fork call was about to rest on that. A field report said otherwise, and hand-built cases
confirmed three behaviours worse than declining: an ordinary `while (!done)` loop **deleted**, a case
without a terminator **duplicated**, a discriminant without `++` **threw**. All three are unreachable
from that encoder, so the corpus was no evidence about them.

**Cases that existed and still could not see it.** A shared visitor had six passing cases, all built
from one encoder's dead-code shape. A seventh, three lines with a dead branch referencing a binding
declared outside it, failed at once on an assertion the six had run all along.

**A normal form on one side only.** Inlining single-use locals was added to a lowering shared by
several readers, to make two handler bodies compare equal. Five decodes that had worked failed:
matcher templates and a reader's own substituted body were never inlined, so only one side of each
comparison changed.

## M1 — judge an output by how it reads against its source

**Two candidate rules ranked by a regression count.** A VM decoder needed a rule for where a function
ends. One candidate (every return or uncaught throw ends it) broke eight fixtures, another (prefer a
return) broke none, and the second was declared better. No output had been read. All eight
failures came from two other defects: every call's implicit exception edge counted as an uncaught
throw, and loops still found their end through the function's end. The only output the first
candidate changed in shape, a guard clause turned into an inverted `if`/`else`, was the readability
question nobody had asked.

## M2 — measure residue: what an encoder stage added and the decode left

**The calibration pair.** A `high`-preset decode came out hundreds of times larger than its source
and was mostly raw scaffolding; a complete decode of a dispatcher-wrapped function collapsed to about
the original's size. The gap between those orders of magnitude is the signal.

**A signature regex scored a total non-decode as clean.** A run showed zero residual interpreter-loop
signatures and was celebrated, while a direct `switch` count was unchanged: no interpreter had been
touched.

**A count that could not move was twice read as "not the fix".** Its subject is only removed by the
last step of a multi-step fix.

**Dead on arrival.** A sample arrived with an XOR string helper with zero call sites, plus the blob
only that helper read: the encoder's own dead code.

**A deletion gate keyed on a spelling an earlier pass stopped emitting** kept a runtime helper on a
large share of samples, a third of all decoded bytes, through three censuses that asked about the
pass's matcher rather than its deletion gate.

**Referenced, and still residue.** A helper referenced only from harnesses a later fix removed went
to zero without anyone touching the sweep. Seen twice.

## M3 — freeze the corpus

**An isolation grid that could not bound what it was asked to.** Several matrix cells were partial
while the same combos read clean in isolation, and "no transform is individually implicated" was
recorded. The cause was one transform's random per-run template selection, reachable from a
two-transform combo at a rate the grid's short runs could not bound.

**Cases that were never frozen.** Reproducers for a control-flow rule were re-encoded inside one-off
commands on every comparison and never saved. The encoder drew no randomness, but nothing recorded
that, so none of the figures read from them could be reproduced.

## M4 — a control must reach its mechanism

**Three controls that read as expected and proved nothing.** A case deleting a rotator used array
items that were all valid identifiers, so the wrong strings were plausible and the identifier check
stayed silent. A second corrupted an element the checksum never reads, so a *different* guard refused
and the status said nothing about the timeout it claimed to test. A third had scaffolding (a reporting
line) whose member names crossed the encoder's minimum-length gate and populated the very array the
case meant to show was never built. Each was fixed by asserting the diagnostic and feeding it a case
that cannot match.

**Emptying a match to mark it consumed, then re-emitting it.** An extraction collected the enclosing
function once per *reference* to a string array, hollowing it after the first collection. Where the
accessor named the array twice, the text ended with a hollow redefinition; under the era whose
accessor is a hoisted function declaration the hollow one wins, the accessor returns nothing, and the
rotator's checksum search runs forever. The sufficiency gate counted five fragments against a minimum
of three and passed.

**The same incident was first recorded as anti-tamper.** The hang was written up, with a mechanism,
as the self-defending guard detecting re-spelled code. Four cheap checks each refuted it: the sample
ran untouched; the guard's shape was absent from the file; the plugin's regenerated fragments
terminated once only the duplicates were removed; and a sweep bounded the failure to exactly the two
versions spanning the hollowing branch. The wrong story survived on reputation.

**An evaluating reversal that missed one component.** A string array's holder and accessor were
extracted while the rotator was read as absent, because its matcher keyed on a spelling the encoder's
statement merging had fused away. Output parsed, ran and drove every residue axis to zero. With the
rotator missing, most decoded strings in computed-member-key position were not valid identifiers;
with it present, none.

## Studying a new encoder/decoder pair

**The worked example of the process** is the `js-confuser` package
([js-confuser.md](js-confuser/js-confuser.md)), studied end to end before the method was written.

**An incumbent's claimed range set the starting era once.** The javascript-obfuscator study opened at
`2.19.0` while the pin was `5.5.0`, because it audited an incumbent decoder's claimed range and
`2.19.0` was the newest release inside it. It is the exception, not the pattern.

**An existing encoder was mistaken for an existing pair.** A new read-only decoder corpus targeted
encoders whose packages already existed, so the work looked like an extension of those studies. The
relationship had never been studied, and treating component identity as pair identity would have
skipped the new-pair workflow exactly where it was needed.

**Qualification-first documentation nearly discarded useful VM prior art.** Experiment folders held
source-backed algorithms, some incomplete, unrunnable here, or without a qualified transfer. One
`unqualified/uncovered` label for all three kept the material out of mechanism docs. The user reversed
that: preserve source and deductions once provenance and limits are clear, recording documentation,
transfer qualification and reproduction separately. The first graduation then showed the opposite
failure: pages met every structural contract while compressing algorithms into summaries no reader
could rebuild. Provenance says where a claim came from; it does not teach the mechanism. The
acceptance test now requires cold reconstruction before source citations are opened.

**This project's closed bugs are almost all combo bugs** no single-transform fixture could catch: a
renaming stage invalidating a name-keyed matcher, a hoisting stage splitting a harness from its entry
point, a statement-merging stage dissolving a partition a downstream matcher expected.

**Tiers are not always subsets.** `low` in one obfuscator skips control-flow flattening entirely.
