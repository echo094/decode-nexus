# convert-conditional-assign.js

Distributes an assignment into both branches of a conditional (on **`exit`**):

```
r = test ? a : b   ->   test ? r = a : r = b
```

**On its own this simplifies nothing** — it is purely positional. A conditional in value position
cannot become an `if`, and this moves it into statement position where
[lint-conditional-if.js](lint-conditional-if.md) can reach it. It is worth running only ahead of
that pass, and is worth nothing otherwise.

The assignment target is **cloned** into each branch rather than shared, so the branches do not
alias one node. Compound operators work unchanged (`r += t ? 1 : 2`), as do member targets
(`o[i] = t ? 1 : 2`).

**A `VariableDeclarator` is deliberately not distributed.** `var r = t ? a : b` would need its
declaration hoisted out of the initializer to become convertible, which changes where the binding
is introduced — a scope decision, and a different one from this.

**Not safe for every target.** A target with its own side effects or an unstable value —
`obj[i++] = t ? a : b` — has that effect duplicated into both branches. Only one branch executes,
so the effect still happens exactly once; what changes is that it is now evaluated *after* the
test rather than before it, which is observable where the test reads what the target writes. No
instance has been met in this encoder's output; recorded as a property of the rewrite.

Exports a plain visitor as default plus `createConvertConditionalAssign(onConvert)`.

## Source

- [`src/visitor/atomic/convert-conditional-assign.js`](https://github.com/echo094/decode-js/blob/6cacb633ceedf0812fe31f951ba8f41ffb431ca1/src/visitor/atomic/convert-conditional-assign.js)
- Wired **first** in [normalize-statements](../obfuscator/normalize-statements.md)'s round. That
  position is the whole of its value: it produces nothing a reader wants and exists only to feed
  [lint-conditional-if](lint-conditional-if.md), so running it after that pass would be running it
  for nothing.

## Fixtures

[`test/visitor/convert-conditional-assign/`](https://github.com/echo094/decode-js/tree/6cacb633ceedf0812fe31f951ba8f41ffb431ca1/test/visitor/convert-conditional-assign),
driven by `convert-conditional-assign.test.js` — which also imports
[lint-conditional-if](lint-conditional-if.md), since the pair is what the rewrite is for. **All
hand-built, so none carries an era.**

| Fixture | Claim it pins |
|---|---|
| `assignment-valid` | the distribution itself, `r = t ? a : b` → `t ? r = a : r = b` |
| `compound-valid` | a compound operator survives unchanged (`r += t ? 1 : 2`) — the operator is carried, not assumed to be `=` |
| `member-target-valid` | a member target works, and **is cloned into each branch** rather than shared, so the two branches do not alias one node |
| `declarator-invalid` | `var r = t ? a : b` is deliberately refused: converting it would hoist the declaration out of its initializer, which is a scope decision this pass does not make |
| `statement-invalid` | a conditional already in statement position is left alone — this pass moves things *into* that position and has nothing to do once they are there |

**The unstable-target hazard has no case.** A target with its own side effects
(`obj[i++] = t ? a : b`) has that effect re-ordered relative to the test, which is observable where
the test reads what the target writes. No instance has been met in this encoder's output, so the
property is recorded in the prose above rather than pinned — a fixture would be asserting a
behaviour nobody has decided is wrong.
