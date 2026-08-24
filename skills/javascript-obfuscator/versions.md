# Era Registry

The single definition of every era this package documents. Docs cite an era **ID**; nothing
else states a version range, so a boundary that turns out to be wrong is one edit here rather
than one per doc.

**This file is a consumer, never a source.** An era is a maximal range over which some measured
thing holds still, so every row here is a *collapse* of readings taken elsewhere — the `P-*`
rows collapse [order.md](order.md)'s per-tag order tables, and each `E-*` row will collapse the
samples its component was read from. The direction is one-way and load-bearing: the pages that
take the readings key on tags and never cite an era ID, because the era list does not exist
until this file has read them. If a row here disagrees with its source page, the source page
wins and this row is re-collapsed.

**Eras come at two levels of change, and the levels behave differently.** They are not two
lists of the same kind of thing, and the difference decides how many axes each needs.

- **`P-*` — pipeline order. One global axis.** A maximal version range over which the
  transformer execution order is identical: same stage sequence, same stage gating, same
  within-stage levels. A level change reorders traversals for *every* transform at once, so no
  component owns it and there is nothing to split it by. Read directly from source; see
  [order.md](order.md)'s "How the order is assembled."
- **`E-<component>-*` — transform-level algorithm. One axis per component.** A maximal version
  range over which one transform emits the same shape. A shape change is one transform's
  algorithm being rewritten, and the transforms are rewritten independently, so a single global
  shape timeline would carry a boundary wherever *any* of them moved — a string-array doc's
  cited era would shift for a reason having nothing to do with the string array.
  - **`E-sa-<part>-*` — the string array subsystem, on separate axes, not one.** The dominant
    component of this encoder. Named for the shape, never for the legacy `V0`/`V2`/`V3` labels.
    The six structural axes — membership, array holder, root wrapper, per-item encoding, scope
    wrapper and rotator — are a *measured* result rather than a filing preference: the four code
    components move at different releases, and membership and encoding can each move while their
    component's holder shape stays fixed. Focused eligibility boundaries, such as
    `E-sa-surrogate-*`, remain separate from those structural axes. A single `E-sa-*` axis would
    take a boundary at every one of these changes and force an array-holder claim to cite an era
    that moved because the rotator changed.
  - **Every other transform is presumed to have its own evolution too**, and gets its own axis
    when it is studied — control-flow flattening, dead-code injection, the object-key and
    string-splitting converters, each custom code helper. An absent axis records that nobody
    has read that component, never that it held still.

The self-defending helper rename sits inside `P-sorted-deadcode-renameidents`, demonstrating that a
component can move within a single pipeline era. Its emitted shape is tracked independently by the
`E-selfdef-*` axis below; coincident component boundaries remain separate rows.

**The `E-` axes open so far.** From U1, the `Simplifying` and `Finalizing` stages:
`E-simplify-*`, `E-escape-*`, `E-adjacent-merge-*`, `E-directive-*`. From U2 and U3, the
`StringArray` stage: `E-sa-membership-*`, `E-sa-array-*`, `E-sa-wrapper-*`, `E-sa-encoding-*`,
`E-sa-rotate-*` and `E-sa-scope-wrapper-*` — four components and six axes, because the array's
membership and holder shape move independently, as do the root wrapper's hold and decode-helper
housing. The rest open as their components are taken.

**Why six axes and not one.** The components move at *different* releases — the rotator alone at
`2.10.0`, the calls wrapper alone at `2.12.0`, `2.15.4` and `4.2.0`, all three together only at
`2.19.0`, the scope wrapper at `2.16.0` where none of the others move, and array membership at
`3.2.2` while the holder shape stays fixed. Measured by reading each component's template, node and
membership gate at every release tag and classifying each content change, then verified against
output at the boundaries studied. A single string-array axis would take a boundary
wherever *any* of them moved, so a doc citing it would see its era shift for a reason having
nothing to do with its own subject. The split is that measurement, not a preference.

**In particular, "is there a rotate function?" is not a shape question.** Rotation is an option, so
its absence is reachable at *any* version and says nothing about which. Treating it as a shape
conflates a `2.9.6` plain-array sample with a `2.19.0` one whose array still sits in a
self-replacing accessor — which are exactly the two shapes furthest apart on the `E-sa-array-*`
axis.

**Where to look first when one does open.** [options.md](options.md) carries a candidate list: an
option is usually added or retyped *because* the transform behind it changed, so its boundaries
are leads worth testing against output. They are only leads — that page measures the inference
failing in both directions, and in particular the two largest string-array shape changes in this
encoder land on releases where the option surface says nothing at all. A lead is never a row here.

**Two more leads for `E-sa-*` specifically, both file-set observations rather than shape
readings.** A file disappearing and another appearing in the same subsystem is a *replacement
pair*, and a replacement is the kind of change an algorithm rewrite leaves in the directory
listing — worth checking against output, never worth recording as a boundary on its own:

- `CryptUtilsSwappedAlphabet.ts` gives way to `CryptUtilsStringArray.ts`.
- The two `StringArrayScopeCallsWrapper{LexicalScope,Names}DataStorage.ts` give way to a single
  `StringArrayScopeCallsWrappersDataStorage.ts`.

Both are between a 2.x era and the pin. The **ranges are deliberately not stated**: earlier
readings of them were expressed in era IDs that no longer exist, and re-deriving a range is one
command ([source-map.md](source-map.md)) against the tags that actually matter to whoever is
asking. The pairing is the durable observation; the span is not.

**A transformer sweep is not a completeness proof for bug-fix releases.** Read every changelog
item as a second, mandatory checklist against the adjacent tag diff. Parser acceptance and
generator correctness often move through pinned dependencies; runtime behavior can move through
templates, option normalization, CLI defaults or target-specific helpers without the component
file a sweep expected. Each item must therefore end in one of three states: focused emitted/runtime
evidence, an explicit non-emitted classification (for example CLI, source-map, build or security
only), or an open discriminator. “No transformer content changed” is never the third state by
itself. This is how the 5.4.x audit found generator, parser and platform boundaries that the source
axes alone had missed.

## If this file becomes unreadable

**The invariant to protect: exactly one file states a version range.** A transform doc carrying
its own `E-` table with ranges in it would put ranges in two places and break "docs cite era IDs,
never inline version ranges" inside the registry's own package. So the split stays: **registry —
ID, range, SHA, one-line signature; transform doc — what the shape actually is, citing the ID.**

If sheer component count ever makes this file unreadable, split it **by axis into a `versions/`
folder**, one file per axis — never by moving ranges out into the transform docs.

**A sample carries per-component evidence, which is the operational reason for the split.** A
transform whose option was off left no trace, so its era is *unknown* from that sample rather
than wrong — a verdict a global axis cannot express, since it would have to name one era for
the whole file on evidence covering part of it. The version range a sample came from is the
**intersection** of its per-component verdicts, computed from them rather than fingerprinted
as a whole.

An order change need not change any transform's shape, and a shape change need not change the
order, so a `P-` boundary is **not** evidence of an `E-` boundary in either direction, nor is
an `E-` boundary on one component evidence of one on another. Measured here in both directions:
`2.15.3 → 2.15.4` rewrites the calls-wrapper helpers and templates heavily with **no**
pipeline-order change at all, while `1.12.0`'s stage split reorders the whole pipeline. Where
two boundaries coincide, that is a finding to record, not a default.

**An ID names the era's signature, never its position.** Under ordinal IDs an era slotting
*between* two existing ones renames every era above it, in this file and in every doc that
cites one — and that is the normal case, not the exception: the `P-*` axis was six eras when it
was sampled and is twenty-three now that every tag has been read. Four of the six sampled
boundaries were also a release out. A signature name survives all of that because it describes
the era rather than counting it. **Eras are listed here in version order, and a span `A–B`
means every era from `A` to `B` inclusive in that order** — the table is what makes a span
readable, so a span is only ever written against this list.

## Sampling — none, on this axis

**Every release tag was read.** The `P-*` rows below are not sampled and carry no
interpolation: the order was derived at all 184 release tags at or above `0.9.0`, and a row
exists exactly where two adjacent tags differ. There is no `~` notation on this axis and no
span that "both ends agree about" — the middle was read too. The `(2.19.0, 5.5.0)` gap that the
rest of this package still treats as unknown **is closed for pipeline order specifically**, and
for nothing else.

Prereleases (`-beta`, `-dev`, `-rc`) are out of scope, so a boundary names the first *release*
carrying a change. If a change actually landed in a prerelease, the row is still right about
releases and says nothing about the prerelease.

**Excluded: the 21 release tags below `0.9.0`.** They have no transformer and no stage concept
at all — a `node-obfuscators/` architecture driven by a single `estraverse.replace`. That is a
differently-architected encoder rather than an era of this one, so it gets this sentence rather
than rows.

## `P-*` — pipeline-order eras

Listed in version order, and **derived, not sampled** — collapsed from [order.md](order.md)'s
per-tag readings, where a boundary exists only where the *structure* moves: the stage sequence
changes, a stage's gating changes, a stage's level count changes, or a transformer present in
both versions changes its stage or level.

**A shared era does not mean the same transformer set.** A transformer merely appearing in or
vanishing from an existing level is deliberately *not* a `P-*` boundary — it changes what is
emitted, not the traversal structure, so it belongs on that component's `E-<component>-*` axis.
Twelve such changes fall inside these rows. Reading "same era" as "nothing changed" is the one
way to misuse this table.

**Stated blind spot: within-level *order* is not in the boundary criterion.** The criterion
above tests stages, gating, level counts and level membership — not the order of transformers
*inside* a level, which is significant (they interleave at node granularity) and is set by graph
insertion order rather than list position, per [order.md](order.md)'s "Within-level order is
first-mention order." Two versions could therefore run one level with two transformers swapped
and be collapsed here as one era. Its two inputs are the transformer list's order and each
`runAfter` array's order; the first was spot-checked as insertion-only across several era
boundaries, the second has not been checked at all. Closing this means re-deriving with order
compared, not reading these rows more carefully.

Within-level survivor order is verified for the registry's documented phase-1 sample tags. The
claim does not extend beyond those sampled rows; adding a tag requires re-running
[order.md](order.md)'s recipe with within-level order included.

