# VM-GLM-1 symbolic handler effects and path-sensitive CFF dissolution

Status: source-inspection only. This page documents the distinct VM-GLM-1 variation at frozen
corpus commit `e90be6ca716e28f4bba91fe39615a665656bd802`. It makes no execution, transfer,
behavioral-equivalence, or production-coverage claim.

## 1. Target

The target is the solution-level variation that gives a static register-VM pipeline two facts it
cannot obtain from handler names or numeric opcode values alone:

1. an ordered symbolic effect description for each JavaScript handler, matched to a supported
   semantic archetype; and
2. a path-sensitive description of the branchless case dispatcher, sufficient to rewire proven
   state transitions into an ordinary block graph.

The input is a parsed VM source tree after the sample's structural VM relationships and static
payload have been recognized. The variation consumes handler ASTs, helper identities, decoded
instruction records, and per-path register facts. Its outputs are a semantic handler table and,
for recoverable functions, a CFG whose proven CFF case transitions have been rewired.

The discriminator is source structure and state provenance: recognized VM properties and helper
calls, ordered operand markers, register/frame/cell roles, exact effect patterns, and path facts
that distinguish integer state cases. The model label, directory name, and randomized numeric
opcode are not discriminators. An unrecognized or ambiguous handler remains unsupported, and a
variable or unresolved state transition does not get a guessed successor.

This is a variation over the shared VM-3 static handler/state-lifting method. Structural
recognition, payload representation, ordinary instruction lifting, cleanup, and caller-facing
fallback are related boundaries; they are not repeated here. The implementation source is
self-contained in `VM-GLM-1/vm.js`, so the ownership statement is about the documented algorithm
boundary, not a claim that the two sample files import one another.

## 2. Algorithm

The distinct work is one coupled solution-level unit with two representations: a symbolic effect
IR for handlers and a path-sensitive abstract state for payload control flow.

### 2.1 Symbolic handler-effect interpretation

For each handler, `interpretHandler` walks the AST without invoking the handler. Its state is
`{env: Map(), ops: 0, effects: [], condStack: [], regReads: []}`. The ordered steps are:

1. Initialize an environment for symbolic bindings, an operand stream counter, an effect list, a
   condition stack, and register-read metadata. Known VM helpers and properties are bound from the
   extracted VM descriptor.
2. Evaluate expressions into symbolic terms. Literal arithmetic is locally folded; identifiers,
   `this`, members, binary/unary/logical/conditional expressions, arrays, objects, sequences,
   assignments, calls, constructors, and functions remain terms when their value is not static.
3. Normalize recognized VM relationships while evaluating members and calls. Stack, frame,
   register-base, globals, code, constants, closure-cell, weak-map, operand-reader, unwind,
   frame-push, cell-read, and metadata-constructor uses become typed terms or effects. A direct
   operand read allocates the next ordered `opnd` marker; a constant-decoder read preserves its
   index/key positions.
4. Attach the active condition to every effect. An `if` is analyzed from saved environment/effect
   snapshots and joins differing bindings as `either` terms. A loop is represented as a bounded
   `forloop` effect containing its body/update effects. This preserves branch and loop shape for
   archetype matching instead of selecting one runtime path.
5. Normalize writes to register, frame, stack, global, code, cell, and element effects, while
   retaining return, throw, handler-stack, call, and property-definition effects. Unsupported
   syntax is opaque rather than executed.

The resulting record is `{effects, env, opsRead, regReads}`. `canonicalizeTerm` and
`canonicalizeEffect` provide a stable textual form for diagnostics and matching support; the
algorithmic output remains the structured record.

### 2.2 Archetype matching and operand contracts

`matchArchetype` reads the effect record in a fixed order. It first recognizes control and handler
effects, then decode/property/cell/closure/call/literal/iterator forms, then simple register
operations. The first supported exact pattern wins; missing or conflicting required effects yield
no semantic match.

