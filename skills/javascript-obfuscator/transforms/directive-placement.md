# Directive Placement

`"use strict"` and its siblings are recorded at the start of the pipeline and re-hoisted to the
top of their lexical scope at the end. The direct placement is stable; whether the original also
survives inside a control-flow switch case changes at `5.2.0`.

**Ungated**, and it runs in two stages rather than one: it *observes* during `Preparing` (2) and
*acts* during `Finalizing` (10).

## 1. Target

Not obfuscation — repair. A directive prologue is positional: `"use strict"` is a directive only
while it is the first statement of a scope, and an ordinary expression statement anywhere else.
Every transform between the two stages is free to move, wrap or merge statements, and several
would silently demote the directive to a no-op string expression, changing the program's
semantics. Upstream's own comment says it plainly: fixing placement afterwards as its own stage is
easier than teaching control-flow and dead-code injection to leave the directive alone.

So this transform exists to keep the *encoder* correct, not to make the output harder to read.

## 2. Algorithm

Two passes over the same node kind — anything that is a lexical scope with a statement body.

**Observe, during `Preparing`.** For each such node whose parent is a lexical scope, if the first
statement of its body is a directive, record it in a `WeakMap` keyed by that parent scope. Only
`body[0]` is inspected, so a later member of a multi-directive prologue is not recorded.

**Act, during `Finalizing`.** For each such node, look its scope up in the map. If a directive was
recorded, clone it and **prepend the clone** to the scope's statements. Through `5.1.0`, recursively
walk the scope and remove the original node by identity, stopping at the first hit. From `5.2.0`,
filter only the scope's direct body by identity.

The clone-then-remove-original order matters: the original may by now be nested arbitrarily deep
inside whatever the intervening stages built around it, so it cannot simply be moved — it is
re-emitted at the top and the stale copy deleted wherever it ended up.

**`runAfter: [CustomCodeHelpersTransformer]`** puts it in the last level of `Preparing`, after the
custom code helpers have been injected — so a helper's own directive, if it had one, is observed
too.

## 3. Implementation

| Item | At the spine's era | Era |
|---|---|---|
| Node match | `NodeGuards.isNodeWithLexicalScopeStatements(node, parentNode)`, both stages | all read eras |
| Parent guard | `NodeGuards.isNodeWithLexicalScope(parentNode)` — bail otherwise | all read eras |
| Directive test | `NodeGuards.isDirectiveNode` on `body[0]` | all read eras |
| Storage | a private `WeakMap<TNodeWithLexicalScope, Directive>` on the transformer instance | `2.10.0` onward |
| Storage | `NodeMetadata.set(parentNode, { directiveNode })` — on the AST node's own metadata | `2.9.6` and below |
| Prepend | `NodeAppender.prepend(scopeStatements, [clone])` | all read eras |
| Remove original | `estraverse.replace` with a `Break` once removed | through `5.1.0` — `E-directive-rehoist-no-residual` |
| Remove original | `body.filter((n) => n !== directiveNode)` | `5.2.0` onward — `E-directive-rehoist-nested-residual` |
| Dependency | `runAfter: [CustomCodeHelpersTransformer]` | all read eras |

The `2.10.0` move from AST metadata to a `WeakMap` is output-invisible. The `5.2.0` unlink change is
not: control-flow flattening stores the same statement identity inside a switch case. The recursive
walk reaches and removes it; the direct-body filter does not. The prepended directive therefore
looks unchanged while an ordinary string expression with the same value survives in the nested
case. This is `E-directive-rehoist-nested-residual` in [versions.md](../versions.md).

**The removal walk is scoped to the current node, not the program**, so a directive recorded for
scope A is only ever removed from within A.

## 4. Downstream Effects

Nothing meaningful runs after it. It shares `Finalizing`'s first level with
[escape-sequences.md](escape-sequences.md), and the two do **not** collide even though they look
like they must: the re-emitted directive comes out unescaped.

