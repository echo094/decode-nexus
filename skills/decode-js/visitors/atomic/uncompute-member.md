# uncompute-member.js

Drops the brackets from a member read whose key is a plain string: `o["foo"]` becomes `o.foo`.
Obfuscators rewrite every static property name into a computed string so that a string-concealing
pass can reach it; once the string is back, the brackets carry no information.

**Restoring the dotted form is a precondition, not a finish.** Every later matcher that navigates by
`o.foo` is blind to `o["foo"]`, so this is the single most consequential spelling in this class of
output as well as the most common.

**The identifier gate is the safety argument and is not cosmetic.** `o["foo bar"]` and `o["0"]` have
no dotted spelling, so they are declined and stay computed — rewriting them would emit code that
does not parse. The same gate doubles as a check on the layer beneath: a decoded string sitting in a
member key that is *not* a valid identifier is evidence the string was decoded wrongly, because the
encoder put a real property name there. That is
[encoder-decoder-method.md](../../../encoder-decoder-method.md)'s W5 check, obtained for free.

**No key needs excluding here, unlike a property *key*.** `o["__proto__"]` and `o.__proto__` are the
same accessor, and there is no member-read analogue of the object-literal `__proto__` special case
or of `class C { ["constructor"](){} }`. Those hazards belong to
[uncompute-property-key.js](uncompute-property-key.md), which is why the two are separate files
rather than one visitor over both shapes.

**Optional members are the same rewrite** and are handled alongside: `o?.["foo"]` becomes `o?.foo`.

**Declines, never stops.** A site failing the gate is skipped and traversal continues.

Exports a plain visitor as default plus `createUncomputeMember(onChange)` for a caller that needs to
know whether it fired — which [normalize-converting.js](../obfuscator/normalize-converting.md) does,
since its fixpoint has to decide whether to run another round.

## Source

- [`src/visitor/atomic/uncompute-member.js`](https://github.com/echo094/decode-js/blob/6cacb633ceedf0812fe31f951ba8f41ffb431ca1/src/visitor/atomic/uncompute-member.js)
- Wired second in [normalize-converting](../obfuscator/normalize-converting.md)'s round, after
  constant folding and before the key pass. Folding has to run first for the reason that doc's
  item 4 gives: with `splitStrings` on, the key arrives as a `+` chain and is not a string literal
  at all until it has been folded.

## Fixtures

**None of its own, and that is a real gap rather than a considered absence.** This is the most
consequential spelling in its class — every later matcher navigating by `o.foo` is blind to
`o["foo"]` — and it is the only pass in the `Converting` group with no case naming it.

What checks it today, all of it transitive:

| Claim | What checks it | Gap |
|---|---|---|
| the rewrite fires | `literals-and-members` under [normalize-converting](../obfuscator/normalize-converting.md), which asserts the member-read axis reads zero **on the tree** rather than in the text | it bundles five reversals, so a regression here is not distinguishable from one in a sibling |
| the identifier gate declines | the corpus-wide U4 census — a non-identifier key left computed is what keeps the axis honest | no committed case, so a gate that started accepting `o["foo bar"]` would emit unparseable code and fail nothing until a corpus run |
| the W5 side-effect: a decoded string in key position that is not an identifier means the layer beneath decoded wrongly | `string-array`'s `guard-rotator-removed` case, which is where that check actually bites | it is pinned as a *string-array* claim, so nothing records that this pass is the instrument |

**A text-level assertion is not the way to close this**, and the first `literals-and-members`
proved it: `/0x[0-9a-f]/i` fails on a correct decode, because renaming leaves `_0x185301`
identifiers everywhere. Any case added here asserts the shape the census reads.
