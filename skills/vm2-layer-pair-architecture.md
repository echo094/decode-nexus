# Layer-pair recovery architecture

## Decision and evidence boundary

This is the target-local design for layer-pair recovery and simplification in
`decode-js`. It specifies proof obligations, not newly implemented support.
The [layer-pair contract](vm2-layer-pair-contract.json) owns fixture production and execution
limits; the [parent comparison](cross-decoder-study.md) owns product comparisons and acceptance.
Neither fixture identifiers, identifier spelling, corpus constants nor reference output may be
recognition inputs. Derive every relationship below from the input being decoded.

The [sequential boundary test](../decoder/decode-js/test/vm/jsconfuser-vm/integration/sequential.test.js)
checks that a parsed outer handoff may still decline at the VM-container boundary and that
the coordinator rolls back to its exact input. A bounded fixture cannot establish universal
equivalence or identify an inner recognizer deficit.

Use a validated machine model plus definition-level analysis and an explicit
instruction-disposition ledger behind an atomic source-to-source boundary. A concrete CFF patch
or exact-target handler normalization requires separate evidence.

This design alone authorizes no production edit, exact recovery, VM2-213 generation, decoder
execution or transfer qualification. VM2-213 remains gated on exact VM-2 acceptance.
No source replacement from a reference program is permitted.

### Supported runtime scope

The proposed benchmark recovery targets ordinary Node and browser execution with standard
JavaScript built-ins at entry.
It does not model arbitrary prior host mutations, exotic proxies, or a particular historical
run. Preserve the input's own environment branches and its observable ambient reads, calls,
writes, exceptions and order as runtime operations in the decoded output. If the input itself
mutates a built-in or host-visible object, preserve that mutation. Do not evaluate an ambient
value during decoding and substitute the value observed in one test environment.

This bounded runtime profile removes the historical host-record prerequisite. It does not
remove the need to recognize the live VM entry, decode its machine and prove that replacing
its handlers preserves the operations they perform. Unsupported machine semantics or a
runtime dependency the decoder cannot retain must decline with exact input rollback.
Representative Node and browser executions are regression checks for the admitted profile,
not a census of possible host histories.

## Independent stages and source-derived dependencies

Composition remains `original bytes -> jsconfuser -> source text -> fresh VM parse -> VM recovery
-> final source`. The conventional plugin owns conventional shapes; the VM target owns wordcode,
handler semantics, opcode/slot relationships, concealed VM constants and frame/capture behavior.
A coordinator must not fabricate a canonical-looking VM container or share Babel paths, bindings,
helper pools or mutation state across the text boundary.

Before a stage is extended, its owner records a dependency table: source mechanism and producer
revision, required input shape, producing decoder operation, consumed facts, invalidated facts,
output contract, and refusal condition. Read producer order and actual matcher gates before
selecting the order; test observations establish correctness, not the order itself. A stage
whose prerequisites are unavailable is unresolved, not proven unsupported.

The current [standalone composition](../decoder/decode-js/src/vm/jsconfuser-vm/decode-standalone.js)
provides the dependency spine: container extraction, wordcode decoding, reference validation,
function partition, CFG, frame/call analysis, capture and exception analysis, scalar/property
analysis, control/call/closure completion plans, then emission. Proposed value optimization consumes
these validated analyses; it cannot precede or replace their coverage checks. Capture and exception
analysis both depend on frames and CFG; scalar facts alone do not authorize effects or completion
rewrites. Emission consumes one mutually consistent model version.

For a demonstrated noncanonical representation, record additional source-derived dependencies
before normalization: how dispatch selects handlers, how each handler reads operands, how encoded
payload/constants are recovered statically, and how those facts determine boundaries and references.
Resolve a prerequisite before its consumer. Cyclic or ambiguous facts require a bounded joint proof
or decline, not guesses from a familiar opcode table. A VM feature whose static prerequisite cannot
be established stays outside the accepted set.

## Validated machine representation

Use immutable records with input/model identity and stable structural IDs, independently of AST
names and source offsets. AST provenance can locate evidence but is not the identity proof. Each
record names its validated predecessors; a schema tag or claimed `complete: true` is insufficient.

