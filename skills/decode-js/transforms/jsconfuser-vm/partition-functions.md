# Partition serialized functions

## 1. Target

Give every parsed instruction one serialized function owner, then relate closure creation sites
and direct labels to those owners. Success returns deeply frozen `jsconfuser-vm-functions.v1`
(Packet D); refusal returns no partial partition. This establishes intervals and lexical creation
relationships, not call reachability or a control-flow graph.

Readers need functions, lexical captures and half-open intervals, plus [B's wordcode](read-wordcode.md),
[C's descriptors/labels](validate-references.md) and the encoder's [serialized function interfaces](../../../js-confuser-vm/container-wordcode.md).
Source scope/binding identity belongs to [A](extract-container.md) and [Babel](../../babel.md).
VM function ownership here is a word-PC interval, not a Babel source function path.

## 2. Algorithm

The encoder concatenates function bodies into one stream and closure descriptors identify their
entry PCs. Use the root entry and each distinct child entry to cut that stream into intervals.
Sorting entries fixes stable IDs and bounds: a function owns every instruction starting at or
after its entry and before the next entry (or wordCount for the last function). B/C already
proved that entries are instruction starts, so intervals cover instructions without guessed
opcode scans or redundant coverage validation.

For each MAKE_CLOSURE, join its creation PC to the parent owner and its entry PC to the child.
Self-entry creation cannot define a child. Ordinary partitioning needs one unique parent per
child, although multiple sites in the same parent may create it. Then join C's direct label rows
to owners: functionEntry labels create a cross-owner relation, while branches/exits/handlers/
finally/throwPad targets must stay within their source owner.

### Worked example: serialization and lexical parent differ

This **synthetic ownership projection** has instruction starts [0,9,11,14,23,26],
wordCount=28, root entry 0, and distinct child entries 11 and 23. A root MAKE_CLOSURE at 0
targets 11; another at 14 targets 23. C has already validated both descriptors.

| Function ID | Interval | Instruction PCs | Parent |
|---:|---|---|---|
| 0 root | [0,11) | 0,9 | null |
| 1 closure | [11,23) | 11,14 | 0 (creation at 0) |
| 2 closure | [23,28) | 23,26 | 1 (creation at 14) |

IDs follow serialized entry order, while parent IDs follow creation-site ownership. A JUMP at
11 to 23 would pass C's boundary check, then fail D with cross-function-target. MAKE_CLOSURE
at 14 to 23 is the permitted functionEntry relation and does not itself transfer execution:
[E](build-cfg.md) treats that creation instruction as ordinary local progress. The example
omits complete operand spans/values and therefore is not a runnable stream or admitted source.

## 3. Implementation

### Components and owned inputs

| Component | Consumes -> produces | Required contract |
|---|---|---|
| Frame index | C -> distinct-entry descriptors and label rows | Preserve descriptor data; C owns equality for repeated entries. |
| Interval builder | B boundaries/wordCount + root/child entries -> functions/PC owners | Root first; ascending IDs; half-open intervals. |
| Closure linker | MAKE_CLOSURE semantic destination/entry -> sites and parent sets | Child differs from owner; ordinary parent set has size one. |
| Label projector | C label rows + owners -> normalized labels | Cross-owner only for MAKE_CLOSURE functionEntry. |
| Publisher | Complete partition -> frozen D | No predecessor mutation; no partial ownership on decline. |

The signature accepts container, wordcode and references for API compatibility. The current
builder obtains its root/frame facts from C and instructions/wordCount from B; it does not
reread A or require caller schema/count/descriptor equality checks. [The owned-record boundary](standalone-diagnosis.md#owned-record-boundary)
establishes their correspondence.

### Exact interval and closure decisions

C keeps descriptors at every creation site. D deduplicates them by startPc using a Map; repeated
starts keep the last descriptor in the original insertion position. C already proved identical
signatures, so this is selection, not a second conflict check. Add a root entry with kind=root
and descriptor=null; add distinct closure entries; sort by numeric startPc. Require first start
equals mainStartPc, and decline invalid-function-boundary on duplicate starts (including a
closure entry equal to root).

Explanatory pseudocode:

```text
entries = sorted(root entry + distinct closure entries)
for i,entry:
  end = entries[i+1].startPc or wordCount
  pcs = B.instructions with entry.startPc <= pc < end, in B order
  fn = {id:i, kind, startPc, endPc:end, metadata, parent:null, pcs, sites:[]}
  owner[each pc in pcs] = i
for MAKE_CLOSURE:
  parent = owner[creationPc]; child = functionAtEntry[startPc]
  if child.id == parent: decline invalid-function-boundary
  append site to parent; add parent to child's parent set
for closure child:
  require at least one parent
  require one parent unless this entry is explicitly allowed by preliminary options
  parentFunctionId = minimum parent ID
for C label:
  join source/target owner
  functionEntry must be MAKE_CLOSURE and enter another owner
  every other role must stay in source owner
publish once
```

Root metadata is paramCount=0, captureCount=0, hasRest=false and C's mainRegCount. Child
metadata copies its descriptor's paramCount/regCount/captureCount/hasRest. Instructions at an
entry belong to that function, not the preceding one. End PCs are exclusive word indexes;
wordCount is a legitimate interval end, not a branch target. D does not require every
instruction to be reachable or verify that the preceding function ends in RETURN.

A closure-site row contains creationPc, parentFunctionId, childFunctionId, childStartPc and
destinationRegister. Append sites in B order. Multiple creation sites in one parent are allowed;
multiple parents ordinarily decline invalid-function-boundary. Function-entry labels do not
become ordinary cross-function CFG edges.

### Preliminary shared-helper exception

The diagnostic API accepts an internal option `allowSharedParentStarts:Set<wordPC>`. For only
those child entries, a parent set of size >1 is allowed and parentFunctionId is its minimum.
The ordinary `partitionFunctions` wrapper supplies no options. This is preparation for removing
proved shared decoding helpers; it is not qualified ambiguous user-function ownership.

[Diagnosis](standalone-diagnosis.md#canonical-frontend-retries) builds the preliminary set only
during string recovery: descriptors with paramCount=4, captureCount=0 repeated at one entry
are candidates; more than one such repeated entry stops preparation. Dispatcher/CFF normalization
and the string inverse must eliminate/rebuild that helper representation before normal semantic
analysis. The producer owns remapping this option's word PCs after a rewrite. Consumers must not
treat the minimum chosen parent as proof that all original captures belong to it.

### Output, refusal and cleanup

D contains schemaVersion/encoding/wordCount/instructionCount, sorted entryPcs, function records,
ownership rows, normalized label rows, and frame metadata. Each function contains the fields
above plus instructionPcs/count, copied descriptor (or null) and closureSites. Ownership is a
B-order array of {pc,functionId}. Label rows preserve C's pc/name/operand/role/target and add
sourceFunctionId/targetFunctionId. Frame preserves frameStart/headerSize/slots and root
{functionId,startPc,regCount}; C's absolute root register window is not duplicated here.

`diagnoseFunctionPartition` returns a frozen {ok,result,diagnostic}; `partitionFunctions`
returns D or null. Typed failures are invalid-function-boundary or cross-function-target;
unexpected failures become function-partition-error. One complete partition is atomic. D creates
private arrays/maps, copies the successful projection, and removes no source helpers/declarations.
A/B/C remain unchanged. Partial normalizer preparation can yield a new D for an intermediate
stream, but final emission still needs ordinary normalized ownership and the later proofs.

### Testing and acceptance

| Scenario | Observable result / oracle | Acceptance criterion | Retained fixture/control |
|---|---|---|---|
| D1: intervals/parents | Sorted entry intervals and exact owner/site rows. | Every B PC has its constructed owner; frozen D, unchanged predecessors. | Partition test: reference, nested closures, finally fixtures. |
| D2: ordinary cross-function label | D first cross-function-target, public functions-declined. | A/B/C succeed; no partial D/public output. | Owned-chain direct branch across functions. |
| D3: shared helper preparation | Internal repeated helper accepted with option, then removed/remapped. | Final ordinary D plus later semantics succeed; no ambiguous user-function support inferred. | String/dispatcher/CFF producer tests/dependencies; no standalone D minimum-parent control. |
| D4: self-entry/ambiguous parent/root collision | Named invalid-function-boundary reached after successful C. | Atomic result:null; no accidental earlier grammar refusal. | Dedicated normal-entry controls missing. |

Inspect ownership and closure-site records as recovery assertions; behavior alone cannot prove
partitioning. The historical corpus [provenance contract](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/qualification-provenance.md)
bounds generated-output claims. No cold reconstruction or novice study is claimed.

## 4. Input Shapes

D consumes B instructions and C descriptors/labels. E relies on these intervals for actual-owner
register checks, local control flow and handler records; F/G use parent/sites for call/capture
analysis. No downstream consumer infers boundaries by searching for probable opcode values.

| Earlier decoder output / origin | Producer-owned inventory | D handoff |
|---|---|---|
| Expanded/decrypted/compacted code, ours | [B producer map](read-wordcode.md#4-input-shapes) | New entries/PCs need new B/C and interval assignment; reuse returned D. |
| Preliminary shared helper/control stream, ours | [Dispatcher](normalize-dispatcher-wordcode.md#3-implementation), [CFF](normalize-cff-wordcode.md#3-implementation) | Explicit temporary allowed entries; rebuilt option PCs after relocation. |
| Helper/capture removal, ours | [String inverse](normalize-string-concealing.md#address-remapping-atomicity-and-derived-state) | Final rebuilt ordinary D replaces temporary ownership. |

[Caller replacement](standalone-diagnosis.md#owned-record-boundary) never keeps old D after
changing B/C. Successful owned D is not schema/count/ownership-revalidated at E; E owns new
control decisions.

## 5. Known Gaps

- Intervals and creation-site parents do not establish instruction reachability, dynamic targets
  or capture lifetime. E/F/G own those subsequent facts.
- Shared-parent tolerance is internal helper-removal preparation, not an ordinary ownership
  feature. Dedicated D3/D4 normal-entry controls remain missing.
- No terminal opcode requirement at each interval is imposed here. A cross-function fallthrough
  is not inferred by D; E restricts local continuation using the exclusive interval end.

## Source

The frame index is
[partition-functions-input.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/partition-functions-input.js);
the public stage and interval builder are
[partition-functions.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/partition-functions.js).
The standalone wiring for ordinary/preliminary ownership in items 3-4 is
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
| [partition-functions.test.js](../../../../decoder/decode-js/test/vm/jsconfuser-vm/partition-functions.test.js) | D1: exact interval/parent/site/label projection, corpus success and frozen unchanged predecessors. D2 refusal is covered by the source control below. |
| [owned-chain-source.test.js](../../../../decoder/decode-js/test/vm/jsconfuser-vm/owned-chain-source.test.js) | D2: direct branch across functions reaches D cross-function-target first and public functions-declined. |
