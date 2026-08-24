# String Array

Every string literal the program uses is moved into one array, and each use site becomes a call
that indexes it. `'hello, '` becomes `_0x393d(0xf4)`.

**Gated on `stringArray`**, and applied per literal at `stringArrayThreshold`. It is the dominant
transform of this encoder: three of the four shipped presets enable it
([presets.md](../presets.md)), and most other string-facing transforms feed it.

This page covers **the array itself** — how it is held, what order it is in, and how an element is
encoded. Its three companions are separate components with separate histories, and each has its own
page: the standalone rotator ([string-array-rotate.md](string-array-rotate.md)), the global accessor
that use sites call ([string-array-calls-wrapper.md](string-array-calls-wrapper.md)), and the
per-scope accessors that forward to it
([string-array-scope-calls-wrapper.md](string-array-scope-calls-wrapper.md)).
**Splitting them is a measured decision, not a filing convenience** — see "Why four pages" below.
The array's threshold membership and its lone-surrogate eligibility are separate axes in
[versions.md](../versions.md): `E-sa-membership-*` and `E-sa-surrogate-*`.

## 1. Target

Deny a reader the correspondence between a program point and the string it uses. Reading the
program shows an opaque index; reading the array shows strings with no indication of where each is
used. Recovering either half alone is worthless, and the array's order is deliberately not the
order of first use.

## 2. Algorithm

Four independent decisions define the emitted lookup: membership, order, encoding, and access.

**Which literals go in.** Three gates, all in `StringArrayStorageAnalyzer`, and a literal has to
clear all of them:

| Gate | Excludes |
|---|---|
| `isProhibitedLiteralNode` | a non-computed property *key*, and any literal directly under an `ImportDeclaration`, `ExportAllDeclaration` or `ExportNamedDeclaration` |
| **minimum length** | anything shorter than **three characters**. A fixed constant, not an option — read as `3` at every release tag in the documented range and at the pin |
| `stringArrayThreshold` | the node, at random, at or below the configured probability; see the zero-threshold eras below |

Collection order is order of first *encounter* during the analysis traversal, and each distinct
encoded value is stored once, so two uses of the same string share one index.

**Zero is its own membership boundary.** At `E-sa-membership-zero-draw`, the analyzer compares a
discrete random value with `<=`, so a draw of exactly zero still admits an eligible literal when
`stringArrayThreshold` is `0`. `E-sa-membership-zero-disabled` adds a truthiness guard before that
comparison, making zero unconditionally disable program-literal storage. A deterministic
real-output discriminator is `seed: 19196` over `var value = 'long-target-value'`: the low side
initializes `value` through the calls wrapper, while the high side leaves the literal directly in
its declarator. This is membership, not a holder-shape change.

**The length gate is what couples this transform to `splitStrings`, and the coupling is one-way.**
`splitStrings` runs at `Converting` (6) and this stage at `StringArray` (8), so the literals
reaching the gate are already **chunks**, and it is the chunk length that is measured against the
three-character minimum — never the length of the string as written. A
`splitStringsChunkLength` below `3` therefore withholds *every* split literal from the array, and
the interaction is total rather than partial: not fewer entries, but none from that source. What
remains eligible is whatever no chunk covers, which at some versions is only the custom code
helpers' own strings. The ordering is in [order.md](../order.md); the gate makes it observable in
the emitted output.

**How each element is encoded.** Per item, an encoding is picked at random from the
`stringArrayEncoding` array:

| encoding | element content | what the use site carries |
|---|---|---|
| `none` | the string itself | index only |
| `base64` | `btoa(value)` against a **swapped** alphabet | index only |
| `rc4` | `btoa(rc4(value, key))`, same swapped alphabet | index **and** the key as a second argument |

