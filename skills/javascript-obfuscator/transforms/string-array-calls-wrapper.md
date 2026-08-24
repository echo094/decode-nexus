# String Array Calls Wrapper

The single global accessor every string-array use site calls. It takes the shifted index (and, for
rc4, a key), subtracts the shift, indexes the array, decodes the element if the item was encoded,
and returns the string.

**Not gated by an option of its own.** It exists whenever the string array does, and there is one
per encoding in use — a sample mixing `base64` and `rc4` carries two, each with its own decode
body. It is emitted as a custom code helper.

This is the **root** wrapper. The per-scope wrappers that `stringArrayWrappersCount` adds are a
different component with a different history, and have their own page:
[string-array-scope-calls-wrapper.md](string-array-scope-calls-wrapper.md). Its other companions are
[string-array.md](string-array.md) and [string-array-rotate.md](string-array-rotate.md).

## 1. Target

Put one chokepoint between every use site and the array, so that neither the index arithmetic nor
the per-item decoding is visible where the string is used. It also gives the encoder a place to
hang the base64/rc4 machinery and the anti-tamper check without repeating either.

## 2. Algorithm

The body is stable across every era read: **subtract the index shift, index the array, run the
decode template for this encoding, return the value.** What changes is how the wrapper is *held*
and where it reads the array from — four shapes in phase 1's range and a fifth above it.

| Era | Shape |
|---|---|
| `E-sa-wrapper-var-fn-expression` | a declaration initialised with a function expression |
| `E-sa-wrapper-fn-declaration` | the same body as a hoisted function declaration |
| `E-sa-wrapper-self-replacing` | a function declaration whose first call **rewrites its own binding** to the real accessor and then delegates to it |
| `E-sa-wrapper-array-fn-call` | as above, and the array comes from calling the accessor function rather than from a binding |
| `E-sa-wrapper-flat` | the self-replacement is **removed** again; a plain declaration with the shift inline |

The historical stable-2.x samples close the old pre-2.9 root-wrapper uncertainty. The root is a
`var`-held function expression at both `2.0.0` and `2.8.1`, and the exact tag templates retain that
holder shape through the 2.9 source change. Here `2.0.0` is the approved stable-2.x read floor,
not a shape boundary. That change replaces the template's fixed-zero shift placeholder with
`indexShiftAmount`; it does not introduce a different root-wrapper holder. The per-scope wrappers
are independent and are documented on
[string-array-scope-calls-wrapper.md](string-array-scope-calls-wrapper.md).

The self-replacing form is the one to understand, because three of the five eras use it and it is
what a naive matcher trips on:

```js
function _0x393d(_0x55401c, _0x590b71) {
  var _0x789d77 = _0x789d();              // E-sa-wrapper-array-fn-call only
  return _0x393d = function (index, key) {
    index = index - 0xeb;
    var value = _0x789d77[index];
    return value;
  }, _0x393d(_0x55401c, _0x590b71);
}
```

The outer function runs **once**. It installs the inner closure over the wrapper's own name and
immediately re-calls it, so every subsequent call goes straight to the inner function. Two things
follow for anything reading it:

- **The index arithmetic lives in the inner function, not the outer one.** The outer function's
  parameters are named for a cache slot, not an index, and are simply forwarded.
- **The `return … , …` is a merge artifact.** The template writes an assignment statement and a
  return statement; adjacent-statement merging fuses them into one sequence expression
  ([statement-and-declaration-merging.md](statement-and-declaration-merging.md)). Matching a
  statement count matches a spelling.

**Where the array comes from is the `2.19.0` change**, and it is forced rather than cosmetic: the
holder became a function ([string-array.md](string-array.md)), so there is no array binding to
close over and the wrapper has to call the accessor. It hoists that call into the outer function,
so it happens once.

**The decode template is per encoding**, substituted into `{decodeCodeHelperTemplate}`:

| encoding | body |
|---|---|
| `none` | empty — `value` is returned as read |
| `base64` | installs an inline `atob` over a **swapped** alphabet on first call, memoises it as a property of the wrapper function, and caches decoded values on the outer function's first parameter (which it reassigns to `arguments`) |
| `rc4` | the same, plus an rc4 pass keyed by the wrapper's second argument, and a once-only `selfDefending` guard |

