# VM-7 behavioral abstract-state lifting

Evidence label: `source-inspection only`. The description is pinned to corpus commit
`e90be6ca716e28f4bba91fe39615a665656bd802`; it makes no execution, behavioral, transfer, or
production claim.

## 1. Target

Recover source-oriented JavaScript from the pinned VM-7 sample by identifying its VM shell,
observing handler/frame effects, decoding the register bytecode, propagating abstract values and
control state, and lifting the recovered graph. Preserve a source-defined unchanged result on
non-match and retain explicit warning/state-machine forms where the implementation cannot safely
structure a result.

## 2. Algorithm

VM-7 uses a two-level behavioral recovery model. First, `Machine` captures the sample's runtime
descriptor and probes handlers with a synthetic frame, discovering shared handler kinds, operand
structure, result types, object/global effects, control effects, and enumeration shape. Arithmetic
sites receive a separate exact trial fit for their operator and operands. Second, `Analyzer`
linear-sweeps the payload, builds blocks/functions, and runs a bounded path-sensitive abstract
interpreter keyed by live registers. Incompatible values join to `TOP`; overflow triggers measured
widening. The analyzer resolves constant dispatch where possible and leaves dynamic edges explicit.
`Lifter` converts the resulting graph to AST, performs dead-pure-code and safe-temporary cleanup,
and `structure`/`emit` recover structured control flow or an explicit state machine.

The solution-level transition is:

`source AST -> captured VM descriptor -> synthetic-frame probe records -> handler model/site fits -> liveness-aware abstract states and CFG -> lifted AST -> structured or state-machine source`.

The distinctive boundary is the handoff from probe/classification records and site fits into the
abstract-state CFG and lift graph. This is not described as partial evaluation: the source uses
handler calls to probe/fold values, but its recovery representation is the `Analyzer` state graph,
not VM-8's environment-memoized dispatcher specialization.

## 3. Implementation

### Admission and descriptor capture

`VM-7/lib/machine.js:23-53` parses with Babel's unambiguous source mode, counts qualifying
top-level numeric computed-member function assignments, and reverse-scans for the final identifier
call with the expected constructor shape. `:55-93` rewrites only that final callee to
`__vmCapture`, exports top-level names, and runs generated setup in a `node:vm` context. The
captured result includes exports, entry arguments, and the sandbox. `VM-7/vm.js:50-73` gates this
path and returns the input source unchanged when `inspect` reports non-VM.

### Frame and handler evidence model

The sample runtime stores code, constants, globals, frame stack, and frame metadata in the
descriptor/runtime objects (`VM-7/lib/machine.js:18-21`, `:152-167`). `runAt` creates a synthetic
frame with program counter, receiver, try stack, flags, function record, salt/key, arguments,
frame size, parent, register base, scratch slot, and registers; it proxies reads/writes and records
errors (`machine.js:169-226`). `makeProbeObject` records property, call, construct, and object
meta-operation effects (`machine.js:97-128`).

`probeAll` learns operand structure and result type, then runs two classification passes so the
first pass can learn the sample's enumeration shape (`machine.js:228-265`). `decideKind` maps
observed frame/object/global/control effects to roles such as return, throw, jump, call, member,
global, for-in, closure, function, array/object, constant, immediate/void, or arithmetic
(`machine.js:267-360`). `decodeConst` documents the numeric and string constant decoding path
(`machine.js:395-409`).

Arithmetic is not accepted solely from a name or source spelling. `VM-7/lib/fit.js:14-57` defines
plain unary/binary candidate pools; `:92-191` observes candidate results through `runAt`, tries
free and pinned operands, requires exact outcomes over deterministic trial values, ranks simpler
fits, and returns an unknown form when no candidate fits. This is a site-fitting helper within the
same transform, not a separate plugin.

### Abstract state, payload, and control recovery

`VM-7/lib/analyze.js:43-91` derives instruction lengths from the learned structure and creates a
linear block map with terminators. `:142-158` seeds the top function and worklist. A merged graph
pass discovers static blocks, edges, captures, and child functions (`:223-259`); liveness is then
computed over uses/defs and captures (`:261-294`).

The main pass is bounded and path-sensitive (`analyze.js:298-427`). Its state key retains only live
registers, merges incompatible facts to `TOP`, caps nodes per PC, and widens selected live inputs
when the budget overflows (`:429-460`). Pure operations execute against known values; unknown
arithmetic uses bounded invariance sampling (`:462-568`). Terminators resolve returns, throws,
branches, for-in steps, trampoline dispatch, constant jumps, and dynamic jumps
(`:570-606`). Function handlers are converted into closure records and queued child analyses
(`:608-631`).

