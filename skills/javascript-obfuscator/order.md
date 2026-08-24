# Stage Order

How the transformer execution order is assembled, and how it has changed. Split out of
[javascript-obfuscator.md](javascript-obfuscator.md), which keeps the pipeline a reader needs to
follow the rest of the package — the ten stages, what each is for, and the execution flow. This
page is the derivation behind that: three assembly mechanisms across the encoder's history, the
level structure per tag, and the reproduction recipe.

**The order is infrastructure, not the subject.** What this package exists to describe is what
the obfuscator *emits*, transform by transform. The order matters because it decides what each
transform's input already looks like, and because it moves — but a reader chasing a particular
emitted shape wants that transform's doc, not this page.

**This page keys everything on tags, never on era IDs, and that is deliberate.** An era is a
maximal version range over which the order is identical, so the era list is *derived from* what
is measured here — the era registry reads this page, not the other way round. Keying these
tables on era IDs would make the two mutually defining, and neither readable first.

The readings behind it are **exhaustive, not sampled**: the order was derived at all 184 release
tags at or above `0.9.0`, so a range stated here is a real release range and the versions inside
it were read, not assumed.

## Two Transformer Kinds

| kind | operates on | stages | list |
|---|---|---|---|
| **code transformers** | the source **text**, before parse and after generate | `PreparingTransformers`, `FinalizingTransformers` | [`codeTransformersList`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/45ad03b8335bee095b17c0d29b0a78bff158c93a/src/JavaScriptObfuscator.ts#L59) — hashbang handling only |
| **node transformers** | the ESTree AST | the ten node stages below | [`nodeTransformersList`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/45ad03b8335bee095b17c0d29b0a78bff158c93a/src/JavaScriptObfuscator.ts#L64-L100) |

Everything that shapes the output is a node transformer, and the rest of this page is about
how their order is assembled.

## How the order is assembled

### The flat list is not the order

`nodeTransformersList` is the first thing a reader finds and it is **alphabetical-ish
registration order, not execution order**. Nothing runs in that sequence, and a transformer's
position in it means nothing. The effective order is built in three steps, and the second and
third are the ones that drift.

1. **The stage sequence** — a fixed sequence of `NodeTransformationStage` values, some of them
   gated on an option
   ([`transformAstTree`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/45ad03b8335bee095b17c0d29b0a78bff158c93a/src/JavaScriptObfuscator.ts#L214-L252)).
2. **Per stage, a filter** — every transformer whose `getVisitor(stage)` returns non-null is in;
   everything else is not merely inert, it is **absent from the graph in step 3**
   ([`buildNormalizedNodeTransformers`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/45ad03b8335bee095b17c0d29b0a78bff158c93a/src/node-transformers/NodeTransformersRunner.ts#L181-L200)).
3. **Per stage, a levelled topological sort** over the surviving set's declared `runAfter`
   dependencies
   ([`build`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/45ad03b8335bee095b17c0d29b0a78bff158c93a/src/utils/AbstractTransformerNamesGroupsBuilder.ts#L52-L64),
   [`sortByGroups`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/45ad03b8335bee095b17c0d29b0a78bff158c93a/src/utils/LevelledTopologicalSorter.ts#L59-L75)).
   Each level costs its own pass over the tree — see "What a level is at runtime" below for
   what that means for any single transformer
   ([`transform`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/45ad03b8335bee095b17c0d29b0a78bff158c93a/src/node-transformers/NodeTransformersRunner.ts#L67-L108)).

So the order can move without a single line of `nodeTransformersList` changing, and without a
CHANGELOG entry: **one transformer editing its own `runAfter`, or its own `getVisitor` gaining
or losing a stage, reorders the pipeline.** That is why the order is read per tag rather than
derived once and reused.

### `runAfter` is resolved against the stage, not the project

[`buildTransformersRelationEdges`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/45ad03b8335bee095b17c0d29b0a78bff158c93a/src/utils/AbstractTransformerNamesGroupsBuilder.ts#L71-L101)
drops any `runAfter` naming a transformer that step 2 filtered out — the dependency is treated
as satisfied, and the dependent becomes a root. It does not fail, and it does not warn.

The consequence is that **the level structure is option-dependent, not just version-dependent.**
Measured at `5.5.0`, `StringArray` stage:

| options | levels |
|---|---|
| rotate + wrappers + calls-transform all on | `[DeadCodeInjection, StringArrayRotateFunction]` · `[StringArray, StringArrayScopeCallsWrapper]` · `[StringArrayControlFlow]` |
| `stringArrayRotate` off | `[DeadCodeInjection, StringArray, StringArrayScopeCallsWrapper]` · `[StringArrayControlFlow]` |
| `stringArrayWrappersCount` 0 | `[DeadCodeInjection, StringArrayRotateFunction]` · `[StringArray]` · `[StringArrayControlFlow]` |
| `stringArrayCallsTransform` off | `[DeadCodeInjection, StringArrayRotateFunction]` · `[StringArrayScopeCallsWrapper, StringArray]` |
| all three off | `[DeadCodeInjection, StringArray]` |

Turning rotate off does not only remove the rotate function. It **collapses a traversal
boundary**: `StringArrayTransformer` and `StringArrayScopeCallsWrapperTransformer` stop being
separated by a full tree walk and start running interleaved on each node in one.

**The all-on profile is generative, and that is the only sense in which the others are a
subset.** Every row above is the top row's graph with the gated nodes deleted and the sort
re-run — derive once at all-options-on, record the gating set below, and any other profile
follows without re-deriving the era. What does *not* follow is the emitted shape: a level
boundary that collapses changes what each survivor sees at its input, so **a shape observed
with one option disabled is not evidence about the same shape with it enabled.** Structure is
derivable; output is not.

The transformers that gate `getVisitor` on an option at `5.5.0`, and therefore move the levels:
`BlockStatementControlFlowTransformer` and `FunctionControlFlowTransformer`
(`controlFlowFlattening`), `StringArrayRotateFunctionTransformer` (`stringArrayRotate`),
`StringArrayScopeCallsWrapperTransformer` (`stringArrayWrappersCount`),
`StringArrayControlFlowTransformer` (`stringArrayCallsTransform`),
`ObjectExpressionKeysTransformer` (`transformObjectKeys`),
`NumberToNumericalExpressionTransformer` (`numbersToExpressions`), `SplitStringTransformer`
(`splitStrings`).

## What a level is at runtime

A **level** is one pass over the AST, and it is the unit that decides what any transformer can
see. `NodeTransformersRunner.transform` loops over the groups `sortByGroups` produced and issues
**one `estraverse.replace` per group**, with that group's visitors merged into a single `enter`
and a single `leave` by
[`mergeVisitorsForDirection`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/45ad03b8335bee095b17c0d29b0a78bff158c93a/src/node-transformers/NodeTransformersRunner.ts#L207-L238).

**Within a level, transformers are interleaved at node granularity — not batched at tree
granularity.** At each node the merged function:

1. checks `NodeMetadata.isIgnoredNode(node)` and returns `VisitorOption.Skip` if set, which
   drops the **entire subtree for every visitor in the level at once**. This is how injected
   helper code is protected from re-obfuscation by the stages that follow it;
2. otherwise calls each of the level's visitors **in list order** on that same node;
3. assigns `node = visitorResult` after each one, but only when the result is a valid node — a
   visitor returning nothing leaves the node untouched for the next.

Four consequences, and the third is the one that misleads readers:

- **Order inside a level is significant**, so `[Parentification, RenameProperties]` is a
  different claim from the reverse. A level is an ordered list, never a set. **It is not the
  filtered `nodeTransformersList` order** — see the next section for what it actually is.
- **`enter` and `leave` are merged separately.** A transformer contributing only `leave` does
  nothing on the descent, so a level describes two interleavings, not one.
- **A level-mate sees a half-transformed tree.** Nodes already visited have had *all* the
  level's visitors applied; nodes not yet visited have had *none*. A **level boundary** is the
  only place that guarantee changes: at level 2, level 1 is complete over the whole program.
  That is exactly what `runAfter` buys, and the only reason to spend another traversal.
- **A level is *at most* one traversal.** `canRunOnProgramNodeOnly` lets a group whose visitors
  only touch the `Program` node run without walking at all.

### Within-level order is first-mention order, and a `runAfter` array leaks into it

The order inside a level is the sorter's **graph insertion order**, which is not the transformer
list order and is not stable under deleting an unrelated transformer. Three source facts
compose into it:

1. [`findRootNodes`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/45ad03b8335bee095b17c0d29b0a78bff158c93a/src/utils/LevelledTopologicalSorter.ts#L107-L116)
   emits each level by iterating `Array.from(this.graph.keys())` — **`Map` insertion order**,
   nothing else.
2. [`link`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/45ad03b8335bee095b17c0d29b0a78bff158c93a/src/utils/LevelledTopologicalSorter.ts#L154-L163)
   registers the **precedent before the consequent**, so a node enters the map the first time it
   is *mentioned* in any edge, not when its own turn comes.
3. [`buildTransformersRelationEdges`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/45ad03b8335bee095b17c0d29b0a78bff158c93a/src/utils/AbstractTransformerNamesGroupsBuilder.ts#L71-L101)
   emits edges walking the filtered transformers in list order, and for each one walks its
   `runAfter` **in the order that array is written**.

So a transformer's `runAfter` array — which reads like an unordered set of constraints — decides
the registration order of the transformers it names, and therefore their order inside a level
**it is not itself in**.

Rows 1 and 4 of the option table above are the worked instance. `StringArrayControlFlowTransformer`
declares `runAfter = [StringArray, StringArrayRotateFunction, StringArrayScopeCallsWrapper]`
([source](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/45ad03b8335bee095b17c0d29b0a78bff158c93a/src/node-transformers/control-flow-transformers/StringArrayControlFlowTransformer.ts#L32-L36)),
and in `nodeTransformersList` it precedes all three. With `stringArrayCallsTransform` **on**, it
is processed first and registers `StringArrayTransformer` ahead of
`StringArrayScopeCallsWrapperTransformer` — giving level 2 as `[StringArray,
StringArrayScopeCallsWrapper]`. With it **off**, no edge mentions either early, registration
falls back to list order, and `StringArrayScopeCallsWrapperTransformer` (listed before
`StringArrayTransformer`) comes first: `[StringArrayScopeCallsWrapper, StringArray]`.

**Deleting a transformer can therefore reorder two survivors that share a level**, without
changing any level count or any edge between them. Two consequences:

- A level's contents may be read off the graph, but its **order** must be replayed with the
  registration rule, not sorted by list position.
- An era's level structure holding still does not mean two versions run their survivors in the
  same order. Any claim that one profile or version is "the other minus a pass" has to check
  within-level order explicitly, because this is the axis on which it silently fails.

### Sharing a walk is the old behaviour; separating is the new one

Before the levelled sort arrives at `0.19.3` a stage is **always exactly one traversal**: the
runner collects every visitor for that stage, merges them, and calls `estraverse.replace` once.
So "several transformers in one walk" was never introduced — it was the original design, and
maximally so. `runAfter` means *finish the whole tree before I start*, and the sort exists to
**stop** transformers sharing a walk. The traversal count therefore rose:

| tag | stages | traversals | max levels |
|---|---|---|---|
| `0.14.0` | 6 | 6 | 1 |
| `0.19.0` | 7 | 7 | 1 |
| `0.19.3` | 7 | **8** | 2 |
| `1.12.1` | 10 | 14 | 3 |
| `2.9.6` | 10 | 16 | 4 |
| `3.2.0` | 10 | 18 | 4 |
| `5.5.0` | 10 | 20 | 4 |

No stage has ever exceeded four levels. The ceiling describes how finely a stage is **cut
apart**, not how much is batched together — and below `0.19.3` there is no point inside a stage
where any transform can be said to have finished.

## Who declares the order — three mechanisms, not one

The order has always existed; what changed twice is **who states it**. This matters to anyone
re-deriving the order at a tag, because the three mechanisms are read from different places and
only the third has levels at all.

| Range | Mechanism |
|---|---|
| `0.9.0` – `0.13.0` | **the obfuscator holds a literal list per pass.** `preparingTransformersList`, `deadCodeInjectionTransformersList`, `controlFlowTransformersList`, `convertingTransformersList`, `obfuscatingTransformersList` are static arrays, run by explicit sequential `transform()` calls gated on their options. Order *is* list order; one pass, one traversal; no dependency graph and no levels. Present already at `0.10.2`, in a separate `Obfuscator.ts`. |
| `0.14.0` – `0.19.2` | **the transformers declare their stage.** The per-pass lists collapse into one `transformersList` plus a `TransformationStage` enum, and each transformer says which stage it serves. The obfuscator stops owning the mapping. |
| `0.19.3` onward | **declared stages plus a levelled topological sort.** `runAfter` and `LevelledTopologicalSorter` arrive, so within a stage the order is computed rather than written, and a stage becomes *several* traversals. This is the mechanism described under "How the order is assembled" above, and the only one where "levels" means anything. |

So a derivation that assumes the third mechanism reads nothing at all below `0.19.3`, and a
claim that the early range "has no stage concept" is false — it has the same stages, written
down somewhere else.

## The order's history is in two file segments

**A rename check is not optional here, and `--follow` does not save you.** The pass lists lived
in `src/Obfuscator.ts` from the initial commit until `6819ba67` ("Refactoring", 2017-09-07),
first tagged **`0.12.0`**, which deleted that file and `JavaScriptObfuscatorInternal.ts` and
consolidated both into `src/JavaScriptObfuscator.ts`.

`src/JavaScriptObfuscator.ts` existed all along as the public facade, so this was a merge and
not a rename. `git log --follow src/JavaScriptObfuscator.ts` therefore runs back past `0.12.0`
into the *facade's* history and reads as though the order file goes to the initial commit. It
does not: before `0.12.0` that file did not hold the order at all.

| Segment | File holding the order |
|---|---|
| initial commit – `0.11.x` | `src/Obfuscator.ts` |
| `0.12.0` – now | `src/JavaScriptObfuscator.ts` |

Any history query about the order runs against **both** paths, and any claim dated from a log
names which segment it came from.

## The sequence settled at 1.12.1

The stage sequence is stable from `1.12.1` through the pin, so it is tempting to read it as the
encoder's design. It is not: it is the *end* of a sequence that changed eight times. Derived from
the same per-tag sweep as the era table, so these are exact release boundaries, not samples.

| First release carrying it | Sequence |
|---|---|
| `0.9.0` | three pass lists: control-flow, converting, obfuscating |
| `0.10.0` | + dead-code-injection list |
| `0.12.0` | + preparing list |
| `0.14.0` | six declared stages — `Preparing`, `DeadCodeInjection`, `ControlFlowFlattening`, `Converting`, `Obfuscating`, `Finalizing` |
| `0.18.7` | `Initializing` prepended |
| `1.1.0` | `RenameProperties` added, ahead of `Converting` |
| `1.4.0` | `Simplifying` added, between `Obfuscating` and `Finalizing` |
| `1.12.0` | **`Obfuscating` splits into `RenameIdentifiers` + `StringArray`**; `RenameProperties` moves behind `Converting` |
| `1.12.1` | `RenameProperties` moves back ahead of `Converting` — the sequence tabled above, unchanged through 5.5.0 |

Separately, `0.26.0` splits the two source-**text** stages into their own `CodeTransformationStage`
enum, giving the two-kind division described at the top of this page. That is not a node-stage
sequence change and so is not a row above.

Two things follow, and neither is visible from inside the 2.x range:

- **Until `1.12.0` the string array had no stage of its own.** A single `Obfuscating` stage
  carried identifier renaming and string-array construction together — at `1.11.0`
  `LiteralTransformer`, `ScopeIdentifiersTransformer`, `ScopeThroughIdentifiersTransformer`,
  `LabeledStatementTransformer`, `DeadCodeInjectionTransformer` and
  `VariablePreserveTransformer` all declare it. At `1.12.0` the stage splits and
  `LiteralTransformer` gives way to `StringArrayTransformer`. So "the array is built in its own
  stage, after renaming, over already-converted strings" is a claim about `1.12.0` onward and
  about nothing earlier; below it the two are one traversal group and interleave.
- **A patch release moved a stage.** `1.12.0` → `1.12.1` is the `RenameProperties`/`Converting`
  swap. Nothing about a sequence change is derivable from how large the version bump is.

## Levels within each stage, at `5.5.0`

Each cell is one full traversal; cells are executed left to right. Within a cell, visitors run
in the listed order and each sees the previous one's output.

| Stage | Level 1 | Level 2 | Level 3 | Level 4 |
|---|---|---|---|---|
| `Initializing` | `Comments` | | | |
| `Preparing` | `Parentification`, `RenameProperties` | `VariablePreserve` | `CustomCodeHelpers`, `EvalCallExpression`, `Metadata`, `ObfuscatingGuards` | `DirectivePlacement` |
| `DeadCodeInjection` | `DeadCodeInjection` | | | |
| `ControlFlowFlattening` | `BlockStatementControlFlow`, `FunctionControlFlow` | | | |
| `RenameProperties` | `RenameProperties` | | | |
| `Converting` | `BooleanLiteral`, `ClassField`, `ExportSpecifier`, `MemberExpression`, `NumberToNumericalExpression`, `ObjectExpressionKeys`, `ObjectExpression`, `ObjectPatternProperties`, `TemplateLiteral`, `VariablePreserve` | `NumberLiteral`, `SplitString` | | |
| `RenameIdentifiers` | `LabeledStatement`, `VariablePreserve` | `ScopeIdentifiers` | `ScopeThroughIdentifiers` | |
| `StringArray` | `DeadCodeInjection`, `StringArrayRotateFunction` | `StringArray`, `StringArrayScopeCallsWrapper` | `StringArrayControlFlow` | |
| `Simplifying` | `VariableDeclarationsMerge`, `ExpressionStatementsMerge` | `BlockStatementSimplify`, `IfStatementSimplify` | | |
| `Finalizing` | `Comments`, `EscapeSequence`, `DirectivePlacement` | `EvalCallExpression` | | |

(`Transformer` suffixes dropped for width.)

**Only the pin is tabled, and that is the design — not a gap.** Twenty-three eras tabled this
way would be twenty-three ten-row tables, most cells identical to their neighbour's, and an era
inserted by a later reading would need a new one. Instead **each era states its own delta**, in
[versions.md](versions.md)'s signature column ("what changed at the lower bound"). To
reconstruct any era's levels, start from the table above and apply the deltas of every era
between it and the pin, in reverse; or start from `P-lists-three-pass` and chain forward. The
deltas are written to compose — `StringArray levels 1->2` plus each transformer's own
`StageLn->StageLm` move is enough to rebuild the table, which is the property to preserve when
writing a new row.

Two consequences worth stating, because they are what this arrangement buys and costs:

- **An inserted era edits one row**, not every table above it. That is the same
  insertion-stability argument that made the era IDs signature-named.
- **A reconstructed table is a derivation, not a reading.** If one is ever load-bearing for a
  decode, re-derive it from source at that tag rather than trusting the chain — the recipe
  below is how, and a disagreement between the two is a defect in a signature, worth fixing at
  its row.

**A transformer is not confined to one stage, so the levels are not a partition of the
transformer list.** `VariablePreserveTransformer` contributes to `Preparing`, `Converting` and
`RenameIdentifiers`; `DeadCodeInjectionTransformer` to two; `CommentsTransformer`,
`EvalCallExpressionTransformer`, `DirectivePlacementTransformer` and
`RenamePropertiesTransformer` to two each. Reading "what runs in this stage" off the directory
a file sits in gives the wrong answer for all of them.

## One transformer runs its own private pipeline

`StringArrayRotateFunctionTransformer` declares exactly **one** stage, `StringArray`
([`getVisitor`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/45ad03b8335bee095b17c0d29b0a78bff158c93a/src/node-transformers/string-array-transformers/StringArrayRotateFunctionTransformer.ts#L136-L160)).
It nonetheless names four more inside `transformNode`: after building the rotate-function node
it runs its **own** `NodeTransformersRunner` over that fragment through `Preparing`,
`Converting`, `RenameIdentifiers` and `Finalizing`, with a private six-entry transformer list,
then marks the result ignored so the outer pipeline leaves it alone
([`transformNode`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/45ad03b8335bee095b17c0d29b0a78bff158c93a/src/node-transformers/string-array-transformers/StringArrayRotateFunctionTransformer.ts#L174-L188),
[the private list](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/45ad03b8335bee095b17c0d29b0a78bff158c93a/src/node-transformers/string-array-transformers/StringArrayRotateFunctionTransformer.ts#L42-L49)).

So the rotate function is obfuscated by a *different and much smaller* pipeline than the
surrounding program — a nested encode, at a stage the outer sequence has already passed. Any
count of "which stages does transformer X declare" taken by grepping for
`NodeTransformationStage` in its file reads five here and is wrong; the declaration is the
`case` labels inside `getVisitor` and nothing else.

## Source

- Stage sequence and both transformer lists:
  [`src/JavaScriptObfuscator.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/45ad03b8335bee095b17c0d29b0a78bff158c93a/src/JavaScriptObfuscator.ts)
  (read at `5.5.0`), and `src/Obfuscator.ts` for the segment before `0.12.0`.
- Per-stage filtering, level execution, visitor merge:
  [`src/node-transformers/NodeTransformersRunner.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/45ad03b8335bee095b17c0d29b0a78bff158c93a/src/node-transformers/NodeTransformersRunner.ts).
- Dependency edges and the sort:
  [`src/utils/AbstractTransformerNamesGroupsBuilder.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/45ad03b8335bee095b17c0d29b0a78bff158c93a/src/utils/AbstractTransformerNamesGroupsBuilder.ts),
  [`src/utils/LevelledTopologicalSorter.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/45ad03b8335bee095b17c0d29b0a78bff158c93a/src/utils/LevelledTopologicalSorter.ts).

**How the order tables were produced, so they can be reproduced rather than trusted.** For each
release tag: export `src/` at that tag, take the transformer list and the stage sequence from
the file that holds the order *at that tag*, take each transformer's `case
NodeTransformationStage.*` labels **from inside its `getVisitor` body only** and its `runAfter`
(walking the `extends` chain, since several inherit both), read each stage's gating from the
enclosing `if (this.options.X)`, then replay the assembly above. Collapse adjacent tags with
identical results into eras. Re-derive per tag; never carry a level structure to an unread tag.

Seven traps, every one of which produced a wrong answer at least once before being handled:

| trap | what goes wrong |
|---|---|
| stage labels grepped file-wide | reads five stages for `StringArrayRotateFunctionTransformer`; the answer is one. Only `case` labels inside `getVisitor` are declarations — see "One transformer runs its own private pipeline" |
| `runAfter` read without the `extends` chain | several transformers inherit it, so edges vanish and levels silently merge |
| the enum is `NodeTransformers` (plural) before `0.10.0` | a singular-only pattern extracts **nothing**, silently, for every early tag |
| an empty extraction treated as a result | 21 tags yielding `{}` collapse into a confident-looking era that does not exist. Assert non-empty per tag and *exclude* explicitly. The same failure has a second, sneakier cause: in `zsh`, `git show $tag:src/File.ts` inside a loop parses `:s` as a **parameter modifier**, so git is handed `<tag>.ts`, errors, and the redirect writes an empty file. Brace the expansion (`"${tag}:src/File.ts"`) or run the loop under `bash` — and assert non-empty, which catches it either way |
| one replay algorithm assumed | there are three, and below `0.19.3` there is no sort to replay, below `0.14.0` no declaration to read. Pick the mechanism from the tag first |
| the order file assumed to be one file | it is two, and `--follow` crosses the seam into the wrong file's history — see "The order's history is in two file segments" |
| a level sorted by list position | within-level order is graph **insertion** order, so a `runAfter` array's own order reorders transformers in a level it is not in — see "Within-level order is first-mention order" |

Below `0.9.0` none of this applies at all: there are no transformers, only `node-obfuscators/`
driven by a single `estraverse.replace`. Those tags are excluded rather than derived.

## Fixtures

**One claim on this page has now been checked against real output, and it is the one this section
used to nominate: the option-dependence of the `StringArray` stage.**

`2.9.6` and `2.10.0` sit either side of a boundary whose whole content is
`StringArrayRotateFunctionTransformer` arriving and splitting the stage into two levels. Built
from the same input at both versions, with `rotateStringArray` **off**, the two emit
**byte-identical** output; with it **on**, they differ. Re-run at three seeds, one of them a
string, with the same result each time — so this is a property of the encoder, not of one build.
The corpus and the comparison method are [corpus.md](corpus.md).

**What that does and does not establish.** It confirms the boundary is entirely attributable to
that one option-gated transformer: disable the option and the two versions become
indistinguishable in output, which is what an option-gated era boundary is supposed to look like.
It does **not** isolate the *level split* from the transformer's own emission — with rotate off
the transformer contributes nothing at either version, so both explanations predict identity.
Separating them needs a case where the transformer is present but its contribution is
distinguishable from the traversal boundary it creates, which no cell in the corpus currently is.

Everything else here remains read from source only.
