# Option Surface

Which option names the obfuscator knows, what type each takes, what values it accepts, and where
those change. Cross-cutting — an option gates transformers across several stages, so this is not
scoped to any one transform.

**This page keys everything on tags, never on era IDs, for the same reason
[order.md](order.md) does.** It is a page that *takes readings*; the era registry is a consumer
that collapses readings into eras. Keying these tables on era IDs would make the two mutually
defining and neither readable first. No option-surface axis is open in
[versions.md](versions.md), and what these boundaries *are* good for — evidence about the
transforms behind them, within stated limits — is "What an option boundary is evidence of" below.

The readings are **exhaustive, not sampled**: the surface was derived at all 58 release tags from
`2.9.6` to `5.5.0`, so every boundary below is an exact release and nothing here is interpolated.

## Two independent readings, because they answer different questions

| reading | source | answers |
|---|---|---|
| **declaration** | `git show "<tag>:src/options/Options.ts"` | which names exist, their TypeScript type, and their `class-validator` contract |
| **probe** | the shipped npm build, via the wrong-type enumerator below | whether the *published tarball* knows the name |

They are not redundant. The declaration is read from the git tag; the probe is read from the
artifact npm actually serves. Provenance makes those the same commit, but not the same object, so
a disagreement between them would be a real finding about the build.

**The enumerator.** A *known* option name given a wrong-type value throws a validation error; an
*unknown* name is silently accepted and ignored. So "does this build know this name" is
mechanical: pass the name a value invalid for its declared type and see whether it throws.

**Its blind spot, which has to be stated or the probe lies by omission.** A name whose declaration
carries *no* validator, or one gated behind `@ValidateIf`, accepts the wrong-type value while
being perfectly well known. So a probe verdict of "accepted" means *unknown **or** unvalidated*,
never "unknown". Four names are unenumerable this way at the phase-1 versions — `seed`,
`splitStringsChunkLength`, `sourceMapBaseUrl`, `identifiersDictionary` — and for those the
declaration is the only reading.

**A sentinel is per-option, not global.** Probing `identifierNamesCache` with `{}` reported it
unknown at four versions where the declaration says otherwise. The declaration was right: `{}` is
a *valid* identifier-names cache, so the sentinel was testing nothing. Re-probed with a value that
is actually invalid for it, the two readings agree everywhere. A probe disagreeing with source is
a reason to suspect the probe first.

## The phase-1 range — every release tag from `2.9.6` to `2.19.1`

`2.9.6` declares **45** options. Five names arrive inside the range and one of those leaves again;
no name present at `2.9.6` is ever removed inside it.

| Boundary | Change |
|---|---|
| `2.10.7` → `2.11.0` | `+ renamePropertiesMode` |
| `2.13.0` → `2.14.0` | `+ identifierNamesCache` |
| `2.14.0` → `2.15.0` | `+ domainDest` |
| `2.15.0` → `2.15.1` | `- domainDest`, `+ domainLockRedirectUrl` |
| `2.16.0` → `2.17.0` | `+ sourceMapSourcesMode`; `inputFileName` validator `@IsString()` → `@IsInputFileName()` |

**`domainDest` exists at exactly one release.** It appears at `2.15.0` and is replaced by
`domainLockRedirectUrl` at `2.15.1` — a one-release lifetime, and the reason this page was derived
per tag rather than sampled: the option is invisible at every version the phase-1 matrix builds,
so a sampled reading would have recorded that it never existed.

Apart from `inputFileName` at `2.17.0`, **no option that persists across the phase-1 range changes
its type or its validator anywhere inside it.**

## What the matrix sets, and the two value forms that throw

Every option the phase-1 corpus sets holds one name, one type and one accepted-value set across
**all 26 release tags** from `2.9.6` to `2.19.1`. This is the property the corpus rests on: the
same option object means the same thing at every phase-1 version, so a difference between two
versions' output is the encoder changing, not the request changing.

| Option | Type | Accepted values |
|---|---|---|
| `compact` | `boolean` | |
| `seed` | `string \| number` | no validator — anything is accepted |
| `stringArray` | `boolean` | |
| `stringArrayThreshold` | `number` | `0`–`1` |
| `rotateStringArray` | `boolean` | |
| `shuffleStringArray` | `boolean` | |
| `stringArrayEncoding` | `string[]` | `'none'`, `'base64'`, `'rc4'`, unique |
| `stringArrayIndexesType` | `string[]` | `'hexadecimal-number'`, `'hexadecimal-numeric-string'`, non-empty, unique |
| `stringArrayIndexShift` | `boolean` | |
| `stringArrayWrappersCount` | `number` | `≥ 0` |
| `stringArrayWrappersType` | `string` | `'variable'`, `'function'` |
| `stringArrayWrappersChainedCalls` | `boolean` | |
| `stringArrayWrappersParametersMaxCount` | `number` | `≥ 2` |
| `deadCodeInjection` | `boolean` | |
| `deadCodeInjectionThreshold` | `number` | unbounded |
| `controlFlowFlattening` | `boolean` | |
| `controlFlowFlatteningThreshold` | `number` | `0`–`1` |
| `selfDefending` | `boolean` | |
| `debugProtection` | `boolean` | |
| `debugProtectionInterval` | `boolean` | |
| `disableConsoleOutput` | `boolean` | |

