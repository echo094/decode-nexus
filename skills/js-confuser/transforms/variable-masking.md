# VariableMasking

Source: `transforms/variableMasking.ts`

Rewrites a function's local `var`/`let` bindings (plus params) into indices/keys on a
single rest-param "stack" object: `function f(...{ph}_varMask){ {ph}_varMask[0] ... }`.
Skips `this`-using, strict-mode, async/generator functions.

## Reversal

Per function, build the index/key→original-binding map from initial param assignment,
then rewrite every `stack[k]` access back to the named variable (symbolic execution /
constant-tracking, since keys can be numeric, negative, or mangled strings).
