# Locate the interpreter's handlers

Part of the [`handlers` module](../handlers.md). The stage `admit-container` and the runtime
observers call it ([map](../../../pipelines/jsconfuser-vm.md#frontend-order)).

## 2. Algorithm

The boot call is the program's only entry into the interpreter, so the locator starts there and
never searches for a `switch`: a `switch` of the program's own is not reached from the boot. The
VM construction in that call receives the word stream and the pool, and the constructor stores
them in two fields. The run loop fetches the word at the frame's PC from the words field and
dispatches on it. Those two facts select the dispatch. The readers are the callables whose bodies
read those fields.

```text
locate(program):                                   // explanatory pseudocode, in the code's order
  {call, holder, wordsIndex, poolIndex} = boot skeleton        // source/container
  V = the function holder constructs, through stable aliases
  wordsField, poolField = the fields V's body stores from parameters wordsIndex, poolIndex
  callables = every method with a unique name and every top-level function, each with its layout
  entry, state = call.callee is o.m ? (V.prototype.m, this)
                                    : (the function, its parameter at holder's argument position)
  selectors = locals of entry written from state.wordsField[i]
  dispatch = the one switch in entry on a selector, or the one call state[selector]()
  operand  = the callable whose body, decoy stores aside, is `return self.wordsField[x++]`
  constant = the other callable reading self.poolField; its operand parameters are those
             defaulted by `p ?? operand(...)`: two, or none where minify dropped the pair
  handlers = the switch's cases with a test, or the table's `T[label] = function () {...}`
             statements (T the VM prototype or a stable alias of it); labels distinct
  split each table handler into prologue and body
  opcodes = createOpcodeTable()                    // canonical until behaviour matching
```

`self` is `this` in a method and the first parameter in a devirtualized function; in the function
form a reader call passes the VM as its first argument. A **label** is the number a case test or
table key always holds: a literal, a member of a stable numeric map (`OP.ADD`), or a top-level
binding that stably holds a number.

Each encoder step that re-spells the interpreter is read through by one of these rules:

| Spelling | Producer | Rule |
|---|---|---|
| Prototype methods on `this`, `OP.NAME` labels | The runtime template | Method form; labels through the stable map |
| Shuffled case order | `shuffleOpcodes` | A label is a value; order is not read |
| A label-keyed method table, a prototype alias, per-handler frame locals | `handlerTable` | Table dispatch; prologue and body |
| Decoy parameters and stores, numeric labels | `classObfuscation` | Layouts |
| Top-level functions taking the VM first, merged declarators, brace-less bodies, hoisted `var` temporaries, a last case without `break`, a constant reader without parameters, the run callee as a `var` alias in a loop head | `minify` | Function form; lowering; stable aliases; `ends` |
| Map members as flat top-level bindings (`case __p_BmUS_OP_LOAD_CONST:`) | An outer js-confuser ObjectExtraction, after its own decoder | Labels and lowering read the binding's stable number |

### Layouts: decoy parameters

[Class obfuscation](../../../../js-confuser-vm/transforms/class-runtime.md#fake-parameters-and-coupled-permutation)
adds one to four parameters to each constructor and uniquely named method, passes a dummy literal
for each at every call site (`this.Q([], "q")`), and stores each group of one or two into a new
field that nothing reads (`this.ab = fake_16 && fake_15`). Minify then moves the store (into an
`if`, a loop head), drops some, and may reuse the freed parameter as a local. The layout undoes
the steps outermost first:

1. **Decoy stores.** A write `self.f = v` where `v` holds only the callable's parameters and dummy
   literals (an array, `&&` or `||` of them) and no code anywhere reads the field `f`. A field is
   read by any member access other than the target of a plain `=`. A real store, such as a
   constructor saving its argument, writes a field other code reads.
2. **Dead parameters.** With the decoy stores set aside, a parameter is dead when nothing uses it,
   or when its first use in source order overwrites it with `=` by a value that does not read it.
   Only references count: a field named like the parameter is no use; a compound assignment reads
   its target.

```text
function v(a, b, c, e) {            // c and e are dead:
  var f = a.u;
  a.y = c;                          //   decoy store: nothing reads .y
  if (f) for (a.f = e,              //   decoy store: nothing reads .f
              c = a.q, ...)         //   c's first remaining use overwrites it (minify's reuse)
    ...
}
```

A call's **real arguments** are its arguments without the dead positions. Arguments past the
parameter count are dead unless the body reads `arguments`. A dead argument must evaluate without
effect: a dummy literal (`null`, a number, a string, `undefined`, `void 0`, `[]`, `{}`) or a bound
variable; anything else refuses. A call may pass fewer arguments than the arity, since minify
drops trailing ones.

### Lowering

Behaviour matching ([identify-handlers](identify-handlers.md)) and the runtime observers compare
handler bodies, and minify spells one operation differently in different cases. `lower` rewrites
cloned statements so that equal operations compare equal; the program's tree is never changed.

| Form | Lowered to |
|---|---|
| Operand read (`this.Q()`, `C(a)`, `a.z(7, 9)`) | `$operand()` |
| Constant read (`this.x()`, `J(a, U[1], U[2])`, `a.a()`) | `$constant(...explicit arguments)`, in the reader's (index, key) order |
| Any other call or `new` of a callable, on any receiver | The same, with its real arguments only |
| Read of a stable numeric map member (`SLOTS.THIS`) or of a top-level binding stably holding a number | The number |
| `var x = v, y = w` outside a loop head; statement-level `x = v, y = w` | `x = v; y = w;` |
| A control body holding one simple statement (`if (c) { throw x }`) | That statement ([statement view](../source/normalize-source.md#2-algorithm)) |
| `for (var a = x, i = 0; ...)`, `for (a = x, i = 0; ...)` | `a = x; for (i = 0; ...)` |
| A statement writing only dummy literals to a named field (an inlined decoy store) | Dropped |

`let` and `const` declarations are kept as written.

### Table handlers: prologue and body

A table handler is its own function, so it opens by reading the frame state that a switch case
takes from the run function (`var regs = this._regs; var base = regs[this._f + 7]`), and minify
coalesces its locals: one variable holds the frame pointer, later the upvalue cell. On the
handler's copy:

- each top-level `=` write of a local starts a new version of it (SSA renaming);
- a leading version that holds a frame-state read is replaced by that read wherever it is used
  (copy propagation), and its statement is removed, unless a nested statement writes the local
  before its next top-level write;
- a write nested in a loop or conditional starts no version, so a loop-carried variable keeps one
  identity;
- propagation stops at the first statement that is not such a write.

Frame state is a field of `this` (`this.h`), or a field indexed by fields and literals
(`this.g[this.h + 0]`). A literal (a specialized handler's baked `dst = 18`) or a register read
(`regs[base + 15]`) is the handler's own and stays. Each remaining version is a distinct local to
whoever compares the copy.

The handler's **prologue** is its leading statements that propagation consumes; its **body** is
the rest. Lowering a table handler's body clones the prologue in front so that propagation can
consume it. A switch case has no prologue.

### Worked example: a switch dispatch under minify and aliased opcodes

Cell `minify-over-aliased-opcodes`: source `composition-finally-abrupt-return`, profile
`randomizeOpcodes+aliasedOpcodes+minify`, seed 251. Abbreviated:

```text
Ga(new Ea([269,1,13628,5,55,1,...], [!0,"window","TEST_OUTPUT",void 0,"push",...], R),
   new Da({o:0,v:8,G:0}), void 0, null)

function Ea(a,g,b){this.l=a;this.K=g;this.i=b;...}
function Ga(a,g,b,m){...var B=a.l[n];...switch(B){...}}
function C(a){return a.l[a.g[a.h+3]++]}
function J(a,g,b){g=g??C(a);b=b??C(a);a=a.K[g];...}
```

1. The boot skeleton gives the call `Ga(...)`, the holder `new Ea(...)`, words at argument 0 and pool
   at argument 1.
2. `Ea` stores parameter 0 in `l` and parameter 1 in `K`: the words and pool fields.
3. The callee `Ga` is a function and the holder is its argument 0, so its parameter `a` is the
   state. `B = a.l[n]` makes `B` a selector, and `switch (B)` is the dispatch, with 76 cases.
4. `C` returns `a.l[x++]`: the operand reader. `J` reads `a.K` and defaults `g` and `b` by
   `?? C(a)`: the constant reader, with explicit arguments in the order `(g, b)`.
5. The case labelled 17857, `var e=C(a);b[d+e]=J(a);break;`, lowers to
   `e=$operand(); b[d+e]=$constant(); break;`.
6. The case labelled 48718,
   `let aa=[C(a),C(a),C(a)],ba=[aa[1],aa[0],aa[2]];e=ba[0];x=J(a,ba[1],ba[2]);...`, lowers to
   `let aa=[$operand(),$operand(),$operand()],ba=[aa[1],aa[0],aa[2]]; e=ba[0];
   x=$constant(ba[1],ba[2]); ...`: its constant read passes both arguments explicitly.

## 3. Implementation

### Exports another file imports

| Export | File | Contract | Imported by |
|---|---|---|---|
| `locateHandlers(ast)` | `locate-handlers.js` | The view below, or a `container` refusal. | `extract-container.js`, `observe/observe-patch-added-opcodes.js` |
| `requireHandlers(ast, code)` | `locate-handlers.js` | The view; a locator refusal becomes `code` with "Numeric container is not admitted", any other error passes on. | `identify-handlers.js` |
| `partitionHandlers(view)` | `locate-handlers.js` | `{canonical, extra, firstAdded}`: a handler whose label is a value of `view.opcodes` is canonical, as `{name, opcode, handler}`; the rest are added handlers, sorted by label; `firstAdded` is one past the table's highest value. | the runtime observers |
| `normalizeStatements(nodes)` | `normalize-handler-statements.js` | The statement rows of the lowering table, in place; returns `nodes`. Also applied to the reference templates of behaviour matching. | `handler-lowering.js`, `handler-meaning.js`, the test |
| `cloneRuntimeFragment(nodes, origins?)` | `runtime-fragment-pattern.js` | `{nodes, origins}`: deep clones, each cloned node mapped to its original. | `handler-lowering.js`, `handler-table.js`, `handler-effects.js` |

### Inside the part

| Piece | File | Does |
|---|---|---|
| `HandlerLocator` | `locate-handlers.js` | One recognition step per method, run in the order of the pseudocode. |
| `callableLayout`, `functionOf`, `functionFor`, `storedFields`, `labelValue`, `caseStatements`, `isDummyLiteral` | `runtime-callables.js` | The layout; the function a binding stably holds, through `var a = b` aliases and a never-written declarator in a loop head; a constructor's `this.field = parameter` statements; a label's value; a case's statements with a single block unwrapped; the dummy literals. |
| `HandlerCalls`, `firstReal` | `handler-calls.js` | Built once the entry fixes how the state is referred to: what a call reaches (`calleeOf` for a call on the state or of a top-level function, `methodOf` for a method call on any receiver), its `realArguments`, `isState`, `isField`, a callable's `selfOf` and `effectiveBody`. `firstReal` is 1 for a function reader, 0 for a method. |
| `HandlerLowering` | `handler-lowering.js` | Built once both readers are located: `lower`, `loweredClone`, `operand`, `constant`. |
| `tableHandlers`, `tablePrologue`, `ssaPropagate` | `handler-table.js` | The table's handlers; the prologue, found by tracing each lowered statement back to the handler statement it came from; the propagation. |

### The view

```js
// view
{
  context,                   // the node context (source/container)
  dispatch,                  // the SwitchStatement, or the table CallExpression
  handlers,
  opcodes,                   // this decode's table; canonical here
  fields,                    // { words, pool }: the two field names
  operand(node),             // true for an operand-reader call with no explicit argument
  constant(node),            // a constant-reader call's explicit arguments in (index, key)
                             // order, [] for a call passing none, null for any other node
  lower(nodes, origins, handler),  // lowers clones in place; for a table handler clones the
                                   // prologue in front and propagates
}
// handler
{
  label,
  entry,                     // the SwitchCase, or the table's FunctionExpression
  statements,                // all of its statements
  prologue, body,            // body equals statements for a case
  ends,
  table,                     // true for a table handler
}
```

`ends` is true when a case ends in `break` or `throw`, when it is the switch's last case and
holds no `break` (minify drops it there), and for every table handler. Readers read `body`.

### Refusals

All are `container` refusals ([Refusals](../../../pipelines/jsconfuser-vm.md#refusals)); those
below the first row carry the code `handler-locator`.

| Input | Message |
|---|---|
| No boot or several; a holder whose arguments do not reach the payload one each | `missing-role`, from the [boot skeleton](../source/container.md#refusals) |
| The holder's callee is not a stable function | "VM construction is not unique" |
| The constructor does not store both payload parameters in fields | "VM payload fields are not stored" |
| The boot's method, or its function and state parameter, is not found once | "VM run method is not unique", "VM run function is not unique" |
| No dispatch on a fetched word, or more than one | "Dispatch on the fetched word is not unique" |
| No operand reader, or several; likewise the constant reader | "Operand reader is not unique", "Constant reader is not unique" |
| The constant reader defaults neither two nor no parameters, or a decoy one | "Constant reader parameters are ambiguous" |
| A label with no stable number; two equal labels; a table with no handler | "Dispatch label has no value", "Dispatch labels are not distinct", "Handler table has no handlers" |
| A dead argument that is not a dummy literal or bound variable, or more arguments than a callable with decoys takes | "Class decoy call arguments changed" |

## 5. Known Gaps

- Minify together with a handler table over one added-opcode option has no suite of its own; the
  combination is covered only with every option at once.
- No committed case has a dead argument with an effect.

## 6. Source

- [locate-handlers.js](../../../../../decoder/decode-js/src/vm/jsconfuser-vm/handlers/locate-handlers.js):
  the locator, the partition, the entry for readers.
- [runtime-callables.js](../../../../../decoder/decode-js/src/vm/jsconfuser-vm/handlers/runtime-callables.js):
  layouts, labels, stable functions.
- [handler-calls.js](../../../../../decoder/decode-js/src/vm/jsconfuser-vm/handlers/handler-calls.js):
  call queries.
- [handler-lowering.js](../../../../../decoder/decode-js/src/vm/jsconfuser-vm/handlers/handler-lowering.js)
  and
  [normalize-handler-statements.js](../../../../../decoder/decode-js/src/vm/jsconfuser-vm/handlers/normalize-handler-statements.js):
  the lowering.
- [handler-table.js](../../../../../decoder/decode-js/src/vm/jsconfuser-vm/handlers/handler-table.js):
  table handlers and propagation.
- [runtime-fragment-pattern.js](../../../../../decoder/decode-js/src/vm/jsconfuser-vm/handlers/runtime-fragment-pattern.js):
  clones with origins.
- The run loop and readers in the pinned encoder:
  [runtime.ts#L44-L217](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/runtime.ts#L44-L217).

## 7. Fixtures

Suites encode their sources with the pinned encoder and require the decode to behave as the
source ([tests.md](../../../tests.md)). No unit test enters this part directly.

| Scenario | Expected result | Committed fixture |
|---|---|---|
| A handler table under class obfuscation, with self-modifying words | The dispatch is found as a table call; taking only a `switch` turns the suite red | [patch-handlers-chain](../../../../../decoder/decode-js/test/vm/jsconfuser-vm/cell-suites/patch-handlers-chain/suite.js) |
| A minified interpreter with added handlers | The function form, readers and lowering are read; the decode behaves as the source | [minify-over-aliased-opcodes](../../../../../decoder/decode-js/test/vm/jsconfuser-vm/cell-suites/minify-over-aliased-opcodes/suite.js) and the other `minify-over-*` suites (coverage) |
| A handler table with added handlers | Prologue and body are split; the decode behaves as the source | the `handler-table-over-*` suites (coverage) |
| Class obfuscation with added handlers | Layouts drop the decoys; the decode behaves as the source | the `class-rewrite-over-*` suites (coverage) |
| Shuffle, table, class and minify together | The decode behaves as the source | [runtime-rewrites-chain](../../../../../decoder/decode-js/test/vm/jsconfuser-vm/cell-suites/runtime-rewrites-chain/suite.js) (coverage) |
| A dead argument with an effect | "Class decoy call arguments changed" | |
| Flat top-level label bindings from an outer ObjectExtraction | Labels read as their numbers; the sequential decode behaves as the source | `object-extraction.js` of the [counter-total](../../../../../decoder/decode-js/test/vm/jsconfuser-vm/layered-inputs/counter-total/generation.json) layered inputs, read by sequential.test.js |
