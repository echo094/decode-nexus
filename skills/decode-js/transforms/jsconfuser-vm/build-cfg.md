# Build per-function control flow

## 1. Target

Construct the immutable `jsconfuser-vm-cfg.v1` model for each serialized function, including
basic blocks, normal and exceptional edges, handler-stack states, finite indirect jumps, and call
sites. The result is a parse-time control-flow model; it does not emit JavaScript.

## 2. Algorithm

Validate the wordcode, references, and function ownership contracts, then create handler records
from `TRY_SETUP` and `FINALLY_SETUP`. Solve each function from its entry with an exact handler
stack. `TRY_SETUP` pushes a handler, `FINALLY_SETUP` pushes a finalizer, and `TRY_END` pops the
top record; underflow and stack disagreement decline.

Direct jumps, conditional branches, iterator exits, and ordinary fallthrough become local edges.
Calls have a normal continuation and an exceptional route through the active stack. `RETURN` and
`THROW` route through the innermost applicable finally/handler or terminate by propagation. A
direct terminator does not acquire a synthetic fallthrough.

For `JUMP_REG`, run bounded register dataflow: `LOAD_INT` seeds a singleton PC, `MOVE` copies a
known value, and other writes kill or make the value unknown. Iterate to a finite fixed point;
only distinct instruction-boundary targets in the same function become indirect edges. A missing,
non-finite, non-boundary, or cross-function target declines. Build leaders at entries, handler and
finally targets, throw pads, branch targets, and post-terminator boundaries. Mark irreducible
multiple-entry regions with `fallback: "state-machine"` while preserving their edge model.

## 3. Implementation

The result has schema `jsconfuser-vm-cfg.v1`, `encoding: "numeric-u32"`, word/instruction/function
counts, per-function records, flattened `edges`, `indirectTargets`, `callSites`, ownership, root
frame data, an irreducible-function list, and source metadata naming the consumed schemas and
function entries. Function records include leaders, blocks, edges, indirect jumps, call sites,
handler/finally records, and irreducible-region proofs. Edges retain kind, target/continuation,
route/mode, payload, and handler state before/after.

`diagnoseControlFlow` returns a frozen envelope; `buildControlFlow` and its alias return the frozen
result or `null`. The builder copies input metadata and fails atomically on stale predecessor
state, invalid routing, unresolved indirect control flow, or unbalanced terminal handler state.

## 4. Upstream Effects

CFG construction consumes [read-wordcode.md](read-wordcode.md),
[validate-references.md](validate-references.md), and
[partition-functions.md](partition-functions.md). Its edges and handler states are the control
contract used by [build-call-frames.md](build-call-frames.md), closure-lifetime analysis, and
exception/finally analysis. It preserves serialized function ownership and does not merge
cross-function control flow.

## 5. Known Gaps

- A `JUMP_REG` without a finite, same-function target set is rejected; runtime discovery is not a
  substitute for static evidence.
- Irreducible regions are marked for a state-machine fallback, not structured or emitted here.
- The CFG models the pinned baseline’s handler/call opcodes but does not execute values, infer host
  behavior, or lift the graph into JavaScript.

## Source

The public stage is [build-cfg.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/build-cfg.js). Supporting modules are [build-cfg-wordcode.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/build-cfg-wordcode.js), [build-cfg-preflight.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/build-cfg-preflight.js), [build-cfg-edges.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/build-cfg-edges.js). The [standalone diagnosis](standalone-diagnosis.md) composes this stage.

## Fixtures

| Committed fixture or test control | Claim pinned |
|---|---|
| [f-branching](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/raw/f-branching/encoded.js) | Conditional branch targets and local normal-flow edges. |
| [f-loop-forms](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/raw/f-loop-forms/encoded.js) | Loop backedges, exits, and block leaders. |
| [f-finally-abrupt](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/raw/f-finally-abrupt/encoded.js) | Nested exceptional routes, continuation `JUMP_REG` targets, and handler-stack merges. |
| [build-cfg.test.js](../../../../decoder/decode-js/test/vm/jsconfuser-vm/build-cfg.test.js) | CFG edge coverage, cross-function and unresolved-target declines, frozen results, and a synthetic irreducible graph. The serialized fixtures above do not claim to contain an irreducible region. |
