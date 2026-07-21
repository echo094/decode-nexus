# parse-control-flow-storage.js

Reverses javascript-obfuscator's **FunctionControlFlowTransformer**, which routes
expressions through a "controlFlowStorage" object of tiny wrapper functions. This visitor
recognizes such an object and inlines every call site back to the original expression.

```javascript
// storage object
var _0xb28de8 = {
  "abcd": function (a, b) { return a == b; },   // BinaryExpression
  "dbca": function (f, x, y) { return f(x, y); }, // CallExpression (callee = first param)
  "aaa":  function (g) { return g(); },
  "bbb":  "eee",                                 // Literal
  "ccc":  A[x][y]                                // MemberExpression
};
// From                              // To
_0xb28de8["abcd"](123, 456);   -->   123 == 456;
_0xb28de8["dbca"](bcd, 11, 22); -->  bcd(11, 22);
_0xb28de8["bbb"];               -->  "eee";
```

Runs on `VariableDeclarator` **`exit`**. Each property must match one of: a
`FunctionExpression` with exactly one `return` of a `BinaryExpression`,
`LogicalExpression`, or `CallExpression` (the call's callee must be the function's first
param), a `StringLiteral`, or a `MemberExpression`. Every qualifying key gets a
`repfunc` that rebuilds the corresponding node from the call's arguments.

**Completeness gates:** if *no* property qualifies it bails; if only *some* qualify it
logs `不完整替换` (incomplete replacement) and bails — a partial match usually means it's an
ordinary object, not a storage object. Reference rewriting walks `referencePaths`
**in reverse** so nested `storage[k](storage[j](…))` calls resolve inner-first; a key
missing from `objKeys` is assumed dead code and skipped. The storage `VariableDeclarator`
is removed only if `usedCount` equals the reference count, otherwise it logs `不完整使用`
and is kept.

Behavior is pinned by `test/visitor/parse-control-flow-storage/`. Consumed by the
`obfuscator`, `sojson`, and `sojsonv7` plugins. Feeds on objects reassembled by
[merge-object.js](merge-object.md).
