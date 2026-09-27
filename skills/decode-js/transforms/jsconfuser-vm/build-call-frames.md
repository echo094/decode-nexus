# Build call frames and completion routes

## 1. Target

Build the immutable `jsconfuser-vm-call-frames.v1` model that relates serialized call sites to
frame layout, proven internal closure targets, normal continuations, exceptional completion, and
return/throw records.

## 2. Algorithm

Validate the wordcode, references, function ownership, and CFG as exact predecessor results. For
each `CALL`, `CALL_METHOD`, and `NEW`, preserve fixed or spread argument metadata and identify
destination, callee, receiver, and continuation from the parsed form.

Run finite closure provenance over function CFGs. `MAKE_CLOSURE` produces the child function ID;
`MOVE` copies a proven cell; normal call results use fixed-point return summaries. A `NEW` call may
retain a proven constructor callee, but its constructed result is unknown for later closure
provenance; unknown/host callee values receive no invented internal target. Exceptional edges use
the call's input state, while normal continuation uses its output state. A call without a normal
continuation or exceptional completion declines.

Represent each function’s frame with the canonical header size, register offset/window, parameter
and rest metadata, and the root frame base when applicable. Constructor calls use an
`allocate-this` state; ordinary calls use `ordinary`. Record caller destinations for proven callee
IDs. Preserve every serialized `RETURN` and `THROW` record, including unreachable records, with a
`reachable` flag and the exact CFG completion routes.

## 3. Implementation

The result has schema `jsconfuser-vm-call-frames.v1`, `encoding: "numeric-u32"`, counts, a copied
`frame` summary, per-function `frames` and function records, flattened `callSites`, `returns`,
`throws`, and `completionRoutes`, plus source schema metadata. Call records include argument form,
callee functions, constructor state, normal target, return destination, exceptional completion,
and CFG handler state. Function records contain frame shape, call sites, returns, throws, and
completion routes.

`diagnoseCallFrames` returns a frozen envelope. `buildCallFrames` and its model alias return the
frozen result or `null`; all predecessor inputs remain untouched. Stale schemas, call encodings,
provenance, or route/state metadata decline atomically.

## 4. Upstream Effects

This pass consumes [read-wordcode.md](read-wordcode.md),
[validate-references.md](validate-references.md),
[partition-functions.md](partition-functions.md), and [build-cfg.md](build-cfg.md). Its proven
callee IDs and completion routes feed [closure-lifetimes.md](closure-lifetimes.md) and
[exception-finally.md](exception-finally.md); its frame records are the target-local contract for
return/call reasoning, not evidence that a host callable was executed.

## 5. Known Gaps

- Dynamic host calls, unknown callee values, and constructor results that cannot be proven as VM
  closures retain empty internal-target sets; no target is invented from names or call syntax.
- The model is static and target-local. It does not execute host functions, resolve arbitrary
  JavaScript aliases, or emit reconstructed code.
- Return summaries remain unknown when reachable returns do not carry a proven closure value; later
  analyses must preserve that uncertainty.

## Source

The stage is implemented by [call-frames-preflight.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/call-frames-preflight.js), [build-call-frames.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/build-call-frames.js). The [standalone diagnosis](standalone-diagnosis.md)
composes its result with predecessor records. The encoder contracts are described in
[instruction-set.md](../../../js-confuser-vm/instruction-set.md) and
[container-wordcode.md](../../../js-confuser-vm/container-wordcode.md).

## Fixtures

| Committed fixture or test control | Claim pinned |
|---|---|
| [f-closures-state](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/raw/f-closures-state/encoded.js) | Internal closure targets, frame ownership, and return relationships. |
| [focused-call-method-spread](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/focused/focused-call-method-spread/encoded.js) | Method receiver preservation and fixed/spread call argument layout. |
| [focused-new-spread](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/focused/focused-new-spread/encoded.js) | Constructor call state and spread argument layout. |
| [f-spread-order](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/raw/f-spread-order/encoded.js) | Ordinary call spread order and caller continuation. |
| [f-finally-abrupt](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/raw/f-finally-abrupt/encoded.js) | Call completion routes through nested finally paths. |
| [build-call-frames.test.js](../../../../decoder/decode-js/test/vm/jsconfuser-vm/build-call-frames.test.js) | Synthetic dynamic empty-target, stale-state, completion-route, and input-immutability controls. |
