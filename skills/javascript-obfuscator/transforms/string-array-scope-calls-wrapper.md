# String Array Scope Calls Wrapper

The per-scope accessors `stringArrayWrappersCount` injects into individual lexical scopes. Each one
forwards to the **root** calls wrapper — or, under `stringArrayWrappersChainedCalls`, to another
scope wrapper in an enclosing scope — so a use site names a local identifier rather than the one
global accessor.

**Gated on `stringArrayWrappersCount`.** Its default is `1`, so a sample built with no options set
already carries one per scope that uses a string. `stringArrayWrappersType` selects between two
emitted forms, and its default is `variable` ([options.md](../options.md)).

This is **not** the root wrapper, which is a separate component with its own history:
[string-array-calls-wrapper.md](string-array-calls-wrapper.md). Its other siblings are
[string-array.md](string-array.md) and [string-array-rotate.md](string-array-rotate.md).

## 1. Target

Break the one-name property the root wrapper leaves behind. With the root wrapper alone every
string read in the program calls the same identifier and passes a number on one arithmetic scale;
collecting all string reads is then a single grep for that name. A per-scope wrapper gives each
scope its own callee name and — in the function form — its own index offset, so two use sites
fetching the *same* array element from different scopes agree on neither the name nor the number.

Chained calls extend this from a name substitution into a chain: a read inside a nested function
hops through one wrapper per enclosing scope before it reaches the root, and each hop is a
different name in a different scope.

## 2. Algorithm

**A wrapper is allocated lazily, by the literal replacement rather than by this transformer.**
While `StringArrayTransformer` rewrites a literal, it asks which wrapper the *current* lexical
scope should route through; if that scope has fewer than `stringArrayWrappersCount` wrappers for
this item's encoding, it creates one and records it, then picks one of the scope's wrappers **at
random** for this use site. Three consequences:

- **A scope with no array-bound string literal gets no wrapper at all**, however deeply it nests.
- **Wrappers are per `(scope, encoding)`**, so a scope reading both a `none` and a `base64` item
  carries `count` wrappers of each, one set per root wrapper.
- **A scope's wrappers are interchangeable at a use site.** Which one a given site calls carries no
  information; it is one random draw per site.

This transformer then walks the tree a second time and emits, into each recorded scope, one node
per wrapper. It runs on **leave**, so a scope's wrappers are emitted after its children have been
visited.

**Two emitted forms, chosen by `stringArrayWrappersType`.**

| Form | Emitted | Where it lands |
|---|---|---|
| `variable` | one declarator aliasing the upper wrapper — `var X = W;` | prepended to the scope body |
| `function` | a forwarding function that subtracts an offset — `function X(a, b) { return W(a - N, b); }` | *see the era table below* |

**The variable form is an alias and nothing else.** It carries no arithmetic, so the per-wrapper
index is `0` and the use-site number is exactly what the root wrapper would have been passed. It
is a rename of the callee, at zero cost to the index scale.

**The function form is where the offset lives.** An offset is drawn at random — per lexical scope
or per wrapper depending on the era, which is item 3's business — the use site adds it into the
number it emits, and the wrapper subtracts it back off before forwarding. The chain telescopes:
whatever the depth, the value reaching the root wrapper is the same number the root would have
received directly. The
use-site half of that arithmetic is stated once, in
[string-array.md](string-array.md) — this page covers only what the wrapper itself subtracts.

**What changes by era is which shape holds the function form**, and it is the same kind of
discriminator the root wrapper's own axis uses:

| Era | Function form |
|---|---|
| `E-sa-scope-wrapper-var-fn-expression` | a declarator initialised with a function **expression**, `var X = function (a, b) { return W(a - N, b); }` |
| `E-sa-scope-wrapper-fn-declaration` | the same body re-held as a hoisted function **declaration**, `function X(a, b) { return W(a - N, b); }`; chained wrappers choose their upper independently |
| `E-sa-scope-wrapper-shared-upper` | the declaration stays, but chained wrappers in one `(scope, encoding)` bucket share one chosen upper wrapper |

The stable-2.x historical samples add the previously unread lower side of the expression form.
Source history places this wrapper implementation at `2.3.0`; the `2.8.1` output uses a
string-valued hexadecimal numeric index in the forwarding subtraction. The `2.9.0` and `2.9.5`
outputs use numeric-valued hexadecimal indexes after the index-node change. Those outputs also
show both carrying-parameter positions, because the 2.9 parameter slots are selected per wrapper;
that random position is not an era discriminator.

