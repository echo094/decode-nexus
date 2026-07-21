# gen-utils.ts

Two generator helpers, both consumed only by [NameGen.ts](name-gen.md):

- **`alphabeticalGenerator(index)`** — converts a 1-based counter into a base-26
  letter sequence (`1` → `a`, `2` → `b`, ... `26` → `z`, `27` → `aa`, ...), used by the
  `"mangled"` identifier mode. Skipped/re-requested by the caller whenever the result
  collides with a `reservedKeywords` entry.
- **`createZeroWidthGenerator()`** — backs the `"zeroWidth"` identifier mode. Returns a
  `{ generate() }` object that, per call, pads each `reservedKeywords` entry with
  `U+200C` (zero-width non-joiner) characters up to a growing target length, filters to
  exactly that length, shuffles the batch ([`shuffle`](random-utils.md)), and pops one
  name at a time — once a batch is exhausted the target length grows and a new batch is
  generated. The result renders as invisible whitespace in most editors/terminals while
  still being a syntactically distinct identifier (a real keyword with trailing
  zero-width joiners appended).
