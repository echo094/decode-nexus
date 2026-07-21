# sojson.js

Target: **sojson** (jsjiami), older versions. Adapted from `babel_asttool.js`. Uses the
`isolated-vm` isolate to run the payload's own decrypt routine, but the global-decode
stage is much simpler than [obfuscator](obfuscator.md)'s — sojson emits a fixed
three-statement decrypt preamble rather than a version-tagged string array.

## Pipeline (default export)

1. `PluginEval.unpack` — peel an `eval()` packer if present (sets `global_eval`).
2. `parse(code)` (no `errorRecovery`), then strip `node.extra` from string/number
   literals.
3. **`decodeGlobal`** ("处理全局加密") — see below. Aborts (returns `null`) on failure.
4. [parse-control-flow-storage](../visitors/parse-control-flow-storage.md)
   ("处理代码块加密").
5. **`cleanDeadCode`** — [calculate-constant-exp](../visitors/calculate-constant-exp.md),
   [prune-if-branch](../visitors/prune-if-branch.md),
   [remove-control-flow-ob](../visitors/remove-control-flow-ob.md).
6. Reparse (refresh bindings).
7. **`purifyCode`** ("提高代码可读性") — `purifyFunction` (below), `calculate-constant-exp`,
   `FormatMember` (`o["ab"]` → `o.ab`), [split-sequence](../visitors/split-sequence.md),
   drop `EmptyStatement`s, [delete-unused-var](../visitors/delete-unused-var.md).
8. **`unlockEnv`** ("解除环境限制") — anti-tamper + version-nag removal (below).
9. Generate; `PluginEval.pack` if `global_eval`.

## Global decode (`decodeGlobal`)

Removes `EmptyStatement`s, then requires **≥ 3** non-empty statements. The first three are
the decrypt preamble — `[signature/version declaration, preprocessing function, decrypt
function]` (the decrypt function may be at index 1 or 2). It reads `decrypt_val` (the
decrypt function/variable name), runs the three preamble statements in the isolate via
`virtualGlobalEval`, then over the remaining content statements evaluates and inlines
every reference to it:

- **`funToStr`** — `CallExpression` whose callee is `decrypt_val` → `virtualGlobalEval`
  the call string → `t.valueToNode(value)`.
- **`memToStr`** — `MemberExpression` whose object is `decrypt_val` → same.

## Purify & env-unlock specifics

- **`purifyFunction`** — a string-concat helper `A = function () { return … + … }` has its
  calls `A(a, b)` rewritten to `a + b`, then `A` is removed ("拼接类函数").
- **`unlockEnv`** runs four fingerprint (`checkPattern`) visitors:
  **`deleteSelfDefendingCode`** (the RegExp `е` formatting trap, whose failure causes
  an infinite call stack), **`deleteDebugProtectionCode`** (v5 inserts `debugger`
  directly, v6 via a doubled `Function` constructor), **`deleteConsoleOutputCode`**
  (matched by `window|process|require|global` + the `console` method list), and
  **`deleteVersionCheck`** — removes the periodic version-nag popup by matching its exact
  Chinese message string.
