# Preparation

Source: [`transforms/preparation.ts`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/preparation.ts) — `Order.Preparation = 0`.

## 1. Target

Not obfuscation itself: always runs first, unconditionally enabled, and normalizes the
parsed AST into one canonical shape the rest of the pipeline can rely on, plus tags nodes
with the safety metadata later transforms gate on.

## 2. Algorithm

Three independent jobs in one visitor object:

- **AST normalization** — five syntax-level rewrites to equivalent forms (computed member
  access, split declarations, block-wrapped statement bodies, string concatenation,
  `RegExp` constructor calls) that give every later transform one predictable shape to
  match against instead of several.
- **Safety metadata** — tags a function (or the Program) `UNSAFE` when rewriting it would
  change observable behavior (`this`-binding, `arguments`), and tags a
  `FunctionDeclaration` `PREDICTABLE` when every call site's argument count is knowable
  ahead of time. Both are read-only signals later transforms check; neither has any
  runtime trace in the emitted code.
- **`@js-confuser-var` escape hatch** — a macro any source file can use to reference a
  variable name that `RenameVariables` will later substitute, with its own immediate
  fallback for when `RenameVariables` is disabled.

## 3. Implementation

**Normalization:**

- **Explicit member/property access**
  ([`preparation.ts#L222-L245`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/preparation.ts#L222-L245)):
  non-computed member/property access becomes a computed string-keyed access —
  `object.foo` → `object["foo"]`, `{ foo: 1 }` → `{ "foo": 1 }` (a class's own
  `constructor` key and private properties are left alone). This is what makes later
  string-literal transforms (StringConcealing, StringSplitting, DuplicateLiteralsRemoval)
  able to reach what were previously bare identifiers.
- **Explicit declarations**
  ([`preparation.ts#L250-L305`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/preparation.ts#L250-L305)):
  `var a, b, c;` splits into `var a; var b; var c;` (a `for (var i = 0, j = 1;;)` init gets
  the same split, hoisted before the loop) — required by VariableMasking/other
  single-declarator-only transforms.
- **Block-ify**
  ([`preparation.ts#L307-L352`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/preparation.ts#L307-L352)):
  arrow function expression bodies, and the bodies of
  `if`/`for`/`for-in`/`for-of`/`while`/`with`, get wrapped in a `BlockStatement` if they
  aren't already one, so every later transform can assume a block exists to operate on.
- **Template literals → string concatenation**
  ([`preparation.ts#L96-L129`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/preparation.ts#L96-L129)):
  `` `Hello ${name}` `` becomes `"Hello " + name` (binary `+` chain). A **tagged** template
  literal (`` tag`...` ``) is left completely untouched — the rewrite would change which
  function receives the raw/cooked parts, so it's skipped outright rather than
  approximated.
- **Regex literals → constructor calls**
  ([`preparation.ts#L135-L152`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/preparation.ts#L135-L152)):
  `/foo/g` becomes `new RegExp("foo", "g")`.

**Safety metadata:**

- **`UNSAFE`**
  ([`preparation.ts#L38-L47`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/preparation.ts#L38-L47),
  [`#L51-L62`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/preparation.ts#L51-L62)):
  a function (or the Program) is flagged `UNSAFE` if it directly contains `this`,
  `super`, `arguments`, or `eval`. Downstream transforms (ControlFlowFlattening,
  Dispatcher, Flatten, VariableMasking, RGF, ...) check this flag and skip functions that
  carry it, since rewriting them would change `this`-binding or the `arguments` object.
- **`PREDICTABLE`**
  ([`preparation.ts#L180-L217`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/preparation.ts#L180-L217)):
  a `FunctionDeclaration` is flagged `PREDICTABLE` if every reference to it is a direct
  call (never passed around as a value, never called with `...spread`), and none of those
  calls exceeds its declared parameter count. This lets MovedDeclarations safely pack
  variables into extra parameters, and lets ControlFlowFlattening's generated `main`
  function assume a fixed argument shape.
  - **This definition scopes what *Preparation* marks, not the flag's population.**
    `PREDICTABLE` is a node symbol, so any transform that emits a function can set it on
    what it generates, and a transform that rewrites one can clear it: Dispatcher marks its
    own `fns` entries
    ([`dispatcher.ts#L361`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/dispatcher.ts#L361)),
    ControlFlowFlattening its generated `main`
    ([`controlFlowFlattening.ts#L1721`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/controlFlowFlattening.ts#L1721)),
    while RGF
    ([`rgf.ts#L282`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/rgf.ts#L282))
    and VariableMasking
    ([`variableMasking.ts#L232`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/variableMasking.ts#L232))
    clear it. So a later stage's `PREDICTABLE` check is not answered by this definition
    alone, and in particular the "named `FunctionDeclaration` only" scope here does **not**
    bound which functions carry the flag at that stage — an anonymous `FunctionExpression`
    can carry it, having been marked by whichever transform emitted it.

**`@js-confuser-var` escape hatch:** a `@js-confuser-var "name"` leading comment on a
string literal is rewritten to `__JS_CONFUSER_VAR__(name)`
([`preparation.ts#L64-L91`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/preparation.ts#L64-L91)) —
a source-level convenience for the same `__JS_CONFUSER_VAR__(identifier)` marker call
other transforms' own generated-code templates write directly (no comment involved,
`variableFunctionName`,
[`constants.ts#L79`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/constants.ts#L79)),
normally resolved to a real identifier name by `RenameVariables` (Order 30) wherever it
appears. If `RenameVariables` is disabled, nothing downstream will ever resolve a marker
call inserted *after* this point — but one created from a `@js-confuser-var` comment
**existing in the source already** is created and consumed within this same traversal, so
Preparation's own `ReferencedIdentifier` visitor
([`preparation.ts#L154-L177`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/preparation.ts#L154-L177))
unwraps it straight back to the literal string immediately, rather than leaving it for
later. Every *other* transform's own later-inserted marker calls are instead cleaned up by
[Finalizer](finalizer.md)'s identical fallback, since it's the last stage that could still
catch them.

## 4. Downstream Effects

None currently documented — Preparation runs first (Order 0), so by definition every later
stage's Downstream Effects entries are about what happens *to* Preparation's output, not
what Preparation does to a later stage's.

## 5. Known Quirks

None currently documented.
