# StringEncoding

Source: [`transforms/string/stringEncoding.ts`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/string/stringEncoding.ts).

Not a separate `Order` stage — a helper invoked from
[Finalizer](finalizer.md)'s own visitor, `Order.Finalizer = 35`.

## 1. Target

Re-spell a string literal's *source text* as `\x`/`\u` escapes without changing its parsed
value — purely a re-spelling, not real obfuscation, but (see Algorithm) not free to reverse
either.

## 2. Algorithm

On `StringLiteral: exit` (module-import strings skipped), subject to
`options.stringEncoding`'s probability map. When it fires, picks `hexadecimal` or
`unicode` at random per string and re-escapes every character below code point 128 as
`\xHH` or `\uHHHH` (characters ≥128 left as-is). The escaped text (including its own
surrounding quotes) becomes a freshly-built `Identifier` node's `.name`, marked `GEN_NODE`
so the generator emits it as raw text — the identical mechanism
[Finalizer](finalizer.md)'s own hexadecimal-numbers rewrite uses, and for the same reason:
`"\x48\x65..."` isn't a valid identifier, so it can't be represented as a real
string/identifier node without the generator rejecting or re-escaping it. See Finalizer's
Implementation for why this specific trick — a synthetic `Identifier` that never survives a
parse — is what makes reversing it require an explicit decode step rather than a plain
re-parse/re-generate.

## 3. Implementation

`StringLiteral` exit
([`stringEncoding.ts#L51-L74`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/string/stringEncoding.ts#L51-L74)):
module-import strings are skipped
([`isModuleImport`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/utils/ast-utils.ts)),
then subject to `options.stringEncoding`'s probability map. When it fires, picks
`hexadecimal` or `unicode` at random per string
([`stringEncoding.ts#L63`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/string/stringEncoding.ts#L63))
and re-escapes every character below code point 128 as `\xHH` or `\uHHHH`
(characters ≥128 are left as-is,
[`toHexRepresentation`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/string/stringEncoding.ts#L21-L33)/
[`toUnicodeRepresentation`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/string/stringEncoding.ts#L35-L47)).

## 4. Downstream Effects

**`Pack` (Order 36) explicitly guards against this transform's `GEN_NODE` identifiers too**
— the same fact and the same source citation as [finalizer.md](finalizer.md)'s own
Downstream Effects, since both literal-respelling pieces share the identical `GEN_NODE`
mechanism and Pack's guard checks the flag, not which transform set it.

## 5. Known Quirks

None currently documented.
