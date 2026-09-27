# Canonical instruction set

This is the pinned `OP_ORIGINAL` conversion table for `js-confuser-vm` tag `0.1.5`. Each row is
paired with a compiler definition/emitter and a runtime handler in the machine-readable census.
The table is a semantic inventory, not a list of independent encoder transforms.

## 1. Target

Give later target-local tooling one canonical name, numeric opcode, symbolic operand form,
serialized operand form, and width for every instruction row. Baseline recovery may implement only
rows classified as `core`; `PATCH` is retained as a hardening-only row outside the unhardened
baseline.

## 2. Algorithm

The compiler emits symbolic operands first. Finalization replaces register, label, and constant
placeholders; the serializer writes the opcode and operands as 32-bit words. A static consumer
must use the row's operand grammar, consume the entire instruction, and reject unknown or
truncated streams. Variable-width rows are parsed from their count or descriptor, never by scanning
until a convenient next opcode.

`EXP` is numerically 60 even though it appears beside the arithmetic definitions. Opcode numbers
are canonical at this pin; randomized or shuffled maps are hardening variants.

`CALL`, `CALL_METHOD`, and `NEW` each have both fixed-arity and spread forms. Fixed arity consumes
`argc` register words; the spread form uses `CALL_SPREAD = 65535` followed by exactly one
array-register word. Each form needs a source-backed compiler emitter and runtime handler.

## 3. Implementation

