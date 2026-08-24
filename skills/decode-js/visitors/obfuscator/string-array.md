# string-array.js

Reverses javascript-obfuscator's string array: every root-wrapper call becomes the string it
returns, and the machinery that produced it is deleted. It is the second half of the string-array
reversal; the first is [detect.js](detect.md), which resolves the entrypoint this consumes.

## 1. Target

Produce the program with its concealed strings back in place and nothing of the concealment left:
no holder, no root calls wrapper, no rotator, no wrapper aliases, and no call sites.

**One run produces one layer, not a fixpoint.** On a sample obfuscated twice the result is the
inner layer — still obfuscated, and correctly so, because the second encode's input *was* the
first encode's output. Reporting that is the caller's cue to run again, which is why the outcome
is a status rather than a boolean.

**Everything short of a complete decode leaves the tree untouched.** A half-resolved string array
is worse than an untouched one: downstream matchers key on how a construct is spelled, so a
partial decode manufactures two entities out of one and the passes after it treat them as
unrelated.

## 2. Algorithm

**Evaluate, don't model.** The subsystem is located structurally, its source text is captured, it
is evaluated in an isolate, and each call site is decoded by evaluating that call. Rotation, the
index arithmetic and the `none` / `base64` / `rc4` encodings are therefore performed by the
encoder's own code rather than reimplemented.

The reason is generality, over three axes that are shape-only:

- **Encodings.** A base64 over a swapped alphabet with a padding-ignoring decoder, and an rc4
  keyed per item out of a key pool. Evaluating covers both at no cost; reimplementing them is
  where "nearly right" becomes silently wrong output rather than a failure.
- **Eras.** The holder, wrapper, rotator and scope-wrapper shapes each move on their own axis
  ([versions.md](../../../javascript-obfuscator/versions.md)'s `E-sa-array-*`, `E-sa-wrapper-*`,
  `E-sa-rotate-*`, `E-sa-scope-wrapper-*`), but their *semantics* never change. So **extraction is era-dependent and
  decoding is era-invariant** — which is why this is one file and one doc rather than one per era,
  and why every era variance lives in the matcher next door.
- **Variants.** Real samples come from *modified* obfuscators. A fork that alters the index
  arithmetic or the rotator's checksum still runs, so an evaluating reversal survives it; a model
  keyed on the stock algorithm does not.

A fourth, weaker reason: from `E-sa-rotate-compare-loop` onward the rotation amount is stated
nowhere in the file — the rotator searches until a checksum over the array's own contents
matches — so a static reversal needs an expression evaluator anyway, at which point it has built
most of a sandbox with none of the isolation.

**The costs, recorded so the choice stays deliberate.** It executes attacker-controlled code —
narrowly, only the extracted machinery and individual wrapper calls, never the program, but not
zero, since the `base64`/`rc4` decode bodies carry an inline `selfDefending` guard. Non-termination
is by design (below), so timeouts are mandatory. And it is harder to unit-test than a pure
AST→AST pass.

