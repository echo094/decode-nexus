# jsconfuser/control-flow.js

## 1. Target

Reverses js-confuser's
[ControlFlowFlattening](../../../js-confuser/transforms/control-flow-flattening.md) — by
far the largest transform in the pipeline. Recovers the original statement/branch
structure from the state-machine interpreter, undoes literal entanglement and
scope-object flattening, and — where the wrapping harness/call-site scaffolding around a
decoded interpreter is fully understood — collapses that scaffolding away too, as a
second, declinable step.

## 2. Algorithm

Given a flattened function's entry vector, symbolically walk the `while(sum(states) !==
END) switch(sum(states)) {...}` interpreter: resolve each matched case group's statements
against its (now-known) entry vector, and classify its terminal into one of a small,
structurally-distinguished set — an unconditional goto (the block's own jump), a
dead-code guard (an `if` with no alternate whose consequent is a goto pair, proven false
for the current vector), a real branch (an `if` with an alternate where both arms are
goto pairs), a `return`, or a `throw`. This produces a small DAG of real blocks in
execution order, branch points included — **not a flat list**, since which arm of a real
`if`/`else` runs depends on data the decoder can't evaluate, and **not a cyclic graph
either**: the residual is verified acyclic in every sample (see "Lessons for extending
this," Implementation), so no relooper is needed.

Three passes clean that DAG up in place — undo literal entanglement (using each node's
own resolved state vector), flatten the scope-object chain back to plain identifiers
(sharing one naming cache across the whole graph, since one source-level variable is read
from many blocks), and fold the DAG's branch points back into real `if`/`else` statements
(detecting shared merge points by reference count, so a reconverging branch's tail is
emitted once, not duplicated) — then a final pass declares whatever locals the
scope-flattening step introduced. The result is a complete, syntactically valid function
body: **confirmed by assembling it with a real `t.functionDeclaration`, evaluating the
generated code with `new Function`, and calling it** — not just a structural comparison.

At the plugin level, every helper this transform's own output depends on (the sum/slice/
xor functions, the packed sequence/strings blobs) is resolved from its own use site,
never from a Program-level name-keyed pre-pass — see Implementation for why, and
`encoder-decoder-method.md`'s
[W1](../../../encoder-decoder-method.md#t1--w1--w4-order-the-work-from-the-stage-order--not-by-byte-share-and-not-by-probing)
for the general form. An outlined nested function is recognized as a re-entrant call into
the *same* shared switch/case table (not a separate function to decode independently) and
decoded by the identical recursive process. A dispatcher-nested inline interpreter (see
Implementation) is decoded in place first, then — where the surrounding call harness is a
single, non-memoized dispatched function — collapsed away as a distinct, declinable
second step: the interpreter's own decode never changes based on whether the collapse
will fire, so a declined collapse is byte-identical to not having the collapse at all.

## 3. Implementation

### Literal entanglement (`control-flow.js`)

`resolveStateNumber` / `resolveStateBoolean` / `resolveStateString` / `xorDecodeString` /
`makeLiteralResolverVisitor` reduce all three mangled-literal shapes to arithmetic
evaluation given a block's own concrete state vector:

- `states[i] + k` → a number (`resolveStateNumber`, which recurses through `states[...]`'s
  own index too, since a dead-code guard predicate's index can itself come out mangled by
  the same generic pass).
- `states[i] == X` / `!= X` → a boolean (`resolveStateBoolean`).
- `xorFn(states[i] + k, start, length)` → a string, XOR-decoded from the shared
  `{ph}_strings` blob (`resolveStateString`/`xorDecodeString`, a straight port of the
  encoder's own `xorDecodeString`, verified byte-for-byte against real ciphertext).

`makeLiteralResolverVisitor({ statesName, stateValues, xorFnName, stringsBlob })` builds a
Babel visitor from a known state vector. **Deliberately scoped to `+` only** at the
auto-replacing level: the encoder only ever emits numeric-literal mangling as `stateVar +
diff`; a top-level `-` only shows up in state-transition-diff assignments or Stage-3
complex switch-case tests, both belonging to the graph-resolution problem below, so
triggering the visitor on `-` would risk evaluating a transition-diff subexpression
against the wrong reference point. `resolveStateNumber` itself still evaluates `-`
generically, since the graph resolver reuses it later without this ambiguity.

### Transition-graph resolution (`control-flow-graph.js`)

These functions symbolically walk the dispatcher to *produce* the state vector the
literal resolver above needs as input:

- **`decompressStateVector(arrayExprPath, sequence, sliceFnName)`** undoes
  `getSpreadArray`'s compression: a mix of plain number literals and
  `...sliceFnName(min, max)` spreads standing for `sequence.slice(min, max)` against the
  one shared `{ph}_cff_sequence` array.
- **`applyStateMutations(sequenceExprPath, statesName, vector)`** symbolically evaluates
  one goto's assignment `SequenceExpression` against a known entry vector. Mutates a
  *working copy* of the vector in place, left to right — a jump can update several slots
  and a later assignment's mangled diff can read a slot an earlier assignment in the same
  sequence already changed, so resolving every expression against the frozen entry vector
  would silently produce a wrong vector.
- **`evaluateBooleanExpression(path, statesName, vector)`** is a superset of
  `resolveStateBoolean`: also handles `<`/`>`/`<=`/`>=` and a leading `!(...)` negation,
  since dead-code guards and the switch's own clash-avoidance clauses pick from all four
  comparison operators. This proves a guard's truth value for the walker; it doesn't
  render a literal back to source, which is why it's separate from `resolveStateBoolean`.
- **`parseSwitchCaseGroups`** / **`evaluateCaseTest`** / **`matchCaseGroup`** read the
  dispatcher's fallthrough structure: Stage 3 gives every block a contiguous run of
  `SwitchCase`s where all but the last are empty-bodied decoys (or a stray complex test
  shuffled out of place), with the real body on the last one. Which specific test in a
  run is "the real one" doesn't matter for matching — every test in a group reaches the
  same body, and decoy ints are drawn from the same collision-free generator as real
  `totalState`s — so `matchCaseGroup` tries every test in every group and keeps whichever
  evaluates to exactly `sum(vector)`, mirroring `switch`'s own `===` semantics including
  `&&`-guard short-circuiting.
- **`parseDispatcher(mainFnPath)`** reads the fixed harness shape
  (`while(sumFn(states)!==END){ switch(sumFn(states)){...} }`) and returns
  `{statesName, sumFnName, endTotalState, switchLabel, switchPath}`. The dispatcher switch
  is always *constructed* as a labeled statement, but a downstream stage can strip a
  redundant label — `parseDispatcher` accepts both shapes, and every label check
  downstream already treats a `null` label as "don't check." Built on the shared
  `parseWhileSwitch`, which also accepts the `while` body with or without its
  `BlockStatement` wrapper — `Minify` (see encoder doc's Downstream Effects) strips it for
  a single-statement body, printing `while(x)switch(y){...}` with no braces.

**`interpretBlockGroup(group, vector, statesName, switchLabel)`** interprets one matched
case group's statements against its entry vector, distinguishing real payload from
synthetic shapes structurally, never by guessing from a test's contents — see Algorithm
for the five terminal classifications. Two shapes needed dedicated handling beyond the
obvious ones:

- **`throw` as a terminal.** `DeadCode` (an earlier encoder stage, Order 8) injects
  templates whose argument guards `throw`; this transform flattens whatever it finds,
  including a `throw`-terminated block. The statement is carried through as an ordinary
  output statement (getting literal/scope-decoded along with the rest of its group), and
  the walk simply stops there with no successor and nothing to rebuild — `resolveBlockGraph`
  gives the node `type: 'throw'`, and `foldBranchesInGraph`'s `emitChain` ends the chain on
  it exactly as it does for a `return`.
- **Reading a goto whose partition `AstScrambler` dissolved** (a later encoder stage —
  see the encoder doc's Downstream Effects). "Goto pair" is the shape this transform
  *prints* on the encode side — one `ExpressionStatement` wrapping a `SequenceExpression`
  of state updates, then `break` — but AstScrambler can merge that into a no-op call
  spreading the sequence into flat arguments, so the goto reaches this decoder in one of
  three shapes: the original single-statement form, a **run** of separate assignment
  statements + `break` (the un-merged scrambled call), or a **bare `break`** with nothing
  before it (the zero-assignment goto, whose empty-sequence placeholder contributes no
  arguments and so vanishes entirely). `readGotoAssignments` reads one statement's
  contribution (a whole `SequenceExpression`'s expressions, or a lone assignment);
  `matchGotoSequence` takes the exact window ending in `break`; `findGotoRunEnd` slices
  the maximal *trailing* run before the `break`, trailing because AstScrambler merges
  across statement boundaries so real user code can end up sharing a run with the goto's
  updates. The bare-`break` relaxation doesn't weaken the fail-closed guard against an
  unrecognized `break`: `findGotoRunEnd` structurally never returns a window starting at
  one, so only the whole-block callers (the dead-jump guard and the two-armed branch) can
  produce it, and the zero-assignment goto only ever occurs there anyway.

**`resolveBlockGraph(groups, statesName, switchLabel, endTotalState, vector)`** is the
walk loop: `matchCaseGroup` → `interpretBlockGroup` → recurse on whichever successor
vector(s) came back, memoized by vector value so two branches that reconverge share their
tail instead of being walked twice. Dead code needs no separate discarding step: blocks
with no real incoming edge are simply never visited, since the walk only follows vectors
it actually computed.

**`undoLiteralEntanglementInGraph(root, {statesName, xorFnName, stringsBlob})`** walks the
DAG once per node and, for each node with a vector, applies `makeLiteralResolverVisitor`
built from that node's own vector to every statement plus (branch) the test or (return)
the argument. `applyVisitor` exists because `path.traverse(visitor)` only visits a
path's *descendants* — a bare `return 5;` can have the entire mangled expression as the
path itself, needing checked directly — and because Babel mutates a visitor object in
place the first time it traverses with it ("exploding" it), so this takes a factory and
builds a fresh instance per call rather than reusing one across nodes.

**`flattenScopeMembersInGraph(root, {scopeName})`** rewrites every
`scope[scopeProperty][varName]` chain back to a plain identifier. `scope` is a **flat**
dictionary, not nested per ancestor scope — `getObjectExpression` on the encode side walks
the scope-parent chain only to collect every ancestor's own `propertyName` into one flat
object, so a reference from any nesting depth is always this same two-level shape. Each
key is read through the shared `readScopeMemberKey`, which accepts both the encoder's
native bracketed-string form (`scope["x"]`) and the dot-notation form `Minify` (see
encoder doc's Downstream Effects) rewrites it to whenever the key is also a valid
identifier — safe to treat as plain-string either way only because this runs *after*
`undoLiteralEntanglementInGraph`. Needs state shared **across the whole graph**, not
per-node (the same `(scopeProperty, varName)` pair is read from multiple blocks and must
resolve to the same identifier everywhere), so naming goes through one shared cache for
the whole walk — keeping the encoder's own generated replacement name rather than
inventing a fresh one, falling back to a numeric suffix only when two independently-named
scopes' generated names happen to collide.

**`unwrapThisGuardCallee(path)`** runs on each chain the rewrite just dissolved and removes
the guard the encoder wrapped around it. Moving a variable into the scope object re-spells
every read as `scope["a"]["b"]`, and a *direct call* of one then has to be re-guarded as
`(1, scope["a"]["b"])()`, because the member access would otherwise supply a `this` the
original call never had (encoder doc's Implementation, "Preserve proper 'this' context").
Once the chain is a plain identifier, `(1, f)()` and `f()` are the same call and the guard
has no remaining reason — so it is unwrapped here, at the pass that strands it, rather than
tolerated per consumer. The condition is exact: a two-element `SequenceExpression` in callee
position whose second element is the identifier just written and whose first is a numeric
literal. Leaving it was not neutral for a downstream matcher, which is the point — it puts a
`SequenceExpression` where a reference should be, which is what walked
[dispatcher.js](dispatcher.md)'s call-site resolution past its own dispatcher's call sites.

**`dropDeadScopeAnchorsInGraph(root, {scopeName})`** removes what the rewrite above leaves
behind, *inside* the graph and while the scope name still means something.
`flattenScopeMembersInGraph` dissolves every **read** of `scope[scopeProperty][varName]`,
but the statement that created the object — `scope[scopeProperty] = {}` — is one level, so
`matchScopeMemberChain` (which requires two by design) never touches it and it survives
with no reader.

Two passes over the graph via the shared `walkGraphPaths`. Pass 1 collects the anchors and
takes **the holder's binding from one of them**; pass 2 classifies every occurrence against
that binding and filters the dead initializers out of each node's `statements`.
**Removal is a filter on the array `foldBranchesInGraph` emits**, not a `path.remove()` —
the fold rebuilds the body from `node.statements` and discards the original block, so there
is no tree mutation and no scope work for a later re-crawl to trip over. It runs *after* the
outlined-wrapper loop so a scope reference surviving inside a wrapper's decoded body is
reachable, which it has to be: it **fails closed as a whole**, not per anchor, because a
bare reference to the holder (the object escapes, so its property set is observable) and an
unreadable key both make *every* key's liveness unknown rather than one key's.

**`scopeName` is a string, so identity has to come from the binding — this is T2 applied
twice over, and both halves were paid for.** An occurrence is only the holder's when it is
(1) a *reference*, not a binding site, and (2) resolves to the holder's own binding. Without
the first, a `var <name>` declarator, a `function <name>(…)` name, and a nested function's
parameter of the same name each read as the holder used as a bare value — a bail, killing
that whole graph's anchors. Without the second, a shadowing same-named reference does the
same. `RenameVariables` hands out short names that collide freely across scopes, so these
are the common case: fixing both took the graph-bail census to **zero**, and the resolved-anchor
count rose accordingly. The diagnostic tell was that the "live keys" the bails reported were `indexOf`,
`length`, `key`, `val` — `Array`/`String` members, not the random slot keys a scope object
has. Name matching survives only as the fallback when the holder has no resolvable binding,
and then only to fail closed: an unrelated reference can add a live key or force a bail,
never authorise a drop.

**Why this cannot be left to the Program-level cleanup below, which is where it used to
live.** The scope object's binding does not survive the decode — the wrapper's parameter
slot is replaced wholesale — so by the time a Program-level pass runs, `scope` in a leftover
`scope.k = {}` resolves *up the scope chain to an unrelated same-named entity*, and any
reference-count gate weighs that entity instead. On a real sample the resolved holder was a
live UTF-8 encoding helper function with nothing to do with the anchor. Corpus-wide the
signature was unmistakable and is worth keeping as the tell: **every** decline was
`escapes`/`opaqueKey` and **none** was a genuine read of the anchor's own key. Running here
is what makes the binding resolvable at all, which is why it is the fix rather than a
tightening of the gate downstream — `doc-conventions.md`'s "fix it at the pass that produces it."

**`cleanupOrphanedScopeAnchors(programPath)`** is the Program-level backstop for the
remainder: anchors whose enclosing application declined, and anchors a later pass exposes
after this one has run. Since the graph-level drop landed it clears everything that reaches
it, and **decoded output carries no surviving anchors at all** — so on the current corpus it
is a guard against shapes no sample currently produces rather than a working pass. Keep it:
what it exists for is precisely the application this decode could not handle, which is the
case a passing corpus does not exercise.

It comes in two kinds, and **the second is a correctness bug rather than clutter**:

- **The holder is still bound.** The anchor is dead weight, and it pads whatever block it
  sits in — a later pass matching that block statement-by-statement counts it as an extra
  role it has no slot for. This is what was padding the non-call branch of a large share of
  dispatcher bodies.
- **The holder is gone.** The scope object is frequently a *parameter* of the CFF main
  function, and the decode relocates that function's body — so the anchor travels out with
  the body while the parameter does not. The surviving statement is then a guaranteed
  `ReferenceError` on a name that resolves to nothing. Samples on a `high` corpus failed
  exactly this way, and at least one passed the runtime check regardless, because its
  site never executed — the unbound-reference census, not the runtime comparison, is the
  oracle for this class.

Gated on the holder's **binding**, never its name — an unrelated same-named parameter in
some nested scope would otherwise disqualify a live holder, which `RenameVariables` makes
routine by handing out short names that collide freely across scopes. For a *bound* holder
an anchor is dropped only when all three of the following hold, because the holder can be
the concealed-globals object rather than a private local: the holder resolves to a binding
in this file; every one of its references is the object of a member access (a holder that
escapes as a value has an observable property set); and no member access reads that
property, including through a key this pass cannot evaluate. Short of all three the
statement stays — a redundant statement costs readability, a dropped live write is a
correctness bug.

An **unbound** holder inverts that trade and is the one place this pass falls back to name
matching. There are no references to weigh and no binding to interrogate — the binding that
would have answered structurally is precisely what went missing — so the test is an
allowlist of identifiers a `X.prop = {}` write may legitimately target with no binding
(`globalThis`, `window`, `module`, …). Anything else unbound is our own dissolved scope
object, and since an unbound member assignment can only throw, removing the statement
restores the program rather than changing it. Keeping the conservative rule here would have
preserved nothing but the crash.

Its **scheduling is the load-bearing part**, and the reason it is a standalone visitor
(`deScopeAnchorCleanupInit`) rather than another line in the CFF decode's own `Program:
exit`. Judging one anchor dead means reading every *other* member key on the same holder,
and at CFF-decode time those keys are still unevaluated `{ph}_STR_N(a, b)` calls and
unfolded concatenations — which the unreadable-key guard correctly reads as "this might be
the reader", declining every anchor. The keys become `StringLiteral`s only after the
string layer's second visit, so the plugin schedules it there. Same "the pass is right,
its position is wrong" shape as the second `DuplicateLiteralsRemoval` visit, and it will
read as a no-op wherever it is placed any earlier.

**That is not a contradiction with `dropDeadScopeAnchorsInGraph` running at CFF-decode
time**, and the difference is the search scope rather than the schedule. Inside the graph
the keys are already readable — `undoLiteralEntanglementInGraph` has run, which is the
same precondition that lets the flattener match its chains at all. What is unreadable that
early is every key *outside* the graph, and only a Program-level pass has to consider
those.

**`foldBranchesInGraph(root)`** turns the DAG into real `t.Statement[]` — a mechanical
walk, not a fresh reversal problem, since the DAG already *is* linear execution order with
branch/fallthrough targets tagged. The real design question is **merge-point detection**:
a `branch` node's two arms each fold into their own `if`/`else` body, but if both
eventually reconverge on the same later node, that node's statements must be emitted
**once**, after the `if`/`else`, not duplicated into both bodies. `computeMergeRefCounts`
counts, for every reachable node, how many distinct parent edges point at it — a refcount
of 1 means "inline into your one parent," 2+ means "stop here, let whichever ancestor owns
both incoming paths emit you once." The recursive walker (`emitChain`) tracks this via a
`skipFirstCheck` flag that's true only for the DAG's actual root and for a node just
resolved as a branch's shared continuation — a branch arm reached fresh always checks,
since its own first node can itself directly be a merge point shared with some unrelated
branch elsewhere. Fails closed if a branch's two arms disagree about where they
reconverge, since the encoder only produces simple forward-converging diamonds.

**`declareIntroducedVariables(names)`** builds the `var a, b, c;` covering whatever names
`flattenScopeMembersInGraph` introduced — always `var` regardless of the original
`let`/`const`/`var` kind, since CFF doesn't preserve that distinction either. Returns
`null` for an empty list.

**`dropTrailingDeadReturn(statements)`** is the last thing `decodeFlattenedFunction` does to
a body. The graph records a function's implicit "and then it ends" as an explicit `return`
node, so `emitChain` writes one out and every reconstructed body would otherwise close with
a `return;` / `return undefined;` doing exactly what falling off the end already does. Only
those two value-less forms are dropped — a `return <anything else>` at the end of a body is
the function's real result. The call-harness collapse (item 3) appends one of its own for
the opposite reason, and has the matching condition: it adds `return;` only when the spliced
statements would fall through to something, which is *not* the case when the harness is the
tail of a function body.

**Dead is not the same as harmless, and that is why this is worth a step of its own.** The
statement displaces the real last one, and a matcher that reads a template's roles from the
end of a body — [dispatcher.js](dispatcher.md)'s does, because the encoder's own later
stages make counting from the front useless — then sees a shape it cannot recognise. The
same fact holds wherever a shape is recognised by being empty: the corpus census of residual
`PredicateGen` guards used to classify every one of their anchors as one-parameter,
*one-statement* functions — explicitly "not the dummy" — and reads them as one-parameter and
**empty** now that the statement is gone.

### Outlined nested functions

A hoisted `function fnName(...){}` outlines into a `FunctionExpression` re-entering the
*same* shared switch/case table at a different start vector — its own declarator `id` is
just another local of the *outer* flattened function, swept into the generic Identifier
mangling like everything else, so by the time a decoder looks for it, it reads back as an
ordinary `plainIdentifier = function(...rest){ return mainFnName(vector, scopeObjExpr,
runtime, rest) }` assignment, structurally indistinguishable from any other local
assignment except for its `FunctionExpression` shape.

**`matchOutlinedFunctionWrapper`** matches that shape on one `FunctionExpression` path: a
single rest-parameter, a body of just `return mainFnName(...)` (tolerating an optional
leading debug-string-literal statement), exactly four call arguments, the fourth
self-forwarding the wrapper's own rest parameter. The second (scope-object) argument is
deliberately *not* inspected: its ancestor-property values are always a 1-level
`scopeName["X"]` read, never the 2-level chain `flattenScopeMembersInGraph` matches, so
it's inert either way. **`findOutlinedFunctionWrappers`** walks a resolved graph the same
memoized, visit-once-per-node way as `flattenScopeMembersInGraph`, collecting every match.

**`decodeFlattenedFunction(vector, ctx)`** is the module's capstone: the same six-function
pipeline factored into one function so it can call *itself* for every nested wrapper it
finds, starting from a different vector but reusing the identical shared switch/case
table. `ctx.pairNames`/`ctx.usedNames` must be the *same* maps across the whole recursion —
a variable closed over by a nested function and the same variable read in an ancestor
function are, by construction, the identical `(scopeProperty, varName)` pair. Each
wrapper's params/body are replaced in place; `ctx.argName` becomes the decoded function's
real rest parameter directly, so no renaming pass over the decoded body is needed.

**Only when the decoded body actually reads it, though** — `statementsMentionName` gates the
parameter, and the difference between *reads* and *spells* is the whole of it. A source
function declared with no parameters decodes to a body that reads nothing from the packed
arguments, and giving it `(...argName)` regardless invents a parameter the source never had —
free to drop, since a rest parameter contributes nothing to `fn.length` and a name nothing
reads cannot be observed. `dropTrailingDeadReturn` above is the same move on the body's other
end, and both exist for the same reason — [dispatcher.js](dispatcher.md)'s Upstream Effects
owns the account of what each was defeating, per the rule that the affected pass's own doc
holds the fact.

**The scan has to stop at a nested function that rebinds the name, and that is structural
rather than a nicety.** Every wrapper in one recursion is handed the *same* `ctx.argName`, so
a nested wrapper does not merely happen to collide with its parent's parameter — it binds the
identical name by construction. A scan counting any `Identifier` therefore answers "used" for
every function that merely *contains* another decoded function, which is exactly the
population the caller exists to decide; the first version of this gate did, and a wrapper in
the corpus kept an invented rest parameter through every occurrence of the name, each of them
the inner wrappers' own. Descending into a function that rebinds a name is reading
someone else's variable.

Crude in the safe direction everywhere else, though: only parameter shadowing is modelled, so
a nested `var argName` reads as a use and keeps a redundant parameter rather than dropping one
the body reads. The statements are freshly built and not yet attached to the tree, so there is
no scope to consult — the walk is by `t.VISITOR_KEYS`.

One existing bug had to be fixed to reach this: `parseReturnValue` originally assumed
*every* flattened `return` uses the outer entry function's `(didReturnVar = true, value)`
wrap. The encoder's `ReturnStatement` visitor only wraps a return whose nearest enclosing
function is the one currently being flattened — a return physically inside an outlined
nested function's own portion of the table doesn't meet that, so it stays a plain `return
value;`. `parseReturnValue` now tries the wrapped shape first and falls back to the
argument as-is. Separately, an argument-less `return;` — CFF's own `return undefined;`
terminator as `Minify` (see encoder doc's Downstream Effects) reprints it — resolves to
`null`, and every caller carries that through as "returns undefined" rather than as an
unrecognized shape, since treating it as a match failure fails the whole enclosing
application closed.

### Plugin wiring

**Helper identification is structural, never by name** (see encoder doc's Downstream
Effects for why). Each helper is resolved from its own use site:

| helper | resolved from | by |
|---|---|---|
| `_cff_slice` + `_cff_sequence` | the `...slice(min, max)` spread being decompressed | `resolveSliceSequence` (memoized per helper node) |
| `_cff_xor` + `_strings` | any 3-arg call inside the application whose callee binds to a 3-param function reading a Program-level string blob | `resolveXorHelper` |
| `_cff_sum` | the interpreter loop's own `while (F(x) !== N)` test callee | `parseWhileSwitch` |

`resolveFunctionBinding(refPath, name)` is the shared primitive: `scope.getBinding()` to
the declaring function. `findProgramDatumRead(fnPath, initType)` finds the Program-level
`var X = <literal>` a helper reads.

**"Structural" has to mean the binding, not just "not a name."** `resolveXorHelper`
originally also required its candidate's start and length arguments to be `NumericLiteral`s
— true of the shape the encoder emits, and a free-looking extra check. It is not free: this
runs *before* `undoLiteralEntanglementInGraph`, so those two positions can still hold plain
arithmetic, and the gate rejected the only call sites present in a substantial minority of
search roots on a `high` corpus. The blast radius was nothing like the check's size, because a search root
that finds no helper does not fail — it decodes with `xorFnName` null, which is a legitimate
state (plenty of applications entangle no strings) and therefore silent:

- no entangled key can be resolved, so `matchScopeMemberChain` declines those chains;
- `flattenScopeMembersInGraph` rewrites the chains it *can* read and leaves the rest, so one
  scope slot ends up addressed two ways — [encoder-decoder-method.md](../../../encoder-decoder-method.md)'s
  **W5** exactly;
- the body is then relocated out of the function binding the scope object, and the surviving
  reference either dangles (`ReferenceError`) or binds to an unrelated same-named identifier
  in the destination (`TypeError`, or silently wrong output — one such sample produced output
  that never terminated).

A single declined chain out of thousands was enough to do that. Identification now rests only on the
binding and the string blob, the two things that actually distinguish this helper from any
other 3-argument call.

**Fixing it here rather than downstream was the cheaper repair, and the difference was
measured.** A guard making the flatten all-or-nothing per application was written first: it
fixed the sample but cost **3.4x** the output size, since a fail-closed application keeps its
entire interpreter, and it could not be placed anywhere safe — after the flatten it abandons
a tree the flatten has already rewritten in place, and after `undoLiteralEntanglementInGraph`
the input is no longer untouched either, that pass having folded entangled values against one
entry vector into case bodies the surviving interpreter still runs under every other vector.
Resolving the helper instead makes the guard unnecessary: the chains resolve, nothing needs
to fail closed, and the corpus got *smaller* rather than larger.

`matchEntryHarness(stmts, afterIndex, mainFnName, isProgram)` matches the fixed wiring
immediately after the `mainFnName` `FunctionDeclaration`, two shapes mirroring the
encoder's own `isTopLevel` split (a bare call statement at Program level; the full
`didReturnVar`/`result`/`if` triple at Function level). Both `var` slots are read through
`readHarnessSlot`, which accepts either a declaration or the bare assignment
`MovedDeclarations` (a later stage) can rewrite it to — the two slots read
**independently**, since the encoder decides per declaration and can move one while
leaving the other.

`dropDeadHarnessSlot(blockPath, name)` removes what removing that harness orphans, and runs
at the removal site rather than in either matcher because both shapes are dead only *because*
the harness went. Two of them, per application:

- **The hoisted declarator.** `MovedDeclarations`' Mechanism 1 rewrites a `var x = init` into
  an assignment where it stood plus a bare declarator pushed onto the enclosing block's
  *existing* leading `var` statement. Applied to the harness's own two slots, what
  `matchEntryHarness` then matches and removes is the assignment run — the declarators are not
  among those statements and are left with nothing to initialize them. So this removes
  **declarators, never statements**: the statement they landed in routinely also holds live
  user declarations.
- **The `didReturnVar = true` writes.** Stage 2 wraps every return in the flattened function,
  including returns nested inside statements CFF never goto-converted — it converts `if`/`else`
  only, so a pre-existing `switch` is copied through whole and every return inside it keeps its
  wrap, which `parseReturnValue` never sees (it unwraps a return that is a direct member of a
  reconstructed block's statement list).

**The gate is that the flag is unread, not which decode path produced it.** Once the harness is
gone nothing reads the flag, which is exactly what makes dropping its writes unobservable — and
an inline-flattened function keeps its own harness, hence its own reader, so it declines there
without this needing to know that path exists. It fails closed on any write that is not one of
Stage 2's return wraps: with no reader the flag's *value* is unobservable, but an assignment can
still carry side effects, and removing the declarator alone would turn the surviving writes into
implicit globals. Deletion itself stays reference-count-gated through `safeDeleteNode`, which
also declines on a slot MovedDeclarations packed into a *parameter* instead (Mechanism 1's
other insertion method) — removing that would change the enclosing function's arity.

`decodeControlFlowApplication` builds the `ctx` `decodeFlattenedFunction` needs from
`mainFnPath`'s own params plus this application's own `resolveXorHelper` result,
unwrapping a decoded body's trailing `return` back to a plain expression statement at real
Program level (a bare `return` there is a syntax error, and only Stage 1's synthetic
"last expression → return" conversion could have produced one).

`decodeControlFlowFlatteningInBlock(blockPath)` is the per-block driver: candidates are
`FunctionDeclaration`s that `parseDispatcher` accepts (a body of exactly one interpreter
loop) — immune to renaming and, measured against the old `.endsWith('_main')` suffix gate,
strictly narrower with no false positives. Because `MovedDeclarations` can separate a
`_main` declaration from its harness (relocating the declaration to the top of the
enclosing body while the harness stays where it ran), the harness is **scanned forward
for**, not read at a fixed offset, and the decoded body is **spliced in at the harness**,
not at the declaration.

`deControlFlowFlatteningGraphInit()` is the exported visitor: `Program: exit` fires last,
after every nested `Function: exit` already ran its own replacement, handles the
Program's own top-level application if any, then cleans up shared helpers via
`safeDeleteNode`. No `Program: enter` and no shared state — with per-use-site resolution
there's nothing to discover up front, so no single gate's failure can take down every
application at once.

`cleanupOrphanedCffHelpers(programPath)` is the one place use-site resolution can't serve
(a helper with no remaining use site has no use site to resolve from). It matches the four
fixed helper body shapes directly (slice, xor, hash — anchored on `HashFunctionTemplate`'s
four seed constants, which survive both `minify` and `renameVariables` — and sum),
collecting all matches before deleting anything, since a data var is found *through* the
helper that reads it. Deletion stays reference-count-gated via `safeDeleteNode`.

Legacy path: `deControlFlowFlatteningStateless` matches a pre-2.0 constant-properties
control-object shape (`controlVar = { <key>: <literal>, ... }`), confirmed via `git log -S`
to exist only between the encoder's `09aef99` and `dd408e8` commits and absent from the
pinned `31c5a47`. Kept for real-world samples predating the 2.0 rewrite; no test coverage
(nothing can generate that shape from the pinned encoder to test against).

### Inline-flattened (dispatcher-nested) functions

When Dispatcher (an earlier stage) nests a function and this transform then flattens it,
the interpreter surfaces **not** as a `_main` `FunctionDeclaration` + entry harness but as
an **inline** `<name> = function (...rest) { var …; [states, scope = {…}, runtime, arg] =
rest; while (...) switch (...) {...} }` assigned to a local, with its harness in the
enclosing scope.

- **Detection**: `matchInlineFlattenedFunction` (local-array-state variant) and
  `matchScopeMemberInterpreter` (state lives in a `scope["a"]["b"]` member, emitted inline
  in a parent application's case body) — both reuse `parseWhileSwitch`, generalized to
  accept either an Identifier or a computed-member state. That generalization also covers
  a shape neither variant actually needs it for: an in-place scope-member interpreter with
  no function wrapper at all, sitting directly inline in a block. Investigated and not
  decoded on purpose — checked corpus-wide against real samples with zero survivors of that exact
  shape, so `matchScopeMemberInterpreter` matching it is a tripwire (it would fire if the
  shape ever showed up) rather than groundwork for a planned decode path.
- **Decode**: `decodeInlineFlattenedFunction`, wired into the CFF visitor's `Function:
  exit`. Unlike a `_main`, an inline fn's `scope`/`runtime`/`arg` may be values its caller
  passes and the decoded body may still read them, so only the `while`/`switch` is
  replaced (via the same `decodeFlattenedFunction`) and the rest-param unpack is left
  standing — `collapseInlineFlattenedFunction` then tries to fold the wrapper away
  entirely (below).
- **Entry vector**: the fn's single **external** call site, via `collectInlineEntryVectors`
  with the fn's own body excluded — in-body self-calls are its fresh-scope nested
  wrappers, decoded in place by `findOutlinedFunctionWrappers`, now comma-guard-aware
  through `resolveGuardedCallee` (unwraps the `(1, fn)` sequence guard the encoder emits
  to null the callee's `this`).

**Collapsing the call harness.** Decoding the interpreter in place is
correctness-complete but leaves the wrapper it lived in standing: a rest-param destructure,
a ~100-element entry vector built from `_cff_slice(...)` calls (which is also what keeps
the Program-level slice/sequence helpers referenced — an orphaned helper here is a symptom
of this residue, not a defect in `cleanupOrphanedCffHelpers`, which is correctly
reference-count-gated). `matchInlineEntryHarness` reads the harness through the same
`readHarnessSlot` as a `_main`'s, plus two differences from being an expression assigned to
a local: the callee carries the `(1, fn)` comma guard, and the `if` may carry an `else {
return; }` (not in the encoder's own Template, but produced once the enclosing function's
own flattening folds its harness back into a linear block).

`collapseInlineFlattenedFunction` splices the decoded body into the enclosing block and
deletes the wrapper. Three design points:

1. **A second step, not a mode of the decode.** `decodeInlineFlattenedFunction` always
   keeps `keepReturnFlag: true`, so a declined collapse leaves exactly the output it
   produced before the collapse existed. The `flag = true` writes are stripped *here*,
   keyed on the harness's own flag name, so a nested outlined function's returns (never
   flag-wrapped) are untouched by construction. Whether to strip the flag is a decode-mode
   choice the AST alone can't answer — `_main` and an inline fn are structurally identical
   at the point the flag is set, so this is threaded explicitly from the decode entry
   point rather than inferred from scope.
2. **`scope`/`runtime`/`arg` are re-declared, not bailed on**, whenever the decoded body
   still reads them after the matcher confirms the entry call passes only the state
   vector — a bare surviving read of `states` **is** still a bail, since that's the
   decode's own scaffolding with no call-time value to reconstruct.
3. **Deletion is by paths collected before any mutation, not `safeDeleteNode`** — a
   preference, not a requirement: every count this collapse needs has just been verified, so
   the reference-count re-check would add nothing. `safeDeleteNode` is safe to call here (see
   Upstream Effects for what a wrapper-body rewrite does and does not do to a binding).

**Dispatcher-closure residue is not collapsed here, and must not be.** CFF stacked on
Dispatcher wraps an already-decoded interpreter body in a dispatcher-nested-function
skeleton: a dispatch object invoked by key, a memoization layer, and a shared-arg-slot
convention. This pass's whole obligation to that shape is to decode the interpreter, which
restores the skeleton to the plain template spelling — at which point it is an ordinary
dispatcher and [dispatcher.js](dispatcher.md), scheduled after this decode, reverses it with
no special case. A narrow collapse of the single non-memoized shape was once built here as
well; it matched nothing on the corpus and nothing on its own fixture, because the
dispatcher pass had already taken every application before it ran, and it has been removed.
The general lesson is
[encoder-decoder-method.md](../../../encoder-decoder-method.md) T8's first in-tree check:
**a second identification path for an entity some other pass already resolves is the thing
to look for before building one**, and a fail-closed duplicate is invisible precisely
because declining costs nothing.

**Checked and not built.** Two further follow-ups that reading suggests and measurement
closed: a **fixpoint re-scan** for inline fns only revealed by decoding an outer one is not
needed (every sample came out complete after a single pass), and **expression-valued
dispatcher end states** are not a gap — the pinned encoder emits no such shape. Together
with the in-place scope-member interpreter above, that is three shapes deliberately left
undecoded on evidence; none is deferred work, and none should be re-opened without new
evidence of its own.

### Lessons for extending this

1. **The residual is acyclic — there is no relooper, and none should be built.** It first
   *looked* self-recursive (an inline fn calling itself), which motivated a whole
   cyclic-CFG builder that then found **0 back-edges across every sample**, including one
   with a real source `for` loop. The apparent self-recursion is fresh-scope
   nested-wrapper re-entry (each self-call passes a *new* scope object) — an outlined
   nested function, not a control-flow back-edge. Verify cyclicity empirically (decode one
   entry, check for surviving interpreter loops) before assuming a structuring pass is
   needed.
2. **Whether to strip the `didReturn` flag is a decode-mode choice, not derivable from the
   AST** — see point 1 under "Collapsing the call harness" above; the same reasoning
   applies to any future decode path that might set or clear it.

## 4. Upstream Effects

**This decode's candidate scan only finds anything because
[`deMovedDeclarations`](moved-declarations.md) has already run.** Candidates are
`FunctionDeclaration`s that `parseDispatcher` accepts, and MovedDeclarations (encoder Order
25, later than this transform's Order 24) can pack an interpreter's own `_main` away
entirely — retyped to an anonymous `FunctionExpression`, its name appended to the enclosing
function's parameter list, and a guarded re-assignment prepended in its place. There is then
no `FunctionDeclaration` in the block to find, the per-block driver reports zero
applications, and **the whole CFF layer for that block fails closed** while the output stays
perfectly correct at runtime. That pass restores the declaration, and also removes the dead
parameter slot it was packed into — which matters here as well, since a slot left behind
shadows the restored declaration in Babel's scope and puts it in `constantViolations`, where
a `binding.path`-keyed lookup does not see it either.

The dependency is on *our pipeline order*, not on the encoder's: the fix for the packed
`_main` was to schedule `deMovedDeclarations` before this pass, not to teach this matcher a
second shape. Nothing in this pass's own behaviour records that, which is the usual problem
with a fail-closed dependency — it reports "no applications here" identically whether the
block has none or has one it cannot see.

Distinct from the above, and **encoder-side rather than upstream**: MovedDeclarations also
*separates* a `_main` declaration from its entry harness and rewrites the harness's own two
`var` slots to bare assignments, hoisting their declarators to the top of the enclosing body.
Those are handled inside item 3 (`readHarnessSlot`, scanning forward for the harness rather
than reading it at a fixed offset, and `dropDeadHarnessSlot` for the declarators the removal
orphans) because they are residue this decoder reads, not a shape another of our passes
produced.

**Stage 2's return wrap reaches `dropDeadHarnessSlot` in more than one width, and the wider
one is the encoder's, not ours.** The wrap is `(didReturnVar = true, value)` — but `value` is
not always a single expression, because a sequence nested inside the wrap is *flattened into
it* rather than kept as its own node. Any transform that had already re-spelled a return's
value as a sequence therefore arrives here as one wider sequence. Which ones are still in the
input is set by the two orders together: an encoder stage earlier than this transform's Order
24 whose decode *our* pipeline schedules after the CFF decode is undecoded input at this
point.

| spelling | produced by | why it is still in this pass's input |
|---|---|---|
| `return didReturnVar = true, value;` | ControlFlowFlattening Stage 2 alone (encoder Order 24) | the base case — nothing else touched the return |
| `return didReturnVar = true, payload = [...args], dispatch(k);` | Stage 2 wrapping a call [Dispatcher](dispatcher.md) (encoder Order 6) had already re-spelled | `deDispatcher` runs long *after* this decode in our pipeline, so the payload sequence is still in the encoder's spelling here |

The gate is therefore *"the write is the sequence's **first** expression"*, and what replaces the
wrap is `expressions.slice(1)` — the whole tail, rebuilt as a sequence when more than one
survives. Two narrower readings are both wrong, and the second is worse than declining:
requiring exactly two expressions declines the whole second row, and taking `expressions[1]`
as "the value" would silently discard the payload assignment the call depends on. Position
matters as much as width — a write that is *not* the head belongs to some construct this has
no basis for reordering, so that still fails closed.

Declining the second row was not merely untidy residue. The orphaned `var didReturnVar;` it
left behind was a second statement in a proxy method body, which failed
[`deFlatten`](flatten.md)'s one-statement property gate, which failed the property, the scope
object, and the whole wrapper — so one un-swept declarator held an entire Flatten layer shut.
That is the general shape worth carrying: a cleanup that fails closed is invisible in its own
pass and shows up as a *different* pass declining.

**`cleanupOrphanedCffHelpers` runs twice, and the second sweep's input is
[dispatcher.js](dispatcher.md)'s output.** The four Program-level CFF runtime helpers are
removed by reference count, and the dispatcher template is routinely the last thing holding
that count above zero — its entry bodies are what the `_cff_slice` entry vectors were built
for. The sweep scheduled inside this decode therefore *correctly* declines on those helpers,
and only the sweep after the dispatcher decode (`deCffHelperCleanupInit`) can reach them.
This is the S3 caveat in its exact form: an undeleted helper here is a symptom of a layer
still undecoded, never a defect in the reference-count gate
([encoder-decoder-method.md](../../../encoder-decoder-method.md) S3, "chase the residue
holding it alive"). Deleting the second sweep's slot on the grounds that the first one exists
would leave every CFF+Dispatcher sample carrying all four helpers.

**A wrapper-body rewrite leaves stale bindings behind, and every later pass doing scope work
inherits them.** `decodeFlattenedFunction` installs a decoded body over an outlined wrapper
by assigning `functionPath.node.body` directly, so any binding a caller resolved beforehand
still points into the block that is now gone. What that costs is narrower than it looks, and
the two halves are worth separating because the wrong half was documented here for a while:

- **Re-registration is not the problem.** A crawl — scope-local or Program-level — rebuilds
  the new body's bindings correctly, and `path.scope.getBinding` on a name the rewrite kept
  resolves to the new declaration. A path-based `get('body').replaceWith(…)` behaves
  identically, so switching to one fixes nothing; Babel's child-path cache is keyed by node
  identity and simply misses, yielding a fresh path either way.
- **The stale binding is the problem, and only when the rewrite *dropped* the name.** The
  caller hands `safeDeleteNode` a binding registered against the old body; its internal
  `binding.scope.crawl()` rebuilds from the new one, the refreshed lookup finds nothing, and
  the old code dereferenced that. It now declines — the same answer its entry guard already
  gave for a name that binds nowhere, since that is the same state discovered one step later.

So `safeDeleteNode` is safe after a wrapper rewrite, and a caller wanting the deletion to
actually happen must still resolve its target *after* the rewrite, not before — declining is
the correct report for a name that no longer exists, not a gap to widen.

### What this pass emits that the rest of the pipeline has to read

The inventory [doc-conventions.md](../../../doc-conventions.md)'s item-4 home rule asks a producing pass to keep: one
list, here, rather than the mechanism restated in every consumer that trips over it. Every
row below has cost a consumer a silent fail-closed decline at least once.

| emitted shape | consumers that must accept it |
|---|---|
| `var f;` + `f = <fn>` for a reconstructed function's holder — and `var f = <fn>` where nothing splits it | the two opposed groups in [moved-declarations.md](moved-declarations.md) item 4 |
| a rest parameter on **every** reconstructed function, whether or not the original had one | [variable-masking.md](variable-masking.md) item 4, `deFlatten`'s `FunctionDeclaration` gate ([flatten.md](flatten.md)) |
| the masked stack as `var stk;` + `[...stk] = rest;` | [variable-masking.md](variable-masking.md) item 4, which also deletes the declaration once the copy goes |
| a **nested** pattern element inside the fold, `[a, [b, c]] = rest`, whenever the reconstructed function had a pattern parameter | [variable-masking.md](variable-masking.md) item 4 — `readFoldedElement` moves the pattern into the parameter list unchanged; declining it leaves every such function rest-masked |
| a merged hoisted `var a, b, c;` at the top of every folded body | anything reading a body's leading statements by position |

Three further shapes it *stopped* emitting are in [dispatcher.md](dispatcher.md) item 4, kept
there because the fix was here and the symptom was theirs.

#### Who reads the split declaration, and which way round

**Moved to [moved-declarations.md](moved-declarations.md) item 4.** The `var x;` + `x = v`
population those consumers actually read is Mechanism 1's, not this pass's — `CUT=pack` shows
the Program-level hoist and the bare `var` inside a Flatten wrapper already written before any
pass of ours runs. That page owns the two opposed consumer tables, the "a grep is not the
census" warning, and the spelling-agnostic pattern list; this one keeps only what it emits
itself, below.

**Every name this decode introduces is emitted as a merged hoisted `var a, b, c;` plus a
separate assignment further down, and later passes keyed on an initialized declarator decline
on the result.** `flattenScopeMembersInGraph` rewrites the CFF scope object's members to bare
identifiers without declaring them, and `declareIntroducedVariables` then declares the whole
set in one statement at the top of the folded body, leaving each value to arrive as
`name = <value>`.

**MovedDeclarations writes an indistinguishable shape, so attribute per name, never per
spelling** — the `CUT=pack` table in
[moved-declarations.md](moved-declarations.md) item 4 is the check, and it is what separates
this pass's population (the GlobalConcealing switch function, unanimous across the samples
carrying it) from that transform's.

**Joining the two halves at emission looks like a two-line change and is not, because this
pass is also the shape's largest consumer.** `var` hoisting makes `var f; … f = v;` and
`… var f = v;` exactly equivalent, so the rewrite is textual — but the collapse and harness
machinery in item 3 depends on an *invariant* the merged declaration provides rather than on
the spelling itself: that removing one declarator never empties its statement.
`readHarnessSlot` accepts either spelling on purpose, and `decodeInlineFlattenedFunction`
resolves its name from an `AssignmentExpression` or a `VariableDeclarator` parent — so the
readers are spelling-agnostic and the dependency is invisible in them. Un-merge the
declaration and `collapseInlineFlattenedFunction` removes the sole declarator of a `var flag;`,
which is the `anchor` it then splices the lifted body onto, and Babel throws `NodePath has
been removed`. Guarding that one line is six lines and provably inert, and it is **not
sufficient**: with it in place and only the unconditional `var x = <value>` half enabled,
`control-flow-flattening-minify-return` decodes *better* than its fixture while
`control-flow-flattening-moved-declarations` regresses to several times its fixture size — a
partial non-decode from a second dependency that has not been isolated. **Anything that
normalizes this shape has to be
scheduled after this pass's own consumers have run, not folded into the emission** — and
restricted to the names recorded here as introduced, so it can never touch a declaration the
author or the encoder wrote.

## 5. Known Gaps

- **One unreproduced crash**: a `high`-preset run once died with `"X ,-<.<" is not a valid
  …"` (pre-`throw`-fix). Not seen again since; re-open only if it recurs.

## Source

[`src/visitor/jsconfuser/control-flow.js`](https://github.com/echo094/decode-js/blob/6c974fb5720518fac9c6b3d4cf558ba90ef9f8e7/src/visitor/jsconfuser/control-flow.js) (literal entanglement) +
[`src/visitor/jsconfuser/control-flow-graph.js`](https://github.com/echo094/decode-js/blob/6c974fb5720518fac9c6b3d4cf558ba90ef9f8e7/src/visitor/jsconfuser/control-flow-graph.js)
(everything else), wired into
[plugin/jsconfuser.js](../../plugins/jsconfuser.md).

## Fixtures

`test/jsconfuser/control-flow-flattening*` and `test/visitor/jsconfuser/control-flow*` — the
broadest coverage of any pass here. **Individual fixtures are cited inline above, at the
mechanism each one pins**, rather than listed again here: this pass has enough of them that a
flat list would say less than the citations do. See [tests.md](../../tests.md) for the
harness.
