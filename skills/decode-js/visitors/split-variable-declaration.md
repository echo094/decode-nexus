# split-variable-declaration.js

Splits a multi-declarator `VariableDeclaration` (`var a, b, c`) into one declaration per
declarator (`var a; var b; var c`), preserving `kind`. Runs only when the declaration's
container is an array (`listKey`) and its parent is **not** a `for` head (whose scope is
its body). No-ops on single-declarator declarations.

Implementation `insertBefore`s a fresh `t.variableDeclaration(kind, [item])` for each
declarator, removes the original, and re-crawls scope. Consumed by the `obfuscator`
plugin, run early "to avoid bugs" before later splitting/renaming passes. Distinct from
[split-variable-declarator.js](split-variable-declarator.md), which splits a single
declarator whose `init` is a sequence.
