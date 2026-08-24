# Encoder/Decoder Incidents — the evidence behind each rule

Companion to [encoder-decoder-method.md](encoder-decoder-method.md). Every rule there was paid
for by a real bug or a wrong plan; this file holds those payments so the rules themselves stay
scannable. **Nothing here is a rule.** If a fact is load-bearing for a decision, it belongs in
the method doc's own text, not in an entry below.

**Read this file when a rule is being questioned, re-litigated, or extended** — the incident is
what makes a rule resistant to a plausible-sounding argument against it. Otherwise read the
method doc alone.

**Sections are keyed on the method doc's rule labels**, which are stable identifiers rather than
positions. A merged rule keeps both labels and both label headings appear here. Identifier names
in the narratives are historical record, not a live API reference; a name that no longer exists
in either tree still names its incident correctly.

Per `SKILL.md`'s Revise by Evolution, a new incident **sharpens an existing entry** or supersedes
one — it does not append a near-duplicate. An entry whose rule is settled and never questioned
can be dropped; an entry that has twice stopped a wrong plan cannot.

---

## T8 — validate a premise before implementing against it

**A guard comment laundered into a documented limit.** One session copied "an `UpdateExpression`
slot is marked invalid by design" out of a source comment into a skill doc and then defended it.
The marking was scoped to *value substitution*; the un-masking routine ignored the invalid list
entirely. The phrase described the operation the guard was written for, never the full set it
blocked.

**Reading and probing found different classes of thing on one plan.** Reading turned up a missed
matcher site and a hidden inter-pass dependency; a fifteen-minute probe turned up a semantic gap
neither had — the dead-helper case under S3. Budget for both rather than choosing.

**A kept probe inventory drifted into fiction.** Entries described scripts that no longer existed
while scripts on disk were described nowhere. A page saying how to *rebuild* a probe stays true;
a preserved script silently stops being honest against the current matcher.

**Both apparent probe failures here were oracle artifacts.** One had a denominator problem —
obfuscation is shape-gated and several samples never exercised the feature (S5). The other
measured presence where it needed *liveness*: a helper can be present yet transitively dead, and
resolving it to nothing is correct.

**And the same fault in the other direction — three times, each reading as expected.** Building
positive controls for a decoder's refusal paths: a case that deleted the machinery's rotator used
array items that were all valid identifiers, so the wrong strings the miss produces were plausible
ones, the identifier check correctly stayed silent, and the case reported a clean decode. A second
corrupted an array element the checksum never reads, so the search terminated and a *different*
guard refused — the status was the expected one and said nothing about the timeout it claimed to
exercise. A third was the probe's own scaffolding: a reporting line appended to make runtime
output observable introduced member names over the encoder's minimum-length gate, populating the
very array the case existed to show was never built. Fixed the same way each time — assert the
diagnostic rather than the status, and verify that assertion by feeding it one that cannot match.

**What reading alone could not surface.** A "linear execution order" that reading predicted
needed real branch points once something tried to reverse it; an inline comment that turned out
to be a stale fossil from a previous encoder version; a helper identified by name that renaming
proved structurally unreliable. Each surfaced only when a decode attempt was made against real
combined output.

## T6 — instrument the failure

**Two reading-based hypotheses about a minifier-interaction bug were both wrong**; breadcrumbs
against one real sample got the cause on the first attempt.

**A residual interpreter shape was attributed to an unbuilt in-place decoder** by matching the
residue to the nearest known-unbuilt feature. That produced a wrong diagnosis, a wrong priority
order, and a nearly-started refactor that would have fixed nothing. The real cause was a bare
`return;` three lines away.

**The per-stage table localized a whole undecoded layer to one stage on its first run**, and is
also where a stage that *grows* the output shows up — which is how an unguarded inlining pass was
found.

**Input-vs-output counting silently inverted.** On a flattened sample the count read zero in the
input and non-zero in the output, scoring the residue as "ours", for a shape that was the
encoder's all along and merely still sealed inside the interpreter. A per-stage run on the same
sample showed it present from the first stage onward.

**"Did the fix even run?" — three times in one project, at a corpus run each.** A pass scheduled
where its input did not yet exist; a matcher whose caller gated on the very blindness the fix
removed; a matcher and its visitor both extended while the call-site filter one level up still
rejected every site. Each measured as literally zero change — byte-identical output.

**A diff named what four reading-based hypotheses could not.** Adding nested-pattern support to
an unmasking pass broke four samples. The pass had rewritten an unpack line while references to
the same slots, inside a nested function *declared above it*, were left addressing a stack
nothing populated any more.

