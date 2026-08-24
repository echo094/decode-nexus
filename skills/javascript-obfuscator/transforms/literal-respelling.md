# Literal re-spelling

Three `Converting` (6) transformers that leave a literal's *value* alone and change how it is
written. Grouped because they preserve value while changing spelling, and because two of the three
are ungated and therefore appear in every sample.

| Transformer | Option | Spelling |
|---|---|---|
| `BooleanLiteralTransformer` | **none** | `true` → `!![]`, `false` → `![]` |
| `NumberLiteralTransformer` | **none** | `1` → `0x1` — the `raw` string only |
| `NumberToNumericalExpressionTransformer` | `numbersToExpressions` | `123` → `50 + (100 * 2) - 127` |

Era axes, all three now recorded ([versions.md](../versions.md)):
`E-boolean-double-negation-array`, `E-boolean-heritage-*`, `E-numhex-raw-only` and `E-numexpr-*`.
The boolean class-heritage guard is a separate axis because it changes only the contextual
`superClass` case; ordinary booleans retain the general spelling.

## 1. Target

Deny a reader the literal. A boolean or a number written plainly is immediately legible and is a
useful landmark when reading obfuscated code; re-spelled, it has to be evaluated before it means
anything. None of the three hides the value from a *program* — every one is constant-foldable — so
the protection is against reading, not against execution.

`BooleanLiteralTransformer` is the one with a second effect worth naming: because it moves a boolean
out of literal position and into an expression, a branch test written as `if (true)` becomes
`if (!![])`, which no longer looks constant to anything matching on literals.

## 2. Algorithm

- **Boolean.** `true` becomes `!![]` and `false` becomes `![]`, built from an empty array
  expression. `![]` is `false` because an empty array is truthy; `!![]` double-negates back to
  `true`. Applied to every boolean literal with a parent through
  `E-boolean-heritage-rewritten`. From `E-boolean-heritage-preserved`, a boolean used as a class
  `superClass` is refused by this rewrite, so the source `true` or `false` remains in the emitted
  heritage while ordinary boolean literals continue through the same spelling path.
- **Number.** The node's **`raw`** is replaced while its `value` is untouched: an integer is
  re-spelled as hexadecimal, and anything else keeps `String(value)`. Results are memoized per value
  in a cache, so one number has one spelling throughout a program. Declares `runAfter` the
  numerical-expression transformer, with the stated reason of keeping its own logic simple.
- **Numerical expression.** The number is decomposed into an addition/subtraction/multiplication
  tree that evaluates back to it, with a fixed **three** additional parts. From
  `E-numexpr-float` the value is first split into integer and decimal parts, and a float is rebuilt
  from an integer tree plus its decimal remainder.

## 3. Implementation

**`NumberLiteralTransformer` changes no AST structure at all** — it writes `raw` and leaves `value`
in place. There is no distinct node shape, only alternate raw spelling. A parser that ignores
`raw` never sees this transform, while one that preserves it carries the hexadecimal spelling into
regenerated output.

**The integer test is `NumberUtils.isCeil`**, so hexadecimal is used for integers and the decimal
spelling is kept otherwise.

**The boolean heritage guard opens at `E-boolean-heritage-preserved`.** The transformer checks the
literal's parent before constructing `!![]` or `![]`; when that parent is a class `superClass`, it
leaves the boolean literal untouched. At the preceding era the same input is rewritten, producing
the malformed `extends!![]` or `extends![]` forms captured by the focused adjacent-release report.

**The additional-parts count is `3` and is not an option.** It was a private constant until
`2.10.0`, when it became a public default passed in by the caller — the same value, so the emitted
expression is unchanged.

## 4. Downstream Effects

