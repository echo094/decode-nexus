# jsconfuser-vm scalar values

## 1. Target

`analyzeScalarValues(wordcode, references, functions, cfg)` is the target-local, parse-only
scalar analysis for the visible numeric-u32 baseline. It reconstructs the canonical wordcode,
reference, function, and CFG
predecessors from copied inputs and returns the immutable
`jsconfuser-vm-scalar-values.v1` operation IR. `diagnoseScalarValues` exposes the same
fail-closed analysis as diagnostics; malformed, stale, unsupported, or schema-inconsistent
inputs decline instead of producing a partial value story.

The target is scalar operation shape and local use/definition information. It is not a
register interpreter, JavaScript emitter, VM runner, or proof of final JavaScript semantics.

## 2. Algorithm

The analyzer first rebuilds the exact canonical wordcode, reference, function, and CFG records from numeric wordcode,
constant references, function/frame metadata, and CFG facts. It requires exact immutable
schema equality with the supplied predecessors, including function ownership, widths,
predecessors, and reachability. It then records one operation row for every reachable or
unreachable B instruction represented by the canonical census; no row may be dropped or
duplicated.

The exact scalar operation set is:

| Family | Operations |
|---|---|
| Load/copy/store | `LOAD_CONST`, `LOAD_INT`, `LOAD_GLOBAL`, `MOVE`, `STORE_GLOBAL` |
| Arithmetic | `ADD`, `SUB`, `MUL`, `DIV`, `MOD`, `EXP` |
| Bitwise/shift | `BAND`, `BOR`, `BXOR`, `SHL`, `SHR`, `USHR` |
| Relation | `LT`, `GT`, `LTE`, `GTE`, `EQ`, `NEQ`, `LOOSE_EQ`, `LOOSE_NEQ` |
| Unary | `UNARY_NEG`, `UNARY_POS`, `UNARY_NOT`, `UNARY_BITNOT`, `TYPEOF`, `VOID`, `TYPEOF_SAFE` |

Each row carries the stable function/PC identity, opcode name and family, typed operands,
original words and width, next PC, destination and input registers, constant/global
references where applicable, use/def information, effect classification, and
`valueSemantics`. Constant knowledge is deliberately narrow: visible `LOAD_CONST` and
`LOAD_INT` literals are represented exactly, `VOID` records its defined result, and
`MOVE` records a typed copy edge without turning dynamic input into a known constant. Other
operations remain dynamic even when their opcode is familiar.

## 3. Implementation

The implementation copies its inputs before reconstruction and freezes the result deeply.
It validates the numeric-u32 container, exact constant/frame references, instruction widths,
owner mapping, CFG reachability, operation census, and the absence of dropped or duplicate
rows. `STORE_GLOBAL` is a mutation with a global reference and no destination; it is not
mistaken for a local scalar definition. Unknown constants, upvalue/`this` operations,
property/collection operations, control transfer, calls/completion, closure creation,
handler state, `PATCH`, and `DEBUGGER` are diagnosed as outside this analysis rather than
invented as scalar facts.

## 4. Upstream Effects

| Producer or consumer | Contract used here or carried forward |
|---|---|
| wordcode/reference/function/CFG predecessors | Supply the exact word, constant, function/frame, predecessor, and CFG facts; these are reconstructed and equality-checked, not trusted by position alone. |
| [property-collections](property-collections.md) | Is a peer target-local analysis; it owns property and collection rows rather than duplicating them here. |
| [call-completion](call-completion.md) and [closure-exception](closure-exception.md) | Consume the same canonical instruction boundary while owning call, completion, closure, and handler facts. |
| [standalone-diagnosis](standalone-diagnosis.md) | Calls the scalar analysis during fresh predecessor preflight before any JavaScript is emitted. |

This analysis exposes typed scalar leaves to the later composition/emission boundary. It does
not rewrite the decoder visitor pipeline or a shared index.

## 5. Known Gaps

Register value-state dataflow, dynamic global resolution, coercion outcomes, upvalues,
receiver state, properties, control semantics, calls, completion, closures, exceptions,
hardening, debugger behavior, and target execution remain intentionally unresolved here.
The result is therefore a structural value-analysis IR, not a claim that every familiar
opcode has been evaluated.

## Source

The stage is implemented by [scalar-values-preflight.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/scalar-values-preflight.js), [analyze-scalar-values.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/analyze-scalar-values.js). The [standalone diagnosis](standalone-diagnosis.md)
composes its result with predecessor records. The encoder contracts are described in
[instruction-set.md](../../../js-confuser-vm/instruction-set.md) and
[container-wordcode.md](../../../js-confuser-vm/container-wordcode.md).

## Fixtures

| Committed fixture or test control | Claim pinned |
|---|---|
| [f-expression-values](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/raw/f-expression-values/encoded.js) | Arithmetic, relation, unary, and literal operation rows with dynamic operands left unknown. |
| [f-global-resolution](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/raw/f-global-resolution/encoded.js) | Global lookup and `typeof` operation roles. |
| [focused-store-global-assignment](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/focused/focused-store-global-assignment/encoded.js) | `STORE_GLOBAL` use/def and mutation classification. |
| [f-short-circuit](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/raw/f-short-circuit/encoded.js) | Short-circuit operation boundaries while retaining dynamic input semantics. |
| [f-instanceof-errors](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/raw/f-instanceof-errors/encoded.js) | `INSTANCEOF` remains a typed operation without inferred runtime outcome. |
| [analyze-scalar-values.test.js](../../../../decoder/decode-js/test/vm/jsconfuser-vm/analyze-scalar-values.test.js) | Synthetic scalar controls for malformed/stale atomic declines, input immutability, and deep freezing. |
