# Lower the numeric program onto the VM switch model

Pipeline stage: `diagnose-and-lower` ([map](../../pipelines/jsconfuser-vm.md)).

## 1. Target

Convert the admitted numeric program into the
[VM switch model](../switch/vm-switch-boundary.md), the typed handoff the shared backend reads.
`numericToVmSwitch(model)` takes the successful
[diagnosis model](standalone-diagnosis.md#handoff-model) and returns `decode-js-vm-switch.v1`:
one typed case per instruction, the frames shared from `partition-functions`, and the storage rows.
It replaces each opcode and operand list with a typed operation: a constant reference becomes a
primitive value, a call count becomes an ordered register list, and a branch becomes an explicit
target plus polarity. By the [boundary's ownership test](../switch/vm-switch-boundary.md#ownership-test) this
is the frontend's last step: after it nothing reads an opcode, a pool key or the interpreter.

It projects owned facts rather than revalidating private record objects: operand roles, constants
and function ownership are already established by the
[predecessor chain](standalone-diagnosis.md#predecessor-chain). Lowering makes every
[model field](../switch/vm-switch-boundary.md#model-fields) true; the backend reads them as given.

Readers need the boundary's [operation grammar](../switch/vm-switch-boundary.md#typed-operation-grammar)
and the [instruction set](../../../js-confuser-vm/instruction-set.md) it maps from.

## 2. Algorithm

For each `partition-functions` frame, read the ordered successful `read-wordcode` instructions
`{name,pc,nextPc,operands}` in `model.instructionsByFunction.get(fn.id)` and lower each one, keeping
its PC and next PC. Each operand is already a typed object, not a raw numeric word, so
lowering selects fields: register, pool and capture indexes use `.index`, label operands use `.pc`,
immediate operands use `.value`, and spread selection uses `.kind`. A constant reference uses
`.index` into `model.constants` (`validate-references`'s resolved values); lowering does not decode
a raw pool pair or key. The source proof and operand grammar belong to the owned chain.

The one compiler-layout fact lowering adds is a catch's `layoutEnd` (section 3).

### Worked example: one load

A source-informed synthetic example, showing field consumption, not a complete numeric model or
source admission. `read-wordcode`'s instruction lowers to a case:

```js
// read-wordcode instruction
{
  name: 'LOAD_INT', pc: 0, nextPc: 3,
  operands: [{ kind: 'register', index: 0 }, { kind: 'immediate', value: 7 }],
}
// lowered case
{
  pc: 0, nextPc: 3,
  operation: { kind: 'assign', destination: 0, value: { kind: 'literal', value: 7 } },
}
```

A branch's `{kind:'label-target',pc:9}` becomes `target:9`; JUMP_IF_FALSE supplies the string
`when:'false'`.

## 3. Implementation

### Operation lowering

LOAD_INT uses the immediate value; VOID becomes undefined without a read of its encoded source. The
unary-minus opcode is `UNARY_NEG`, not `NEG`; the other spellings are `UNARY_POS`, `UNARY_NOT`,
`UNARY_BITNOT`. EXP becomes the binary operator `**`. BUILD_ARRAY drops its count operand and maps
the remaining registers; BUILD_OBJECT reads pair count `.value` and makes ordered index pairs.
MAKE_CLOSURE reads child entry `.pc` and the capture `{kind,index}` pairs after its six fixed
operands; child frame shape was already established by the owned records.

CALL/NEW use destination `.index`, callee `.index`, count at offset 2 and argument tail after it;
CALL_METHOD uses destination, receiver, callee, count at offset 3 and argument tail. Count
`kind==='spread-sentinel'` selects `array-register`; its canonical sentinel is 65535, but the
lowerer does not compare a raw numeric operand to 65535. Otherwise it selects `fixed`. The argument
list is the ordered tail's `.index` values. NEW uses `construct/none`, CALL_METHOD uses
`apply/register`, and a plain CALL uses `apply/none`: the source's `f(...)`. The interpreter calls
its own closures with its globals as `this` and applies a host function to null; that split is its
machinery, not the program's ([boundary](../switch/vm-switch-boundary.md#the-source-program-not-the-interpreter)), and the rendered
closure shell already maps a null `this` to `globalThis`. So lowering reads no call record.

### The catch layout hint

A `catch-setup` also carries `layoutEnd` wherever the compiler's normal exit of its try block,
`TRY_END; JUMP after_catch`, is compiled immediately before the catch entry: the jump's target,
where the source closed the statement. The [statement planner](../switch/vm-switch-statements.md#try-end)
applies it only to a try with no reachable end, whose block always throws.

**Why this one fact is read from dead code.** When a try block always throws, the program reaches
the code after the statement only by falling out of the catch. Every reachable path then says the
same thing for "after the catch" and "the catch's own tail", so no reachable instruction records
where the source closed the try. The compiler's normal exit is the one record left, and it is dead
there: the throw comes first. So the hint is read from layout, never from reachability, and only
here, in the frontend, which knows this compiler's grammar: the exit is the pair compiled right
before the catch entry. The [shared backend](../switch/vm-switch-boundary.md) reads no unreachable
case; it takes `layoutEnd` as a supplied fact, as it takes any other model field.

Worked example: the plain compile (options `{}`, seed 1, the encoder's own listing) of the
`f-throw-catch` corpus source

```js
var result = [];
try { throw "boom"; } catch (error) { result.push({ type: typeof error, value: error }); }
try { throw new Error("bad"); } catch (error) { result.push({ type: error.name, message: error.message }); }
throw { kind: "uncaught", caught: result };
```

| PC | Instruction | Reading |
|---:|---|---|
| 8 | `TRY_SETUP catch_1 (20), r3` | the first try |
| 11-15 | `LOAD_CONST r4 = "boom"; THROW r4` | the block always throws |
| 17-18 | `TRY_END; JUMP after_catch_2 (52)` | the normal exit: dead, right before the catch entry; `layoutEnd = 52` |
| 20-51 | `result.push({...})` | the catch; it falls through to 52 |
| 52 | `TRY_SETUP catch_3, r3` | the second try: where the source closed the first |

From the reachable graph alone, 52 is just the catch's next case. With the hint the first try closes
at 52 and the two tries read as siblings, as in the source; without it the second try and the final
`throw` render nested inside the first catch. Both layouts behave the same; the hint decides layout
only, never what runs. Where the pair is not compiled so (an encoder stage moved or dropped it), no
hint is given, and the catch keeps the code only it reaches.

### Output, allocation and counts

Cases retain PC/nextPc and receive new semantic operation objects. A global `lowered` Map indexes
them by PC. Top-level `instructionCount` is exactly `lowered.size`, not `read-wordcode`'s reported
instructionCount or an independently summed array count. Owned successful global PC uniqueness
makes the censuses agree, but an example with equal counts does not independently test the
formula. No later step checks case totals; lowering does not revalidate owned records.

| Projection part | Exact allocation / identity |
|---|---|
| `functions` | The original `model.functions` object, shared. |
| `instructionsByFunction` | A new Map; each case array and case object is new. |
| Operation | New lowered object per case. |
| `storage` | New storage rows; the count follows the rule above. |

No deep clone/freeze is promised here. Normalization can change canonical wordcode width from the
original payload.

### Testing and acceptance

| Scenario | Oracle | Criterion | Fixture |
|---|---|---|---|
| Numeric arithmetic handoff | Cases present; serialized instruction fields and control fields absent. | Lowering succeeds and the model carries only typed cases. | Numeric adapter test; it does not assert every operation's exact lowering. |

## 4. Input Shapes

| Producer | Supplied shape / treatment |
|---|---|
| [Numeric diagnosis](standalone-diagnosis.md) | Source-admitted current model; lowering consumes `read-wordcode`, `validate-references` and `partition-functions` records and the compiler layout behind `layoutEnd`. |
| [Numeric normalizers](standalone-diagnosis.md#canonical-frontend-retries) | Rebuilt current wordcode, ownership and control; the frontend completes admission before lowering. |

## 5. Known Gaps

- EXP lowers to `**` while the
  [pinned handler](../../../js-confuser-vm/instruction-set.md#loads-stores-scalar-operations-and-coercion)
  uses Math.pow, so numeric emission's `finalJavaScriptSemantics:false` remains necessary.
- No test asserts every operation's exact lowering; the committed test pins the arithmetic handoff
  only.

## Source

[numeric-to-vm-switch.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/numeric-to-vm-switch.js)
exports `numericToVmSwitch`; its internal `lower` and `lowerCall` implement section 3.
[decode-standalone.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/decode-standalone.js)
calls it after diagnosis and hands the result to the shared backend.

## Fixtures

| Committed fixture or test | Claim pinned |
|---|---|
| [numeric-to-vm-switch.test.js](../../../../decoder/decode-js/test/vm/jsconfuser-vm/single-component/numeric-to-vm-switch.test.js) (unit) | A hand-written boot of `window.TEST_OUTPUT = 1 + 2` resolves; case serialized opcode/word fields and the control fields are absent. |

A retired field verifier, built from the documents before source consultation, credited selected
literal controls over supplied scaffolds, followed by a static source audit:

| Selected credit | Exact boundary |
|---|---|
| Typed lowering | LOAD_INT/LOAD_CONST/MOVE/VOID/UNARY_NEG fields, array tail, ordered object pairs, label PC, fixed/spread kind and method/constructor carriers. `read-wordcode` and `validate-references` grammar and provenance are supplied; other opcodes and closure lowering are excluded. |
| Projection allocations and counts | Selected new Maps/arrays/cases/control/block/leaves, shared functions/nested metadata/case-leaf operation, and new structuredControl with shared edge array/row. A private duplicate-PC scaffold distinguishes lowered.size from `read-wordcode` count and array sum; it is private scaffolding inconsistent with successful owned records, not source admission or a duplicate-PC refusal oracle. |

Its selected allocation observations do not establish generic clone/freeze semantics or a whole
numeric schema.
