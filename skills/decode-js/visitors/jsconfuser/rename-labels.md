# jsconfuser/rename-labels.js — not applicable

## 1. Target

No decode target. Reversing
[RenameLabels](../../../js-confuser/transforms/rename-labels.md) would mean recovering the
original label text, but nothing in the obfuscated output carries that information — a
renamed label's new name is drawn from the same `NameGen` as every other generated
identifier, with no relationship to what it replaced.

## 2. Algorithm

Renamed labels are purely cosmetic — the name carries no recoverable information, and
there is nothing else in the AST that could stand in for it. Removed labels are
semantically inert by construction (the encoder's own first pass proved they were
redundant before removing them, per its Algorithm), so there's nothing to recover there
either — a `break`/`continue` that lost its label already targets the correct
loop/switch/block unlabeled.

## 3. Implementation

Nothing implemented.

## 4. Upstream Effects

None, and not for want of looking: item 3 implements nothing, so there is no input in this
pipeline for an earlier pass to reshape. Nothing would change this — the section stays empty
for as long as item 1 holds.

## 5. Known Gaps

None — both outcomes (renamed, removed) are genuinely irreversible by design, not merely
unbuilt.

## Source

No dedicated visitor file.

## Fixtures

None. This transform has no decoder coverage.
