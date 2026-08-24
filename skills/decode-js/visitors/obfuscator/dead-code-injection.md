# Dead-code injection — the reversal with no pass of its own

`obfuscatorx`'s reversal of javascript-obfuscator's
[dead-code injection](../../../javascript-obfuscator/transforms/dead-code-injection.md). **There is
no file for it**, and that is the finding rather than an omission: two shared visitors already in
the pipeline reverse it completely, and writing a matcher for the injected shape would add a pass
whose population they have already taken.

## 1. Target

Remove the injected branch and restore the block that was wrapped, leaving no trace that the wrap
happened. The transform is exactly reversible in the direction that matters — the original block is
carried through unmodified and the clone is discarded — so a correct reversal is byte-recoverable,
unlike the *donation* it performed, which is unrecoverable and is nobody's to undo.

## 2. Algorithm

Fold the test, take the branch. Nothing else.

- [calculate-constant-exp](../calculate-constant-exp.md) reduces the test where it needs reducing.
- [prune-if-branch](../prune-if-branch.md) decides the branch. It evaluates a `BinaryExpression`
  over two literals **itself**, so on this encoder's output it does not in fact need the fold to
  have run first — the emitted test is a comparison of two string literals as soon as the string
  array is decoded.

**Why no dedicated matcher is worth writing.** A pass keyed on the injected shape would have to
recognise all four spellings the encoder draws, and would then do what the generic pair already
does. It could only differ by being *narrower* — declining a constant branch that some other
transform emitted — and narrower is not better here, because taking a statically-decided branch is
correct regardless of who wrote it.

## 3. Implementation

The two visitors are scheduled inside the group documented at
[unflatten-switch-dispatch.md](unflatten-switch-dispatch.md)'s Upstream Effects, and the ordering
constraint is real in both directions:

- the string-array decode **must** precede them, because both test operands are five-character
  strings that the encoder puts in the array — the raw spelling is a pair of accessor calls, not
  literals;
- `prune-if-branch` **must** be in the group rather than after it, because the block un-flattener
  depends on it: injected clones can carry a whole dispatch loop, and those copies are unresolvable
  where they land.

**So `prune-if-branch` does double duty**, and neither role is optional. Removing it from the group
leaves both this transform's residue and flattened blocks the un-flattener rightly declines.

## 4. Upstream Effects

| Earlier pass | What this reversal inherits | Era |
|---|---|---|
| the string-array decode | **a hard dependency.** Until the array is resolved the test is `S(0x1) !== S(0x2)`, which no constant folder can decide | all read eras — the array's *shape* moves at `2.19.0` (`E-sa-array-declaration` → `E-sa-array-self-replacing-fn`), but the concealment of the injected test does not, so what changes is which shape the decode has to match and never whether this pass depends on it |
| [normalize-statements](normalize-statements.md) | the encoder's `Simplifying` stage collapses a single-statement branch, so the emitted `else` is routinely a bare statement rather than a block. Nothing here requires a block, which is what makes that harmless | all read eras, across three of them — `E-simplify-braces-optional`, `-guard-single-body` and `-guard-nested-if` all sit inside the range and each only *widens what is refused*. None stops collapsing a block whose single statement is an ordinary one, so the shape arrives at every era |

**The dependency this pass has on its own encoder-side era axis is the one worth stating
separately, because it is the only place two read eras genuinely differ.** `E-dci-host-*` moves at
`2.15.3`: below it the clone's host restore runs at `Finalizing`, late enough that the identity
check can miss and leave a zero-reference function declaration holding the clone on the dead
branch; at and above it the restore runs at `RenameIdentifiers` and no host survives
([versions.md](../../../javascript-obfuscator/versions.md)). Both eras are in the corpus — the
columns straddle `2.15.2`/`2.15.3` for exactly this reason — and the residue census reads zero on
all four axes at **every** column, so the reversal covers both. What it does not do is treat them
differently, and nothing here needs to.

## 5. Known Gaps

- **A surviving branch owning a `let`/`const` keeps one redundant nesting level.**
  `prune-if-branch` splices a branch's body into the parent statement list only where that cannot
  move a block-scoped binding, so `{ { const … } }` survives. **The shape is reachable against this
  encoder** — the wrapped-block gate rejects only a scope-hoisting function declaration, not a
  lexical one — and was reproduced on a hand-built input, since no corpus input uses `let`/`const`.
  [delete-nested-blocks](../delete-nested-blocks.md) removes it, so closing this is a scheduling
  decision for the integrated pipeline rather than a pass to write.

## Source

No file. The reversal is
[calculate-constant-exp.js](../calculate-constant-exp.md) plus
[prune-if-branch.js](../prune-if-branch.md), both imported unchanged and both scheduled in the
control-flow group. Item 3 says why that position is forced.

## Fixtures

| Claim | Fixture |
|---|---|
| all four test spellings the encoder draws are decided correctly | `test/visitor/prune-if-branch/dci-taken-consequent`, `dci-taken-alternate`, `dci-not-equal-same` |
| a branch owning a lexical declaration keeps its block | `test/visitor/prune-if-branch/lexical-branch-kept` — the gap in item 5, pinned rather than left implicit |
| a real sample carrying the transform decodes end to end | `test/obfuscatorx/2.19.0-dead-code-control` — the **isolated** dead-code profile, so a failure implicates this reversal rather than the whole pipeline. Certified on the residue census and on runtime; migrated from the frozen `obfuscator` entry's suite with its golden re-earned against this one |

**Corpus evidence no fixture replaces:** the dead-code residue census reads zero on every cell of
every version column after the group runs, against a non-zero control taken on
*decoded-but-unpruned* output. That control is deliberately not the raw corpus: on raw input the
test hides behind string-array scope-wrapper spellings no axis can enumerate, so the raw reading is
an undercount and would flatter the result.
