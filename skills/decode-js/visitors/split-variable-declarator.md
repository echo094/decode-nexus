# split-variable-declarator.js

Splits a single `VariableDeclarator` whose `init` is a `SequenceExpression`, lifting the
leading expressions out as statements and keeping the last as the initializer:

```javascript
// From
var aa = (a, b);
// To
a;
var aa = b;
```

Requires the declarator's container to be an array (`listKey`). Pops the last expression,
`insertBefore`s each earlier one as an `ExpressionStatement` on the parent declaration,
replaces `init` with the last expression, re-crawls scope.

**Not wired into any plugin pipeline at this pin** — the only importer is its own test,
`test/visitor/split-variable-declarator.test.js`. Contrast
[split-variable-declaration.js](split-variable-declaration.md) (the multi-declarator
splitter, which *is* used by `obfuscator`) and [split-sequence.js](split-sequence.md)
(sequences in other positions).
