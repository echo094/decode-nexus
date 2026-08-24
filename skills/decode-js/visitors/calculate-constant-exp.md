# calculate-constant-exp.js

The workhorse constant folder — every heavy plugin (`common`, `sojson`, `obfuscator`,
`sojsonv7`, `jsconfuser`) runs it, usually several times, because unfolding other
transforms keeps exposing new foldable literals. Three visitors, all on **`exit`** (so
nested sub-expressions fold first, bottom-up):

- **`BinaryExpression`** — folds only when both `left` and `right` pass `checkLiteral`.
  `checkLiteral(node)` classifies a node as `'positive'` (a `NumericLiteral`),
  `'literal'` (any other literal), `'negative'` (a `UnaryExpression` `-` over a
  `NumericLiteral`), or `false`. When both sides qualify it evaluates
  `eval(generator(node).code)` with the **host `eval`**. A string result is rebuilt with
  `t.stringLiteral(ret)` — *not* `replaceWithSourceString`, because a source string like
  `"ab"` would otherwise re-parse as the identifier `ab`; everything else uses
  `replaceWithSourceString(ret)`.
- **`UnaryExpression`** — operator-specific: `!` folds an empty `ArrayExpression` to
  `false` and any literal to a boolean; `-` folds a `'negative'`; `+` and `~` fold any
  number; `void` over a literal becomes the identifier `undefined`; `typeof` over a
  literal becomes its type string. Non-constant cases (e.g. `typeof window`) are left
  alone even though they'd evaluate.

- **`LogicalExpression`** (added 2026-07-22, for
  [jsconfuser/opaque-predicates.js](jsconfuser/opaque-predicates.md)) — short-circuits
  `&&`/`||` when the **left** side is a simple literal (`checkSimpleLiteral`: string,
  numeric, boolean, or null - a narrower check than `checkLiteral` above, since
  short-circuit truthiness only needs a plain `.value` read, not the negative-number
  special case). `true && x` / `false || x` -> `x`; `false && x` / `true || x` -> the
  literal itself (preserving whichever falsy/truthy value it actually was, not forcing
  a `BooleanLiteral`). The right side is substituted as-is whether or not it's itself
  constant - unlike the two folds above, this one only ever proves *half* the
  expression, by design.

Negative numbers matter here: they are `UnaryExpression` nodes, not literals, which is
why `checkLiteral` treats them as a distinct `'negative'` class. Pairs naturally with
[prune-if-branch.js](prune-if-branch.md), which folds the branches this pass makes
constant.

## Source

- [`src/visitor/calculate-constant-exp.js`](https://github.com/echo094/decode-js/blob/6cacb633ceedf0812fe31f951ba8f41ffb431ca1/src/visitor/calculate-constant-exp.js)
- Consumed by five plugins. In `obfuscatorx` it occupies **three** slots per round: one inside
  [normalize-converting](obfuscator/normalize-converting.md), and two in the plugin's fixpoint
  group either side of
  [obfuscator/inline-control-flow-storage](obfuscator/inline-control-flow-storage.md) — because
  inlining a wrapper body produces `a + b` over operands that only just became constant.
- **The plugin-level slots are measurably redundant against this encoder** and are kept anyway;
  normalize-converting's item 4 has the measurement and the reason.

## Fixtures

[`test/visitor/calculate-constant-exp/`](https://github.com/echo094/decode-js/tree/6cacb633ceedf0812fe31f951ba8f41ffb431ca1/test/visitor/calculate-constant-exp),
driven by `calculate-constant-exp.test.js`. **All hand-built, so none carries an era.**

| Fixture | Claim it pins |
|---|---|
| `and-true`, `and-false` | `&&` short-circuits on a literal left side in both directions — and the falsy case yields **the literal itself**, not a coerced `false` |
| `or-true`, `or-false` | the same for `\|\|` |
| `non-literal-left` | a non-literal left side is left alone: this fold proves only half the expression by design |

**Five cases for three visitors, and the two uncovered ones are the older and heavier.** Every
committed case is a `LogicalExpression`, added with that visitor in 2026-07. The
`BinaryExpression` and `UnaryExpression` folds — which is where the `checkLiteral` classes, the
host-`eval` call, and the `t.stringLiteral` special case that stops `"ab"` re-parsing as an
identifier all live — have **no case at all**. They are exercised transitively by every plugin's
end-to-end fixtures, so a regression would surface somewhere; it would not surface *here*, and the
`'negative'` class in particular is the kind of distinction that reads as removable.
