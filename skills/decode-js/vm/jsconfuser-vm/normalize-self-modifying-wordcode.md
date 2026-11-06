# Normalize self-modifying wordcode

Pipeline stage: `recover-patch` ([map](../../pipelines/jsconfuser-vm.md)).

## 1. Target

Remove what selfModifying added and nothing else. Given the
[observation](self-modifying-observation.md), drop the PATCH headers, decoy PATCHes, decoy fillers
and the storage after the code, keep every other instruction's words, and publish where each
`extract-container` address now lives. Suspects (fillers the observation could not decide while a
dispatcher hid labels) stay as code until a later component recovers those labels; the settle then
removes the ones that are fillers. Success differs from passthrough by the absence of PATCH and its
junk; added opcodes (alias, macro, specialized, anti) remain for their own components.

Readers need [`extract-container`](extract-container.md), the observation's record and the
[shared relocation contract](normalize-macro-wordcode.md#shared-expansion-and-address-relocation).
Input is admitted source text and its `extract-container`; both stay unchanged.

## 2. Algorithm

Labels resolve after selfModifying adds its headers, so every address in the stream points into the
with-headers layout. Removing the headers moves code; the component relocates only the addresses it can
read as canonical, and hands the rest on as a map:

1. **Keep or drop.** Walk the observed code in order. PATCH, DECOY and filler entries emit nothing;
   every other instruction emits its materialized words. Record each kept instruction's output PC,
   map each PATCH header to the next emitted word (a block's label can sit on its header), and map
   the code end to the output length. Decoys and fillers get no entry: they sit after a terminator
   and before the next label, so an address naming one proves the entry was code, and declines.
   A suspect is kept with an entry: a hidden label may name it.
2. **Select continuation literals once, over every step.** Run the shared continuation rule over the
   steps of every kept instruction, canonical or added, reading past suspects by the
   [shared rule](normalize-macro-wordcode.md#shared-expansion-and-address-relocation): a filler
   LOAD_INT draws registers 0..24 and can name a continuation register, so a suspect load keeps its
   `extract-container` word until the settle decides it. A FINALLY_SETUP and its continuation
   LOAD_INT are chosen independently by the added-opcode components, so they can sit in two different
   added opcodes; only this whole view sees both.
3. **Relocate canonical addresses.** In a canonical instruction, map each direct target and each
   selected continuation literal; a target with no entry declines.
4. **Leave the rest, with the proof.** An added opcode keeps its words: its addresses are still
   `extract-container` addresses, translated by its own component through the published `originPcMap`
   (`extract-container` PC -> output PC). The continuation literals selected inside added opcodes
   are published as `originContinuationLoads` (output PC -> step indexes), so that component translates
   them without selecting again over a view where another added opcode hides the FINALLY_SETUP. The
   dispatcher's encoded endpoints are translated the same way.
5. **Parse once.** Canonical `read-wordcode` is built when no added opcode remains; otherwise the
   [standalone schedule](standalone-diagnosis.md#canonical-frontend-retries) runs the added-opcode
   routes on the output with the map. `suspects` and `suspectRuns` are published as
   `extract-container` PCs.

### Settling suspects

A suspect is undecided only because a label is hidden: the observation's rule is right, its input
incomplete. So the owner's rule reruns once a later decoder has recovered the labels, over the
current canonical stream, reading every address through the composed origin map O
(`extract-container` PC -> current PC). Every component in between keeps suspects in place and reads
past them; a component that removes one (the dispatcher drops its decode closure, anti drops a decoy)
leaves it without an entry in O, so it leaves the suspect set.

```text
explanatory
settle(stream, suspects, suspectRuns, O, recoveredLabels):
  if some JUMP_REG is not a finalizer's (reads no FINALLY_SETUP continuation register of its
     function): return nothing             # labels still hidden; E declines the JUMP_REG later
  current = { O(s) : s in suspects, O has s }
  labels  = function starts
          + direct targets of non-suspects
          + continuation literals selected over non-suspects
          + O(recoveredLabels)             # dispatcher skip labels, now reached by fallthrough
  repeat:
    code = for each run (in O, suspects only):
             all its entries if its anchor still exists and, walking back, a label comes
             before a body end (the anchor stands inside a collected body);
             otherwise the entries from the first one in labels on
    labels += direct targets of code, and O(word 2) of continuation loads among code
  until labels stop growing
  fillers = current - code
  drop fillers; remap direct targets and continuation literals (a code suspect's literal is a
  `extract-container` word: through O first); parse; publish pcMap; suspects = []
```

The anchor test is the [observation's](self-modifying-observation.md#2-algorithm), repeated because
a dispatcher hides the label of the body a finalizer's `JUMP_REG` sits in: the observation's walk
finds a body end and calls the state transition after it a suspect. With the labels known the walk
stops at the label, and the transition stays. An anchor a later decoder removed decides nothing.

The recovered labels matter because a dispatcher rewrites a conditional route's final JUMP as a
JUMP_IF whose skip edge is now fallthrough: the stream no longer names the label the decoys sat
before. The dispatcher publishes each skip label it decodes (`skipLabels`, `extract-container` PCs).

Worked example (real encoder output, `loops-dispatcher-2`: loops.src.js, selfModifying and
dispatcher on the qualification baseline, seed 2; `extract-container` PCs from the encoder listing):

```text
117: JUMP dispatcher_10        end of a conditional route
119: LTE r20 = r3 <= r20       suspect (run 1, entry 1)
123: GT  r23 = r24 > r7        suspect (run 1, entry 2)
127: PATCH -> for_exit_6_skip_11   the route's skip label
371: JUMP dispatcher_14        end of another conditional route
373: ADD r13 = r3 + r4         suspect (run 2), and the skip label for_exit_3_skip_15
377: MOVE r6 = r13             suspect (run 2)
```

The dispatcher recovers both routes and publishes skip labels 127 and 373. Run 1 holds no label,
so 119 and 123 are fillers and leave; the new JUMP_IF falls through to 127. Run 2 starts on a
label, so 373 and 377 are code. Treating run 2 as filler drops the loop body (wrong output);
treating run 1 as code runs the decoys, whose registers ignore the frame.

### Worked example

In the [observation example](self-modifying-observation.md#worked-example-real-encoder-output), the
code is [0,107) with real PATCHes at 0, 21, 57, 64 and 80, a decoy at 52 and fillers at 49, 95 and
99. The output starts `[4,1, 47,3,39,1,6,0,0, 5,2,3, ...]`: the PATCH at 0 maps to 0, the
plaintext `LOAD_THIS r1` at 5 maps to 0, and `MAKE_CLOSURE r3` at 7 maps to 2, whose closure
entry 57 (a PATCH) is rewritten to 39, the output PC of its first materialized instruction. The
427 input words become 68.

## 3. Implementation

`diagnoseNormalizeSelfModifyingWordcode(container, { source = null })` returns
`{ ok, result, diagnostic }`. With source it first proves the added-opcode definitions
(`diagnosePatchAddedOpcodes`); without source no added opcode is admitted.

| Component | Contract |
|---|---|
| Observation | `diagnoseSelfModifyingRegions`; its refusal is this component's refusal. |
| Compaction | As in item 2; offsets JUMP 1, JUMP_IF_FALSE/TRUE 2, FOR_IN_NEXT 3, TRY_SETUP 1, FINALLY_SETUP 1 and 4, MAKE_CLOSURE 2; continuation literals at offset 2 by `selectContinuationLoads`, functions from 0 and every MAKE_CLOSURE target (canonical or inside an added opcode's steps). A missing target declines `self-modifying-target`. |
| Result | `schemaVersion` `jsconfuser-vm-self-modifying-normalization.v2`, cloned `container` with the compact words, `wordcode` (canonical `read-wordcode`, or null while added opcodes remain), `originPcMap`, `originContinuationLoads` (Map from output PC of an added opcode to the step indexes of its selected continuation LOAD_INTs), `suspects`, `suspectRuns`, `originalWordCount`, `wordCount`, `patchCount`, `decoyCount`, `fillerCount`, `addedOpcodeCounts`. |
| Settle | `diagnoseSettleSelfModifyingSuspects(container, wordcode, { suspects, suspectRuns, originPcMap, recoveredLabels })` over canonical current `read-wordcode`, as in item 2. `result` is null while a JUMP_REG is not a finalizer's; otherwise `container`, `wordcode`, `pcMap` (current -> settled), empty `suspects` and `suspectRuns`, `fillerCount`. A target with no entry declines `self-modifying-target`. |
| Failure | `{ ok: false, result: null, diagnostic }`; unexpected errors are `normalizer-error`. No partial result. |

The component builds no `validate-references` or `partition-functions` and calls no other
normalizer. The schedule passes `originPcMap`, `originContinuationLoads` and `suspects` to the
alias, macro, specialized, anti-specialized and anti routes, keeps the map as its
[origin map](normalize-macro-wordcode.md#shared-expansion-and-address-relocation) for every later
dispatcher call, and runs the settle after each result it adopts from a component that can recover
labels (an added-opcode or anti route, the string-concealing dispatcher adapter, the dispatcher),
passing every `skipLabels` adopted so far; it then rebuilds `validate-references` and
`partition-functions` from the settled stream. No settle follows CFF: it emits no JUMP_REG.

### Acceptance scenarios

| Scenario | Oracle | Criterion | Fixture |
|---|---|---|---|
| S1 compaction | Fresh parse and behaviour | Shorter canonical stream, no VM residue, consistent derived state, source behaviour | `single-payload-stage` below |
| S2 added opcodes stay | Their own components | `wordcode` is null while added opcodes remain; public decode recovers | `patch-widths-chain` below |
| S3 storage address | Named refusal | A finally continuation literal moved into storage declines `self-modifying-target` | No committed test |
| S4 inner components | Public decode | Dispatcher endpoints, anti fake branches and an alias continuation literal whose FINALLY_SETUP is specialized reach their components through the map | `flattened-self-modifying-dispatcher`, `self-modifying-dispatcher-anti`, `self-modifying-patch-stack` below |
| S5 settle | Encoder listing and public decode | After the dispatcher, a run before a recovered label leaves and a run from a label on stays; a route starting on a suspect counts its target; the cells decode with source behaviour | `flattened-self-modifying-dispatcher`, `self-modifying-dispatcher-anti` below |

## 4. Input Shapes

| Earlier producer | Shape | Effect |
|---|---|---|
| [Observation](self-modifying-observation.md) | Code, patches, decoys, fillers, suspects and their runs, materialized words | Consumed whole. |
| [Dispatcher](normalize-dispatcher-wordcode.md), anti's or the schedule's | Canonical stream with routes rewritten, `skipLabels` | Input to the settle. |
| [`extract-container`](extract-container.md#4-input-shapes) | Numeric words for every transport | The map's domain is `extract-container` PCs. |

Later stages receive the output words, `originPcMap` and `originContinuationLoads`; each
[added-opcode route](normalize-macro-wordcode.md#shared-expansion-and-address-relocation) and the
[dispatcher](normalize-dispatcher-wordcode.md) owns the translation of the addresses it encoded.

## 5. Known Gaps

The observation's gaps apply: dead compiler code read as filler, and an unauthenticated cipher.
Anti's deferred seeds (an optional seed a suspect touches) stay as code after the settle; no
encoder-generated case has reached one. Wider option stacks are bounded by the suites below and the
[finite PATCH census](qualify-jsconfuser-vm.md#finite-patch-added-opcode-qualification).

## Source

The normalizer is
[normalize-self-modifying-wordcode.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/normalize-self-modifying-wordcode.js)
(`diagnoseNormalizeSelfModifyingWordcode`, `diagnoseSettleSelfModifyingSuspects`), wired in
[diagnose-standalone.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/diagnose-standalone.js).
The producer resolves labels after selfModifying
([compiler.ts](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/compiler.ts#L3400-L3420)),
which is why encoded addresses are `extract-container` addresses.

## Fixtures

Each suite encodes its sources with the pinned encoder and requires the decode to behave as the
source ([tests.md](../../tests.md#suites)); a Proved line names the code whose break turns the case
red.

| Suite and cases | Claims | Proved |
|---|---|---|
| [single-payload-stage](../../../../decoder/decode-js/test/vm/jsconfuser-vm/generated-cells/single-payload-stage/suite.js), file `self-modifying` | S1: the stage step leaves no PATCH; the decode behaves as the source | A decoy PATCH header is skipped and does not end the code scan |
| [patch-widths-chain](../../../../decoder/decode-js/test/vm/jsconfuser-vm/generated-cells/patch-widths-chain/suite.js) | S2: added opcodes stay for their own components | A PATCH region holding added opcodes is read with their widths |
| [flattened-self-modifying-dispatcher](../../../../decoder/decode-js/test/vm/jsconfuser-vm/generated-cells/flattened-self-modifying-dispatcher/suite.js) | S4, S5: dispatcher endpoints through the map; the settle | Settle's anchor test in this pass |
| [self-modifying-dispatcher-anti](../../../../decoder/decode-js/test/vm/jsconfuser-vm/generated-cells/self-modifying-dispatcher-anti/suite.js) | S4, S5: anti decoys behind a dispatcher; the hidden labels settle | Settle in `diagnose-standalone` |
| [self-modifying-patch-stack](../../../../decoder/decode-js/test/vm/jsconfuser-vm/generated-cells/self-modifying-patch-stack/suite.js) | S4: every added-opcode stage over PATCH | The patch-ciphertext storage end |
| [transport-patch-chain](../../../../decoder/decode-js/test/vm/jsconfuser-vm/generated-cells/transport-patch-chain/suite.js) | The encoded and minified PATCH combination decodes with source behaviour | The encoded transport read as little-endian words |

S3 has no committed test: the old storage-address control edited input by hand.
