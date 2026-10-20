# Normalize aliased VM opcodes

## 1. Target

Replace proved alias headers and permuted tails with canonical opcode words. An alias takes
exactly the same word span as its original operation; successful projection changes the words
without changing their PCs. This supplies Packet B to the normal decoder instead of its
`unknown-opcode` decline. Mixed added-opcode recovery publishes a fully canonical result only after
its subsequent expansion/anti route succeeds.

Readers need arrays, word PCs and the [Babel binding/path foundation](../../babel.md), plus
[Packet A](extract-container.md), [canonical word grammar](read-wordcode.md) and the pinned
[alias producer](../../../js-confuser-vm/transforms/aliased-opcodes.md). Input is admitted source
text (or a Babel File for the runtime observer) and its owned numeric container. Supplied
private observations are not another public model-input API. Source/AST and Packet A remain
unchanged. The input boundary is narrower than every output the encoder allocator could emit.

## 2. Algorithm

An unknown header has no safe width until the runtime proves it. Take the interpreter's
dispatch from the [handler locator](locate-handlers.md)'s view. Keep the handlers whose labels
are values of this decode's opcode table as canonical references (item 3). For each extra alias, prove that an eager operand array is read once, that a second
array is a permutation of it, and that the remaining handler restores exactly one canonical
body. Neither comments nor generated names identify the operation.

Undo that permutation while parsing the whole stream. Copy nonalias instructions unchanged;
replace each alias with its original header and canonical tail. Equal width makes this first
projection an identity address map. In a mixed stream, numeric cases first prove anti,
specialized and macro prefixes; alias proof owns only the remaining suffix. A subsequent
expansion then inserts canonical headers, and anti compaction removes fake state if present.
The final canonical parse is required before publishing any result.

### Annotated synthetic example

Supply an admitted runtime whose numeric `case 61` has these schematic bodies; this excerpt
omits the rest of Packet A and is not itself admitted source:

```text
let unsorted=[operand(),operand(),operand()];
let ordered=[unsorted[2],unsorted[0],unsorted[1]];
dst=ordered[0]; name=constant(ordered[1],ordered[2]); R[dst]=globals[name]; break;
input at PC 10: [61,7,0,4]
canonicalToStored=[2,0,1]; restored=[4,7,0]
output at PC 10: [2,4,7,0]          // LOAD_GLOBAL dst=4,index=7,key=0
```

With pool[7]=`"answer"` and an ordinary globals.answer=42, both handlers assign R4=42 and
finish at PC 14. The canonical reference instead reads dst then its constant index/key.
Replacing the explicit constant pair with a zero-argument constant call accounts for two
operand slots in the proof. Applying the stored three-cycle again would restore `[0,4,7]`;
this example distinguishes direction, unlike a swap. The canonical case is never mutated.

```mermaid
flowchart LR
  A[Admitted source / canonical cases] --> H[Prove eager bridge and unique body]
  H --> W[Parse whole mixed stream with observed widths]
  W --> P[Alias projection / same PCs]
  P --> X[Expand specialized and macro words]
  X --> C[Anti compaction or dispatcher relocation]
  C --> B[Canonical B / current owned records]
```

The last two operations are conditional, but a mixed projection cannot escape before they finish.

## 3. Implementation

### Source proof and observation contract

