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
- **`testTimeout`, raised well above Vitest's 5s default.** The jsconfuser combination
  fixtures below are whole-pipeline decodes of real encoder output, and the largest inputs run
  to six figures of obfuscated source bytes — one full decode per case, with v8 coverage
  instrumenting every visitor the decode walks. They are the only cases in the suite whose
  cost is measured in seconds rather than milliseconds, and the default left the heaviest
  of them too little margin: it **passed on a dev machine and timed out on a shared CI
  runner**, whose per-case times run several times slower across the whole file, not just
  on that one case. Read a timeout here as a host-speed artifact until proven otherwise —
  a decode regression changes the *output*, and shows up as a `.fix.js` mismatch on a fast
  machine too. The axis to check if it recurs is the per-case time of the heaviest
  fixtures against the configured limit (`npx vitest run --reporter=verbose`), never a
  remembered figure.

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
[encoder-decoder-method.md](../encoder-decoder-method.md)'s S1 size ratio computable later.
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

## Testing against real encoder output

The fixtures above are frozen samples; the loop that *finds* the bugs they then guard is a
live one, and it is worth running directly whenever a decode is in question:

1. **Encode with the real encoder** — `encoder/js-confuser`'s built `dist/index.js`
   `obfuscate`, or its CLI. Its output is randomized per run and many transforms are
   probability-gated, so repeat any verdict you intend to act on
   ([encoder-decoder-method.md](../encoder-decoder-method.md) S5).
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
`npx vitest run` (with `always()` so a report posts even on failure), then
`davelosert/vitest-coverage-report-action` publishes the coverage summary as a PR comment.
