# Dual emission

Evidence label: source-inspection only. This page is the E5 reconstruction contract for the two
VM-1 output representations. It does not qualify either output, execute generated code, or imply
support for VM layouts outside the E1-E3 representation.

## 1. Target

Provide two alternative Babel AST outcomes over the same decoded function/block representation:

- a readability-oriented structured program, produced by the reducer described in
  [reducible register structuring](vm-1-reducible-register-structuring.md); or
- an explicit program-counter dispatcher that preserves block control in
  `while (true) { switch (pc) { ... } }` form.

The structured outcome is reducibility-gated. The dispatcher outcome retains VM-like state and
supports the represented dynamic PC and handler-stack forms, but it cannot recover source
semantics for `CODE_COPY`. These are alternative consumers of E3, not sequential cleanup stages.

## 2. Algorithm

### Shared composition

1. Map function starts to function records and recursively resolve child `DEFINE_FUNCTION` capture
   descriptors. A register capture (`c.Y`) reads the current function register; an outer capture
   reads the current upvalue node. Clone AST nodes when inserting captures.
2. In structured mode, call E4's function reducer, optionally prefix registers as `f<fid>_` when
   any function has captures, add `__forInKeys` if a path requests it, call the top-level function,
   and return a Babel file.
3. In dispatcher mode, build raw E3 blocks for each function and one switch case per leader.
   Create explicit register/argument/handler/PC state, lower all side operations and the final
   control operation, and wrap the switch in an infinite loop.

### Dispatcher lowering

1. The dispatcher function has no formal parameters. Its prologue creates `R = []` and
   `A = Array.prototype.slice.call(arguments)`. Non-rest functions copy `A` into `R` up to the
   function's frame size; rest functions copy fixed parameters and store `A.slice(l - 1)` in the
   rest slot. If `l < frameSize`, store the complete `A` in register `l`; handler-bearing
   functions also create `H = []`. Set `pc` to the function entry.
2. For every block, lower loads, moves, globals/upvalues, members, operators, calls, constructors,
   child functions, arrays/objects, accessors, for-in initialization, debugger, handler stack
   updates, and the `CODE_COPY` marker. Every destination becomes an explicit `R[index] = value`.
3. Lower block control by assigning `pc` and breaking the switch iteration for jumps, conditional
   jumps, dynamic jumps, and for-in. Return and throw become direct statements. A block that ends
   without a terminator assigns the fall-through PC and breaks.
4. For handler-bearing functions, wrap the switch in `try/catch`. If `H` is empty, rethrow. Pop
   one handler record; for `catch`, store the error in `R[hd.reg]` and jump to `hd.pc`; for
   `finally`, store the marker in `R[hd.regV]`, error in `R[hd.regZ]`, and jump to `hd.pc`.
5. If any function uses for-in, emit one top-level `__forInKeys` helper returning `{ keys, i }`.
   Call the emitted top-level function and leave final source generation to E6.

## 3. Implementation

### Mode-level structured composition

The structured-side `emitProgram` creates `byStart`, detects whether any function has captures,
chooses the register prefix policy, and keeps a program-wide `needForIn` flag. Its nested
`emitFunc` builds the E4 context, finds the defining instruction for a child, maps captures, calls
the structured function reducer, and returns a function expression with parameters and a block
body. The program adds the helper if marked and calls the top-level function. E4 owns the model,
liveness, folding, control recovery, prologue, and beautification inside that context.

### Dispatcher program and function state

