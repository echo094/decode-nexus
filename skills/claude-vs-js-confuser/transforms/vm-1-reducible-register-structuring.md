# Reducible register structuring

Evidence label: source-inspection only. This page is the E4 reconstruction contract for the
readability-oriented VM-1 emitter. It documents source-level AST reconstruction for recognized
reducible shapes, not arbitrary CFG structuring, execution, or an equivalence result.

## 1. Target

Lift E2 register instructions and E3 basic blocks into source-oriented Babel expressions and
statements when the control graph is reducible and try/catch regions are well nested. The target
contains named register locals, source-level branches/loops/returns/throws, `for-in`, catch
regions, properties, calls, constructors, closures, and preserved observable effects.

The discriminator is the emitter's structural guards. Dynamic jumps, `TRY_FINALLY`, unbalanced
try markers, unsupported register IR, missing or repeated blocks, irreducible/backward branches,
escaping branches, unhandled for-in exits, and an emission runaway raise `Unstructurable`.

## 2. Algorithm

1. Build a model from E3 blocks. Split each block into side instructions and a final structured
   terminator; collect backward-edge loop candidates; scan side instructions into well-nested
   `TRY_CATCH` regions; reject `JUMP_DYN` and `TRY_FINALLY` during modeling.
2. Build register use/def sets for each modeled block. Add ordinary terminator successors and an
   exception edge from every block inside a try interval to its catch block. Iterate backward to a
   `liveOut` fixpoint.
3. Emit a sequence from a start address. Prefer a pending try region, then an unentered loop, then
   one un-emitted block. Fold its side instructions into local IR and lower its terminator to
   structured AST. Track emitted and consumed block addresses so every modeled block is accounted
   for once.
4. Fold each block locally. Resolve register reads through pending definitions, clone only
   duplicable pure values for multiple uses, preserve effect-only operations, and materialize a
   named register when liveness or safety prevents inlining.
5. Translate recognized targets to fall-through, if/else, labeled while loops, continue/break,
   return/throw, or the helper-backed `for-in` shape. Recursively emit child functions using
   capture descriptors.
6. Build parameters/prologue declarations and apply only the two `beautify` cleanups: fold a
   leading break guard into a while test and drop unreferenced labels.

## 3. Implementation

### Model, loops, and try/catch regions

`buildModel` obtains raw blocks from E3 and computes `endAddr` from the last instruction. The last
instruction becomes one of these terms:

| E2 terminator | Modeled term |
| --- | --- |
| `JUMP` | `{ kind: "jump", target }` |
| `JUMP_IF_FALSE` | `{ kind: "branch", cond, whenTrue: endAddr, whenFalse: target }` |
| `JUMP_IF_TRUE` | `{ kind: "branch", cond, whenTrue: target, whenFalse: endAddr }` |
| `RETURN`, `THROW` | `{ kind: "return"/"throw", val }` |
| `FORIN_NEXT` | `{ kind: "forin", f, iter, target, next: endAddr }` |
| `JUMP_DYN` | immediate `Unstructurable` |
| any other final instruction | `{ kind: "fall", target: endAddr }` |

For every modeled term target `t`, a target `t <= addr` that is a block is recorded as a loop
header; its end is the maximum `endAddr` of contributing blocks, and its exit is set equal to
that end. A side `TRY_CATCH` pushes `{ tryFrom, catchPc, catchReg }`; `TRY_POP` closes the latest
region, records `popAddr`, `popBlock`, and an after-address resolved only from a jump or fall term;
an empty stack or leftover stack throws. Any side `TRY_FINALLY` throws immediately.

### Liveness and sequence state

`computeLiveness` skips try markers when collecting side reads/defs, uses `instrReads` and
`instrDef`, and adds reads from the term. Normal term targets are added only when modeled blocks
contain them. For each region, every block address `addr` satisfying
`tryFrom <= addr < popAddr` receives an exception successor to `catchPc`. `liveIn` and `liveOut`
start empty, then update backward until unchanged:

```text
liveOut[block] = union(liveIn[successor])
liveIn[block]  = use[block] union (liveOut[block] - def[block])
```

