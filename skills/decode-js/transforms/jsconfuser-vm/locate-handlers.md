# Locate the interpreter's handlers

## 1. Target

The handler locator (H) finds the interpreter's dispatch and its operand and constant readers by
what they do, and publishes a view that the runtime readers consume: the
[anti](anti-runtime-observation.md), [specialized](normalize-specialized-wordcode.md),
[macro](normalize-macro-wordcode.md), [aliased](normalize-aliased-wordcode.md) and
[PATCH added-opcode](normalize-self-modifying-wordcode.md) observers. Runtime-layer options (class
obfuscation, Closure ADVANCED minify, case shuffle) re-spell the interpreter; they keep the
behaviour H selects by, so one locator serves every spelling.

H is analysis. It reads the supplied tree, never edits it, and executes nothing. Its view holds the
dispatch's handlers, two reader predicates, a lowering for comparing handler bodies on clones, and
this decode's opcode table. A refusal is a `ContainerDecline` with code `handler-locator`; each
reader reports it under its own `*-runtime-container` code.

Readers need JavaScript functions, `switch`, prototype methods and the [Babel binding
foundation](../../babel.md), and the encoder's [runtime stages](../../../js-confuser-vm/js-confuser-vm.md#compiler-order)
(stage 11: added-opcode handlers, then case shuffle, handler table and class obfuscation; stage 12:
minify).

## 2. Algorithm

The boot call is the program's only entry into the interpreter, so H starts there instead of
searching for a switch: a program's own `switch` is never reached from it. The VM construction in
that call receives the word stream and the pool, and the constructor stores them in two fields. The
run loop fetches the word at the frame's PC from the words field and dispatches on it. Those two
facts select the dispatch. The readers are the callables whose bodies read those fields.

```text
locate(program):                                   // explanatory
  {call, holder, wordsArg, poolArg} = boot skeleton           // Packet A's boot locator
  V = the function holder constructs (through stable aliases)
  wordsField, poolField = fields V's body stores from parameters wordsArg, poolArg
  entry, state = call.callee is o.m ? (V.prototype.m, this)
                                    : (the function, its parameter at holder's argument position)
  selectors = locals of entry assigned from state.wordsField[i]
  dispatch = the one switch in entry on a selector, or the one call state[selector]()
  handlers = the switch's cases, or the table's `T[label] = function () {...}` assignments
             (T the VM prototype or a stable alias of it);
             label = the number it always holds: a literal, a stable map member (`OP.ADD`),
                     or a top-level binding stably holding one; distinct
  operand = the callable whose body, decoy writes aside, is `return self.wordsField[x++]`
  constant = the other callable reading self.poolField; its operand parameters are the ones
             defaulted by `p ?? operand(...)`, an operand read on its own receiver (a function
             call or a method call): two, or none where minify dropped the pair
  opcodes = createOpcodeTable()                     // this decode's table, canonical by default
```

`self` is `this` in a method and the first parameter in a devirtualized function. A reader call
passes the VM as its first argument in the function form.

