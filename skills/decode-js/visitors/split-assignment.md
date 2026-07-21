# split-assignment.js

Hoists an `AssignmentExpression` out of an expression position into a preceding
statement, leaving its `left` operand behind as the value. Turns e.g. `if (a = b) {…}`
into `a = b; if (a) {…}`.

`getInsertPath(path)` walks upward from the assignment, allowing only these wrapper
kinds on the way to a statement boundary (`BlockStatement`/`Program`):
`AssignmentExpression`, `CallExpression` (when the path is its `callee`),
`ExpressionStatement`, `IfStatement` (when the path is its `test`), `MemberExpression`,
`VariableDeclarator` (init), and `VariableDeclaration` (first declarator). Several of
these set `needSplit`; if the climb never hits a `needSplit` wrapper (or hits a
disallowed node) it returns `undefined` and nothing happens. On success it
`insertBefore`s the full assignment as an `ExpressionStatement`, replaces the original
with its `left`, and re-crawls scope.

Consumed by the `obfuscator` plugin. Behavior is pinned by
`test/visitor/split-assignment/` (if-test, member, call, and variable fixtures). Related
statement-splitters: [split-sequence.js](split-sequence.md),
[split-variable-declaration.js](split-variable-declaration.md).
