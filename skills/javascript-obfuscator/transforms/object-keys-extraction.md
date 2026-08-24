# Object-keys extraction

`ObjectExpressionKeysTransformer`, `Converting` (6), gated on **`transformObjectKeys`**. It takes an
object literal apart and rebuilds it as a sequence of assignments, so the keys and their values are
no longer syntactically grouped.

Era axis: `E-objkeys-*` ([versions.md](../versions.md)). **This is the one non-atomic transform in
the stage** — every other `Converting` transform rewrites a node in place, while this one moves
properties into separate assignments whose relationship is visible only through dataflow.

## 1. Target

Two things at once, with the second explaining why this is more than a structural rewrite.

**Structure hiding.** `{ foo: 1, bar: 2 }` states its shape in one expression. Split across
assignments, the object's shape is only recoverable by following the variable, and the assignments
can be separated from the declaration by other statements.

**Concealment eligibility.** A key written as a non-computed object property is *prohibited* from
the string array ([property-name-literalization.md](property-name-literalization.md)) — so an object
literal's keys are the one class of property name the encoder cannot conceal. Extraction converts
each key into a **computed member write**, `_0xabc123['foo'] = 1`, which is eligible. So this
transform is what lets object keys reach the string array at all, and turning `transformObjectKeys`
on is what moves them from plain text into the array.

## 2. Algorithm

For each object expression, in `leave` order: bail if it is empty or prohibited, then run the
extractor chain over it and replace the original node with whatever the chain returns.

```js
// from
var object = { foo: 1, bar: 2 };
// to
var _0xabc123 = {};
_0xabc123['foo'] = 1;
_0xabc123['bar'] = 2;
var object = _0xabc123;
```

**The visitor fires on `leave`, not `enter`**, so a nested object literal is extracted before its
parent is. The consequence a reader meets in real output is that nesting produces several
interleaved assignment runs rather than one, innermost-first.

**Two extractors run in sequence, recursively**, and the order is fixed in a static list:
`ObjectExpressionToVariableDeclarationExtractor` first, then `BasePropertiesExtractor`. Each returns
a triple — the node to replace, the new host statement, and the new object expression — and the
next extractor is applied to *that* result. The first hoists the literal into a variable
declaration of its own; the second is what turns the properties into member writes.

## 3. Implementation

**The prohibition set is where every era boundary in this transform lives**, and every boundary
*narrows* it — each release refuses more objects than the last. Checked before any extraction, via
`isProhibitedObjectExpressionNode`:

| Prohibition | Era |
|---|---|
| the host statement is prohibited (several statement kinds) | all |
| the host statement is a `SequenceExpression` containing a `super()` call | all |
| the object is a **prohibited arrow-function expression** | `E-objkeys-arrow-prohibited` and up |
| the object **contains a `CallExpression` or `NewExpression`** anywhere within it | `E-objkeys-call-prohibited` |
| the object sits below a non-block loop body | `E-objkeys-loopbody-prohibited` and up |
| the object is a direct non-first sequence child, or is nested there after an earlier call/`new` | `E-objkeys-sequence-prohibited` |

The call prohibition is the widest of the phase-1 set and the one most visible in output: from `2.16.0` an object
literal holding any call — including a method value that calls something, or a `new` — is left
whole. An `E-objkeys-call-prohibited` sample therefore has *fewer* extracted objects than an earlier
one built with the same options, which reads like the option doing less rather than like a version
difference.

**The two later refusals protect evaluation placement.** `E-objkeys-loopbody-prohibited` prevents a
fresh object from being hoisted out of a non-block loop body. `E-objkeys-sequence-prohibited`
prevents extraction from moving object creation or property capture ahead of earlier side effects
in a sequence expression. Both leave the object whole; ordinary property-name literalization may
still rewrite its keys.

**`this` joins the referenced-identifier set at `E-objkeys-this-aware`.** Below it the scan that
collects the identifiers an object's properties reference accepted only `Identifier` nodes;
from `2.15.2` a `ThisExpression` is collected too, under the reserved name `'this'`.

**An empty object is never extracted** — the length check precedes everything, so `{}` in the source
stays `{}`.

## 4. Downstream Effects