**The mechanism is real and was observed — at a boundary already recorded, which is why it costs no
row.** Across `2.15.2 → 2.15.3` the `RenameIdentifiers` level-1 survivors swap from
`[LabeledStatement, ScopeIdentifiers, …]` to `[ScopeIdentifiers, LabeledStatement, …]`, because
`DeadCodeInjectionTransformer` arrives in that stage declaring
`runAfter: [ScopeIdentifiersTransformer]` and so registers `ScopeIdentifiers` into the graph first —
reordering two transformers in a level **it is not itself in**, which is order.md's rule with a
measured instance. That tag pair is already a boundary on its level count, so the reorder adds
nothing; had it landed mid-era it would have been a missed boundary.

**The name says which mechanism the era uses, because that decides how it must be read.** The
order has been declared three different ways over the encoder's life, and the three are read
from different places — only the last has levels at all. Each mechanism is a group here, and its
eras sit inside it. The mechanisms themselves are described in [order.md](order.md)'s "Who
declares the order."

### `P-lists-*` — the obfuscator holds a literal list per pass

Order **is** list order. One pass, one traversal, no dependency graph, and *levels do not exist*
— asking which level a transformer is in has no meaning here. Read from the static
`*TransformersList` arrays and the sequential `transform()` calls that consume them.

| Era | Version range | Commit SHA | Order signature — what changed at the lower bound |
|---|---|---|---|
| `P-lists-three-pass` | `0.9.0 – 0.9.4` | `19723f6fc69056243defbfc1946696af39686918` | first tag read |
| `P-lists-deadcode` | `0.10.0 – 0.11.2` | `215004aba8599e7fb5647f52b4c4d0ca40758a23` | +stage deadCodeInjectionTransformersList |
| `P-lists-preparing` | `0.12.0 – 0.13.0` | `10375da2a500072796e7ffc4b5ba818e778794f3` | +stage preparingTransformersList |

### `P-declared-*` — the transformers declare their stage

The per-pass lists collapse into one `transformersList` plus a stage enum, and each transformer
names the stages it serves. The obfuscator stops owning the mapping. Still **one traversal per
stage**, so levels still do not exist; what changed is where the mapping is written.

| Era | Version range | Commit SHA | Order signature — what changed at the lower bound |
|---|---|---|---|
| `P-declared-six-stages` | `0.14.0 – 0.14.3` | `c6cb82c1d006e56d099d838cf0b504314f2cc026` | **the declaration inverts.** The five per-pass lists collapse into one `transformersList` plus a `TransformationStage` enum, and every transformer moves from a list the obfuscator held to a stage it declares itself. Six stages: `Preparing`, `DeadCodeInjection`, `ControlFlowFlattening`, `Converting`, `Obfuscating`, `Finalizing` |
| `P-declared-objectexpr-converting` | `0.15.0 – 0.18.6` | `24dd515aada666eeb9a09b18b1e1f70d02a06344` | ObjectExpression ObfuscatingL1->ConvertingL1 |
| `P-declared-initializing` | `0.18.7 – 0.19.2` | `ce7449563754830909b80690778e4577363656c2` | +stage Initializing; Comments PreparingL1->InitializingL1 |

### `P-sorted-*` — declared stages plus the levelled topological sort

`runAfter` and `LevelledTopologicalSorter` arrive, so within-stage order is *computed* and a
stage becomes several traversals. **This is the only mechanism where a level means anything**,
and every claim in this package about levels is scoped to it. Seventeen of the twenty-three eras
are here, including the pin.

| Era | Version range | Commit SHA | Order signature — what changed at the lower bound |
|---|---|---|---|
| `P-sorted-converting-split` | `0.19.3 – 0.23.2` | `34f4300090e4515d436566c622c580614ac522b7` | Converting levels 1->2; SplitString ConvertingL1->ConvertingL2 |
| `P-sorted-literal-finalizing` | `0.24.0 – 0.24.6` | `65f8bb84d42814e4ff174856ff0a1fcc10bb22ee` | Literal ObfuscatingL1->FinalizingL1 |
| `P-sorted-varpreserve-obfuscating` | `0.25.0` | `fbab8149f712ad4ff7d3f70bb9629ea2ccd288e6` | VariablePreserve PreparingL1->ObfuscatingL1 |
| `P-sorted-preparing-3levels` | `0.25.1 – 1.0.1` | `4860db799fc983948c2d12281d5a97674ea326fe` | Preparing levels 1->3; Metadata PreparingL1->PreparingL3; ObfuscatingGuards PreparingL1->PreparingL3 |
| `P-sorted-renameprops-stage` | `1.1.0 – 1.1.1` | `d65c9af46e21efc787f214d3e409921276020c3a` | +stage RenameProperties |
| `P-sorted-comments-finalizing` | `1.2.0 – 1.3.0` | `dcec5f673752effd1f839424439e4abb34104345` | Comments InitializingL1->FinalizingL1 |
| `P-sorted-simplifying-stage` | `1.4.0 – 1.11.0` | `cd20be40369c0ff36fc64fdb083521ce2cb39862` | +stage Simplifying |
| `P-sorted-obfuscating-split` | `1.12.0` | `8c91a254beba14fa491652bdd8b6c00e935779d0` | +stage RenameIdentifiers,StringArray; -stage Obfuscating; VariablePreserve ObfuscatingL1->RenameIdentifiersL1; LabeledStatement ObfuscatingL1->RenameIdentifiersL1; ScopeIdentifiers ObfuscatingL1->RenameIdentifiersL1 |
| `P-sorted-renameprops-first` | `1.12.1 – 2.3.1` | `062802fd3c910a16247b2d57e4a2fa6996f5f8e5` | stage sequence reordered |
| `P-sorted-stringarray-stage` | `2.4.0` | `2dc37c389f849dcec239f2f0ae41fb1b6ba985f4` | StringArray FinalizingL1->StringArrayL1 |
| `P-sorted-finalizing-3levels` | `2.4.1 – 2.9.4` | `444c378884af359283aa0c74b05a3a2d61073166` | Finalizing levels 1->3; EvalCallExpression FinalizingL1->FinalizingL3; EscapeSequence FinalizingL1->FinalizingL2 |
| `P-sorted-helpers-to-preparing` | `2.9.5` | `e7fb615cba43efed35d080d4bdaeeec22bd04251` | Finalizing levels 3->2; CustomCodeHelpers FinalizingL1->PreparingL3; EvalCallExpression FinalizingL3->FinalizingL2; EscapeSequence FinalizingL2->FinalizingL1 |
| `P-sorted-directive-placement` | `2.9.6` | `0afcf7a5b2f56ba7c31246928f8f1b485a0a030a` | Preparing levels 3->4 |
| `P-sorted-rotate-transformer` | `2.10.0 – 2.15.2` | `86fe1df40c8a391f909375cb7ebec552fea781fa` | StringArray levels 1->2; StringArrayScopeCallsWrapper StringArrayL1->StringArrayL2; StringArray StringArrayL1->StringArrayL2 |
| `P-sorted-deadcode-renameidents` | `2.15.3 – 3.1.0` | `993cf7a2a850365baf105e54a09a761724d47da9` | RenameIdentifiers levels 1->2; DeadCodeInjection FinalizingL1->RenameIdentifiersL2 |
| `P-sorted-sa-controlflow` | `3.2.0 – 5.4.3` | `711a1353341f4dcea4a1b0c972735545e48a8f11` | ControlFlowFlattening gating controlFlowFlattening -> none; RenameIdentifiers levels 2->1; StringArray levels 2->3; DeadCodeInjection RenameIdentifiersL2->StringArrayL1 |
| `P-sorted-renameidents-3levels` | `5.4.4 – 5.5.0` | `c6d0872a631ed290d29fce6551fbfceb6c31577d` | RenameIdentifiers levels 1->3; ScopeIdentifiers RenameIdentifiersL1->RenameIdentifiersL2; ScopeThroughIdentifiers RenameIdentifiersL1->RenameIdentifiersL3 |

**No row is derived from output.** Every one is read from source, so each records what the
encoder *says* it does and nothing about what it emits. That is the gap the hub's Encoder Pin
Gate exists to close, and it applies to all 23 rows, the pin's included.

## `E-<component>-*` — transform-shape eras

Each component's axis gets its own table here when that component is studied, with the same
columns as `P-*` except that the signature is the observable shape rather than the order, plus an
**Evidence** column — a shape era is entered from output, not from source, and this axis has rows
of both kinds.

**What `Evidence` means, and why the column exists rather than a footnote.** `output` means the
shape was read off emitted samples at that era. `source` means the boundary was found by reading
the transformer at every release tag and classifying each content change as shape-affecting or
mechanical, with no sample built. A `source` row is a real finding — it is exhaustive over tags,
not sampled, so it carries no interpolation — but it has not met the standard the rest of this
axis is held to, and merging the two kinds into one unmarked table is how a reading gets promoted
to a measurement by being written down next to one. `source, and unreachable in output` is reserved
for a source-derived distinction whose subject cannot produce an emitted artifact (for example,
an input rejected at parse or encoder acceptance); it is not output evidence.

The first four axes below come from U1, the normalization unit: the `Simplifying` (9) and
`Finalizing` (10) stages. The next five come from U2, the string-array unit, and
`E-sa-scope-wrapper-*` from U3 — the `StringArray` stage (8). `E-propname-*`,
`E-shorthand-static-*`, `E-classfield-*`, `E-numexpr-*`, `E-template-*` and the boolean heritage
axis come from U4, the `Converting` (6) unit. The `E-cff-*` axes come from U5, the
`ControlFlowFlattening` (4) unit. The focused `E-renameprops-*` axes are release-note boundaries
in the irreversible `RenameProperties` (5) stage; they have no full transform document here. The
generator, parser and domain-lock axes are release-note boundaries whose evidence is kept separate
from these transform units.

### `E-simplify-*` — the statement and `if` collapse

One axis for two transformers, because they share the collapse algorithm outright
([statement-simplification.md](transforms/statement-simplification.md)). Every boundary is in the
guard list that decides whether a collapsed `if` branch may drop its braces, except the last,
which is in the shared collection routine.

