# Encoder/Decoder Method — cross-project notes

Working method for studying an obfuscator and for building/debugging its decoder — one
discipline, not two, for the reason T8's "treat a decode attempt as the verification step"
states. Applies to any encoder/decoder submodule pair here, not to one obfuscator's transforms.
Kept separate per `SKILL.md`'s Project Independence rule; a skill *package* still documents
exactly one submodule.

**Read on its own.** Every rule carries the incident that produced it: none of this is general
software-engineering advice, each item cost this repo a real bug or a wrong plan. Identifier
names in the incidents are historical record, not a live API reference. Per `SKILL.md`'s Revise
by Evolution, a new incident sharpens an existing rule rather than adding one.

**Ordered by how often a session needs the rule**, broadest first: tier 1 every session, tier 2
once per work item, tier 3 when judging a decode, tier 4 only in its named situation. Rank a new
rule by how many sessions would want it, not by how interesting its incident was. The order
exists because it failed once — the two rules that would have caught a wrong claim were buried at
the end of a file the session had read start-to-finish that morning. **A rule that cannot be
retrieved when its shape appears is worth nothing**, which is what the symptom table is for.

**Labels are stable identifiers, not positions.** Other docs cite `T1`, `W1`, `S3` by name, so a
label keeps its content permanently; only grouping and order change. A merged rule carries both
labels. Cite by label, never by tier or position.

## Background: why decoders fail silently

Every decoder here is built to **fail closed**: a pass that cannot recognise its expected shape
leaves the input untouched and moves on. That is right — a half-rewritten program is far worse
than an obfuscated one — but it shapes everything below:

> A completely broken decoder and a perfectly working one produce the same *runtime behaviour*.
> They differ only in the *shape* of the output.

A declining pass emits no error, no log line, and correct output. Three things follow, cited
rather than restated hereafter: runtime correctness cannot tell you whether anything decoded
(S4); coupling between passes is invisible, because the bail-out conditions *are* the dependency
graph and nothing else records it (W2, in T3); and the first failure hides every cascading one,
so the symptom is routinely several layers from its cause (T6).

### S4. Runtime-correctness is not a decode-quality signal

The direct corollary, kept among the rules rather than the signals because it is the absence of
one. Passthrough always runs correctly, so a green check at diagnosis time cannot tell "decoded"
from "safely didn't decode". Judge by S1/S2/S3. Its value as a **regression guard** after a fix
is real (T7), but that is a property of a fixed decoder, not a diagnostic for a broken one.

## Find the rule from the symptom

