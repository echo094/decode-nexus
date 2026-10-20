# Read numeric wordcode

## 1. Target

Parse the copied numeric word stream from `jsconfuser-vm-container.v1` into immutable
`jsconfuser-vm-wordcode.v1` instructions with both serialized and semantic operand views. This
pass is parse-only: it establishes boundaries and arity, not register ownership or control-flow
validity. A successful parse is recovery into ordered typed instructions, not a promise of
source emission. Readers need arrays, counts and word PCs plus [A](extract-container.md) and
the [encoder grammar](../../../js-confuser-vm/instruction-set.md). The [Babel foundation](../../babel.md)
governs source admission; B reads values rather than source bindings.

## 2. Algorithm

Consume the word array established by container admission or an owned normalizer. The parser
names each opcode word through the container's opcode table (`roles.op.values`, this decode's
object from [opcode-table.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/opcode-table.js),
canonical by default) and recognizes a spread argument count by the container's sentinel
(`roles.sentinels.values.CALL_SPREAD`, 65535 by default); A or a materializer has already proved
those values give the copied stream its meaning. Later stages read a call's spread form from
B's instruction (`form.kind`), never by comparing words with a constant. The reader does not repeat the container schema, role,
encoding, or source-admission checks. A cursor consumes the opcode at the current PC and
dispatches by canonical name.

Fixed rows consume their declared width and classify operands as registers, constants, upvalue
indexes, immediates, or label targets. Constant-bearing rows consume the pool index and conceal key
pair. `CALL`, `CALL_METHOD`, and `NEW` read destination/callee (and receiver for methods), then
either `argc` register words or the spread sentinel followed by exactly one array-register word.
`MAKE_CLOSURE` reads its function metadata and `captureCount` pairs. `BUILD_ARRAY` and
`BUILD_OBJECT` consume element or key/value registers from their counts. Opcode-only rows such as
`TRY_END` and `DEBUGGER` consume their opcode word and no further operands.

Every count is checked against the remaining stream before consumption. The parser records the
raw instruction words, typed serialized operands, semantic operands, form metadata, width, and
next PC. It must finish exactly at the end of the array; an unknown opcode, truncated payload,
invalid count/flag or hardening-only `PATCH` declines the whole stream. A suffix is parsed as
another instruction: an extra word 61 declines as unknown-opcode, but an appended DEBUGGER
parses. Full consumption alone does not prove that code ends at its intended terminator.

### Worked example: counted payload

The **synthetic** stream `[43,0,1,2,65535,3,45,0]` has eight words. CALL_METHOD at PC 0
reads destination r0, receiver r1, callee r2, argc=65535 and one array register r3. Its width
is 6, next PC 6. RETURN r0 then has width 2, next PC 8. r3 is neither a count nor a value
read here. Changing argc to 2 consumes 3 and 45 as argument register indexes; the next opcode
is 0 with a missing payload, so the entire parse declines. Opcode-looking payload cannot
delimit an instruction. This example omits runtime, pool, register validity and call semantics.


## 3. Implementation

### Component contracts

| Component | Consumes -> produces | Responsibility |
|---|---|---|
| Cursor | A words -> validated u32 reads | PC and remaining length are words; bound every read. |
| Dispatch | Header value -> fixed or counted row | Exact canonical lookup below; refuse PATCH before consuming it. |
| Counted-tail reader | Header/count + remaining words -> full form | Sentinel-first calls; pair count <= floor(remaining/2). |
| Projector | Full span -> raw/semantic/tagged record | Preserve order, width, nextPc and form fields. |
| Publisher | Complete instruction list -> frozen B | No partial list on failure; copy words and publish once. |

### Operand grammar

One word is an unsigned 32-bit integer. `pc` indexes **words**, not bytes. The first word of
each instruction is its opcode; all widths below **include** that opcode. This differs from the
encoder [instruction table](../../../js-confuser-vm/instruction-set.md), whose `Width` column
counts words **after** the opcode. `r` is a register index, `uv` an upvalue index, `t` an absolute
word PC, `i` an immediate, and `c,k` a constant-pool index and conceal-key pair. These are
serialized roles, not promises that the referenced register, label, or constant exists.

