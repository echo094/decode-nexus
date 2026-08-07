# StringSplitting

Source: `transforms/string/stringSplitting.ts` — `Order.StringSplitting = 16`.

## 1. Target

Break a string literal into randomly-sized chunks joined by `+`, so a static reader (or a
naive string-scanning tool) doesn't see the original string as one contiguous literal.

## 2. Algorithm

A single `StringLiteral` is rewritten into a chain of `+` `BinaryExpression`s over
string-literal chunks, random chunk sizes: `"hello"` → `"he" + "ll" + "" + "o"`.

## 3. Implementation

Nothing beyond the algorithm above — this is a genuinely small transform.

## 4. Downstream Effects

None currently documented.

## 5. Known Quirks

None currently documented.