| Effect evidence | Semantic archetype | Distinct contract preserved |
| --- | --- | --- |
| handler-stack pop, catch push, or finally push | `POPH`, `PUSHCATCH`, `PUSHFIN` | control/handler effect, not a normal register op |
| unwind plus stack write/register read | `RET` | return value and cleanup shape |
| looped code writes with four or more ordered operands | `DECODE` | loop-derived range/key roles and multiplier inference |
| property set/delete or getter/setter descriptor | `SETPROP`, `DELPROP`, `DEFGET`, `DEFSET` | member and descriptor roles |
| cell store or recognized cell read | `CSET`, `CGET` | closure-cell source/destination roles |
| closure metadata object plus metadata construction and capture loop | `MKFUNC` | entry, parameters, registers, rest flag, destination, and capture pairs |
| apply/call/construct effect plus looped element stores | `CALL`, `CALLI`, `CONSTRUCT` | fixed header versus count-driven argument tail, including spread |
| array/object loop with element stores | `ARRLIT`, `OBJLIT` | fixed header plus count-selected tail |
| iterator object shape or conditioned iterator update | `FORIN_INIT`, `FORIN_NEXT` | iterator and state-register roles |
| state write with a path condition | `JMP`, `JMPR`, `JMPT`, `JMPF` | direct, indirect, and conditional target roles |
| simple register write with recognized binary/unary/load shape | arithmetic, move, load, member, or global archetype | destination and source roles from symbolic terms |

Operand positions come from the `opnd` stream markers, not from every `$`-like term. Immediate
numeric literals consume no payload word. `countRefs` therefore separates stream operands from
baked values, and the matcher records fixed widths or a count-driven tail. Closure captures,
array/object elements, and call arguments retain their source order; a spread or variable count
is not flattened into a guessed fixed width.

`classifyHandlers` applies this process independently to the numeric handler functions. Successful
records populate the semantic opcode table; failures are recorded and omitted from the successful
table. The table is therefore a source-derived partial vocabulary, not a claim that every handler
in an arbitrary VM is supported.

### 2.3 Path-sensitive payload analysis

The second distinct phase is `analyze`'s abstract executor. It uses the semantic table to decode
instructions, then carries a per-function worklist state with concrete values and boolean pairs.
The important order is:

1. Decode an instruction at an instruction pointer, applying a known semantic kind and its operand
   width. `DECODE` decrypts a private word copy once at that IP; it does not execute the input VM.
2. Maintain per-IP stable facts. On revisits, retain only values present and equal on all visits;
   conflicting or missing facts are dropped. In-flight `__sel` values are exempt from this
   intersection so branchless selections can be propagated until their dispatch use.
3. Fold supported arithmetic and comparisons. A comparison whose truth is not concrete becomes a
   boolean pair carrying the condition register and its true/false values.
4. Build a branchless selection when a constant is combined with a boolean pair using a supported
   operation and the two resulting values differ. Propagate that selection through supported
   member projections and, when a pure uncaptured VM function has one selection argument and
   otherwise concrete arguments, evaluate the function twice with `concreteEval2` and retain the
   two results as a new selection.
5. Inline a short fall chain ending in `JMPR` as dispatcher machinery. A `JMPR` with an in-range
   numeric `__sel` emits two dispatch edges, each carrying the condition register, branch sense,
   and the straight-line block start. A concrete integer emits one edge. Other targets are
   recorded as unresolved rather than forced to a case.
6. Split conditional branches with path bindings for the true and false facts. Handle returns,
   throws, handler edges, and iterator exits as explicit terminal or exceptional edges. Repeat
   bounded analysis passes while stable facts or unresolved-jump information changes.

`concreteEval2` is a bounded, whitelisted evaluator over already lifted pure VM instructions. It is
used as an abstract dual evaluation for selection propagation and returns a failure marker for an
unsupported operation or unsafe call; it is not an execution of handler or sample input code.

### 2.4 Case-dispatch dissolution

`prepareFn` consumes the dispatch edges and performs the distinct CFF rewrite. It is guarded by
`VM_NODISSOLVE` and four rounds. In each round it:

1. Finds a hub with at least three goto predecessors whose terminator is conditional. The hub must
   compare a state register with a numeric exit constant using strict equality or inequality.
2. Follows the opposite hub side through a comparison ladder. Each ladder node must compare that
   same state register with a running numeric constant, and its matching side must target a case
   block. The ladder stops only at a fallback block that returns to the hub; an ambiguous or
   malformed ladder aborts this round.
3. Propagates a constant state environment from the entry and each case head. Header and ladder
   blocks do not participate in ordinary propagation. If a shared case is reached with a
   different state constant, it is cloned for that state, up to twelve split rounds and a queue
   limit of 50,000 items.
4. Resolves each state by following only pure, state-preserving goto trampolines. A pure goto that
   changes the state is a real salt body and remains the successor. A cycle with no matching link
   is dead; an unknown or variable state is unresolved and keeps the ladder.
5. Rewrites reachable back edges with constant state to their resolved case successors. Entry is
   rewired to its resolved successor. Dead states are routed through the ladder fallback so the
   original pure-dispatch infinite behavior is represented without inventing a live case.
