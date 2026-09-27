# Container and wordcode

The pinned `js-confuser-vm` output is a JavaScript container whose declarations, binding graph,
and runtime boot jointly define the virtual program. This document records the emitted contract.

## 1. Target

Describe the minimum unhardened container and flat wordcode shape produced by tag `0.1.5` so later
work can identify complete output roles and avoid using generated names or comments as structural
evidence.

## 2. Algorithm

The encoder allocates virtual registers and symbolic labels, interns constants, patches function
descriptors, flattens instructions, and builds a runtime around the result. A serialized word is
an unsigned 32-bit value. When `ENCODE_BYTECODE` is true, each word is encoded as four
little-endian bytes and reconstructed with a `Uint32Array`; when it is false, the emitted numeric
array is already the word stream.

Constant operands use a value/key pair after the mandatory `concealConstants` structural pass.
The baseline vector uses visible values and a zero key. This pair must still be consumed by a
static reader; treating every constant reference as one word shifts the remainder of the stream.

Fixed-width operations have the widths in [instruction-set.md](instruction-set.md). Calls,
closures, arrays, and objects are variable width and carry their counts or descriptors in the
stream. The `CALL_SPREAD` sentinel is `65535`; it selects the spread branch for `CALL`, `CALL_METHOD`, and
`NEW` and is not a word-width marker.

## 3. Implementation

### Container declarations

The accepted core boundary contains, by role rather than generated spelling:

- a heterogeneous `CONSTANTS` pool and flat numeric `BYTECODE` array;
- `MAIN_START_PC`, `MAIN_REG_COUNT`, `ENCODE_BYTECODE`, `TIMING_CHECKS`, `HEADER_SIZE`, and
  `FRAME_START` roots or equivalent role bindings;
- an opcode map with exactly the 61 canonical operation keys and values at this pin (`0..60`,
  including `EXP=60` and hardening-only `PATCH=56`);
- a `SENTINELS` map containing `CALL_SPREAD`;
- a `SLOTS` map containing `PC`, `CALLER`, `RET_DST`, `THIS`, `CLOSURE`, `HANDLERS`,
  `FRAME_SIZE`, and `REG_BASE`;
- `Closure`, `VM`, and upvalue machinery with registers, frame state, wordcode, constants, and
  globals; and
- a root call equivalent to `vm.run(new Closure({ startPc, regCount }), undefined, null)`.

The scalar roots are validated by their uses, not just their values: the main start PC and register
count must feed the root closure, frame/header scalars must agree with frame construction, and the
bytecode mode/timing flags must occupy their expected runtime branches. The runtime graph must also
connect constructors, dispatch methods, register/frame state, closure/upvalue state, handler state,
wordcode, constants, and the root boot call. The binding graph may be renamed. A complete
binding/name variation is valid; missing, duplicate, ambiguous, altered-map, altered-slot,
altered-boot, or disconnected graph roles decline before mutation.

### Frame and function records

The frame layout reserves slot zero for the host/result sentinel and uses `FRAME_START = 1` in the
accepted baseline. `MAKE_CLOSURE` records destination, entry PC, parameter count, register count,
upvalue count, rest flag, and local/upvalue capture pairs. Calls either link a VM frame or invoke a
host callable; returns close upvalues and place the result in the caller's destination.

Exception state is frame-local. `TRY_SETUP`, `TRY_END`, `FINALLY_SETUP`, `JUMP_REG`, `THROW`, and
the `HANDLERS` slot must be treated as one contract, not as unrelated opcode cases.

### Contract completeness

The emitted core container is complete only when all of the following hold:

1. every required role has one unambiguous binding and all references resolve;
2. pool, roots, maps, slots, frame metadata, and boot call have the expected types;
3. every word is an unsigned 32-bit value and every instruction consumes its complete arity;
4. constants, registers, labels, function records, capture pairs, and handler edges are in range;
5. no unknown, truncated, extra, duplicated, or unsupported hardened region is present; and
6. the root and every nested function have complete boundaries and a consistent frame contract.

## 4. Downstream Effects

The serializer runs after register, label, and constant resolution. Runtime construction then
parses and emits the interpreter, and optional runtime passes may rename or reshape bindings. The
emitted contract is therefore defined by roles and references rather than source-order
declarations. The debug build may add comments; the stripped build is the structural endpoint used
by the static checks.

## 5. Known Quirks

- `op-utils.ts` contains a stale-looking `u16` comment, but the executable serialization
  contract is unsigned 32-bit. The opcode allocator's `U16_MAX` is a separate concern.
- `BYTECODE` numeric arrays in the baseline are words. Little-endian byte decoding applies only to
  the encoded-byte option.
- `concealConstants` always creates value/key operand pairs, even when its value-hiding option is
  false.
- Hardened output may add randomization, concealment, patches, dispatcher code, handler tables,
  or timing logic. Those variants are excluded until separately evidenced.

## Source

The compiler's finalization and serializer are in [compiler.ts](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/compiler.ts#L3153-L3272), with the mandatory pass order in [compiler.ts](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/compiler.ts#L3276-L3444). Constant-pair expansion is in [concealConstants.ts](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/transforms/bytecode/concealConstants.ts#L4-L51), register resolution is in [resolveRegisters.ts](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/transforms/bytecode/resolveRegisters.ts#L34-L38), and byte decoding is in [runtime.ts](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/runtime.ts#L23-L36). Frame roles are defined in [frame-layout.ts](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/utils/frame-layout.ts#L41-L45).

## Fixtures

No committed fixtures pin this container description. Qualification must regenerate samples from
the pinned source and retain their provenance with the resulting evidence.
