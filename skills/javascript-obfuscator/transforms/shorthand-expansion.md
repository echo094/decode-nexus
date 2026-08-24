# Shorthand expansion

Two `Converting` (6) transformers that write out a shorthand in full. Neither hides anything and
neither changes what the program does when its input is valid — they exist so that a *later* stage
has a distinct node to rename. `ObjectPatternPropertiesTransformer` has one focused exception:
from 5.4.0 it also expands a pattern inside a class static block when `renameGlobals` is off.

| Transformer | Option | Expansion |
|---|---|---|
| `ObjectPatternPropertiesTransformer` | `renameGlobals` (narrowing only) | `const {foo} = bar` → `const {foo: foo} = bar` |
| `ExportSpecifierTransformer` | **none** | `export {foo}` → `export {foo as foo}` |

`ExportSpecifierTransformer` holds still across the studied range. The ordinary pattern expansion
also holds still, but the static-block scope exception opens
[`E-shorthand-static-*`](../versions.md) at the focused 5.3.1/5.4.0 boundary.

## 1. Target

**A shorthand fuses two roles into one identifier**, and renaming needs them separated. In
`const {foo} = bar` the single token `foo` is both the *property being read* from `bar` and the
*binding being declared*. A renamer that rewrites it renames both at once — which is wrong, because
the property name belongs to `bar`'s shape and the binding is local. Writing it as `{foo: foo}`
gives the renamer two nodes, so it can rewrite the binding and leave the property alone.

`export {foo}` is the same problem: the token is both the local binding and the exported name, and
the exported name is part of the module's public interface that must not change.

So these are **enablers for `RenameIdentifiers` (7)**, not protections in themselves. Their output
is more verbose than their input and no less readable.

## 2. Algorithm

Both are one-line rewrites: clear the `shorthand` flag and give the node an explicit second half,
cloning the value node so the two are separate objects rather than one node referenced twice.

**`ObjectPatternPropertiesTransformer` is scope-narrowed rather than option-gated.** When
`renameGlobals` is **off**, a property whose lexical scope is the `Program` is left shorthand — the
reasoning being that a global binding is not going to be renamed, so there is nothing to separate.
From `E-shorthand-static-expanded`, a containing `StaticBlock` is checked before that Program-scope
skip, so a pattern in a class static block is expanded even with `renameGlobals` off. When
`renameGlobals` is on, every scope is expanded. The option does not switch the transform off; it
decides which non-static top-level cases participate.

## 3. Implementation

- **The parent must be an `ObjectPattern`** and the property must actually be `shorthand`; anything
  else returns unchanged. So this is destructuring only, never an object *literal* — an object
  literal's shorthand is cleared by `ObjectExpressionTransformer` instead
  ([property-name-literalization.md](property-name-literalization.md)), which is a separate code
  path reaching the same spelling.
- **The value is cloned and re-parentized**, so the pattern's key and value are independent nodes.
- **`ExportSpecifierTransformer` has no gate at all** and no scope condition.
- **The static-block exception is an ancestor check, not a new pattern spelling.** The transformer
  walks parents until it reaches a `StaticBlock`, function or Program; only the first of those
  bypasses the Program-scope skip. Wrapped static-block controls therefore already expand on both
  sides of the focused boundary.

## 4. Downstream Effects

| Later stage | What it does to this transform's output |
|---|---|
| `RenameIdentifiers` (7) | the reason both exist. With the halves separated it renames the binding and leaves the property or exported name intact |
| `StringArray` (8) | nothing — neither emits a string literal. An `ObjectPattern` key stays an identifier, and is not a literal that could be concealed |
| `Converting` (6), property-name literalization | does **not** apply here: these produce pattern and specifier nodes, not member accesses or object-literal keys |

## 5. Known Quirks

- **They make output longer and no harder to read**, which is unusual for this stage — their value is
  entirely in what stage 7 can then do.
- **`{foo: foo}` in output is ambiguous in origin.** The author may have written it, this
  transform may have expanded it, or `ObjectExpressionTransformer` may have cleared a literal's
  shorthand. Nothing distinguishes them, which is a reason to treat re-collapsing it as a readability
  choice rather than a provenance claim.
- **`renameGlobals` off does not mean the transform is off** — it means the Program scope is skipped.
  A sample built with `renameGlobals: false` still carries expanded patterns in every nested scope,
  and reading its absence at the top level as "the transform did not run" is wrong.
- **The old top-level static-block assignment is a malformed encoder output.** At the low focused
  tag it can leave `{x}` while the binding and later use have been renamed, producing a
  `ReferenceError`; it is malformed output rather than a successful runtime result. The high
  focused tag expands the pattern and runs correctly. Wrapped controls are equal and do not
  establish this boundary.

## Source

- [`ObjectPatternPropertiesTransformer.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/84861e8e397179d6597195626fe6783757eee3e0/src/node-transformers/converting-transformers/ObjectPatternPropertiesTransformer.ts)
- [`ExportSpecifierTransformer.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/node-transformers/converting-transformers/ExportSpecifierTransformer.ts)

The pattern transformer is read at the exact 5.3.1 and 5.4.0 tags for the static-block exception;
the export transformer is read at `2.19.0`, the spine. The ordinary pattern algorithm and export
transform remain otherwise unchanged in the evidence here.

## Fixtures

**None committed, and the corpus cannot supply any.**

| Claim | What checks it | Gap |
|---|---|---|
| destructuring shorthand is expanded | — | **no corpus input uses destructuring** |
| `renameGlobals` off skips only the Program scope outside static blocks | exact 5.3.1/5.4.0 focused static-block outputs | the focused matrix covers only the adjacent tags |
| export shorthand is expanded | — | **the corpus's inputs are scripts, not modules**, so no `export` exists to transform |
| wrapped static-block patterns are equal across the adjacent tags | exact focused outputs | this does not establish the boundary; only top-level controls differ |

**This is the least-covered doc in the package and the reason is structural.** Both transforms need
input shapes the corpus's three fixtures do not contain, and the export half needs a *module*, which
changes how a sample is built and run rather than just what it contains. A destructuring fixture is
cheap; an ESM fixture is a corpus change with its own harness consequences and should not be added
casually.
