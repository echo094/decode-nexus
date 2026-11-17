# Partition the stream into functions

Part of the [`wordcode` module](../wordcode.md). The stage `read-program` calls it through the
[frontend driver](../frontend-driver.md), and every transform that rebuilds the stream calls it
again on its output ([map](../../../pipelines/jsconfuser-vm.md#frontend-order)).

## 2. Algorithm

The encoder concatenates the function bodies into one stream, and each closure descriptor names
its function's entry PC. The partition cuts the stream at the root entry and every distinct
closure entry, gives each instruction the function whose interval holds it, and relates creation
sites and direct labels to those owners. An interval is a range of word PCs, not a set of
reachable instructions: no control flow is read.

```text
partition(wordcode, references, options):            // explanatory pseudocode
  entries = [root at mainStartPc] + one per distinct descriptor startPc, sorted by startPc
  require the first entry is the root, and no two entries share a PC
                                                     else invalid-function-boundary
  for entry i:
    function i owns [entry.startPc, next entry's startPc or wordCount)
    and every instruction whose PC lies in it
  for each MAKE_CLOSURE at pc:
    parent = owner of pc; child = function entered at its entry PC
    require child != parent                          else invalid-function-boundary
    parent.closureSites += the site; parents[child] += parent
  for each closure function:
    one parent:      parentFunctionId = it
    several parents: require the caller admitted this entry as a suspect
                                                     else invalid-function-boundary
                     parentFunctionId = the lowest; sharedParentStarts += its entry
  for each direct label reference:
    functionEntry: require it enters another function    else invalid-function-boundary
    any other role: require source and target share an owner  else cross-function-target
  publish the functions record
```

Function ids follow serialized entry order; parents follow creation sites, so a function's
parent is not its predecessor in the stream. Several descriptors of one entry are one function,
taken from the last creation site. Several creation sites in one parent are allowed. A
`functionEntry` label is a relation between owners, never a control edge: creating a closure is
ordinary progress in the parent ([vm-switch-control](../../switch/vm-switch-control.md)).

### Shared-parent suspects

The encoder's string concealing creates one decode closure in every
function that uses strings ([shared string bank](../../../../js-confuser-vm/transforms/shared-string-bank.md)),
so that helper's entry has several parents. The partition cannot tell such a helper from an
ambiguous user function. Only `normalize-string-concealing` can, by the helper's own trace, and
it runs after the dispatcher and CFF transforms, which must re-partition first. So a caller may
admit multi-parent entries as suspects: the partition publishes them in `sharedParentStarts`
instead of refusing, each transform in between carries them, and the driver refuses a partition
that still holds one after the string stage
([Frontend order](../../../pipelines/jsconfuser-vm.md#frontend-order)). The lowest parent is a
placeholder; no consumer may take it as the owner of the helper's captures.

### Worked example

Two **synthetic** streams under canonical opcodes.

The stream of [validate-references](validate-references.md#worked-example), with boundaries
`[0, 9, 11, 14]`, 16 words and one closure entry at 11:

| Function | Interval | Instruction PCs | Parent | Closure sites |
|---:|---|---|---|---|
| 0 root | `[0, 11)` | 0, 9 | none | `{creationPc: 0, childFunctionId: 1, childStartPc: 11, destinationRegister: 1}` |
| 1 closure | `[11, 16)` | 11, 14 | 0 | none |

Replacing the root's `RETURN` at PC 9 by `JUMP 11` (`[39, 11]`) passes the validator, since 11 is
a boundary, and refuses here: `cross-function-target`, "JUMP@9 targets function 1 from 0".

A stream where the root creates closures at entries 16 and 23, and the function at 16 creates the
one at 23 again:

```text
0  MAKE_CLOSURE r1, entry 16      7  MAKE_CLOSURE r1, entry 23      14 RETURN r0
16 MAKE_CLOSURE r0, entry 23      23 RETURN r0
```

Entry 23 has parents 0 and 1. Without an option, or with a suspect set that does not hold 23, it
refuses: "Function entry 23 has ambiguous parents". With `sharedParentSuspects: true` the record
has `sharedParentStarts: [23]` and function 2 takes parent 0.

## 3. Implementation

### Exports another file imports

| Export | Contract | Imported by |
|---|---|---|
| `diagnoseFunctionPartition(container, wordcode, references, options)` | `{ok, result, diagnostic}`, deeply frozen: the functions record or a `partition` refusal ([Refusals](../../../pipelines/jsconfuser-vm.md#refusals)); fallback code `function-partition-error`. `options.sharedParentSuspects` is `true` (admit every multi-parent entry), a `Set` of entry PCs (admit those), or absent (admit none). `container` is not read. | the frontend driver, the `normalize-*` transforms that rebuild the stream, the cell tests |
| `partitionFunctions(container, wordcode, references)` | The record, or `null`; admits no suspect. | the test |
| `functionIndexAt(functions, pc)` | The index of the function whose interval holds `pc`, or -1. | `normalize-cff-wordcode`, `normalize-dispatcher-wordcode` |

What each caller passes as `sharedParentSuspects`:

| Caller | Value |
|---|---|
| The driver's partition before the string stage; the anti and specialized transforms' own partitions | `true` |
| The dispatcher and CFF transforms' rebuilt partitions | The incoming record's `sharedParentStarts`, mapped through the transform's PC changes |
| Everything after the string stage | Absent |

### The functions record

```text
schemaVersion: 'jsconfuser-vm-functions.v1'
encoding:      'numeric-u32'
wordCount, instructionCount
entryPcs                    // ascending; index = function id
sharedParentStarts          // admitted suspect entries; empty when none
functions [
  { id, kind: 'root' | 'closure',
    startPc, endPc,         // half-open; the last endPc is wordCount
    paramCount, regCount, captureCount, hasRest,
    parentFunctionId,       // null for the root
    instructionPcs, instructionCount,
    descriptor,             // the references record's descriptor, or null for the root
    closureSites [{ creationPc, parentFunctionId, childFunctionId, childStartPc,
                    destinationRegister }] } ]
ownership [{ pc, functionId }]          // one row per instruction, in stream order
labels [{ pc, instruction, operand, role, target, sourceFunctionId, targetFunctionId }]
frame { frameStart, headerSize, slots, root { functionId, startPc, regCount } }
```

The root's counts are 0 parameters, 0 captures, no rest and the container's root register count;
a closure's are its descriptor's.

### Refusals

Owner `partition`. A refusal publishes no partial record; no input is changed.

| Code | When |
|---|---|
| `invalid-function-boundary` | The root is not the first entry; a closure entry equals the root's; a `MAKE_CLOSURE` enters its own function; a multi-parent entry that was not admitted |
| `cross-function-target` | A jump, exit, handler, finally or throw-pad label whose target has another owner |
| `function-partition-error` | Any other error |

## 5. Known Gaps

- An interval does not show that its instructions are reachable or that the function before it
  ends in a terminator; the control solver reads one function's instructions and never continues
  past its last.
- Descriptors of one entry that disagree are not detected: the last creation site's is used.
- No committed test reaches a refusal of the partition directly, or a suspect through this entry
  alone; suspects are exercised only through the string, dispatcher and CFF transforms.

## 6. Source

- [partition-functions.js](../../../../../decoder/decode-js/src/vm/jsconfuser-vm/wordcode/partition-functions.js):
  the whole part.
- Entry PCs and closure descriptors in the pinned encoder:
  [resolveLabels.ts#L21-L107](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/transforms/bytecode/resolveLabels.ts#L21-L107),
  [compiler.ts#L617-L735](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/compiler.ts#L617-L735).

## 7. Fixtures

The unit test is
[partition-functions.test.js](../../../../../decoder/decode-js/test/vm/jsconfuser-vm/single-component/partition-functions.test.js).

| Scenario | Expected result | Committed fixture |
|---|---|---|
| Programs with closures | A creation site enters a child function; removing that check turns the suite red | [compiled-forms](../../../../../decoder/decode-js/test/vm/jsconfuser-vm/cell-suites/compiled-forms/suite.js) |
| A hand-written container, wordcode and references | The record is read without changing its inputs and is deeply frozen | partition-functions.test.js |
| A direct jump into another function | `cross-function-target` | |
| A closure entry created from two functions, not admitted | `invalid-function-boundary` | |
