# Build per-function control flow

## 1. Target

Turn instruction boundaries and serialized ownership into a static per-function control model:
edges, exact handler-stack states, finite indirect targets, call sites and blocks. Success returns
deeply frozen `jsconfuser-vm-cfg.v1` (Packet E); unsupported control returns no partial graph.
This is observable recovery of control facts, not JavaScript emission or runtime execution.

Readers need directed graphs, worklists, registers and exceptions, plus [B grammar](read-wordcode.md),
[C references](validate-references.md) and [D ownership](partition-functions.md). The encoder's
[handler/completion semantics](../../../js-confuser-vm/instruction-set.md#catch-finally-and-abrupt-completion)
explain why finally continuation values are PCs. Source scope/path prerequisites live in
[Babel](../../babel.md); this stage operates on decoder-owned numeric records.

## 2. Algorithm

Control depends on both PC and the stack of armed catch/finally records. Start each function
at its entry with an empty stack and follow local successors. TRY_SETUP/FINALLY_SETUP push a
record; TRY_END pops one. When paths meet, require exactly the same ordered stack. Refusing a
disagreement avoids assigning one meaning to a PC whose exception route depends on how it arrived.

Direct targets are already legal/local from C/D. Calls gain a normal continuation and a possible
exception route; THROW follows the innermost record or propagates. RETURN terminates or records
an active-finalizer route. These are analysis edges, not an interpreter. Higher-level
[H](exception-finally.md) still owns the finalizer continuation-register check, and
emission must pass the subsequent semantic/coverage contracts.

JUMP_REG has no direct PC operand. Track finite PC values in registers: LOAD_INT seeds a value,
MOVE copies it, other destination writes make it unknown, and merge unions values while
preserving unknownness. Initially give indirect jumps no successors. Solve stack flow, then
value flow; use the resulting finite target sets as successors and repeat until unchanged.
Validate target boundaries and same-function ownership before admitting the graph.

Finally divide the owned instructions at leaders and retain handler/indirect/call facts. Detect
strongly connected cycles with more than one externally entered node and mark them for a
state-machine fallback. E neither structures those regions nor emits that fallback.

### Worked example: indirect target from a copied seed

This **synthetic canonical stream** has root regCount=2, no closures or handlers:

| PC | Words | Data/control effect |
|---:|---|---|
| 0 | `[1,0,8]` | LOAD_INT seeds r0={8}, origin PC 0; next 3. |
| 3 | `[5,1,0]` | MOVE copies r0 into r1; next 6. |
| 6 | `[58,1]` | JUMP_REG reads r1; no ordinary fallthrough. |
| 8 | `[45,0]` | RETURN r0; propagation edge to null. |

B boundaries are [0,3,6,8], wordCount=10; D gives them root owner 0. On solver round one,
stack flow reaches 0/3/6 with no indirect successors; value flow finds r1={8}, unknown=false
at 6. The next indirect map is {6:[8]}. Round two reaches RETURN at 8 and produces the
same map, so it converges. Indirect evidence is pc=6, sourceRegister=1, targets=[8],
origins={8:["0"]}; edges are 0->3 fallthrough, 3->6 fallthrough, 6->8 indirect branch,
8->null return. Leaders are [0,3,6,8], including every fallthrough target.

Replacing the seed 8 with 7 gives out-of-range-target because 7 is an operand word. Replacing
MOVE with an operation that writes an unknown r1 gives unresolved-jump-reg. No runtime trial
is used to discover a target. This assembly omits source/runtime admission, merged target sets
and exception registers; it is a grammar/control example rather than encoder output.

## 3. Implementation

### Components and consumed state

| Component | Consumes -> produces | Required responsibility |
|---|---|---|
| Record indexes | B/C/D -> instructions, owners, label rows | Lookup successful records; do not rerun schema/count/correspondence checks. |
| Owner register preflight | Instructions + D regCounts -> refusal or continuation | Current exact operand selection is below; C's global bound is not repeated. |
| Handler-record builder | TRY/FINALLY_SETUP -> stable record IDs | Join C targets and D owner; preserve registers/pad metadata. |
| Stack-flow worklist | Entry + indirect map -> reachable states/edges | Exact ordered-stack merge, pop/push/routing and terminal restrictions. |
| Register-flow worklist | Stack edges -> finite values/origins | Transfer then edge writes; union merge; refuse unknown indirect values. |
| Outer fixed point | Stack/value solvers -> stable indirect edges | At most 32 rounds; every target same-owner boundary. |
| Blocks/SCC/call projection | Stable edges + all owned instructions -> graph/call model | Exact leaders, interval coverage, irreducible marker, call grammar. |
| Publisher | Complete function graphs -> frozen E | Copy state, publish atomically; no predecessor mutation. |

C supplies a label lookup keyed by "pc:semanticOperand"; D supplies functions, IDs and PC owners.
Indexing is not independent-model admission. Unexpected malformed private records are not a
contract to add defensive revalidation at every handoff.

### Owner ranges and handler records

On the instructions a function's stack solve reaches, before its data-flow solve reads them,
require each selected register index < its D owner's regCount (failure register-range); the
root's count is A's N. Unreachable code is not bounded: it never decides behaviour.
Selection is raw word offsets: loads/closure creation use destination word 1; MOVE/FOR_IN_SETUP
use words 1/2; BUILD_ARRAY/OBJECT use destination and all tail registers; STORE_GLOBAL uses
word 3; STORE_UPVALUE word 2; property/binary/accessor rows use every word after opcode;
conditionals/RETURN/THROW/JUMP_REG use word 1; calls use destination/callee/receiver and argument
registers with sentinel-first selection; FOR_IN_NEXT uses words 1/2; FINALLY_SETUP words 2/3.
Current unary rows select only destination word 1, and TRY_SETUP selects none here; nothing
bounds their other registers (see [Known Gaps](#5-known-gaps)).

Build `try@setupPc` records {type:handler,ownerFunction,setupPc,handlerPc,exceptionReg} and
`finally@setupPc` records {type:finally,ownerFunction,setupPc,finallyPc,continuationReg,
payloadReg,throwPadPc}. Target PCs come from C semantic offset 0 (and 3 for throwPad);
registers use the raw grammar. Runtime record IDs are not inferred from generated names.

A handler state is an ordered list of these IDs, oldest first. Public stateView contains both
`stack` (all corresponding record views) and `finallyStack` (finalizer views only), retaining
setup/target/register/pad fields. IDs/owner are attached separately to published handler records.

### Stack flow and routes

Worklist starts at fn.startPc with []. Process each first-seen reachable instruction; a second
arrival must have an identical ordered ID list or handler-stack-merge-disagreement. Direct
fallthrough is nextPc only while nextPc < fn.endPc. If no next exists and the outgoing stack
is non-empty, decline unbalanced-handler-stack; an empty ordinary terminal produces no edge.
A call with no local next declines missing-call-continuation.

| Instruction | Outgoing edge(s) | Stack after / value-flow edge writes |
|---|---|---|
| TRY_SETUP / FINALLY_SETUP | fallthrough | Push corresponding setup ID. |
| TRY_END | fallthrough | Pop one; empty input -> handler-stack-underflow. |
| JUMP | branch to C target; kind finally/route normal if target equals any same-owner finallyPc | Stack unchanged; finalizer payload records its continuation/payload/pad fields. |
| JUMP_IF_FALSE/TRUE | conditional target + local fallthrough | Stack unchanged; condition={register,truthy:false/true}. |
| FOR_IN_NEXT | branch to exit + local fallthrough | Stack unchanged; condition={kind:iterator,register:iter,available:false}. |
| JUMP_REG | branch per solved target, mode indirect, route direct | Stack unchanged. Whether a resume lands inside its own finalizer is a graph question, left to the reader that needs it. |
| CALL/CALL_METHOD/NEW | call to next, route normal; plus exceptional route below | Normal stack unchanged; exceptional route pops/transforms stack as below. |
| THROW | exceptional route below | Source payload register is raw word 1. |
| RETURN | return/propagate to null when no finalizer; otherwise finally/exceptional to nearest active finalizer | Exact payload and stack/write decisions below. |
| Other rows | local fallthrough | Stack unchanged. |

THROW and a call's possible exception share this route selection:

```text
if stack empty:
  edge throw -> null, route propagate; after []
else if top is catch:
  edge handler -> top.handlerPc, route exceptional
  after = stack without top
  exceptionReg becomes unknown with empty values/origins
else:
  edge finally -> top.finallyPc, route exceptional
  after = stack without top
  continuationReg becomes singleton top.throwPadPc (origin exception@sourcePc)
  payloadReg becomes unknown
```

An explicit THROW payload carries throwRegister; call exceptions carry callSitePc and the
exceptional-completion marker when propagating. Finally payload also carries finallyPc,
continuationRegister, payloadRegister and throwPadPc.

RETURN instead searches the ordered stack backwards for the nearest finalizer, skipping catch
records. Its source register is raw word 1:

```text
if no active finalizer:
  edge kind return -> null, route propagate
  payload = {returnRegister: rawWord1}; after = []; no edge writes
else let j be nearest finalizer index, record = records.get(stack[j]):
  edge kind finally -> record.finallyPc, route exceptional
  payload = {throwRegister: rawWord1, finallyPc: record.finallyPc,
             continuationRegister: record.continuationReg,
             payloadRegister: record.payloadReg, throwPadPc: record.throwPadPc}
  after = stack.slice(0, j)  // drops this finalizer and all newer records
  continuationReg then payloadReg become unknown with empty values/origins
```

The active-finalizer payload really uses `throwRegister` even for RETURN. For example,
`[olderCatch, finally@5, newerCatch]` becomes `[olderCatch]`; a stack containing only catches
becomes [] on the ordinary return. RETURN to a finalizer is an analysis completion route; the
pinned runtime's RETURN itself does not run finally, so supported source must still have
compiler-produced routing and pass H/K-M. E success alone does not establish it.

Each published edge includes kind/sourcePc/targetPc, condition, continuationPc, payload,
callSitePc, route (default direct), mode (default direct), functionId and handler states before/
after. Null target denotes propagation beyond this function. Internal extraWrites are applied
during value analysis then removed from published edges. Unknown edge writes privately carry
`exception@sourcePc` or `return@sourcePc`, but `writeUnknown` discards that metadata and clears
values/origins. It is not retained finite-value provenance. Singleton writes, such as a
finalizer's throw-pad continuation, retain their origin with the known value. No synthetic fallthrough is attached
to JUMP/JUMP_REG/RETURN/THROW. Unreachable TRY/FINALLY_SETUP records decline
unbalanced-handler-stack; ordinary unreachable instructions remain owned without edges.

Calls and THROW always carry their exceptional edge. Any other ordinary instruction inside a
protected range can throw natively (a missing global, GET_PROP on null, INSTANCEOF on a
non-callable, a throwing valueOf/toString coercion), so it carries the same exceptional edge to
its innermost catch or finalizer, with the same extraWrites. The exceptions are the opcodes
whose pinned runtime handler only moves values between registers, the constant pool, capture
cells and fresh arrays or closures: LOAD_CONST, LOAD_INT, LOAD_THIS, LOAD_UPVALUE,
STORE_UPVALUE, MOVE, MAKE_CLOSURE, BUILD_ARRAY, TYPEOF, TYPEOF_SAFE, VOID, UNARY_NOT and
DEBUGGER. Any other opcode, including one a later encoder adds, counts as throwing. Outside
protection a native exception only propagates and changes no control flow inside the function,
so no edge is modeled there.

This set models program operations only. The pinned runtime wraps each dispatch step in one
try/catch, so once a record is armed it also receives failures of the VM's own machinery (stack
exhaustion in operand or capture reads, timing-tamper poisoning, memory), which no program
operation models. A try statement is therefore one unit: each TRY_SETUP and FINALLY_SETUP also
carries the exceptional route from its own PC with the new record on the stack, the catch's
handler edge or the finalizer edge with the throw-pad continuation, and the same extraWrites as
any exceptional edge. A catch or throw pad whose body has no throwing program operation, such as
`try { declaredVariable; } catch (e) { … }`, stays reachable with its unit and keeps its edges;
nothing downstream prunes it. The setup's own route also means a JUMP into a finalizer whose
record is still armed disagrees with the setup's outer-state entry, which declines
handler-stack-merge-disagreement here.

### Register dataflow and indirect fixed point

A cell is {values:Set<u32>,unknown:Boolean,origins:Map<value,Set<origin>>}. At entry every
register is unknown with empty values/origins. Clone per transfer. LOAD_INT overwrites destination
with its raw immediate singleton and numeric source-PC origin; MOVE copies the source cell.
Every other destination write becomes empty/unknown with empty origins; rows without destinations preserve state.
Destinations are word 1 for loads, MOVE, GET/DELETE_PROP, all binary/unary/TYPEOF_SAFE rows,
calls, MAKE_CLOSURE, arrays/objects and FOR_IN_SETUP/NEXT. Stores/SET_PROP/accessor definitions
do not have a destination.

After instruction transfer, apply edge writes from the route table **in listed order** (if two
writes alias, the later write wins). Merge cells by values/origins union and logical OR of
unknown; even a known incoming path cannot remove another path's unknownness. Iterate the
register worklist until states stop changing. There is no target-set cardinality cutoff.

At every owned JUMP_REG, require a reachable input state, source unknown=false and a non-empty
value set; otherwise unresolved-jump-reg. Sort target values numerically and origin strings
lexicographically. Require each target to be B's boundary (out-of-range-target) and D's same
owner (cross-function-target). For each outer round:

```text
targets = map(all owned JUMP_REG PCs -> [])
repeat at most 32 rounds:
  stacks/edges = solve stack worklist with targets
  data/jumps = solve register worklist over those edges
  check all derived target boundaries and owners
  next = map(jump PC -> sorted finite targets)
  if targets equals next by exact arrays: finish with this stacks/data result
  targets = next
  if this was round 32: decline dataflow-nonconvergence
```

The comparison checks target arrays, not origin metadata; final origin evidence comes from the
last value solve. An unreachable owned JUMP_REG declines even if dead code would never execute.
This conservative supported subset differs from a runtime exploration algorithm.

### Blocks, irreducibility and call projection

Leaders include fn.startPc; every handler/finally target and finalizer throw pad; **every non-null
edge target**, including ordinary fallthrough; and nextPc after each terminator if within the
function. Terminators are JUMP/JUMP_REG/RETURN/THROW/JUMP_IF_FALSE/JUMP_IF_TRUE/FOR_IN_NEXT.
Sort leaders and form [leader,nextLeader-or-end) blocks from all owned instruction PCs.
A leader must begin a non-empty block, and concatenated block PCs must equal fn.instructionPcs;
otherwise invalid-basic-block. This often creates one-instruction blocks for reachable straight
line code. It is the actual representation, not a maximal-basic-block requirement.

Each block records id="functionId:b@startPc", functionId/startPc/endPc/instructionPcs,
successors from its last PC, and handlerStateIn. An unreachable leader's published state defaults
to empty, so empty state by itself is not proof of reachability.

Run a strongly connected component search over all owned PCs and non-null same-function edges,
including exceptional edges. A component is cyclic when it has multiple PCs or a self-edge.
For a cyclic component, collect distinct target nodes entered by edges from outside it. More
than one gives {startPcs,instructionPcs,reason:multiple-entry-cycle}; fn.irreducible.required=true,
fallback=state-machine. No reachability/structured rendering claim is added by the marker.

Project every owned CALL/METHOD/NEW, including unreachable ones, to pc/kind/destination/callee/
receiver, constructorState={isConstructor,mode:allocate-this|ordinary}, fixed or spread arguments,
continuationPc=nextPc, returnDestination and possible exceptionalCompletion. calleeFunctions=[]
is deliberately unresolved here; [F](build-call-frames.md) owns callee provenance. Use grammar
offsets and B's spread form (`form.kind`; the build's sentinel, 65535 in the canonical build). Exceptional completion is selected from an existing non-normal
callSitePc edge, or null for an unreachable site.

### Output, atomicity and acceptance

E contains schemaVersion/encoding and word/instruction/function counts, functions, flattened
edges/indirectTargets/callSites, copied D ownership/frame, irreducibleFunctions and source
metadata naming B/C/D schemas and function entries. Each function preserves D identity/metadata
and adds leaders/blocks/edges/indirect targets/call sites/handlerRecords/finallyRecords/irreducible
proofs. Indirect rows retain pc/sourceRegister/targets/origins, with functionId in the flattened
view. No mutable Sets/Maps or register worklist state escape.

`diagnoseControlFlow` returns frozen {ok,result,diagnostic}; `buildControlFlow` returns E or
null. The typed failures above are decode decisions; unexpected failures become cfg-builder-error.
One entire E is atomic: a later function failure returns no earlier function graphs. B/C/D remain
unchanged, no source helpers are removed, and private analysis maps are discarded on decline.
Normalizers may deliberately defer E while preparing a still encoded control stream, but final
semantic analysis/publication requires a successful current E.

### Testing and acceptance

| Scenario | Observable result / oracle | Acceptance criterion | Retained fixture/control |
|---|---|---|---|
| E1: local branches/loops/calls | Exact edge kinds/continuations/ownership and frozen states. | No unconditional-terminator fallthrough, unchanged B-D; graph recovery assertions. | CFG test, reference, branching/loop/closure fixtures. |
| E2: finalizer indirect targets | Finite sorted targets/origins and stack routes. | Local boundary proof plus subsequent H routing acceptance. | CFG finally fixture; owned-chain indirect/source controls. |
| E3: source target/setup damage | E first unresolved-jump-reg/out-of-range-target/cross-function-target/unbalanced-handler-stack; public cfg-declined. | Named first check reached after A-D success; no partial graph/output. | Owned-chain unknown/inside/outside/cross-owner indirect targets, unreachable finalizer setup. |
| E4: stack merge/pop/call terminal/32-round limit | Exact named diagnosis, no partial graph. | Reach named decision through source entry. | Dedicated retained normal-entry controls missing. |
| E5: irreducible and owner-range edges | Correct SCC marker, owner-refinement behavior. | State-machine marker retained; selected register omissions stay explicit. | Structured-control test builds a synthetic B-E multiple-entry cycle; direct owner-range source control is missing. |
| E6: native operation exceptions | Every protected instruction outside the non-throwing set has its catch or finalizer edge; unprotected native throws have none. | Exact edge inventory on a finally/catch corpus fixture; call-free try bodies reach their handler. | build-cfg finally/abrupt inventory (f-finally-abrupt); corpus raw f-global-resolution and f-instanceof-errors (call-free try bodies) through public recovery. |
| E7: document-only reduced E reconstruction | Asserted direct/finite-indirect targets and origins, catch-stack transitions, named refusals, unchanged/frozen supplied records and later-function atomic failure. | Freeze implementation/results before source consultation; progress oracle rejects passthrough; credit only asserted projections. | Retired frozen verifier |

Graph/indirect assertions would fail for passthrough; behavior is a separate regression oracle.
Historical corpus qualification is bounded by the [provenance contract](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/qualification-provenance.md).
The worked example is synthetic arithmetic. E7 used one independent agent, these seven candidate
pages, the declared Babel/encoder foundation documents and generic Node/JavaScript infrastructure.
Synthetic B-D consumed fields were supplied from the documented grammar/contracts; their parsers,
validators, admission and complete schemas were not reconstructed. The comprehension/plan and
then executable/results were frozen before source consultation. The verifier retains the literal
inputs/oracles, and rerunning it reproduces the run. This is synthetic validation
of a reduced graph subset, separate from actual source qualification and no novice reader study.
Later corrections to these documents do not change the frozen verifier.
In particular its RETURN defaults to route=direct and omits payload; its oracle did not assert
those fields. E7 therefore supplies no proof of the exact production RETURN metadata above.

## 4. Input Shapes

E consumes B instructions, C label metadata and D interval/owner facts. [F](build-call-frames.md),
[G](closure-lifetimes.md) and [H](exception-finally.md) use its control/call/stack/provenance
facts; E does not repeat the source, grammar or ownership proofs.

| Earlier decoder output / origin | Producer-owned inventory | E handoff |
|---|---|---|
| New canonical compact/expanded words and D, ours | [B producer map](read-wordcode.md#4-input-shapes), [D dependencies](partition-functions.md#4-input-shapes) | Rebuild E when any consumed control fact changes. |
| Preliminary dispatcher/control rewrite, ours | [Dispatcher](normalize-dispatcher-wordcode.md#3-implementation), [CFF](normalize-cff-wordcode.md#3-implementation) | cfg:null can defer this proof for helper preparation; caller fills it before F. |
| Helper removal and pool/capture repair, ours | [String inverse](normalize-string-concealing.md#address-remapping-atomicity-and-derived-state) | Returned B-D precede a new E; old graph cannot survive relocated PCs. |

[Diagnosis](standalone-diagnosis.md#canonical-frontend-retries) reuses returned successful E,
building one only when absent. PC relocation must update direct target words and proved
LOAD_INT address origins before rebuilding; ordinary integers are not all addresses.

## 5. Known Gaps

- Unknown/unreachable/non-boundary/cross-owner JUMP_REG and nonconverging target refinement
  decline. There is no dynamic discovery or arbitrary arithmetic evaluator for indirect values.
- Owner-range preflight currently omits unary source registers and TRY_SETUP.exceptionReg, and
  C no longer bounds registers, so nothing bounds them. A direct owner-range source control and consumer audit
  remain required before claiming full owner-bound validation. No production fix is made here.
- Explicit THROW/call exceptions do not form an exhaustive native-operation exception graph.
  Finalizer bypass/continuation validation belongs to H, not E success; re-entry into an armed
  finalizer is an E handler-stack merge refusal.
- E4 and owner-range E5 source controls are missing. The current CFG test proves corpus
  success/finite targets/state freezing; the structured-control test supplies a synthetic
  irreducible B-E graph. No retained encoder-produced irreducible admission fixture is claimed.
- E7 reconstructs only its asserted direct/finite-indirect targets/origins, catch-stack and
  refusal/state decisions from synthetic supplied B-D. It omits owner preflight beyond the small
  supplied register forms, finalizers, full call/block/SCC projections, complete production
  schemas and A-D/source admission. Its unasserted RETURN
  route=direct/no-payload differs from production, so exact RETURN metadata is excluded from
  this reconstruction claim. Synthetic stack controls do not retire E4's missing normal-entry
  controls. Optional combinations, native exception coverage and actual encoder qualification
  remain separate; no full E/frontend or novice reconstruction is claimed.
- Irreducible marking does not emit or certify structured output. Ordinary dead instructions can
  remain; unreachable setup/JUMP_REG is specifically refused. No whole-system proof is claimed.

## Source

The public stage is [build-cfg.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/build-cfg.js). Supporting modules are [build-cfg-wordcode.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/build-cfg-wordcode.js), [build-cfg-preflight.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/build-cfg-preflight.js), [build-cfg-edges.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/build-cfg-edges.js). The [standalone diagnosis](standalone-diagnosis.md#canonical-frontend-retries) wires E after the current B-D and control normalization, as forced by item 4. Pinned runtime interpretation is declared through the [instruction semantics dependency](../../../js-confuser-vm/instruction-set.md#catch-finally-and-abrupt-completion); E routing remains the analysis contract in item 3.

## Fixtures

| Committed fixture or test control | Claim pinned |
|---|---|
| [f-branching](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/raw/f-branching/encoded.js) | Conditional branch targets and local normal-flow edges. |
| [f-loop-forms](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/raw/f-loop-forms/encoded.js) | Loop backedges, exits, and block leaders. |
| [f-finally-abrupt](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/raw/f-finally-abrupt/encoded.js) | Nested exceptional routes, continuation `JUMP_REG` targets, and handler-stack merges. |
| [build-cfg.test.js](../../../../decoder/decode-js/test/vm/jsconfuser-vm/build-cfg.test.js) | E1/E2: exact reference/call/finally graph projections, finite indirect targets, corpus success and frozen unchanged predecessors. E4 and owner-range E5 controls are absent here; synthetic irreducibility is in the structured-control test. |
| [emit-structured-control.test.js](../../../../decoder/decode-js/test/vm/jsconfuser-vm/emit-structured-control.test.js) | E5: retained synthetic words [40,0,5,39,5,39,3] build B-E and assert the multiple-entry-cycle marker before K fallback; not source/encoder admission. |
| [owned-chain-source.test.js](../../../../decoder/decode-js/test/vm/jsconfuser-vm/owned-chain-source.test.js) | E3: unknown/inside/outside/cross-owner indirect targets and unreachable finalizer setup reach their exact E diagnostic first, then public cfg-declined. |
| Retired `verify-jsconfuser-vm-cfg-spec.mjs` | E7: frozen one-agent document-first reconstruction and retained run for asserted reduced-E synthetic projections/refusals/state/atomicity. Supplied B-D, omitted production fields and the unasserted RETURN discrepancy bound this evidence as stated above. |
