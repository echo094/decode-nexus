# AstScrambler

Source: `transforms/astScrambler.ts`

Consecutive `ExpressionStatement`s in a block get merged into one comma-separated
`{ph}_ast(expr1, expr2, ...)` call (a function that immediately no-ops itself after first
call). Purely a statement-boundary obfuscation.

## Reversal

Inline the call back into a `SequenceExpression`/separate statements.
