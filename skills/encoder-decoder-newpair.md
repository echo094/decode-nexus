# Studying a New Encoder/Decoder Pair

The workflow for taking on an encoder/decoder submodule pair that has no package here yet. Split
out of [encoder-decoder-method.md](encoder-decoder-method.md), which is read every session and so
holds only the labelled rules; this is read once per pair. Those rules still apply throughout —
T8 in particular — and are not repeated here.

Follow the process used for `js-confuser` ([js-confuser.md](js-confuser/js-confuser.md) as a worked
example). T8 applies throughout and is not repeated.

- **Go incrementally, from unit to combo**, letting whoever is driving pick the next piece rather
  than front-running unrequested sections. Single-transform coverage is a first phase, not a finish
  line: a decoder tested one transform at a time never sees the interactions a later stage's
  residue creates, and this project's closed bugs are almost entirely combo bugs. The unit loop
  that worked: **(1)** stop first if a decoder file already exists reusing a *shared* visitor —
  keep-or-fork is a decision, not a default; **(2)** document the encoder side; **(3)** write the
  decoder pass; **(4)** document the decoder side; **(5)** build fixtures from the *encoder's own*
  test cases, a free and authoritative case list — **and mine them as a measurement, not just as a
  source of cases**: encoding every upstream fixture for a stage and comparing the decoded
  structure against its source has twice found a reversal nobody had noticed was missing, on units
  whose own censuses, corpus and test suite all read clean, because none of them was asking that
  question; **(6)** pause for review; **(7)** commit, then
  clear context.
- **Pin the encoder at its current release and make that your reference cell.** For a pair with no
  package here, that is the whole of the version decision — there are no prior claims to audit, so
  there is nothing to argue for opening anywhere else. Walking *backwards* into older releases is a
  later, separate decision, driven by prevalence rather than by completeness (below); it is not
  part of getting started. `V1` says why some reference has to be closed end to end before any
  comparison means anything.
  - **This project's own history is the exception rather than the pattern, and is easy to
    misread.** Its javascript-obfuscator study opened at `2.19.0` while the pin was `5.5.0`,
    because what it was auditing was an *incumbent decoder's claimed range*, and `2.19.0` was the
    newest release inside that range. Absent an incumbent making claims, that reasoning has no
    input.
- **Where the encoder has many versions, cut the work into phases, and make each phase an era
  slice taken *end to end*.** A phase is not a verification stage: it is one slice of era coverage
  carried all the way through — study the encoder, verify whatever incumbent exists, write the new
  decoder — and the boundary between phases is what the decoder *claims*, not what kind of work it
  contains. Splitting by behaviour instead (document everything, then verify everything, then
  build) fails three ways, and each has been paid for:
  - **Each behaviour alone is unfalsifiable.** An encoder doc written from reading is a hypothesis
    until something inverts it (T8). A verification verdict rests on the residue census, since S4
    rules out runtime correctness as a substitute. And a fixture pins *a claim*, so fixtures built
    before the claims exist are a name inventory.
  - **A census written before the encoder study is defined by the thing under test** — its subject
    list can only come from the decoder's own prose. This is the same trap the three-step incumbent
    loop below exists to avoid, one level up.
  - **Anything else forces a rewrite backwards**: a stage's output is provisional until the next
    stage tests it, so one late finding invalidates a large body of already-written docs.

  **Order the phases so a failure stays interpretable.** Take the range the incumbent already
  claims first: a failure there means the problem is *not* version drift, which is exactly what
  makes a later phase's failure readable as a version finding. `V1` governs the ordering *within* a
  phase's range and constrains which leaps between phases are interpretable at all.
- **An incumbent's boundary set is evidence, and it encodes prevalence.** Boundaries that
  accumulated from real user-submitted samples over years — with issue numbers in the source
  where shapes diverged — are not unverified claims. They carry a second signal free: **which
  versions people actually encounter.** Four consequences:
  - **Era granularity should follow prevalence.** An era earns a strategy by being *met*, not by
    existing.
  - **Prevalence predicts which refusals fire**, so uncovered eras determine the real-world refusal
    rate of a decoder that refuses rather than guessing.
  - **Whether to cover a range at all is a prevalence question, not a completeness one.** Do not
    enlarge a corpus before asking it.
  - **"No samples seen" and "no change occurred" are different findings** and must never be
    recorded as the same one.
- **Budget a unit by the questions it has to answer, never by whether a pass falls out of it.**
  Two units here closed with **no new code** — one because a shared visitor imported unchanged
  already did the job, one because two passes an earlier unit had scheduled already performed the
  reversal — and each still cost an encoder doc, an era axis swept per tag, a census built twice,
  and fixtures. The work is establishing *that* nothing is needed, which is the same size as
  writing something. **Do not read a unit's value off the diff it lands**, and expect more of them
  as the pipeline fills in.
- **Budget for the composition step; it is where the finding usually is.** Passes that each read
  clean on their own census routinely surface a real dependency the moment they run as one
  pipeline — an earlier stage's reversal re-opening work a later one had finished, or a pass
  turning out to be another's precondition. Treating composition as a formality after the parts are
  green is how those arrive late. It is the same rule as "a stage's output is provisional until the
  next stage tests it", one level down.
- **Where a decoder for this encoder already exists, the loop gains three steps, and their order
  is the point.** Between documenting the encoder side and writing anything, insert: **(a)** define
  this unit's residue census *from the encoder side you just documented* — the construct list is
  encoder knowledge, never the incumbent's description of what it removes, or the census is defined
  by the thing under test; **(b)** run the incumbent over the cells that exercise this unit and
  record the verdict, which only means something once (a) exists; **(c)** read how the incumbent
  *inverts* this shape before designing your own, since a decoder that works is the cheapest
  account of how a shape inverts and beats any probe.
  - **That lends the incumbent's algorithms, never its pass order.** How it recognises and inverts
    a shape is prior art worth adopting; *when* it runs a pass is evidence of nothing. Taking the
    order from it is circular and has been paid for here — a unit list derived from an incumbent's
    pass order, then citing that incumbent as corroboration, had to be re-derived from the
    encoder's stage order and gained a whole missing unit.
  - **The exit criterion is the census reading zero on this unit's own cells, plus a pass that
    exists and is fixture-pinned.** A green run of the *incumbent* is an input to (c), never an
    exit.
- **Respect the preset order.** Climb the shipped tiers as the combo ladder instead of inventing
  one — smallest first, largest reserved for the final integration check. **Don't assume subset
  semantics**: a smaller tier can be a genuinely distinct shape, so verify the relationship before
  treating one tier's coverage as implying another's.
- **Only encoder-agnostic normalization transfers between decoders.** The reusable slice of an
  existing plugin is its *normalization prelude* — operator-to-statement, sequence splitting,
  re-bracing — which every obfuscator's output needs alike, and which is why the shared-visitor
  layer exists at all. Encoder-specific reversal does not transfer, so **do not generalize this
  into "search the repo for prior art"**: one plugin here is ~1325 lines of which ~350 are that
  prelude, and the rest is a keyed state machine with no analogue in the encoder next door. Mining
  it for a string array or a control-flow shape costs time and returns nothing.
- **Summarize the test suite** in a `tests.md` — framework, project structure, directory
  breakdown — so readers have somewhere to go when prose needs more precision.
- **Cross-reference upstream docs, but verify them too.** Confirm a shipped `docs/` page still
  matches the pinned commit; note, don't silently drop, any upstream doc describing a feature the
  pinned version lacks.

[Incidents](encoder-decoder-incidents.md#studying-a-new-encoderdecoder-pair)
