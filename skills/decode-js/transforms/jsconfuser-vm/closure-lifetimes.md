# Analyze closure and upvalue lifetimes

## 1. Target

Produce the immutable `jsconfuser-vm-closure-lifetimes.v1` model of capture pairs, stable owner
bindings, upvalue uses, closure provenance, escape events, and open/closed lifetime states. This
is static target-local analysis; it does not execute or emit the VM.

## 2. Algorithm

Validate the exact wordcode, references, function ownership, CFG, and call-frame predecessors.
Resolve each child capture recursively: a local capture names a parent function register, while an
upvalue capture resolves through the parent closure’s capture pair. The resolved identity is
`binding:<ownerFunctionId>:register:<index>`, independent of generated variable names.

For every closure site, copy its descriptor capture pairs and mark reachability. Scan
`LOAD_UPVALUE`/`STORE_UPVALUE` uses, resolve them to binding IDs, and retain register, operation,
and reachability. Every binding must have a proved terminal close event from the owner’s reachable
return/throw completion path; a missing close event declines. This reflects the runtime’s close
before-frame-release rule.

Run a finite register provenance analysis. Empty values represent non-closures, unknown values
represent unresolved values, and closure values carry creation-site IDs. `MAKE_CLOSURE` creates a
site value, `MOVE` copies it, collection construction unions inputs, and ordinary destinations
kill precision. Normal internal calls use return summaries; exceptional call routes use the input
state. Iterate summaries to a finite fixed point or decline.

Use the resulting closure values to record internal/external invocation, call argument/receiver,
property/global stores, and returns. A proven return or global store is a closed escape; an
internal call argument can preserve an open path. Each use receives `open`, `closed`, or
`open-or-closed` possible state without inventing a target for host calls.

## 3. Implementation

The result has schema `jsconfuser-vm-closure-lifetimes.v1`, `encoding: "numeric-u32"`, counts,
function summaries, `capturePairs`, `bindings`, `uses`, `closureSites`, `terminationEvents`, and
source metadata naming the consumed wordcode, references, functions, CFG, and call-frame schemas.
Bindings include owner function/register, pair/use IDs, and lifecycle fields. Closure sites include
creation/child/destination identity, reachability, pair IDs, and escape events. Uses preserve
upvalue operation, binding, reachability, and possible states.

The modules separate shared schemas and value helpers (`closure-lifetimes-contract.js`), Packet B
validation (`closure-lifetimes-wordcode.js`), Packet C validation (`closure-lifetimes-input.js`),
function/CFG/call-frame ownership checks (`closure-lifetimes-ownership.js`), and capture,
provenance, and lifetime flow (`closure-lifetimes-flow.js`).

`diagnoseClosureLifetimes` returns a deep-frozen envelope; `analyzeClosureLifetimes` and its alias
return the frozen result or `null`. The pass validates predecessor snapshots and declines malformed
captures, missing owners, stale routes, unknown lifetimes, or nonconvergent provenance atomically.

## 4. Upstream Effects

This analysis consumes [read-wordcode.md](read-wordcode.md),
[validate-references.md](validate-references.md),
[partition-functions.md](partition-functions.md), [build-cfg.md](build-cfg.md), and
[build-call-frames.md](build-call-frames.md). Its binding and lifecycle facts are consumed by
the target-local closure/call emission layer; its result is also independently cross-checked by
the standalone decoder before later reconstruction.

## 5. Known Gaps

- Arbitrary host-call behavior, object/property aliasing, and dynamic values are not treated as
  proven internal closure targets or precise escape paths.
- The analysis reports possible open/closed states; it does not perform runtime garbage
  collection, execute user code, or emit equivalent JavaScript.
- It covers the pinned baseline’s explicit capture/close machinery. Optional hardening and another
  encoder era require separate evidence.

## Source

The public stage is
[analyze-closure-lifetimes.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/analyze-closure-lifetimes.js).
It uses
[closure-lifetimes-contract.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/closure-lifetimes-contract.js),
[closure-lifetimes-wordcode.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/closure-lifetimes-wordcode.js),
[closure-lifetimes-input.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/closure-lifetimes-input.js),
[closure-lifetimes-ownership.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/closure-lifetimes-ownership.js),
and
[closure-lifetimes-flow.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/closure-lifetimes-flow.js).
The [standalone diagnosis](standalone-diagnosis.md) composes this stage.

## Fixtures

| Committed fixture | Claim pinned |
|---|---|
| [f-closures-state](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/raw/f-closures-state/encoded.js) | Local capture identity, owner-return close, nested upvalue resolution, and child reads/writes. |
| [f-arrow-lexical-state](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/raw/f-arrow-lexical-state/encoded.js) | Lexical host use without inventing an internal VM closure target. |
