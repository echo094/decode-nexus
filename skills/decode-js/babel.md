# Babel semantics a matcher has to know

Facts about Babel's `Scope`/`Binding`/`NodePath` model that several decode passes depend on and
none of them owns. Each is here because a pass got it wrong first, and because stating it per
pass produced several drifting copies of the same sentence.

This is the *mechanism* half. [encoder-decoder-method.md](../encoder-decoder-method.md)'s T2 is
the rule that follows from it — key on AST shape or on a resolved binding, never on name text —
and it is cross-project. Read T2 for what to do; read this for what Babel actually does and
which call to reach for. `decode-js.md`'s Babel + isolated-vm Foundation covers the packages
themselves: versions, import style, what each one is for.

## A function's own `.scope` includes its parameters

**A `FunctionDeclaration` path's `.scope` is the function's *inner* scope, not the scope the
declaration lives in.** Its parameters are bindings in that inner scope, so
`fnPath.scope.getBinding(fnName)` can resolve to a **shadowing parameter** rather than to the
declaration itself — whenever the encoder's renaming stage happens to give a function and one of
its own parameters the same generated name.

**Resolve from `fnPath.scope.parent` instead**, which starts the walk at the block that actually
contains the declaration.

The failure this produces is invisible, which is why it is worth stating rather than leaving to
be rediscovered. The function stays genuinely referenced from its now-unmatched call sites, so a
reference-gated cleanup correctly declines to delete it, and the call sites are never rewritten.
The result is a wholly undecoded layer that still runs correctly — no correctness signal moves,
no interpreter count moves, and only a structural check sees it. It cost
[calculator.js](visitors/jsconfuser/calculator.md) a confirmed total non-decode;
[global-concealing.js](visitors/jsconfuser/global-concealing.md) was hardened against the same
shape before it was ever observed there.

Passes whose matching is provably immune say so and why — see
[opaque-predicates.md](visitors/jsconfuser/opaque-predicates.md) item 2, where the lookup starts
from the reference site rather than from the function, so the collision cannot arise by
construction.

## `binding.path` shows one definition spelling out of three

A definition reaches a pass in any of three forms, and `binding.path` distinguishes them:

| spelling | what `binding.path` is | where the definition sits |
|---|---|---|
| `function f(…) {…}` | the `FunctionDeclaration` | on `binding.path` itself |
| `var f = function (…) {…}` | the `VariableDeclarator` | on `.init` |
| `var f;` … `f = function (…) {…}` | the init-less `VariableDeclarator` | in `binding.constantViolations` |

A matcher reading `binding.path` alone sees only the first. **A gate written as
`binding.path.isFunctionDeclaration()` therefore reads false on the other two** — and since both
the encoder's MovedDeclarations stage and this decoder's own control-flow decode emit the split
form routinely, that gate rejects most of a real population.

`utility/binding-def.js`'s `resolveBindingFunction` answers the question the gate was trying to
ask — *given this binding, what does it actually define?* — across all three.

**It fails closed on a binding written more than once**, and every caller depends on that:

- For a **matcher**, a re-assigned holder means the call sites are not all reading the function
  the match was built from, so substituting them would be wrong rather than merely incomplete.
- For a **cleanup**, the decline is required rather than conservative: a pass that deletes the
  holder would, on a twice-written binding, delete some other definition along with it. This is
  [dispatcher.md](visitors/jsconfuser/dispatcher.md)'s reason, and it is stronger than the
  matcher's.

**A cleanup's deletion gate is the half that gets missed.** Teaching a matcher to resolve through
a binding while leaving the pass's *deletion* gate keyed on `isFunctionDeclaration()` produces a
failure with no decline and no log line: the layer decodes, every signal reads clean, and a dead
helper is left behind that is indistinguishable from encoder-emitted dead code
([encoder-decoder-method.md](../encoder-decoder-method.md) S3). Audit both in the same change.

## A name is not an identity, even after resolving it

Two distinct traps, both of which cost a round here. T2 carries the rule; these are the API
calls.

- **Declaration sites are not references.** A `var x` declarator id, a `function x(…)` name, and
  a nested function's own parameter `x` are *bindings*, not uses. A reference scan that omits
  `isReferencedIdentifier()` counts all three as the target being used — which, in a fail-closed
  pass, kills every application in that scope.
- **A real reference can still belong to a shadowing binding of the same name.** Compare the
  binding object, never the text. This is not an edge case wherever a renaming stage hands out
  short names reused across non-overlapping scopes.

## `referencePaths` can list one node twice

A crawl records a reference per *path* it reaches, and by late in the pipeline this decoder's own
synthesizing passes can leave the same identifier node reachable at two positions. **A duplicate
here is a crash, not a declined match:** replacing the second occurrence finds the parent slot
already holding what the first replacement put there, the path resyncs to a null key, and
Babel's validator throws. Guard by node identity rather than relying on the fail-closed reflex.

Adding a `getProgramParent().crawl()` before reading the binding does *not* fix it — that was
tried against the stale-paths hypothesis, measured byte-identical across the corpus, and removed
again. Worked case:
[global-concealing.md](visitors/jsconfuser/global-concealing.md) item 4.

## Source positions are meaningless after an earlier pass rebuilds a subtree

Several passes here reparse function bodies or synthesise statements outright, so by the time a
later pass reads `node.start` / `node.end` they are routinely absent, or relative to a fragment
rather than to the program. A containment or ordering test built on them is wrong in a way that
looks like a matcher bug: one reported a function's own local as an outside dependency and
hoisted it out of scope, breaking the bundle it was building.

**Ask the path ancestry instead** — `searchPath.isAncestor(binding.path)` for containment, and
the trail of container keys down from the Program root for document order. Both are always
current, whatever rebuilt the tree. Worked case:
[string-concealing.md](visitors/jsconfuser/string-concealing.md) item 2.
