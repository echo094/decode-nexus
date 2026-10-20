# Fused real and fake effects for anti-instrumentation

## 1. Target

Hide the register footprint of selected canonical arithmetic/comparison/unary/MOVE operations
by fusing each with fake effects and permuting all operand positions. Fake effects operate on
extra per-function registers; the real step can appear anywhere in the fused sequence. One
handler structure is shared by every occurrence of a given real opcode, while operand values
vary. The intended observable result is the real operation's result with additional fake state.

Read the [workflow/AST prerequisites](../js-confuser-vm.md#prerequisites-and-scope),
[operand identity, register pools and finalization](../container-wordcode.md#augmentation-operand-handoff),
[canonical semantics](../instruction-set.md) and
[shared allocator/random primitives](runtime-layout.md#added-opcode-allocation).
Input is private symbolic IR after mandatory constant-pair expansion, before specialization,
macros, aliases and register resolution. Output includes ANTI_OPS, rewritten instructions,
entry seeds, possible fallthrough labels and later eager-read handlers. This is the exact
pinned recipe, not a proof that fake operations are harmless in every host/coercion environment.

## 2. Algorithm

Find eligible real instructions with enough register identity to attribute them to a function.
For each distinct real opcode, choose fake step definitions, shuffle the real step among them,
then choose one permutation for their combined operand slots. Reserve one synthetic opcode and
record its step operations, static arities and permutation. Later instruction occurrences use
this shared structure but supply their own real operands and newly chosen fake operands.

Give fake values a separate home. Scan existing virtual register IDs, allocate above each
function's maximum and seed a small flowing pool immediately after its entry label. Add truthy
and falsy anchors only if that function uses a fused conditional step. Anchors are never fake
write targets. Fake reads favor registers recently selected as write targets to create apparent
data-flow chains, though this is a sampling bias, not proof that every fake write is consumed.

Build operands in step order, then permute them into the stream. Runtime construction reads the
entire tail first, restores that canonical order and executes cloned step bodies in the recorded
sequence. Ordinary fake branches use anchors to stay untaken and a label immediately after the
fused instruction as their target. Eager reads also make that target the already-fetched
fallthrough position. The real step's destination stays separate from the fake pool through
the register allocation contract.

### Annotated synthetic example

Supply a function with two flowing fake registers f0/f1, initialized to 5 and 7, and truthy
anchor t=1. Let a selected ADD use R[1]=10, R[2]=20, destination R[0]. Choose these steps,
which contribute ten operand slots in total:

| Step | Canonical operands | Effect |
|---|---|---|
| LOAD_INT (fake, arity 2) | f0,9 | f0 becomes 9. |
| ADD (real, arity 3) | 0,1,2 | R[0] becomes 30. |
| BUILD_ARRAY (fake, arity 3) | f1,2,f0 | f1 becomes `[9,9]`; the one indexed operand is reused by both loop iterations. |
| JUMP_IF_FALSE (fake, arity 2) | t,after | Truthy t means untaken; after is still the safe fallthrough target. |

The operand width is 2+3+3+2=10. Choose the ten-position
permutation `[1,2,0,3,4,5,6,7,8,9]`, whose inverse begins `[2,0,1]`. With concrete fake
slots f0=3, f1=4, t=5, header PC 10 and free anti code 61:

```text
canonical tail = [3,9,0,1,2,4,2,3,5,21]
stored tail    = [9,0,3,1,2,4,2,3,5,21]
emitted words  = [61,...stored tail]             width 11
after label    = 21                              10+1+10
eager read -> inverse placement -> canonical tail
step bodies consume indexed values, not more stream words
final PC = 21, R[0]=30, f0=9, f1=[9,9], t=1
```

This supplied deterministic composition shows a middle real step and repeated-loop reads; it
omits randomized selection, constant/global steps, full entry-register resolution and late
runtime representation. It is not retained encoder output. A fake LOAD_CONST instead contributes
three slots (destination, index, key); its explicit two K arguments likewise add no later reads.

## 3. Implementation

### Components and exact target/slot tables

| Component | Input -> output | Dependency |
|---|---|---|
| Real census | IR/OP/real arity -> fusable functions and present real opcodes | Exact length, first register's fnId and descriptors determine attribution. |
| Structure selection | Distinct real ops/random choices -> ANTI_OPS and local step-kind records | One structure per real op, static read widths, permutation. |
| Pool/seeds | Scanned IDs/descriptors/needed anchors -> per-function registers and seed IR | Fresh IDs and fresh occurrence refs; valid entry label and expanded constant pairs. |
| Occurrence rewrite | Real operands/pool/structure -> permuted fused tail and optional label | All slots supplied in step order; total length equals recorded permutation. |
| Handler assembly | ANTI_OPS and canonical switch -> cloned eager-read case | Restored operands execute in recorded order, with exact syntactic substitution count. |

The eligible real table is closed:

| Real names | Required operand arity |
|---|---|
| ADD, SUB, MUL, DIV, MOD, EXP, BAND, BOR, BXOR, SHL, SHR, USHR | 3 |
| LT, GT, LTE, GTE, EQ, NEQ, LOOSE_EQ, LOOSE_NEQ | 3 |
| UNARY_NEG, UNARY_POS, UNARY_NOT, UNARY_BITNOT, MOVE | 2 |

Slots describe handler read positions: wReg writes a flowing fake register, rReg reads one,
int is a raw small integer, cAny/cGlobal/cName each supply a constant **index/key pair**,
predT/predF use immutable anchors, label is the fused fallthrough label, count is the collection
count. A constant slot has width 2; every other slot width 1. Fake definitions are exactly:

| Fake names | Slot sequence / static arity |
|---|---|
| ADD, SUB, MUL, DIV, MOD, EXP, BAND, BOR, BXOR, SHL, SHR, USHR, LT, GT, LTE, GTE, EQ, NEQ, LOOSE_EQ, LOOSE_NEQ | wReg,rReg,rReg / 3 |
| UNARY_NEG, UNARY_POS, UNARY_NOT, UNARY_BITNOT, TYPEOF, MOVE | wReg,rReg / 2 |
| LOAD_INT | wReg,int / 2 |
| LOAD_CONST | wReg,cAny / 3 |
| LOAD_GLOBAL | wReg,cGlobal / 3 |
| TYPEOF_SAFE | wReg,cName / 3 |
| JUMP_IF_FALSE | predT,label / 2 |
| JUMP_IF_TRUE | predF,label / 2 |
| BUILD_ARRAY | wReg,count,rReg / 3 |
| BUILD_OBJECT | wReg,count,rReg,rReg / 4 |

The safe-name sample list for cGlobal is exactly Object, Array, String, Number, Boolean, Math,
JSON, Date, RegExp, Error, Function, parseInt, parseFloat, isNaN, isFinite, Infinity, NaN,
undefined. These are ordinary host binding names, not values captured at compilation.

| Random decision | Domain / update |
|---|---|
| Fake steps per real opcode | Inclusive integer 2..4; each fake name chosen independently from table keys with replacement. |
| Step placement | In-place shuffle of one real plus all fake definitions; real is not fixed first. |
| Operand permutation | Shuffle fresh identity copies, retry identity up to 20 attempts, use final result; identity remains possible. |
| Flowing registers per function | Inclusive integer 2..3. |
| Fake values / seed values | Equal two-way integer/string choice; integers 0..65535, strings length 3..8. |
| Random string characters | `abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789`, chosen independently. |
| Truthy/falsy seed | Integer 1..65535 / zero. |
| int / count / cName | Integer 0..65535 / integer 0..2 / string length 3..10. |
| Recent-read bias | When nonempty and chance(70), choose from recentWrites; otherwise choose from flowing pool. |

Inclusive integer draws, choice, chance and shuffle follow the
[layout primitive equations](runtime-layout.md#components-and-exact-allocation); no seed API
or guaranteed change between builds exists.

### Producer procedure and metadata

Map current compiler.OP values for the real-name table. Scan instructions: require a nonnull
mapped real opcode, `instr.length-1` equal to its real arity, and at least one operand object
with type register. Take fnId from the **first** such operand; the pass does not separately
verify that every real operand belongs to that function. Collect functions, distinct real ops
and each function's occurring real ops. If none, return unchanged.

For each distinct real opcode in encounter order, allocate a
[free slot](runtime-layout.md#added-opcode-allocation), stopping on -1. Sample fake definitions
and their slot-derived arities, shuffle real and fake steps, sum arities, and sample order.
Store `ANTI_OPS[anti]={steps:[{op,arity},...],order}` and
`OP_NAME[anti]="ANTI_"+realName+"_"+order.join("_")`, reserving the code. Local records remember
which step is real, fake slot definitions and whether the structure needs either anchor;
ANTI_OPS itself does **not** record real identity/slot kinds. If no allocation succeeds,
return original IR. No canonical OP or JUMP_OPS entry is added.

Use the [shared max-ID/allocation/ref contract](../symbolic-helper-assembly.md#exact-shared-register-and-partition-operations).
For each previously fusable function with a descriptor, allocate flowing registers through that
allocator. Its plain register objects enter the nonreused local:: pool under
[container allocation](../container-wordcode.md#symbolic-operands-and-register-assignment).
If any actually allocated structure used by that function needs a predT or predF slot, allocate
**both** anchors and their values. Functions can receive flowing seeds even when their occurring
real opcode lost allocation to exhaustion. Shuffle pending seeds and emit
`[LOAD_CONST,freshRef(reg),constant(value),constant(value,key:true)]` for each. The constant
pair is made here because mandatory expansion has already run. Fresh seed/fake refs use the
linked shared occurrence contract; real operands retain their
existing objects.
Map descriptor entry labels to seeded functions; missing entry label means no entry injection.

Rescan in order with recentWrites initially empty. Preserve pseudo records. On defineLabel,
clear recentWrites and inject that entry's seeds immediately after the label. Other pseudo
records do not clear it. For a real opcode with allocated anti structure, recheck arity and
first-register attribution; missing pool or mismatch preserves the instruction.

Generate canonical operands by recorded step order: the real step contributes its existing
tail; each fake slot supplies the table's objects/numbers. wReg chooses a flowing register,
appends it to recentWrites and drops the oldest entry when length exceeds eight. rReg uses
the bias above; this may choose the current fake step's write target before that step executes.
Constant slots create fresh index/key objects with equal value. pred slots create fresh refs
to anchors. The first label slot creates `anti_after_<counter>`, incrementing the local counter;
all label slots for that occurrence reuse the name. count supplies its fixed sampled integer.

If canonical length differs from order.length, preserve the original instruction. Otherwise
emit `[anti,...order.map(i=>canonical[i])]`, copy SOURCE_NODE_SYM, and append a zero-width
defineLabel for after when used. Real operand objects retain identity; fake refs are independent.
There is no block-CFG analysis or automatic recentWrites reset at every branch.

### Runtime construction, loops and state

Empty/missing ANTI_OPS returns immediately. Otherwise find the first switch with a leading
comment containing @SWITCH; absence asserts `Could not find @SWITCH statement for anti-instrumentation`.
Build name -> case from MemberExpression tests on Identifier OP with Identifier property;
numeric tests are not step source cases and computed flag is not checked. For each entry,
resolve steps in stored order through OP_NAME and that map. Missing step case skips the entire
new handler. Extract sole-block bodies or direct consequents, remove all top-level breaks/empty
statements and deep-clone remaining nodes. Concatenate directly; despite the source comment,
there is no separate block per step. Canonical locals are `var` redeclarations.

Traverse the concatenated statements with noScope. The exact zero-argument ThisExpression
MemberExpression `_operand`/`_constant` CallExpression tests and sequential indexed substitution
are the same scheme described in [aliases](aliased-opcodes.md#runtime-construction-and-read-contract).
A constant call consumes two indexed positions. A collection loop's syntactic read is replaced
once; every runtime iteration reuses that position instead of advancing stream PC. BUILD_ARRAY
with count=2 therefore reads the same register twice; count=0 uses none of that read's value
but its static slot is still present. BUILD_OBJECT similarly reuses one key and value operand
for every sampled pair, assigning the same key repeatedly. Step arity fields are metadata;
the builder checks only total replaced count against order.length, not each step's arity.

Mismatch skips the case. On success eagerly read order.length words into `_unsortedOperands`,
restore `_operands[j]=_unsortedOperands[inverse[j]]` with `inverse[order[i]]=i`, execute all
clones in recorded order, add one final break and append a numeric case/fresh block. Fake
branches' indexed reads do not move PC; normal anchors keep them untaken, and the resolved after
label equals the eager-read fallthrough PC. Anchors have no fake wReg consumers. No original
case is mutated, and fake seeds/registers are retained program state, not consumed helpers.

Private maps/IR mutate without rollback. Missing-case/count skips do not revert emitted anti
words or seeds; they are internal outcomes, not a safe public damage contract. Successful raw
AST insertion does not refresh a public binding graph. Assertions reject compilation; the
[publication contract](../options.md#publication-state-and-testing) publishes no partial code.
Fake state lives within each frame and is released by ordinary frame completion, with no extra
cleanup pass. Host exceptions/side effects from fake operations use ordinary runtime semantics.

### Acceptance scenarios

| Scenario | Observable result / oracle | Acceptance criterion | Evidence |
|---|---|---|---|
| N1: middle real step / permutation | Canonical real effect and recorded fake-step state/word trace | Changed IR and added case; inverse correct; actual real value, complete PC and fake state agree. | Bounded verifier: supplied structure, actual tail placement/AST eager assembly and real/fake values/PC; random structure selection excluded. |
| N2: pools/seeds/ref identity | Scanned virtual maxima and container local-pool oracle | Fresh IDs per fn, distinct occurrence refs, nonreused real/fake slots, seeds after correct entry, both anchors only when needed. | Bounded verifier: selected single-function IDs/ref disjointness and seed placement; general descriptor scan/register allocation/random pools excluded. |
| N3: constant/collection/branch slots | Canonical read/K/coercion oracle versus eager substitutions | Pairs occupy two slots; counted loops reuse indexed values; anchors unchanged; fallthrough label/PC correct. | Bounded verifier: indexed array reuse, anchors and supplied absolute/relative after-PC translation; fake constant/nonzero-key/all-family execution excluded. |
| N4: missing source case / total count | Reach each named skip with otherwise valid marked AST | No new case and no base mutation; emitted metadata/IR not silently described as rolled back. | Bounded verifier: count/source-case skips and total-only arity behavior; exact original source-case node/state untested. |
| N5: host/coercion domain | Frozen host bindings/descriptors and actual fake operations | Observe presence, getters, conversion effects and exceptions; bound preservation claim to that environment. | Source-inspected limits; host negative controls missing. |
| N6: actual generated/combined forms | Source/options/data/handlers and original program oracle plus effect census | Actual selected structures and every credited option effect observed; behavior and state agree. | Selected arithmetic/string/stack test intent; frozen generated/effect/state evidence missing. |

## 4. Later Stages

| Later stage / spelling | Effect |
|---|---|
| [Specialized](specialized-opcodes.md) -> [macro](macro-opcodes.md) -> [alias](aliased-opcodes.md) | ANTI names are not OP_ORIGINAL, so these producers leave fused anti instructions intact. Canonical entry seeds can still be selected independently; later frequencies change. |
| Registers -> labels -> constants | Fake and real refs resolve through shared objects; after labels measure full permuted width; fake pairs get ordinary pool/key values. |
| Self-modifying construction / encryption | Consumes established anti widths and can move/encrypt the instructions. Read order remains defined by matching runtime metadata; region/routing/encryption recipe remains separate. |
| Runtime anti after specialized/macro/alias, before representation changes | Step source bodies are still canonical symbolic cases; real-step ordering comes from metadata, not builder scheduling. |
| [Shuffle](runtime-layout.md), [table](handler-table.md), [class](class-runtime.md), [minify](minify-runtime.md) | Completed numeric handlers can move/lift/reshape; comments and temporary names need not survive. |

## 5. Known Quirks

- The claim that every fake effect is universally total and side-effect free is broader than
  the source establishes. LOAD_GLOBAL reads current globals and throws if a name is absent;
  getters, reassigned globals and value-to-primitive conversion can be observable or throw.
  Fake state may hold constructors/native objects, not only the introductory comment's scalar
  list. Describe ordinary intact-host assumptions and retain direct domain controls as debt.
- Recent-write sampling is not an actual liveness proof; its history is label-reset, capped,
  and can include the current target before execution. The real step is shuffled, not first.
- Up to 20 permutation attempts can still yield identity. Handler assembly concatenates
  statements despite its per-step-block comment, and checks only total static read count.
- The [retained bounded proof](#fixtures) reconstructs a selected structure's seed/tail/handler
  subset. Random structure/slot generation, general descriptors, recentWrites/chance sampling,
  every fake operation, host domains, exact original-case state and generated stacks remain
  excluded. Source-informed owner checks do not extend that partial doc-only proof or establish
  novice readability.

## Source

Producer tables, random domains, pool/seed and occurrence decisions in items 2-3:
[bytecode/antiInstrumentation.ts#L64-L525](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/transforms/bytecode/antiInstrumentation.ts#L64-L525).
Runtime assembly is
[runtime/antiInstrumentation.ts#L11-L194](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/transforms/runtime/antiInstrumentation.ts#L11-L194).
Canonical global and collection bodies relevant to item 5 and indexed-loop reuse are
[runtime.ts#L288-L299](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/runtime.ts#L288-L299)
and [runtime.ts#L737-L761](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/runtime.ts#L737-L761).
Wiring is [compiler.ts#L3310-L3419](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/compiler.ts#L3310-L3419)
and [build-runtime.ts#L58-L89](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/build-runtime.ts#L58-L89),
forcing item 4's order. Common allocation/finalization/semantic contracts remain in linked pages.

## Fixtures

| Retained control | Scenario / demonstrated subset | Excluded evidence |
|---|---|---|
| Retired bounded verifier | N1-N4: supplied middle-real structure/permutation/pool values, selected fresh IDs/ref disjointness and entry seeds, actual tail placement/eager AST assembly, indexed array reuse, anchors/fallthrough and count/source-case skips; per-step arity not checked | Random structure/slot generation, general descriptor/register allocator, recentWrites/chance sampling, fake constant/nonzero-key/all-family execution, host conversion/getters, exact original-case node/state and whole publication/generated stacks |

Exact inputs, supplied canonical handlers and tiny oracle remain in the frozen tool, and rerunning
it reproduces its results. It builds the chosen single-function seeds/tail directly rather
than reconstructing the complete producer scan. Execution uses relative after-PC 11; a separate
supplied finalization assertion checks absolute after-PC 27. This is the stated synthetic
translation, not full compiler execution. Base comparison uses a fresh runtime; independent
source cloning is source-inspected, not a direct original-case before/after state assertion.
This partial agent document-only reconstruction does not establish novice readability or
generated-output qualification.

No generated anti fixture bytes are retained here.
[antiInstrumentation.test.js](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/test/options/antiInstrumentation.test.js)
asserts an ANTI comment and selected arithmetic result, arithmetic/comparison/string behavior,
and behavior under an explicit anti/specialized/macro/alias/shuffle/randomize/conceal stack (N6).
The combined case does not assert that every enabled effect appeared. Generation uses
[test-utils.js](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/test/test-utils.js),
whose explicit options override global profiles. The bounded N1-N4 subset above leaves complete
fake-family/identity/state controls and N5 host-domain evidence open. These option tests supply
intent, not fresh runs or qualified generated-stack evidence.
