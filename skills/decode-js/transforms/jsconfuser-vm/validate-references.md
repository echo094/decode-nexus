# Validate references and frame shape

## 1. Target

Relate parsed operand indexes to the admitted pool, instruction boundaries and frame descriptors.
Success returns deeply frozen `jsconfuser-vm-references.v1` (Packet C) with constants, register
references, labels and frame arithmetic; decline returns no partial record. This establishes
stream-wide legality before [D assigns ownership](partition-functions.md). It does not yet prove
each index belongs to the instruction's actual function.

Readers need arrays/indexes, registers, word PCs and [B's grammar/record](read-wordcode.md).
[A](extract-container.md) owns source/binding admission, using [Babel](../../babel.md).
The encoder's [frame/capture interfaces](../../../js-confuser-vm/container-wordcode.md#frame-and-capture-state)
explain why register indexes are relative and capture indexes belong to the creating closure.

## 2. Algorithm

A constant index without a pool is meaningless, and a numeric branch target can point into an
operand rather than an opcode. First index B's already parsed instruction PCs. Derive the root
frame from A's scalar values, then collect every closure descriptor before checking references.
This collection order obtains the largest described register/capture bounds across the stream;
it permits C to check broad legality before D knows which function owns each instruction.

Validate closure frame metadata and entry boundaries, retaining every creation descriptor and
requiring descriptors for the same entry to agree. Then check semantic operands: constants use
key zero and a valid pool index, global-name constants are strings, registers/upvalues fit the
stream-wide bounds, and direct targets are instruction starts. Direct targets retain roles such
as function entry, iterator exit, catch handler and finalizer throw pad, so D can apply ownership
rules to the same fact without reparsing raw words. Last, the root descriptor's register count
must cover every register the root uses: the root's code is laid out first, before the first
nested function's entry, so its highest register there bounds the count from below.

### Worked example: broad bounds before ownership

This **synthetic** assembly has main regCount=2, a child regCount=5 and one local capture:

| PC | Words | Meaning |
|---:|---|---|
| 0 | `[47,1,11,0,5,1,0,1,0]` | MAKE_CLOSURE into main r1; child entry 11, 0 params, 5 regs, 1 capture of main r0, no rest. |
| 9 | `[45,0]` | Main RETURN r0. |
| 11 | `[3,0,0]` | Child LOAD_UPVALUE r0, capture 0. |
| 14 | `[45,0]` | Child RETURN r0. |

B boundaries are [0,9,11,14], wordCount=16. With frameStart=1/headerSize=8, the root
size is 10, base 9 and register window [9,11). C's maxCount=5 and maxCaptureCount=1.
It records functionEntry 0 -> 11 and the local capture index 0. Child frame size is 13,
registerBaseOffset=8; no child absolute frame base is invented because calls allocate it later.

Changing main RETURN to r4 still passes C's global maximum 5, but r4 lies before the first
nested entry 11, so the root count check declines: main's count 2 does not cover r4. Changing
the local capture to index 4 passes C; [G](closure-lifetimes.md) refuses it against main's
actual register owner. A child register above the child's own count passes C's global bound and
is left to [E](build-cfg.md) once D assigns owners. This example demonstrates stage boundaries,
not admissible source by itself.

## 3. Implementation

### Components, state and indexes

| Component | Consumes -> produces | Required decisions |
|---|---|---|
| Word/frame index | A pool/scalars + B -> boundary set/root frame | Trust B grammar; index existing instruction PCs. |
| Descriptor collector | MAKE_CLOSURE records -> descriptors/global maxima | Check counts/rest, entry, signature equality; preserve all creation sites. |
| Semantic reference collector | B operands + pool/maxima -> constant/register/label rows | Check typed indexes; classify direct targets by explicit semantic offsets. |
| Publisher | Complete summaries -> frozen C | Copy values and roles; publish once, mutate no predecessor. |

The boundary set is B's instruction-start PCs; end-of-stream is not a target boundary.
Require MAIN_START_PC in that set and equal to its first entry. Failure is
invalid-label-reference or invalid-frame-metadata respectively. A has already supplied canonical
scalar/map values; C does not validate A's schema or repeat map matching.

Root arithmetic uses ordinary JavaScript addition, not modular u32 arithmetic:

```text
frameBase = FRAME_START
frameSize = HEADER_SIZE + MAIN_REG_COUNT
registerBase = FRAME_START + HEADER_SIZE
frameEnd = FRAME_START + frameSize
registerWindow = [registerBase, frameEnd)
```

Canonical slots are PC=0, CALLER=1, RET_DST=2, THIS=3, CLOSURE=4, HANDLERS=5,
FRAME_SIZE=6, REG_BASE=7. They are copied into C; register operands remain relative indexes.
C is static analysis: this root window does not create a runtime register array.

### Closure and reference decisions

For each MAKE_CLOSURE require regCount >= 1, paramCount <= regCount, and
hasRest implies paramCount >= 1. B already supplies u32 counts and Boolean flags. Require
startPc to be an instruction start. For a repeated startPc, compare exactly paramCount,
regCount, captureCount, hasRest and ordered captures (kind,index,isLocal); creationPc does
not participate. A conflict is invalid-descriptor. Identical repeats are legal at C.

Collect records with creationPc/startPc/counts/rest/captures, frameSize=headerSize+regCount
and registerBaseOffset=headerSize. Set maxCount to max(rootCount, every closure regCount),
and maxCaptureCount to max(every closure captureCount), or 0 with no descriptors. Only then
check each descriptor's local capture index < maxCount and nonlocal capture index <
maxCaptureCount. This is a necessary global bound, not a parent-owner proof.

| Semantic operand/form | C check and recorded state | Failure |
|---|---|---|
| register(index) | No bound (see Register operands); record pc, instruction, semantic operand offset, index. | None at C |
| constant-ref(index,key) | index < pool.length and key == 0; record pc/name/operand/index/concealKey. | invalid-constant-reference |
| LOAD_GLOBAL/STORE_GLOBAL/TYPEOF_SAFE constant | Above check plus typeof pool[index] == string. | invalid-constant-reference |
| upvalue-index(index) | index < maxCaptureCount; no separate upvalue-reference output array. | invalid-descriptor |
| local/upvalue capture object | Bounds from descriptor collector; parent assignment deferred. | Global local bound: invalid-register-reference; global upvalue bound: invalid-descriptor |
| immediate/spread-sentinel | No additional reference check. | None at C |
| label-target | Explicit row below identifies target role and requires a boundary. | invalid-label-reference |

The label collector uses these **semantic operand offsets**, not wordOperands tags:

| Instruction | Operand offset(s) | Role |
|---|---|---|
| JUMP | 0 | target |
| JUMP_IF_FALSE/JUMP_IF_TRUE | 1 | target |
| FOR_IN_NEXT | 2 | exit |
| TRY_SETUP | 0 | handler |
| FINALLY_SETUP | 0 / 3 | finally / throwPad |
| MAKE_CLOSURE | 1 | functionEntry |

Each label row contains pc, instruction, operand, role, target. Boundary validity is separate
from ownership: a branch to another function's valid entry passes C and can decline at D.
A LOAD_INT immediate equal to a PC is not a direct label; E's indirect provenance and
normalizer-owned relocation proofs determine when it represents an address.

### Register operands

C does not bound register operands. It has no owners and no reachability, and it reads streams that
still hold selfModifying's [suspects](self-modifying-observation.md#2-algorithm), whose registers
(0..24) ignore the frame. E bounds every register against its owner's count, the root's against
N, on the code it reaches ([owner ranges](build-cfg.md#owner-ranges-and-handler-records)); code that
never runs decides no behaviour. Capture indexes stay with the descriptor bounds above.

### Output and atomicity

C has schemaVersion/encoding/wordCount/instructionCount, and:
`constants:{poolSize,values,references}` (copied pool);
`registers:{rootCount,maxCount,maxCaptureCount,references}`;
`labels:{boundaries,references}` (ascending PCs for admitted root 0);
and `frame:{frameStart,headerSize,slots,mainStartPc,mainRegCount,root,descriptors}`.
The component decisions above define each field and which later owner refines it.

`diagnoseReferences` returns frozen {ok,result,diagnostic};
`validateReferences`/its result alias return C or null. A typed decline carries the listed
code; unexpected errors become reference-validator-error. Whole C is the atomic unit.
Local arrays/maps remain private until success, input A/B are unchanged, and no declarations
or helpers are removed. This stage never cleans source or repairs private predecessor records.

### Testing and acceptance

| Scenario | Observable result / oracle | Acceptance criterion | Retained fixture/control |
|---|---|---|---|
| C1: pool/frame projection | Pool values, descriptor widths and frame arithmetic match A/B. | Frozen C, unchanged A/B, exact boundaries/reference roles. | References test, reference, closure/finally fixtures below. |
| C2: source reference damage | C first reports invalid-constant/label-reference or invalid-descriptor. | Damage reaches the named check through A/B; public references-declined, no partial result. | Owned-chain controls: constant outside pool, entry inside operand, invalid descriptor counts. |
| C3: owner refinement | Global pass followed by responsible E/G refusal. | Do not claim C proves parent register/upvalue ownership. | Owned-chain local/inherited capture controls reach G; direct E owner-range source control is missing. |
| C4: repeated descriptor/global-name/key domain | Exact signature/key/string decisions above. | Named C decision reached, rather than earlier grammar refusal. | No dedicated retained normal-entry conflict/global-name/nonzero-key C controls; key normalization owns its source controls. |

Assertions on references/frame state fail for a passthrough implementation. Behavior regression
is separate from C's data proof. The [provenance contract](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/qualification-provenance.md)
limits historical fixture qualification; this page claims no fresh encode or reconstruction.

## 4. Input Shapes

C consumes [A](extract-container.md) values and [B](read-wordcode.md) semantic operands, with
source admission and grammar already owned by those producers. It supplies descriptors/global
bounds/labels to [D](partition-functions.md) and [E](build-cfg.md); [G](closure-lifetimes.md)
later proves parent captures and function-owned upvalue use.

| Earlier decoder output / origin | Producer-owned inventory | C handoff |
|---|---|---|
| Visible pool and key-zero words, encoder or ours | [A routes](extract-container.md#4-input-shapes), [constant normalizer](normalize-concealed-constants.md#3-implementation) | Nonzero keys must be normalized before ordinary C; copied restored values become authoritative. |
| Expanded/compacted words, ours | [B producer map](read-wordcode.md#4-input-shapes) | Use rebuilt B boundaries/operands; do not carry old C reference PCs. |
| Helper/capture/control rewrite, ours | [String normalizer](normalize-string-concealing.md#address-remapping-atomicity-and-derived-state), [dispatcher](normalize-dispatcher-wordcode.md), [CFF](normalize-cff-wordcode.md) | Rebuild C after pool/descriptor/PC changes; caller reuses the returned C. |

B's current FOR_IN_NEXT wordOperands tags differ from semantic roles; C explicitly uses
operand 2 as the exit and registers at semantic offsets 0/1. It does not reclassify these
tags or propagate them into its label rows. A changed stream/pool invalidates C even if a
particular index/PC remains numerically equal; normalizers own replacement, as specified by
[the caller](standalone-diagnosis.md#owned-record-boundary).

## 5. Known Gaps

- Stream-wide bounds are intentionally coarse. E checks actual owner register ranges; G checks
  parent captures and function-owned upvalues. C success alone does not qualify those facts.
- Constant values are copied, not evaluated; nonzero keys decline ordinary C and need the
  source-bound constant inverse. Encoded/randomized representations must first reach A's
  canonical value contract.
- Indirect targets, function locality, call/exception semantics and finalizer routing remain
  downstream work. C4 and the direct E owner-range source control remain acceptance debt.
- No cold/whole-system reconstruction or novice reader study is asserted.

## Source

The public stage is [validate-references.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/validate-references.js). Supporting modules are [validate-references-operands.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/validate-references-operands.js). The [standalone diagnosis](standalone-diagnosis.md#canonical-frontend-retries) wires C after key normalization and before ownership, as forced by item 4.

## Fixtures

| Committed fixture or test control | Claim pinned |
|---|---|
| [f-literals-order](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/raw/f-literals-order/encoded.js) | Root frame arithmetic and references in the accepted numeric baseline. |
| [f-closures-state](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/raw/f-closures-state/encoded.js) | Closure descriptor fields and capture/register bounds. |
| [f-finally-abrupt](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/raw/f-finally-abrupt/encoded.js) | Handler and finally label roles at instruction boundaries. |
| [reference-invalid-constant](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/negative/reference-invalid-constant/encoded.js), [reference-invalid-register](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/negative/reference-invalid-register/encoded.js), and [reference-invalid-label](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/negative/reference-invalid-label/encoded.js) | Atomic decline for out-of-range pool, frame, or label references. |
| [closure-invalid-capture](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/negative/closure-invalid-capture/encoded.js) | Atomic decline for an invalid capture descriptor. |
| [validate-references.test.js](../../../../decoder/decode-js/test/vm/jsconfuser-vm/validate-references.test.js) | C1: reference/frame projection and frozen unchanged predecessors; other negative decisions are pinned by the owned-chain source controls. |
| [owned-chain-source.test.js](../../../../decoder/decode-js/test/vm/jsconfuser-vm/owned-chain-source.test.js) | C2 exact first diagnostics; C3 local/inherited capture damage passes C and reaches G, preventing a per-owner overclaim. |