| Later stage | What it does to this transform's output |
|---|---|
| `StringArray` (8) | nothing — none of the three produces a string, so none of their output is eligible for concealment |
| `Simplifying` (9) | the numerical expression is an expression, so it participates in statement merging like any other |
| `ControlFlowFlattening` (4), `DeadCodeInjection` (3) | run **earlier**, and their injected predicates are ordinary booleans by the time this stage sees them — so their guards are re-spelled by `BooleanLiteralTransformer` too, which is why `!![]` is the spelling of a control-flow guard rather than `true` |

**The order between the two number transformers is declared, not incidental.** `NumberLiteral`
declares `runAfter` `NumberToNumericalExpression`, so the expression tree is built first and its
component literals are then hex-spelled — which is why a numerical expression in real output reads
`0x32 + 0x64 * 0x2 - 0x7f` rather than in decimal.

## 5. Known Quirks

- **`NumberLiteralTransformer` is a formatting change wearing a transformer's clothes.** It is the
  only member of this stage that alters no AST structure whatsoever.
- **The memo cache makes one value's spelling global.** Two unrelated occurrences of `1000` get the
  same `raw`, so spelling carries no positional information — worth knowing before reading anything
  into two sites sharing a spelling.
- **`BooleanLiteralTransformer` is unconditional and therefore the most common single artefact in
  the corpus.** Nothing turns it off; a sample with no `!![]` in it is a sample with no booleans.
- **Class heritage is the contextual exception from `E-boolean-heritage-preserved`.** A boolean
  `superClass` is retained rather than rewritten; ordinary booleans, including controls injected
  by other transformers, remain on the general spelling axis.
- **The float path begins at `E-numexpr-float` and persists through the pin.** Below it a
  non-integer was handled by the integer path alone. The `3.0.1` factor-predicate rewrite is a
  performance change over the same safe-integer domain, not another emitted-shape era.

## Source

- [`BooleanLiteralTransformer.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/node-transformers/converting-transformers/BooleanLiteralTransformer.ts)
- [`NumberLiteralTransformer.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/node-transformers/converting-transformers/NumberLiteralTransformer.ts)
- [`NumberToNumericalExpressionTransformer.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/node-transformers/converting-transformers/NumberToNumericalExpressionTransformer.ts)
- [`NumberNumericalExpressionAnalyzer.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/analyzers/number-numerical-expression-analyzer/NumberNumericalExpressionAnalyzer.ts)
  — where the parts count lives.
- [`BooleanLiteralTransformer.ts` at the heritage-guard boundary](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/c6d0872a631ed290d29fce6551fbfceb6c31577d/src/node-transformers/converting-transformers/BooleanLiteralTransformer.ts)
  — the `superClass` refusal at `E-boolean-heritage-preserved`.

Read at `2.19.0`, the spine; the `E-numexpr-*` rows are read at the tags named against them.
The float path's extension was swept at every release tag through `5.5.0`.

## Fixtures

**None committed yet** — U4's fixtures are built at step 7.

| Claim | What checks it | Gap |
|---|---|---|
| every boolean is re-spelled, in every option set | a corpus census of `!![]` / `![]`, non-zero on every cell | not pinned by a committed fixture |
| boolean re-spelling reaches branch tests | the same census restricted to `if`/loop/conditional test position, which is non-zero corpus-wide | — |
| integers are hex in `raw` only, with `value` intact | source read plus any corpus cell | no fixture asserts the `value`/`raw` split |
| one value has one spelling program-wide | source read of the memo cache | unmeasured |
| the parts count is 3 and unchanged at `2.10.0` | per-tag read of the analyzer constant, `3` either side | — |
| boolean class heritage is malformed below the guard and preserves `true`/`false` at it | focused `5.4.3`/`5.4.4` class-heritage cases | `E-boolean-heritage-rewritten`, `E-boolean-heritage-preserved` |
| float support arrives at `2.10.4` | per-tag diff plus the built boundary sample recorded in `versions.md` | no corpus input carries a non-integer; above the spine is source-only |
| the float shape persists through `5.5.0` | per-release source sweep | **not output-verified above the spine** |
