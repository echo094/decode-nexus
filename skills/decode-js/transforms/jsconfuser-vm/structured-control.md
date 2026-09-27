# jsconfuser-vm structured control

## 1. Target

`emitStructuredControl(wordcode, references, functions, cfg, handlers)` is the target-local,
parse-only control-plan analysis. Despite its historical `emit` name, it returns the immutable
`jsconfuser-vm-structured-control.v1` control plan and never emits JavaScript. It reconstructs
exact B/E/H predecessors for the visible numeric-u32 baseline, proves instruction and edge
coverage, and classifies the control graph for a later semantic/emission stage.

## 2. Algorithm

K reconstructs canonical B instructions, function intervals/owners, CFG blocks, successors,
indirect targets, and H handler state from copied inputs. It requires exact immutable equality
with the supplied predecessors and validates every instruction, edge, route, block, and
handler-state transition. Every B instruction receives one typed leaf and every CFG edge gets
one stable edge record; a missing, duplicate, stale, or unsupported record declines atomically.

For each function, the plan is selected from structural facts rather than a source-shape
guess:

| Proven graph fact | Plan |
|---|---|
| Linear fallthrough only | `linear` |
| Conditional branches with one unique nearest reconvergence | Structured conditional |
| Natural loop with dominator/back-edge/explicit exit proof | Structured loop |
| Other reducible shape | Explicit opaque region, retaining exact blocks and edges |
| Required irreducible region | Exact state-machine dispatch over block/edge IDs |

Leaves retain their opcode identity, typed operands, source words, and
`semanticBoundary: later-packet` marks the deferred semantic interpretation. The result also carries block/edge coverage, reachability,
indirect-jump facts, call-site projections, and H state-in/state-out information. It does not
turn a control plan into `if`, `while`, `switch`, `try`, or other JavaScript syntax.

## 3. Implementation

The modules separate shared schema and comparison helpers (`structured-control-contract.js`),
canonical wordcode and function ownership reconstruction (`structured-control-predecessors.js`),
frame/block/edge validation (`structured-control-input.js`), CFG record validation
(`structured-control-cfg.js`), handler-state validation (`structured-control-exceptions.js`), and
plan selection (`emit-structured-control.js`).

The implementation validates canonical wordcode reconstruction, function/frame ownership, block
leaders and successors, fallthrough/conditional/loop edge kinds, `JUMP_REG` targets, H
records/states/merges/transitions/jump checks/completion routes, and exact coverage. It
freezes nested plans and diagnostics and does not mutate the wordcode or predecessor inputs.
Unsupported reducible shapes remain explicit opaque regions; irreducibility is represented by
an exact state machine only when the graph proof requires it. Exception syntax and operation
semantics are intentionally deferred.

## 4. Upstream Effects

| Producer or consumer | Contract used here or carried forward |
|---|---|
| wordcode/CFG/handler predecessors | Supply exact instructions, CFG, function ownership, handler states, routes, and edge facts; this analysis replays and checks these contracts. |
| [property-collections](property-collections.md) and [call-completion](call-completion.md) | Their operation leaves remain later semantic inputs; this analysis carries one typed leaf per instruction without evaluating it. |
| [closure-exception](closure-exception.md) | Owns the richer closure/exception emission record; this analysis consumes handler state for control validation but does not emit handler syntax. |
| [standalone-diagnosis](standalone-diagnosis.md) | Validates the proven structured plan or required irreducible state-machine proof against current wordcode and function ownership. |
| [standalone-decode](standalone-decode.md) | Renders the validated control form during standalone emission. |

K is a plan boundary: it makes later emission deterministic without changing the shared
decoder pipeline.

## 5. Known Gaps

The plan does not express scalar/property/call semantics, closure capture behavior,
completion semantics, exception syntax, target execution, or universal source-level
structured recovery. Reducible but not narrowly provable forms remain opaque by design.
Hardening/PATCH, debugger execution, concealed/encoded input, and earlier eras are not
covered by this target-local plan.

## Source

The public stage is
[emit-structured-control.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/emit-structured-control.js).
It uses
[structured-control-contract.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/structured-control-contract.js),
[structured-control-predecessors.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/structured-control-predecessors.js),
[structured-control-input.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/structured-control-input.js),
[structured-control-cfg.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/structured-control-cfg.js),
and
[structured-control-exceptions.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/structured-control-exceptions.js).
The [standalone diagnosis](standalone-diagnosis.md) composes this stage.

## Fixtures

| Committed fixture or test control | Claim pinned |
|---|---|
| [f-branching](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/raw/f-branching/encoded.js) | Conditional branches with a unique reconvergence. |
| [f-loop-forms](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/raw/f-loop-forms/encoded.js) | Natural-loop proof and explicit loop exits. |
| [f-switch-flow](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/raw/f-switch-flow/encoded.js) | Switch-flow boundaries without claiming JavaScript switch emission. |
| [f-finally-abrupt](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/raw/f-finally-abrupt/encoded.js) | Handler/control boundaries while preserving the deferred exception-syntax boundary. |
| [control-stale-target](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/negative/control-stale-target/encoded.js) | Atomic decline for a graph that violates the structured-control proof. |
| [emit-structured-control.test.js](../../../../decoder/decode-js/test/vm/jsconfuser-vm/emit-structured-control.test.js) | Synthetic linear, conditional, natural-loop, handler-state, stale-input, coverage, freezing, and irreducible-graph controls. The serialized fixtures above do not claim to contain an irreducible region. |