| Opcode | Name | Semantic family | Symbolic IR operands | Serialized words after `op` | Width | Class |
|---:|---|---|---|---|---:|---|
| 0 | `LOAD_CONST` | literal/constant load | `dst, constant(value)` | `dst, constIdx, concealKey` | 3 | core |
| 1 | `LOAD_INT` | immediate/PC seed | `dst, number or label` | `dst, u32` | 2 | core |
| 2 | `LOAD_GLOBAL` | global resolution | `dst, constant(name)` | `dst, constIdx, concealKey` | 3 | core |
| 3 | `LOAD_UPVALUE` | closure state | `dst, uvIdx` | `dst, uvIdx` | 2 | core |
| 4 | `LOAD_THIS` | receiver | `dst` | `dst` | 1 | core |
| 5 | `MOVE` | register move | `dst, src` | `dst, src` | 2 | core |
| 6 | `STORE_GLOBAL` | global mutation | `constant(name), src` | `constIdx, concealKey, src` | 3 | core |
| 7 | `STORE_UPVALUE` | closure mutation | `uvIdx, src` | `uvIdx, src` | 2 | core |
| 8 | `GET_PROP` | property read | `dst, obj, key` | `dst, obj, key` | 3 | core |
| 9 | `SET_PROP` | property mutation | `obj, key, val` | `obj, key, val` | 3 | core |
| 10 | `DELETE_PROP` | property deletion | `dst, obj, key` | `dst, obj, key` | 3 | core |
| 11 | `ADD` | arithmetic | `dst, src1, src2` | `dst, src1, src2` | 3 | core |
| 12 | `SUB` | arithmetic | `dst, src1, src2` | `dst, src1, src2` | 3 | core |
| 13 | `MUL` | arithmetic | `dst, src1, src2` | `dst, src1, src2` | 3 | core |
| 14 | `DIV` | arithmetic | `dst, src1, src2` | `dst, src1, src2` | 3 | core |
| 15 | `MOD` | arithmetic | `dst, src1, src2` | `dst, src1, src2` | 3 | core |
| 60 | `EXP` | arithmetic | `dst, src1, src2` | `dst, src1, src2` | 3 | core |
| 16 | `BAND` | bitwise arithmetic | `dst, src1, src2` | `dst, src1, src2` | 3 | core |
| 17 | `BOR` | bitwise arithmetic | `dst, src1, src2` | `dst, src1, src2` | 3 | core |
| 18 | `BXOR` | bitwise arithmetic | `dst, src1, src2` | `dst, src1, src2` | 3 | core |
| 19 | `SHL` | bitwise arithmetic | `dst, src1, src2` | `dst, src1, src2` | 3 | core |
| 20 | `SHR` | bitwise arithmetic | `dst, src1, src2` | `dst, src1, src2` | 3 | core |
| 21 | `USHR` | bitwise arithmetic | `dst, src1, src2` | `dst, src1, src2` | 3 | core |
| 22 | `LT` | relational | `dst, src1, src2` | `dst, src1, src2` | 3 | core |
| 23 | `GT` | relational | `dst, src1, src2` | `dst, src1, src2` | 3 | core |
| 24 | `LTE` | relational | `dst, src1, src2` | `dst, src1, src2` | 3 | core |
| 25 | `GTE` | relational | `dst, src1, src2` | `dst, src1, src2` | 3 | core |
| 26 | `EQ` | strict equality | `dst, src1, src2` | `dst, src1, src2` | 3 | core |
| 27 | `NEQ` | strict equality | `dst, src1, src2` | `dst, src1, src2` | 3 | core |
| 28 | `LOOSE_EQ` | loose equality | `dst, src1, src2` | `dst, src1, src2` | 3 | core |
| 29 | `LOOSE_NEQ` | loose equality | `dst, src1, src2` | `dst, src1, src2` | 3 | core |
| 30 | `IN` | membership | `dst, src1, src2` | `dst, src1, src2` | 3 | core |
| 31 | `INSTANCEOF` | prototype relation | `dst, src1, src2` | `dst, src1, src2` | 3 | core |
| 32 | `UNARY_NEG` | numeric unary | `dst, src` | `dst, src` | 2 | core |
| 33 | `UNARY_POS` | numeric unary | `dst, src` | `dst, src` | 2 | core |
| 34 | `UNARY_NOT` | logical unary | `dst, src` | `dst, src` | 2 | core |
| 35 | `UNARY_BITNOT` | bitwise unary | `dst, src` | `dst, src` | 2 | core |
| 36 | `TYPEOF` | typeof | `dst, src` | `dst, src` | 2 | core |
| 37 | `VOID` | void/evaluation | `dst, src` | `dst, src` | 2 | core |
| 38 | `TYPEOF_SAFE` | safe global typeof | `dst, constant(globalName)` | `dst, constIdx, concealKey` | 3 | core |
| 39 | `JUMP` | direct control flow | `label(target)` | `targetPc` | 1 | core |
| 40 | `JUMP_IF_FALSE` | conditional control flow | `src, label(target)` | `src, targetPc` | 2 | core |
| 41 | `JUMP_IF_TRUE` | conditional control flow | `src, label(target)` | `src, targetPc` | 2 | core |
| 42 | `CALL` | plain call | `dst, callee, argc or spreadSentinel, args or arrayReg` | `dst, callee, argc or 65535, args... or arrayReg` | variable | core |
| 43 | `CALL_METHOD` | method call | `dst, receiver, callee, argc or spreadSentinel, args or arrayReg` | `dst, receiver, callee, argc or 65535, args... or arrayReg` | variable | core |
| 44 | `NEW` | constructor call | `dst, callee, argc or spreadSentinel, args or arrayReg` | `dst, callee, argc or 65535, args... or arrayReg` | variable | core |
| 45 | `RETURN` | function return | `src` | `src` | 1 | core |
| 46 | `THROW` | exception throw | `src` | `src` | 1 | core |
| 47 | `MAKE_CLOSURE` | closure creation | `dst, label(entry), paramCount, fnRegCount, uvCount, hasRest, capture pairs` | `dst, startPc, params, regs, uvCount, hasRest, pairs...` | variable | core |
| 48 | `BUILD_ARRAY` | array construction | `dst, count, elemRegs` | `dst, count, elemRegs...` | variable | core |
| 49 | `BUILD_OBJECT` | object construction | `dst, pairCount, key/value regs` | `dst, pairCount, keyReg, valReg...` | variable | core |
| 50 | `DEFINE_GETTER` | accessor definition | `obj, key, fn` | `obj, key, fn` | 3 | core |
| 51 | `DEFINE_SETTER` | accessor definition | `obj, key, fn` | `obj, key, fn` | 3 | core |
| 52 | `FOR_IN_SETUP` | for-in setup | `dst, src` | `dst, src` | 2 | core |
| 53 | `FOR_IN_NEXT` | for-in iteration | `dst, iter, label(exit)` | `dst, iter, exitPc` | 3 | core |
| 54 | `TRY_SETUP` | catch setup | `label(handler), exceptionReg` | `handlerPc, exceptionReg` | 2 | core |
| 55 | `TRY_END` | handler disarm | none | none | 0 | core |
| 56 | `PATCH` | self-modifying hardening | `destPc, sliceStart, sliceEnd, key` | `destPc, sliceStart, sliceEnd, key` plus opaque region | variable | hardening-only |
| 57 | `DEBUGGER` | debug statement | none | none | 0 | core |
| 58 | `JUMP_REG` | unconditional indirect/finally control flow | `src` | `src` | 1 | core |
| 59 | `FINALLY_SETUP` | finally setup | `label(finally), contReg, payloadReg, label(throwPad)` | `finallyPc, contReg, payloadReg, throwPadPc` | 4 | core |

This table is the opcode reference for source and runtime semantics. Every row requires a
compiler definition/emitter and a runtime handler; absence from one sample is no dead-code proof.

## 4. Downstream Effects

Register, label, and constant resolution changes symbolic operands into numeric words. Constant
rows therefore carry the value/key pair, label rows carry PCs, and variable-width rows carry
counts or descriptors. Runtime dispatch consumes the same grammar. A later optional pass may
rewrite the representation, but it does not change the baseline table's meaning.

## 5. Known Quirks

- The row order in source is not numeric order because `EXP` is 60 and the hardening `PATCH` row
  occupies 56.
- `PATCH` has a canonical header shape but an opaque self-modifying region; it is not an
  unhardened-baseline row.
- No table row is complete without both its compiler emitter and runtime handler source; the pinned
  source section above identifies those locations.

## Source

Opcode definitions are in [compiler.ts](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/compiler.ts#L56-L159); dispatch and handlers are in [runtime.ts](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/runtime.ts#L276-L900).

## Fixtures

No committed fixtures pin this table. Qualification must regenerate samples from the pinned
source and retain their provenance with the resulting evidence.