6. Repeats for newly exposed state machines, then prunes unreachable blocks. Generic block lifting,
   structuring, cleanup, and source emission consume the resulting graph; those downstream
   boundaries are outside this variation page.

The invariant is that a case edge is dissolved only when its state is a proven constant and its
target is resolved through the source-defined ladder/trampoline rules. Variable state, an unknown
target, a conflicting split, or a failed hub/ladder shape leaves the dispatcher structure in place.

## 3. Implementation

The local implementation keeps all phases in one `vm.js`; this page assigns only the distinct
representations and rewrites to this variation. The surrounding extraction, generic instruction
lifting, rendering, and top-level output gates remain shared method boundaries documented by the
VM-3 pages.

| Representation or operation | Concrete shape | Ownership in this page |
| --- | --- | --- |
| Symbolic handler state | `env`, `ops`, `effects`, `condStack`, `regReads` | Owned by handler-effect interpretation |
| Symbolic terms | literals, `opnd`, register/frame references, VM property terms, `either`, loop terms, helper/call terms | Owned by interpretation only as needed to preserve effect provenance |
| Effect record | ordered effects such as `streg`, `setip`, `stackwrite`, `codewrite`, `setglobal`, `cellstore`, property/handler/call effects, `forloop` | Owned by interpretation and consumed by the matcher |
| Semantic handler table | numeric handler key -> `{kind, ...roles, ...fixed, slots}` | Owned by archetype matching; partial on failed matches |
| Abstract execution state | per-function worklist with `v` concrete/special values and `b` boolean pairs | Owned by path-sensitive analysis |
| Branchless selection | `__sel` with true/false values, optionally projected or dual-evaluated | Owned by path-sensitive analysis; not a runtime value |
| Dispatch edge | `{kind: "dispatch", to, cond, sense, blockStart}` | Produced by path analysis and consumed by CFF preparation |
| CFF preparation state | blocks, terms, state environments, ladder links, conflict clones, rewires | Owned by `prepareFn`'s case-dissolution branch |

The key implementation boundaries are:

- `interpretHandler` symbolically evaluates syntax and models the recognized VM helper/member
  relationships. Its `push` helper captures the active guard, and its branch/loop handlers preserve
  `either` and `forloop` structure rather than selecting a runtime path.
- `matchArchetype` reads those effects in a fixed priority order. `countRefs` counts only ordered
  operand markers, while literal values and explicit variable-tail counts retain their separate
  roles. `flattenEither` and register-reference helpers support conditional terms without turning
  them into empirical observations.
- `classifyHandlers` is the coordinator that builds the successful partial table. It catches a
  handler interpretation/match failure and does not assign an invented kind.
- `concreteEval2` and `exploreFunction` implement the path-sensitive abstract facts, selection
  algebra, dual pure-leaf evaluation, widening, and dispatch-edge production. The bounds are
  source-defined; they are not claims about unbounded VM execution.
- `prepareFn` performs the hub/ladder test, state injection, state-specific cloning, trampoline
  resolution, back-edge rewiring, fallback routing, and reachability pruning. The state arithmetic
  in a salt block remains real payload code; only the dispatch edge is rewritten.

## 4. Upstream Effects

The earlier structural recognition/extraction boundary supplies handler functions, helper
identities, VM state relationships, payload words, constants, and the entry metadata. The
handler-effect variation consumes those values and produces the semantic opcode table that the
payload disassembler needs for variable-width instruction decoding.

The path-sensitive analysis consumes that table and the static payload. It produces typed
instructions, function records, and dispatch edges with path condition and block-start metadata.
`prepareFn` consumes those edges and emits a block graph with only proven CFF transitions rewired.
The later ordinary lifting, control-flow structuring, cleanup, and source-emission boundaries
consume that graph; they must not infer a target from a raw unresolved dispatch edge.

The dependency chain is therefore:

`VM descriptor and payload -> symbolic handler effects -> partial semantic table -> abstract
instruction/edge analysis -> CFF-dissolved block graph -> shared downstream lifting and emission`.

Material safety edges are:

| Boundary | Source behavior |
| --- | --- |
| Unmatched handler | Not entered into the successful semantic table; no guessed operation |
| Unknown instruction target | Retained as an unresolved jump; not converted to fallthrough |
| Unsupported pure dual evaluation | Returns a failure marker; selection propagation stops |
| Widening conflict | Drops the conflicting stable fact rather than choosing one path |
| Variable CFF state | Dissolution aborts for that hub and preserves the ladder |
| Unknown CFF target or excess split | Rewriting stops for the affected hub; no invented successor |
| Top-level recognition/lift failure | The local driver returns unchanged source on its documented failure gates; source inspection does not establish that behavior empirically |

