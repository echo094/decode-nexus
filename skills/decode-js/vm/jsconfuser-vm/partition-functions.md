# Partition serialized functions

Pipeline stage: `read-program` ([map](../../pipelines/jsconfuser-vm.md)).

## 1. Target

Give every parsed instruction one serialized function owner, then relate closure creation sites and
direct labels to those owners. Success returns deeply frozen `jsconfuser-vm-functions.v1`
(`partition-functions`); refusal returns no partial partition. This establishes intervals and
lexical creation relationships, not call reachability or a control-flow graph.

Readers need functions, lexical captures and half-open intervals, plus
[`read-wordcode`'s wordcode](read-wordcode.md),
[`validate-references`'s descriptors/labels](validate-references.md) and the encoder's
[serialized function interfaces](../../../js-confuser-vm/container-wordcode.md). Source
scope/binding identity belongs to [`extract-container`](extract-container.md) and
[Babel](../../babel.md). VM function ownership here is a word-PC interval, not a Babel source
function path.

## 2. Algorithm

The encoder concatenates function bodies into one stream and closure descriptors identify their
entry PCs. Use the root entry and each distinct child entry to cut that stream into intervals.
Sorting entries fixes stable IDs and bounds: a function owns every instruction starting at or after
its entry and before the next entry (or wordCount for the last function). `read-wordcode` and
`validate-references` already proved that entries are instruction starts, so intervals cover
instructions without guessed opcode scans or redundant coverage validation.

For each MAKE_CLOSURE, join its creation PC to the parent owner and its entry PC to the child.
Self-entry creation cannot define a child. Ordinary partitioning needs one unique parent per child,
although multiple sites in the same parent may create it; a caller can instead admit a child with
several parents as a published suspect (below). Then join `validate-references`'s direct label rows
to owners: functionEntry labels create a cross-owner relation, while branches/exits/handlers/
finally/throwPad targets must stay within their source owner.

### Worked example: serialization and lexical parent differ

This **synthetic ownership projection** has instruction starts [0,9,11,14,23,26],
wordCount=28, root entry 0, and distinct child entries 11 and 23. A root MAKE_CLOSURE at 0
targets 11; another at 14 targets 23. `validate-references` has already validated both descriptors.

| Function ID | Interval | Instruction PCs | Parent |
|---:|---|---|---|
| 0 root | [0,11) | 0,9 | null |
| 1 closure | [11,23) | 11,14 | 0 (creation at 0) |
| 2 closure | [23,28) | 23,26 | 1 (creation at 14) |

IDs follow serialized entry order, while parent IDs follow creation-site ownership. A JUMP at 11 to
23 would pass `validate-references`'s boundary check, then fail `partition-functions` with
cross-function-target. MAKE_CLOSURE at 14 to 23 is the permitted functionEntry relation and does not
itself transfer execution: the backend's [control solver](../switch/vm-switch-control.md) treats that
creation instruction as ordinary local progress. The example omits complete operand spans/values and therefore is not a runnable
stream or admitted source.

## 3. Implementation

### Components and owned inputs

| Component | Consumes -> produces | Required contract |
|---|---|---|
| Frame index | `validate-references` -> distinct-entry descriptors and label rows | Preserve descriptor data; `validate-references` owns equality for repeated entries. |
| Interval builder | `read-wordcode` boundaries/wordCount + root/child entries -> functions/PC owners | Root first; ascending IDs; half-open intervals. |
| Closure linker | MAKE_CLOSURE semantic destination/entry -> sites and parent sets | Child differs from owner; ordinary parent set has size one. |
| Label projector | `validate-references` label rows + owners -> normalized labels | Cross-owner only for MAKE_CLOSURE functionEntry. |
| Publisher | Complete partition -> frozen `partition-functions` | No predecessor mutation; no partial ownership on decline. |

The signature accepts container, wordcode and references for API compatibility. The current builder
obtains its root/frame facts from `validate-references` and instructions/wordCount from
`read-wordcode`; it does not reread A or require caller schema/count/descriptor equality checks.
[The owned-record boundary](standalone-diagnosis.md#owned-record-boundary) establishes their
correspondence.

### Exact interval and closure decisions

`validate-references` keeps descriptors at every creation site. `partition-functions` deduplicates
them by startPc using a Map; repeated starts keep the last descriptor in the original insertion
position. `validate-references` already proved identical signatures, so this is selection, not a
second conflict check. Add a root entry with kind=root and descriptor=null; add distinct closure
entries; sort by numeric startPc. Require first start equals mainStartPc, and decline
invalid-function-boundary on duplicate starts (including a closure entry equal to root).

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
  if several parents:
    decline unless the caller admits this entry as a suspect
    append entry to sharedParentStarts
  parentFunctionId = minimum parent ID
for C label:
  join source/target owner
  functionEntry must be MAKE_CLOSURE and enter another owner
  every other role must stay in source owner
publish once
```

Root metadata is paramCount=0, captureCount=0, hasRest=false and `validate-references`'s
mainRegCount. Child metadata copies its descriptor's paramCount/regCount/captureCount/hasRest.
Instructions at an entry belong to that function, not the preceding one. End PCs are exclusive word
indexes; wordCount is a legitimate interval end, not a branch target. `partition-functions` does not
require every instruction to be reachable or verify that the preceding function ends in RETURN.

A closure-site row contains creationPc, parentFunctionId, childFunctionId, childStartPc and
destinationRegister. Append sites in `read-wordcode` order. Multiple creation sites in one parent
are allowed; multiple parents decline invalid-function-boundary unless admitted as suspects.
Function-entry labels do not become ordinary cross-function control edges.

### Shared-parent suspects

The encoder's string concealment creates one decode closure in every function that uses strings
([shared bank](../../../js-confuser-vm/transforms/shared-string-bank.md)), so that helper entry has
several parents. `partition-functions` cannot tell such a helper from an ambiguous user function;
only the [string inverse](normalize-string-concealing.md), which proves the helper by its trace, can
decide it, and it runs after the dispatcher and CFF inverses that must re-partition first (P1).
`partition-functions` therefore publishes a multi-parent entry as a suspect instead of declining,
and every decoder in between carries it unchanged (P3).

The diagnostic API accepts `sharedParentSuspects`: `true` admits every multi-parent entry; a
`Set<wordPC>` admits only those entries. An admitted entry takes the minimum parent ID and is listed
in the published `sharedParentStarts` (ascending). Every `partition-functions` carries that field,
empty when nothing was admitted. The ordinary `partitionFunctions` wrapper admits none.

| Caller | Option | Why |
|---|---|---|
| [Diagnosis](standalone-diagnosis.md#canonical-frontend-retries) before the string attempt; anti and specialized routes' internal `partition-functions` | `true` | First partition of a stream that may still hold the shared helper |
| [Dispatcher](normalize-dispatcher-wordcode.md) and [CFF](normalize-cff-wordcode.md) rebuilds | the incoming `partition-functions`'s `sharedParentStarts`, remapped through each word-PC change | A rewrite carries the suspects; it cannot create new ones |
| String inverse's reachability partition | `true` | Reads the stream before its own removal |
| String inverse's rebuilt `partition-functions`, every later component | none | Ordinary: a suspect left after the string attempt declines |

Consumers must not treat the minimum parent as proof that all original captures belong to it.
Diagnosis refuses functions-declined when its current `partition-functions` still publishes a
suspect after the string attempt.

### Output, refusal and cleanup

`partition-functions` contains schemaVersion/encoding/wordCount/instructionCount, sorted entryPcs,
sharedParentStarts, function records, ownership rows, normalized label rows, and frame metadata.
Each function contains the fields above plus instructionPcs/count, copied descriptor (or null) and
closureSites. Ownership is a `read-wordcode`-order array of {pc,functionId}. Label rows preserve
`validate-references`'s pc/name/operand/role/target and add sourceFunctionId/targetFunctionId. Frame
preserves frameStart/headerSize/slots and root {functionId,startPc,regCount};
`validate-references`'s absolute root register window is not duplicated here.

`diagnoseFunctionPartition` returns a frozen {ok,result,diagnostic}; `partitionFunctions` returns
`partition-functions` or null. Typed failures are invalid-function-boundary or
cross-function-target; unexpected failures become function-partition-error. One complete partition
is atomic. `partition-functions` creates private arrays/maps, copies the successful projection, and
removes no source helpers/declarations. `extract-container`, `read-wordcode` and
`validate-references` remain unchanged. Partial normalizer preparation can yield a new
`partition-functions` for an intermediate stream, but final emission still needs ordinary normalized
ownership and the later proofs.

### Testing and acceptance

| Scenario | Observable result / oracle | Acceptance criterion | Retained fixture/control |
|---|---|---|---|
| S1: intervals/parents | Sorted entry intervals and exact owner/site rows. | Every `read-wordcode` PC has its constructed owner; frozen `partition-functions`, unchanged predecessors. | Partition test: reference, nested closures, finally fixtures. |
| S2: ordinary cross-function label | `partition-functions` first cross-function-target, public functions-declined. | `extract-container`, `read-wordcode` and `validate-references` succeed; no partial `partition-functions` or public output. | Owned-chain direct branch across functions. |
| S3: shared-parent suspects | A multi-parent helper entry published, remapped by dispatcher/CFF, removed by the string inverse. | Final ordinary `partition-functions` plus later semantics succeed; no ambiguous user-function support inferred. | String/dispatcher/CFF producer tests; no standalone `partition-functions` suspect control. |
| S4: self-entry/ambiguous parent/root collision | Named invalid-function-boundary reached after successful `validate-references`. | Atomic result:null; no accidental earlier grammar refusal. | Dedicated normal-entry controls missing. |

Inspect ownership and closure-site records as recovery assertions; behavior alone cannot prove
partitioning. No cold reconstruction or novice study is claimed.

## 4. Input Shapes

`partition-functions` consumes `read-wordcode` instructions and `validate-references`
descriptors/labels. The numeric projection reads its frames and ordered PCs: each function's
cases, which the backend's control solver walks. No downstream consumer infers boundaries by searching for probable opcode
values.

| Earlier decoder output / origin | Producer-owned inventory | `partition-functions` handoff |
|---|---|---|
| Expanded/decrypted/compacted code, ours | [`read-wordcode` producer map](read-wordcode.md#4-input-shapes) | New entries/PCs need new `read-wordcode` and `validate-references` and interval assignment; reuse returned `partition-functions`. |
| Shared-helper control stream, ours | [Dispatcher](normalize-dispatcher-wordcode.md#3-implementation), [CFF](normalize-cff-wordcode.md#3-implementation) | Incoming suspects remapped after relocation and admitted as a Set. |
| Helper/capture removal, ours | [String inverse](normalize-string-concealing.md#address-remapping-atomicity-and-derived-state) | Final rebuilt ordinary `partition-functions` replaces temporary ownership. |

[Caller replacement](standalone-diagnosis.md#owned-record-boundary) never keeps old
`partition-functions` after changing `read-wordcode` and `validate-references`. Successful owned
`partition-functions` is not schema/count/ownership-revalidated downstream; the backend's control
solver owns control decisions.

## 5. Known Gaps

- Intervals and creation-site parents do not establish instruction reachability, dynamic targets or
  capture lifetime. The backend's control solver owns reachability and targets.
- Shared-parent suspects serve the string helper's removal, not ordinary ownership. Dedicated
  S3/D4 normal-entry controls remain missing.
- No terminal opcode requirement at each interval is imposed here. A cross-function fallthrough is
  not inferred by `partition-functions`; the control solver reads one function's cases and never
  continues past the last.

## Source

The frame index (`indexFrame`: deduplicated frame descriptors keyed by start PC, and the label
references), the schema name (`FUNCTION_SCHEMA`), the typed refusal (`PartitionDecline`, `decline`)
and the record freeze (`deepFreeze`) are
[partition-functions-input.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/partition-functions-input.js);
the public entry and interval builder are
[partition-functions.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/partition-functions.js).
The standalone wiring for suspect and ordinary ownership in items 3-4 is
[diagnose-standalone.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/diagnose-standalone.js).
The pinned entry-PC and closure descriptor sources are
[resolveLabels.ts](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/transforms/bytecode/resolveLabels.ts#L21-L107)
and
[compiler.ts](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/compiler.ts#L617-L735).

## Fixtures

Each suite encodes its sources with the pinned encoder and requires the decode to behave as the
source ([tests.md](../../tests.md#suites)); a Proved line names the code whose break turns the case
red.

| Suite and cases | Claims | Proved |
|---|---|---|
| [compiled-forms](../../../../decoder/decode-js/test/vm/jsconfuser-vm/generated-cells/compiled-forms/suite.js), `fn-closure` (f-closures-state), `control-try` (f-finally-abrupt) | S1: closure entries, parent creation sites, function intervals and function-local handler labels | A closure creation site enters a child function |
| [partition-functions.test.js](../../../../decoder/decode-js/test/vm/jsconfuser-vm/single-component/partition-functions.test.js) (unit) | Inputs read without change into a deeply frozen partition | Not a suite |

S2 (a direct branch across functions) has no committed test: the old control edited input by
hand.
