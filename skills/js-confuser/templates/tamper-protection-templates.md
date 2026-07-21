# tamperProtectionTemplates.ts

Four related helpers, all consumed by [Lock / Integrity](../transforms/lock-integrity.md)
under `lock.tamperProtection`:

- **`StrictModeTemplate`** — detects strict mode via `delete arr["length"]`, which
  throws only in strict mode; if triggered, runs countermeasures and clears the
  native-function-check name (Tamper Protection requires non-strict mode, since it
  relies on `eval` assigning into the local scope).
- **`IndexOfTemplate`** — a manual substring search (`indexOf(str, substr)`), used
  instead of the native `String.prototype.indexOf` so the tamper check doesn't rely on
  a builtin that could itself have been hooked.
- **`NativeFunctionTemplate`** — `checkFunction(fn)` / the two-argument
  `checkFunction(object, property)` form: verifies `("" + fn).indexOf("[native code]") !== -1`
  and that `fn` has no own `toString` property descriptor (a common way to fake the
  native-code string), running countermeasures and returning `undefined` if either check
  fails. This is the function [GlobalConcealing](../transforms/global-concealing.md)
  wraps native call sites in (`nativeFunctionName`) when tamper protection is on.
- **`createEvalIntegrityTemplate`** — generates a function that verifies local-scope
  `eval` still behaves normally, by `eval`-assigning a local flag variable and checking
  it actually got set; used to gate [RGF](../transforms/rgf.md)'s `eval(code)` call and
  the tamper-protected variant of `getGlobalTemplate.ts`. When tamper protection is
  disabled, this collapses to a trivial always-`true` stub instead.