**The variable form does not move across that boundary** — an alias declarator on both sides. The
era is named for the function form because that is what the signature reads
([versions.md](../versions.md)).

**Chained calls change what `W` is, and the sharing rule changes by era.** With `stringArrayWrappersChainedCalls` off,
every wrapper forwards to the root wrapper for its encoding. With it on, a wrapper forwards to a
randomly chosen wrapper of its **parent** lexical scope for the same encoding, falling back to the
root when the parent has none. Through `E-sa-scope-wrapper-fn-declaration`, that choice is made per
wrapper; at `E-sa-scope-wrapper-shared-upper`, it is made once and reused by every wrapper in the
bucket. The holder and forwarding-call syntax do not change.

**The fallback is decided by allocation *timing*, not by depth, and it is why the option can be on
and do nothing at all.** A scope's wrapper is allocated lazily, by the literal replacement, while
this transformer emits on **leave** — so a scope is transformed before any parent whose own
literals sit lower in the source has been given a wrapper, and it takes the root. A chain therefore
needs the parent scope to have already read an array-bound string: an outer literal lexically
*above* the nested function, or a second level of nesting. Where neither holds, output with the
option on is byte-identical to output with it off — not merely equivalent, since the absent branch
also skips its random draw. Measured across a whole matrix of versions and inputs in
[corpus.md](../corpus.md), which is why the shape is exercised there only under the presets.

### Two shapes that make every argument look alike

Both are emitted deliberately and both are era-invariant across the read range.

**Fake parameters.** A wrapper's parameter count is not the number of values it uses. When the
upper wrapper is the root, the count is `2`; when the upper is another scope wrapper — which is
what chained calls produce — it is `stringArrayWrappersParametersMaxCount`, and only two of those
parameters carry anything. The index-carrying and key-carrying slots are placed at two randomly
chosen positions; every other parameter is a name that is used once and means nothing.

**Fake arguments.** The call to the upper wrapper is filled the same way. Every argument is spelled
`param - <literal>` — the real index argument and the padding are the *same shape* — and only the
argument at the upper wrapper's own index position is the real one:

```js
function _0x1941c0(_0x49f34f, _0x39be9f, _0x55ad22, _0xea85e1) {
  return _0x2f9c28(_0x49f34f - 0x1e6, _0x39be9f - 0x11c, _0x39be9f, _0x55ad22 - 0x2de);
}
```

Which of the four is real is decided by `_0x2f9c28`'s own parameter layout, which is readable only
from `_0x2f9c28`'s body — and if that is itself a scope wrapper, the question recurses one scope
outwards.

At a **use site** the same padding is literals rather than expressions: all arguments are numbers
drawn from a window the width of the array's own length, centred on the real index, so the real one
is not the outlier.

## 3. Implementation

