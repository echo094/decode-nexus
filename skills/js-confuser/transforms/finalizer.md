# Finalizer

Source: [`transforms/finalizer.ts`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/finalizer.ts) — `Order.Finalizer = 35`.

## 1. Target

Three small, independent last-mile rewrites bundled into the pipeline's final visitor
stage (right before `Pack`, Order 36): re-spell a string/number literal's *source text*
without changing its parsed value (`StringEncoding`, `hexadecimalNumbers`), and clean up a
`RenameVariables`-owned marker call left over when that transform is disabled. None of the
three is order-dependent on the others.

## 2. Algorithm

Three independent visitors combined into one visitor object:

- **StringEncoding** — spread in as a helper's own visitor; see
  [string-encoding.md](string-encoding.md).
- **Hexadecimal numbers** — the same respelling idea applied to integers, in this
  transform's own `NumericLiteral` visitor.
- **`__JS_CONFUSER_VAR__` backup replacement** — unrelated cleanup, only registered when
  `RenameVariables` is absent from the active plugin list.

Both literal-respelling pieces use the identical trick: replace the literal with a
freshly-built `Identifier` node whose `.name` *is* the desired output text, flagged
`GEN_NODE` so the generator emits that text verbatim instead of validating it as a real
identifier. This is a **generation-time-only** trick — see Implementation's closing note
for why it still needs an explicit decoder step despite not touching the AST's semantic
value at all.

## 3. Implementation

### Hexadecimal numbers

`NumericLiteral` exit
([`finalizer.ts#L43-L71`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/finalizer.ts#L43-L71)):
when `options.hexadecimalNumbers` is set and the value is a finite integer, replaces
the literal with an `Identifier` node whose `.name` is literally the hex text
(`"0x1a"`, or `"-0x1a"` for a negative value) and sets the `GEN_NODE` symbol on it.
`GEN_NODE` marks a node whose `.name`/text should be emitted by the generator
verbatim instead of going through normal identifier-validity handling — this is how
the transform gets arbitrary text (`0x1a`, not a valid identifier) into the output
without it being a real `NumericLiteral` with `extra.raw` set.

### `__JS_CONFUSER_VAR__` backup replacement

[`finalizer.ts#L17-L41`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/finalizer.ts#L17-L41):
only registered when `Order.RenameVariables` is *not* in the active plugin list.
Several earlier transforms (`preparation.ts`, `controlFlowFlattening.ts`,
`globalConcealing.ts`, `variableMasking.ts`, `pack.ts`) call
`__JS_CONFUSER_VAR__(someIdentifier)` internally as a marker for "this identifier's
name needs to end up as a string here" — normally consumed by `RenameVariables`
itself. When `RenameVariables` is disabled, nothing else would ever resolve that
marker call, so Finalizer does it here instead: unwraps
`__JS_CONFUSER_VAR__(id)` to a plain `StringLiteral` of `id`'s name. Not obfuscation
in its own right, just cleanup for a mechanism belonging to a different
(cosmetic, unrestorable) transform — see
[RenameVariables](rename-variables.md).

### Why the literal-respelling pieces aren't "free" to reverse

Both StringEncoding and hexadecimalNumbers replace a literal with a **freshly-built
`Identifier`**, not the original literal node — `GEN_NODE` only controls how the
*generator* prints that identifier's `.name`. By the time any decoder sees this output, it
has gone through a full parse of generated *source text*, and `0x1a` / `"\x48\x65..."` are
both syntactically valid literal spellings in their own right — so the parser reads them
back as an ordinary `NumericLiteral`/`StringLiteral` again, not an `Identifier`. The
`GEN_NODE` `Identifier` never survives a parse; it exists purely to get that exact text
into the generated output in the first place.

What *does* survive is the parser's own `node.extra.raw` — the exact source text it parsed
the literal from — and Babel's generator prefers that raw text over re-deriving output
from `.value` whenever it's present. So a plain re-parse/re-generate round trip, with no
decoder pass touching the node at all, prints the hex/escaped spelling back out unchanged
indefinitely. Reversing this requires deleting `extra` from the node before generation (or
constructing a fresh literal node, which has no `extra` to begin with) — worth flagging
since it's the reason a prior "nothing to build" description of both of these specifically
was wrong, unlike most of this project's other genuinely-free cosmetic transforms.

## 4. Downstream Effects

**`Pack` (Order 36) explicitly guards against both literal-respelling pieces' own
`GEN_NODE` identifiers.** Pack's `Identifier: exit` visitor
([`pack.ts#L75-L83`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/pack.ts#L75-L83))
re-crawls scope first (`Program`'s own `path.scope.crawl()`,
[`pack.ts#L69-L71`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/pack.ts#L69-L71)),
which — since Finalizer already ran and left these fake identifiers in the tree — would
otherwise register `0x1a` or a quoted hex/unicode blob as an unresolved global reference
and try to remap it onto Pack's own globals object, corrupting the output. The explicit
`if ((path.node as NodeSymbol)[GEN_NODE]) return;` check is what makes the two schemes
compatible; without it, enabling `pack` together with either `hexadecimalNumbers` or
`stringEncoding` would silently mis-rewrite every respelled literal.

## 5. Known Quirks

None currently documented.