The cache is what the outer parameter is *for* under `base64`/`rc4`, which is why the template
names it `stringArrayCacheName` rather than an index. Under `none` the parameter is vestigial.

## 3. Implementation

| Item | At the spine's era | Era |
|---|---|---|
| Emitted by | `StringArrayCallsWrapperCodeHelper`, plus `…Base64CodeHelper` / `…Rc4CodeHelper` subclasses | all read eras |
| Template obfuscation | the template is run through `JavaScriptObfuscator.obfuscate` **recursively** before being appended — `CustomCodeHelperObfuscator.obfuscateTemplate`, under `NO_ADDITIONAL_NODES_PRESET` plus forwarded `identifierNamesGenerator`, `identifiersDictionary`, `numbersToExpressions`, `simplify` and a fresh seed | read identical at `2.19.0` and `5.5.0` |
| One per | encoding actually used in the sample | all read eras |
| Name | `identifierNamesGenerator.generateForGlobalScope(4)`, cached per encoding on the storage | all read eras |
| Index arithmetic | `index = index - {indexShiftAmount}` | all read eras |
| Array read | `{stringArrayName}[index]` — a binding | up to `E-sa-wrapper-self-replacing` |
| Array read | `{stringArrayFunctionName}()` hoisted into the outer function, then indexed | `E-sa-wrapper-array-fn-call` |
| Holder | `const NAME = function (index, key) { … };` | `E-sa-wrapper-var-fn-expression` |
| Holder | `function NAME (index, key) { … }` | `E-sa-wrapper-fn-declaration` |
| Holder | `function NAME (cache, key) { NAME = function (index, key) { … }; return NAME(cache, key); }` | `E-sa-wrapper-self-replacing` and up |
| base64 alphabet | `Base64AlphabetSwapped` — **not** the standard alphabet | all read eras |
| rc4 key | the wrapper's second argument, supplied per use site | all read eras |

**The emitted declaration kind is not the template's**, exactly as for the holder: the template
says `const`, the corpus prints `var`.

**`E-sa-wrapper-flat` is above phase 1's range** and is recorded from source only. It is worth
having on the axis now because it is a *reversion* — the self-replacement that arrived at `2.15.4`
is removed again at `4.2.0`. The self-replacing signature is therefore non-monotonic across eras.

## 4. Downstream Effects

| Later | Effect on this transform's output |
|---|---|
| `Finalizing` — adjacent-statement merging | fuses the self-replacement and its delegating return into one sequence expression, and the outer function's declarations into one |
| `Finalizing` — `EscapeSequenceTransformer` | escapes the base64 alphabet string and every member-key literal in the decode bodies |
| `RenameIdentifiers` (7) — before this | the wrapper's name, its parameters and its memoisation property names are all generated. The `base64`/`rc4` property names are additionally **random 6-character strings baked into the template**, so they differ per run even at a fixed seed's neighbours |
| `StringArrayRotateFunctionTransformer`, same stage | emits a rotator whose comparison operands are calls to **this** wrapper, so the wrapper must already be reachable when the rotator runs |
| its own emission route (item 3) | the recursive template run re-spells the wrapper before the main pipeline ever sees it, which is how `numbersToExpressions` reaches the index shift despite `Converting` (6) running *before* `StringArray` (8) |

**Those four forwarded options are the complete set of re-spellings the wrapper can carry**, and
that is the useful part: `numbersToExpressions` turns the index shift and any other numeric
constant into an arithmetic tree, `simplify` fuses the body's statements, the name generator
regenerates every identifier. Nothing else reaches inside a helper, because
`NO_ADDITIONAL_NODES_PRESET` switches the rest off — so the set is closed and readable from source
rather than open-ended.

## 5. Known Quirks

- **The outer parameter changes meaning by encoding.** Under `none` it is a plain index forwarded
  once; under `base64`/`rc4` it is reassigned to `arguments` and used as the value cache. Same
  slot, two unrelated jobs, decided by a template substitution.
- **`atob` here ignores padding by design**, and the template says so. It is not a standard `atob`
  and it is over a swapped alphabet, so decoding an element with a stock base64 decoder produces
  the wrong string rather than an error.
- **The `selfDefending` guard rides inside the rc4 decode body**, not in a separate helper — one
  more reason the anti-tamper strip and the string-array decode are not cleanly separable at this
  era.

