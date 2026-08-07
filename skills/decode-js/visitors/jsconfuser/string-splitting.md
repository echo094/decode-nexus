# jsconfuser/string-splitting.js — no dedicated decoder file needed

## 1. Target

Reverse js-confuser's [StringSplitting](../../../js-confuser/transforms/string-splitting.md).
No `decoder/decode-js/src/visitor/jsconfuser/string-splitting.js` file exists — none is
needed.

## 2. Algorithm

`stringSplitting.ts` rewrites a single `StringLiteral` into a chain of `+`
`BinaryExpression`s over string-literal chunks. Reversing it is exactly constant-folding a
binary `+` over string literals, already handled unconditionally, program-wide, by the
shared [`calculate-constant-exp.js`](../calculate-constant-exp.md)'s `BinaryExpression`
visitor (`calculateBinaryExpression`), which every jsconfuser decode pass already runs
several times over for other transforms' own literal cleanup. No jsconfuser-specific
matching logic is needed or written.

**Provably safe under `RenameVariables`, not just empirically.** None of
`calculate-constant-exp.js`'s three visitors (`BinaryExpression`, `UnaryExpression`,
`LogicalExpression`) ever read an `Identifier`'s `.name` at all — they only pattern-match
literal/unary/logical node shapes. That's a stronger guarantee than the structural-only
clears recorded for other jsconfuser transforms (e.g. [dead-code.md](dead-code.md),
[lock.md](lock.md)): there is no name-based matching here at all for a coincidental
`RenameVariables` collision to exploit in the first place. Confirmed empirically too — a
sample where `RenameVariables` coincidentally renamed a function and its own parameter to
the identical identifier (the same collision shape that broke
[calculator.js](calculator.md) and required hardening
[global-concealing.js](global-concealing.md)) still folded every split-string chunk chain
back to a single literal with zero residue, since the fold never inspects that name.

## 3. Implementation

Nothing jsconfuser-specific — see `calculate-constant-exp.md` for the shared fold's own
mechanics.

## 4. Upstream Effects

The fold itself is generic, but its *input* is manufactured by two earlier jsconfuser
passes, and on a real `high` sample nothing folds until both have run. Both are properties
of where the shared pass is **slotted for this plugin**, not of the fold's own matcher,
which is why they are recorded here rather than in
[`calculate-constant-exp.md`](../calculate-constant-exp.md) — that pass serves every plugin
family and this ordering is jsconfuser's.

- **[StringConcealing](string-concealing.md)** — a concealed chunk is a call to the
  encoder's lookup helper, not a `StringLiteral`, and `calculateBinaryExpression` folds
  literal operands only. The plugin runs this fold after StringConcealing's visit for
  exactly this reason.
- **[Calculator](calculator.md)** — a `+` rewritten to the `{ph}_calc(operator, a, b)`
  dispatch call is a `CallExpression`, so there is no `BinaryExpression` for the fold to
  visit until Calculator has unwrapped it back. Calculator occupies the slot directly above
  this one, and its own doc has why that pairing is forced.

Neither is a gate this transform can fail closed on — with either upstream pass declining,
the chain is simply left un-folded, indistinguishable from a program that never had a split
string in it.

## 5. Known Gaps

None currently open.

## Source

No dedicated visitor file. Covered by
[`calculate-constant-exp.js`](../calculate-constant-exp.md), wired into
[plugin/jsconfuser.js](../../plugins/jsconfuser.md).

## Fixtures

`test/jsconfuser/rename-variables/string-splitting.{js,fix.js,src.js}` — the fold with and
without `renameVariables`, which is what item 2's safety claim rests on.
