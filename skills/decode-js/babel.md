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

**Two different causes produce this one symptom, and they respond to opposite remedies.** Tell them
apart before reaching for either: ask whether the duplicated node is reachable from the live
Program at **two positions** or at **one**.

### Cause A — the node really is at two positions

A crawl records a reference per *path* it reaches, and by late in the pipeline this decoder's own
synthesizing passes can leave the same identifier node reachable at two positions. **A duplicate
here is a crash, not a declined match:** replacing the second occurrence finds the parent slot
already holding what the first replacement put there, the path resyncs to a null key, and
Babel's validator throws. Guard by node identity rather than relying on the fail-closed reflex.

Adding a `getProgramParent().crawl()` before reading the binding does *not* fix it — that was
tried against the stale-paths hypothesis, measured byte-identical across the corpus, and removed
again. **It cannot help, and that is the diagnostic:** a fresh crawl re-finds the node at both
positions and re-records both, because the tree really does hold it twice. Worked case:
[global-concealing.md](visitors/jsconfuser/global-concealing.md) item 4.

### Cause B — the insertion/replacement family re-registers a subtree it was handed

**Measured at `@babel/traverse` 8.0.0**, and version-anchored deliberately: unlike the rest of this
file, this is a claim about behaviour upstream owns, and an unanchored measurement of someone else's
code cannot be re-checked. But the anchor is belt-and-braces, not a hedge that a future release
fixes this — Babel's own maintainer has already said it won't. Asked on the near-identical report
[babel/babel#16531](https://github.com/babel/babel/issues/16531#issuecomment-2132129010),
`liuxingbaoyu` answered "You can use `path.scope.crawl()` to refresh binding information. But
specifically for this use case, I think the current solution is good, which is to rerun a complete
process" — declining to change the registration behaviour itself. The same maintainer, in
[babel/babel#16314](https://github.com/babel/babel/discussions/16314#discussioncomment-8616208),
called it "a long-standing problem with Babel, where current binding information is not always
reliable," and put the remedy on the caller: `path.scope.crawl()` to refresh fully, or
`scope.registerDeclaration()` for a cheaper targeted update. **So this is not a reported bug
awaiting a fix — it is Babel's stated position that binding-cache correctness after a mutating API
is the plugin's job, not the core's.** The workarounds below are the permanent correct usage, not a
stopgap.

**`replaceWith`, `insertBefore`, `insertAfter`, `unshiftContainer` and `pushContainer` are one
family** — they re-home a node through the same machinery, and every one of them leaves the
binding bookkeeping wrong. Minimal case, `var x = 1; f(x);` with the statement wrapped in a block,
one live reference throughout, so **every row below should read `refs=1`**:

| Operation | `references` | distinct nodes | Wrong how |
|---|---|---|---|
| baseline, no mutation | 1 | 1 | — |
| `replaceWith(reuse)` | 2 | 1 | **duplicate** |
| `insertBefore(reuse)` + `remove` | 2 | 1 | **duplicate** |
| `insertAfter(reuse)` + `remove` | 2 | 1 | **duplicate** |
| `unshiftContainer(reuse)` + `remove` | 2 | 1 | **duplicate** |
| `pushContainer(reuse)` + `remove` | 2 | 1 | **duplicate** |
| `replaceWith(cloneNode)` | 2 | 2 | **stale** — the replaced node stays registered |
| `insertBefore(cloneNode)` + `remove` | 2 | 2 | **stale** |

Four consequences worth keeping:

- **Cloning is not a remedy — it swaps which error you get.** Reuse leaves a duplicate; cloning
  leaves a stale entry for the node you removed. On a real rewrite, cloning one subtree moved the
  duplicate count from 139 to 109, which reads like progress and is a different bug.
- **A crawl clears this one**, unlike cause A, because a fresh crawl finds each live node once —
  but it must be `getProgramParent().crawl()`. **A crawl scoped to an inner scope makes it worse:**
  it appends to outer-scope bindings that already hold those references. Measured on one visitor
  that already carried a crawl — `path.scope.crawl()` produced **37 duplicates**, no crawl **lost**
  references (1096 entries against a 1448 baseline), and `getProgramParent().crawl()` gave exactly
  the baseline with none.
- **So "did a crawl help?" separates the two causes** — and "which crawl" separates the two ways
  of getting cause B wrong.
- **Prefer in-place mutation where the rewrite allows it.** Re-bracing a branch, splitting a
  sequence, splitting a declaration — none of these need a new node, and the in-place form is
  duplicate-free, cheaper, and cannot re-enter. (`replaceWith` requeues the replacement, so a
  rewrite without a guard against its own output recurses until it OOMs — met twice while
  reducing this case.) A rewrite that genuinely needs a new node because it *duplicates* a subtree
  must clone what it duplicates and repair the bookkeeping after;
  `atomic/convert-conditional-assign.js` is the worked example, and it measures clean.

**The failure mode is not only the crash cause A gives.** A duplicate inflates
`binding.referencePaths.length` **and** `binding.references`, so a consumer whose completeness gate
compares "references I resolved" against "references that exist" can satisfy that gate while a live
reference goes unhandled — then delete the declaration it was gating. That failure is silent: the
pass logs nothing, the output text is well-formed, and the program throws a `ReferenceError` at
runtime. Worked case:
[parse-control-flow-storage.md](visitors/parse-control-flow-storage.md).

**What detects each.** `detachedReferences()` in the shared test helper sees **neither** — nothing
is detached in either cause. `referenceState()` sees cause B, because `binding.references` is
inflated against a fresh parse of the same output; it is the check every fix-case visitor test
already runs, so a visitor with no test, or with fixtures too small to duplicate, is where this
survives ([tests.md](tests.md)).

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
