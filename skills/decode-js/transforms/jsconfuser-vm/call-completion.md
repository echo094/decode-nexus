# jsconfuser-vm calls and completion

## 1. Target

`emitCallCompletion(wordcode, references, functions, cfg, frames, closures)` is the
target-local, parse-only call/completion analysis. It returns the immutable
`jsconfuser-vm-call-completion.v1` record set after exact reconstruction of the canonical
wordcode, reference, function, CFG, frame, and closure predecessors.
It makes call grammar, receiver preservation, constructor state, normal/exceptional routes,
and return/throw completion explicit for later emission. It does not call a callee, execute
the VM, or emit JavaScript.

## 2. Algorithm

The analysis reconstructs and equality-checks the canonical predecessor schemas, function/owner maps,
frames, call sites, closure facts, and CFG routes from copies. It emits an instruction leaf for
every B instruction and detailed records for `CALL`, `CALL_METHOD`, `NEW`, `RETURN`, and
`THROW`. Calls use the instruction-set sentinel `65535` to distinguish spread from fixed
arity; payload width and register positions are validated exactly.

| Opcode | Read order recorded | Receiver/constructor fact |
|---|---|---|
| `CALL` | callee, argument count, fixed arguments or spread payload | no implicit receiver |
| `CALL_METHOD` | receiver, callee, argument count, fixed arguments or spread payload | receiver is preserved for the method call |
| `NEW` | constructor, argument count, fixed arguments or spread payload | allocate `this`; explicit object return may replace it |

Call targets are classified as internal closures only when F proves the callee function
mapping. Otherwise the target is `host-or-dynamic`; the analysis does not guess a function from a
register value. Each call carries destination, read order, fixed/spread grammar, receiver or
constructor state, and normal/exceptional route IDs. `RETURN` and `THROW` records preserve
source/payload registers, caller destinations, constructor callers, and completion route
records. G contributes closure-owner and lifetime facts without asserting closure instance
multiplicity.

## 3. Implementation

The implementation validates exact predecessor reconstruction, call payload boundaries, sentinel
grammar, owner/reachability maps, route identity, completion coverage, and the absence of
dropped or duplicated instruction/call/completion/route records. Results and nested arrays
are deeply frozen, and all inputs remain unchanged. Constructor records preserve the
allocate-this/object-return rule as a semantic boundary; they are not evaluated while
parsing.

## 4. Upstream Effects

| Producer or consumer | Contract used here or carried forward |
|---|---|
| wordcode/reference/function/CFG/frame/closure predecessors | Supply exact instructions, constants, function frames, CFG routes, call sites, and closure lifetime facts; this analysis checks their schemas before recording calls. |
| [structured-control](structured-control.md) | Carries the same instruction leaves into a control plan; this analysis owns call/completion meaning and does not emit control syntax. |
| [closure-exception](closure-exception.md) | Uses the stable completion/route facts when adding closure and handler records. |
| [standalone-diagnosis](standalone-diagnosis.md) | Calls the analysis during fresh predecessor preflight and requires complete records. |
| [standalone-decode](standalone-decode.md) | Emits calls, returns, and throws from the validated records. |

The record set is a later-emission input, not a replacement for the runtime or source
program.

## 5. Known Gaps

Host/dynamic call behavior, coercion, proxy effects, callee side effects, closure instance
multiplicity, and final constructor/exception semantics are not inferred. Upvalue details,
property semantics, structured syntax, target execution, hardening/PATCH, concealed/encoded
input, earlier eras, and universal JavaScript equivalence remain outside this analysis.

## Source

The stage is implemented by [call-completion-input.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/call-completion-input.js), [emit-call-completion.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/emit-call-completion.js). The [standalone diagnosis](standalone-diagnosis.md)
composes its result with predecessor records. The encoder contracts are described in
[instruction-set.md](../../../js-confuser-vm/instruction-set.md) and
[container-wordcode.md](../../../js-confuser-vm/container-wordcode.md).

## Fixtures

| Committed fixture or test control | Claim pinned |
|---|---|
| [f-closures-state](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/raw/f-closures-state/encoded.js) | Proven internal closure targets, frames, and normal return destinations. |
| [focused-call-method-spread](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/focused/focused-call-method-spread/encoded.js) | Method receiver, fixed/spread grammar, and host-or-dynamic call classification. |
| [focused-new-spread](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/focused/focused-new-spread/encoded.js) | Constructor allocation state and spread argument grammar. |
| [f-spread-order](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/raw/f-spread-order/encoded.js) | Ordinary call argument read order and continuation records. |
| [f-throw-catch](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/raw/f-throw-catch/encoded.js) and [f-finally-abrupt](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/raw/f-finally-abrupt/encoded.js) | Throw/catch and finally completion routes. |
| [emit-call-completion.test.js](../../../../decoder/decode-js/test/vm/jsconfuser-vm/emit-call-completion.test.js) | Synthetic malformed/stale-input declines, host/internal target controls, and immutable result behavior for call completion. |
