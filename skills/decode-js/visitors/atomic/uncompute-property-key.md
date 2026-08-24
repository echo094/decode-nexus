# uncompute-property-key.js

Restores a property or class-member key that was rewritten into a string:
`["foo"]() {}` → `"foo"() {}` → `foo() {}`, and `{ "foo": 1 }` → `{ foo: 1 }`.

**This is two rewrites, not one, and only the first is dangerous.** Keeping them as separate steps
is the whole design: it confines the risk to one step and lets that step delegate to a guard that
already exists.

**Step 1 — un-compute, via `safeFunc.uncomputeStringKey`.** Three keys change meaning when they lose
their brackets, and that shared helper already refuses all three:

| Key | Computed | Un-computed |
|---|---|---|
| `{ ["__proto__"]: v }` | defines an own property | `{ "__proto__": v }` sets the **prototype** |
| `class C { ["constructor"](){} }` | an ordinary method | `"constructor"(){}` **is** the class constructor |
| `static ["prototype"]` | a SyntaxError computed | a runtime error un-computed |

This pass calls the helper rather than reimplementing the list, so a fourth case has one place to be
corrected. **The existing `obfuscator` plugin's inline equivalent does not**, and un-computes any
string key unguarded — recorded in [plugins/obfuscator.md](../../plugins/obfuscator.md) as the
clearest case in that stage where the shared helper beats the plugin's own copy.

**Step 2 — de-literalize, gated only on the identifier form.** Once a key is non-computed the
remaining change is spelling: `{ "__proto__": v }` and `{ __proto__: v }` are both the prototype
setter, `"constructor"(){}` and `constructor(){}` are both the constructor. So no exclusion list
applies here — the only gate is whether the string has an identifier spelling at all, which leaves
`{ "foo bar": 1 }` and `{ "0": 1 }` quoted.

**A key that was already non-computed skips step 1 and is still eligible for step 2**, which is what
makes the pass idempotent and safe to re-run in a fixpoint loop.

Covers `ObjectProperty`, `ObjectMethod`, `ClassMethod` and `ClassProperty`. Exports a plain visitor
as default plus `createUncomputePropertyKey(onChange)`, used by
[normalize-converting.js](../obfuscator/normalize-converting.md).

## Source

- [`src/visitor/atomic/uncompute-property-key.js`](https://github.com/echo094/decode-js/blob/6cacb633ceedf0812fe31f951ba8f41ffb431ca1/src/visitor/atomic/uncompute-property-key.js)
- The exclusion list it delegates to lives in
  [`src/utility/safe-func.js`](https://github.com/echo094/decode-js/blob/6cacb633ceedf0812fe31f951ba8f41ffb431ca1/src/utility/safe-func.js) as
  `uncomputeStringKey`, deliberately shared so a fourth dangerous key has one place to be added.
- Wired third in [normalize-converting](../obfuscator/normalize-converting.md)'s round, after
  member un-computing and before `merge-object`.

## Fixtures

**None of its own; its claims are pinned as cases of
[normalize-converting](../obfuscator/normalize-converting.md)**, which is the composition that
schedules it. That is defensible for the two-step design — both steps are exercised — but it means
a failure here surfaces as a failure of the composition.

| Claim | What pins it | Era |
|---|---|---|
| step 1 refuses all three dangerous keys | the `dangerous keys are never un-computed` unit case: `["__proto__"]`, `["constructor"]` and `static ["prototype"]` all keep their brackets | hand-built — none |
| **the guard is not vacuous** | the `ordinary keys are un-computed` case, a safe key in the same three positions that *is* rewritten | hand-built — none |
| step 2 de-literalizes a quoted key | `class-member-keys`, plus the entry-level `test/obfuscatorx/2.19.0-class-logical` focused producer cell | real output from an upstream-derived fixture and from the frozen focused corpus cell |
| the pass survives getter/setter members | `object-keys-getset`, from upstream's `get-set-property-kind` fixtures | real output, one column |
| idempotence — an already-non-computed key still reaches step 2 | nothing | — |

**The last row is the honest gap.** Idempotence is what makes this pass safe to re-run inside a
fixpoint loop, and it is asserted nowhere: every committed case runs the pass once. A second
traversal over a case's own output would close it and costs one line.
