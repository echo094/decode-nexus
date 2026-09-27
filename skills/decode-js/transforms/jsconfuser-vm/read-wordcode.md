# Read numeric wordcode

## 1. Target

Parse the copied numeric word stream from `jsconfuser-vm-container.v1` into immutable
`jsconfuser-vm-wordcode.v1` instructions with both serialized and semantic operand views. This
pass is parse-only: it establishes boundaries and arity, not register ownership or control-flow
validity.

## 2. Algorithm

First require numeric encoding, a non-empty unsigned-u32 word array, the canonical opcode map,
the `CALL_SPREAD` sentinel, and a main entry at PC zero. A cursor consumes the opcode at the
current PC and dispatches by canonical name.

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
invalid count/flag, hardening-only `PATCH`, or trailing word declines.

## 3. Implementation

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
sentinel is exactly `65535`; the sentinel takes the spread form **before** any ordinary count
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

`wordOperands` mirrors **every serialized word after `op`**, tagging register, label target,
constant index, constant key, upvalue index, immediate, spread sentinel, capture kind, or capture
index. `operands` groups related words into semantic objects: notably `(c,k)` becomes one
`constant-ref`, while a closure capture pair becomes one `{kind:local|upvalue,index,isLocal}`
object. These two arrays therefore need not have equal lengths. For example, words
`[0, 2, 7, 0]` are `LOAD_CONST` at PC 0, width 4, next PC 4, with serialized operands
`register(2), constant-index(7), constant-key(0)` and semantic operands
`register(2), constant-ref(7,0)`. This parse alone does not assert that pool entry 7 exists.

The cursor algorithm is: validate the container and each read word; take the opcode at `pc`;
select its row; check that fixed operands or the selected counted payload fit; consume exactly
that row; record `nextPc = pc + width`; repeat at `nextPc` until it equals `wordCount`. A payload
word equal to an opcode is still payload. `MAKE_CLOSURE` rejects nonboolean flags, and all
counted forms reject truncation before constructing an instruction. Unknown opcode and `PATCH`
decline the whole stream. Later passes, beginning with
[reference validation](validate-references.md), decide whether the parsed references and machine
semantics are valid.

The result has schema `jsconfuser-vm-wordcode.v1`, `encoding: "numeric-u32"`, copied `words`,
`wordCount`, ordered `instructions`, `instructionCount`, `consumedWords`, and `nextPc`. Each
instruction contains `pc`, `name`, `{ name, value }` opcode metadata, `operands`, `wordOperands`,
copied `words`, `width`, and `nextPc`. Calls additionally expose `form`, `arguments`,
`destination`, `callee`, `receiver`, and serialized argument offset; closures expose
`functionMeta`, `captures`, `capturePairs`, and destination; arrays and objects expose their
counted forms.

`diagnoseWordcode` returns a deep-frozen success/diagnostic envelope. `readWordcode` returns the
frozen result or `null`; it never repairs, mutates, or executes input. Width is defined by the
canonical grammar, so an operand that happens to resemble a later opcode is still payload when
the current instruction says it is payload.

## 4. Upstream Effects

The reader consumes the `roles.words`, `roles.op`, and `roles.sentinels` values from
[extract-container.md](extract-container.md). It supplies contiguous instruction boundaries,
typed operand identity, and variable-form metadata to [validate-references.md](validate-references.md)
and every later target-local pass. No later pass should rescan the raw array with guessed widths.

## 5. Known Gaps

- Encoded bytecode and `PATCH`/optional hardening forms are rejected rather than decoded by an
  assumed inverse.
- Register ranges, constant indexes, label targets, frame layout, and function ownership are
  intentionally validated by later passes.
- This reader recognizes the pinned canonical opcode values; randomized or shuffled opcode maps
  need a separately evidenced decoder shape.

## Source

The active parser and result contract are [read-wordcode.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/read-wordcode.js#L448-L816). The standalone call site is [diagnose-standalone.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/diagnose-standalone.js#L397-L402). The pinned compiler/runtime agreement for serialized widths is [compiler.ts](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/compiler.ts#L56-L159) and [runtime.ts](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/runtime.ts#L565-L760).

## Fixtures

| Committed fixture or test control | Claim pinned |
|---|---|
| [f-spread-order](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/raw/f-spread-order/encoded.js) | Ordinary fixed/spread call operand order. |
| [focused-call-method-spread](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/focused/focused-call-method-spread/encoded.js) | Method-call receiver and spread-form metadata. |
| [focused-new-spread](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/focused/focused-new-spread/encoded.js) | Constructor and spread payload boundaries. |
| [f-closures-state](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/raw/f-closures-state/encoded.js) | Closure capture-pair and counted payload boundaries. |
| [unknown-opcode](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/negative/unknown-opcode/encoded.js), [truncated-wordcode](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/negative/truncated-wordcode/encoded.js), and [extra-trailing-word](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/negative/extra-trailing-word/encoded.js) | Atomic decline for unknown, truncated, or incompletely consumed word streams. |
| [read-wordcode.test.js](../../../../decoder/decode-js/test/vm/jsconfuser-vm/read-wordcode.test.js) | Synthetic opcode-only rows, full word consumption, deep freezing, and reader-level atomic decline controls. |
