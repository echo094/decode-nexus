# Block-statement control-flow flattening

The `ControlFlowFlattening` (4) transformer that takes a block's statements out of source order and
drives them from a data table: `BlockStatementControlFlowTransformer`, gated on
`controlFlowFlattening` and its threshold.

Its emitted shape is one era across the whole of phase 1 and beyond —
[`E-cff-block-switch-dispatch`](../versions.md). The transformer file's own content moves once in
range, at `2.13.0`, and that change is an import path.

## 1. Target

**Break the correspondence between reading order and execution order.** Every other transform in
this encoder hides *what* a statement says; this one hides *when* it runs. The statements survive
verbatim — they are moved, never rewritten — so what is destroyed is only the order, and the order
is then restored at runtime from a string.

The protection is worth naming precisely because it is narrow: a reader who recovers the controller
string recovers the order exactly. There is no arithmetic on it, no key, and no state carried
between cases.

## 2. Algorithm

For a block of `n` statements:

1. `originalKeys = [0 … n-1]`.
2. `shuffledKeys = shuffle(originalKeys)` — a Fisher-Yates shuffle over a copy.
3. `originalKeysIndexesInShuffledArray[k] = shuffledKeys.indexOf(k)` — for each *original*
   statement `k`, which switch case now holds it.
4. Emit a replacement block: a controller array, an index, and a `while` loop whose `switch`
   dispatches on the next controller element.

```js
{
    const C = '<order>'['split']('|');   // order = originalKeysIndexesInShuffledArray, joined
    let I = 0;
    while (true) {
        switch (C[I++]) {
        case '0': <statement shuffledKeys[0]>; continue;
        case '1': <statement shuffledKeys[1]>; continue;
        …
        }
        break;
    }
}
```

**Case `i` holds original statement `shuffledKeys[i]`; controller position `k` names the case that
holds original statement `k`.** The two are inverse permutations of each other, and only the second
is emitted.

**Termination is by running off the end of the controller.** Once `I` passes the last element,
`C[I++]` is `undefined`, no case test matches, the `switch` falls through, and the `break` after it
leaves the loop. The `break` is therefore reached exactly once per execution and is not a case
consequent.

**A `return` statement ends its case without a `continue`**, because the function has already
returned; every other statement's case ends with one. Those are the only two consequent shapes.

**It runs on `leave`, so blocks are flattened innermost-first** — which is what makes nesting
possible (item 4).

## 3. Implementation

| Element | Detail |
|---|---|
| visitor | `leave` on any `BlockStatement` that has a parent, in the `ControlFlowFlattening` stage |
| threshold | `randomGenerator.getMathRandom() > controlFlowFlatteningThreshold` returns the block untouched, per block |
| size gate | `blockStatementNode.body.length <= 4` refuses — so a flattened block always has **at least five** cases |
| controller name / index name | `randomGenerator.getRandomString(6)` each, independent |
| separator | `StringSeparator.VerticalLine`, `'\|'`, used both in the joined literal and as the `split` argument |
| case test | `String(index)` — a **string** literal, matching the strings `split` produces |
| declaration kinds | `const` for the controller, `let` for the index, **subject to the rewrite in item 4** |

**The prohibition scan is over the whole subtree, and it is what usually refuses a block.**
`canTransformBlockStatementNode` walks the block with `estraverse.traverse` and sets `canTransform =
false` on any of:

- a `FunctionDeclaration`
- a `BreakStatement` or `ContinueStatement`
- a `VariableDeclaration` whose kind is `let` or `const`
- a `ClassDeclaration`

**Only `WhileStatement` subtrees are skipped** (`VisitorOption.Skip`). So a `break` or `continue`
that belongs to a `while` is invisible to the scan, while the same statement inside a `for`,
`do-while` or `switch` refuses the entire block. Measured at `2.19.0` by encoding six one-statement
variants of the same five-statement function: `while`-with-`continue` flattens, and each of
`for`-with-`continue`, `do-while`-with-`break`, `switch`-with-`break` and a nested function
declaration refuses.