**A load-bearing decline read as a gap.** One element gate showed a large, unanimous-in-kind pile
of declines that had cleared every other gate, while the output census for that shape read zero
across every sample — the population was entirely intermediate. The fix was built anyway and had
to be reverted: it blew the corpus up by orders of magnitude and took samples from correct to
broken, because a later pass consumed the shape the gate was declining.

**A bucket that looked like one population split once an instance was printed.** A tally reading
"reference, not a callee" turned out to be entirely `new F(…)`, whose arity is perfectly
readable; most of the population closed on one line.

**Two items closed with no work at all once a census ran inside the pass** — the reversal was
already in production in a sibling pass, and the pass under investigation simply had no
candidates.

**A name-filtered breadcrumb inverted its answer.** One session gated a breadcrumb on a single
identifier, read zero hits, concluded the pass was never reached with that slot, and wrote an
unreconciled contradiction into the worklist. The pass was reached repeatedly with that exact
name, which recurred throughout the sample because a renaming stage reuses short names across
non-overlapping scopes — the decoded output alone held a live one shadowed by the dead one under
investigation.

**A fully breadcrumbed pass reported matches and not one rejected call site** — reading as a pass
doing its job — while every match had died in a caught exception. The failures became countable
only once the *warnings* were tallied instead of the returns.

**A bound landing on a known boundary produced two confident wrong answers in one sitting**, which
is why step 5 now treats it as a candidate. A sabotage ladder over ten encoder versions split them
into three dependency profiles, with one boundary bracketed by two adjacent corpus columns. The
first answer attributed it to the string-array scope wrapper, whose era turns over exactly there —
found by checking the string-array axes, the family the subsystem made salient, and no others.
Sweeping **all** twenty-one axes then showed a second axis turning at the identical point, so the
first answer had never been separated from anything. The second answer attributed it to *that* axis
instead, on the grounds that the option sets carrying it were exactly the sets whose cells differed
— a comparison whose control turned out to be **confounded with profile strength**: every set that
would have discriminated was too weak to show the effect at either version, so its silence was not
evidence. Both answers were reached without a sample in which one candidate had moved and the other
had not.

What broke the deadlock was **diffing encoder source across the two versions instead of re-reading
the registry**: a third component changed there and had no axis at all, because nobody had swept
it. Deriving it turned up the one version in the whole range at which it had moved while the two
rivals had not — and measuring there **eliminated it**, the profile reading identical to its
neighbour below. Version sweeping was then exhausted, the two survivors having identical ranges, so
the separation had to come from the option axis: two appended one-option siblings of the maximal
profile, built at the two versions. Removing one option reproduced the post-boundary reading and
removing the other changed nothing, which attributed **half** the differing cells and left the
other half explained by neither — the state the rule now insists be written as *confounded* rather
than as a finding.

## T1 · W4 — order the work from the stage order

**Measuring the prize predicted badly.** One fix measured a large win on the fixtures that
motivated it and a small *negative* on a full-preset corpus. Both numbers were correctly
irrelevant to whether it got done.

**Premature troubleshooting.** Flattening at 24 sits on top of variable masking at 20. Masking was
visibly not reversing its own patterns and the tempting move was to breadcrumb its matcher, while
its input still carried flattening residue that survives the flattening decode by design. The same
ranking error put the masking decoder ahead of the flattening one whose residue sat in its input.

**Residue misfiled under an encoder stage, three times, the reflex surviving each correction.** A
residual rest-masked population blamed on a masking transform's no-length case, when the
flattening *decoder* was giving every reconstructed function a rest param; undecodable string
wrappers blamed on a declaration-hoisting stage, when our own reversal of it was leaving each
restored declaration shadowed by the parameter slot it declined to remove; and a destructuring
spelling blamed on that same stage, which turned out to bail on non-identifier declarators
outright — one guard in its source, readable before any measurement.

**Two runs were burned probing for the ordering**, one relocating a decode pass to see whether
that unblocked it. It changed nothing, which was readable from the order enum without running
anything.

**A unit list justified only by stage order got re-litigated at the boundary stage order cannot
explain.** Two decode units sat in the same encoder stage, one the basis for the other; asked why
they were split, a reading of the encoder source found both declaring that stage while a
*different* stage's thirteen transformers formed a single unit, and concluded the boundary had
been drawn mid-reversal. The evidence was right and the conclusion wrong: the units split along a
decode dependency chain, which every artifact in the plan already behaved as though it knew — a
fourth "a later unit owns the rest" outcome, worklist entries reading "awaiting" that unit — and
which the derivation had never stated. The basis unit's inertness on the dependent samples, which
had looked like the strongest evidence against the split, is the signature of a foundation.