| what you are looking at | go to |
|---|---|
| correct-running output, and you don't know whether anything decoded | S4, then S1 · S2 · S3 |
| a residual obfuscated shape in correct-running output | T6 — bail-out breadcrumb |
| a `TypeError`/`ReferenceError` thrown by the decoded program | T6 — output diff |
| a pass that fires on nothing, or suddenly stopped firing | T1 (a later encoder stage rewrote its input), T6 (the caller's gate) |
| an earlier pass left a shape your matcher can't handle | T9 |
| a guard rejecting something that looks like it should pass | T3 |
| deciding what to work on next | T1 — and nothing else decides it |
| several open bugs in one subsystem | T4 |
| a gap that appears under a preset but under no single-transform test | T5 |
| a doc, comment, or worklist status you are about to rely on | T8 |
| a brand-new encoder/decoder submodule pair | "Studying a new encoder/decoder pair" |

## Tier 1 — every session

### T8. Validate a premise before implementing against it — in-tree first, then a probe

**A comment, a doc, or a worklist's "Covered" status is not evidence that a decoder matches
current source.** All three describe intent when written, and a decoder's target — an
obfuscator's emitted shape — can change under it silently. Treat them as hypotheses to check.
**Verify against source, always**; never document a mechanism from memory or inference.

**Distrust most a guard comment asserting something is impossible.** "By design", "marks
invalid", "cannot be resolved" describe *the operation the guard was written for*, never the full
set it now blocks — that is T3, and the two are usually needed together. Repeating such a phrase
into a skill doc launders a hypothesis into a documented limit: one session copied "an
`UpdateExpression` slot is marked invalid by design" into a doc and defended it, when the marking
was scoped to *value substitution* and the un-masking routine ignored it entirely.

**A status is only as strong as the criterion it was recorded under.** Entries marked done before
the decode-quality signals existed were judged on runtime-correctness alone, which S4 says is no
evidence. Re-read such a status when the transform is being revisited anyway.

**Treat a decode attempt as the verification step for an encoder claim**, not just a downstream
consumer of it. A mechanism documented from reading alone is a hypothesis; building its
reversal — matching the shape against real, adversarially-stacked output (renamed, minified,
combined) and executing the result — is what proves it complete. Reading gets some things right
for free (exhaustiveness against a closed case set, a stage-order dependency) but cannot surface
what shows up only under attack: a "linear execution order" that reading predicted needed real
branch points once reversed; an inline comment that was a stale fossil from a previous encoder
version; a helper identified by name that renaming proved structurally unreliable. Don't mark an
encoder-side transform doc settled before something has attempted to invert it against real
output. `SKILL.md`'s Encoder Pin Gate applies this to a pinned commit — a pin is an encoder
claim too.

**Then validate the plan itself, in-tree before probing:**

- **Look for a matcher that already does it correctly.** Decoders accrete duplicate
  identification paths for one entity, and the older is often already right — in T1's renaming
  case, one function already resolved the helper structurally while another re-derived it by
  name suffix, turning "would a structural rewrite work?" into "delete the duplicate and extend
  the one already in production." Free, and stronger than a probe, so do it first. The same
  search answers T9's question about which pass already owns a reversal.
- **Then a throwaway probe.** Reading and probing find **different classes** of thing, so budget
  for both: on one plan, reading found a missed matcher site and a hidden inter-pass dependency
  while a fifteen-minute probe found a semantic gap neither had — the dead-helper case in S3.
  **A probe is throwaway by default — keep the recipe, not the script.** One kept per-probe
  inventory drifted until entries described scripts that no longer existed while scripts on disk
  were described nowhere; a page saying how to rebuild one stays true, and a rebuilt probe is
  honest against the current matcher where a preserved one silently is not.
- **If a probe reports a miss, suspect the sample and the oracle before the code.** Verify the
  denominator first — obfuscation is shape-gated, and on one run several samples didn't exercise
  the feature at all (S5). Then verify the oracle measures *liveness*, not presence: a helper can
  be present yet transitively dead, and resolving it to nothing is *correct* (compute liveness to
  a fixpoint). Both apparent probe failures here were oracle artifacts, not code defects.

### T6. Instrument the failure; don't root-cause from reading alone

The symptom is usually several layers from its cause (Background), and this is the
highest-yield rule in the file: **every cause found in this project so far was found by
breadcrumbing a real failure, and none by an isolation matrix.** Budget accordingly.

Two successive hypotheses about a minifier-interaction bug, both from careful reading, were
wrong; breadcrumbs against one real sample got the cause on the first attempt. Independently, a
residual interpreter shape was attributed to an unbuilt in-place decoder by matching the residue
to the nearest known-unbuilt feature — producing a wrong diagnosis, a wrong priority order and a
nearly-started refactor that would have fixed nothing, when the real cause was a bare `return;`
three lines away. **A residual shape proves *something* failed, never *what*** — instrument the
actual bail-out rather than guessing from the wreckage.

**The tell for which instrument to reach for is what the failure looks like, not where you
suspect it is.** Residual shape in correct-running output → the bail breadcrumb. A runtime
`TypeError`/`ReferenceError` from the decoded program → an output diff, because the pass you
want did not decline, it committed. Reaching for the first when the symptom is the second is how
reading gets a turn it hasn't earned.

**Four instruments, four questions:**

- **"Which guard rejected this shape?"** — the bail-out breadcrumb. Tag every `return null` with
  its own source line, so it survives a rewrite instead of going stale against a hand-maintained
  list of named bail points.
- **"Which *stage* is responsible for the output looking like this?"** — the cheaper one: replay
  the decoder's own pipeline stage by stage against one real sample, printing generated size
  after each plus whatever structural count matters (S2). A stage that should shrink the file and
  reports `+0` never fired — invisible in finished output, since a fail-closed pass leaves no
  trace. That table localized a whole undecoded layer to one stage on its first run and is worth
  building before any matcher is read; it is also where a stage that *grows* the output shows up,
  which is how an unguarded inlining pass was found.

  **This is also the only reliable way to answer "is this residue ours or the encoder's?"** The
  tempting cheaper version — counting the shape in the obfuscated input and in the decoded output
  — is valid only when the construct is *visible in both*, and it silently is not whenever an
  outer undecoded layer still hides it. On a flattened sample that count read zero in the input
  and non-zero in the output, scoring as "ours", for a shape that was the encoder's all along and
  merely still sealed inside the interpreter; a per-stage run on the same sample showed it
  present from the first stage onward. Prefer the form with no precondition. T1's third corollary
  is what depends on this.
- **"Did the fix even run?"** — the same breadcrumb, asked of the **caller**. A fix can be
  entirely correct and never execute, and it measures as *literally zero change* —
  byte-identical output, indistinguishable from a wrong fix until the caller is checked. Three
  times in one project, at a corpus run each: a pass scheduled where its input did not yet exist;
  a matcher whose caller gated on the very blindness the fix removed; a matcher and its visitor
  both extended while the call-site filter one level up still rejected every site. The gate to
  instrument is the one *above* the code you are about to write.
- **"The pass ran, and the output is wrong."** — a before/after **diff of the decoded output**,
  taken at the site the runtime error names. A guard counter cannot see this at all: it is not a
  decline, so the breadcrumb reports the rewrite firing correctly and the tally actively
  reassures. Decode one failing sample with and without the change and read the three lines that
  differ. Incident: adding nested-pattern support to an unmasking pass broke four samples, and
  four successive reading-based hypotheses were all wrong; one diff named the real cause
  immediately — the pass had rewritten an unpack line while references to the same slots, inside
  a nested function *declared above it*, were left addressing a stack nothing populated any more.

**Five ways the instrument itself lies.** Each cost a wrong conclusion here:

- **A bail tally measures the pipeline's interior, not its output**, so a decline is not a defect
  until an output census says so. One element gate showed a large, unanimous-in-kind pile of
  declines that had cleared every other gate — textbook evidence of a gap — while the output
  census for that shape read **zero across every sample**: the population was entirely
  intermediate. The fix was built anyway and had to be reverted, blowing the corpus up by orders
  of magnitude and taking samples from correct to broken, because a later pass consumed the shape
  the gate was declining. **A gate that declines can be load-bearing.** Output census first, bail
  tally second.
- **A tally names the gate, never the thing.** It answers *which* guard declined, so the next
  instrument reads one offending candidate's own bindings — a bucket that looks like one
  population routinely splits once an instance is printed. One reading as "reference, not a
  callee" turned out to be entirely `new F(…)`, whose arity is perfectly readable, and most of the
  population closed on one line. Run the dump before writing a cause down, not after someone
  questions it.
- **A pass with no candidates at all looks identical to one that resolved everything** — no log
  line, no residue, no failing test, and input-vs-output reads 0/0 (see the per-stage instrument
  above for why). Only a census *inside* the pass, classified against the encoder's full variant
  matrix, separates "nothing to do" from "declined everything". Two items closed with no work at
  all once that census was run: the reversal was already in production in a sibling pass. **So
  establish an item's population is non-zero before working it.**
- **A breadcrumb filtered by name inverts the answer** — T2's name trap applies to instruments
  exactly as to matchers. One session gated a breadcrumb on one identifier, read zero hits,
  concluded the pass was never reached with that slot, and wrote an unreconciled contradiction
  into the worklist. The pass was reached repeatedly with that exact name, which recurred
  throughout the sample because a renaming stage reuses short names across non-overlapping
  scopes — the decoded output alone held a live one shadowed by the dead one under investigation.
  Dump *every* call with the resolved binding's own location and aggregate afterwards.
- **A guard counter cannot see a failure that happens after a successful match.** A pass can throw
  inside something it evaluates, and the fail-closed catch turns that into the same silent
  passthrough. One pass's bail-outs were fully breadcrumbed and reported matches with not one
  rejected call site — reading as a pass doing its job — while every match had died in a caught
  exception; the failures became countable only once the *warnings* were tallied instead of the
  returns. Instrument the catch blocks alongside the guards, and prefer whatever the pass already
  reports over new counters.

### T7. One fix is never the whole fix

A defect's shape almost never occurs once. Whatever the fix was — a spelling a matcher didn't
accept, a gate keyed on a declaration form, a name-based identification — grep for the *shape*
across the pipeline before closing the item, because the audit is a grep rather than a review.
S4's regression value is what makes this cheap to verify afterwards: the correctness check that
proves nothing at diagnosis time is exactly what proves a broadened fix broke nothing.

## Tier 2 — deciding what to fix, and in what order

These are decisions readable from the encoder's stage order and the decoder's own source.
**None of them needs a run**, and reaching for tier 1's instruments to settle one is the mistake
T1 and T9 record: a probe cannot beat a structural fact, only cost time and, if misread,
manufacture false confidence. Measurement still earns its place everywhere the stage order is
silent — whether a matcher is correct, which guard fired, whether a fix regressed anything.

### T1 · W1 · W4. Order the work from the stage order — not by byte share, and not by probing

Map the encoder's stage order against the decoder's pipeline order and fix in **reverse encoder
order**, asking of each stage what its matcher needs its input to already look like and which
stage produces that.

**W1 — anything later in the encoder's stage order can invalidate an earlier matcher's
assumptions.** The failure is silent *and total* rather than partial, because a late stage's
rewrites are semantics-preserving by construction: nothing about behaviour changes, only the
shape the matcher was written against, so the pass declines on every application at once. Two
confirmed forms:

- **A late renaming stage** (order 30, over flattening at 24). The flattening decoder identified
  the obfuscator's own runtime helpers by literal name suffix; renaming reassigns *every*
  identifier, internal helper names included, with zero functional effect. Once renamed the lookup
  returned nothing and the **entire** control-flow decode failed closed — not one interpreter, all
  of them, silently, with correct runtime output.
- **A late minifier** (order 28, again over 24). It strips the `BlockStatement` from a
  single-statement loop body (`while(x)switch(y)`) and rewrites `a["k"]` to `a.k` for
  valid-identifier keys, breaking body-shape matchers that hardcoded the un-minified form.

The sub-case worth naming: **names are unreliable by design, not by convention.** Any
identification keyed on a variable or function name is a latent total failure waiting for the
renaming stage, in any obfuscator that has one — which is T2. Corollary: a matcher validated only
against an isolated single-transform fixture is not proven robust to real combined output, since
that fixture omits exactly the later stages that would break it.

**W4 — a defect's size in the output says nothing about where it originates.** Because decoder
stages feed each other, a defect contributing almost nothing to the output can be holding a large
one shut. Byte attribution measures a **symptom's size** and points nowhere near the cause, even
though a plan sorted by residue share looks well-founded. Two instances, both from one fix:

- **A one-element rejection wiped out a whole layer.** A literal-extraction array was matched
  all-or-nothing, and a later minifier re-spelled exactly one element (`undefined` as `void 0`),
  failing the entire array closed and leaving every indexed read — and the runtime prelude they
  index — undecoded. A cause a few bytes wide; a consequence of most of the file.
- **A later stage rewrote an earlier stage's reference sites.** Flattening at 24, literal
  extraction at 22, so the flattener rewrote much of the extraction array's *already-placed* reads
  to index through its own state array. Those are unresolvable until the flattening decode runs,
  so the extraction decoder had to be **scheduled twice, not improved**: a defect can sit in the
  decoder's *pipeline ordering* rather than in any matcher (T9).

Neither was reachable by asking which residue was biggest.

**It is a dependency order, not a priority order.** The deliverable is readable output, so every
open shape is release-blocking and the working set is *all* of them; sequencing only keeps a
stage from being worked while a later one still owns its input. Nothing here selects, defers or
promotes — so "measure the prize first" is not a step, it is W4 in the costume of diligence, and
it predicts badly besides (one fix measured a large win on the fixtures that motivated it and a
small *negative* on a full-preset corpus; both numbers were correctly irrelevant to whether it
got done). Three corollaries, each a mistake made here:

- **Troubleshooting a decoder whose input still carries a later encoder stage's residue is
  premature.** Remove the residue first, then re-measure — the symptom may not survive. Anchor:
  flattening at 24 sits on top of variable masking at 20; masking was visibly not reversing its
  own patterns and the tempting move was to breadcrumb its matcher, while its input still carried
  flattening residue that survives the flattening decode by design.
- **Our own pipeline position never sets priority.** "Our pass X runs before our pass Y" is not
  the stage order and does not imply X's input is clean. The same ranking error put a masking
  decoder ahead of a flattening one whose residue sat in its input.
- **Confirm the residue is the encoder's before filing it under an encoder stage — and name the
  *specific* stage only from its source.** A decoder pass emits shapes too, and one that looks
  like un-reversed obfuscation gets an encoder stage attached by reflex, ordering the work against
  a dependency that does not exist. Three times in one project, the reflex surviving each
  correction: a residual rest-masked population blamed on a masking transform's no-length case
  when the flattening *decoder* was giving every reconstructed function a rest param; then
  undecodable string wrappers blamed on a declaration-hoisting stage when our own reversal of it
  was leaving each restored declaration shadowed by the parameter slot it declined to remove; then
  a destructuring spelling blamed on that same stage, which turned out to bail on non-identifier
  declarators outright — one guard in its source, readable before any measurement.
  **Use T6's per-stage count to settle it**, never input-vs-output; T6 has why that shortcut
  silently inverts.

**Do not probe for the ordering.** Two runs were burned confirming what the order enum already
stated, one relocating a decode pass to see whether that unblocked it. It changed nothing, for
the reason T9 gives, which was readable without running anything.

### T9. When an earlier pass leaves a shape you can't match, find out why before adapting

The reflex is to teach the matcher in front of you to tolerate the shape. That is the **last** of
four options and usually the worst, because it is the same fix re-paid at every consumer:
auditing the consumers of one half-reversed shape turned up dozens of candidate sites, of which
only two were ever live — and none needed changing once the producing pass stopped emitting the
shape. Diagnose which case you are in first; nothing about the residue tells them apart.

**The empirical result, across every readability defect closed in one project: the cause was
always a shape one of our own passes emitted — never an encoder variation, never a matcher merely
too narrow — and the fix was always at the producer or in the schedule, cases 1 and 2.** Case 4
has yet to be right once. So when the reflex says "widen it", the prior is that something upstream
is wrong or mistimed, and **a pass's schedule is part of its correctness**: audit *when* a
reference-gated sweep runs, not only what it accepts. Several defects every census reported clean
were exactly this — the census asked about the matcher, and the matcher was fine.

1. **The producing pass emits a genuinely wrong shape** → **fix the producer.** A half-finished
   reversal is a *source* of the shape, so every downstream matcher tripping over it is a
   symptom, and the cheapest complete fix is upstream of all of them. This inverts what the
   cluster rule (T4) would otherwise recommend.
2. **The input does not exist yet, but will** → **reschedule the pass.** The test: does the
   missing input actually come into existence later? If yes, reschedule — that is why W4's second
   instance was fixed by scheduling a pass twice rather than improving its matcher. If the residue
   survives that decode by design, moving the pass changes nothing, which is what one burned run
   measured.
3. **The producing pass is correct but *uninformed* — it declined for want of a fact only a later
   pass possesses** → **route the fact to the pass that owns the reversal**, and drive it
   directly. Nothing upstream is wrong for case 1 to fix and nothing later comes into existence
   for case 2 to wait for; the information exists, just not where the pass can see it. Anchor: an
   un-masking routine requires an *exact* parameter count and can only read one from a truncation
   statement, which one transform's entries never carry — anonymous, zero-arity, never called, so
   no arity is inferable either. Three callers now supply that count and drive the reversal
   directly: the pass's own entry point from the truncation statement, a function-length pass from
   an unwrapped `fnLength(fn, length)` argument, and a dispatcher pass from the structural fact
   that its template always builds entries with zero declared params.
4. **None of the above** → tolerate the shape in the consumer, knowing you will pay it again.

**Distinguishing 1 from 3 is the step that gets skipped**, and the tell is whether the upstream
pass is *wrong* or merely *stopped*. A guard comment asserting the shape is unresolvable is not
evidence of case 1 — read what the guard actually protects (T3) first. One session documented an
unresolvable slot as an inherent limit and built a fail-closed guard in the consumer; the
resolving routine existed all along and was simply unreachable.

**Cost of case 3, so it isn't applied blindly:** injection creates a direct call dependency
between two passes that a scheduled pipeline does not have, and it mutates before the calling
matcher has confirmed its own match — so decide explicitly what happens to that mutation when the
match then fails. Leaving it in place can be the right answer, and was.

### T3 · W2. Ask what a guard protects, and whether that is what you are doing

Two questions of every early `return null` in the pipeline: **"what upstream state makes this
fire?"** and **"what is this guard protecting, and is that what I am doing?"**

The second gets skipped, and it is a correctness rule rather than a planning one. **A fail-closed
rule outlives the operation it was written for.** One cluster of guards existed to make
substituting a *value* safe — rejecting nested scopes, `++` updates, reassigned aliases — and was
silently also blocking a pure *rename*, which needs none of them. The same cluster struck later
from the other direction: a slot rejected for carrying a `++` update was read as *unresolvable*
and written up as an inherent limit, when only value substitution was ever at stake — promoting
the slot to a real local, which the un-masking routine does without consulting the invalid list,
handles `stk[3]++` as `_local++` perfectly well. Same guard, same wrong inference, years apart.

**This is source reading, not measurement**, and it is the only way coupling between passes ever
gets written down. Documentation describes what a pass does when it *succeeds*, so coupling never
gets recorded — and it cannot be observed either, since a declining pass is indistinguishable
from a working one (Background). Anchor: a later pass rejected any function body capturing
variables declared outside itself, which an *undecoded* interpreter body always does — it calls
the obfuscator's Program-level helpers. That pass silently declined on exactly the programs where
an earlier pass had already failed, and no document recorded the gate.

The planning payoff: the reading tells you which passes are **unmeasurable** until an earlier gap
is fixed, and therefore which experiments not to run yet.

### T2 · W5. Hold matchers to two contracts — shape-keyed, and all-or-nothing

- **Key on AST shape, or on a binding captured the moment a pass first resolves it — never on
  name text** (T1's renaming case is why). The audit form is a grep rather than a review:
  name-keyed identification is almost never a single site (T7).

  **The trap that survives knowing the rule: a name a matcher resolved is still a name.** A pass
  receiving its target as `{ scopeName }` and reasoning "this came from the interpreter's own
  shape, so it is not name matching" has resolved *nothing* — it holds a string, and every
  same-named identifier in reach answers to it. Two populations do. **Declaration sites are not
  references:** a `var x` declarator id, a `function x(…)` name, and a nested function's parameter
  `x` are bindings, not uses, so a matcher counting "references" without
  `isReferencedIdentifier()` reads all three as the target being used — which, fail-closed, kills
  every application in that scope. **And a real reference can belong to a shadowing binding of the
  same name.** Compare the binding object, not the text. The diagnostic tell is worth keeping: the
  "live keys" the bail reported were `indexOf`, `length`, `key`, `val` — members of an ordinary
  array/string, not of the generated object the pass thought it had.

  **Source positions are the same trap one level down:** a decoder's own earlier passes reparse
  function bodies and synthesise statements, so by the time a later pass reads
  `node.start`/`node.end` they are routinely absent or relative to a fragment. A containment test
  built on them reported a function's own local as an outside dependency and hoisted it out of
  scope. Ask the path ancestry, which is always current whatever rebuilt the tree.
- **Resolve a matched structure completely or leave it entirely alone**, and schedule a second
  visit for when the missing input exists. "Leave it alone" is cheap and always safe; the half-way
  state is neither.

**W5 — half-resolution manufactures two entities from one.** Downstream matchers routinely key on
how a construct is *spelled* rather than on what it evaluates to, so half-resolving makes one
entity appear as two — one site carrying the resolved form, another the unresolved one — and a
later pass treats them as unrelated. **This is W1 with the agency reversed:** there a later
*encoder* stage changes the spelling a matcher was written against, here a decoder pass changes
it under its own later pass. Anchor, from the same fix as W4: resolving only the readable share of
a literal array left one storage slot written as `slot[-1]` at some sites and `slot[-literals[1]]`
at others. The masking decoder read those as two slots and split a single object in two — a read
from the new binding, the matching write still going to the old one. Output was silently wrong on
a minority of samples, on a change where **every size metric had improved**: partial decoding
looks like progress on exactly the signals tier 3 recommends, so S1/S2 cannot catch it and only a
runtime comparison did.

Once a structure cannot be partially resolved, the only question left is *when* enough information
exists to resolve it — T1 for the ordering, T9 for the remedy.

### T4 · W3. When bugs cluster, price the refactor against *all* of them

Ask what a cluster has in common in how the code **represents** something, not in what the bugs
do. Three separate open issues — a rename-reliance failure, an inability to handle a member-chain
state accessor, and a residual harness never cleaned up — all followed from one decision: identity
was stored as a **name string** threaded through a context object rather than as a binding or a
NodePath. A string cannot represent `scope.a.b`, cannot survive renaming, and cannot be revisited
later to clean up what it named.

They were never three bugs; they were three symptoms with one address. Each looked independently
patchable, which is exactly why the cluster stayed open — every individual patch was cheap, so the
shared cause was never priced. The honest comparison is refactor-versus-all-the-patches;
refactor-versus-one keeps a cluster open indefinitely.

Exception: when the cluster's members are all *consumers* of one half-reversed shape, T9's case 1
beats this rule — fix the producer and the cluster evaporates without any of the patches.

## Tier 3 — judging whether a decode worked

Cheap measurements answering "did this actually decode, or did it just not break?" Scoped to
diagnosis: what you use *before* a gap is fixed, when there is no trustworthy expected output to
diff against. Read S4 first — it rules out the signal everyone reaches for.

### S1. Size ratio — two of them, and the second works in production

- **decoded ÷ pre-obfuscation source.** The higher the multiple, the more went unreversed. Some
  growth is legitimate — transforms irreversible by design (identifier renaming, object
  extraction, injected dead code) leave residue no decoder can remove — but a multi-hundred-x
  ratio is not cosmetic residue; it means whole mechanisms were never reversed. Calibration: a
  `high`-preset decode came out hundreds of times larger than its source and was, on inspection,
  mostly raw scaffolding; a genuinely complete decode of a dispatcher-wrapped function collapsed
  to roughly the original's size. The gap between those two orders of magnitude is the whole
  signal — take the pair on the run in front of you, not against these words.
- **decoded ÷ obfuscated input.** If decoding barely shrinks the file, little was reversed. Needs
  no pre-obfuscation source, which makes it the one available on a real-world sample where the
  original does not exist — the production case.

Keeping the pre-obfuscation source beside every fixture (as `<name>.src.js`) is what keeps the
first ratio computable later. A ratio is only comparable within one frozen corpus.

### S2. Count the obfuscation-characteristic constructs, before vs. after

A decode should drive them toward zero. This is the honest oracle, and specifically **not** a
regex for the residue a partial decode leaves: a signature regex looks for the wreckage of a
decode that ran and didn't finish, so it reports "clean" in two opposite situations — a decode
that finished, and one that never started. Incident: a `high`-preset run showed zero residual
interpreter-loop signatures and was celebrated as clean, while a direct `switch` count was
unchanged before and after — not one of the control-flow interpreters had been touched.

| family | count |
|---|---|
| control-flow flattening | `switch`, `while` |
| dispatchers / goto encoding | sequence (comma) expressions |
| string concealing | bracket-member reads, array-index lookups |
| packers | `Function(`, `eval(` |

A count that drops to zero is a real decode; a count unchanged across the run is a *total*
non-decode that a signature grep scores as clean.

**Pick a count that *can* move before the fix is finished.** A structural count whose subject is
only removed by the last step of a multi-step fix reads flat through every intermediate step,
indistinguishable from no progress. One count sat unchanged across several changes — including one
that removed a quarter of the residue a *different* count was tracking — and was twice read as
"measured not to be the fix". Prefer the count over what the intermediate steps actually change.

**A saturated count stops discriminating.** Once a signal reads clean everywhere it finds nothing;
switch to whatever axis is still open rather than building a second scoreboard for the closed one.

### S3. Zero-reference bindings left in the output

Any runtime helper the decoder was supposed to consume should end at zero references *and* be gone
from the output. A helper still printed with no callers is dead scaffolding, and it is always
fixable by reference-count-gated deletion.

**Two caveats, both found the hard way, running in opposite directions — which is why the
reference count has to be read before either conclusion.**

- **Unreferenced does not mean missed.** Obfuscators emit dead helpers of their own: one sample
  arrived with an XOR string helper that had zero call sites, plus the string blob only that dead
  helper read — both dead on arrival. Check whether it was ever live in the input. This also
  bounds use-site-driven decoding: a helper with no live references has no use site to be
  discovered from.

  **But run that check, because the answer routinely inverts.** The same zero-reference helper is
  also what a *cleanup sweep* leaves when one of its own gates keys on a spelling an earlier pass
  stopped emitting — and that failure is invisible in a way a declining matcher is not. A matcher
  that declines leaves the shape intact and is countable by a breadcrumb (T6); a sweep whose
  deletion gate reads false deletes nothing, logs nothing, and the residue then looks exactly like
  the encoder's own dead code. One such gate kept a runtime helper on a large share of samples —
  a third of all decoded bytes — through three censuses that reported the pass clean, because
  every one asked about the pass's *matcher*. Whenever a matcher is taught to resolve through a
  binding instead of a declaration form, audit that pass's deletion gates in the same change.
- **Referenced does not mean live work either.** A helper the sweep declines to delete can have
  plenty of references and still be pure residue, when every one sits inside a *different*
  undecoded layer — seen twice as a helper referenced only from the entry vectors of harnesses a
  later fix removed wholesale, at which point the orphan went to zero without anyone touching the
  sweep. An undeleted helper is a symptom to attribute, not a cleanup bug to fix: chase the residue
  holding it alive, not the helper.

### S5. Obfuscator output is randomized by design

Placeholder names, state vectors, key strings and case ordering are regenerated per run, and many
transforms are probability-gated rather than unconditional — so a transform requested at full
strength may still not fire on a given source. One run can false-negative in two different ways.
Three to five runs per side, minimum, on any verdict you intend to act on. Two fresh encodes are
not comparable to each other at all, so **freeze a corpus before A/B-ing anything.**

**This compounds across an isolation matrix (T5).** A grid of cells that all read clean in
isolation does not bound a probability-gated transform's own bug rate — it can mean only that
every short isolated run missed the payload. Seed case: several matrix cells were partial while
the same transform combos read clean in isolation; "no transform is individually implicated" was
recorded from that grid, and the real cause was one transform's own bug (random per-run template
selection), reachable from a two-transform combo alone at a rate the grid's short runs were never
going to bound.

## Tier 4 — situational

### T5. Isolate a combo gap empirically, then read only what is left

**Reach for this only when a breadcrumb cannot be placed** — when the gap appears under a preset
or multi-transform sample, under no single-transform test, and there is no failing site to
instrument yet. Where a real failing sample exists, T6 is strictly better: it has named every
cause in this project on its first run, and no isolation matrix here has ever named one. S5 bounds
what this procedure can conclude.

1. **Fix one small source shape and a base combo already known to decode cleanly** — a
   previously-closed gap's own base is ideal, being already known-good.
2. **Obfuscate with base + one candidate transform at a time**, forced to full strength
   (`1`/`true`, never a probability), decode, and judge against a structural count (S2), never a
   signature regex. Three-plus runs each (S5).
3. **Whichever single addition flips the verdict** from clean to consistently broken is the
   trigger — cheaper than reading each transform's source hoping to predict the interaction.
4. **Then shrink the reproducing combo itself:** drop one transform at a time, 3–5 runs each, to
   the true minimum. This usually shrinks the *sample* dramatically too, which matters for reading
   the residue and for keeping the eventual fixture small.

**Read encoder source only after that** — reading is for explaining a known-minimal reproduction,
not for searching. One corollary worth keeping: a cause has needed a *second* transform present to
reproduce at all, so a matrix that varies one transform at a time could not have reached it.

### Studying a new encoder/decoder pair

Follow the process used for `js-confuser` (see [js-confuser.md](js-confuser/js-confuser.md) and
its supporting files as a worked example) when building a skill package for a new submodule pair.
T8's "verify against source" and "treat a decode attempt as the verification step" apply
throughout and are not repeated here.

- **Go incrementally, from unit to combo.** Document one transform/module at a time rather than
  the whole surface in one pass, and let whoever is driving direct which piece comes next rather
  than front-running unrequested sections. But single-transform coverage is a first phase, not a
  finish line: schedule a second pass against real multi-transform output before calling a package
  complete. A decoder built and tested one transform at a time exercises each matcher in isolation
  and never the interactions a later encoder stage's residue creates — this project's own closed
  bugs are almost entirely combo bugs (a renaming stage invalidating a name-keyed matcher, a
  declaration-hoisting stage splitting a harness from its entry point, a statement-merging stage
  dissolving the partition a downstream matcher expected) that no single-transform fixture could
  have caught.

  The unit-phase loop that worked, per transform: **(1)** stop first if the decoder file already
  exists and reuses a *shared*, non-target-specific visitor — whether to keep sharing or fork is a
  decision for whoever is driving, not a default; **(2)** document the encoder side; **(3)** write
  the decoder pass; **(4)** document the decoder side; **(5)** build the fixtures from the
  *encoder's own* test cases for that transform, a free and authoritative case list; **(6)** pause
  for review; **(7)** commit, then clear context before the next transform's research.
- **Respect the preset order.** When the obfuscator ships named complexity tiers (e.g.
  `low`/`medium`/`high`), climb that hierarchy as the combo ladder instead of inventing one —
  smallest first, largest reserved for the final integration check. A bug is cheaper to isolate at
  a smaller tier, and a gap found directly against the largest is far harder to shrink to a minimal
  repro. Don't assume subset semantics, though — a smaller tier can be a genuinely distinct shape
  rather than a subset (`low` here skips ControlFlowFlattening entirely), so verify the actual
  relationship before treating one tier's coverage as implying another's.
- **Summarize the test suite.** A `tests.md` covering the framework, project/config structure and
  directory breakdown pins down exact before/after behaviour in a way prose can't, and gives
  readers somewhere to go when the docs need more precision.
- **Cross-reference upstream docs, but verify them too.** If the submodule ships its own `docs/`,
  link the matching page from the corresponding skill file — but confirm it still matches the
  pinned source commit first; note (don't silently drop) any upstream doc describing a feature
  absent from the pinned version.
