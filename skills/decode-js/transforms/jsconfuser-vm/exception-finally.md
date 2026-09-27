# Analyze exception and finally state

## 1. Target

Produce the immutable `jsconfuser-vm-exception-finally.v1` model of handler/finally records,
per-instruction handler state, completion routes, finite continuation jumps, and CFG/call-frame
cross-checks for the pinned baseline.

## 2. Algorithm

Validate wordcode, references, function ownership, CFG, and call frames as exact predecessor
contracts. Reconstruct a handler record for each `TRY_SETUP` and `FINALLY_SETUP`. A handler stores
its handler PC and exception register; a finally record stores finalizer PC, continuation register,
payload register, and throw-pad PC. Every target is a local instruction boundary and every register
fits its function.

Walk each function from its entry with an exact stack state. `TRY_SETUP` and `FINALLY_SETUP` push
records; `TRY_END` pops the top record and declines on underflow. Normal branches must not bypass an
active finally. Calls produce normal and exceptional routes. Returns route through the innermost
finally or propagate; throws route to the active handler/finally or propagate. Finally routes carry
the pending value/exception and continuation/throw-pad payload, and `JUMP_REG` continuations must
use a finite, same-function target set and the finalizer’s continuation register.

At every reachable merge, incoming handler stacks must agree exactly. Terminal edges must have an
empty stack, all reachable edges must agree with CFG metadata, and all call exceptional routes,
return records, throw records, and completion routes must match the call-frame model. Preserve
unreachable serialized instruction records in the result with null state rather than inventing a
route.

## 3. Implementation

The result has schema `jsconfuser-vm-exception-finally.v1`, `encoding: "numeric-u32"`, counts,
function records, flattened `handlerRecords`, `finallyRecords`, `instructionStates`, `edgeStates`,
`merges`, `jumpRegChecks`, `transitions`, `completionRoutes`, a call-frame route count, and source
schema metadata. State views expose both the complete handler stack and its finally-only projection.
Routes preserve kind, source/target, normal/exceptional/propagating route, call site,
continuation, payload, and before/after state.

`diagnoseExceptionFinally` returns a deep-frozen envelope. `analyzeExceptionFinally` and its aliases
return the frozen result or `null`; cross-function targets, invalid handler routing, stale
predecessor state, unresolved continuation jumps, stack underflow, and unbalanced terminal stacks
decline atomically.

## 4. Upstream Effects

This analysis consumes [read-wordcode.md](read-wordcode.md),
[validate-references.md](validate-references.md),
[partition-functions.md](partition-functions.md), [build-cfg.md](build-cfg.md), and
[build-call-frames.md](build-call-frames.md). It is the final pre-emission control/completion shape used by
the standalone decoder before later structured-control or emission checks; it does not replace the
CFG or call-frame contracts, and instead verifies them.

## 5. Known Gaps

- The result is a state analysis, not execution or structured JavaScript emission. It does not
  infer behavior of arbitrary host exceptions or missing dynamic targets.
- Unproven or non-finite continuation values are rejected rather than approximated.
- Optional handler-table, dispatcher, self-modifying, randomized, and other hardening variants are
  outside this pinned baseline shape.

## Source

The public stage is [analyze-exception-finally.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/analyze-exception-finally.js). Supporting modules are [exception-finally-input.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/exception-finally-input.js), [exception-finally-control.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/exception-finally-control.js), [exception-finally-routes.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/exception-finally-routes.js). The [standalone diagnosis](standalone-diagnosis.md) composes this stage.

## Fixtures

| Committed fixture | Claim pinned |
|---|---|
| [f-finally-abrupt](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/raw/f-finally-abrupt/encoded.js) | Nested handler/finally records, normal and exceptional routes, continuation jumps, and merge states. |
| [f-throw-catch](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/raw/f-throw-catch/encoded.js) | Handler-only throw/catch routing and propagation. |
| [focused-call-method-spread](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/focused/focused-call-method-spread/encoded.js) | No-handler control case for call completion and empty handler state. |
