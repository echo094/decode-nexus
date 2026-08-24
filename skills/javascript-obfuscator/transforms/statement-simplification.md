# Statement Simplification

The `Simplifying` stage's collapse: a block's trailing run of expression/return statements
becomes **one** statement built from a sequence expression, and an `if` whose branches collapsed
that way is rewritten into a smaller form — a de-braced branch, a `&&`, or a ternary.

One doc for two transformers because they share item 2 outright. The collection algorithm lives
in a single abstract base both extend; they differ only in what they wrap its result in, which is
item 3. The era boundaries land in both places, and splitting the doc would duplicate every row.

**Gated on `simplify`, which defaults to `true`** — so this fires in any sample not explicitly
built with it off. Measured: with `simplify: false` at 2.19.0 and an otherwise identical
configuration, every construct this doc describes goes to exactly zero.

## 1. Target

Shrink the emitted program and destroy the statement-level structure of the original. Where the
source had a readable sequence of statements, the output has one comma expression; where it had a
braced branch, the output has an operator. The block boundaries a reader — or a shape matcher —
would navigate by stop existing.

## 2. Algorithm

Two steps, the first shared and the second per transformer.

**Collect, walking the block backwards.** From the last statement of a `BlockStatement` body
upwards, absorb every `ExpressionStatement` (splicing a `SequenceExpression`'s own expressions in
flat) and a `ReturnStatement` *with an argument*, stopping at the first statement that is neither.
What was absorbed becomes `unwrappedExpressions`; everything before the stopping point stays as
`leadingStatements`. A `return` anywhere in the absorbed run sets `hasReturnStatement`.

**Rebuild.** The absorbed expressions become one expression — the single element if there is only
one, otherwise a `SequenceExpression` — wrapped in a `ReturnStatement` if the run contained a
`return` and an `ExpressionStatement` otherwise. Leading statements, if any, keep their block.

Both transformers run in the same traversal level and both use `leave`, so they see a block whose
inner blocks have already been rewritten — the collapse composes upwards.

**Ordering that matters:** this level runs *after* the merge level
([statement-and-declaration-merging.md](statement-and-declaration-merging.md)), declared through
`runAfter`. The merge transformers have already fused adjacent siblings, so the run this
algorithm absorbs is frequently one already-merged statement rather than the several the source
had. The two are not independent and cannot be read in isolation.

### The `if` rewrite's seven outcomes

Selected by what the branches collapsed to. Rows 2, 3, 4 and 7 are verified against 2.19.0 output
by the four-function probe below (`compact: false`, string array off); rows 5 and 6 are read from
source and are present in the corpus by census but not isolated; row 1 is the fall-through.

| # | Condition | Emitted |
|---|---|---|
| 1 | consequent did not collapse | unchanged |
| 2 | consequent has leading statements, or no trailing statement | `if (t) { …leading; <collapsed> }` |
| 3 | consequent is a lone `return` | `if (t) return e;` — no braces |
| 4 | consequent is a lone expression, no `else` | `t && e;` — the `if` disappears entirely |
| 5 | both branches are lone `return`s | `return t ? a : b;` |
| 6 | one branch returns, the other does not | `if (t) return a; else b;` |
| 7 | neither branch returns | `t ? a : b;` |

Worked sample, all in one 2.19.0 encode:

```js
function f(a) { if (a) { g(a); } }                        // -> a && g(a);
function h(a) { if (a) { g(1); } else { g(2); } }         // -> a ? g(1) : g(2);
function k(a) { if (a) { return 1; } }                    // -> if (a) return 1;
function m(a) { if (a) { var x = 1; g(x); return x; } }   // -> if (a) { var x = 1; return g(x), x; }
```

### The prohibition list is where this transform's eras live

