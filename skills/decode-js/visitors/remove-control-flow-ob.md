# remove-control-flow-ob.js

Undoes javascript-obfuscator's **BlockStatementControlFlowFlattening** — a
`while(true){ switch(order[idx++]){ case ...} break; }` whose execution order is driven
by a `"|"`-joined index string. Runs on `WhileStatement` **`exit`**.

Match requirements:

- the `while` test is an always-true form: `true`, a prefix `UnaryExpression` (e.g.
  `!![]`), or an empty `ArrayExpression`;
- the body's first statement is a `SwitchStatement` on a `MemberExpression`
  discriminant (`arr[idx]` style) and the second is a `BreakStatement`;
- scanning the `while`'s previous siblings finds both control variables — `arr`, defined
  as `"a|b|c".split("|")` (`init.callee.object` is the `StringLiteral`), and the numeric
  index var. Exactly those two declarations must be found; both are removed.

Reconstruction (`扁平化还原: arr[idx]`): for each token in the order array it starts at that
case index and appends each case's `consequent` statements, walking to the next index,
stopping at a `continue` (loop back) or `return` (which is emitted, then stops).
Out-of-order case labels and stray `break`s are logged but tolerated. The whole `while`
is replaced with the linear body via `replaceInline`.

Consumed by the `sojson`, `sojsonv7`, and `obfuscator` plugins. This is the
**switch/block** flavor of flattening; the object-dispatch flavor is handled by
[parse-control-flow-storage.js](parse-control-flow-storage.md).