| Opcode name(s) and numeric value(s) | Serialized instruction, starting at opcode | Total width | Semantic operands in order |
|---|---|---:|---|
| `LOAD_CONST` 0, `LOAD_GLOBAL` 2, `TYPEOF_SAFE` 38 | `op, dst, c, k` | 4 | register `dst`; one constant reference `(c,k)` |
| `STORE_GLOBAL` 6 | `op, c, k, src` | 4 | constant reference `(c,k)`; register `src` |
| `LOAD_INT` 1 | `op, dst, i` | 3 | register `dst`; immediate `i` |
| `LOAD_UPVALUE` 3 | `op, dst, uv` | 3 | register `dst`; upvalue index `uv` |
| `STORE_UPVALUE` 7 | `op, uv, src` | 3 | upvalue index `uv`; register `src` |
| `LOAD_THIS` 4 | `op, dst` | 2 | register `dst` |
| `MOVE` 5, `FOR_IN_SETUP` 52 | `op, dst, src` | 3 | registers `dst, src` |
| `GET_PROP` 8, `DELETE_PROP` 10 | `op, dst, obj, key` | 4 | registers `dst, obj, key` |
| `SET_PROP` 9 | `op, obj, key, value` | 4 | registers `obj, key, value` |
| `DEFINE_GETTER` 50, `DEFINE_SETTER` 51 | `op, obj, key, fn` | 4 | registers `obj, key, fn` |
| `ADD` 11, `SUB` 12, `MUL` 13, `DIV` 14, `MOD` 15, `EXP` 60; `BAND` 16, `BOR` 17, `BXOR` 18, `SHL` 19, `SHR` 20, `USHR` 21; `LT` 22, `GT` 23, `LTE` 24, `GTE` 25, `EQ` 26, `NEQ` 27, `LOOSE_EQ` 28, `LOOSE_NEQ` 29, `IN` 30, `INSTANCEOF` 31 | `op, dst, lhs, rhs` | 4 | registers `dst, lhs, rhs` |
| `UNARY_NEG` 32, `UNARY_POS` 33, `UNARY_NOT` 34, `UNARY_BITNOT` 35, `TYPEOF` 36, `VOID` 37 | `op, dst, src` | 3 | registers `dst, src` |
| `JUMP` 39 | `op, t` | 2 | label target `t` |
| `JUMP_IF_FALSE` 40, `JUMP_IF_TRUE` 41 | `op, src, t` | 3 | register `src`; label target `t` |
| `RETURN` 45, `THROW` 46, `JUMP_REG` 58 | `op, src` | 2 | register `src` |
| `FOR_IN_NEXT` 53 | `op, dst, iter, exitPc` | 4 | registers `dst, iter`; label target `exitPc` |
| `TRY_SETUP` 54 | `op, handlerPc, exceptionReg` | 3 | label target `handlerPc`; register `exceptionReg` |
| `FINALLY_SETUP` 59 | `op, finallyPc, contReg, payloadReg, throwPadPc` | 5 | label target, two registers, label target |
| `TRY_END` 55, `DEBUGGER` 57 | `op` | 1 | none |

Variable-width instructions use the following grammar. `n` and `m` are count words, and the
sentinel is exactly the container's (`65535` in the canonical build; the grammar rows below show
that value); the sentinel takes the spread form **before** any ordinary count
interpretation. The count does not itself bound register IDs. The register and reference validator
owns those range checks.

