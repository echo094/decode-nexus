# js-confuser-vm - Virtualization Reference

Reference for the read-only `js-confuser-vm` encoder at tag `0.1.5`, commit
`20c5b96bf57337c568579352758d7685358650de`.

The pinned encoder's [option behavior matrix](options.md) records which settings change
the visible numeric representation used by the current decoder fixtures.

This package describes the target's one virtualization system: source is lowered to symbolic
instructions, finalized into a flat word stream, and shipped with the interpreter that gives that
stream meaning. It is intentionally not a general JavaScript VM guide and it does not document
optional hardening as completed coverage.

## Scope and baseline

The accepted baseline vector disables opcode randomization and shuffling, bytecode and constant
concealment, macro, specialized, and aliased opcodes, self-modification, dispatcher and control
flow flattening, runtime reshaping, minification, anti-instrumentation, timing checks, handler
tables, and other optional hardening. Required compilation, register and label resolution,
constant pooling, serialization, runtime construction, frames, calls, closures, and exceptions
remain enabled.

The release and vector are fixed by the pinned source. Claims about another release or a
hardened vector require separate evidence.

## Skill Layout

```
skills/js-confuser-vm/
  js-confuser-vm.md       package index, compiler order, and runtime flow
  container-wordcode.md   emitted container, words, slots, and binding contract
  instruction-set.md      canonical opcode and operand conversion table
```

The package records emitted shapes and ordering without treating source or comments as a reversal
oracle.

## Compiler and runtime model

The core path is:

```
source
  -> Babel script AST
  -> symbolic IR and function descriptors
  -> optional IR transforms
  -> concealConstants structural expansion
  -> resolveRegisters
  -> optional selfModifying pass
  -> resolveLabels
  -> resolveConstants
  -> flat wordcode, constants, roots, maps, and frame metadata
  -> runtime AST construction and generation
```

`concealConstants` is a mandatory structural pass: constant operands become value/key pairs even
when the value-concealment option is disabled. The option controls whether those values are hidden;
it does not remove the pair shape. Register resolution must precede label and constant resolution.
The compiler also removes pseudo-instructions before serialization.

At runtime, the generated code decodes encoded bytes only when the encoded-word option is enabled,
constructs a `VM`, creates a root `Closure`, pushes a frame, dispatches by program counter, and
returns the result from the root frame. Raw numeric `BYTECODE` arrays are already words and are
not little-endian byte arrays.

The compiler and runtime are separate evidence paths:

```
BOOT globals -> decodeBytecode(BYTECODE) -> VM(wordcode, constants, globals)
             -> Closure(startPc, regCount) -> frame push -> dispatch loop
             -> RETURN -> close upvalues -> root result
```

The target's own instruction handlers are the semantic source of truth. The complete canonical
table, including variable-width calls, closures, arrays, objects, and exception setup, is in
[instruction-set.md](instruction-set.md). The surrounding binding and serialization contract is
in [container-wordcode.md](container-wordcode.md).

## Core versus hardening

Virtualization is one encoder transform with internal layers, not one pipeline stage per opcode.
The core layers are lowering, instruction selection, register and frame allocation, labels,
constants, serialization, and runtime construction. Optional passes may rename bindings, add
words, alter dispatch, or rewrite the representation; they are outside this reference's accepted
boundary.

The `PATCH` opcode is classified as hardening-only at this pin because its meaningful region is
self-modifying. It is present in the canonical census but is not a baseline implementation
requirement. `DEBUGGER` is a core statement opcode even though it has no VM value result.

## Known quirks

- A stale `u16` comment appears near opcode allocation. The executable serializer and runtime
  decode use unsigned 32-bit words.
- `U16_MAX` is used for opcode or sentinel allocation, not as the serialized word width.
- The `CALL_SPREAD` sentinel is `65535` in the accepted baseline. It is an operand value, not a
  claim that every word is 16 bits.
- Debug or disassembly comments are useful for inspection but are not part of the container
  contract.

## Source

The pinned source is [MichaelXF/js-confuser-vm at 0.1.5](https://github.com/MichaelXF/js-confuser-vm/tree/20c5b96bf57337c568579352758d7685358650de). The compiler flow is wired by
[src/index.ts](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/index.ts#L7-L13)
and [src/compiler.ts](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/compiler.ts#L3276-L3444). The runtime boot and dispatch are in
[src/runtime.ts](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/runtime.ts#L23-L36)
and [src/runtime.ts](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/runtime.ts#L950-L976).

## Fixtures

No committed fixtures pin this encoder description. Qualification must regenerate samples from
the pinned source and keep their provenance with the resulting evidence.
