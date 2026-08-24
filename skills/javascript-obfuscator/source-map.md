# Source Map

The crossing between the submodule's directory tree and this package's own layout, in the
direction the per-doc `## Source` sections cannot answer: **given a source file, which doc
claims it — and which files does no doc claim at all?**

**This page is a recipe, not a stored table.** A generated inventory decays whenever upstream
source or this package's era coverage changes. The commands below compute both answers from the
current source tree and the docs' own `## Source` sections.

## The two questions

Run from the hub root, with the submodule checked out at whatever commit you are asking about.

**1. Which doc claims this file?** Grep the package for the path.

```sh
grep -rn 'StringArrayRotateFunctionTransformer.ts' skills/javascript-obfuscator/
```

**2. Which source files does no doc claim?** Every `*.ts` under `src/`, minus the exclusions
below, minus everything any doc's `## Source` already cites.

```sh
cd encoder/javascript-obfuscator
git ls-tree -r --name-only HEAD src \
  | grep '\.ts$' \
  | grep -vE '^src/(interfaces|types|declarations|decorators)/' \
  | sed 's#^src/##' | sort -u > /tmp/all.txt
cd -
grep -rhoE 'src/[A-Za-z0-9_./-]+\.ts' skills/javascript-obfuscator/ \
  | sed 's#^src/##' | sort -u > /tmp/claimed.txt
comm -23 /tmp/all.txt /tmp/claimed.txt        # unclaimed
comm -13 /tmp/all.txt /tmp/claimed.txt        # cited but absent — a stale reference
```

The second `comm` is the half that is easy to forget and is the one that catches rot: a path a
doc cites that no longer exists at the commit being asked about. Both directions are needed —
one alone hides exactly one of the two failure modes.

**Ask it at a tag, not only at the pin.** `git ls-tree -r --name-only <tag> src` answers the
same question at any era, which is the whole reason this is a command rather than a table: one
table can only ever be about one commit, and this package documents several.

## Exclusion rules

These are decisions, not measurements, so they live here as text. A reverse lookup for a path
matching one of these terminates here; no doc will ever claim it.

| subtree | why |
|---|---|
| `interfaces/` | type-only declarations, erased at compile time — no emitted behaviour |
| `types/` | same |
| `declarations/` | same (ambient `.d.ts` augmentations) |
| `decorators/` | metadata plumbing for the DI container, no AST effect |

Everything else in `src/` is fair game, including `container/`, `cli/` and `pro-api/`. Those are
not obviously shape-bearing, but "obviously" is the wrong test for an exclusion: a DI module
decides which implementation a token resolves to, so a binding edit can change emitted output
with nothing else in the diff. They stay in scope and unclaimed.

**Files that exist only outside the documented range are not exclusions.** `Obfuscator.ts` held
the pass lists until `0.12.0` and is absent from every tag this package currently registers, so
it appears in no listing taken at the pin. [order.md](order.md) describes it. Ask the question
at a tag where the file exists.

## What "claimed" has to mean

The `## Source` section of a doc is the claim. A doc is **not finished while a file it actually
describes** fails to appear in its `## Source` — that is the condition question 2 exists to
catch, and the condition that went unnoticed while this page was a table, because a table can
be regenerated with the gap baked into it.

Claiming is not exclusive: one file can be cited by several docs, and
`src/JavaScriptObfuscator.ts` is cited by both [javascript-obfuscator.md](javascript-obfuscator.md)
and [order.md](order.md) for different reasons.

## Why the layout does not mirror the source tree

Kept here because it is the standing answer to "why not just key the docs on files?", and this
is the page a reader lands on when asking it. **The file set and the emitted shape move
independently** — and the sharpest way to see it is that the two measurements land on
*different* tag boundaries:

- Across `2.15.3 → 2.15.4` the file set does not move **at all**: `git diff --name-status
  --diff-filter=ADR` over `src` is empty. Yet the string-array calls-wrapper helpers and
  templates are modified heavily, and that content change is a named era boundary,
  `E-sa-wrapper-self-replacing` ([versions.md](versions.md)) — so the silence is measured
  against a shape change on the record rather than against a suspicion.
- Across `2.18.1 → 2.19.0` the file set does move:
  `custom-code-helpers/self-defending/SelfDefendingUnicodeCodeHelper.ts` is renamed to
  `SelfDefendingCodeHelper.ts` and `templates/SelfDefendingNoEvalTemplate.ts` is deleted. That
  one *does* accompany a shape change (`E-selfdef-search`) — but the shape boundary is keyed on
  the surviving template's rewritten body, not on the rename, and the two coincide here only by
  accident: the same release renames the helper class without that rename implying anything
  about what is emitted.

A doc keyed on a source file would churn on the first and stay silent through the second. That
is why the package is laid out on the components every obfuscator has — order, options,
transforms, templates — and why this crossing is a lookup rather than the layout.
