# String Array Rotator

The string array is emitted **already rotated**, and a self-contained IIFE prepended to the program
rotates it back before any use site runs. The indexes at the use sites address the unrotated array,
so nothing works until this has run.

**Gated on `rotateStringArray`.** Its default is on ([options.md](../options.md)), so it is present
in samples built with no options set. It is inert when the program has no string literals at all —
the transformer traverses for one and gives up if it finds none, *before* the array storage exists.

Its three companions are separate components with separate histories:
[string-array.md](string-array.md),
[string-array-calls-wrapper.md](string-array-calls-wrapper.md) and
[string-array-scope-calls-wrapper.md](string-array-scope-calls-wrapper.md).

## 1. Target

Make the array's printed order wrong. A reader who extracts the array literal and indexes it
directly gets the wrong string at every index; the correct order exists only after the program has
run its own prelude. Under `E-sa-rotate-compare-loop` it is stronger than that: **the file does not
state how far to rotate.**

## 2. Algorithm

Rotation is `push(shift())` repeated — the array is rotated left one element at a time. Every era
does that. What separates the eras is **how the loop knows when to stop**, and that difference is
the whole decoding difficulty.

**`E-sa-rotate-counter-loop` — the amount is a literal in the file.**

```js
(function (array, times) {
  const rot = function (times) { while (--times) { array['push'](array['shift']()); } };
  rot(++times);
})(_0x110e, 0x1bf);
```

The IIFE's second argument *is* the rotation amount. `rot(++times)` entered with `N+1` and
`while (--times)` executes the body `N` times, so the array is rotated exactly `N` times.
**Recoverable by reading**: take the literal, rotate the extracted array that many times, done.

**`E-sa-rotate-compare-loop` — the amount is not stated anywhere.**

```js
(function (array, comparisonValue) {
  while (!![]) {
    try {
      var result = parseInt(w(0x101)) / 0x1 + parseInt(w(0xf1)) / 0x2 + /* … */;
      if (result === comparisonValue) break;
      else array['push'](array['shift']());
    } catch (e) { array['push'](array['shift']()); }
  }
})(_0x789d, 0x93d6c);
```

The loop rotates until a **checksum over the array's own contents** matches a random target. Its
operands are read back out of the string array itself, through the calls wrapper: the encoder
force-adds the comparison expression's numeric-looking literals — strings like `'548GnnLDk'`, from
which `parseInt` takes the leading digits — to the string array as ordinary items. So each rotation
changes the operands, and the equality holds exactly at the correct arrangement.

Three consequences follow from the emitted loop:

- **The rotation amount appears nowhere.** Not as a literal, not as a derivable constant. The only
  way to obtain it is to perform the search the loop performs.
- **The `try`/`catch` is load-bearing, not decoration.** Before enough rotations the operands land
  on elements that are not numeric-ish; `parseInt` yields `NaN` and the comparison simply fails, or
  an element is missing and the access throws. The `catch` rotates and continues, so a wrong
  arrangement is indistinguishable from a thrown one — both just rotate again.
- **It is an infinite loop if the array is wrong.** Feed it a modified or truncated array and it
  never terminates. Anything that *executes* a sample's prelude to recover the order needs a
  timeout for that reason alone, and this is a live hazard rather than a hypothetical one — the
  same class of trap as `selfDefending`'s.

**`E-sa-rotate-compare-loop-fn-arg`** is the same loop with one structural change: the first
parameter is no longer the array but the **array accessor function**, called once inside the IIFE
(`var arr = fn();`). It moves in lockstep with the holder becoming a function
([string-array.md](string-array.md)) — the rotator has to call it because there is no array binding
to pass. The comparison expression also changes spelling, from products of `parseInt` terms to
`parseInt(...) / n` terms with an incrementing divisor; that is the arithmetic the encoder built,
an implementation detail of the generated checksum rather than an additional era signature.

**The fragment is obfuscated by a private pipeline.** The transformer builds the rotator, then runs
it through its own four-stage transformer subset (`Preparing`, `Converting`, `RenameIdentifiers`,
`Finalizing`) with six transformers only — boolean literals, member expressions, number literals,
number-to-numerical-expression, parentification, scope identifiers. That is why `true` reads
`!![]`, why `push`/`shift` are string-keyed member reads, and why its identifiers are renamed like
everything else. Its literals are then marked ignored so the main string-array pass does not
collect them — **except** the comparison expression's, which are force-added on purpose.

## 3. Implementation