### Lift, structure, emit, and cleanup

`VM-7/lib/lift.js:215-321` maps recovered instruction kinds to AST expressions/statements, uses
folded analyzer values, handles calls/method calls/new/closures/for-in/try operations, and defers
warnings for unsupported or unknown forms. `:358-440` builds graph terms and maps dynamic control
to an explicit warning/bare-return form. `:452-590` computes live sets, eliminates dead pure
assignments, and inlines only safe temporaries.

`VM-7/lib/structure.js:69-214` computes graph relations, loops, joins, and structured branches;
`:216-257` simplifies loop conditions. `VM-7/lib/emit.js:17-178` simplifies empty gotos, merges
equivalent nodes/chains, and folds method calls. `:180-292` emits functions and catches
`StructureError` by emitting `var state = ...; while (true) { switch (state) ... }`. `:294-335`
renumbers names and emits the program. `VM-7/lib/polish.js:23-167` applies source-level cosmetic
passes after emission.

### Safety and decline boundary

Source-defined branches are distinct:

| Condition | Source-defined result | Anchor |
| --- | --- | --- |
| Shape is not admitted | Original source returned | `VM-7/vm.js:50-73` |
| Handler/operator cannot be resolved | Warning-bearing `undefined`/unknown lift | `VM-7/lib/lift.js:215-321` |
| Graph is unstructured | Explicit state-machine emission | `VM-7/lib/emit.js:180-292` |
| Parse/analysis failure | Can escape the driver | `VM-7/lib/machine.js:23-53`, `VM-7/lib/analyze.js:43-59` |

The implementation invokes generated setup and handler probes in its own source path; this source
inspection does not establish runtime behavior or safety.

## 4. Upstream Effects

Within the pinned decoder, the root admission stage is the producer of this transform's input
shapes. The transform consumes:

| Produced spelling/shape | Producer | VM-7 use |
| --- | --- | --- |
| Babel unambiguous AST with top-level computed numeric-member handler assignments | `machine.js:23-53` | Counts handlers and identifies the entry relationship |
| Final identifier call with constructor-shaped arguments | `machine.js:23-53` | Rewrites only the entry callee for capture |
| Captured `{exports, args, sandbox}` descriptor | `machine.js:55-93` | Seeds `Machine` and synthetic frames |
| `KIND`/structure/result records and fitted site operations | `machine.js:228-409`, `fit.js:92-191` | Drives instruction widths, state execution, and lifting |
| Analyzer graph nodes/outcomes | `analyze.js:395-606` | Drives lifting and structuring |

No separate earlier decoder pass or cross-sample source reuse is established by the pinned files.
The VM-7 root owns the dependency and its decline behavior; generic Babel/runtime facilities are
substrate only.

## 5. Known Gaps

- **Sample-shape scope:** admission is tied to the exact top-level relationship and a handler-count
  threshold; this page does not generalize it to other VM builds (`machine.js:23-53`).
- **Unknown arithmetic/control:** a failed fit, dynamic jump, or unsupported operation remains a
  warning-bearing/fallback representation rather than a claimed semantic recovery
  (`fit.js:92-191`, `lift.js:215-321`, `lift.js:402-440`).
- **Structuring failure:** explicit state-machine emission preserves control state but is not the
  same representation as structured source (`emit.js:180-292`).
- **Runtime execution boundary:** descriptor loading and probes execute generated setup/handlers in
  the implementation's sandbox; no safety or equivalence conclusion is made from that mechanism
  (`machine.js:55-93`, `:169-226`).


## Source

Pinned directory: [`decoder/claude-vs-js-confuser/VM-7/`](https://github.com/MichaelXF/claude-vs-js-confuser/tree/e90be6ca716e28f4bba91fe39615a665656bd802/VM-7), commit
`e90be6ca716e28f4bba91fe39615a665656bd802`. Wiring:
[`VM-7/vm.js:35-73`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-7/vm.js#L35-L73). Primary algorithm
anchors: `VM-7/lib/machine.js:23-409`, `VM-7/lib/fit.js:92-191`, `VM-7/lib/analyze.js:43-649`,
`VM-7/lib/lift.js:215-590`, `VM-7/lib/structure.js:69-257`, `VM-7/lib/emit.js:17-335`, and
`VM-7/lib/polish.js:156-167`.

## Fixtures

No maintained sample input/output fixture is available. `VM-7/test.js` records intended checks; no
validation result is claimed.
