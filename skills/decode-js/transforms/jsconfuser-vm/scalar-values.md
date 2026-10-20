# Analyze scalar operations

## 1. Target

Recover typed scalar leaves, local use/definition facts and literal knowledge from canonical
wordcode. `analyzeScalarValues(B,C,D,E)` returns deeply frozen
`jsconfuser-vm-scalar-values.v1` (I) or null; `diagnoseScalarValues` returns frozen
`{ok,result,diagnostic}`. Success produces one row per **I-family** instruction, including
unreachable rows. It does not produce a row for every B instruction or interpret register values.

Readers need JavaScript operators/values, registers and graph reachability, plus
[B's grouped semantic operands](read-wordcode.md), [C pool references](validate-references.md),
[D owners](partition-functions.md) and [E edges](build-cfg.md). The encoder's
[scalar/coercion contract](../../../js-confuser-vm/instruction-set.md#loads-stores-scalar-operations-and-coercion)
explains runtime meaning. Words/indexes are u32; register **values** remain JavaScript values.
PC/width/nextPc units are words; function IDs come from D.

`diagnoseScalarValues` exposes detailed stage diagnostics. `analyzeScalarValues` returns only the
result or null, discarding those details. Standalone reconstruct uses that wrapper and reports
`scalar-values-declined` on null; the plugin preserves this generic standalone diagnostic.

## 2. Algorithm

Separate operation shape from value knowledge. Index C constants and D ownership, traverse E
from every function entry to tag reachability, then walk B's instruction order. For each supported
scalar name project its destination, ordered register inputs, constant/global reference and
operation descriptor. Keep only directly available literal facts: LOAD_CONST's copied pool value,
LOAD_INT's immediate, and VOID's undefined result. MOVE records a copy edge, not a known value.

Known peer operations are skipped and reported as boundary omissions, allowing I and
[J](property-collections.md) to coexist on one stream. An unknown name outside the closed canonical
inventory declines. Check the constructed I census for unique functionId:pc keys and complete
coverage of the I subset, then publish the whole immutable result. No operation evaluates user
code or propagates values across moves/branches/merges.

### Worked example: coercion meaning without constant folding

This **synthetic canonical stream** supplies root regCount=5 and pool `["2","out"]`:

| PC | Words | I row/oracle |
|---:|---|---|
| 0 | `[1,0,4294967295]` | scalar:0:0, LOAD_INT known-integer 4294967295. |
| 3 | `[0,1,0,0]` | LOAD_CONST r1, constant0/key0, known-constant "2". |
| 7 | `[11,2,0,1]` | ADD inputs r0/r1, destination r2, dynamic-operation/add, known=false. |
| 11 | `[33,3,1]` | UNARY_POS r3,r1, unary-positive/number, known=false. |
| 14 | `[37,4,2]` | VOID defines r4 as known-undefined; structural use of r2. |
| 17 | `[6,1,0,2]` | STORE_GLOBAL constant1/key0, input r2; destination/defines null. |
| 21 | `[45,4]` | RETURN is a peer completion row and is skipped by I. |

B wordCount=23; I emits six rows, all reachable, with unchanged B-E. Literal 4294967295 is
unsigned and does not become -1. Under the pinned native operators, `4294967295 + "2"` is
"42949672952" and unary `+"2"` is 2, but I deliberately leaves both computed rows dynamic.
Replacing only ADD at PC7 with SUB preserves shape/inputs while changing operation from add to
subtract; the native result would be 4294967293, still not a constant fact in I. RETURN contributes
no extra scalar row in either control. This is a source-informed private-A/record example, not
actual generated output or source admission; no coercion/host execution is performed by I.

## 3. Implementation

### Components and operation inventory

| Component | Input -> output | Required decision |
|---|---|---|
| Owner/reachability index | D ownership + per-function E edges -> owner/reachable keys | BFS from each entry over non-null edges, including exceptional ones. |
| Constant projector | C references/values + B semantic offsets -> constant/global facts | Join pc/name/semantic operand offset; no name-text guessing. |
| Scalar projector | B instruction + row definition -> operation | Exact destination/input selection and valueSemantics below. |
| Census/publisher | Constructed subset -> frozen I | No dropped/duplicate I row; inputs untouched. |

Canonical opcode values/forms/widths are [B-owned](read-wordcode.md#operand-grammar). Use semantic
operand offsets after constant-pair grouping, not raw-word offsets. The I inventory and descriptor
operation/resultType are:

| Names | Family | Descriptor operation(s), same order | Descriptor resultType |
|---|---|---|---|
| LOAD_CONST / LOAD_INT / LOAD_GLOBAL | load | load-constant / load-integer / load-global | constant / integer / dynamic |
| MOVE | move | move | copy |
| STORE_GLOBAL | global-mutation | store-global | input (valueSemantics reports no-register-result) |
| ADD / SUB / MUL / DIV / MOD / EXP | arithmetic | add / subtract / multiply / divide / modulo / exponentiate | dynamic |
| BAND / BOR / BXOR / SHL / SHR / USHR | bitwise | bitwise-and / bitwise-or / bitwise-xor / shift-left / shift-right / unsigned-shift-right | number |
| LT / GT / LTE / GTE | relational | less-than / greater-than / less-than-or-equal / greater-than-or-equal | boolean |
| EQ / NEQ / LOOSE_EQ / LOOSE_NEQ | equality | strict-equal / strict-not-equal / loose-equal / loose-not-equal | boolean |
| UNARY_NEG / UNARY_POS / UNARY_NOT / UNARY_BITNOT | unary | unary-negate / unary-positive / logical-not / bitwise-not | number / number / boolean / number |
| TYPEOF / VOID / TYPEOF_SAFE | conversion | typeof / void / typeof-safe-global | string / undefined / string |

### Operand meaning and runtime effects

Every I row except STORE_GLOBAL defines register(words[1]). LOAD_CONST/INT/GLOBAL use no
register input; STORE_GLOBAL uses semantic operand1; binary rows use operands1/2; MOVE, unary,
TYPEOF and VOID use operand1; TYPEOF_SAFE uses no register input. STORE_GLOBAL has no local
destination despite a leading constant index in raw word1. Typed operand arrays preserve B order.

For LOAD_CONST/GLOBAL/TYPEOF_SAFE join C.constants.references at operand1; for STORE_GLOBAL use
operand0. Preserve `{kind:constant,index,concealKey,value:C.values[index]}`. Global rows also
carry `{kind:global,name:constant.value,constant}`; C already proved string global names and
key zero. LOAD_INT takes operands[1].value and records immediate={kind:uint32,value}; no signed
coercion or PC reinterpretation occurs here.

Runtime binary inputs are read left then right before the destination is written, so a destination
alias does not overwrite an input early. ADD uses native + (numeric addition or concatenation);
SUB/MUL/DIV/MOD use native subtraction, multiplication, division and remainder, EXP uses **Math.pow(a,b)**, not a blanket u32 or BigInt
exponent rule. Native arithmetic/relation/equality coercion can throw and is not simulated.
BAND/BOR/BXOR use native bitwise operators; shifts use native <<, >>, >>>, with their 32-bit
numeric conversions and masked shift distance. LT/GT/LTE/GTE use native comparisons; EQ/NEQ
are ===/!==, LOOSE_EQ/NEQ are ==/!=. UNARY_NEG/POS/NOT/BITNOT use native negation, unary plus, logical not and bitwise not; TYPEOF uses
`typeof R[src]`. VOID's runtime consumes the source **index** and writes undefined without
reading the register, although I records that structural source as a use. These descriptor
resultType labels describe the row inventory, not a proof that all dynamic JavaScript inputs
have that type (for example native operators may encounter BigInt or throw).

LOAD_GLOBAL first tests `name in globals`, throws ReferenceError if absent, then reads the
property; inherited names therefore participate. STORE_GLOBAL assigns globals[name]=R[src].
TYPEOF_SAFE instead uses Object.prototype.hasOwnProperty.call(globals,name), reads only an own
property or undefined, then typeof; absence does not cause ReferenceError, but a getter/proxy
may still throw. Global reads/writes and their runtime outcomes remain unknown in I.

Every valueSemantics object has kind/operation/resultType/known with these exact variants:

| Instruction | kind | operation | resultType | known | Additional fields |
|---|---|---|---|---|---|
| LOAD_CONST | known-constant | load-constant | constant | true | value=constant.value |
| LOAD_INT | known-integer | load-integer | integer | true | value=unsigned immediate |
| MOVE | register-copy | move | copy | false | sourceRegister=inputs[0] register object |
| STORE_GLOBAL | input-value | store-global | no-register-result | false | sourceRegister=inputs[0] register object |
| VOID | known-undefined | void | undefined | true | None; value is absent. |
| Every other I row | dynamic-operation | definition.operation | definition.resultType | false | None. |

Only LOAD_CONST/INT carry value; only MOVE/STORE_GLOBAL carry sourceRegister. These conditional
keys are absent elsewhere, not null. Dynamic rows remain unknown even if earlier loads appear
to make their inputs obvious. No CFG value-state lattice or SSA is introduced.

### Output, partial boundary and refusal

Each row has id=`scalar:functionId:pc`, functionId/pc/reachable, opcode={name,value}, name/family,
operands, copied words/width/nextPc, destination, inputs, constantReference/globalReference or null,
immediate or null, useDef, effect and valueSemantics. useDef contains uses/defines/globalReads/
globalWrites; reads apply to LOAD_GLOBAL/TYPEOF_SAFE, writes to STORE_GLOBAL. effect contains
kind=register-write|global-read|global-write, register=destination-or-null, global=reference-or-null.

I contains schemaVersion/encoding/api, parseOnly=true/targetExecution=false, total word/instruction/
function counts, opcodeScope={family:I-scalar-value,count,names,rows}, operations/operationCount,
functionCensus, census, reachability, valueState, predecessorSchemas, boundaryOmissions, proof and
inputs. Definition rows expose name/opcode/family/operandForm/operation/effect/resultType/known/count;
only LOAD_CONST/INT/VOID definitions have known=true. Per-function census carries functionId,
startPc/endPc/instructionCount/scalarOperationCount/reachableScalarOperationCount/
unreachableScalarOperationCount. Census carries expectedInstructionCount (I subset), operationCount,
countsByName, ordered operationKeys, dropped=[]/duplicated=[]/complete=true. Row counts must sum to
operationCount. valueState reports dataflow=not-introduced and mergeAgreement=not-applicable.

predecessorSchemas names B/C/D/E schemas; inputs reports word/instruction/pool/function/edge/block
counts. proof reports generated row presence/uniqueness and noTargetCodeExecuted=true, not a
source-admission proof. The partial boundary is an **operation-family projection**, not partial
rewrite: known canonical peer names (upvalues/THIS/J/K/L/M/H/PATCH/DEBUGGER) are skipped and listed
in boundaryOmissions, a complete grouped static peer inventory, not only encountered names.
PATCH remains unsupported by ordinary B unless earlier recovery normalizes
it; its omission here does not admit it. A stream with no I-family instructions succeeds with
empty operations.

Unknown names -> unsupported-opcode; duplicate keys -> duplicate-operation; missing/count-inconsistent
generated rows -> incomplete-scalar-census; unexpected construction errors -> scalar-values-analysis-error.
These are whole-I result:null failures. Producer schemas/raw-word correspondence are not replayed;
private malformed records are not an externally supported boundary. Nothing mutates source, scope,
helpers or predecessors, so no cleanup/rollback edit is needed.

### Testing and acceptance

| Scenario | Result / oracle | Acceptance | Evidence |
|---|---|---|---|
| I1 scalar projection | Exact example literals, inputs/definitions, dynamic descriptors. | Every I row unique/present; RETURN/J rows skipped; freeze and unchanged B-E. | Scalar test/fixture and its private-A scaffolds below. |
| I2 mutation/global/typeof | STORE_GLOBAL no destination; string C ref; distinct global/safe lookup. | Correct useDef/effect; no evaluated getter/global value. | Global/store fixtures and scalar test. |
| I3 reachability/coercion boundary | Unreachable rows retained; ADD/SUB control changes descriptor, never folds result. | Dynamic outcomes remain unknown, structural VOID use distinct from runtime read. | Expression/short-circuit tests; generic JS oracles only for worked example. |
| I4 unknown/duplicate/census refusal | Named construction diagnostic and no partial I. | Reach actual projector decision, not earlier B refusal. | Dedicated source-entry I refusal missing (closed B inventory normally prevents unknown names); private damage would not justify owned-chain gates. |

## 4. Input Shapes

[Diagnosis](standalone-diagnosis.md#owned-record-boundary) restores constants/normalizes words and
completes current B-E before I. [C](validate-references.md) supplies copied key-zero values and
semantic offset references; [D](partition-functions.md) ownership and [E](build-cfg.md) edges
supply owner/reachability only. [J](property-collections.md) owns IN/INSTANCEOF/property/collection
rows; [L](call-completion.md) and [M](closure-exception.md) own peer call/capture/completion facts.
I is retained as scalarValues in the resolved diagnosis model; current rendering reads B/C
and derived emission records rather than consulting I as a propagated value store.

## 5. Known Gaps

- No register value flow, folding, SSA, alias/global resolution or dynamic coercion outcome is
  inferred. Descriptor types and useDef are structural facts with the stated VOID caveat.
- Missing I-family source-entry refusal evidence is explicit; later public completeness and
  supported-operation checks are separate contracts.
- Native throwing scalar/property operations are not all exceptional E edges. I does not fix
  control coverage or qualify arbitrary BigInt/proxy/global/host behavior.
- No fresh encoder output, full compiler, whole-I cold reconstruction or novice claim follows from
  retained [fixture provenance](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/qualification-provenance.md).

## Source

The runtime read/coercion/update decisions in item 3 are pinned by
[scalar handlers](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/runtime.ts#L276-L543).

The stage is implemented by [scalar-values-preflight.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/scalar-values-preflight.js), [analyze-scalar-values.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/analyze-scalar-values.js). The [standalone diagnosis](standalone-diagnosis.md)
composes its result with predecessor records. The encoder contracts are described in
[instruction-set.md](../../../js-confuser-vm/instruction-set.md) and
[container-wordcode.md](../../../js-confuser-vm/container-wordcode.md).

## Fixtures

I1/I3 use the worked example's complete words, pool and register count with the
[F private-record scaffold](build-call-frames.md#fixtures); after successful B-E call
diagnoseScalarValues(B,C,D,E). Assert six I rows, exact unsigned literal/value, ADD known=false,
STORE_GLOBAL inputs=[r2]/destination=null, and no RETURN row. Change only words[7] from11 (ADD)
to12 (SUB): inputs/destination remain the same and valueSemantics.operation changes add to
subtract with known=false. Generic JavaScript supplies the separate +/unary-plus/subtraction
oracles; I executes none of them. The [scalar test](../../../../decoder/decode-js/test/vm/jsconfuser-vm/analyze-scalar-values.test.js)
pins both variants and the representation control below. These are private-record checks, not
fresh generated output, admitted new source or cold proof. I4 has no new source-entry refusal
claim.

| Committed fixture or test control | Claim pinned |
|---|---|
| [f-expression-values](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/raw/f-expression-values/encoded.js) | Arithmetic, relation, unary, and literal operation rows with dynamic operands left unknown. |
| [f-global-resolution](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/raw/f-global-resolution/encoded.js) | Global lookup and `typeof` operation roles. |
| [focused-store-global-assignment](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/focused/focused-store-global-assignment/encoded.js) | `STORE_GLOBAL` use/def and mutation classification. |
| [f-short-circuit](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/raw/f-short-circuit/encoded.js) | Short-circuit operation boundaries while retaining dynamic input semantics. |
| [f-instanceof-errors](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/raw/f-instanceof-errors/encoded.js) | `INSTANCEOF` is a J-family peer and produces no I row; no outcome is inferred. |
| [analyze-scalar-values.test.js](../../../../decoder/decode-js/test/vm/jsconfuser-vm/analyze-scalar-values.test.js) | Scalar operation projection, input immutability, deep freezing, complete producer coverage, and the I1/I3 and representation scaffolds. |

Exact representation control uses root regCount=3, pool=["out"] and words
`[1,0,7,5,1,0,6,0,0,1,37,2,1,45,2]` in the same private scaffold. Assert LOAD_INT@0
valueSemantics={kind:"known-integer",operation:"load-integer",resultType:"integer",known:true,value:7};
MOVE@3={kind:"register-copy",operation:"move",resultType:"copy",known:false,
sourceRegister:{kind:"register",index:0}}; STORE_GLOBAL@6={kind:"input-value",operation:"store-global",
resultType:"no-register-result",known:false,sourceRegister:{kind:"register",index:1}};
VOID@10={kind:"known-undefined",operation:"void",resultType:"undefined",known:true}, with no value
or sourceRegister key. Four I rows, no RETURN@13 row. The scalar test pins these exact objects
with unchanged A-E snapshots (I consumes B-E) and a deeply frozen I; that check is separate from
independent reconstruction.

The retired frozen semantic-record verifier,
built from the documents before source consultation, asserted selected literal/dynamic operand
facts and ADD/SUB/STORE use/def decisions on supplied B-E. Excluded are guessed MOVE/STORE kind
literals, unasserted schema fields and source/public/generated behavior. The separate
retired frozen field verifier, built
from the corrected documents before source consultation, reconstructed all six selected valueSemantics variants, including
exact MOVE/STORE kind/sourceRegister objects, literal values, VOID/dynamic conditional key
absence, unsigned literals, ADD/SUB and empty I projection. The supplied semantic operands/
constants are scaffolds; full opcode definitions, dynamic coercion outcomes, census refusals,
whole I rows and source/public/generated behavior remain outside that cold claim.
