# prune-if-branch.js

Folds an `IfStatement` or `ConditionalExpression` whose test is statically constant.
The test qualifies when it is a `StringLiteral`/`NumericLiteral`/`BooleanLiteral`, or a
`BinaryExpression` whose `left` and `right` are both such literals. Truthiness is
computed with the host `eval` over JSON-stringified operands
(`eval(JSON.stringify(left) + operator + JSON.stringify(right))`, or
`eval(JSON.stringify(value))` for a bare literal).

`clear(path, toggle)` then keeps the winning branch: replace with `consequent` when
truthy; when falsy, replace with `alternate` or `remove()` if there is none. The header
warns the code must be **reloaded** afterward so Babel's reference/binding info reflects
the removed branch. Consumed by the `obfuscator`, `sojson`, and `sojsonv7` plugins,
typically right after [calculate-constant-exp.js](calculate-constant-exp.md) has made the
tests constant.
