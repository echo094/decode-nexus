# Validate references and frame shape

## 1. Target

Turn the container and parsed wordcode into the immutable
`jsconfuser-vm-references.v1` contract: every constant, register, label, closure descriptor, and
root/frame arithmetic fact must be tied to the accepted numeric stream.

## 2. Algorithm

Revalidate the container’s copied words, pool, scalar roots, canonical maps, and numeric encoding,
then require that parsed instructions reproduce the same word slices, widths, opcode metadata, and
typed operands. Recompute instruction boundaries and require complete consumption.

Build the frame summary from `FRAME_START`, `HEADER_SIZE`, `MAIN_START_PC`, `MAIN_REG_COUNT`, and
the canonical slot map. The root frame begins at `frameStart`; its register base is
`frameStart + headerSize`, its size is `headerSize + mainRegCount`, and its end is the register
window end. For each `MAKE_CLOSURE`, validate descriptor fields, capture-pair shape, parameter and
register counts, and the descriptor’s implied frame size/register offset.

Collect typed references: constant rows must point into the pool and use the accepted conceal key;
global names must be strings; register and upvalue indexes must fit the corresponding frame or
capture count; and every direct label must target an instruction boundary with the correct role.
Keep the serialized `FOR_IN_NEXT` word-operand positions distinct from its semantic view: its
word stream carries the iterator and exit slots in their historical order, while semantic operands
identify the iterator register and exit label.

## 3. Implementation

The result has schema `jsconfuser-vm-references.v1`, `encoding: "numeric-u32"`, `wordCount`,
`instructionCount`, and three reference sections:

- `constants`: pool size, copied values, and constant references;
- `registers`: root/max register counts, max capture count, and register references; and
- `labels`: sorted boundaries and label references with instruction, operand, role, and target.

`frame` contains frame start, header size, canonical slots, main start/register count, root frame
window, and closure descriptors. The validator returns a deeply frozen result or an atomic frozen
diagnosis. A stale predecessor, non-boundary target, out-of-range register/upvalue/constant,
malformed descriptor, or inconsistent word/instruction metadata returns `null` without modifying
either predecessor.

## 4. Upstream Effects

This pass consumes [extract-container.md](extract-container.md) and
[read-wordcode.md](read-wordcode.md). Its boundaries, descriptor table, frame arithmetic, and
typed references are required inputs to [partition-functions.md](partition-functions.md),
[build-cfg.md](build-cfg.md), and all later analyses. It is the last place that combines the
source container’s pool/scalars with parsed instruction identity before ownership is assigned.

## 5. Known Gaps

- The validator checks reference and frame legality; it does not assign instructions to functions,
  solve indirect control flow, model calls, or analyze exception semantics.
- Only the pinned numeric, canonical-map, baseline frame contract is accepted. Encoded or
  randomized/hardened variants require separate evidence.
- A constant reference is structurally validated, not evaluated into a JavaScript value or used to
  infer higher-level program meaning.

## Source

The public stage is [validate-references.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/validate-references.js). Supporting modules are [validate-references-operands.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/validate-references-operands.js), [validate-references-wordcode.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/validate-references-wordcode.js). The [standalone diagnosis](standalone-diagnosis.md) composes this stage.

## Fixtures

| Committed fixture or test control | Claim pinned |
|---|---|
| [f-literals-order](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/raw/f-literals-order/encoded.js) | Root frame arithmetic and references in the accepted numeric baseline. |
| [f-closures-state](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/raw/f-closures-state/encoded.js) | Closure descriptor fields and capture/register bounds. |
| [f-finally-abrupt](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/raw/f-finally-abrupt/encoded.js) | Handler and finally label roles at instruction boundaries. |
| [reference-invalid-constant](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/negative/reference-invalid-constant/encoded.js), [reference-invalid-register](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/negative/reference-invalid-register/encoded.js), and [reference-invalid-label](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/negative/reference-invalid-label/encoded.js) | Atomic decline for out-of-range pool, frame, or label references. |
| [closure-invalid-capture](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/negative/closure-invalid-capture/encoded.js) | Atomic decline for an invalid capture descriptor. |
| [validate-references.test.js](../../../../decoder/decode-js/test/vm/jsconfuser-vm/validate-references.test.js) | Predecessor agreement, synthetic range/boundary and descriptor declines, and frozen inputs/results. |
