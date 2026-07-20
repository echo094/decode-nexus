# Flatten

Source: `transforms/flatten.ts`

Not to be confused with [ControlFlowFlattening](control-flow-flattening.md) (a separate,
later, much larger transform) — `Flatten` runs early (order index 2) and works per
function: every outer-scope variable a function closes over gets replaced with a
`{ph}_flat_object` property access (`get`/`set` methods, or a `method` wrapper for
identifiers that are only ever called or only ever used with `typeof`). The function body
is then moved into a new top-level `{ph}_flat_{name}(flatObject, argsArray)` declaration,
and the original function is reduced to:

```js
function original(...{ph}_args) {
  var {ph}_flat_object = { get x() {...}, set x(v) {...}, ... };
  return {ph}_flat_{name}({ph}_flat_object, {ph}_args);
}
```

This severs the lexical closure — the extracted function no longer directly references
outer variables, only the passed-in accessor object.

## Reversal

Inline the extracted `{ph}_flat_{name}` function body back into the original function,
replacing every `{ph}_flat_object.prop` access with the original outer-scope identifier
name (recoverable from the getter/setter/method bodies, which just proxy to the real
name). Once inlined, the wrapper function and the flat-object literal are dead and can be
removed.
