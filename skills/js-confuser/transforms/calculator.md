# Calculator

Source: `transforms/calculator.ts`

Numeric `left OP right` (OP ∈ `+ - * /`, both operands numeric literals) becomes
`{ph}_calc("opKey", left, right)` dispatched through a `switch(operator)` function.

## Reversal

Inline the switch to recover the operator, constant-fold.
