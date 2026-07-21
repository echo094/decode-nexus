# OpaquePredicates

Source: `transforms/opaquePredicates.ts` + `utils/PredicateGen.ts`

Wraps `if`/ternary/`switch case`/`return` tests with `PREDICATE && test`, where
`PREDICATE` is `!("randomProp" in dummyFunctionName)` — always true, from
[`utils/PredicateGen.ts`](../utils/predicate-gen.md); see that file for exactly how
it's built.

## Reversal

Recognize the `"randomProp" in dummyFunctionName` (or its negation) shape, resolve it
statically to `true` (the dummy function is always an empty, unmodified function
declaration — the property never exists), simplify `true && X` → `X`.