## 5. Known Gaps

- Handler matching is tied to the modeled AST node forms and VM helper/property relationships. A
  semantically similar handler with a different source shape can remain unmatched.
- The successful handler table is partial. A nonempty table can continue analysis while unsupported
  handlers remain unavailable; this page does not claim complete handler coverage.
- `concreteEval2` accepts only its bounded pure instruction and safe-global vocabulary. Native
  calls, unsupported effects, bad arguments, and non-concrete values fail closed.
- Stable facts are intersected across revisits, so widening can remove useful information. The
  analysis records unresolved jumps when it cannot prove an indirect target.
- CFF recognition requires the strict hub/ladder shape, a numeric exit constant, and a bounded
  ladder. The implementation caps dissolution at four rounds, ladder links at 300, queue items at
  50,000, and split rounds at twelve.
- A state-preserving pure trampoline may be skipped; a state-changing salt block is retained as a
  successor. Same-state dispatch cycles and unmatched state constants are treated as dead only
  under the source-defined fallback rules.
- This page does not document the ordinary VM container, generic instruction lifter, relooping,
  cleanup, or output formatting in detail. It points to those shared boundaries so the variation
  is not mistaken for a second full pipeline.
- The source-backed mechanism description does not establish behavioral equivalence, transfer, or
  production coverage.

## Source

All source links are pinned to the frozen corpus commit:

- [`extractVM` and `literalValue`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-GLM-1/vm.js#L39-L217) own static VM recognition, handler-table discovery, payload/helper extraction, and literal limits.
- [`interpretHandler`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-GLM-1/vm.js#L246-L665) owns the symbolic environment, terms, guarded effects, branch joins, loop records, and modeled helper calls.
- [`matchArchetype`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-GLM-1/vm.js#L797-L1211) and [`classifyHandlers`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-GLM-1/vm.js#L1265-L1282) own effect-pattern matching, operand contracts, and semantic-table assembly.
- [`makeConstDecoder`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-GLM-1/vm.js#L1288-L1306) owns static constant lookup and rolling string decoding for the recovered payload.
- [`concreteEval2`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-GLM-1/vm.js#L1382-L1512), [`exploreFunction`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-GLM-1/vm.js#L1576-L1968), and the bounded multi-pass return in [`analyze`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-GLM-1/vm.js#L1970-L1989) own abstract values, branchless selections, widening, dispatch edges, and unresolved-target handling.
- [`prepareFn`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-GLM-1/vm.js#L2150-L2621), especially its [CFF case-dispatch dissolution](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-GLM-1/vm.js#L2314-L2571), owns hub/ladder recognition, state propagation, cloning, target resolution, rewiring, fallback routing, and reachability pruning.
- [`liftProgram`, `buildFunction`, and program assembly](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-GLM-1/vm.js#L2117-L3348) own the local graph-to-AST boundary, structured-CFG attempt, machine fallback, declaration handling, and top-level assembly.
- [`deobfuscateSource` and the public boundary](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-GLM-1/vm.js#L3429-L3491) own parser/extraction/lift fallbacks, unresolved-jump warning, generation, and CLI/module wiring.
- The related [VM-3 plugin entry](../plugins/vm-3.md) and [VM-3 transform pages](../transforms/vm-3-handler-canonicalization.md), [payload disassembly](../transforms/vm-3-payload-disassembly.md), [state lifting](../transforms/vm-3-state-specialized-lifting.md), [cleanup/emission](../transforms/vm-3-reloop-cleanup-emission.md), and [fallback validation](../transforms/vm-3-fallback-validation.md) own the common method boundaries. Those links are method references; this page does not copy their implementation detail.

## Fixtures

The retained sample files provide input, negative-control, generated-output, and test-intent
provenance; they do not establish a behavioral claim.

| Fixture | Claim it can pin | Evidence role |
| --- | --- | --- |
| `VM-GLM-1/input.js` | Source-level handler, dispatcher, and payload shapes consumed by the implementation | Source fixture |
| `VM-GLM-1/regular.js` | No-VM control shape for the documented decline boundary | Source fixture |
| `VM-GLM-1/output.js` | Existing generated-output provenance for the sample | Generated-output provenance only |
| `VM-GLM-1/test.js` | Intended parser, output-shape, and sample checks | Test-intent evidence |
| `VM-GLM-1/README.md`, `NOTES.md` | Sample architecture and implementation context | Documentation provenance only; source links define the algorithm |
