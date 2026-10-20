# Normalize VM dispatcher routes

## 1. Target

Replace proved encoded-PC routes with ordinary direct branches, then remove their per-function
decode closures and terminal dispatcher blocks. Passthrough retains the key/selector machinery
and a JUMP_REG whose targets Packet E cannot ordinarily prove. Successful recovery publishes
copied A and current B/C/D, plus E unless an explicit preparation mode defers that graph.

The implemented adapter consumes owned [A](extract-container.md), [B](read-wordcode.md) and
[D](partition-functions.md). D already derives from current C and supplies function ownership,
creation metadata and instruction PCs. It statically interprets a closed arithmetic subset;
it never executes the target closure or arbitrary JavaScript. Readers need registers, branches,
function frames, JavaScript truthiness/bitwise coercion and the linked packet contracts.

## 2. Algorithm

A candidate owner begins by creating a decode closure and ends in JUMP_REG. Connect that hoist to
its child descriptor and the terminal CALL; prove the optional result-container extraction and
ordered key arguments. Scan each direct jump to that CALL backwards through its complete route.
Otherwise a nearby key load or arithmetic fragment could belong to application code.

Evaluate the helper with each route's encoded endpoint and key arguments. Direct routes recover
one destination. A branchless route has two endpoints: !condition selects the second when falsy.
Exactly one decoded endpoint must be the route's next PC; the other is the taken target. Recover
the corresponding JUMP_IF_FALSE/TRUE, or one JUMP when both endpoints agree. Prove targets stay
inside the owner body and retained payload cannot observe any erased scratch/closure register.

Plan all replacements and deletions together. Replace only route starts, remove the remaining
route instructions, hoist, dispatcher and helper body, then map surviving instruction starts to
new word PCs. Translate all direct references and the selected finally continuation loads.
Rebuild current records from copied A before publishing. Functions without candidate plans carry
through, subject to the whole rebuilt stream's normal packet admission.

```mermaid
flowchart LR
  D[Current B / D ownership] --> O[Hoist / tail / route proof]
  O --> V[Static endpoint evaluation]
  V --> X[Direct edge / erased-state proof]
  X --> M[Removal map / target relocation]
  M --> R[Copied A / rebuilt B-C-D / optional E]
```

### Synthetic direct route with exact PCs