| Opcode name(s) and numeric value(s) | Serialized instruction | Total width | Required interpretation |
|---|---|---:|---|
| `CALL` 42, `NEW` 44 | `op, dst, callee, n, argReg[0..n)` | `4+n` | Fixed arguments, including `n=0`. `dst` and `callee` are registers; `n` is an immediate. |
| `CALL` 42, `NEW` 44 | `op, dst, callee, 65535, arrayReg` | 5 | Spread arguments from one register. |
| `CALL_METHOD` 43 | `op, dst, receiver, callee, n, argReg[0..n)` | `5+n` | Fixed arguments; receiver and callee are separate registers. |
| `CALL_METHOD` 43 | `op, dst, receiver, callee, 65535, arrayReg` | 6 | Spread arguments from one register; retain receiver identity. |
| `MAKE_CLOSURE` 47 | `op, dst, entryPc, params, regs, m, hasRest, (isLocal, index)[0..m)` | `7+2m` | `entryPc` is a label; counts are immediates; `hasRest` and `isLocal` are 0 or 1. `isLocal=1` captures a local, `0` an enclosing upvalue. |
| `BUILD_ARRAY` 48 | `op, dst, n, elementReg[0..n)` | `3+n` | Ordered element registers. |
| `BUILD_OBJECT` 49 | `op, dst, m, (keyReg, valueReg)[0..m)` | `3+2m` | Ordered key/value register pairs. |
| `PATCH` 56 | hardening-dependent header and opaque region | unsupported | Decline before treating its following words as ordinary instructions. |

