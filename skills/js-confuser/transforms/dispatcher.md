# Dispatcher

Source: `transforms/dispatcher.ts`

Top-level function declarations get merged into one `{ph}_dispatcher(name, flagArg,
returnTypeArg, fnLengths)` closure holding an object of `{newName: functionExpression}`;
call sites become `{ph}_dispatcher("newName")(...)` or, for non-call references, a cached
wrapper fetched via a `nonCall` flag. ~50% of call sites are further wrapped so the
dispatcher call itself looks like `new Dispatcher(...)["prop"]` instead of a direct call.

## Reversal

Parse the `fns` object literal in the dispatcher body, map `newName` back to original
function name via the call-site string args, inline/rename accordingly.
