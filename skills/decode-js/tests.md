# Test Suite Reference (`decoder/decode-js/test/`)

A [Vitest](https://vitest.dev/) suite spanning end-to-end plugin fixtures, per-visitor
fixtures, the jsconfuser combination fixtures and the VM cells below. Outside `test/vm/` every case
is fixture-driven: a `.js` input is transformed and its output compared to either the input itself
(no-op expected) or a `.fix.js` golden file. The VM tests encode committed programs with the pinned
encoder and compare behaviour ([`test/vm/`](#testvm--vm-recovery)).

## Config (`vitest.config.js`)

- **Path aliases** — `#plugin` → `src/plugin`, `#visitor` → `src/visitor`. Tests import
  the code under test through these (e.g. `#plugin/sojsonv7.js`, `#visitor/split-assignment`).
- **Coverage** — enabled by default (`@vitest/coverage-v8`), scoped to `src`, with
  `text` + `json` + `json-summary` reporters and `reportOnFailure: true`.
- `passWithNoTests: true`.
- **`testTimeout`, one generous global limit and no per-test overrides.** The jsconfuser
  combination fixtures and the heavier VM cases are whole-pipeline decodes of real encoder output,
  the largest running to six figures of obfuscated source bytes. Their per-case time grows
  several-fold under v8 coverage and full parallel load, and a lower limit that passed alone or
  with coverage off **timed out on a shared CI runner and again in a full coverage run**. Read a
  timeout here as a host-speed artifact until proven otherwise — a decode regression changes the
  *output*, and shows up as a `.fix.js` or oracle mismatch on a fast machine too. Keep the limit in
  the config rather than on individual tests: a per-test value below the global one silently caps
  it. The axis to check if a timeout recurs is the per-case time of the heaviest cases under
  coverage (`npx vitest run --reporter=verbose`) against the configured limit, never a remembered
  figure.
- **`scriptTimeout`, one generous limit for every script a test runs in a Node VM context.**
  [`test/helper.js`](../../decoder/decode-js/test/helper.js) exports it, and every
  `runInNewContext`/`runInContext` in `test/` and the integration harness's behavioral-oracle
  bound take it; no test and no oracle fixture carries its own. It is a different setting from
  `testTimeout`, and the only one that stops a synchronous hang in target code, so it stays finite.
  It is generous for the same reason: an encoded program interpreted under stacked control-flow
  options runs for seconds on its own, and a short per-file limit that passed alone failed under
  full parallel load. The axis if one recurs is that script's own time in the same context
  against the limit. A test that needs a limit to fire passes its own to the code under test
  (the string-array pass's evaluation limit, the harness test's own bound).

**What a run executes, and what Vitest's timer cannot stop.** There are no `pretest`/`posttest`
scripts or include overrides, so default discovery picks up every `*.test.js` under `test/`. One
global setup runs first: it generates the [input cells](#input-cells-and-layered-inputs), the
encoded inputs of the VM tests that are not cells, so a run needs the pinned encoder checkout and,
for minify cells, a JDK on `PATH` or in `JAVA_HOME`. The one exclude added to Vitest's defaults is
the ignored `sandbox-tests/`, which holds the encoder checkout
([the cell scripts](#the-cell-scripts)) and the cell cache; the encoder's own suites are not decoder
tests. Child processes: the
`public-entry-points/` files `cli.test.js` and `sequential.test.js` launch `src/main.js` with no
subprocess timeout and `integration.test.js` with 30 s; `test/scripts/render-vm-switch.test.js`
launches the render script without one; the cells generate through the cell scripts' worker, 65 s
per cell. Vitest's per-test timer cannot interrupt synchronous decoder work, a direct `Function`
call, an `isolated-vm` `evalSync` without its own limit, or a Node VM call before `scriptTimeout`
ends it. A supervised run therefore needs an outer process-group deadline; a test summary on stdout
without an observed process exit earns no credit. To keep the CLI/backend entries out, pass those
three `public-entry-points/` paths to `--exclude`.

Run with `npm test` (`vitest --config vitest.config.js`) or `npx vitest run`. **To read
the pass/fail tally, run `npx vitest run --coverage.enabled=false`** — with coverage on, a
stray non-JS file under `src/` (a `.DS_Store` will do it) makes the reporter throw while
remapping coverage, and the run prints the coverage table but never the counts, exiting 0
either way.

## Harness (`test/helper.js`)

Three helpers, all reading fixtures relative to a passed-in base path and asserting with
Vitest's `expect(...).toBe(...)`:

- **`getVisitorResult(visitor, fix, input)`** — parses `<input>.js`, runs
  `traverse(ast, visitor)`, generates, and compares. When `fix` is **true** the output
  must equal `<input>.fix.js` (the visitor changed the code); when **false** it must equal
  the original source (the visitor must **no-op** — the "invalid"/negative cases). For
  `fix` cases, it additionally asserts `referenceState(ast)` (a sorted per-scope snapshot
  of each binding's `references`/`constant`/`constantViolations.length`) equals
  `referenceState(parse(cmpCode))` — a fresh parse of the golden output. This catches a
  missing or mis-scoped `scope.crawl()` (stale reference counts) even when the generated
  text already matches; added after a real bug of this kind in
  [split-assignment](visitors/split-assignment.md).
  It also asserts `detachedReferences(ast)` is empty — no binding holding a reference to a
  node that has left the tree — for `fix` **and** no-op cases alike, since "output unchanged"
  is not "nothing happened". **Reachability is the only check that sees this**: a stale
  reference reports `removed === false` and its ancestry still reaches a Program path,
  because the cached parent chain survives, so the detector walks the live tree instead of
  asking the path. `helper.test.js` exists to prove the detector *can* fail — a check that
  only ever reports zero is indistinguishable from one whose population is empty.
- **`getPluginResult(plugin, fix, input)`** — same contract but calls `plugin(source)`
  directly (full pipeline, not a single visitor).
- **`getPipelineResult(passes, fix, input)`** — runs several passes on **one AST**, in order,
  each either a visitor object or a function taking the AST. It exists because the other two
  cannot reach the failure class a real pipeline has: `getVisitorResult` runs one visitor on a
  fresh parse, so no earlier pass has detached anything, and a fixture built by running the
  earlier passes and *writing the result to disk* is certified across a re-parse — which
  rebuilds every path from text and silently repairs the state a pipeline carries forward. So
  its input is raw source and the passes run inside the test; a pre-baked intermediate would
  restore exactly the state that hides the defect. Worked example and the incident behind it:
  [unlock-env](visitors/obfuscator/unlock-env.md).

So a fixture directory pairs `name.js` with an optional `name.fix.js`; the test's `fix`
flag encodes whether a transformation is expected.

## Directory breakdown

### `test/scripts/` — command-line script tests

`render-vm-switch.test.js` exercises the source-input form of
[`scripts/render-vm-switch.mjs`](vm/switch/vm-switch-emit.md#inspecting-the-switch-handoff).
It checks the generated switch text, compares the encoded and step-one arithmetic programs
under the same host bindings, and refuses to overwrite an existing artifact. Tests for
`src/utility/` remain in `test/utility/`.

`jsconfuser-vm-cells/` tests [the cell scripts](#the-cell-scripts) in
`scripts/jsconfuser-vm-cells/`, one file per script (`codec`, `oracles`, `layout`, `run-worker`),
all without generating encoder output; that section's table says what each pins.

### `test/sojsonv7/` — end-to-end plugin test

`sojsonv7.test.js` → one case `sample_189`, run through `getPluginResult(PluginSojsonV7,
true, …)`. The input `sample_189.js` is a **~101 KB** real `jsjiami.com.v7` sample
(`var version_ = "jsjiami.com.v7"; …`) that decodes all the way down to the 8-byte golden
file `sample_189.fix.js` containing just `"width";` — a compact regression anchor for the
entire [sojsonv7](plugins/sojsonv7.md) pipeline (global decode + dead-code + purify +
env-unlock). It is the only full-plugin fixture in the suite.

### `test/visitor/` — per-visitor fixtures

| test file | visitor | cases (valid → `.fix.js`, invalid → no-op) |
|-----------|---------|--------------------------------------------|
| `split-assignment.test.js` | [split-assignment](visitors/split-assignment.md) | `call-valid-1`, `if-assignment-valid`, `if-member-valid`, `member-valid-1`, `assignment-member-name-valid`, `variable-valid` (valid); `if-invalid`, `variable-invalid` and eight behaviour-gate cases (no-op), listed in its [Fixtures](visitors/split-assignment.md#fixtures) |
| `split-variable-declarator.test.js` | [split-variable-declarator](visitors/split-variable-declarator.md) | `init-valid-1` (valid); `parent-invalid`, `init-invalid` (no-op) |
| `parse-control-flow-storage.test.js` | [parse-control-flow-storage](visitors/parse-control-flow-storage.md) | `object-invalid-1` (no-op); `nested-delegating-wrapper-outer-first` pins the current outer-first traversal dependency and one binary resolving path |
| `merge-object.test.js` | [merge-object](visitors/merge-object.md) | ObjectPattern/ArrayPattern declarators (no-op); Identifier declarator merge (valid) |

Concrete examples of what the fixtures pin down:

- **split-assignment `call-valid-1`** — hoists an assignment buried in a computed
  member/callee chain (`b = d[(d = _)("1")]("2"); x[…] = …`) and keeps the inner `d = _` in
  place, because the member object `d` is read before it runs: exactly the
  [split-assignment](visitors/split-assignment.md) `getInsertPath` behavior.
- **split-variable-declarator `init-valid-1`** — `let a = (() => {}, function(){})` →
  `() => {}; let a = function(){}`. Note this visitor is otherwise
  [wired into no plugin](visitors/split-variable-declarator.md) — the test is its only
  caller.
- **parse-control-flow-storage `object-invalid-1`** — a one-property object whose function
  returns a `typeof … || … || …` logical chain (params length 1, not the accepted 2-arg
  shapes). It must be left untouched, exercising the "incomplete match ⇒ bail"
  [completeness gate](visitors/parse-control-flow-storage.md).
- **parse-control-flow-storage `nested-delegating-wrapper-outer-first`** — an outer binary wrapper
  precedes an inner storage whose wrapper delegates through it. The exact golden proves the outer
  storage resolves first and makes the inner storage recognizable before its `exit` handler runs.

Coverage is uneven by design among the shared visitors: `split-assignment`,
`split-variable-declarator`, and `parse-control-flow-storage` have dedicated fixtures, while
the rest are exercised transitively through the `sample_189` end-to-end case.

### `test/generator-minimal/` — shared generation contract

`generator-minimal.test.js` drives one escaped-string input through both current consumers of
[delete-extra](visitors/delete-extra.md), `PluginObfuscatorX` and `PluginJsconfuser`. Its exact
golden contains an ordinary `A` and a literal non-ASCII `é`, proving that each entry combines the
visitor with `jsescOption: { minimal: true }` instead of re-escaping the decoded values.

### `test/visitor/obfuscator/` — the obfuscatorx visitor fixtures

Inputs here are **real javascript-obfuscator output** where the claim is about an encoder spelling;
the isolated numeric-storage accept/decline pair is hand-written because it pins the local
visitor's transaction boundary instead. The string-array cases are triples like the jsconfuser
ones. These drive a pass, or a composition of passes, **directly** rather than through the
`obfuscatorx` entry — which does exist, and has its own directory below. Driving the pass directly
is what lets a case pin a decline, an intermediate state, or an era the entry as a whole has no
separate assertion for.

| test file | pass | cases |
|-----------|------|-------|
| `normalize-statements.test.js` | [normalize-statements](visitors/obfuscator/normalize-statements.md) | `nested-encoder-output` — four conditionals in four positions, one of which is unreachable until an `&&` has been reversed, so the case pins that a single round is not enough |
| `inline-control-flow-storage.test.js` | [obfuscator/inline-control-flow-storage](visitors/obfuscator/inline-control-flow-storage.md) | `storage-numeric` resolves and refreshes reference state; `storage-numeric-write` proves an unsupported write leaves the whole candidate untouched; `storage-binary`/`storage-logical`/`storage-call`/`object-invalid-1` are the shared visitor's cases, **copied** so the fork's claim to accept everything the shared matcher accepts is falsifiable against the fork itself |
| `string-array.test.js` | [string-array](visitors/obfuscator/string-array.md) | every one of the pass's four outcomes, and one damaged input per refusal path. Fixture-to-claim table in the pass's own [`## Fixtures`](visitors/obfuscator/string-array.md#fixtures) |
| `normalize-converting.test.js` | [normalize-converting](visitors/obfuscator/normalize-converting.md) | per-claim table in that pass's own [`## Fixtures`](visitors/obfuscator/normalize-converting.md#fixtures) |
| `unflatten-switch-dispatch.test.js` | [unflatten-switch-dispatch](visitors/obfuscator/unflatten-switch-dispatch.md) | same — and five of its cases are **declines**, which is the half a golden cannot express |
| `unlock-env.test.js`, `unlock-env-pipeline.test.js` | [unlock-env](visitors/obfuscator/unlock-env.md) | same. The second file exists because the strip's dependency on an earlier pass is only observable on a composition |
| `era-below-2-16.test.js` | the whole composition | one case per distinct string-array era below `2.16.0` — see below |

The unlock-env set also carries the exact `self-defending-newline-bail` fixture from the 5.4.5
encoder output. It pins the existing search-chain removal after the encoder's early newline bail;
the visitor does not treat that new spelling as a decline.

**`era-below-2-16.test.js` is the one set keyed on an era rather than on a pass**, and it is the
only committed pinning those eras have. Seven corpus columns sit below `2.16.0` and carry four
distinct era combinations between them — `2.9.6` and `2.11.1` differ only in the rotator, `2.15.3`
and `2.15.5` only in the wrapper — so four cases exhaust the range and a fifth would pin a shape
one of them already covers. Two properties are worth keeping:

- **It runs the pipeline's own pass order on one AST**, with no serialize/parse boundary, because
  a reparse restores exactly the derived state a real pipeline never has.
- **Three of the four goldens are byte-identical apart from one renamed identifier**, which
  `renameIdentifiers` makes irreversible by design. Four encoder eras decoding to the same program
  is the collapse claim as an artifact rather than an argument.

### `test/obfuscatorx/` — the entry-level fixtures

Triples driven through `PluginObfuscatorX` itself, so a break in the entry — the pass order, the
refusal gate, the final generation — fails the suite rather than only a visitor break. The
fixture-to-claim mapping lives in [obfuscatorx.md](plugins/obfuscatorx.md#fixtures), including the
focused `3.2.0` composition case. Each golden is written by a builder that refuses unless the
decoded output **runs** and reproduces the pre-obfuscation source's own output, *and* the source
itself reproduces it — so a golden cannot be certified against a broken expectation.

**Not subject to the one-process-per-decode constraint the `obfuscator` entry imposes**: that
plugin builds its isolate at module scope, so two decodes in one process share a global object and
the second can pass for the wrong reason. This one builds a fresh isolate per decode, so its cases
share a file and the suite grows a case at a time.

Two things about the string-array set generalize past it:

- **The case list came from the encoder's own `.spec.ts` files**, not from cases invented here,
  and that is what found the gap worth finding: two options with no live-call-site coverage
  anywhere in the frozen corpus. A fixture pins a claim, so a case written to match what a pass
  already does pins the pass to itself.
- **Three of the four outcomes are not failures**, so only `decoded` has a golden. The others
  assert a status *and* an untouched tree — compared against a **normalize-only run of the same
  input**, since an earlier pass in the same file runs first and a raw-input comparison would
  report every one of them as mutated.

`5.4-regressions.test.js` adds the exact 5.4.4/5.4.5 entry fixtures: the low-side wrapper-reuse
case runs raw as `"broken"` while the decoder recovers the source's intended `"ok"`; the two
5.4.5 encounter-order cases assert both plain and spread wrapper shapes before decoding; and the
corrected concise-arrow `in` fixture remains parseable and runnable. Existing optional-call
coverage remains the `4.2.0-optional-cff` case. These fixture assertions are entry-level; the
focused reports separately own direct/plugin, one-AST and fresh-derived-state comparisons.

`2.19.0-class-logical` is a focused producer cell rather than an ordinary matrix row. Its test
first proves the frozen input AST contains both a computed quoted class-method key and a top-level
statement-level `&&`, then checks the exact `PluginObfuscatorX` output. This closes two population
gaps without claiming that runtime equivalence alone proves either reversal ran.

`static-top-level-declaration.test.js` adds the exact 5.3.1 and 5.4.0 declaration outputs from
the release-note backfill. It asserts direct/plugin parity, parser acceptance, runtime `42`,
fresh-derived-state parity and zero split-object writes, while explicitly checking that the low
side retains shorthand and the high side carries the expanded binding. The shared
`merge-object.test.js` cases separately prove that the guard is a no-op for ObjectPattern and
ArrayPattern declarators and that Identifier merging still fires. The guard is a refusal, not a
destructuring decoder.

### `test/visitor/jsconfuser/` and `test/jsconfuser/` — the jsconfuser suites

The bulk of the suite: one per-visitor file per
[plugin/jsconfuser](plugins/jsconfuser.md) visitor, exercising them one at a time, plus the
files that run whole *combinations* through `getPluginResult`, named for the transforms they
combine (`control-flow-flattening-minify`, `duplicate-literal-string-concealing`,
`rename-variables/*`, …). Both are needed and neither substitutes for the other: a
per-visitor case exercises a matcher in isolation and never the plugin's entry-point wiring,
which is where the combination bugs live —
[decoding-method/with-encoder.md](../decoding-method/with-encoder.md#p6)'s "unit to combo".

**Fixtures come in triples, not pairs.** Alongside `<name>.js` (obfuscated input) and
`<name>.fix.js` (expected output), a jsconfuser fixture keeps `<name>.src.js`: the
pre-obfuscation source it was generated from. `helper.js` does not read it — it is what
makes a fixture reviewable for decode *quality* (is the output readable, or merely
self-consistent?) rather than only for equality, and it is what keeps
[M5](../decoding-method/with-encoder.md#m5) size ratio computable later.
A fixture frozen while its gap is still open certifies a passthrough as expected output, so
freeze only once size and structural counts show the decode actually fired.

**Four combination fixtures cover the interactions deliberately, and their configs are chosen
against cost.** `cff-dispatcher-masking` (CFF + dispatcher + variableMasking), `string-stack`
(stringConcealing + stringEncoding + stringSplitting), `pack-payload` (four transforms inside
a Function-constructor payload) and `high-template-regex` (the only sample carrying a template
or regex literal). Two `high`-preset fixtures predate them, and the gap those left is worth
recording: **neither of their sources contains a function**, so CFF function flattening,
dispatcher entries, masking and Flatten had no committed coverage at all until the trio
fixture landed.

**Prefer an explicit combo to a preset unless the preset is the thing under test.** `high` is
probability-gated and its output size swings by an order of magnitude across repeat encodes of
the *same* input, where an explicit trio stays within a narrow band; adding
`controlFlowFlattening` to the pack fixture likewise cost dozens of times the bytes for the
same pack coverage.
A combo also states in its config exactly what it covers, where a preset leaves that to be
inferred.

**A committed fixture is the only durable coverage.** The corpus these fixtures' sources also
feed ([probes.md](probes.md)) is untracked and regenerated on demand, so every figure it
produces is local to one working copy and a fresh clone starts with none of it. "The corpus
already covers this" is therefore not a reason to skip a fixture — it is a reason to check which
of the two a regression would actually reach.

**Verify runtime equivalence before freezing, and check the comparison is not vacuous.** The
builder for a fixture triple encodes, decodes, runs both and compares `TEST_OUTPUT` — and must
**refuse to write the triple when the source sets no `TEST_OUTPUT` at all**. That guard is not
optional: the first run of one compared `undefined` against `undefined` and reported a pass.
Build it per [probes.md](probes.md)'s conventions; it needs the encoder's `dist/`.

### `test/vm/` — VM recovery

The VM tests are of three kinds, and each kind has its own place:

| Kind | Tests | Input | Where |
|---|---|---|---|
| Unit | One module or transform | Hand-written records or source; **no compiler input** | `single-component/` |
| Stage | The compiler plus one encoder stage | Cells | a suite under `cell-suites/` |
| Combination | The compiler plus several stages | Cells | a suite under `cell-suites/` |

**A unit test has no compiler in it, whatever it calls.** Its input is written by hand in the test:
a boot whose words hold `window.TEST_OUTPUT = 1 + 2`, a minified handler pair, a typed switch
model. A test that feeds decoder code the encoder's output is a stage or combination test, whichever
function it calls, and is written as a suite. The tests that read encoder output without being
cells (the public entry points, the harness test and the render-script test) read
[input cells](#input-cells-and-layered-inputs).

```text
test/vm/
├── switch/single-component/                       unit: the shared backend on typed models
│   ├── models.js                                  the typed-model builders the files share
│   ├── values.test.js, emit.test.js, model.test.js
│   └── statements/<module>.test.js               one per statement module: conditionals,
│                                                  loop-ends, switches, try-ends
└── jsconfuser-vm/
    ├── sources/<name>/source.js                   every program, once (oracle.json beside it if needed)
    ├── cell-suites/
    │   ├── <suite>/suite.js                       the suite's definition
    │   ├── <suite>/<file>.test.js                 one per key of suite.js `files`
    │   ├── <suite>/stage-effect.test.js           stage suites only: the stage changes the program
    │   └── distinct-cells.test.js                 what crosses suites
    ├── layered-inputs/<program>/                  the second encoder's committed outputs
    ├── support/                                   cells, cell tests, form indicators, stage effect,
    │                                              input-cell setup, harness, oracle runner
    ├── single-component/                          unit: the frontend's modules and the lowering
    └── public-entry-points/                       plugin, CLI, sequential target, debugger policy
```

Name files and folders for the behaviour they test, never for a task ID, sequence number or trial
attempt. Nothing under `test/vm/` carries a hash of tracked bytes
([Git identifies tracked bytes](../doc-conventions.md#where-facts-live)), and no encoded input is
committed except the second encoder's layered outputs.

#### Suites

A suite is one folder, `cell-suites/<suite>/`, holding its own definition in `suite.js`. Nothing
defines a suite elsewhere, and suites are never merged: each scenario and each chain is its own
suite. `support/cells.js` collects the folders only for what crosses suites (the cache and the
distinctness checks below).

```js
// cell-suites/<suite>/suite.js (explanatory shape)
export default {
  name,               // the folder name
  protects,           // what a red case means; ends "Proved: …" once a break has shown it,
                      // or "Not proved by a break: …" for a suite kept for what it composes
  files: {            // one test file per key: <key>.test.js
    [file]: [{
      sources,        // program names under sources/
      profile,        // the encoder options, below
      seeds,          // one fixed seed (251, or one pinned for the shape it encodes)
      protects,       // optional: this row's own claim, where rows encode one program under
                      // different seeds
    }],
  },
  cases,              // optional: protects text per source, where sources protect different things
  proofs,             // optional: [{ claim, file, find, replace }], each claim's break
  indicators,         // optional: per source, the form indicators its decode must share with it
  inertControls,      // optional: [{ source, profile, seed, protects }], programs the stage
                      // cannot act on
}
```

A profile is `baseline` or `+`-joined option names over `baselineOptions`, every option of the
encoder explicitly false with target `browser` (`name=N` sets a number; an unknown name throws). A test file is three lines: it imports its `suite.js` and calls
`defineCellTests(suite, '<file>')` from `support/cell-tests.js`. A real example, `try-arm-exits`:

```js
export default {
  name: 'try-arm-exits',
  protects:
    "A try that never completes normally inside a conditional arm leaves through the arm with no label. Proved: the try end in a conditional's arm in conditionals.",
  files: { cells: [{ sources: ['try-arm-exits'], profile: 'baseline', seeds: [1] }] },
  proofs: [
    {
      claim: 'try-arm-exits',
      file: 'src/vm/switch/statements/conditionals.js',
      find: 'fallthrough.ends.has(tryEnd) &&',
      replace: '',
    },
  ],
}
```

Its cell `try-arm-exits/cells/try-arm-exits/baseline/1` encodes `sources/try-arm-exits/source.js`
with every option off at seed 1, decodes it, and runs source, encoded and decoded programs.
Replacing the proof's `find` with its `replace` changes the decoded program and turns the case red;
that break is what earned the Proved line.

**One seed per source.** A source is encoded at one fixed seed, 251, unless a row pins the seed
that encodes the shape it is there for: `dispatcher-branches` runs in three rows, at seeds 33, 32 and
35, each with its own `protects` (a split route key, an array result, an object result). Further
seeds of one source failed together or not at all, so they add time and no proof; the random
variation comes from CI's fresh seed ([below](#sources-and-the-cell-cache)).

**What a suite keeps.** A cell stays only if a break in decoder code that is not broad turns it red.
Reaching code is not proof, and a break whose decoded output is unchanged proves nothing. A proof
is that break, recorded as `{ claim, file, find, replace }`; `find` stands exactly once in `file`,
and a Proved line in `protects` or `cases` says the same in words. A suite with no recorded proof
says so in its `protects` (`Not proved by a break: stack only`, `coverage only`, `behaviour only`)
and stays for what it composes, not for a break. `scripts/proof-census.mjs` applies the rule: it
copies the decoder into the ignored `sandbox-tests/proof-census/`, with its own copy of the cell
cache, and runs a suite clean and then under each break (`prepare`, `suite <name>`,
`report <name>`, `cross`); a break still on trial goes in that folder's `breaks.json`. In
explanatory pseudocode:

```text
per suite: run its cells clean, then once per recorded proof with that break applied
cross pass: apply every break that turned some cell red to every cell no own proof turned red
a break that deletes a binding and fails every cell crashes on the missing name: it is no break
a break is broad when it fails half or more of the cross pool, which mixes every stage and
  rewrite: it shows that a cell runs, not what it holds
keep each cell some break that is not broad turns red; a cell none does goes, with the sources
  only it reads
```

A scenario keeps the old test's scenario, never its encoded bytes. The suites by shape:

| Suite | Shape |
|---|---|
| `compiled-forms` | One test file per JavaScript form family (control, expressions, functions, data, host effects), plain compiled code; `expr-compare` holds `numeric-edges`, the numeric edge values and greater-or-equal |
| `compiled-forms-canonical-opcodes` | One representative per form family under the baseline options, opcodes unrandomized |
| `single-payload-stage` | One test file per payload stage, the fewest sources that reach its decoder step |
| `single-payload-stage-conditions` | One test file per stage: sources each built for one condition of that stage's decoder |
| `<stages>-chain` | Several stages in encoder order over the compiled-forms representatives |
| `<rewrite>-over-<stage>` | An interpreter rewrite (handler table, class rewrite, minify) over one opcode stage |
| `all-stages-together` | Every option at once, one test file per source |
| `interpreter-rewrite-fixed` | A rewrite of the interpreter alone; the decode must equal the plain decode |
| `reads-as-source` | Whole small programs at baseline, read by their [form indicators](#readability) |
| One scenario | A single decoder rule on its own source and seed (`try-arm-exits`, `anti-macro-route`, …) |
| `open-decoder-gaps` | What is red today, one test file per open issue |
| `whole-programs` | Two whole programs under randomized opcodes |

`open-decoder-gaps` cases are ordinary tests that stay red until their issue is fixed; they carry no
`test.fails` or expected-decline marking. A fixed case moves to its natural suite. A gap that a red
check finds becomes a suite of the chain's shape.

#### What every cell checks

```text
defineCellTests(suite, file), for each cell (suite, file, source, profile, seed):
  beforeAll: generate the missing cells                 # pinned encoder, ignored cache; with their
                                                        # plain cells where a check compares them
  if suite is single-payload-stage:
    run that stage's decoder step alone on the encoded input; it must remove its stage
  test "decodes with the source behaviour: <protects>":
    generation succeeded
    public decode (inspectCurrent) accepts
    the output checks pass; the input AST is unchanged   # the cell scripts, below
    source behaviour equals oracle.json's expectation, where the source has one
    encoded behaviour equals source behaviour
    decoded behaviour equals source behaviour
    interpreter-rewrite suites: decoded output equals the plain cell's decoded output
  if suite.indicators names this source:
    test "reads as its source": each named form indicator of the decode equals the source's
```

Behaviour is what the program leaves in `window.TEST_OUTPUT`, run by `support/oracle-runner.js` in a
browser-like host (`window`/`self`, `performance`, `atob`/`btoa`) under the shared script limit. The
plain cell of a cell is the same source and seed under `randomizeOpcodes` alone: the stage-free
program a stage step, a stage effect, an inert control and an interpreter rewrite are compared with.
A source whose encoded program does not behave as the source under a suite's profile is no cell of
that suite: the encoder's own failure leaves the encoded-equals-source check nothing to compare, so
the cell is dropped, never exempted.

`cell-suites/distinct-cells.test.js` checks what crosses suites, decoding nothing: every `files` key
has its test file and every test file a key; every cell says what it protects (its row's
`protects`, its source's `cases` entry or the suite's `protects`); every proof's `find` stands
exactly once in its file and differs from its `replace` (re-prove a protection when its code
changes); no two cells encode the same text; every inert control says what it protects and its
payload equals its plain cell's; and the stage suites (`single-payload-stage` and the `-chain`
suites but `runtime-rewrites-chain` and `timing-runtime-chain`) are exactly those with a
`stage-effect.test.js`.

An inert control is a program its suite's stage cannot act on (`no-eligible-string` under string
concealing, say). It is never decoded: its payload, the container's words and constant pool, must
equal its plain cell's (`inertCells` in `support/cells.js`). `<suite>/stage-effect.test.js` calls
`defineStageEffectTests(suite)` from `support/stage-effect.js` for the opposite check: each of a stage
suite's cells must have a payload unlike its plain cell's. It has one file per stage suite so Vitest
spreads it over its workers and no single test carries every stage cell under the global time limit.

#### Readability

Readability is checked by form indicators, never by golden outputs or a size or count recorded from
an earlier decoder ([M1](../decoding-method/rules.md#m1),
[M2](../decoding-method/rules.md#m2)).
`support/form-indicators.js` (`formIndicators(code)`) counts, in one program:

| Indicator | What it counts |
|---|---|
| `copies` | Adjacent copies: a producer's value moved into another variable by the next statement |
| `objectProperties`, `accessors`, `conditionals`, `logicals` | What object literals write and their native getters and setters; `test ? a : b`; `a && b`, `a \|\| b`, `a ?? b` |
| `methodCalls`, `memberAssignments`, `globalThisReferences` | The host-access forms a sloppy program writes natively |
| `ifs`, `loops`, `forIns`, `switches`, `labels`, `parameters` | The statement forms, and the parameters functions declare |
| `scaffolding` | The decode's own machinery for a call or a closure: capture cells, captured registers, wrapped arguments and receivers, the for-in enumeration helper; a source has none |

A suite's `indicators` names, per source, the indicators its decode must equal the source's; a name
the module does not compute fails. `reads-as-source` holds whole small programs (`branch-forms`,
`closure-loop`, `conditional-increment`, `scale`) at baseline; `compiled-forms` names indicators for
its form families.

#### Sources and the cell cache

A cell's program is `sources/<name>/source.js`, and every program lives there once; one program
encoded under several seeds is one source in several rows. `oracle.json` beside a source is needed
only for a special host or a committed expectation. The runner reads four of its fields:
`hostProfile` (`cash-dom-test-v1` adds a document stub and the host's globals), `actions` (reads
of `TEST_OUTPUT` or `window` by `get`, `keys`, `typeOf` or `call`, each stored under its `as` name;
none means `TEST_OUTPUT` itself), and `expected` or `expectedThrow`, the committed expectation of
the source's own run. The committed files carry further fields (`cellId`, `provenance`,
`semanticTags`, `globals`, `setup`) that nothing reads.

```text
cellKey = sha256(PIN, installed dependency tree, Node major, JDK major if minify, sha256(source), options, seed)
sandbox-tests/vm-cells/<cellKey>/
  cell.json        generation record: the first cell id that asked for it, options, seed, pin,
                   toolchain, ok or the error
  source.js        the program encoded
  raw.js           encoder output with its instruction listing
  encoded.js       the input a cell decodes (listing comment removed)
  decoded.js       the last run's decode
  result.json      the last run's diagnostic, first refusing reader, checks, opcodes, sizes, behaviour
```

A failed generation is not cached, so a timeout or a missing JDK is retried. `decoded.js` and
`result.json` are rewritten by every run, a run over broken decoder code included: decode afresh
when measuring. Cells are shared by key, not by name: two suites that encode one source with the
same options and seed read one directory, so look a cell up through `expandCells()` in
`support/cells.js`, never by the id in `cell.json`. `VM_FRESH_SEEDS=N` adds N random seeds per source, recorded in each `cell.json`
(CI runs with 1); a fresh cell the decoder fails is kept by adding its seed to the suite, and one
whose encoded program fails is dropped as above. `VM_CELLS=<regexp>` runs the cells whose id
matches.

**Quick runs** use one suite folder (`npx vitest run test/vm/jsconfuser-vm/cell-suites/<suite>`)
or `VM_CELLS`; `npm test` is the full suite and the one to pass before a commit.

#### Input cells and layered inputs

The tests that are not cells but read encoder output read **input cells**: cells listed in
`inputCells` (`support/cells.js`) by source, profile and seed, in the same cache. Vitest's global
setup (`support/generate-input-cells.js`) generates them before any test file runs, so those tests
run no encoder; a test looks its input up with `inputPath(name, profile, seed, { listing })`, where
`listing` gives the encoder's output with its instruction listing.

A real example: the sequential test's numeric input is `inputPath('f-literals-order', 'baseline', 1)`,
the `f-literals-order` program encoded with every option off; the baseline options draw no
randomness.

**Layered inputs** are the one committed encoder output: the second encoder's (js-confuser's) output
over a VM layer, which the cell tools cannot regenerate. `layered-inputs/<program>/` holds one
file per outer configuration, named for it, and a `generation.json` naming its program in `sources/`,
both encoders' revisions and options and the seed of the encoder randomness. The VM layer itself,
where a test reads it, is an input cell.

There are no fixture recipes, corpus folder, qualification or provenance records, or ignore list of
generated paths: every program is in `sources/` and every other encoded input is a cell.

#### The cell scripts

[`scripts/jsconfuser-vm-cells/`](../../decoder/decode-js/scripts/jsconfuser-vm-cells/) is what the
cell tests stand on: it fetches the pinned encoder, encodes one source reproducibly, and inspects
a decode's output. It decodes nothing itself.

**The encoder.** `fetch-encoder.mjs` clones the encoder at `PIN` (`audit.mjs`) into the ignored
`sandbox-tests/js-confuser-vm` and installs its runtime dependencies with `npm install --omit=dev`.
The encoder tracks no lockfile and its dependencies are ranges, so their versions are whatever
resolves at install: the tests judge a decode against its source, never against encoded bytes, and
hold under any of them. The cell key reads the tree npm recorded at install
(`node_modules/.package-lock.json`, `installedTree`), so cells encoded under another tree are a
miss; the record is copied once to `vm-cells/encoder-dependencies/<digest>.json` and each
`cell.json` names its digest. A row that pins a seed for a shape holds that shape only under the
tree it was chosen with; its proof's break is what shows the shape is still there.
`JSCONFUSER_VM_ENCODER` names another checkout. Before generating, the tests
refuse either at a commit other than `PIN` or with a dirty worktree (`ensureEncoder`). `PIN` must
equal the hub's encoder pin. Node and the JDK are not pinned; their major versions are in the cell
key.

**Generation.** One encoding runs in its own worker process, so an encoder that hangs or alters
globals cannot reach the test:

```text
runWorker({ action: 'generate', source, options, seed }, timeoutMs):     # explanatory pseudocode
  spawn worker.mjs --worker in its own process group; write the request to its stdin
  after timeoutMs: SIGKILL the group
  on close: the worker's record { ok: true, result: { raw } } or { ok: false, error };
            with no readable record, { ok: false, error, exit: { exitCode, signal, timedOut, stderr } }
worker, generationSession:
  load the encoder's source at the pin (src/index.ts, through Node's type stripping)
  Math.random = mulberry32(seed) for the call; PATH gains the JDK's bin
  each Closure process is killed after 60 seconds
  minify: exactly one Closure process must have run and exited 0, else the encoding fails
  restore everything replaced, also on failure
```

A recipe of source, options and seed therefore gives the same bytes on every machine with the
same Node and JDK majors. The JDK is `JAVA_HOME`, else the first `java` on `PATH` that resolves
into a JDK (a directory with a `release` file; a launcher stub does not). The cell tests give a
generation 65 seconds. Requests and results cross the process boundary through `codec.mjs`, which
keeps what JSON loses (undefined, holes, NaN, -0, non-enumerable keys, Map and Set) and throws on
what it cannot carry (accessors, symbol keys, opaque prototypes, cycles).

**Output checks.** `inspectCurrent(encoded)` runs the public entry on one input and returns:

```text
publicRecord     the entry's record
analysis         the frontend driver's record for the same input
checks           outputChecks of the output; { ok: false, declined: true } on a decline
inputState       the input's AST and its derived state are unchanged by the container extraction
firstBoundary    the first reader that refuses the raw input (container, wordcode, references,
                 frontend, entry), or null; for PATCH input that is read-wordcode
```

`outputChecks(output, input, result)` is `ok` only when all of these hold. It is the test of
decoding against passthrough, which behaviour alone cannot give:

| Check | Holds when |
|---|---|
| `fresh` | The output differs from the input, as text and as printed trees |
| `outputIdentity` | `result.output` is the output |
| `complete` | The result's schema is `jsconfuser-vm-standalone.v3` |
| `recoveredCoverage` | `coverage` equals the counts; `emitted + safelyEliminated + provenUnreachable` equals the instruction count; there is one `statements` entry and one recovered function (the root declaration `__recovered_function_<id>` or a function written inside it) per function that is not unreachable |
| `derivedState` | The output's scope state equals a fresh parse's, with no node shared between two places and no reference to a node outside the tree |
| `residue` empty | No array equal to the input's word array; no `switch` in a loop whose discriminant reads an advancing stream cursor, or is a variable assigned numeric literals inside it; none of the runtime's names nor `__recovered_pc`, `__recovered_dispatch`; no `eval` or `Function` call; no payload still connected to a decoder (`runtimeLayout`) |

An ordinary `switch` of the compiled program passes: it reads no stream cursor.

**Numeric transport.** `runtimeLayout(source)` (`layout.mjs`) finds a payload reached through the
encoder's numeric transport, for the last residue check. It follows only a stable, top-level,
once-used decoder with the pinned complete body, a stable disabled mode, the connected base64
helper and a numeric payload used only by that call. The base64 helper is recognized by
`runtimeSignature` (`runtime-source-signature.js`): a digest of its parameters and body with
positions and comments dropped and bindings numbered, compared with `BASE64_SHA256`. The digest is a matcher for a
structure in a program under test, not the identity of a tracked file. `diagnoseRuntimeLayout` names each
mismatch (`numeric-transport-binding`, `-body`, `-call`, `-helper`, `-mode`, `-payload`, or
`unconnected-layout`).

| Script | Exports | Used by |
|---|---|---|
| `audit.mjs` | `PIN`, `ENCODER_REPOSITORY`, `decoderRoot`, `encoderRoot`, `javaRoot`, `sha256` | `support/cells.js`, the worker, `fetch-encoder.mjs`; CI keys the encoder cache on this file and `fetch-encoder.mjs` |
| `config.mjs` | `baselineOptions` | `support/cells.js` |
| `fetch-encoder.mjs` | `fetchEncoder()`, `installedTree`; run directly, it fetches | `support/cells.js` |
| `run-worker.mjs` | `runWorker(request, timeoutMs, hooks)`; `hooks` replace spawn, kill and timers in its test | `support/cells.js` |
| `worker.mjs` | none: the `--worker` entry, one action `generate` | `runWorker` |
| `generation.mjs` | `generationSession(request, { loadCompiler, loadEncoder, setTimer, clearTimer })` | the worker, its test |
| `codec.mjs` | `tagged`, `exactEqual`, `stringifyRecord`, `parseRecord` | the worker, `runWorker`, `oracles.mjs` |
| `oracles.mjs` | `inspectCurrent(source, adapter)`, `outputChecks(output, input, result)` | `support/cell-tests.js` |
| `layout.mjs`, `runtime-source-signature.js` | `runtimeLayout`, `diagnoseRuntimeLayout`; `runtimeSignature`, `BASE64_SHA256` | `oracles.mjs` |

| Scenario | Expected result | Committed test (`test/scripts/jsconfuser-vm-cells/`) |
|---|---|---|
| undefined against null, holes, NaN, -0, infinities; own data keys, non-enumerable keys and collection extras | Kept across a round trip; an accessor is refused, never invoked | codec.test.js |
| A seed, twice | The same draws; `Math.random`, `PATH` and the Closure runner restored | run-worker.test.js |
| A minify encoding whose Closure process fails or times out | The encoding fails | run-worker.test.js |
| A worker that outlives its timeout; a worker that cannot spawn | The group is killed and the run keeps its exit; the spawn error is resolved at close | run-worker.test.js |
| A renamed numeric dispatcher passed through as output; a surviving dispatch or fallback; a user `switch` | Refused; refused; accepted | oracles.test.js |
| The numeric transport with its exact decoder, helper, mode and payload bindings; each one damaged | Followed; each damage refuses with its named diagnostic | layout.test.js |

Limits: the behaviour runs use Node's `vm` context, which separates globals and is no security
sandbox, so only committed sources and their encodings run there. The decoder's own residue gate
is narrower than `outputChecks` ([standalone-decode](vm/jsconfuser-vm/standalone-decode.md#2-algorithm)).

#### Unit, entry-point and support tests

| Folder | Tests |
|---|---|
| `jsconfuser-vm/single-component/` | `normalize-source`, `extract-container`, `read-wordcode`, `validate-references`, `partition-functions`, `finally-continuations` and the lowering (`numeric-to-vm-switch`) on hand-written input: refusal of ordinary or malformed input, an unchanged input and deeply frozen output; `handler-effects` on a hand-written minified handler pair |
| `switch/single-component/` | The shared backend on supplied typed models, one file per stage: `values.test.js` (copy coalescing, literal reads, folds, dead definitions, conditional values), `emit.test.js` (the source-switch model, `DEBUGGER` emission, refusal of work after a handler pop, a retained catch dispatch), `model.test.js` (unreachable code), `statements/<module>.test.js` (loop ends, switches, try ends, conditionals) |
| `jsconfuser-vm/public-entry-points/` | The plugin's independence from a debug comment, CLI output and sidecar paths, the registered CLI against direct diagnosis, the sequential target's rollback and publication over input cells and layered inputs, and the debugger policy |
| `jsconfuser-vm/support/` | `harness.test.js` proves the harness's residue, derived-state and debug-comment detectors can fail |

#### Where a claim's evidence lives

This file is not a claim index. An owner doc's `## Fixtures` names the suites whose cases pin its
claims, and each suite's `proofs` names the break that turns them red. A claim no suite holds says
so there. Behaviour alone does not tell decoding from passthrough; the output checks do: they
refuse a decode that keeps the source's word array, a dispatch over a numeric stream or an opaque
state, or a name of the encoder's runtime.

## Testing against real encoder output

The fixtures above are frozen samples; the loop that *finds* the bugs they then guard is a
live one, and it is worth running directly whenever a decode is in question:

1. **Encode with the real encoder** — `encoder/js-confuser`'s built `dist/index.js`
   `obfuscate`, or its CLI. Its output is randomized per run and many transforms are
   probability-gated, so repeat any verdict you intend to act on
   ([M4](../decoding-method/with-encoder.md#m4)).
2. **Decode with the plugin** — `PluginJsconfuser` imported directly, or `node src/main.js
   -t jsconfuser`.
3. **Run the decoded output and compare its runtime result to the original source's.**

Only the full encode → decode → run comparison surfaces combination bugs, and two harness
details are required for the comparison to be valid at all:

- **capture output by patching the real `console.log`.** GlobalConcealing rewrites `console`
  into a global lookup, so a `console` injected through `new Function`'s scope is never the
  one the decoded program reaches, and the capture comes back silently empty.
- **parse decoded output with `allowReturnOutsideFunction: true`.** The `pack` wrapper
  leaves a legitimate top-level `return` behind.

## What the suite still does not cover

**`src/main.js`'s CLI wiring.** Every jsconfuser case imports `PluginJsconfuser` and calls it
directly, never `-t jsconfuser`, so the dispatch path from argv to plugin is exercised by
nothing. That matters because it is half of a real incident: the whole plugin was once silently
broken by a stale CJS-interop import shim, invisible to a suite that only drove visitors. The
plugin half of that gap is closed — `jsconfuser.test.js` runs `PluginJsconfuser` itself over the
committed fixture triples, so an entry-point break now fails the suite — but a broken `-t`
mapping would still land green. One CLI smoke run closes it.

### There is no `test/obfuscator/`, and that is a decision

**`obfuscator` is frozen** ([decode-js.md](decode-js.md#obfuscator-is-frozen-obfuscatorx-is-where-its-target-is-worked-on)),
so the regression baseline that directory was opened to build was never built, and the directory is
gone. Worth recording as a reversal rather than letting the absence read as an oversight: the plan
was sound while that entry was still expected to change, and it stopped being sound the moment it
was not. **A regression baseline's only job is to catch a change.**

- **The uncovered pieces stay uncovered by decision, not as a gap.** The three string-array
  detectors, the calls-wrapper sub-shapes and the anti-tamper strippers are *described* instead, in
  [plugins/obfuscator.md](plugins/obfuscator.md), and that description is the deliverable.
- **Its one case was migrated rather than deleted, on coverage grounds rather than sentiment.**
  `2.19.0-dead-code-control` now lives in `test/obfuscatorx/`, because it carries two things that
  suite lacked: an **isolated-feature** profile — the string-array base plus dead-code injection and
  nothing else, so a failure implicates that reversal specifically where an `all-on` failure
  implicates everything — and the only plugin-level case on the `control` input, the one with
  branches, a loop and a `switch`.
- **Its golden was re-earned, not copied.** The old entry's expected output is *that entry's*
  behaviour. Run through the refusing builder against `obfuscatorx`, the two differ in exactly one
  place and the new entry is the better of the two there: it reverses the encoder's
  conditional-to-statement collapse back into an `if`/`else` where the old one leaves
  `i % 2 === 0 ? acc += i : acc -= i;` standing. **A migrated fixture is a new fixture** — carrying
  a golden across entries would have pinned one plugin to another's behaviour.
- **The bar a cell had to clear is kept**, because `obfuscatorx`'s fixtures inherit it: a cell
  graduates only once something has certified the decode is *right*, never merely that it
  completed. Exact string equality makes a buggy-but-plausible golden look authoritative, which is
  worse than having no fixture at all.

## CI (`.github/workflows/test.yml`)

"Unit Tests" runs on push / PR to `main`: Node **26** with npm cache, `npm ci` with
`npm_config_build_from_source: true` (so `isolated-vm`'s native module builds reliably),
`npm run format` and `npm run lint`, a JDK (`actions/setup-java`, Temurin 21) for minify cells, the encoder checkout and `sandbox-tests/vm-cells`
restored from `actions/cache` (a cell whose key did not change is reused from any earlier entry),
`npx vitest run` with `VM_FRESH_SEEDS=1` (with `always()` so a report posts even on failure), then
`davelosert/vitest-coverage-report-action` publishes the coverage summary as a PR comment, and the
generated cells (source, encoded, `cell.json`, decoded, `result.json`) upload as the `vm-cells`
artifact, kept 90 days.