Two forms a corpus recipe gets wrong by writing what the option's *name* suggests, both measured
as throwing at `2.9.6`, `2.12.0` and `2.19.0`:

- **`stringArrayEncoding` is an array at every phase-1 version.** `['base64']` is accepted;
  `'base64'` throws. It is not a scalar that later became a list — it is `TStringArrayEncoding[]`
  as far back as `2.9.6`.
- **`debugProtectionInterval` is a boolean at every phase-1 version.** `true` is accepted; a
  millisecond number throws. The millisecond form belongs to `4.0.0` onward, below.

`stringArrayWrappersParametersMaxCount`'s floor is `2`, not `0` — a set written with `0` or `1` to
mean "no parameters" throws rather than degrading.

## Above the phase-1 range, up to the pin

Four boundaries between `2.19.1` and `5.5.0`, each read at source and each matching what
`CHANGELOG.md` claims for it. The pin declares **51** options.

| Boundary | Change |
|---|---|
| `2.19.1` → `3.0.0` | three renames: `rotateStringArray` → `stringArrayRotate`, `shuffleStringArray` → `stringArrayShuffle`, `ignoreRequireImports` → `ignoreImports` |
| `3.1.0` → `3.2.0` | `+ stringArrayCallsTransform`, `+ stringArrayCallsTransformThreshold` |
| `3.2.7` → `4.0.0` | `debugProtectionInterval` `boolean` → `number` (`@Min(0)`), milliseconds |
| `4.0.1` → `4.1.0` | `target` gains `ServiceWorker` |

**A rename is not a deprecation here.** The old spellings are *gone* at `3.0.0`, not accepted
alongside the new ones — and because an unknown name is silently ignored, passing
`rotateStringArray` to a `3.x` build does not error, it encodes with rotation at its default. That
is the precise mechanism behind the corpus's option-efficacy check: acceptance by the encoder
proves nothing about whether the option was understood.

**`stringArrayCallsTransform` arrives at the same release that `StringArrayControlFlowTransformer`
joins the graph** — `3.2.0`, the lower bound of `P-sorted-sa-controlflow` in
[versions.md](versions.md). The two axes are read independently and a shared boundary is normally
a finding to record rather than assume; this one is not a coincidence but a consequence, since
that option is the transformer's own `getVisitor` gate ([order.md](order.md), "`runAfter` is
resolved against the stage"). It is written here as prose, never as a merged registry row.

## What an option boundary is evidence of

**The surface is not the algorithm.** An option's name, type and accepted values describe the
*request* a caller makes; nothing about them says what the transform emits. So an option boundary
is never an `E-<component>-*` boundary, and no doc may cite one as though it were shape.

**But it is not noise either.** An option is usually added, retyped, or given a new mode *because*
the transform behind it changed, so these boundaries are a **candidate list** — the first places to
look when a component's own axis opens. What they are worth is measurable rather than a matter of
taste, and measuring it gives a sharper rule than "to some degree":

| Boundary | Emitted-shape event at the same release | Axis fires? |
|---|---|---|
| `3.1.0` → `3.2.0` | `StringArrayControlFlowTransformer` joins the graph | **yes** — `stringArrayCallsTransform` arrives with it |
| `3.2.7` → `4.0.0` | the debug-protection helper's timing changes | **yes** — `debugProtectionInterval` retyped to milliseconds |
| `2.18.1` → `2.19.0` | the string array's `V2 → V3` rewrite, the largest emitted-shape change in the encoder | **no** — nothing on this axis moves |
| `2.15.3` → `2.15.4` | the calls-wrapper helpers and templates rewritten | **no** — nothing on this axis moves |
| `2.19.1` → `3.0.0` | none — three pure renames | fires, and means nothing |

**So the axis tracks capability *arrival*, not algorithm change.** A new or retyped option marks a
capability appearing or changing kind; a transform rewritten behind an *unchanged* capability is
invisible here. Both failure directions are real and the second is the dangerous one:

- **False positive** — a rename reflects no transform change at all (`3.0.0`).
- **False negative** — the two largest string-array shape changes in this encoder's history each
  land on a release where this axis says nothing. **"No option change" is never evidence that a
  shape held still.**

