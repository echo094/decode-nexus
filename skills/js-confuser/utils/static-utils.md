# static-utils.ts

One function: **`isStaticValue(node)`** — recursively determines whether an expression
is a compile-time-constant value: literals (string/number/boolean/null, excluding
directive literals), `-`/`+`/`!`/`~`/`void` unary expressions over a static operand,
binary/logical expressions with two static operands, ternaries with all three branches
static, and arrays/objects whose every element/property is static. Anything else
(identifiers, calls, member access, template literals, ...) is not static.

Its only consumer is
[MovedDeclarations](../transforms/moved-declarations.md), which checks
`isStaticValue(declaration.init)` to decide how safe a hoisted variable's initializer is
to relocate — a static initializer can be moved anywhere without changing what it
evaluates to, unlike one with side effects or a dependency on surrounding scope.