`emitSeq` carries `from`, `to`, a loop stack, and a context containing model/liveness and sets
`emitted`, `consumed`, and `materialized`. It increments a guard on each iteration and throws
after 100000 iterations. Region starts consume their `popBlock`; loop headers are emitted once;
an absent or already-emitted block is an error.

### Control structuring

`emitTryRegion` emits `try { emitSeq(tryFrom, popAddr) } catch (r) { emitSeq(catchPc, afterAddr) }`.
It does not emit a structured finally clause. `emitLoop` creates `L<n>: while (true) { ... }`,
passes a loop context with header/exit/label, and removes a trailing unlabeled continue.

`emitTerminator` translates jumps to continue/break when `translate` finds the target in the
innermost applicable loop; otherwise a forward jump can continue a sequence, but an irreducible
back jump throws. Branches require one fall-through arm, reject backward targets outside a loop
and targets beyond the current region, then use `detectElse` to recognize a then-block ending in
a forward merge jump. `emitForIn` emits an index/length test over `{ keys, i }`, assigns the next
key into the target register with a post-increment, materializes that register, and requires its
exit target to translate to a non-goto action.

### Local register folding

`foldBlock` converts side instructions to local operations and appends a terminator pseudo-op. It
tracks the last definition of each register, use counts/positions, and the final definition. A
read resolves to a pending node if available; duplicable entries are cloned, while non-duplicable
entries are consumed. `safeDefer` rejects deferral when a dependency is redefined between the
definition and use, an effectful value crosses another effect, or an intervening global store
touches a read global. A dead non-live definition is dropped unless its expression is effectful.
Otherwise an operation is inlined only when it is not `noInline`, not live out, has one use or is
duplicable and pure, and passes `safeDefer`. Failed inlining emits `rN = expression` and records
`N` in `materialized`.

### Instruction-to-AST mapping

| Operation family | Generated Babel shape and important policy |
| --- | --- |
| loads/immediates | `litNode` for constants/immediates; global names use `identRef`; top-level `this` loads as `undefined`, nested loads as `this`. |
| upvalues and moves | Capture nodes are cloned; moves propagate their source; stores emit assignments to cloned capture/global nodes. |
| members | `GET_PROP` reads object/key; valid identifier string keys use dot form, other keys computed form. Set/delete preserve computed member semantics. |
| arithmetic/unary | `POW`, `BINOP`, `UNOP`, and `VOID_OP` become corresponding Babel expressions. |
| calls/new | Calls read function plus list/spread registers; method calls become direct member calls only when the function member's object equals the receiver, otherwise `fn.apply(receiver, args)`; `NEW` becomes `new fn(args)`. |
| child function | `DEFINE_FUNCTION` recursively calls `ctx.emitChild` and is `noInline`. Captures map register captures via `reg(c.M)` and outer captures via cloned upvalues. |
| arrays/objects | Arrays preserve element order. Object pairs use identifier keys for valid strings, literal keys for string/numeric literals, and computed keys otherwise. |
| getter/setter | `Object.defineProperty(obj, key, { get/set: fn, configurable: true, enumerable: true })`. |
| for-in/debugger | `FORIN_INIT` calls generated `__forInKeys`; debugger emits a Babel debugger statement. |
| `CODE_COPY` | Throws `Unstructurable("CODE_COPY not structurable")`; no source-semantic lift. |

`identRef` emits an identifier only for `/^[A-Za-z_$][A-Za-z0-9_$]*$/`; otherwise it emits
`globalThis["name"]`. `nodeEq` is a limited structural equality check used only for the direct
method-call optimization.

### Prologue and cleanup

`buildParams` creates named register parameters, replacing the final parameter with a rest element
when `f.rest` is truthy. `buildPrologue` detects reads of the argument slot `l`; if `l < frameSize`
and the slot is read, it initializes `r<l>` with `Array.prototype.slice.call(arguments)`. It then
declares sorted materialized non-parameter registers with `var`. The E5-owned structured wrapper
adds closure prefixes (`f<fid>_`) when any function has captures and adds the helper/top-level call.

