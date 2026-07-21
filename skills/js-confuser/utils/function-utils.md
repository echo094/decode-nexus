# function-utils.ts

Two small helpers used by several transforms that restructure functions:

- **`isVariableFunctionIdentifier(path)`** — true only when `path` is the sole
  argument of a call to `variableFunctionName`
  (`__JS_CONFUSER_VAR__(identifier)`, from
  [constants.ts](../constants.md)). This is the marker call
  [Preparation](../transforms/preparation.md) creates from `@js-confuser-var` comments;
  everywhere an identifier gets renamed or rewritten as a reference —
  [Dispatcher](../transforms/dispatcher.md), [Flatten](../transforms/flatten.md),
  [VariableMasking](../transforms/variable-masking.md),
  [RenameVariables](../transforms/rename-variables.md) — checks this first and skips
  the node if true, since it's a marker argument, not a real variable reference, and
  [RenameVariables](../transforms/rename-variables.md) resolves it separately to the
  real (possibly renamed) identifier name.
- **`computeFunctionLength(fnPath)`** — returns the function's original `.length`
  (count of leading simple/pattern parameters, stopping at the first default/rest
  parameter). Checks the `FN_LENGTH` symbol first (set by `me.setFunctionLength()`, see
  [plugin-api.md](../plugin-api.md)) so a function reshaped
  more than once doesn't lose its *original* length on the second pass. Called by
  [Dispatcher](../transforms/dispatcher.md), [Flatten](../transforms/flatten.md),
  [VariableMasking](../transforms/variable-masking.md), and [RGF](../transforms/rgf.md)
  before they rewrite a function's parameter list, so the original length can be
  restored via `me.setFunctionLength()` when `options.preserveFunctionLength` is on.
