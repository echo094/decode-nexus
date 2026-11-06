# Test Suite Reference (`decoder/decode-js/test/`)

A [Vitest](https://vitest.dev/) suite spanning end-to-end plugin fixtures, per-visitor
fixtures, and the jsconfuser
combination fixtures below. Every case is fixture-driven: a `.js` input is transformed and
its output compared to either the input itself (no-op expected) or a `.fix.js` golden file.

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
global setup runs first: it regenerates the committed fixtures' encoded VM inputs ([generated
fixture inputs](#generated-fixture-inputs)), so a run needs the pinned encoder checkout and, for
minify cells, a JDK on `PATH`. The one exclude added to Vitest's defaults is the ignored
qualification workspace that
[fetch-encoder.mjs](../../decoder/decode-js/scripts/qualify-jsconfuser-vm/fetch-encoder.mjs) clones
encoder checkouts into; their own suites are not decoder tests. Child processes: the
`public-entry-points/` files `cli.test.js` and `sequential.test.js` launch `src/main.js` with no
subprocess timeout and `integration.test.js` with 30 s; `test/scripts/render-vm-switch.test.js`
launches the render script without one; the cells generate through the qualifier's worker, 65 s
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

`qualify-jsconfuser-vm/` tests the [VM qualifier](vm/jsconfuser-vm/qualify-jsconfuser-vm.md#finite-minified-class-qualification) in
`scripts/qualify-jsconfuser-vm/`: its lossless codec, output-structure and replay oracles,
option-effect and damage controls, publication/recovery boundaries and generation journal, all
without generating encoder output. `replay.test.js` runs retained known-source fixtures in a fresh
Node VM context. The qualifier's Python capture and evidence-retention helpers keep their
`unittest` tests beside them (`python3 -m unittest discover -s scripts/qualify-jsconfuser-vm`).

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

Triples driven through `PluginObfuscatorx` itself, so a break in the entry — the pass order, the
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
[encoder-decoder-method.md](../encoder-decoder-method.md)'s "unit to combo".

**Fixtures come in triples, not pairs.** Alongside `<name>.js` (obfuscated input) and
`<name>.fix.js` (expected output), a jsconfuser fixture keeps `<name>.src.js`: the
pre-obfuscation source it was generated from. `helper.js` does not read it — it is what
makes a fixture reviewable for decode *quality* (is the output readable, or merely
self-consistent?) rather than only for equality, and it is what keeps
[M2](../encoder-decoder-method.md#m2-measure-residue-what-an-encoder-stage-added-and-the-decode-left) size ratio computable later.
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
| Unit | One decoder component | Hand-written records or source; **no compiler input** | `single-component/` |
| Stage | The compiler plus one encoder stage | Generated cells | a suite under `generated-cells/` |
| Combination | The compiler plus several stages | Generated cells | a suite under `generated-cells/` |

**A unit test has no compiler in it, whatever it calls.** Its input is written by hand in the test:
a boot whose words hold `window.TEST_OUTPUT = 1 + 2`, a minified handler pair, a typed switch
model. A test that feeds a component the encoder's output is a stage or combination test, whichever
component it calls, and is written as a suite. The public entry points (`public-entry-points/`:
plugin, CLI, sequential target, debugger policy) are tested over committed fixture inputs.

```text
test/vm/
├── fixture-recipes.js, materialize-fixtures.js    regenerate fixtures' encoded inputs (below)
├── fixture-recipes.test.js                        the ignore list equals the recipe set
├── switch/single-component/                       unit: the shared backend on typed models
└── jsconfuser-vm/
    ├── generated-cells/<suite>/                   one folder per suite
    │   ├── suite.js                               the suite's definition
    │   └── <file>.test.js                         one per entry in suite.js `files`
    ├── sources/<name>/source.js                   programs the cells encode (oracle.json if needed)
    ├── stage-effect/<suite>.test.js               one per stage suite: the stage changes the program
    ├── support/                                   cell runner, cross-suite checks, harness, oracle
    ├── single-component/                          unit: numeric frontend components
    ├── public-entry-points/                       plugin, CLI and sequential behaviour
    └── fixtures/                                  committed inputs of the entry-point, readability
                                                   and qualifier tests
```

Name files and folders for the behaviour they test, never for a task ID, sequence number or trial
attempt. Nothing under `test/vm/` carries a hash of tracked bytes
([Git identifies tracked bytes](../doc-conventions.md#where-facts-live)).

#### Suites

A suite is one folder, `generated-cells/<suite>/`, holding its own definition in `suite.js`.
Nothing defines a suite elsewhere, and suites are never merged: each scenario and each chain is its
own suite. `support/cells.js` collects the folders only for what crosses suites (the cache and the
distinctness checks below).

```js
// generated-cells/<suite>/suite.js (explanatory shape)
export default {
  name,               // the folder name
  protects,           // what a red case means; ends "Proved: …" once a break has shown it
  files: {            // one test file per key: <key>.test.js
    [file]: [{ sources, profile, seeds }],  // sources × seeds, all under one profile
  },
  cases,              // optional: protects text per source, where sources protect different things
  proofs,             // optional: [{ claim, file, code }], the decoder code a break turned red
  indicators,         // optional: per source, form indicators its decode must share with it
  inertControls,      // optional: sources the stage must leave unchanged
}
```

A profile is `baseline` or `+`-joined option names over the qualifier's explicit-false baseline
(`name=N` sets a number). A test file is three lines: it imports its `suite.js` and calls
`defineCellTests(suite, '<file>')` from `support/cell-tests.js`. A real example, `try-arm-exits`:

```js
export default {
  name: 'try-arm-exits',
  protects:
    "A try that never completes normally inside a conditional arm leaves through the arm with no label. Proved: the try end in a conditional's arm in vm-switch-statements.",
  files: { cells: [{ sources: ['try-arm-exits'], profile: 'baseline', seeds: [1] }] },
  proofs: [
    {
      claim: 'try-arm-exits',
      file: 'src/vm/switch/vm-switch-statements.js',
      code: 'reached.get(fallthroughId).has(tryEnd) &&',
    },
  ],
}
```

Its cell `try-arm-exits/cells/try-arm-exits/baseline/1` encodes `sources/try-arm-exits/source.js`
with every option off at seed 1, decodes it, and runs source, encoded and decoded programs.
Deleting the condition the proof names changes the decoded program and turns the case red; that
break is what earned the Proved line.

**What a suite holds.** A test stays only if a break in decoder code turns it red; reaching code
is not proof, and a break whose decoded output is unchanged proves nothing. `proofs` records the
code each break named, and a Proved line in `protects` or `cases` says it in words. A scenario
keeps the old test's scenario, never its encoded bytes. The suites by shape:

| Suite | Shape |
|---|---|
| `compiled-forms` | One test file per JavaScript form family (control, expressions, functions, data, host effects), plain compiled code |
| `compiled-forms-canonical-opcodes` | One representative per form family under the baseline options, opcodes unrandomized |
| `single-payload-stage` | One test file per payload stage, the fewest sources that reach its decoder step |
| `single-payload-stage-conditions` | One test file per stage: sources each built for one condition of that stage's decoder |
| `<stages>-chain` | Several stages in encoder order over the compiled-forms representatives, seeds 251-253 |
| `<rewrite>-over-<stage>` | An interpreter rewrite (handler table, class rewrite, minify) over one opcode stage |
| `all-stages-together` | Every option at once, one test file per source |
| `interpreter-rewrite-fixed`, `-seeded` | A rewrite of the interpreter alone; the decode must equal the plain decode |
| One scenario | A single decoder rule on its own source and seed (`try-arm-exits`, `anti-macro-route`, …) |
| `open-decoder-gaps` | What is red today, one test file per open issue |
| `whole-programs` | Two whole programs under randomized opcodes |

`open-decoder-gaps` cases are ordinary tests that stay red until their issue is fixed; they carry no
`test.fails` or expected-decline marking. A fixed case moves to its natural suite. A gap that a red
check finds becomes a suite of the chain's shape.

#### What every cell checks

```text
defineCellTests(suite, file), for each cell (suite, file, source, profile, seed):
  beforeAll: generate the missing cells                 # pinned encoder, ignored cache
  if suite is single-payload-stage:
    run that stage's decoder step alone on the encoded input; it must remove its stage
  test "decodes with the source behaviour: <protects>":
    generation succeeded
    public decode (inspectCurrent) accepts
    the qualifier's output checks pass; the input AST is unchanged
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
program a stage step and an interpreter rewrite are compared with. A source whose encoded program
does not behave as the source under a suite's profile is no cell of that suite: the encoder's own
failure leaves the encoded-equals-source check nothing to compare, so the cell is dropped, never
exempted.

`support/distinct-cells.test.js` checks what crosses suites, decoding nothing: every `files` key has
its test file and every test file a key; every cell says what it protects; every `proofs` entry's
code still stands in its file (re-prove a protection when its code changes); no two cells encode
the same text; an inert control's payload equals its plain cell's; and every stage suite
(`single-payload-stage` and the payload chains) has its `stage-effect/<suite>.test.js` and every such
file a stage suite.

`stage-effect/<suite>.test.js` calls `defineStageEffectTests(suite)` from `support/stage-effect.js`:
each of that suite's cells must have a payload, the container's words and constant pool, unlike its
plain cell's. The check has one file per stage suite so Vitest spreads it over its workers and no
single test carries every stage cell under the global time limit.

#### Sources and the cell cache

A cell's program is `sources/<name>/source.js`; while a corpus fixture of that name still exists,
`fixtures/` supplies it, and `sources/` wins where both do. `oracle.json` beside a source is needed
only for a special host or a committed expectation.

```text
cellKey = sha256(PIN, encoder lock, Node major, JDK major if minify, sha256(source), options, seed)
sandbox-tests/vm-cells/<cellKey>/
  cell.json        generation record: options, seed, pin, toolchain, ok or the error
  raw.js           encoder output with its instruction listing
  encoded.js       the input a cell decodes (listing comment removed)
  decoded.js       the last run's decode
  result.json      the last run's diagnostic, first refusing reader, checks, opcodes, sizes, behaviour
```

A failed generation is not cached, so a timeout or a missing JDK is retried. `decoded.js` and
`result.json` are rewritten by every run, a run over broken decoder code included: decode afresh
when measuring. `VM_FRESH_SEEDS=N` adds N random seeds, recorded in each `cell.json`; a fresh cell
the decoder fails is kept by adding its seed to the suite, and one whose encoded program fails is
dropped as above. `VM_CELLS=<regexp>` runs the cells whose id
matches.

**Quick runs** use one suite file (`npx vitest run test/vm/jsconfuser-vm/generated-cells/<suite>`)
or `VM_CELLS`; `npm test` is the full suite and the one to pass before a commit.

#### Unit, entry-point and support tests

| Folder | Tests |
|---|---|
| `jsconfuser-vm/single-component/` | `extract-container`, `read-wordcode`, `validate-references`, `partition-functions` and the numeric handoff on a hand-written boot: refusal of ordinary or malformed input, an unchanged input and deeply frozen output; `handler-effects` on a hand-written minified handler pair |
| `switch/single-component/` | The shared backend on supplied typed models: `DEBUGGER` emission, copy coalescing, refusal of work after a handler pop, a dispatch-free emission and a retained catch dispatch |
| `jsconfuser-vm/public-entry-points/` | The plugin's independence from a debug comment, CLI output and sidecar paths, the registered CLI against direct diagnosis, the sequential target's rollback and publication, and the debugger policy |
| `jsconfuser-vm/support/` | `harness.test.js` proves the harness's residue, derived-state and debug-comment detectors can fail; `readability.test.js` reads the readability fixtures' metrics against their baseline |

#### Generated fixture inputs

The entry-point, readability and qualifier tests read committed fixtures under `fixtures/`. Their
encoded inputs are generated, not committed: a fixture keeps its source and the recipe its own
metadata records, and the global setup regenerates the bytes with the pinned encoder before any
test reads them.

```text
setup (test/vm/materialize-fixtures.js), before any test file:
  for each recipe in fixtureRecipes():              # test/vm/fixture-recipes.js
    if recipe.file is absent:
      take the cell for (source, options, seed) from the cell cache, generating it if missing
      copy encoded.js (listing comment stripped) or raw.js (listing kept) to recipe.file
```

A real example: `fixtures/corpus/raw/f-expression-values/` commits `source.js` and `oracle.json`.
Its recipe is that source with the baseline options, which draw no randomness; setup writes
`encoded.js` from the cached cell.

| Metadata a fixture directory carries | Recipe it yields |
|---|---|
| `qualification.json`, `qualification-N.json` | `source.js` with the record's options and seed, to `encoded[-N].js` |
| `generation.json` `cells` / `files` | each cell's or file's source, options (over the encoder options) and seed; `listing` keeps the comment |
| `provenance.json` `records` / `fixtureRows` | each row's encoded file from its source or qualifier case, options and seed |
| `readability/manifest.json` | each case's `source.js` with the manifest options, listing kept |
| a corpus `source.js` | baseline options |

Ownership is explicit: `test/vm/.gitignore` lists exactly the generated paths (rewrite it with
`node test/vm/materialize-fixtures.js --write-ignore`), and `fixture-recipes.test.js` fails when the
list drifts or an encoded input has neither a recipe nor a place in its short committed list (the
second encoder's layered outputs and one ordinary non-VM input). A file already present is left
alone; deleting it regenerates it. A fixture stays only while a test reads it.

The encoder comes from
[fetch-encoder.mjs](../../decoder/decode-js/scripts/qualify-jsconfuser-vm/fetch-encoder.mjs), which
clones the pin and installs from the committed `encoder-lock.json` with `npm ci`: the encoder tracks
no lockfile and its dependencies are ranges, so without it a fresh clone could encode differently.
`JSCONFUSER_VM_ENCODER` names another checkout; either is refused at another commit or with a dirty
worktree. Node and the JDK are not pinned; their major versions are in the key.

#### Where a claim's evidence lives

This file is not a claim index. An owner doc's `## Fixtures` names the suites whose cases pin its
claims, and each suite's `proofs` names the code a break turned red. A claim no suite holds says
so there. Behaviour alone does not tell decoding from passthrough; the output checks do: they
refuse a decode that keeps the source's word array, a dispatch over a numeric stream or an opaque
state, or a name of the encoder's runtime.

## Testing against real encoder output

The fixtures above are frozen samples; the loop that *finds* the bugs they then guard is a
live one, and it is worth running directly whenever a decode is in question:

1. **Encode with the real encoder** — `encoder/js-confuser`'s built `dist/index.js`
   `obfuscate`, or its CLI. Its output is randomized per run and many transforms are
   probability-gated, so repeat any verdict you intend to act on
   ([M3](../encoder-decoder-method.md#m3-freeze-the-corpus)).
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

## Retired document-first verifiers

The VM docs in this package cite *retired* frozen, immutable or bounded verifiers. Each was a
one-off document-first reconstruction, built from these docs before source consultation to test
whether they sufficed, and was retired once its accepted findings graduated into the docs. A claim
citing one is a historical result: nothing re-runs it and its retained inputs are not available.
Only the committed tests indexed here are maintained evidence.

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
a JDK (`actions/setup-java`) for minify cells, the encoder checkout and `sandbox-tests/vm-cells`
restored from `actions/cache` (a cell whose key did not change is reused from any earlier entry),
`npx vitest run` with `VM_FRESH_SEEDS=1` (with `always()` so a report posts even on failure), then
`davelosert/vitest-coverage-report-action` publishes the coverage summary as a PR comment, and the
generated cells (source, encoded, `cell.json`, decoded, `result.json`) upload as the `vm-cells`
artifact, kept 90 days.