| Item | At the spine's era | Era |
|---|---|---|
| Stage | `StringArray` (8), before `StringArrayTransformer`, which declares `runAfter` on it | `2.10.0` and up |
| Emitted by | a code helper only — there is no rotate transformer | `E-sa-rotate-counter-loop` |
| Emitted by | `StringArrayRotateFunctionTransformer` plus the code helper | `E-sa-rotate-compare-loop` and up |
| Placement | `NodeAppender.prepend` onto the `Program` | all read eras |
| Applicability | `isProgramNodeHasStringLiterals` — an `estraverse` walk that breaks on the first string literal | `2.10.0` and up |
| Stop condition | second IIFE argument, a hex literal = the rotation amount | `E-sa-rotate-counter-loop` |
| Stop condition | `result === comparisonValue`, `comparisonValue` random in `[100000, 1000000)` | `E-sa-rotate-compare-loop` and up |
| Comparison operands | `parseInt('<digits><random>')` read through the calls wrapper, 7 additional parts | `E-sa-rotate-compare-loop` and up |
| Comparison spelling | products and sums of `parseInt` terms | `E-sa-rotate-compare-loop` |
| Comparison spelling | `parseInt(…) / n` with `n` incrementing from 1 | `E-sa-rotate-compare-loop-fn-arg` |
| First IIFE argument | the array binding | up to `E-sa-rotate-compare-loop` |
| First IIFE argument | the array accessor function, called inside | `E-sa-rotate-compare-loop-fn-arg` |
| Private pipeline | 6 transformers over 4 stages, then literals marked `ignoredNode` | `2.10.0` and up |

**`selfDefending` replaces the loop body's call.** At `E-sa-rotate-counter-loop` the helper emits
either `rot(++times)` or, with `selfDefending` on, a `SelfDefendingTemplate` expansion in the same
slot. So the counter-loop shape has two sub-spellings and only one of them states the amount
plainly.

**Read at `2.9.6`, the sub-spelling fuses rotation into the anti-tamper helper, and the rotation
becomes conditional on the tamper check passing.** Both live in one IIFE — the rotator function and
a `{data, setCookie, removeCookie, getCookie}` object beside it — and the call `rot(++times)` sits
**inside `getCookie`**, which is reached only from the branch taken when the check succeeds:

- the check is a `RegExp` over `removeCookie.toString()`, so it fails as soon as the emitted source
  has been re-spelled;
- its false branch calls `setCookie(['*'], 'counter', 1)`, whose loop **pushes into the array it is
  iterating and re-reads `length` each turn**, so it never terminates and the string it accumulates
  grows without bound — the program dies of `RangeError: Invalid string length` rather than hanging;
- so at this era a tampered sample also **loses its rotation**, because the only call site is on
  the branch it no longer reaches.

**From `2.10.0` the rotator is its own transformer and the fusion is gone** — the two shapes are
separately emitted, and the same tampering leaves a program that still runs. That is what makes
this a boundary on *this* axis rather than on the self-defending one, whose own era
(`E-selfdef-regexp`) spans both sides of it unchanged.

**Four source changes inside `E-sa-rotate-compare-loop` are deliberately not boundaries**, each
read and classified: a regex test extracted into a named method (`2.10.1`), a converter method
renamed `convert` → `convertIntegerNumberData` (`2.10.4`), a parameter type renamed to
`TStringLiteralNode` (`2.11.0`), and the `estraverse` import repointed to the project's own fork
(`2.13.0`). None changes the emitted shape, and the corpus agrees: `2.10.0`, `2.11.1` and `2.12.0`
emit the same rotator signature.

## 4. Downstream Effects

| Later | Effect on this transform's output |
|---|---|
| `StringArrayTransformer`, same stage | collects the comparison expression's literals into the array — so the rotator's own operands are string-array calls, and the rotator therefore *depends on* the calls wrapper being defined |
| `Finalizing` — `EscapeSequenceTransformer` | escapes any surviving literal, including the `'push'` / `'shift'` member keys |
| `Finalizing` — adjacent-statement merging | fuses the IIFE's inner statements; at the spine `var w = W, arr = fn();` is one merged declaration |
| `RenameIdentifiers` (7) — before this | every identifier here is generated. **Nothing may be identified by name** |
| its own transformer's private pipeline | `StringArrayRotateFunctionTransformer` re-runs a private six-transformer list over the rotate function through `Preparing`, `Converting`, `RenameIdentifiers` and `Finalizing`, then marks the result ignored so the outer pipeline leaves it alone. `NumberToNumericalExpressionTransformer` is in that list, so under `numbersToExpressions` the checksum's numeric operands arrive as arithmetic trees. Read identical at `2.19.0` and `5.5.0` |