## Source

- Code helper:
  [`StringArrayCallsWrapperCodeHelper.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/custom-code-helpers/string-array/StringArrayCallsWrapperCodeHelper.ts)
- Recursive template obfuscation and its forwarded option set:
  [`CustomCodeHelperObfuscator.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/custom-code-helpers/CustomCodeHelperObfuscator.ts)
- Append gating — one wrapper per `stringArrayEncoding`, and no dependence on
  `stringArrayWrappersCount`:
  [`StringArrayCodeHelperGroup.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/custom-code-helpers/string-array/group/StringArrayCodeHelperGroup.ts)
- Template, `E-sa-wrapper-array-fn-call`:
  [`StringArrayCallsWrapperTemplate.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/custom-code-helpers/string-array/templates/string-array-calls-wrapper/StringArrayCallsWrapperTemplate.ts)
- Template, `E-sa-wrapper-var-fn-expression`:
  [at 2.11.1](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/99194f145698a378b14114cbb4bec89d3cdc34f2/src/custom-code-helpers/string-array/templates/string-array-calls-wrapper/StringArrayCallsWrapperTemplate.ts)
- The same stable-2.x root template before the index-shift placeholder change:
  [at 2.8.1](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/44ac6c3ec8de32259c10d5c8a395cff110281dca/src/custom-code-helpers/string-array/templates/string-array-calls-wrapper/StringArrayCallsWrapperTemplate.ts)
- Template, `E-sa-wrapper-fn-declaration`:
  [at 2.12.0](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/36ea9c08f3244533b466b3031824da6493aa2d4e/src/custom-code-helpers/string-array/templates/string-array-calls-wrapper/StringArrayCallsWrapperTemplate.ts)
- Template, `E-sa-wrapper-self-replacing`:
  [at 2.15.4](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/08aad1b7069e9f8b510765dcbf01c88aa741378d/src/custom-code-helpers/string-array/templates/string-array-calls-wrapper/StringArrayCallsWrapperTemplate.ts)
- Template, `E-sa-wrapper-flat`:
  [at 4.2.0](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/01465a233c977c45d2f238806a95a06387cc7a39/src/custom-code-helpers/string-array/templates/string-array-calls-wrapper/StringArrayCallsWrapperTemplate.ts)
- base64 decode body and the swapped alphabet:
  [`AtobTemplate.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/custom-code-helpers/string-array/templates/string-array-calls-wrapper/AtobTemplate.ts)
- rc4 decode body:
  [`StringArrayRC4DecodeTemplate.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/custom-code-helpers/string-array/templates/string-array-calls-wrapper/StringArrayRC4DecodeTemplate.ts)

Read at `2.19.0`, the spine; the other four era rows at `2.11.1`, `2.12.0`, `2.15.4` and `4.2.0`.

## Fixtures

**None committed.** What checks the claims today:

| Claim | What checks it | Era | Gap |
|---|---|---|---|
| held by a declaration initialised with a function expression | focused output samples at `2.0.0` and `2.8.1`, plus corpus `strings__baseline` at 2.9.6, 2.10.0, 2.11.1 | `E-sa-wrapper-var-fn-expression` | the two historical sites are output evidence; the intervening stable-2.x range is source-derived, not interpolated |
| held by a function declaration | corpus `strings__baseline` at 2.12.0, 2.15.3 | `E-sa-wrapper-fn-declaration` | — |
| rewrites its own binding on first call | corpus `strings__baseline` at 2.15.4, 2.18.1 | `E-sa-wrapper-self-replacing` | — |
| reads the array by calling the accessor | corpus `strings__baseline` at 2.19.0 | `E-sa-wrapper-array-fn-call` | upper bound is source-read only |
| the self-replacement is removed again | source read at 4.1.1 / 4.2.0 | `E-sa-wrapper-flat` | **no output** — outside the corpus range |
| one wrapper per encoding | not observed | all | **no fixture**; no corpus set mixes two encodings — each `encoding-*` set pins exactly one |
| base64 uses a swapped alphabet | corpus `strings__encoding-base64` at 2.19.0 carries the alphabet inline | all | not checked against a decode |

Upstream's own cases:
`test/functional-tests/custom-code-helpers/string-array/`.
