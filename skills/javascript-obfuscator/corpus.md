# Corpus Recipe

How to rebuild the sample corpus and what has to be in it: which versions, which option sets,
which inputs, and the rules that make one build comparable to another. **This page is the recipe;
the encode script is not tracked.** A script kept beside a recipe drifts from it silently and then
answers confidently, so the durable artifact is the specification here and the script is
regenerated from it.

## What this page holds, and what it never holds

**Encoding needs nothing but the encoder**, which is the property that makes a corpus worth
freezing: it cannot be contaminated by whatever is later measured against it. This page exists to
keep that true, so it carries only what the encoder alone can answer.

| Belongs here | Never here |
|---|---|
| which versions are built, and the encoder-side reason each column exists | what any consumer of the samples found in them, or the state of its repairs |
| which option sets, seeds and targets a column carries, and which sets a version can accept at all | another project's pass names, censuses, runtime tallies — or its commit ids, which a rebuild of that project silently invalidates |
| the inputs verbatim, and the shapes they can and cannot reach | a measured value with nothing behind it: record the axis and the census that reads it, per `SKILL.md`'s Measured Figures Are Diary |
| emitted-shape facts read off the samples — what differs between two columns, what a cell does when run | the study reasoning that selected a version, which is [versions.md](versions.md)'s |
| the freeze, manifest and append rules that keep two builds comparable | anything that would have to be re-checked when a downstream consumer changes |

Keep this boundary as a table: downstream results belong with their consumer, while this recipe
records only the encoder material from which a boundary is read.

## Generated builder contract

The builders are deliberately generated for a reconstruction run and are not retained. The next
clean-room run must generate these five files under `sandbox-tests/encoders/` (the names and
interfaces are part of this recipe):

