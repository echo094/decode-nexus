# Partition serialized functions

## 1. Target

Assign every parsed instruction to exactly one serialized function and return the immutable
`jsconfuser-vm-functions.v1` ownership contract. The partition is lexical/serialized ownership;
it does not claim control-flow, call, or exception semantics.

## 2. Algorithm

Validate the container, wordcode, reference/frame result, and predecessor metadata as one coherent
stream. Use the root entry and every `MAKE_CLOSURE` descriptor entry as function starts. Sort the
starts and form half-open intervals: each interval ends at the next entry or at the end of the
word stream. Require that intervals cover all instructions exactly once and that each closure
descriptor has one coherent child function and parent creation site.

Create an ownership map from instruction PC to function ID and attach closure sites with parent,
child, destination, creation PC, and descriptor information. Recheck every label reference. A
function-entry label may cross ownership to create the child edge; all ordinary target, exit,
handler, finally, and throw-pad labels must remain in their source function. Missing/orphaned
descriptors, overlapping or uncovered intervals, and cross-function ordinary edges decline.

## 3. Implementation

The result has schema `jsconfuser-vm-functions.v1`, `encoding: "numeric-u32"`, word/instruction
counts, sorted `entryPcs`, and function records containing IDs, kind, start/end PCs, parameter,
register, capture, and rest metadata, parent ID, instruction PCs, optional descriptor, and
closure sites. `ownership` maps each instruction PC to its function; `labels` carries normalized
source/target function IDs; `frame` preserves the root frame summary and slots.

`partition-functions-input.js` checks the Packet A/B/C schemas, frame metadata, labels, and closure
descriptors before interval construction. `partition-functions.js` assigns intervals, attaches
closure sites, enforces local targets, and freezes the result.

`diagnoseFunctionPartition` returns a frozen envelope. `partitionFunctions` and its ownership
alias return the frozen result or `null`. The pass copies predecessor data into its result and
does not mutate the container, wordcode, or references.

## 4. Upstream Effects

The partition consumes [read-wordcode.md](read-wordcode.md) and
[validate-references.md](validate-references.md), with the container as a consistency source. It
provides function intervals, ownership, entry labels, and closure sites to [build-cfg.md](build-cfg.md)
and downstream call/closure/exception analyses. Later passes must not infer function boundaries
by scanning for likely opcodes.

## 5. Known Gaps

- Ownership follows serialized closure entry descriptors; it does not prove reachability, infer
  dynamic function targets, or build a CFG.
- Cross-function edges are permitted only for the closure-entry relation represented by
  `MAKE_CLOSURE`; runtime host behavior is outside this partition.
- The accepted shape is for the pinned baseline and does not generalize optional dispatcher or
  self-modifying layouts.

## Source

The predecessor validator is
[partition-functions-input.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/partition-functions-input.js);
the public stage and interval builder are
[partition-functions.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/partition-functions.js).
The standalone wiring is
[diagnose-standalone.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/diagnose-standalone.js).
The pinned entry-PC and closure descriptor sources are
[resolveLabels.ts](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/transforms/bytecode/resolveLabels.ts#L21-L107)
and
[compiler.ts](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/compiler.ts#L617-L735).

## Fixtures

| Committed fixture or test control | Claim pinned |
|---|---|
| [f-closures-state](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/raw/f-closures-state/encoded.js) | Serialized closure entries, parent creation sites, and complete function intervals. |
| [f-finally-abrupt](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/raw/f-finally-abrupt/encoded.js) | Multiple function entries with function-local handler/finally labels. |
| [finally-stale-target](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/negative/finally-stale-target/encoded.js) | Atomic decline when a finally throw-pad label crosses function ownership. |
| [partition-functions.test.js](../../../../decoder/decode-js/test/vm/jsconfuser-vm/partition-functions.test.js) | Function interval coverage, parent/child ownership, ordinary-edge locality, and atomic partition declines. |
