# ObjectExtraction

Source: [`transforms/extraction/objectExtraction.ts`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/extraction/objectExtraction.ts) — `Order.ObjectExtraction = 1`.

## 1. Target

Eliminate the "these variables were one object" relationship from the AST entirely, not
just conceal it: split a qualifying object literal into independent flat identifiers with
no residual structure tying them back together.

## 2. Algorithm

`var obj = { a: 1, b: 2 }` — never reassigned, no `this`-referencing methods, no dynamic
property access anywhere it's used — splits into independent
`{ph}_obj_a = 1; {ph}_obj_b = 2;` declarations; every `obj.a`/`obj["a"]` reference becomes
the flat identifier directly. The `{ph}` prefix is `me.getPlaceholder()`
(`__p_<random4>_...`, see
[transforms/plugin.ts#L142](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/plugin.ts#L142)),
whose own doc-comment notes these are temporary names "typically before RenameVariables
has ran."

## 3. Implementation

[`objectExtraction.ts#L24-L145`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/extraction/objectExtraction.ts#L24-L145),
gated on all of:

- Single-declarator `VariableDeclaration`, no destructuring, a plain `Identifier` id, an
  `ObjectExpression` init.
- The binding is never reassigned (`constantViolations.length === 0`).
- Every property is a plain `ObjectProperty` with a static string key — no
  computed/dynamic key, no duplicate key across properties.
- A method/function property value doesn't reference `this` anywhere in its body (the
  extracted value would no longer have the original object as `this`).
- Every *other* reference to the object identifier throughout its enclosing
  function/Program is itself a `MemberExpression` with a statically-resolvable property
  string that names a property the literal actually had — a bare reference to the object
  itself (passed as a value, spread, etc.), a `delete obj.prop`, or an access to a property
  added later are all disqualifying.
- `options.objectExtraction`'s probability map.

Naming: `newObjectName = {ph}_{originalName}`; each property's flat name is
`{newObjectName}_{propertyKey}` if `propertyKey` is a valid identifier, else
`{newObjectName}_{ph}`.

## 4. Downstream Effects

**`RenameVariables` (Order 30) unconditionally renames every placeholder-prefixed
identifier this transform produces.** `shouldRename()` returns `true` unconditionally for
any name starting with the placeholder prefix ("Placeholder variables should always be
renamed",
[`renameVariables.ts#L258-L259`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/identifier/renameVariables.ts#L258-L259)).
Combined with `renameVariables: true` being on in all three built-in presets
([`presets.ts`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/presets.ts)
lines 34, 78, 107), the `{ph}_objName_prop` naming this transform produces is guaranteed to
be scrubbed to a short mangled name in the default path for any preset-based obfuscation,
not just an edge case.

## 5. Known Quirks

None currently documented.
