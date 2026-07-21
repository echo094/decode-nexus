# RenameVariables

Source: `transforms/identifier/renameVariables.ts`

Upstream docs: [`docs/RenameVariables.md`](../../../encoder/js-confuser/docs/RenameVariables.md)

Two-pass, scope-aware renaming. First crawls every scope, recording which identifier
names are defined vs. merely referenced in each function/Program context. Then walks
scopes top-down, assigning each locally-defined name a new one from the shared
`NameGen` — reusing an already-generated name from a sibling or now-out-of-scope
context where safe, rather than always minting a fresh one, which keeps the total pool
of generated names smaller. Global bindings are only renamed if `options.renameGlobals`
allows it; exported identifiers and any name prefixed `__NO_JS_CONFUSER_RENAME__` are
always left alone.

This pass is also the primary place `__JS_CONFUSER_VAR__(x)` marker calls (see
[Preparation](preparation.md)) get resolved to their final string — since renaming is
what determines each marked variable's ultimate name, this transform swaps the marker
call for the resolved name directly rather than waiting for a later pass.

## Reversal

Purely cosmetic — mangled names carry no recoverable information. The only actionable
step is running a standard minifier/pretty-printer/renamer over the result, identical
to how any other transform's freshly-inserted identifiers get handled.
