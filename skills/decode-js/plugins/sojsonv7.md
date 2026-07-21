# sojsonv7.js

Target: **jsjiami.com.v7**. The most involved of the sojson family (~786 lines). Same
overall shape as [sojson](sojson.md) — isolate-run decrypt preamble, control-flow and
dead-code cleanup, readability, env-unlock — but the global-decode stage does full
version-variable / string-table / rotate-function discovery and a `dfs` over the decoder's
reference tree, and it adds a v7-specific switch-flattening reversal and a distinct set of
environment guards.

## Pipeline (default export)

1. `PluginEval.unpack` — peel an `eval()` packer if present (sets `global_eval`).
2. `parse(code, { errorRecovery: true })`, then
   [delete-illegal-return](../visitors/delete-illegal-return.md) and strip `node.extra`.
3. **`decodeGlobal`** ("处理全局加密") — see below. Aborts (returns `null`) on failure.
4. [parse-control-flow-storage](../visitors/parse-control-flow-storage.md)
   ("处理代码块加密").
5. **`cleanDeadCode`** — [calculate-constant-exp](../visitors/calculate-constant-exp.md),
   [prune-if-branch](../visitors/prune-if-branch.md),
   [remove-control-flow-ob](../visitors/remove-control-flow-ob.md), then **`cleanSwitchCode2`**
   (below).
6. Reparse; **`purifyCode`** — `purifyFunction` (2-param `a + b` concat helper inlining),
   `calculate-constant-exp`, `FormatMember`,
   [split-sequence](../visitors/split-sequence.md), drop `EmptyStatement`s,
   [delete-unused-var](../visitors/delete-unused-var.md); reparse again.
7. **`unlockEnv`** ("解除环境限制") — v7 guards (below).
8. Generate; `PluginEval.pack` if `global_eval`.

## Global decode (`decodeGlobal`)

More elaborate than sojson's fixed preamble:

- Split line 1 (version marker + string table) into separate declarations.
- Find the **version variable** — either a `VariableDeclaration`, or a `CallExpression`
  whose callee is a `FunctionDeclaration` assigning to `global.<version>` (duplicate
  definitions are emptied out).
- Classify every reference of the version var: the **string table** (an `ArrayExpression`
  with no inner `MemberExpression`), definitions, and left-hand assignments (deleted in
  place).
- Locate the string-table variable, the **rotate function** (found in a
  `SequenceExpression`; in newer versions wrapped in an empty `IfStatement`), and the
  **main decrypt wrapper**, assembling them into `decrypt_code` and running it in the
  isolate.
- **`dfs`** walks the decrypt wrapper's reference tree, handling four ref kinds:
  `VariableDeclarator` init, `AssignmentExpression` right (issue #165),
  `MemberExpression` object (`memToStr`), and `CallExpression` callee (`funToStr`).
  `getAssignmentRange` bounds a non-constant binding's references to the window before its
  first `constantViolation`.

## v7-specific cleanups

- **`cleanSwitchCode2`** (`ForStatement` exit) — the v7 flavor of switch-flattening: an
  empty `for (;;) { switch (arr[i++]) … break; }` whose order array is recovered by
  `evalOneTime` (a throwaway one-shot isolate) running the preceding declaration plus
  `arr.join('|')`. Cases are reassembled in order until a `continue`/`return`. Compare the
  `while`-based [remove-control-flow-ob](../visitors/remove-control-flow-ob.md).
- **`unlockEnv`** — four guards, all built on `removeUniqueCall` (removes a
  decorator-style self-invoking guard and its binding): **`unlockDebugger`** (a
  `DebuggerStatement` inside an infinite loop; `setInterval` or direct-call forms),
  **`unlockConsole`** (an array of ≥ 5 `console` method names), **`unlockLint`** (the
  newline-guard regex string `(((.+)+)+)+$`), and **`unlockDomainLock`** (an
  `ArrayExpression` matching the encoded allowed-domain byte arrays like
  `[7,116,5,101,3,117,0,100]`).