| Era | Version range | Commit SHA | Evidence | Shape signature — what changed at the lower bound |
|---|---|---|---|---|
| `E-simplify-braces-optional` | `2.9.6 – 2.10.1` | `0afcf7a5b2f56ba7c31246928f8f1b485a0a030a` | source | lower bound is **the floor of what was read**, not a boundary — see below. Brace-dropping is refused only for a `FunctionDeclaration` and a non-`var` declaration |
| `E-simplify-guard-single-body` | `2.10.2` | `76eed2017f81bd96ca7ee35c7213731d75ea2c83` | source | + refuses any node with a single-statement body (`for`, `while`, `do-while`, `for-in`, `for-of`, `with`, labeled, and a single-branch `if`) |
| `E-simplify-guard-nested-if` | `2.10.3 – 3.2.1` | `314855eb8bb65653b8c292e7a65ffcdc6c39761b` | output + source | + refuses an `IfStatement` outright (upstream issue #860). **The spine, 2.19.0, is this era**, and the SHA is the spine's. Output is byte-identical at `3.0.0` and `3.0.1`; source keeps the guard through `3.2.1` |
| `E-simplify-halt-after-return` | `3.2.2 – 5.5.0` | `77f64bf5df0e943ac2f9c035577e0e44a9f5f3e4` | output + source | a block with statements *after* its `return` stops collapsing at all, rather than collapsing the trailing run |

**`E-simplify-braces-optional`'s lower bound is a floor, not a boundary.** The file set moves
several times between `1.4.0` (where the `Simplifying` stage arrives) and `2.9.6`, and none of
those changes has been classified. So that row means "unchanged from `2.9.6` up", and says nothing
about `2.9.5` and below. Narrowing it downward is a reading, not a new row.

### `E-escape-*` — string-literal escaping

| Era | Version range | Commit SHA | Evidence | Shape signature — what changed at the lower bound |
|---|---|---|---|---|
| `E-escape-from-value` | `2.9.6 – 5.4.5` | `314855eb8bb65653b8c292e7a65ffcdc6c39761b` | **output** | escapes the literal's *decoded value*; `\xNN` for ASCII, `\uNNNN` otherwise. Lower bound is the read floor, as above. SHA is the spine's |
| `E-escape-from-raw` | `5.4.6 – 5.5.0` | `f1805500f807b8e2090f8ad70ace5f958413f2b2` | output + source | the encoder is handed the literal's **original raw spelling** alongside its value (`encodeLiteral`), so unicode, code-point and hex spellings survive; the literal cache key also includes `raw`, keeping duplicate values with distinct source spellings separate |

### `E-adjacent-merge-*` — sibling statement and declaration merging

| Era | Version range | Commit SHA | Evidence | Shape signature — what changed at the lower bound |
|---|---|---|---|---|
| `E-adjacent-merge-pairwise` | `2.9.6 – 5.5.0` | `314855eb8bb65653b8c292e7a65ffcdc6c39761b` | **output** | one era across the whole read range. Adjacent same-kind siblings fuse leftwards; expression statements flatten into one `SequenceExpression`, declarations concatenate declarators and refuse to cross a `kind` change. Lower bound is the read floor |

### `E-directive-*` — directive re-placement

| Era | Version range | Commit SHA | Evidence | Shape signature — what changed at the lower bound |
|---|---|---|---|---|
| `E-directive-rehoist-no-residual` | `2.9.6 – 5.1.0` | `6866396e9a74dd1d5d8c38f169a40889802907da` | **output** | the directive is observed during `Preparing`, re-emitted as a clone at the top of its scope during `Finalizing`, and the original identity is removed by a recursive walk even if control-flow flattening nested it in a switch case. Lower bound is the read floor |
| `E-directive-rehoist-nested-residual` | `5.2.0 – 5.5.0` | `3848bca7941ed86d62e6a7108b960201613d2172` | output + source | re-hoisting is unchanged, but removal filters only the scope's direct body. A directive already moved into a control-flow switch case survives there as an ordinary string expression beside the prepended clone. Output is frozen at the lower bound; persistence above it is source-proven |

The bookkeeping move from AST metadata to a `WeakMap` at `2.10.0` and the whole-file reformat at
`4.2.1` are source changes inside the first era, not boundaries. The `5.2.0` unlink change is a
boundary after all: direct placement looks unchanged, but CFF exposes the nested identity that the
new shallow filter cannot reach
([directive-placement.md](transforms/directive-placement.md) carries the interaction).

**A note on what these four axes share, since it is a coincidence and not a rule:** all four have
their read floor at `2.9.6`, because that is where phase 1's version matrix starts, not because
anything happened there. `2.9.6` is a `P-*` boundary — it is the whole of
`P-sorted-directive-placement` — and that is unrelated. A `P-` boundary is not evidence of an
`E-` one.

### `E-sa-membership-*` — the zero-threshold membership gate

Which eligible literals enter the string array
([string-array.md](transforms/string-array.md)). This is separate from how the resulting array is
held: membership can change while the holder's emitted shape stays fixed. The threshold comparison
was read from its introduction through the pin and verified against real output at the boundary.

| Era | Version range | Commit SHA | Evidence | Shape signature — what changed at the lower bound |
|---|---|---|---|---|
| `E-sa-membership-zero-draw` | `0.23.0 – 3.2.1` | `711a1353341f4dcea4a1b0c972735545e48a8f11` | output + source | an inclusive `random <= threshold` comparison means threshold `0` can still capture a literal when the discrete random draw is exactly zero. Output verified at `3.2.0`; `0.23.0` is where this analyzer first gains the threshold gate |
| `E-sa-membership-zero-disabled` | `3.2.2 – 5.5.0` | `77f64bf5df0e943ac2f9c035577e0e44a9f5f3e4` | output + source | an explicit truthiness check rejects threshold `0` before drawing, so zero means no program literal enters storage |

### `E-sa-surrogate-*` — lone-surrogate eligibility for encoded storage

This is separate from the threshold axis above. It concerns whether a literal containing a lone
UTF-16 surrogate can enter base64/RC4 storage without the encoder failing while preparing its
encoded value.

| Era | Version range | Commit SHA | Evidence | Shape signature — what changed at the lower bound |
|---|---|---|---|---|
| `E-sa-surrogate-urierror` | `~ – 5.4.6` | `f1805500f807b8e2090f8ad70ace5f958413f2b2` | source, **and unreachable in output** | base64/RC4 storage preparation rejects a lone high or low surrogate with `URIError: URI malformed`; no encoded helper-array artifact exists for the failed input, and the lower bound is unread |
| `E-sa-surrogate-inline` | `5.4.7 – 5.5.0` | `35860ec7087b1e53e89233419f91336f6d4f0bd5` | output + source | a lone-surrogate guard leaves the literal inline and excludes it from encoded helper-array members; valid surrogate pairs remain eligible |

Focused `5.4.6`/`5.4.7` string and escape cases record the low-side encoder failures and supply
output evidence for the guarded forms. The ordinary corpus columns do not
populate this surrogate axis, so they are not used as evidence for it. The adjacent ordinary
`5.4.6`/`5.4.7`/`5.5.0` comparison supplies the persistence check; its task-local cell totals do
not become a durable version claim.

### `E-sa-array-*` — how the string array is held

The array itself ([string-array.md](transforms/string-array.md)). Boundaries read from
`StringArrayTemplate.ts` at **every** release tag, then classified by diffing each content change;
the only other change in the file's whole history is a placeholder rename at `2.4.1` and a
whitespace reformat at `4.2.1`, neither of which is a boundary.

| Era | Version range | Commit SHA | Evidence | Shape signature — what changed at the lower bound |
|---|---|---|---|---|
| `E-sa-array-declaration` | `0.25.0 – 2.18.1` | `18f5210871a6574f256938d4ad56e2ac19ac8884` | **output** | the array is a single declaration, `NAME = [ … ]`. Output read at 2.9.6, 2.10.0, 2.11.1, 2.12.0, 2.15.3, 2.15.4, 2.18.1; SHA is 2.18.1's. Below 2.9.6 the row is source-only, and `0.25.0` is **the read floor** — where this template file begins, not a shape boundary; earlier releases emit the array from somewhere else and are unread |
| `E-sa-array-self-replacing-fn` | `2.19.0 – 5.5.0` | `314855eb8bb65653b8c292e7a65ffcdc6c39761b` | **output** | the array moves inside an accessor function that rewrites its own binding to a closure returning it. Output read at 2.19.0, which is the SHA; the range above 2.19.0 is **source**-read only |

### `E-sa-wrapper-*` — the root string-array calls wrapper

The global accessor use sites call
([string-array-calls-wrapper.md](transforms/string-array-calls-wrapper.md)). **Not** the per-scope
wrappers, which are a separate component on the axis below
([string-array-scope-calls-wrapper.md](transforms/string-array-scope-calls-wrapper.md)). Boundaries
read from
`StringArrayCallsWrapperTemplate.ts` at every release tag; the `4.2.1` change is whitespace only.

| Era | Version range | Commit SHA | Evidence | Shape signature — what changed at the lower bound |
|---|---|---|---|---|
| `E-sa-wrapper-var-fn-expression` | `2.0.0 – 2.11.1` | `99194f145698a378b14114cbb4bec89d3cdc34f2` | output + source | a declaration initialised with a function expression. `2.0.0` is the approved stable-2.x read floor, not a shape boundary. The stable-2.x root holder is output-verified at `2.0.0`, `2.8.1`, `2.9.0`, `2.9.5`, `2.9.6`, `2.10.0` and `2.11.1`; exact tag history keeps that holder shape across the row. The pre-2.9 template supplies a fixed-zero shift, while the 2.9 template supplies `indexShiftAmount`; that source change does not make a different root-wrapper holder |
| `E-sa-wrapper-fn-declaration` | `2.12.0 – 2.15.3` | `36ea9c08f3244533b466b3031824da6493aa2d4e` | **output** | same body, re-held as a hoisted function declaration |
| `E-sa-wrapper-self-replacing` | `2.15.4 – 2.18.1` | `08aad1b7069e9f8b510765dcbf01c88aa741378d` | **output** | the first call rewrites the wrapper's own binding to the real accessor and delegates to it |
| `E-sa-wrapper-array-fn-call` | `2.19.0 – 4.1.1` | `314855eb8bb65653b8c292e7a65ffcdc6c39761b` | **output** | the array is obtained by *calling* the accessor function, hoisted into the outer function. Forced by `E-sa-array-self-replacing-fn`. SHA is the spine's; above 2.19.0 the range is **source**-read |
| `E-sa-wrapper-flat` | `4.2.0 – 5.5.0` | `01465a233c977c45d2f238806a95a06387cc7a39` | **output** | the self-replacement is **removed**; a plain function declaration shifts the index inline, calls the array holder and returns the indexed value. Base64/RC4 caches move from the captured `arguments` object to data on the wrapper function. The focused root-wrapper signature census and ordinary column both populate the flat form. A reversion, so "self-replacing" is not a monotonic newer-is-more signal |

### `E-sa-scope-wrapper-*` — the per-scope calls wrappers

The wrappers `stringArrayWrappersCount` / `stringArrayWrappersType` inject into individual lexical
scopes, which forward to the root wrapper
([string-array-scope-calls-wrapper.md](transforms/string-array-scope-calls-wrapper.md)). **Not** the
root wrapper itself, which is `E-sa-wrapper-*` above. Boundaries read from `StringArrayScopeCallsWrapperFunctionNode.ts`,
`…VariableNode.ts` and their transformer at every release tag, then verified against output.

| Era | Version range | Commit SHA | Evidence | Shape signature — what changed at the lower bound |
|---|---|---|---|---|
| `E-sa-scope-wrapper-var-fn-expression` | `2.3.0 – 2.15.5` | `08aad1b7069e9f8b510765dcbf01c88aa741378d` | output + source | the function form is a function **expression** held in a declarator, `var X = function (a, b) { return root(…) }`. Source history puts the form's stable-2.x introduction at `2.3.0`; output is verified at `2.8.1`, `2.9.0` and `2.9.5`, plus the existing corpus sites from `2.9.6` onward. The pre-2.9 output carries a string-valued numeric index; the 2.9 output carries a numeric-valued index. Parameter slots are randomized per wrapper on the latter source path, so their position is not an era signature |
| `E-sa-scope-wrapper-fn-declaration` | `2.16.0 – 5.1.0` | `6866396e9a74dd1d5d8c38f169a40889802907da` | output + source | same body, re-held as a hoisted function **declaration**, `function X(a, b) { return root(…) }`; under chained calls, each wrapper independently chooses its upper wrapper |
| `E-sa-scope-wrapper-shared-upper` | `5.2.0 – 5.5.0` | `45ad03b8335bee095b17c0d29b0a78bff158c93a` | source | the declaration form stays; under chained calls, every wrapper in one `(scope, encoding)` bucket shares one chosen upper wrapper rather than choosing independently |

**The two later function-node changes are mechanical.** `4.2.1` reformats the source and `5.4.3`
adds dependency-injection decoration; both preserve the returned `FunctionDeclaration`. The real
later boundary is in the transformer at `5.2.0`, where upper-wrapper selection moves outside the
per-wrapper loop.

**Two things about this axis that a reader will otherwise assume wrongly.**

- **The variable form does not move at `2.16.0`.** `stringArrayWrappersType: 'variable'` emits one
  declarator aliasing the root wrapper on both sides of the boundary; only the function form
  changes hold. The era name describes the function form because that is what the signature reads.
- **The index-carrying parameter's position is randomised per wrapper, not per era.** One sample
  carries `root(p2 - 0x218, p1)` beside `root(p1 - -0x9a, p2)`. Comparing two samples without
  checking *within* one reads this as a version difference. Any consumer that models the arithmetic
  must therefore do so per wrapper.

**What the source diff alone got wrong here, recorded because the same trap is live on every other
axis.** Reading only the custom-node files across `2.15.5 → 2.16.0` shows the index computation
changing from a precomputed `shiftedIndex` to `scopeIndex - upperIndex` and *nothing about the
declaration form* — so the boundary reads as a value change with no observable signature, and the
row nearly went unwritten. The declaration form is chosen by the **transformer**, which the node
diff cannot show. Output at both ends is what settled it, and sampling the low boundary directly is
what pinned it to `2.16.0` rather than to somewhere in `(2.15.4, 2.18.1]`.

### `E-sa-rotate-*` — the standalone rotator

The IIFE that rotates the array back at load time
([string-array-rotate.md](transforms/string-array-rotate.md)). Boundaries read from
`StringArrayRotateFunctionTemplate.ts` at every release tag; four content changes to
`StringArrayRotateFunctionTransformer.ts` inside `E-sa-rotate-compare-loop` were each diffed and
are mechanical.

| Era | Version range | Commit SHA | Evidence | Shape signature — what changed at the lower bound |
|---|---|---|---|---|
| `E-sa-rotate-counter-loop` | `0.28.0 – 2.9.6` | `0afcf7a5b2f56ba7c31246928f8f1b485a0a030a` | **output** | a counted loop, `while (--times) push(shift())`, whose trip count **is the second IIFE argument** — the rotation amount is a literal in the file. Output read at 2.9.6, which is the SHA; below it the range is source-only. Emitted by a code helper alone; there is no rotate transformer yet |
| `E-sa-rotate-compare-loop` | `2.10.0 – 2.18.1` | `86fe1df40c8a391f909375cb7ebec552fea781fa` | **output** | the trip count disappears: an unbounded `while` rotating until a `parseInt` checksum over the array's own elements equals a random target, with a `catch` that rotates and retries. The amount is stated nowhere |
| `E-sa-rotate-compare-loop-fn-arg` | `2.19.0 – 5.5.0` | `314855eb8bb65653b8c292e7a65ffcdc6c39761b` | **output** | the first parameter becomes the array *accessor*, called inside the IIFE; the checksum re-spells as `parseInt(…) / n` terms. Output read at 2.19.0; above it **source**-read only |

**A coincidence worth recording rather than merging:** `2.19.0` is a boundary on all three of these
axes at once, and it is also where both source-derived axes go quiet
([order.md](order.md), [options.md](options.md)). Three components rewritten in one release is a
finding about that release, not evidence that they share an axis — the other four boundaries in
these tables each move exactly one of the three.

### `E-sa-encoding-*` — where the per-item decode logic lives

The calls wrapper's **decode** helpers, for a non-`none` `stringArrayEncoding`
(`AtobTemplate.ts`, `StringArrayBase64DecodeTemplate.ts` and their RC4 siblings). Swept by reading
those templates at every release tag that has them.

| Era | Version range | Commit SHA | Evidence | Signature — what changed at the lower bound |
|---|---|---|---|---|
| `E-sa-encoding-decode-in-wrapper` | `0.25.0 – 2.15.4` | `08aad1b7069e9f8b510765dcbf01c88aa741378d` | source | `atob` returns its raw output, and the calls wrapper carries **its own** decode function — a `%`-escape loop plus `decodeURIComponent` — which the wrapper then calls. Two helpers. SHA is 2.15.4's |
| `E-sa-encoding-decode-in-atob` | `2.15.5 – 5.5.0` | `ac8b8c4b078411d941a86bbf1db1025d9d2d097d` | source | the escape loop **moves into the `atob` helper**, which now returns the decoded string, and the wrapper's decode member collapses to a bare alias of it. One helper. SHA is 2.15.5's |

**Why this axis exists at all, and why it is `source` rather than `output`.** It was found while
diffing encoder source across `2.15.4 → 2.16.0`, not by studying the component — the case
doc-conventions' "a component with no axis is one nobody has studied" is about. **The two eras emit
equivalent logic**: the escape loop and `decodeURIComponent` are present on both sides, merely
housed in different helpers. The structural census that would promote the row to **output** —
whether the wrapper's decode member is a function *expression* or an *alias* — has not been run.

`2.15.5` remains the useful discriminator because this axis moves there while
`E-sa-scope-wrapper` and `E-objkeys` do not; the registry records only that encoder-side isolation.

### `E-renameprops-*` — focused property-renaming release-note boundaries

`RenameProperties` (5) is irreversible by design and remains a census concern rather than a full
transform document. These two focused axes are the exception needed to record the exact 5.4.0
release-note shapes. The adjacent-tag backfill supplies output at `5.3.1` and `5.4.0`; the old
side is therefore written with an unknown lower bound (`~`) rather than implying that `5.3.1`
introduced it. The high side reaches the `5.5.0` pin only where the relevant source was checked
through that pin: between `5.4.0` and `5.5.0`, the only edits to the two transformer files are
the Inversify-v7 decorator migration, and the reserved-name data is unchanged. Thus the high
rows have exact output at `5.4.0` plus source persistence to `5.5.0`; they do not interpolate
unsampled output.

#### `E-renameprops-private-*` — private field and method names

The #1220 fixture enables `renameProperties` in `unsafe` mode and keeps all other shape-bearing
options off. At the low tag the private field and method names remain `#field` and
`#privateMethod`; at the high tag the same private names become generated `#_0x...` names, with
declarations and accesses changed together. Both emitted forms parse and run in the focused
matrix.

| Era | Version range | Commit SHA | Evidence | Shape signature — what changed at the lower bound |
|---|---|---|---|---|
| `E-renameprops-private-preserved` | `~ – 5.3.1` | `7792fb0be3ab36af2f3925c4e754b24a5a4008fa` | **output** | **lower bound unread**; at the exact low tag, private field and method names remain their source spellings, including every declaration and access in the focused control |
| `E-renameprops-private-renamed` | `5.4.0 – 5.5.0` | `45ad03b8335bee095b17c0d29b0a78bff158c93a` | output + source | exact `5.4.0` output has `PrivateIdentifier` nodes entering the property replacer, so private field and method declarations and accesses receive generated names together; the relevant transformer source remains equivalent at the `5.5.0` pin |

#### `E-renameprops-reserved-modern-*` — modern reserved-name list entries

The #1066 fixture is a **plain-object** harness. At the low tag `at`, `toSorted` and `findLast`
are renamed while the ordinary control is also renamed; at the high tag those three names remain
and the ordinary control still renames. The source diff is an update to the reserved-name list,
not evidence of a browser implementation or a browser-wide compatibility matrix.

| Era | Version range | Commit SHA | Evidence | Shape signature — what changed at the lower bound |
|---|---|---|---|---|
| `E-renameprops-reserved-modern-renamed` | `~ – 5.3.1` | `7792fb0be3ab36af2f3925c4e754b24a5a4008fa` | **output** | **lower bound unread**; at the exact low tag, the focused plain-object methods `at`, `toSorted` and `findLast` are renamed, alongside the ordinary-property control |
| `E-renameprops-reserved-modern-preserved` | `5.4.0 – 5.5.0` | `45ad03b8335bee095b17c0d29b0a78bff158c93a` | output + source | exact `5.4.0` output has the updated reserved-name list preserving the three focused modern names while an ordinary property still renames; the reserved-name data and relevant replacer source persist at the `5.5.0` pin |

Focused `5.3.1`/`5.4.0` cases pin the exact source/output qualification and the plain-object
limitation. The rows do not
claim that every reserved entry, browser API, or unsampled release has been tested.

### `E-propname-*` — property-name literalization

From U4, the `Converting` (6) unit. One axis for three transformers, because they apply one rule at
three syntactic positions
([property-name-literalization.md](transforms/property-name-literalization.md)). None is gated on
an option, so this axis is read on every cell of every column rather than on an option set.

| Era | Version range | Commit SHA | Evidence | Shape signature — what changed at the lower bound |
|---|---|---|---|---|
| `E-propname-computed-literal` | `2.9.0 – 4.1.1` | `828a190cf80a86227ef77be38e99aad9838aed70` | output + source | every statically written property name becomes a string literal: a member access and a class **method** key also become `computed`, an object-literal key does not. Already-computed nodes untouched; `constructor` exempt. The lower bound is a read floor |
| `E-propname-ignored-metadata` | `4.2.0 – 5.1.0` | `6866396e9a74dd1d5d8c38f169a40889802907da` | output + source | + a member expression whose object or property carries ignored-node metadata stays unchanged; three focused adjacent seeds emit `import.meta['url']` at `4.1.1` and `import.meta.url` at `4.2.0`. The ordinary corpus has no `MetaProperty` population |
| `E-propname-process-env-plain` | `5.2.0 – 5.3.1` | `7792fb0be3ab36af2f3925c4e754b24a5a4008fa` | source | + the preparing guard marks the complete `process.env.*` chain ignored, so it stays identifier-keyed and non-computed |
| `E-propname-reserved-class-plain` | `5.4.0 – 5.5.0` | `45ad03b8335bee095b17c0d29b0a78bff158c93a` | output + source | + class **method** names matching `reservedNames` stay non-computed; ordinary members and object-literal keys retain the preceding shapes |

**Class *fields* are deliberately not on this axis**, and separating them is the whole reason this
section has two tables. The `5.4.0` source change affects methods and fields through one transformer,
but it opens one row here for methods and a separate row below for fields.

**The lower bound is a read bound, not a boundary.** `MemberExpressionTransformer` exists from
`0.9.0`, `ObjectExpressionTransformer` from `0.15.0`, and the class-member transformer from `0.9.0`,
last changing content at `0.26.0`. Narrowing downward is a reading, not a new row. Above the spine,
the member path gains ignored-metadata exemptions at `4.2.0` and `5.2.0`, and the class-method path
gains the reserved-name exemption at `5.4.0`; the object-literal path remains unchanged through the
pin.

**The `2.18.0` rename is structural drift, not shape drift** — the clearest instance in this package
of the two axes coming apart in the direction that would fool a file-keyed layout.
`MethodDefinitionTransformer.ts` disappears at `2.18.0` and `ClassFieldTransformer.ts` appears; the
file set moves, and for class *methods* nothing whatsoever changes — the logic is the same two paths,
the same `ignoredNames: ['constructor']`, the same emitted shape at every version either side. What
the rename actually carries is a widened visitor, and that belongs to the next axis.

### `E-shorthand-static-*` — ObjectPattern shorthand inside class static blocks

`ObjectPatternPropertiesTransformer` normally skips a Program-scope binding when
`renameGlobals: false`. The 5.4.0 fix checks for a containing `StaticBlock` before applying that
skip. This is a local exception to the shorthand expansion algorithm. Wrapped controls are equal
across the two tags; only the top-level static-block
controls expose the boundary.

| Era | Version range | Commit SHA | Evidence | Shape signature — what changed at the lower bound |
|---|---|---|---|---|
| `E-shorthand-static-global-shorthand` | `~ – 5.3.1` | `7792fb0be3ab36af2f3925c4e754b24a5a4008fa` | **output** | **lower bound unread**; at the exact low tag with `renameGlobals: false`, a top-level static-block declaration remains shorthand; the paired assignment control leaves `{x}` while the renamed binding is used, and the emitted program throws `ReferenceError` |
| `E-shorthand-static-expanded` | `5.4.0 – 5.5.0` | `45ad03b8335bee095b17c0d29b0a78bff158c93a` | output + source | exact `5.4.0` output has a containing static block exempted from the Program-scope skip, so `{x}` expands to `{x: generated}` and the declaration and assignment controls emit and run with result `42`; the relevant transformer source persists at the `5.5.0` pin |

The low-side assignment is a malformed encoder artifact, not a successful runtime result. The
exact adjacent-tag controls pin their wrapped/non-wrapped qualification.

### `E-classfield-*` — class field keys

Its own axis because it is the one position that moves. `ClassFieldTransformer`'s visitor accepts
`PropertyDefinition` where its predecessor accepted only `MethodDefinition`, so class fields begin
being literalized at `2.18.0`.

| Era | Version range | Commit SHA | Evidence | Shape signature — what changed at the lower bound |
|---|---|---|---|---|
| `E-classfield-rejected` | `~ – 2.17.0` | `8acfac18d7bccd8524008ab4175838f1e4a51ed8` | **output** | **no emitted shape exists: the encoder refuses the input.** A class field is a parse error at `2.9.6` (`Unexpected token`) and a `RangeError: Maximum call stack size exceeded` at `2.16.0`. Two different failure modes, and the boundary between them is unlocated |
| `E-classfield-computed-literal` | `2.18.0 – 5.3.1` | `7792fb0be3ab36af2f3925c4e754b24a5a4008fa` | output + source | the field key is literalized and marked computed exactly like a method key — `size = 3` emits as `['size']=0x3` |
| `E-classfield-reserved-aware` | `5.4.0 – 5.5.0` | `45ad03b8335bee095b17c0d29b0a78bff158c93a` | output + source | a field name matching `reservedNames` stays non-computed; unmatched names retain the computed-literal shape |

**This axis is a detection discriminator, which is why an "it throws" row earns a place.** A sample
containing a computed-literal class field key cannot have been produced below `2.18.0`, and the
rejection below it is not a decline that a sample could hide — nothing is emitted at all.

**`E-classfield-rejected`'s SHA names where the refusal was last observed, not a transformer.** The
row records a refusal rather than a shape, so no commit "proves" it the way the other rows are
proven; the SHA is `2.16.0`, the upper of the two versions actually run. Both failure modes were read
from real encoder runs, at `2.9.6` and `2.16.0`. The lower bound is unread — do not narrow it without
running one.

**The field boundary is at `5.4.0`.** It is the same reserved-name-aware transformer change that
opens the method row above, but the field position remains on this independent axis. Ignored member
expressions are unrelated: they belong to `E-propname-*`, not to a class field key.

### `E-objkeys-*` — object-keys extraction

From U4. `ObjectExpressionKeysTransformer`, gated on `transformObjectKeys`
([object-keys-extraction.md](transforms/object-keys-extraction.md)). **Every boundary on this axis
is in the prohibition set, and every one of them narrows it** — each era refuses strictly more
objects than the last, so the transform touches less of a sample as versions rise.

| Era | Version range | Commit SHA | Evidence | Shape signature — what changed at the lower bound |
|---|---|---|---|---|
| `E-objkeys-base` | `2.9.0 – 2.9.1` | `c7cc68bedb307775650728a2d0fa2c43137d93f9` | source | lower bound is the **read floor**, not a boundary. Prohibition set without the arrow-function case |
| `E-objkeys-arrow-prohibited` | `2.9.2 – 2.15.1` | `21c6fa803daa9f44de7d445fdf51730ffc20668c` | source | + a prohibited arrow-function expression is refused |
| `E-objkeys-this-aware` | `2.15.2 – 2.15.5` | `ac8b8c4b078411d941a86bbf1db1025d9d2d097d` | source | + `ThisExpression` joins the referenced-identifier scan, collected as `'this'` |
| `E-objkeys-call-prohibited` | `2.16.0 – 5.2.0` | `3848bca7941ed86d62e6a7108b960201613d2172` | output + source | + **any object containing a `CallExpression` or `NewExpression` is refused outright.** Output read through the spine and source-read above it |
| `E-objkeys-loopbody-prohibited` | `5.2.1 – 5.3.1` | `7792fb0be3ab36af2f3925c4e754b24a5a4008fa` | output + source | + an object below a non-block `for`, `for-in`, `for-of`, `while` or `do-while` body is refused, preventing extraction outside the loop |
| `E-objkeys-sequence-prohibited` | `5.4.0 – 5.5.0` | `45ad03b8335bee095b17c0d29b0a78bff158c93a` | output + source | + a direct object child at a non-first sequence position is refused; a nested object there is refused when an earlier expression contains a call or `new`, preserving evaluation order |

**Mechanical changes do not open rows.** Besides the phase-1 import and rename changes, `4.2.0` and
`5.2.0` are performance rewrites with equivalent predicates and extractor order, `4.2.1` is
formatting, and `5.4.3` is dependency-injection migration. The later behavioral changes are the
loop-body and sequence-position refusals above.

**`2.16.0` is a boundary on this axis and on `E-sa-scope-wrapper-*`, and that is a coincidence.**
The two were found by unrelated instruments — a prohibition-set diff here, real output there — and
per this file's own rule a coincidence between axes is prose, never a merged row.

**Three of the six rows remain source-only.** The boundaries are exhaustive over tags rather than
sampled, so they carry no interpolation; the call, loop-body and sequence-position prohibitions
have each been confirmed against emitted output.

**The call-prohibition row has been promoted, and the case that did it is the shape to copy for the
other five:** one source carrying both the prohibited shape and a control that differs in nothing else,
encoded at the versions bounding the era with every unrelated option off. The control is what makes
the reading a boundary rather than an observation — extraction stopping for *both* objects would
have meant something else changed, and the call-free object still being extracted at and above the
bound is what rules that out.

### `E-numexpr-*` — numbers as numerical expressions

From U4. `NumberToNumericalExpressionTransformer`, gated on `numbersToExpressions`
([literal-respelling.md](transforms/literal-respelling.md)).

| Era | Version range | Commit SHA | Evidence | Shape signature — what changed at the lower bound |
|---|---|---|---|---|
| `E-numexpr-integer-only` | `2.9.0 – 2.10.3` | `d996e1ae3af06775e057bd062a18c4337230566e` | **output** | lower bound is the **read floor**. A number is decomposed into an addition/subtraction/multiplication tree with three additional parts. A **non-integer keeps its decimal inside one of the terms** — `3.75` emits as `… + 2003.75`, so the tree carries a float literal. Read at `2.9.6` and `2.10.0` |
| `E-numexpr-float` | `2.10.4 – 5.5.0` | `45ad03b8335bee095b17c0d29b0a78bff158c93a` | output + source | + the value is split into integer and decimal parts first, and a non-integer is rebuilt from an integer tree plus its decimal remainder — `3.75` emits as an all-integer tree `+ 0.75`, with the remainder standing alone. Output read through the spine; source-read through the pin |

**`2.10.0` is not a boundary on this axis**, and it looks like one in a diff: the additional-parts
count moves from a private constant to a public default passed in by the caller. **The value is `3`
on both sides**, so the emitted expression is unchanged. Recorded so the diff is not re-read.

**`3.0.1` is also mechanical.** The factor test changes from remainder to
division/floor/subtraction for an Apple M1 performance fix; on the analyzer's safe integer domain it
selects the same sorted factor set and therefore the same possible multiplication subtrees.

**Both rows are now `output`, read from a built sample rather than from the corpus.** No corpus
input carries a non-integer numeric literal — the fixtures contain only `0 1 2 3 5 6` — so this is
the gap [corpus.md](corpus.md) says to close by building the shape at the versions bounding the era
rather than by appending an input, the axis being a single one. The sample carries an integer
alongside the float as its control: the integer's tree is the same shape in both eras, so the
difference is attributable to the float path and not to the decomposition changing generally.

### `E-template-*` — template literals to concatenation

From U4. `TemplateLiteralTransformer`, ungated
([string-construction.md](transforms/string-construction.md)).

| Era | Version range | Commit SHA | Evidence | Shape signature — what changed at the lower bound |
|---|---|---|---|---|
| `E-template-concat` | `2.9.0 – 2.11.0` | `05cd3bed61f19c44968be9b9b60331636f087c9a` | **output** | lower bound is the **read floor**. Quasis and expressions interleave into a left-leaning `+` chain; empty quasis are dropped; a leading `''` is prepended when neither of the first two nodes is a string literal, so `+` stays concatenation. Tagged templates are left alone. Read at `2.9.6` and `2.10.0`: no template literal survives and a `+` chain stands where it was |
| `E-template-skip-uncooked-shift` | `2.11.1 – 5.1.0` | `6866396e9a74dd1d5d8c38f169a40889802907da` | source, **and unreachable in output** | + a quasi whose `cooked` is `null`/`undefined` is skipped without consuming the queued expression, so a later cooked quasi takes it. **The subject cannot be built**: an invalid escape is rejected untagged and legal only tagged, which returns before conversion |
| `E-template-skip-uncooked-indexed` | `5.2.0 – 5.5.0` | `45ad03b8335bee095b17c0d29b0a78bff158c93a` | source, **and unreachable in output** | the skip is now index-paired, so the corresponding expression is skipped too. Valid templates emit the same concatenation as before; only a synthetic invalid untagged AST distinguishes the rows |

**The first row is `output` and the two uncooked rows cannot be.** No corpus input contains a template
literal, so the reading comes from a built sample. The later rows' subject is unreachable rather
than merely unbuilt, which is a different finding: **before filing an axis as uncovered, check
whether the shape can exist at all** — the same correction this package already made once, where a
census axis recorded as a corpus gap turned out to be impossible by construction.

### `E-boolean-*`, `E-numhex-*`, `E-splitstring-*` — one era each, and the rows exist to say so

From U4. `BooleanLiteralTransformer` and `NumberLiteralTransformer`, both ungated
([literal-respelling.md](transforms/literal-respelling.md)), and `SplitStringTransformer`, gated on
`splitStrings` ([string-construction.md](transforms/string-construction.md)). Both docs already
stated that these hold still across phase 1; **the rows are what make that citable** — any
table naming an era has to resolve to one, and "no axis" is the spelling reserved for a component
nobody has read.

| Era | Version range | Commit SHA | Evidence | Shape signature — what changed at the lower bound |
|---|---|---|---|---|
| `E-boolean-double-negation-array` | `1.12.0 – 4.2.0` | `314855eb8bb65653b8c292e7a65ffcdc6c39761b` | **output** | `true` → `!![]`, `false` → `![]`, on every boolean including the guards `ControlFlowFlattening` and `DeadCodeInjection` injected earlier. The focused adjacent-boundary disguise census is byte-identical, proving `4.2.0` is the high endpoint rather than a successor boundary |
| `E-numhex-raw-only` | `1.12.0 – 4.2.0` | `314855eb8bb65653b8c292e7a65ffcdc6c39761b` | **output** | `1` → `0x1`: the literal's `raw` is rewritten and its `value` left alone, so this transformer changes no AST node. Two content changes in range, `2.11.1` and `2.14.0`, are TypeScript-only. The focused adjacent-boundary hexadecimal-literal census is byte-identical, proving `4.2.0` is still inside the row rather than its successor boundary |
| `E-splitstring-two-pass` | `2.6.2 – 4.2.0` | `314855eb8bb65653b8c292e7a65ffcdc6c39761b` | **output** | a first pass at a fixed 1000-character chunk, then a second at `splitStringsChunkLength`, emitted as a left-leaning `+` chain. The focused adjacent-boundary concatenation census is byte-identical, proving `4.2.0` remains inside this row |

### `E-boolean-heritage-*` — boolean class heritage

The general boolean spelling above is independent of this contextual guard. A boolean used as a
class `superClass` follows its own axis because the 5.4.4 fix refuses the literal rewrite there,
preserving the source boolean for the parser and runtime to reject as non-constructible.

| Era | Version range | Commit SHA | Evidence | Shape signature — what changed at the lower bound |
|---|---|---|---|---|
| `E-boolean-heritage-rewritten` | `~ – 5.4.3` | `a4ed35565af643c00fdf32d65cb50fd9a9674927` | **output** | a boolean superclass is rewritten as `!![]` or `![]`, yielding malformed `extends!![]` or `extends![]` output; the lower bound is unread |
| `E-boolean-heritage-preserved` | `5.4.4 – 5.5.0` | `c6d0872a631ed290d29fce6551fbfceb6c31577d` | output + source | the boolean superclass is excluded from literal rewriting, so `true`/`false` are retained in the emitted class heritage; ordinary `extends Base` and `extends null` controls are unchanged |

Focused `5.4.3`/`5.4.4` class-heritage cases supply the accepted output evidence.

**The three content changes inside phase 1's range are all mechanical, and the third had to be
measured rather than read.** `2.13.0` swaps the `estraverse` import for the vendored fork — the
same edit `E-cff-storage-object` already records at that release. `2.14.0` adds a TypeScript
`override` modifier. `2.19.0` is the one that reads like a boundary and is not:

- the `splitStrings` check moves from inside the visitor to `getVisitor`, which changes when the
  option is consulted and not what an enabled run emits;
- `parentizeNode`/`parentizeAst` move from the per-chunk helper to one call on the finished node,
  which is parent metadata rather than emitted shape;
- **the second pass drops a `parentNode &&` guard**, and reading that alone predicts a real shape
  change: when the first pass leaves a short string untouched, the literal *is* the traversal root,
  whose parent looks null — so a string under 1000 characters would go unsplit below `2.19.0` and
  split at it. **Built and run at five columns, that prediction is false**: a 16-character string
  emits `'abcd'+'efgh'+'ijkl'+'mnop'` identically at `2.18.1` and `2.19.0`. `estraverse.replace`
  hands the root a sentinel holder rather than `null`, so the guard was satisfied all along.

**Worth keeping because the near-miss is the lesson, not the result.** A guard removal is the most
plausible-looking shape change a diff can contain, and the classification that would have opened an
era here was one sample away from being written down. Both bounds above `2.19.0` are the next
content change and are **unclassified**, so neither row extends past `4.2.0` on evidence.

### `E-cff-block-*` — the flattened block's dispatch

From U5. `BlockStatementControlFlowTransformer` and its custom node, gated on
`controlFlowFlattening` ([control-flow-block-flattening.md](transforms/control-flow-block-flattening.md)).

| Era | Version range | Commit SHA | Evidence | Shape signature — what changed at the lower bound |
|---|---|---|---|---|
| `E-cff-block-switch-dispatch` | `1.8.1 – 4.2.0` | `314855eb8bb65653b8c292e7a65ffcdc6c39761b` | **output** | a controller string of `\|`-joined case indexes, `split` into an array; an index initialised to `0`; a `while (true)` whose body is a `switch` on `controller[index++]` followed by a `break`. Case tests are `String(i)` in ascending order, consequents are `[statement, continue]` or a lone `return`. The focused adjacent-boundary dispatch census is byte-identical, proving the high endpoint remains this form |

**Below `1.8.1` there are further rows nobody has read**, not an absence of shape — the file exists
back to `0.9.0` and its content moves twelve times before this era begins.

**The transformer's own content moves once inside phase 1, at `2.13.0`, and it is not a boundary**:
the change is the `estraverse` import path moving to the `@javascript-obfuscator` scope. The
prohibition set, the size gate and the emitted structure are untouched.

### `E-cff-storage-*` — the expression storage object and its call sites

From U5. `FunctionControlFlowTransformer`, its four replacers, and every custom node they emit
except the call wrapper, which has its own axis
([control-flow-expression-storage.md](transforms/control-flow-expression-storage.md)).

| Era | Version range | Commit SHA | Evidence | Shape signature — what changed at the lower bound |
|---|---|---|---|---|
| `E-cff-storage-object` | `2.9.6 – 3.1.0` | `314855eb8bb65653b8c292e7a65ffcdc6c39761b` | **output** | lower bound is the **read floor**, not a boundary. A `const` object of wrapper functions keyed by 5-character random names, prepended to a host **function body** — never the `Program`, never a bare block; call sites `S.k(a, b)`, `S.k(callee, …args)` and `S.k`. Read in output at every full corpus column through `3.1.0` |
| `E-cff-storage-stringarray-shared` | `3.2.0 – 3.2.2` | `77f64bf5df0e943ac2f9c035577e0e44a9f5f3e4` | output + source | a second consumer at the `StringArray` stage stores numeric string-array call indexes under identifier keys. One inherited storage can serve nested hosts: the focused upstream fixture emits one four-entry object shared by the outer IIFE and its nested function |
| `E-cff-storage-stringarray-per-host` | `3.2.3 – 5.5.0` | `ec4b70f908da47c75dc7ce4d23667d41a01c76b5` | output + source | traversal skips an existing storage instead of stopping and each host requests a fresh storage. The focused nested-host census distinguishes one shared storage from one fresh storage per host |

**One row, not three, and the two content changes inside it were classified rather than counted.**
The transformer's own content moves at `2.13.0` — an `estraverse` import path — and at `2.19.0`,
where removing a host's existing storage node changes from shifting off the host's first statement
to looking up the recorded node with a type guard, and the storage custom node comes to be
constructed twice per host. Neither moves an emitted shape: no input has been found where the two
removals disagree, and both constructions are deterministic functions of the same storage. What
would falsify the first is a host whose first statement is not the storage node when a second
function selects it; until something produces one, splitting the row would open an era that does
not exist.

**The storage-side custom nodes hold still `0.25.0 – 3.1.0`** — the storage node itself, the three
call-site nodes, the binary and logical wrappers, and the string-literal entry. The row's read floor
is `2.9.6` because that is where the *transformer* was read; below it the transformer's content
moves at `1.12.0` and is unclassified.

**The boundary that changes this shape most is not on this axis at all.** Object-keys extraction
destroys the storage object into `S = {}` plus one assignment per property, and stops doing so for
any storage containing a call wrapper at `E-objkeys-call-prohibited`. That is an `E-objkeys-*`
boundary with no structural footprint in this stage's directories, and it is the reason this
component has two shapes in output that neither row above names.

### `E-cff-callee-*` — the call-expression wrapper

From U5. `CallExpressionFunctionNode`. Its two phase-1 spread changes are followed at `4.2.0` by a
separate optional-call semantic boundary.

| Era | Version range | Commit SHA | Evidence | Shape signature — what changed at the lower bound |
|---|---|---|---|---|
| `E-cff-callee-positional` | `0.25.0 – 2.10.4` | `86fe1df40c8a391f909375cb7ebec552fea781fa` | **output** | lower bound is the **read floor**. `function (callee, param1 … paramN) { return callee(param1 … paramN) }`, one parameter per argument. A spread argument binds to one positional parameter, so the wrapper receives only its first element — **and this era is therefore not semantics-preserving**, see below. Output read at `2.9.6` and `2.10.0`; SHA is `2.10.0`'s |
| `E-cff-callee-spread` | `2.10.5 – 2.12.0` | `36ea9c08f3244533b466b3031824da6493aa2d4e` | **output** | + a spread argument becomes a `RestElement` parameter and a `SpreadElement` in the inner call. A spread in a non-final position still emits parameters after the rest element, and **the emitted program does not parse** — `Rest element must be last element`. Output read at `2.11.1` and `2.12.0` |
| `E-cff-callee-spread-truncating` | `2.13.0 – 4.1.1` | `314855eb8bb65653b8c292e7a65ffcdc6c39761b` | **output** | + the loop stops at the first spread argument, so the rest parameter absorbs the remainder and the parameter list is valid. Output read at `2.15.3` and `2.19.0` |
| `E-cff-callee-optional-wrapper` | `4.2.0 – 5.5.0` | `01465a233c977c45d2f238806a95a06387cc7a39` | output + source | + when an optional wrapper is constructed, it returns `callee?.(…)` inside a chain rather than the ordinary `callee(…)`. A single null-callee discriminator returns `undefined`; `4.1.1` wrongly throws. Ordinary calls retain the spread-truncating parameter algorithm. This row describes the wrapper body, not reuse correctness: until `5.4.3`, same-arity ordinary and optional calls can share the wrong cached wrapper |

Wrapper construction and wrapper **reuse** are independent axes. Once optional wrappers exist, the
cache key determines whether the right body is selected:

| Era | Version range | Commit SHA | Evidence | Shape signature — what changed at the lower bound |
|---|---|---|---|---|
| `E-cff-callee-reuse-arity` | `4.2.0 – 5.4.2` | `01465a233c977c45d2f238806a95a06387cc7a39` | output + source | wrapper reuse is keyed only by argument count. Mixed same-arity ordinary and optional calls can therefore share whichever body is encountered first; a plain-first null-callee discriminator loses the optional short circuit and throws |
| `E-cff-callee-reuse-kind` | `5.4.3 – 5.4.4` | `a4ed35565af643c00fdf32d65cb50fd9a9674927` | output + source | + the reuse key includes `optional` or `standard`, so mixed same-arity traffic keeps separate wrapper entries; spread and plain calls of the same argument count can still collide |
| `E-cff-callee-reuse-shape-kind` | `5.4.5 – 5.5.0` | `a3df841839d4549ea521cf3e5dbbb01d67b0f5dc` | output + source | + the key records each argument position as plain or spread as well as optional/standard kind. Both encounter orders keep separate wrappers; below the boundary, plain-first reuse can discard spread elements and change the result |

**No corpus input passes a spread argument, so all three rows were entered from purpose-built
encodes rather than from the corpus** — `f(...a)` separates the first era from the other two,
`f(...a, b)` separates the second from the third, and each was built at both ends of its range
(2026-08-14).

The ordinary `5.4.2`/`5.4.3` columns contain call-wrapper storage but no optional calls, so their
byte-identical comparison is a negative population control rather than boundary evidence. The
focused same-arity census supplies both encounter orders, different-arity and single-kind controls;
it observes old-side reuse and the plain-first runtime harm, then separate high-side entries.

At `5.4.5`, the same method is widened to spread/plain shape. The focused adjacent-release census
observes both old encounter orders, the plain-first argument-loss outcome, high-side separation,
and different-length/single-kind controls.

**Two of the three eras emit output that is wrong rather than merely differently shaped**, which is
unusual on this axis and worth stating plainly:

- `E-cff-callee-positional` **changes what the program computes.** A source summing
  `sink(...[1,2,3])` returns `6`; the obfuscated program returns `1`, at both `2.9.6` and `2.10.0`.
  Every argument after the first is silently discarded.
- `E-cff-callee-spread` **emits a program that cannot be parsed at all** when the spread is not
  last. Such a sample could never have run, which bounds how much of it can exist in the wild.
- `E-cff-callee-optional-wrapper` is the first row on this axis able to retain a source optional
  call's null-short-circuit semantics. Babel exposes its stored return as `OptionalCallExpression`;
  a separate `5.4.3` reuse-key change prevents an ordinary same-arity wrapper from being selected.

### `E-generator-*` — dependency-driven printing boundaries

The printer is part of emitted syntax even though it is a pinned dependency rather than a
transformer. `@javascript-obfuscator/escodegen`'s NoIn handling has its own axis:

| Era | Version range | Commit SHA | Evidence | Shape signature — what changed at the lower bound |
|---|---|---|---|---|
| `E-generator-arrow-noin-unparenthesized` | `~ – 5.4.4` | `c6d0872a631ed290d29fce6551fbfceb6c31577d` | **output** | a concise arrow body containing `in`, when the arrow is the initializer of a `for`, loses the parentheses required by the surrounding NoIn grammar and the emitted program does not parse. The lower bound is unread |
| `E-generator-arrow-noin-parentheses` | `5.4.5 – 5.5.0` | `a3df841839d4549ea521cf3e5dbbb01d67b0f5dc` | output + source | escodegen 2.4.2 passes the NoIn flag into the arrow body and retains parentheses. The exact upstream fixture parses and loads; block-bodied, outside-`for` and non-`in` controls remain valid on both sides |
| `E-generator-keyword-compact-gap` | `~ – 5.4.0` | `84861e8e397179d6597195626fe6783757eee3e0` | **output** | under compact generation, `return`, `throw` and `typeof` can run into a following non-BMP identifier, changing the tokenization of the emitted program. The lower bound is unread |
| `E-generator-keyword-spacing` | `5.4.1 – 5.5.0` | `dd62feadaea6de64eb743eea6ea475949f1c4974` | output + source | escodegen 2.4.1 preserves the required separator after those keywords; the focused 5.4.0/5.4.1 fixtures populate the old and fixed forms. Source at the 5.5.0 pin uses escodegen 2.4.2; no ordinary 5.5.0 keyword census is claimed |

### `E-parser-ecma-*` — parser acceptance and syntax level

The parser's `ecmaVersion` is an encoder acceptance boundary, not a transform shape. The focused
RegExp-modifier inputs at the adjacent tags establish the emitted/accepted distinction; the source
value at the pin establishes persistence of the high syntax level. This axis does not claim support
in any particular runtime engine.

| Era | Version range | Commit SHA | Evidence | Shape signature — what changed at the lower bound |
|---|---|---|---|---|
| `E-parser-ecma13-regexp-modifiers-rejected` | `~ – 5.4.3` | `a4ed35565af643c00fdf32d65cb50fd9a9674927` | source, **and unreachable in output** | `ecmaVersion` 13 rejects ES2025 RegExp inline modifiers during encoder acceptance; no emitted artifact exists for those inputs |
| `E-parser-ecma2026-regexp-modifiers-accepted` | `5.4.4 – 5.5.0` | `c6d0872a631ed290d29fce6551fbfceb6c31577d` | output + source | `ecmaVersion` 2026 accepts the inline-modifier forms and preserves their raw pattern/flags in the emitted artifact; the value remains 2026 at the pin |

Focused `5.4.3`/`5.4.4` RegExp-modifier cases pin the exact acceptance/rejection and emitted-output
distinction. Node execution was checked for those fixtures only; it does not establish cross-engine
compatibility.

### `E-domainlock-*` — normalized domain-list casing

Domain lock is an option-normalization boundary rather than a new helper template. The normalizer
extracts each configured domain and, from 5.4.1, lowercases the extracted value before the helper
is generated. The domain-lock focused report exercises mixed case, leading-dot, URL-like,
subdomain and multiple-domain forms in a browser-like harness; it does not claim a browser engine
or platform matrix.

| Era | Version range | Commit SHA | Evidence | Shape signature — what changed at the lower bound |
|---|---|---|---|---|
| `E-domainlock-case-preserved` | `~ – 5.4.0` | `84861e8e397179d6597195626fe6783757eee3e0` | **output** | extracted domain strings retain their source casing in the emitted domain guard; the lower bound is unread |
| `E-domainlock-lowercase` | `5.4.1 – 5.5.0` | `dd62feadaea6de64eb743eea6ea475949f1c4974` | output + source | `DomainLockRule` applies `.toLowerCase()` after `Utils.extractDomainFrom`; the focused 5.4.0/5.4.1 output establishes the boundary, and the normalizer remains unchanged at the pin |

Focused `5.4.0`/`5.4.1` cases supply the exact output and normalization evidence. The browser-like
harness is an explicit test harness, not a browser-platform claim.

### `E-dci-host-*` — where the injected clone's host node is unwrapped

From U6. `DeadCodeInjectionTransformer`, gated on `deadCodeInjection`
([dead-code-injection.md](transforms/dead-code-injection.md)). **The axis is not either file's
content** — both hold still across the whole of phase 1 apart from an `estraverse` import path at
`2.13.0` and an `override` keyword at `2.14.0`, neither of which is a boundary. What moves is the
*stage* the transform's second visit runs in, and it moves twice across the 205 release tags,
swept per tag with no interpolation.

| Era | Version range | Commit SHA | Evidence | Shape signature — what changed at the lower bound |
|---|---|---|---|---|
| `E-dci-host-finalizing` | `0.26.0 – 2.15.2` | `b26692ae0455bba82e7b20cff193f71d4002a8d5` | **output** | lower bound is where the file first exists. The restore runs at `Finalizing` (10), after two stages that rebuild nodes, and the host's identity check can therefore miss — leaving **a zero-reference function declaration holding the clone**, nested inside the wrapped block, on the branch the test does not take. Output read at `2.15.2`; SHA is `2.15.2`'s |
| `E-dci-host-renameidents` | `2.15.3 – 3.1.0` | `993cf7a2a850365baf105e54a09a761724d47da9` | **output** | + the restore moves to `RenameIdentifiers` (7), ahead of those stages, and no host survives: same fixture and same seed emits the clone's statements directly, with the function declaration gone. Output read at `2.15.3`, `2.15.4`, `2.16.0`, `2.18.1` and `2.19.0` |
| `E-dci-host-stringarray` | `3.2.0 – 5.5.0` | `711a1353341f4dcea4a1b0c972735545e48a8f11` | **source** | + the restore moves again, to `StringArray` (8). Full columns now exist on both sides, but the isolated `dead-code` cells are byte-identical and the changed high-option cells share the pipeline-order boundary with other axes, so no emitted consequence is attributable to this host move yet |

**The `2.15.2` column was appended to settle the first boundary**, and holds only the `dead-code`
set — nothing else straddles it, since the next column down is `2.12.0`. The two columns agree on
every other emitted detail of that cell, including identifier names, which is what makes the two
surviving function declarations attributable to this change rather than to four intervening
releases.

**The leak is emitted-shape only, not semantic.** The surviving host is unreferenced and sits on
the dead path, so both eras run identically; this axis records a difference in what is *written*,
which is what an era is for.

### `E-selfdef-*` — the self-defending callback's body

From U7. `SelfDefendingCodeHelperGroup`, gated on `selfDefending`
([custom-code-helpers.md](transforms/custom-code-helpers.md)). Boundary extraction checks file
presence separately from content so an absent template cannot be mistaken for an empty era.

| Era | Version range | Commit SHA | Evidence | Shape signature — what changed at the lower bound |
|---|---|---|---|---|
| `E-selfdef-regexp` | `1.2.1 – 2.18.1` | `18f5210871a6574f256938d4ad56e2ac19ac8884` | **output** | the callback declares a **nested** function that builds a `RegExp` through `constructor` and returns the negated `test`, then calls it. A second template of the same shape serves `browser-no-eval` using `new that.RegExp`. Output read at `2.9.6`, `2.10.0`, `2.11.1`, `2.12.0`, `2.15.3`, `2.15.4`, `2.16.0` and `2.18.1` |
| `E-selfdef-search` | `2.19.0 – 5.4.4` | `314855eb8bb65653b8c292e7a65ffcdc6c39761b` | **output** | + the nested function is gone: the callback is a single `return` of a member-call chain built from `toString().search(…)`, and the no-eval template is deleted rather than rewritten. The helper class is renamed in the same release, which is *not* what the boundary is keyed on. Output read at `2.19.0` |
| `E-selfdef-search-newline-bail` | `5.4.5 – 5.5.0` | `a3df841839d4549ea521cf3e5dbbb01d67b0f5dc` | output + source | + an early `return` guard ahead of the chain: if the function's own `bind().toString()` contains a newline the callback bails out instead of proceeding. The focused adjacent-release census emits the predicate across raw and beautified forms; an exact upstream reserialization simulation times out below the boundary and completes above it. Actual Bun/JavaScriptCore timing remains unmeasured |

**Below `1.2.1` the template changes repeatedly** — fourteen further content changes down to
`0.6.0`, across a rename from `custom-nodes/self-defending-nodes/` — and none of them has been
read. They are below the studied read range and get no rows rather than a hull.

### `E-helper-global-*`, `E-dbgprot-*`, `E-consoleout-*`, `E-callsctl-*` — the function is stable; its interval is not

From U7, same sweep and same method. The debug-protection function, console-output callback and
calls controller each retain one shape across the studied range. The global-variable prelude is a
separate target-selected component: its original three shapes remain stable, while `4.1.0` adds a
service-worker arm. The optional interval is another separate emitted piece and moves at `4.0.0`;
keeping it inside the function row previously hid a reachable boundary that the `4.1.1` runtime
control exposed.

| Era | Version range | Commit SHA | Evidence | Shape signature |
|---|---|---|---|---|
| `E-dbgprot-recursive-counter` | `0.25.0 – 5.5.0` | `314855eb8bb65653b8c292e7a65ffcdc6c39761b` | **output** | a `{dp}(ret)` function declaration wrapping a recursive `debuggerProtection(counter)` inside a `try`/`catch`, plus a call form routed through the calls controller. Output read at every phase-1 corpus column and at `4.1.1` |
| `E-dbgprot-interval-global-call` | `0.25.0 – 3.2.7` | `77f64bf5df0e943ac2f9c035577e0e44a9f5f3e4` | output + source | a fixed global call, `setInterval(function () { dp(); }, 4000)`. Output read through `3.2.2`; the upper bound is source-read |
| `E-dbgprot-interval-global-member` | `4.0.0 – 5.5.0` | `828a190cf80a86227ef77be38e99aad9838aed70` | output + source | the option becomes milliseconds and the interval moves inside a global-resolver IIFE as `that.setInterval(dp, milliseconds)`. Source opens at `4.0.0`; the focused interval census at `4.1.1` emits the member form. The resolver prelude varies by target as recorded below |
| `E-helper-global-default` | `2.9.6 – 4.0.1` | `314855eb8bb65653b8c292e7a65ffcdc6c39761b` | **source** | lower bound is the read floor, not a boundary. Ordinary targets randomly select either a `let that` plus `try`/`catch` resolver or a `getGlobal` function-expression resolver; `browser-no-eval` selects a `typeof window`/`process`/`require`/`global` conditional. The formatter may rewrite their declarations to `var` for a `var` host |
| `E-helper-global-serviceworker` | `4.1.0 – 5.5.0` | `1000402f10f61bd367cd971d55f0f832d940d60e` | output + source | + the new `service-worker` target selects `const that = typeof global === 'object' ? global : this;`. The ordinary and `browser-no-eval` arms persist unchanged; focused output at `4.1.0` and `4.1.1` populates the added arm in both reachable consumers |
| `E-consoleout-bound-stubs` | `1.10.0 – 5.5.0` | `314855eb8bb65653b8c292e7a65ffcdc6c39761b` | **output** | a callback that opens with a global-object prelude and rebinds seven `console` methods to a bound stand-in carrying the original's `toString`. Output read at every phase-1 corpus column |
| `E-callsctl-firstcall` | `0.25.0 – 5.5.0` | `314855eb8bb65653b8c292e7a65ffcdc6c39761b` | **output** | a `firstCall` IIFE returning a wrapper that invokes its target once and nulls it. Output read at every phase-1 corpus column |

**The filename is part of the subject.** `DebugProtectionFunctionTemplate` itself has only
node-neutral content changes at `4.0.0` and `4.2.1`, so its recursive-counter row remains one era.
But `DebugProtectionFunctionIntervalTemplate` changes at the first of those releases: boolean to
milliseconds, global call to resolved-global member call, and callback wrapper to direct function
argument. A sweep of only the defining-function template correctly says that function is stable
and incorrectly says the whole helper group is stable.

## How a row is added or moved

- A row's **SHA is the commit its claims were verified against**, not whatever the submodule
  is checked out at. It moves only when someone re-reads that era, never when the pin moves.
- **Two SHAs in one row** means both ends of the range were read and agree; the middle is
  still `~`.
- Narrowing a `~` span is a new reading, not a new row — read a tag inside the span and either
  the span narrows or the row splits.
- A removed shape keeps its row. A row points into submodule history, so an era whose source
  the current checkout no longer contains stays fully describable.
- **A row never spans axes.** A `P-*` boundary does not open, move or close an `E-` row, and
  one component's `E-` boundary does nothing to another's. Each axis is read on its own
  evidence, and a coincidence between two of them is a finding written in prose, never a
  merged row.
