# Fixed-opcode disassembly

Evidence label: source-inspection only. This page is the E2 reconstruction contract for the
frozen VM-1 word grammar. It documents fixed numeric interpretation, not handler analysis,
randomized-opcode inference, execution, or generalized VM support.

## 1. Target

Convert E1's word array and constant pool into instruction descriptors keyed by bytecode program
counter. Decode operands, keyed literals, calls, objects, functions, closures, control transfers,
exception markers, and special operations sufficiently for static function/CFG discovery and the
two emitters.

The discriminator is membership in the hard-coded numeric `OP`, `BINOP`, `UNOP`, `VOID_OP`, and
spread-sentinel tables. Known `CODE_COPY` is a normal descriptor. A numeric word absent from all
tables is an unknown opcode and throws in the production decoder.

## 2. Algorithm

1. Use the frozen opcode/operator tables and the exact spread sentinel
   `1609168361`. For each instruction, set `start` to the current PC, read the opcode, and use a
   local reader that advances the PC one word per operand.
2. For a constant pair `(e, g)`, call `decodeConst`. If `g` is falsy, return `consts[e]`; otherwise
   XOR numbers with `g`, or decode a base64 string into little-endian 16-bit characters and XOR
   character `k` with `(g + k) & 65535`.
3. Decode the fixed-width operation cases: loads, moves, global/upvalue/member operations, `POW`,
   unary/binary operators, `TYPEOF_GLOBAL`, jumps, returns/throws, exception markers, dynamic
   jump, `CODE_COPY`, and debugger.
4. Decode variable tails. `CALL`, `CALL_METHOD`, and `NEW` read their destination/function (and
   receiver for methods), argument count, and either a register list or one spread register.
   `DEFINE_FUNCTION` reads destination, child entry, parameter count, frame size, rest flag,
   capture count, an additional metadata word, and capture pairs. Arrays and objects read their
   length/count tails.
5. Store the descriptor's `size` as words consumed. `disassemble` records it at the start PC and
   advances by `size` until `pc >= words.length`.

## 3. Implementation

### Fixed descriptor schema

| Opcode family | Descriptor fields and consumed shape |
| --- | --- |
| `LOAD_CONST` | `f`, decoded `k` from `(constIndex,key)` |
| `LOAD_IMM` | `f`, immediate `k` |
| `LOAD_GLOBAL`, `TYPEOF_GLOBAL` | `f`, decoded global `name` |
| `LOAD_UPVAL` | `f`, upvalue `idx` |
| `LOAD_THIS` | `f` |
| `MOVE` | `f`, source `src` |
| `STORE_GLOBAL` | decoded `name`, source `src` |
| `STORE_UPVAL` | `idx`, source `src` |
| `GET_PROP`, `SET_PROP`, `DELETE_PROP` | destination where applicable and register `obj`, `key`, `val` fields |
| `POW` and tabled binary operations | `f`, `a`, `b` |
| tabled unary operations and `VOID_OP` | `f`, `a` |
| `JUMP` | `target` |
| `JUMP_IF_FALSE`, `JUMP_IF_TRUE` | condition `cond`, `target` |
| `CALL` | `f`, `fn`, `args: { list }` or `{ spread }` |
| `CALL_METHOD` | `f`, `recv`, `fn`, and list/spread `args` |
| `NEW` | `f`, `fn`, and list/spread `args` |
| `RETURN`, `THROW` | value `val` |
| `DEFINE_FUNCTION` | `f`, child entry `fT`, params `fl`, frame `fi`, capture count, rest flag `fJ`, and `caps: [{ Y, M }]` |
| `NEW_ARRAY` | `f`, `elems` of declared length |
| `NEW_OBJECT` | `f`, `pairs: [{ k, v }]` of declared count |
| getter/setter | `obj`, `key`, `fn` |
| `FORIN_INIT` | `f`, `obj` |
| `FORIN_NEXT` | `f`, iterator `iter`, `target` |
| `TRY_CATCH` | `catchPc`, `catchReg` |
| `TRY_POP` | no operands |
| `TRY_FINALLY` | `W`, `V`, `Z`, `aa` |
| `CODE_COPY` | `dst`, `lo`, `hi` |
| `JUMP_DYN` | register `reg` |
| `DEBUGGER` | no operands |

The `DEFINE_FUNCTION` source reads the capture count after `fi`, then reads the rest flag into
`ins.fJ`, followed by that many `{ Y, M }` capture pairs. The descriptor field used by E3 is the
rest flag. The diagnostic decoder names the same fields `T`, `l`, `i`, `J`, and `caps`.

### Concrete decoder state and tables

