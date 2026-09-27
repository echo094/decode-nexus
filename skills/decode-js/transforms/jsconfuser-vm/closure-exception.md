# jsconfuser-vm closures and exceptions

## 1. Target

`emitClosureException(wordcode, references, functions, cfg, frames, closures, handlers)` is
the target-local, parse-only closure/exception analysis. It returns the immutable
`jsconfuser-vm-closure-exception-emission.v1` record set after exact reconstruction of the
canonical wordcode, reference, function, CFG, frame, closure, and handler predecessors. The analysis joins closure capture/lifetime facts with handler/finally states,
completion routes, and control fallback requirements for a later emitter. It does not emit
JavaScript, execute the target, or claim final runtime semantics.

## 2. Algorithm

The analysis copies and reconstructs every canonical predecessor, then equality-checks function
ownership, frames, CFG, call/completion routes, closure facts, and handler state. It emits
complete instruction records with handler state-in, closure-site records, capture and binding
records, upvalue uses, lifetime/termination transitions, handler/finalizer records, state
merges, transitions, jump checks, throw pads, and stable completion routes.

Closure records preserve the exact local/upvalue capture roles and owner/lifetime transitions
that the predecessor facts prove. They do not infer how many runtime closure instances a
program will allocate. Handler records preserve catch/finally states and abrupt/completion
routes; they do not rewrite those states into source-level `try` syntax.

For each function, the analysis keeps the proven structured/opaque boundary. A function remains
`opaque` unless the CFG proof requires an irreducible fallback, in which case the result
records an exact state-machine requirement with block/edge identity. Every record carries
`semanticBoundary: later-packet` marks the deferred semantic interpretation, and all instruction, closure, handler, transition, and
route coverage must be complete and unique.

## 3. Implementation

The implementation validates exact predecessor snapshots from copied inputs, stable owner and route
IDs, captures/bindings, handler/finalizer state graphs, jump checks, throw pads, completion
routes, per-function fallback classification, and full census coverage. It deeply freezes
the result and diagnostics and never mutates its inputs. Unsupported or incomplete
predecessors decline atomically; no guessed catch binding, upvalue value, closure instance,
or runtime exception outcome is inserted.

## 4. Upstream Effects

| Producer or consumer | Contract used here or carried forward |
|---|---|
| wordcode/reference/function/CFG/frame/closure/handler predecessors | Supply exact instruction, frame, CFG, call/completion, closure, and handler facts; this analysis checks every predecessor before composing records. |
| [structured-control](structured-control.md) | Supplies the control-plan boundary that this analysis preserves while adding handler state and completion routes. |
| [call-completion](call-completion.md) | Supplies stable call/return/throw completion records and route identity; this analysis does not redefine call grammar. |
| [standalone-diagnosis](standalone-diagnosis.md) | Calls the analysis during fresh predecessor preflight and requires complete coverage. |
| [standalone-decode](standalone-decode.md) | Uses the validated records for closure and exception emission. |

This is the final parse-only shape boundary before the target-local JavaScript emitter.

## 5. Known Gaps

The record set does not prove final JavaScript exception semantics, closure instance
multiplicity, host behavior, value-state resolution, universal source recovery, or
production equivalence. Arbitrary reducible control remains opaque where the proof is not
narrow; hardening/PATCH, concealed/encoded bytecode, earlier eras, debugger execution, and
target execution are not covered.

## Source

The stage is implemented by [closure-exception-records.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/closure-exception-records.js), [emit-closure-exception.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/emit-closure-exception.js). The [standalone diagnosis](standalone-diagnosis.md)
composes its result with predecessor records. The encoder contracts are described in
[instruction-set.md](../../../js-confuser-vm/instruction-set.md) and
[container-wordcode.md](../../../js-confuser-vm/container-wordcode.md).

## Fixtures

| Committed fixture or test control | Claim pinned |
|---|---|
| [f-closures-state](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/raw/f-closures-state/encoded.js) | Closure creation sites, nested capture roles, and lifetime transitions. |
| [f-throw-catch](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/raw/f-throw-catch/encoded.js) | Throw pads, handler state, and exceptional completion routes. |
| [f-finally-abrupt](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/raw/f-finally-abrupt/encoded.js) | Finally state, abrupt completion, and replacement/resumption routes. |
| [emit-closure-exception.test.js](../../../../decoder/decode-js/test/vm/jsconfuser-vm/emit-closure-exception.test.js) | Synthetic irreducible fallback and malformed/stale/underflow controls, plus immutable result behavior. |