[`emit-dispatcher.js#L28-L105`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-1/emit-dispatcher.js#L28-L105)
builds a function expression from cases and prologue statements:

| State | Initialization | Use |
| --- | --- | --- |
| `R` | `[]`; populated from `A` under rest/non-rest rules | Every VM register read/write is `R[n]`. |
| `A` | `Array.prototype.slice.call(arguments)` | Original argument list; copied to parameter slots and optional argument register. |
| `H` | `[]` only when body has `TRY_CATCH` or `TRY_FINALLY` | LIFO handler records for the catch wrapper. |
| `pc` | Function entry address | Selects the next `switch` case. |

Each E3 leader becomes `switchCase(numericLiteral(ld), caseBody)`. `emitBlock` calls
`lowerSideEffect` for each non-control instruction and then lowers the first control instruction;
if the list falls through, it assigns `pc` to the last instruction's next address and emits a
`break`.

### Side-effect lowering

`lowerSideEffect` writes all register results explicitly. Loads use `litNode`, `identRef`, or
`this`/`undefined`; upvalue/global stores assign through cloned nodes; member access always uses
computed register keys; binary/unary/void operations map directly to Babel operators. Calls use
`R[fn](...)`; method calls always use `R[fn].apply(R[recv], args)`; constructors use `new R[fn](...)`.
Function definitions recursively emit children. Arrays preserve register order, objects use
computed register keys, and accessors use `Object.defineProperty` with configurable/enumerable
properties.

`FORIN_INIT` assigns `__forInKeys(R[obj])`. `TRY_CATCH` pushes
`{ kind: 'catch', pc, reg }`; `TRY_FINALLY` pushes
`{ kind: 'finally', pc: W, regV: V, regZ: Z, marker: aa }`; `TRY_POP` pops. `DEBUGGER` emits a
debugger statement. `CODE_COPY` emits the string literal `__CODE_COPY_UNSUPPORTED__` and returns
as a handled side effect; it does not modify bytecode.

### Control lowering

`lowerControl` sets `pc` and breaks for `JUMP`, or uses a conditional expression to choose next vs.
target for either conditional branch. Returns and throws read their register directly. `JUMP_DYN`
assigns `pc = R[reg]`. `FORIN_NEXT` compares `iter.i >= iter.keys.length`; the true branch sets
the target PC, while the false branch assigns the next key to `R[f]`, increments `iter.i`, and
sets the fall-through PC. It then breaks the switch iteration.

### Source ownership

| Source span | Ownership | What it owns |
| --- | --- | --- |
| [`emit-structured.js#L28-L80`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-1/emit-structured.js#L28-L80) | shared mode coordinator owned here | Structured program wrapper, child capture wiring, closure-prefix policy, helper insertion, and top-level call. E4 owns the internal reducer. |
| [`emit-dispatcher.js#L20-L105`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-1/emit-dispatcher.js#L20-L105) | owned algorithm | For-in/handler detection, function/case assembly, handler wrapper, loop, and prologue. |
| [`emit-dispatcher.js#L107-L126`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-1/emit-dispatcher.js#L107-L126) | owned algorithm | Basic-block case lowering and fall-through PC. |
| [`emit-dispatcher.js#L130-L210`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-1/emit-dispatcher.js#L130-L210) | owned algorithm | Side-effect/register lowering and known-operation marker. |
| [`emit-dispatcher.js#L212-L252`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-1/emit-dispatcher.js#L212-L252) | owned algorithm | Explicit-PC control and for-in lowering. |
| [`vm.js#L479-L484`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-1/vm.js#L479-L484) | shared coordinator | Supplies common tables, block builder, literal helpers, and Babel types to both emitters. |

## 4. Upstream Effects

E5 consumes E2 descriptors and E3 function/block records. It relies on E3's block partition but
does not require E4's reducibility for its dispatcher branch. The structured branch additionally
consumes E4's local model and decline conditions. E2 must retain known `CODE_COPY`, handler, and
dynamic-PC descriptors so the dispatcher can represent them even if the structured path cannot.

E6 owns which mode is selected: `VM_FORCE_DISPATCH` selects E5's dispatcher directly, while a
structured-emitter error also selects it. E5 only constructs the selected AST; E6 invokes Babel
generation. The two mode outputs are therefore alternative representations, not a structured
pass followed by dispatcher cleanup.

## 5. Known Gaps

- Dispatcher lowering keeps explicit VM state and does not recover source-level readability or
  generalized VM support.
- `CODE_COPY` is recognized but emitted as `__CODE_COPY_UNSUPPORTED__`; it is not self-modifying
  bytecode recovery and is distinct from E2's unknown-opcode throw.
- The dispatcher source comments describe a correctness-oriented representation; this is source
  intent, not a behavioral guarantee.
- Structured-mode differences (reducibility checks, local folding, direct method-call optimization,
  and computed-property spelling) are owned by E4, not silently assumed to match dispatcher output.
- The helper, register arrays, handler stack, and generated candidate have no runtime or safety
  qualification.

## Source

| File | Pinned source | Role |
| --- | --- | --- |
| `VM-1/emit-structured.js` | [`structured wrapper`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-1/emit-structured.js#L28-L80) | Mode-level structured assembly; reducer is owned by E4. |
| `VM-1/emit-dispatcher.js` | [`dispatcher assembly`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-1/emit-dispatcher.js#L20-L126) | Function/case/prologue construction. |
| `VM-1/emit-dispatcher.js` | [`operation and control lowering`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-1/emit-dispatcher.js#L130-L252) | Explicit state-machine output. |
| `VM-1/vm.js` | [`common emitter dependencies`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-1/vm.js#L479-L484) | Shared injection boundary. |

## Fixtures

No independent regression fixture isolates the two emission modes; the retained sample artifacts
below map their source and output shapes.

| Corpus artifact | Claim it pins | Evidence status |
| --- | --- | --- |
| `VM-1/output.js` | Existing structured-emission shape | Generated-output provenance only. |
| `VM-1/output.dispatch.js` | Existing explicit-PC dispatcher shape | Generated-output provenance only. |
| `VM-1/input.js` | Shared decoded-input provenance | Source fixture. |
| `VM-1/NOTES.md` | Documented structured-primary/dispatcher-fallback arrangement | Documentation provenance only. |
