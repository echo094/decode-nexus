# delete-unused-var.js

Prunes a `VariableDeclarator` whose binding is unreferenced. Guards, all required:

- the binding exists, is **not `referenced`**, and is **`constant`** (never reassigned);
- `init` is absent or a **`Literal`** — so an initializer with potential side effects
  (a call, etc.) is never dropped;
- the declarator is not the head of a `ForOfStatement` / `ForInStatement` (checked two
  parents up), which must keep their loop variable.

Removes the whole `VariableDeclaration` when it holds a single declarator, otherwise just
the one declarator, then re-crawls scope. Logs `Unused variable: <name>`. Consumed by the
`sojson`, `obfuscator`, and `sojsonv7` plugins.
