# jsconfuser/moved-declarations.js — reversing the parameter-packing guard

## 1. Target

Reverses js-confuser's [MovedDeclarations](../../../js-confuser/transforms/moved-declarations.md)'s
mechanism 2 (nested `FunctionDeclaration` → appended parameter + `if (!X) { X = function
(…) {…} }` guard) in full — the guard statement is replaced in place by a real
`FunctionDeclaration`. Mechanism 1 (single-declarator `var` → bare assignment) is
deliberately left unreversed: the shared
[`split-variable-declaration.js`](../split-variable-declaration.md) splits the merged
`var a, b, c` the block-top hoist produces, but the assignment form itself is valid,
readable code and not fully reversible in principle (restoring `var x = 1;` from `var x;`
+ `x = 1;` would require proving nothing reads `x` in between).

## 2. Algorithm

Reversing mechanism 2 is not just a readability question: while its guard stands, the
function is not a `FunctionDeclaration` at all, so every decode pass that identifies
structure by declaration shape stops seeing it — silently, and without any runtime symptom,
since the packed code is perfectly correct. That makes this pass a prerequisite for those,
which is why it is scheduled early; each affected pass records the dependency in its own
Upstream Effects section rather than it being enumerated here (the
[ControlFlowFlattening decode](control-flow.md) is the one that has actually been bitten).

