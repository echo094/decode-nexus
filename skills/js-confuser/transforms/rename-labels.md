# RenameLabels

Source: `transforms/renameLabels.ts`

Two-pass pass over `LabeledStatement`s. First it determines whether each label is
actually load-bearing — i.e. whether some `break`/`continue` needs it to disambiguate
from the *nearest* enclosing loop/switch, as opposed to being present but redundant
(the label matches what an unlabeled `break`/`continue` would already target). Then,
for each label:

- **Not required:** the label is stripped entirely — `label: body` becomes just
  `body`, and the label is removed from every `break`/`continue` that referenced it.
- **Required:** the label is renamed via the same `NameGen` used elsewhere, gated
  per-label by `options.renameLabels`.

## Reversal

Renamed labels are purely cosmetic — not worth reversing, the name carries no
information. Removed labels are semantically inert by construction (the pass proved
they were redundant before removing them), so there's nothing to recover there either.