**Lone-surrogate eligibility is encoding-specific.** Before `E-sa-surrogate-inline`, a lone high
or low UTF-16 surrogate reaching base64 or RC4 preparation can make the encoder throw
`URIError: URI malformed`. From `E-sa-surrogate-inline`, the analyzer leaves that literal in the
source rather than placing it in an encoded helper-array member; valid surrogate pairs remain
eligible. This guard is separate from the threshold comparison and does not claim that every
string-array encoding mode treats the literal identically.

The rc4 keys are not per item: 50 four-character keys are generated once per run and each item
picks one. So a sample carries at most 50 distinct keys however many strings it has.

**What order the array is in.** Two shuffles, both optional and both applied at encode time to the
storage rather than to the emitted text:

- `shuffleStringArray` permutes the items and renumbers them, so index order still matches array
  order.
- `rotateStringArray` rotates the storage by a random amount in `[100, 500]` **without**
  renumbering. This is the one that matters: the array is emitted rotated, and the emitted program
  rotates it *back* at load time. The indexes at the use sites are indexes into the **unrotated**
  array.

**What number appears at the use site.** Not the item's index. The emitted number is

```
indexShiftAmount + callsWrapperData.index + itemIndex
```

and the accessor subtracts the same total back off. `indexShiftAmount` is a random value in
`[100, 500]` when `stringArrayIndexShift` is on (**its default is on**, which is why a
no-options-set sample still shows `index = index - 0xeb`), and `0` otherwise. The middle term is
the per-scope wrapper's own offset and is `0` for the root wrapper.

**The consequence for anything reading this statically:** the array as printed is rotated, and the
rotation amount is recoverable only by running the rotator's own comparison loop. There is no
constant in the file that states it.

### Why four pages

The array, the rotator, the root calls wrapper and the per-scope calls wrappers are one *subsystem*
and four *components*, and — measured across every release tag — **their shapes change at different
releases.** The rotator's shape changes at `2.10.0` while the others hold; the root wrapper's
changes at `2.12.0` and again at `2.15.4` while the others hold; the per-scope wrappers' changes at
`2.16.0`, which moves nothing else; and `2.19.0` moves the array, the rotator and the root wrapper
together but leaves the per-scope wrappers alone. **No release moves all four.** One shared page
would have to name an era on evidence covering a quarter of its subject, which is the dilution
[doc-conventions.md](../../doc-conventions.md) rules out. Each therefore carries its own
`E-sa-<component>-*` axis in [versions.md](../versions.md).

## 3. Implementation

| Item | At the spine's era | Era |
|---|---|---|
| Stage | `StringArray` (8) | see [order.md](../order.md) |
| Visitor | `enter` on every `Literal`; `prepareNode` on `Program` | all read eras |
| Analysis entry | `stringArrayStorageAnalyzer.analyze(programNode)` from `prepareNode` | all read eras |
| Applicability | `isStringLiteralNode` and not `isProhibitedLiteralNode` and not already a string-array call literal | all read eras |
| Zero threshold | the inclusive random comparison can admit an exact zero draw | `E-sa-membership-zero-draw` |
| Zero threshold | an explicit truthiness guard rejects the literal before the random comparison | `E-sa-membership-zero-disabled` |
| Emitted holder | `const {stringArrayName} = [{stringArrayStorageItems}];` — one declaration | `E-sa-array-declaration` |
| Emitted holder | a self-replacing accessor function that returns the array (below) | `E-sa-array-self-replacing-fn` |
| Rotation amount | `getRandomInteger(100, 500)`, `0` when `rotateStringArray` is off | all read eras |
| Index shift amount | `getRandomInteger(100, 500)`, `0` when `stringArrayIndexShift` is off | all read eras |
| Use-site index | `indexShiftAmount + itemIndex` | up to `2.15.5` |
| Use-site index | `indexShiftAmount + callsWrapperData.index + itemIndex` | `2.16.0` and up |
| rc4 key pool | 50 keys, 4 chars, generated once per run | all read eras |
| Storage key | `` `${encodedValue}-${encoding}` `` — so the same text under two encodings is two items | all read eras |
| Lone surrogate with base64/RC4 | encoding preparation can throw `URIError: URI malformed` | `E-sa-surrogate-urierror` |
| Lone surrogate with base64/RC4 | literal remains inline and is excluded from encoded helper-array members | `E-sa-surrogate-inline` |