**The scan descends into nested functions**, so a `let` anywhere inside a nested arrow or function
expression also refuses the enclosing block. Combined with the `let`/`const` rule this means a block
written in modern style is essentially never flattened — verified by encoding the same function body
twice, once with `var` and once with `const`: the `var` spelling produces two flattened blocks and
the `const` spelling produces none.

## 4. Downstream Effects

### The controller literal rarely survives as a literal

| Later pass | What it does to this transform's output | Era |
|---|---|---|
| `ControlFlowFlattening` (4), the **sibling** `FunctionControlFlowTransformer` | shares the stage's traversal, and its `StringLiteralControlFlowReplacer` takes any string literal of length ≥ 3 inside a function body. The controller string qualifies, so it is moved into that transformer's storage object and the declaration becomes `const C = S['key']['split']('\|')` — see [control-flow-expression-storage.md](control-flow-expression-storage.md) | all in range |
| `Converting` (6) | `while (true)` re-spells as `while (!![])`; `splitStrings` can break the controller literal into a `+` chain; `numbersToExpressions` rewrites the `0` initialiser | all in range |
| `StringArray` (8) | conceals the controller string *if it is still a literal* — i.e. when the block is not inside a function and the sibling transformer never reached it | all in range |
| `RenameIdentifiers` (7) | renames the controller and index bindings | all in range |
| `Simplifying` (9) | merges the two prelude declarations into one declaration with two declarators, once they share a kind | `E-adjacent-merge-pairwise` |
| `Finalizing` (10) | escape sequences re-spell the case tests, so `case '0'` can arrive as `case '\x30'` | `E-escape-*` |
| `Finalizing` (10) | directive placement prepends a clone of a recorded directive. Through `5.1.0` its recursive unlink removes the same statement identity from a case; from `5.2.0` its direct-body filter leaves that nested original behind | `E-directive-rehoist-no-residual` → `E-directive-rehoist-nested-residual` |

**The case tests are the one part that reliably survives**: at one character they are below
`StringLiteralControlFlowReplacer`'s length-3 floor and below the string array's own threshold, so
they stay literal at every version and option profile in the corpus.

### The declaration kind is decided by the input program, not by this transform

`AbstractCustomNode.getNode()` passes every custom node's structure through
`CustomCodeHelperFormatter.formatStructure()`, which rewrites **every** `VariableDeclaration.kind`
to `var` when `PrevailingKindOfVariablesAnalyzer` reports the input program's most-occurring kind as
`var` — defaulting to `var` when the input declares nothing at all. The rewrite is one-directional:
nothing ever becomes `let` or `const`.

| Spelling | When | Producing pass |
|---|---|---|
| `const C = …; let I = 0;` | the input's prevailing kind is not `var` | this transform's own structure, unrewritten |
| `var C = …; var I = 0;` | prevailing kind is `var`, or the input has no declarations | `CustomCodeHelperFormatter` |
| `var C = …, I = 0;` | as above **and** `simplify` on | `VariableDeclarationsMergeTransformer`, `Simplifying` (9) |

Both kind spellings are reachable and both were built at `2.19.0`: an input of seven top-level
`const` declarations around a `var`-bodied function emits the `const`/`let` prelude, and the same
function in a `var`-written program emits the `var` one. The mechanism is not this transform's and
is not confined to it — the same rewrite reaches the string-array helpers
([string-array-scope-calls-wrapper.md](string-array-scope-calls-wrapper.md)).

### Flattened blocks nest

Because the transform runs on `leave`, an inner block is flattened before its enclosing block is
tested. Whether the enclosing block can *then* be flattened turns on the kind rewrite above:

- **prevailing kind `var`** — the emitted prelude is two `var` declarations, which are not
  prohibited, and every `break`/`continue` the flattened body contains sits inside the `while` that
  the prohibition scan skips. So the enclosing block is still eligible, and nesting happens.