`matchPackedFunctionGuard` requires the exact emitted shape, fail-closed on anything else:
an `IfStatement` with no alternate; a prefix `!` test on a bare `Identifier`; a consequent
holding exactly one `ExpressionStatement` (accepted as either a block or a bare statement,
since `minify` strips braces from a single-statement consequent) assigning the same name
with `=` to a `FunctionExpression` with no `id` (the encoder always clears it, so a
*named* function expression here is somebody else's code). `findPackedParameter` then
confirms the name is a genuine slot: a plain `Identifier` in the enclosing function's
parameter list, `binding.kind === 'param'`, with exactly one assignment anywhere — the
guard's own.

The guard statement is replaced in place by a real `FunctionDeclaration`, the scope is
re-crawled, and the now-dead parameter is spliced out of the signature.

**Removing that slot is load-bearing, not cosmetic.** A parameter and a restored
declaration of the same name are a *single* binding, and Babel resolves it to the
parameter: `binding.kind` reads `param`, `binding.path` is the parameter's own
`Identifier`, and the restored `function X(…) {…}` is demoted to a `constantViolations`
entry. So a pass that identifies structure as "a binding whose path is a
`FunctionDeclaration`" — the rename-proof idiom this decoder is built on throughout —
stops seeing a declaration that is sitting right there in the body, and fails closed on
it. That is the same class of silent, total failure as leaving the guard itself in place
(above); it just moves one step later.

Splicing an *interior* slot renumbers every parameter after it, so it is gated on arity
rather than done unconditionally: the slot is removed when it is the last parameter (which
renumbers nothing), or when no call site of the enclosing function passes an argument that
far. `maxArgumentsAtCallSites` establishes the second all-or-nothing, declining on
anything it cannot see the whole of — an owner that is not a named `FunctionDeclaration`,
an unresolvable binding, a reference that is not the callee of a call or a `new`
(`new F(a, b)` binds positionally exactly as `F(a, b)` does, so it reads an arity just as
well), or a spread argument. An owner with no references at all splits by scope: a
Program-level one may still be an entry point called from outside the file, so its
argument counts are unknowable, while a function-scoped one that nothing references cannot
be reached at all and no argument ever lands in any of its slots.

## 3. Implementation

Reversing mechanism 2 restores the declaration **where the guard stood** (the top of the
enclosing body), not at its original offset, which the encoder discarded. For CFF that
separates `_main` from its entry harness, which the encoder emits immediately after it —
two adjustments in `decodeControlFlowFlatteningInBlock`:

- the harness is **scanned forward for**, not read at `i + 1` — the run itself always
  stays contiguous and `matchEntryHarness` keys on `mainFnName`, so a scan cannot pick up
  a different application's harness.
- the decoded body is spliced in **at the harness**, not at the declaration — the harness
  is where the flattened code actually ran, and the declaration is removed separately.

`matchEntryHarness` separately accepts mechanism 1's rewrite of its own two `var` slots
(`didReturn = undefined;` / `result = _main([…]);`) via `readHarnessSlot`, read
independently per slot, since mechanism 1's `isDefinedAtTop` early-return can skip one
declaration while moving the other.

**Structural throughout, verified safe under `RenameVariables`.** The pass reads no name
*text*, only that the guard's three identifiers agree with each other and that one of
them is a parameter binding — the collision class that hit
[flatten.js](flatten.md)/[calculator.js](calculator.md)/[global-concealing.js](global-concealing.md)/
[variable-masking.js](variable-masking.md)/[string-concealing.js](string-concealing.md)
cannot occur here.

## 4. Upstream Effects

**This pass's one structural decline is invisible in the output because
[dispatcher.js](dispatcher.md) runs later and removes the shapes it declines on.**
`maxArgumentsAtCallSites` resolves call sites through the owner's *own* binding, and a
function expression sitting at `{ ["key"]: function (…) {…} }` has none — it is reached
through the object, so nothing here can bound its arity, the splice declines, and the
restored declaration stays shadowed by the parameter with the downstream consequence §2
describes. On a `high` corpus **every** instance of that shape is a
[Dispatcher](dispatcher.md) `fns` entry, and the Dispatcher decode reconstructs those
functions outright, so the residue is gone from decoded output without this pass gaining an
arity route.

Worth stating as a dependency rather than deleting, because the decline is still real and
the guard still fires: what makes it costless is a *later pass in our own pipeline*, not
anything this one does. If a dispatcher ever declines again the shadowed declarations come
back with it, and they will read as a defect in `maxArgumentsAtCallSites` rather than in the
pass that owns the population. [dead-code.md](dead-code.md) carries the other half — a dead
helper packed into one of those same slots, unreachable for the same reason and retired by
the same decode.

### The split declaration this pass leaves standing

Mechanism 1 is deliberately unreversed (item 1), so `var x;` … `x = v;` reaches every pass
scheduled after this one, and the shared
[`split-variable-declaration.js`](../split-variable-declaration.md) re-spells the encoder's one
merged `var a, b, c;` into N solo statements on the way. **This pass emits nothing here** — the
shape is the encoder's and we decline to reverse it — but it owns the ground, so the consumer
audit lives here once rather than restated in each matcher that trips over it
([doc-conventions.md](../../../doc-conventions.md)'s item-4 home rule).

**Two producers write an indistinguishable shape, and telling them apart is per-name, never
per-spelling.** Reading the spelling has misattributed it in both directions, most recently
into a worklist item built on the wrong owner. The check costs seconds: cut the pipeline at
`pack` — the stage breadcrumb's tree dump ([probes.md](../../probes.md)), where the tree is
unpacked but no decode pass has run — and read
what the encoder actually wrote.

| population | what `CUT=pack` shows | whose |
|---|---|---|
| a Program-level `var x;` … `x = v;` | statement 1 is already `var a, b, …, o;`, split into solo statements later by our own pass | **this transform's** |
| a bare `var s;` inside a Flatten wrapper | `function W(…){ var s; …` is already there | **this transform's** |
| the [GlobalConcealing](global-concealing.md) switch function | `X.Y.name = function (…){…}` — an anchor property, no declaration anywhere, unanimous across the samples carrying it | the [CFF decode](control-flow.md)'s |

**Neither of the first two is worth rejoining.** `var x; … x = v;` reads no worse than
`var x = v;`, the byte delta is nil, and the encoder's split is indistinguishable from an
author's own deferred assignment — so a general reversal edits author-written code. What the
gap between the two statements *contains* is a separate and far more productive question: it is
a locator for an undecoded layer, which is how [flatten.md](flatten.md) item 4's scope-object
residue was found.

#### Who reads it, and which way round

Audited 2026-08-03 across every pass scheduled after this one, by grepping for the tests that
can tell `var x;` + `x = v` apart from `var x = v` (`.init`, `isVariableDeclaration`,
`isVariableDeclarator`). **The consumers are not on one side**, which is what makes "just
normalize the shape" wrong however it is scheduled: a rewrite in either direction fixes one
group by breaking the other. Cite by function name — line numbers drift.

**That grep is not the whole census, and what it missed was the largest consumer of all.**
A gate can demand the joined form without naming a declarator at all:
`binding.path.isFunctionDeclaration()` reads false on the split spelling just as surely as
`!declarator.init` reads false on the joined one, and it matches none of the three search
terms above. [global-concealing.md](global-concealing.md)'s sniffer cleanup was gated that
way, silently kept a dead helper on a large share of samples, and did not appear in either
table below until it was found by *reading ranked residue* rather than by re-grepping.
**A spelling audit has to enumerate the shapes a binding can define, not the tests a matcher
might spell them with** — `isFunctionDeclaration`, `isClassDeclaration` and a bare
`binding.kind` check all encode the same assumption.

**Require the split form** (an initializer makes them decline):

| pass | site | what it demands |
|---|---|---|
| [variable-masking.md](variable-masking.md) | `unmaskDestructuredRest`, pre-destructuring scan | every statement above the unpack is an *initializer-less* declaration |
| [variable-masking.md](variable-masking.md) | `unmaskDestructuredRest`, name check | each destructured name's declarator has no `init` |
| [duplicate-literal.md](duplicate-literal.md) | the array binding gate | declarator with **no** `init` plus exactly one write — the split form named explicitly |
| [string-concealing.md](string-concealing.md) | wrapper-body scan | every statement before the `return` is an initializer-less declaration |
| [dispatcher.md](dispatcher.md) | `isInertAboveUnpack` | a `VariableDeclaration` counts as inert only if no declarator has an `init` |
| [string-concealing.md](string-concealing.md) | `addDependency` | an initialized declarator skips the value-override path (behaviour change, not a decline) |

**Require the joined form** (the split makes them decline):

| pass | site | what it demands |
|---|---|---|
| [flatten.md](flatten.md) | the `arguments` alias read | `var x = arguments` |
| [lock.md](lock.md) | six template reads | each names an initialized declarator |
| [rgf.md](rgf.md) | the payload array, the `arguments` alias, the integrity read | initialized declarators |
| [control-flow.md](control-flow.md) | the harness's own two-declarator read | an initialized declaration |

**Spelling-agnostic, and the pattern to copy**: `utility/binding-def.js`,
[control-flow.md](control-flow.md)'s `readHarnessSlot`,
[dispatcher.md](dispatcher.md)'s `readDispatcherCandidate`,
[global-concealing.md](global-concealing.md)'s holder read **and its sniffer cleanup**,
[calculator.md](calculator.md)'s holder read and dispatch-fn cleanup,
[string-concealing.md](string-concealing.md)'s `resolveDeclaredValue`, and
[flatten.md](flatten.md)'s `matchWrapper` — the last two of which moved out of the second
table by being rewritten this way — the sniffer cleanup the larger of the two, and **the
single largest readability change this shape has produced**. Each asks
what the binding *defines* instead of how the declaration is written, and none of them
appears in either table above.

## 5. Known Gaps

None currently open. Mechanism 1's unreversed split is a decision (item 1), not a gap.

## Source

[`src/visitor/jsconfuser/moved-declarations.js`](https://github.com/echo094/decode-js/blob/6c974fb5720518fac9c6b3d4cf558ba90ef9f8e7/src/visitor/jsconfuser/moved-declarations.js), wired into
[plugin/jsconfuser.js](../../plugins/jsconfuser.md) early — item 2 has why it must precede
every pass that identifies structure by declaration shape.

## Fixtures

`test/visitor/jsconfuser/moved-declarations/`:

| fixture | what it pins |
|---|---|
| `simple` | the base guard-to-declaration rewrite |
| `trailing-var-slot` | the last-parameter case, where splicing renumbers nothing |
| `nested` | a guard inside a nested function body |
| `not-packed` | the four shapes that must **not** match — a local `var` rather than a parameter, a named function expression, a slot written more than once, and a guard with an `else` |

`test/jsconfuser/control-flow-flattening-moved-declarations.{src,,fix}.js` — a real
`{ controlFlowFlattening, renameVariables, movedDeclarations, dispatcher, minify }` encode
with `_main` packed away, decoding to zero residual interpreters. `dispatcher` is
load-bearing in that combo: it is what nests `_main` inside a `PREDICTABLE` function, and
without it MovedDeclarations never packs it at all.
