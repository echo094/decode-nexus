# jsconfuser/finalizer.js — no dedicated file, reuses the shared `delete-extra.js`

## 1. Target

Reverses the decode-relevant half of js-confuser's
[Finalizer](../../../js-confuser/transforms/finalizer.md) transform: undo
`hexadecimalNumbers`' and [StringEncoding](../../../js-confuser/transforms/string-encoding.md)'s
literal re-spelling (`26` → `0x1a`, `"H"` → `"\x48"`) so the generator prints the plain
decimal/unescaped value again.

**Finalizer's third piece is deliberately out of scope, not unbuilt.** Unwrapping a leftover
`__JS_CONFUSER_VAR__(id)` marker call to a plain string, which only appears when
`RenameVariables` is disabled, exists solely to clean up after `RenameVariables` — a
transform this project treats as cosmetic and unrestorable. It is not an independent
obfuscation mechanism, so there is nothing for a decoder to reverse.

## 2. Algorithm

**Delete the parser's preserved raw text, don't hand-port the respelling.** Per the
encoder doc's Implementation, both mechanisms replace a literal with a synthetic
`GEN_NODE`-flagged `Identifier` at *generation* time — a trick that never survives a parse.
By the time decode-js parses the obfuscated output, that `Identifier` is already gone:
`0x1a` and `"\x48\x65..."` are both syntactically valid literal spellings in their own
right, so the parser reads them back as an ordinary `NumericLiteral`/`StringLiteral`, with
its exact source spelling preserved in `node.extra.raw`. Babel's generator prefers that raw
text over re-deriving output from `.value` whenever it's present, so a literal no other
decode-js pass ever replaces prints back out in its original hex/escaped form unchanged,
indefinitely — deleting `node.extra` is what makes the generator fall back to plain-value
printing.

This is why the natural assumption — that re-parsing and re-generating normalizes this away
for free, the same way `!0`/`void 0` get folded back to `true`/`undefined` by
`calculate-constant-exp.js` — is wrong specifically for these two mechanisms: that fold
works because `calculate-constant-exp.js` builds a **brand-new** literal node
(`t.booleanLiteral(...)`, `t.identifier('undefined')`, ...), which has no `extra` field to
begin with. `hexadecimalNumbers`/`StringEncoding` never get touched by any other decode-js
pass in a way that would rebuild them, so their `extra.raw` survives untouched unless
something removes it explicitly.

## 3. Implementation

`plugin/jsconfuser.js` wires in the existing, previously-unused shared `visitor/delete-extra.js`
— `delete node.extra` on every `StringLiteral`/`NumericLiteral` — as its very last decode
step, right before the final `generator()` call.

Confirmed by generating a real `hexadecimalNumbers: true, stringEncoding: true`
sample and running it through `plugin/jsconfuser.js` both before and after
wiring in `delete-extra.js`: before, `var count=0x1000;` and
`"\x48\x65\x6c\x6c\x6f..."`-style strings passed through completely unchanged;
after, `var count = 4096;` and `"Hello, World!"`.

**Why the shared file, not a jsconfuser-specific one.** `delete-extra.js` is a tiny,
fully generic, jsconfuser-agnostic visitor already used inline (duplicated, not imported)
by `sojson.js`/`obfuscator.js`/`sojsonv7.js` for the exact same purpose — stripping a
parser-preserved raw literal spelling so the generator prints the plain value. It has zero
jsconfuser-specific logic and is safe to run unconditionally as a final cleanup step
regardless of which transforms produced which literals (every literal any other jsconfuser
decode pass constructs is already a fresh node with no `extra` to strip, so this is a no-op
for all of them). Reusing the shared visitor rather than forking a jsconfuser-specific
copy was a deliberate call; this is jsconfuser's decode pipeline's first actual import of
the file.

## 4. Upstream Effects

**This pass is a no-op on everything the other decode passes produce, and that is why it is safe
to run unconditionally.** `delete-extra.js` strips a parser-preserved `extra.raw` so the
generator prints the plain value — but `extra` exists only on nodes Babel *parsed*. Every
literal any other jsconfuser pass constructs is a fresh `t.numericLiteral`/`t.stringLiteral`
with no `extra` to remove, so the only nodes this reaches are ones that survived from the
original parse untouched. It therefore cannot undo an earlier pass's work, whatever ran before
it, which is what allows it to sit last with no gate of its own.

## 5. Known Gaps

None currently open.

## Source

[`src/visitor/delete-extra.js`](https://github.com/echo094/decode-js/blob/6c974fb5720518fac9c6b3d4cf558ba90ef9f8e7/src/visitor/delete-extra.js) — shared, not a jsconfuser-specific file
(item 3 has why). Wired into [plugin/jsconfuser.js](../../plugins/jsconfuser.md) as the very
last decode step, immediately before the final `generator()` call.

## Fixtures

None of its own. The pass is a no-op on every literal the other decode passes construct, so
what it does is only observable end to end — item 3 records the
`hexadecimalNumbers` / `stringEncoding` before-and-after that established it.