| Later stage | What it does to this transform's output |
|---|---|
| `StringArray` (8) | the emitted `_0xabc123['foo']` writes are **computed**, so unlike an untouched object literal's keys they are eligible for concealment and normally taken — which is this transform's second purpose (item 1) |
| `Converting` (6), property-name literalization | the member writes this transform emits are themselves literalized like any other member access; the relative order inside the stage is [order.md](../order.md)'s |
| `Simplifying` (9) | adjacent expression statements merge, so the assignment run is commonly emitted as **one `SequenceExpression`** rather than as separate statements ([statement-and-declaration-merging.md](statement-and-declaration-merging.md)). This is the single biggest difference between the shape in this doc's example and the shape in real output |
| `ControlFlowFlattening` (4) | runs *earlier*, so its storage objects are already present and are themselves candidates — an extracted control-flow storage is a compound of two transforms rather than either alone |

## 5. Known Quirks

- **The example in the transformer's own comment is not what output looks like.** Statement merging
  fuses the assignment run into a sequence expression, so the four-line illustration above appears
  as roughly one statement. The comment has never been updated.
- **Extraction is all-or-nothing per object but not per program.** With the option on, some objects
  are extracted and others are refused by the prohibition set, so one sample legitimately contains
  both shapes. That is not partial application in the threshold sense — the refusals are
  deterministic and readable from the set above.
- **Each era refuses strictly more than the last**, so "the option did nothing here" and "this
  version stopped extracting this shape" look identical without the era in hand.

## Source

- [`ObjectExpressionKeysTransformer.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/node-transformers/converting-transformers/ObjectExpressionKeysTransformer.ts)
- Later loop-body and sequence-position refusals:
  [`ObjectExpressionKeysTransformer.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/45ad03b8335bee095b17c0d29b0a78bff158c93a/src/node-transformers/converting-transformers/ObjectExpressionKeysTransformer.ts)
- [`BasePropertiesExtractor.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/node-transformers/converting-transformers/object-expression-extractors/BasePropertiesExtractor.ts)
- [`ObjectExpressionToVariableDeclarationExtractor.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/node-transformers/converting-transformers/object-expression-extractors/ObjectExpressionToVariableDeclarationExtractor.ts)
- [`ObjectExpressionExtractor.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/enums/node-transformers/converting-transformers/properties-extractors/ObjectExpressionExtractor.ts)
  — the enum naming the two extractors, whose order in the transformer's static list is the chain order
- The prohibition on concealing a non-computed key lives in
  [`NodeLiteralUtils.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/node/NodeLiteralUtils.ts),
  not here — it is what item 1's second half rests on.

Read at `2.19.0`, the spine; the era rows are read at the tags named against them, and the extension
was swept at every release tag through `5.5.0`.

## Fixtures

**None committed yet** — U4's fixtures are built at step 7. The corpus does exercise this transform:
the `objects` fixture plus the option sets that enable `transformObjectKeys`.

| Claim | What checks it | Gap |
|---|---|---|
| an extracted object emits computed member writes | corpus cells with the option on | not pinned by a committed fixture |
| an object literal's keys are plain when the option is **off** | corpus `baseline` cells, read at `2.19.0` | — |
| the assignment run is emitted merged, not as separate statements | corpus cells | not isolated from statement merging |
| `2.16.0` refuses objects containing a call | per-tag source read, diff classified | **not output-verified**; the corpus has no cell pair isolating it |
| `2.15.2` collects `this` | per-tag source read, diff classified | as above |
| `2.9.2` refuses arrow-function expressions | per-tag source read, diff classified | as above |
| `5.2.1` refuses non-block loop-body objects | exact-tag focused output census over every loop kind, with block-body controls | positive and control shapes are both pinned by the census |
| `5.4.0` refuses evaluation-order-sensitive sequence positions | exact-tag focused output over both refusal branches, with first-position, no-side-effect and outside-sequence controls | positive and control shapes are both pinned by the census |

**The arrow and `this` rows remain source-only.** Each was found by diffing the transformer at every
release tag and classifying the change, which is exhaustive over tags but not a substitute for
emitted output. The call, loop-body and sequence-position prohibitions have exact-tag output
evidence.
