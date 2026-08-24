# Control-flow expression storage

The `ControlFlowFlattening` (4) transformer that lifts expressions out of a function into a table of
trivial wrapper functions and calls back into it: `FunctionControlFlowTransformer`, its four
replacers, and the custom nodes they emit. Gated on `controlFlowFlattening` and its threshold.

Two era axes, because one part moves and the rest does not:
[`E-cff-storage-*`](../versions.md) for the storage object and its call sites,
[`E-cff-callee-*`](../versions.md) for the call-expression wrapper.

## 1. Target

**Put an indirection between an operation and the operator that performs it.** A `a + b` becomes a
call to a function that happens to add; a `f(x)` becomes a call to a function that happens to call
its first argument; a string literal becomes a property read. The operator, the callee and the
literal all move to one place, and every use site becomes a call into that place.

The second, quieter goal is **reuse**: several sites sharing an operator can share one wrapper, so a
storage entry's arity says nothing about how many places use it and the call sites do not partition
by entry.

## 2. Algorithm

On `leave` of every `FunctionDeclaration`, `FunctionExpression` and `ArrowFunctionExpression` with a
block body:

1. **Choose a host** — the statement list the storage object will be prepended to. Not the function
   itself in general; see item 3.
2. **Get or merge the storage for that host.** If the host already carries one, its existing storage
   node is removed from the host and its entries are merged into the new storage, which also takes
   over the old storage's identifier. So one host ends with exactly one storage object holding every
   entry contributed by every function that chose it.
3. **Walk the function body** with `estraverse.replace`, and for each node whose type has a
   registered replacer, roll the threshold and replace it.
4. **If the storage is empty, leave the function alone.** Otherwise build the storage object and
   prepend it to the host.

The four registered replacers, all of which put a value in the storage under a fresh key and return
a call or read against that key:

| Node | Stored value | Call site | Reuse key | Reuse chance |
|---|---|---|---|---|
| `BinaryExpression` | `function (x, y) { return x <op> y }` | `S.k(left, right)` | the operator | `0.5` |
| `LogicalExpression` | `function (x, y) { return x <op> y }` | `S.k(left, right)` | the operator | `0.5` |
| `CallExpression` | `function (callee, param1, …) { return callee(param1, …) }` | `S.k(callee, …args)` | `String(arguments.length)` | `0.5` |
| `Literal` (string) | the string literal itself | `S.k` | the string's own value | `1` |

**The left and right operands move into the call unchanged**, so the operands are not hidden — only
the operator is. The same holds for the callee and the arguments.

## 3. Implementation

### Host selection

`getParentNodesWithStatements(functionNode.body)` collects, innermost-first, the enclosing nodes
that hold *lexical scope* statements — function bodies and the `Program`, never an arbitrary block
and never a `SwitchCase`. The function's own body is excluded from that walk by a depth guard.

- **One entry** (only `Program`, i.e. a top-level function) → the host is **the function's own
  body**.
- **Otherwise** the `Program` entry is popped, the list is capped at the nearest **two** enclosing
  function bodies, and one of them is picked at random.

So a storage object is always prepended to a *function body*, never to the `Program` and never to a
bare block. Confirmed on the frozen corpus: every storage object found sits in a `BlockStatement`
(`u5-shape.mjs`, 2026-08-14).

`hostNodeSearchMinDepth` is `0`, which makes the `splice(0, hostNodeSearchMinDepth)` that uses it a
no-op; `hostNodeSearchMaxDepth` is `2` and is the cap that matters.

### The body walk

| Guard | Effect |
|---|---|
| `NodeMetadata.isIgnoredNode(node)` | skip the subtree |
| the node is a function this transformer has already **visited** | skip the subtree — an inner function's body is not re-processed by its enclosing function's pass. **"Visited" means reached by the stage visitor**, so it does not cover the wrapper functions this transform *constructs*; item 4 is where that matters |
| no `parentNode` | skip |
| node type not in the replacer map | leave unchanged |
| `getMathRandom() > controlFlowFlatteningThreshold` | leave unchanged, per node |

Per-replacer gates, beyond the map:

- **`CallExpressionControlFlowReplacer`** — the callee must be an `Identifier`. A method call
  (`a.b()`) is left alone.
- **`StringLiteralControlFlowReplacer`** — refuses a literal that is its parent `Property`'s key;
  requires a string literal whose **`value.length >= 3`**. This floor is why one-character case
  tests elsewhere in the stage are never lifted.
- **`LogicalExpressionControlFlowReplacer`** — refuses unless *both* operands, after unwrapping a
  unary expression, are a `Literal`, `Identifier`, `ObjectExpression` or `ExpressionStatement`.
