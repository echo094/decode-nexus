# detect.js

Locates javascript-obfuscator's string-array subsystem and resolves its entrypoint. It is the
first half of the string-array reversal; the second is [string-array.js](string-array.md), which
consumes what this returns.

## 1. Target

Answer three questions about a sample, and keep them apart:

1. **Is a string-array subsystem here at all?**
2. **If so, where are its parts** — the holder, every root calls wrapper, the rotator, the aliases?
3. **If evidence is here but the parts will not resolve, say so** rather than reporting nothing.

The third is the whole reason this is a separate file. A detector fused into its decoder can only
return the handles or a falsy value, and "no string array present" then becomes indistinguishable
from "a string array I could not read". Those need opposite responses: the first is the terminating
verdict of a peel loop, the second is a refusal a user has to act on.

## 2. Algorithm

**Shape-first, with era correspondence kept as development evidence.** The pass matches a union of
the emitted shapes and returns the handles needed to decode them. Nothing here branches on a
version or reports one at runtime; a new era adds a row in
[versions.md](../../../javascript-obfuscator/versions.md) plus a row in item 3's table, with this
matcher untouched.

The union is small because the three components vary independently but semantically not at all.
One matcher covers all five wrapper eras by returning the two things that differ — whether the
real body is hidden behind a self-reassignment, and how the body reaches the array — instead of
branching on them.

**Three outcomes, never a boolean:**

| Outcome | Means | The caller should |
|---|---|---|
| `resolved` | the entrypoint is complete | decode |
| `absent` | no string-array evidence at all | report success; this is what a terminating peel round looks like |
| `unreadable` | evidence present, entrypoint unresolved | refuse, with the diagnostic attached |

**Separating `absent` from `unreadable` needs a second, weaker probe**, because the strict matchers
cannot tell "nothing here" from "here in a shape nobody wrote a branch for" — a probe mirroring a
matcher gate for gate finds only near-misses and is blind by construction to a whole missing holder
kind. The weak probe therefore keys on the payload's cheapest structural traces, independently of
how the matchers are written.

**No single weak signal is evidence, and the threshold is two.** Every signal occurs in ordinary
code; `array-of-strings` fires on a literal as plain as `var parts = ['alpha', 'beta', 'gamma']`.
Refusing on one signal makes the pass refuse over source that was never obfuscated — measured, on
this project's own un-obfuscated test fixture. The asymmetry is deliberate and is the reason the
threshold is not tuned for sensitivity: **a missed diagnostic costs a re-run, a false refusal
discards a completed decode.**

## 3. Implementation

**The signature, and the eras it resolves to.** `detect` returns three signature strings and never
an era ID. The correspondence is documentation, kept here so the registry can gain rows without the
matcher changing, and grep-checkable in both directions against
[versions.md](../../../javascript-obfuscator/versions.md).

| Signature | Era |
|---|---|
| `holder=var-declaration` | `E-sa-array-declaration` |
| `holder=fn-self-replacing` | `E-sa-array-self-replacing-fn` |
| `wrapper=var-function-expression/plain/reads-identifier` | `E-sa-wrapper-var-fn-expression` |
| `wrapper=function-declaration/plain/reads-identifier` | `E-sa-wrapper-fn-declaration` |
| `wrapper=function-declaration/self-replacing/reads-identifier` | `E-sa-wrapper-self-replacing` |
| `wrapper=function-declaration/self-replacing/reads-call-hoisted` | `E-sa-wrapper-array-fn-call` |
| `wrapper=function-declaration/plain/reads-call-hoisted` | `E-sa-wrapper-flat` — output-verified at `4.2.0` |
| `rotate=counter-loop/none` | `E-sa-rotate-counter-loop` |
| `rotate=compare-loop/parseint-mul` | `E-sa-rotate-compare-loop` |
| `rotate=compare-loop/parseint-div` | `E-sa-rotate-compare-loop-fn-arg` |
| `rotate=none` | **no era** — rotation is an option, so its absence is evidence about the options, not the version |