## V1 — work the era axis outward

**A ten-version sweep was attributed from the wrong end, and the biggest boundary turned out to be
partly explained by the smallest one nobody had read.** A sabotage ladder over every corpus version
split them into three dependency profiles against the spine, at three boundaries. The work started
at the boundary with **eleven** differing cells rather than the one with **one**, because eleven
looked like the stronger signal. Two of the three axes turning at that boundary had identical
ranges, so nothing there could separate them, and two successive attributions were made and
withdrawn before the confound was noticed.

The boundary with one differing cell was then attributed in a single reading of data already
collected, with no new samples at all: three axes turn there too, but only one belongs to a single
transform, and **only the option set enabling that transform flipped** — a shape change under the
shared subsystem would have flipped all eight sets that read it. The maximal profile carrying the
same option did *not* flip, being already saturated for other reasons, so the per-feature set was
the only one that could show it.

Reading that boundary first would also have corrected the eleven: **ten new differences plus one
carried down**, since every comparison beyond an unattributed boundary inherits its difference.
Counting eleven is what sent the first attribution to the wrong axis.

**And one of the eleven was not an era difference at all — it was a defect in the decoder doing the
measuring.** Dumping the decoded output per case showed a program that computed everything and
printed nothing: the anti-tamper strip removed the *statement* holding its target, and the
encoder's adjacent-statement merging had fused that target into one sequence expression alongside
the program's own output calls. Both versions produced the same fused sequence; they differed only
in whether the randomized injection landed inside it. So a seeded coin flip had been read as an era
boundary, and the profile groups themselves were partly an artifact of an unfixed bug — which is
why the rule now says to fix a known defect before attributing anything beyond it.

## W1 — a later stage invalidates an earlier matcher's assumptions

**A late renaming stage** (order 30, over flattening at 24). The flattening decoder identified the
obfuscator's own runtime helpers by literal name suffix; renaming reassigns every identifier,
internal helper names included, with zero functional effect. Once renamed the lookup returned
nothing and the **entire** control-flow decode failed closed — not one interpreter, all of them,
silently, with correct runtime output.

**A late minifier** (order 28, again over 24). It strips the `BlockStatement` from a
single-statement loop body (`while(x)switch(y)`) and rewrites `a["k"]` to `a.k` for
valid-identifier keys, breaking body-shape matchers that hardcoded the un-minified form.

**A one-element rejection wiped out a whole layer.** A literal-extraction array was matched
all-or-nothing, and a later minifier re-spelled exactly one element (`undefined` as `void 0`),
failing the entire array closed and leaving every indexed read — and the runtime prelude they
index — undecoded. A cause a few bytes wide; a consequence of most of the file.

**A later stage rewrote an earlier stage's reference sites.** Flattening at 24, literal extraction
at 22, so the flattener rewrote much of the extraction array's *already-placed* reads to index
through its own state array. Those are unresolvable until the flattening decode runs, so the
extraction decoder had to be scheduled twice rather than improved.

## W6 — repeated encoding

**The second-encode anchors.** A sample encoded twice where incomplete validation in the first
layer's decode processed second-layer content and threw; and a real decode procedure recorded as
six invocations across three different decoders with a hand edit in the middle.

**An evaluating reversal was believed exempt from layer order, then measured not to be.** The
claim that a decoder which *runs* the machinery can see through a layer was written down and
believed before anyone tried it. An inner prelude extracted verbatim from a doubly-encoded sample
throws a `ReferenceError` on the outer helper it references, because its own literals are
outer-encoded calls.

## W7 — what a validation set cannot show

**A shared visitor read as proven by a corpus that could not test it.** A control-flow pass used by
three decoders reversed every live block of one encoder's whole frozen corpus, on every version
column, with the residue census at zero — and its keep-or-fork call was about to be made on that.
A field report said otherwise, and hand-built cases confirmed three off-corpus behaviours worse
than declining: an ordinary `while (!done)` state-machine loop had its loop **deleted**, a case
without a terminator **duplicated** statements, and a discriminant without `++` **threw** and
aborted the decode. All three are unreachable from that encoder, which always emits the regular
form — so the corpus was not weak evidence, it was **no** evidence about the shapes that mattered.

