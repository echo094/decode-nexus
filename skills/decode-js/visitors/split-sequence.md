# split-sequence.js

Splits a `SequenceExpression` (`a, b, c`) into separate statements, but only in parent
positions where that's safe and the container is an array (`listKey`):

- first `VariableDeclarator` (`key === 0`) — insert before the enclosing
  `VariableDeclaration`;
- `ReturnStatement` — insert before it;
- `ExpressionStatement` — insert before it.

`doSplit` pops the last expression, `insertBefore`s each earlier expression as its own
`ExpressionStatement`, then replaces the sequence with that last expression, and
re-crawls scope. Consumed by the `sojson`, `obfuscator`, and `sojsonv7` plugins.
Compare [split-variable-declarator.js](split-variable-declarator.md), which handles a
sequence specifically in a declarator's `init`.
