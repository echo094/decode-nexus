# setFunctionLengthTemplate.ts

Provides `SetFunctionLengthTemplate`: a small helper —
`function {fnName}(fn, length = 1){ Object.defineProperty(fn, "length", { value: length, configurable: false }); return fn; }`
— that overrides a function's `.length` property back to its original value.

Used by `me.setFunctionLength()` in
[plugin-api.md](../plugin-api.md): since many transforms
reshape a function's parameter list (rest params, stack objects, dispatcher wrapping,
...), calling code that introspects `fn.length` would otherwise observe a changed
value. Only inserted (once, lazily, shared across all call sites) when
`options.preserveFunctionLength` is enabled.
