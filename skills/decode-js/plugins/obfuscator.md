# obfuscator.js

Target: **javascript-obfuscator / obfuscator.io**. The largest and fullest plugin,
integrating ideas from `cilame/v_jstools` and `Cqxstevexw/decodeObfuscator`. It
is the canonical example of the [sandbox-assisted partial
evaluation](../decode-js.md#babel--isolated-vm-foundation) technique: it extracts the
obfuscator's own string-array + decoder functions, runs them in an `isolated-vm` isolate
(`virtualGlobalEval`), and substitutes evaluated results back into the AST.

## Pipeline (default export)

1. `PluginEval.unpack` — peel an `eval()` packer if present (see [eval](eval.md)); sets
   `global_eval` so `pack` re-wraps at the end.
2. `parse(code, { errorRecovery: true })`.
3. [delete-illegal-return](../visitors/delete-illegal-return.md),
   [lint-if-statement](../visitors/lint-if-statement.md),
   [split-variable-declaration](../visitors/split-variable-declaration.md), then strip
   `node.extra` from string/number literals (inline visitor).
4. **`decodeObject`** ("还原数值") — fold a `var o = { k: <literal> }` that is only ever read
   as `o.k` (non-computed): inline each literal at its use and remove the object.
5. **`decodeGlobal`** ("处理全局加密") — the string-array decoder; see below. Returns `false`
   (aborting the whole plugin) if no string array is found.
6. **`purifyCode`** ("提高代码可读性") — readability pass: `lintIfStatement`,
   [prune-if-branch](../visitors/prune-if-branch.md), normalize `for`/`while` bodies to
   blocks, drop `EmptyStatement`s, [split-assignment](../visitors/split-assignment.md),
   [delete-unused-var](../visitors/delete-unused-var.md), `FormatMember`
   (`o["ab"]` → `o.ab`), method/property key de-computing and string→identifier, and
   [split-sequence](../visitors/split-sequence.md).
7. **`stringArrayLite`** — inline a constant literal array read only by numeric index.
8. **`decodeCodeBlock`** ("处理代码块加密") —
   [calculate-constant-exp](../visitors/calculate-constant-exp.md),
   [merge-object](../visitors/merge-object.md),
   [parse-control-flow-storage](../visitors/parse-control-flow-storage.md),
   `calculate-constant-exp` again.
9. **`cleanDeadCode`** — `calculate-constant-exp`, `prune-if-branch`,
   [remove-control-flow-ob](../visitors/remove-control-flow-ob.md).
10. Reparse the generated code (refresh bindings), run `purifyCode` again.
11. **`unlockEnv`** ("解除环境限制") — strip anti-tamper traps (below).
12. Generate; `PluginEval.pack` if `global_eval`.

## String-array detection (`decodeGlobal`)

Tries three detectors in order, newest first, until one returns a `stringArrayName`:

- **`stringArrayV3`** (obfuscator **≥ 2.19.0**) — the string array lives inside a
  wrapper function `function aaa(){ const bbb=[…]; aaa=function(){return bbb}; return
  aaa() }`, matched with a `checkPattern` fingerprint. References are classified into
  `func2` (the rotate call) and `func3` (calls-wrapper functions).
- **`stringArrayV2`** (**< 2.19.0**, single array) — locate the **rotate function** by
  fingerprint (`fp1` for ≥ 2.10.0, `fp2` for < 2.10.0), then handle the
  calls-wrapper across four sub-version shapes (`2.12.0 ≤ v < 2.15.4`, `v < 2.12.0`,
  `2.15.4 ≤ v < 2.19.0`).
- **`stringArrayV0`** — no rotate function present; the array can only be confirmed via
  the StringArrayCallsWrapper.

The detected function sources are `virtualGlobalEval`'d into the isolate, then **`dfs`**
walks each decoder's `referencePaths`: a call that evaluates to a string is replaced with
`t.StringLiteral`; a call that throws is treated as a *chained/nested* decoder and
recursed into, accumulating parent definitions first. Four chained-call reference kinds
are handled: `VariableDeclarator` and `FunctionDeclaration` (original), plus
`AssignmentExpression` (issue #50) and `FunctionExpression` (issue #94).

## Anti-tamper removal (`unlockEnv`)

Three fingerprint-matched (`checkPattern`) visitors, each removing both the guard and its
call-func binding:

- **`deleteSelfDefendingCode`** — the self-defending formatter guard (`this`, function
  expr; patterns `@7920538`, `@7135b09`, `#94`).
- **`deleteDebugProtectionCode`** — the `debugger` infinite-loop protection, including its
  `setInterval` variants (`@e8e92c6`, `@51523c0`) and call form, with `#95` exceptions.
- **`deleteConsoleOutputCode`** — the console-disabling guard.

The header comment warns `unlockEnv` "may mistakenly delete some code" and can be disabled.