This source-informed private scaffold has root regCount 5, mainStartPc 0, pool `[undefined]`,
one zero-capture, nonrest helper with two parameters/regCount 5, and these canonical instructions.
The [B grammar](read-wordcode.md#operand-grammar) supplies every serialized width.

```text
0  MAKE_CLOSURE r3,28,2,5,0,0   # seven words; helper entry 28
7  LOAD_INT r0,42               # retained payload
10 LOAD_INT r1,105              # encoded endpoint 18 XOR 123
13 LOAD_INT r2,123              # nonzero site key
16 JUMP 20                     # route enters terminal CALL
18 RETURN r0                   # explicit terminator before dispatcher
20 CALL r1,r3,2,r1,r2           # reads args before writing r1
26 JUMP_REG r1
28 LOAD_THIS r4                # helper; receiver is not used
30 BXOR r2,r0,r1
34 LOAD_INT r3,0
37 BOR r2,r2,r3                # signed bitwise coercion, result remains 18
41 RETURN r2
43 LOAD_CONST r4,0,0           # exact dead undefined-return suffix
47 RETURN r4                   # old wordCount 49
```

The evaluator starts helper registers r0=105,r1=123 and obtains 18. Removing the hoist and
helper/tail leaves the payload, route replacement and RETURN. Map entries are
`0->0,7->0,10->3,18->5,49->7`; other removed starts have no entry. New JUMP target is map(18)=5.
Output words are `[1,0,42,39,5,45,0]`; current D has only root and current E is complete.
Changing word 15 (key 123) to 122 decodes 19, which is not an instruction start, and reaches
dispatcher-target, "Decoded target leaves the original body". This helper is an admitted
synthetic evaluator input, not a newly generated scheme or a full source/public admission proof.

## 3. Implementation

### Components and candidate boundaries

| Component | Consumes -> produces | Consequential contract |
|---|---|---|
| Owner/closure binder | Current D and B -> hoist, child, tail | Ownership/creation relationship connects the decoder. |
| Route observer | Owner instructions/tail -> complete route spans | No overlapping consumed starts; key and selector grammar is closed. |
| Arithmetic evaluator | Child instructions/metadata/pool/args -> result | Only listed operations and exact dead-return suffix; no target execution. |
| Escape proof | Erased PCs/registers plus retained operands -> accepted plan | Neither payload nor retained condition observes deleted state. |
| Relocator/rebuilder | All plans/current A-D -> copied A/current records | Map and allowed shared entries describe changed word PCs. |

**PATCH suspects.** partitionOptions may carry `suspects`: undecided selfModifying fillers as
Packet A PCs, read in this input through decodedTargetMap (identity without one). selfModifying
plants them after a terminator, so this stage reads past them exactly where it relies on what
follows a terminator: the instruction before the CALL block, the closure's RETURN suffix, a route's
skip label, and the two dispatcher-register scans (the closure-register census and the
erased-state proof). Route grammar matches over every instruction: a label the encoded endpoints
hid can sit on a suspect that starts a route. Continuation-literal selection skips suspects (a
suspect load keeps its Packet A word). Suspects stay in the output unchanged; the
[settle](normalize-self-modifying-wordcode.md#settling-suspects) decides them afterwards.

For each D function, obtain instructions in instructionPcs order. Skip a function unless its first
instruction is MAKE_CLOSURE and its last is JUMP_REG. A candidate hoist has captureCount/rest
words 5/6 both zero. Its target entry must identify a child whose descriptor.creationPc equals
the hoist PC and paramCount equals hoist word 3. Candidate shape failure aborts the observer;
it does not silently skip that malformed candidate. No plans declines no-dispatcher.

The terminal JUMP_REG's word 1 is disp. In forward order the tail is CALL, optionally followed by
LOAD_INT 0 or zero-key LOAD_CONST string then GET_PROP disp,disp,keyRegister, and finally JUMP_REG.
The optional load/GET_PROP pair is between CALL and JUMP_REG. Unwrap load's
destination equals GET_PROP key register; array mode is only integer zero, object mode records
the literal string. CALL destination is disp, callee is hoist destination, count equals child
paramCount and is 2 or 3, raw length is count+4. Two arguments contain disp exactly once; the
other is the key register, allowing either order. Three arguments are disp,keyLo,keyHi with
three distinct registers. The last non-suspect instruction before the CALL block must be RETURN,
THROW, JUMP or JUMP_REG, proving no physical fallthrough into that block.

Outside hoist/CALL, the closure register may not occur in B's `wordOperands` tagged register
census. This historical tag view has [B's FOR_IN_NEXT limit](read-wordcode.md#5-known-gaps);
the later erased-state proof uses semantic operands/captures instead. Across all functions the
child body has exactly one MAKE_CLOSURE creation, at this hoist, and planned child IDs are distinct.

### Route grammar and endpoint choice

Only JUMP directly targeting tail.call.pc opens routeAt. Read immediately preceding LOAD_INT key
loads backwards in reverse tail key-register order; restore forward argument order. One key is its
full u32 word. Split key is `(lo | (hi<<16))>>>0`, both halves <=65535. Zero combined key or an
oversized half declines dispatcher-key. Each site's literal key arguments are passed in the tail's
observed parameter order; the evaluator determines whether the closure uses them correctly.

A LOAD_INT into disp before the keys is a direct route. Otherwise require this complete adjacent
sequence before the key loads and JUMP:

```text
UNARY_NOT test,condition
UNARY_POS test,test
[UNARY_NEG test,test]                 # required only for BAND
LOAD_INT disp,baseEncoded
LOAD_INT delta,otherEncoded
SUB delta,delta,disp
MUL-or-BAND delta,delta,test          # either input order allowed; other input != delta
ADD disp,disp,delta
```

The optional negation turns 0/1 into 0/-1 for masking. The stored endpoint literals are evaluated
separately rather than evaluating arbitrary payload truthiness. Array/object results must have
the observed mode and, for object, the exact key; unwrap their value. Require integer 0..0xffffffff
or decline dispatcher-target. If supplied decodedTargetMap exists, that decoded original PC must
be present; translate it before current-boundary/owner checks. A missing entry declines
dispatcher-target, "Decoded target has no anti PC boundary"; the wording also covers expansion
maps supplied by earlier producers.

Let b/o be the translated base/other targets. A target is the skip edge when it is the route JUMP's
nextPc, a suspect between that and the first non-suspect after the JUMP, or that first
non-suspect. If b==o emit JUMP b. Otherwise require exactly one skip edge. If b is it emit
JUMP_IF_FALSE condition,o; if o is it emit JUMP_IF_TRUE condition,b. The rewritten branch reaches
the skip label by fallthrough, so the route records its decoded Packet A value (`skipOrigin`)
and the result publishes them as `skipLabels` for the settle. Neither or both skip matches decline dispatcher-target. Every
target must be a current B start owned by the candidate owner and precede tail.call.pc; a
conditional endPc must also be a B start. Routes' oldPcs may not overlap. A direct/conditional
reference into a consumed interior cannot be remapped later merely because its number is in range.

### Closed static evaluator

Initialize descriptor.regCount slots to undefined; copy args to slots 0 onward. Require no
captures/rest, paramCount==args.length and regCount>=args.length. Every read/write register
must be integer and in frame. The receiver and recognized Math/imul values are private symbols,
not host objects extracted from target code. The interpreter walks instructions once in order;
no branch, loop, arbitrary property access or general CALL is accepted.

| Operation | Exact evaluation / refusal boundary |
|---|---|
| LOAD_THIS / MOVE / LOAD_INT | Receiver symbol; copy slot value; immediate word. |
| LOAD_CONST | Key zero and index<pool.length; load actual pool value. |
| LOAD_GLOBAL | Key zero and pool value exactly "Math"; produce Math symbol. |
| GET_PROP | Object is Math symbol and key slot exactly "imul"; produce imul symbol. |
| CALL_METHOD | Receiver Math, method imul, count 2/raw length 7; actual Math.imul on finite numeric arguments. |
| UNARY_BITNOT | `~x` after finite-number check. |
| ADD / SUB | Number x+y / x-y after finite-number checks. |
| BOR / BXOR / SHL / USHR | JavaScript x\|y / x^y / x<<y / x>>>y after finite-number checks; source imposes no extra shift-count range. |
| BUILD_ARRAY | Count 1/raw length 4; private `{kind:"array",value:slot}`. |
| BUILD_OBJECT | Count 1/raw length 5, string key slot; private `{kind:"object",key,value}`. |
| RETURN | Read result; require the remaining non-suspect instructions to be exactly LOAD_CONST(key zero,pool value undefined), RETURN of that load's destination. |

A numeric operand is typeof number and Number.isFinite, otherwise dispatcher-decode. Stored
intermediate results follow ordinary JS arithmetic; a later numeric read or final target check
can refuse them. Missing RETURN/unsupported operation/frame/constant/global/property/method/
container/tail metadata uses dispatcher-closure. A RETURN without the two-instruction suffix is
not admitted by this evaluator, even if semantically equivalent. This rule is distinct from the
string helper's optional suffix choice. Host standard Math.imul is an explicit infrastructure
assumption; monkey-patched host semantics are not qualified.

### Erased-state proof and relocation

Erased PCs include hoist, terminal block and every route span. Erased registers start with closure,
disp and key registers, then include word 1 destinations of erased instructions except JUMP/JUMP_REG.
A retained conditional's condition cannot be in that set. For each retained owner instruction,
reject semantic register operands or local capture indexes in that set (dispatcher-shape).
This includes writes as well as reads. Helper deletion cannot preserve a final scratch value merely
because application code only uses it later.

Across all plans remove hoists, tail blocks and complete child instruction lists. Route starts
emit direct branch words; their other PCs are consumed. Refuse route/removed overlap. In original
B order, map each retained start/route start to next new PC. Removed hoist entries also map there,
so an owning function entry survives. Other removed/consumed starts do not. Map old wordCount to
new end. Replacements use canonical opcodes and widths 2/3; retained raw words are copied.

Translate offsets JUMP:1; JUMP_IF_FALSE/TRUE:2; FOR_IN_NEXT:3; TRY_SETUP:1; FINALLY_SETUP:1,4;
MAKE_CLOSURE:2. Missing map entries decline dispatcher-target-boundary. Remap the finally
continuation literals the [shared continuation rule](normalize-macro-wordcode.md#shared-expansion-and-address-relocation) selects, functions from the original D owners.

Clone A and install words. Require B, C, D on the clone; their typed diagnostics propagate.
If partitionOptions was supplied, rebuild only `{allowSharedParentStarts:new Set(remapped entries)}`
for D. Supplied nonempty option objects therefore owe that Set; no invented malformed-record
contract is added. decodedTargetMap is input-only; the stage returns its own removal map as
`pcMap` (input PC -> output PC, surviving starts and hoists only) for the caller to compose.
With partitionOptions.deferControlFlow truthy return cfg:null; otherwise require E. Deferred
success is valid preparation, not complete control admission.

### Result, atomicity and acceptance

Result schema jsconfuser-vm-dispatcher-normalization.v1 contains container, wordcode, references,
functions, cfg, pcMap, originalWordCount, normalizedWordCount, routeCount, decoderClosureCount and skipLabels.
Counts concern all accepted plans, not every function in the input. Envelope/copied A are not
deeply frozen here; rebuilt B-E are owned frozen records. Source/A/predecessors remain unchanged.
Typed DispatcherDecline codes above propagate; unexpected errors become dispatcher-observation-error
in the observer or dispatcher-normalization-error in the adapter. Both return no partial result.

Atomicity covers the complete set of matched owners and decoder children: a later failure discards
all plans. Unmatched functions carry through; residual indirect/finally instructions are allowed
only as the final required E proves them, or remain for the explicit deferred caller. No source
helper is incrementally deleted; standalone emission later replaces the entire VM.

| Scenario | Oracle / acceptance | Evidence boundary |
|---|---|---|
| D1 route/evaluation | Exact endpoints/condition/opcode/current B-D-E; words/maps differ from passthrough | Synthetic example and retained direct/branchless/array/object/split tests. |
| D2 source-written damage | Changed helper global or key reaches dispatcher-closure/target; public cfg-declined | Retained tests write changed words back into source before entry. |
| D3 erased uses | Payload/key/selector/retained-condition use reaches named dispatcher-shape; no result | Retained source controls; local-capture and historical-tag edge controls missing. |
| D4 maps/preparation | Original decoded PC translated, shared entries remapped, cfg:null only when requested | Earlier added-opcode and string-combination producers/tests; no universal map composition claim. |
| D5 current state/atomicity | Re-read B/C/D/E; unchanged predecessors, fewer words, no public residue/fresh AST consistency | Retained tests; unmatched-function partial carry-through is source-derived, no dedicated mixed-candidate control. |

## 4. Input Shapes

[Current added-opcode/PATCH B](read-wordcode.md#4-input-shapes) and
[restored constants](normalize-concealed-constants.md) supply widths, values and zero keys.
The [shared-parent exception](partition-functions.md#preliminary-shared-helper-exception) allows
only specified temporary helper entries; this normalizer relocates that Set before rebuilding D.
Decoded endpoints are Packet A PCs ([address identity](normalize-macro-wordcode.md#shared-expansion-and-address-relocation)).
A route that runs this stage inside itself passes its composed map; otherwise the
[schedule](standalone-diagnosis.md#canonical-frontend-retries) passes its origin map whenever an
earlier stage moved code. Consume the map as supplied; this stage's deletion map is a different
operation, returned as `pcMap`.

[Diagnosis](standalone-diagnosis.md#canonical-frontend-retries) uses deferred E for string preparation
and before [CFF](normalize-cff-wordcode.md). Success adopts the complete returned record set. An
optional decline leaves that caller's current stream intact; it may later fail E as cfg-declined
rather than exposing this private observer diagnostic. String-prefix recovery remains mandatory
once its coordinator gate opens. Representations are owned by [A's adapters](extract-container.md#4-input-shapes).
The [pinned dispatcher producer](../../../js-confuser-vm/transforms/encoded-branch-dispatch.md)
explains encoded final-PC literals, modes and CFF-before-dispatcher ordering; these references do
not add generated/option qualification.

## 5. Known Gaps

The evaluator accepts only its closed instruction subset and exact suffix. Modified Math.imul,
arbitrary helper side effects or equivalent unrecognized decoders are outside the contract.
The compatibility-tag closure census and temporary shared-helper
ownership have the limits stated above. Changed source controls pin selected errors, not every
private refusal. Wider option stacks, added-opcode PATCH, minified-class entry and complete
host/front-end qualification remain open. Historical fixture provenance bounds regeneration;
owner examples are not independent cold reconstruction or novice evidence.

## Source

The decoder is [normalize-dispatcher-wordcode.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/normalize-dispatcher-wordcode.js),
using [route observation and the static evaluator](../../../../decoder/decode-js/src/vm/jsconfuser-vm/observe-dispatcher-wordcode.js).
It is
wired by [diagnose-standalone.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/diagnose-standalone.js)
under the dependencies described in item 4.

The pinned encoder's [dispatcher bytecode pass](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/transforms/bytecode/dispatcher.ts)
defines the route, closure and result variants. The [compiler pass list](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/compiler.ts)
places it before register and label resolution, as item 4 accounts for.

## Fixtures

The retired frozen verifier reconstructed
selected finite arithmetic, a direct route/removal map, one branchless MUL route choice and
original-PC translation from supplied root/helper metadata and canonical words. Exact changed
words/maps and erased-register refusal fail passthrough. Separate array/object evaluator controls
check container values, not integrated CALL/load/GET_PROP/JUMP_REG tail recognition. Split-key,
Math.imul binding, BAND integrated routes, local captures and full D/E rebuilding were excluded
or supplied; the XOR-only scaffold also omits mandatory ingredients of generated producer schemes.
This selected reconstruction does not qualify generated routes, public admission or full helper/frame
records. The frozen executable and the report's frozen metadata/stdout section stay unchanged;
postfreeze audit/verdict sections remain appendable. Owner checks and retained regressions below
provide separate evidence.

D1-D5 above specify recovery, current state and the reached refusal boundaries. The owner item 2
control clones A from the retained [reference](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/reference/encoded.js),
installs the listed instructions using B's canonical opcodes/widths, pool `[undefined]` and
MAIN_REG_COUNT=5, retains mainStartPc=0 and all other roles, then builds B/C/D and invokes the
normalizer. Exact seven-word output, complete cfg and unchanged supplied A/B/D are asserted;
returned B/C/D/E equal fresh reads/rebuilds from their owned builders for that output. Current B starts are
0/3/5 with widths 3/2/2, D contains root [0,7) only with regCount 5, and E progresses 0->3->5->exit.
The word-15 key control reaches the named dispatcher-target. Maps are source-derived internal
decisions, not published Map fields. This is private source-informed scaffolding, not newly
generated or public source admission, independent cold evidence or full helper/frame reconstruction.
The [historical provenance contract](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/qualification-provenance.md)
bounds the retained records below. Source-written observer controls establish their selected
internal/public diagnostics without qualifying every erased-register or helper variant.

| Committed fixture or test control | Claim pinned |
|---|---|
| [dispatcher-branches](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/dispatcher-branches/encoded.js) and its [qualification record](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/dispatcher-branches/qualification.json) | Branchless masking and direct routes recover target boundaries. |
| [dispatcher-array-result](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/dispatcher-array-result/encoded.js) and its [qualification record](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/dispatcher-array-result/qualification.json) | Array return mode unwraps the decoded PC. |
| [dispatcher-split-key](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/dispatcher-split-key/encoded.js) and its [qualification record](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/dispatcher-split-key/qualification.json) | Two u16 key halves recombine through the decode closure. |
| [dispatcher-object-result](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/dispatcher-object-result/encoded.js) and its [qualification record](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/dispatcher-object-result/qualification.json) | Object return mode unwraps a generated property. |
| [dispatcher-switch](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/dispatcher-switch/encoded.js) and its [qualification record](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/dispatcher-switch/qualification.json) | Multiple routed cases preserve switch behavior. |
| [dispatcher-finally](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/dispatcher-finally/encoded.js) and its [qualification record](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/dispatcher-finally/qualification.json) | Finally continuation jumps remain distinct from the dispatcher jump. |
| [dispatcher-exceptions](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/dispatcher-exceptions/encoded.js) and its [qualification record](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/dispatcher-exceptions/qualification.json) | Exception handler stack joins survive route recovery. |
| [cff-dispatcher-try-finally](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/cff-dispatcher-try-finally/encoded.js) and its [qualification record](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/cff-dispatcher-try-finally/qualification.json) | Dispatcher routes are inverted before CFF while a finalizer continuation is preserved. |
| [dispatcher-anti-instrumentation-switch](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/dispatcher-anti-instrumentation-switch/encoded.js) and its [qualification record](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/dispatcher-anti-instrumentation-switch/qualification.json) | Anti compaction maps old decoded route PCs to compact boundaries. |
| [string-cff-dispatcher-concealed-constants-anti-instrumentation-exceptions](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/string-cff-dispatcher-concealed-constants-anti-instrumentation-exceptions/encoded.js) and its [qualification record](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/string-cff-dispatcher-concealed-constants-anti-instrumentation-exceptions/qualification.json) | The full qualified stack preserves exception routes. |
| [string-cff-dispatcher-concealed-constants-specialized-arithmetic](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/string-cff-dispatcher-concealed-constants-specialized-arithmetic/encoded.js) and its [qualification record](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/string-cff-dispatcher-concealed-constants-specialized-arithmetic/qualification.json) | Specialized expansion maps old dispatcher targets before string/CFF inversion. |
| [string-cff-dispatcher-concealed-constants-anti-specialized-exceptions](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/string-cff-dispatcher-concealed-constants-anti-specialized-exceptions/encoded.js) and its [qualification record](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/string-cff-dispatcher-concealed-constants-anti-specialized-exceptions/qualification.json) | The original-to-expanded and expanded-to-compact maps preserve exception routes. |
| [normalize-dispatcher-wordcode.test.js](../../../../decoder/decode-js/test/vm/jsconfuser-vm/normalize-dispatcher-wordcode.test.js) | Complete proof, immutable Packet A, rebuilt CFG, matching source/encoded/decoded behavior, no VM residue, derived state, and atomic declines for changed closure globals and keys, plus source-text controls for payload uses of erased state, key and selector registers and retained conditions using erased state. |