`wordOperands` has one entry for **every serialized word after `op`**, normally tagging register, label target,
constant index, constant key, upvalue index, immediate, spread sentinel, capture kind, or capture
index. `operands` groups related words into semantic objects: notably `(c,k)` becomes one
`constant-ref`, while a closure capture pair becomes one `{kind:local|upvalue,index,isLocal}`
object. These two arrays therefore need not have equal lengths. The current FOR_IN_NEXT tagged-view
exception is stated in [Known Gaps](#5-known-gaps); its semantic view carries the actual roles. For example, words
`[0, 2, 7, 0]` are `LOAD_CONST` at PC 0, width 4, next PC 4, with serialized operands
`register(2), constant-index(7), constant-key(0)` and semantic operands
`register(2), constant-ref(7,0)`. This parse alone does not assert that pool entry 7 exists.

The following is explanatory pseudocode. The word test is
`Number.isInteger(value) && 0 <= value <= 0xffffffff`. Counts also require a nonnegative
safe integer. Single-word tails require `count <= remaining`; pairs require
`count <= floor(remaining/2)`. Prove the bound before allocating/iterating the tail.

```text
pc = 0; privateInstructions = []
while pc < wordCount:
  begin private span; validate words[pc] as u32
  look up the name in the container's opcode table; absent -> unknown-opcode;
    PATCH -> unsupported-hardening-opcode
  choose fixed or call/closure/array/object row
  read header with cursor bounds and u32 checks
  prove selected counted tail fits, then consume it
  closure hasRest and every isLocal must each be 0 or 1
  build full span record; require nextPc == cursor.pc
  append private record; pc = nextPc
require pc == wordCount; publish copied words and instructions, deep-frozen
```

No instruction prefix escapes a failed whole-stream parse. No AST, container values, bindings
or helpers change, so there is no cleanup or rollback mutation.
Later passes, beginning with
[reference validation](validate-references.md), decide whether the parsed references and machine
semantics are valid.

### Records and diagnoses

The result has schema `jsconfuser-vm-wordcode.v1`, `encoding: "numeric-u32"`, copied `words`,
`wordCount`, ordered `instructions`, `instructionCount`, `consumedWords`, and `nextPc`. Each
instruction contains `pc`, `name`, `{ name, value }` opcode metadata, `operands`, `wordOperands`,
copied `words`, `width`, and `nextPc`. Calls additionally expose `form`, `arguments`,
`destination`, `callee`, `receiver`, and serialized argument offset; closures expose
`functionMeta`, `captures`, `capturePairs`, and destination; arrays and objects expose their
counted forms.

`diagnoseWordcode` returns a deep-frozen `{ok,result,diagnostic}` envelope. Named failures include
unknown-opcode, truncated-instruction, invalid-word, invalid-count, invalid-descriptor,
invalid-capture-pair and unsupported-hardening-opcode. Unexpected errors become word-reader-error;
internal consumption disagreement is reader-internal-error. Every failure has result:null. `readWordcode` returns the
frozen result or `null`; it never repairs, mutates, or executes input. Width is defined by the
canonical grammar, so an operand that happens to resemble a later opcode is still payload when
the current instruction says it is payload.

`diagnoseWordcodeInstruction` uses the same grammar for one instruction at
an explicit PC. It does not establish that the PC is a boundary in the whole stream. The
[self-modifying observer](self-modifying-observation.md) supplies that reachability and interval
context while keeping ciphertext and junk outside the parser.

`diagnoseObservedWordcodeInstruction(container, pc, addedOpcodes)` shares that cursor grammar
with reached PATCH regions. Owned source definitions select the same anti/specialized/macro
widths as the full-stream readers. It projects aliases as ALIAS with one full canonical step,
while preserving original raw words/width/nextPc; no expansion or added-opcode-use requirement is
introduced at a single-instruction boundary. The observer supplies reachability and interval
proof; this helper does not establish them independently.

The anti, alias, macro and specialized stream readers are internal consumers of records produced
by the corresponding source observers. They build opcode lookup maps directly from those proved
records; schema tags, case counts, operand permutations, step spans and predecessor-prefix
agreement are not admission checks at this handoff. The source observers own those proofs.
Cursor bounds, unsigned word reads, counted operand parsing, unknown opcodes, complete stream
consumption and the presence of the requested added opcodes remain stream decode decisions.
The normalizers still require canonical wordcode and valid control/reference semantics before
standalone emission. A separately supplied shared switch model crosses its own
[validated boundary](../../vm-switch-boundary.md).

### Testing and acceptance

| Scenario | Observable result / oracle | Acceptance criterion | Retained fixture/control |
|---|---|---|---|
| B1: spans/forms | Widths/fields match grammar, including zero argc and spread receiver. | Ordered boundaries, copied words, full consumption, deep freeze, A unchanged. | Reader test; spread/method/new/closure fixtures below. |
| B2: source damage | B first reports unknown-opcode or truncated-instruction; public wordcode-declined. | Named responsible check reached through A; no partial B/output. | Owned-chain test: unknown word, truncated call. |
| B3: other truncation/PATCH | Named selected-row failure. | No prefix result. | Reader's fixed/spread/closure/array/object/PATCH copied-packet controls; grammar unit evidence only. |
| B4: tagged/semantic projection | Correct iterator/exit semantics despite compatibility tags. | No consumer infers exit from the wrong tag. | Owned-chain for-in behavior succeeds; exact tag/relocation control missing. |

Instruction names/forms/PC assertions fail for passthrough. Behavior alone cannot establish grammar
recovery. No cold reconstruction or novice study is claimed. Retained output qualification follows
the [provenance contract](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/qualification-provenance.md).

## 4. Input Shapes

B reads `roles.words.values` from [A](extract-container.md). A's source-bound routes project
numeric values with canonical interpretation. Physical case shuffle does not change the values.
B supplies boundaries, semantic operand roles and variable forms to [C](validate-references.md).
No later stage guesses widths.

| Earlier decoder output / origin | Producer-owned inventory | B handoff |
|---|---|---|
| Encoded/randomized projection, ours | [A routes](extract-container.md#4-input-shapes) and linked materializers | Same canonical grammar. |
| Alias/macro/specialized/anti expansion/erasure, ours | [Aliases](normalize-aliased-wordcode.md#4-input-shapes), [macros](normalize-macro-wordcode.md#4-input-shapes), [specialized](normalize-specialized-wordcode.md#4-input-shapes), [anti](normalize-anti-wordcode.md#4-input-shapes) | Parse new words; caller reuses returned B. |
| Reachable decrypted compact words, ours | [PATCH normalizer](normalize-self-modifying-wordcode.md#3-implementation) | Parse recovered code, not ciphertext/junk. |
| Pool/key-zero or helper/control changes, ours | [Constants](normalize-concealed-constants.md), [string](normalize-string-concealing.md#address-remapping-atomicity-and-derived-state), [dispatcher](normalize-dispatcher-wordcode.md), [CFF](normalize-cff-wordcode.md) | Changed words invalidate old spans; producer supplies B and any rebuilt later records. |

[Diagnosis](standalone-diagnosis.md#canonical-frontend-retries) owns retry order. Optional mixed
readers remain separate source-observer dependencies, not wider canonical admission. Successful
owned B is consumed without schema/map/count/raw-word revalidation.

## 5. Known Gaps

- Encoded transport first needs numeric A; B has no byte/string inverse.
  `PATCH`/optional forms are rejected rather than decoded by an assumed inverse. The [self-modifying normalizer](normalize-self-modifying-wordcode.md) supplies
  a separately proved canonical container when the direct reader declines PATCH.
- Register ranges, constant indexes, label targets, frame layout, and function ownership are
  intentionally validated by later passes.
- This reader recognizes the values in the container's opcode table, which are canonical unless
  a stage overwrote them; randomized values are named by Packet A's table from handler behaviour
  ([runtime meaning](runtime-meaning.md)). Physical switch-case shuffling
  preserves the opcode values and does not change the wordcode grammar.
- The direct canonical reader declines synthetic anti-instrumentation opcodes. The
  [anti-runtime observation](anti-runtime-observation.md) reads their emitted shape, and
  [normalization](normalize-anti-wordcode.md) supplies a proved canonical container to the
  standalone pipeline.

- Current `FOR_IN_NEXT [53,dst,iter,exitPc]` semantic operands are register(dst),
  register(iter), label-target(exitPc). `wordOperands` instead tags iter as label-target and
  exitPc as register. C/E use semantic operands/explicit raw offsets and preserve actual roles.
  J copies these tags and reports proof.historicalForInNextWordOperandsPreserved from their
  kinds; this is a reported flag, not a refusal guard. Dispatcher and anti analyses also
  inspect wordOperands. This is a compatibility/state defect, not a different
  encoder operand order. A correction must reconcile consumers and add exact tag/relocation
  controls. Successful for-in behavior does not qualify every optional combination.
- A parseable suffix can pass B; terminal/control intent belongs to E and later plans. The
  trailing-word guard does not prove rejection of all extra instructions.

## Source

The canonical grammar and owned publication in items 2-3 are implemented by [read-wordcode.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/read-wordcode.js). The compatibility-tag consumers are [property/collection projection](../../../../decoder/decode-js/src/vm/jsconfuser-vm/analyze-property-collections.js), [dispatcher observation](../../../../decoder/decode-js/src/vm/jsconfuser-vm/observe-dispatcher-wordcode.js) and [anti register flow](../../../../decoder/decode-js/src/vm/jsconfuser-vm/analyze-anti-register-flow.js). The standalone call site for the schedule in item 4 is [diagnose-standalone.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/diagnose-standalone.js). The pinned compiler/runtime agreement for serialized widths is [compiler.ts](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/compiler.ts#L56-L159) and [runtime.ts](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/runtime.ts#L565-L760).

## Fixtures

| Committed fixture or test control | Claim pinned |
|---|---|
| [f-spread-order](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/raw/f-spread-order/encoded.js) | Ordinary fixed/spread call operand order. |
| [focused-call-method-spread](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/focused/focused-call-method-spread/encoded.js) | Method-call receiver and spread-form metadata. |
| [focused-new-spread](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/focused/focused-new-spread/encoded.js) | Constructor and spread payload boundaries. |
| [f-closures-state](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/raw/f-closures-state/encoded.js) | Closure capture-pair and counted payload boundaries. |
| [unknown-opcode](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/negative/unknown-opcode/encoded.js), [truncated-wordcode](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/negative/truncated-wordcode/encoded.js), and [extra-trailing-word](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/negative/extra-trailing-word/encoded.js) | Atomic decline for unknown, truncated, or incompletely consumed word streams. |
| [read-wordcode.test.js](../../../../decoder/decode-js/test/vm/jsconfuser-vm/read-wordcode.test.js) | Synthetic opcode-only rows, full word consumption, deep freezing, and reader-level atomic decline controls. |
| [analyze-anti-runtime.test.js](../../../../decoder/decode-js/test/vm/jsconfuser-vm/analyze-anti-runtime.test.js) | Source-admitted truncated and unknown synthetic words decline at the word reader and through standalone decoding; valid runtime metadata remains producer-owned. |
| [owned-chain-source.test.js](../../../../decoder/decode-js/test/vm/jsconfuser-vm/owned-chain-source.test.js) | B2: unknown word/truncated call reach B first and public wordcode-declined; B4: for-in succeeds behaviorally, without certifying all tags/normalizer consumers. |
