# Validate references and frame shape

Pipeline stage: `read-program` ([map](../../pipelines/jsconfuser-vm.md)).

## 1. Target

Relate parsed operand indexes to the admitted pool, instruction boundaries and frame descriptors.
Success returns deeply frozen `jsconfuser-vm-references.v1` (`validate-references`) with constants,
register references, labels and frame arithmetic; decline returns no partial record. This
establishes stream-wide legality before
[`partition-functions` assigns ownership](partition-functions.md). It does not yet prove each index
belongs to the instruction's actual function.

Readers need arrays/indexes, registers, word PCs and
[`read-wordcode`'s grammar/record](read-wordcode.md). [`extract-container`](extract-container.md)
owns source/binding admission, using [Babel](../../babel.md). The encoder's
[frame/capture interfaces](../../../js-confuser-vm/container-wordcode.md#frame-and-capture-state)
explain why register indexes are relative and capture indexes belong to the creating closure.

## 2. Algorithm

A constant index without a pool is meaningless, and a numeric branch target can point into an
operand rather than an opcode. First index `read-wordcode`'s already parsed instruction PCs. Derive
the root frame from `extract-container`'s scalar values, then collect every closure descriptor
before checking references. This collection order obtains the largest described register/capture
bounds across the stream; it permits `validate-references` to check broad legality before
`partition-functions` knows which function owns each instruction.

Check closure entry boundaries, retaining every creation descriptor. Then check semantic operands:
constants use key zero and a valid pool index, global-name constants are strings, upvalues and
captures fit the stream-wide bounds, and direct targets are instruction starts. Direct targets
retain roles such as function entry, iterator exit, catch handler and finalizer throw pad, so
`partition-functions` can apply ownership rules to the same fact without reparsing raw words.

Each check guards a value a frontend rewrite changes, since every normalizer re-runs this
component on the stream it rebuilds ([the model rule](../switch/vm-switch-boundary.md#a-correct-model)):
relocation rewrites direct targets and closure entries, removing instructions can strand an upvalue
or capture, and constant and string restoration rewrite pool references. What neither the encoder
varies nor a rewrite touches is read, not checked: descriptor frame counts, agreement between
descriptors of one entry, `MAIN_START_PC`, register indexes.

### Worked example: broad bounds before ownership

This **synthetic** assembly has main regCount=2, a child regCount=5 and one local capture:

| PC | Words | Meaning |
|---:|---|---|
| 0 | `[47,1,11,0,5,1,0,1,0]` | MAKE_CLOSURE into main r1; child entry 11, 0 params, 5 regs, 1 capture of main r0, no rest. |
| 9 | `[45,0]` | Main RETURN r0. |
| 11 | `[3,0,0]` | Child LOAD_UPVALUE r0, capture 0. |
| 14 | `[45,0]` | Child RETURN r0. |

`read-wordcode` boundaries are [0,9,11,14], wordCount=16. With frameStart=1/headerSize=8, the root
size is 10, base 9 and register window [9,11). `validate-references`'s maxCount=5 and
maxCaptureCount=1. It records functionEntry 0 -> 11 and the local capture index 0. Child frame size
is 13, registerBaseOffset=8; no child absolute frame base is invented because calls allocate it
later.

Changing the local capture to index 4 passes `validate-references`'s global maximum 5: no
component checks it against main's actual register owner. Changing it to 5 declines here, invalid-register-reference. This example demonstrates component
boundaries, not admissible source by itself.

## 3. Implementation

### Components, state and indexes

| Component | Consumes -> produces | Required decisions |
|---|---|---|
| Word/frame index | A pool/scalars + `read-wordcode` -> boundary set/root frame | Trust `read-wordcode` grammar; index existing instruction PCs. |
| Descriptor collector | MAKE_CLOSURE records -> descriptors/global maxima | Check the entry; preserve all creation sites. |
| Semantic reference collector | `read-wordcode` operands + pool/maxima -> constant/register/label rows | Check typed indexes; classify direct targets by explicit semantic offsets. |
| Publisher | Complete summaries -> frozen `validate-references` | Copy values and roles; publish once, mutate no predecessor. |

The boundary set is `read-wordcode`'s instruction-start PCs; end-of-stream is not a target boundary.
MAIN_START_PC is read, not checked: the encoder lays the root out first, and every rewrite keeps it
there. `extract-container` has already supplied canonical scalar/map values; `validate-references`
does not validate `extract-container`'s schema or repeat map matching.

Root arithmetic uses ordinary JavaScript addition, not modular u32 arithmetic:

```text
frameBase = FRAME_START
frameSize = HEADER_SIZE + MAIN_REG_COUNT
registerBase = FRAME_START + HEADER_SIZE
frameEnd = FRAME_START + frameSize
registerWindow = [registerBase, frameEnd)
```

Canonical slots are PC=0, CALLER=1, RET_DST=2, THIS=3, CLOSURE=4, HANDLERS=5, FRAME_SIZE=6,
REG_BASE=7. They are copied into `validate-references`; register operands remain relative indexes.
`validate-references` is static analysis: this root window does not create a runtime register array.

### Closure and reference decisions

For each MAKE_CLOSURE require startPc to be an instruction start (failure invalid-label-reference).
Its counts, rest flag and captures are the encoder's and are copied unchecked; `read-wordcode`
already supplies u32 counts and Boolean flags. Every creation descriptor is kept, also several for
one entry.

Collect records with creationPc/startPc/counts/rest/captures, frameSize=headerSize+regCount
and registerBaseOffset=headerSize. Set maxCount to max(rootCount, every closure regCount),
and maxCaptureCount to max(every closure captureCount), or 0 with no descriptors. Only then
check each descriptor's local capture index < maxCount and nonlocal capture index <
maxCaptureCount. This is a necessary global bound, not a parent-owner proof.

| Semantic operand/form | `validate-references` check and recorded state | Failure |
|---|---|---|
| register(index) | No bound (see Register operands); record pc, instruction, semantic operand offset, index. | None at `validate-references` |
| constant-ref(index,key) | index < pool.length and key == 0; record pc/name/operand/index/concealKey. | invalid-constant-reference |
| LOAD_GLOBAL/STORE_GLOBAL/TYPEOF_SAFE constant | Above check plus typeof pool[index] == string. | invalid-constant-reference |
| upvalue-index(index) | index < maxCaptureCount; no separate upvalue-reference output array. | invalid-descriptor |
| local/upvalue capture object | Bounds from descriptor collector; parent assignment deferred. | Global local bound: invalid-register-reference; global upvalue bound: invalid-descriptor |
| immediate/spread-sentinel | No additional reference check. | None at `validate-references` |
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

Each label row contains pc, instruction, operand, role, target. Boundary validity is separate from
ownership: a branch to another function's valid entry passes `validate-references` and can decline
at `partition-functions`. A LOAD_INT immediate equal to a PC is not a direct label; the control solver's
indirect provenance and normalizer-owned relocation proofs determine when it represents an address.

### Register operands

`validate-references` does not bound register operands, and no later component does: the
encoder sets each count and every index in one register allocation
([a correct model](../switch/vm-switch-boundary.md#a-correct-model)). The streams it reads may still
hold selfModifying's [suspects](self-modifying-observation.md#2-algorithm), whose registers (0..24)
ignore the frame. Capture indexes stay with the descriptor bounds above.

### Output and atomicity

`validate-references` has this shape; the component decisions above define each field and which
later owner refines it:

```js
{
  schemaVersion, encoding, wordCount, instructionCount,
  constants: { poolSize, values, references },          // copied pool
  registers: { rootCount, maxCount, maxCaptureCount, references },
  labels: { boundaries, references },                   // ascending PCs for admitted root 0
  frame: { frameStart, headerSize, slots, mainStartPc, mainRegCount, root, descriptors },
}
```

`diagnoseReferences` returns frozen {ok,result,diagnostic}; `validateReferences`/its result alias
return `validate-references` or null. A typed decline carries the listed code; unexpected errors
become reference-validator-error. Whole `validate-references` is the atomic unit. Local arrays/maps
remain private until success, input `extract-container` and `read-wordcode` are unchanged, and no
declarations or helpers are removed. This component never cleans source or repairs private predecessor
records.

### Testing and acceptance

| Scenario | Observable result / oracle | Acceptance criterion | Retained fixture/control |
|---|---|---|---|
| S1: pool/frame projection | Pool values, descriptor widths and frame arithmetic match `extract-container` and `read-wordcode`. | Frozen `validate-references`, unchanged `extract-container` and `read-wordcode`, exact boundaries/reference roles. | References test, reference, closure/finally fixtures below. |
| S2: source reference damage | `validate-references` first reports invalid-constant/label-reference or invalid-descriptor. | Damage reaches the named check through `extract-container` and `read-wordcode`; public references-declined, no partial result. | Owned-chain controls: constant outside pool, entry inside operand. |
| S3: owner bound | Global pass only. | Do not claim `validate-references` proves parent register/upvalue ownership. | None: the encoder's allocation fixes capture owners ([F4](../../../encoder-decoder-method.md#f4-keep-a-guard-only-where-a-real-case-needs-it)). |
| S4: global-name/key domain | Exact key/string decisions above. | Named `validate-references` decision reached, rather than earlier grammar refusal. | No dedicated retained normal-entry global-name/nonzero-key `validate-references` controls; key normalization owns its source controls. |

Assertions on references/frame state fail for a passthrough implementation. Behavior regression is
separate from `validate-references`'s data proof. This page claims no fresh encode or
reconstruction.

## 4. Input Shapes

`validate-references` consumes [`extract-container`](extract-container.md) values and
[`read-wordcode`](read-wordcode.md) semantic operands, with source admission and grammar already
owned by those producers. It supplies descriptors/global bounds/labels to
[`partition-functions`](partition-functions.md) and the [numeric projection](lower-switch-model.md).

| Earlier decoder output / origin | Producer-owned inventory | `validate-references` handoff |
|---|---|---|
| Visible pool and key-zero words, encoder or ours | [`extract-container` routes](extract-container.md#4-input-shapes), [constant normalizer](normalize-concealed-constants.md#3-implementation) | Nonzero keys must be normalized before ordinary `validate-references`; copied restored values become authoritative. |
| Expanded/compacted words, ours | [`read-wordcode` producer map](read-wordcode.md#4-input-shapes) | Use rebuilt `read-wordcode` boundaries/operands; do not carry old `validate-references` reference PCs. |
| Helper/capture/control rewrite, ours | [String normalizer](normalize-string-concealing.md#address-remapping-atomicity-and-derived-state), [dispatcher](normalize-dispatcher-wordcode.md), [CFF](normalize-cff-wordcode.md) | Rebuild `validate-references` after pool/descriptor/PC changes; caller reuses the returned `validate-references`. |

A changed stream/pool
invalidates `validate-references` even if a particular index/PC remains numerically equal;
normalizers own replacement, as specified by
[the caller](standalone-diagnosis.md#owned-record-boundary).

## 5. Known Gaps

- Stream-wide bounds are intentionally coarse: `validate-references` success does not qualify
  parent captures or function-owned upvalues, and no later component checks them.
- Constant values are copied, not evaluated; nonzero keys decline ordinary `validate-references` and
  need the source-bound constant inverse. Encoded/randomized representations must first reach
  `extract-container`'s canonical value contract.
- Indirect targets, function locality, call/exception semantics and finalizer routing remain
  downstream work. S4 remains acceptance debt.
- No cold/whole-system reconstruction or novice reader study is asserted.

## Source

The component is implemented by
[validate-references.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/validate-references.js).
[validate-references-operands.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/validate-references-operands.js)
holds the schema name (`REFERENCE_SCHEMA`), the canonical frame slots (`CANONICAL_SLOTS`), the typed
refusal (`ReferenceDecline`, `decline`), the record freeze (`deepFreeze`) and the container view
(`containerData`: pool values, words and scalar values read from the container roles).
The [standalone diagnosis](standalone-diagnosis.md#canonical-frontend-retries) wires
`validate-references` after key normalization and before ownership, as forced by item 4.

## Fixtures

Each suite encodes its sources with the pinned encoder and requires the decode to behave as the
source ([tests.md](../../tests.md#suites)); a Proved line names the code whose break turns the case
red.

| Suite and cases | Claims | Proved |
|---|---|---|
| [compiled-forms](../../../../decoder/decode-js/test/vm/jsconfuser-vm/generated-cells/compiled-forms/suite.js), `data-literal` (f-literals-order), `fn-closure` (f-closures-state), `control-try` (f-finally-abrupt) | S1: root frame references, closure descriptors and capture bounds, handler and finally labels | A captured register stays within the frame |
| [validate-references.test.js](../../../../decoder/decode-js/test/vm/jsconfuser-vm/single-component/validate-references.test.js) (unit) | Inputs read without change into deeply frozen references | Not a suite |

S2 (exact first diagnostics) has no committed test: the old controls edited input by hand.
