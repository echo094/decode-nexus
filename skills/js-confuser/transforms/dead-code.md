# DeadCode

Source: `transforms/deadCode.ts`

Wraps a randomly-chosen dead-code template (see
[dead-code-templates.md](../templates/dead-code-templates.md)) in a never-taken
`if(FALSE_PREDICATE){ {ph}_dead_N() }`, gated by the same `PredicateGen` used by
[OpaquePredicates](opaque-predicates.md) (`!("randomProp" in dummyFunctionName)`,
negated once for the false case).

## Reversal

Once the false predicate is proven statically false (same evaluation as
OpaquePredicates), the whole `if` + helper function is dead and can be deleted outright.
