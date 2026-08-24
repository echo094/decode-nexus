# normalize-statements.js

The `obfuscatorx` entry's first pass: undo javascript-obfuscator's `Simplifying` stage by putting
statement-level control flow that was packed into operators back into statements.

## 1. Target

That encoder stage collapses a block's trailing run of statements into one comma expression and
rewrites an `if` whose branches collapsed that way into `&&`, `?:`, or a de-braced branch.
Semantics are untouched; what it destroys is the **statement boundary**. Since every later matcher
navigates by statement boundaries, this runs before anything that reads shape — it is a
precondition for the rest of the pipeline, not a cosmetic finish.

## 2. Algorithm

**This file is scheduling and nothing else.** Every rewrite lives in a single-purpose visitor,
each reusable on its own and each carrying its own safety argument:

| Step | Visitor | What it unlocks |
|---|---|---|
| 1 | [convert-conditional-assign.js](../atomic/convert-conditional-assign.md) | turns value position into statement position |
| 2 | [lint-if-statement.js](../lint-if-statement.md) | gives steps 3–4 a statement list to insert into |
| 3 | [split-sequence.js](../split-sequence.md) | exposes statements packed into a comma expression |
| 4 | [split-variable-declaration.js](../split-variable-declaration.md) | one declaration per declarator — the other half of the same encoder transform step 3 reverses |
| 5 | [split-if-test-sequence.js](../atomic/split-if-test-sequence.md) | the position step 3 does not cover |
| 6 | [lint-conditional-if.js](../atomic/lint-conditional-if.md), [lint-logical-if.js](../atomic/lint-logical-if.md) | the reversals themselves |

**Step 6 is last deliberately**: it is what creates the brace-less branches and fresh statement
positions that steps 2 and 3 of the *next* round act on.

**Step 4 reverses the half of `E-adjacent-merge-pairwise` that step 3 does not.** That encoder
transform fuses adjacent siblings two ways: expression statements into one `SequenceExpression`,
and declarations by concatenating declarators.

**It runs before the string array is decoded.** The
encoder emits string-array wrapper aliases as *extra declarators inside one `var`*
(`var a=W,b=W,foo=a(0x109);`), so splitting is precisely what turns the shape those matchers see
into a different spelling. The detector resolves the same binding graph after the split, so the
normalization remains first.

**What it cannot recover, and this is by construction rather than a gap.** The merge destroys where
the source's own declaration boundaries were: `var a=1,b=2; var c=3,d=4;` and `var a=1,b=2,c=3,d=4;`
merge to the same thing, so splitting yields four single-declarator statements and not the original
two. The output is a normal form, not the source — the same kind of loss as renaming.

**Iteration is required, not tidiness.** The rewrites unlock each other because the encoder nests
its own outputs. `if (t) { x(); if (c) { a(); } else { b(); } }` is emitted as
`t && (x(), c ? a() : b());` — a conditional inside a sequence inside a `&&`. Nothing can reach
that conditional until the `&&` is reversed, which creates a statement; re-bracing then gives that
statement a block; only then can the sequence split; only then is the conditional in statement
position. Each round peels one layer, so the round count is the **nesting depth**, not a constant.
That example settles in three rounds and is the committed fixture.

`maxRounds` (default 8) is a runaway guard rather than a tuning knob. The loop exits as soon as a
round reverses nothing; hitting the cap means pathological nesting or an oscillating rewrite, so
it is reported in the log line rather than passed over.

## 3. Implementation

Returns a stats object — per-rewrite counts, `rounds`, and `cappedOut` — which is what the
`create…(onChange)` factories on the atomic visitors exist to supply. Progress goes through
[`src/utility/logger.js`](../../decode-js.md), not `console.error`; individual declines are not
logged as progress.

## 4. Upstream Effects

**Nothing of ours runs before it**, which is the point — it is scheduled first precisely so that
no later matcher has to tolerate the packed spellings. What it must tolerate is the encoder's own
composition, not another decoder pass's output.

Its own emitted shapes matter to everything after it: it produces block-bodied `if`s and one
statement per expression, which is the shape the rest of the `obfuscatorx` pipeline is written
against. [delete-nested-blocks.js](../delete-nested-blocks.md) removes the redundant blocks that
re-bracing can leave.

## 5. Known Gaps

- **A hand-written statement-level `&&` or ternary is reversed too.** After the position gate,
  what remains is a discarded-value operator expression at statement level, and the decoder cannot
  tell an encoder-produced one from a deliberate one. `c && f();` written by hand comes back as
  `if (c) f();`. This is accepted rather than worked around: the output is semantically identical
  and readable either way, and the deliverable is readable output rather than a faithful
  round-trip. Recorded so it is not mistaken for a defect.
- **A `VariableDeclarator` initializer is never distributed**, so `var r = t ? a : b` stays a
  conditional. Reaching it means hoisting the declaration, which is a scope change.

## Source

- [`src/visitor/obfuscator/normalize-statements.js`](https://github.com/echo094/decode-js/blob/6cacb633ceedf0812fe31f951ba8f41ffb431ca1/src/visitor/obfuscator/normalize-statements.js)
- Wired as the first pass of the `obfuscatorx` plugin. Why that position is forced is item 1.

## Fixtures

| Fixture | Claim it pins |
|---|---|
| `test/visitor/obfuscator/normalize-statements/nested-encoder-output` | real 2.19.0 output for four source shapes that reduce to the same `if`/`else`, each landing the conditional in a different position — statement, mid-sequence, sequence-in-return, and inside a `&&`. Asserts the exact output, that all five sites reverse, that **more than one round** is needed, and that the loop terminates without hitting the cap |
| `test/obfuscatorx/2.19.0-class-logical` | a focused 2.19.0 producer cell whose top-level source `if` is emitted as a statement-level `&&`; the test asserts the positive input-AST population and the entry's exact restored output |

The per-visitor cases live with their own visitors under `test/visitor/<name>/`, split by the
`-valid` / `-invalid` convention — `-invalid` asserting byte-identical output, which is how each
declined position is pinned. Between them they cover the `if`/`while`/`for` test positions, an
arrow concise body, declarator, argument, operand and property positions, and `||`.