**This matters because escaping it would break it.** A directive prologue is recognised by the
spelling of its literal — `'use strict'` is a directive, `'use\x20strict'` is an ordinary string
expression statement and the scope silently stops being strict. What prevents it is that this
transform *prepends a clone* during `Finalizing`, and the traversal that is already walking that
scope does not descend into the newly inserted node; the escape transformer never sees it. The
original — which the escape transformer may well have escaped — is deleted in the same pass.

Verified at 2.19.0 with `unicodeEscapeSequence: true`, `simplify: false`, string array off, one
file carrying all three cases:

```js
"use strict";                                        // -> 'use strict';
function f() { "use strict"; return 1; }             // -> 'use strict';
function g() { var a = 1; "not a directive"; return a; }
//                        ^ not first in scope, so never recorded as a directive
//                        -> '\x6e\x6f\x74\x20\x61\x20\x64\x69\x72\x65\x63\x74\x69\x76\x65';
```

The third line is the discriminator: same node type, same stage, same run — escaped, because it
was never recorded and so was never re-emitted as a clone.

`EvalCallExpressionTransformer` runs in the level after, and re-serializes `eval` host bodies to
text — a directive inside one is emitted as source text rather than as a tree node.

## 5. Known Quirks

- **The prologue survives escaping only because of an insertion-order accident.** Item 4 has the
  measurement and the mechanism. It is recorded as a quirk rather than a design because nothing in
  either transformer expresses the dependency: neither consults the other, neither declares a
  `runAfter` against the other, and the property rests entirely on a node inserted mid-traversal
  not being revisited. A change to how the clone is appended would silently de-strict every
  obfuscated program that uses a directive.
- **Only the first directive in a prologue is tracked.** `analyzeNode` reads `body[0]`; it does not
  iterate the prologue. A later directive is a different, untracked node. This is source-read and
  not separately tested.
- **A later ordinary string with the same value is not the retained original.** Identity, nesting
  and source position distinguish it; string value alone does not identify the retained directive.
- **A directive in a scope whose parent is not a lexical scope is dropped from the map entirely** —
  both passes bail on that guard. Whether such a position exists in practice is not established.

## Source

- Transformer:
  [`DirectivePlacementTransformer.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/node-transformers/finalizing-transformers/DirectivePlacementTransformer.ts)
- Shallow-removal successor:
  [`DirectivePlacementTransformer.ts` at `5.2.0`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/3848bca7941ed86d62e6a7108b960201613d2172/src/node-transformers/finalizing-transformers/DirectivePlacementTransformer.ts)
- Its two stage registrations, and the level each lands in: [order.md](../order.md).

Read at `2.19.0`, the spine; the storage and removal rows are read at the tags named against them.

## Fixtures

**None of this package's own**, but the doc is no longer resting on source reads alone: the corpus
gained a fourth input, `directives.js`, carrying a `"use strict"` prologue at two scopes and a
string expression statement that is deliberately *not* a directive
([corpus.md](../corpus.md)). Every column now carries it, so the claims below have emitted output
behind them across the whole version range rather than at one built sample.

| Claim | What checks it | Gap |
|---|---|---|
| observe-then-re-emit across two stages | source read at 2.19.0 | the re-emission is observed; the two-stage split is not separately isolated |
| the emitted directive is **not** escaped, at either scope level | every `directives__*` corpus cell, at all eleven columns | — |
| a non-recorded string statement is treated as ordinary content | the same cells: `'not-a-directive'` is pulled into the string array while the two directives stay in place, unescaped and unconcealed | it carries no character in the force-escape class, so *escaping* it specifically is still unobserved — concealment is what separates the two here |
| only the first directive in a prologue is tracked | source read | no dedicated multi-directive output cell |
| nested original removal changes at `5.2.0` | `directives__cff`: the low side leaves an empty case; the high side retains the original string expression in that case while keeping the scope clone | persistence above `5.2.0` is source-proven until those columns are built |

**The discriminating case is one line's position, and it is fragile.** `'not-a-directive'` sits
*after* a `var` statement in the fixture on purpose: a directive prologue is the maximal run of
string expression statements at the **start** of a body, so moving it up by one would make it a
second directive and silently destroy the contrast this table rests on. Upstream's own
cases:
`test/functional-tests/node-transformers/finalizing-transformers/directive-placement-transformer/`.
