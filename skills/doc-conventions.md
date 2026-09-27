# Doc Conventions

The specifications `SKILL.md`'s Standing Rules point at: how a package is laid out, how a
transform doc inside it is structured, and how a reference crossing between the hub and a
submodule is written. Read this before writing or editing any transform doc. Standing Rules
keeps the invariants that apply to *every* change; this file keeps the detail you only need
while writing one.

## Package Layout

**Name files and folders for the behavior or content they own, never for the task that created
them.** Task IDs, phase numbers, worklist positions, and chronology do not describe what a
reader will find and become misleading when work moves between tasks. Use a number in a name
only when it is part of the subject itself, such as a protocol version or an opcode, and state
that meaning in the file or folder's documentation. When renaming either, update executable
references, documentation links, and any integrity records that bind its path or bytes.

**Every encoder has its own file-layout habit; they have the same components.** Order,
options, transforms, templates. So a package's layout is designed around *those*, and it is
**ours** — never a mirror of whichever directory tree the submodule happens to ship. Where the
two need relating, that is a mapping (below), not a naming convention.

This is settled practice rather than a new idea: `skills/js-confuser/` converged on it with no
rule telling it to — the root file carries the pipeline order, `options.md` and
`validate-options.md` the option surface, `transforms/<name>.md` one per transform,
`templates/<name>.md` plus `template-engine.md` the templates. Its own Skill Layout section
already justifies *departing* from the source tree, noting that `options.md` is "cross-cutting,
not scoped to a single transform, so it isn't under transforms/" and that `validate-options.md`
"runs once, so it isn't under utils/ alongside the per-file helper docs."

- **Docs are named for the transform or shape, never for a source file.** Same rule as naming
  a strategy by shape rather than version, and citing era IDs rather than ranges: never key a
  doc on something that drifts. A doc named after a source file has to be renamed, split or
  duplicated the first time the encoder moves the concept — one obfuscator's rotate function is
  *only* a code helper at 2.9.6 and becomes a code helper **plus** a transformer in a different
  directory by 2.19.0. One concept, one file at one era and two at another.
- **Source-tree mirroring applies only inside large helper folders** — `utils/<name>.md`,
  `templates/<name>.md`, one file per source file, flat and distinctly named, against the
  pinned commit. That is a navigability rule for bulk, and it was never a mandate that the
  package's top level follow the submodule's directories.
- **Structural drift and shape drift are independent axes**, which is what makes a file-keyed
  layout actively wrong rather than merely inconvenient. The axis to measure is the **file
  set** — what a file-keyed layout tracks — against **file contents**, which is where a shape
  lives; the two answer differently at the same boundary, in both directions. Measured on one
  obfuscator (`git diff --name-status --diff-filter=ADR <a> <b> -- src` for the first,
  `--diff-filter=M` for the second): across `2.15.3 → 2.15.4` the file set does not move at
  all — nothing added, removed or renamed — while every modified file is a string-array
  calls-wrapper helper or template, and a decoder distinguishes two wrapper shapes across
  exactly that boundary. So an era boundary can have **no structural footprint at all**. And
  across `2.18.1 → 2.19.0` the file set moves in three places, none of them string-array (two
  self-defending helpers consolidate into one, plus an added tsconfig), while the string-array
  transformers, storages and templates are all modified in place. A file-keyed doc tree would
  have churned on the self-defending rename and stayed silent through both string-array
  changes. **Beware the shorthand that reads "changes zero files"** — an earlier statement of
  this measurement said exactly that, meaning the file set, and it reads as "nothing in the
  source changed", which was false and would have retired the boundary from study.
- **A file moving is never a reason to split a doc.** A relocation is implementation-level, so
  it is an era-tagged row; what earns a new file is an algorithm divergence, decided by reading
  the shape rather than the path. Both are specified under "Documenting Multiple Eras."

### The source map, where one is necessary

`source-map.md` in the package: one row per submodule source file, the doc that claims it, and
the era where those differ. **Required only when the reverse lookup is otherwise hard** — a
package documenting more than one era, or one where a concept spans directories. A single-era
package whose layout tracks its source closely needs none.

It is not a duplicate of the per-doc `## Source` sections, because it answers what they
structurally cannot:

- **The reverse direction.** "Which doc covers this source file?" is unanswerable from docs
  keyed the other way without grepping the whole package.