**The order axis is silent at exactly the same place**, and for its own reason: `runAfter` records
ordering requirements rather than data flow, so a wholesale rewrite needs no edge change
([order.md](order.md)). Both infrastructure axes go quiet at `2.19.0`. That is the concrete reason
a collapse between two eras has to be read off decoded output and can never be read off source
signatures — neither axis is watching the thing a collapse is about.

**No axis is opened in [versions.md](versions.md), and now for a stated reason rather than a
deferred one.** A registry axis exists so docs can cite an era instead of inlining a range; citing
an option era *as shape evidence* is precisely the misuse the paragraphs above rule out. The
readings stay here, exact and complete, as leads for the `E-<component>-*` axes to test — starting
with `E-sa-*`, where the prediction this page makes is a boundary at `3.2.0` and, more usefully,
no boundary anywhere near the two releases that matter most.

## Known Quirks

- **An unknown option name is accepted silently and ignored.** Measured at all eight phase-1
  versions with a control name that exists nowhere: no error, no warning, and output byte-identical
  to leaving it out. A misspelled or version-inappropriate option therefore yields a sample that
  quietly encodes with the default, and nothing about the encode reports it.
- **`IsInputFileName` is not type-safe.** From `2.17.0`, passing `inputFileName` a non-string
  crashes the validator with `t.replace is not a function` rather than producing a validation
  error. It still proves the name is known, but it is a crash, not a rejection — and at `2.15.4`
  and below the same value is cleanly rejected by `@IsString()`.
- **Four names cannot be enumerated by probing** (`seed`, `splitStringsChunkLength`,
  `sourceMapBaseUrl`, `identifiersDictionary`) because they carry no validator or a `@ValidateIf`
  gate. Their existence rests on the declaration alone.

## Source

- [`src/options/Options.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/45ad03b8335bee095b17c0d29b0a78bff158c93a/src/options/Options.ts)
  — the declaration of every option, its type and its validators (read at `5.5.0`; the per-tag
  readings are the same path at each tag).
- Accepted values for the enum-typed string-array options:
  [`StringArrayEncoding.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/45ad03b8335bee095b17c0d29b0a78bff158c93a/src/enums/node-transformers/string-array-transformers/StringArrayEncoding.ts),
  [`StringArrayWrappersType.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/45ad03b8335bee095b17c0d29b0a78bff158c93a/src/enums/node-transformers/string-array-transformers/StringArrayWrappersType.ts),
  [`StringArrayIndexesType.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/45ad03b8335bee095b17c0d29b0a78bff158c93a/src/enums/node-transformers/string-array-transformers/StringArrayIndexesType.ts).
  All three hold their accepted values unchanged across every release tag from `2.9.6` to `5.5.0`.
- Custom validators:
  [`src/options/validators/`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/45ad03b8335bee095b17c0d29b0a78bff158c93a/src/options/validators/IsIdentifierNamesCache.ts).
- Defaults are not stated here. A default is a preset entry — `DEFAULT_PRESET` is one of the four
  tiers `Options` maps — so it belongs with the preset study, not with the surface.

**How this page was produced, so it can be reproduced rather than trusted.** For each release tag:
export `src/options/Options.ts` at that tag, take each `public readonly <name>!: <type>;` on the
`Options` class together with the decorators immediately above it, and collapse adjacent tags with
identical results. Then probe the installed builds with the enumerator and reconcile the two
readings name by name; a mismatch is a defect in one of them and must be resolved before any row
is believed.

Five traps, each of which produced a wrong answer here before being handled:

| trap | what goes wrong |
|---|---|
| a multi-line decorator | `@IsIn([\n A,\n B\n])` spans four lines, and a parser that accumulates only single-line decorators drops it silently — reporting "no validator drift" from an empty reading. Balance the brackets before closing a decorator |
| formatting read as change | a trailing comma or a reflowed argument list changes the decorator text without changing the contract. Compare whitespace-blind, or `4.2.0` → `4.2.1` reads as three option changes and is none |
| one global wrong-type sentinel | `{}` is *valid* for `identifierNamesCache`, so the enumerator reported it unknown where it exists. The sentinel has to be invalid for the option's own declared type |
| a probe verdict read as two-valued | "accepted" is *unknown or unvalidated*. Without the declaration beside it, four known names read as absent |
| `git show $tag:src/...` in a `zsh` loop | `:s` parses as a parameter modifier, git is handed `<tag>.ts`, and the redirect writes an empty file. Brace it, run under `bash`, or bypass the shell. The same session also lost a run to `for t in $TAGS` — zsh does not word-split unquoted parameters, so every iteration hashed the empty string. Assert non-empty per tag; it catches both |

## Fixtures

Option declarations and validator behavior are source or installed-build evidence. The preset
cells in [corpus.md](corpus.md) cover the option forms they contain, but they are not dedicated
fixtures for every option or wrong-type value. Wrong-form rejection remains a direct validator
probe rather than an emitted-output claim.