Before a collapsed branch may be emitted **without braces**, the single statement replacing the
block is tested against a prohibition list; a prohibited statement keeps its block. The list has
grown **twice** in the read range, and each growth is an emitted-shape change — see
[versions.md](../versions.md)'s `E-simplify-*` axis, whose third boundary is not in this list at
all but in the shared collection routine. At the spine's era the list rejects:

- a `FunctionDeclaration` — not allowed outside a block in strict mode;
- a `let`/`const` declaration — not allowed as an `if` branch body at all;
- **an `IfStatement`** — otherwise a nested `if` inside a braced consequent can capture the outer
  `else`, which is upstream's issue #860;
- **any node with a single-statement body** — `for`, `for-of`, `for-in`, `while`, `do-while`,
  `with`, `labeled`, and an `if` whose own branch is a single statement — the same dangling-else
  hazard one level out.

The first two are present for the whole read range. The last two arrive at `2.10.2` and `2.10.3`,
one release apart, which is the only shape movement this component has inside phase 1's range.

## 3. Implementation

| Item | At the spine's era | Era |
|---|---|---|
| Collection | `collectIteratedStatementsSimplifyData`, reverse loop over `body`, `break` on the first non-absorbable statement | all read eras |
| Leading statements | `getLeadingStatements` — whole body when nothing absorbed, `[]` when everything did, `slice(0, startIndex)` otherwise | all read eras |
| Rebuild | `getPartialStatement` — the trailing statement alone when there are no leading statements, else a `BlockStatement` of both | all read eras |
| Block variant | `BlockStatementSimplifyTransformer.transformNode` — re-wraps a non-block result in a `BlockStatement`, so a block stays a block | all read eras |
| `if` variant | `IfStatementSimplifyTransformer.getConsequentNode` / `getConsequentAndAlternateNode` — the seven-row table above | all read eras |
| Brace-dropping guard | `isProhibitedSingleStatementForIfStatementBranch` | grows at `E-simplify-guard-single-body`, `E-simplify-guard-nested-if` |
| Absorption halt after a non-final `return` | `hasStatementsAfterReturnStatement` — a block with statements *after* its `return` refuses to collapse at all | `E-simplify-halt-after-return` only |
| Storage of the merge dependency | `runAfter = [ExpressionStatementsMerge, VariableDeclarationsMerge]` on the abstract base; `BlockStatementSimplify` additionally names `VariableDeclarationsMerge` | all read eras |

**A `return` with no argument is not absorbable** — the collection tests `statementBodyStatementNode.argument`
— so a bare `return;` terminates the run and keeps its block. That is the difference between a
function ending `return x;` and one ending `return;`, and it is invisible in the output.

## 4. Downstream Effects

`Simplifying` is stage 9 of 10, so almost nothing runs after it. What does:

| Later stage | Effect on this transform's output |
|---|---|
| `Finalizing` — `EscapeSequenceTransformer` | re-spells every string literal inside the collapsed expressions ([escape-sequences.md](escape-sequences.md)). Independent of structure, but it means a collapsed sequence's literals are not in their source spelling |
| `Finalizing` — `DirectivePlacementTransformer` | re-hoists a `"use strict"` to the top of each lexical scope ([directive-placement.md](directive-placement.md)). It cannot be absorbed by this collapse — a directive is neither an absorbable expression statement nor a return — so the two do not interact on the same node |
| `Finalizing` — `EvalCallExpressionTransformer` | re-serializes an `eval` host body to a string. Anything this transform collapsed *inside* an `eval` argument is emitted as text, not as tree |

**What runs *before* is the larger effect, and it is why this transform's output does not look
like its documented examples.** Every earlier stage has already run: identifiers are renamed,
numbers are numerical expressions, member reads are bracket reads, and the string array is built.
So the expressions this collapse concatenates are already obfuscated ones — the emitted comma
expression is over `_0x393d(0xeb)` calls, not over the source's own subexpressions.

## 5. Known Quirks

