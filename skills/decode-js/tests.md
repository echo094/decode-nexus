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

Two helpers, both reading fixtures relative to a passed-in base path and asserting with
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
- **`getPluginResult(plugin, fix, input)`** — same contract but calls `plugin(source)`
  directly (full pipeline, not a single visitor).

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
| `parse-control-flow-storage.test.js` | [parse-control-flow-storage](visitors/parse-control-flow-storage.md) | `object-invalid-1` (no-op) |

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

Coverage is uneven by design among the shared visitors: `split-assignment`,
`split-variable-declarator`, and `parse-control-flow-storage` have dedicated fixtures, while
the rest are exercised transitively through the `sample_189` end-to-end case.

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

## CI (`.github/workflows/test.yml`)

"Unit Tests" runs on push / PR to `main`: Node **26** with npm cache, `npm ci` with
`npm_config_build_from_source: true` (so `isolated-vm`'s native module builds reliably),
`npx vitest run` (with `always()` so a report posts even on failure), then
`davelosert/vitest-coverage-report-action` publishes the coverage summary as a PR comment.
