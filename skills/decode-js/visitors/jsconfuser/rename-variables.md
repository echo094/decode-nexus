# jsconfuser/rename-variables.js — not applicable, but load-bearing everywhere else

## 1. Target

No decode target of its own: mangled names carry no recoverable information, so there is
nothing to reconstruct for [RenameVariables](../../../js-confuser/transforms/rename-variables.md)
itself. What actually matters for this project isn't reversing this transform — it's
making every *other* decoder in this pipeline tolerate having it run underneath them,
since it reassigns every identifier in the program, including every other transform's own
internal runtime-helper names.

## 2. Algorithm

Purely cosmetic on its own output — a generated name is chosen for decidability and
collision-safety (per the encoder doc's Algorithm: reused from a disjoint sibling scope
where safe, otherwise freshly minted), with no relationship to the name it replaced, so no
function maps a mangled name back to the original. The only actionable step on the
mangled result itself is running a standard minifier/pretty-printer/renamer over the
decoded output — identical to how any other transform's own freshly-inserted identifiers
(a promoted local from VariableMasking's un-mask, a hoisted declaration from
MovedDeclarations) already get handled; nobody tries to recover the original developer's
name for those either.

**The real decode-relevant surface of this transform is everyone else's, not its own.**
See [encoder-decoder-method.md](../../../encoder-decoder-method.md)'s W1 — "names are
unreliable by design, not by convention" — whose anchor case *is* this transform breaking
a name-keyed ControlFlowFlattening matcher completely, silently, on every application at
once. A project-wide audit closed this out transform-by-transform; each affected
transform's own decoder doc carries its own "Verified safe"/"Known bug"/"Hardened"
section rather than repeating the audit here (e.g. [control-flow.md](control-flow.md),
[calculator.md](calculator.md), [string-concealing.md](string-concealing.md),
[variable-masking.md](variable-masking.md), [global-concealing.md](global-concealing.md)).

## 3. Implementation

Nothing implemented, and nothing to implement — see Algorithm.

## 4. Upstream Effects

None — item 3 implements nothing, so no pass here has an input for an earlier one to
reshape. The reason this file exists at all runs the other way: `RenameVariables` is a
hazard *to* every other pass, and each affected pass records its own exposure in its own
item 4 or its rename-safety section rather than here (item 2 lists them).

## 5. Known Gaps

None specific to this transform's own (nonexistent) decode target. The open general risk
is structural, not a gap in this file: any *future* jsconfuser matcher added anywhere in
this codebase that identifies encoder-emitted structure by variable/function name text,
rather than by AST shape or a captured binding, is a latent `RenameVariables` bug waiting
to be found — see
[encoder-decoder-method.md](../../../encoder-decoder-method.md#t2--w5-hold-matchers-to-two-contracts--shape-keyed-and-all-or-nothing)'s
T2 for the rule and its audit form (a grep, not a review).

## Source

No dedicated visitor file.

## Fixtures

None of its own, by design: this transform is a *hazard* to every other pass rather than a
layer to strip, so it is covered by each affected transform's own `renameVariables`-combo
fixture under `test/jsconfuser/rename-variables/`, and the claim each one pins is recorded in
that transform's doc.
