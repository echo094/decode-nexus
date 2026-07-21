# Test Suite Reference (`encoder/js-confuser/test/`)

Jest suite, ~630 individual `test()`/`it()` cases (plus 2 `test.each` parameterized
blocks) across ~55 files. Kept as a separate top-level file — like
[options.md](options.md) and [validate-options.md](validate-options.md) — since it
isn't scoped to a single transform and several files here cut across the whole
pipeline.

## Harness (`test-utils.ts`)

Every test goes through two small helpers, not `JsConfuser.obfuscate()` directly:

- **`obfuscate(source, overrideOptions?)`** — wraps `JsConfuser.obfuscate()`, defaulting
  `target: "browser"` and forcing `pack: false` (the harness's sandbox can't override
  `new Function()`'s scope the way [Pack](transforms/pack.md) needs — see below). Falls
  back to `global.OPTIONS` when no explicit options are passed — the hook the Jest
  project matrix below uses to sweep the same test file across many option
  combinations.
- **`evalCode(code, windowProperties?)`** — runs the obfuscated output via `new
  Function("window", "globalThis", "global", code)` inside a constructed object that
  mirrors the real `global`, then returns `window.TEST_OUTPUT` — the convention nearly
  every test writes its result to and asserts against. Uses `new Function` rather than
  `eval` specifically so the code executes in non-strict mode (needed for
  [This.test.ts](../../encoder/js-confuser/test/features/This.test.ts)'s sloppy-mode
  `this` cases).

## Jest project structure (`jest.config.js`) — the key architectural fact

Two kinds of projects run against the same test files:

1. **`main`** — every test file *except* `test/features/`, run once, using each test's
   own explicit options.
2. **`features:<option>`** — one full extra run of the *entire* `test/features/` suite
   (189 tests) per project, once per entry in a 20-option matrix (`minify`,
   `renameVariables`, `renameLabels`, `controlFlowFlattening`, `globalConcealing`,
   `stringConcealing`, `stringSplitting`, `duplicateLiteralsRemoval`, `dispatcher`,
   `rgf`, `objectExtraction`, `flatten`, `deadCode`, `calculator`, `movedDeclarations`,
   `opaquePredicates`, `variableMasking`, `preserveFunctionLength`, `astScrambler`,
   `pack` — each forced `true` individually), plus one more project with `preset:
   "high"`. That's **21 full passes of the features suite** (~3,969 test executions from
   that one folder), each verifying every language-feature test still behaves
   identically with that one transform forced on in isolation, and once more under the
   full high preset combined. This dwarfs the ~440 tests everywhere else in the suite
   combined and is the suite's real correctness guarantee: semantic preservation,
   transform by transform.
   - Wired through Jest's per-project `globals: { OPTIONS }`, read back by
     `test-utils.ts`'s `obfuscate()` as `global.OPTIONS`.

## Directory breakdown

- **`code/`** (7 tests, 5 fixture files — `AES.src.js` ~1400 lines, `Cash.src.js`
  ~1000, plus `Dynamic`/`ES6`/`StrictMode.src.js`) — real-world-sized programs run once
  through the full `"high"` preset (some variants stack RGF/Integrity/SelfDefending/
  TamperProtection on top), asserting the obfuscated output still produces identical
  results. The closest thing to an integration/smoke test in this suite.
- **`features/`** (189 tests, 18 files) — one file per language construct
  (`BreakContinue`, `Closures`, `Expressions`, `ForIn`, `Functions`, `GetterSetter`,
  `Globals`, `IfStatements`, `LabeledStatements`, `Literals`, `Loops`, `Statements`,
  `SwitchStatement`, `TemplateLiterals`, `This`, `Throw`, `TryCatch`,
  `UpdateExpressions`) asserting semantic preservation — run 21x total per the matrix
  above.
