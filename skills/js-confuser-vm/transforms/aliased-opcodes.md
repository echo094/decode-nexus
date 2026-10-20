# Aliased opcodes and operand permutations

## 1. Target

Give an eligible canonical operation a second dispatch value and move its operands into a
different stream order. The emitted handler reads that order eagerly, restores the original
order and executes a clone of the canonical body. Intended program effects remain those of
the original operation; the original handler also remains installed.

Read the [workflow/AST prerequisites](../js-confuser-vm.md#prerequisites-and-scope),
[word/operand contract](../container-wordcode.md#word-addresses-and-serialization),
[canonical semantics](../instruction-set.md) and
[shared opcode allocation](runtime-layout.md#added-opcode-allocation).
Input is private post-macro symbolic IR with expanded constant pairs and a fresh compiler's
maps, not arbitrary supplied bytecode or runtime AST. Output is rewritten IR plus ALIASED_OPS
metadata and, later, matching cases. This page specifies the pinned producer/runtime recipe;
retained generated variants and comprehensive direct controls remain missing.

## 2. Algorithm

Count occurrences of eligible base operations in the instructions that earlier passes left.
An alias needs one stable operand count: a varying tail cannot be eagerly captured by this
fixed handler. Allocate in descending frequency order so limited opcode space goes to the
most frequent candidates. Each candidate receives one alias, not several randomly selected
clones. Every matching occurrence is rewritten to that alias.

For each alias, shuffle the operand positions. The metadata records where each original
operand was placed, so runtime construction can undo that placement before executing the
canonical body. The handler reads all operands before performing any operation; branch
effects therefore cannot redirect one of those initial reads. Constant access uses its two
ordinary index/key values after reordering, without consuming the stream again.

### Annotated synthetic example

Use plain LOAD_GLOBAL=2, a chosen free alias 61 and resolved operands `[dst=4,idx=7,key=0]`.
These numbers model the final values of private operands; the example omits selection sampling,
symbolic resolution and late runtime reshaping. Let the recorded `order=[1,2,0]`:

```text
original: [2,4,7,0]       meaning: R[4] = globals[K(7,0)]
alias:    [61,7,0,4]     new slot i holds original operand order[i]
inverse:  [2,0,1]        inverse[order[i]] = i
read:     unsorted=[7,0,4], operands=[4,7,0]
body:     dst=operands[0]; name=K(operands[1],operands[2]); R[dst]=globals[name]
```

With constants[7] equal to `"answer"` and an ordinary own globals.answer=42, the result is
R[4]=42. Starting the header at word PC 10 fetches the opcode at 10, reads words 11..13,
then leaves PC 14. Explicit arguments to K consume no further words. The three-cycle matters:
applying `order` again would produce `[0,4,7]`, not the correct operands. A swap alone would
hide this mistake. Both forms occupy four words and leave the base case unchanged.

## 3. Implementation

### Components and eligibility

| Component | Input -> output | Required invariant |
|---|---|---|
| Candidate census | Current IR and OP/OP_NAME -> frequency, consistent arity | Only canonical names and eligible base values; placeholders are not created by this pass. |
| Allocation/permutation | Ranked census -> aliasMap, ALIASED_OPS, OP_NAME | One reserved free code per base; order lists every operand position once. |
| IR placement | Instruction -> alias header and permuted existing operands | Operand objects retain identity; SOURCE_NODE_SYM is copied from that instruction. |
| Handler construction | ALIASED_OPS and marked switch -> cloned numeric cases | Reads match metadata arity; canonical body remains independent. |

Build a value-to-name map from compiler.OP, excluding these exact names:

| Exclusion | Reason for the fixed-read boundary |
|---|---|
| MAKE_CLOSURE, BUILD_ARRAY, BUILD_OBJECT, CALL, CALL_METHOD, NEW | Count-dependent operand reads. |
| PATCH, TRY_SETUP, TRY_END, DEBUGGER | Excluded infrastructure; no alias promised for them. |

For each real instruction, require its value in that map, `instr.length-1 >=1`, and
`OP_ORIGINAL[compiler.OP_NAME[op]] !== undefined`. Thus canonical zero-operand operations and
all added opcodes are ignored. First occurrence fixes arity; any different length sets
arity to null permanently. Frequency still increments. Filter null arities and stable-sort
descending frequency; ties retain encounter order. No minimum frequency or candidate cap
exists. If no candidate, return the same IR without assigning a new alias map.

### Allocation, placement and metadata

For each candidate obtain a [free slot](runtime-layout.md#added-opcode-allocation), stopping
on -1. Arity one uses `[0]`. For larger arities start with `[0..arity-1]`, shuffle a fresh
copy, and retry while the result is identity and fewer than 20 attempts have occurred. The
last result is used even if still identity. Record `ALIASED_OPS[alias]={originalOp,order}`
and `OP_NAME[alias]="ALIAS_"+originalName+"_"+order.join("_")`; this also reserves the code.
The local aliasMap maps originalOp to alias. Assign the assembled ALIASED_OPS object even
when allocation supplied no aliases.

Rescan in order. Nonmatching and pseudo instructions are passed through by array identity.
For a match, check `instr.slice(1).length===order.length`; mismatch preserves the original
instruction. Otherwise emit `[alias,...order.map(i=>originalOperands[i])]`. This creates a
new instruction array but reuses operand objects, so register/label/constant resolution later
updates the same semantic references. This pass does not change compiler.OP or JUMP_OPS.

### Runtime construction and read contract

Empty/missing ALIASED_OPS returns before AST traversal. Otherwise find the first SwitchStatement
with a leading comment containing `@SWITCH`, stopping traversal; absence asserts
`Could not find @SWITCH statement for aliased opcodes`. Map cases whose tests are MemberExpressions
with object Identifier OP and Identifier property to that property's name. There is no
computed-property exclusion; canonical input uses `OP.NAME`. Numeric case tests are not alias
source bodies. Resolve originalOp through OP_NAME and this map; missing name or case skips
that alias.

If consequent is exactly one BlockStatement, take its body; otherwise take consequent directly.
Filter every top-level BreakStatement and EmptyStatement, deep-clone the remaining statements,
and traverse the temporary block with noScope. A zero-argument CallExpression whose callee is
a MemberExpression on ThisExpression with Identifier property `_operand` becomes
`_operands[next++]`. The corresponding `_constant` call gets two arguments,
`_operands[next++]` and `_operands[next++]`. These are exact AST tests, not binding-aware
recognition of arbitrary helper functions. Existing nonzero-argument calls are untouched.
Nested calls in loops are rewritten once per syntactic call site.

Require the resulting read count to equal order.length; mismatch skips insertion. Prepend a
let declaration initializing `_unsortedOperands` with arity sequential `this._operand()` calls,
then a let `_operands` array using the inverse permutation. Append the cloned statements and
one break inside a fresh block under numeric `case alias`. Add a descriptive comment to the
first declaration. No canonical case is changed and no helpers/declarations are removed.

### State, failure and acceptance

Compilation mutates private maps/IR; there is no matched-unit rollback or public retry API.
Skipped runtime aliases leave any previously emitted alias words and metadata in place. The
normal producer is expected to supply compatible bodies; this internal skip is not a promise
that arbitrary metadata damage yields safe code. Successful builders append raw case nodes
without refreshing a public binding cache. Later runtime stages traverse the completed AST;
this page does not promise an independently reusable Babel scope graph after insertion.
Assertions reject compilation; publication follows the [option/publication contract](../options.md#publication-state-and-testing).

| Scenario | Observable result / oracle | Acceptance criterion | Evidence |
|---|---|---|---|
| A1: three-cycle / constant pair | Canonical operation versus actual cloned/substituted alias body, word trace | Correct destination/value/key; exact inverse and final PC; base body unchanged; IR actually changes. | Bounded verifier: IR placement/AST eager read/value/PC and key-zero pair; exact original-case before/after state untested. |
| A2: eligibility / frequencies | Exact census and original-name table above | Exclusions, zero arity, inconsistent tails and synthetic names ignored; all selected occurrences replaced. | Bounded verifier: selected eligibility/frequency census; complete generated populations excluded. |
| A3: bounded randomness / allocation | Scripted choices and shared allocator | One alias per base, immediate reservation, identity after 20 attempts allowed, exhaustion preserves remaining instructions. | Bounded verifier: deterministic shared allocator and identity retry; random distribution/full production excluded. |
| A4: source-case / count mismatch | Reach the named lookup/read-count decision with otherwise valid AST | Skip means no added case, no base mutation; distinguish marker assertion from alias skip. | Bounded verifier: count/source-case skips and marker assertion; exact original-case node/state and publication untested. |
| A5: emitted runtime / stacks | Frozen source/options/data/handlers plus original program oracle | Runtime case and tail actually correspond; later representations preserve meaning. | Selected option test intent; retained generated/effect/state evidence missing. |

## 4. Later Stages

| Later stage / spelling | Effect |
|---|---|
| Registers -> labels -> constants | Permuted objects resolve in place; constant index and key need not remain adjacent physically. Width remains `1+order.length`. |
| Self-modifying construction / encryption | Moves already-width-set instructions and encrypts emitted words. Alias metadata still installs the handler; ciphertext is opaque. PATCH producer recipe remains separate. |
| Runtime alias insertion after specialized/macro, before anti | Base symbolic cases still supply alias bodies; original-name selection prevents ordinary nested augmentation. |
| [Shuffle](runtime-layout.md), [table](handler-table.md), [class](class-runtime.md), [minify](minify-runtime.md) | Numeric alias cases can move, become prototype entries or be renamed/folded; marker/temporary/comment spellings are not final-output guarantees. |

## 5. Known Quirks

- Nonidentity is attempted, not guaranteed. Arity-one and rare retry-exhausted aliases can retain
  original operand order while still changing the dispatch value.
- Every selected occurrence uses the alias; this is not random alternation between base and clone.
- Runtime skips are not propagated back into bytecode. No general malformed-metadata preservation
  or comprehensive option-stack behavior claim follows from this source recipe.
- The [retained bounded proof](#fixtures) supplies selected permutation/read/census/skip evidence.
  It compares with a fresh runtime rather than directly preserving the exact original source-case
  nodes. Complete state, nonzero keys, generated stacks and publication controls remain missing.
  Source-informed owner checks do not extend that partial doc-only reconstruction boundary.

## Source

Producer/census in items 2-3:
[aliasedOpcodes.ts#L11-L152](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/transforms/bytecode/aliasedOpcodes.ts#L11-L152).
Handler construction is
[runtime/aliasedOpcodes.ts#L10-L191](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/transforms/runtime/aliasedOpcodes.ts#L10-L191).
Wiring is [compiler.ts#L3317-L3419](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/compiler.ts#L3317-L3419)
and [build-runtime.ts#L58-L89](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/build-runtime.ts#L58-L89),
forcing item 4's order. Common allocation and resolution source references belong to the linked
layout/container contracts; canonical K and global semantics belong to the instruction set.

## Fixtures

| Retained control | Scenario / demonstrated subset | Excluded evidence |
|---|---|---|
| Retired bounded verifier | A1-A4: selected eligibility/frequency census, actual three-cycle IR placement and eager AST substitution, key-zero constant pair/value/PC, count/source-case skips and marker assertion; shared allocator/identity retry | Full generated AST/option stacks, nonzero keys, exact original source-case before/after node/state and whole publication |

Exact synthetic input bytes, supplied canonical handler strings, tiny oracle and deterministic
choices live in the frozen tool, and rerunning it reproduces its results.
The supplied sparse OP map is not a full compiler map. The frozen base comparison uses a fresh
runtime; independent cloning is source-inspected rather than completely proved by that comparison.
This is one agent's partial document-only reconstruction, not novice readability or generated
output qualification. Owner source-informed checks are separate from the frozen evidence.

No generated alias fixture bytes are retained in this package.
[aliasedOpcodes.test.js](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/test/options/aliasedOpcodes.test.js)
asserts an ALIAS_LOAD_GLOBAL comment and expected window value under explicit aliasedOpcodes=true
(A5). That option test does not assert A1-A4's permutation, case, state or skip decisions. It generates through
[test-utils.js](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/test/test-utils.js);
explicit options override the global project profile. These are committed test intentions, not
fresh runs, generated-output provenance or a qualification claim.