**One run decodes exactly one layer, deliberately, and there is no internal loop.** A second
encode wraps the first's whole output, so peeling is outermost-first and each layer is an ordinary
single-encode once it is outermost — but the dangerous failure there is a pass mutating the layer
*beneath* it, and stopping at the boundary is what makes that boundary observable. Layers also
need not come from the same encoder, so no single decoder can internalise the loop
([encoder-decoder-method.md](../../../encoder-decoder-method.md)'s W1 limiting case); it would
loop for a homogeneous stack and hand back for a foreign one, which is two behaviours where the
caller wants one.

**Four outcomes, because three of them are not failures.**

| Outcome | Means | The caller should |
|---|---|---|
| `decoded` | every call site resolved, the machinery is gone | continue, and run again if a layer remains |
| `absent` | no string array here | report success — this is what a terminating peel round looks like |
| `unowned` | ours and readable, but a construct a later unit owns is still calling it | schedule that unit; nothing is wrong |
| `unreadable` | ours, and we could not read it | refuse, with the diagnostic attached |

`unowned` exists so that a sample merely *awaiting another pass* stays distinguishable from a
matcher failure. Folding the two together is the collapse [detect.js](detect.md) exists to undo,
one level further in.

**Two guards catch a wrong decode, and both work with no expected output** — which matters
because this is the failure mode a residue census cannot see. A missed component does not throw:
it returns real strings from an unrotated array, so the output parses, runs, and reads clean on
every axis while being wrong.

- **The machinery proves its own extraction.** A compare-loop rotator searches until a checksum
  over the array's own contents matches, so it cannot terminate on an array it was not written
  for. Termination is therefore evidence the extraction was complete, and a timeout means it was
  not — not that the sample is hostile. This is why the timeout is a correctness instrument rather
  than a safety net.
- **A decoded string in computed-member-key position must be a valid identifier**, because the
  encoder put a real property name there. Under `E-sa-rotate-counter-loop`, and on any sample built
  with rotation off, the first guard has nothing to check — so this is the general one.

## 3. Implementation

**The order is the design, and two steps of it are load-bearing.**

1. **Gate before touching anything.** Each of the following ends the run at its own outcome, with
   the tree untouched: an undeclared alias, a function calling the machinery with non-constant
   arguments that is *not* a resolvable scope wrapper, a rotator that does not rotate this holder,
   a reference to a wrapper that is neither a call nor a known alias, and a read of the **array
   itself** from outside the machinery.

   The last of those is the one that is easy to leave out, and it is the same fail-open direction
   as the first. The wrapper's call sites are enumerated exhaustively, so nothing can be missed
   there — but the holder is a *separate binding* whose references nothing else counts, and a
   program indexing the array directly would have it deleted out from under it. That is a broken
   sample rather than countable residue. It is also only answerable before anything is replaced,
   which is why it belongs in this step rather than beside the removal it protects.
2. **Build the prelude** — holder, every root wrapper, every scope wrapper, then the rotator's
   invocation **last** — and evaluate it in an isolate built **per decode**, with a mandatory
   timeout. Source order is not the constraint and following it would be wrong: renamed output
   routinely emits the rotator above the rest, relying on function hoisting that no longer applies
   once the pieces are lifted out of their file. The rotator goes last so that its termination
   still proves the extraction complete (item 2's first guard).

   **Among the scope wrappers the order is deliberately not load-bearing**, and this is worth
   stating because the obvious reading is that it must be: chained calls let one forward to
   another, so a dependency order looks required. Each is emitted as a *hoisted function
   declaration*, so a chain resolves whichever way round they are written — measured by reversing
   the emission, which changes no result. They are emitted root-ward anyway, purely so a failing
   prelude reads in dependency order. Do not add a guard asserting the order matters.
3. **Rewrite each call site's callee to its wrapper's own lifted name before evaluating it**,
   rather than evaluating the alias declarations into the isolate. Renamed output reuses short
   names across non-overlapping scopes, so evaluating alias declarations can collide two distinct
   bindings onto one name. Resolution already knows which wrapper each site reached, so nothing is
   guessed.

   **Every scope wrapper is lifted under a synthetic name for the same reason**, and here the
   collision is not hypothetical: they are lifted out of their own lexical scopes into one flat
   isolate scope, and the `mangled` name generator reuses short names across sibling scopes, so
   two wrappers can arrive spelled alike and the second definition would silently win. Its upper's
   reference is rewritten to the upper's lifted name on a *clone*, so the real tree is untouched
   until the decode commits.
4. **Collect every `(call site, value)` pair before mutating anything.** All-or-nothing is not
   satisfiable while the tree is being edited and sites are still being resolved: any later
   failure would leave a half-decoded array behind.
5. **Apply both guards, then replace, then delete** — aliases first, then the rotator, the scope
   wrappers, the root wrappers, and the holder. That removal order is for readability only: what
   makes it safe is that every call site was replaced in step 4, so nothing references any of them
   by then. Then crawl from the **program** scope: bindings are deleted in
   several scopes at once, so crawling locally leaves the enclosing scopes' reference counts stale
   for whatever runs next, and a cleanup sweep is exactly the kind of pass that decides what to
   delete from a count.

**The isolate is built per decode, never at module scope.** A shared one is reused by every decode
in the process, so the second sample evaluates its machinery into a context still holding the
first's bindings: a name that should be missing resolves, and the cell passes for the wrong
reason.

**Three deliberate departures from the existing plugin's `dfs`**, which walks the same references
and is the prior art this pass was designed against
([plugins/obfuscator.md](../../plugins/obfuscator.md)). Each is a departure on the merits, not an
oversight, and each costs something:

| It does | We do | Why |
|---|---|---|
| classifies a reference by **whether evaluating it throws** — success means a use site, a throw means a nested wrapper | classify **structurally**, on whether the arguments fold to constants | its `catch` is bare, so an inline `selfDefending` guard, a `ReferenceError` from an incomplete extraction, or any bug is silently reclassified as "a nested wrapper" — and the reference is then dropped while the machinery is deleted anyway. What we give up: it needs no model of the wrapper's argument shape, so it follows nesting forms our matcher would not match. Our miss is loud (`unowned`, tree untouched); its miss is silent |
| **re-enters** `dfs` on the same item after rewriting it | resolve each wrapper once, no re-entrancy | the branch that does this is the plugin's own `AssignmentExpression` case, which its own comment flags as incomplete and liable to produce extra replacements |
| **mutates as it walks** — `replaceWith` per site inside the loop | collect every `(site, value)` pair, then mutate | a later failure otherwise leaves earlier replacements standing, which is exactly the half-resolution item 1 exists to prevent |

**Extraction is where the eras differ, and only in how each piece is re-declared.**

| Era | Extracted as |
|---|---|
| `E-sa-array-declaration` | the matched **declarator**, re-wrapped in a `var` |
| `E-sa-array-self-replacing-fn` | the function declaration verbatim |
| `E-sa-wrapper-var-fn-expression` | the matched declarator, re-wrapped in a `var` |
| `E-sa-wrapper-fn-declaration` | the function declaration verbatim |
| `E-sa-wrapper-self-replacing` | the function declaration verbatim |
| `E-sa-wrapper-array-fn-call` | the function declaration verbatim |
| `E-sa-wrapper-flat` | the function declaration verbatim; output-verified at `4.2.0` for the plain form that shifts the index inline and reads the array holder directly |
| `E-sa-rotate-counter-loop` | the rotator's **call**, wrapped in a statement so that a callee in function position is parenthesised |
| `E-sa-rotate-compare-loop` | as above |
| `E-sa-rotate-compare-loop-fn-arg` | as above |

Nothing in the list below the extraction differs by era, which is what makes this one file: the
prelude is evaluated, the call sites are evaluated, and neither step asks what produced them.

**A reference inside the machinery is not a use site.** The encoder injects scope aliases into
every lexical scope — the rotator's own body and the wrapper's inner closure included — and the
`base64`/`rc4` bodies hang a memo cache off the wrapper object. All of those look like ordinary
uses and all of them vanish with the machinery around them. Decoding them is work thrown away;
counting them as blockers refuses on samples that are entirely decodable.

**A call site's arguments are folded, not matched.** `numbersToExpressions` re-spells every numeric
constant as an arithmetic tree, so requiring a `NumericLiteral` reads the argument as unevaluable
on exactly the high-strength samples that matter most.

**Decoded values are cached by `(wrapper, argument text)`.** The same index recurs across a
program, and once the rotation has run the wrappers are pure with respect to the array.

## 4. Upstream Effects

| Spelling reaching this pass | Produced by | Whose | Era |
|---|---|---|---|
| the rotator's IIFE fused with an unrelated following statement into one sequence | the encoder's adjacent-statement merging | encoder's | all read eras |
| index shift and call-site arguments as arithmetic trees rather than literals | the encoder's `numbersToExpressions` | encoder's | all read eras |
| a `var` declaration holding the array or the wrapper **beside unrelated declarators** | the encoder's declaration merging | encoder's | `E-sa-array-declaration`, `E-sa-wrapper-var-fn-expression` |
| block-bodied `if`s, one statement per expression | [normalize-statements.js](normalize-statements.md) | **ours** | all read eras |
| the holder handed back as a declarator rather than a declaration | [detect.js](detect.md) | **ours** | `E-sa-array-declaration` |
| calls whose index argument was a numeric control-flow storage read | [inline-control-flow-storage.js](inline-control-flow-storage.md), in its pre-string-array slot | **ours** | `E-cff-storage-stringarray-shared`; `E-cff-storage-stringarray-per-host` |

The last two rows are one dependency each and both are load-bearing. Removing what the *declaration*
matcher would have handed back takes any sibling declarator with it, which is why the handle is the
declarator and why this pass puts the `var` back when it re-declares the array in the isolate. And
removing the rotator's whole *statement* takes the fused-in effect with it — on a sample that also
enables a timer, the `setInterval`.

## 5. Known Gaps

- **`unowned` has no encoder input below `3.2.0`; from `3.2.0` the composition resolves its known
  producer before this pass.** A `2.x` use site is constant by construction — the real index, fake
  padding and rc4 key come from a literal factory — so the only non-constant argument is a scope
  wrapper's own forwarding call, which is machinery. `stringArrayCallsTransform` later introduces
  `storage.key` arguments, but the obfuscator-specific storage pre-pass now exposes those indexes
  first. The local `unowned` answer remains correct and both gates remain necessary for a readable
  shape owned by any other unit; composition, rather than a weakened gate, handles the known one.
- **An undeclared alias is refused, not resolved.** `_ = W;` with no declaration makes `_` a global
  with no binding, so its call sites cannot be enumerated; deleting the machinery after missing one
  is fail-open corruption rather than countable residue. This is the shape a real sample needed
  hand-edited before any tool could touch it.
- **The computed-member-key guard is strict on purpose and has an admissible false positive.**
  A program with a legitimately non-identifier computed key (`obj['foo-bar']`) whose value came
  from the string array would be refused. No corpus cell contains one; the guard stays strict until
  one does, because loosening a guard before it has ever failed is how a guard stops guarding.
- **A sample built with rotation off has only the second guard.** Nothing self-validates the
  extraction there, so a missed component is caught only where a decoded string lands in
  computed-member-key position.
- **Evaluating a wrapper can execute an anti-tamper check.** The `base64` and `rc4` decode bodies
  carry an inline `selfDefending` guard. Probed at `E-sa-wrapper-array-fn-call` in a bare isolate
  it returned values with no hang; that says nothing about other eras or about an isolate carrying
  different globals, and the timeout is what bounds it either way.
- **Re-obfuscated input is the caller's loop, not this pass's.** A `decoded` result on a doubly
  encoded sample is a complete peel of one layer, and nothing here reports how many remain.

## Source

- [`src/visitor/obfuscator/string-array.js`](https://github.com/echo094/decode-js/blob/6cacb633ceedf0812fe31f951ba8f41ffb431ca1/src/visitor/obfuscator/string-array.js)
- Wired after the storage pre-pass in
  [`src/plugin/obfuscatorx.js`](https://github.com/echo094/decode-js/blob/6cacb633ceedf0812fe31f951ba8f41ffb431ca1/src/plugin/obfuscatorx.js), after
  `normalize-statements` and before the fixpoint group. Item 1's outcome contract is what that entry
  consumes: `unreadable` is the one status it refuses on, `absent` and `unowned` both fall through
  to the rest of the pipeline.

## Fixtures

[`test/visitor/obfuscator/string-array/`](https://github.com/echo094/decode-js/tree/6cacb633ceedf0812fe31f951ba8f41ffb431ca1/test/visitor/obfuscator/string-array),
driven by
[`string-array.test.js`](https://github.com/echo094/decode-js/blob/6cacb633ceedf0812fe31f951ba8f41ffb431ca1/test/visitor/obfuscator/string-array.test.js).
Each case is a triple — `.src.js` pre-obfuscation source, `.js` obfuscated input, `.fix.js`
golden — and every `decoded` case's golden was written only after its decoded output was shown to
reproduce the source's runtime output.

**Every fixture in the table below is at one era**, the `2.19.0` quadruple
`E-sa-array-self-replacing-fn` / `E-sa-wrapper-array-fn-call` / `E-sa-rotate-compare-loop-fn-arg` /
`E-sa-scope-wrapper-fn-declaration`
([versions.md](../../../javascript-obfuscator/versions.md)). That is the era column for this
directory, stated once rather than repeated per row.

**The earlier eras are pinned elsewhere, and deliberately at pipeline level.** Four cases under
[`test/visitor/obfuscator/era-below-2-16/`](https://github.com/echo094/decode-js/tree/6cacb633ceedf0812fe31f951ba8f41ffb431ca1/test/visitor/obfuscator/era-below-2-16)
cover the four distinct string-array era combinations below `2.16.0` — the wrapper moving at
`2.12.0` and again at `2.15.4`, the rotator at `2.10.0` — which is every combination the seven
corpus columns down there carry between them. They run the whole composition rather than this pass
alone because the surrounding passes are what make the decode assertable at all; the era column and
what each pins are in [tests.md](../../tests.md).

`E-sa-scope-wrapper-var-fn-expression` is covered by all four of them, since that scope-wrapper era
is constant across the whole range below `2.16.0`.

**The `decoded` and `absent` claims are the encoder's, not ours** — each names the variant in
`StringArrayTransformer.spec.ts` (SAT), `StringArrayRotateFunctionTransformer.spec.ts` (SARF) or
`StringArrayScopeCallsWrapperTransformer.spec.ts` (SASCW) that asserts the shape. A case invented
to match what the pass already does pins the pass to itself.

| Fixture | Claim it pins | From |
|---|---|---|
| `baseline` | the default shape decodes: holder, root wrapper, call sites | SAT #1 |
| `index-numeric-string` | a call-site index spelled as a **string** (`w('0x0')`) decodes | SAT #3.2 |
| `index-mixed-types` | both index spellings in one sample, resolved per site rather than per sample | SAT #3.3 |
| `index-shift` | the wrapper's `index - N` shift is absorbed by evaluating, not modelled | SAT #4.1 |
| `index-shift-rotate-shuffle` | shift, rotation and shuffle interact: the shift is computed against an order the rotator must restore first | SAT #4.5 |
| `same-literal-values` | one array item serving several sites decodes at every one — the eval cache is keyed on the call, not the site | SAT #5 |
| `encoding-rc4` | the memo cache hung off the wrapper object and the inline `selfDefending` guard are machinery, not use sites | SAT #8 |
| `encoding-base64-rc4` | two root wrappers with **no** `none` fallback: every site reaches the wrapper it was compiled against | SAT #11 |
| `calls-wrapper-name` | resolution goes through bindings — under mangled names the wrapper's own parameters collide with a function declaration and an inner `var`/`function` pair | SAT #13 |
| `object-computed-key` | a site in computed-member-key position decodes and passes the identifier check — the guard's positive direction | SAT #16.2 |
| `rotate-search` | the checksum search runs to completion in the isolate on an array too large to succeed on the first trial rotation | SARF, "prevent early successful comparison" |
| `string-array-off` | obfuscated output with the option off reads `absent` — what a peel loop's terminating round sees | SAT #2 |
| `short-literal-value` | every literal under the three-character membership gate leaves no array, and that is `absent` rather than a missed fingerprint | SAT #6 |
| `wrappers-function` | function-form scope wrappers decode, including two that forward to a Program-scope wrapper rather than the root | SASCW #1.2 |
| `scope-chained-mangled` | a chain decodes under **mangled** names, which reuse short names across sibling scopes — the case the synthetic lifted names exist for. Independently reproduces the value upstream's own spec asserts | SASCW #6.1.1 |
| `scope-chained-deep` | a three-level chain: a wrapper whose upper is a wrapper whose upper is a wrapper, so membership cannot be settled in one pass | SASCW #6.2.2 |
| `scope-numeric-string-offset` | an offset spelled as a **coercing string** (`param - '0x28b'`) decodes. Distinct from `index-numeric-string`, whose variable-form index is a bare literal and never exercises the coercion | SASCW #7.1.2 |
| `scope-no-root-wrappers` | a wrapper in a function scope with none on the root scope — the chain bottoms out at the root *wrapper*, which is what a fixpoint seeded from the wrong end would miss | SASCW #7.3 |
| `scope-prevailing-const` | the wrapper takes the scope's prevailing declaration kind, so a `const` program gets `const` wrappers | SASCW #4 |
| `scope-prohibited-if` | an `if` block is a prohibited scope, so a read inside it routes to an enclosing scope's wrapper and the callee is not declared in the call's own block | SASCW #3.1 |
| `scope-default-parameter` | a literal in a function default parameter, read in the enclosing scope rather than the body's | SASCW #2.4 |
| `guard-rotator-removed` | a missed rotator is caught by the computed-member-key identifier check | damaged |
| `guard-checksum-corrupted` | an incomplete extraction is caught by the compare loop failing to terminate | damaged |
| `guard-alias-undeclared` | an alias with no binding refuses rather than decoding past it | damaged |
| `guard-array-read-outside` | a read of the array from outside the machinery blocks removal | damaged |
| `guard-wrapper-removed` | evidence present with an unresolvable entrypoint is `unreadable`, distinct from `absent` | damaged |
| `nested-one-layer` | one run peels exactly one layer, and what comes back is an ordinary single-encode | doubly encoded |

**What the non-`decoded` cases assert is a status *and* an untouched tree**, compared against a
normalize-only run of the same bytes rather than against the raw input — U1 runs first, so a raw
comparison would report every one of them as mutated and would be measuring the wrong pass.

**Each refusal case also asserts its own note.** They all report `unreadable`, so a case that
lands on a different guard still reads as passing; the recorded instance is a corrupted-array case
that terminated normally and was caught by the identifier check while claiming to exercise the
timeout. The array items in `guard-rotator-removed` are deliberately not identifier-shaped for the
same reason — with identifier-shaped items the wrong strings are plausible ones and the guard
correctly stays silent.

**The `nested-one-layer` golden is derivable, not merely observed**, which is why it is worth
having: the second encode's input *was* the first encode's output, so peeling layer 2 has to
reproduce it — up to the identifier names layer 2 destroyed and the formatting our own
normalization reprinted. The case therefore asserts the golden, that running the pass again on it
reports `decoded`, and that the source's own literals come back as literals. A peel that corrupted
the inner layer fails all three where a size- or residue-based check could pass.

Two checks stay outside the suite, because they read a corpus that is rebuilt on demand and so is
local to one working copy:

| Check | Reads | Worth |
|---|---|---|
| every corpus cell, all eras, U1 normalization then this pass | the outcome | **every cell reports `decoded`**, at every era, except the one whose array the encoder never populated — which reports `absent`. No cell reports `unowned` or `unreadable` |
| the residue census over decoded output — the six string-array axes and the three scope-wrapper ones | residue | zero on every axis at every era, against a non-zero control on the same inputs. The control is what makes the zero readable: run the same census over the raw corpus and it is four figures |
| decoded output run against the pre-obfuscation source's own output | correctness | equal on every cell where it is measurable, which is every cell that does not carry anti-tamper. Those are excluded by name rather than by timeout, because `selfDefending` detects reformatting and never returns — the strip is U7's |

The same census run over the committed goldens reads zero on all six axes against a non-zero
control, with **one deliberate exception**: `nested-one-layer` carries a full subsystem, because
one run peels one layer. The census is **not** imported by this pass, and the duplication is the
point: sharing the matchers would make "the census reads zero" mean only "the pass removed what
its own matcher can see."