**`rotate=none` carries no era evidence.** A sample built with rotation disabled says nothing about
that axis at any version, so naming an era for it would be inventing one. This distinction belongs
to corpus and registry interpretation; it does not alter runtime decoding.

**There is no mapping from the legacy `stringArrayV0` / `V2` / `V3` labels, and looking for one is
a mistake worth naming.** Those are [plugin/obfuscator.js](../../plugins/obfuscator.md)'s detector
branches, and the premise behind them fails twice. **`V0` is not a shape** — it keys on "no rotate
function present", which is an *option* reachable at any version, so it puts a `2.9.6` plain-array
sample and a `2.19.0` self-replacing-accessor sample in one bucket; those are the two shapes
furthest apart on the array axis. And **the calls wrapper is not a sub-shape of the array**: it has
its own history and moves at releases where the array does not. That is why this file returns three
independent signature strings rather than one label.

**The map is one-to-one across phase 1's range, and that validates the shape vocabulary.**
Measured over the whole corpus: each version emits exactly one signature triple, every `E-sa-*`
boundary shows up as a signature change, and no signature changes *inside* an era. If it were
many-to-one the documentation would record all matching eras for that signature; the decoder would
still consume the same resolved handles without runtime version logic.

Two consequences worth keeping with it. The measurement turned up a discriminator the shape names
do not mention — the rotator's checksum flips from `parseInt(…) * n` to `parseInt(…) / n`, which is
what `parseint-mul` / `parseint-div` above key on, and it is a second independent tell on that axis.
And the one collision the table predicts — `E-sa-wrapper-flat` against `E-sa-wrapper-fn-declaration`,
both plain declarations — **does not materialise**. Output verification at `4.2.0` confirms the
flat signature is `function-declaration/plain/reads-call-hoisted`, while the earlier declaration
form is `function-declaration/plain/reads-identifier`; they therefore remain distinct on the
wrapper axis. If that discriminator were absent, two eras would share one signature and the lookup
would stop being a function ([doc-conventions.md](../../../doc-conventions.md)'s
registry-read-backwards rule says what a collision then obliges).

**Every matcher is shape-keyed and every cross-reference goes through a binding.** Renaming runs
before every stage this file reads, so no name in the subsystem is stable, and a name a matcher
already resolved is still a name — two identifiers spelled alike in non-overlapping scopes answer
to the same text. Three consequences that are not obvious:

- **The rotator is matched through a flattened candidate list, not off `.expression`.** Adjacent
  statement merging fuses it with whatever follows, so on a sample that also enables a timer it
  arrives as `(function (a, b) { … })(A, 0xb89ba), setInterval(…)`. Reading `.expression` directly
  reports the rotator **absent** there — and that is the dangerous direction, because a decode run
  without the rotator returns real strings from an unrotated array, so the output parses, runs, and
  reads clean on every residue axis while being wrong.
- **The index shift is folded, not matched.** `numbersToExpressions` re-spells every numeric
  constant as an arithmetic tree, so requiring a `NumericLiteral` reads the shift as absent on
  exactly the high-strength samples that matter most.
- **Statement counts are never used.** Adjacent-statement merging fuses the templates' statements
  into sequence expressions, so a body is read through a flattened effect list instead.

**The plain-declaration holder is matched permissively and filtered afterwards**, because
`var parts = ['a','b','c']` has exactly that shape. It counts as the subsystem's holder only once a
matched wrapper indexes it or a rotator rotates it. Tightening at the match site would push the
decision to where the reason is no longer visible; filtering keeps it next to the rule.

**Every handle is the node the decoder removes, which is not always the node the shape was read
from.** Two of them differ, and both differences are removal-safety rather than tidiness:

| Component | Handle | Why not the enclosing node |
|---|---|---|
| the plain-declaration holder | the **declarator** | `var a = 1, ARRAY = ['…'];` is a legal spelling, and removing the declaration takes the sibling with it |
| the rotator | the **call**, alongside the statement | adjacent-statement merging fuses the IIFE with the statement after it, so removing the statement takes that effect — a `setInterval`, on a sample enabling a timer — with it |

The same reasoning decides what counts as machinery for the "is this reference inside something we
delete wholesale" test: the rotator's *call*, never its statement, since a wrapper reference in a
fused-in effect is a real use site.

**Every root wrapper is returned, not one.** With several encodings configured the encoder emits one
wrapper per encoding, each with its own decode body, so stopping at the first leaves the rest of the
call sites undecodable.

**A reference inside the machinery is not a blocker**, and getting this wrong is not a subtle error.
The encoder injects scope wrappers into *every* lexical scope, the rotator's own body and the
wrapper's inner closure included. Those call the root wrapper with non-constant arguments — but
they are deleted along with the machinery that contains them. Counting them made the maximal
profile look unfinishable when it is fully decodable.

**The function-form scope wrappers are resolved here too, and membership is a fixpoint rather than
a shape test.** `function X(a, b) { return W(a - N, b); }` is a legal thing for any program to
contain, so the shape alone does not identify one; what does is that its forwarding chain
*terminates at a root wrapper*. Candidates are matched structurally and then grown outward from
the root wrappers, so a chain of any depth is admitted and one that never reaches a root wrapper is
left entirely alone. `stringArrayWrappersChainedCalls` is what makes the depth unbounded, and the
function form is emitted at a random position in its scope's body — so **source order carries no
dependency information** and a single pass keyed on it would admit the wrong set.

What remains in `foreignWrappers` after that is the genuine blocker: a function calling the
machinery with non-constant arguments that is *not* a resolvable scope wrapper. Control-flow
storage is the expected shape, and nothing in the corpus or the fixtures produces one yet.

## 4. Upstream Effects

| Spelling reaching this pass | Produced by | Whose | Era |
|---|---|---|---|
| holder/wrapper statements fused into sequence expressions | the encoder's adjacent-statement merging | encoder's | all read eras |
| the rotator IIFE fused with a following statement | same | encoder's | all read eras |
| index shift as an arithmetic tree rather than a literal | the encoder's `numbersToExpressions` | encoder's | all read eras |
| block-bodied `if`s, one statement per expression | [normalize-statements.js](normalize-statements.md) | **ours** | all read eras |

**`normalize-statements` runs before this pass and its output is the input this is written
against.** It does not un-fuse the sequence expressions inside the string-array templates — its
position gate is about statement-level control flow — so this pass still has to read through them.
That is why the flattening helpers above are here rather than assumed away.

**A re-obfuscated inner layer arrives canonical, so the matchers stay strict.** Measured across
three fixtures and six outer option sets: after one complete peel, every recovered inner layer
carries the pristine single-encode signature. Robustness comes from the peel above being *complete*,
not from these matchers being lenient — so an inner layer that does **not** look canonical is
evidence the outer peel was incomplete, which is a far better diagnostic than a matcher that
silently accommodates it.

## 5. Known Gaps

- **The two-signal threshold is not calibrated against adversarial input.** It is measured against
  this project's own fixtures and the frozen corpus, where it separates cleanly. A hand-written
  program combining an array of strings with a `push`/`shift` pair would be reported `unreadable`
  on a sample carrying no obfuscation at all.
- **An undeclared alias is reported but not resolved.** `_ = W;` with no declaration makes `_` a
  global, and there is no binding to resolve its call sites through. This is the shape a real
  sample needed hand-edited before any tool could touch it. The list is **returned as well as
  noted**, because a consumer has to *gate* on it rather than log it — deleting the machinery
  after missing one is fail-open corruption, where declining leaves residue that can be seen and
  counted.
- **`rotate=none` cannot distinguish "rotation disabled" from "rotator not matched".** Nothing
  visible to a matcher separates them, which is why the check that does
  belongs to the decoder pass: the compare loop cannot terminate on a wrong array, so
  termination proves the extraction.

