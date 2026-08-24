# String construction

Two `Converting` (6) transformers that replace a string written as one piece with an expression that
builds it from several. Grouped because both emit the same `+`-chain shape, although they are gated
differently and only one of them is about concealment.

| Transformer | Option | Emits |
|---|---|---|
| `SplitStringTransformer` | `splitStrings` | `'abcd'` → `'ab' + 'cd'`, chunked by `splitStringsChunkLength` |
| `TemplateLiteralTransformer` | **none** | `` `a${x}b` `` → `'a' + x + 'b'` |

Era axes: `E-splitstring-two-pass` for the first and `E-template-*` for the second
([versions.md](../versions.md)). The first is a single era over the whole of phase 1 — its three
content changes in range are all mechanical, and the registry records why the third one is not the
boundary it reads as.

## 1. Target

The two have genuinely different purposes and only the first is protection.

**`SplitStringTransformer` multiplies the string array's work.** A string cut into chunks becomes
several literals, each independently eligible for concealment, so one readable string becomes
several unreadable array lookups joined by `+`. It is also what starves the array in the pathological
case: chunk a program's strings small enough and the interesting ones stop meeting the string
array's own length gate.

**`TemplateLiteralTransformer` is a normalization.** A template literal is a syntax the rest of the
pipeline would otherwise have to handle separately — its quasis are string data in a node kind
nothing else knows about. Rewriting it to concatenation reduces it to literals the string array
already understands. That is why it is ungated: it is not offering protection, it is removing a
special case.

## 2. Algorithm

**Splitting is two-pass, and the reason is an upstream crash rather than obfuscation.** The literal
is first cut into large chunks of a fixed internal length, then each of those is cut again to
`splitStringsChunkLength`. The transformer's own comment gives the reason: doing it in one pass
raised `Maximum call stack size exceeded` inside the `esrecurse` package. So the emitted tree's
*associativity* is an artefact of a workaround, not a design choice.

**Template rewriting walks quasis and expressions alternately**, emitting each quasi's `cooked` value
as a string literal and interleaving the interpolated expressions, then folding the whole list into a
left-leaning `+` chain. Two details are load-bearing:

- **Empty quasis are dropped.** `` `${a}${b}` `` contributes no `''` between the two expressions.
- **A leading `''` is prepended when neither of the first two nodes is a string literal.** Since `+`
  is left-associative, `` `${1}${2}` `` would otherwise emit `1 + 2` and evaluate to `3` instead of
  `'12'`. The prepended empty string forces string semantics. **This is the one place in the stage
  where the encoder emits a node purely to preserve meaning**; without it the emitted expression
  would perform numeric addition.

**A tagged template is left alone** — the transform returns early when the parent is a
`TaggedTemplateExpression`, because the tag function receives the quasis and raw strings themselves
and rewriting them would change what it is handed.

## 3. Implementation

- **`SplitStringTransformer` consults `isProhibitedLiteralNode`**, so a non-computed property key, an
  import declaration and an export declaration are never split — the same exemption set that governs
  string-array eligibility ([property-name-literalization.md](property-name-literalization.md)).
- **The option gate moved into `getVisitor` at `2.19.0`**, returning `null` for the whole stage
  rather than returning early per node. Behaviourally identical, and classified as mechanical.
- **From `E-template-skip-uncooked-shift`, a quasi whose `cooked` is `null` or `undefined` is
  skipped.** The queue form does not consume the corresponding expression, so a later cooked quasi
  takes it. At `E-template-skip-uncooked-indexed`, quasi and expression are paired by index and both
  positions are skipped together. `cooked` is null for an invalid escape, which is rejected in an
  untagged template and legal only in a tagged one — and the transform already returns early there.
  The distinction is therefore source-readable only on a synthetic invalid untagged AST; every
  valid input emits the same concatenation on both sides.

## 4. Downstream Effects

| Later stage | What it does to this transform's output |
|---|---|
| `StringArray` (8) | the chunks and quasi literals are ordinary string literals and are concealed like any other, subject to that stage's own length and threshold gates. **This is the whole point of splitting** and merely incidental for templates |
| `Simplifying` (9) | the `+` chain is an expression and merges like any other |
| `Converting` (6), object-keys extraction | `SplitStringTransformer` declares `runAfter` `ObjectExpressionKeysTransformer`, so splitting sees the member writes extraction has already emitted |

**A split string's chunks can fail the string array's own gates while the whole string would have
passed**, which is how a heavily split sample ends up with *more* readable text in it rather than
less. Recorded in [corpus.md](../corpus.md) as the `all-on` starvation.

## 5. Known Quirks

- **The two-pass split is a workaround for a stack overflow**, so the shape of the emitted tree
  carries no meaning worth reading.
- **`TemplateLiteralTransformer` is ungated**, so a source using template literals has them rewritten
  even at the encoder's least aggressive settings — including `baseline`.
- **The `''` prefix is a semantic guard, and appears only when it is needed**, so its presence in
  output is evidence about what the first two nodes were, not a constant marker.
- **No later encoder stage restores a template literal**; the concatenation is the final emitted
  shape.

## Source

- [`SplitStringTransformer.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/node-transformers/converting-transformers/SplitStringTransformer.ts)
- [`TemplateLiteralTransformer.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/node-transformers/converting-transformers/TemplateLiteralTransformer.ts)
- Indexed uncooked pairing at the pin:
  [`TemplateLiteralTransformer.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/45ad03b8335bee095b17c0d29b0a78bff158c93a/src/node-transformers/converting-transformers/TemplateLiteralTransformer.ts)
- [`NodeLiteralUtils.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/node/NodeLiteralUtils.ts)
  — the prohibition set splitting shares with the string array.

Read at `2.19.0`, the spine; the `E-template-*` rows are read at the tags named against them.
The template extension was swept at every release tag through `5.5.0`.

## Fixtures

**None committed yet** — U4's fixtures are built at step 7.

| Claim | What checks it | Gap |
|---|---|---|
| splitting emits a `+` chain of literals | corpus cells with `splitStrings` on | not pinned by a committed fixture |
| a non-computed property key is never split | corpus cells, cross-checked against the same exemption on the concealment side | — |
| chunking can starve the string array | recorded in [corpus.md](../corpus.md) from the `all-on` cell | — |
| the `''` prefix appears when neither of the first two nodes is a string | source read | **no corpus input uses a template literal**, so every template claim here is source-only |
| empty quasis are dropped | source read | as above |
| a tagged template is left alone | source read | as above |
| `E-template-skip-uncooked-shift` | per-tag diff, classified | unreachable in real output |
| `E-template-skip-uncooked-indexed` | per-tag diff at `5.2.0`, classified | unreachable in real output |

**Every template-literal claim in this doc is a source reading**, because no corpus input contains a
template literal — checked, not assumed. That is the same corpus gap as the missing class input, and
it is the cheaper half to close: a template literal is one line.