### Source ownership

| Source span | Ownership | What it owns |
| --- | --- | --- |
| [`emit-structured.js#L86-L143`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-1/emit-structured.js#L86-L143) | owned algorithm | Model, loop candidates, try/catch regions, and structural declines. |
| [`emit-structured.js#L165-L212`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-1/emit-structured.js#L165-L212) | owned algorithm | Register liveness and exception successors. |
| [`emit-structured.js#L217-L371`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-1/emit-structured.js#L217-L371) | owned algorithm | Sequence, loops, branches, jumps, try/catch, and for-in emission. |
| [`emit-structured.js#L376-L473`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-1/emit-structured.js#L376-L473) | owned algorithm | Per-block IR folding, safety checks, and materialization. |
| [`emit-structured.js#L479-L577`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-1/emit-structured.js#L479-L577) | owned algorithm | Instruction IR and AST spelling helpers. |
| [`emit-structured.js#L583-L623`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-1/emit-structured.js#L583-L623) | owned algorithm | Liveness read/def inventory. |
| [`emit-structured.js#L628-L699`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-1/emit-structured.js#L628-L699) | owned algorithm | Parameters, prologue, and limited beautification. |
| [`emit-structured.js#L28-L80`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-1/emit-structured.js#L28-L80) | delegated to [dual emission](vm-1-dual-emission.md) as shared mode coordinator | Program wrapper, closure-prefix policy, child context setup, helper insertion, and top-level call. |

## 4. Upstream Effects

E4 consumes E3's contiguous blocks and E2's operand descriptors. E3 only supplies static targets;
E4 decides whether those targets form a recognized reducible shape. E2's register fields drive
`instrReads`, `instrDef`, folding, and generated AST operations; an E2 unknown-opcode throw cannot
be repaired here.

The structured mode does not consume E5's dispatcher state. Its structural error is an input to
E6's fallback branch, where E5 may generate an explicit-PC candidate. E5 owns the top-level
structured wrapper and helper insertion; this page owns the reducer and the AST meaning of each
instruction. Neither side executes generated helpers or candidates.

## 5. Known Gaps

- `JUMP_DYN`, `TRY_FINALLY`, unbalanced regions, irreducible/backward control, escaping branches,
  missing/re-emitted blocks, unhandled for-in exits, unsupported IR, and emission runaway are
  explicit decline paths. The driver may catch the resulting error broadly and select E5.
- `CODE_COPY` is known to E2 but raises from `irForInstr`; it is not the unknown-opcode path.
- Folding is block-local and conservative. It has no whole-function SSA, alias, handler,
  mixed-boolean-arithmetic, or flattened-state specialization.
- Structured method-call spelling differs from dispatcher spelling because the direct-call
  optimization is conditional on limited AST equality.
- The generated `__forInKeys` helper and source-level operations are not runtime-qualified.
- Source inspection does not establish behavioral equivalence, transfer, or runtime safety.

## Source

| File | Pinned source | Role |
| --- | --- | --- |
| `VM-1/emit-structured.js` | [`model and control`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-1/emit-structured.js#L86-L371) | CFG modeling and structured control. |
| `VM-1/emit-structured.js` | [`folding and AST IR`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-1/emit-structured.js#L376-L577) | Register lifting and concrete instruction mapping. |
| `VM-1/emit-structured.js` | [`liveness, prologue, cleanup`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-1/emit-structured.js#L583-L699) | Read/def inventory and final function shape. |

## Fixtures

No independent regression fixture isolates the structured reducer; the retained sample input/output
files map its source and output shapes.

| Corpus artifact | Claim it pins | Evidence status |
| --- | --- | --- |
| `VM-1/output.js` | Released readability-oriented output shape | Generated-output provenance only. |
| `VM-1/input.js` | Register-bytecode source input | Source fixture. |
| `VM-1/test.js` | Intended decoded-literal/output-shape checks | Test-intent evidence; no result is claimed. |
| `VM-1/verify.js` | Intended multi-environment comparison | Test-intent evidence; no result is claimed. |