**Decoys.** [Class obfuscation](../../../js-confuser-vm/transforms/class-runtime.md#fake-parameters-and-coupled-permutation)
adds 1-4 parameters to each constructor and uniquely named method, passes a dummy literal for each
at every call site (`this.Q([], "q")`), and stores each group of one or two into a new field that
nothing reads (`this.ab = fake_16 && fake_15`), so the parameter does not look dead. Minify then moves the store (into an `if`, a loop initializer), drops some, and
may reuse the freed parameter as a local. H undoes the stages outermost-first: it removes class
obfuscation's store, then reads what minify left. Every method with a unique name and every
top-level function gets a layout:

1. **Decoy stores.** A write `self.f = v` where `v` holds only the callable's parameters and dummy
   literals (an array, `&&` or `||` of them) and no code anywhere reads the field `f` (a member
   access other than the target of a plain `=` write). A real store, such as a constructor saving
   its argument or a run function saving the frame pointer (`a.g = f`), writes a field other code
   reads.
2. **Dead parameters.** With the decoy stores removed, a parameter is dead when nothing reads it, or
   when its first use, in source order, overwrites it (`=`) with a value that does not read it.
   Only references count: a field name spelled like the parameter (`this.b` beside parameter `b`)
   is not a use; a compound assignment or update reads its target.

```text
function v(a, b, c, e) {            // c and e are dead:
  var f = a.u;
  a.y = c;                          //   decoy store: nothing reads .y; removed
  if (f) for (a.f = e,              //   decoy store: nothing reads .f; removed
              c = a.q, ...)         //   c's first remaining use overwrites it (minify's reuse)
    ...
}
```

Arguments past the parameter count are dead unless the body reads `arguments`. A dead argument must
evaluate without effect: a dummy literal (`null`, a number or string, `void 0`, `[]`, `{}`) or a
bound variable; anything else refuses (`Class decoy call arguments changed`). A call may pass fewer
arguments than the arity (minify drops trailing ones).

**Lowering.** The handler effects of [runtime meaning](runtime-meaning.md)
read handler bodies, and minify spells the same operation differently in different cases.
`lower(nodes, origins)` rewrites cloned statements so that equal operations compare equal:

| Form | Lowered to |
|---|---|
| Operand read (`this.Q()`, `C(a)`, `a.z(7, 9)`) | `$operand()` |
| Constant read (`this.x()`, `J(a, U[1], U[2])`, `a.a()`) | `$constant(...explicit arguments)` |
| Other call or `new` of a callable with dead arguments, on any receiver | Without them |
| Read of a stable numeric map (`SLOTS.THIS`) or of a top-level binding stably holding a number (outer ObjectExtraction's `__p_BmUS_OP_LOAD_CONST`, `var x;` with its one top-level `x = 3`) | Its value (`3`) |
| `var x = v, y = w` (not a loop head) | `x = v; y = w;` |
| Statement-level `x = v, y = w` | `x = v; y = w;` |
| Control body holding one simple statement (`if (c) { throw x }`) | That statement |
| `for (var a = x, i = 0; ...)`, `for (a = x, i = 0; ...)` | `a = x; for (i = 0; ...)` |
| A named-field write of dummy literals only (an inlined decoy write) | Dropped |

A table handler is its own function, so it opens by reading the frame state that a switch case
takes from the run function (`var regs = this._regs; var base = regs[this._f + 7]`), and minify
coalesces its locals (one variable holds the frame pointer, then the upvalue cell). Its copy is
further renamed: each top-level write of a local starts a new SSA version, and a leading version
holding a frame-state read is replaced by that read (copy propagation), unless a nested statement
writes the variable before its next top-level write. A macro coalesces the register base with a
variable its RETURN part later writes inside a conditional; the base's own version still
propagates. Frame state is a VM field (`this.h`) or a field indexed by fields and
literals (`this.g[this.h + 0]`). A literal (a specialized handler's baked `dst = 18`) or a register
read (`regs[base + 15]`) is the handler's own and stays. A write nested in a loop or conditional
starts no version, so a loop-carried variable keeps one identity; each version is a local of the
fragment pattern. The handler's **prologue** is its leading statements whose writes propagation
consumes; its **body** is the rest, which readers read. Lowering a table handler's body clones the
prologue in front so propagation can consume it. A switch case has no prologue. Lowering always
works on a copy; the program's tree is never changed.

### Worked example: minify with aliased opcodes

The `runtime-layers` `minify-aliased` fixture (source `f(4)` summing 0..3) ends in this boot:

```text
za(new xa([64,1,47,3,39,…],["window","TEST_OUTPUT",4,void 0,0,1],P), new wa({m:0,v:7,G:0}),
   void 0, null)
```

1. The boot skeleton gives the call `za(…)`, holder `new xa(…)`, words at argument 0, pool at 1.
2. `function xa(a,g,b){this.l=a;this.K=g;this.i=b;…}` stores the words in `l` and the pool in `K`.
3. The callee `za` is a function; the holder is its argument 0, so `a` is the state in
   `function za(a,g,b,m){…var B=a.l[n];…switch(B){…}}`. `B` is the selector; that switch is the
   dispatch. Its labels are 0..60 and 61..70.
4. `function C(a){return a.l[a.g[a.h+0]++]}` is the operand reader;
   `function J(a,g,b){g=g??C(a);b=b??C(a);a=a.K[g];…}` reads the pool and defaults two
   parameters: the constant reader, with explicit arguments `(g, b)`.
5. Case 0 `var e=C(a);b[d+e]=J(a);break;` lowers to `e=$operand(); b[d+e]=$constant();`.
   Alias 61, `let A=[C(a),C(a),C(a)],U=[A[2],A[1],A[0]];e=U[0];b[d+e]=J(a,U[1],U[2]);break;`,
   lowers to reads and constant arguments taken from `U`; its effects equal case 0's with the
   operand slots in order `[2,1,0]`, so the [classifier](runtime-meaning.md#2-algorithm) names 61
   LOAD_CONST with that order.

## 3. Implementation

| Component | Input -> output | Decision |
|---|---|---|
| Boot skeleton (`locateBootSkeleton`, locate-boot-payload.js) | Program -> call, holder, words and pool argument positions | Exactly one boot; exactly one holder argument reaches each payload. |
| Opcode table (`CANONICAL_OPCODES`, `createOpcodeTable`, opcode-table.js) | -> a fresh table object | The module is never changed; each decode owns its object. |
| Locator (`locateHandlers`, `diagnoseHandlers`) | Program -> view | Item 2. `diagnoseHandlers` reports the labels or the refusal. |
| Partition (`partitionHandlers`) | View -> canonical, extra, firstAdded | A label equal to a value of the view's table is canonical, named by that table; the rest are added handlers, sorted by label. `firstAdded` is one past the highest table value. |
| Reader entry (`requireHandlers`) | Program, code -> view | A locator refusal becomes the reader's `code` with "Numeric container is not admitted". The readers start from the [identified view](runtime-meaning.md#3-implementation) built on it, whose table names the canonical handlers by behaviour. |
| Statement view (`normalizeStatements`) | Statements -> the same, in place | The statement rows of the lowering table; also applied to the [reference](runtime-meaning.md#2-algorithm) templates. |

The view is `{context, dispatch, handlers, opcodes, fields, operand, constant, lower}`; `fields`
names the words and pool fields. A handler is `{label, entry, statements, prologue, body, ends,
table}`: `entry` the `SwitchCase` (or the table's function), `statements` its body with a single
block unwrapped, `prologue` and `body` its split in item 2 (`body` equals `statements` for a case),
`ends` true when it ends in `break`, is the switch's last case with no `break` (minify drops it
there), or is a table function. Readers read `body`. `lower(nodes, origins, handler)` clones the
prologue in front and applies the table renaming when `handler.table`. `operand(node)` is true for a reader call with no explicit
arguments. `constant(node)` returns the explicit arguments in (index, key) order, `[]` for a call
that passes none, or `null` for any other node.

| Input | Disposition |
|---|---|
| No boot, or two | `missing-role`, "Boot call is missing or not unique". |
| Holder argument reach not unique | `missing-role`. |
| Constructor not a stable function, or payload not stored in fields | `handler-locator`. |
| Run method or function not unique | `handler-locator`. |
| No switch, or two, on a fetched word | `handler-locator`, "Dispatch on the fetched word is not unique". |
| A label with no value, or two equal labels | `handler-locator`. |
| Operand or constant reader not unique; constant parameters neither two nor none | `handler-locator`. |

### Testing and acceptance

| Scenario | Oracle | Criterion | Fixture |
|---|---|---|---|
| L1: minified runtime with added opcodes | Public decode behaves as the source. | Readers identify every added handler through the view, also over a handler table and under class obfuscation. | `runtime-layers` minify-aliased, minify-table-{aliased, macro, specialized, anti} and class-minify-{aliased, specialized}. |
| L2: class, table and encoded spellings | Every reader fixture decodes as before. | Readers read handler bodies, a table handler's prologue split off. | The reader owner docs' fixtures. |
| L3: renamed bindings | Decode equal to the unrenamed input. | Alpha renaming never changes a lowered pattern. | runtime-binding-identities.test.js. |

## 4. Input Shapes

| Input spelling | Producer | Handling |
|---|---|---|
| Prototype methods on `this`, `OP.NAME` labels | Pinned runtime template, encoder | Method form; labels through the stable map. |
| Decoy parameters, numeric labels | classObfuscation, encoder | Layouts drop decoys before comparison. |
| Devirtualized top-level functions, merged `let` declarators, brace-less cases, hoisted `var` temporaries, last case without `break`, constant reader without parameters | minify (Closure ADVANCED), encoder | Function form; lowering; dead-at-entry locals; `ends`. |
| Run callee as a `var` alias in a loop initializer | minify with encodeBytecode, encoder | Stable alias resolution through the binding. |
| Shuffled case order | shuffleOpcodes, encoder | Labels are values; order is not read. |
| Map members as flat top-level bindings (`case __p_BmUS_OP_LOAD_CONST:`, `argc === __p_2AtS_SENTINELS_CALL_SPREAD`) | An outer js-confuser ObjectExtraction, after its own decoder | Labels and lowering read the binding's stable number. |
| Label-keyed method table, a prototype alias, per-handler frame locals | handlerTable, encoder | Table dispatch; prologue and body; SSA renaming and copy propagation on the copy. |
| Decoy parameters dropped, renamed or reused; decoy stores moved into nested statements; methods called on the VM parameter, the constant reader's defaults among them; helpers inlined | classObfuscation with minify, encoder | Decoy stores removed by the unread field, then dead-argument layouts; method calls on any state reference; dropped dummy writes. |

## 5. Known Gaps

None recorded.

## Source

[locate-handlers.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/locate-handlers.js)
(locator, partition, reader entry),
[opcode-table.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/opcode-table.js),
[locate-boot-payload.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/locate-boot-payload.js)
(`locateBootSkeleton`) and
[runtime-fragment-pattern.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/runtime-fragment-pattern.js)
(`cloneRuntimeFragment`, the clones lowering works on).
The readers call `requireIdentifiedHandlers`
([identify-handlers.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/identify-handlers.js)),
which calls `requireHandlers`, at the start of their recognition. The run loop and readers
derive from the pinned
[runtime.ts#L44-L217](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/runtime.ts#L44-L217).

## Fixtures

| Committed fixture or test | Claim pinned |
|---|---|
| [runtime-layers](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/runtime-layers/generation.json) minify-aliased, via [extract-container.test.js](../../../../decoder/decode-js/test/vm/jsconfuser-vm/extract-container.test.js) | L1: a minified runtime's aliases are proved through the view and the decode behaves as the source. |
| [runtime-binding-identities.test.js](../../../../decoder/decode-js/test/vm/jsconfuser-vm/runtime-binding-identities.test.js) | L3: class and table stacks decode identically after every binding is renamed. |
| [runtime-layers](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/runtime-layers/generation.json) minify-table-randomized | A minified randomized handler table is located and its renamed handlers named. |
| [runtime-layers](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/runtime-layers/generation.json) minify-table-{aliased, macro, specialized, anti} | L1 over a handler table: SSA propagation with a coalesced macro variable, and every added kind identified. |
| [runtime-layers](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/runtime-layers/generation.json) class-minify-aliased | L1 under class obfuscation: a decoy parameter stored into an unread field and then reused by minify is dead. |
| [runtime-layers](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/runtime-layers/generation.json) class-minify-specialized | L1 under class obfuscation: the constant reader's defaults are method reads on its receiver, and a field named like a parameter is not its use. |
| The reader owner docs' fixture tables | L2: each added-opcode reader's observations through the view. |