- **The coverage gap** — which source files *no* doc claims. This is the same question the
  fixture table is required to answer ("which claim nothing tests") and the spellings table
  ("which spelling nobody implemented"), one axis over. A map that lists only what is
  documented reproduces exactly the failure those two rules exist to prevent.

**Anti-drift discipline:** each doc keeps its own `## Source` exactly as specified below, and
the map is **verified by grep against those sections in both directions**, never maintained
independently. A map that can drift silently is worse than no map, for the same reason a stale
probe is worse than no probe.

## Transform Doc Layout

An encoder transform doc and its paired decoder doc share one numbered structure, so matching
numbers make a pair easy to cross-check. A section left blank for lack of knowledge is fine;
an invented one is not.

- **1. Target** — the requirement: what the transform is meant to achieve. Encoder: the
  protection it adds. Decoder: what decoding it means to produce.
- **2. Algorithm** — the solution-level design, kept high enough to survive a re-read
  without the source open. On the decoder side this is the *only* place a reversal
  strategy is ever asserted — see `SKILL.md`'s "Reversal Lives Only in the Decoder."
  This is also the level at which an era divergence becomes a **separate doc and file**
  rather than a section — see "Documenting Multiple Eras."
- **3. Implementation** — the granular design: which functions, which AST node shapes,
  line citations, data structures. Whatever a doc puts under a heading like "Stage
  1/2/3" beyond the high-level approach belongs here, not in Algorithm. Where an era
  differs only here, it is a tagged row, not a second doc.
