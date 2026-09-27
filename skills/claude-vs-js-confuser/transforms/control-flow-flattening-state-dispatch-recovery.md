# Control Flow Flattening state-dispatch recovery

Evidence label: `source-inspection only`.

This page documents the one cohesive solution-level transform implemented by the pinned
`ControlFlowFlattening/cff.js`: recognize the sample's state-vector/sum dispatcher, recover a
concrete control-flow graph, fold the supported state/string expressions, emit structured or
explicit-state functions, and remove the resulting scaffolding. The companion character decoder
is included because it is part of the transform's constant-evaluation domain; it is not a
separate generalized string-decoding algorithm.

## 1. Target

The input is an unambiguous Babel JavaScript program containing a sample-shaped dispatcher. The
recognizer looks among top-level function declarations for a function with a `while` whose test is
`sum(state) !== terminal`, whose body contains a `switch`, and whose switch discriminant is a call
expression. It then searches two-parameter functions whose generated source contains both
`charCodeAt` and `fromCharCode`, and requires a top-level expression statement that calls the
dispatcher with an array argument ([`detect`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/ControlFlowFlattening/cff.js#L32-L92)).

The output is a generated source object `{ code, changed, info }`. `code` contains one generated
function for each concrete state-vector entry reachable from the main call, with recovered block
statements and branch/return edges. The emitter chooses structured statements for an acyclic
recoverable graph and an explicit local `state`/`switch` machine otherwise; later de-scoping and
cleanup can promote shared state properties and remove recognized residue. A non-matching program
returns its original source string with `changed: false`.

## 2. Algorithm

1. **Detect the dispatcher and entry.** Walk top-level function declarations in source order. A
   candidate needs the `while`/`!==`/sum-call shape, a nested switch, and a matching top-level
   dispatcher call whose first argument is an array. The final matching top-level call encountered
   by the source loop supplies the main entry. The decoder name is a heuristic from generated
   function text, not a binding contract.

2. **Define the concrete evaluator.** `makeEval` recognizes numeric, string, and boolean literals,
   parenthesized expressions, selected unary and binary operators, short-circuit logical
   expressions, tracked numeric-array members, calls to the discovered decoder, and calls to the
   discovered sum helper. `evalArray` maps a concrete array to numeric values. Any unsupported
   node or non-numeric array item throws `NotConcrete`; the folder then either leaves that node or
   propagates a non-`NotConcrete` error ([`makeEval`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/ControlFlowFlattening/cff.js#L98-L224)).

3. **Fold concrete expressions without crossing function bindings.** `makeFolder` first tries to
   replace an entire node with a literal result, rejects non-finite numeric results, and otherwise
   recursively visits Babel visitor keys. Nested functions are not descended into because their
   state binding is different ([`makeFolder`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/ControlFlowFlattening/cff.js#L230-L280)).

4. **Seed function records and rewrite nested dispatcher calls.** The main concrete state array
   becomes `f_main`. A call to the dispatcher carrying another concrete array is rewritten to a
   generated function name and its baked-in state argument is removed. Closure assignments and
   concrete closure call sites are recorded so nested V-arrays can be supplied to later
   simulation ([`deobfuscate` setup, `rewriteKCalls`, and `recordClosures`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/ControlFlowFlattening/cff.js#L285-L377)).

5. **Simulate each reachable state vector.** For a function record, calculate the sum of the
   current vector, stop at the terminal sum, and select the switch case whose test evaluates to
   that sum. Clone the case tail, apply supported state assignments (`=`, `+=`, `-=`, `*=`), fold
   side effects, rewrite nested calls, and record a return, goto, or concrete branch terminator.
   Branch arms receive independent copies of the current vector; newly seen vectors enter the
   worklist. Nested V-backed loops are linearized through the same concrete state machinery, with
   a 100,000-step nested guard and a 50,000-state per-function guard ([`linearizeNestedVM`, `stepStatements`, and `simulate`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/ControlFlowFlattening/cff.js#L379-L602)).

6. **Normalize the recovered graph.** Relay blocks with an empty body and one goto are collapsed;
   unreachable blocks are removed. `tryStructure` computes dominators/post-dominators and emits
   nested `if` statements only when the graph is acyclic and its arms can be visited without a
   conflict. A cycle or unstructurable join returns `null`, selecting the explicit-state emitter
   ([`optimize` and `tryStructure`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/ControlFlowFlattening/cff.js#L604-L774)).

7. **Emit an alternative representation.** The structured path returns a function with the
   recovered block body. The fallback creates a local numeric `state`, an unbounded `for` loop,
   and switch cases whose terminators assign the next state, return, or throw an unreachable
   error. Both forms preserve the generated function parameters `T`, `U`, and `V` and are later
   passed through the same de-scoping cleanup ([`paramsForFunction` and `emitFunction`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/ControlFlowFlattening/cff.js#L776-L840)).

8. **Remove sample scaffolding and generate.** Promote static `T[scope][property]` accesses to
   `scope_property` variables, strip scope-threading object properties, remove whole-scope
   assignments, hoist closure functions, simplify sequence callees, propagate constant
   `undefined`, fold constant `if`s, eliminate dead stores, drop trailing void returns, remove
   unused parameters, inline trivial forwarders, inline eligible void helpers, and convert safe
   bracket properties to dots. Finally retain only variables referenced by the emitted functions,
   optionally retain the decoder/sum helper when a generated function still calls it, and generate
   the final program ([`promoteScope` through `bracketsToDots`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/ControlFlowFlattening/cff.js#L841-L1265) and [`final cleanup/emission`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca71615a665656bd802/ControlFlowFlattening/cff.js#L1267-L1363)).

The transform's state flow is:

```text
source AST
  -> detected dispatcher + concrete main state vector
  -> state-vector worklist and per-entry CFGs
  -> structured body or explicit state/switch body
  -> scope promotion, closure/parameter cleanup, and literal normalization
  -> generated { code, changed, info }
```

## 3. Implementation

| Phase | Source anchor | Representation and material behavior |
| --- | --- | --- |
| Recognition | [`detect`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/ControlFlowFlattening/cff.js#L32-L92) | A top-level dispatcher record contains function declarations, sum/decoder names, the switch, terminal value, and main array call. It returns `null` for a missing dispatcher or main call. |
| Constant domain | [`makeDecoder`, `memberKey`, `makeEval`, `evalArray`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/ControlFlowFlattening/cff.js#L98-L224) | Numeric/string/boolean values, selected operators, tracked array members, the Caesar-style decoder, and numeric array entries are represented as concrete evaluator results; unsupported nodes are `NotConcrete`. |
| Literal folding | [`litNum`, `litFromResult`, `makeFolder`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/ControlFlowFlattening/cff.js#L230-L280) | Maximal concrete subexpressions become fresh Babel literals; nested functions are left untouched and non-finite numeric results are not folded. |
| Entry and closure state | [`nameForEntry`, `rewriteKCalls`, `recordClosures`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/ControlFlowFlattening/cff.js#L303-L377) | A map keys function records by comma-joined state vectors; generated names are `f_main`/`f_N`; nested calls drop baked-in state arrays and closure sites may supply a concrete V-array. |
| CFG simulation | [`applyStateAssign`, `findCaseIndex`, `linearizeNestedVM`, `simulate`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/ControlFlowFlattening/cff.js#L379-L602) | Each record stores a concrete entry, keyed blocks, and an ordered list. Block terms are exit, return, goto, or a two-arm branch; guards bound nested and outer simulation. |
| Graph normalization | [`optimize`, `computeIdom`, `tryStructure`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/ControlFlowFlattening/cff.js#L613-L774) | Relay edges and unreachable blocks are removed; acyclic graphs can become `if`/return bodies, while cycles and unstructurable joins select the explicit-state fallback. |
| Function emission | [`paramsForFunction`, `emitFunction`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/ControlFlowFlattening/cff.js#L776-L840) | Structured functions or local `state`/`for`/`switch` functions are built as Babel AST nodes with `T`, `U`, and `V` parameters. |
| De-scoping | [`promoteScope` through `hoistClosures`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/ControlFlowFlattening/cff.js#L841-L964) | Static scope properties become top-level-style names, scope-threading assignments are removed, and identifier closure assignments are hoisted. |
| Cleanup fixpoint | [`simplifySeqCallees` through `bracketsToDots`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/ControlFlowFlattening/cff.js#L965-L1265) | Binding-spelling cleanup performs parameter/forwarder analysis, undefined propagation, constant-if folding, dead-store elimination, helper inlining, and safe member normalization. |
| Final generation | [`stripTrailingVoidReturns` and final assembly](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/ControlFlowFlattening/cff.js#L1267-L1363), [`controlFlowFlattening.js`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/ControlFlowFlattening/controlFlowFlattening.js#L22-L66) | The final program retains only referenced scope variables and residual decoder/sum helpers, then generates code with comments and minimal escaping; the wrapper exposes file/string APIs and CLI output. |

The source uses a source-level transform, not a runtime VM or a validation oracle. The supplied
exact example and generated-input profile are identified in the registry.

## 4. Upstream Effects

There is no earlier decoder pass. Babel parsing is the only input substrate, and the transform's
own detector, evaluator, state worklist, emitters, and cleanup operate on the same parsed program.
The companion character decoder is called only from the concrete evaluator when a decoder call is
encountered; it does not establish an independent string-concealing pipeline.

On the producer side, JS-Confuser places Control Flow Flattening at order 24 after String
Concealing, Variable Masking, and duplicate-literal removal, and before moved declarations, label
renaming, minification, AST scrambling, and variable renaming ([`order.ts`](https://github.com/MichaelXF/JS-Confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/order.ts#L24-L35)).
Those later producer stages can alter names and expression spelling. The `CFF-213` profile names
one encoder configuration; this source-only transform page does not infer a decoder pipeline order
or transfer coverage from it.

## 5. Known Gaps

- Detection is limited to the observed top-level function/`while`/`switch`/sum shape. It also
  identifies the companion decoder from generated source text and selects the last matching
  top-level dispatcher call encountered by the source loop; neither is a general binding/data-flow
  proof.
- The evaluator recognizes only its explicit literal, selected-operator, tracked-array, decoder,
  and sum domain. Unsupported expressions, dynamic array entries, non-numeric state elements, and
  non-concrete branches decline folding or can abort the source transform.
- State simulation assumes concrete numeric state transitions and exact switch-case sums. Indirect
  targets, unknown state writes, unrelated decoys, nested forms outside the V-array convention, and
  state-space growth beyond the guards are outside the documented boundary.
- `tryStructure` rejects cyclic graphs and falls back to the explicit state machine; the fallback
  itself preserves a generated dispatcher representation rather than proving recovered source
  semantics. Unreachable or unstructurable conditions are not a semantic validation failure path.
- De-scoping and cleanup use source-specific names and syntactic shape. They do not prove alias,
  closure, `this`, constructor, side-effect, host-global, or generated-code equivalence, and a
  residual decoder/sum helper can remain when emitted code still refers to it.
- The wrapper propagates parse, read, write, evaluation, simulation, and generation errors. No
  second pass-through catch or runtime validator is supplied by this sample.
- The pinned fixtures, tests, and retained generated output do not establish new behavioral results.
  Exact-example success, the `CFF-213` transfer population, runtime equivalence, unseen coverage,
  and production decoder support remain separate bounded claims.

## Source

The source of record is the pinned
[`ControlFlowFlattening/cff.js`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/ControlFlowFlattening/cff.js)
at revision `e90be6ca716e28f4bba91fe39615a665656bd802`. The wrapper is
[`controlFlowFlattening.js`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/ControlFlowFlattening/controlFlowFlattening.js#L22-L66).
The source spans are summarized in the [Control Flow Flattening plugin root](../plugins/control-flow-flattening.md)
and the reverse [source map](../source-map.md).

## Fixtures

| Pinned file | Claim it pins | Evidence boundary |
| --- | --- | --- |
| [`ControlFlowFlattening/input.js`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/ControlFlowFlattening/input.js) | Main state-array call and flattened dispatcher shape | Source fixture. |
| [`ControlFlowFlattening/original.js`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/ControlFlowFlattening/original.js) | Readable source-side reference | Provenance only; no comparative result is claimed. |
| [`ControlFlowFlattening/output.js`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/ControlFlowFlattening/output.js) | Retained structured/generated output shape | Generated-output provenance only. |
| [`ControlFlowFlattening/regular.js`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/ControlFlowFlattening/regular.js) and [`regular_out.js`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/ControlFlowFlattening/regular_out.js) | Ordinary control-flow negative pair | Intended negative evidence only. |
| [`ControlFlowFlattening/test.js`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/ControlFlowFlattening/test.js) and debug artifacts | Intended detection, folding, simulation, and comparison checks | Test-intent and diagnostic provenance. |
