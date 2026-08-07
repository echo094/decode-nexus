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
the removed branch. Consumed by the `obfuscator`, `sojson`, `sojsonv7` and `jsconfuser`
plugins, typically right after
[calculate-constant-exp.js](calculate-constant-exp.md) has made the tests constant.

**The surviving branch is spliced, not planted whole** (`replaceWithBranch`). A branch is
usually a `BlockStatement`, and putting that block where the `IfStatement` stood leaves a
bare `{ ... }` in the parent statement list. It changes nothing about execution, which is
why it survived unnoticed, but it changes the *shape a later matcher reads*: a pass keying
on a statement list's last element sees a `BlockStatement` where it required something
else. So the block's statements are spliced into the list instead, and the block is kept
only where it is load-bearing — when the path is not in a statement list, or when the block
owns a `let`/`const`/`class`/`function` declaration that would change meaning if relocated.
An empty surviving block removes the statement outright.

[delete-nested-blocks.js](delete-nested-blocks.md) performs the same splice as a **cleanup**
pass and is an alternative for a pipeline that already schedules it. Doing it here is
preferred where both are available: it stops the shape from being created rather than
removing it afterwards, and it costs no scope crawl (that pass re-crawls the parent scope
per block to test for binding collisions).
