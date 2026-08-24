# Escape Sequences

Every string literal in the program is re-spelled with escape sequences before printing.
`'hello, '` is emitted as `'hello,\x20'`.

**Ungated.** There is no option that turns this off. `unicodeEscapeSequence` controls only
*how much* is escaped, and its default (`false`) still escapes a fixed character class — so
escaped literals appear in output built with no options at all.

## 1. Target

Deny a reader and a text-level tool the string content. A `grep` for a known string fails; a
regex over the source that expects a quoted word fails; the literal is legible only after parsing
and decoding the escapes. It also composes with the string array — the array's elements are string
literals, so they are escaped too.

## 2. Algorithm

Two parts: which characters are escaped, and how the escaped text survives generation.

**Which characters.** Each character of the literal's value is tested:

- if `unicodeEscapeSequence` is on — **every** character is escaped;
- otherwise, only characters in a fixed force-escape class: `[\x00-\x1F\x7F-\x9F'"\\\s]` — the C0
  and C1 control ranges, both quote characters, backslash, and **all whitespace**.

An escaped character becomes `\xNN` if it is ASCII (`[\x00-\x7F]`) and `\uNNNN` otherwise, with the
code point in lower-case hex, zero-padded to the template width.

The whitespace member of that class is what makes this visible without any option set: an ordinary
sentence with a space in it comes out escaped.

**How it survives generation.** The transformer replaces the literal node with a new one whose
`value` is the *escaped text* and whose `raw` is that text in single quotes, and it sets an
`x-verbatim-property`. escodegen is configured with `verbatim: 'x-verbatim-property'`, so it
prints that content **literally** instead of re-deriving an escaping from the value. Without the
verbatim channel the backslashes would be re-escaped and the output would read `'hello,\\x20'`.

This is the general mechanism behind any spelling in the output that ESTree alone does not explain
— see [javascript-obfuscator.md](../javascript-obfuscator.md)'s note on `verbatim`.

**Idempotence is a cache, not a property of the function.** Encoding an already-encoded string
would escape its backslashes again. What prevents it is that the encoder stores each result under
*both* the input key and the result key, so a second encode of the same text is a cache hit and
returns it unchanged. From `E-escape-from-raw`, the cache key also includes the literal's original
`raw` spelling: two source spellings with the same decoded value remain distinct cache entries.
The guard is per encoder instance.

## 3. Implementation

| Item | At the spine's era | Era |
|---|---|---|
| Visitor | `enter`, `Finalizing` stage, on every `Literal` node | all read eras |
| Applicability | `NodeLiteralUtils.isStringLiteralNode` — `typeof value === 'string'`, and nothing else. Not gated on `ignoredNode` | all read eras |
| Force-escape class | `/[\x00-\x1F\x7F-\x9F'"\\\s]/` | all read eras |
| ASCII test | `/[\x00-\x7F]/` → `\x` + 2 hex digits, else `\u` + 4 | all read eras |
| Replacement | `NodeFactory.literalNode(encoded)`, `raw = '<encoded>'`, `x-verbatim-property` | all read eras |
| Encoder entry point | `escapeSequenceEncoder.encode(literalNode.value, unicodeEscapeSequence)` | up to `E-escape-from-value` |
| Encoder entry point | `encodeLiteral(literalNode.value, literalNode.raw)` — reads the *original source spelling* alongside the value | `E-escape-from-raw` |
| Cache | `Map`, keyed by value/escape mode and written under both input and result keys | up to `E-escape-from-value` |
| Cache | `Map`, keyed with the literal's value, original `raw` spelling and escape mode | `E-escape-from-raw` |

**No `ignoredNode` check.** The stage runner does not filter on it and this transformer does not
consult it, so nodes another transformer marked ignored are escaped too — including the
rotate-function fragment that `StringArrayRotateFunctionTransformer` builds through its own
private pipeline and then marks ignored ([order.md](../order.md)). The cache is what stops that
fragment's literals being double-escaped.

## 4. Downstream Effects