| Item | At the spine's era | Era |
|---|---|---|
| Stage | `StringArray` (8) | see [order.md](../order.md) |
| Declared `runAfter` | `StringArrayRotateFunctionTransformer` | all read eras |
| Gate | falsy `stringArrayWrappersCount` returns **no visitor at all** | all read eras |
| Scope set | `Program`, or a `BlockStatement` whose parent is an `ArrowFunctionExpression`, `FunctionDeclaration`, `FunctionExpression` or `MethodDefinition` | all read eras |
| Visitor | `enter` pushes the scope on a stack; `leave` pops it, **then** transforms — so the stack top during a transform is the *parent* scope | all read eras |
| Stack ownership | this transformer is the **only** writer of that stack; `StringArrayTransformer` reads it and never pushes. The two share one `StringArray`-stage traversal, which is what makes the read well-defined — and with the gate closed nothing pushes, but nothing reads either, since a falsy count routes every use site to the root wrapper | all read eras |
| Allocation | in `StringArrayTransformer`, per `(scope, encoding)`, capped at `stringArrayWrappersCount` | all read eras |
| Emission order | a scope's wrappers are iterated in reverse, so that repeated insertion at index `0` leaves them in allocation order. It is written for the prepending path and is inert for the randomly-placed one | all read eras |
| Wrapper name | `generateForGlobalScope()` at `Program`, `generateNext()` in any other scope | all read eras |
| Parameter names | `generateForLexicalScope(<the emitted function>)`, assigned after the node is built | all read eras |
| Offset draw | `getRandomInteger(-1000, 1000)` for the function form, `0` for the variable form. A negative offset prints as `param - -0x1b` | all read eras |
| Upper wrapper | the root wrapper for this encoding | `stringArrayWrappersChainedCalls` off |
| Upper wrapper | a random pick per emitted wrapper from the parent scope's wrappers for this encoding, else the root | `stringArrayWrappersChainedCalls` on, through `E-sa-scope-wrapper-fn-declaration` |
| Upper wrapper | one random pick per `(scope, encoding)` bucket, shared by every emitted wrapper, else the root | `stringArrayWrappersChainedCalls` on, `E-sa-scope-wrapper-shared-upper` |
| Parameter count | `2` when the upper is the root wrapper; `stringArrayWrappersParametersMaxCount` when it is a scope wrapper | all read eras |
| Fake argument | `parameters[i] - getRandomInteger(0, 500)` | all read eras |
| Offset carried on | the **lexical scope**, accumulated down the scope chain — every wrapper in one scope shares it, and shares one parameter layout | `E-sa-scope-wrapper-var-fn-expression` |
| Offset carried on | the **wrapper**, drawn independently per wrapper along with its own parameter layout; the emitted literal is `scopeOffset - upperOffset` | `E-sa-scope-wrapper-fn-declaration`, `E-sa-scope-wrapper-shared-upper` |
| Emitted position | prepended, both forms | `E-sa-scope-wrapper-var-fn-expression` |
| Emitted position | prepended for the variable form; inserted at `getRandomInteger(0, body.length - 1)` for the function form | `E-sa-scope-wrapper-fn-declaration`, `E-sa-scope-wrapper-shared-upper` |
| Function-form index spelling | string-valued hexadecimal numeric literal in the forwarding subtraction | `E-sa-scope-wrapper-var-fn-expression` (pre-2.9 source/output slice) |
| Function-form index spelling | numeric-valued hexadecimal literal in the forwarding subtraction | `E-sa-scope-wrapper-var-fn-expression` (2.9 sampled output and later source/output sites) |
| Carrying-parameter position | fixed first parameter in the pre-2.9 function node | `E-sa-scope-wrapper-var-fn-expression` (pre-2.9 source/output slice) |
| Carrying-parameter position | independently selected per wrapper; either position can occur in one sample | `E-sa-scope-wrapper-var-fn-expression` (2.9 sampled output and later source/output sites) |
| Emission route | `NodeFactory` directly — no template, and so no recursive template obfuscation | all read eras |

**The emitted declaration kind is not the node's.** Both the variable form and the earlier
function form are built as `const` and print as the scope's *prevailing* kind of variables, which
`var` fixtures make `var` and `const` fixtures make `const`. Same trap as the array and the root
wrapper, one component over: a matcher keying on `const` matches nothing in a `var` program.

**The two forms as emitted**, from the corpus's `wrappers-variable` and `wrappers-function` sets:

```js
// variable form — the whole wrapper
var _0xae9392 = _0x393d, _0x2438a9 = _0x393d;

// function form, E-sa-scope-wrapper-fn-declaration
function _0x2c2ad6(_0x3f7427, _0x1e6f33) { return _0x393d(_0x1e6f33 - -0x1b, _0x3f7427); }
function _0x36727b(_0x4a29a1, _0xbf90d1) { return _0x393d(_0x4a29a1 - -0x35b, _0xbf90d1); }
```

Two things are visible in that pair and neither is a version difference. The **index-carrying
parameter sits at a different position in each** — first wrapper's second parameter, second
wrapper's first — and the **offsets differ**, `-0x1b` against `-0x35b`, though both wrappers live
in one scope and call one upper. Under `E-sa-scope-wrapper-var-fn-expression` the same two reads
come out equal on the pre-2.9 source path, because both are properties of the scope there rather
than of the wrapper. On the 2.9 source path, the carrying slot and offset are per-wrapper. The
parameter-position difference is therefore readable **inside a single sample**, but comparing two
samples is how a per-wrapper random draw gets mistaken for a version boundary.

**Wrappers are injected into the rotator's own IIFE**, which is a lexical scope like any other and
does contain array reads. So the wrappers of that scope are part of the string-array machinery
rather than of the program, and the rotator's comparison operands are calls to them rather than to
the root wrapper.

## 4. Downstream Effects

