# lint-if-statement.js

Normalizes `IfStatement` shape (on **`exit`**): if `consequent` or `alternate` is not a
`BlockStatement`, it wraps the bare statement in `t.blockStatement([...])` and rebuilds
the node via `t.ifStatement(test, consequent, alternate)`. No-ops when both branches are
already blocks.

Guarantees downstream passes always see block-bodied `if`s, so statement insertion /
removal inside branches is uniform. Consumed by the `obfuscator` plugin (which also
re-runs the same normalization as a standalone step in its `purifyCode`). Compare
[delete-nested-blocks.js](delete-nested-blocks.md), which removes the redundant blocks
this pass can introduce.
