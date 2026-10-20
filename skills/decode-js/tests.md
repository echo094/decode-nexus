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
  figure. A Node VM `timeout` inside a test bounds target execution and is a different setting.

- **The light run, `npm run test:light`** (`vitest.light.config.js`), is the default config minus
  a `heavy` list of files that dominate its time: stacked-option combinations, large retained-cell
  populations and the native record replay. It is for the edit loop. `npm test` stays the full
  suite and is the one to pass before a commit. A file joins the list for its cost, never because
  it fails, and the list lives only in that config. The axis that justifies an entry is the
  file's share of run time against the `src` lines only it covers, read by a coverage run with
  and without it, never a remembered figure.

**What a run executes, and what Vitest's timer cannot stop.** There are no `pretest`/`posttest`
scripts, setup files or include overrides, so default discovery picks up every `*.test.js` under
`test/`. The one exclude added to Vitest's defaults is the ignored qualification workspace that
[fetch-encoder.mjs](../../decoder/decode-js/scripts/qualify-jsconfuser-vm/fetch-encoder.mjs)
clones encoder checkouts into; their own suites are not decoder tests. Three entries launch `src/main.js` as a child process — `integration/cli.test.js` and
`integration/sequential.test.js` with no subprocess timeout, `integration/integration.test.js`
with 30 s — and `test/scripts/render-vm-switch.test.js` launches the render script, also without
one. Vitest's per-test timer cannot interrupt synchronous decoder work, a direct `Function` call,
an `isolated-vm` `evalSync` without its own limit, or a Node VM call without a `timeout` option.
A supervised run therefore needs an outer process-group deadline; a test summary on stdout
without an observed process exit earns no credit. To keep the CLI/backend entries out, pass
each of the three integration paths to `--exclude`.

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

