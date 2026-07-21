# node.ts

Small AST-node construction/cloning helpers, used across the transforms that build a
lot of synthetic literals and reuse the same subtree at multiple insertion points:

- **`createLiteral(value)`** — builds the right `t.Node` for a JS primitive:
  `t.nullLiteral()`, `t.identifier("undefined")`, or `t.stringLiteral`/`numericLiteral`/
  `t.booleanLiteral` depending on `typeof value`. Used by
  [DuplicateLiteralsRemoval](../transforms/duplicate-literals-removal.md) (building the
  hoisted literal-pool array) and [VariableMasking](../transforms/variable-masking.md)
  (masked property values).
- **`numericLiteral(value)`** — handles negative numbers, which Babel's own
  `t.numericLiteral` can't represent directly: returns a plain `t.numericLiteral(value)`
  for `value >= 0`, or `t.unaryExpression("-", t.numericLiteral(-value))` (i.e. `-N` as
  an AST-level unary minus) for negatives. The most widely used helper in this file —
  every numeric AST literal in
  [ControlFlowFlattening](../transforms/control-flow-flattening.md) (state values,
  which range negative-to-positive via [IntGen](int-gen.md)),
  [Dispatcher](../transforms/dispatcher.md),
  [DuplicateLiteralsRemoval](../transforms/duplicate-literals-removal.md),
  [StringConcealing](../transforms/string-concealing.md), and
  [RGF](../transforms/rgf.md) goes through this function rather than raw
  `t.numericLiteral`.
- **`deepClone(node)`** — recursively clones a node (or array of nodes), including
  non-enumerable/symbol-keyed properties added via `Object.getOwnPropertyNames`/
  `getOwnPropertySymbols` (so `NodeSymbol` flags like `SKIP`/`UNSAFE` on a cloned
  subtree survive the clone, as long as their values aren't themselves objects — the
  symbol-copy branch skips object-typed values to avoid infinite recursion). Necessary
  because Babel `NodePath.replaceWith`/insertion APIs can't reuse the same node object
  at two locations in the AST — every "reference this same variable/discriminant again
  elsewhere" pattern in
  [ControlFlowFlattening](../transforms/control-flow-flattening.md) (by far the
  heaviest consumer) goes through `deepClone` first.
