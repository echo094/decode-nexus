# common.js

The default target (`-t common`, or no `-t`). Aimed at "high-frequency local
obfuscation" — no specific vendor, no string-array/global encryption, no sandbox. The
simplest plugin: parse once with `errorRecovery`, run four reusable visitors, generate.

Pipeline:

1. [delete-unreachable-code](../visitors/delete-unreachable-code.md) — drop statements
   after an unconditional return.
2. [delete-nested-blocks](../visitors/delete-nested-blocks.md) — flatten redundant nested
   blocks.
3. [calculate-constant-exp](../visitors/calculate-constant-exp.md) — fold literal
   binary/unary expressions.
4. [calculate-rstring](../visitors/calculate-rstring.md) — fold
   `"…".split("").reverse().join("")` chains.

Returns the generated code (default generator options). Because it neither unwraps an
`eval` packer nor drives the isolate, `common` is the right choice for lightly-obfuscated
snippets that just need constant folding and structural tidy-up.
