# Addresses across code-moving stages

Part of the [`wordcode` module](../wordcode.md). The `recover-added-opcodes` transforms expand
their streams through it, and every transform that moves code uses its address rules
([map](../../../pipelines/jsconfuser-vm.md#frontend-order)).

## 2. Algorithm

An address is a word PC written into the stream. The encoder resolved every label on one stream,
so every address it wrote is an **origin PC**: valid in that stream, and stale as soon as a stage
inserts or removes words. Three rules keep addresses correct.

**1. Where an address is.** A word holds an address in exactly two cases:

- a label operand: the offsets in `LABEL_WORD_OFFSETS` for the instruction's opcode
  ([read-wordcode](read-wordcode.md#exports-another-file-imports)), the entry PC of
  `MAKE_CLOSURE` included;
- a **continuation load**: the immediate of a `LOAD_INT` whose destination is a continuation
  register of its function. The compiler gives each `try`/`finally` a dedicated register that
  only label loads write and only the finalizer's `JUMP_REG` reads; `FINALLY_SETUP` names it as
  its second operand. So within one function, every `LOAD_INT` into a register some
  `FINALLY_SETUP` of that function names loads an address.

No other immediate is rewritten, whatever its value.

**2. Where each PC went.** A stage that moves code publishes a **PC map** from each input
instruction PC to its output PC, the end of the stream included. A stage that reads an address
written before an earlier move resolves it through the **origin map**, origin PC to current PC,
which is the composition of every map so far:

```text
compose(originMap, pcMap):                       // explanatory pseudocode
  no originMap: pcMap
  else: { origin -> pcMap[input] : (origin -> input) in originMap, input in pcMap }
```

An origin whose instruction a stage removed drops out of the map.

**3. Suspects are read past.** A self-modifying filler that is not yet decided
([normalize-self-modifying-wordcode](../normalize-self-modifying-wordcode.md)) is a suspect. A
filler `LOAD_INT` draws any register, so a suspect neither names a continuation register nor
loads one: it is left out of rule 1 and keeps its words until its owner settles it.

### Expanding added opcodes

`expandObservedWordStream` rewrites a stream read with added-opcode cases
([read-wordcode](read-wordcode.md#added-opcode-instructions)) into canonical words:

```text
expand(stream, originPcMap, suspects):           // explanatory pseudocode
  parts = for each instruction: its steps if MACRO or SPECIALIZED, else itself;
          each part at its new PC, marked `encoded` when it came from a step
  pcMap = instruction PC -> new PC, and wordCount -> the new length
  function starts = 0 and every MAKE_CLOSURE entry
  loads = continuation loads among the parts, per function, suspects read past
  for each part, each address word (label offsets; immediate of a continuation load):
    target = the word
    if encoded: target = originPcMap[target]     else origin-target-boundary
    word = pcMap[target]                         else macro-target-boundary
  return the words, and with includePcMap the pcMap and the parts
```

The words inside a macro or specialized step were baked into the handler by the encoder, so they
still hold origin PCs after an earlier stage moved the stream; every other word was already
rewritten by that stage and holds a current PC. That is why only `encoded` parts go through the
origin map. A part that is neither macro nor specialized is copied under its own name with its
own words: anti's synthetic instructions pass through unchanged for their own transform.

### Worked example

A **synthetic** stream of 6 words, canonical opcodes, with one specialized opcode 77 that the
observer proved to be `LOAD_INT r1, 5`:

| PC | Instruction | Words |
|---:|---|---|
| 0 | `SPECIALIZED`, step `LOAD_INT` `[1, 1, 5]` | `[77]` |
| 1 | `JUMP 4` | `[39, 4]` |
| 3 | `DEBUGGER` | `[57]` |
| 4 | `RETURN r1` | `[45, 1]` |

The expansion is `[1, 1, 5, 39, 6, 57, 45, 1]` with PC map `0->0, 1->3, 3->5, 4->6, 6->8`: the step
takes three words where the opcode took one, and the jump's target 4 becomes 6. If an earlier
stage had published the origin map `0->0, 10->1, 12->3, 13->4`, composing it with this PC map gives
`0->0, 10->3, 12->5, 13->6`.

The committed unit test gives one function whose `FINALLY_SETUP` names continuation register 5,
and three `LOAD_INT` items writing r5, r5 and r6. The two loads into r5 are selected. With the
second marked a suspect, only the first is; with the `FINALLY_SETUP` itself a suspect, none is.

## 3. Implementation

### Exports another file imports

| Export | File | Contract | Imported by |
|---|---|---|---|
| `expandObservedWordStream(stream, {includePcMap = false, originPcMap = null, suspects = []})` | `expand-observed-word-stream.js` | The expanded words, or with `includePcMap` `{words, pcMap, parts}`. `stream` is a stream reader's record; `suspects` are origin PCs when `originPcMap` is given. Throws an `observed-expansion` refusal. | `normalize-aliased-wordcode`, `normalize-macro-wordcode`, `normalize-specialized-wordcode` |
| `composePcMaps(originPcMap, pcMap)` | `expand-observed-word-stream.js` | Rule 2; both are `Map`s. | the frontend driver, the aliased, anti, macro and specialized transforms |
| `declineExpansion`, `unwrapExpansion`, `acceptExpansion`, `refuseExpansion` | `expand-observed-word-stream.js` | The `observed-expansion` refusal's `decline`, `unwrap`, `accepted` and `refused` ([Refusals](../../../pipelines/jsconfuser-vm.md#refusals)). | `normalize-macro-wordcode`, `normalize-specialized-wordcode` |
| `selectContinuationLoads(items, suspects = new Set())` | `finally-continuations.js` | Rule 1's second case and rule 3. `items` are `{pc, key, functionId, name, words}` with `words` starting at the opcode; `suspects` is a set of `pc` values in the caller's own PC space. Returns the set of selected `key`s. | the expansion; `normalize-anti-wordcode`, `normalize-cff-wordcode`, `normalize-dispatcher-wordcode`, `normalize-string-concealing`, `normalize-self-modifying-wordcode`, `analyze-self-modifying-regions` |

A part of the expansion is `{originPc, pc, name, words, encoded}`: the PC of the instruction it
came from, its new PC, its canonical name and words.

### Refusals

Owner `observed-expansion`.

| Code | When |
|---|---|
| `origin-target-boundary` | An address inside a macro or specialized step that the origin map does not hold |
| `macro-target-boundary` | An address that is not an instruction PC of the stream being expanded |
| `macro-expanded-width` | The expanded words do not end where the PC map says |

## 5. Known Gaps

- A function's continuation registers are found from the `FINALLY_SETUP` instructions in its PC
  interval. A `LOAD_INT` into such a register that is not a label load would be rewritten; the
  compiler's dedicated register is what excludes it.
- The expansion takes function starts from `MAKE_CLOSURE` entries in the stream it is given, not
  from the functions record.

## 6. Source

- [expand-observed-word-stream.js](../../../../../decoder/decode-js/src/vm/jsconfuser-vm/wordcode/expand-observed-word-stream.js):
  the expansion, the composition, the refusal.
- [finally-continuations.js](../../../../../decoder/decode-js/src/vm/jsconfuser-vm/wordcode/finally-continuations.js):
  continuation loads.

## 7. Fixtures

| Scenario | Expected result | Committed fixture |
|---|---|---|
| A `LOAD_INT` into a register a `FINALLY_SETUP` of its function names | Selected as a continuation load | [finally-continuations.test.js](../../../../../decoder/decode-js/test/vm/jsconfuser-vm/single-component/finally-continuations.test.js) |
| A suspect load into that register; a suspect `FINALLY_SETUP` | The suspect load is not selected; a suspect setup names no register | finally-continuations.test.js |
| Self-modifying fillers behind a dispatcher under macro opcodes: a filler `LOAD_INT` draws a continuation register | The filler keeps its words; the decode behaves as the source. Reading suspects like any item turns the suite red | [patch-dispatcher-macro-chain](../../../../../decoder/decode-js/test/vm/jsconfuser-vm/cell-suites/patch-dispatcher-macro-chain/suite.js) |
| An address in a macro step after an earlier stage moved code | Resolved through the origin map | |