**And the sharper form, where cases existed and still could not see it.** A different shared
visitor had six committed cases, all passing, all built from one encoder's dead-code shape. A
seventh case — three lines, a dead branch referencing a binding declared *outside* it — failed
immediately on an assertion the other six had been running all along. The six were clean because
their dead branches declared what they used, so the bindings left with the branch. A suite can be
green, on-topic, and structurally unable to express the defect.

## T9 — find out why before adapting

**A producer can be wrong while its output is right**, which the four cases could not express and
which cost a wrong ruling for most of a session: see S6.

**Auditing the consumers of one half-reversed shape turned up dozens of candidate sites**, of
which only two were ever live — and none needed changing once the producing pass stopped emitting
the shape.

**Case 3's anchor.** An un-masking routine requires an *exact* parameter count and can only read
one from a truncation statement, which one transform's entries never carry — anonymous,
zero-arity, never called, so no arity is inferable either. Three callers now supply that count and
drive the reversal directly: the pass's own entry point from the truncation statement, a
function-length pass from an unwrapped `fnLength(fn, length)` argument, and a dispatcher pass from
the structural fact that its template always builds entries with zero declared params.

**Case 4's one right answer, and why it is bounded.** An obfuscator emits its own helpers by
re-running itself over each helper template with a handful of forwarded options, so exactly those
options bound how a helper can be re-spelled. A matcher that folded arithmetic and flattened
sequences was complete against that set; the one matcher in the same file that did neither read a
present component as absent.

**An unresolvable slot documented as an inherent limit.** One session wrote up the limit and built
a fail-closed guard in the consumer. The resolving routine existed all along and was simply
unreachable.

## T3 · W2 — ask what a guard protects

**One guard cluster, the same wrong inference, years apart.** Guards existed to make substituting
a *value* safe — rejecting nested scopes, `++` updates, reassigned aliases — and were silently
also blocking a pure *rename*, which needs none of them. Later the same cluster struck from the
other direction: a slot rejected for carrying a `++` update was read as *unresolvable* and written
up as an inherent limit, when only value substitution was ever at stake. Promoting the slot to a
real local, which the un-masking routine does without consulting the invalid list, handles
`stk[3]++` as `_local++` perfectly well.

**Coupling that no document recorded.** A later pass rejected any function body capturing
variables declared outside itself, which an *undecoded* interpreter body always does — it calls
the obfuscator's Program-level helpers. That pass silently declined on exactly the programs where
an earlier pass had already failed.

## T2 · W5 — shape-keyed, and all-or-nothing

**A resolved name is still a name.** A pass receiving its target as `{ scopeName }` and reasoning
"this came from the interpreter's own shape, so it is not name matching" had resolved nothing — it
held a string, and every same-named identifier in reach answered to it. The diagnostic tell is
worth keeping: the "live keys" the bail reported were `indexOf`, `length`, `key`, `val` — members
of an ordinary array/string, not of the generated object the pass thought it had.

**Source positions are the same trap one level down.** A decoder's own earlier passes reparse
function bodies and synthesise statements, so `node.start`/`node.end` are routinely absent or
relative to a fragment by the time a later pass reads them. A containment test built on them
reported a function's own local as an outside dependency and hoisted it out of scope.

**Cached scope state was stale, and the symptom pointed the wrong way.** A pass resolved its two
control declarations through the scope's binding table, which is recorded at the last crawl. Every
pass scheduled ahead of it replaces nodes, so the binding pointed at a **detached** node that still
printed identically to the live one, and the identity comparison against it failed silently. The
tell was the inverted pass rate: the pass accepted every hand-built case and rejected **all** of
the real corpus blocks, because only the hand-built trees had never been rewritten. Resolving by a
sibling scan of the live tree fixed it and bought a dominance guarantee the binding lookup never
had.

**Half-resolution manufactured two entities from one.** Resolving only the readable share of a
literal array left one storage slot written as `slot[-1]` at some sites and `slot[-literals[1]]`
at others. The masking decoder read those as two slots and split a single object in two — a read
from the new binding, the matching write still going to the old one. Output was silently wrong on
a minority of samples, on a change where every size metric had improved.

**Emptying a match to mark it consumed, then re-emitting it.** An extraction walked every
*reference* to a string array and collected the enclosing function once per reference, hollowing
that function's body after the first collection so it would not be processed twice. Where the
accessor named the array more than once — the rc4 form writes its decoded value back into the
array, the plain form only reads — the collected text ended with a hollow redefinition of the same
function. Under the era whose accessor is a hoisted **function declaration** the hollow one wins,
the accessor returns nothing, and the rotator's checksum search runs forever. The sufficiency gate
in front of all this counted collected fragments against a minimum of three: it saw five and passed,
because it was written to catch *missing* pieces and duplicates read as abundance.

