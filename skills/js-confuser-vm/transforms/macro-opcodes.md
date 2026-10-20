# Macro opcodes for repeated instruction windows

## 1. Target

Fold a repeated sequence of canonical operations into one dispatch header, preserving its
operand tails and executing cloned canonical bodies in sequence. The intended effects are those
of the original window. Interior opcode words disappear, so labels must be measured after folding.

Read the [workflow/AST contract](../js-confuser-vm.md#prerequisites-and-scope),
[container word/identity contract](../container-wordcode.md#augmentation-operand-handoff),
[canonical grammar and frame effects](../instruction-set.md), and
[shared allocation](runtime-layout.md#added-opcode-allocation). Input is private post-specialization
IR with labels and expanded constants; output is new instruction arrays and MACRO_OPS plus later
numeric handler cases. This page states exact pinned selection and composition, including the
finite terminal checks and their JUMP_REG omission. It does not promise safety for every window
the implementation can select or qualification of every combined option profile.

## 2. Algorithm

Census short opcode sequences independently of operand values: the same sequence can run over
different registers and constants. Only repeated eligible windows earn codes. Frequency decides
allocation priority, with longer windows preferred at equal frequency. Emission then makes a
different choice: at each position, use the longest allocated matching window, emit it once and
advance past its constituents. Census overlap can therefore allocate a macro that is never used.

Concatenate the constituent operand tails in their original order. Runtime construction clones
each source case body and places those bodies in the same order under the macro case. Their
ordinary operand reads naturally consume the concatenated tails. No eager operand array or
permutation is introduced. A frame-changing or branching operation generally belongs last:
later bodies would otherwise read from a changed PC/frame using the dispatch iteration's cached
frame/register base. The exact source checks implementing that intention are narrower than a
universal safety proof, as item 5 explains.

### Annotated synthetic example

Suppose `[LOAD_INT,MOVE]` occurs twice, with operand tails `[dst=2,int=9]` and `[dst=3,src=2]`
on the first occurrence. Choose free macro code 61 and metadata `[LOAD_INT,MOVE]`:

```text
before: [LOAD_INT,2,9], [MOVE,3,2]     six words
after:  [61,2,9,3,2]                  five words
body 1: dst=read(); R[dst]=read()      reads 2,9
body 2: dst=read(); R[dst]=R[read()]   reads 3,2
```

With header PC 10, fetch leaves PC 11; the two bodies finish at 13 and 15 respectively.
R[2] and R[3] become 9. The following label measures PC 15, rather than the original 16.
A later occurrence with tails `[2,11]` and `[4,2]` uses the same macro but produces 11 in
R[2]/R[4]. This is a deterministic symbolic/word walkthrough, not generated encoder output.

A terminal `[LOAD_UPVALUE,CALL]` macro similarly retains CALL's complete argument tail.
After the upvalue body obtains the callee, CALL consumes all its operands, then an internal
callee push changes the current frame. The macro has no subsequent body to use the old cached
fp/base. Caller PC is already after the macro; RETURN later restores that caller and writes
its destination under the [canonical call contract](../instruction-set.md#branches-and-call-completion).
No variable CALL width can be inferred from the opcode sequence alone: argc/spread determines
each occurrence's tail.

## 3. Implementation

### Components and eligible windows

| Component | Input -> output | Invariant |
|---|---|---|
| Window census | Current IR and mapped opcode roles -> signatures/counts | Labels/pseudo records split windows; constituent names are canonical. |
| Ranking/allocation | Repeated signatures -> MACRO_OPS and reserved OP_NAME entries | Frequency then length allocation; one code per candidate. |
| Greedy folding | Current IR and allocated signatures -> new arrays | Longest match at current position; flatten tails without cloning operands. |
| Handler composition | Marked switch and MACRO_OPS -> cloned sequential case bodies | Operand read order agrees with concatenation; one final break. |

Eligibility is exactly:

| Decision | Outcome |
|---|---|
| op is null | Ineligible; windows cannot cross any pseudo-instruction, including defineLabel. |
| OP_NAME[op] missing | Assert `Unknown opcode <value> (not in OP_NAME)`. |
| Name includes PATCH, TRY_SETUP, TRY_END, DEBUGGER or MAKE_CLOSURE | Always ineligible. |
| Nonterminal op in compiler.JUMP_OPS | Ineligible. The mapped set is JUMP, JUMP_IF_FALSE, JUMP_IF_TRUE, FOR_IN_NEXT, TRY_SETUP, FINALLY_SETUP. |
| Nonterminal name includes RETURN, CALL, CALL_METHOD, NEW or THROW | Ineligible. |
| Name exists in OP_ORIGINAL after the preceding checks | Eligible; added opcodes are excluded. |

Terminal means the last constituent of this candidate window, not a whole-program terminator.
CALL/CALL_METHOD/NEW use count-dependent reads but can be terminal; BUILD_ARRAY/BUILD_OBJECT
can be interior and retain their dynamic tail loops. MAKE_CLOSURE is always excluded. The
substring checks and canonical-name test are separate: names of added opcodes can trigger
an exclusion before ultimately failing the canonical test. JUMP_REG is absent from JUMP_OPS.

For each start index, try lengths 2..5, stopping at end of input. Validate all positions with
the final position marked terminal. On any invalid window, break this start's length loop.
Valid signatures are comma-joined numeric op values; increment count even for overlapping
windows and differing tails. Retain count>=2, stable-sort by descending count then descending
length, preserving census encounter order for exact ties. If none, return the original IR.
Allocate each candidate until the [allocator](runtime-layout.md#added-opcode-allocation) returns
-1. Set `MACRO_OPS[code]=ops` and `OP_NAME[code]=ops.map(OP_NAME).join(",")`; this immediately
reserves the code. The fresh compiler initializes MACRO_OPS; the pass adds entries rather than
replacing the whole map.

Build signature -> code lookup from all MACRO_OPS entries. At each IR index, try lengths 5 down
to 2 and recheck eligibility. On an allocated match, emit one array with code followed by every
constituent's `slice(1)`, copying SOURCE_NODE_SYM from the first constituent; advance by window
length. Otherwise preserve the original instruction and advance one. Operand objects retain
identity. Width is `1 + sum(constituent operand widths)`, saving one header for every constituent
after the first. For producer-selected canonical windows, no baked placeholders remain inside.
Do not use allocation rank as emission preference or infer usage from metadata alone.

### Runtime construction

Find the first switch whose leading comment contains `@SWITCH`; absence asserts
`Could not find @SWITCH statement for macro opcodes`. Construct a numeric case map once:

- Skip default cases. For a MemberExpression on Identifier OP with Identifier property, find
  the first OP_NAME key whose value equals that property name and apply unary plus to the key.
  The computed flag is not checked; ordinary source uses OP.NAME.
- For a NumericLiteral test, use its value. Every other nondefault spelling, or a missing
  symbolic mapping, fails `Failed to parse <value> from <name>` because the result must be a
  number and not NaN. Repeated keys overwrite earlier entries.

For each MACRO_OPS entry resolve every constituent through that map. Missing case throws
`Could not find all constituent ops for macro op <code>`. The map is not extended by newly
added macros; normal metadata refers only to canonical source cases. Rebuild the comma-joined
OP_NAME from constituent names. Extract each case's sole-block body or direct consequent,
filter every top-level BreakStatement/EmptyStatement and deep-clone the remaining statements.
Nested loop/branch breaks remain. Concatenate these statements directly with per-body comments,
add the macro comment and one final break, and append numeric `case code` with a fresh block.
No operand-call substitution, per-step block wrapper or independent operand-count validation
occurs. Repeated canonical `var` locals remain function-scoped redeclarations as in the pinned
runtime; this is not a safe composition recipe for arbitrary lexical declarations or fallthrough
switches. The AST foundation is supplied infrastructure, not an alternate runtime implementation.

### State, publication and acceptance

MACRO_OPS and OP_NAME mutate; rewritten arrays keep constituent operand references but only the
first source annotation. Original case bodies remain unchanged. Raw case insertion does not
refresh a public Babel binding cache, remove canonical cases or consume declarations. Exceptions
can occur after some metadata/cases have changed; there is no per-window rollback or public
retry object. The public compile call publishes code only after successful completion under
[options](../options.md#publication-state-and-testing). An allocated but unused macro still
receives a runtime case. There is no added branch-target/frame validation at runtime.

| Scenario | Observable result / oracle | Acceptance criterion | Evidence |
|---|---|---|---|
| M1: repeated/different tails | Census and canonical sequential effects versus macro | Reduced header count and exact operand/value/PC traces; base cases unchanged. | Bounded verifier: actual census/folding/composition/value/PC; exact original-case before/after state untested. |
| M2: overlap/rank/labels | Fixed IR and allocated signatures | Overlaps counted, frequency/length ranking, longest nonoverlapping emission, no crossing pseudo records. | Bounded verifier: selected overlap/longest/label subset; all compiler populations excluded. |
| M3: terminal call/branch, variable collection | Canonical frame/branch and count-tail oracle | Complete tails consumed, correct caller/current frame or target; dynamic collection loop preserved. | Bounded verifier: array tails, terminal JUMP and tiny internal CALL frame/argument oracle; full CALL/RETURN lifecycle missing. |
| M4: missing case/map spelling | Otherwise eligible metadata and AST reach named error | Reject compilation; no base mutation or successful partial publication. | Bounded verifier: missing-constituent error; exact original-case state/map spelling coverage and whole publication untested. |
| M5: JUMP_REG interior / combined producers | Actual eligibility plus PC/read trace | Record source hazard, without asserting unsupported blanket preservation. | Bounded verifier demonstrates target-word reads in a supplied synthetic macro; generated interaction evidence missing. |

## 4. Later Stages

| Later stage / spelling | Effect |
|---|---|
| [Aliases](aliased-opcodes.md) | Comma-joined macro name is not OP_ORIGINAL; ordinary alias selection leaves macros intact. |
| Register/label/constant resolution | Concatenated symbolic tails resolve in place; relocated PCs account for removed interior headers and full variable tails. |
| Self-modifying construction / encryption | Consumes already-folded widths. A macro name/value does not automatically carry a constituent's JUMP_OPS membership; producer region/routing recipe remains separate. |
| Runtime specialized -> macro -> alias -> anti | Canonical source bodies coexist with earlier specialized cases; normal macros contain only canonical constituents. |
| [Shuffle](runtime-layout.md), [table](handler-table.md), [class](class-runtime.md), [minify](minify-runtime.md) | Completed numeric case body moves/lifts/reshapes; physical adjacency and comments are not promised final signatures. |

## 5. Known Quirks

- JUMP_REG changes PC but is missing from JUMP_OPS and the nonterminal-name exclusions. If
  selected before another macro body, later `_operand()` calls can read at that indirect target.
  Earlier dispatcher output can contain JUMP_REG. This is a source-derived hazard requiring
  dedicated generated evidence. The retained synthetic proof demonstrates the target-read
  consequence under its tiny oracle; it is not an observed encoder-output failure or edit request.
- FINALLY_SETUP is conservatively terminal-only through JUMP_OPS despite merely installing
  handler state during normal execution. Source intent is not a broader semantic classifier.
- Metadata allocation can outnumber used macro signatures because frequency census overlaps
  while emission consumes each instruction once. Operand values do not distinguish signatures.
- The [retained bounded proof](#fixtures) reconstructs selected census/folding/body and PC/frame
  decisions; full CALL/RETURN/capture semantics, exact original-case state, publication and
  generated stacks remain excluded. Owner arithmetic/AST checks do not extend that partial
  cold evidence or establish novice readability.

## Source

Producer/eligibility/folding in items 2-3:
[bytecode/macroOpcodes.ts#L31-L193](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/transforms/bytecode/macroOpcodes.ts#L31-L193).
AST map/composition:
[runtime/macroOpcodes.ts#L14-L141](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/transforms/runtime/macroOpcodes.ts#L14-L141).
JUMP_OPS is [compiler.ts#L419-L430](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/compiler.ts#L419-L430);
the item 5 hazard is [runtime.ts#L894-L898](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/runtime.ts#L894-L898).
Wiring is [compiler.ts#L3317-L3419](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/compiler.ts#L3317-L3419)
and [build-runtime.ts#L58-L89](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/build-runtime.ts#L58-L89),
forcing item 4's order. Canonical tail/frame behavior and common allocation/finalization are
owned by the linked instruction/layout/container contracts.

## Fixtures

| Retained control | Scenario / demonstrated subset | Excluded evidence |
|---|---|---|
| Retired bounded verifier | M1-M5: repeated/overlap census, longest folding/pseudo boundaries, actual AST concatenation, dynamic array tails, terminal JUMP and supplied internal CALL argument/caller-PC/child-link/retDst oracle, missing-constituent error and JUMP_REG target-read hazard | Full CALL/RETURN/clearing/native-shell/host/rest/constructor/capture semantics, all compiler windows, exact original source-case state and whole publication/generated stacks |

The frozen tool retains exact supplied handlers, symbolic notation, inputs and tiny execution
oracle. The frozen macro group does
not directly compare original case nodes before and after insertion. Deep cloning
is additionally source-inspected. The CALL scaffold never executes RETURN or frame clearing.
This partial document-only reconstruction is not a novice study, whole-compiler reconstruction
or qualification of real option combinations.

No generated macro fixture bytes are retained here.
[macroOpcodes.test.js](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/test/options/macroOpcodes.test.js)
asserts a LOAD_UPVALUE,CALL comment and counter result under explicit macroOpcodes=true (M3).
It generates through
[test-utils.js](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/test/test-utils.js),
whose explicit options override global profiles. That option test does not retain frame/PC state,
M1/M2/M4 direct controls or M5 evidence; the synthetic subset above has its own stated boundary.
Test intent is not a fresh run or combined-output qualification.
