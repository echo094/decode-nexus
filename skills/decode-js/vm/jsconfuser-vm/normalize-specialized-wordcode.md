# Expand specialized VM opcodes

Pipeline stage: `recover-added-opcodes` ([map](../../pipelines/jsconfuser-vm.md)).

## 1. Target

Recover operands baked into a proved runtime handler and expand each one-word specialized
instruction into its canonical header and tail. This turns unknown `read-wordcode` headers into
ordinary instructions while relocating addresses. Success changes both the word stream and
its consumed records; it does not reconstruct compiler-side symbolic tuples or return original
source names.

Readers need [Babel binding semantics](../../babel.md), [`extract-container`](extract-container.md),
[`read-wordcode`'s operand grammar](read-wordcode.md),
[handler effects](runtime-meaning.md#2-algorithm) and the pinned
[specialization producer](../../../js-confuser-vm/transforms/specialized-opcodes.md). Input is
admitted source and its owned numeric `extract-container`. Other added opcodes need their own
proofs; PATCH ciphertext and arbitrary supplied model records are outside this input boundary.

## 2. Algorithm

A specialized handler has the canonical operation's complete body with operand reads replaced
by numbers. Compare it with each canonical fixed-width reference after the binding-aware
projection. At an operand call capture one literal; at a constant call capture its explicit
index/key arguments. Every other semantic field must match. Exactly one reference must fit,
with at least one recovered operand.

Read specialized headers as one-word instructions, retaining their recovered canonical step.
Expand them using the [shared map procedure](normalize-macro-wordcode.md#shared-expansion-and-address-relocation):
addresses in the original stream name compact one-word boundaries, not the new operand positions.
Relocate direct/finalizer operands, then consume old-PC dispatcher routes if present. With anti,
copy synthetic words unchanged and hand anti composePcMaps(O,E) as its originPcMap; anti translates
its own fake operands and erases registers/seeds.
Macros and aliases use joint routes rather than treating their headers as specialized cases.

### Annotated synthetic example

Supply a specialized case 61 whose body corresponds uniquely to LOAD_GLOBAL=2 with
`dst=4; name=constant(7,0); R[dst]=globals[name]`. With pool[7]=`"answer"` and ordinary
host answer=42, its one-word instruction assigns R4=42:

```text
old: PC0 [61]; PC1 [39,3]; PC3 [45,4]       // JUMP, RETURN
recovered tuple=[4,7,0]
new: PC0 [2,4,7,0]; PC4 [39,6]; PC6 [45,4]
E={0:0,1:4,3:6,5:8}
```

The canonical step finishes at PC4 rather than PC1; return still receives 42. Reading another
three words from the old stream would consume its jump and corrupt the program. This supplied
handler/word example omits source admission, tuple selection, frame completion and keyed constants.
A wrong baked register or captured runtime binding must fail body proof or later legality checks;
comments cannot repair it.

```mermaid
flowchart LR
  H[Complete canonical / added handlers] --> T[Unique body match / baked tuple]
  T --> W[One-word parse]
  W --> E[Expand words / relocate through E]
  E --> D[Dispatcher old-PC adapter]
  E --> A[Anti compaction C]
  D --> B[Current canonical records]
  A --> B
```

## 3. Implementation

### Specialized handlers from the classifier

The [classifier](runtime-meaning.md#2-algorithm) identifies a specialized handler: its effects
unify with exactly one fixed-width canonical handler, every canonical operand slot bound to a
literal, in canonical read order. The observer takes the added handlers of that kind from the
[identified view](runtime-meaning.md#3-implementation); labels and their order are never read.
Each must leave the dispatch (the view's `ends`), and each baked operand must be an integer in
0..4294967295, since it becomes a word. With allowAntiPrefix=true the anti handlers the classifier
names count as the anti prefix. Without allowMacroTail every other added handler must be one of
those; with it, the macro proof accounts for the rest.

The classifier excludes the variable-width references MAKE_CLOSURE, BUILD_ARRAY, BUILD_OBJECT, CALL,
CALL_METHOD and NEW. Do not invent a second encoder selection cap in this observer: it requires >=1 captured operand,
not the producer census's 1..6/candidate/frequency limits. Exactly one handler match returns
`{opcode,originalName,originalOpcode,operands}`. The frozen observation schema is
`jsconfuser-vm-specialized-runtime-observation.v1` with antiPrefixCount and specialized array.
No original tuple objects or compiler placeholders survive in this decoder observation.

The mixed reader emits `SPECIALIZED` entries with raw words=[opcode], width=1,
nextPc=pc+1 and one `steps` row `{name,opcode,words:[originalOpcode,...operands]}`. Other
canonical/anti forms retain their grammar. Require a used specialized header. The frozen stream
record has schemaVersion `jsconfuser-vm-specialized-word-stream-observation.v1`, wordCount and
instructions. Canonical counted parsing still owns any surrounding variable tails.

### Dispatcher and anti-specialized routes

| Route | Sequence and map owner | Returned records |
|---|---|---|
| Specialized alone | Prove/parse -> expand with includePcMap and the caller's originPcMap O -> dispatcher adapter with composePcMaps(O,E) | Current `extract-container` and `read-wordcode`; dispatcher success can add `validate-references` and `partition-functions`. |
| Anti-specialized public retry | Prove anti prefix + complete specialized tail -> expand with includePcMap and O -> anti reader -> anti normalizer with allowSpecializedTail true and originPcMap composePcMaps(O,E) | Anti result with specialized/synthetic counts. |
| Macro/alias joint route | Their prefix proof/whole stream -> shared expansion -> anti or dispatcher | Those normalizers own publication and pass actual E. |

Every route passes the map from its own expansion, composed with the caller's O
([address spaces](normalize-macro-wordcode.md#shared-expansion-and-address-relocation)), so no
consumer rebuilds a map from the source's `extract-container`. These are actual call contracts, not
alternate public options inferred from encoder flags.

The dispatcher adapter first canonical-parses expanded `extract-container`. If no JUMP_REG, return
`extract-container` and `read-wordcode` directly. Otherwise normalize keyed constants only if a
constant-ref has nonzero concealKey, then build `validate-references`. Build `partition-functions`
with every multi-parent entry published as a
[suspect](partition-functions.md#shared-parent-suspects) (the shared string helper); a
`partition-functions` refusal propagates. Call the
[dispatcher inverse](normalize-dispatcher-wordcode.md) with
decodedTargetMap:E. Success returns its current records, with `originPcMap` = E composed with the
dispatcher's `pcMap` (E alone when no dispatcher ran); `no-dispatcher` leaves the original expanded
`extract-container` and `read-wordcode` result; any other dispatcher decline propagates. Even when
keyed records and `partition-functions` were privately prepared, no-dispatcher does not publish
those temporary records. Later standalone constant/reference/partition gates and the backend's control solver still decide
admission.

### Output, atomicity and acceptance

All word writes target cloned `extract-container`. Whole-route failure returns result:null and typed
diagnosis; unexpected failures become specialized-normalization-error or
anti-specialized-normalization-error. The successful specialized result is
`jsconfuser-vm-specialized-wordcode-normalization.v1` with container/wordcode, optional current
rebuilt records, originalWordCount, expandedWordCount and specializedInstructionCount. The pair uses
`jsconfuser-vm-anti-specialized-wordcode-normalization.v1` with originalWordCount,
specializedInstructionCount and syntheticInstructionCount. Envelope/container are not universally
frozen; observations and `read-wordcode`, `validate-references` and `partition-functions` are
frozen owned facts. No AST helpers are deleted or caller scopes refreshed here.
Reused records belong to the current words; absent records are built later by the
[owned chain](standalone-diagnosis.md#owned-record-boundary). A successful internal expansion can
still receive a public atomic decline at later components.

| Scenario | Oracle / acceptance criterion | Evidence and limit |
|---|---|---|
| S1 literal and constant-pair inversion | Exact tuple/one-word width/example map; output contains canonical header/operands and correct value | Worked synthetic calculation; `single-payload-stage` below. |
| S2 anti/macro/alias composition | Complete added-opcode proofs and current mapped targets, positive added-opcode counts | `added-opcodes-chain`, `patch-widths-chain`, `all-stages-together` below. |
| S3 source body/range damage | Reach specialized-runtime with `extract-container` admitted; result:null and public decline | No committed test. |
| S4 current state and atomicity | Original `extract-container`/source unchanged; no VM residue, emitted behavior agrees and fresh parse state is consistent | Every cell and the stage step. Dispatcher/no-dispatcher partial boundary is source-inspected. |

## 4. Input Shapes

[PATCH recovery](normalize-self-modifying-wordcode.md) consumes these proved added-opcode definitions
at original widths, then expands only recovered executable instructions. Its finite combined
boundary is [the PATCH census](qualify-jsconfuser-vm.md#finite-patch-added-opcode-qualification); the linear
stream reader on this page still does not interpret encrypted storage.

| Earlier decoder producer / spelling | Effect |
|---|---|
| [`extract-container`](extract-container.md) / [handler locator](locate-handlers.md#4-input-shapes) | Supply the words and the handler bodies (a table handler's frame prologue split off) for every runtime spelling the locator lists. |
| [PATCH compaction](normalize-self-modifying-wordcode.md) | Words with selfModifying's additions removed; addresses inside added opcodes are still `extract-container` addresses and go through its `originPcMap` ([address spaces](normalize-macro-wordcode.md#shared-expansion-and-address-relocation)). |
| [Classifier](runtime-meaning.md#2-algorithm) | Sorts every added handler by its effects; anti, macro and alias handlers belong to their own readers whatever their labels. |
| [Alias projection](normalize-aliased-wordcode.md) / [macro observer](normalize-macro-wordcode.md) | Restore aliases before joint expansion or prove suffix after this prefix; no speculative added opcode is trusted. |
| [Canonical `read-wordcode`](read-wordcode.md) / [constant inverse](normalize-concealed-constants.md) | Define tuple semantics and restore keyed values for dispatcher proof. |

The pinned [specialization recipe](../../../js-confuser-vm/transforms/specialized-opcodes.md#4-later-stages)
owns hidden-operand/finalization production. The decoder observes final numbers, not that
private object graph. No broad representation qualification follows from this source relation.

## 5. Known Gaps

Only complete matches with one fixed-width canonical handler are admitted. A baked operand whose
value no effect shows (a read the handler never uses) cannot be recovered, and such a handler stays
unclassified.
The general allocator has a wider domain; no complete selection/slot population is qualified.
Added-opcode PATCH slices use the separate [finite original-width contract](normalize-self-modifying-wordcode.md).
Wider PATCH representations, minified-class admission, unrestricted JUMP_REG/continuation provenance
and other combinations no suite holds remain open.

## Source

Item 3's complete substitution proof and one-word cursor are
[observe-specialized-runtime.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/observe-specialized-runtime.js)
(`diagnoseSpecializedRuntime(source, options)`) and [read-wordcode.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/read-wordcode.js).
The same normalizer file owns the dispatcher adapter and anti-specialized route;
[normalize-anti-wordcode.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/normalize-anti-wordcode.js)
consumes the pair's map. Expansion and binding comparison remain linked
shared contracts, not duplicated implementations.

The decoder is [normalize-specialized-wordcode.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/normalize-specialized-wordcode.js):
`diagnoseNormalizeSpecializedWordcode(source, container, options)` for specialization alone,
`diagnoseNormalizeAntiSpecializedWordcode(source, container, options)` for the anti-specialized
route, and `normalizeExpandedSpecializedDispatcher(source, normalized, pcMap, suspects)`, the
dispatcher adapter that the alias and macro normalizers also call on their expanded stream. It is
wired by [diagnose-standalone.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/diagnose-standalone.js)
under the dependencies described in item 4.

The pinned encoder's [bytecode specialization pass](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/transforms/bytecode/specializedOpcodes.ts)
chooses frequent opcode/operand tuples and drops their operands from serialization. Its
[runtime specialization pass](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/transforms/runtime/specializedOpcodes.ts)
clones the original handlers and inlines the resolved numeric operands.

## Fixtures

The scenario tables in item 3 state acceptance oracles; the suites below hold them. The annotated
examples are source-informed synthetic controls, not independent cold proofs.

The retired frozen bounded verifier demonstrated S1/S3's synthetic LOAD_GLOBAL tuple [4,7,0],
literal/constant-pair capture, exact one-word expansion, and fractional
baked-literal refusal at specialized-runtime. Its
[shared proof boundary](normalize-aliased-wordcode.md#independent-bounded-proof) supplies the
handler reference/A and reduced span-state builder. Class dummy arguments, inventory/prefix
admission, key restoration, anti-specialized map passing, dispatcher/no-dispatcher routes, full
`read-wordcode` through `partition-functions` and public emission are source-audited or declared dependencies,
not cold rebuilt. The selected words/spans and unchanged originals are evidence of recovery, not
generated or combined-profile qualification.

Each suite encodes its sources with the pinned encoder and requires the decode to behave as the
source ([tests.md](../../tests.md#suites)); a Proved line names the code whose break turns the case
red.

| Suite and cases | Claims | Proved |
|---|---|---|
| [single-payload-stage](../../../../decoder/decode-js/test/vm/jsconfuser-vm/generated-cells/single-payload-stage/suite.js), file `specialized-opcodes` | S1, S4: the stage step expands specialized cases to words equal to the plain program's; the decode behaves as the source | Specialized operands become the expanded instruction's words |
| [dispatcher-specialized-chain](../../../../decoder/decode-js/test/vm/jsconfuser-vm/generated-cells/dispatcher-specialized-chain/suite.js) | Dispatcher old-PC targets survive expansion without anti instrumentation | `decodedTargetMap` in this pass |
| [dispatcher-keys-specialized](../../../../decoder/decode-js/test/vm/jsconfuser-vm/generated-cells/dispatcher-keys-specialized/suite.js) | A specialized instruction's concealed key restored before the dispatcher reads it | The concealKey test in this pass |
| [added-opcodes-chain](../../../../decoder/decode-js/test/vm/jsconfuser-vm/generated-cells/added-opcodes-chain/suite.js) | S2: anti, specialized, macro and alias each read the previous output | The alias macro tail in `normalize-aliased-wordcode` |
| [patch-widths-chain](../../../../decoder/decode-js/test/vm/jsconfuser-vm/generated-cells/patch-widths-chain/suite.js) | S2: PATCH regions over the width-changing passes | A PATCH region holding added opcodes is read with their widths |
| [all-stages-together](../../../../decoder/decode-js/test/vm/jsconfuser-vm/generated-cells/all-stages-together/suite.js) | S2: the six-option stack and every other stage | Specialized operands up to a full 32-bit word |
| [minify-over-specialized-opcodes](../../../../decoder/decode-js/test/vm/jsconfuser-vm/generated-cells/minify-over-specialized-opcodes/suite.js) | Handlers found under minify over specialized cases | No break of its own |
| [handler-table-over-specialized-opcodes](../../../../decoder/decode-js/test/vm/jsconfuser-vm/generated-cells/handler-table-over-specialized-opcodes/suite.js) | Handlers found through a handler table | No break of its own |
| [class-rewrite-over-specialized-opcodes](../../../../decoder/decode-js/test/vm/jsconfuser-vm/generated-cells/class-rewrite-over-specialized-opcodes/suite.js) | Handlers found under the class rewrite | No break of its own |
| [transport-patch-chain](../../../../decoder/decode-js/test/vm/jsconfuser-vm/generated-cells/transport-patch-chain/suite.js) | Body proofs hold after minify renames the bindings | The payload is reached by structure through renamed bindings |

S3 has no committed test: the old changed-handler controls edited encoded input by hand, a shape
no encoder emits.