**The same incident is the anti-tamper misattribution.** The symptom — an evaluating decode that
never returns — was recorded, with a written mechanism, as the encoder's self-defending guard
detecting re-spelled code. That explanation was never tested and was wrong in a way four cheap
checks each closed independently: the sample **ran to completion untouched**; the guard's shape was
**absent from the file** (present, as a control, in a preset that enables it); the plugin's own
regenerated fragments **terminated once only the duplicates were removed**, holding the
re-spelling constant; and a sweep bounded the failure to **exactly** the two versions spanning the
one extraction branch that hollows a matched node — a range that coincides with a boundary the code
already had, which is what made it an explanation rather than a second observation. The wrong story
survived because anti-tamper is the thing famous for hanging, and the true cause had no reputation.

**An evaluating reversal that missed one component.** A string array's holder and accessor were
extracted while the rotator was read as absent, because the matcher for it keyed on a spelling the
encoder's own statement-merging had fused away. Every call site then returned a real string from
an unrotated array — the wrong one. Output parsed, ran, and drove every residue axis to zero.
Measured on the corrective probe: with the rotator missing, most decoded strings in
computed-member-key position are not valid identifiers; with it present, none.

## T4 · W3 — price the refactor against all of them

**A workaround repeated across four consumers was read as evidence against fixing the producer**,
which is this rule inverted; the count of consumers *not* paying it was the finding. See S6.

**Three open issues, one address.** A rename-reliance failure, an inability to handle a
member-chain state accessor, and a residual harness never cleaned up all followed from storing
identity as a **name string** threaded through a context object rather than as a binding or a
NodePath. A string cannot represent `scope.a.b`, cannot survive renaming, and cannot be revisited
later to clean up what it named. Each looked independently patchable, which is exactly why the
cluster stayed open — every individual patch was cheap, so the shared cause was never priced.

## S6 — a pass's contract is (output, derived state)

**The incident that produced the rule, and the four labels it also sharpened.** A pass that strips
anti-tamper helpers declined on every sample combining debug protection with control-flow
flattening, emitting code that threw. It had been certified through a staged probe chain that wrote
each stage's output and re-parsed it; rebuilt on one AST per cell, runtime equivalence fell from
the whole corpus to 489 of 597. The reparse had been silently repairing the state the real pipeline
carries.

**It was then fixed at the wrong end, and the wrongness was recorded as a curiosity.** A
`traverse.cache.clear()` at the failing pass's entry restored the corpus. Clearing or crawling
between that pass's two phases did not, and running it twice declined identically — so the position
was written down as "measured, do not tidy", and an open item was filed asking why. That item
protected the patch for a session. **The answer was that there was nothing to explain**: the
repair was at a consumer, and a consumer-side repair has a placement question only because it is
compensating for something upstream.

**The producer had declared the defect in a comment the whole time.** The pass that detached the
references carried `The code must be reloaded to update the references` in its own header — read
as a contract its callers had accepted rather than as a repair it had declined to do. Counting the
callers settled it in one grep: of four consuming plugins, three answered it with a full re-parse
each, and the fourth did not answer it at all and had been carrying the exposure unrepaired.

**The argument that nearly kept it there.** "Three plugins already reload, so fixing the producer
makes them pay twice." That reads N copies of a workaround as evidence the workaround belongs at
the consumers — and it assumed the reloads were fixed constants, when fixing the producer makes
them removable. It was a *user* objection, twice, that overturned it.

**What the fix cost and what it retired.** One `scope.crawl()` on the producer's `Program.exit`,
gated on having detached anything. The consumer's cache clear was then removed with output
byte-identical across all 597 cells and runtime unchanged — where before the producer fix, removing
it had cost 108 of them. Retired with it: a process-global cache wipe that constrained any future
re-ordering, the unexplained placement, and an open design question about whether the pipeline
should re-parse at stage boundaries at all, which dissolved once the only pass that creates the
condition began repairing it.

**And the ordering lesson (T7).** The detector that made all of this provable — a reachability walk
asserting no binding holds a reference to a node that has left the tree — was written **26 minutes
after** the fix it validated. Built first, it would have demonstrated the defect rather than
ratified a repair at the wrong level. Placed in the shared test helper rather than in a probe, it
retroactively audited every existing case for free, which is how the seventh case in W7 above was
found to fail in one line.