- **prevailing kind `const`/`let`** — the prelude is `const`/`let`, which the scan does prohibit, so
  the enclosing block is refused. In practice this branch is moot, since such a program's own
  declarations would already have refused both blocks.

Nesting is not a corner case: a census over the frozen corpus (`u5-shape.mjs`, 2026-08-14) finds a
substantial minority of flattened blocks lying inside another flattened block's case consequent.

## 5. Known Quirks

- **The prohibition scan is over-conservative in one direction and under-conservative in another,
  for the same reason.** Skipping `WhileStatement` subtrees is meant to ignore a `break`/`continue`
  that already has its own loop; it also ignores a `let`, `const`, `ClassDeclaration` or
  `FunctionDeclaration` inside a `while` body, which are harmless to relocate anyway because the
  whole `while` moves as one statement. The cost lands on `for`, `do-while` and `switch`, which are
  not skipped and whose own `break`/`continue` refuses the block.
- **The size gate is `<= 4`, not `< 4`.** A four-statement block is refused; five is the minimum.
- **`shuffle` can return the identity permutation**, so a flattened block whose controller reads
  `'0|1|2|3|4'` is a legitimate output and not evidence of a partial transform.
- **The transform reorders but never rewrites.** A statement lands in a case consequent as the same
  node object; nothing about the statement's own shape records that it was moved.

## Source

- [`BlockStatementControlFlowTransformer.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/node-transformers/control-flow-transformers/BlockStatementControlFlowTransformer.ts)
- [`BlockStatementControlFlowFlatteningNode.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/custom-nodes/control-flow-flattening-nodes/BlockStatementControlFlowFlatteningNode.ts)
- [`ArrayUtils.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/utils/ArrayUtils.ts) — `createWithRange`, `shuffle`
- [`CustomCodeHelperFormatter.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/custom-code-helpers/CustomCodeHelperFormatter.ts) and
  [`PrevailingKindOfVariablesAnalyzer.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/analyzers/prevailing-kind-of-variables-analyzer/PrevailingKindOfVariablesAnalyzer.ts) — the kind rewrite

Read at `2.19.0`, the spine and the era's SHA. The custom node's content is unchanged from `1.8.1`
through `4.2.0`; the transformer's from `0.26.0` through `2.12.0` and again from `2.13.0`, the
boundary being an `estraverse` import path.

## Fixtures

The corpus is the evidence for every claim marked measured; this encoder package has no separate
committed fixture for the transform.

| Claim | What checks it | Era |
|---|---|---|
| the emitted block is `while` → `[switch, break]`, discriminant `C[I++]` | the shape census over the documented corpus matrix | `E-cff-block-switch-dispatch` |
| case tests are `'0' … 'n-1'` in ascending order, no `default` | same census | same |
| every consequent is `[stmt, continue]` or a lone `return` | same census | same |
| at least five cases | same census | same |
| the controller literal is not directly readable in encoder output | same census — every block's controller arrives as a member expression or a `+` chain | same |
| flattened blocks nest | same census | same |
| only `while` subtrees escape the prohibition scan | six one-variant encodes at `2.19.0` | same |
| the `const`/`let` prelude is reachable | one `const`-prevailing encode at `2.19.0` | same |
| the shape holds `1.8.1 – 4.2.0` | per-tag content hash over 205 release tags | same |
| moving the original directive identity into a case exposes the `5.2.0` shallow-unlink boundary | `directives__cff` at the adjacent frozen columns; [directive-placement.md](directive-placement.md) owns the era | `E-directive-rehoist-*` |

**Two gaps, both in the corpus rather than in the reading.** No corpus input is `const`/`let`-written,
so every corpus block carries the `var` prelude and the `const`/`let` row is verified only by a
purpose-built encode. And no corpus input places a five-statement block outside a function, so the
case where the controller literal reaches `StringArray` (8) as a literal is unmeasured on the corpus
— it was built by hand at `2.19.0` to confirm it exists.