`render-vm-switch.test.js` exercises the saved-model and source-input forms of
[`scripts/render-vm-switch.mjs`](vm-switch-boundary.md#inspecting-the-switch-handoff).
It checks the generated switch text, compares the encoded and step-one arithmetic programs
under the same host bindings, and refuses to overwrite an existing artifact. Tests for
`src/utility/` remain in `test/utility/`.

`qualify-jsconfuser-vm/` tests the [VM qualifier](#finite-minified-class-qualification) in
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
| `split-assignment.test.js` | [split-assignment](visitors/split-assignment.md) | `call-valid-1`, `if-assignment-valid`, `if-member-valid`, `member-valid-1`, `variable-valid` (valid); `if-invalid`, `variable-invalid` (no-op) |
| `split-variable-declarator.test.js` | [split-variable-declarator](visitors/split-variable-declarator.md) | `init-valid-1` (valid); `parent-invalid`, `init-invalid` (no-op) |
| `parse-control-flow-storage.test.js` | [parse-control-flow-storage](visitors/parse-control-flow-storage.md) | `object-invalid-1` (no-op); `nested-delegating-wrapper-outer-first` pins the current outer-first traversal dependency and one binary resolving path |
| `merge-object.test.js` | [merge-object](visitors/merge-object.md) | ObjectPattern/ArrayPattern declarators (no-op); Identifier declarator merge (valid) |

Concrete examples of what the fixtures pin down:

- **split-assignment `call-valid-1`** — hoists assignments buried in a computed
  member/callee chain into ordered statements (`d = _; b = d[d("1")]("2"); x[…] = …`),
  exactly the [split-assignment](visitors/split-assignment.md) `getInsertPath` behavior.
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

Focused component tests mirror the source modules under `test/vm/jsconfuser-vm/` and
`test/vm/switch/`. Behavior tests spanning the plugin, CLI, corpus harness, readability,
and sequential coordination live in `test/vm/jsconfuser-vm/integration/`. Their inputs
are in the adjacent `fixtures/` tree. **A fixture follows the decoder file layout:** it lives
under the test tree of the module whose rule it pins, in a folder named for that module, even
when its input is a frontend's encoded output. A shared-backend rule's fixtures sit in
`test/vm/switch/fixtures/<module>/<family>/`, not with the frontend whose encoder built them. The removed private VM-2 trial has no tests or
implementation here. A future independent VM-2 benchmark needs a generated fixture
with provenance alongside its decoder test.

```text
test/vm/
├── jsconfuser-vm/
│   ├── *.test.js       numeric frontend and standalone component contracts
│   ├── integration/    adapter, CLI, corpus, readability and sequential checks
│   └── fixtures/       reference, generated corpus, readability and sequential inputs
└── switch/             shared typed model and source emission
    └── fixtures/       <module>/<family>/: inputs pinning a backend module's rules
```

Name files and folders for the behavior they test, never for a task ID, sequence number,
or trial attempt. A fixture may include source, encoded input, oracle and expected result.
It carries no hash of tracked bytes ([Git identifies tracked bytes](../doc-conventions.md#where-facts-live)).
The record check `qualification-provenance.test.js` and the native replay
`qualification-replay.test.js`, sharing discovery in `qualification-records.js`, treat every
`qualification.json` or `qualification-N.json` as single-cell metadata with its own source, encoded input and observations, so an aggregate
record must take another name (the local exception population uses `native-qualification.json`).
Generated attempts and temporary review outputs belong outside the tracked test tree. The current corpus
manifest records a historical generation run; its named generator is absent, so fresh
coverage work must supply a maintained generator rather than claiming reproducibility.

| Test file | Scope |
|---|---|
| [`vm/jsconfuser-vm/analyze-closure-lifetimes.test.js`](../../decoder/decode-js/test/vm/jsconfuser-vm/analyze-closure-lifetimes.test.js) | Component |
| [`vm/jsconfuser-vm/analyze-exception-finally.test.js`](../../decoder/decode-js/test/vm/jsconfuser-vm/analyze-exception-finally.test.js) | Component |
| [`vm/jsconfuser-vm/analyze-property-collections.test.js`](../../decoder/decode-js/test/vm/jsconfuser-vm/analyze-property-collections.test.js) | Component |
| [`vm/jsconfuser-vm/analyze-scalar-values.test.js`](../../decoder/decode-js/test/vm/jsconfuser-vm/analyze-scalar-values.test.js) | Component |
| [`vm/jsconfuser-vm/build-call-frames.test.js`](../../decoder/decode-js/test/vm/jsconfuser-vm/build-call-frames.test.js) | Component |
| [`vm/jsconfuser-vm/build-cfg.test.js`](../../decoder/decode-js/test/vm/jsconfuser-vm/build-cfg.test.js) | Component |
| [`vm/jsconfuser-vm/decode-standalone.test.js`](../../decoder/decode-js/test/vm/jsconfuser-vm/decode-standalone.test.js) | Component |
| [`vm/jsconfuser-vm/diagnose-standalone.test.js`](../../decoder/decode-js/test/vm/jsconfuser-vm/diagnose-standalone.test.js) | Component |
| [`vm/jsconfuser-vm/emit-call-completion.test.js`](../../decoder/decode-js/test/vm/jsconfuser-vm/emit-call-completion.test.js) | Component |
| [`vm/jsconfuser-vm/emit-closure-exception.test.js`](../../decoder/decode-js/test/vm/jsconfuser-vm/emit-closure-exception.test.js) | Component |
| [`vm/jsconfuser-vm/emit-structured-control.test.js`](../../decoder/decode-js/test/vm/jsconfuser-vm/emit-structured-control.test.js) | Component |
| [`vm/jsconfuser-vm/extract-container.test.js`](../../decoder/decode-js/test/vm/jsconfuser-vm/extract-container.test.js) | Component |
| [`vm/jsconfuser-vm/runtime-finalizers.test.js`](../../decoder/decode-js/test/vm/jsconfuser-vm/runtime-finalizers.test.js) | Every timing value decodes to the disabled program, plus known-fixture native equality/poison and throwing-host-clock contrasts; bounded Node VM execution, no generated population credit |
| [`vm/jsconfuser-vm/runtime-finalizers.behavior.test.js`](../../decoder/decode-js/test/vm/jsconfuser-vm/runtime-finalizers.behavior.test.js) | Native: current recovery/refusal of retained finalizer profiles, independent current PATCH state, source/encoded/current fast/slow/supervised pause behavior; fresh browser-like VM limit 10 s, parent worker 12 s |
| [`scripts/qualify-jsconfuser-vm/timing.test.js`](../../decoder/decode-js/test/scripts/qualify-jsconfuser-vm/timing.test.js) | Emitted-effect detector (transport, table, timing scalar; shell located by Packet A and the handler locator) and known-source native stop/resume completion; includes a wrong-behavior oracle control |
| [`vm/jsconfuser-vm/numeric-to-vm-switch.test.js`](../../decoder/decode-js/test/vm/jsconfuser-vm/numeric-to-vm-switch.test.js) | Component |
| [`vm/jsconfuser-vm/partition-functions.test.js`](../../decoder/decode-js/test/vm/jsconfuser-vm/partition-functions.test.js) | Component |
| [`vm/jsconfuser-vm/read-wordcode.test.js`](../../decoder/decode-js/test/vm/jsconfuser-vm/read-wordcode.test.js) | Component |
| [`vm/jsconfuser-vm/validate-references.test.js`](../../decoder/decode-js/test/vm/jsconfuser-vm/validate-references.test.js) | Component |
| [`vm/jsconfuser-vm/vm-copy-simplification.test.js`](../../decoder/decode-js/test/vm/jsconfuser-vm/vm-copy-simplification.test.js) | Component |
| [`vm/jsconfuser-vm/analyze-anti-register-flow.test.js`](../../decoder/decode-js/test/vm/jsconfuser-vm/analyze-anti-register-flow.test.js) | Component |
| [`vm/jsconfuser-vm/analyze-anti-runtime.test.js`](../../decoder/decode-js/test/vm/jsconfuser-vm/analyze-anti-runtime.test.js) | Component |
| [`vm/jsconfuser-vm/integration/cli.test.js`](../../decoder/decode-js/test/vm/jsconfuser-vm/integration/cli.test.js) | Integration |
| [`vm/jsconfuser-vm/integration/harness.test.js`](../../decoder/decode-js/test/vm/jsconfuser-vm/integration/harness.test.js) | Integration |
| [`vm/jsconfuser-vm/integration/integration.test.js`](../../decoder/decode-js/test/vm/jsconfuser-vm/integration/integration.test.js) | Integration |
| [`vm/jsconfuser-vm/integration/plugin.test.js`](../../decoder/decode-js/test/vm/jsconfuser-vm/integration/plugin.test.js) | Integration |
| [`vm/jsconfuser-vm/integration/readability.test.js`](../../decoder/decode-js/test/vm/jsconfuser-vm/integration/readability.test.js) | Integration |
| [`vm/jsconfuser-vm/integration/sequential.test.js`](../../decoder/decode-js/test/vm/jsconfuser-vm/integration/sequential.test.js) | Integration |
| [`vm/jsconfuser-vm/runtime-binding-identities.test.js`](../../decoder/decode-js/test/vm/jsconfuser-vm/runtime-binding-identities.test.js) | Native: executes retained source, renamed encoded and decoded programs with window, host atob/btoa/Buffer and zero `performance.now()`, VM timeout 30 s |
| [`vm/jsconfuser-vm/owned-chain-source.test.js`](../../decoder/decode-js/test/vm/jsconfuser-vm/owned-chain-source.test.js) | Parser source-damage controls plus native behavior cases executing retained encoded and decoded programs with window, host Buffer and zero `performance.now()`, VM timeout 1 s |
| [`vm/jsconfuser-vm/exception-region-parser.test.js`](../../decoder/decode-js/test/vm/jsconfuser-vm/exception-region-parser.test.js) | Parser-only numeric source/public recovery, state and reaching region controls |
| [`vm/jsconfuser-vm/minified-class-admission.test.js`](../../decoder/decode-js/test/vm/jsconfuser-vm/minified-class-admission.test.js) | Parser-only source-entry admission and named B/C payload-damage refusals |
| [`vm/jsconfuser-vm/minified-class-frontend.test.js`](../../decoder/decode-js/test/vm/jsconfuser-vm/minified-class-frontend.test.js) | Parser-only source-entry admission and structured exception recovery |
| [`vm/jsconfuser-vm/randomized-class.test.js`](../../decoder/decode-js/test/vm/jsconfuser-vm/randomized-class.test.js) | Parser-only admission, canonical word meaning and remapping positives |
| [`vm/jsconfuser-vm/randomized-minified-class.test.js`](../../decoder/decode-js/test/vm/jsconfuser-vm/randomized-minified-class.test.js) | Parser-only admission, canonical word meaning and remapping positives |
| [`vm/jsconfuser-vm/minified-class-admission.behavior.test.js`](../../decoder/decode-js/test/vm/jsconfuser-vm/minified-class-admission.behavior.test.js) | Native: current public output of the local exception cells, with source and encoded input, in a fresh browser-like context (window/self, performance, atob/btoa; no Buffer), VM timeout 10 s |
| [`vm/jsconfuser-vm/qualification-provenance.test.js`](../../decoder/decode-js/test/vm/jsconfuser-vm/qualification-provenance.test.js) | Record consistency only: id, seed, target, status/diagnostic, effect-component logic, provenance flags and present source/encoded files; executes nothing |
| [`vm/jsconfuser-vm/qualification-replay.test.js`](../../decoder/decode-js/test/vm/jsconfuser-vm/qualification-replay.test.js) | Native: source and encoded programs of every retained record and focused oracle against their recorded observations, with window, atob/btoa and performance, VM timeout 30 s. Git fixes the bytes, so it detects a host change altering a frozen program; heavy |
| [`vm/jsconfuser-vm/class-runtime-combinations.test.js`](../../decoder/decode-js/test/vm/jsconfuser-vm/class-runtime-combinations.test.js) | Component; native callbacks execute retained programs with window, atob/btoa and performance, VM timeout 30 s |
| [`vm/jsconfuser-vm/encoded-bytecode-combinations.test.js`](../../decoder/decode-js/test/vm/jsconfuser-vm/encoded-bytecode-combinations.test.js) | Component; native callbacks execute retained programs with window, atob/btoa and performance, VM timeout 30 s |
| [`vm/jsconfuser-vm/minified-self-modifying-encoded.test.js`](../../decoder/decode-js/test/vm/jsconfuser-vm/minified-self-modifying-encoded.test.js) | Component; native callbacks execute retained programs with window, atob/btoa and performance, VM timeout 30 s |
| [`vm/jsconfuser-vm/normalize-alias-combinations.test.js`](../../decoder/decode-js/test/vm/jsconfuser-vm/normalize-alias-combinations.test.js) | Component; native callbacks execute retained programs with window, atob/btoa and performance, VM timeout 30 s |
| [`vm/jsconfuser-vm/normalize-aliased-wordcode.test.js`](../../decoder/decode-js/test/vm/jsconfuser-vm/normalize-aliased-wordcode.test.js) | Component; native callbacks execute retained programs with window and performance, VM timeout 1 s |
| [`vm/jsconfuser-vm/normalize-anti-concealed-constants.test.js`](../../decoder/decode-js/test/vm/jsconfuser-vm/normalize-anti-concealed-constants.test.js) | Component; native callbacks execute retained programs with window, atob, host Buffer and performance, VM timeout 10 s |
| [`vm/jsconfuser-vm/normalize-anti-routing-combinations.test.js`](../../decoder/decode-js/test/vm/jsconfuser-vm/normalize-anti-routing-combinations.test.js) | Component; native callbacks execute retained programs with window, atob, host Buffer and performance, VM timeout 30 s |
| [`vm/jsconfuser-vm/normalize-anti-specialized-combinations.test.js`](../../decoder/decode-js/test/vm/jsconfuser-vm/normalize-anti-specialized-combinations.test.js) | Component; native callbacks execute retained programs with window, atob, host Buffer and performance, VM timeout 30 s |
| [`vm/jsconfuser-vm/normalize-anti-wordcode.test.js`](../../decoder/decode-js/test/vm/jsconfuser-vm/normalize-anti-wordcode.test.js) | Component; native callbacks execute retained programs with window and performance, VM timeout 1 s |
| [`vm/jsconfuser-vm/normalize-cff-wordcode.test.js`](../../decoder/decode-js/test/vm/jsconfuser-vm/normalize-cff-wordcode.test.js) | Component; native callbacks execute retained programs with window, host Buffer and performance, VM timeout 1 s |
| [`vm/jsconfuser-vm/normalize-concealed-constants.test.js`](../../decoder/decode-js/test/vm/jsconfuser-vm/normalize-concealed-constants.test.js) | Component; native callbacks execute retained programs with window, host Buffer and performance, VM timeout 1 s |
| [`vm/jsconfuser-vm/normalize-dispatcher-wordcode.test.js`](../../decoder/decode-js/test/vm/jsconfuser-vm/normalize-dispatcher-wordcode.test.js) | Component; native callbacks execute retained programs with window, host Buffer and performance, VM timeout 1 s |
| [`vm/jsconfuser-vm/normalize-macro-combinations.test.js`](../../decoder/decode-js/test/vm/jsconfuser-vm/normalize-macro-combinations.test.js) | Component; native callbacks execute retained programs with window, atob/btoa and performance, VM timeout 30 s |
| [`vm/jsconfuser-vm/normalize-macro-wordcode.test.js`](../../decoder/decode-js/test/vm/jsconfuser-vm/normalize-macro-wordcode.test.js) | Component; native callbacks execute retained programs with window and performance, VM timeout 1 s |
| [`vm/jsconfuser-vm/normalize-self-modifying-wordcode.test.js`](../../decoder/decode-js/test/vm/jsconfuser-vm/normalize-self-modifying-wordcode.test.js) | Component; native callbacks execute retained programs with window and performance, VM timeout 1 s |
| [`vm/jsconfuser-vm/normalize-specialized-wordcode.test.js`](../../decoder/decode-js/test/vm/jsconfuser-vm/normalize-specialized-wordcode.test.js) | Component; native callbacks execute retained programs with window and performance, VM timeout 1 s |
| [`vm/jsconfuser-vm/normalize-string-concealing.test.js`](../../decoder/decode-js/test/vm/jsconfuser-vm/normalize-string-concealing.test.js) | Component; native callbacks execute retained programs with window, atob, host Buffer and performance, VM timeout 1 s |
| [`vm/jsconfuser-vm/normalize-string-concealing-combinations.test.js`](../../decoder/decode-js/test/vm/jsconfuser-vm/normalize-string-concealing-combinations.test.js) | Component; native callbacks execute retained programs with window, atob, host Buffer and performance, VM timeout 10 s |
| [`vm/jsconfuser-vm/patch-added-opcodes.test.js`](../../decoder/decode-js/test/vm/jsconfuser-vm/patch-added-opcodes.test.js) | Component; retained known-source numeric PATCH pairs/stacks, independent B-E rebuild, named damage/removal controls and native source/encoded/current equality with VM timeout 10 s |
| [`vm/jsconfuser-vm/self-modifying-observation.test.js`](../../decoder/decode-js/test/vm/jsconfuser-vm/self-modifying-observation.test.js) | Component; native callbacks execute retained programs with window and performance, VM timeout 1 s |
| [`vm/jsconfuser-vm/try-region.test.js`](../../decoder/decode-js/test/vm/jsconfuser-vm/try-region.test.js) | Component; native callbacks execute source, encoded and recovered programs with window and performance, VM timeout 5 s |
| [`vm/switch/vm-switch-to-source.test.js`](../../decoder/decode-js/test/vm/switch/vm-switch-to-source.test.js) | Component; native callbacks use an explicit VM invocation timeout |

### Emission and publication claims

Read [the shared design](vm-switch-boundary.md) for model grammar, exact operations,
copy/control decisions and supplied-model versus source proof. Read
[standalone decode](transforms/jsconfuser-vm/standalone-decode.md#scenario-and-oracle-map) for
numeric publication and [the public adapter](plugins/jsconfuser-vm.md#public-scenarios-and-acceptance)
for CLI/error behavior. Tests are an assertion index, not a count of qualified cases. The mappings
below describe current assertions inspected from source; they do not assert a fresh run,
replay of historical fixture generation or document-only reconstruction.

| Claim / scenario | Test family and actual oracle | Evidence limit |
|---|---|---|
| Minified class admission | [minified-class-admission.test.js](../../decoder/decode-js/test/vm/jsconfuser-vm/minified-class-admission.test.js): normal A/B/public source, state/residue checks and exact B/C payload damages. | Parser assertions remain source data; separate finite current native qualification is owned by the [finite minified-class qualification](#finite-minified-class-qualification). |
| Fresh minified class frontend | [minified-class-frontend.test.js](../../decoder/decode-js/test/vm/jsconfuser-vm/minified-class-frontend.test.js): local seed/config/pin identities, A admission, and mandatory exception data recovering structured output through the shared region proof. | Parser-only. |
| Randomized class words | [randomized-class.test.js](../../decoder/decode-js/test/vm/jsconfuser-vm/randomized-class.test.js): baseline word-meaning and pool parity with meaning from the handlers ([Packet A](transforms/jsconfuser-vm/extract-container.md)), full B consumption, preserved input AST/state, fresh public output and residue/derived-state checks; case-order, alpha and full-remapping positives. | Parser-only [provenanced fixtures](../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/randomized-class/provenance.json); execution belongs to the [finite randomized-class qualification](#finite-randomized-class-qualification). `finalJavaScriptSemantics: false` remains explicit. |
| Randomized final-minified class words | [randomized-minified-class.test.js](../../decoder/decode-js/test/vm/jsconfuser-vm/randomized-minified-class.test.js): as above on class plus minify inputs, with alpha/case-order and full-remapping positives. | Same provenance and limits; other optimizer spellings remain unqualified. |
| Fresh exception native closure | [minified-class-admission.behavior.test.js](../../decoder/decode-js/test/vm/jsconfuser-vm/minified-class-admission.behavior.test.js): all four mandatory exception profiles/seeds use the current public decoder and newly emitted output. | Published local [native qualification metadata](../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/minified-class-admission/native-qualification.json) binds exact inputs/current outputs; the [finite minified-class qualification](#finite-minified-class-qualification) states this finite host/trace boundary. Excluded from parser-only commands. |
| Try regions | [exception-region-parser.test.js](../../decoder/decode-js/test/vm/jsconfuser-vm/exception-region-parser.test.js): current public structured recovery, exact frozen provenance, captured writes/saved returns, fresh AST state and each damage reaching its named [try-region](vm-switch-try-region.md) check. [try-region.test.js](../../decoder/decode-js/test/vm/jsconfuser-vm/try-region.test.js): every try form and exception route against the source's own execution. | Current-output qualification is bounded by the [finite minified-class qualification](#finite-minified-class-qualification); loop exits remain the [listed control boundaries](vm-switch-boundary.md#5-known-gaps). |
| Numeric semantic carrier | [numeric-to-vm-switch.test.js](../../decoder/decode-js/test/vm/jsconfuser-vm/numeric-to-vm-switch.test.js): arithmetic preflight succeeds, model validates and serialized instruction fields are absent from cases/leaves. | Does not compare every lowered semantic field or native operation. |
| Independent model structuring | [vm-switch-to-source.test.js](../../decoder/decode-js/test/vm/switch/vm-switch-to-source.test.js): a supplied linear graph planned and emitted without dispatch; RESULT; catch scaffold under dispatch. [vm-switch-statements.test.js](../../decoder/decode-js/test/vm/switch/vm-switch-statements.test.js): planned rows and readable form over numeric fixtures. | Supplied typed cases, not a source extractor or production admission claim. |
| Indirect/handler dispatch | Same shared test: indirect RESULT and no unrelated catch/stack; explicit catch setup handles boom with handler-register switch. | No arbitrary finite-indirect, finalizer or host-effect proof. |
| Supplied catch boundaries | Same shared test: post-pop throw escapes; grouped setup/pop leaves survive; setter-induced exceptional route skips normal-only work and joins continuation. | Synthetic supplied blocks/edges; not proof that a source frontend derives every such plan. |
| Supplied model refusal | Same shared test: malicious operator, missing case/target, unknown mode and missing edge throw matching error text. | Selected checks, not exhaustive model/region validation; private packet mutation is not source-chain evidence. |
| Copy/liveness recovery | [vm-copy-simplification.test.js](../../decoder/decode-js/test/vm/jsconfuser-vm/vm-copy-simplification.test.js): positive copy-removal census and exact proof identities, branch proof incoming-count equal to one, selected closure empty-copy arrays/cell presence, retained ADD/BUILD_ARRAY/BUILD_OBJECT producers, source TEST_OUTPUT and fresh AST checks. | These assertions do not isolate a candidate rejected because of a join or capture, and do not exercise every call/property producer or repeat guard. Planner flags alone are not independent semantic evidence. |
| Numeric structured/exception output | [decode-standalone.test.js](../../decoder/decode-js/test/vm/jsconfuser-vm/decode-standalone.test.js): corpus output versus retained JSON oracle, expected structural declines, no dispatch for structured functions, required irreducibility metadata for dispatch, named terminal/catch/finally controls. | Retained corpus loop; arbitrary host coercion/exception/reentrancy and universal equivalence excluded. |
| Source refusal and internal admission | [diagnose-standalone.test.js](../../decoder/decode-js/test/vm/jsconfuser-vm/diagnose-standalone.test.js) and [owned-chain-source.test.js](../../decoder/decode-js/test/vm/jsconfuser-vm/owned-chain-source.test.js): named source damage versus positive model/output controls; decode-standalone tests assert null result/output on malformed or unsupported shapes. | Do not infer a public detailed helper diagnostic where standalone publishes a generic stage code. |
| Direct result adapter | [plugin.test.js](../../decoder/decode-js/test/vm/jsconfuser-vm/integration/plugin.test.js): spy pins one diagnosis call with internally prepared source, output/result agreement, frozen envelope, exact-original source/bytes/hash decline, debug-comment output agreement, fresh AST/residue/state. | Selected public controls; flags do not establish universal native semantics. |
| CLI output and sidecar | [cli.test.js](../../decoder/decode-js/test/vm/jsconfuser-vm/integration/cli.test.js): subprocess exit/status/path files, direct-result equality, lexical alias sentinel, unknown/read/output errors and unchanged legacy output. | Child process test family; result-write/serialization/decode-throw and filesystem-identity alias cases lack focused controls. Writes are not transactional. |
| Registered behavioral agreement | [integration.test.js](../../decoder/decode-js/test/vm/jsconfuser-vm/integration/integration.test.js): branch input across registered CLI/direct diagnosis and retained fixture oracle. | Bounded input/host behavior; no all-option qualification. |
| Setup/readability regression | [readability.test.js](../../decoder/decode-js/test/vm/jsconfuser-vm/integration/readability.test.js): deterministic metrics/current output equals golden, frozen input hashes, reductions versus baseline, preserved operation counts, zero eligible copies, required cells/args/helper, golden TEST_OUTPUT/fresh AST. | Arithmetic/closure-loop/scale frozen inputs and separate enumeration setup control; no original identifier/scope reconstruction. |
| Review switch rendering | [render-vm-switch.test.js](../../decoder/decode-js/test/scripts/render-vm-switch.test.js): arithmetic encoded and switch output have same window effects under fixed host, saved model renders identical text, no host/logger shim or overwrite. | Subprocess review interface and one fixture; not general step-one native semantic proof. |
| Sequential rollback/publication | [sequential.test.js](../../decoder/decode-js/test/vm/jsconfuser-vm/integration/sequential.test.js): actual outer null, changed outer/VM decline, numeric success/result agreement, wrapped recovery and payload removal (no array of literals left, the outer stage's output holding some as the control) with and without outer string concealing and under each single outer option of the [outer-layers](transforms/jsconfuser-vm/runtime-meaning.md#fixtures) fixture over a randomized VM, with bounded source/encoded/current TEST_OUTPUT equality, plus CLI original-output rollback. | No coordinator parse stage or general layered/native semantic qualification. |

The retired immutable reduced emission/public verifier, built from the documents before
source consultation, formed a separate callback/scaffold evidence family. Its surviving credit is selected literal
lowerings and register/target/mode/operator predicates; reduced reaching-definition/use and copy
controls; nearest reconvergence, dispatch and retry decisions; selected public record/flags/error
normalization/freezing; exact-original adapter and sequential staging; and simulated CLI ordering.
Its postfreeze source audit
excludes whole projection/identity, valid-model validator success/census/leaf-gate claims, guessed
`NEG`, Boolean polarity, exact residue message and mirrored plain-CALL receiver expectations.
It does not execute a production frontend/backend/parser/CLI, filesystem or native source oracle.
No excluded claim is restored by source edits or model consistency.

The separate retired immutable field verifier, built from the corrected documents before
source consultation, added independent literal selected typed-operand lowerings, projection allocations/sharing, Map
census, block/root/nested-region observations, string polarity, plain-CALL receiver expectations,
repeat/incoming copy decisions and exact synthetic error fields. This is a new supplied-scaffold
family, separate from both retained project assertions and the first frozen verifier. Its complete
baseline is statically source-valid; selected validator positives/opposites are reduced gates,
with their own trace order. No actual validator import/call or return-identity assertion follows
from the constant sameObject marker. Private duplicate PCs distinguish the census formula without
qualifying owned admission; the extra reduced matching-use-register test is uncredited. There is
no input-preservation assertion, actual dataflow/compiler/parser/source/native/CLI reconstruction,
or filesystem run. [The shared boundary](vm-switch-boundary.md#fixtures) owns the exact selected
credit/limits and [standalone publication](transforms/jsconfuser-vm/standalone-decode.md#fixtures)
owns the supplied error fields and skeletal-success exclusion. All first-verifier exclusions remain
permanent; new literal controls do not retroactively repair that run.

Fresh AST checks compare consumed scope/reference state against a fresh parse using the shared
helper. The source-string emitter itself returns no caller AST and does not promise to repair an
existing tree's derived state. Recovery assertions (different output, absent dispatch/residue,
positive eliminated copies, or required native syntax) discriminate successful decoding from
passthrough; runtime checks alone do not.

The [shared semantic gaps](vm-switch-boundary.md#5-known-gaps) separate source-inspected EXP,
delete, host-apply, object publication, strict/host/cell/constructor contrasts from executed
behavioral controls. Missing focused controls remain missing; metadata counts, static consistency
and historical-generation records cannot fill them. The owning F/G/J/M designs preserve their
current defects. Component tests need a recursive local-import audit before a bounded rerun;
CLI/sequential/render families invoke child processes, and corpus tests iterate retained inputs.
Do not infer execution permission or safety from their directory name or this evidence index.

### Finite minified-class qualification

This is the qualification boundary for final runtime minification and class obfuscation, stated
as axes rather than as a run. Each cell is one source case, one profile and one seed, encoded by
the pinned encoder and decoded by the current public adapter.

| Axis | Covered |
|---|---|
| Source cases | The fourteen qualifier cases arithmetic, branches, closures, nestedStrings, collections, repeatedArrays, switch, forIn, methods, tryCatch, throwCatch, tryFinally, exceptions and the mandatory exceptionRoutes (spread was added later and is outside this boundary) |
| Profiles | baseline, minify, classObfuscation and minifyClassObfuscation; every other representation option explicitly false, target browser |
| Seeds | 172, 173, 174 |
| Per-cell oracle | Source, encoded and current decoded output agree in a fresh browser-like VM context; normalized projection agrees with the same-seed baseline; public parse/state/coverage/structure/residue checks pass; each enabled option's emitted effect is observed, the pair crediting both components against its one-option-removed controls |
| Mandatory trace | Every exceptionRoutes cell reproduces [the independent expected trace](../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/minified-class-admission/exception-routes.expected.json) for source, encoded and current output |
| Required controls | Parser payload-damage controls reach their B/C refusals with atomic decline ([admission](../../decoder/decode-js/test/vm/jsconfuser-vm/minified-class-admission.test.js)); the [replay oracle controls](../../decoder/decode-js/test/scripts/qualify-jsconfuser-vm/replay.test.js) fail a wrong current output despite good historical bytes and never observe a current decline |
| Excluded | Missing E/H native property/coercion exception edges, F/G precision limits, M terminal-kind coverage, other option stacks and global JavaScript equivalence; `finalJavaScriptSemantics` stays false |

**Census and expected outcome.** The maintained re-reader is
[minified-class-admission.behavior.test.js](../../decoder/decode-js/test/vm/jsconfuser-vm/minified-class-admission.behavior.test.js)
over the twelve local exceptionRoutes cells listed in
[native-qualification.json](../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/minified-class-admission/native-qualification.json);
every cell must match the trace. The whole population is re-read by a fresh generation and native
replay with the [qualification tool](../../decoder/decode-js/scripts/qualify-jsconfuser-vm/qualify.mjs) (`--profiles baseline,minify,classObfuscation,minifyClassObfuscation --seeds 172,173,174`, then `--replay-mode native`);
every cell must be accepted and qualified, with both pair components observed. One such run
qualified every cell on the decoder at that time; it is a historical result, because its decoder
branch was unpushed and its Node/Java/Closure toolchain unpinned, so its counts are not
reproducible and its frozen population is not maintained evidence.

### Finite randomized-class qualification

This is the qualification boundary for opcode/layout randomization combined with class
obfuscation and final minification, with opcode meaning from the handlers
([Packet A](transforms/jsconfuser-vm/extract-container.md)). Cells are
formed as in the minified-class boundary above.

| Axis | Covered |
|---|---|
| Source cases | arithmetic, spread (under randomization its payload carries a noncanonical CALL_SPREAD sentinel) and the mandatory exceptionRoutes |
| Profiles | baseline, randomizeOpcodes, minify, classObfuscation, randomizeOpcodesClassObfuscation, randomizeOpcodesMinify, minifyClassObfuscation and randomizeOpcodesClassObfuscationMinify; every other representation option and timingChecks explicitly false, target browser. The single- and two-option profiles are the removal controls of the pair and the triple |
| Seeds | 191, 192, 193 |
| Accepted-cell oracle | Complete A/B admission; B consumes every canonical word; the canonical instruction/operand/root/pool projection equals the same-case/seed baseline; the input AST and bindings are unchanged; public output is fresh, differs from the input, parses, has consistent consumed derived state, fresh simplification state and zero VM residue; source, encoded and decoded output agree in a fresh browser-like VM context. Every enabled option's emitted effect is observed independently of recovery, and each pair/triple has all its one-option-removed counterparts |
| Declined-cell oracle | Enabled effects observed and source/encoded behavior agreeing; public decoding returns the exact input with the first declining packet's diagnostic named; no recovery or decoded-behavior credit |
| Mandatory trace | Every exceptionRoutes cell, accepted decoded output included, reproduces [the independent expected trace](../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/minified-class-admission/exception-routes.expected.json) |
| Required controls | Alpha, case-order and consistent full-remapping positives in [randomized-class.test.js](../../decoder/decode-js/test/vm/jsconfuser-vm/randomized-class.test.js) and [randomized-minified-class.test.js](../../decoder/decode-js/test/vm/jsconfuser-vm/randomized-minified-class.test.js): every case label and every instruction-boundary opcode word of the inlined and minified arithmetic fixtures is remapped, plus, in the inlined source, the disabled-timing `op = JUMP` literal (Closure folds that branch away). Each must still admit with identical canonical word meaning (instruction names and operands) and fresh public output. This supplies no timing qualification |
| Recorded declines | None: randomizeOpcodesMinify, where no randomized map survives minify, is accepted because the handlers name the words |
| Excluded | Other layouts, option stacks and optimizer spellings; added opcodes under PATCH, timing/finalizers; CLI, subprocess backend and sequential pipeline families; E/H/F/G/J/M semantic limits and global JavaScript equivalence. `finalJavaScriptSemantics` stays false |

**Census and expected outcome.** Regenerate with the
[qualification tool](../../decoder/decode-js/scripts/qualify-jsconfuser-vm/qualify.mjs) (`--cases arithmetic,spread,exceptionRoutes --profiles <the eight above> --seeds 191,192,193`,
then `--replay-mode native`). Every pair/triple cell must be accepted with all its
components observed; every other cell must be accepted, and a decline is a finding. A run on the
decoder with handler meaning matched this outcome. It is a historical result for the same reasons
as above: unpushed decoder branch, unpinned Node/Java/Closure toolchain.

### Finite PATCH added-opcode qualification

This boundary qualifies original-width PATCH recovery through aliases, macros, specialized
and anti-instrumentation instructions. It is separate from the earlier representation matrices.
The maintained [PATCH qualifier](../../decoder/decode-js/scripts/qualify-jsconfuser-vm/patch.mjs)
writes its protocol before generation and applies the current public adapter to each new input.

The named PATCH fixture pairs carry aggregate [generation metadata](../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/patch-added-opcodes/generation.json).
This index is distinct from per-cell `qualification.json` records with recorded observations;
[patch-added-opcodes.test.js](../../decoder/decode-js/test/vm/jsconfuser-vm/patch-added-opcodes.test.js) supplies
their current recovery, behavior and state evidence.

| Axis | Required census / oracle |
|---|---|
| Source cases | arithmetic, closures, tryFinally and patchArrays from the maintained config; the longer array case preserves repeated canonical windows after specialization takes its first four signatures per opcode |
| Profiles | Every subset of selfModifying, aliasedOpcodes, macroOpcodes, specializedOpcodes and antiInstrumentation, including baseline and all one-option-removed controls; target browser, all other representation/timing options explicitly false |
| Seeds | 211, 212, 213, using the checked-in mulberry32 generator |
| Recovery | Source, encoded and current decoded output agree in fresh browser-like VM contexts; output differs, parses, passes independent residue/coverage/simplification checks and consumed derived-state checks; input AST/bindings stay unchanged |
| Effects | Separate emitted handler counts from reached PATCH/added-opcode headers and kinds inside decrypted regions. Each enabled option must be reached in an effect-qualified cell and absent from its same-source/seed removal peer, which must itself pass recovery. A requested option without a reached instruction supplies no component credit |
| Population acceptance | Every cell passes recovery; every subset has at least one cell reaching all enabled components with qualifying removal peers. Short-source cells may recover without full effect credit; profileWitnesses must not be empty. A new decline is a finding with public and PATCH-normalizer diagnostics, not an invalid-encoder verdict |
| Required controls | [patch-added-opcodes.test.js](../../decoder/decode-js/test/vm/jsconfuser-vm/patch-added-opcodes.test.js) removes each added-opcode width input and reaches patch-ciphertext; damages normal source to reach patch-ciphertext; a source-admitted nonterminal JUMP_REG macro passes the PATCH stage and is refused by E (cfg-declined). The named-diagnostic oracle must reject success and a different diagnostic, and the behavior oracle must reject wrong current output |
| State | Retained pairs, arithmetic/finally stacks and counted-array macros compare the PATCH stage's returned B (null while added opcodes remain) to a fresh parse of its container, plus public fresh output/binding/residue checks |
| Limits | Numeric nonminified runtime in this population; dispatcher, CFF and string-concealing layers are covered only by the [self-modifying layers](../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/self-modifying-layers/generation.json) fixtures; no added-opcode minified/class/randomized/transport qualification, timing/finalizer hardening, arbitrary host semantics or E/H/F/G/J/M gap closure. finalJavaScriptSemantics remains false |

From the decoder root, run the focused controls, then use a physically absent output directory:

```sh
npx vitest run --coverage.enabled=false test/vm/jsconfuser-vm/patch-added-opcodes.test.js
node scripts/qualify-jsconfuser-vm/patch.mjs NEW_POPULATION
```

Toolchain: Node 26.10.0, JDK 27 and Closure 20260216.0.0. The tool requires the encoder at its explicit PIN, a JDK supplied through
JAVA_HOME or PATH, and the installed Closure dependency. Its protocol records Node/JDK/dependency identities and
the starting encoder/source/tool/dependency snapshot and requires an equal snapshot at completion. Do not edit those inputs or run tools that
write dependency caches during qualification. Each worker must complete with exit zero and no
signal/timeout; native VM execution is limited to 10 seconds, its parent to 12 seconds,
inspection to 20 seconds and generation to 65 seconds (Closure has 60 seconds). Native
execution is restricted to these known generated sources. Process completion and unchanged
snapshot are required; partial output receives no population credit.

The short arithmetic source can emit no macros when specializedOpcodes is enabled without anti.
Specialization selects even single-occurrence signatures and admits four signatures per opcode;
macro selection then sees only surviving canonical windows. patchArrays supplies enough distinct
constant-load sites to leave repeated eligible windows after that cap. The census decides which
cells reach macros; anti insertion can preserve eligible windows but does not guarantee macro
emission for every seed. Requesting the option or comparing serialized bytecode is insufficient.
A finite generated run and retained controls do not establish universal option support.

### Finite timing and finalizer qualification

The [timing-checks contract](transforms/jsconfuser-vm/timing-checks.md) qualifies
recovery for every timing value: timing checks live in the interpreter only, so the decoded
program must behave as the source under fast, slow and paused execution, while the encoded
active program poisons. Interpreter RETURN, capture-close and exception unwind are the finalizers
at issue.
Compiler and qualifier finalization are separate mechanisms.

| Axis | Required census / oracle |
|---|---|
| Known source cases | arithmetic and finalizers from [timing.mjs](../../decoder/decode-js/scripts/qualify-jsconfuser-vm/timing.mjs); finalizers exposes a captured value, calls a controlled host pause inside a child frame with a parent finally region, and independently expects `[7,true,7]` |
| Profiles | baseline/timing; full selfModifying+aliasedOpcodes+macroOpcodes+specializedOpcodes+antiInstrumentation stack with/without timing; base64 encodeBytecode with/without timing; handlerTable with/without timing. Every other representation option explicitly false; target browser |
| Seeds / thresholds | 231, 232, 233, mulberry32; enabled threshold 100 ms. The decode controls additionally cover false, 0, -0, 1000 (strict-true serialization) and -1; NaN and infinities are untested |
| Emitted / reached effects | Observe scalar value, numeric transport and table scaffold independently. PATCH census distinguishes emitted added-opcode handlers from reached PATCH/added-opcode words on an observation-only disabled clone. Each active cell has a timing-disabled peer with the same seed. A missing requested option gives no full PATCH component credit; the prior PATCH subset census owns those added-opcode claims |
| Controlled clocks | Every successive delta exactly 100 ms preserves the independent source behavior; one initial delta 101 ms followed by a frozen clock poisons and reaches the unknown-opcode error. Repeated above-threshold deltas may keep forcing JUMP and time out instead; no guaranteed halt is claimed |
| Real clocks | Fresh browser-like VM (window/self, atob/btoa, nonthrowing performance.now). Fast source/encoded behavior agrees. Finalizers additionally uses 250 ms synchronous host work and child SIGSTOP/parent SIGCONT after 250 ms. Completion, signal records and measured blocked duration are required |
| Recovery | Every cell: current public output differs, parses, passes coverage/residue/fresh simplification and consumed binding checks, input AST/bindings unchanged; decoded behavior equals source for fast/slow/paused modes. Disabled cells: encoded behavior also agrees. Passthrough fails recovery |
| Active encoded effect | Slow/paused encoded execution differs from source: words zero, parent finally marker absent, current frame lost, an open current-frame scalar capture with undefined backing; surviving root callable captures are type-only census. This confirms the requested effect was emitted |
| Decode / oracle controls | [runtime-finalizers.test.js](../../decoder/decode-js/test/vm/jsconfuser-vm/runtime-finalizers.test.js): every timing value decodes to the disabled program, also with transport and with a handler table; threshold equality/greater on the encoded program; a renamed Upvalue close method still recovers. [Timing instrument controls](../../decoder/decode-js/test/scripts/qualify-jsconfuser-vm/timing.test.js) pin present/absent/active/damaged table effects, observed real stop/resume and wrong-behavior rejection |
| Retained replay | [runtime-finalizers.behavior.test.js](../../decoder/decode-js/test/vm/jsconfuser-vm/runtime-finalizers.behavior.test.js) consumes the seed 231 [source](../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/runtime-finalizers/finalizers.src.js), [independent oracle](../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/runtime-finalizers/oracle.json) and every profile named in [generation metadata](../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/runtime-finalizers/generation.json). It rechecks current recovery, real native behavior/state/completion, and independent B-E versus current consumed PATCH state. Metadata records explicit baseline options plus profile overrides, pin, RNG and toolchain; Git identifies the retained bytes |
| Existing emission boundary | The retained [top-level finally input](../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/runtime-finalizers/top-level-finally.js) and [source](../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/runtime-finalizers/top-level-finally.src.js) pass A/preflight but decline at the existing unproved FINALLY_SETUP return-continuation boundary. The replay pins exact public passthrough and unchanged input state; it earns no successful recovery/population credit |
| Excluded | Arbitrary side-effecting/throwing performance globals; minified/class/randomized timing stacks, other option combinations/releases, CLI/sequential/subprocess backends and E/H/F/G/J/M gap closure. finalJavaScriptSemantics stays false |

Run focused controls before generation, then use a physically absent population path:

```sh
npx vitest run --coverage.enabled=false test/vm/jsconfuser-vm/runtime-finalizers.test.js test/scripts/qualify-jsconfuser-vm/timing.test.js test/vm/jsconfuser-vm/runtime-finalizers.behavior.test.js
node scripts/qualify-jsconfuser-vm/timing.mjs NEW_POPULATION
```

Generation uses the explicit encoder PIN and installed Node/JDK/Closure supplied through PATH or
JAVA_HOME. Protocol is written before generation and records the complete input/tool/dependency
snapshot; it must equal the final snapshot. Per-worker completion must have exit zero, no signal
and no timeout. The native VM limit is 10 seconds and its parent 12 seconds; generation is 65
seconds (Closure 60 seconds) and inspection 20 seconds. An outer
[capture command](../../decoder/decode-js/scripts/qualify-jsconfuser-vm/capture_command.py) records
actual whole-tool exit/signal/timeout. Cell and summary readbacks must equal the just-produced
records. Do not edit consumed source/tools or change dependencies during qualification. Native
execution is only for these known generated sources. A failed/partial run earns no population credit.

The maintained replay owns the retained seed/profile claims; the generation tool owns the
population axes and process checks.

The retained top-level finally boundary has its own `separateGeneration.topLevelFinally` entry
in generation metadata. It names [worker.mjs](../../decoder/decode-js/scripts/qualify-jsconfuser-vm/worker.mjs)
and the [runWorker API](../../decoder/decode-js/scripts/qualify-jsconfuser-vm/qualify.mjs), exact
source/options/seed, toolchain, pin, request construction, leading-comment normalization and
process/snapshot/readback conditions. It is not a case emitted by timing.mjs; the metadata replay
checks that separation and its baseline option agreement.

Disabled timing still reads performance.now once per runtime invocation. The recovered program
omits that host bookkeeping; callable, nonthrowing, observationally inert clock reads are a stated
native assumption, not a globally proved source property. Static input admission and a finite
successful run cannot establish arbitrary JavaScript host equivalence.

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
`npx vitest run` (with `always()` so a report posts even on failure), then
`davelosert/vitest-coverage-report-action` publishes the coverage summary as a PR comment.