## Source

- [`src/visitor/obfuscator/detect.js`](https://github.com/echo094/decode-js/blob/6cacb633ceedf0812fe31f951ba8f41ffb431ca1/src/visitor/obfuscator/detect.js)
- Consumed by [string-array.js](string-array.md), which is where the `undeclared`,
  `foreignWrappers` and `rotators` handles above turn into outcomes.
- Reached through `string-array.js` from
  [`src/plugin/obfuscatorx.js`](https://github.com/echo094/decode-js/blob/6cacb633ceedf0812fe31f951ba8f41ffb431ca1/src/plugin/obfuscatorx.js), which
  calls no detector directly. Item 1 is why detection is its own file regardless: the entry's
  refusal diagnostic needs "no string array present" to be distinguishable from "one I could not
  read", and that distinction is this pass's output.

## Fixtures

**No fixture directory of its own**, deliberately: this pass has no output a golden can hold, so
every case that pins one of its claims does so through
[string-array.js](string-array.md)'s fixtures, which run detection on the way in. Its own
[`## Fixtures`](string-array.md#fixtures) table is the index; the rows below are the subset that
pin a claim made *here*.

| Fixture | The claim of this pass that it pins |
|---|---|
| `string-array-off`, `short-literal-value` | `absent` on real obfuscated output carrying no array — the verdict the weak-evidence probe has to reach without refusing |
| `guard-wrapper-removed` | `unreadable` with the diagnostic naming which half failed: holder matched, no root wrapper. Evidence present and entrypoint unresolvable is not absence |
| `calls-wrapper-name` | wrapper resolution through bindings rather than name text, on a sample whose wrapper parameters collide with two unrelated bindings |
| `encoding-base64-rc4` | the wrapper **set**, one per encoding, resolved together — not "the wrapper" |
| `wrappers-function`, `scope-chained-deep` | scope wrappers resolved as machinery, including a chain whose depth the fixpoint has to grow into |
| `scope-chained-mangled` | resolution through bindings where **mangled** names repeat across sibling scopes — the case a name-keyed set would merge |
| `scope-no-root-wrappers` | the chain terminating at the root *wrapper* with no root-scope wrapper present, which a fixpoint seeded from the wrong end would miss |
| `scope-numeric-string-offset` | a coercing string offset (`param - '0x28b'`) recognised as constant, so the wrapper is admitted rather than read as a blocker |
| `index-shift`, `index-mixed-types` | the shift and both index spellings survive resolution, so an argument the caller must fold is still recognised as a call site |

**Every one of them is at the `2.19.0` era triple**, so the signature→era table in item 3 has
committed coverage of exactly one of its rows per axis. The other eras are checked only by the
corpus runs below, which is `S`'s worklist rather than a claim of coverage.

Three checks stay outside the suite, because they read a corpus rebuilt on demand and therefore
local to one working copy:

| Check | Reads | Worth |
|---|---|---|
| every corpus cell, all versions and option sets | status and signature | one signature per version, matching an **independently written** census matcher, and no cell unresolved except the one whose array the encoder never populated |
| the pre-obfuscation fixtures | status | `absent` on all three — the negative control, and the check that caught the one-signal threshold refusing on clean source |
| alias and wrapper counts vs. the census | counts | exact agreement per option set, from two matchers written independently — the disagreement is what would be the finding |

**The census is deliberately not imported by this pass**, and the duplication is the point: sharing
the matchers would make the residue census tautological, since "the census reads zero" would then
only mean "the pass removed what its own matcher can see."

**It has paid twice, and how it paid is the argument.** Both defects this pass's own development
turned up read as *correct* in isolation, and both carried a comment explaining why they were
right. Neither was found by re-reading either matcher. Both were found by running the two over one
corpus and looking at where the numbers disagreed — so the duplication is not redundancy, it is the
only oracle available when the thing under test is a matcher."