`EscapeSequenceTransformer` is in the **last** node stage, in its first level. Two things follow it:

| Later | Effect on this transform's output |
|---|---|
| `Finalizing` level 2 — `EvalCallExpressionTransformer` | serializes an `eval` host body back to source text and wraps it in a **new** literal built after this transformer has passed. That literal is therefore *not* escaped by this transform; it carries whatever `StringUtils.escapeJsString` produced |
| `escodegen.generate` | prints the verbatim content unchanged. `format.compact` from the `compact` option affects layout only |

Nothing later re-parses or re-escapes, so what this transform emits is what the file contains.

**One class of literal escapes this transform, and it is a same-level effect rather than a later
one.** `DirectivePlacementTransformer` shares `Finalizing`'s first level and re-emits each recorded
directive as a **clone prepended mid-traversal**, which the walk does not descend into — so
`'use strict'` reaches the output unescaped even at `unicodeEscapeSequence: true`, while a string
expression statement that is *not* a directive, in the same file and the same run, is escaped in
full. Measurement and the discriminating case:
[directive-placement.md](directive-placement.md).

## 5. Known Quirks

- **The literal's `value` is left lying about itself.** After this transformer runs, the node's
  `value` holds the *escaped text* rather than the string the program will produce — the two
  differ by every backslash. Nothing downstream reads it as a value, so the lie is harmless within
  the pipeline, but any analysis walking the post-`Finalizing` tree is reading escaped text out of
  a field that means "decoded value" everywhere else.
- **`isProhibitedLiteralNode` exists next door and is not consulted here.** The same utility class
  carries a guard excluding property keys, import sources and export sources; this transformer
  calls only `isStringLiteralNode`. So an unquoted-safe property key *is* escaped by this
  transform. That is legal — the key is quoted in the output — but it is a case a reader of the
  neighbouring guard would expect to be excluded.
- **A cache shared across a run is also a correctness dependency.** Before
  `E-escape-from-raw`, the value-based key could conflate source spellings that decode to the same
  value. The raw-aware key keeps those spellings separate; the focused boundary report exercises
  duplicate semantic values with distinct unicode, code-point and hex spellings.

## Source

- Transformer:
  [`EscapeSequenceTransformer.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/node-transformers/finalizing-transformers/EscapeSequenceTransformer.ts)
- Encoder:
  [`EscapeSequenceEncoder.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/utils/EscapeSequenceEncoder.ts)
- Raw-aware encoder entry and cache key at `E-escape-from-raw`:
  [`EscapeSequenceTransformer.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/f1805500f807b8e2090f8ad70ace5f958413f2b2/src/node-transformers/finalizing-transformers/EscapeSequenceTransformer.ts)
- Applicability guard:
  [`NodeLiteralUtils.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/node/NodeLiteralUtils.ts)
- The verbatim channel:
  [`JavaScriptObfuscator.escodegenParams`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/JavaScriptObfuscator.ts#L49-L53)
- `unicodeEscapeSequence`'s type and default: [options.md](../options.md).

Read at `2.19.0`, the spine.

## Fixtures

**None committed.** What checks the claims today:

| Claim | What checks it | Gap |
|---|---|---|
| escaping fires with no option set | corpus `strings__baseline` at all eight versions carries `'hello,\x20'` | — |
| whitespace is the visible member of the force class | the same cell — the escapes are spaces and newlines | other class members not separately observed |
| `unicodeEscapeSequence: false` still escapes | every corpus cell; `\u` escapes read zero across the matrix | the `true` setting is in no corpus option set, so `\u` output is **unobserved** |
| ungated by `simplify` | the `simplify` on/off A/B — the escape count is identical either way | — |
| `E-escape-from-raw` preserves source spelling and separates cache entries by `raw` | focused `5.4.6`/`5.4.7` source-spelling and duplicate-value cases, plus the adjacent ordinary corpus comparison | `E-escape-from-raw` |

Upstream's own cases: `test/functional-tests/node-transformers/finalizing-transformers/escape-sequence-transformer/`.