- **The `&&` output (variant 4) is unreachable from the corpus's three fixtures.** A census over
  the whole frozen matrix — every version, every option set — reads zero for
  `ExpressionStatement > LogicalExpression[&&]`, while the other variants are all present in the
  hundreds. It is reachable: a one-line probe at 2.19.0 (`if (a) { g(a); }` in a function body,
  string array off) emits `a && g(a)`. The fixtures simply have no `if` whose branch is a single
  side-effecting call with no `else` and no `return`. Recorded because a variant with no sample is
  a variant nothing can be checked against.
- **The transform is not idempotent in an interesting way, but it is fixed-point after one pass.**
  Both transformers use `leave`, so a block is visited once with its children final. Re-running
  the stage would find the already-collapsed forms unabsorbable (a `SequenceExpression` in an
  `ExpressionStatement` splices flat and rebuilds identically), so nothing accumulates.
- **`hasSingleExpression` is computed and stored, and at the spine's era nothing reads it.** It is
  set on every `IStatementSimplifyData` and consulted by neither transformer's branch logic. A
  dead field, not a behaviour.

## Source

- Shared collection and rebuild:
  [`AbstractStatementSimplifyTransformer.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/node-transformers/simplifying-transformers/AbstractStatementSimplifyTransformer.ts)
- Block variant:
  [`BlockStatementSimplifyTransformer.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/node-transformers/simplifying-transformers/BlockStatementSimplifyTransformer.ts)
- `if` variant, including the prohibition list:
  [`IfStatementSimplifyTransformer.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/node-transformers/simplifying-transformers/IfStatementSimplifyTransformer.ts)
- The guard the prohibition list calls:
  [`NodeGuards.isNodeWithSingleStatementBody`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/node/NodeGuards.ts#L374-L390)
- Stage gating on `simplify`:
  [`JavaScriptObfuscator.transformAstTree`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/JavaScriptObfuscator.ts)
- Where this stage sits, and which level each transformer is in: [order.md](../order.md).

All read at `2.19.0`, the spine. Era boundaries above and below it are read from the tags named
in [versions.md](../versions.md).

## Fixtures

**None committed, and the corpus is not one.** [corpus.md](../corpus.md)'s inputs exercise
variants 2, 3, 5, 6 and 7 incidentally — this transform is never the thing a corpus cell varies,
since `simplify` is not one of the option sets and is on in all of them. What exists
instead:

| Claim | What checks it | Gap |
|---|---|---|
| every construct here is the `Simplifying` stage's, nothing else's | an A/B encode at 2.19.0 with `simplify` on and off, same seed, at `baseline`, `cff`, `dead-code` and `preset-high` | one axis has a second producer — see the table in [statement-and-declaration-merging.md](statement-and-declaration-merging.md) |
| `if` outcomes 2, 3, 4, 7 | the four-function probe above, at 2.19.0 | — |
| `if` outcomes 5 and 6 | present in the spine's corpus column by census (`ReturnStatement > ConditionalExpression` reads non-zero) | not isolated to a fixture; outcome 6 not separated from outcome 3 |
| variant 4 (`&&`) exists at all | the same probe, **and now every `directives__*` corpus cell**: the fixture's `if (flag) { out = … }` is collapsed to a statement-level `&&` at every column | it is reached rather than isolated — the same cells also carry an `&&` the *input* wrote, so a census counts both |
| the prohibition list's two later entries change emitted shape | source read at `2.10.1`/`2.10.2`/`2.10.3` | **not confirmed against output** — the corpus has no 2.10.1–2.10.3 column |
| a non-final value-return stops the whole block collapse | direct `3.2.0` / `3.2.2` encode of `function f() { return 7; sideEffect(); }`, replicated on both sides with unrelated machinery disabled | `E-simplify-halt-after-return`; no frozen input contains this shape |

Upstream's own cases are the authoritative list and are not yet mined:
`test/functional-tests/node-transformers/simplifying-transformers/`.
