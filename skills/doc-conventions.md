# Doc Conventions

The two specifications `SKILL.md`'s Standing Rules point at: how a transform doc is
structured, and how a reference crossing between the hub and a submodule is written. Read
this before writing or editing any transform doc. Standing Rules keeps the invariants that
apply to *every* change; this file keeps the detail you only need while writing one.

## Transform Doc Layout

An encoder transform doc and its paired decoder doc share one numbered structure, so matching
numbers make a pair easy to cross-check. A section left blank for lack of knowledge is fine;
an invented one is not.

- **1. Target** — the requirement: what the transform is meant to achieve. Encoder: the
  protection it adds. Decoder: what decoding it means to produce.
- **2. Algorithm** — the solution-level design, kept high enough to survive a re-read
  without the source open. On the decoder side this is the *only* place a reversal
  strategy is ever asserted — see `SKILL.md`'s "Reversal Lives Only in the Decoder."
- **3. Implementation** — the granular design: which functions, which AST node shapes,
  line citations, data structures. Whatever a doc puts under a heading like "Stage
  1/2/3" beyond the high-level approach belongs here, not in Algorithm.
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
    vs. the encoder's. A sentence like "keyed on the binding, not on the shape" is a claim
    about the accepted set wearing the clothes of a summary, and it hides the only thing
    worth knowing: which spelling nobody implemented. Write the row when the branch is
    written. Worked example and its incident:
    [decode-js/visitors/jsconfuser/dispatcher.md](decode-js/visitors/jsconfuser/dispatcher.md).
  - **Fixing one is a different decision from documenting it.** An encoder is read-only,
    so a Downstream Effect can only ever be worked around. An Upstream Effect has a
    second option the encoder side lacks: change the pass that *emits* the shape. Prefer
    that when the shape is ours — it fixes every pass the shape defeats at once, whereas
    teaching each affected matcher to tolerate it is the same fix re-paid per consumer
    (`encoder-decoder-method.md`'s T1, "fix it at the pass that produces it").
- **5. Known Quirks (encoder) / Known Gaps (decoder)** — open items only, different
  names because they're different in kind. An encoder is pinned and read-only, so its
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
  which claim nothing tests. Where a pass has no fixtures, say so and say why; an absent
  section reads as an oversight, and "none, and here is why" does not. Both halves were
  unwritten convention until they drifted: twenty-one docs had bundled the two into
  `## Source`, one had `## Fixtures` and no source path at all, and the fixture lists had
  decayed into name inventories that omitted real fixtures — including ones backing claims
  their own doc already made.

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
  — the form the `js-confuser` package uses throughout. **The pin is the hub's `main`-branch
  gitlink for that submodule, not whatever the local checkout happens to be at.** A bare
  `file.js:42` drifts on the next edit to that file and is wrong with no signal; a pinned
  permalink stays true permanently, which is the same reason the encoder is pinned at all.
  Verify each one resolves before committing
  (`curl -s -o /dev/null -w '%{http_code}'` → `200`).
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
