# delete-extra.js

A two-line visitor that deletes `node.extra` from every `StringLiteral` and `NumericLiteral`,
forcing `@babel/generator` to re-emit the value in canonical form rather than reprinting the
source's raw text: `0x10` → `16`, `'\x20'` → `" "`.

## 1. Target

Reverse the class of encoder transform that rewrites **only a literal's spelling**. Several
obfuscators finish by re-writing `raw` and leaving `value` untouched — hex and octal numbers,
escape-sequenced strings — so the parsed value is already the answer and there is no shape for a
matcher to key on. Babel preserves `extra.raw` and prefers it over the value when printing, which
is why the encoded spelling otherwise survives a decode that changed everything else.

## 2. Algorithm

Delete `extra`. That is the whole reversal, and it is total rather than best-effort: there is no
partial state and nothing to decline on, because the field being discarded is a cache of the input
text and never a semantic carrier.

**It depends on the caller's generator options.** Discarding `extra` is not ASCII-safe on its own
— with Babel's default `jsesc` settings a non-ASCII character in a literal is re-escaped on the way
out, so the pass reads as though it had not run. Both consumers pass
`jsescOption: { minimal: true }`, and a third would have to as well.

**It is a print-time pass, so it is scheduled last.** Nothing downstream navigates by `raw`;
every matcher reads `value`, which the encoder left correct. Running it early is not wrong so much
as pointless, and for `obfuscatorx` it is worse than pointless: `string-array` hands generated
source to an isolate, and re-spelling that source before it gets there buys nothing.

## 3. Implementation

| Item | Detail |
|---|---|
| Visitor keys | `StringLiteral`, `NumericLiteral` — nothing else carries a spelling this reverses |
| Operation | `delete node.extra`, unconditional |
| Reports | nothing. It has no change channel, so a caller running to a fixpoint cannot count it |

## 4. Upstream Effects

| Shape reaching this pass | Producing pass | Ours or the encoder's | Era |
|---|---|---|---|
| numeric `extra.raw` already discarded | [normalize-converting](obfuscator/normalize-converting.md)'s `stripNumericRaw` | ours | all `obfuscatorx` read eras |
| string `extra.raw` holding an escape spelling | the encoder's `Finalizing` stage | the encoder's | all `obfuscatorx` read eras |

**The numeric overlap is deliberate and harmless.** `normalize-converting` strips numeric `extra`
inside the fixpoint group because a folded expression has to print in decimal for the next round to
read it; this pass strips whatever is left. Deleting an already-absent field is a no-op, so the two
do not have to be reconciled — and the scoping comment in `normalize-converting` explains why it
declines to take the *string* half rather than quietly absorbing it.

## 5. Known Gaps

None currently open.

## Source

- [`src/visitor/delete-extra.js`](https://github.com/echo094/decode-js/blob/6cacb633ceedf0812fe31f951ba8f41ffb431ca1/src/visitor/delete-extra.js)
- Wired last, immediately before generation, in
  [`src/plugin/jsconfuser.js`](https://github.com/echo094/decode-js/blob/6cacb633ceedf0812fe31f951ba8f41ffb431ca1/src/plugin/jsconfuser.js) and
  [`src/plugin/obfuscatorx.js`](https://github.com/echo094/decode-js/blob/6cacb633ceedf0812fe31f951ba8f41ffb431ca1/src/plugin/obfuscatorx.js). Item 2 is
  why that position is forced.
- **Other plugins inline the identical visitor rather than importing it** — `obfuscator.js`,
  `sojson.js` and `sojsonv7.js` each carry their own `delete node.extra` pair. That is prior
  duplication, not a decision recorded anywhere; consolidating it would touch three widely-depended-on
  entries at once, which is a wider blast radius than any current change needs.

## Fixtures

The pass has no standalone fixture because it has no declines or intermediate state. Its shared
generation contract is pinned through both current callers instead.

| Claim | What checks it | Gap |
|---|---|---|
| the string half fires, and the escape spelling is what it removes | `test/obfuscatorx/2.9.6-baseline-strings` and `2.19.0-all-on-objects` — both goldens carry `" "` and `"\n"` where the input carries `'\x20'` and `'\x0a'` | — |
| the numeric half fires | `test/jsconfuser/` goldens, where hex literals decode to decimal | not isolated from `normalize-converting`'s own numeric strip |
| ASCII/non-ASCII output under `jsescOption: { minimal: true }` | `test/generator-minimal/escaped-literals`, run through both `PluginObfuscatorX` and `PluginJsconfuser`; the exact golden contains literal `A` and `é` where the input uses escapes | — |