- **4. Downstream Effects (encoder) / Upstream Effects (decoder)** — one slot and one
  principle, mirrored: **what another pass in the same project's pipeline does to the
  shapes this one has to live with.** Each side names the other party by its position in
  *its own* pipeline, which is why the two halves have opposite names — an encoder runs
  forwards, a decoder runs the same ground in reverse.
  - **Encoder — Downstream Effects.** What a *later* encoder stage does to this
    transform's own output, derived from the stage order
    (`encoder-decoder-method.md`'s W1) rather than discovered only after a decoder breaks
    on it. Harvest an existing decoder-doc bug writeup first (rename-proofing, minify
    compatibility, moved-declarations spelling, …) before re-deriving one from scratch.
    **The stage order is itself era-dependent**, so derive it per era rather than once:
    an order is rarely a flat list to read off, and where it is assembled from per-stage
    dependencies a reordering leaves no trace in a changelog. One such change rewrites
    this item for many transforms at once, which is why it is carried as rows.
  - **Decoder — Upstream Effects.** What an *earlier decoder pass* does to this pass's
    input. A decoder pass is not only a consumer of encoder output: it emits shapes of
    its own, and every pass scheduled after it inherits them. Reading the encoder's stage
    order tells you which *encoder* residue is still in your input; it says nothing about
    what your own pipeline put there, and that has repeatedly been the actual blocker —
    a reconstructed function given a rest parameter unconditionally, a restored
    declaration left shadowed by the parameter slot it was packed into, a call re-spelled
    `(1, f)()`. Each defeated a later pass that was reading for the encoder's spelling,
    and each was found only after that pass was wrongly blamed on an encoder stage.
  - **Home rule, split by what each side knows.** The *affected* pass owns the
    dependency and what its own gates do with it — that is where a decline is debugged
    from, so an empty section there costs a re-derivation. The *producing* pass owns one
    inventory of the shapes it emits, since one producer feeds many consumers and the
    mechanism restated per consumer drifts per consumer. The affected side links to it
    rather than repeating it. Encoder-side, only the first half applies: an encoder stage
    is pinned and never coordinates for our benefit.
  - **List the spellings, don't describe the intent.** A matcher reading one construct
    through several spellings records them as a table — spelling, producing pass, ours
    vs. the encoder's, and **the era it applies to** once a package documents more than
    one. A sentence like "keyed on the binding, not on the shape" is a claim
    about the accepted set wearing the clothes of a summary, and it hides the only thing
    worth knowing: which spelling nobody implemented. The era column answers the same
    question along the other axis — which era nobody covered. Write the row when the
    branch is written. Worked example and its incident:
    [decode-js/visitors/jsconfuser/dispatcher.md](decode-js/visitors/jsconfuser/dispatcher.md).
  - **Fixing one is a different decision from documenting it.** An encoder is read-only,
    so a Downstream Effect can only ever be worked around. An Upstream Effect has a
    second option the encoder side lacks: change the pass that *emits* the shape. Prefer
    that when the shape is ours — it fixes every pass the shape defeats at once, whereas
    teaching each affected matcher to tolerate it is the same fix re-paid per consumer
    (`encoder-decoder-method.md`'s T1, "fix it at the pass that produces it").
- **5. Known Quirks (encoder) / Known Gaps (decoder)** — open items only, different
  names because they're different in kind. Each entry names the era it applies to once a
  package documents more than one: an entry scoped to a superseded era can never close,
  because nothing will be released against that era again, while the same words about a
  current era describe live work. An unscoped entry silently claims to be both. An
  encoder is pinned and read-only, so its
  quirks are permanent, descriptive, non-actionable oddities (an upstream-doc
  discrepancy, a dead code path) — never a bug to fix. A decoder's gaps are usually
  fail-closed incompleteness, not wrongness, and are meant to close eventually. Once a
  gap closes, it leaves this section — the durable fact it revealed graduates into
  Algorithm, Implementation, or item 4 (Downstream Effects on the encoder side, Upstream
  Effects on the decoder side), whichever level it actually sits at. A closed decoder gap
  lands in item 4 more often than it looks: if what blocked the pass was a shape another
  of our passes emits, the durable fact is that dependency, not the matcher tweak that
  absorbed it. The discovery narrative (dates, how it was found, before/after numbers)
  does not move into the doc at all, and doesn't need parking anywhere else either —
  `checkpoint.md` is scratch, disposed of once the work it tracks is done, and a commit
  message isn't durable once a release rebuild rebases history down to something concise.
  Once the fact itself has migrated, the narrative around discovering it has done its job
  and can simply go.
- **Then two unnumbered closing sections, in this order: `## Source`, then
  `## Fixtures`.** They sit outside the numbering because they are pointers, not levels of
  the design — but they are not optional, and they are not one section. `## Source` is the
  file path plus where the pass is wired, and it cites the numbered item that explains
  *why* that position is forced rather than restating the reason; a scheduling argument
  living here is the same misplacement as mechanism living here. `## Fixtures` maps each
  committed fixture to **the claim it pins**, naming the fixture so the mapping can be
  checked by grep in both directions, as a table once there are more than a few — a bare
  list of names records what exists while hiding the only thing worth knowing, which is
  which claim nothing tests. A fixture pins a claim **at an era**, so the table carries an
  era column once a package documents more than one; without it a claim looks covered when
  only one of its eras is, which is the same omission one axis over. Where a pass has no
  fixtures, say so and say why; an absent
  section reads as an oversight, and "none, and here is why" does not. Both halves were
  unwritten convention until they drifted: twenty-one docs had bundled the two into
  `## Source`, one had `## Fixtures` and no source path at all, and the fixture lists had
  decayed into name inventories that omitted real fixtures — including ones backing claims
  their own doc already made.

## Marking something done

**Marking a step done means re-reading every place that names it.** A status lives in more than one
place by design — a step table, a summary line, an action list, a pointer table — and updating the
one you are looking at leaves the others asserting the opposite. This is the most frequently
repeated mistake in this repository: it has been recorded, and then made again in the same session
that recorded it, more than once. The cheap guard is a grep for the step's own identifier before
the commit, not a memory of where it was mentioned.

The same applies one level up: **a fact that graduates out of scratch into a skill doc has to leave
the scratch copy behind**, or the two drift and the stale one is indistinguishable from the fresh
one. Prune in the same commit that graduates.

**And it applies to open questions, not only to answers — which is the direction that gets
missed.** A worklist item is a status too, so it decays the same way, except that nothing ever
re-reads it: an answered question left standing in scratch reads exactly like an unanswered one and
is re-opened at full price. The recorded instance is a residue axis carried as "the emitter is
unidentified, start by reading the encoder" for several sessions, while the package's own transform
doc opened by naming the emitter, calling it ungated, and quoting its character class — the item was
answerable from two paragraphs of a doc the same study had written. **So before working an open
item, grep the packages for its subject.** That is the doc-side face of the rule that a matcher
already doing the job beats a probe
([encoder-decoder-method.md](encoder-decoder-method.md)'s T8): the cheapest source of an answer is
the one already written down, and it is checked last precisely because a worklist reads as the
authority on what is unknown.

## A Doc That Replaces an Artifact

Where a doc stands in for working artifacts — probes, instruments, tooling — **write it as a build
recipe and then rebuild from it cold, in the same change**. Inputs, naming contracts,
prerequisites, and above all the failure modes that report success: an inventory of what exists is
not a recipe, and a doc nobody has rebuilt from is unverified. Doing the rebuild here found five
gaps in a freshly written page, four of which would have produced a confidently wrong answer
rather than an error, one of them a defect the original scripts had carried all along. A preserved
script silently stops matching the code it targets, while a recipe stays true — which is why the
recipe is the artifact worth keeping.

**A script that is run rather than rebuilt is the exception, and it is a checked-in executable, not
a fenced code block.** The two are decided by whether anything executes the thing: a probe is
rebuilt per session from its recipe and belongs in prose, while a tool that must run unchanged
belongs in `tools/` where it can be run and corrected in place. Code fenced in a document is never
executed, so nothing tests it, and a defect in it survives every reading — which is how one
extractor shipped globbing a filename pattern its harness does not emit, and its replacement
shipped double-counting every input total.

## Documenting Multiple Eras

An encoder changes what it emits over time, and samples in the wild keep being produced by
older releases — so a package often has to describe more than one shape. An **era** is a
maximal version range over which some named thing about the encoder holds still. Emitted
output can never identify an exact version, only an era, which is why eras rather than
versions are the unit throughout.

- **Change arrives at two levels, and they need different numbers of axes.**
  - **Global** — the pipeline itself: which stages run, in what order, how transforms are
    grouped into traversals. One change here moves every transform at once, so no component
    owns it and there is nothing to split it by. **One axis, for the whole encoder.**
  - **Local** — one transform's algorithm being rewritten. Transforms are rewritten
    independently, so **one axis per component**. A single global shape timeline would take a
    boundary wherever *any* component moved, and a doc citing it would see its era shift for
    a reason having nothing to do with its own subject — the same dilution that makes a
    file-keyed layout track the wrong thing.

  Assume every transform has its own history until someone has read it. A component with no
  axis is one nobody has studied, never one that held still, and the two must not be recorded
  as the same thing.
- **Per-component axes are what let a verdict be partial.** A sample whose option was off
  carries no evidence about that transform, so its era is *unknown* from that sample rather
  than wrong. A global axis cannot express that: it has to name one era for the whole file on
  evidence that covers part of it. The version range a sample came from is the **intersection**
  of its per-component verdicts, computed from them rather than fingerprinted whole.
- **The era registry is the single definition.** A package documenting more than one era
  carries a `versions.md` with one table per axis and one row per era: **era ID, version
  range, verified commit SHA, signature.** Required only once a second era is documented — a
  single-era package needs nothing. A row never spans axes, and a coincidence between two
  axes' boundaries is a finding written in prose, never a merged row.
- **A registry row is a claim in one direction, and a detector reads it in the other.** The
  registry states `version → shape`, which is a function. A decoder observes a shape and needs
  `shape → version`, which is **not**: a shape can recur non-contiguously, because an encoder can
  revert a change. So a detector's per-axis verdict is the **set** of ranges consistent with what
  it matched — a union — never one era ID chosen from several, and the version range for the whole
  sample is the intersection of those unions across axes.
  - **Two same-shape eras therefore stay separate rows**, precisely so the union is computable.
    Merging them forces the row's range to be either a hull, which is a *false* claim about every
    version in the gap, or a disjoint set, which is not a range and breaks the row's own shape.
    The maximal-range definition already forbids the merge; this is why the definition is right.
  - **The era-ID naming rule is the tripwire.** Two eras cannot honestly share a signature name,
    so a would-be collision is a prompt rather than a shrug: either the shapes differ in a way the
    signature has not captured — find it, and the detector gains a discriminator — or the axis
    genuinely cannot separate them and the verdict must say so.
  - **The mapping is documentation, not code.** A shape-first detector needs no era at runtime,
    since matching is a union over shapes and the era is read off whichever matched. Keeping the
    correspondence in the decoder's own doc, as item 3 rows, is what lets the registry gain rows
    without the matcher changing — and it must be grep-checkable in both directions, like
    `source-map.md`: every registry row appears in the decoder's table or is listed as uncovered,
    and every era ID in that table resolves to a row.
- **Docs cite era IDs, never inline version ranges.** Twenty docs saying `≥ 2.19.0` is
  twenty edits and some misses the day the boundary turns out to have been 2.18.0; twenty
  docs saying `E-fn-wrapped` is one edit, in the registry. The registry row is also the
  only place a range and its SHA are stated together, so a citation can be checked.
- **An era ID names the era's signature, never its position or its version.** `P-rotate-helper`
  and `E-fn-wrapped`, not `P1`/`E1` and not `P2.9.6`. Both rejected forms defeat the rule
  above rather than merely reading worse. An **ordinal** ID is stable only while the era list
  is complete, and no era list is: ranges between sampled versions are unread by construction,
  so an era slotting *between* two existing ones is the expected result of narrowing one — and
  it renumbers every era above it, in the registry and in every doc that cites one. A
  **version-derived** ID reintroduces the inline range through the back door, and lies as soon
  as the boundary moves, since the version in the name is a reading the registry is free to
  correct. Signature names cost width in any table that spans eras; that is the price of the
  registry being the only thing an insertion edits. Lay the registry out in version order and
  say so, so that a span `A–B` has a defined meaning.
- **An era's SHA is the commit its claims were verified against**, not whatever the pin
  happens to be. A recorded claim always names the commit that proved it, so the SHA does
  not drift when the pin moves; it moves when someone re-verifies. This is what lets a
  package document an era whose shapes the *current* source no longer contains — the row
  points into submodule history, and a pinned checkout stops being the limit of what can
  be described.
- **Where era divergence resolves depends on which numbered item it hits**, and only the
  first answer is a new file:

  | Item | If it differs by era |
  |---|---|
  | 1. Target | never diverges — if the purpose changed it is a different transform |
  | 2. Algorithm | **split into a separate doc and code file** |
  | 3. Implementation | era-tagged table rows |
  | 4. Downstream/Upstream Effects | era column on the spellings table |
  | 5. Known Quirks / Known Gaps | era-scoped entry |
  | `## Fixtures` | era column |

  Item 2 is the hinge, and it is the doc-side face of one rule: a **different algorithm**
  earns its own file, **different parameters** stay in one. Everything below item 2 stays
  in a single doc as rows.
- **Rows, never prose duplicated per era.** This is the same principle item 4's spellings
  table already rests on: prose hides the case nobody covered. A doc that repeats a
  section per era hides *which era nobody covered*, and drifts per copy besides.

## Reference Direction and Form

The hub and a submodule are read by different people, so a reference that crosses between
them has one legal direction and one legal shape.

- **Submodule source never references the hub.** Not a path, not a doc name, not a section
  title, not a worklist label. A submodule ships as its own repository, so every such
  pointer is unresolvable for the only people who will read it — and it rots invisibly,
  because nothing in either repo checks it. This was worth 46 removals in one pass across
  `decoder/decode-js`: development issue labels (`checkpoint gap #2`), citations into
  `skills/`, and the hub's own doc-layout conventions quoted inside shipped code. Five
  of them pointed at a section deleted long before, and two described work as
  "not-yet-built" that had since been built. A comment that needs the hub to make sense is
  a comment saying the wrong thing: state the invariant locally, or move it to the doc and
  drop it from the code.
- **A hub doc referencing *frozen* submodule source uses a commit-pinned permalink, never a
  line number.**
  [`calculator.ts#L26-L58`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/calculator.ts#L26-L58)
  — the form the `js-confuser` package uses throughout. **The pin is the SHA of the era the
  passage describes, never whatever the local checkout happens to be at.** For a
  single-era package that SHA is the hub's `main`-branch gitlink for the submodule, which
  is what existing packages already cite; once a package documents more than one era, each
  era's SHA comes from its registry row. A bare
  `file.js:42` drifts on the next edit to that file and is wrong with no signal; a pinned
  permalink stays true permanently, which is the same reason the encoder is pinned at all.
  Verify each one resolves before committing
  (`curl -s -o /dev/null -w '%{http_code}'` → `200`).

  **There is no "current era" exemption.** Citing the newest era through the live gitlink
  rather than through its own recorded SHA reads as correct right up to the next pin bump,
  at which point the doc describes one commit and points at another — with nothing edited
  and nothing to notice. "Current" is a fact about when a passage was written, not about
  what it says, so it is never what a reference is keyed on.
- **While a target is still actively edited, plain relative paths are the correct form** —
  a permalink into a moving tree is a promise the next commit breaks. So a decoder
  documenting its own live source links relatively, and converts to permalinks only once
  that source is frozen at a release commit. The two halves of this rule are one rule about
  *whether the target can still move*, not a preference about link style.
- **A permalink can only be written once its target commit is final.** Where a submodule's
  history is going to be rebuilt, the order is forced: rebuild the submodule, take its
  settled commit ids, update the hub's references, then rebuild the hub — the hub rewrite
  absorbs its own reference-update commit. Writing the links first pins them to commits the
  rebuild destroys.
