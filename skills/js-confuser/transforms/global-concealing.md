# GlobalConcealing

Source: [`transforms/identifier/globalConcealing.ts`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/identifier/globalConcealing.ts#L35-L315) — `Order.GlobalConcealing = 12`.

## 1. Target

Hide every reference to a global identifier (`console`, `Math`, etc.) behind an opaque
lookup keyed by a random string, padded with 20-40 decoy cases of the identical shape so
real and fake mappings are indistinguishable by position or naming.

## 2. Algorithm

Every unbound global identifier reference (no local binding, no assignment/`for-in`/
`for-of` target use) becomes a `{ph}_getGlobal("mappingKey")` call. `{ph}_getGlobal` is
inserted once per program — a `switch` whose cases are all the identical shape
(`NameGen`-generated random string key → `return globalVar["realName"]`), real mappings
and decoys shuffled together so they're indistinguishable by position or naming:

```js
var {ph}_globalVar = {ph}_getGlobalVarFn();
function {ph}_getGlobalVarFn() { /* getGlobalTemplate.ts sniff, see string-concealing.md */ }
function {ph}_getGlobal(mapping) {
  switch (mapping) {
    case "randomKey1": return {ph}_globalVar["realName1"];
    // ...
    case "randomKey37": return {ph}_globalVar["console"];
    // ...
  }
}
```

`{ph}_globalVar` itself is the sniffed `globalThis`/`global`/`window`/`new
Function("return this")()` result, shared with [StringConcealing](string-concealing.md)'s
own `bufferToString` chain (same `getGlobalTemplate.ts` sniffer, compiled separately per
use site rather than shared as one function).

When `lock.tamperProtection` is on, every native call site this transform rewrites also
gets wrapped in a `{nativeFunctionName}(fn)` / `{nativeFunctionName}(obj, "prop")` guard
(see [Lock / Integrity](lock-integrity.md)) — e.g. `console.log(...)` becomes
`checkNative(getGlobal("console")["log"])(...)` instead of the plain
`getGlobal("console")["log"](...)`.

## 3. Implementation

Nothing beyond the algorithm above and the shared sniffer template
([string-concealing.md](string-concealing.md)) — the switch/decoy generation is a single
mechanism with no further sub-cases.

## 4. Downstream Effects

- **`StringConcealing` (Order 17)** can conceal this transform's own switch-case key
  strings and `realName` arguments, same as any other string literal in the program.
- **`RenameVariables` (Order 30)** could in principle coincidentally assign the switch
  function and its own parameter the identical new name — the same class of bug confirmed
  in [Calculator](calculator.md) — though not observed live for this transform: this
  transform's `Program: exit` handler prepends its three declarations
  (`globalVar`/sniffer/switch function) in a fixed order that happens to offer the
  sniffer's own name to `RenameVariables`'s "first free name" search before the switch
  function's, an artifact of the current `prepend` ordering rather than a documented
  guarantee.

## 5. Known Quirks

None currently documented.