| Record | Required relationships |
|---|---|
| Container and dispatch | The live entry invokes this interpreter; program counter, register/frame storage, constant storage and dispatch belong to this machine. All dispatch arms and aliases are accounted for; no unmatched live runtime mutation or competing writer changes their meaning. |
| Handler semantics | Dispatch selector maps to a verified operation with operand order, width, reads, writes, effects, possible exceptions and completion behavior. Specializations or aliases require their own equivalence proof; matching a number or handler name is insufficient. |
| Instruction | Unique machine/function/PC identity, complete word interval, decoded operands, handler proof and next-PC rule. Word intervals cannot overlap or leave unexplained payload; distinguish data from instructions structurally. |
| Operand and reference | Register indices and constant indices have validated domains; register reads/writes have explicit roles. Branch/catch/finally/closure targets land on valid boundaries in the correct function; argument ranges, arities, capture pairs and sentinels are checked. |
| Function and frame | Entry, parameters, receiver, frame lifetime, return destination and closure target agree with call sites and partition. A nested function is a separate analysis domain even when storage indices repeat. |
| Control and completion | Normal and exceptional edges, computed targets, fallthrough, calls/returns, catches, finally entry/resumption and abrupt completion replacement agree with instructions and frames. Every completion route is accounted for. |

Validate the full recognized machine before optimizing. Keep current structural and unsupported
instruction guards unless a separately reviewed shape contract replaces them. In particular,
unknown reachable semantics always decline; the new unreachable disposition is no permission to
skip word decoding, handler validation or reference checking in dead regions. Dynamic patching or
unbounded computed dispatch cannot be accepted by pretending its observed targets are complete.

## Values, reaching definitions and liveness

A register number denotes a storage location, not one value. Create a definition for every write,
identified by function, instruction and write position, plus explicit parameter/entry definitions.
A read names its reaching definition set. Unknown or potentially uninitialized entry contents are
explicit values with the machine's actual semantics, never invented constants. Model a read/write
instruction in evaluation order: read operands use the pre-write state.

Compute forward reaching definitions to a fixed point over the complete intra-function graph.
At a join, union each predecessor's definitions; preserve predecessor identity in a merge value.
Loop headers include backedges. On exceptional edges, use the state at the throwing operation,
including only writes known to occur before it throws; never propagate an unconditional destination
write to a handler. If that timing is unsupported, keep conservative sets or decline the rewrite.

Compute backward liveness over the same edges, including return/throw values, branch tests,
receiver/argument uses, captured cells, handler inputs and finally continuation state. A kill removes
only the definition overwritten on that route, not every lifetime of that register. Merge operands
are live on their own predecessor edges. Calls conservatively use/mutate escaping cells and unknown
memory; they need not invalidate unrelated private register values when the frame proof establishes
that isolation. Recompute after accepted transformations until stable, with a bounded termination
policy; nonconvergence declines the optimization, never silently truncates a proof.

Optimization is initially restricted to private, noncaptured scalar definitions in a validated
function. Its planned operations are pure dead-definition elimination, copy-chain propagation,
noninterfering destination coalescing and expression formation with preserved evaluation order.
Each accepted operation must record its definitions, uses, affected edges and proof:

- A dead definition has no live use on any normal, exceptional or completion route, and its
  evaluation is removable under the effect rules below. Dead storage is not proof of dead effects.
- Propagation replaces uses only where the same value reaches them on every feasible predecessor.
  At a join with different definitions, retain assignments/merge storage. Equal constants may merge
  only with proven same-value semantics, including `NaN`, negative zero and identity distinctions.
- A copied private value can cross register reuse only if the referenced definition stays available.
  For `a = value; b = a; a = other; use(b)`, replacing `b` by current storage `a` is forbidden.
  Either use a stable value representation or retain the copy. Whole-register read counts cannot
  decide this, which bounds the current emitter's `adjacentCopyPlan`.
- Destination coalescing proves absence of interference on all routes, including handler reads of
  the old destination if the producer throws. Removing the adjacent move alone is not that proof.
- Expression inlining proves dominance, operand availability, identical execution count/order and
  completion region. It may not duplicate an effect or move a potentially throwing expression from
  before a branch into only one arm. Parallel merge copies need cycle-safe lowering with temporary
  storage when necessary; no speculative lowering is required to simplify a supported function.

