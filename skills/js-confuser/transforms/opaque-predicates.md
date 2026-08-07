# OpaquePredicates

Source: [`transforms/opaquePredicates.ts`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/opaquePredicates.ts) — `Order.OpaquePredicates = 13`,
plus [`utils/PredicateGen.ts`](../utils/predicate-gen.md).

## 1. Target

Wrap a genuine test (an `if` condition, ternary, `switch case`, or `return` value) with an
always-true predicate ANDed in front of it, so a reader can't immediately tell the extra
clause is inert without proving the dummy-function property check always fails.

## 2. Algorithm

Wraps `if`/ternary/`switch case`/`return` tests with `PREDICATE && test`, where
`PREDICATE` is `!("randomProp" in dummyFunctionName)` — always true, since the dummy
function is a niladic, empty declaration that never gains the checked-for property. See
[`utils/PredicateGen.ts`](../utils/predicate-gen.md) for exactly how the predicate is
built; the same generator backs [DeadCode](dead-code.md)'s own guard.

## 3. Implementation

Nothing beyond the algorithm above and `PredicateGen`'s own mechanics.

## 4. Downstream Effects

None currently documented.

## 5. Known Quirks

**Legacy "Control Object" mechanism (2024-09-07 .. 2024-11-10).** Before `PredicateGen`,
`OpaquePredicates` used a much more elaborate mechanism: a `ControlObject` per `Plugin`
instance ([`2a6eb26`](https://github.com/MichaelXF/js-confuser/commit/2a6eb2643707e14cc2743c89f8b76e3fe9eb2914)),
an IIFE-returned object literal with array/number/string-typed properties, each readable
through a getter with its own dummy runtime check, consumed via
`predicateName[prop]() ? test : fake`-style ternaries. Removed the same day it was
replaced ([`19d74dd`](https://github.com/MichaelXF/js-confuser/commit/19d74ddaa084f234df1c4874efb6f13f842133aa)
immediately followed by
[`fbe3449`](https://github.com/MichaelXF/js-confuser/commit/fbe344911ae4d0450b97c1c3519d33bac1d60eeb)).
Real js-confuser releases published in that ~2-month window can still produce this shape;
it has no relationship to the current `PredicateGen`-based mechanism described above.
