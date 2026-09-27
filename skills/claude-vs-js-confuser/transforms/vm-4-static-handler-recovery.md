# VM-4 static handler-observation and frame-aware operation recovery

Evidence label: `source-inspection only`. This transform page reconstructs the pinned
VM-4 implementation; it does not implement, execute, or validate a decoder.

## 1. Target

Recover enough semantic operation information from VM-4's randomized register handlers that the
existing VM-4 disassembler, path engine, and JavaScript emitter can replace a sample-shaped VM with
ordinary JavaScript. The concrete input shape is a Babel-parsable JavaScript program containing a
numeric handler-assignment table, a bytecode reader, a decoder/pool, a frame constructor, an
embedded base64 word stream, and an entry function. The pinned `VM-4/input.js` has this shape; its
existing `output.js` shows the intended lifted form with decoded browser strings and a regular
`while` loop.

This transform owns the sample-specific boundary between handler source and operation records. It
does not own the general register VM substrate, later graph cleanup, or a claim that every handler
can be semantically recovered.

## 2. Algorithm

The algorithm is one cohesive static-observation pipeline:

1. **Establish the VM descriptor — shared coordinator with VM-4 layout facts.** `locateVM` scans
   the parsed AST for at least ten numeric handler assignments, structurally finds the operand
   reader, identifies the bytecode/stack/frame/PC fields, finds the decoder/pool, recognizes frame
   construction and entry metadata, and selects the longest base64 payload. `decodeConst` later
   turns numeric and encoded string pool entries into values. This stage produces a descriptor, not
   a semantic opcode table.

2. **Observe a handler as a symbolic state transition — VM-4-owned algorithm.** `runHandler`
   interprets handler ASTs against a symbolic mock. Register slots use symbolic markers; frame/VM
   field accesses, object members, assignments, calls, returns, throws, conditions, loops, and
   try-handling become symbolic expressions/effects. The operand-reader interception converts each
   handler operand fetch into a symbolic operand. A step bound and loop guard terminate the
   observation. No embedded payload instruction is run by this static oracle.

3. **Recover operand shape and provenance — VM-4-owned algorithm.** `probeStructure` compares
   observations from two operand bases to identify fixed versus variable arity, groups, and spread.
   `srcOf` and `upvalRef` retain whether a symbolic value came from a register, immediate, constant,
   global, upvalue, or frame slot. This prevents the classifier from treating a bytecode operand,
   a register value, and a frame field as interchangeable.

4. **Classify observed effects — VM-4-owned algorithm.** `classify` recognizes returns, throws,
   try/catch/finally operations, debugger, decrypt, jumps, global/this/upvalue/property operations,
   arrays/objects/functions, calls/new, for-in, and unary/binary expression forms. A residual write
   without a more specific semantic is represented as `ARITH`, with chronological register and
   immediate inputs extracted by `arithInputs`. An unrecognized shape remains `UNKNOWN` rather than
   receiving a guessed operation.

5. **Fit residual arithmetic per actual instruction — VM-4-owned algorithm.** `fitInstr` tests a
   bounded fixed candidate set of identity, unary, binary, and fused three-input forms. It uses the
   actual operand values and the current frame register count, whose header is 13 slots in the
   recovered VM-4 layout. The cache key includes opcode, register count, and actual operands, so
   size-dependent MBA variants are not collapsed into a single global rule. A fit is accepted only
   when all fixed trials agree; otherwise the result is absent.

6. **Consume records in control recovery — shared coordinator.** `disassemble` walks reachable
   variable-width instructions and nested functions, following known static edges and leaving
   register-computed jumps for the later engine. `makeEngine` evaluates the decoded subset and
   bounded pure VM calls. `explorePaths` creates trace nodes keyed by `(pc, abstract constant
   state)`, folds pure values, and forks recognized branch/try edges. `resolveIndirect` widens
   registers with more than eight values and retries, preserving the trace as the state model that
   lifting consumes.

7. **Lift and clean — shared coordinator.** `liftInstr` converts operation records and path-state
   values into JavaScript AST nodes. `generateBody` builds/prunes the graph, folds constants,
   removes dead stores, minimizes equivalent state partitions, substitutes temporaries, and
   structures dominators, loops, and try regions before readability cleanup and generation.

The key representation changes are:

`source AST -> VM descriptor -> symbolic handler observation -> classified operation record ->
frame/operand-specific instruction descriptor -> (pc,state) trace -> JavaScript AST -> generated
source`

The operation record is the handoff invariant: downstream code may consume its `kind`, operand
shape, source provenance, and fitted arithmetic, but cannot infer a missing semantic from the
generated output.

## 3. Implementation