| Later | Effect on this transform's output |
|---|---|
| `Simplifying` (9) — declaration merging | the variable form's declarator is fused with whatever `var` follows it, including the program's own variables and the rotator IIFE's. It is **not** a statement of its own in the output: `var _0x36727b=_0x393d,_0x4cf97b=_0x393d,_0x59b035=_0x912b57();` is two wrappers and one unrelated local ([statement-and-declaration-merging.md](statement-and-declaration-merging.md)) |
| `Simplifying` (9) — statement fusion | nothing to fuse in the function form: its body is a single `return` |
| `Finalizing` (10) — `EscapeSequenceTransformer` | no effect, and it is worth stating rather than omitting — a wrapper's operands are identifiers and numbers, with no string literal anywhere in either form |

**No later stage rewrites the offsets**, which is the asymmetry against the root wrapper worth
carrying: `numbersToExpressions` runs at `Converting` (6), *before* this stage, and the root wrapper
is nonetheless reached by it through the recursive template obfuscation its emission route uses
([string-array-calls-wrapper.md](string-array-calls-wrapper.md)). This component has no template
and no recursive run, so nothing reaches its numbers. In one `preset-medium` sample the root
wrapper's shift prints as `-(-0x2157+0xa1d*0x2+0xe43)` while the scope wrappers in the same file
print `- -0x8f`.

## 5. Known Quirks

- **Some scopes are structurally excluded, and they are ordinary-looking scopes.** The guard accepts
  only a `Program` or a `BlockStatement` under a function-ish parent, so an `if` block gets no
  wrapper however many strings it reads, and an expression-bodied arrow (`() => f(0x1)`) gets none
  because it has no block to hold one. Upstream's own cases call these "prohibited scopes". The
  reads in them route to an enclosing scope's wrapper instead, so the wrapper a call names is not
  reliably declared in the call's own immediate block.
- **The wrapper count is a ceiling per scope, not a count of wrappers in the file**, and it is per
  encoding besides. A sample built with `stringArrayWrappersCount: 5` and two encodings in use can
  carry ten wrappers in one scope and none in the next.
- **A wrapper's parameters outnumber its uses by design under chained calls**, and the surplus
  parameter names are generated by the same generator as everything else — so nothing about a name
  distinguishes a carrying slot from padding.
- **The variable form's alias is a plain identifier copy**, indistinguishable in shape from any
  other single-identifier alias a program might contain. Only its target identifies it.

## Source

- Transformer — the gate, the scope set, the visited-scope stack, chained-call resolution, and both
  insertion positions:
  [`StringArrayScopeCallsWrapperTransformer.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/8acfac18d7bccd8524008ab4175838f1e4a51ed8/src/node-transformers/string-array-transformers/StringArrayScopeCallsWrapperTransformer.ts)
- Shared-upper routing at `E-sa-scope-wrapper-shared-upper`:
  [`StringArrayScopeCallsWrapperTransformer.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/45ad03b8335bee095b17c0d29b0a78bff158c93a/src/node-transformers/string-array-transformers/StringArrayScopeCallsWrapperTransformer.ts)
- Function form, `E-sa-scope-wrapper-fn-declaration` — the fake parameters and fake arguments, and
  the `scopeOffset - upperOffset` literal:
  [`StringArrayScopeCallsWrapperFunctionNode.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/8acfac18d7bccd8524008ab4175838f1e4a51ed8/src/custom-nodes/string-array-nodes/StringArrayScopeCallsWrapperFunctionNode.ts)
- Function form, `E-sa-scope-wrapper-var-fn-expression` — the same body in a declarator, and the
  precomputed per-scope offset:
  [at 2.15.4](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/08aad1b7069e9f8b510765dcbf01c88aa741378d/src/custom-nodes/string-array-nodes/StringArrayScopeCallsWrapperFunctionNode.ts)
- Historical pre-2.9 function form and string-valued index:
  [at 2.8.1](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/44ac6c3ec8de32259c10d5c8a395cff110281dca/src/custom-nodes/string-array-nodes/StringArrayScopeCallsWrapperFunctionNode.ts)
- The numeric index-node and randomized parameter positions:
  [at 2.9.0](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/a4328da67f10fe505e15217d1310650d4432e7be/src/custom-nodes/string-array-nodes/StringArrayScopeCallsWrapperFunctionNode.ts)
- Variable form, all eras:
  [`StringArrayScopeCallsWrapperVariableNode.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/8acfac18d7bccd8524008ab4175838f1e4a51ed8/src/custom-nodes/string-array-nodes/StringArrayScopeCallsWrapperVariableNode.ts)
