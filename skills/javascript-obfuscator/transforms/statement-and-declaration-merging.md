# Statement and Declaration Merging

Adjacent sibling statements of the same kind are fused into one. Two transformers, one algorithm:
walk to the previous sibling, and if it is the same kind of statement, absorb into it and delete
yourself.

```js
console.log(1); console.log(2);   // -> (console.log(1), console.log(2));
var foo = 1; var bar = 2;         // -> var foo = 1, bar = 2;
```

One doc because item 2 is genuinely shared — same sibling lookup, same absorb-and-remove
structure, same visitor direction, same stage level. They differ only in the node kind they match
and in how absorption is spelled, which is item 3.

**Gated on `simplify`, which defaults to `true`.**

## 1. Target

Destroy statement boundaries. A matcher that navigates by "the statement after the one that does
X" loses its landmarks, and the program's statement count drops sharply — on the corpus's own
fixtures a whole function body routinely becomes a single expression statement.

## 2. Algorithm

On `leave`, for a node of the matched kind whose parent holds statements:

1. Take the **previous sibling statement**. Bail if there is none.
2. Bail unless it is the same kind of node.
3. Absorb this node's payload into it.
4. Return `VisitorOption.Remove`, deleting this node.

Because the visitor is `leave` and removal happens as the traversal passes, a run of *N* adjacent
siblings collapses pairwise into one — each absorbs into the survivor on its left.

**Absorption differs per transformer**, and the expression case has a flattening rule:

- **Expression statements.** If the previous statement's expression is *already* a
  `SequenceExpression`, push onto its `expressions` array; otherwise replace it with a new
  two-element `SequenceExpression`. So a run of five statements yields one flat five-element
  sequence, never a nested tree.
- **Variable declarations.** Concatenate this declaration's `declarations` onto the previous one's.
  **Guarded on `kind`** — a `var` will not absorb into a `let`, and vice versa — so a run of mixed
  kinds collapses into one declaration per contiguous same-kind stretch.

These run in the **first** level of the `Simplifying` stage, and
[statement-simplification.md](statement-simplification.md)'s collapse runs in the second, declared
through its `runAfter`. The ordering is load-bearing in one direction only: the collapse sees
already-merged runs, so what it absorbs is often one statement rather than several. Reading either
transform without the other gives the wrong picture of what the output contains.

## 3. Implementation

| Item | Expression statements | Variable declarations |
|---|---|---|
| Visitor | `leave`, on `ExpressionStatement` | `leave`, on `VariableDeclaration` |
| Parent guard | `NodeGuards.isNodeWithStatements(parentNode)` | same |
| Sibling lookup | `NodeStatementUtils.getPreviousSiblingStatement` | same |
| Kind guard | previous sibling is an `ExpressionStatement` | previous sibling is a `VariableDeclaration` **and** `kind` matches |
| Absorb | push onto an existing `SequenceExpression`, else build a new one | `prevStatement.declarations.push(...)` |
| Reparenting | `NodeUtils.parentizeNode` / `parentizeAst` on the moved expression | none — declarators keep their parent pointers |
| Removal | `estraverse.VisitorOption.Remove` | same |

No era-tagged rows: neither transformer's emitted shape moves anywhere in the read range
(`2.9.6` – `5.5.0`). See [versions.md](../versions.md)'s `E-adjacent-merge-*`.

## 4. Downstream Effects

| Later stage | Effect on this transform's output |
|---|---|
| `Simplifying` level 2 — the statement collapse | consumes this output directly. A sequence expression this transform built is spliced **flat** into the collapse's own run, so the two transforms' products are indistinguishable in the emitted tree ([statement-simplification.md](statement-simplification.md)) |
| `Finalizing` — `EscapeSequenceTransformer` | re-spells string literals inside the merged expressions ([escape-sequences.md](escape-sequences.md)) |
| `Finalizing` — `DirectivePlacementTransformer` | a directive is an `ExpressionStatement` with a string literal, and it **is** absorbable by the expression merger — which is precisely why directive placement exists as a separate later stage ([directive-placement.md](directive-placement.md)) |

## 5. Known Quirks

- **The multi-declarator shape has a second producer, and it is not a transform.** Merged
  declarations are the obvious signature of the declaration merger, but the string-array
  **encoding helper templates** contain authored multi-declarator `var` statements such as
  `var i = 0, j, k, s = '';`. Therefore a multi-declarator declaration is not, by itself, evidence
  that this transform ran.
- **A merged run does not record how many statements it came from.** Five statements and one
  five-element sequence are the same tree. There is no marker, no metadata, and the count is not
  recoverable from the output.

## Source

- Expression statements:
  [`ExpressionStatementsMergeTransformer.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/node-transformers/simplifying-transformers/ExpressionStatementsMergeTransformer.ts)
- Variable declarations:
  [`VariableDeclarationsMergeTransformer.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/node-transformers/simplifying-transformers/VariableDeclarationsMergeTransformer.ts)
- Where this stage sits and which level each transformer is in: [order.md](../order.md).

Read at `2.19.0`, the spine; the no-movement claim is a read of every release tag's copy of both
files from `2.9.6` to `5.5.0`.

## Fixtures

**None committed.** What checks the claims today:

| Claim | What checks it | Gap |
|---|---|---|
| both constructs are the `Simplifying` stage's | the `simplify` on/off A/B at 2.19.0, four option sets, same seed | — |
| multi-declarator has a second producer | the same A/B at `preset-high`, then dumping the twelve survivors | not traced to the specific template source file |
| pairwise collapse yields a flat sequence | read from source; visible in corpus output | not isolated in a fixture |
| neither shape moves across `2.9.6` – `5.5.0` | per-tag content read of both files | mechanical-vs-shape classified by diff, not by output |

Upstream's own cases: `test/functional-tests/node-transformers/simplifying-transformers/`.
