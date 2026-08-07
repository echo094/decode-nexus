# Pack

Source: [`transforms/pack.ts`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/pack.ts) — `Order.Pack = 36`.

## 1. Target

Stop the real program from ever appearing as parseable top-level AST at all: wrap the
entire (root-level only) program as a string literal, executed through the `Function`
constructor, with every free/global identifier reference redirected through one shared,
property-mapped object — so a static reader sees only a giant string blob and an opaque
object of getters/setters, never the real source structure.

## 2. Algorithm

Two independent mechanisms, both scoped to identifiers with no binding in the program
(`path.scope.hasGlobal(name) && !path.scope.hasBinding(name)`) — a real local variable is
never touched:

- **Global/free-identifier remapping.** Every qualifying identifier reference becomes
  `{objectName}["{propName}"]`, backed by a `get` accessor on one shared object literal
  generated once, at the very end; a `set` accessor is added too, but only for an
  identifier that's ever the target of an assignment, since a read-only global needs no
  setter.
- **`typeof` operand remapping.** `typeof x` becomes `{objectName}["{propName}"]` as well,
  but through a *separate*, getter-only mapping — `x` and `typeof x` evaluate to different
  values, so they can't share one property even when `x` itself also qualifies for the
  first mapping.

Both mappings accumulate into `Map`s keyed by identifier name; nothing is emitted per
reference. Only once, at the very end (`finalASTHandler`, and only for the *root*
obfuscator — RGF's own sub-obfuscators skip this entirely and let their own parent handle
it), the accumulated maps become one `ObjectExpression` of getter/setter `ObjectMethod`
pairs, the whole (already-rewritten) program is generated to a compact source string, and
a fixed `Function({objectName}, {outputCode})({objectExpression})` template replaces the
program wholesale — with any `ImportDeclaration`s that were hoisted out during the
identifier pass re-prepended *before* that call, since `import` can't appear inside a
`Function`-constructor body.

Because `outputCode` becomes a function *body*, and a plain function body's last
expression has no special completion-value treatment the way a `Function(...)()` call site
does, the program's own last statement — if it's an `ExpressionStatement` — is rewritten
into a `ReturnStatement` first, so that value survives as the wrapper call's own completion
value.

## 3. Implementation

**Identifier visitor**
([`pack.ts#L75-L141`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/pack.ts#L75-L141)):
guards before either mapping applies — `isVariableIdentifier` (skip a non-reference
identifier, e.g. a property key or import specifier name), `isDefiningIdentifier` (skip a
declaration site itself), the `GEN_NODE` flag (skip `Finalizer`'s own synthetic literal-respelling
identifiers — see that transform's Downstream Effects for why this guard has to exist),
`WITH_STATEMENT`, `reservedIdentifiers`/`reservedNodeModuleIdentifiers` (allow
`module`/`exports`/`require` through unmapped when `target: "node"`),
`options.globalVariables`, the transform's own `objectName`/`variableFunctionName`, then
finally `hasGlobal(name) && !hasBinding(name)` and the user's own `options.pack`
probability map. `ImportDeclaration`/export handling
([`pack.ts#L56-L70`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/pack.ts#L56-L70)):
imports are collected into `prependNodes` and removed (forcing a scope re-crawl so the
now-unbound names read as globals); any export declaration is an outright,
unconditional `me.error(...)` — Pack does not support export statements at all.

**`finalASTHandler`**
([`pack.ts#L149-L239`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/pack.ts#L149-L239)):
returns the AST untouched for any non-root obfuscator
([`pack.ts#L150`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/pack.ts#L150)).
Builds one `get propName() { return identifierName; }` per global mapping, a matching
`set propName(objectName) { return identifierName = objectName; }` only where a setter was
flagged needed, and one getter-only `get propName() { return typeof identifierName; }` per
`typeof` mapping. Rewrites the program's trailing `ExpressionStatement` to a `ReturnStatement`
([`pack.ts#L210-L217`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/pack.ts#L210-L217)) —
in place, via `Object.assign`, so anything that already held a reference to that statement
node observes the mutation. Generates the whole rewritten program to a compact string
(`Obfuscator.generateCode`), then substitutes a fixed `Template`
([`pack.ts#L226-L229`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/pack.ts#L226-L229)):
`{prependNodes}\nFunction({objectName}, {outputCode})({objectExpression});`.

## 4. Downstream Effects

None currently documented — Pack is the last content-changing stage before `Integrity`
(Order 37), and nothing has been found that further rewrites Pack's own wrapper output; a
checksum/anti-tamper stage reading the already-generated string is a different kind of
interaction than the AST rewrites this section tracks elsewhere.

## 5. Known Quirks

**Export statements are entirely unsupported**, not degraded gracefully: any
`ExportNamedDeclaration`/`ExportDefaultDeclaration`/`ExportAllDeclaration` hits an
unconditional `me.error(...)` the moment `pack` is enabled, regardless of what else the
program contains.
