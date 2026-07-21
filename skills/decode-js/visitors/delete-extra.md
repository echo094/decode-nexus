# delete-extra.js

A two-line visitor that deletes `node.extra` from every `StringLiteral` and
`NumericLiteral`, forcing `@babel/generator` to re-emit the value in canonical form
rather than the source's raw text: `0x10` → `16`, `"X"` → `"X"`. The result is
**not ASCII-safe** — it relies on the generator running with `jsescOption: { minimal:
true }` to keep output readable.

**Not wired in at this pin.** No plugin and no test imports this module; a repo-wide
grep for `delete-extra` finds only the file itself. The plugins that want this behavior
(e.g. `obfuscator`) inline the identical `StringLiteral`/`NumericLiteral` `delete
node.extra` visitor directly instead of importing here. Treat it as a standalone helper
kept for reuse, not part of any live pipeline.