- **`BinaryExpressionControlFlowReplacer`** — no gate.

### Keys and reuse

A storage key is `getRandomString(5)`, regenerated on collision with an existing key. The storage's
own identifier is `getRandomString(6)`.

Reuse is per `(storage id, replacerId)`: with probability `usingExistingIdentifierChance` an
existing key for the same replacer id is reused instead of a new entry being made. **The bookkeeping
keeps only one key per replacer id** — `storageKeysById.set(replacerId, [storageKey])` replaces the
recorded array rather than appending to it — so the `pickone` that selects among "existing keys"
always has exactly one candidate, and a fresh key overwrites the record of the previous one.

For call wrappers, the replacer id is a second era axis. From optional-call support through `5.4.2`
it is only the argument count, so same-arity ordinary and optional calls can reuse the first body
created and thereby lose or gain optional short-circuiting. From `5.4.3` it is
`<arity>-optional` or `<arity>-standard`; the two call kinds no longer share a cache entry. From
`5.4.5`, each argument position also contributes `s` for spread or `p` for plain, so a spread and a
plain argument at the same position cannot reuse one another's wrapper. The three cache-key eras
are `E-cff-callee-reuse-arity`, `E-cff-callee-reuse-kind` and
`E-cff-callee-reuse-shape-kind`.

### The emitted storage

```js
const S = {
    k1: function (x, y) { return x + y },
    k2: function (callee, param1) { return callee(param1) },
    k3: 'a string'
};
```

Keys are emitted as **identifiers**; item 4 is where they stop being identifiers. The declaration
kind is `const`, subject to the prevailing-kind rewrite described in
[control-flow-block-flattening.md](control-flow-block-flattening.md) — the same mechanism, since
both are custom nodes.

### The call-expression wrapper's spread handling

Four eras: three spread behaviours, then the independent `4.2.0` optional-call repair:

| Era | Behaviour |
|---|---|
| [`E-cff-callee-positional`](../versions.md) | parameters are `param1 … paramN` and the inner call passes the same identifiers. A spread argument at the call site is bound to a single positional parameter, so `f(...a)` wraps to `callee(param1)` and receives only the first spread element |
| [`E-cff-callee-spread`](../versions.md) | a spread argument becomes a `RestElement` parameter and a `SpreadElement` in the inner call. A spread in a **non-final** position still emits parameters after the rest element, which is not valid JavaScript |
| [`E-cff-callee-spread-truncating`](../versions.md) | on the first spread argument the loop stops, so the rest parameter absorbs every remaining argument and the emitted parameter list is valid |
| [`E-cff-callee-optional-wrapper`](../versions.md) | the spread-truncating argument loop remains; when the source call gets its optional wrapper, that wrapper returns `callee?.(…)` inside a chain so a null callee yields `undefined` |

**The first two eras do not merely emit a different shape — they emit broken programs**, which is
rare enough on any of this package's axes to be worth stating here as well as in the registry. At
`E-cff-callee-positional` a source that sums `sink(...[1,2,3])` obfuscates into a program returning
`1` instead of `6`: every argument after the first is discarded. At `E-cff-callee-spread` a
non-final spread emits `function (callee, ...param1, param2)`, which is a parse error, so the
obfuscated file cannot be loaded at all. Both measured at both ends of their ranges.

At `4.2.0`, `(function(){var sum=null;return sum?.(1,2);})();` is the minimum semantic
discriminator. `4.1.1` stores an ordinary call and throws; `4.2.0` stores an optional call and
returns `undefined`. This boundary is independent of spread arguments.
The wrapper cache remains keyed only by arity until `5.4.3`, so mixed same-arity ordinary and
optional calls can still select the wrong wrapper; that is a later reuse-key axis, not this body's
syntax boundary.

## 4. Downstream Effects

| Later pass | What it does to this transform's output | Era |
|---|---|---|
| `Converting` (6), property-name literalization | rewrites every identifier storage key to a **string literal**, non-computed. Measured: every storage key in the frozen corpus is a `StringLiteral`, none an identifier | `E-propname-computed-literal` |
| `Converting` (6), object-keys extraction | **can destroy the object entirely** — see below | `E-objkeys-*` |
| `Converting` (6), `splitStrings` | a stored string entry becomes a `+` chain | all in range |
| `StringArray` (8) | the literalized keys and any stored string entry are concealed, so a call site arrives as `S[<array call>](a, b)` | all in range |
| `RenameIdentifiers` (7) | renames the storage identifier and the wrapper parameters (`x`, `y`, `callee`, `param1`) | all in range |
| `Simplifying` (9) / `Finalizing` (10) | declaration merging and escape sequences, as for any declaration | `E-adjacent-merge-*`, `E-escape-*` |

