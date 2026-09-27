# Extract the target-local container

## 1. Target

Recognize the complete baseline `jsconfuser-vm-container.v1` boundary in source text or a
Babel `File`/`Program` AST without relying on generated names, comments, or runtime execution.
The accepted representation is the non-encoded numeric-u32 container emitted by the pinned
`js-confuser-vm` baseline.

## 2. Algorithm

Parse source as a script with return-outside-function syntax allowed, then index top-level
declarations, bindings, identifier paths, and reference paths. Candidate roles are selected by
shape and binding identity:

- the primitive constant pool and non-empty unsigned numeric word array;
- exact canonical opcode, sentinel, and frame-slot objects;
- scalar roots for main start/register count, bytecode encoding, timing checks, header size, and
  frame start;
- `Upvalue`, `Closure`, and `VM` constructors and their prototype methods; and
- the global object, VM construction, bytecode decoder, and root `run` call.

Each candidate must be unique. The extractor then checks the role graph: opcode and slot maps are
used by the dispatch/runtime machinery, upvalues connect to register storage and close operations,
closures connect to VM calls, and the boot call uses the extracted main values. The runtime graph
and scalar branches are checked together so an isolated declaration cannot satisfy the boundary.

## 3. Implementation

The result has schema `jsconfuser-vm-container.v1`, `encoding: "numeric-u32"`, and a frozen
`roles` object containing:

- `pool` and `words`, each with the declaration `name` and copied `values`;
- `op`, `sentinels`, and `slots`, each with its declaration name and canonical `values`;
- `scalars`, whose entries contain declaration `name` and scalar `value` for
  `MAIN_START_PC`, `MAIN_REG_COUNT`, `ENCODE_BYTECODE`, `TIMING_CHECKS`, `HEADER_SIZE`, and
  `FRAME_START`;
- constructor names, the uniquely identified upvalue and VM method names, and boot roots for
  globals, VM, decoder, and the root method.

`schemaVersion` names this decoder-owned Packet A result shape. The `.v1` suffix versions
that internal record contract; it is not a marker in the encoded JavaScript or the encoder's
release version. The wordcode reader requires this exact schema string and `numeric-u32`
encoding before using the extracted roles.

`container-role-helpers.js` holds AST shape and binding utilities. `container-runtime-roles.js`
identifies VM methods, the boot graph, decoder mode, and scalar roles. `extract-container.js` checks
the connected runtime graph, copies pool values, assembles the result, and exposes the public entry
points.

`diagnoseContainer` returns a frozen `{ ok, result, diagnostic }` envelope. `extractContainer`
and `extractContainerFromSource` return the result or `null`. Parser errors and structural
declines are atomic: the input AST/source is not rewritten and no partial role set is returned.
Missing, duplicate, ambiguous, altered, or disconnected roles decline. Numeric mode is required;
encoded bytecode and optional hardening/runtime variants are not reinterpreted as baseline roles.

## 4. Upstream Effects

This is the source-boundary pass and has no earlier target-local decoder schema. It supplies the
container schema to [read-wordcode.md](read-wordcode.md), and its copied pool, words, maps, and
scalar/frame roots are the authority used by all later validators. The standalone decoder invokes
it before any wordcode or semantic shape pass.

## 5. Known Gaps

- Encoded bytecode, randomized maps/frame layouts, dispatcher/self-modifying regions, timing
  hardening, and other optional variants are outside this baseline contract.
- The extractor recognizes the VM container and boot graph; it does not execute the VM or infer
  JavaScript meaning from the word stream.
- A different container generation or a second encoder era requires separate structural evidence;
  this shape is not a name-based compatibility layer.

## Source

The stage uses
[container-role-helpers.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/container-role-helpers.js),
[container-runtime-roles.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/container-runtime-roles.js),
and the public
[extract-container.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/extract-container.js)
entry. The [standalone diagnosis](standalone-diagnosis.md) composes its result with predecessor
records. The encoder contracts are described in
[instruction-set.md](../../../js-confuser-vm/instruction-set.md) and
[container-wordcode.md](../../../js-confuser-vm/container-wordcode.md).

## Fixtures

| Committed fixture or test control | Claim pinned |
|---|---|
| [f-literals-order](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/raw/f-literals-order/encoded.js) | Complete numeric baseline container and connected boot/runtime role graph. |
| [ordinary-near-miss](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/negative/ordinary-near-miss/encoded.js) | Ordinary JavaScript declines without a partial role result. |
| [missing-container-role](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/negative/missing-container-role/encoded.js) | Missing required container role declines atomically. |
| [encoded-bytecode-mode](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/negative/encoded-bytecode-mode/encoded.js) | Encoded bytecode is refused at the numeric-container boundary. |
| [extract-container.test.js](../../../../decoder/decode-js/test/vm/jsconfuser-vm/extract-container.test.js) | Synthetic renamed-binding/comment-stripped acceptance and ambiguous-role, altered-map, slot, or boot-root declines at container extraction. |
