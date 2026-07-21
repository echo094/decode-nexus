# Constants (`constants.ts`)

Every "flag" other sections and transform docs in this reference refer to comes from
here — a fixed set of `Symbol()`s attached to AST nodes as out-of-band metadata (merged
onto `t.Node` via the `NodeSymbol` interface), plus a handful of shared string
constants.

| Symbol | Meaning |
|---|---|
| `UNSAFE` | function uses `this`/`super`/`arguments`/`eval` — set by [Preparation](transforms/preparation.md), read by nearly every later transform to skip functions it can't safely rewrite |
| `PREDICTABLE` | function's call sites are all direct calls with a known, non-spread argument count — set by [Preparation](transforms/preparation.md), read by MovedDeclarations and ControlFlowFlattening |
| `SKIP` | this node was already produced/claimed by the plugin at this `order` value — set via `me.skip()`, checked via `me.isSkipped()`, both in [plugin-api.md](plugin-api.md) |
| `FN_LENGTH` | the function's original `.length`, saved by `me.setFunctionLength()` before a transform reshapes its parameters |
| `NO_RENAME` | this identifier must not be touched by RenameVariables (ControlFlowFlattening uses it to protect its own generated discriminant expression) |
| `GEN_NODE` | this identifier was synthesized to represent a hex/unicode-escaped literal (Finalizer, StringEncoding) or an already-generated Pack replacement, not a real variable reference |
| `MULTI_TRANSFORM` | rewriting this inserted code again would likely blow the call stack (e.g. the native-function check) — left alone by subsequent passes |
| `WITH_STATEMENT` | node belongs to (or is) a `with`-statement construct from ControlFlowFlattening's scope emulation — tells [Pack](transforms/pack.md) and RenameVariables not to touch it |
| `NO_REMOVE` | tells Minify not to strip this node even though it looks unused (e.g. StringConcealing's decoder helpers) |

And the shared string constants:

- **`variableFunctionName`** (`"__JS_CONFUSER_VAR__"`) — the internal marker function
  name [Preparation](transforms/preparation.md) creates from `@js-confuser-var`
  comments, which [RenameVariables](transforms/rename-variables.md) resolves to a real
  (possibly renamed) identifier name.
- **`noRenameVariablePrefix`** (`"__NO_JS_CONFUSER_RENAME__"`) — any identifier
  starting with this is skipped by RenameVariables.
- **`placeholderVariablePrefix`** (`"__p_"`) — the prefix every `me.getPlaceholder()`
  name starts with; referred to as `{ph}` throughout this reference.
- **`reservedIdentifiers`**, **`reservedNodeModuleIdentifiers`**,
  **`reservedObjectPrototype`**, **`reservedKeywords`** — allow-lists checked by
  various transforms (GlobalConcealing, Pack, RenameVariables' zero-width name
  generator, ...) to avoid colliding with names that carry special meaning.
