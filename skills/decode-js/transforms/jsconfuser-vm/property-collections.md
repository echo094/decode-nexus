# jsconfuser-vm property and collections

## 1. Target

`analyzePropertyCollections(wordcode, references, functions, cfg, frames)` is the target-local,
parse-only property/collection analysis for the visible numeric-u32
baseline. It returns the immutable `jsconfuser-vm-property-collections.v1` IR after exact
reconstruction of the canonical wordcode, reference, function, CFG, and frame predecessors. `diagnosePropertyCollections` reports the same fail-closed
decisions. It describes operand roles, evaluation order, mutation descriptors, and iterator
edges; it does not execute property access or infer dynamic values.

## 2. Algorithm

The analysis copies and reconstructs the canonical predecessor records, then requires exact equality of
their schemas, owners, widths, references, frames, and CFG facts. It emits one immutable
operation row for each of the following eleven opcode leaves:

| Family | Operations |
|---|---|
| Property | `GET_PROP`, `SET_PROP`, `DELETE_PROP`, `IN`, `INSTANCEOF` |
| Collection | `BUILD_ARRAY`, `BUILD_OBJECT` |
| Accessor | `DEFINE_GETTER`, `DEFINE_SETTER` |
| Enumeration | `FOR_IN_SETUP`, `FOR_IN_NEXT` |

Typed roles preserve evaluation order: `GET_PROP`/`DELETE_PROP` evaluate object then key;
`SET_PROP` evaluates object, key, value; `IN` evaluates property key then object;
`INSTANCEOF` evaluates instance then constructor; array payloads preserve element order;
object payloads preserve key/value pair order; accessor rows preserve object, key, and
function; and enumeration rows preserve source/iterator and exit-label roles. The historical
`FOR_IN_NEXT.wordOperands` compatibility shape remains destination, label-target, register,
while its typed semantic operands are destination, iterator, exit label.

Serialized widths are exact: `FOR_IN_SETUP` is a fixed width-three instruction and
`FOR_IN_NEXT` is fixed width four; array/object/accessor payloads retain their variable
payload boundaries. `FOR_IN_SETUP` records the iterator effect. `FOR_IN_NEXT` records its
conditional write/increment on the normal iteration path and its exit jump without claiming
that a key exists on the exit path. Property mutation rows retain Reflect/set, delete, and
descriptor intent as structural effect data, not as an executed result.

## 3. Implementation

The implementation validates copied canonical predecessor inputs, exact predecessor reconstruction,
owner and reachability maps, instruction width and payload boundaries, and the exact J
census. It verifies the special normal/exit CFG edges for `FOR_IN_SETUP` and `FOR_IN_NEXT`.
Results, nested role arrays, diagnostics, and census records are deeply frozen; input objects
are not mutated. Dynamic object/key/value/constructor behavior remains unknown, including
prototype lookup, proxies, coercion, getters, and host exceptions.

## 4. Upstream Effects

| Producer or consumer | Contract used here or carried forward |
|---|---|
| wordcode/reference/function/CFG/frame predecessors | Supply exact instruction, constant/reference, frame, owner, predecessor, and CFG facts; this analysis revalidates them from copied inputs. |
| [scalar-values](scalar-values.md) | Owns scalar leaves used by later composition; this analysis does not duplicate scalar value-state claims. |
| [structured-control](structured-control.md) | Owns the control plan and carries the iterator edge shape as a later semantic leaf; this analysis emits no control syntax. |
| [standalone-diagnosis](standalone-diagnosis.md) | Calls the analysis during fresh predecessor reconstruction before collection/accessor/for-in JavaScript emission. |

The analysis's output is a typed collection/property record set, not an AST edit and not a
runtime observation.

## 5. Known Gaps

No dynamic property execution, prototype enumeration observation, accessor invocation,
receiver coercion, constructor validation, or host/proxy equivalence is inferred. Upvalues,
calls/completion, closure/exception semantics, structured emission, `PATCH`, `DEBUGGER`,
and target execution remain later boundaries. These limits are intentional fail-closed
boundaries for the visible baseline, not evidence of support for hardened or concealed input.

## Source

The stage is implemented by [property-collections-operands.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/property-collections-operands.js), [analyze-property-collections.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/analyze-property-collections.js). The [standalone diagnosis](standalone-diagnosis.md)
composes its result with predecessor records. The encoder contracts are described in
[instruction-set.md](../../../js-confuser-vm/instruction-set.md) and
[container-wordcode.md](../../../js-confuser-vm/container-wordcode.md).

## Fixtures

| Committed fixture or test control | Claim pinned |
|---|---|
| [f-accessors-and-methods](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/raw/f-accessors-and-methods/encoded.js) | Accessor definitions, method/property roles, and evaluation order. |
| [f-for-in-enumeration](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/raw/f-for-in-enumeration/encoded.js) | `FOR_IN_SETUP`/`FOR_IN_NEXT` operands and the iteration/exit edges. |
| [f-expression-mutation](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/raw/f-expression-mutation/encoded.js) | Property mutation and deletion operation roles. |
| [f-instanceof-errors](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/raw/f-instanceof-errors/encoded.js) | `INSTANCEOF` operand roles while leaving dynamic errors unresolved. |
| [analyze-property-collections.test.js](../../../../decoder/decode-js/test/vm/jsconfuser-vm/analyze-property-collections.test.js) | Committed synthetic controls for variable payloads, malformed/stale declines, and immutable analysis results. |
