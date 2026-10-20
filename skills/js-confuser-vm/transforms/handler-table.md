# Lift opcode handlers into a prototype table

## 1. Target

Replace the completed opcode switch with numeric property dispatch on the VM instance. Each
case becomes a zero-argument function on the VM prototype, preserving its operand reads and
frame effects. This adds indirection while allowing the subsequent class/minifier stages to
process the extracted bodies like other runtime methods.

The input is the private Babel File after added-handler construction and optional case shuffle;
`handlerTable` truthiness enables this pass. Read the
[AST foundation](../js-confuser-vm.md#runtime-ast-dependency-contract),
[frame/transport interface](../container-wordcode.md), [canonical handlers](../instruction-set.md)
and [layout/case shuffle](runtime-layout.md). The output is a mutated File containing one dynamic
call and prototype assignments. This is a pinned, source-derived recipe, not arbitrary switch
lifting or proof of every option combination.

## 2. Algorithm

Clone each non-default case's statements into an independent function. A case's ordinary switch
break must now exit that function, so replace switch-owned unlabeled breaks with bare returns.
Keep breaks inside loops/nested switches in place: they still exit their own construct. Drop a
single final bare return because reaching a function's end already returns undefined.

The new function cannot read the run method's frame/register locals. Recreate only the specific
`fp`, `regs` and `base` aliases its body names, reading from the VM receiver. Keep shared top-level
helpers/maps captured from the same runtime file. Assign the function under the case's original
test expression, so words and keys retain their current map relationship.

Replace the marked switch with `this[op]()` inside the same run-loop try/catch. Initialize a
prototype alias and install all handlers before boot. The member-call form preserves `this` as
the executing VM; its return value is ignored. RETURN's root completion remains an explicit
frame/result-cell update observed by the outer run loop, so it does not depend on returning a
value from the extracted handler.

### Worked example

This **synthetic canonical JUMP case** omits the rest of dispatch and exception routing:

```text
case OP.JUMP:
  regs[fp + SLOTS.PC] = this._operand();
  break;

becomes, before boot:
var VMPrototype = VM.prototype;
VMPrototype[OP.JUMP] = function () {
  var fp = this._f;
  var regs = this._regs;
  regs[fp + SLOTS.PC] = this._operand();
};

and at the old switch site:
this[op]();
```

The body names fp and regs but not base, so no base local is injected. Its final break becomes
return and is then omitted. With plain `fp=1`, PC slot zero, fetched JUMP at word 10 and its target
operand 20 at word 11, dispatch sets the frame PC to 11; `_operand()` reads 20 and increments to
12; the assignment then writes 20 into `_regs[1]`. The handler returns undefined and the next
iteration fetches word 20. If OP.JUMP is randomized, both the word header and prototype key use
that same value. A nested `while (...) { break; }` would retain its break rather than return
from the handler.

## 3. Implementation

### Components and AST decisions

| Component | Input -> output | Consumer invariant |
|---|---|---|
| Marked-switch selection | First leading comment containing @SWITCH -> SwitchStatement | All handler additions have already run. |
| Body extraction | Case consequent -> deeply cloned statements | Unwrap only a sole BlockStatement; original case remains until switch replacement. |
| Exit conversion | Cloned statements -> function-compatible exits | Only switch-owned breaks converted; last bare return removed. |
| Local injection | Body identifier census -> zero or more var statements | Current VM supplies frame/register aliases in fp, regs, base order. |
| Installation | Case tests/functions -> top-level alias/assignments | Keys preserve test expressions; declarations installed before boot. |
| Dispatch | Switch path -> `this[op]();` | Same exception try/catch and timing-selected op remain active. |

For each SwitchCase, skip `test===null` (default). If its consequent is exactly one BlockStatement,
use that block's body; otherwise use its consequent list. Deep-clone every statement, convert
breaks, drop a final argumentless ReturnStatement, then create an anonymous FunctionExpression
with no parameters and a BlockStatement containing injected declarations followed by that body.
Emit a computed assignment `VMPrototype[clone(case.test)] = function(){...}`. Canonical tests are
`OP.NAME` MemberExpressions; added opcodes can provide NumericLiteral tests. Neither the test
nor its map is changed here.

Exit conversion recursively visits BlockStatement bodies, IfStatement consequent/alternate
(single statements or blocks), and TryStatement try/catch/finally bodies. Replace an unlabeled
BreakStatement reached there with ReturnStatement(null). Do not descend into for/while/do loops,
nested switches, function bodies, labeled statements or other unlisted statements. Labeled breaks
stay unchanged. The pass does not synthesize fallthrough between handlers or validate arbitrary
cross-case dependencies. The pinned case producers must supply terminal, self-contained bodies.

Local injection uses a fast traversal of **all Identifier nodes**, not a binding/reference-only
analysis. Thus declarations and identifier property keys also count. Let F mean the body names
`fp`, R mean it names `regs`, B mean it names `base`:

| Condition | Injected declaration |
|---|---|
| F | `var fp = this._f;` |
| R | `var regs = this._regs;` |
| B | `var base = (R ? regs : this._regs)[(F ? fp : this._f) + SLOTS.REG_BASE];` |

The third row is explanatory substitution, not an emitted ternary: choose the corresponding AST
receiver/frame expression when building the var. A base-only body reads both fields inline;
a body naming regs and base but not fp gets `var base=regs[this._f+SLOTS.REG_BASE]`.
Other run locals (`bc`, `pc`, clock variables) are not injected. Canonical extracted bodies do
not depend on them; later added-opcode bodies must satisfy that same ownership contract.

### Receiver, captures, completion and installation

An ordinary FunctionExpression obtains the VM receiver through `this[op]()`. Using a detached
function call would lose that relationship. The cloned body keeps references to OP, SLOTS,
SENTINELS, VM/Closure/Upvalue constructors, the base64 helper and CLOSURE_MAP in the shared outer
file environment where applicable. Nested callable shells keep their own lexical captures and
receiver rules; this pass neither copies the closure map nor creates a second VM register array.
The [instruction contract](../instruction-set.md#closures-receiver-capture-and-upvalue-lifetime)
owns those shell/cell relationships. Per-handler var declarations become function-local; there
is no intentional data transfer via a run-local case variable to the next case.

The replacement uses the actual `op` local, including the timing branch's reassignment to
OP.JUMP. Exceptions thrown by a handler propagate through the dynamic call into the existing
run-loop catch/unwind. Root RETURN still sets `_f=0`, clears/releases its frame, and writes slot
zero; the outer post-dispatch check returns that result. An ordinary bare function return only
ends one dispatch. Dropping default removes the explicit `Unknown opcode...` throw: an absent
callable property ordinarily raises TypeError at the dynamic call, which follows the same catch.
Prototype lookup is normal JavaScript lookup; it is not an own-handler membership check.

After replacing the first marked switch, assert that a handler list was found. If shuffleOpcodes
is truthy, shuffle the extracted assignments a second time using the
[shared random primitive](runtime-layout.md#components-and-exact-allocation). Parse
`var VMPrototype=VM.prototype` and insert it followed by the handlers immediately before the
first top-level statement with a **leading** comment containing `@BOOT`. If none exists, append
at end. The generated template supplies the marker; absence is not a refusal branch here.

The transform mutates the private AST, with no returned per-handler records or rollback protocol.
Compilation only publishes after later generation/minification succeed. Later class inlining
starts with a scope crawl because handler assignments were installed by raw list splicing.
No stronger persistent scope-cache guarantee is provided by this pass itself.

### Testing and acceptance

| Scenario | Observable result / oracle | Acceptance criterion | Retained control |
|---|---|---|---|
| H1: canonical lifting/local needs | Dynamic call plus matching keyed functions; JUMP PC trace above | One function per non-default case, correct aliases, body effects retained | handlerTable variant 1; bounded reconstructed table/local-mask/break controls; real-runtime direct controls missing |
| H2: terminal/nested exits and root RETURN | Nested break exits loop; switch-owned break exits handler; root result exits run | No fallthrough transfer; full frame/result cleanup still occurs | Variants 1/2 behavior; bounded synthetic exits/frame/result checks; real capture/unwind/return-state controls missing |
| H3: unknown value | Absent callable property produces normal member-call failure | Default omitted; catch route uses current frame | Bounded missing-member failure; real default/unknown/prototype-collision controls missing |
| H4: added/class/off forms | Added cases lifted; class literals/renames remain coupled; false retains switch | Completed handlers precede table, class sees table | Variants 2/3 and class tests; every added-opcode combination not established |
| H5: capture/marker/publication | Top-level helper/map binding remains shared; absent @SWITCH asserts | No second helper/map or successful publication after selection failure | Behavioral capture test; bounded shared-helper/marker controls; complete real capture/publication controls missing |

The retired bounded verifier retained a
reconstruction built before implementation consultation. It actually transforms a synthetic
marked switch into three prototype handlers/dynamic dispatch and executes that reconstructed
runtime, asserting output shape, receiver/shared-helper connection, word-PC progression and
chosen frame/result clearing. AST controls cover all fp/regs/base masks, switch-owned versus
nested/labeled exits, missing switch marker and boot append fallback; a missing table member
reaches the named call failure. These are tests of the reconstructed subset, not execution of
the source pass or real VM. The proof omits added opcodes, real captures, unwind and complete
canonical behavior. Its chosen synthetic completion is not the full RETURN algorithm.

These criteria test changed dispatch shape as well as program behavior. Evaluation alone cannot
certify installation order, local ownership or captures. Arbitrary early returns, fallthrough and
extra run-local dependencies require their own control and are outside the pinned producer contract.

## 4. Later Stages

| Later producer | Shape emitted | Effect on lifted handlers |
|---|---|---|
| [Class constants](class-runtime.md#constant-inlining) | OP/SLOTS/SENTINELS values inlined | Numeric keys and literal frame offsets replace map-member reads together. |
| [Class renaming/order](class-runtime.md) | Renamed VM fields/methods; alias assignments grouped after declarations | Handler field accesses share the same global rename map. Computed alias handlers are not discovered as named class methods for parameter reordering. |
| [Final minification](minify-runtime.md) | Optimized functions/calls and lexical names | Table spelling/body formatting is not stable; optimizer sees shared helpers and numeric property lookup. |

## 5. Known Quirks

- The pass drops default and uses ordinary property lookup. It does not promise the switch's
  exact error message or behavior for malformed opcodes/prototype pollution.
- Case lifting depends on self-contained terminal cases. No generic fallthrough, labeled-exit,
  shadowed fp/regs/base or arbitrary free-variable analysis is implemented.
- Alias/boot names and markers are build-time conventions; minification may erase their spelling.
- Real-runtime direct AST, capture/state/default and negative controls remain evidence gaps;
  the frozen synthetic subset above supplies only its named table controls.

## Source

Case extraction, exits and local injection in items 2-3 are
[handlerTable.ts#L14-L121](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/transforms/runtime/handlerTable.ts#L14-L121).
Installation/dispatch are
[handlerTable.ts#L123-L185](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/transforms/runtime/handlerTable.ts#L123-L185),
wired after additions/shuffle and before class in
[build-runtime.ts#L58-L95](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/build-runtime.ts#L58-L95),
forcing item 4's order. Runtime fetch/try context is
[runtime.ts#L232-L280](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/runtime.ts#L232-L280);
JUMP is [runtime.ts#L546-L548](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/runtime.ts#L546-L548),
root completion is [runtime.ts#L645-L675](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/runtime.ts#L645-L675)
and [runtime.ts#L903-L957](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/runtime.ts#L903-L957).
Shared helper/map/shell contracts are
[runtime.ts#L15-L50](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/runtime.ts#L15-L50)
and [runtime.ts#L681-L754](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/runtime.ts#L681-L754).

## Fixtures

| Retained source/control | Scenario / bounded intent | Missing evidence |
|---|---|---|
| [handlerTable.test.js](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/test/options/handlerTable.test.js) | H1/H2/H4: table/dynamic call, injected aliases, selected capture/call behavior; specialized/class recursion; false retains switch | Real-pass direct break/local-mask/default/capture/state and generated-byte controls |
| [classObfuscation.test.js](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/test/options/classObfuscation.test.js) | H4: alias before assignment and selected table/class result | Complete table/rename/binding invariants |
| Retired bounded verifier | H1/H2/H3/H5 subset: actual synthetic table transformation/execution, local/exit/receiver/helper/PC/frame/result state and marker/boot/member-failure controls | Real VM/capture/unwind, added opcodes and actual generated-output evidence |
| No retained direct real-runtime control | H3/H5 and other missing criteria above | Proposed acceptance criteria remain unqualified |

Encoder-local option tests generate through [test-utils.js](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/test/test-utils.js).
The frozen document-only subset is not complete runtime reconstruction. No fresh encoder execution,
retained generated table qualification or novice study is claimed.
