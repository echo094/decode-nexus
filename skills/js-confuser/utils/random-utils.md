# random-utils.ts

Base `Math.random()` primitives every other generator/transform in this reference is
built on top of — no seeding, no PRNG of its own, just thin wrappers:

- **`choice(choices)`** — one random array element. Backs
  [`NameGen`](name-gen.md)'s `"randomized"` mode character selection.
- **`chance(percentChance)`** — `true` with the given 0–100 probability. The gate behind
  most "sometimes do X" behavior: [ControlFlowFlattening](../transforms/control-flow-flattening.md)'s
  block shuffling/fake-test insertion,
  [OpaquePredicates](../transforms/opaque-predicates.md)' insertion depth falloff,
  [Dispatcher](../transforms/dispatcher.md)'s payload-shape randomization,
  [Lock](../transforms/lock-integrity.md)'s per-block custom-lock percentage,
  [StringConcealing](../transforms/string-concealing.md)'s per-string encoding choice.
- **`shuffle(array)`** — in-place Fisher–Yates shuffle. Used to randomize
  case/block order ([ControlFlowFlattening](../transforms/control-flow-flattening.md),
  [GlobalConcealing](../transforms/global-concealing.md)'s switch cases), the character
  table in [StringEncoding](../transforms/string-encoding.md)'s `encoding.ts`, and the
  zero-width identifier batches in [gen-utils.ts](gen-utils.md).
- **`getRandomHexString(length)`** — uppercase hex digits; backs
  [`NameGen`](name-gen.md)'s `"hexadecimal"` mode.
- **`getRandomChineseString(length)`** — random codepoints in the CJK Unified
  Ideographs range (`U+4E00`–`U+9FFF`); backs [`NameGen`](name-gen.md)'s `"chinese"`
  mode.
- **`getRandomString(length)`** — alphanumeric string. The generic "give me a random
  ASCII token" used well outside identifier generation:
  [`me.getPlaceholder()`](../plugin-api.md)'s `{ph}`
  suffix, `templates/template.ts`'s per-instance AST-identifier prefix,
  [Dispatcher](../transforms/dispatcher.md)'s payload key names,
  [GlobalConcealing](../transforms/global-concealing.md)'s fake case labels,
  [OpaquePredicates](../transforms/opaque-predicates.md)' decoy return values, and
  [StringConcealing](../transforms/string-concealing.md)'s junk padding between real
  strings.
- **`getRandom(min, max)`** / **`getRandomInteger(min, max)`** — uniform float/int in
  `[min, max)`. Used throughout for things that don't need uniqueness (unlike
  [IntGen](int-gen.md)), e.g. `NameGen`'s randomized-mode length.
- **`splitIntoChunks(str, size)`** — splits a string into fixed-size substrings (last
  chunk may be shorter). Used by
  [StringSplitting](../transforms/string-splitting.md) to break a string literal into
  concatenated pieces.
