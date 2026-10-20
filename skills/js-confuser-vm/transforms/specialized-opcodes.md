# Specialized opcodes with baked operand tuples

## 1. Target

Replace an eligible canonical operation and its complete operand tuple with a new opcode whose
handler already contains the final operand values. The emitted instruction occupies one word;
its symbolic operands remain in private IR as references until finalization resolves them.
This reduces ordinary operand reads and exposes a distinct dispatch value for that tuple.

Read the [workflow/AST contract](../js-confuser-vm.md#prerequisites-and-scope),
[container identity/finalization](../container-wordcode.md#augmentation-operand-handoff),
[canonical semantics](../instruction-set.md) and
[shared allocator](runtime-layout.md#added-opcode-allocation). Input is post-anti private IR
with expanded constant pairs and fresh compiler metadata. This is a source-derived recipe
for tuple selection and matching AST construction, not a single-integer-operand algorithm or
a guarantee for arbitrary IR/metadata. Direct and retained generated-output controls remain owed.

## 2. Algorithm

Gather eligible canonical tuples before concrete registers, label addresses and constant pool
indexes are known. Compare their symbolic object descriptions, including register/function
identity, rather than values that happen to resolve alike later. More frequent tuples receive
allocation priority, but one occurrence is sufficient. Each selected tuple owns one free code.

Mark each matching instruction's operand objects as placeholders. They still participate in
resolution, so handler metadata can see the final values; word sizing and serialization omit
them. After finalization, clone the canonical handler and replace its operand reads with numeric
literals in canonical read order. Constant access receives two literal arguments instead of
reading its index/key from the stream. The handler then performs the original effect without
advancing PC for operands.

### Annotated synthetic example

Let two post-expansion LOAD_GLOBAL instructions contain a register object `(fnId=0,id=4)` and
the constant pair for `"answer"`. Distinct operand objects carry identical serialized descriptions.
Choose free special code 61. The first tuple's objects become SPECIALIZED_OPS[61].operands;
every matching occurrence keeps its own tuple objects and marks them `placeholder:true`.

```text
IR before: [LOAD_GLOBAL, reg(0,4), const("answer"), constKey("answer")]
IR after:  [61, reg(0,4)*, const("answer")*, constKey("answer")*]   *=placeholder
resolution (chosen final values): [dst=4, idx=7, key=0]
emitted words: [61]
cloned body: dst=4; name=this._constant(7,0); R[dst]=globals[name]
```

With constants[7]=`"answer"` and ordinary globals.answer=42, both occurrences assign R[4]=42.
An instruction at PC 10 fetches 61 and finishes at 11, rather than the original four-word
span's 14. Labels and function entries are measured using that one-word width. This example
supplies resolved slot/pool values to illustrate the interface; it does not reconstruct the
whole compiler, select random allocations or qualify a host-global environment.

## 3. Implementation

### Components and exact selection

| Component | Input -> output | Consumer dependency |
|---|---|---|
| Tuple census | Current instructions -> JSON signatures/frequencies and per-instruction key | Signature frozen before placeholder or resolver mutations. |
| Selection | Ranked tuples -> reserved codes and SPECIALIZED_OPS | Metadata refers to first encountered tuple objects. |
| Placeholder rewrite | Matching instructions -> new arrays with marked existing operands | Resolver must visit hidden operands; size excludes them. |
| Final-value inlining | Resolved metadata and marked switch -> numeric cases | Exact syntactic read count matches complete tuple; cloned original body unchanged. |

Exclude the actual compiler.OP values of MAKE_CLOSURE, BUILD_ARRAY, BUILD_OBJECT, CALL,
CALL_METHOD and NEW. Ignore pseudo instructions and any name not in OP_ORIGINAL. Compute
eligible operand count as `width(instr)-1` using the container's placeholder-filtered emitted
width, and require 1..6 inclusive. This private pipeline normally has no placeholders on the
remaining canonical candidates. It is not a general contract for externally premarked IR.

For every eligible instruction, convert each numeric operand into
`{type:"number",value:n,resolvedValue:n}`; retain other operand objects. Mutate that instruction
array in place to contain the converted tail. Capture `operandsKey=JSON.stringify(operands)`
in a WeakMap keyed by the instruction, and census using `op+","+operandsKey`. Object properties
and their JSON serialization are part of this equivalence rule; it is not normalized semantic
equality, and function-valued fields are omitted by JSON. The census's first tuple objects become
candidate metadata. Frequencies stable-sort descending; retain `occurrences>=1`, then take the
first 1000. Comments claiming >=2 or one integer operand do not describe this implementation.

For each candidate, skip when its base count is already greater than 3; otherwise increment
that count and ask for a [free code](runtime-layout.md#added-opcode-allocation), stopping on -1.
This permits at most four candidates per base. Record the original/signature -> code lookup,
`SPECIALIZED_OPS[code]={originalOp,operands}`, and
`OP_NAME[code]=originalName+"_"+operandsKey`, which reserves the slot. Assign the assembled
SPECIALIZED_OPS object. A no-candidate return occurs before that assignment, but the census may
already have wrapped numbers and mutated instruction arrays.

Rescan using the previously captured keys, not newly serialized mutated objects. Pass through
pseudo records, instructions with no operands, MAKE_CLOSURE and those with no captured key.
Lookup the selected code. The executable check is `if (!specialOpCode)`: code zero is therefore
not rewritten even when allocated/registered. For a truthy code, reuse each existing operand
object and set placeholder=true; a primitive fallback would wrap it with type number and
resolvedValue. Emit a new array `[code,...markedOperands]` and copy SOURCE_NODE_SYM. First-tuple
metadata and that occurrence's operands share identity; other matching occurrences have their
own objects with matching descriptions. Canonical OP and JUMP_OPS are not extended.

### Resolution and runtime AST construction

The [container handoff](../container-wordcode.md#augmentation-operand-handoff) owns the mutable
object contract. Register resolution fills slots, label resolution mutates label operands into
resolved numbers, and constant resolution fills index/key numbers without shrinking private
arrays. Serialization validates numeric operands including placeholders, then emits only the
header. This is why copying primitive values into metadata before resolution would be wrong.

The runtime builder finds the first switch with a leading comment containing `@SWITCH`; absence
asserts `Could not find @SWITCH statement for specialized opcodes`. It builds the shared
[numeric/symbolic case map](macro-opcodes.md#runtime-construction) before checking whether
SPECIALIZED_OPS exists. For each entry, require its original case; absence asserts
`Could not find original case for opcode <name> (<value>)`. Extract the sole-block body or
direct consequent, filter all top-level breaks/empty statements and deep-clone it.

Require info.operands, then derive values with
`placedOperand?.resolvedValue ?? placedOperand` in tuple order. Optional access permits null
to survive this mapping; null also escapes the initial falsy-invalid scan and fails if consumed
by the numeric assertion below. This differs from dereferencing placedOperand directly.
The initial nonnumeric scan uses `.find(v=>typeof v!=="number")` followed by truthiness: a
falsy invalid value can escape that scan. Every actually consumed value is separately asserted
numeric by the substitution step, so do not describe the initial scan as complete validation.
Rename OP_NAME[code] to `originalName+"_"+resolvedValues.join("_")`.

Traverse a temporary block with noScope. Match zero-argument CallExpressions on ThisExpression
whose MemberExpression property is Identifier `_operand` or `_constant` (computed flag is not
tested). Replace `_operand` with the next numeric literal; add two next literals as arguments
to `_constant`. Existing explicit-argument calls remain. Each consume asserts typeof number;
too few values fails that assertion. After traversal, unequal consumed count versus tuple
length logs the tuple/info and throws `Specialized Opcode Inline Error: Given <n> operands to
replace, but only found <m> for <name>`. Thus extra operands also reject. No integrality/u32
assertion is added here; normal container finalization supplies the documented numbers.
Add descriptive comments, append one break and install a numeric case with a fresh block.

### State, failures and acceptance

Private operand objects, OP_NAME and SPECIALIZED_OPS mutate; there is no speculative rollback
or retry result. Earlier cases may already have been appended before a later entry throws;
the public call rejects, rather than publishing partial code. Original case nodes are deep
cloned and remain unchanged. Hidden references remain private until serialization; generated
runtime has literal operands and no placeholder machinery to clean up. Raw case insertion does
not supply an independently refreshed public Babel binding graph. Publication and wrapping of
other errors follow [options](../options.md#publication-state-and-testing).

| Scenario | Observable result / oracle | Acceptance criterion | Evidence |
|---|---|---|---|
| S1: symbolic tuple and constant pair | Shared object resolution, flat width and actual inlined canonical effect | IR changes; resolved metadata agrees; one emitted word, no operand reads, correct value and PC. | Bounded verifier: selected shared resolution/placeholder/baking subset; complete finalizer/state controls missing. |
| S2: candidates/caps | Exact signature census versus scripted tuples | Singleton admitted, 1..6 count, variable/synthetic exclusion, first 1000 then four per base; stable ties. | Bounded verifier: selected tuple census/wrapping; complete cap populations and selection controls missing. |
| S3: opcode zero / exhaustion | Scripted allocator and rewrite trace | Zero remains canonical despite registered metadata; exhausted candidates remain unchanged. | Bounded verifier: registered-unrewritten zero and shared allocator exhaustion; wider producer controls missing. |
| S4: lookup/type/read-count errors | Otherwise valid AST reaches the named failing decision | Original body unchanged; compilation rejects and publishes no code; distinguish count from marker/case error. | Bounded verifier: false-based consumed-type, count and source-case errors; null source outcome, exact original-case state and whole publication untested. |
| S5: actual output and combined stages | Frozen source/options/stream/handler plus original program oracle | Matching runtime case, baked tuple and later representations; actual effects observed. | Selected test intent; generated/effect/state evidence missing. |

## 4. Later Stages

| Later stage / spelling | Effect |
|---|---|
| [Macro](macro-opcodes.md) and [alias](aliased-opcodes.md) selection | Synthetic specialized name is not OP_ORIGINAL, so these instructions are not ordinary later candidates. |
| Register/label/constant resolution | Writes final values through hidden operand objects; labels use one-word widths. |
| Self-modifying construction / encryption | Counts one emitted word, moves the IR tuple and encrypts its header without placeholders. Opaque ciphertext cannot be reinterpreted as a specialized instruction. Producer/encryption recipe remains separate. |
| Runtime specialized -> macro -> alias -> anti | Handler exists before later builders; canonical source cases still exist. Source comments describing a macro-first requirement are stale. |
| [Shuffle](runtime-layout.md), [table](handler-table.md), [class](class-runtime.md), [minify](minify-runtime.md) | Numeric literal cases and baked values can move or be folded; readable OP_NAME/comment spelling is not a stable final signature. |

## 5. Known Quirks

- Opcode-zero selection can install an unused specialized case while leaving original words.
  This is a source-inspected outcome, not an observed randomized failure.
- Singleton eligibility, full tuples and four-per-base allocation contradict older source
  comments. JSON signatures are representation-based; equal final values need not share a code.
- Nonnumeric metadata errors are not uniformly caught by the initial truthiness scan; consume
  and count assertions are distinct boundaries. No arbitrary damaged-input preservation is promised.
- The [retained bounded proof](#fixtures) reconstructs selected tuple/reference/read/error
  decisions. Its mapping dereferences directly, so it does not establish the corrected null
  source outcome; its false control reaches consumption. Full selection/cap populations,
  finalization, exact original-case node state, publication, stacks and generated output remain
  outside that proof. Source-informed owner checks do not extend its cold boundary.

## Source

Producer and selection in items 2-3:
[bytecode/specializedOpcodes.ts#L5-L172](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/transforms/bytecode/specializedOpcodes.ts#L5-L172).
Inlining and errors:
[runtime/specializedOpcodes.ts#L12-L161](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/transforms/runtime/specializedOpcodes.ts#L12-L161).
Wiring is [compiler.ts#L3317-L3419](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/compiler.ts#L3317-L3419)
and [build-runtime.ts#L58-L89](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/build-runtime.ts#L58-L89),
forcing the resolution/runtime ordering in item 4. Shared width, allocation and finalization
references are owned by the linked container/layout pages.

## Fixtures

| Retained control | Scenario / demonstrated subset | Excluded evidence |
|---|---|---|
| Retired bounded verifier | S1-S4: selected tuple census/wrapping, first-tuple identity, placeholder width, supplied slot/pool resolution, actual AST baking/value/PC, registered-unrewritten zero, false-based consumption/count/source-case errors | Complete cap populations/register allocation/interning/label transforms, nonzero keys, null source mapping, exact original source-case node/state and whole-source publication |

The tool's exact synthetic inputs, supplied canonical handler strings and tiny oracle are retained
in the frozen tool, and rerunning it reproduces its results. It uses a sparse supplied OP map, not full compiler
allocation. Its direct property mapping is narrower than optional access in the corrected recipe;
the tool remains immutable. The frozen specialization group does not directly compare original
case nodes before and after insertion. Deep cloning is additionally source-inspected; do not
credit a direct original-case before/after invariant.
This is a partial agent doc-only reconstruction, not a novice study or source-equivalence claim
for every private input.

No generated specialized fixture bytes are retained in this package.
[specializedOpcodes.test.js](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/test/options/specializedOpcodes.test.js)
asserts a baked LOAD_GLOBAL comment and expected window value under explicit specializedOpcodes=true
(S5); its comment describing a single operand does not replace the executable regex/tuple.
It generates through
[test-utils.js](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/test/test-utils.js),
whose explicit options override global profiles. The option test supplies S5 intent; the
bounded S1-S4 subset above does not fill its generated-output/state gaps or qualify option stacks.
No fresh encoder run or output qualification is claimed.