### Object-keys extraction is the era boundary that matters, and it is not on this transform's axis

`ObjectExpressionKeysTransformer` extracts an object literal into an empty object plus one
assignment per property. Applied to a control-flow storage, the object literal is replaced by:

```js
var S = {};
S['k1'] = function (x, y) { return x + y };
S['k2'] = 'a string';
```

Whether it fires on a storage depends on the `E-objkeys-*` era
([object-keys-extraction.md](object-keys-extraction.md)):

- **Before `E-objkeys-call-prohibited`** — every storage in a `transformObjectKeys` sample is
  extracted into assignment form.
- **From `E-objkeys-call-prohibited`** — an object containing a `CallExpression` or `NewExpression`
  is refused outright. A `callee` wrapper's body *is* a call expression, so a storage holding one
  survives as an object literal. A storage made only of operator wrappers and string entries
  contains no call and is **still extracted**.

The paired object-form / assignment-form census reads the transition directly: below the boundary
`transformObjectKeys` traffic carries the assignment form, while above it call-bearing storages
carry the object form and call-free storages remain extracted. The same option-gated population is
used on both sides, which distinguishes an era boundary from sampling noise.

**This is the clearest case in the package of a shape boundary with no structural footprint in the
transform that owns the shape**: not one file under `control-flow-transformers/` or
`control-flow-flattening-nodes/` changes at that release.

### It re-enters its own output, which gives a fourth wrapper body

A storage node prepended to a host is **inside that host** by the time the host's own enclosing
function is transformed. The wrapper functions it contains were *constructed*, not reached by the
stage visitor, so they are not in `visitedFunctionNodes` and the enclosing pass walks straight into
them — replacing a wrapper's `return x + y` with a call into the *outer* storage:

```js
var OUTER = { 'qjmcc': function (x, y) { return x - y }, … };
function f(a, b) {
    var INNER = { 'coxnd': function (x, y) { return OUTER['qjmcc'](x, y) }, … };
    …
}
```

So a fourth body shape exists alongside the three item 2 lists — a **delegating** wrapper, whose
body is a call on another storage rather than an operator or a parameter. It arises only when host
selection puts two storages in different function bodies; when the merge collapses them into one
host there is a single storage and no delegation. Both outcomes are reachable from the same input,
since the host is picked at random.

The U5 census finds delegating wrappers in every version column; it records the population beside
the operator-wrapper control rather than turning a corpus-dependent ratio into a durable claim.

Two consequences worth stating because neither is visible from the transform's own source: the
storage graph can be **more than one level deep**, and it is **acyclic with the outer storage as the
base** — an inner storage's entries reference an outer one, never the reverse, because the outer
pass runs strictly after the inner one.

### Its own sibling depends on it

`BlockStatementControlFlowTransformer` shares this stage's traversal and emits a controller string
literal of length ≥ 3. That literal is inside a function body whenever the flattened block is, so
this transform's `StringLiteralControlFlowReplacer` lifts it into the storage — which is why a
flattened block's controller is normally a storage read rather than a literal. The direction is
recorded on both sides; see [control-flow-block-flattening.md](control-flow-block-flattening.md).

### A second consumer of this machinery arrives at `3.2.0`, in a different stage

`StringArrayControlFlowTransformer` **extends `FunctionControlFlowTransformer`**, so it is this same
storage — the same wrapper table, the same call-site shapes — driven by a different replacer. Three
things about it invert the traffic described above, and none of them is visible below `3.2.0`:

- it declares the **`StringArray`** stage (8), not `ControlFlowFlattening` (4), with
  `runAfter: [StringArrayTransformer, StringArrayRotateFunctionTransformer,
  StringArrayScopeCallsWrapperTransformer]`;
- its only replacer, `StringArrayCallControlFlowReplacer`, wraps literals marked
  `isStringArrayCallLiteralNode` — **the index arguments of string-array calls**;
- so from `3.2.0` a string-array call is emitted *already wrapped*, as `wrapper(S['k'])`.

**Below `3.2.0` the traffic runs strictly the other way**, which is what makes this a boundary
rather than a detail: `ControlFlowFlattening` is stage 4 and `StringArray` is stage 8, so control
flow cannot wrap a string-array call — those calls do not exist yet — and the only cross-traffic is
the array concealing strings the storage already holds (the `StringArray (8)` row above).