| Generated file | Required interface |
|---|---|
| `sets.cjs` | CommonJS export `{ SEED, SETS }`, with the exact definitions below. It must have no dependency on a downstream project or on an output directory. |
| `encode.cjs` | `node encode.cjs [version ...]`; no arguments means the spine `2.19.0` only, and explicit arguments are built in the order supplied. It writes the ordinary corpus under `../out/`. |
| `append-fixture.cjs` | `node append-fixture.cjs <fixture-name>`; the fixture is a basename from `../fixtures/` and is appended to each existing version column using that column's existing set list. |
| `build-nested.cjs` | `node build-nested.cjs`; builds the two-layer `2.19.0` samples described under [Nested cells](#nested-cells--a-source-encoded-twice) and never overwrites an existing target. |
| `build-nested-robust.cjs` | `node build-nested-robust.cjs`; builds the inner controls and outer-option samples described under [The robustness variant](#the-robustness-variant--fix-the-inner-layer-vary-the-outer), and never overwrites an existing target. |

All five builders must resolve an encoder as `jso-<version with dots replaced by hyphens>` from
the single `sandbox-tests/encoders/node_modules` install. The package manifest and lockfile must
contain an exact npm alias for every version in the [Version matrix](#version-matrix), and the
builder must fail before writing output when an alias is missing or its package version is not the
requested version. A fresh reconstruction may install the aliases with exact npm specs and must
record the resulting lockfile and package provenance; it must not import the encoder from another
project's dependency tree, a read-only submodule, or an ambient global install. For each
alias, `npm view javascript-obfuscator@<version> gitHead` is the provenance check, and its result is
compared with the corresponding upstream tag before a column is accepted.

The focused class/logical cell has a separate generated interface so the ordinary matrix stays
closed. A reconstruction for this cell may generate `build-class-logical.cjs` with `snapshot` and
`build` commands under its task directory. `snapshot` must validate and record every pre-existing `out/` manifest entry
and file digest before mutation. `build` must validate the exact alias/version and option names,
encode only the source and set in [Focused producer cells](#focused-producer-cells), assert both
AST populations, run source/output with a timeout, append one manifest entry, and on a second run
report a frozen no-op. This builder is not an ordinary `encode.cjs` version column or an
`append-fixture.cjs` fixture append.

The generated `sets.cjs` must be equivalent to this data contract. `SEED` is the numeric seed
`20260809`; it is not the encoder preset seed `0`.

```js
const B = { compact: true, seed: SEED, target: 'browser' };
const SA = { ...B, stringArray: true, stringArrayThreshold: 1 };

baseline                  = { ...SA };
no-rotate                 = { ...SA, rotateStringArray: false };
wrappers-variable         = { ...SA, stringArrayWrappersCount: 2,
                               stringArrayWrappersType: 'variable',
                               stringArrayWrappersChainedCalls: false };
wrappers-function         = { ...SA, stringArrayWrappersCount: 2,
                               stringArrayWrappersType: 'function',
                               stringArrayWrappersChainedCalls: false };
chained-calls             = { ...SA, stringArrayWrappersCount: 2,
                               stringArrayWrappersType: 'function',
                               stringArrayWrappersChainedCalls: true };
encoding-base64           = { ...SA, stringArrayEncoding: ['base64'] };
encoding-rc4              = { ...SA, stringArrayEncoding: ['rc4'] };
dead-code                 = { ...SA, deadCodeInjection: true,
                               deadCodeInjectionThreshold: 1 };
cff                       = { ...SA, controlFlowFlattening: true,
                               controlFlowFlatteningThreshold: 1 };
self-defending            = { ...SA, selfDefending: true };
debug-protection          = { ...SA, debugProtection: true };
debug-protection-interval = { ...SA, debugProtection: true,
                               debugProtectionInterval: true };
console-output            = { ...SA, disableConsoleOutput: true };
wrappers-none             = { ...SA, stringArrayWrappersCount: 0 };
encoding-all              = { ...SA, stringArrayEncoding: ['none', 'base64', 'rc4'] };

preset-default            = { optionsPreset: 'default', seed: SEED };
preset-low                = { optionsPreset: 'low-obfuscation', seed: SEED };
preset-medium             = { optionsPreset: 'medium-obfuscation', seed: SEED };
preset-high              = { optionsPreset: 'high-obfuscation', seed: SEED };

all-on = {
  ...B,
  controlFlowFlattening: true, controlFlowFlatteningThreshold: 1,
  deadCodeInjection: true, deadCodeInjectionThreshold: 1,
  debugProtection: true, debugProtectionInterval: true,
  disableConsoleOutput: true, numbersToExpressions: true, renameGlobals: true,
  rotateStringArray: true, shuffleStringArray: true, simplify: true,
  splitStrings: true, splitStringsChunkLength: 2,
  stringArray: true, stringArrayThreshold: 1,
  stringArrayEncoding: ['none', 'base64', 'rc4'],
  stringArrayIndexesType: ['hexadecimal-number', 'hexadecimal-numeric-string'],
  stringArrayIndexShift: true,
  stringArrayWrappersCount: 5, stringArrayWrappersType: 'function',
  stringArrayWrappersChainedCalls: true,
  stringArrayWrappersParametersMaxCount: 5,
  transformObjectKeys: true, unicodeEscapeSequence: true,
};
all-on-split10   = { ...all-on, splitStringsChunkLength: 10 };
all-on-selfdef   = { ...all-on, selfDefending: true };
all-on-noobjkeys  = { ...all-on, transformObjectKeys: false };
all-on-nowrappers = { ...all-on, stringArrayWrappersCount: 0 };

calls-transform = { ...baseline, stringArrayCallsTransform: true,
                    stringArrayCallsTransformThreshold: 1 };
```

The notation above is a specification, not JavaScript that can be pasted without quoting the
hyphenated keys. `SETS` must expose those names as string keys. `all-on-noobjkeys` and
`all-on-nowrappers` are present only in columns `2.15.5` and `2.16.0`; `calls-transform` is
present only in `3.2.0`; and `2.15.2` carries only `dead-code`. Every other version carries the
22-set `COLUMN_SETS` formed by all names above except those three column-specific siblings. The
builder must use the exact preset names and must not force thresholds on preset cells. It must not
add `domainLock` or `renameProperties`: the former is target-restricted and the latter makes the
fixtures fail before their reporting channel.

Before every call to an alias, copy the set object and normalize only this compatibility detail:
`debugProtectionInterval: true` remains boolean through `3.2.7`, and becomes numeric `4000` at
`4.0.0` and later. This normalization applies to ordinary builds, fixture appends, nested builds
and robustness builds. No other option may be silently renamed, defaulted, or inferred from the
version. `stringArrayEncoding` is always an array, and the wrapper sets explicitly carry their
`stringArrayWrappersChainedCalls` value.

The ordinary builder's fixture and output mapping is exact:

```text
fixtures/{strings,control,objects,directives}.js
  -> out/{version}/{fixture}__{set}.js
```

Read fixture bytes verbatim, including their final newline. Do not use `console.log` as a fixture
comparison channel: each fixture's expected output is written through `process.stdout.write`, and
each also contains the deliberate `console.log('console-channel')` shape line described above.
The builder only encodes; it does not decode or run samples.

`manifest.json` is `out/manifest.json` and has the shape `{ seed: 20260809, cells: {},
builtAt: {} }`. Each cell key is the output path relative to `out/`; its value is
`{ bytes: code.length, sha256_16: first 16 hexadecimal characters of SHA-256(code) }`, where
`code` is the exact UTF-8 string returned by `getObfuscatedCode()`. `builtAt[version]` is set only
when that version is first created. The builder must refuse a nonempty output tree with no
manifest, a manifest with a different seed, malformed cell metadata, an unmanifested output, a
manifest entry whose file is absent, or an existing file whose digest does not match its entry.
It must also refuse an unknown version, fixture, set, unsupported option, or missing alias before
writing that cell.

Freeze and no-op behavior is part of the interface. A cell already present and matching its
manifest entry is skipped byte-for-byte; it is never re-encoded. A rerun of the same command must
report zero new cells and leave every existing output and the manifest bytes unchanged. A first
build writes the spine `2.19.0` before any other column; later invocations append versions and
never regenerate a prior cell. The command's machine-readable summary must report the requested
versions, cells written, cells skipped, manifest cell paths and seed so that a clean-room run can
assert the no-op rather than trusting a message.

`append-fixture.cjs` must first validate the existing manifest and derive each column's set list
from its existing `__<set>.js` files. It must never use the global set list to widen a ragged
column. Existing cells are checked and skipped; new cells use the same normalized options and
manifest fields as the ordinary builder. It must report old-cell digest equality, new paths and
the per-column set list, and must fail on a missing fixture, unknown set, missing alias, seed
mismatch, or any old-cell change. The append command must leave all pre-existing output and
manifest cell values unchanged.

The nested builders have a separate, exact mapping and are not ordinary matrix columns. Both
layers use version `2.19.0`, the string-array base (`compact: true`, `target: 'browser'`,
`stringArray: true`, `stringArrayThreshold: 1`), and different seeds: inner `20260809`, outer
`20260810`. `build-nested.cjs` reads only `strings.js`, `control.js` and `objects.js`, writes
`out-nested/{fixture}__x1.js` and `{fixture}__x2.js`, and does not add `directives`. `x1` is the
inner output; `x2` is the outer encode of that exact x1 string. Existing targets are regenerated
in a temporary path for a byte comparison and then left untouched; a mismatch is an error.

`build-nested-robust.cjs` first writes or verifies
`out-nested/robust/_inner__{fixture}.js` from the same inner options, then writes or verifies one
outer encode for each of `baseline`, `numbers-to-expr`, `cff`, `dead-code`, `split-strings` and
`preset-high`. The outer seed is `20260810`; `baseline` is the string-array base,
`numbers-to-expr` adds `numbersToExpressions: true`, `cff` adds
`controlFlowFlattening: true` and threshold `1`, `dead-code` adds `deadCodeInjection: true` and
threshold `1`, `split-strings` adds `splitStrings: true` and
`splitStringsChunkLength: 3`, and `preset-high` is exactly
`{ optionsPreset: 'high-obfuscation', seed: 20260810 }`. Outputs are
`out-nested/robust/{set}__{fixture}.js` for the same three fixtures. The inner artifact is held
constant across all outer sets; no robustness file is allowed to be produced from another
robustness output.

The builders' validation output must make failures distinguishable. A successful ordinary run
reports `written`, `frozen`, `seed`, and manifest paths; a successful append additionally reports
the set list copied for every column; nested runs report every expected target and whether it was
created or byte-matched. A nonzero exit is required for usage errors, missing inputs, missing
aliases, wrong package versions, unsupported options, manifest/seed/digest disagreement, an
unexpected output path, a frozen-byte mismatch, or a ragged-column violation. After the builders
run, the reconstruction task must verify alias provenance, every manifest digest, no orphan or
missing cell, ordinary-set neighbor attribution (including known inert cells), nested output
byte stability, and the timed execution rules in [What the emitted samples do when run](#what-the-emitted-samples-do-when-run).

## Version matrix

The releases below, installed side by side through npm aliases in a single `package.json`
(`"jso-2-9-6": "npm:javascript-obfuscator@2.9.6"`), so one install provides them all and each is
importable by alias. **Read the table rather than a count** — versions are appended as a question
needs them, so any total stated here would be stale by the next append.

**A tarball's provenance reaches a commit, and it is one command to confirm:**
`npm view javascript-obfuscator@<version> gitHead` returns the commit the tarball was published
from, and for every version in the matrix it is byte-identical to the submodule's own tag for that
version. Two consequences — submodule history is a legitimate source for *every* version rather
than only the pin, so option definitions and preset contents are readable at `git show <tag>:<path>`
without building anything; and a sample can be traced to source. Re-run the command rather than
trusting a stored table of hashes.

| Version | Where it sits on the pipeline-order axis ([versions.md](versions.md)) |
|---|---|
| `2.9.6` | the whole of `P-sorted-directive-placement` — a single-release era |
| `2.10.0` | low end of `P-sorted-rotate-transformer` |
| `2.11.1` | inside `P-sorted-rotate-transformer` |
| `2.12.0` | inside `P-sorted-rotate-transformer` |
| `2.15.2` | **high end** of `P-sorted-rotate-transformer` — a **partial column**, see below |
| `2.15.3` | low end of `P-sorted-deadcode-renameidents` |
| `2.15.4` | inside it — and the far side of a calls-wrapper rewrite that moves no file |
| `2.15.5` | inside it — appended as a **discriminator**, see below |
| `2.16.0` | inside it — appended to settle where the scope calls wrapper's shape changes |
| `2.18.1` | inside it |
| `2.19.0` | inside it, and **the spine** (below) |
| `3.0.0` | inside `P-sorted-deadcode-renameidents`; appended to test the first supposed post-spine boundary |
| `3.0.1` | inside the same era; byte-identical to `3.0.0` across every shared cell |
| `3.1.0` | high end of `P-sorted-deadcode-renameidents`; low side of the first real post-spine order boundary |
| `3.2.0` | low end of `P-sorted-sa-controlflow`; a full option-off column plus the focused `calls-transform` discriminator below |
| `3.2.2` | inside `P-sorted-sa-controlflow`; high side of `E-simplify-halt-after-return` and `E-sa-membership-zero-disabled` |
| `3.2.3` | inside `P-sorted-sa-controlflow`; high side of `E-cff-storage-stringarray-per-host` |
| `4.0.0` | exact low side of `E-dbgprot-interval-global-member`; a full ordinary column |
| `4.1.1` | high-end control for the eras ending there; also the first built output above `E-dbgprot-interval-global-member`'s `4.0.0` lower bound |
| `4.2.0` | full high-side column for `E-sa-wrapper-flat`; focused samples cover ignored `import.meta` metadata and optional-call CFF |
| `5.1.0` | inside `P-sorted-sa-controlflow`; first ordinary column after the previously studied `4.2.0` endpoint |
| `5.2.0` | inside `P-sorted-sa-controlflow`; high side for `E-sa-scope-wrapper-shared-upper`, `E-propname-process-env-plain` and `E-directive-rehoist-nested-residual` |
| `5.2.1` | inside `P-sorted-sa-controlflow`; low side of `E-objkeys-loopbody-prohibited` |
| `5.3.1` | high end of `E-propname-process-env-plain` and `E-objkeys-loopbody-prohibited` |
| `5.4.0` | low side of `E-propname-reserved-class-plain`, `E-classfield-reserved-aware` and `E-objkeys-sequence-prohibited` |
| `5.4.2` | inside `P-sorted-sa-controlflow`; ordinary control for the `5.4.3` wrapper-reuse boundary |
| `5.4.3` | high side of `P-sorted-sa-controlflow`; ordinary control for `E-cff-callee-reuse-kind` |
| `5.4.4` | low side of `P-sorted-renameidents-3levels`; high side of `E-cff-callee-reuse-kind` and `E-selfdef-search` |
| `5.4.5` | inside `P-sorted-renameidents-3levels`; low side of `E-generator-arrow-noin-parentheses`, `E-cff-callee-reuse-shape-kind` and `E-selfdef-search-newline-bail` |
| `5.4.6` | inside `P-sorted-renameidents-3levels`; low side of `E-escape-from-raw` |
| `5.4.7` | inside `P-sorted-renameidents-3levels`; low side of `E-sa-surrogate-inline` |
| `5.5.0` | high-side pinned column in `P-sorted-renameidents-3levels`; latest ordinary persistence control |

**One column is partial, and that is legal rather than an oversight.** `2.15.2` carries the
`dead-code` set at every fixture and nothing else: it was appended to settle a dead-code era
boundary straddling `2.15.3`, and no other set in that column would have been read. A partial
column is the cheaper shape when one axis is the question — note that this boundary also happens to
sit on a `P-sorted-*` boundary, `2.15.2` being the last release before
`P-sorted-deadcode-renameidents` opens.

**`2.15.5` was appended to separate two axes that no other version can.** **Two** era axes turn
over at `2.16.0` with identical ranges — the per-scope calls wrapper and object-keys extraction — so no version
separates them. `2.15.5` is the one release in the range at which a *third* axis
(`E-sa-encoding-*`) has moved while both rivals have not, which is what made it worth building.
The result was an elimination: it separated nothing, and the axis earns its column for what that
rules out ([versions.md](versions.md)). **A column appended to rule something out is as legitimate
as one appended to confirm** — and cheaper to interpret, because a negative needs no further
separation.

**Two option sets were appended for the same attribution**, and they are the corpus's first sets
built at *some* columns only: `all-on-noobjkeys` and `all-on-nowrappers`, one-option siblings of
`all-on` (`transformObjectKeys: false` and `stringArrayWrappersCount: 0`), built at `2.15.5` and
`2.16.0`. Once versions are exhausted the only remaining lever is an **option** that varies one
candidate without the other, which is what these are. **So the matrix is now ragged on both
axes** — partial in the set dimension at two columns, partial in the fixture dimension at
`2.15.2` — and a probe that assumes a rectangle is wrong twice over.

**One of them is measurably inert on one cell, and that is a finding rather than a defect.**
`all-on-noobjkeys` is byte-identical to `all-on` on the `control` fixture at `2.16.0` while
differing on the other two, and differing on all three at `2.15.5` — object-keys extraction stops
firing on that input at the era boundary, which is `E-objkeys-call-prohibited` doing exactly what
its name says. Read it per cell; the efficacy of an option is a property of the (version, set,
fixture) triple, never of the option.

**The consequence to hold onto: cells per column is not a constant across the matrix**, so any
probe that divides a total by "cells per column" is wrong here. Count the cells.

**`3.0.0` and `3.0.1` are a negative discriminator.** With the same seed, their shared cells are
byte-identical and the source diff changes no emitted transform shape. They rule out an intervening
boundary before the control-flow storage and dead-code host axes move.

**`3.1.0` and `3.2.0` need an option discriminator as well as full columns.** The ordinary columns
have no population on the axis this boundary turns, so they are indistinguishable on it however
they are read: `stringArrayCallsTransform` is false in every shipped preset and absent from the
corpus's frozen `all-on` family, so no ordinary cell can emit the transformer introduced there.

The focused `calls-transform` set is the existing `baseline` set plus exactly
`stringArrayCallsTransform: true` and `stringArrayCallsTransformThreshold: 1`. It is built only at
`3.2.0`, where the option exists, and at all four fixtures. Its same-version control is the frozen
`baseline` cell, and the option-on cells emit numeric-valued control-flow storage entries on every
fixture. As with the earlier attribution siblings, a set built at only one column is intentional:
the option axis is the only discriminator once the version boundary carries several changes
together.

**`3.2.2` is an ordinary full column whose common cells are byte-identical to `3.2.0`.** That
identity is expected rather than evidence that the source boundary is unreachable: none of the
four frozen inputs contains a value-return followed by another statement in the same block, so the
matrix cannot exercise `E-simplify-halt-after-return`. A direct discriminator does: with
`simplify: true` and unrelated machinery disabled, the low side absorbs the later statement into
the return sequence while `3.2.2` leaves it after the return. The column remains useful as the
nearest-boundary control; the focused shape is cheaper and more precise than appending an input
whose only purpose is this one axis.

The same release also closes `E-sa-membership-zero-draw`, which no ordinary set can expose because
every string-array set uses a non-zero threshold. A direct threshold-zero discriminator at seed
`19196` captures `long-target-value` into the array at `3.2.0` and leaves it directly in the source
declarator at `3.2.2`. That focused pair is again the right shape: appending a general corpus set
for a rare zero-draw edge would add a mostly inert column-wide option axis.

**`3.2.3` is an ordinary full column plus the upstream nested-host discriminator.** Every ordinary
cell is byte-identical to `3.2.2`, and that zero is an absent population rather than an unchanged
shape: no frozen fixture places string-array call indexes in both an outer host and its nested
function. The encoder's own `multiple-storages-1.js` does. On that focused input the low side emits
one shared four-entry storage while `3.2.3` emits two two-entry storages, one per host — the pair
`E-cff-storage-stringarray-shared` → `E-cff-storage-stringarray-per-host` is read from
([versions.md](versions.md)).

**`4.1.1` is a full ordinary column, and building it takes one change to how a set is requested.**
From `4.0.0` `debugProtectionInterval` is milliseconds rather than a boolean, so the package rejects
the corpus's historical `true`; it is mapped mechanically to the shipped high preset's `4000`,
changing no set name and no other option. The interval-bearing cells then emit
`that.setInterval(dp, 4000)` inside a global-resolver IIFE — the member form
`E-dbgprot-interval-global-member` names, whose exact low side is the `4.0.0` column and not this
one. The frozen `4.1.1` cells are the farther-side output control for the two eras that end there.

**`4.1.0` also brings the `service-worker` target, which the ordinary browser/node columns cannot
reach.** A focused three-seed matrix at that target populates its direct `typeof global` resolver in
the console-output and debug-interval helpers, at both `4.1.0` and `4.1.1`. `domainLock` is
validator-unreachable there, as it is for `node`, so the target adds no cell for it.

**`4.2.0` is a full ordinary column plus focused boundary samples.** Every ordinary cell differs
from `4.1.1`, and every difference carries the flat root wrapper `E-sa-wrapper-flat` names.
The ordinary inputs contain neither `import.meta` nor an optional call, so three-seed focused pairs
pin the boundary's other two shapes directly: `import.meta['url']` → `import.meta.url`, and the
flat-wrapper rewrite on its own. Four rows whose documented ranges end inclusively at `4.2.0` —
boolean, numeric raw, split-string and block-switch — are same-seed byte-identical across it and do
not turn here.

A separate minimum source, `(function(){var sum=null;return sum?.(1,2);})();`, reaches the new CFF
call-wrapper producer: the `4.2.0` output stores `callee?.(…)` where `4.1.1` stores an ordinary
call, which throws for the null callee. It stays a focused sample rather than a fifth input,
because it isolates a semantic boundary the existing inputs cannot populate at all.

**The post-4.2.0 columns are ordinary append controls, not a new corpus definition.** The
`5.1.0`–`5.4.5` columns carry the same frozen fixture and per-column set lists, so their rows can
be read against the component axes in [versions.md](versions.md): `5.2.0` exposes the scope-wrapper,
property-name and directive boundaries, `5.2.1` the loop-body object-key refusal, and `5.4.0` the
reserved-class and sequence-position refusals. The `5.4.2`/`5.4.3` ordinary pair is a negative
population control for optional-call wrapper reuse; a focused adjacent-tag census supplies its
discriminator.

The `5.4.4`/`5.4.5` ordinary pair carries the existing self-defending and generator boundaries;
the spread/plain wrapper and `for`-initializer `in` shapes are focused rather than ordinary corpus
inputs and are supplied by focused adjacent-tag cases.
The compact keyword-spacing, RegExp-modifier acceptance and boolean class-heritage changes are
also focused adjacent-tag release-note cases, not claims made from these ordinary cells.

The `5.4.5`→`5.4.6` ordinary differences are the raw-spelling/cache boundary
`E-escape-from-raw`; focused `5.4.6`/`5.4.7` string and escape cases supply the source-spelling,
duplicate-value and lone-surrogate cases. The ordinary `5.4.6`,
`5.4.7` and `5.5.0` columns do not populate the lone-surrogate axis, so no ordinary zero is used
as evidence for that focused behavior. The `5.4.6`/`5.4.7`/`5.5.0` ordinary comparison supplies
the persistence check; its task-local cell counts are not durable version claims.
The `5.5.0` row is a persistence control for the pinned encoder output; it does not turn every
source-only or unpopulated axis into an output claim.

**`2.19.0` is the spine** — the column built, frozen and closed out first, and the reference every
later column is appended alongside. Which version takes that role was a study decision rather than
an encoder fact ([versions.md](versions.md)); what this page owes is that one column holds it, and
becoming older than the newest column in the matrix does not change that.

## Input fixtures

Four small programs. Each is deterministic, terminates immediately, and reports a fixed set of
lines, so two builds of the same fixture can be compared as text.

**The fourth was appended later, and how it was appended is part of the recipe.** A new input is
built at **the set list each column already carries**, read off the existing cells — never at a
global list. Columns do not agree: two carry the two attribution siblings and one is a three-cell
partial, so a global list would quietly widen the corpus along the *option* axis while claiming to
widen it along the input axis. The freeze rule covers the rest: existing cells are not rewritten,
and after the append every pre-existing cell was verified byte-identical by digest.

**Reporting goes through `process.stdout.write`, never through `console.log`, and that is a
correctness requirement rather than a style choice.** The `disableConsoleOutput` option replaces
the console methods with no-ops, and **three of the four shipped presets set it**
([presets.md](presets.md)). A fixture that reported through `console.log` would fall silent in
exactly the cells that matter most. `process.stdout.write` is untouched by it — measured at
`2.19.0`, including under `high-obfuscation`.

Each fixture also carries **one** `console.log('console-channel')` line. It is deliberate: it is
shape material for the transforms that rewrite member expressions and string literals, and whether
it survives to the output is a fact about the sample worth being able to see. It is excluded from
the comparison channel precisely because it is expected to vanish in some cells.

`strings.js` — string literals, concatenation, member reads; the string array's own input:

```js
function greet(who) { return 'hello, ' + who + '!'; }
var parts = ['alpha', 'beta', 'gamma'];
var joined = parts.join('-');
var upper = joined.toUpperCase();
console.log('console-channel');
process.stdout.write(greet('world') + '\n');
process.stdout.write(joined + ' ' + upper + ' ' + parts.length + ' ' + 'literal'.charAt(0) + '\n');
```

`control.js` — branches, a loop, a `switch`; control-flow flattening and dead-code injection:

```js
function classify(n) {
  if (n < 0) { return 'neg'; }
  else if (n === 0) { return 'zero'; }
  return 'pos';
}
var acc = 0;
for (var i = 0; i < 5; i++) { if (i % 2 === 0) { acc += i; } else { acc -= i; } }
var label;
switch (acc) {
  case 2: label = 'two'; break;
  case 6: label = 'six'; break;
  default: label = 'other';
}
console.log('console-channel');
process.stdout.write(label + ' ' + acc + '\n');
process.stdout.write(classify(-1) + ' ' + classify(0) + ' ' + classify(1) + '\n');
```

`objects.js` — object literals, computed member access, closures; the converting transforms:

```js
var config = { name: 'widget', size: 3, nested: { flag: true } };
function makeCounter(start) {
  var n = start;
  return function () { n += 1; return n; };
}
var next = makeCounter(config.size);
var key = 'na' + 'me';
console.log('console-channel');
process.stdout.write(config[key] + ' ' + config.nested.flag + ' ' + config['size'] + '\n');
process.stdout.write(next() + ' ' + next() + ' ' + Object.keys(config).join(',') + '\n');
```

`directives.js` — a `"use strict"` prologue at two scopes, a statement-level `&&`, and a string
expression statement that is **not** a directive:

```js
'use strict';
var trace = [];
function tag(flag, name) {
  'use strict';
  var out = name;
  'not-a-directive';
  flag && trace.push('and-taken');
  if (flag) { out = name.toUpperCase(); }
  return out;
}
var first = tag(true, 'alpha');
var second = tag(false, 'beta');
console.log('console-channel');
process.stdout.write(first + ' ' + second + ' ' + trace.length + '\n');
process.stdout.write(trace.join(',') + ' ' + typeof tag + '\n');
```

**Three details in it are load-bearing rather than incidental**, and each would be lost by an
innocent-looking edit:

- **`'not-a-directive'` sits *after* `var out = name;` on purpose.** A directive prologue is the
  maximal run of string expression statements at the *start* of a body, so moving that line up by
  one would make it a second directive and destroy the discriminating case — the whole point is one
  string that is a directive and one that is not, in the same scope and the same run.
- **The `if (flag) { … }` is there to be collapsed by the encoder**, so the emitted cells carry a
  statement-level `&&` the *encoder* produced as well as the one the input wrote. The axis would
  otherwise only ever see our own input echoed back.
- **Everything in it is strict-safe**, since the directive makes the whole program strict. A
  fixture that relied on sloppy-mode behaviour would throw rather than report.

## Focused producer cells

The ordinary matrix remains the four fixtures and its existing per-column set lists. A focused
cell is a separate, named producer probe: it is frozen under the same `out/` manifest, but it does
not widen any ordinary version column or change any ordinary set definition.

`class-logical.js` is the focused 2.19.0 input. It must be stored verbatim, including its final
newline:

```js
const enabled = true;
class Greeter {
  ["quoted"]() {
    return "class-value";
  }
}
if (enabled) {
  process.stdout.write(new Greeter()["quoted"]() + "\n");
}
```

Its one focused set, `class-logical`, is exactly:

```js
{
  compact: true,
  seed: 20260809,
  target: 'browser',
  stringArray: false,
  simplify: true,
  transformObjectKeys: true,
  renameGlobals: false,
}
```

The clean-room builder resolves the exact `jso-2-19-0` npm alias from
`sandbox-tests/encoders/node_modules`, verifies its package version is `2.19.0`, and validates
these option names against the installed upstream typings before encoding. It writes exactly
`out/2.19.0/class-logical__class-logical.js` and adds exactly that path to `out/manifest.json`.
Before appending it must validate every pre-existing manifest entry and output digest; a rerun
must skip the frozen cell byte-for-byte and leave all pre-existing files and manifest values
unchanged. The focused output is accepted only when an ESTree parse finds both a computed class
method whose quoted string key is `"quoted"` and a top-level `ExpressionStatement` whose
`LogicalExpression.operator` is `&&`. Runtime is a regression check only: source and output must
both write `class-value\n`.

The emitted 2.19.0 shape is compactly:

```js
const enabled=!![];class Greeter{['quoted'](){return'class-value';}}enabled&&process['stdout']['write'](new Greeter()['quoted']()+'\x0a');
```

The class member closes the ordinary-input class population gap, and the top-level `&&` closes the
producer population gap left by an input expression nested in `directives.js`. This focused cell
is not a fifth ordinary fixture and `class-logical` is not added to the ordinary set matrix.

## What the four ordinary inputs cannot reach

**The option matrix decides which transforms are *enabled*; the inputs decide which ones have
anything to act on.** These programs are small and deliberately so, and the consequence is
that several transforms can never be observed firing anywhere in the corpus, at any version, under
any option set. That is a property of the inputs rather than of the encoder, so it belongs here
next to them — and it is stable, because the fixtures above are frozen and quoted verbatim.

Every row below was checked against the four files mechanically rather than by reading them:

| Absent from all four inputs | What it makes unobservable |
|---|---|
| a `class` declaration or class field | computed/quoted class-member shapes and the ordinary matrix's `ClassFieldTransformer` population, so [`E-classfield-*`](versions.md) has no ordinary output behind it; the focused cell above supplies one producer-faithful class-method-key population |
| a template literal | `TemplateLiteralTransformer`, so both [`E-template-*`](versions.md) rows are source-only |
| a spread argument in any call | the control-flow call wrapper's spread handling, [`E-cff-callee-*`](versions.md) |
| any `let` or `const` declaration | the `const`/`let` spelling of every custom node. The prevailing-kind analyzer sees an all-`var` program and rewrites each one to `var`, so the alternative spelling is unreachable ([control-flow-block-flattening.md](transforms/control-flow-block-flattening.md)) |
| a destructuring pattern | `ObjectPatternPropertiesTransformer` ([shorthand-expansion.md](transforms/shorthand-expansion.md)) |
| an `export` — the inputs are scripts, not modules | `ExportSpecifierTransformer`, same doc |

**One of these cuts the other way and is worth not misreading.** The absence of `let`/`const` does
not weaken control-flow flattening's coverage — it is what *gives* the corpus that coverage at all,
since a block whose subtree contains either is refused outright. An all-`var` input is the
favourable case for that transform, not the neutral one.

**Two ways to close a row, and the freeze rule allows both.** Append an input, which makes the gap
measurable across every version column at the cost of a corpus rebuild; or build the shape directly
at the versions that bound the era, which is cheaper and is what closed `E-cff-callee-*`. Prefer the
second for a gap that touches one axis, the first for a shape several transforms would act on.
**Neither is done by editing the fixtures above** — a set whose definition moves is not
comparable with the columns already built against it.

**The ordinary append closed the strict-directive row, but it did not by itself close the producer
`&&` question.** `directives.js` carries an input `&&` inside `tag`, while the focused source above
places an `if` at program level so `simplify` must emit a top-level statement-level `&&`. The focused
cell therefore supplies the positive AST population rather than treating runtime equivalence or
the pre-existing nested input expression as encoder evidence. Its one output is appended to the
manifest without rebuilding any ordinary cell; any corpus-wide census that combines ordinary and
focused rows must be rerun against this frozen manifest.

## Option sets

Per-feature sets, the four shipped presets, and the maximal profile with focused variants.

**Sets are appended, never edited or removed**, so this list grows and the count is not a fixed
property of the corpus — read the section headings rather than a total. Appending is what the
freeze rule permits: an ordinary coverage set adds cells to every compatible version column, while
a boundary discriminator is built only where its option exists and can separate the candidates.
Neither disturbs a byte of what is already there, so figures measured against the old cells stay
comparable. Editing a set's definition would not, which is why a set that turns out to under-cover
something gets a **sibling** rather than a correction.

Two settings are shared by every hand-built set and pinned rather than left to the encoder's
defaults:

- **`seed`.** Without it, identifier names and string-array order vary per run and no two builds
  are comparable. The shipped presets carry `seed: 0`, which is **not** reproducible — two runs at
  `seed: 0` differ. Overriding it is therefore required even for the preset cells, and it is
  shape-neutral: it fixes which random choices are made, not which transforms run or how often.
- **`target: 'browser'`**, which is what all four presets ship. It gates which custom code helpers
  are emitted, so it is a shape input and is recorded rather than defaulted.

### The per-feature sets

Each is the string-array base `{ compact: true, seed: S, target: 'browser', stringArray: true,
stringArrayThreshold: 1 }` varying **one** thing. Thresholds are forced to `1`, never a
probability, so a transform either fires everywhere it can or not at all — which is what makes a
cell attributable to one feature.

| Set | Adds to the base |
|---|---|
| `baseline` | nothing — the reference the others are compared against |
| `no-rotate` | `rotateStringArray: false` |
| `wrappers-variable` | `stringArrayWrappersCount: 2`, `stringArrayWrappersType: 'variable'`, `stringArrayWrappersChainedCalls: false` |
| `wrappers-function` | `stringArrayWrappersCount: 2`, `stringArrayWrappersType: 'function'`, `stringArrayWrappersChainedCalls: false` |
| `chained-calls` | as `wrappers-function`, but `stringArrayWrappersChainedCalls: true` |
| `encoding-base64` | `stringArrayEncoding: ['base64']` |
| `encoding-rc4` | `stringArrayEncoding: ['rc4']` |
| `dead-code` | `deadCodeInjection: true`, `deadCodeInjectionThreshold: 1` |
| `cff` | `controlFlowFlattening: true`, `controlFlowFlatteningThreshold: 1` |
| `self-defending` | `selfDefending: true` |
| `debug-protection` | `debugProtection: true` |
| `debug-protection-interval` | `debugProtection: true`, interval enabled — `debugProtectionInterval: true` through `3.2.7`, normalized to `4000` from `4.0.0` |
| `console-output` | `disableConsoleOutput: true` |
| `wrappers-none` | `stringArrayWrappersCount: 0` |
| `encoding-all` | `stringArrayEncoding: ['none','base64','rc4']` |
| `calls-transform` | `stringArrayCallsTransform: true`, `stringArrayCallsTransformThreshold: 1` — `3.2.0` only |

**`wrappers-none` and `encoding-all` were appended after the original list**, each closing a branch
it could not reach:

- **`wrappers-none` varies the count *downward*, which nothing else does.** The three wrappers sets
  all raise it and every shipped preset ships at least one, so "no scope wrapper at all" — a
  configuration the encoder fully supports — had no cell in the matrix.
- **`encoding-all` is the only set with more than one encoding and live use sites.** The maximal
  profile also carries all three, and therefore one root calls wrapper per encoding, but its array
  is starved (see the maximal profile below), so it emits that shape with nothing using it. Kept as
  a per-feature set rather than folded into the maximal one because the point is to vary *one*
  thing: three concurrent wrappers, everything else at the base.

**`calls-transform` is a boundary discriminator, not a general coverage append.** The option does
not exist below `3.2.0`, and every shipped preset at that release leaves its boolean off even where
the threshold is non-zero. Building the base plus the boolean and a forced threshold at the high
side is therefore the only same-version comparison that proves the new transformer populated; the
ordinary `baseline` cell at `3.2.0` is its control.

**`stringArrayWrappersChainedCalls` defaults to `true`**, so the wrappers sets must switch it
*off* explicitly or they would silently also be testing chained calls, and `chained-calls` would
differ from `wrappers-function` in nothing at all.

**They do switch it off, and `chained-calls` is nonetheless byte-identical to `wrappers-function`
on every cell of the matrix.** The option is applied correctly; it has nothing to act on, and the
cause is the inputs' *shape* rather than the set definitions. A scope's wrapper is
allocated lazily, when a literal in that scope is replaced, while the wrapper is emitted on
**leave** — so a nested scope resolves its upper wrapper before its parent has necessarily
allocated one, and falls back to the root. Every input declares its functions *above* the
program-level string reads and nests one level deep, so the parent scope is always still empty at
that moment and the chained branch is never taken. Not even the random draw differs, which is what
makes the outputs identical rather than merely equivalent.

Any input append re-opens this check: a source that nests two levels deep or declares a function
below a program-level string read can make the chained-wrapper set live.

Confirmed by building the same source both ways at the spine: a program whose outer literals sit
**before** the nested function, or which nests two functions deep, differs immediately and emits
wrappers forwarding to other wrappers. So the missing coverage is a **fixture** gap, not a set
gap — adding a fourth input would reach it, at the cost of a column across the whole matrix.

**What this leaves uncovered:** chained calls are exercised in the matrix only by `preset-medium`
and `preset-high`, which also enable `controlFlowFlattening` and so cannot attribute anything read
off their cells to this component alone. The axis that reads it is **the wrapper's forwarding target** —
a scope wrapper whose callee is another scope wrapper rather than the root
([string-array-scope-calls-wrapper.md](transforms/string-array-scope-calls-wrapper.md)). A census
over it should find none on `chained-calls` and some on the two presets, at every version.

**`stringArrayEncoding` is an array**, at every version in the matrix — `'base64'` as a bare
string is a validation error. Likewise `debugProtectionInterval` is a **boolean** here; the
millisecond form belongs to later releases ([options.md](options.md)).

### The four shipped presets

`preset-default`, `preset-low`, `preset-medium`, `preset-high` — `{ optionsPreset: <tier>, seed: S }`
and nothing else.

**Taken exactly as shipped.** The forced-to-`1` rule above applies to the per-feature sets only;
overriding a tier's thresholds would manufacture a configuration the encoder never ships. Only
`high` forces its thresholds, so the other three run at partial strength, and **these cells are
the corpus's only coverage of partial application** — a transform firing at some sites and not
others, which every forced-to-`1` cell structurally cannot produce. `default` is included as a
tier in its own right: it is what the encoder emits when asked for nothing.

### The maximal profile

`all-on` — every boolean in the option surface it was frozen against, every threshold at `1`, every
array-valued option carrying all of its values (`stringArrayEncoding: ['none','base64','rc4']`, both
`stringArrayIndexesType` values), and each scalar enum pinned to what the shipped tiers use. It sits
strictly **above** `high-obfuscation`, which leaves several transforms off and pins each array
option to one value.

**The name does not update when a later release adds an option.** At `3.2.0`, this frozen set omits
the new `stringArrayCallsTransform` boolean, so it is option-off there despite being called
`all-on`. The `calls-transform` sibling is the legal append that covers it; editing this set would
invalidate every earlier cell.

**A scalar enum cannot be "all on".** `stringArrayWrappersType: ['variable','function']` is a
validation error, so this profile reaches exactly one wrapper shape; the other is covered by its
own per-feature set. The same applies to any other scalar-enum option.

**Turning everything on turns the string array off, and this cell is the corpus's weakest one for
it — not its strongest.** `splitStringsChunkLength: 2` chops every program string into two-character
chunks, and a literal shorter than three characters never enters the string array
([string-array.md](transforms/string-array.md), item 2). So no program string reaches the array in
this profile at any version in the matrix: from `2.10.0` up the subsystem is emitted complete —
holder, rotator, one wrapper per encoding — while serving nothing but the custom code helpers' own
strings.

**At `2.9.6` it is not emitted at all, and that is the one column where this profile differs in
kind rather than in degree.** Read off the emitted samples per column at this profile: `2.10.0` and
above carry a holder, a wrapper and a rotator, while `2.9.6` carries none of the three. It is the
only cell in the whole matrix that does. The
sibling below isolates the cause as the starvation rather than the version: at `2.9.6`
`all-on-split10`, which differs only in the chunk length, resolves normally. What differs across
that one column boundary is that `StringArrayRotateFunctionTransformer` does not exist until
`2.10.0` — the same boundary [versions.md](versions.md)'s `E-sa-rotate-counter-loop` records as
"emitted by a code helper alone; there is no rotate transformer yet" — so at `2.9.6` a starved array
leaves nothing behind, and from `2.10.0` the transformer emits the machinery regardless. **So this
profile covers three concurrent wrappers at every column except `2.9.6`, where it covers nothing at
all**, and any census reading it as the multi-encoding cell is reading one column short. Re-encoding
the same profile with the chunk length raised is what isolates it, and it flips the cell from no
program use sites to many.

- **The general rule, of which this is one instance:** an "everything at maximum" profile is not a
  maximum of *exercise*. Options interact through the stage order, and one set late enough in that
  order can starve a transform earlier readers assume it strengthened. Whether a cell exercises a
  transform is a property to measure per cell, never to infer from the option list.
- **"Starved" means starved of *program* strings, and the distinction is worth holding onto**,
  because the shorter reading — that the cell has no live accessor call sites at all — is false and
  has been written down here before. Counted through the accessor binding rather than
  by identifier shape, the profile's cells carry plenty of live call sites; they are
  simply all made by the custom code helpers, which `splitStrings` does not chunk. So the index
  options that act on a call site *are* exercised in this profile, on helper-served sites, even
  though no program string reaches the array. **Count through the binding, never through an
  `_0x…` name pattern** — this profile does not use the hexadecimal identifier generator, so a
  name-shaped count reads a blind zero here and a plausible number everywhere else.
- **What the cell still covers**, and it is the only cell that does: three concurrent root calls
  wrappers, one per value of `stringArrayEncoding`. That is a real shape and this is the corpus's
  sole coverage of it — the reason the cell keeps its place rather than being rebuilt.
- **Deliberately not fixed by editing the profile.** The corpus is frozen, and a set whose
  definition moves is not comparable with the columns already built against it. The gap is closed by
  *appending* a set, which the freeze rule allows, never by rewriting this one.

**`all-on-split10` is that sibling** — the same profile with `splitStringsChunkLength: 10`, which
clears the length gate and is the only difference between them. The pair is worth more than either
alone: they differ in exactly one option, so anything that differs between their cells is
attributable to it, which is what turned the starvation from an observation into an isolated cause.
Note what the un-starved cell is *not*: its wrappers are function-form like the parent profile's,
so it is a maximal-strength cell, not a second multi-encoding cell with simple use sites —
`encoding-all` is what covers that.

**`all-on-selfdef` is the second sibling**, the profile plus `selfDefending: true` and nothing
else. It exists because the maximal profile does **not** set `selfDefending`, despite being defined
as every boolean on — and unlike `domainLock` and `renameProperties`, which are excluded for stated
structural reasons, this one is simply an omission. The sibling restores the profile's own stated
intent rather than adding a new axis, and appending is the only legal repair: the definition of a
frozen set is never edited.

- **What it covers that nothing else did.** `preset-high` is the corpus's only other full-strength
  cell carrying `selfDefending`, and it has none of `renameGlobals`, `unicodeEscapeSequence`, three
  concurrent encodings, or the index-shift and indexes-type options. So self-defending combined
  with *those four* had no cell anywhere in the matrix.
- **The one-option claim is exact, and it was worth checking**: `SelfDefendingRule` normalizes
  `selfDefending: true` by also forcing `compact: true`, which the maximal profile already sets. So
  no second option moves silently underneath the pair, which is what would have made the two cells
  non-attributable.
- **Not inert, measured against its true neighbour rather than against `baseline`.** Every cell
  built for the set differs from its `all-on` counterpart, and each carries exactly one guard
  trigger its neighbour lacks.
- **It exercises both self-defending eras**, which a single-version cell could not: the
  callback carries the nested-function body below `2.19.0` and the `search` chain at `2.19.0`,
  splitting on that boundary across the columns that represent both eras.
- **The un-starved variant was deliberately not also appended.** `all-on-split10 + selfDefending`
  is a legal further append, but the guard's own strings are helper strings, which `splitStrings`
  does not chunk — so starvation does not reach the machinery this set exists to exercise. Append
  it if a use for it appears, not on principle.

**Two options are excluded from `all-on` and from the corpus entirely**, for the same structural
reason rather than a preference — nothing can exercise them here, and nothing ever undoes them:

- **`domainLock`.** Its content is a browser domain check. It is restricted to browser targets by
  `@IsAllowedForObfuscationTargets`, so it is a validation error against `target: 'node'`, and no
  shipped tier enables it. A sample carrying it cannot be run anywhere the corpus runs.
- **`renameProperties`.** It renames property names it has no way to know are external API — it
  renames `stdout` on `process`, so the emitted program dies with `Cannot read properties of
  undefined (reading 'write')` before producing a line. Measured at `2.19.0` by bisecting the
  maximal profile; removing it makes the profile run. It is in no shipped preset either.

## Nested cells — a source encoded twice

A separate, smaller set answering a different question: what does the encoder emit when its
**input is already its own output**? Built into `sandbox-tests/out-nested/`, never into the frozen
`out/` — a nested cell is a different kind of cell, and the freeze rule forbids disturbing an
existing column.

- **Both layers at `2.19.0`**, the string-array base set (`stringArray: true`,
  `stringArrayThreshold: 1`, `compact`, `target: 'browser'`). All-options-on is unnecessary: the
  question is layering, not option coverage, and a smaller set keeps the sample readable.
- **The two layers take *different* seeds.** Same-seed layers would make the outer layer's name
  allocation mirror the inner layer's, which is not what a real double encode looks like and could
  manufacture a name collision that a later reader credits to something else.
- Both the once- and twice-encoded outputs are kept (`<fixture>__x1.js`, `__x2.js`); the singly
  encoded one is the control that says what one layer looks like at the same seed.

**What it emits, measured at `2.19.0`:** the outer layer's machinery is in **plain string
literals**, and the inner layer's string-valued parts are routed through the outer layer's calls
wrapper — the inner array's elements are `outerWrapper(0xNN)` calls rather than literals, and the
inner rotator's `push`/`shift` member keys are too. Size roughly doubles per layer — measure the
pair in front of you rather than carrying a figure from an earlier build.

That asymmetry is the durable observation: **re-encoding hides strings and not numbers.** Anything
keyed on a string literal sees only the outermost layer; anything keyed on numeric shape sees every
layer.

### The robustness variant — fix the inner layer, vary the outer

A second nested set answering "how far does the outer layer re-spell the inner one?", under
`out-nested/robust/`. The inner layer is held at the string-array base set and **only the outer
set varies**, so the inner layer is identical across every cell by construction and any difference
is attributable to the outer options alone.

Outer sets are chosen for what each does to the inner layer's *machinery*, not for coverage:
`baseline`, `numbers-to-expressions` (rewrites the inner index shift into an arithmetic tree),
`controlFlowFlattening` (restructures the inner prelude), `deadCodeInjection` (injects branches
into it), `splitStrings` (breaks up the inner array's elements), and `high-obfuscation` (all of the
above plus the anti-tamper helpers). One inner sample keyed `_inner__<fixture>.js` is written
alongside as the control.

**Scale, so the cost is known before building it:** a single-feature outer set costs a small
multiple of the inner sample's size, while `high-obfuscation` costs one to two orders of magnitude
more — enough that the robustness cells dominate the nested directory.

## Determinism and the freeze rule

**Freeze the corpus before measuring anything against it.** The encoder randomizes by design —
placeholder names, string-array order, injected-code placement and template choice are regenerated
per run, and several transforms are probability-gated — so two fresh encodes are not comparable to
each other at all, and re-encoding turns every figure previously measured against the old samples
into anecdote. A pinned `seed` makes a *rebuild* reproducible; it does not make two differently
seeded builds comparable.

**Build the spine column first, then append.** `2.19.0` is encoded and frozen before any earlier
version is built. Later columns are added alongside; an already-frozen cell is never regenerated.
Each batch pins the same seed, so a column added later is reproducible on its own terms.

**Make the freeze mechanical, not remembered.** The encode script skips any cell already present
on disk, and records a digest per cell in a manifest alongside the seed it was built under. Two
things follow that a convention alone does not give: re-running the script is a no-op rather than
a silent regeneration, and "was this cell rebuilt?" stays answerable afterwards. The manifest also
refuses to extend a corpus with a different seed, since a differently seeded batch is not
comparable to the frozen ones and would otherwise sit in the same directory looking like one.

**One append falls short of that guarantee, and it is recorded rather than repaired.** The `4.2.0`
append's intended pre-append snapshot was overwritten by an immediate no-op rerun, so for the cells
added between the last durable snapshot and that append, immutability rests on the current digests
matching the manifest rather than on an independent before-and-after comparison. Repairing it would
mean rewriting frozen history, which costs more than carrying the caveat does.

## Reading the corpus across versions

A frozen matrix answers one question for free, and it is a question no source reading can answer:
**where does the emitted output actually change?** Hash the same `(fixture, option set)` cell at
two adjacent versions and compare.

**Byte-identity is strong evidence; byte-difference is weak.** If two versions emit identical
bytes for every fixture, that transform pipeline is unchanged between them for those options. If
they differ, *something* moved — but identifier allocation alone can account for it, so a
difference is a place to look rather than a finding.

**Identity is seed-independent, which is what makes it usable.** If two versions' algorithms agree
they agree at every seed; if they differ they differ at essentially any seed. Verified by
re-running the comparison at three different seeds, one of them a string — the identities were the
same each time. This is worth restating because almost nothing else measured against a corpus has
that property: it is a fact about the encoder rather than about the build.

**Do not read a per-set identity table as an era boundary.** It is a lead. An emitted-shape era is
entered by studying the component, not by diffing bytes — and one set's agreement says nothing
about another's, which is the same per-component argument [versions.md](versions.md) makes.

## What the emitted samples do when run

Properties of the encoded artifact, measured over the **whole matrix** — every set at every
version on every fixture, built and executed, twice independently. They are facts about the
encoder's output, and anything that executes these samples has to accommodate them:

| Cells | Behaviour |
|---|---|
| `debug-protection-interval`, `preset-high`, `all-on`, `all-on-split10`, `all-on-selfdef` | **hang.** A `setInterval` holds the event loop open. The reported lines are written *before* the hang, so reading the stream and then killing on a timeout still recovers them |
| `console-output`, `preset-low`, `preset-medium`, `preset-high`, `all-on`, `all-on-selfdef` | the `console-channel` line disappears, wholly or partly. How much vanishes depends on where the seeded injection of the console-disabling helper lands relative to the call |
| every other cell | run to completion |

**A timeout is mandatory on every execution**, not only the cells known to hang. The table holds
uniformly across every version column in the matrix, but it is a statement about *these* releases and
is re-measured rather than carried to an unbuilt one.

**The reporting channel held on every cell.** Building and running the entire matrix, every sample
reproduced its fixture's `process.stdout.write` lines exactly — including the cells that hang,
whose lines are written before the event loop is pinned open. That is the property the fixture
design exists to guarantee, and it is worth re-checking whenever a version or a set is added,
because a set that silently reports nothing looks identical to a set that reports correctly.

## Layout

Everything below lives in the gitignored sandbox and is regenerable from this page.

```
sandbox-tests/
  fixtures/<fixture>.js                          the four inputs, verbatim above
  encoders/                                      one npm-alias install providing every version
  out/<version>/<fixture>__<optionset>.js        encoded samples
  out/2.19.0/class-logical__class-logical.js     the focused producer cell above
```

**A version that has no npm tarball is exported, never built in place.** The pinned commit is the
case: `git archive <pin> | tar -x` into a directory under `encoders/` and build *there*. The
submodule's own `.gitignore` covers `/dist` and `/node_modules`, so an in-place build would be
mostly invisible — which is the argument for exporting rather than against it. Exporting keeps the
read-only checkout provably untouched and ties the build's provenance to a SHA. A version built
this way is a different toolchain from the npm ones, so a build failure there is a fact about that
toolchain and must never be read as a finding about the encoder's output.

## Traps

| trap | what goes wrong |
|---|---|
| reporting through `console.log` | three of the four presets disable it, so the cells that matter most report nothing and read as a broken build |
| thresholds forced to `1` on preset cells | manufactures a configuration the encoder never ships, and destroys the corpus's only coverage of partial application |
| leaving `seed` at the shipped `0` | not reproducible; two runs of the same tier differ, and no comparison against the corpus means anything afterwards |
| `stringArrayWrappersChainedCalls` left at its default | it defaults to `true`, so a "wrappers" cell silently tests chained calls too |
| `stringArrayEncoding` written as a string | a validation error, not a coercion |
| a crashing cell's stderr | the emitted program is one enormous line, so a crash dumps the whole sample into the log. Capture stderr rather than inheriting it |
| assuming a cell that runs proves the option worked | an **unknown** option name is accepted silently and ignored ([options.md](options.md)), so a set can encode cleanly and test nothing. Compare each cell against `baseline` and treat identity as a failed cell |
| comparing an option's cell against `baseline` only | **the check `chained-calls` passes while testing nothing.** A set that varies one option off another set has *two* neighbours, and baseline is the one that cannot detect an inert option: `chained-calls` differs from `baseline` in everything `wrappers-function` differs in, so the efficacy oracle reads green while the option under test does nothing. Diff each set against **the set it varies against**, not only against `baseline` |

## Source

- Option names, types and accepted values per version: [options.md](options.md).
- Tier contents and how they nest: [presets.md](presets.md).
- What each version is on the pipeline-order axis: [versions.md](versions.md).
- The `domainLock` target restriction:
  [`src/options/validators/IsAllowedForObfuscationTargets.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/45ad03b8335bee095b17c0d29b0a78bff158c93a/src/options/validators/IsAllowedForObfuscationTargets.ts).

## Fixtures

This page is the ordinary fixture specification, and the four inputs above are its content. The
focused `class-logical.js` input is the one explicit exception: it is retained with its frozen
2.19.0 output and manifest entry so the two positive AST populations remain independently
reproducible. The ordinary matrix samples remain large, regenerable, and frozen per build rather
than per commit.