- The per-scope store the transformer reads, keyed by lexical scope node:
  [`StringArrayScopeCallsWrappersDataStorage.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/8acfac18d7bccd8524008ab4175838f1e4a51ed8/src/storages/string-array-transformers/StringArrayScopeCallsWrappersDataStorage.ts)
- Allocation, the offset draw and the parameter-position draw — in the literal replacement rather
  than in this transformer:
  [`StringArrayTransformer.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/8acfac18d7bccd8524008ab4175838f1e4a51ed8/src/node-transformers/string-array-transformers/StringArrayTransformer.ts)
- The use site's own fake arguments:
  [`StringArrayCallNode.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/8acfac18d7bccd8524008ab4175838f1e4a51ed8/src/custom-nodes/string-array-nodes/StringArrayCallNode.ts)
- The scope guard and its accepted parent types:
  [`NodeGuards.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/8acfac18d7bccd8524008ab4175838f1e4a51ed8/src/node/NodeGuards.ts)

Read the stable-2.x source bounds at `2.3.0` and `2.9.0`, and output at `2.8.1`, `2.9.0` and
`2.9.5`, for the historical backfill; the existing corpus reads the later expression form through
`2.15.4`. Read at `2.16.0` for the declaration boundary and at every release tag through `5.5.0`
for the extension. The function node's later changes are formatting and dependency-injection
decoration; the routing boundary is the `5.2.0` transformer change that moves upper-wrapper
selection outside the per-wrapper loop.

## Fixtures

**None committed.** What checks the claims today:

| Claim | What checks it | Era | Gap |
|---|---|---|---|
| the variable form is one declarator aliasing the upper wrapper | corpus `wrappers-variable` at every matrix version | all read eras | above the spine is source-only |
| the function form is a declarator holding a function expression | focused output samples at `2.8.1`, `2.9.0` and `2.9.5`, plus corpus `wrappers-function` through 2.15.4 | `E-sa-scope-wrapper-var-fn-expression` | only the named sites are sampled; no interpolation is claimed |
| the pre-2.9 function wrapper uses a string-valued numeric index | historical report at `2.8.1` | `E-sa-scope-wrapper-var-fn-expression` | stable-2.x source bounds are read, but only this lower-side output site is sampled |
| the 2.9 function wrapper uses a numeric-valued index and can place the carrying parameter in either slot | historical report at `2.9.0` and `2.9.5` | `E-sa-scope-wrapper-var-fn-expression` | parameter position is random per wrapper, not a separate era claim |
| the function form is a hoisted function declaration | corpus `wrappers-function` at 2.16.0, 2.18.1, 2.19.0 | `E-sa-scope-wrapper-fn-declaration` | — |
| two wrappers in one scope share an offset and a parameter position | corpus `wrappers-function`, every matrix version through 2.15.4 — the wrappers pair up on both readings in each | `E-sa-scope-wrapper-var-fn-expression` | — |
| they are drawn independently per wrapper | corpus `wrappers-function` at 2.16.0, 2.18.1, 2.19.0 — no two wrappers in a sample share an offset | `E-sa-scope-wrapper-fn-declaration` | — |
| chained wrappers share one upper wrapper per bucket | per-tag source diff at `5.2.0` | `E-sa-scope-wrapper-shared-upper` | **not output-verified**; it requires a parent bucket with multiple choices |
| the upper wrapper is one of the parent scope's | corpus `preset-medium`, `preset-high`, every matrix version | all read eras | **`chained-calls` does not check this.** That set is byte-identical to `wrappers-function` on every cell — the option is applied but never taken, because all three inputs nest one level deep with their program-level string reads below the function declarations, so a scope resolves its upper before its parent has allocated one ([corpus.md](../corpus.md)). The only cells carrying the shape also enable `controlFlowFlattening`, so nothing isolates it; above the spine is source-only |
| fake parameters and fake arguments appear once the upper is a scope wrapper | corpus `preset-medium`, `preset-high` at 2.19.0 | all read eras | only via presets; no set varies `stringArrayWrappersParametersMaxCount` on its own; above the spine is source-only |
| the offsets survive `numbersToExpressions` unrewritten | corpus `preset-medium` at 2.19.0 | all read eras | one sample, one version; above the spine is source-only |
| prohibited scopes get no wrapper | not observed | all read eras | **no fixture** — no corpus input puts a string inside an `if` block or a statement-less arrow |
| the emitted kind follows the scope's prevailing kind | not observed | all read eras | **no fixture** — all three corpus inputs are `var` programs, so the `const`/`let` outcome is source-read only |

Upstream's own cases:
`test/functional-tests/node-transformers/string-array-transformers/string-array-scope-calls-wrapper-transformer/`.