**This is a different mechanism from the calls wrapper's** — that one re-runs the whole obfuscator
over its template ([string-array-calls-wrapper.md](string-array-calls-wrapper.md)), this one runs a
fixed six-transformer list in-process — with the same visible consequence: a numeric constant in
the rotator is not reliably a `NumericLiteral`. Both are why the machinery's spelling varies while
the emitted *era* does not.

**The circular-looking dependency is real and resolved by hoisting.** The rotator calls the calls
wrapper, which reads the array, which the rotator is rotating. It works because the wrapper is a
hoisted function declaration and the array holder is either hoisted too or already initialised, and
because the wrapper reads the array *live* on each call rather than capturing a snapshot at
definition time.

## 5. Known Quirks

- **The applicability test predates the storage it protects.** `isProgramNodeHasStringLiterals`
  exists because this transformer runs *before* the string-array analyzer, so it cannot ask the
  storage whether it is empty and re-derives the answer by walking the program. Its own comment
  says so.
- **A rotator can be emitted for an array that ends up empty.** The walk above finds a string
  literal that a later guard (`isProhibitedLiteralNode`, or `stringArrayThreshold`) then declines
  to collect. Not observed in the corpus; readable from the ordering.
- **`shuffleStringArray` and `rotateStringArray` are independent and compose.** Shuffling
  renumbers, rotation does not. Only rotation leaves a runtime artifact.

## Source

- Transformer:
  [`StringArrayRotateFunctionTransformer.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/node-transformers/string-array-transformers/StringArrayRotateFunctionTransformer.ts)
- Template, `E-sa-rotate-compare-loop-fn-arg`:
  [`StringArrayRotateFunctionTemplate.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/custom-code-helpers/string-array/templates/string-array-rotate-function/StringArrayRotateFunctionTemplate.ts)
- Template, `E-sa-rotate-counter-loop`, and the amount as a literal:
  [`StringArrayRotateFunctionTemplate.ts` at 2.9.6](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/0afcf7a5b2f56ba7c31246928f8f1b485a0a030a/src/custom-code-helpers/string-array/templates/string-array-rotate-function/StringArrayRotateFunctionTemplate.ts)
- Code helper, and the `selfDefending` slot:
  [`StringArrayRotateFunctionCodeHelper.ts` at 2.9.6](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/0afcf7a5b2f56ba7c31246928f8f1b485a0a030a/src/custom-code-helpers/string-array/StringArrayRotateFunctionCodeHelper.ts)
- Rotation amount and its range:
  [`StringArrayStorage.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/storages/string-array-transformers/StringArrayStorage.ts)

Read at `2.19.0`, the spine; the `E-sa-rotate-counter-loop` rows at `2.9.6`.

## Fixtures

**None committed.** What checks the claims today:

| Claim | What checks it | Era | Gap |
|---|---|---|---|
| the amount is the second IIFE argument | corpus `strings__baseline` at 2.9.6 — `(…)(_0x110e, 0x1bf)`, and `0x1bf` is 447, inside `[100, 500]` | `E-sa-rotate-counter-loop` | the rotation has not been *performed* and checked against the decoded strings |
| the loop is a checksum search | corpus `strings__baseline` at 2.10.0 – 2.18.1 | `E-sa-rotate-compare-loop` | — |
| operands come back through the calls wrapper | the same cells — every `parseInt` argument is a wrapper call | `E-sa-rotate-compare-loop` and up | — |
| the first argument becomes the accessor | corpus `strings__baseline` at 2.19.0 | `E-sa-rotate-compare-loop-fn-arg` | upper bound is source-read only |
| absent when `rotateStringArray` is off | corpus `*__no-rotate` at all eight versions — the rotator is gone and the array and wrapper remain | all | — |
| the `selfDefending` sub-spelling | corpus `*__self-defending` at 2.9.6 | `E-sa-rotate-counter-loop` | read: the fusion, the conditional call site inside `getCookie`, and the runaway `setCookie` on the tampered branch (item 3). The **plain** sub-spelling at the same era is still not diffed against it |

Upstream's own cases:
`test/functional-tests/node-transformers/string-array-transformers/string-array-rotate-function-transformer/`.
