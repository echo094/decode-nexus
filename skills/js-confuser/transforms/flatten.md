# Flatten

Source: [transforms/flatten.ts](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/flatten.ts)

Not to be confused with [ControlFlowFlattening](control-flow-flattening.md) (a separate,
later, much larger transform) — `Flatten` runs early (`Order.Flatten = 2`) and works
per function.

## 1. Target

Sever the lexical link between a function and the outer-scope variables it closes over:
replace direct references with property accesses on a passed-in accessor object, and move
the function body itself out of its original lexical position — so neither closure
analysis nor a naive text scan can trace which outer variables a given function actually
touches.

## 2. Algorithm

Every outer-scope variable a function closes over gets replaced with a `{ph}_flat_object`
property access (`get`/`set` methods, or a `method` wrapper for identifiers that are only
ever called or only ever used with `typeof`). The function body is then moved into a new
top-level `{ph}_flat_{name}(flatObject, argsArray)` declaration, and the original function
is reduced to a thin wrapper:

```js
function original(...{ph}_args) {
  var {ph}_flat_object = { get x() {...}, set x(v) {...}, ... };
  return {ph}_flat_{name}({ph}_flat_object, {ph}_args);
}
```

## 3. Implementation

The accessor object's shape tags how each original reference was used:

| original use | object property shape |
|---|---|
| plain read | `get "k"(){ return outer }` |
| plain write (paired with the getter) | `set "k"(v){ outer = v }` |
| `typeof outer` | `get "k"(){ return typeof outer }` |
| `outer(...)` direct call | `"k"(...a){ return outer(...a) }` |

## 4. Downstream Effects

- **`RenameVariables` (Order 30)** assigns a name to every binding independently, so it can
  hand the identical string to both an outer free variable this transform's accessor
  object proxies and one of the extracted function's own params — the two are unrelated
  bindings that happen to share text after renaming.

## 5. Known Quirks

**A function nothing calls is still severed, and the halves then meet different fates.** The
transform does not check whether its target is reachable, so an uncalled source function gets
the same treatment as a live one: an extracted `{ph}_flat_{name}(flatObject, argsArray)`
declaration plus a thin wrapper holding the accessor object. The wrapper is the only thing
that ever referenced the extracted body *and* the only thing carrying the accessor object, so
once a later pass removes it as unreachable, what remains is an extracted body addressing
property keys that are now defined nowhere in the program.

Observed under `preset: 'high'` on a source whose function is declared and never called: the
extracted body survives (further wrapped by Dispatcher into an entry nothing dispatches),
while **no `get`/`set` accessor object remains anywhere in the emitted program** — verified
structurally, zero `ObjectMethod`s of any kind across three such samples. A minimal
`{ flatten: true }` encode of the same source emits the accessor object in full, so the
elimination is downstream of this transform rather than a case it declines.

The quirk is descriptive, not a defect: the program is semantically unchanged, since the
orphaned body is unreachable too. It is recorded because the surviving half *looks* like an
incompletely-processed application when read on its own, and the key-to-variable mapping that
would explain it is genuinely absent rather than merely concealed.
