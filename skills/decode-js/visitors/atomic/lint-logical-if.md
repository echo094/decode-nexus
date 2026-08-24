# lint-logical-if.js

Reverses a short-circuit used as a statement (on **`exit`**): `test && body;` becomes
`if (test) body;`. Obfuscators emit this to pack a single-branch `if` onto one line.

**The position gate is the whole safety argument.** The parent must be the `ExpressionStatement`
*and* the node must be its entire expression. That one test excludes every position where the
operator carries a value rather than a branch — an `if`/`while`/`for` test, an arrow function's
concise body, a declarator initializer, a call argument, an operand of an enclosing operator. At
statement level the operator's value is discarded either way, which is what makes the rewrite
semantics-preserving in both directions.

**Only the outermost `&&` of a chain qualifies**, and that is what makes a chain survive rather
than shred. `if (c && d) { f(); }` is emitted as `c && d && f();`, which parses as
`(c && d) && f()`; reversing the outermost alone recovers the original test. A nested `&&`'s
parent is the `LogicalExpression` above it, so it is never a candidate.

**`||` is deliberately not handled.** It has no equivalent single-branch `if` — `a || b` runs `b`
when `a` is *falsy*, so the reversal would have to introduce a negated test, which is a shape no
encoder emitted.

**Declines, never stops.** A site failing the gate is skipped and traversal continues.
`path.stop()` would halt the entire traversal rather than the subtree, and on obfuscated input
the declined sites outnumber the matched ones by roughly two to one.

Exports a plain visitor as default plus `createLintLogicalIf(onReverse)` for a caller that needs
to know whether it fired — which [normalize-statements.js](../obfuscator/normalize-statements.md)
does, since its fixpoint has to decide whether to run another round. Runs alongside
[lint-conditional-if.js](lint-conditional-if.md), whose gate is the same shape.

## Source

- [`src/visitor/atomic/lint-logical-if.js`](https://github.com/echo094/decode-js/blob/6cacb633ceedf0812fe31f951ba8f41ffb431ca1/src/visitor/atomic/lint-logical-if.js)
- Wired **last** in [normalize-statements](../obfuscator/normalize-statements.md)'s round, beside
  `lint-conditional-if`. Both report through their `create*` channel because the fixpoint decides
  on another round from whether either fired — which is why the factory form exists at all.

## Fixtures

[`test/visitor/lint-logical-if/`](https://github.com/echo094/decode-js/tree/6cacb633ceedf0812fe31f951ba8f41ffb431ca1/test/visitor/lint-logical-if),
driven by `lint-logical-if.test.js`. **All hand-built, so none carries an era** — the gate is
positional and no part of it is version-specific. **Six of the eight are declines**, which is the
right ratio for a pass whose whole safety argument is the gate: a table of accepting cases would
say nothing about the positions that must be refused.

| Fixture | Claim it pins |
|---|---|
| `statement-valid` | the reversal itself: `test && body;` becomes `if (test) body;` |
| `chain-valid` | **only the outermost `&&` qualifies**, so `c && d && f();` recovers `if (c && d) f();` rather than shredding into nested `if`s |
| `if-test-invalid`, `while-test-invalid`, `for-test-invalid` | the operator carries a value in each of the three test positions, and is refused in all three |
| `arrow-body-invalid` | a concise arrow body reads statement-like and is an expression — the position most likely to be got wrong |
| `declarator-invalid` | an initializer is a value position |
| `or-invalid` | `\|\|` is refused outright, since its reversal would need a negated test — a shape no encoder emitted |

**No committed case is harvested from real encoder output, but the corpus now reaches this pass.**
Its fourth input carries a statement-level `&&` and an `if` the encoder collapses into a second
one, so the `logical-statement` residue axis reads non-zero on the inputs at every column and zero
on decoded output — where before the append it read zero on *both*, which is indistinguishable
from a clean decode. So a regression here would now be caught by a corpus run, though still not by
the suite.