The focused `calls-transform` corpus cells verify the emitted form at the lower bound. Each source
shape gains an object whose identifier keys hold numeric string-array indexes, and the call sites
read those entries through the new storage. Keeping this consumer on separate era rows matters:
the ordinary full columns and every shipped preset leave the option off, so they cannot verify it.

**Its storage lifetime changes at `3.2.3`.** The inherited implementation can stop traversal when
it meets an existing storage and reuse one storage across nested hosts. On the upstream
`multiple-storages-1.js` fixture, 3.2.2 therefore emits one four-entry object serving both the outer
IIFE and its nested function. At 3.2.3 the visitor changes `Break` to `Skip` and
`getControlFlowStorage` returns a fresh instance per host; the same input emits two two-entry
objects, one in each scope. These are `E-cff-storage-stringarray-shared` and
`E-cff-storage-stringarray-per-host`. The ordinary columns do not populate this nested-host
condition; the focused object-count and host-ownership census distinguishes it.

## 5. Known Quirks

- **Reuse is capped at one key per replacer id by a bookkeeping slip**, as above. The intent reads
  as "pick among the keys already made for this operator"; the effect is "reuse the most recent one,
  half the time".
- **`usingExistingIdentifierChance` is `1` for string literals**, so within one storage a given
  string value maps to exactly one key, deterministically. The other three replacers are `0.5`.
- **Removing a host's existing storage node changes mechanism at `2.19.0`, inside one era.** Up to
  `2.18.1` it is `hostNode.body.shift()` / `hostNode.consequent.shift()` — the host's *first*
  statement, on the assumption that it is the storage node. From `2.19.0` it is a lookup of the
  recorded node with a type guard, and the storage custom node comes to be constructed twice per
  host (a `controlFlowStorageCustomNode` is initialised and then never read, while a helper builds a
  second one). Neither half moves an emitted shape: nothing in the stage prepends to a host between
  two visits, so no input has been found where the two removals disagree, and both constructions are
  deterministic functions of the same storage. What would falsify the first is a host whose first
  statement is something other than the storage node at the moment a second function selects it.
- **`hostNodeSearchMinDepth` is dead.** It is `0`, and the only use is a `splice(0, 0)`.
- **A method call is never wrapped**, because the callee gate requires an `Identifier`. In
  member-heavy code this transform's call-expression half barely fires.
- **The wrapper functions are semantically thin but not transparent**: `function (x, y) { return x
  && y }` evaluates both operands before the call, where `a && b` does not. The logical replacer's
  operand gate — literals, identifiers, object expressions only — is what keeps that from changing
  behaviour, and it is the reason that gate exists rather than a shape preference.

## Source

- [`FunctionControlFlowTransformer.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/node-transformers/control-flow-transformers/FunctionControlFlowTransformer.ts)
- [`AbstractControlFlowReplacer.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/node-transformers/control-flow-transformers/control-flow-replacers/AbstractControlFlowReplacer.ts) — keys, reuse
- the four replacers, in the same directory:
  [`BinaryExpression…`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/node-transformers/control-flow-transformers/control-flow-replacers/BinaryExpressionControlFlowReplacer.ts),
  [`LogicalExpression…`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/node-transformers/control-flow-transformers/control-flow-replacers/LogicalExpressionControlFlowReplacer.ts),
  [`CallExpression…`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/node-transformers/control-flow-transformers/control-flow-replacers/CallExpressionControlFlowReplacer.ts),
  [`StringLiteral…`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/node-transformers/control-flow-transformers/control-flow-replacers/StringLiteralControlFlowReplacer.ts)
- [`ExpressionWithOperatorControlFlowReplacer.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/node-transformers/control-flow-transformers/control-flow-replacers/ExpressionWithOperatorControlFlowReplacer.ts) —
  the call-site builder the binary and logical replacers share, and
  [`ControlFlowReplacer.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/enums/node-transformers/control-flow-transformers/control-flow-replacers/ControlFlowReplacer.ts) —
  the replacer enum
- the stored values:
  [`BinaryExpressionFunctionNode.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/custom-nodes/control-flow-flattening-nodes/BinaryExpressionFunctionNode.ts),
  [`LogicalExpressionFunctionNode.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/custom-nodes/control-flow-flattening-nodes/LogicalExpressionFunctionNode.ts),
  [`CallExpressionFunctionNode.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/custom-nodes/control-flow-flattening-nodes/CallExpressionFunctionNode.ts),
  [`StringLiteralNode.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/custom-nodes/control-flow-flattening-nodes/StringLiteralNode.ts)
