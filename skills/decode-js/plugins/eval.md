# eval.js

A shared helper, **not a `-t` dispatch target**. Exports `unpack` / `pack`, used by the
`obfuscator`, `sojson`, and `sojsonv7` plugins to peel an `eval(...)` self-executing
wrapper before decoding and restore it afterward.

- **`unpack(code)`** — parses `code` (with `errorRecovery`) and requires the program body
  (ignoring `EmptyStatement`s) to be exactly one statement of the shape
  `eval(<CallExpression>)`. When it matches, it generates the inner call's source and runs
  it through the **host `eval`**, returning the unwrapped source string the call produces
  (the classic `eval(function(p,a,c,k,e,d){…}(…))` packer emits the real program as that
  call's return value). Any other shape returns `null`.
- **`pack(code)`** — the inverse: parses a `(function(){}())` template, replaces the empty
  function's body with `code`'s statements, and returns the generated (non-minified)
  source. Consumers call this only when `unpack` originally succeeded (tracked by a
  `global_eval` flag), so the output keeps the same wrapper the input had.

Note this is the one place decode-js runs untrusted input through the **host** `eval`
rather than the `isolated-vm` sandbox — it executes the packer wrapper directly. The
per-string decoding inside the plugins uses the isolate instead (see
[decode-js.md](../decode-js.md) → Sandbox-assisted partial evaluation).