The result must retain a clear reason for definitions left behind: live value, ambiguous merge,
capture identity, effect/exception barrier, or unsupported optimization shape. A sound unoptimized
emission is allowed, but residual eligible definitions inside the declared optimizer domain fail
that domain's simplicity acceptance. Do not broaden the domain by calling every opcode pure.

## Effects, captures and completion barriers

Represent effects independently of destination liveness: private reads/writes, captured-cell
reads/writes, heap/global reads/writes, allocation/identity escape, calls, possible throws,
receiver use and completion changes. Unknown is effectful and potentially throwing. Operator syntax
is not a purity certificate: property access can call a getter/proxy, arithmetic/comparison can
coerce an object, global access can throw, and allocation can expose identity. Begin with literal
loads, proven private copies and total operations on proven primitive domains; extend with evidence.

Preserve left-to-right evaluation, number of evaluations, getter/setter and coercion order,
strict-mode write failure and delete semantics. An unused result of an effectful operation still
needs its operation emitted. It is `emitted`, with no destination if that lowering is proven,
not `safely-eliminated`. Keep Reflect-based helpers unless the replacement proves all those
observable behaviors, including boolean failure versus throwing behavior.

A method call's receiver is a value relationship separate from the callee. Preserve the difference
between member invocation, detached invocation, explicit apply/call and construction; do not turn
`obj.method()` into a detached function call or reconstruct a member read twice. Retain receiver
wrappers where proof is absent. Receiver-independent inlining needs a proof about the called
function, not a name-based assumption that it is a decoder helper.

Capture cells retain location identity, not just their current contents. Model creation, binding,
reads/writes, aliasing across closures, escape, close/termination events and post-return lifetime.
Initially exclude all captured/escaping registers from scalar substitution and coalescing. Removing
a capture cell later needs proof that every closure and external call sees the same lifetime,
identity and updates; a zero local read count cannot prove that.

Treat return, throw, break/continue-like VM transfers, call completion, catch and finally routes as
explicit semantic edges. Finally may replace an earlier return/throw; pending completion values and
resume targets stay live until the selected route consumes or replaces them. Calls that throw must
enter the same handler with the same visible state. Do not move definitions across handler setup,
finally boundaries or unknown calls without a route/effect proof. Unsupported routes decline whole
recovery; irreducible but fully modeled control can retain a justified state machine.

## Complete dispositions without dead-code printing

After validation, give every instruction exactly one disposition. The expected inventory is the
validated instruction set, not the set visited by the emitter. Sets are disjoint and their union
must equal that inventory; validate IDs and proofs, not just counts.

| Disposition | Proof and emitted result |
|---|---|
| `emitted` | Semantics are represented by a statement, expression, structured edge or justified helper/state machine. Record output-node/region mapping; fused expressions can cover several instruction IDs, each explicitly. |
| `proven-unreachable` | No path from any admitted entry reaches the instruction using the complete normal, exceptional and completion graph. Record roots, graph identity and reachability proof; emit no dead-code surrogate. |
| `safely-eliminated` | The reachable instruction is redundant under a named optimization and its value/effects/completion proof. Record surviving value/output provenance and eliminated uses as applicable; emit no surrogate. |

Maintain a block ledger derived from its instructions and control edges. An all-unreachable block
has a reachability certificate. An entirely eliminated reachable block needs edge redirection and
completion preservation proofs; a mixed block records its per-instruction dispositions rather than
being falsely labeled all emitted or dead. Record edge and completion-route dispositions separately;
source coverage is not textual statement coverage. Verify capture and handler inventories too.

Analyze reachability from every admitted function entry, closure/call target and external entry
allowed by the container contract. Include catch/finally entry and conservative computed successors.
Do not infer whole-function deadness from absence of observed calls. Removing a branch on a constant
requires proven value and evaluation effects; then rebuild the CFG and revalidate routes before
claiming new unreachable blocks. Unknown edges cannot become absent edges.