- **`transforms/`** (358 tests) — one file (or subfolder) per pipeline stage, 1:1 with
  both `src/transforms/*.ts` and this reference's [transforms/](transforms/):
  - top level: `astScrambler`, `calculator`, `deadCode`, `dispatcher`, `flatten`,
    `hexadecimalNumbers` (covers [Finalizer](transforms/finalizer.md)'s hex-literal
    option — see [options.md](options.md); there's no dedicated `finalizer.test.ts`
    beyond this), `minify`, `opaquePredicates`, `pack`, `preparation`, `renameLabels`,
    `rgf`, `variableMasking`
  - `extraction/` (26): `duplicateLiteralsRemoval`, `objectExtraction`
  - `identifier/` (56): `globalConcealing`, `movedDeclarations`, `renameVariables` —
    the latter includes a `test.each` sweep over every `identifierGenerator` mode (see
    [NameGen.ts](utils/name-gen.md))
  - `lock/` (36): `antiDebug`, `countermeasures`, `dateLock`, `domainLock`,
    `integrity`, `lock`, `selfDefending`, `tamperProtection` — one file per `lock.*`
    sub-option, all exercising [Lock / Integrity](transforms/lock-integrity.md)
  - `string/` (30): `customStringEncoding`, `stringConcealing`, `stringEncoding`,
    `stringSplitting`
  - `controlFlowFlattening/` (45) — the single largest test file in the suite, matching
    [ControlFlowFlattening](transforms/control-flow-flattening.md) being "by far the
    most complex transform in the pipeline"
- **`semantics/`** (6 tests, 4 files) — cross-cutting guarantees not owned by one
  transform: `functionLength` (`preserveFunctionLength` option — see
  [function-utils.md](utils/function-utils.md)), `lastExpression` (a script's trailing
  expression value survives, including combined with RGF), `moduleImport` (import
  declarations survive the High preset), `newFeatures` (BigInt literals).
- **`util/`** (16 tests, 5 files) — unit tests for a *subset* of `utils/*.ts`:
  [IntGen](utils/int-gen.md), a slice of [ast-utils](utils/ast-utils.md)
  (`getFunctionName`, `isDefiningIdentifier`, `getPatternIdentifierNames`,
  `isUndefined`), [gen-utils](utils/gen-utils.md) (`alphabeticalGenerator` only),
  [object-utils](utils/object-utils.md), [random-utils](utils/random-utils.md)
  (`choice`/`getRandomString`/`getRandomHexString` only). No test files for
  [NameGen.ts](utils/name-gen.md), [node.ts](utils/node.md),
  [static-utils.ts](utils/static-utils.md), or [PredicateGen.ts](utils/predicate-gen.md).
- **`templates/`** (15 tests, 1 file) — `template.test.ts` exercises the
  [Template Engine](template-engine.md) API directly:
  string interpolation, AST subtree insertion (value or callback), nested `Template`
  insertion, duplicate-node-insertion errors, `.single()` edge cases, `.addSymbols()`.
- Root level:
  - `index.test.ts` — the public API surface: `obfuscate`/`obfuscateAST`/
    `obfuscateWithProfiler` (see [result-profiling.md](result-profiling.md)).
  - `obfuscator.test.ts` — two `Obfuscator` internals directly:
    `globalState.lock.createCountermeasuresCode` and `shouldTransformNativeFunction`
    (the [Tamper Protection](transforms/lock-integrity.md) native-function gate).
  - `options.test.ts` — `ProbabilityMap` value shapes (percentages/arrays/weighted
    maps), `compact`/`verbose`, and `validateOptions()` error cases (invalid
    `lock`/`target`/dates/unknown-key).
  - `presets.test.ts` — `test.each` over every preset name, asserting each resolves to
    valid, self-consistent options (`preset` field matches, passes
    `validateOptions()`).
  - `probability.test.ts` — `isProbabilityMapProbable` (true/false/invalid-shape
    examples) — the check `obfuscator.ts` uses to skip registering a transform whose
    option resolves to "never" up front, part of the same machinery as
    [options.md](options.md)'s `ProbabilityMap<T, F>`.
  - `sourceMap.test.ts` — source map generation, plain and combined with
    RenameVariables/ControlFlowFlattening/Dispatcher/Flatten.

## Running

`npm test` → `jest` (the multi-project config above); `npm run test:coverage` for an
HTML coverage report.