- the storage and its call sites:
  [`ControlFlowStorageNode.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/custom-nodes/control-flow-flattening-nodes/control-flow-storage-nodes/ControlFlowStorageNode.ts),
  [`ExpressionWithOperatorControlFlowStorageCallNode.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/custom-nodes/control-flow-flattening-nodes/control-flow-storage-nodes/ExpressionWithOperatorControlFlowStorageCallNode.ts),
  [`CallExpressionControlFlowStorageCallNode.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/custom-nodes/control-flow-flattening-nodes/control-flow-storage-nodes/CallExpressionControlFlowStorageCallNode.ts),
  [`StringLiteralControlFlowStorageCallNode.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/custom-nodes/control-flow-flattening-nodes/control-flow-storage-nodes/StringLiteralControlFlowStorageCallNode.ts)
- [`ControlFlowStorage.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/storages/custom-nodes/ControlFlowStorage.ts)
  over [`MapStorage.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/storages/MapStorage.ts) —
  the storage id and `mergeWith`, and
  [`NodeAppender.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/node/NodeAppender.ts) —
  `prepend` and `remove`
- [`NodeStatementUtils.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/node/NodeStatementUtils.ts) — host selection; its content does not change anywhere in phase 1's range

The pre-`2.19.0` removal-by-position is at
[`FunctionControlFlowTransformer.ts@2.18.1`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/18f5210871a6574f256938d4ad56e2ac19ac8884/src/node-transformers/control-flow-transformers/FunctionControlFlowTransformer.ts),
and the two earlier call-wrapper eras at
[`CallExpressionFunctionNode.ts@2.10.4`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/40dac436fd72af026c38758fb9202ed16cd12323/src/custom-nodes/control-flow-flattening-nodes/CallExpressionFunctionNode.ts)
and
[`@2.12.0`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/36ea9c08f3244533b466b3031824da6493aa2d4e/src/custom-nodes/control-flow-flattening-nodes/CallExpressionFunctionNode.ts).

## Fixtures

| Claim | What checks it | Era |
|---|---|---|
| the storage is an object of wrapper functions prepended to a function body | `u5-shape.mjs` over every full corpus column through `3.1.0` | `E-cff-storage-object` |
| a delegating wrapper body exists, and storages can nest recursively | `u5-census.mjs` over the corpus, plus a nested-host focused encode whose ownership census follows each outer-storage reference | same |
| the extraction's alias hand-off, `var REAL = S`, is what use sites read | `u5-census.mjs` — without following it the read axis reads zero on exactly the extracted columns | `E-objkeys-*` |
| storage keys arrive as string literals, never identifiers | same census | same |
| the object form is destroyed below the object-keys boundary and survives above it | paired object-form / assignment-form census over the same cells | `E-objkeys-*` |
| a call-free storage is still extracted above the boundary | the surviving assignment-form entries in the paired storage-shape census, read individually | same |
| the storage-side files hold still `0.25.0 – 3.1.0` | per-tag content-hash census across the complete release range | `E-cff-storage-object` |
| the call wrapper's three spread behaviours | purpose-built encodes at **both ends** of each range: `f(...a)` for the first boundary, `f(...a, b)` for the second | `E-cff-callee-*` |
| the positional era discards arguments | the same encode run compares a multi-element spread's source result with the first-element-only obfuscated result | `E-cff-callee-positional` |
| the middle-spread era emits an unparseable program | the same encode parsed with Babel | `E-cff-callee-spread` |
| same-arity ordinary and optional calls stop sharing a wrapper | focused adjacent-release cases covering both encounter orders plus different-arity and single-kind controls | `E-cff-callee-reuse-arity` / `E-cff-callee-reuse-kind` |
| same-length spread and plain calls stop sharing a wrapper | focused `5.4.4`/`5.4.5` cases covering both encounter orders plus single-shape controls | `E-cff-callee-reuse-kind` / `E-cff-callee-reuse-shape-kind` |
| the StringArray-stage consumer stores call indexes as numeric values | the focused `calls-transform` cells against their same-version `baseline` controls | both `E-cff-storage-stringarray-*` eras |
| shared storage becomes one fresh storage per nested host | upstream's `multiple-storages-1.js` fixture encoded at both bounds; the object-count and host-ownership census distinguishes shared from per-host storage | both `E-cff-storage-stringarray-*` eras |

**The spread eras are output-verified but not corpus-verified**, and cannot be: no corpus input uses
a spread argument. They were closed by building the two distinguishing inputs directly, which is
the right instrument here — the shapes are reachable in three lines and adding a spread fixture to
a frozen corpus would be a corpus change for one axis.