The current `emitUnreachableBlocks` prints leaves under `if (false)` to satisfy emitter coverage.
Replace that accounting only when the new ledger and its negative tests are accepted. Do not weaken
predecessor coverage fields or label omitted instructions emitted. Version changed result semantics
explicitly so existing adapter/report consumers cannot confuse total accounted instructions with
textually emitted instructions.

## CFF and String Concealing handoff audit

An outer-handoff repair starts with a conventional visitor investigation. The current
[conventional schedule](../decoder/decode-js/src/plugin/jsconfuser.js) visits String Concealing
before and after graph CFF and shares a dependency pool across visits. Thus a retry or scope crawl
that happens to green the sample is not itself a causal explanation.

Before any production edit, retain an audit of the first failing reconstruction:

1. Recheck the frozen input/configuration and the report's before/after hashes; keep original
   bytes unchanged. Follow the malformed callee and argument by binding and definition through the
   graph reconstruction, nested function lifting, scope-member flattening and wrapper collapse.
   Capture the exact mutating operation that changes their relationship, not only the stage label.
2. Compare lexical binding identity, shadowing, initializer/write order, helper receiver and argument
   evaluation before/after that operation. Trace live String Concealing wrapper, decoder and table
   dependencies as complete entities, including their initialization and cleanup. State whether a
   callable was replaced/shadowed, receiver semantics changed, or another obligation failed.
3. Check the live AST and derived state immediately after the mutation and against a strict fresh
   parse of emitted text. Compare scope ownership, declaration/reference/write membership and
   dependency-pool reachability. Detached cached nodes do not become valid because they still have
   a parent chain. A reparsed consumer success with live-tree failure is a derived-state deficit.
4. Separate wrong producer output/state from a correct producer whose consumer input is not yet
   available. Fix the responsible mutation for the former; propose scheduling only after proving
   the operation correct and identifying the unavailable prerequisite. Route missing facts to
   their owner before widening a consumer. Audit other consumers if a shared operation is implicated.
5. Freeze the unseen positives and near-miss negative below, demonstrate that the asserted
   mechanism is reached, and retain baseline results before production edits. Record proposed
   change scope, supported spellings, refusal conditions and tests for independent acceptance.

The report does not settle the operation, receiver proof, complete concealed constants or machine
correspondence. If this audit cannot distinguish causes, stop at that bounded decision and name the
missing differential evidence. Do not special-case the reported callee or insert a VM adapter into
CFF/String Concealing. A repaired exception alone is insufficient: rerun strict parsing, live
residue census, machine/constant/handler/payload correspondence, bounded intermediate behavior and
downstream VM diagnosis. Remaining conventional residue retains an unresolved outer boundary.

## Fresh state and atomic publication

Every AST mutation owns invalidation/rebuilding of the state its consumers read. Verify live node
reachability, scopes, bindings, references and constant writes against a fresh parse using structural
correspondence rather than cross-tree object identity. Rebuild candidate pools after invalidation
or prove each retained member live. Add this assertion to the shared harness before repairing an
invisible state defect. A text round-trip alone is insufficient.

Within the VM stage, rebuild dependent CFG, reachability, use/definition, liveness, frame/capture,
effect, completion and disposition projections after changes. Check record identities and exact
sets against source-derived predecessors; intentionally stale records must be rejected. Strictly
parse final emitted JavaScript, then validate output mappings, residual machinery and route/effect
obligations. Parsing cannot replace semantic model checks.

Keep original input bytes independently of working text. Analyze and emit into private candidate
state; no caller-visible source changes until all required stages and checks succeed. Null outer
output, exceptions, worker/resource limits, invalid intermediate, VM decline, unknown semantics,
incomplete dispositions or invalid final output all publish the exact original bytes. Direct VM
use preserves its own input; composed use preserves the original outer input, never the intermediate.
Diagnostics and optional intermediate artifacts are separate from final output. A smaller or changed
outer result is neither necessary nor sufficient for success. Decline is not recovery credit.

The coordinator must define its caller contract before implementation: registration, immutable result identity,
one output/result record, per-stage status/diagnostic, input/intermediate/final provenance and safe
file publication/error behavior. Recovery atomicity is distinct from filesystem failure handling;
never report a partially written artifact as successful. Preserve existing direct-target contracts.

