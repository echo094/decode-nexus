# IntGen.ts

`IntGen` is the numeric twin of [NameGen](name-gen.md): generates unique random
integers instead of unique random names. Constructor takes `(min = -250, max = 250)`.

`generate()` loops `Math.random()`-based integers in `[min, max]` until one isn't
already in `generatedInts`, then records and returns it. If the generated-set size
reaches 80% of the current range, both bounds expand by 100 before the next attempt —
so a caller that keeps generating past the initial range doesn't spin forever looking
for an unused value.

The only consumer is
[ControlFlowFlattening](../transforms/control-flow-flattening.md)'s `stateIntGen =
new IntGen(-999, 999)` — mints the unique numeric discriminant values
(`this.totalState`, per-block state-transition targets) that drive each flattened
function's dispatch `switch`.