**The emitted declaration kind is not the template's.** The template says `const`; the corpus
prints `var` at every version read. A matcher keying on `const` matches nothing.

**The self-replacing holder**, at `E-sa-array-self-replacing-fn`:

```js
function _0x789d() {
  var _0x494639 = ['hello,\x20', /* … */];
  _0x789d = function () { return _0x494639; };
  return _0x789d();
}
```

The first call builds the array and rewrites the binding to a closure returning it; every later
call is that closure. The three statements are frequently **fused** by adjacent-statement merging
([statement-and-declaration-merging.md](statement-and-declaration-merging.md)), so a matcher
counting statements in the body is matching a spelling rather than the shape.

**The 2.16.0 index change is the scope wrapper's, not this component's.** It adds a term
contributed by whichever scope calls wrapper the use site was routed through, and it is inert for
the root wrapper. It is recorded here because it changes the emitted index arithmetic.

## 4. Downstream Effects

The `StringArray` stage is late — 8 of 10 — so little follows it, but what does is load-bearing.

| Later | Effect on this transform's output |
|---|---|
| `Finalizing` — `EscapeSequenceTransformer` | every element is a string literal, so every element is escaped. The array's printed content is escaped text, not the values ([escape-sequences.md](escape-sequences.md)) |
| `Finalizing` — adjacent-statement merging | fuses the holder's three statements, and the wrapper's, into sequence expressions ([statement-and-declaration-merging.md](statement-and-declaration-merging.md)) |
| `RenameIdentifiers` (7) — runs *before* | the array binding, the holder function and the accessor all carry generated names. **No name in this subsystem is stable**, so nothing may be identified by name text |

**Within the same stage**, `StringArrayRotateFunctionTransformer` runs first — `StringArrayTransformer`
declares `runAfter` on it — and it builds its own fragment through a private four-stage pipeline,
then marks its literals ignored so this transform does not collect them. The exception is
deliberate: the fragment's *numeric-looking* literals are force-added to this storage, which is why
the rotator's comparison expression reads its own operands back out of the string array.

## 5. Known Quirks

- **`stringArrayEncoding: []` throws rather than defaulting.** `getEncodedValue` raises
  ``'`stringArrayEncoding` option array is empty'`` if the array is empty, so the option's
  normalizer is what guarantees a `['none']` default ever reaches here.
- **rc4 keeps a cache keyed by encoded value**, whose only purpose is to detect two distinct
  sources colliding on one encoded form. It is bookkeeping, not shape.
- **A maximal profile can turn this transform off by accident, and the interacting option is
  `splitStringsChunkLength`.** The length gate in item 2 can starve the program's strings. The
  corpus carries the isolation as a
  pair of cells rather than as a probe: `all-on-split10` differs from `all-on` in the chunk length
  and nothing else, and at `2.9.6` — where the parent profile emits no array, no rotator and no use
  site at all — the sibling emits the whole subsystem. The version-dependence is a *consequence*,
  not a second cause: what changes across versions is only how much of the eligible text comes
  from custom code helpers rather than from the program, so at later versions the helpers alone
  keep an array alive while the program contributes nothing to it. Two things follow, and the
  second is the one that misleads:
  - **The interaction is not `2.9.6`'s**, so nothing here is era-scoped. Every version in the
    documented range behaves this way; only the residual helper text differs.
  - **"An array is present" is not evidence the program's strings are in it.** A profile can emit
    a complete, rotated, wrapper-fronted subsystem serving nothing but the helpers it shipped
    with. Any claim about this transform read off such a cell is a claim about the helpers.

## Source

