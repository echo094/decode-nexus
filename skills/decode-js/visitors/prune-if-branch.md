# prune-if-branch.js

Folds an `IfStatement` or `ConditionalExpression` whose test is statically constant.
The test qualifies when it is a `StringLiteral`/`NumericLiteral`/`BooleanLiteral`, or a
`BinaryExpression` whose `left` and `right` are both such literals. Truthiness is
computed with the host `eval` over JSON-stringified operands
(`eval(JSON.stringify(left) + operator + JSON.stringify(right))`, or
`eval(JSON.stringify(value))` for a bare literal).

`clear(path, toggle)` then keeps the winning branch: replace with `consequent` when
truthy; when falsy, replace with `alternate` or `remove()` if there is none. Consumed by the
`obfuscator`, `sojson`, `sojsonv7` and `jsconfuser` plugins, typically right after
[calculate-constant-exp.js](calculate-constant-exp.md) has made the tests constant.

**Restoring Babel's scope cache is this pass's postcondition, not its caller's problem.**
Detaching a subtree leaves every *other* binding's `referencePaths` pointing into it, and such a
reference reports `removed === false` while its cached parent chain still reaches a Program — so
only node reachability can see it, which is why it went unnoticed. The header used to say the code
must be *reloaded* to update the references, and each consumer answered that separately: three
plugins re-parse the whole program immediately afterwards, and the fourth does not re-parse at
all, so it carried the exposure with nothing answering for it. A `Program.exit` handler now crawls
once per traversal, and only when something was actually detached. A crawl rebuilds cached scope
information without touching the tree, so it cannot change emitted output.

**This is the only pass in `obfuscatorx`'s pipeline that creates the condition** — measured per
step over a maximal cell, every other pass in that pipeline reads zero detached references both
before and after itself. The inventory lives here rather than in each consumer because the pass
that breaks an invariant owns it; the consumer that paid for its absence is
[obfuscator/unlock-env.md](obfuscator/unlock-env.md), whose gates read `binding.referencePaths`
and which briefly carried a cache clear of its own to compensate.

**The surviving branch is spliced, not planted whole** (`replaceWithBranch`). A branch is
usually a `BlockStatement`, and putting that block where the `IfStatement` stood leaves a
bare `{ ... }` in the parent statement list. It changes nothing about execution, which is
why it survived unnoticed, but it changes the *shape a later matcher reads*: a pass keying
on a statement list's last element sees a `BlockStatement` where it required something
else. So the block's statements are spliced into the list instead, and the block is kept
only where it is load-bearing — when the path is not in a statement list, or when the block
owns a `let`/`const`/`class`/`function` declaration that would change meaning if relocated.
An empty surviving block removes the statement outright.

[delete-nested-blocks.js](delete-nested-blocks.md) performs the same splice as a **cleanup**
pass and is an alternative for a pipeline that already schedules it. Doing it here is
preferred where both are available: it stops the shape from being created rather than
removing it afterwards, and it costs no scope crawl (that pass re-crawls the parent scope
per block to test for binding collisions).

## Source

- [`src/visitor/prune-if-branch.js`](https://github.com/echo094/decode-js/blob/6cacb633ceedf0812fe31f951ba8f41ffb431ca1/src/visitor/prune-if-branch.js)
- Consumed by the `obfuscator`, `sojson`, `sojsonv7` and `jsconfuser` plugins, and by
  `obfuscatorx`, where it is scheduled inside the fixpoint group after constant folding and
  **before** [obfuscator/unflatten-switch-dispatch](obfuscator/unflatten-switch-dispatch.md).
- **It is load-bearing three times over in that pipeline, not tidying**, and the three roles are
  argued where each is measured rather than restated here: it is the un-flattener's precondition
  ([unflatten-switch-dispatch](obfuscator/unflatten-switch-dispatch.md)), it is the whole of the
  dead-code reversal ([obfuscator/dead-code-injection](obfuscator/dead-code-injection.md)), and it
  keeps donated helper clones out of the anti-tamper strip's way
  ([obfuscator/unlock-env](obfuscator/unlock-env.md)). Anyone moving it needs all three.

## Fixtures

`test/visitor/prune-if-branch/`, driven by `prune-if-branch.test.js` through the shared helper.
**The visitor had no committed coverage at all until U6**, despite four plugins consuming it, so
this table is the whole of what is pinned rather than a selection from it.

| Claim | Fixture |
|---|---|
| a true test keeps the consequent, spliced | `dci-taken-consequent` |
| a false test keeps the alternate, spliced | `dci-taken-alternate` |
| `!==` over two equal strings is false | `dci-not-equal-same` |
| a false test with no `else` removes the statement | `falsy-no-alternate` |
| the same folding applies to a `ConditionalExpression` | `conditional-expression` |
| a branch owning `let`/`const` keeps its block rather than being spliced | `lexical-branch-kept` |
| a test that is not statically decidable is left exactly as found | `non-constant-test`, which has **no** `.fix.js`: with `fix` false the helper compares against the input source |
| removing a branch leaves no reference pointing into the detached subtree | `outer-reference-in-dead-branch` |

**The last row is pinned by an assertion rather than by its golden, and that is the point.** Its
`.fix.js` is what every other case's would be — the output text is correct with or without the
postcondition — so what fails without the crawl is the shared helper's own
`detachedReferences` check. The six cases above stay clean only because their dead branches
declare what they use, so those bindings leave with the branch; a dead branch referencing
something declared *outside* it is the shape none of them could express.

**The cases are built around one encoder's shape on purpose.** javascript-obfuscator's dead-code
injection emits `if ('<rand5>' <===|!==> '<rand5>')` with the real block on the taken side, and this
visitor plus constant folding is the *entire* reversal of that transform
([obfuscator/dead-code-injection.md](obfuscator/dead-code-injection.md)) — so the four spellings it
can draw are the natural basis for a suite, and they exercise both operators and both branch
positions. That does not make the coverage encoder-specific: every case is a plain constant test.
