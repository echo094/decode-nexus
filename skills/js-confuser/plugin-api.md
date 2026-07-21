# Plugin API (`transforms/plugin.ts`)

Every transform module is a `PluginFunction`: `({ Plugin }) => PluginObject`. Calling
`Plugin(Order.X, mergeObject?)` — always aliased to `me` by convention — registers a
`PluginInstance` for that transform and returns the shared object every transform's
code interacts with. This file has no pipeline stage of its own; it's the scaffolding
every other file in `transforms/` is built on, referenced throughout this reference as
`me.*` and `{ph}`.

**`PluginObject`** — what a transform's factory returns:
- `visitor` — a Babel `Visitor`, passed to `traverse(ast, plugin.visitor)` for this
  transform's turn in the pipeline (see
  [Execution Flow](js-confuser.md#execution-flow-encoderjs-confusersrcobfuscatorts)).
- `post?()` — runs immediately after this transform's traversal finishes (e.g.
  ControlFlowFlattening uses it to flag every function it modified as `UNSAFE`, so later
  transforms in the same pass don't re-touch them).
- `finalASTHandler?(ast)` — instead of running now, queues a whole-AST rewrite for after
  *every* transform has traversed (Pack's `Function(objName, code)(...)` wrapping is the
  only consumer of this).

**`PluginInstance` (`me`)** — the API surface every transform is written against:
- `me.options` / `me.globalState` — proxy the user's `ObfuscateOptions` and the
  `Obfuscator`'s cross-transform shared state (renamed-variable map, lock/integrity
  internals) respectively.
- `me.computeProbabilityMap(map, ...args)` — the single gate almost every transform
  calls per-candidate-node to decide "should I transform *this* one," honoring the
  user's boolean / number / percentage / function / per-mode option value.
- `me.skip(path)` / `me.isSkipped(path)` — tags a node with this transform's `order` via
  a `SKIP` symbol, so the same transform (or a check elsewhere) can recognize a
  node it already produced and not reprocess it infinitely.
- `me.getPlaceholder(suffix?)` — mints a random long identifier (`__p_XXXX[_suffix]`),
  used everywhere in this reference as `{ph}` — every inserted helper function/variable
  starts with an intentionally ugly, collision-proof name that RenameVariables later
  mangles down to something short, so transforms never have to worry about colliding
  with user code or each other.
- `me.setFunctionLength(path, originalLength)` — since transforms routinely reshape a
  function's parameter list (rest params, stack objects, ...), this restores the
  original `fn.length` by wrapping/calling a lazily-inserted shared helper, gated behind
  `options.preserveFunctionLength`.
- `me.log()` / `me.warn()` / `me.error()` — verbose-gated logging and a throw helper,
  each automatically tagged with the transform's name (from `Order[order]`).
