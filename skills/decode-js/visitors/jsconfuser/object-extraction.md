# jsconfuser/object-extraction.js — not built, confirmed irreversible on real output

## 1. Target

No decoder exists for
[ObjectExtraction](../../../js-confuser/transforms/object-extraction.md), and — on the
default, preset-based path — building one would decode nothing: per the encoder doc's own
Downstream Effects, `RenameVariables` unconditionally scrubs every placeholder-prefixed
name this transform produces, in all three built-in presets, before output is ever
generated.

## 2. Algorithm

**Not reversible on real obfuscated output.** Confirmed via source, not inferred — three
independent facts, each sufficient on its own:

- `RenameVariables`'s `shouldRename()` returns `true` unconditionally for any name
  starting with the placeholder prefix ("Placeholder variables should always be renamed"),
  so the `{ph}_objName_prop` naming this transform produces is guaranteed to be scrubbed to
  a short mangled name by the time `RenameVariables` (Order 30) finishes.
- `renameVariables: true` is on in all three built-in presets, so this isn't an edge case —
  it's the default path for any preset-based obfuscation.
- Unlike StringConcealing/GlobalConcealing/OpaquePredicates, which leave a decodable
  runtime structure behind (an array, a switch-dispatch function) that a decoder can
  statically evaluate regardless of identifier names, ObjectExtraction leaves **no
  structural trace at all**: `obj.a` becomes a bare identifier reference, indistinguishable
  post-mangling from any other plain variable. Nothing in the final AST marks a group of
  loose variables as having come from one object in the first place.

Net effect: the same "not restorable" bucket as
[RenameVariables](rename-variables.md)/[RenameLabels](rename-labels.md)/[AstScrambler](ast-scrambler.md),
except worse — those preserve the program's shape, this one destroys the grouping
information entirely with no residue to key a matcher on. A decoder would only be useful
in the narrow case where `renameVariables` is explicitly disabled (non-default), where the
`{ph}_objName_prop` naming survives and could in principle be grouped back by its own
naming convention.

## 3. Implementation

Nothing implemented.

## 4. Upstream Effects

None — item 3 implements nothing, so no pass here has an input for an earlier one to
reshape. The dependency that decides this transform's fate is an *encoder*-side one
(`RenameVariables` at Order 30 scrubbing the placeholder naming, item 2), which is a
Downstream Effect on the encoder's side of the pipeline and does not belong in this slot.

## 5. Known Gaps

The `renameVariables`-disabled case above is the only scenario where a decoder would have
anything to reverse. Not built: non-default, and no sample or fixture in this project has
needed it so far.

## Source

No dedicated visitor file.

## Fixtures

None. This transform has no decoder coverage.