**The same misplacement recurred one level down, which is what added the granularity half of the
rule.** A later session found a decode that threw `ReferenceError`: a control-flow storage
declaration had been deleted while one live reference remained. The consumer's completeness gate
was *correct* — it refuses to delete unless every reference resolved — but it was reading a
reference list inflated to 112 entries for 102 distinct live nodes, so the gate passed while one
reference went unhandled. Bisecting located the inflation immediately after a normalization pass,
and the repair was written there. It worked: symptom gone, suite green.

**That pass rewrites nothing.** Its own header says "This file is scheduling and nothing else" —
seven `traverse` calls and no rewrite of its own. The repair was compensation at a composition, and
the only reason it looked like a producer is that the probe measuring the pipeline had **per-pass
resolution**, so the finest unit it could report was read as a leaf. Measuring the seven composed
visitors one at a time found four that inflate, three of them shared with other plugins and none
with any test at all.

**Then it was mislocated a second time, in the other direction.** Challenged on the placement, the
fix was moved to the consumer — on a plausible argument about shared visitors and many possible
dirtiers — without measuring first. The measurement contradicted it: the consumer does not dirty
its own state and its existing crawl demonstrably *repairs* some of the inflation as it goes. Two
wrong sites, one plausible argument each, and both were settled in minutes by a probe that reported
per-visitor rather than per-pass.

**What each candidate site actually cost, since "it works" was true at all three:** at the
composition, one crawl that masks four dirty visitors for one pipeline and leaves them dirty for
every other consumer; at the consumer, a repair that could not have fixed the producers at all; at
the four operations, byte-identical output, the shared visitors correct for every consumer, and a
pipeline whose scheduler needs no crawl of its own — the composition-level patch was deleted as
redundant the moment the producers repaired themselves.

**The tell that was available before any of it.** Open the file, look for the operation that causes
the defect. Seven `traverse` calls and no rewrite is visible in one screen, and it settles the level
without a probe at all.

## S1 — size ratio

**The calibration pair.** A `high`-preset decode came out hundreds of times larger than its source
and was, on inspection, mostly raw scaffolding; a genuinely complete decode of a dispatcher-wrapped
function collapsed to roughly the original's size. The gap between those two orders of magnitude is
the whole signal — take the pair on the run in front of you, not against these words.

## S2 — count the characteristic constructs

**A signature regex scored a total non-decode as clean.** A `high`-preset run showed zero residual
interpreter-loop signatures and was celebrated, while a direct `switch` count was unchanged before
and after — not one of the control-flow interpreters had been touched.

**A count that could not move was twice read as "measured not to be the fix".** It sat unchanged
across several changes, including one that removed a quarter of the residue a *different* count
was tracking, because its subject is only removed by the last step of a multi-step fix.

## S3 — zero-reference bindings

**Dead on arrival.** One sample arrived with an XOR string helper that had zero call sites, plus
the string blob only that dead helper read. Both were the encoder's own dead code, not something
a decode missed.

**A deletion gate keyed on a spelling an earlier pass had stopped emitting** kept a runtime helper
on a large share of samples — a third of all decoded bytes — through three censuses that reported
the pass clean, because every one asked about the pass's *matcher* rather than its deletion gate.

**Referenced, and still pure residue.** A helper was referenced only from the entry vectors of
harnesses a later fix removed wholesale, at which point the orphan went to zero without anyone
touching the sweep. Seen twice.

## S5 — output is randomized by design

**An isolation grid that could not bound what it was asked to bound.** Several matrix cells were
partial while the same transform combos read clean in isolation; "no transform is individually
implicated" was recorded from that grid. The real cause was one transform's own bug — random
per-run template selection — reachable from a two-transform combo alone, at a rate the grid's
short runs were never going to bound.

## T5 — isolate a combo gap

**A cause needed a second transform present to reproduce at all**, so a matrix that varies one
transform at a time could not have reached it.

## Studying a new encoder/decoder pair

**This project's closed bugs are almost entirely combo bugs**, none of which a single-transform
fixture could have caught: a renaming stage invalidating a name-keyed matcher, a
declaration-hoisting stage splitting a harness from its entry point, a statement-merging stage
dissolving the partition a downstream matcher expected.

**Tiers are not always subsets.** `low` in one obfuscator skips control-flow flattening entirely,
so one tier's coverage does not imply a smaller tier's.