- Transformer:
  [`StringArrayTransformer.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/node-transformers/string-array-transformers/StringArrayTransformer.ts)
- Membership — the three gates and the minimum length:
  [`StringArrayStorageAnalyzer.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/analyzers/string-array-storage-analyzer/StringArrayStorageAnalyzer.ts)
- Zero-threshold membership guard at `E-sa-membership-zero-disabled`:
  [`StringArrayStorageAnalyzer.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/77f64bf5df0e943ac2f9c035577e0e44a9f5f3e4/src/analyzers/string-array-storage-analyzer/StringArrayStorageAnalyzer.ts)
- Lone-surrogate guard at `E-sa-surrogate-inline`:
  [`StringArrayStorageAnalyzer.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/35860ec7087b1e53e89233419f91336f6d4f0bd5/src/analyzers/string-array-storage-analyzer/StringArrayStorageAnalyzer.ts)
- Storage — order, index shift, encoding, rc4 keys:
  [`StringArrayStorage.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/storages/string-array-transformers/StringArrayStorage.ts)
- Holder template, `E-sa-array-self-replacing-fn`:
  [`StringArrayTemplate.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/custom-code-helpers/string-array/templates/string-array/StringArrayTemplate.ts)
- Holder template, `E-sa-array-declaration`:
  [`StringArrayTemplate.ts` at 2.18.1](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/18f5210871a6574f256938d4ad56e2ac19ac8884/src/custom-code-helpers/string-array/templates/string-array/StringArrayTemplate.ts)
- Use-site call construction, and the `2.16.0` index term:
  [`StringArrayCallNode.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/custom-nodes/string-array-nodes/StringArrayCallNode.ts)
- Option names, types and defaults, including `stringArrayIndexShift`: [options.md](../options.md).

Read at `2.19.0`, the spine; the `E-sa-array-declaration` row additionally at `2.18.1`, and the
zero-threshold membership boundary at `3.2.0` and `3.2.2`.

## Fixtures

**None committed.** What checks the claims today:

| Claim | What checks it | Era | Gap |
|---|---|---|---|
| the holder is a plain declaration | corpus `strings__baseline` at 2.9.6, 2.10.0, 2.11.1, 2.12.0, 2.15.3, 2.15.4, 2.18.1 | `E-sa-array-declaration` | — |
| the holder is a self-replacing function | corpus `strings__baseline` at 2.19.0 | `E-sa-array-self-replacing-fn` | upper bound is source-read only |
| the emitted kind is `var`, not `const` | every corpus cell carrying an array | both | — |
| index shift is on by default | `index = index - 0xeb` in `strings__baseline` at 2.19.0 | both | the *off* case is in no option set |
| rc4 carries a key at the use site | corpus `strings__encoding-rc4` | both | key-pool size of 50 is source-read only |
| the array is emitted rotated | not directly observed — inferred from the rotator's presence | both | **no fixture**; the corpus does not assert final array order |
| a literal shorter than three characters never enters the array | source-read at every tag in the range; observable in the corpus only through the `splitStrings` coupling below | both | the gate is never exercised *directly* — no option set varies literal length |
| `splitStringsChunkLength < 3` withholds every split literal | the corpus pair `all-on` / `all-on-split10`, which differ in that option alone, at every version in the matrix | both | the two cells bracket the gate; no cell sits *at* it (a chunk length of exactly 3) |
| threshold `0` admits only an exact zero draw before `3.2.2`, and none after | direct `3.2.0` / `3.2.2` encode of `var value = 'long-target-value'` at seed `19196`, with the threshold at zero | `E-sa-membership-zero-draw`, `E-sa-membership-zero-disabled` | — |
| base64/RC4 lone-surrogate handling changes from encoder failure to inline preservation | focused `5.4.6`/`5.4.7` cases with valid-pair controls | `E-sa-surrogate-urierror`, `E-sa-surrogate-inline` | the ordinary corpus columns do not populate this axis |

Upstream's own cases:
`test/functional-tests/node-transformers/string-array-transformers/string-array-transformer/`.
