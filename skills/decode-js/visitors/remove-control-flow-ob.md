# remove-control-flow-ob.js

Undoes javascript-obfuscator's **BlockStatementControlFlowFlattening** — a
`while(true){ switch(order[idx++]){ case ...} break; }` whose execution order is driven
by a `"|"`-joined index string. Runs on `WhileStatement` **`exit`**.

Match requirements:

- the `while` test is an always-true form: `true`, a prefix `UnaryExpression` (e.g.
  `!![]`), or an empty `ArrayExpression`;
- the body's first statement is a `SwitchStatement` on a `MemberExpression`
  discriminant (`arr[idx]` style) and the second is a `BreakStatement`;
- scanning the `while`'s previous siblings finds both control variables — `arr`, defined
  as `"a|b|c".split("|")` (`init.callee.object` is the `StringLiteral`), and the numeric
  index var. Exactly those two declarations must be found; both are removed.

Reconstruction (`扁平化还原: arr[idx]`): for each token in the order array it starts at that
case index and appends each case's `consequent` statements, walking to the next index,
stopping at a `continue` (loop back) or `return` (which is emitted, then stops).
Out-of-order case labels and stray `break`s are logged but tolerated. The whole `while`
is replaced with the linear body via `replaceInline`.

Consumed by the `sojson`, `sojsonv7`, and `obfuscator` plugins. This is the
**switch/block** flavor of flattening; the object-dispatch flavor is handled by
[parse-control-flow-storage.js](parse-control-flow-storage.md).

## Known Gaps

**Three of these are not fail-closed incompleteness — they corrupt or crash.** That is unusual for
a decoder pass and is stated first for that reason. Each was built as a minimal case and run
(2026-08-14); the first two produce wrong output *silently*, which no residue census can catch
because the residue is gone.

| Input | Result |
|---|---|
| `while (!done) { switch (o[i++]) { … } break; }` — an ordinary state-machine loop | **the loop is deleted** and its body emitted straight-line, executed once. The always-true gate accepts *any* prefix `UnaryExpression`, and `!done` is one |
| a case whose consequent has neither `continue` nor `return` | **statements are duplicated** — the walk-forward loop runs on into the next case and appends it again. `case '0': a(); case '1': b(); continue;` with order `0\|1` emits `a(); b(); b();` |
| `switch (o[i])` — a discriminant without `++` | **throws** `Cannot read properties of undefined (reading 'name')`, aborting the whole decode. The match checks that the discriminant is a `MemberExpression` but never that its property is an `UpdateExpression` |
| the controller declaration is not a previous sibling of the `while` | declines silently — the one benign outcome of the four |

**The throw is the same class as the bug closed in
[#99](https://github.com/echo094/decode-js/issues/99)**, where `getAllPrevSiblings` returned a node
whose type was never validated. That fix guarded the sibling scan and left the discriminant access
two lines above it unguarded, which is the shape of "one fix is never the whole fix".

**The corpus cannot find any of this.** Over every javascript-obfuscator sample in the frozen
corpus the pass un-flattens every live block correctly, because this encoder always emits
`while(true)`, always terminates a case with `continue` or `return`, and always writes `[i++]`. The
failures need input the encoder does not produce — a hand-written loop, or a tree some earlier pass
has moved a `continue` out of.

- **The order-string gate matches nothing the obfuscator actually emits.** It requires
  `init.callee.object` to be a bare `StringLiteral`, i.e. literally `"a|b|c".split("|")`. Across
  every javascript-obfuscator sample in the frozen corpus, **not one** flattened block presents
  that shape: the controller arrives as a member read on a control-flow storage, because the same
  stage's sibling transformer lifts any string of length ≥ 3 into that storage, or as a `+` chain
  where `splitStrings` has broken it up. So this visitor is inert on raw encoder output and depends
  entirely on [parse-control-flow-storage.js](parse-control-flow-storage.md) and constant folding
  having run first — which is why `obfuscator.js` schedules it in `cleanDeadCode`, after
  `decodeCodeBlock`. The dependency is load-bearing, not incidental.
- **The always-true test accepts any prefix `UnaryExpression`**, so `while (!x)` passes the gate.
  The branch exists because the encoder's Converting stage re-spells `true` as `!![]`; once a
  boolean fold runs upstream the branch is both unnecessary and unsound, and nothing narrows it.
- **`discriminant.property.argument.name` is unguarded.** The match checks that the discriminant is
  a `MemberExpression` but never that its property is an `UpdateExpression`, so a discriminant like
  `arr[k]` throws rather than declining.
- **The walk-forward-until-`continue` loop is written for a fallthrough this encoder never emits.**
  Every case consequent is `[statement, continue]`, or a lone `return`, so the loop always consumes
  exactly one case. The generality is unused and it obscures what the pass actually does, which is
  a permutation: read the order string left to right and index the case list.
- **It detects two violations and only logs them, then rewrites anyway** — an out-of-order case
  label and an unexpected `break`. Both are signs the tree is not the shape the pass assumes, and
  continuing past them produces a rewrite nobody can check. It also removes the two control
  declarations *before* rebuilding, so there is no point at which it can still decline.
- **No `onChange` channel**, so a caller cannot run it to a fixpoint or tell whether it fired.
- **No test coverage anywhere in the tree.**

## Source

- `src/visitor/remove-control-flow-ob.js` — the whole visitor.

Consumed by `src/plugin/obfuscator.js` inside `cleanDeadCode`, and by the `sojson` and `sojsonv7`
plugins. **Not** consumed by `obfuscatorx`, which runs a fork —
[unflatten-switch-dispatch.md](obfuscator/unflatten-switch-dispatch.md) states the four behaviours
that decided the fork and why three of them are worse than declining.

## Fixtures

**None, and the absence is the point rather than an oversight.** This visitor has no committed
cases at all, in a repository where three plugins depend on it. What stands in for coverage today
is one encoder's corpus, and Known Gaps above is a list of behaviours that corpus cannot reach —
which is the shape of evidence W7 warns about: a pass validated only against one
encoder's whole output is not proven sound, because the gaps are exactly the inputs that encoder
cannot produce, so every census reads clean and the pass looks proven.

The cases worth having are therefore the ones that go *off* the encoder's path, and they have to be
hand-built:

| Claim | Status |
|---|---|
| a well-formed flattened block is linearised in order | uncovered; exercised only through plugin-level corpus runs |
| a discriminant that is not `arr[idx++]` is declined rather than read | uncovered — and the fork exists because this one **throws** here instead |
| out-of-order case labels and stray `break`s are tolerated | uncovered; the visitor logs and continues, so nothing distinguishes tolerate from mis-order |
| exactly the two control declarations are found and removed | uncovered |

Adding them is additive and changes no behaviour, so nothing in the shared-visitor rules blocks it;
it is unowned rather than forbidden.
