# Validate references and frame shape

Part of the [`wordcode` module](../wordcode.md). The stage `read-program` calls it through the
[frontend driver](../frontend-driver.md), and every transform that rebuilds the stream calls it
again on its output ([map](../../../pipelines/jsconfuser-vm.md#frontend-order)).

## 2. Algorithm

The validator relates the instructions' operand indexes to the pool, the instruction boundaries
and the closure descriptors, over the whole stream. It does not yet know which function an
instruction belongs to ([partition-functions](partition-functions.md)).

```text
validate(container, wordcode):                       // explanatory pseudocode
  boundaries = the instructions' PCs                 // the end of the stream is no boundary
  root frame = arithmetic on the container's scalars
  for each MAKE_CLOSURE:                             // all descriptors first
    require its entry PC is a boundary               else invalid-label-reference
    keep its descriptor, also when several name one entry
  maxCount        = max(root register count, every descriptor's register count)
  maxCaptureCount = max(every descriptor's capture count), 0 with none
  for each descriptor's capture:
    local:   require index < maxCount                else invalid-register-reference
    upvalue: require index < maxCaptureCount         else invalid-descriptor
  for each instruction, each operand:
    register:  recorded, not bounded
    constant:  require index < pool size and key == 0     else invalid-constant-reference
               for LOAD_GLOBAL, STORE_GLOBAL, TYPEOF_SAFE: require a string
    upvalue:   require index < maxCaptureCount       else invalid-descriptor
    label:     require the target is a boundary      else invalid-label-reference
  publish the references record
```

The descriptors are collected before any reference is checked, so the bounds are the largest the
stream describes. They are necessary bounds, not proofs of ownership: a capture index is not
checked against the function that creates the closure.

**What is checked and what is read.** Each check guards a value a frontend rewrite changes, since
every transform re-runs the validator on the stream it rebuilds
([a correct model](../../switch/vm-switch-boundary.md#a-correct-model)): relocation rewrites
direct targets and closure entries, removing instructions can strand an upvalue or a capture, and
constant and string recovery rewrite pool references. What neither the encoder varies nor a
rewrite touches is read: a descriptor's counts and rest flag, agreement between descriptors of one
entry, the root's start PC, and every register operand. The encoder sets each register count and
index in one allocation, and a stream may still hold
[self-modifying suspects](../normalize-self-modifying-wordcode.md) whose registers ignore the
frame.

**Root frame.** Ordinary addition on the container's scalars:

```text
frameBase      = FRAME_START
frameSize      = HEADER_SIZE + MAIN_REG_COUNT
registerBase   = FRAME_START + HEADER_SIZE
frameEnd       = FRAME_START + frameSize
registerWindow = [registerBase, frameEnd)
```

Register operands stay relative indexes; no child frame base is computed, since a call allocates
it at run time ([frame and capture state](../../../../js-confuser-vm/container-wordcode.md#frame-and-capture-state)).

**Label roles.** A direct label operand is identified by its position in `operands`:

| Instruction | Operand index | Role |
|---|---|---|
| `JUMP` | 0 | `target` |
| `JUMP_IF_FALSE`, `JUMP_IF_TRUE` | 1 | `target` |
| `FOR_IN_NEXT` | 2 | `exit` |
| `TRY_SETUP` | 0 | `handler` |
| `FINALLY_SETUP` | 0, 3 | `finally`, `throwPad` |
| `MAKE_CLOSURE` | 1 | `functionEntry` |

A `LOAD_INT` immediate that equals a PC is no label here; whether it is an address is decided
where indirect jumps are solved ([origin-addresses](origin-addresses.md),
[vm-switch-control](../../switch/vm-switch-control.md)). A boundary is not ownership: a branch to
another function's entry passes here and refuses at the partition.

### Worked example

A **synthetic** stream with root register count 2, canonical opcodes, an empty pool:

| PC | Words | Meaning |
|---:|---|---|
| 0 | `[47,1,11,0,5,1,0,1,0]` | `MAKE_CLOSURE` into r1: entry 11, 0 parameters, 5 registers, 1 capture, no rest; the capture is local r0 |
| 9 | `[45,0]` | `RETURN` r0 |
| 11 | `[3,0,0]` | `LOAD_UPVALUE` r0, upvalue 0 |
| 14 | `[45,0]` | `RETURN` r0 |

Boundaries are `[0, 9, 11, 14]`. With `FRAME_START` 1 and `HEADER_SIZE` 8 the root frame has size
10, register base 9 and window `[9, 11)`. `maxCount` is 5 and `maxCaptureCount` 1. The one label
reference is `{pc: 0, instruction: 'MAKE_CLOSURE', operand: 1, role: 'functionEntry', target: 11}`.
The descriptor gets `frameSize` 13 and `registerBaseOffset` 8.

With the capture index changed to 4 the record is still published: 4 is under `maxCount`,
although the root has only two registers. Changed to 5 it refuses, `invalid-register-reference`.

## 3. Implementation

### Exports another file imports

| Export | Contract | Imported by |
|---|---|---|
| `diagnoseReferences(container, wordcode)` | `{ok, result, diagnostic}`, deeply frozen: the references record or a `references` refusal ([Refusals](../../../pipelines/jsconfuser-vm.md#refusals)); fallback code `reference-validator-error`. | `normalize-cff-wordcode`, `normalize-dispatcher-wordcode`, `normalize-string-concealing`, the cell oracle script |
| `validateReferences(container, wordcode)` | The record, or `null`. | the frontend driver, `normalize-anti-wordcode`, `normalize-specialized-wordcode`, tests |

The validator reads the container's pool, words and scalars and the wordcode record's
instructions through [`indexWordcode`](read-wordcode.md#exports-another-file-imports). It trusts
both: it repeats neither the container's nor the reader's checks.

### The references record

```text
schemaVersion: 'jsconfuser-vm-references.v1'
encoding:      'numeric-u32'
wordCount, instructionCount
constants
  poolSize
  values                    // a copy of the pool
  references [{ pc, instruction, operand, index, concealKey }]
registers
  rootCount                 // MAIN_REG_COUNT
  maxCount, maxCaptureCount
  references [{ pc, instruction, operand, index }]
labels
  boundaries                // instruction PCs, ascending
  references [{ pc, instruction, operand, role, target }]
frame
  frameStart, headerSize
  slots                     // the canonical frame slot indexes
  mainStartPc, mainRegCount
  root { frameBase, frameSize, registerBase, registerWindow { start, end }, frameEnd }
  descriptors [{ creationPc, startPc, paramCount, regCount, captureCount, hasRest,
                 captures [{ kind, index, isLocal }], frameSize, registerBaseOffset }]
```

`operand` is the operand's index in the instruction's `operands`. `frameSize` of a descriptor is
`headerSize + regCount` and `registerBaseOffset` is `headerSize`. Upvalue operands are checked
and not listed.

### Refusals

Owner `references`. A refusal publishes no partial record; neither input is changed.

| Code | When |
|---|---|
| `invalid-label-reference` | A closure entry or a direct label that is not an instruction PC |
| `invalid-constant-reference` | A pool index outside the pool, a nonzero conceal key, or a global name that is not a string |
| `invalid-register-reference` | A local capture index at or above `maxCount` |
| `invalid-descriptor` | An upvalue capture or an upvalue operand at or above `maxCaptureCount` |
| `reference-validator-error` | Any other error |

A nonzero key means the constants are still concealed: the driver recovers them before this
validator sees the stream ([`recover-constants`](../../../pipelines/jsconfuser-vm.md#frontend-order)).

## 5. Known Gaps

- The bounds are stream-wide. No component checks a capture against the function that creates
  the closure, or an upvalue operand against its own function's capture count.
- No committed test reaches a refusal of this validator directly.
- A comment in the code still names later components by retired letter labels.

## 6. Source

- [validate-references.js](../../../../../decoder/decode-js/src/vm/jsconfuser-vm/wordcode/validate-references.js):
  the whole part.
- [wordcode-index.js](../../../../../decoder/decode-js/src/vm/jsconfuser-vm/wordcode/wordcode-index.js):
  the index it reads.

## 7. Fixtures

No suite breaks this part's code; every cell passes through it. The unit test is
[validate-references.test.js](../../../../../decoder/decode-js/test/vm/jsconfuser-vm/single-component/validate-references.test.js).

| Scenario | Expected result | Committed fixture |
|---|---|---|
| A hand-written container and its wordcode | The record is read without changing either input and is deeply frozen | validate-references.test.js |
| Closures, try and finally, literals in encoded programs | Descriptors, handler and finally labels and pool references are admitted; the decode behaves as the source | [compiled-forms](../../../../../decoder/decode-js/test/vm/jsconfuser-vm/cell-suites/compiled-forms/suite.js) (coverage) |
| A constant index outside the pool; a nonzero key | `invalid-constant-reference` | |
| A jump into an operand | `invalid-label-reference` | |
| A local capture index at `maxCount` | `invalid-register-reference` | |
