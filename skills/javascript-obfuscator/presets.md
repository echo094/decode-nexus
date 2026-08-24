# Shipped Presets

The complexity tiers the obfuscator ships in `src/options/presets/`: what each one sets, how they
relate to each other, and where their contents move. Cross-cutting, like the option surface it
sits on top of — a preset is a bundle of options, so [options.md](options.md) is what says whether
a name in one of these tiers even exists at a given release.

**This page keys on tags, never on era IDs**, for the reason [order.md](order.md) states: it takes
readings, and the era registry is a consumer of readings. Contents below are read at `2.19.0`
(phase 1's newest version) and at `5.5.0` (the pin), with the range between them swept for drift.

**Why these matter more than any option set someone assembles by hand: most real-world samples are
preset output.** People obfuscating something reach for a named tier — or for nothing at all,
which is `default`. A hand-built option combination is a diagnostic instrument; a preset is what
the encoder is actually asked to do.

## Four selectable tiers, and one that is not

`default`, `low-obfuscation`, `medium-obfuscation`, `high-obfuscation` — the four values of
`OptionsPreset`, selectable through the `optionsPreset` option. `Options` holds them in a
`Map<TOptionsPreset, TInputOptions>` and merges the chosen one under the caller's own options.

A fifth file, `NoCustomNodes.ts`, is **not** selectable and is not a tier. It feeds
`CustomCodeHelperObfuscator`, the private pipeline that obfuscates injected helper code — the same
nested-encode mechanism [order.md](order.md) describes for the rotate function.

**`default` is not "no preset".** It is the preset applied when the caller names none, so it is
the configuration behind every sample produced by someone who just ran the tool. It is a tier like
the others and behaves like one.

## They are strictly nested

Each tier literally spreads the previous one — `LOW` spreads `DEFAULT`, `MEDIUM` spreads `LOW`,
`HIGH` spreads `MEDIUM` — so tier *n+1* is tier *n* plus a delta, with no option ever removed or
reverted. Subset semantics therefore holds here.

**That is a measurement, not an assumption, and it can come out the other way.** In another
obfuscator studied under this hub the `low` tier skips a whole transform the higher tiers use, so
its output is a genuinely distinct shape rather than a subset. Read the relationship per encoder
rather than inheriting it.

## What each tier adds, at `2.19.0`

`default` is stated in full because everything else is a delta on it; only the shape-bearing
options are listed, and the source is linked below for the rest.

| Tier | Sets |
|---|---|
| `default` | `compact`, `simplify`, `stringArray`, `stringArrayThreshold 0.75`, `rotateStringArray`, `shuffleStringArray`, `stringArrayIndexShift`, `stringArrayWrappersChainedCalls`, `stringArrayWrappersCount 1`, `stringArrayWrappersType variable`, `stringArrayWrappersParametersMaxCount 2`, `stringArrayEncoding [none]`, `stringArrayIndexesType [hexadecimal-number]`, `identifierNamesGenerator hexadecimal`, `target browser`, `controlFlowFlatteningThreshold 0.75`, `deadCodeInjectionThreshold 0.4`, `domainLock []`, `seed 0`. Everything else off |
| `low-obfuscation` | `disableConsoleOutput`, `selfDefending` |
| `medium-obfuscation` | `controlFlowFlattening`, `deadCodeInjection`, `numbersToExpressions`, `splitStrings` + `splitStringsChunkLength 10`, `transformObjectKeys`, `stringArrayEncoding [base64]`, `stringArrayWrappersCount 2`, `stringArrayWrappersType function`, `stringArrayWrappersParametersMaxCount 4` |
| `high-obfuscation` | `controlFlowFlatteningThreshold 1`, `deadCodeInjectionThreshold 1`, `stringArrayThreshold 1`, `debugProtection`, `debugProtectionInterval`, `splitStringsChunkLength 5`, `stringArrayEncoding [rc4]`, `stringArrayWrappersCount 5`, `stringArrayWrappersParametersMaxCount 5` |

**`low`'s real delta is two options.** It also restates `rotateStringArray`, `shuffleStringArray`
and `simplify`, all of which `default` already sets to the same values — so reading the file as a
list of what the tier turns on overstates it by three.

### What the pin changes

The tiers keep their shape; the deltas move only where the option surface moved under them.

- `rotateStringArray` / `shuffleStringArray` become `stringArrayRotate` / `stringArrayShuffle`
  ([options.md](options.md), the `3.0.0` renames).
- `stringArrayCallsTransform` joins the ladder, which did not exist in phase 1: `default` sets it
  `false` with `stringArrayCallsTransformThreshold 0.5`, `low` pins it `false` / `0`, `medium`
  raises the threshold to `0.75`, `high` to `1`. So the calls transform is a *graduated* setting
  at the pin rather than a boolean anyone flips.
- `debugProtectionInterval` becomes milliseconds, and `high` sets **`4000`** rather than `true`.

## Only `high` forces its thresholds

The single most consequential fact on this page for anyone building samples from these tiers.

| Tier | `stringArrayThreshold` | `controlFlowFlatteningThreshold` | `deadCodeInjectionThreshold` |
|---|---|---|---|
| `default` | `0.75` | `0.75` | `0.4` |
| `low` | `0.75` | `0.75` | `0.4` |
| `medium` | `0.75` | `0.75` | `0.4` |
| `high` | `1` | `1` | `1` |

`medium` turns control-flow flattening and dead-code injection **on** without touching their
thresholds, so it runs both at partial strength. Three of the four tiers therefore emit **partial
application** — a transform firing at some sites and not others — and that is what the great
majority of real samples look like. Any sample set built with thresholds forced to `1` for
isolation reasons contains none of it, by construction.

## Contents move, and not where the tier files do

Swept across every release tag from `2.9.6` to `5.5.0`:

- **The three tiers' own deltas do not change anywhere inside phase 1.** `LowObfuscation.ts`,
  `MediumObfuscation.ts` and `HighObfuscation.ts` are byte-stable across the whole `2.x` range and
  move only at the pin.
- **`default` changes five times inside phase 1**, and every one of the five lands exactly on an
  option-surface boundary from [options.md](options.md) — a newly declared option acquiring its
  default value, nothing more. No shape-bearing default is retuned anywhere in the range.

So for every option a phase-1 sample set would touch, tier contents are constant across the range,
and a tier read at one `2.x` tag can be trusted at another. That is a finding, not a licence: it
was established by reading all 26 release tags, and the same claim above `2.19.1` rests on the two
ends plus the sweep between them.

## Known Quirks

- **The shipped `seed` is `0`, and `seed: 0` is not reproducible.** Two runs of the same tier over
  the same input at `seed: 0` differ; pinning any non-zero seed makes them byte-identical
  (measured at `2.19.0`). Anything that needs to compare two builds must therefore override the
  seed, which is a departure from the tier as shipped — a deliberate one, since it fixes *which*
  random choices are made rather than which transforms run or at what rate.
- **No tier enables `domainLock`.** All four ship `domainLock: []`. The option is additionally
  restricted to browser targets by `@IsAllowedForObfuscationTargets([Browser, BrowserNoEval])`, so
  it is a validation error against `target: 'node'` — it is a browser-only feature that no shipped
  tier reaches for.
- **`high-obfuscation` is not "everything on".** It leaves `renameProperties`, `renameGlobals`,
  `unicodeEscapeSequence`, `domainLock` and `forceTransformStrings` off, keeps the hexadecimal
  identifier generator, and pins each array-valued option to a *single* value (`[rc4]`,
  `[hexadecimal-number]`) where the option would accept all of them. A maximal configuration sits
  strictly above the top tier, and is not something the encoder ever ships.

## Source

- The tiers themselves:
  [`src/options/presets/`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/45ad03b8335bee095b17c0d29b0a78bff158c93a/src/options/presets/Default.ts)
  — `Default.ts`, `LowObfuscation.ts`, `MediumObfuscation.ts`, `HighObfuscation.ts`, plus the
  non-selectable `NoCustomNodes.ts` (read at `5.5.0`; per-tag readings are the same paths at each
  tag).
- The selectable names:
  [`src/enums/options/presets/OptionsPreset.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/45ad03b8335bee095b17c0d29b0a78bff158c93a/src/enums/options/presets/OptionsPreset.ts).
- Where a tier is chosen and merged, and the `optionPresetsMap` that binds name to contents:
  [`src/options/Options.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/45ad03b8335bee095b17c0d29b0a78bff158c93a/src/options/Options.ts).
- The target restriction on `domainLock`:
  [`src/options/validators/IsAllowedForObfuscationTargets.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/45ad03b8335bee095b17c0d29b0a78bff158c93a/src/options/validators/IsAllowedForObfuscationTargets.ts).

**How to re-read this page at any tag.** `git show "<tag>:src/options/presets/<Tier>.ts"` for each
of the four, resolving the spread chain upward to `Default`; the nesting means a tier is only
meaningful together with the ones it spreads. To check drift, hash each file's non-import body per
tag and collapse adjacent identical results — and assert the extraction is non-empty per tag, since
an empty read collapses into a confident-looking "unchanged" span. The shell traps that produce
exactly that empty read are listed in [options.md](options.md)'s recipe.

## Fixtures

The `preset-default`, `preset-low`, `preset-medium`, and `preset-high` cells in
[corpus.md](corpus.md) exercise the selectable tiers with a non-zero seed. They pin emitted tier
composition, not the shipped `seed: 0` reproducibility quirk or target-validation behavior; those
claims remain source- and direct-option evidence.
