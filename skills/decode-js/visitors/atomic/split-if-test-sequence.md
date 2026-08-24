# split-if-test-sequence.js

Hoists all but the last expression out of a sequence used as an `if` test (on **`enter`**):
`if ((a, b)) …` becomes `a; if (b) …`. The hoisted expressions still evaluate before the test and
keep their order, so this is safe even where they have side effects the test depends on.

**This is precisely the gap in [split-sequence.js](../split-sequence.md)**, which covers a
sequence in `ExpressionStatement`, `ReturnStatement` and first-`VariableDeclarator` position but
not an `if` test. The two are complementary and are meant to run together.

**Requires the `if` to be in a statement list** (`path.inList`), because the reversal inserts
siblings before it. An `if` that is itself an unbraced branch of another `if` has nowhere to
insert; it is skipped here and becomes eligible once
[lint-if-statement.js](../lint-if-statement.md) has given it a block — which is why those two want
to run in the same loop rather than once each.

Exports a plain visitor as default plus `createSplitIfTestSequence(onSplit)`.

## Source

- [`src/visitor/atomic/split-if-test-sequence.js`](https://github.com/echo094/decode-js/blob/6cacb633ceedf0812fe31f951ba8f41ffb431ca1/src/visitor/atomic/split-if-test-sequence.js)
- Wired as step 5 of
  [normalize-statements](../obfuscator/normalize-statements.md)'s round, after `lint-if-statement`
  and `split-sequence` and before the two `lint-*-if` passes. Both halves of that placement are
  forced by the paragraphs above: it needs `lint-if-statement` to have braced an unbraced branch
  first, and the `lint-*-if` passes want the test already split.

## Fixtures

[`test/visitor/split-if-test-sequence/`](https://github.com/echo094/decode-js/tree/6cacb633ceedf0812fe31f951ba8f41ffb431ca1/test/visitor/split-if-test-sequence),
driven by `split-if-test-sequence.test.js`. **All four are hand-built, so none carries an era** —
the shapes are positional and nothing about them is specific to an encoder or a version.

| Fixture | Claim it pins |
|---|---|
| `simple-valid` | the basic hoist: `if ((a, b))` becomes `a; if (b)`, with the hoisted expression still evaluating first |
| `three-valid` | a sequence longer than two hoists **all but the last** and keeps their order, rather than only the head |
| `not-sequence-invalid` | an ordinary `if` test is left byte-identical — the pass declines rather than rewriting what it does not own |
| `not-in-list-invalid` | the `path.inList` gate: an `if` that is itself an unbraced branch has nowhere to insert siblings, so it is skipped. **This is the case that makes the pairing with `lint-if-statement` load-bearing** rather than stylistic |