`decodeInstr` begins with `pc = start`, reads `op`, and builds `{ op, start }`. Each switch case
advances `pc` through `rd()`; the final `ins.size = pc - start`. The production map contains
[loads/moves](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-1/vm.js#L35-L45),
[arithmetic/control](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-1/vm.js#L47-L68),
and [debugger](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-1/vm.js#L69);
`BINOP` maps addition through `instanceof`, `UNOP` maps negation through `typeof`, and `VOID_OP`
is `34224`.
The operand width is therefore an operation-specific property, not a universal fixed stride.

`readArgs(rd, argc)` treats only the exact spread sentinel as spread. Every other unsigned word is
used as a loop bound to read that many registers. `decodeConst`'s string branch consumes two bytes
per character and masks the XOR result to 16 bits; its numeric branch follows JavaScript bitwise
XOR semantics.

### Source ownership

| Source span | Ownership | What it owns |
| --- | --- | --- |
| [`vm.js#L35-L83`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-1/vm.js#L35-L83) | owned algorithm | Production opcode/operator/sentinel tables and the block terminator set exported downstream. |
| [`vm.js#L152-L162`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-1/vm.js#L152-L162) | owned algorithm | Keyed numeric/string constant decoding. |
| [`vm.js#L167-L176`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-1/vm.js#L167-L176) | owned algorithm | PC-keyed linear disassembly and size advancement. |
| [`vm.js#L178-L264`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-1/vm.js#L178-L264) | owned algorithm | Fixed and variable operand layouts and unknown-opcode throw. |
| [`vm.js#L267-L272`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-1/vm.js#L267-L272) | owned algorithm | List/spread argument representation. |
| [`disasm.js#L73-L86`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-1/disasm.js#L73-L86), [`disasm.js#L157-L252`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-1/disasm.js#L157-L252) | delegated diagnostic helper | Duplicate decoder that returns a size-one unknown descriptor instead of throwing. |
| [`vm.js#L479-L484`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-1/vm.js#L479-L484) | shared coordinator | Injects tables and Babel helpers into downstream emitters. |

## 4. Upstream Effects

E2 consumes E1's `Uint32Array` and ordered static constants. It assumes the bytes use the source's
little-endian word packing and that the constant indices/keys are meaningful under the fixed
grammar. It does not consume or produce an interpreter handler table.

E3 consumes descriptor `start`, `size`, `op`, static targets, and `DEFINE_FUNCTION` metadata. E4
and E5 consume the register fields, decoded values, captures, handler records, dynamic target
register, and variable argument representation. Consequently E2's descriptor schema must retain
known operations even when a later emitter cannot lift them: `CODE_COPY` is known and reaches E4/E5,
whereas an unknown numeric opcode never reaches either emitter.

The E2 production throw is outside the driver's structured-emitter `try` block. This is the source
reason an unknown opcode is not rescued by the dispatcher fallback; [fallback and validation](vm-1-fallback-validation.md)
owns the driver-level consequence.

## 5. Known Gaps

- The opcode numbers, operator maps, operand widths, spread sentinel, frame conventions, and
  keyed-constant format are frozen sample observations. No randomized or inferred map is present.
- The production decoder has no independent bounds, count, alignment, checksum, or descriptor
  consistency validation. Linear progress relies on each case's consumed width.
- Production unknown values throw `Unknown opcode <op> at pc <start>` before E6's structured catch.
  The diagnostic decoder's unknown descriptor is a debug-tool behavior, not recovery.
- `CODE_COPY` decodes as a known descriptor but has no source semantics in either emission path;
  its separate marker/decline boundary is documented by [dual emission](vm-1-dual-emission.md).
- The source-backed opcode description does not establish behavioral equivalence, transfer, or
  runtime safety.

## Source

| File | Pinned source | Role |
| --- | --- | --- |
| `VM-1/vm.js` | [`tables`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-1/vm.js#L35-L83), [`constants and walk`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-1/vm.js#L152-L176), [`decoder`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-1/vm.js#L178-L272) | Production fixed interpretation. |
| `VM-1/disasm.js` | [`diagnostic decoder`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-1/disasm.js#L73-L252) | Diagnostic duplicate and unknown continuation. |

## Fixtures

No maintained fixture is created or decoded here.

| Corpus artifact | Claim it pins | Evidence status |
| --- | --- | --- |
| `VM-1/input.js` | Released encoded word stream and constant pool | Fixture evidence only; not decoded. |
| `VM-1/disasm.js` | Diagnostic spelling of the fixed grammar and unknown descriptor | Source/diagnostic provenance. |
| `VM-1/output.js` | Downstream generated literals | Generated-output provenance only. |
| `VM-1/test.js` | Intended decoded-string and no-bytecode-marker checks | Test-intent evidence; no result is claimed. |
