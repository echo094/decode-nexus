# Options Reference

Source: `options.ts` (`ObfuscateOptions` interface, plus its `ProbabilityMap<T, F>`,
`CustomLock`, and `CustomStringEncoding` helper types). Kept separate from
`js-confuser.md` and `transforms/` because it isn't a pipeline stage and isn't scoped to
a single transform — most transforms only read one or two of these options, and several
options (`globalVariables`, `preserveFunctionLength`, `verbose`, `sourceMap`) are
cross-cutting, read by many transforms or by `obfuscator.ts` itself.

## `ProbabilityMap<T, F>` — the shared option idiom

Nearly every non-boolean option below is typed `ProbabilityMap<T, F>`. This is exactly
the value `me.computeProbabilityMap(map, ...args)` (see
[plugin-api.md](plugin-api.md)) resolves per candidate node — the mechanism behind
every transform's "should I transform *this specific* node" check throughout this
reference:

| Value | Meaning |
|---|---|
| `false` | disabled |
| `true` | enabled, default mode |
| `0.5` (number 0–1) | enabled, applied to this fraction of candidates |
| `"mode"` (string) | enabled, always use this specific mode |
| `["mode1", "mode2"]` | enabled, random mode chosen per occurrence |
| `{ mode1: 0.5, mode2: 0.5 }` | enabled, weighted random mode choice |
| `(candidateArg, ...) => boolean \| string` | enabled, user-supplied predicate/mode function |
| `{ value: ProbabilityMap<...>, limit: number }` | wraps any of the above with a cap on total occurrences |

## Options by transform

| Option | Controls |
|---|---|
| `controlFlowFlattening` | [ControlFlowFlattening](transforms/control-flow-flattening.md) |
| `globalConcealing` | [GlobalConcealing](transforms/global-concealing.md) |
| `stringConcealing`, `customStringEncodings` | [StringConcealing](transforms/string-concealing.md) — `customStringEncodings` supplies alternate `CustomStringEncoding` codecs (`encode`/`decode`/`code` template) in place of the built-in base91 |
| `stringEncoding` | [StringEncoding](transforms/string-encoding.md) |
| `stringSplitting` | [StringSplitting](transforms/string-splitting.md) |
| `duplicateLiteralsRemoval` | [DuplicateLiteralsRemoval](transforms/duplicate-literals-removal.md) |
| `dispatcher` | [Dispatcher](transforms/dispatcher.md) |
| `rgf` | [RGF](transforms/rgf.md) |
| `variableMasking` | [VariableMasking](transforms/variable-masking.md) |
| `objectExtraction` | [ObjectExtraction](transforms/object-extraction.md) |
| `flatten` | [Flatten](transforms/flatten.md) |
| `deadCode` | [DeadCode](transforms/dead-code.md) |
| `calculator` | [Calculator](transforms/calculator.md) |
| `movedDeclarations` | [MovedDeclarations](transforms/moved-declarations.md) |
| `opaquePredicates` | [OpaquePredicates](transforms/opaque-predicates.md) |
| `astScrambler` | [AstScrambler](transforms/ast-scrambler.md) |
| `pack` | [Pack](transforms/pack.md) |
| `minify` | [Minify](transforms/minify.md) |
| `hexadecimalNumbers` | [Finalizer](transforms/finalizer.md)'s hex-literal rewrite |
| `lock.*` (see below) | [Lock / Integrity](transforms/lock-integrity.md) |

`renameLabels`, `renameVariables`, `renameGlobals`, and `identifierGenerator` (modes:
`hexadecimal`, `randomized`, `zeroWidth`, `mangled`, `number`, `chinese`) all feed the
RenameVariables/RenameLabels pipeline stages — cosmetic pure-renaming, intentionally
not written up as transforms in this reference (see the note in
[js-confuser.md](js-confuser.md#pipeline-order-encoderjs-confusersrcorderts)).

## `lock` sub-options

`lock` is an object, not a `ProbabilityMap` itself — the [Lock](transforms/lock-integrity.md)
transform activates if *any* key in it resolves truthy:

| Key | Purpose |
|---|---|
| `selfDefending` | breaks code formatters/beautifiers |
| `antiDebug` | injects `debugger;` statements |
| `tamperProtection` | detects `Function.prototype.toString` tampering on native functions; gates `getGlobal`/RGF `eval` |
| `startDate`, `endDate` | time-window lock (`number` ms or `Date`) |
| `domainLock` | array of regexes `window.location.href` must match |
| `integrity` | per-function source-hash tamper check |
| `countermeasures` | name of a user-defined function to call when any lock triggers (`false` = no-op, unset = crash) |
| `customLocks` | array of `CustomLock` (arbitrary `{countermeasures}`-templated guard code, with `percentagePerBlock`/`minCount`/`maxCount`) |
| `defaultMaxCount` | default `maxCount` for built-in and custom locks (25) |

## Cross-cutting / non-transform options

These aren't owned by any single transform:

- **`target: "node" | "browser"`** (required) — affects which globals
  [GlobalConcealing](transforms/global-concealing.md) special-cases, and whether
  `fetch` is tamper-protected under `lock.tamperProtection`.
- **`preset: "high" | "medium" | "low" | false`** — see
  [Pipeline order](js-confuser.md#pipeline-order-encoderjs-confusersrcorderts) for what
  each enables.
- **`compact`** — strips whitespace from final output; a `@babel/generator` `minified`
  flag, distinct from the `minify` transform.
- **`preserveFunctionLength`** — gates `me.setFunctionLength()` in
  [plugin-api.md](plugin-api.md); read by any transform that reshapes a function's
  parameter list.
- **`globalVariables: Set<string>`** — names the caller declares as already-global, so
  transforms (Pack, GlobalConcealing, VariableMasking, ...) know not to touch them.
- **`sourceMap`** — passed straight through to `@babel/generator`; not obfuscation.
- **`verbose`** — gates `me.log()`/`me.warn()` console output across every transform.
