# Expand macro VM opcodes

## 1. Target

Expand a proved macro header into its two-to-five canonical constituent instructions. The tails
retain their meaning but inserted opcode words move later addresses. Success supplies current
canonical Packet B and any downstream records rebuilt by dispatcher/anti recovery; decline
supplies no partially expanded container. This differs from passing unknown macro words through.

Readers need [Babel bindings](../../babel.md), [A](extract-container.md), [B's counted grammar](read-wordcode.md),
[handler effects](runtime-meaning.md#2-algorithm)
and the pinned [macro producer](../../../js-confuser-vm/transforms/macro-opcodes.md).
Input is admitted source and its owned numeric container. Runtime observations prove structure,
not comments or macro names. Variable-width calls/arrays/objects are allowed as constituents;
PATCH ciphertext and unadmitted runtime representations are excluded.

## 2. Algorithm

A macro executes canonical handler bodies sequentially, so identify it by a unique decomposition
of its complete effects into canonical handlers' effects. Classify every added handler by what it
does, independently of its label and of physical switch order. Every kind keeps its own proof. Match
only eligible sequences; then let the ordinary canonical reader parse each constituent's tail.
This gives both the original macro width and the expanded canonical widths without guessing
from the runtime body length.

Build an address map before rewriting targets. Every original instruction start maps to the
start of its replacement; a macro's internal newly inserted starts have no old-PC counterparts.
Use that map for control operands and proved continuation loads. Copy synthetic anti words
unchanged: their fake jumps are anti's addition, and anti compaction translates them itself through
the map this route composes. Otherwise consume old-PC dispatcher routes through the same map.
Publish only a canonical result.

### Annotated synthetic example

Supply macro 61 proved as `[LOAD_INT,MOVE]`. Symbols below denote canonical headers; actual
LOAD_INT=1, MOVE=5, JUMP=39 and RETURN=45:

```text
old PC 0: [61,2,9,3,2]       // R2=9; R3=R2; width=5
old PC 5: [39,7]             // JUMP to RETURN boundary
old PC 7: [45,3]             // RETURN R3
new PC 0: [1,2,9]            // inserted first canonical header
new PC 3: [5,3,2]            // inserted second header
new PC 6: [39,8]             // old target 7 maps to 8
new PC 8: [45,3]
map={0:0,5:6,7:8,9:10}
```

Both programs return 9. Expansion increases nine words to ten, and the jump must change.
A target at old PC 2 is an operand, so it has no mapping even though new PC 2 exists.
For a BUILD_ARRAY constituent, parse destination/count and its count-dependent registers at
that occurrence; a second occurrence of the same macro can have a different width. This is a
synthetic word example with supplied handler proof, not standalone source admission.

```mermaid
flowchart LR
  R[Runtime canonical bodies] --> M[Unique macro decomposition]
  M --> W[Counted constituent parsing]
  W --> P[Expansion map / control relocation]
  P --> A[Anti compaction when present]
  P --> D[Dispatcher adapter otherwise]
  A --> B[Current canonical B and rebuilt records]
  D --> B
```

## 3. Implementation

### Runtime proof and mixed reader

The [classifier](runtime-meaning.md#2-algorithm) identifies a macro: its effects are, in exactly
one way, two or more canonical handlers' effects in sequence, its operands read as each step uses
them. The observer takes the added handlers of that kind from the
[identified view](runtime-meaning.md#3-implementation); labels and their order are never read, as
in the [alias source contract](normalize-aliased-wordcode.md#source-proof-and-observation-contract).
Prefix counts come from the anti and specialized observations. Each macro leaves the dispatch
(the view's `ends`), has 2..5 steps, and reads its operands in order across them. Every position
excludes PATCH, TRY_SETUP, TRY_END, DEBUGGER, MAKE_CLOSURE. RETURN, CALL, CALL_METHOD, NEW,
THROW, JUMP, JUMP_IF_FALSE, JUMP_IF_TRUE, FOR_IN_NEXT and FINALLY_SETUP may appear only at the
end. JUMP_REG is **not** in these sets; this reflects the producer's literal omission, not a
general safe-transfer proof. Require at least one macro. In the alias route `allowAliasTail:true`
lets other added handlers remain for alias proof; in the ordinary macro route every added handler
must be a macro or belong to the prefix observations. The frozen runtime record
`jsconfuser-vm-macro-runtime-observation.v1` contains antiPrefixCount, specializedPrefixCount and
`macros:[{opcode,steps:[{name,opcode}]}]`.

The mixed reader consumes one macro header, then each step by constructing a virtual stream
`[canonicalStepOpcode,...remainingOriginalWords]` and applying the canonical cursor grammar.
Consume exactly the parsed tail from the original cursor; retain step words including the
canonical header. Macro width is `1+sum(step.words.length-1)`; expanded width is
`sum(step.words.length)`. The frozen stream record has schemaVersion
`jsconfuser-vm-macro-word-stream-observation.v1`, wordCount and instructions; macro entries
have pc/name/opcode/raw words/width/nextPc/steps. At least one used MACRO is required.
Canonical truncation, invalid words/counts and PATCH still decline; observations supply widths
as owned facts rather than a second externally supplied schema to validate.

### Shared expansion and address relocation

This contract is used by every compactor: macro, specialization, mixed aliases, anti, dispatcher,
CFF and string concealing. `expandObservedWordStream` implements it for added-opcode expansion.

```text
E = new Map()                                  // word-PC units, input PC -> output PC
for instruction in stream (in order):
  E[instruction.pc] = nextPc
  for step in (MACRO or SPECIALIZED ? instruction.steps : [instruction]):
    emit part {originPc: instruction.pc, pc: nextPc, name: step.name, words: copy,
               encoded: instruction is MACRO or SPECIALIZED}
    nextPc += step.words.length
E[stream.wordCount] = nextPc
address(part, w) = E[part.encoded ? O[w] : w]  // O = originPcMap, identity when absent
```

A macro interior is never an original boundary. A target missing from E declines
`macro-target-boundary`; an encoded word missing from O declines `origin-target-boundary`. Emitted
words must total nextPc (`macro-expanded-width`).

**Packet A PC is the address identity.** The encoder resolves every label once, after
selfModifying adds its headers ([resolveLabels](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/transforms/bytecode/resolveLabels.ts#L30-L90)),
and applies the dispatcher's endpoint encoding in that same step. The runtime patches regions in
place and JUMP_REG jumps to the raw register value
([runtime](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/runtime.ts#L879-L897)),
so every address the encoder wrote is a Packet A PC: direct targets, operands kept inside added
opcodes, finally continuation literals and decoded dispatcher endpoints.

```text
O = null                                    // Packet A PC -> current PC; null while they coincide
after each stage that moves code:
  route (alias, macro, specialized, anti):  O = stage.originPcMap      // already composed
  dispatcher, string, CFF:                  O = composePcMaps(O, stage.pcMap)
address the encoder wrote, read by a later stage = O[a]               // missing: decline
address a stage already relocated           = that stage's own E
```

The [standalone schedule](standalone-diagnosis.md#canonical-frontend-retries) owns O and hands it to
every route and every dispatcher call (as `decodedTargetMap`). A stage relocates the canonical
addresses it reads with its own map and leaves an encoded address in Packet A space for the stage
that decodes it. Each map holds only surviving instructions, plus an entry the encoder's own
semantics forward (a PATCH header carries its block's label). A removed instruction has no entry, so
an address naming one declines instead of moving to the next instruction. The self-modifying stage
also publishes which continuation literals inside added opcodes it selected
(`originContinuationLoads`), because a route reading a stream that still holds other added opcodes
cannot see every FINALLY_SETUP.

Direct address offsets count from the header (offset 0):

| Canonical operation | Address offsets |
|---|---|
| JUMP | 1 |
| JUMP_IF_FALSE, JUMP_IF_TRUE | 2 |
| FOR_IN_NEXT | 3 |
| TRY_SETUP | 1 |
| FINALLY_SETUP | 1 and 4 |
| MAKE_CLOSURE | 2 |

Plain immediate operands are not addresses. A SYNTHETIC instruction's words are copied unchanged,
fake conditional targets included: they are anti's addition, so only anti reads them (P3). The
route hands anti `composePcMaps(O,E)` as its `originPcMap`, and anti's
[fake-slot rule](anti-runtime-observation.md#function-models-and-exact-domains) translates each
fake target through it before comparing it with the instruction's fallthrough. Anti emits only
real steps, so an untranslated fake operand never reaches output, and a tampered one declines in
anti's flow proof (`register-isolation`), not here.

**Finally continuation literals** (`selectContinuationLoads`). The compiler gives each try/finally
a dedicated continuation register ([`_finallyContReg`](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/compiler.ts#L491-L495)), writes it
only through [`_emitLoadLabel`](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/compiler.ts#L739-L748) and reads it only with the
finalizer's [JUMP_REG](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/compiler.ts#L1646-L1648). It is a `local::` register, and that pool
assigns slots [with no reuse](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/transforms/bytecode/resolveRegisters.ts#L5-L9). So within one
function, every LOAD_INT whose destination is a FINALLY_SETUP continuation register (words[2])
loads an address: relocate its literal at offset 2 like a direct target. Function membership comes
from the caller's function starts (0 and MAKE_CLOSURE targets, or D's ownership). No boundary
guard applies: a selected literal that is not a boundary declines with the stage's target code.
Other LOAD_INTs stay unchanged.

### Route ownership, state and failures

| Component | Owned input -> output | Required consumer fact |
|---|---|---|
| Prefix/body proof | Source -> added-opcode definitions | No unproved extra cases escape suffix handling. |
| Mixed reader | A + definitions -> complete spans | Counted constituent widths and original boundaries established. |
| Expansion | Stream -> words and E | Direct and selected continuation targets relocated together; synthetic words unchanged. |
| Anti route | Expanded A + E -> compact A/B, optional C/D/E | Compactor composes maps as C(E(oldPc)). |
| Nonanti dispatcher route | Expanded A + E -> canonical A/B, optional rebuilt records | Encoded dispatcher endpoints still name old PCs. |

The normalizer first attempts anti with allowSpecializedTail:true, then specialized with
allowAntiPrefix=Boolean(anti) and allowMacroTail:true; failed optional prefixes contribute null.
Macro proof must account for all remaining cases. Expand with includePcMap:true and the
caller's originPcMap O. Clone A and replace words only. With anti, call anti normalization with
allowSpecializedTail:true/originPcMap:composePcMaps(O,E). Otherwise pass that map to the
[specialized dispatcher adapter](normalize-specialized-wordcode.md#dispatcher-and-anti-specialized-routes).
Return its current records plus schemaVersion `jsconfuser-vm-macro-wordcode-normalization.v1`,
originalWordCount, expandedWordCount (before later compaction), macroInstructionCount.

The whole route is atomic: failure returns `{ok:false,result:null,diagnostic}` without publishing
or mutating source/A. Typed expansion failures preserve their codes; unexpected failures use
`macro-normalization-error`. Successful container/envelope need not be frozen; consumed B/C/D/E
are owned current producer records. Expansion builds no caller AST cache and deletes no source
helpers. Later source emission removes the VM; the [owned chain](standalone-diagnosis.md#owned-record-boundary)
reuses returned records and builds absent records against current words, never stale predecessors.

The [source-informed example scaffold](normalize-aliased-wordcode.md#source-informed-example-control-boundary)
uses the exact words above and the supplied retained canonical runtime to reach the normal source
entry. Its normalization succeeds with exact expected words and unchanged A; public emission then
returns unemittable-structured-control for the unconditional jump directly to RETURN. This
separately records recovery and later valid decline, without expanding this page's admission claim.

### Acceptance scenarios

| Scenario | Oracle / acceptance criterion | Evidence and limit |
|---|---|---|
| M1 header insertion / branch | Exact example words/map/value; expandedWordCount increases and old target relocates | Worked synthetic calculation and macro boot/branch tests. |
| M2 counted tail / terminal call | Canonical reader's per-occurrence count/spread grammar; complete stream consumed and frame behavior agrees | Arrays/closures fixtures; all canonical variable grammars remain B dependencies. |
| M3 mixed routes | Every added-opcode effect observed; canonical B and C(E(oldPc)) dispatcher endpoints | Combination/alias tests; retained profiles only. |
| M4 source handler/count/target damage | Reach body match, counted reader or boundary remap as named; result:null and public decline | Body and oversized-array source controls; mid-macro test includes private packet plus source mutation. |
| M5 immutable and derived state | A/source unchanged; current records agree with emitted spans/targets; fresh parse has no VM residue and consistent consumed state | Existing normalization/identity tests. |

## 4. Input Shapes

[PATCH recovery](normalize-self-modifying-wordcode.md) consumes these proved added-opcode definitions
at original widths, then expands only recovered executable instructions. Its finite combined
boundary is [the PATCH census](../../tests.md#finite-patch-added-opcode-qualification); the linear
stream reader on this page still does not interpret encrypted storage.

| Earlier decoder output / spelling | Gate or dependency |
|---|---|
| [Packet A](extract-container.md) / [handler locator](locate-handlers.md#4-input-shapes) | Supply the words, the handler bodies and the opcode table for every runtime spelling the locator lists. |
| [PATCH compaction](normalize-self-modifying-wordcode.md) | Words with selfModifying's additions removed; addresses inside added opcodes are still Packet A addresses and go through its `originPcMap` ([address spaces](normalize-macro-wordcode.md#shared-expansion-and-address-relocation)). |
| [Classifier](runtime-meaning.md#2-algorithm) and the anti and specialized observations | The classifier decides each added handler's kind; the observations' counts account for the non-macro ones. |
| [Alias projection](normalize-aliased-wordcode.md) | Canonicalizes alias operands at equal width before this shared expansion; alias suffix was separately proved. |
| [B canonical parser](read-wordcode.md) | Supplies the sole counted/spread/constant operand grammar, including variable-width macro tails. |

A allows extra CALL_SPREAD uses inside run while requiring one per canonical call case; a macro
ending in CALL adds a legitimate use. The [pinned macro recipe](../../../js-confuser-vm/transforms/macro-opcodes.md#4-later-stages)
explains canonical-only constituents and the terminal checks; it does not establish all combinations.

## 5. Known Gaps

A unique decomposition into the runtime's own canonical handlers remains required; it does not
prove those handlers' semantics. Nonterminal JUMP_REG can pass the literal decomposition checks,
but general correctness of that producer hazard is not qualified; document it rather than silently
strengthen the matcher. PATCH storage needs the earlier
[PATCH compaction](normalize-self-modifying-wordcode.md); it is never a linear macro stream.
Minified class and profiles beyond the retained fixtures and the linked finite PATCH census
remain unqualified.

## Source

The observer and mixed cursor grammar in item 3 are
[observe-macro-runtime.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/observe-macro-runtime.js),
on the classifier in [identify-handlers.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/identify-handlers.js),
and [read-wordcode.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/read-wordcode.js).
The shared relocation contract is implemented by
[expand-observed-word-stream.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/expand-observed-word-stream.js)
(`expandObservedWordStream`, `composePcMaps`), with the continuation rule in
[finally-continuations.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/finally-continuations.js)
(`selectContinuationLoads`).
Dispatcher/anti adapters and binding comparison are linked item 3 dependencies.

The decoder is [normalize-macro-wordcode.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/normalize-macro-wordcode.js),
wired by [diagnose-standalone.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/diagnose-standalone.js)
under the dependencies described in item 4.

The pinned encoder's [bytecode macro pass](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/transforms/bytecode/macroOpcodes.ts)
counts and replaces repeated instruction windows. Its
[runtime macro pass](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/transforms/runtime/macroOpcodes.ts)
appends handlers made from cloned constituent bodies.

## Fixtures

The scenario tables in item 3 state acceptance oracles; rows below index retained inputs/tests.
The annotated examples are source-informed synthetic controls, not independent cold proofs.
Fixture qualification records and the [shared provenance contract](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/qualification-provenance.md)
bound historical generated evidence; no fresh encoder generation or wider profile qualification
is asserted by this specification. Private copied-packet controls establish internal choices
only; source mutations that still reach A/B pin normal-entry refusals separately.

The retired frozen bounded verifier demonstrated
M1/M2/M4's selected LOAD_INT/MOVE and BUILD_ARRAY/MOVE body decomposition, per-occurrence counted
array widths, inserted headers, exact E and the original-operand target refusal. The
[shared proof boundary](normalize-aliased-wordcode.md#independent-bounded-proof) supplies canonical
handler functions/A and reduced span-state builders. Complete canonical inventory/case syntax,
CALL/closure/object grammar, class layouts, continuation provenance and actual mixed dispatcher
recovery are not reconstructed. Current words/spans and selected unchanged inputs are asserted;
no C/D/E, public emission or generated-option qualification follows.

| Committed fixture or test control | Claim pinned |
|---|---|
| [macro-runtime-boot](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/macro-runtime-boot/encoded.js) and its [qualification record](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/macro-runtime-boot/qualification.json) | Two repeated constant loads form a simple macro. |
| [macro-runtime-branches](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/macro-runtime-branches/encoded.js) and its [qualification record](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/macro-runtime-branches/qualification.json) | A terminal jump inside a macro requires PC expansion and branch-target remapping. |
| [macro-runtime-closures](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/macro-runtime-closures/encoded.js) and its [qualification record](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/macro-runtime-closures/qualification.json) | A terminal variable-width call adds a `CALL_SPREAD` use and preserves closure behavior. |
| [macro-runtime-exceptions](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/macro-runtime-exceptions/encoded.js) and its [qualification record](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/macro-runtime-exceptions/qualification.json) | Exception/finally control preserves continuation labels through expansion. |
| [macro-runtime-arrays](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/macro-runtime-arrays/encoded.js) and its [qualification record](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/macro-runtime-arrays/qualification.json) | Repeated variable-width array builders are parsed inside macro instructions. |
| [anti-macro-exceptions](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/anti-macro-exceptions/encoded.js) and its [qualification record](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/anti-macro-exceptions/qualification.json) | Synthetic and macro cases compose through catch/finally behavior. |
| [specialized-macro-nested-strings](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/specialized-macro-nested-strings/encoded.js) and its [qualification record](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/specialized-macro-nested-strings/qualification.json) | Specialized and macro cases compose around nested string captures. |
| [macro-six-option-no-anti-exceptions](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/macro-six-option-no-anti-exceptions/encoded.js) and its [qualification record](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/macro-six-option-no-anti-exceptions/qualification.json) | Dispatcher targets use original PCs after macro and specialized expansion without anti compaction. |
| [macro-seven-option-exceptions](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/macro-seven-option-exceptions/encoded.js) and its [qualification record](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/macro-seven-option-exceptions/qualification.json) | All seven effects are observed while exception behavior survives the composed inverse. |
| [macro-seven-option-repeated-arrays](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/macro-seven-option-repeated-arrays/encoded.js) and its [qualification record](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/macro-seven-option-repeated-arrays/qualification.json) | Three macro instructions include variable-width array builders in the full stack. |
| [normalize-macro-wordcode.test.js](../../../../decoder/decode-js/test/vm/jsconfuser-vm/normalize-macro-wordcode.test.js) | Full-stream expansion, source/encoded/decoded behavior, no VM residue, derived-state consistency, changed-handler and mid-instruction target declines, and a source-admitted oversized array count rejected by counted-payload parsing and standalone decoding. |
| [normalize-macro-combinations.test.js](../../../../decoder/decode-js/test/vm/jsconfuser-vm/normalize-macro-combinations.test.js) | Mixed-runtime prefix proof, immutable Packet A, behavior and derived-state agreement, and atomic decline for changed macro or specialized cases. |
| [runtime-binding-identities.test.js](../../../../decoder/decode-js/test/vm/jsconfuser-vm/runtime-binding-identities.test.js) | Combined class/handler stacks retain complete body proofs after every lexical binding is independently renamed. |
