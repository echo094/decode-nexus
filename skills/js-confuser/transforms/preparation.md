# Preparation

Source: `transforms/preparation.ts`

Always runs first (order 0, unconditionally enabled) and isn't obfuscation itself — it
normalizes the parsed AST into a canonical shape the rest of the pipeline can rely on,
and tags nodes with the safety metadata later transforms gate on.

## AST normalization

- **Explicit identifiers:** non-computed member/property access becomes a computed
  string-keyed access — `object.foo` → `object["foo"]`, `{ foo: 1 }` → `{ "foo": 1 }`.
  This is what makes later string-literal transforms (StringConcealing, StringSplitting,
  DuplicateLiteralsRemoval) able to reach what were previously bare identifiers.
- **Explicit declarations:** `var a, b, c;` splits into `var a; var b; var c;` — required
  by VariableMasking/other single-declarator-only transforms.
- **Block-ify:** arrow function expression bodies, and the bodies of
  `if`/`for`/`for-in`/`for-of`/`while`/`with`, get wrapped in a `BlockStatement` if they
  aren't already one, so every later transform can assume a block exists to operate on.
- **Template literals → string concatenation:** `` `Hello ${name}` `` becomes
  `"Hello " + name` (binary `+` chain).
- **Regex literals → constructor calls:** `/foo/g` becomes `new RegExp("foo", "g")`.

## Safety metadata

- **`UNSAFE`:** a function (or the Program) is flagged `UNSAFE` if it directly contains
  `this`, `super`, `arguments`, or `eval`. Downstream transforms (ControlFlowFlattening,
  Dispatcher, Flatten, VariableMasking, RGF, ...) check this flag and skip functions that
  carry it, since rewriting them would change `this`-binding or the `arguments` object.
- **`PREDICTABLE`:** a `FunctionDeclaration` is flagged `PREDICTABLE` if every reference
  to it is a direct call (never passed around as a value, never called with
  `...spread`), and none of those calls exceeds its declared parameter count. This lets
  MovedDeclarations safely pack variables into extra parameters, and lets
  ControlFlowFlattening's generated `main` function assume a fixed argument shape.

## Internal escape hatch

A `@js-confuser-var "name"` leading comment on a string literal is rewritten to
`__JS_CONFUSER_VAR__(name)` — used internally by other transforms' generated code
templates to reference a variable name that RenameVariables will later substitute. If
RenameVariables is disabled, Preparation's own `ReferencedIdentifier` visitor unwraps
`__JS_CONFUSER_VAR__(name)` straight back to the literal string, since nothing downstream
will do it otherwise.

## Reversal

Not applicable — Preparation only normalizes syntax into equivalent forms (computed
member access, wrapped blocks, `RegExp` calls, string concatenation) that don't need
undoing for readability, and the `UNSAFE`/`PREDICTABLE` tags are internal bookkeeping
with no runtime trace in the emitted code.
