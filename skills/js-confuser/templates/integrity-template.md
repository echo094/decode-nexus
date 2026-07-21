# integrityTemplate.ts

Provides `HashFunction` (and its inserted-code twin `HashTemplate`): the `cyrb53` string
hash — `h1`/`h2` accumulators mixed with `Math.imul` (an ES5 polyfill is inlined for
environments without it), seeded, folded together into one number. Used to hash a
function's stringified source (`fn.toString()`, run through a `sensitivityRegex` first
to strip whitespace/punctuation so formatting changes don't trip the check) against a
value computed at obfuscation time.

Used by [Lock / Integrity](../transforms/lock-integrity.md)'s per-function tamper
detection: at call time, the function re-hashes its own source and compares against the
expected value baked in at build time, branching to `countermeasures()` on mismatch.
