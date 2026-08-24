# collapse-property-shorthand.js

Collapses a property whose key and value are the same name back to shorthand:
`const { foo: foo } = bar` becomes `const { foo } = bar`, and `({ foo: foo })` becomes `({ foo })`.

**Why the expanded form exists at all.** Obfuscators expand shorthand so a renaming pass has two
nodes where the source had one: in `{ foo }` the single token is both the property read and the
binding declared, and a renamer must rewrite the binding while leaving the property name alone.

**And that is exactly why this pass never fires on javascript-obfuscator output.** The renaming it
was expanded for then happens, so the emitted form is `{ foo: _0x31be2d }` — key and value differ
permanently, and the information needed to collapse is gone. Measured at both settings of
`renameGlobals`, which makes no difference: the destructured *bindings* are renamed either way.

So this visitor is **correct and, for that one encoder, dead**. It is kept because the atomic layer
is plugin-agnostic and an encoder that does not rename — or renames symmetrically — leaves the shape
intact. What it must not be mistaken for is coverage: a residue census keyed on this shape reads
zero against javascript-obfuscator because the shape is unreachable, not because the pass removed
anything.

**One exclusion, and it is the mirror image of the usual `__proto__` trap.** In an
*ObjectExpression*, `{ __proto__: x }` sets the prototype while the shorthand `{ __proto__ }` merely
defines an own property, so collapsing it changes meaning. The special case is scoped to the
`PropertyName : AssignmentExpression` form, which is exactly what collapsing removes. Verified by
construction rather than read from the spec: `Object.getPrototypeOf` reports the prototype set for
the expanded form and not for the shorthand.

In an *ObjectPattern* there is no such hazard — destructuring `{ __proto__: __proto__ }` and
`{ __proto__ }` both bind the name — but the gate does not distinguish the two positions. Refusing
the name in both costs one unreachable collapse and removes a class of error entirely.

**Note the direction of the risk against [uncompute-property-key.js](uncompute-property-key.md).**
There, `__proto__` is refused when *losing brackets*; here it is refused when *gaining shorthand*.
Same name, opposite operations, and both change meaning — which is why neither pass may assume the
other's exclusion list covers it.

**`export { foo as foo }` is deliberately not handled.** It parses to the *same* AST as
`export { foo }` — an `ExportSpecifier` whose `local` and `exported` names match — so there is no
node to rewrite and nothing to detect. The generator already prints the short form, making that
reversal free at generation time.

Exports a plain visitor as default plus `createCollapsePropertyShorthand(onChange)`, used by
[normalize-converting.js](../obfuscator/normalize-converting.md).

## Source

- [`src/visitor/atomic/collapse-property-shorthand.js`](https://github.com/echo094/decode-js/blob/6cacb633ceedf0812fe31f951ba8f41ffb431ca1/src/visitor/atomic/collapse-property-shorthand.js)
- Wired **last** in [normalize-converting](../obfuscator/normalize-converting.md)'s round, after
  `merge-object`. Position is uncontentious here for the reason above: against this encoder the
  pass has no population at all, so nothing it produces is anyone's input.

## Fixtures

**None of its own; two cases of [normalize-converting](../obfuscator/normalize-converting.md) carry
its claims.** A dedicated directory would be misleading rather than merely redundant — see the last
paragraph.

| Claim | What pins it | Era |
|---|---|---|
| `__proto__` is never collapsed to shorthand, and the guard is not vacuous | the `__proto__ is never collapsed` unit case, which puts a safe sibling in the same object literal and requires *it* to collapse | hand-built — none |
| the pass leaves renamed patterns alone rather than corrupting them | `object-pattern-shorthand`, real encoder output | real output, one column |

**A zero here is unreachability, not coverage, and that is what the fixture table has to say out
loud.** The shorthand expansion exists so a renamer has two nodes to work with; the renamer then
runs, so javascript-obfuscator's emitted form is `{ foo: _0x31be2d }` and the information needed to
collapse is permanently gone — measured at both settings of `renameGlobals`, which changes nothing
because the destructured bindings are renamed either way. So `object-pattern-shorthand` pins that
the pass **declines**, and a census keyed on this shape reads zero against this encoder because the
population is empty.

**The pass is kept because the atomic layer is plugin-agnostic**: an encoder that does not rename,
or renames symmetrically, leaves the shape intact. Judging it on this corpus alone is exactly what
`W7` warns against — one encoder's output is a narrow slice, and its regularities are invisible
from inside.
