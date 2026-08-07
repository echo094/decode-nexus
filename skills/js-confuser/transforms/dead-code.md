# DeadCode

Source: [`transforms/deadCode.ts`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/deadCode.ts) — `Order.DeadCode = 8`.

## 1. Target

Insert dead-code camouflage: wrap a randomly-chosen unreachable code template in a
never-taken `if` guard, so the guard's predicate looks like it could matter even though it
can never evaluate true — padding the program with plausible-looking but inert branches.

## 2. Algorithm

Wraps a randomly-chosen dead-code template (see
[dead-code-templates.md](../templates/dead-code-templates.md)) in a never-taken
`if(FALSE_PREDICATE){ {ph}_dead_N() }`, gated by the same `PredicateGen` used by
[OpaquePredicates](opaque-predicates.md) (`!("randomProp" in dummyFunctionName)`, negated
once for the false case).

## 3. Implementation

Nothing beyond the algorithm above — the template selection and predicate mechanics
themselves live in [dead-code-templates.md](../templates/dead-code-templates.md) and
[predicate-gen.md](../utils/predicate-gen.md), shared with `OpaquePredicates`.

## 4. Downstream Effects

- **`OpaquePredicates` (Order 13)** wraps *every* `if` statement it visits, including this
  transform's own inserted guard, since `Order.DeadCode = 8` runs before it — so real
  combined output can show `if (!(x1 in dummy1) && (x2 in dummy2)) { deadFn() }` (a
  `LogicalExpression` test) instead of the bare `BinaryExpression` this transform emits on
  its own.
- **`ControlFlowFlattening` (Order 24)** flattens whatever this transform injected, same
  as any other code in an eligible function. Some of the dead-code templates guard their
  argument with a `throw`, which CFF's own Stage 1 has no special handling for — it's
  just an ordinary statement that happens to end a block. See
  [control-flow-flattening.md](control-flow-flattening.md)'s Stage 1.

## 5. Known Quirks

None currently documented.