The [classifier](runtime-meaning.md#2-algorithm) identifies an alias: its effects unify with exactly
one canonical handler, every canonical operand slot bound to one of the alias's own reads, all of
them distinct. Whatever the prelude's spelling (two `let` arrays, one `let` with both declarators,
a single folded read array, or none when minify inlines an identity copy), the reads land in
operand slots, so `canonicalToStored[j]` is the read canonical operand j takes. A read the handler
never uses still takes its place in that order. The observer takes the added handlers of that kind
from the [identified view](runtime-meaning.md#3-implementation); labels and their order are never
read. Each leaves the dispatch (`ends`).

The canonical handlers are those the view's table names by behaviour (`partitionHandlers`); there
must be as many as table entries, and at least one added handler. Every added handler that is not
an alias must belong to the prefix observations supplied (anti, specialized, macro), whose counts
must cover it exactly. The result is `{opcode,originalOpcode,originalName,arity,canonicalToStored}`
per alias; the frozen runtime record is `jsconfuser-vm-aliased-runtime-observation.v1` with
aliases and the three prefix counts. No alias, or an unaccounted added handler, declines at
`alias-runtime`; a [handler locator](locate-handlers.md) refusal is `alias-runtime-container`.

The canonical reference bodies come from the admitted runtime itself, so this proves the
added/base handler relationship, not the canonical semantics, which source and test qualification
bound. An identically damaged base and added body cannot be certified harmless merely by matching
each other.

### Stream projection, composition and publication

| Component | Owned input -> output | Consumer fact |
|---|---|---|
| Runtime proof | Source -> alias/prefix definitions | Complete bodies determine header semantics and fixed arity. |
| Mixed reader | A + definitions -> aliased stream observation | Entire source words consumed; raw words, pc/nextPc/width retained. |
| Alias projection | Stream -> cloned A, canonical alias words | `tail[j]=stored[canonicalToStored[j]]`; width is 1+arity. |
| Expansion/compaction | Projected stream + earlier added-opcode proofs -> current A/B and optional C/D/E | Address changes and erased fake state owned by the linked inverses. |
| Publication | Successful whole route -> normalization result | No alias or other added header remains in B. |

The reader represents aliases as `SYNTHETIC` with one step; actual anti entries also use that name.
Distinguish them by opcode membership in the alias definition map. Require at least one alias
instruction (`no-alias-instructions` otherwise). Leave true anti raw tails intact.

A projected alias keeps Packet A addresses (the
[two address spaces](normalize-macro-wordcode.md#shared-expansion-and-address-relocation)). When the
caller passes originPcMap O, translate each projected alias's direct targets through O, then the
finally continuation literal of each alias the caller's `originContinuationLoads` lists (an alias
has one step, index 0). The route does not select continuation loads itself: in the projected
stream a FINALLY_SETUP can still sit inside a specialized or macro instruction, so only the PATCH
stage's whole-stream selection is complete. A target missing from O declines
`origin-target-boundary`. Canonical instructions are already current.

With prefixes, reparse projected words using macro if present, otherwise specialized, otherwise
anti definitions; use the shared expansion with `includePcMap:true` and O for the remaining added
opcodes. Anti compaction receives composePcMaps(O,E) with `allowSpecializedTail:true`; without anti
pass that map to the
[specialized dispatcher adapter](normalize-specialized-wordcode.md#dispatcher-and-anti-specialized-routes).
If no later adapter returns B, construct canonical B once on the output container.

The normalizer returns `{ok,result,diagnostic}`: success result carries cloned `container`,
current `wordcode`, optional rebuilt records, schemaVersion
`jsconfuser-vm-aliased-wordcode-normalization.v1`, originalWordCount, aliasedInstructionCount
and macroInstructionCount. Its envelope/container are not universally frozen; B is frozen.
It trusts owned prefix/stream records and never revalidates hypothetical damaged packets.
A typed failure returns result:null and the named diagnostic; unexpected errors become
`alias-normalization-error`. The transaction is the whole container route, not each alias.
Independent standalone calls retry from original source; no intermediate projection is public.

### Source-informed example control boundary

Owner checks use the retained [reference source](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/reference/encoded.js)
as supplied canonical runtime/AST infrastructure. Parse as Babel File; retain root entry 0,
main regCount=7 and all maps/methods. Replace BYTECODE with the exact example words (alias
example prepends ten DEBUGGER=57 words and appends RETURN=45,r4). Replace CONSTANTS with
[`"sentinel"`,5,7,1,0,0,0,`"answer"`]. Append numeric case 61 by deep-cloning the relevant
canonical bodies, removing top-level BreakStatement/EmptyStatement, and adding one final
break/block. Macro concatenates LOAD_INT then MOVE unchanged. Specialized LOAD_GLOBAL replaces
operand calls with 4 and supplies constant arguments 7,0. Alias LOAD_GLOBAL and anti's
LOAD_INT/ADD/BUILD_ARRAY/JUMP_IF_FALSE replace each syntactic operand call with ordered[i] and
constant calls with the next two indexed arguments; prepend the exact eager/permutation arrays
in the examples. Repeated collection-loop reads remain one syntactic slot. PATCH adds no case.
Generate this synthetic analysis source using supplied Babel, re-extract A normally, then call
the corresponding inverse; no target or encoder execution is required.

Exact expected normalized words live in each worked example. Require original A equality,
positive added-opcode recovery and current B (PATCH also C/D/E); anti flow must select index 1 and
changing its fake target 33 to 34 must yield register-isolation on a private copied A. PATCH
must recover PCs [0,5,8] and clear [1,0,7]; replacing RETURN@8 by JUMP=39,target12 must yield
source-reachable, while wrong key 2147483652 must never receive credit for the expected clear
words. Public diagnosis succeeds for the alias/anti/PATCH scaffolds. Macro and specialized
examples normalize exactly but the jump directly to RETURN gets a later
unemittable-structured-control decline. These outcomes pin the internal/public boundary;
they do not establish arbitrary emitter or host equivalence.

A separate source control parses the retained
[aliased-runtime-boot source](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/aliased-runtime-boot/encoded.js)
and adds 0.5 to every numeric index in case 61's second bridge array before Babel generation.
A and alias runtime observation still succeed; normalization returns result:null/invalid-word
(the first restored invalid word is at PC7 for this fixture). This reaches the missing integer
check directly, rather than crediting an unrelated early refusal; it establishes no positive
fractional-permutation support.

These are source-informed one-agent controls with supplied canonical reference and AST/generation
infrastructure, not cold reconstruction, retained encoder output or novice readability evidence.
The word expectations/control recipes are durable here; no ignored staging/tool path is a dependency.

### Acceptance scenarios

| Scenario | Oracle / acceptance criterion | Evidence and limit |
|---|---|---|
| A1 three-cycle and constant pair | Exact tail/value/PC above; alias header disappears, canonical case remains unchanged | Synthetic worked calculation; existing alias tests pin real fixture recovery. Whole compiler excluded. |
| A2 mixed prefixes and shuffled dispatch | Numeric ordering plus every added opcode's body proof; actual alias count>0 and canonical B | Combination tests and binding tests below; only retained profiles. |
| A3 source body/permutation damage | A still admits source; alias-runtime declines, result:null; public output absent | normalize-aliased-wordcode and analyze-anti-runtime controls; private packet tests are separately bounded. |
| A4 immutable/state contract | Original A/source unchanged; current spans/targets agree with output; fresh emitted parse has consistent state and no VM residue | Combination and identity tests; no public AST scope is returned by this pass. |

## 4. Input Shapes

[PATCH recovery](normalize-self-modifying-wordcode.md) consumes these proved added-opcode definitions
at original widths, then expands only recovered executable instructions. Its finite combined
boundary is [the PATCH census](../../tests.md#finite-patch-added-opcode-qualification); the linear
stream reader on this page still does not interpret encrypted storage.

| Earlier decoder producer / accepted spelling | Gate or handoff affected |
|---|---|
| [Handler locator](locate-handlers.md#4-input-shapes) | Supplies the dispatch, handler bodies (a table handler's frame prologue split off), reader predicates, lowering and opcode table for every runtime spelling it lists. |
| [PATCH compaction](normalize-self-modifying-wordcode.md) | Words with selfModifying's additions removed; addresses inside added opcodes are still Packet A addresses and go through its `originPcMap` ([address spaces](normalize-macro-wordcode.md#shared-expansion-and-address-relocation)). |
| [Classifier](runtime-meaning.md#2-algorithm) and the anti, specialized and macro observations | The classifier decides each added handler's kind; the observations' counts account for every non-alias one. |

The actual encoder [alias recipe](../../../js-confuser-vm/transforms/aliased-opcodes.md#4-later-stages)
explains why aliases remain canonical fixed-arity clones. It is a narrow source dependency,
not a qualification result. Earlier decoder producers own their shape inventories.

## 5. Known Gaps

Aliases whose effects unify with exactly one canonical handler are the admitted source shape.
Matching the runtime's own canonical handlers is not proof of untouched canonical semantics or
dispatch completeness. Variable tails, noncanonical bodies and other representations need
separate proof. Added-opcode PATCH recovery
has the separate [finite original-width contract](normalize-self-modifying-wordcode.md); wider
PATCH representations remain unqualified.
Minified class admission and profiles beyond the retained fixtures remain open.

## Source

The observer in item 3 is
[observe-aliased-runtime.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/observe-aliased-runtime.js),
on the classifier in [identify-handlers.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/identify-handlers.js),
with [read-wordcode.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/read-wordcode.js).
Mixed expansion/anti/dispatcher dependencies are owned by their linked item 3 recipes.

The decoder is [normalize-aliased-wordcode.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/normalize-aliased-wordcode.js),
wired by [diagnose-standalone.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/diagnose-standalone.js)
under the dependencies described in item 4.

The pinned encoder's [bytecode alias pass](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/transforms/bytecode/aliasedOpcodes.ts)
chooses free opcode slots and permutes stored operands. Its
[runtime alias pass](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/transforms/runtime/aliasedOpcodes.ts)
appends the corresponding dispatch cases.

## Fixtures

The scenario tables in item 3 state acceptance oracles; rows below index retained inputs/tests.
The annotated examples are source-informed synthetic controls, not independent cold proofs.
Fixture qualification records and the [shared provenance contract](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/qualification-provenance.md)
bound historical generated evidence; no fresh encoder generation or wider profile qualification
is asserted by this specification. Private copied-packet controls establish internal choices
only; source mutations that still reach A/B pin normal-entry refusals separately.

### Independent bounded proof

The retired frozen verifier retained exact synthetic inputs, expected words/maps/spans, controls and the pre-source freeze.
One experienced agent reconstructed selected mechanics from the ten candidate pages plus Babel
and B prerequisites, using supplied Node/assert/Babel infrastructure and no production imports.
The tested consumed state is ordered raw words, spans, widths and nextPc, not full register-value,
C/D/E, scope-cache or emitted-program state. The recovery assertions fail passthrough.

Alias proof covers the declared three-slot LOAD_GLOBAL bridge, inverse three-cycle and selected
body/capture/repeated-index refusals. Its source is a function with a supplied labeled-break marker
removed by the scaffold, not an admitted numeric switch case. Binding projection covers declared
identifier/variable/function-parameter spellings and capture/read/write/shadow controls; it does
not cover destructuring, catches/rest, repeated var or complete clone-origin handling. Supplied A,
role names and canonical inventory are not reconstructed. Numeric labels, full case-ending syntax,
class layouts, prefix allocation, source admission and whole runtime semantics remain source-audit
or qualification dependencies.

The proof's single guessed anti-prefix diagnostic equality is
[quarantined](normalize-anti-wordcode.md#fixtures); its selected changed words/maps/spans remain
credited under their declared scope. Owner source-informed scaffolds and retained-input test runs
are separate evidence. This is neither a whole-frontend reconstruction nor generated-output,
public-admission, option-stack or novice-readability qualification. The frozen executable and the
report's frozen metadata/stdout section remain unchanged after reference consultation; the report's
post-freeze audit and verdict sections remain appendable.

| Committed fixture or test control | Claim pinned |
|---|---|
| [aliased-runtime-boot](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/aliased-runtime-boot/encoded.js) and its [qualification record](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/aliased-runtime-boot/qualification.json) | Alias opcode and operand permutation in a simple numeric program. |
| [aliased-runtime-closures](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/aliased-runtime-closures/encoded.js) and its [qualification record](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/aliased-runtime-closures/qualification.json) | Nested closures retain the same alias relationship. |
| [aliased-runtime-exceptions](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/aliased-runtime-exceptions/encoded.js) and its [qualification record](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/aliased-runtime-exceptions/qualification.json) | Exception control includes a permuted `FINALLY_SETUP` alias. |
| [normalize-aliased-wordcode.test.js](../../../../decoder/decode-js/test/vm/jsconfuser-vm/normalize-aliased-wordcode.test.js) | Parse-only proof, full-stream normalization, source/encoded/decoded behavior, no VM residue, derived-state consistency and changed-handler decline. |
| [macro-alias-exceptions](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/macro-alias-exceptions/encoded.js) and its [qualification record](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/macro-alias-exceptions/qualification.json) | Width-preserving alias projection precedes macro expansion through exception/finally control. |
| [anti-alias-exceptions](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/anti-alias-exceptions/encoded.js) and its [qualification record](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/anti-alias-exceptions/qualification.json) | A one-step alias handler remains outside the anti synthetic prefix. Both option effects and decoded behavior are observed. |
| [eight-option-alias-exceptions](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/eight-option-alias-exceptions/encoded.js) and its [qualification record](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/eight-option-alias-exceptions/qualification.json) | The retained option stack composes with matching exception behavior. |
| [normalize-alias-combinations.test.js](../../../../decoder/decode-js/test/vm/jsconfuser-vm/normalize-alias-combinations.test.js) | Mixed prefix proof, original-container immutability, behavior and derived-state agreement, and changed macro/alias atomic decline. |
| [runtime-layers](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/runtime-layers/generation.json) minify-aliased | Minify's merged, folded and prelude-free aliases and a final case without `break` are proved and decode to source behaviour. |
| [shuffled-alias-stack-exceptions](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/shuffled-alias-stack-exceptions/encoded.js) and its [qualification record](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/shuffled-alias-stack-exceptions/qualification.json) | A physically permuted switch still decodes through the retained alias stack. |
| [runtime-binding-identities.test.js](../../../../decoder/decode-js/test/vm/jsconfuser-vm/runtime-binding-identities.test.js) | Complete combined class/handler/alias stacks decode after independent lexical renaming; fragment controls preserve captured reads, writes and shadow topology. |
