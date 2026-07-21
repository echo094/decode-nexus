# object-utils.ts

One function: **`createObject(keys, values)`** — zips two parallel arrays into a
`{ [key]: value }` object, throwing on a length mismatch.

Its only consumer is `Obfuscator.prototype.computeProbabilityMap` in `obfuscator.ts` —
the runtime behind `me.computeProbabilityMap()` (see
[plugin-api.md](../plugin-api.md)). When a `ProbabilityMap`
option value is an array or weighted object, `computeProbabilityMap` normalizes it to
`{ mode: weight, ... }`, divides each weight by the total to get percentages via
`createObject(Object.keys(asObject), Object.values(asObject).map(x => x / total))`,
then picks a winner by drawing `Math.random()` against the cumulative percentages.
