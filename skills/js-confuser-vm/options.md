# js-confuser-vm 0.1.5 option behavior

## Verdict

The explicit reference vector disables every representation-changing option. `target` is a
no-effect selector, while `verbose` and `profile` are instrumentation-only. Core compilation,
register/label/constant resolution, serialization, and runtime construction remain active.

## Option-to-effect matrix

| Option | Source evidence | Effect on the visible numeric baseline |
|---|---|---|
| `target` | `src/options.ts:3-5`; no `options.target` use in `src/` | no-effect selector |
| `randomizeOpcodes` | `src/compiler.ts:390-400,404-417`; `src/utils/op-utils.ts:19-28`; `src/utils/frame-layout.ts:87-105` | changes the emitted representation |
| `shuffleOpcodes` | `src/build-runtime.ts:78-81`; `src/transforms/runtime/shuffleOpcodes.ts` | changes the emitted representation |
| `encodeBytecode` | `src/compiler.ts:3198-3206,3224-3228`; `src/runtime.ts:23-31` | changes the emitted representation |
| `concealConstants` | `src/transforms/bytecode/resolveConstants.ts:66-84`; `src/runtime.ts:230-267` | changes the emitted representation; constant-pair expansion is core |
| `controlFlowFlattening` | `src/compiler.ts:3297-3303`; `src/transforms/bytecode/controlFlowFlattening.ts` | changes the emitted representation |
| `dispatcher` | `src/compiler.ts:3305-3310`; `src/transforms/bytecode/dispatcher.ts` | changes the emitted representation |
| `stringConcealing` | `src/compiler.ts:3290-3295`; `src/transforms/bytecode/stringConcealing.ts` | changes the emitted representation |
| `macroOpcodes` | `src/compiler.ts:3333-3338`; `src/build-runtime.ts:63-66` | changes the emitted representation |
| `specializedOpcodes` | `src/compiler.ts:3326-3331`; `src/build-runtime.ts:58-61` | changes the emitted representation |
| `aliasedOpcodes` | `src/compiler.ts:3340-3345`; `src/build-runtime.ts:68-71` | changes the emitted representation |
| `antiInstrumentation` | `src/compiler.ts:3317-3324`; `src/build-runtime.ts:73-76` | changes the emitted representation |
| `selfModifying` | `src/compiler.ts:3403-3407,3415-3419`; `src/transforms/bytecode/selfModifying.ts` | changes the emitted representation |
| `timingChecks` | `src/compiler.ts:3234-3240`; `src/runtime.ts:256-268` | changes the emitted representation |
| `classObfuscation` | `src/build-runtime.ts:87-90`; `src/transforms/runtime/classObfuscation.ts` | changes the emitted representation |
| `handlerTable` | `src/build-runtime.ts:83-85`; `src/transforms/runtime/handlerTable.ts` | changes the emitted representation |
| `minify` | `src/build-runtime.ts:106-120`; `src/minify.ts` | changes the emitted representation |
| `verbose` | `src/compiler.ts:353-356,3371-3390`; `src/build-runtime.ts:40-55` | baseline instrumentation |
| `profile` | `src/compiler.ts:3382-3386`; `src/build-runtime.ts:47-51`; `src/types.ts:117-160` | baseline instrumentation |

`DEFAULT_OPTIONS` is `{}` (`src/options.ts:100`), so omitted options do not introduce hidden true
defaults. The tracked reference input uses this explicit option vector.

## Mandatory unguarded core

`concealConstants` is called unconditionally in `compileAndSerialize` (`src/compiler.ts:3312-3315`),
but it only adds a zero concealment key when `concealConstants` is false. `resolveConstants` is also
always called (`src/compiler.ts:3412-3413`), followed by serializer validation and emission
(`src/compiler.ts:3209-3272`) and runtime construction (`src/compiler.ts:3422-3444`). These are
core layers, not optional hardening. The emitted reference therefore has numeric u32 wordcode,
constant-pool indexes paired with key zero, root PC/register metadata, opcode/sentinel/frame-layout
metadata, and the canonical interpreter runtime.

The complete false-vector order is:

1. Source compilation and lowering into virtual bytecode (`src/compiler.ts:3282-3284`).
2. Optional string-concealing, CFF, and dispatcher passes are skipped.
3. Unconditional constant-pair expansion runs; with `concealConstants: false`, each constant
   operand carries key zero (`src/compiler.ts:3312-3315`,
   `src/transforms/bytecode/resolveConstants.ts`).
4. Optional anti-instrumentation, specialized, macro, and aliased passes are skipped.
5. Virtual registers resolve to concrete frame slots (`src/compiler.ts:3399-3401`).
6. Optional self-modifying patch generation is skipped.
7. Labels resolve to concrete program counters (`src/compiler.ts:3409-3410`).
8. Constants resolve to pool indexes and concealment-key operands
   (`src/compiler.ts:3412-3413`).
9. Optional patch encryption is skipped, then serializer validation/emission produces numeric
   u32 wordcode and runtime metadata (`src/compiler.ts:3415-3423`,
   `src/compiler.ts:3179-3228`).
10. Runtime source is parsed and generated; the required leading debug-comment block is prepended
    by the final runtime builder (`src/build-runtime.ts:20-29,94-101`). The comments are baseline
    instrumentation outside the production decoder input because the reference cell records both
    debug-bearing and comment-stripped forms.

The generated runtime is therefore core even though its optional hardening passes are all disabled.
The comment block is semantically external instrumentation: it is emitted by the pinned encoder and
must be removed at the decoder boundary before production source recovery.