| Stage | Source anchor | Produced/consumed shape | Ownership |
| --- | --- | --- | --- |
| Recognition and extraction | [`locateVM`, `56-297`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-4/vm.js#L56-L297); [`decodeConst`, `304-330`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-4/vm.js#L304-L330) | AST -> `{ handlers, reader, decoder, pool, code, entry }`-like descriptor | Shared coordinator plus VM-4 layout facts |
| Symbolic handler observation | [`runHandler`, `366-918`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-4/vm.js#L366-L918) | Handler AST -> symbolic values/effects; operand reader is intercepted at `715-741` | VM-4-owned |
| Shape/provenance | [`probeStructure`, `983-1005`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-4/vm.js#L983-L1005); [`srcOf`/`upvalRef`, `1011-1053`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-4/vm.js#L1011-L1053) | Two-base probe -> arity/spread; symbolic tree -> operand provenance | VM-4-owned |
| Semantic classification | [`classify`, `1061-1369`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-4/vm.js#L1061-L1369); [`arithInputs`, `1384-1404`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-4/vm.js#L1384-L1404) | Effects -> operation kind/roles/slots; residual write -> `ARITH` inputs | VM-4-owned |
| Instruction recovery | [`disassemble`, `1484-1591`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-4/vm.js#L1484-L1591) | Code words + records -> PC-keyed descriptors/function records | Shared coordinator |
| Numeric fitting | [`fitInstr`, `1602-1702`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-4/vm.js#L1602-L1702) | `ARITH` + actual operands/frame size -> fitted expression or no fit | VM-4-owned |
| Path/state recovery | [`makeEngine`, `1718-1931`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-4/vm.js#L1718-L1931); [`explorePaths`/`resolveIndirect`, `1962-2080`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-4/vm.js#L1962-L2080) | Decoded ops -> `(pc,state)` trace and indirect targets | Shared coordinator |
| Lift/cleanup/driver | [`liftInstr`, `2087-2397`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-4/vm.js#L2087-L2397); [`generateBody`, `2402-3122`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-4/vm.js#L2402-L3122); [`deobfuscateSource`, `3501-3559`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-4/vm.js#L3501-L3559) | Trace/descriptors -> AST -> generated source | Shared downstream substrate |

The frame convention observed in the source is a VM-4 input fact used by the fitter and path
engine: frame metadata lives in the header and register base is at `fp+13`; `frameSize - 13` is
used in the arithmetic handlers. The root and this page keep that fact sample-owned rather than
assuming VM-5's different frame slots.

## 4. Upstream Effects

Upstream recognition must provide the handler table, operand reader, pool/decoder, entry spec, and
frame metadata. If it does not, this transform has no safe operation-recovery input. Downstream
disassembly consumes the classified shape and fitted arithmetic; the path engine consumes decoded
operations and produces constant-state traces; the lifter consumes those traces and never repairs
an unknown handler by looking at output text.

The sample's retained artifacts give concrete provenance for this contract: `input.js` embeds a
large encoded word stream and many numeric handlers; `output.js` contains decoded strings, DOM
operations, and an ordinary loop; `regular.js` represents the non-VM input; and `test.js` specifies
intended parse, pass-through, output-shape, and equivalence checks. These materials do not establish
a runtime or equivalence result.

## 5. Known Gaps

- `locateVM` associates sample-shaped AST clues structurally; it does not establish general data
  flow or prove that arbitrary decoys belong to one VM.
- `runHandler` is a bounded interpreter of a supported handler-AST subset. Unsupported syntax,
  native behavior, step exhaustion, or symbolic ambiguity can prevent classification.
- `classify` has an explicit `UNKNOWN` outcome and residual `ARITH`; a residual arithmetic fit may
  fail. The source then emits an `undefined` assignment and warning rather than a verified semantic
  replacement.
- The fitter's fixed candidate set and 40 trials do not prove algebraic equivalence for arbitrary
  MBA expressions, and its actual-operand/frame-size cache is not a generalized model.
- `disassemble` does not statically resolve every register-computed jump. Path exploration widens
  high-cardinality registers and remains bounded; unresolved control or unsafe structure can stay
  in the source-defined fallback/error behavior.
- Decrypt operations are warned about rather than emulated; unknown opcodes throw at the
  disassembly boundary. Existing output and tests are not evidence that these gaps are absent.
- This page makes no behavioral-equivalence,
  host-safety, transfer, or production-coverage claim.

## Source

The algorithm authority is the pinned [`VM-4/vm.js`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-4/vm.js).
The driver order is [`deobfuscateSource#L3501-L3559`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-4/vm.js#L3501-L3559).
The related root is [VM-4](../plugins/vm-4.md). No VM-1 or VM-3 transform is an algorithmic
dependency of this sample-owned page.

## Fixtures

| Artifact | Claim retained here | Evidence status |
| --- | --- | --- |
| `VM-4/input.js` | Concrete embedded handler table, reader, pool, base64 code, frame setup, and payload shape | Source/fixture evidence only. |
| `VM-4/output.js` | Existing lifted representation: decoded browser strings, DOM operations, arithmetic, and loop | Generated-output provenance only. |
| `VM-4/regular.js` | Ordinary program shape that should use the driver's no-VM branch | Negative/provenance evidence only. |
| `VM-4/README.md` | Described VM roles, frame slots, pipeline, and intended recovery behavior | Documentation provenance only. |
| `VM-4/NOTES.md` | Stated implementation notes and observations | Documentation provenance only. |
| `VM-4/test.js` | Intended parse, pass-through, output-shape, round-trip, and behavioral checks | Test-intent evidence; no check result is claimed. |
