# OpaquePredicates

Source: `transforms/opaquePredicates.ts` + `utils/PredicateGen.ts`

Wraps `if`/ternary/`switch case`/`return` tests with `PREDICATE() && test`, where
`PREDICATE()` is an always-true expression built from a shared predicate object
(numbers/strings/array-length tricks) so it *looks* data-dependent but statically
evaluates to `true`.

## Reversal

Resolve the predicate object's static shape, evaluate `PREDICATE()` to `true`, simplify
`true && X` → `X`.
