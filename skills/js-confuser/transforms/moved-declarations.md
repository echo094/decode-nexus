# MovedDeclarations

Source: [`transforms/identifier/movedDeclarations.ts`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/identifier/movedDeclarations.ts)
· `Order.MovedDeclarations` = 25

Because Order 25 runs **after** ControlFlowFlattening (Order 24), everything CFF emits —
its `_main` declaration, its entry harness — reaches later stages already rewritten by
this transform. Anything reading that output has to expect both forms (see
[control-flow-flattening.md](control-flow-flattening.md)'s Downstream Effects).

## 1. Target

Hide a declaration's structural identity: rewrite a `var` declaration into a bare
assignment with the declaration recreated elsewhere (block top, or folded into the
enclosing function's parameter list), and rewrite a nested function declaration into a
parameter slot plus a lazy-init guard — so a reader or a structural matcher relying on
"this is a `VariableDeclaration`" or "this is a `FunctionDeclaration`" no longer sees one
where the source had one.

## 2. Algorithm

Two independent mechanisms, in two separate visitors — both *structural* rewrites, not
reordering: each replaces a declaration form with a different statement form, and the name
survives only because a matching binding is created somewhere else.

**Mechanism 1** — a single-declarator `var` becomes a bare assignment (a missing
initializer becomes the literal identifier `undefined`), with the declaration itself
re-created either as a bare `var name` prepended to the enclosing block's top (or folded
into that block's existing top `var` statement, producing a merged `var a, b, c`), or —
when the enclosing function is `PREDICTABLE` and eligible — pushed onto the enclosing
function's own parameter list instead.

**Mechanism 2** — a nested `FunctionDeclaration` that is a direct child of an enclosing
`PREDICTABLE` function's body is retyped to an anonymous `FunctionExpression`, its name
appended to the enclosing function's parameters, and a guard prepended to the body's top
that lazily assigns the function expression to that parameter the first time it's needed:

```js
function outer(a) {                function outer(a, inner) {
  function inner(x) {                if (!inner) {
    return x * 2                       inner = function (x) {
  }                        ───────▶      return x * 2;
  return inner(a)                      };
}                                    }
                                     return inner(a);
                                   }
```

Both mechanisms push onto the **same** parameter list, so a packed slot from either one is
frequently not the last parameter — neither a reader nor a decoder can assume the synthetic
slots appear in any particular order, only that they follow the real parameters.

## 3. Implementation

**Mechanism 1** ([`VariableDeclaration.exit`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/identifier/movedDeclarations.ts#L118-L249))
fires on any `var` with exactly one declarator and an `Identifier` id:

```ts
path.replaceWith(
  t.assignmentExpression(
    "=",
    t.identifier(name),
    declaration.init || t.identifier("undefined"),
  ),
);
```

Two `insertionMethod`s for where the declaration itself reappears:

- **`variableDeclaration`** — a bare `var name` declarator prepended to the top of the
  enclosing block, or pushed onto the block's existing top `var` statement if there is one.
- **`functionParameter`** — chosen when the enclosing function is `PREDICTABLE` and
  [eligible](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/identifier/movedDeclarations.ts#L28-L55)
  (no rest param, ≤1000 params, no duplicate name). If the value is static and the
  declaration was already first in its block, the statement is dropped entirely and the
  parameter carries the value as a default (`t.assignmentPattern`) instead.

The decision is made **per declaration**: the `isDefinedAtTop` early-return can skip one
statement while moving its neighbour, so adjacent declarations do not necessarily end up
in the same form.

**Mechanism 2** ([`FunctionDeclaration.exit`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/identifier/movedDeclarations.ts#L59-L116))
requires the enclosing function to not be in strict mode (it relies on a non-simple
parameter):

```ts
functionExpression.type = "FunctionExpression";
functionExpression.id = null;

var identifier = t.identifier(functionName);
functionPath.node.params.push(identifier);
// ... binding.kind = "param"
prepend(
  fnBody,
  new Template(`
    if(!${functionName}) {
      ${functionName} = {functionExpression};
    }
    `).single({ functionExpression: functionExpression }),
);
path.remove();
```

The guard exists because the slot is a real parameter a caller *could* supply — no caller
ever does (it's appended beyond the function's original arity purely as a hiding place),
so the guard is always taken. It's prepended to the **top of the body**, not to where the
declaration stood — any adjacency between that declaration and the statements that
followed it is lost.

## 4. Downstream Effects

**`Minify` (Order 28) re-spells Mechanism 1's output twice**, and it runs after this
transform (Order 25), so what a reader of finished output sees is the *composition*, not
what §3 emits:

- **The merged `var a, b, c` at block top is not evidence that Mechanism 1 folded.** §3's
  fold produces one, but so does Minify's `var a; var b;` → `var a, b;`
  ([`minify.ts#L82-L138`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/minify.ts#L82-L138))
  from declarations this transform prepended separately. The two are indistinguishable in
  the output, so a count of merged declarations attributes to neither on its own.
- **The `undefined` initializer this transform writes for a missing one (§2) is stripped
  again**: `var x = undefined` → `var x`
  ([`minify.ts#L293-L301`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/minify.ts#L293-L301)).
  That rewrite fires on the `VariableDeclarator` form, so it reaches the re-created
  declaration, not the bare assignment Mechanism 1 left in the statement's place.

Mechanism 1 also fires on **any** single-declarator `var` with an `Identifier` id (§3), so
neither effect is scoped to a particular construct — every block that reaches Order 28 with
declarations carries the composed shape.

`RenameVariables` (Order 30) has no effect worth recording: neither mechanism's own output
is identified by name anywhere.

## 5. Known Quirks

None currently documented.
