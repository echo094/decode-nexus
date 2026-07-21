# calculate-constant-exp.js

The workhorse constant folder — every heavy plugin (`common`, `sojson`, `obfuscator`,
`sojsonv7`) runs it, usually several times, because unfolding other transforms keeps
exposing new foldable literals. Two visitors, both on **`exit`** (so nested
sub-expressions fold first, bottom-up):

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

Negative numbers matter here: they are `UnaryExpression` nodes, not literals, which is
why `checkLiteral` treats them as a distinct `'negative'` class. Pairs naturally with
[prune-if-branch.js](prune-if-branch.md), which folds the branches this pass makes
constant.
