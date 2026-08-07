# RenameLabels

Source: [`transforms/renameLabels.ts`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/renameLabels.ts) — `Order.RenameLabels = 27`.

## 1. Target

Purely cosmetic: strip a loop/`with`/block label if nothing actually needs it to
disambiguate, otherwise rename it to something meaningless — no data or control-flow
protection of its own, unlike most of this pipeline.

## 2. Algorithm

Two-pass pass over `LabeledStatement`s. First it determines whether each label is
actually load-bearing — i.e. whether some `break`/`continue` needs it to disambiguate
from the *nearest* enclosing loop/switch, as opposed to being present but redundant
(the label matches what an unlabeled `break`/`continue` would already target). Then,
for each label:

- **Not required:** the label is stripped entirely — `label: body` becomes just
  `body`, and the label is removed from every `break`/`continue` that referenced it.
- **Required:** the label is renamed via the same `NameGen` used elsewhere, gated
  per-label by `options.renameLabels`.

## 3. Implementation

**First pass** — collecting usage
([`renameLabels.ts#L35-L121`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/renameLabels.ts#L35-L121)):
for every labeled `break`/`continue`, walks up the enclosing `For`/`While`/`SwitchStatement`
nodes plus any labeled `BlockStatement`, building an ordered list of candidate targets (a
`continue` filters `BlockStatement`/`SwitchStatement` out of that list first, since
`continue` can only ever target a loop). A label is **required** if its target is a
labeled `BlockStatement` (there's no unlabeled way to `break` out of a bare block at all)
*or* if it isn't the nearest candidate in that list — i.e. some closer, unlabeled
loop/switch would otherwise catch the `break`/`continue` instead. Otherwise the label is
redundant for that particular reference, and the reference's own `.label` is cleared
immediately, right in this same pass.

**Decision loop**
([`renameLabels.ts#L122-L142`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/renameLabels.ts#L122-L142)):
every `LabeledStatement` seen in the first pass is either renamed (if any of its own
references came back `required`, subject to `options.renameLabels`'s probability map — a
label that isn't renamed keeps its original text) or marked for removal (if none did).

**Second pass**
([`renameLabels.ts#L144-L172`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/renameLabels.ts#L144-L172)):
applies the decision — a removed `LabeledStatement` is replaced by its own body outright;
a renamed one keeps its structure with a new label name; every `break`/`continue` that
referenced it is updated to match (label cleared, or renamed to the same new name).

## 4. Downstream Effects

None currently documented.

## 5. Known Quirks

None currently documented.
