# PredicateGen.ts

Source: [`utils/PredicateGen.ts`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/utils/PredicateGen.ts)

The single primitive behind every "opaque predicate" in this reference. `PredicateGen`
wraps one `PluginInstance` and lazily inserts one empty dummy function declaration
(`{ph}_dummyFunction`, via `me.getPlaceholder()` + `me.skip()`) at the top of the
Program — created once, reused for every predicate that plugin generates.

- `generateFalseExpression(path)` returns `"randomProp" in dummyFunctionName` — a
  freshly-generated random property name (checked against `Function.prototype` to
  avoid an accidental collision with a real inherited property like `length` or
  `call`), tested with the `in` operator against the always-empty dummy function.
  Since that property can never exist, this is always `false` — but statically
  determining that requires knowing the dummy function's shape never changes.
- `generateTrueExpression(path)` is just `!generateFalseExpression(path)`.

That's the entire mechanism — no object-expression prop tricks, no array-length
checks, no string `charCodeAt` comparisons: one `in` check against a function that's
guaranteed never to gain the property being checked. It's consumed by
[OpaquePredicates](../transforms/opaque-predicates.md) (wraps `if`/ternary/`switch
case`/`return` tests with `PREDICATE && test`) and
[DeadCode](../transforms/dead-code.md) (wraps decoy code in `if(!PREDICATE){ ... }`, i.e.
the negated, always-false form).
