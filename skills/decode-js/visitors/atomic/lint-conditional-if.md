# lint-conditional-if.js

Reverses a conditional used as a statement (on **`exit`**), in two positions:

```
test ? a : b;          ->  if (test) a; else b;
return test ? a : b;   ->  if (test) return a; else return b;
```

Each branch keeps the statement kind of the site it replaces, which is what makes the return form
safe — two `return`s preserve the function's completion where two expression statements would
silently drop it.

**The position gate matters more here than for the logical form**, because conditionals in value
position are common in ordinary code. The node must be the *entire* expression of an
`ExpressionStatement` or the *entire* argument of a `ReturnStatement`; everything else is a value.
Measured over a javascript-obfuscator corpus, **value-position conditionals outnumber
statement-position ones roughly two to one**, and an ungated pass is wrong on every one of them —
so the gate rejects more sites than it accepts, and that is the pass working rather than failing.
The census to re-read it with is the ratio of declined to matched, not either count alone.

**A declined site is skipped and traversal continues**, for the reason
[lint-logical-if.js](lint-logical-if.md) gives.

**Nested conditionals resolve in one traversal.** Babel requeues a replaced node, so an inner
conditional that was in value position while the outer still existed becomes convertible once the
outer has become an `if`. `c ? d ? a() : b() : e()` reaches
`if (c) { if (d) a(); else b(); } else e()`, correctly braced against a dangling `else`.

**A conditional in value position is often one rewrite away from being convertible** — see
[convert-conditional-assign.js](convert-conditional-assign.md), which is why that one runs first.

Exports a plain visitor as default plus `createLintConditionalIf(onReverse)`.

## Source

- [`src/visitor/atomic/lint-conditional-if.js`](https://github.com/echo094/decode-js/blob/6cacb633ceedf0812fe31f951ba8f41ffb431ca1/src/visitor/atomic/lint-conditional-if.js)
- Wired second-to-last in [normalize-statements](../obfuscator/normalize-statements.md)'s round,
  immediately before [lint-logical-if](lint-logical-if.md) and after
  [convert-conditional-assign](convert-conditional-assign.md) has moved value-position
  conditionals into reach.

## Fixtures

[`test/visitor/lint-conditional-if/`](https://github.com/echo094/decode-js/tree/6cacb633ceedf0812fe31f951ba8f41ffb431ca1/test/visitor/lint-conditional-if),
driven by `lint-conditional-if.test.js`. The `-valid` shapes are what
javascript-obfuscator's `IfStatementSimplifyTransformer` emits; the `-invalid` ones are every
position where a conditional carries a value and must come back byte-identical.

| Fixture | Claim it pins | Era |
|---|---|---|
| `statement-valid` | the statement form, `test ? a : b;` → `if (test) a; else b;` | hand-built — none |
| `return-valid` | the return form emits **two `return`s**, preserving the function's completion where two expression statements would drop it | hand-built — none |
| `nested-consequent-valid` | nested conditionals resolve in **one** traversal, because Babel requeues a replaced node — and the result is braced against a dangling `else` | hand-built — none |
| `declarator-invalid`, `argument-invalid`, `arrow-body-invalid`, `operand-invalid`, `property-invalid` | the five value positions the gate must refuse | hand-built — none |
| `bound-statement-valid`, `bound-return-valid` | the rewrite against **real bindings**: both bind `x` and reference it inside each branch, so the helper's reference-state check has two non-empty lists to compare instead of two empty ones | hand-built — none |
| `real-output-state` | the state invariant on **harvested** encoder output, with no golden | real output; the column it came from is recorded nowhere, so its era is unknown |

**Three things about this table are the point of it.**

- **The `-invalid` cases are the pass working, not gaps.** Value-position conditionals outnumber
  statement-position ones roughly two to one on real output, so a gate that rejects more than it
  accepts is the expected shape.
- **`real-output-state` has no `.fix.js` deliberately.** The input is eleven kilobytes of generated
  identifiers, so a golden could not be honestly reviewed — and an unreviewed golden is worse than
  none, because exact string equality makes it look authoritative. It asserts the derived-state
  invariant against a fresh parse of the visitor's own output, which needs no expected text.
- **It is harvested because the defect it pins is not buildable.** This visitor duplicated
  references on real output; six hand-built shapes and a sweep to 200 references all read zero
  against the pre-fix visitor, and deleting any single statement from the real function kills it
  too. That is `W7` exactly — an isolated fixture omits the thing that breaks a matcher on combined
  output — and it is why the two `bound-*` cases, which *do* exercise real bindings, still did not
  reproduce it.
