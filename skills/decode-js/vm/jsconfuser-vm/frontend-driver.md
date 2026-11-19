# jsconfuser-vm frontend driver

Pipeline stage: the frontend driver; it runs `admit-container` through `build-model`
([map](../../pipelines/jsconfuser-vm.md#frontend-order)).

The map gives the order the driver calls the stages in, as pseudocode, a chart and a table. This
doc owns what the map does not: how the record-building stages are composed, the exact trigger
and refusal rule of each stage, how a stage's result is adopted, how suspects are settled, the
gate, and the numeric model.

## 1. Target

Given the prepared source, return the **numeric model**: the compiled program as canonical
instructions grouped by function, with the constant pool, every encoder option undone. Given
anything a stage refuses where the decode cannot go on, return one refusal under a code of the
driver's own.

The driver decides only order and policy. It recognizes no shape itself beyond each stage's
trigger, rewrites no word, and never executes the input. Its records are private to one call;
nothing it adopts is published unless the whole frontend succeeds.

## 2. Algorithm

The driver is a class, `Frontend`, holding the current records, and one function that calls its
methods in the [map's order](../../pipelines/jsconfuser-vm.md#frontend-order).

### State

```text
source                     the prepared source; every runtime observer reads it, unchanged
container, wordcode        the current payload and its instructions; wordcode is null while unread
references, functions      null until built from the current words
records                    the last adopted stage result, kept for its recovered labels
originPcMap                origin PC -> current PC; null while no stage has moved code
originContinuationLoads    PATCH removal's continuation loads, by origin PC, for the routes
suspects, suspectRuns      PATCH fillers not yet decided (origin PCs), and their runs
recoveredLabels            labels later stages recovered, collected for the settle
```

The rule the state keeps: `references` and `functions` always describe the current `wordcode`.
Every adoption replaces all four records together, with `null` for one the stage did not rebuild,
and `read-program` then builds what is missing. Old references are never kept beside new words.

### Building the records

Three stages have no transform; the driver calls the modules.

**`admit-container`** is `extractContainer`, the one composition of the `source` and `handlers`
modules:

```text
diagnoseContainer(input):                       // explanatory pseudocode
  ast     = input parsed with the container's parser options, or a Babel File/Program as given
  located = locateBootPayload(ast)              the payload by the boot skeleton, canonical table
  view    = locateHandlers(ast)                 a refusal of the locator's own: no runtime found
  if no view: return located
  { opcodes, sentinel } = behaviourTable(view)  every opcode named by its handler's behaviour
  return locateBootPayload(ast, { opcodes, sentinels: { CALL_SPREAD: sentinel or the canonical } })
```

The payload is located first with the canonical table, so input that is no container refuses
before the handlers are searched. When the interpreter's handlers are found, the container is
read again with the opcode table their behaviour gives
([`identify-handlers`](handlers/identify-handlers.md)), which is how randomized opcode values
are read; when they are not found, the first container stands. The table is built whatever the
words hold: an added opcode the table does not name is left for `read-wordcode` to refuse, which
is the trigger of the recoveries below. The [`container`](source/container.md) doc owns the
record and its refusal codes.

**`read-program`, first part** is `readWordcode(container)` in the constructor. A refusal is not
the decode's: the words stay unread (`wordcode` null) and the refusal's code selects the recovery.

**`read-program`, the rest** (`readProgram`) builds whichever of `references` and `functions` is
null: `validateReferences`, then `diagnoseFunctionPartition` with `sharedParentSuspects: true`,
so a closure entry with several parents (a shared string helper) is published as a
[suspect](wordcode/partition-functions.md#shared-parent-suspects) and not refused.

### Triggers and refusal policy

"Unread code" is the code `diagnoseWordcode(container)` gives while `wordcode` is null.

| Method | Runs when | On the stage's refusal |
|---|---|---|
| `recoverPatch` | the unread code is `unknown-opcode` or `unsupported-hardening-opcode` | carries on, nothing adopted |
| `recoverAddedOpcodes` | the unread code is `unknown-opcode` | the next route; after the last, carries on |
| `recoverConstants` | always first requires the words to be read, else `wordcode-declined`; then runs when `hasConcealedConstant(wordcode)` | `concealed-constants-declined` |
| `readProgram` | a record is null | `references-declined`, `functions-declined` |
| `recoverDispatcher` | some instruction is `JUMP_REG` | carries on with the indirect jumps |
| `recoverCff` | always | `cff-absent`: carries on; `refusedBy` naming a record builder: that builder's code; otherwise `cff-declined` |
| `recoverStrings` | the first three instructions are `MAKE_CLOSURE` with one parameter, `LOAD_CONST`, `CALL` | `string-concealing-declined` |
| `model` | always | the gate, below |

Why the policies differ:

- **PATCH and added opcodes are tried, not required.** The trigger is a refusal code, not proof
  of the option. If no recovery reads the words, the decode stops at the next step with
  `wordcode-declined`.
- **A dispatcher refusal is not the decode's.** An indirect jump may be the compiler's own (a
  finalizer's), which the backend's [control solve](../switch/vm-switch-control.md) reads; a
  jump nothing resolves is refused there.
- **A CFF refusal is the decode's.** A state loop CFF has read and cannot invert would otherwise
  reach the backend as ordinary code. When CFF's rewritten words are refused by a record builder,
  the public code names that builder, since that is the shape that refused.
- **Strings come last** because the encoder conceals strings first: the string inverse reads the
  program its own encoder step saw
  ([P3](../../../decoding-method/with-encoder.md#p3)).
- **Each recovery runs once.** Nothing loops back.

What each recovery is handed: the routes get `(source, container, options)`, where `options` is
empty until a stage has moved code and then holds `originPcMap`, `originContinuationLoads` and
`suspects`; the dispatcher gets the origin map as `decodedTargetMap`, and `suspects`; constants
get the source; CFF and strings get the current records only.

### Adoption

A stage result holds `container` and `wordcode`, optionally `references` and `functions`, and one
of two address fields ([`origin-addresses`](wordcode/origin-addresses.md)):

| | `adoptRoute` | `adoptRewrite` |
|---|---|---|
| Used for | PATCH removal, the added-opcode routes | constants, dispatcher, CFF, strings, the settle |
| Address field | `originPcMap`, origin PC to the result's PC, already composed by the stage; absent when the stage kept PCs, and the driver's map then stands | `pcMap`, the stage's input PC to output PC; the driver composes it onto its origin map (`composePcMaps`); absent when PCs are unchanged |
| Suspects | `suspects` replaces the driver's when present | untouched |

PATCH removal also publishes `originContinuationLoads` and `suspectRuns`, which the driver keeps.

### Settling suspects

A PATCH filler that cannot be decided while a dispatcher hides labels stays in the stream as a
suspect ([P5](../../../decoding-method/with-encoder.md#p5);
the rule is [normalize-self-modifying-wordcode's](normalize-self-modifying-wordcode.md#settling-suspects)).
The driver's part is when to ask again:

```text
settle():                                          // explanatory pseudocode
  recoveredLabels += records.skipLabels            what the stage just adopted recovered
  if no suspects: return false
  settled = diagnoseSettleSelfModifyingSuspects(container, wordcode,
              { suspects, suspectRuns, originPcMap, recoveredLabels })   a refusal is the decode's
  if nothing settled: return false
  adoptRewrite(settled); suspects, suspectRuns = settled's
  return true
```

It runs after the two adoptions that can recover hidden labels: an added-opcode route (the anti
route runs the dispatcher inverse itself) and the dispatcher. After the dispatcher, a settle that
changed the words is followed by `readProgram`, since the references and functions were dropped
with the old words. The suspects of the other kind, shared-parent closure entries, need no call:
the dispatcher and CFF remap them and the string inverse removes the helper.

### The gate

`model` refuses in two cases and otherwise builds the model:

1. `functions.sharedParentStarts` is not empty: a closure with several parents is left, which no
   function can own. `functions-declined`.
2. An instruction's name is not in `SUPPORTED_INSTRUCTIONS`, the names the
   [lowering](lower-switch-model.md) has a row for. `unsupported-opcode`.

### Worked example

The committed cell `loop-sum` of suite `self-modifying-dispatcher-anti` (profile
`selfModifying+dispatcher+stringConcealing+antiInstrumentation`, seed 2), traced through the
driver's methods:

| Step | What happened | State after |
|---|---|---|
| constructor | container admitted; `read-wordcode` refuses, `unsupported-hardening-opcode` | words unread |
| `recoverPatch` | PATCH removal adopted as a route. It returns no wordcode: anti's opcodes remain | unread code `unknown-opcode`; origin map of 288 PCs; 5 suspects in 4 runs |
| `recoverAddedOpcodes` | the first five routes refuse; the anti route recovers the stream and, having run the dispatcher inverse, returns references and functions and three recovered labels. `settle` then decides all 5 suspects | 107 instructions in 402 words; origin map of 125 PCs; no suspects; references and functions null again |
| `recoverConstants` | no nonzero key | unchanged |
| `readProgram` | both records built | 4 functions, no shared-parent suspect |
| `recoverDispatcher` | no `JUMP_REG` left | unchanged |
| `recoverCff` | `cff-absent` | unchanged |
| `recoverStrings` | the helper prefix is there; the inverse returns all four records | 27 instructions in 93 words; 2 functions; origin map of 40 PCs |
| `model` | gate passes | functions of 10 and 17 instructions |

The suite's proof deletes the adoption and settle of `recoverAddedOpcodes`, which turns the cell
red.

## 3. Implementation

### Exports another file imports

| Export | File | Contract | Imported by |
|---|---|---|---|
| `diagnoseStandaloneInput(source)` | `diagnose-standalone.js` | `{ ok, result, diagnostic }`, not frozen: the numeric model, or a `standalone` refusal. An exception that is no `standalone` refusal passes to the caller. | [`standalone-decode`](standalone-decode.md); `scripts/render-vm-switch.mjs`, the cell oracle script, `numeric-to-vm-switch.test.js` |
| `diagnoseContainer(input)` | `extract-container.js` | `{ ok, result, diagnostic }`, deeply frozen: the container record or a `container` refusal; fallback code `extractor-error`. `input` is source text or a Babel `File` or `Program`; anything else is `invalid-input`. | the cell oracle script, the cell tests' support files |
| `extractContainer(input)` | `extract-container.js` | The record, or `null`. | the driver; the `wordcode` module's unit tests and `extract-container.test.js` |
| `decline`, `requireValue`, `unwrap`, `accepted`, `refused` | `standalone-contract.js` | The `standalone` owner's helpers ([Refusals](../../pipelines/jsconfuser-vm.md#refusals)). | the driver, `standalone-decode` |

### The numeric model

```text
constants                 the pool's values (references.constants.values)
functions                 the functions record
instructionsByFunction    Map: function id -> its instructions, in the record's instructionPcs order
wordcode                  the wordcode record
```

The instructions are the wordcode record's own objects, not copies. The
[lowering](lower-switch-model.md) is the only reader.

### Refusals

Owner `standalone`. These are the frontend's public codes
([the public diagnostic](standalone-decode.md#the-public-diagnostic)); a stage's detailed code
stays in that stage's own record and is not copied.

| Code | When |
|---|---|
| `invalid-input` | The source is not a string |
| `container-declined` | `extractContainer` returned no record |
| `wordcode-declined` | The words are still unread after the PATCH and added-opcode recoveries; or CFF's rewritten words were refused by `read-wordcode` |
| `references-declined` | `validateReferences` returned no record, in `readProgram` or on CFF's words |
| `functions-declined` | The partition returned no record, in `readProgram` or on CFF's words; or a shared-parent suspect reached the gate |
| `concealed-constants-declined` | The constant inverse refused |
| `cff-declined` | CFF read a state loop it cannot invert |
| `string-concealing-declined` | The string inverse refused |
| `unsupported-opcode` | The gate found an instruction with no lowering |
| the settle's own code | `diagnoseSettleSelfModifyingSuspects` refused: its code and message are kept (`unwrap`) |

## 4. Input Shapes

| Shape | Producer | Treatment |
|---|---|---|
| The prepared source | the [entry](../../plugins/jsconfuser-vm.md) | parsed by the container extraction; handed unchanged to every runtime observer |
| The container, wordcode, references and functions records | the [`source`](source.md), [`handlers`](handlers.md) and [`wordcode`](wordcode.md) modules | held as the current records |
| A stage result | each `normalize-*` transform | adopted whole (Adoption) |
| A stage's refusal record | the same | read for `ok` only, except the wordcode's code (the trigger) and CFF's `code` and `refusedBy` |

## 5. Known Gaps

- A PATCH or added-opcode recovery's refusal is dropped: the public code is `wordcode-declined`
  whichever recovery refused and why. The reason is in the recovery's own record, which the
  driver does not keep.
- The gate's opcode check has no input that reaches it. `SUPPORTED_INSTRUCTIONS` is every
  canonical name but `PATCH`, and `read-wordcode` refuses `PATCH`, so a read stream holds no other
  name.
- The triggers are shape tests on the current words, not proofs of an option: a compiled program
  that itself opens with a one-parameter closure called on a constant opens the string inverse,
  and its refusal is then the decode's.
- A settle refusal publishes the settle's detailed code, unlike every other stage.
- No committed test asserts a public refusal code other than `container-declined`.

## 6. Source

- [diagnose-standalone.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/diagnose-standalone.js):
  `Frontend`, the stage order (`reconstruct`), the gate, the model.
- [extract-container.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/extract-container.js):
  the container extraction.
- [standalone-contract.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/standalone-contract.js):
  the `standalone` owner's helpers.

## 7. Fixtures

Every cell of every suite passes through the driver ([tests.md](../../tests.md#suites)); one suite
has a proof that breaks it.

| Scenario | Expected result | Committed fixture |
|---|---|---|
| Anti decoys inside self-modifying code behind a dispatcher: suspects left by PATCH removal, labels recovered by the anti route | The suspects settle after the route is adopted and the decode behaves as the source. Deleting the adoption and settle in `recoverAddedOpcodes` turns the suite red | [self-modifying-dispatcher-anti](../../../../decoder/decode-js/test/vm/jsconfuser-vm/cell-suites/self-modifying-dispatcher-anti/suite.js) |
| A container extracted from encoder output and from input that is none | The record, deeply frozen; `null` for ordinary JavaScript | [extract-container.test.js](../../../../decoder/decode-js/test/vm/jsconfuser-vm/single-component/extract-container.test.js) |
| Ordinary JavaScript through the public entry | `container-declined` | [plugin.test.js](../../../../decoder/decode-js/test/vm/jsconfuser-vm/public-entry-points/plugin.test.js) |
| Words no recovery reads | `wordcode-declined` | |
| A state loop CFF reads and cannot invert; CFF's words refused by a record builder | `cff-declined`; that builder's code | |
| A shared-parent suspect left at the gate | `functions-declined` | |
| A settle that refuses | the settle's code | |
