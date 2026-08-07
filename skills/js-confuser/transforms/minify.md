# Minify

Source: [`transforms/minify.ts`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/minify.ts) — `Order.Minify = 28`.

## 1. Target

Standard structural minification — the same class of rewrite a general-purpose minifier
(Terser, `@babel/minify`) would apply — not obfuscation. It shrinks and normalizes shape;
none of its own rewrites are meant to conceal anything, unlike every other transform in
this pipeline.

## 2. Algorithm

Every sub-rule is a plain `exit` visitor in a single combined visitor object; none of them
depend on any other jsconfuser transform having run first. Six behavior groups, by how
reversible each is:

- **Literal shortening** — reversible, syntax-level only (same value, shorter spelling).
- **Constant folding** — one-directional; the pre-fold form is not recoverable, but there
  is nothing meaningful to recover since the folded value *is* the original semantics.
- **Readability-*increasing* rewrites** — makes minified output easier to read, not
  harder; nothing to reverse.
- **Statement-level cosmetics** — merges/unwraps that change spelling, not semantics.
- **Dead code elimination** — genuinely destructive, same as any minifier's DCE pass; the
  removed code is gone.
- **Simple destructuring collapse** — folds a single-binding destructure into a plain
  assignment.

## 3. Implementation

**Literal shortening:**

- `true`/`false` → `!0`/`!1` (`BooleanLiteral`,
  [`minify.ts#L140-L148`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/minify.ts#L140-L148))
- `undefined` → `void 0`, `Infinity` → `1/0` (`Identifier`,
  [`minify.ts#L246-L257`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/minify.ts#L246-L257),
  using the `identifierMap` defined at
  [`minify.ts#L18-L24`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/minify.ts#L18-L24))
- `return undefined` → `return` (`ReturnStatement`,
  [`minify.ts#L359-L365`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/minify.ts#L359-L365))
- `var x = undefined` → `var x` (`VariableDeclarator`,
  [`minify.ts#L293-L301`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/minify.ts#L293-L301))

**Constant folding:** `"a"+"b"` → `"ab"` (`BinaryExpression`) and `!literal` → boolean
(`UnaryExpression`), both at
[`minify.ts#L150-L179`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/minify.ts#L150-L179);
`cond ? a : b` with a statically-known `cond` → `a`/`b` (`ConditionalExpression`,
[`#L259-L268`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/minify.ts#L259-L268));
`a += 1` → `a++` (`AssignmentExpression`,
[`#L339-L356`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/minify.ts#L339-L356)).

**Readability-increasing rewrites:** `a["key"]` → `a.key` and `{"key": 1}` → `{key: 1}`
whenever `key` is a valid identifier
([`minify.ts#L180-L217`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/minify.ts#L180-L217)).

**Statement-level cosmetics:** `var a; var b;` → `var a, b;`
([`minify.ts#L82-L138`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/minify.ts#L82-L138)),
single-element `SequenceExpression` unwrap, `EmptyStatement` removal, bare-identifier
`ExpressionStatement` removal, single-statement block unwrap on
`while`/`for`/`with`, and `if`/`else` → ternary/`&&`/return-conditional collapsing
([`minify.ts#L369-L523`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/minify.ts#L369-L523)).

**Dead code elimination:** unused `FunctionDeclaration`/`VariableDeclarator` removal
([`minify.ts#L269-L336`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/minify.ts#L269-L336)),
unreachable-code and implied-trailing-`return` removal in the shared
`Block|SwitchCase` visitor
([`minify.ts#L528-L612`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/minify.ts#L528-L612)).

**Simple destructuring collapse:** `var [a] = [b]` → `var a = b`, `var {a} = {a: b}`
→ `var a = b`, via `trySimpleDestructuring`
([`minify.ts#L26-L63`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/minify.ts#L26-L63)).

## 4. Downstream Effects

None currently documented — Minify runs at Order 28, and no later stage (`AstScrambler`
29, `RenameVariables` 30, `Finalizer` 35, `Pack` 36) has been found to rewrite its output
in a way that matters. The relationship the other direction is the significant one: Minify
is itself late enough to rewrite several *earlier* transforms' output out from under a
matcher written against the un-minified shape — see
[control-flow-flattening.md](control-flow-flattening.md)'s Downstream Effects for the
three confirmed cases (while/for/with brace-stripping, computed-to-dot member rewrite,
`return undefined` → bare `return`).

## 5. Known Quirks

**Function-length preservation is not part of this transform, despite changelog/older-fork
association.** js-confuser's changelog and older forks' decoders associate "preserve
`function.length`" with Minify, but in the pinned source that mechanism has moved out of
`minify.ts` entirely — it's `PluginInstance.setFunctionLength`, a shared helper any
transform can call (currently `flatten.ts`, `rgf.ts`, and `variableMasking.ts` do, whenever
their own param-list rewrite would otherwise change a function's observable `.length`). See
[`set-function-length-template.md`](../templates/set-function-length-template.md) for that
mechanism; it is unrelated to and runs independently of whether `minify` is enabled.
