# delete-illegal-return.js

Removes any `ReturnStatement` that has no `getFunctionParent()` — i.e. a `return` at
Program scope, which is illegal JavaScript. Obfuscated payloads that were sliced out of
a wrapping function (or parsed with `errorRecovery`) can leave such a stray top-level
return; dropping it lets the rest of the pipeline parse and traverse cleanly.

Run early, before statement-splitting passes. Consumed by the `obfuscator` and
`sojsonv7` plugins.
