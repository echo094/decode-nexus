# Calculator

Source: [`transforms/calculator.ts`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/calculator.ts) — `Order.Calculator = 9`.

## 1. Target

Hide simple arithmetic between literal operands behind an opaque dispatch call keyed by a
random per-operator string, so a static reader can't tell what operation two adjacent
literals actually combine with just by reading the source.

## 2. Algorithm

A single `Program: exit` visitor traverses every `BinaryExpression` in the whole program
and rewrites the narrow subset where **both operands are already numeric literals** and
the operator is one of `+ - * /`:

```js
// before
1 + 2

// after
{ph}_calc("aB3", 1, 2)
```

Every matched operator gets a random per-Program key, consistent throughout one Program
(`+` always maps to the same key, `-`/`*`/`/` each to their own). Once traversal finishes,
if at least one operator was used, a single dispatch function is prepended to the Program:

```js
function {ph}_calc(operator, a, b) {
  switch (operator) {
    case "aB3": return a + b;
    case "xY9": return a - b;
    // one case per distinct operator actually used
  }
}
```

## 3. Implementation

Guard conditions, in order
([`calculator.ts#L26-L58`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/calculator.ts#L26-L58)):
skip `t.isPrivate(left)` (private class fields), skip unless `right` is a
`NumericLiteral`, skip unless `left` is a `NumericLiteral`, skip unless `operator` is in
the allowed set. The source's own `TODO` comment
([`calculator.ts#L32`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/calculator.ts#L32))
flags this as deliberately conservative — no precedence/associativity handling, so it only
ever catches expressions where both sides are *already* literal, not general arithmetic
subexpressions.

Keys come from `NameGen`, keyed by `"binaryExpression_" + operator`. The dispatch function
([`calculator.ts#L67-L94`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/calculator.ts#L67-L94))
is one function per Program (not per-block like Dispatcher/StringConcealing), built
directly from `operatorsMap`'s insertion order, so the case count always equals the number
of *distinct* operators actually rewritten (1 to 4), never one case per call site. If
`operatorsMap.size < 1` (no qualifying `BinaryExpression` found anywhere in the Program),
the function is never inserted at all
([`calculator.ts#L62-L65`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/calculator.ts#L62-L65)).

## 4. Downstream Effects

- **`StringConcealing` (Order 17)** conceals *every* string literal in the program
  indifferently, including this transform's own operator-key strings — a switch case's
  test becomes a call like `__p_STR(262, 2)` instead of a bare string literal.
- **`DuplicateLiteralsRemoval` (Order 22)** can fold the operator-key string (and the
  numeric `a`/`b` call arguments, when they repeat elsewhere in the program too) into its
  own shared array, since the key appears at least twice by construction — once in the
  `switch` case test, once at each call site.
- **`RenameVariables` (Order 30)** can coincidentally assign the dispatch function and its
  own first parameter (`operator`) the identical new name, since it renames every binding
  independently — reproducible as `function S5tLFcy(S5tLFcy, a, b) { switch (S5tLFcy)
  {...} }`.

## 5. Known Quirks

None currently documented.
