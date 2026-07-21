# awsc.js

Target: **fireyejs / bx-ua** (the "225" algorithm — reference: a zhihu writeup on
Taobao's `bx-ua` login parameter). Not listed in the README. Unlike the other plugins it
does **no decryption, no string-array handling, and no sandbox** — it is purely a
*de-linter*: a fixed sequence of AST normalizations that turn the fireyejs VM's
expression-dense, comma/`&&`-driven code into ordinary statement-structured JavaScript so
it can be read.

Parse (plain `parse`, no `errorRecovery`), then traverse in this order, generate:

1. `RemoveVoid` (`UnaryExpression`) — `void x` → `x`.
2. `LintConditionalAssign` (`ConditionalExpression` exit) — pull an assignment into both
   arms: `a = t ? x : y` → `t ? a = x : a = y`.
3. `LintConditionalIf` — rewrite conditional-expression *statements* into `if/else`,
   recursing through `SequenceExpression`/`LogicalExpression` parents (`&&` only).
4. `LintLogicalIf` (`LogicalExpression` exit) — `a && b;` statement → `if (a) b;`.
5. `LintIfStatement` (exit) — wrap `if` branches in `BlockStatement`s (a private copy of
   the same logic as [lint-if-statement](../visitors/lint-if-statement.md), not the shared
   visitor).
6. `LintIfTest` (enter) — hoist a sequence out of an `if` test: `if ((a, b, c)) {}` →
   `a, b; if (c) {}`.
7. `LintSwitchCase` — wrap each `case` consequent in a block.
8. `LintReturn` — hoist a sequence out of `return`: `return (a, b, c)` → `a, b; return c`.
9. `LintSequence` (exit) — a `SequenceExpression` statement → a block of statements.
10. `LintBlock` (exit) — flatten nested blocks.

Everything here is structural; the decoded control flow is exposed by de-sequencing and
by turning short-circuit/ternary idioms into real branches. No env-unlock or global
decode stage exists in this plugin.