Safety is stage-scoped: VM recognition/analysis/emission never execute target or recovered code;
the conventional plugin can evaluate extracted helpers in `isolated-vm`. Report helper execution
capability/actual status separately from VM execution and bounded oracle activity. Apply the
contract's worker limits to helper-executing stages. Byte rollback cannot undo execution effects;
Node `vm` is not a security boundary. Behavioral oracles are controlled test activity with retained
inputs and declared effects, never a runtime recovery strategy.

## Fixture and acceptance obligations

Freeze decoder-owned controls before comparisons. Record revisions, exact input
lineage/options/harness randomness, hashes, actual mechanism populations, structural assertions,
bounded behavior and expected diagnostics. Generation is separately scoped fixture production, not
an implicit test dependency. New controls cannot invoke VM2-213 before exact VM-2 acceptance.

| Requirement | Evidence required |
|---|---|
| Outer-handoff positive A | Independently produced nested CFF with live String Concealing and a different source/helper use topology from the baseline control; prove binding-resolved mechanism population and the audited handoff. Retain source and all relevant intermediate bytes before patching. |
| Outer-handoff positive B | Another independent topology exercising scope/name reuse or nested helper capture/receiver relationships at that handoff. A new seed of the same source alone is insufficient; use independent source and randomized spellings. |
| Outer-handoff near-miss negative | Change one proof-critical binding, write, receiver or escape relationship while retaining the candidate shape. Assert the responsible refusal diagnostic or unchanged unsafe-to-rewrite region, plus bounded behavior. A malformed parser input does not exercise this guard. |
| Definition optimization | Positive straight-line copy chains, register reuse, equal-value joins and loops within the declared domain; negative differing joins, use before definition, source overwritten after copy and throwing producer with old destination live in a catch. |
| Effects and captures | Paired removable pure definitions and unused-result getter/coercion/call/strict-write operations that must remain; receiver-sensitive calls, constructor behavior, escaping closures and shared-cell updates. Assert effect count/order, exception and result. |
| Completions | Return/throw through finally, finalizer replacing completion, call throw into handler, loop exit and supported irreducible control. Mutate a route or handler target to verify precise fail-closed validation. |
| Dispositions | Unreachable valid blocks disappear; reachable pure dead definitions disappear; effects remain. Deliberately omit, duplicate or misclassify an instruction/block/edge and require rejection even when totals match. Include an exception-only reachable block. |
| Machine relationships | Positive independently renamed/reordered accepted shapes; negatives for wrong handler width/operand roles, missing dispatch relationship, bad targets/captures/arity, stale predecessor and unknown reachable operation. |
| Atomic boundary | Outer null/throw/limit, invalid intermediate, VM decline, incomplete output and final parse failure preserve exact original bytes with the correct stage diagnostic; successful unchanged-outer handoff remains possible. |
| Derived state | Live-tree versus fresh-parse equivalence at producer mutations; stale binding/candidate/CFG/use/route/disposition records rejected at the consumer that reads them. |

For every targeted negative, assert the intended mechanism or guard, and a neighboring positive
that passes that guard; otherwise an earlier unrelated rejection can falsely certify coverage.
Compare actual emitted output, not a handcrafted expected substitute. Simplicity acceptance requires
ordinary expressions/control, no outer or VM/handler/wordcode residue, no dead-code printing, and
explicit reasons for residual helpers, captures, wrappers and state-machine control. Formatting,
naming or a historical size baseline alone cannot certify it.

Before **any** production edit, the change needs accepted architecture, explicit owner/scope,
source-derived input/output/dependency contracts, baseline evidence and positive/targeted-negative
controls for the change. A conventional repair additionally needs the mutation-level audit and the
report's unseen controls. A VM extension additionally needs complete handler/operand derivation for
the new shape. After edits, require relevant targeted and conventional/VM regressions, off-target
consumer checks for shared changes, fresh-state and rollback checks, and independent integration
review. Integration acceptance requires a supported end-to-end control after accepted outer
qualification or repair. VM-only simplification cannot repair a semantically wrong outer
intermediate. Exact outer and inner representations need their own qualification before actual
final output is compared with the reference retained for that run. Exact acceptance does not imply
independent-profile coverage.
