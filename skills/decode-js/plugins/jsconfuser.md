# jsconfuser.js

Target: **[js-confuser](../../js-confuser/js-confuser.md)**. Unlike `obfuscator.js`
(one large hand-tuned pipeline), this plugin is a flat sequence of independent
`traverse` passes, each reversing one js-confuser transform (or a piece of one) by AST
shape. Matching is structural throughout; the sandbox appears only where a value has to
be *computed* from the encoder's own runtime helper, which three passes do —
`string-concealing.js`, `string-compression.js` and `variable-masking.js` each construct
an `isolated-vm` isolate at module scope. Dispatched via `-t jsconfuser`
([`src/main.js`](https://github.com/echo094/decode-js/blob/6c974fb5720518fac9c6b3d4cf558ba90ef9f8e7/src/main.js)).

Built originally against **pre-2.0 js-confuser**; the inline `// StageName` comments
next to each `traverse` call are historical labels from that era and are not reliable at
face value against the current pinned encoder source — each stage's actual target gets
re-verified independently as it's documented (per
[Studying a new encoder/decoder pair](../../encoder-decoder-method.md#studying-a-new-encoderdecoder-pair)).
Confirmed correct-but-renamed so far: decode-js's old `Stack` file name was this project's
pre-2.0 name for what the encoder now calls `VariableMasking` (the
[VariableMasking](../visitors/jsconfuser/variable-masking.md) entry below); decode-js's own
file naming follows the encoder's current terminology.

## Pipeline (default export)

Runs in this fixed order
([`src/plugin/jsconfuser.js`](https://github.com/echo094/decode-js/blob/6c974fb5720518fac9c6b3d4cf558ba90ef9f8e7/src/plugin/jsconfuser.js)); **not** the reverse of the
encoder's `Order` enum throughout — later entries interleave stages from earlier encode
positions as they get added, rather than a strict reversal:

1. **Pack** (`pack.js`) — peel the eval-wrapper the encoder's `Integrity`/output
   step produces. Must run first; everything after this operates on the unwrapped AST.
2. **[Integrity](../visitors/jsconfuser/integrity.md)** (`integrity.js`) — placed right
   after Pack, before everything else, the mirror image of Flatten's placement: Integrity
   runs *last* on the encode side (`Order.Integrity = 37`), so its output is never
   reshaped by anything else on the encode side — decoding it first gives it the
   least-processed input.
3. **AntiTooling** (`anti-tooling.js`) — targets a **legacy, pre-2.0, removed**
   transform (merged-`ExpressionStatement`s via a call to an always-*empty*
   top-level function), not the current `Lock` family — and not the same shape as
   AstScrambler below either, despite the superficial resemblance (both merge
   consecutive statements into one call): this legacy shape's helper body is
   completely empty, with no self-reassignment, unlike AstScrambler's self-nulling
   template. The two checks don't overlap on either shape, so both visitors run
   without conflict. Kept for real-world samples predating the 2.0 rewrite
   ([`dd408e8`](https://github.com/MichaelXF/js-confuser/commit/dd408e8)), which removed it;
   no trace of the merged-call shape remains in the pinned source. **Present through 1.7.3,
   gone from 2.0.0 on** — so it shipped in released versions, which is what justifies
   keeping the decoder.
   Its guard conditions had two bugs, fixed 2026-07-23: `!x === y` instead of
   `x !== y` (operator precedence - `!` binds before `===`, so the check was
   always false) on both the callee-position check and the body-position
   check, the latter compounded by checking the wrong path's `listKey`
   (`call.listKey`, always `undefined`, instead of `call.parentPath.listKey`).
   Together these made the matcher unsafe on arbitrary code containing an
   unrelated empty no-op function referenced as a plain value (not a callee) -
   `deAntiToolingCheckFunc`'s shape match is generic enough to fire on any
   such function, and the broken guards let extraction proceed anyway,
   silently deleting the call site that referenced it. Fixing precedence
   alone regresses the genuine merge case to a permanent no-op, since
   `call.listKey` is never `'body'` either way - both bugs needed fixing
   together. See `test/visitor/jsconfuser/anti-tooling/` for both cases.
4. **[AstScrambler](../visitors/jsconfuser/ast-scrambler.md)** (`ast-scrambler.js`) —
   the *current* (2.0+) version of the same "merge statements into a no-op call"
   idea AntiTooling targeted historically, now with a self-nulling helper instead of
   a permanently-empty one. Must run before every other jsconfuser-specific decoder
   below (only Pack/Integrity/AntiTooling precede it) since it's one of the last
   encoder stages (`Order.AstScrambler = 29`) and its statement-merging can swallow
   the standalone-statement shapes those other decoders pattern-match — confirmed
   empirically with a `dispatcher + controlFlowFlattening + stringConcealing`
   combo, see the visitor doc's own "Interaction with other transforms" section.
5. **[Minify](../visitors/jsconfuser/minify.md)** — no dedicated decode step; a comment at
   this pipeline position explains why (literal shortenings and `var` merging are already
   covered by the generic `calculate-constant-exp.js`/`split-variable-declaration.js`
   passes elsewhere, everything else is destructive-or-already-clearer). Formerly ran
   `deMinifyArrow` here, removed as dead code once confirmed it matched nothing against the
   current pinned encoder — kept as a numbered position so later "step N" cross-references
   in this file don't shift.
6. **[MovedDeclarations](../visitors/jsconfuser/moved-declarations.md)** (shared
   `visitor/split-variable-declaration.js` + `moved-declarations.js`) — split
   `var a, b, c` back into separate declarations, and reverse the transform's
   *parameter packing*: `if (!X) { X = function (…) {…} }` plus an appended
   parameter, back into a real `FunctionDeclaration`. The second half must run
   before anything that identifies structure by looking for a
   `FunctionDeclaration` — most consequentially the ControlFlowFlattening decode
   at step 16, whose entry scan found zero applications on any sample carrying
   `movedDeclarations` and failed the whole block closed while staying
   runtime-correct.
7. **[DuplicateLiteralsRemoval](../visitors/jsconfuser/duplicate-literal.md)**
   (`duplicate-literal.js`) — rewritten 2026-07-22, same failure mode as the
   StringConcealing/GlobalConcealing/OpaquePredicates findings below (found while
   verifying Calculator, fixed in its own later pass): resolves `{ph}_dlrArray`'s
   static contents and inlines them at every indexed read. Placed right after
   MovedDeclarations, before everything else jsconfuser-specific, since this stage
   runs after almost every other optional encode-side transform and its output can
   block Calculator/StringConcealing/etc.'s own decoders from recognizing their
   expected literal shapes otherwise. **Run a second time after the CFF decode at
   step 16** — ControlFlowFlattening (Order 24) is later than
   DuplicateLiteralsRemoval (Order 22) and rewrites part of the array's reference
   sites to index through the CFF state array, which nothing this early can resolve.
   The early pass bails on the array as a unit when it sees such an index, because a
   half-substituted array makes VariableMasking read one slot under two spellings and
   split a single object in two; the late pass then resolves the array completely,
   still ahead of Lock/RGF/Dispatcher/Flatten's own literal-key matchers. The array
   is matched in **two spellings**: its own `var arr = [...]`, and the hoisted
   `var arr;` + `arr = [...]` pair MovedDeclarations (Order 25, later still) splits
   that into. Only accepting the first left every `high` sample carrying the split
   spelling — and every VariableMasking key inside its array — entirely undecoded.
8. **[VariableMasking](../visitors/jsconfuser/variable-masking.md)**
   (`variable-masking.js` + `function-length.js`) — run **three times**:
   `variable-masking.js` again after StringConcealing/StringSplitting below, since
   resolving concealed/split strings can unblock rest-param cache lookups that were
   previously unreadable; and a third time immediately after
   DuplicateLiteralsRemoval's late pass at step 16. That third pass exists because
   DuplicateLiteralsRemoval (Order 22) extracts VariableMasking's (Order 20) own mask
   keys, so until the array resolves a slot reads `stk[arr[4]]` — unmatchable to every
   matcher in the file, truncation statement included, which leaves the whole enclosing
   function masked rather than partly decoded (added 2026-07-27). Split 2026-07-22 out of a single combined `stack.js`
   file (decode-js's own pre-2.0 name for this transform) into two files along a
   real seam: `variable-masking.js` holds the rest-param/slot-alias reversal itself
   (`processStackParam` and its helper chain, exported for reuse); `function-length.js`
   holds the separate, cross-cutting reversal of the shared `preserveFunctionLength`
   wrapper (`{ph}_fnLength(fn, length)`) any of Dispatcher/Flatten/RGF/VariableMasking
   can produce — it imports `processStackParam` from `variable-masking.js` once it
   unwraps a wrapper and learns the target function's real param count that way
   instead. `function-length.js`'s matcher had two bugs fixed while verifying
   [RGF](../visitors/jsconfuser/rgf.md) against real `preserveFunctionLength` output
   (see that doc's "Known gap" section, from before the split); a third, deeper gap
   (functions using `preserveFunctionLength` *without* a rest-masked param at all -
   e.g. RGF's own zero-param `return {ph}[0].apply(...)` stub) crashed
   `checkStackInvalid` until fixed 2026-07-23 with a `hasRestParam` guard in
   `function-length.js` that skips the `processStackParam` handoff (the wrapper
   itself still gets stripped either way).
   **Fully covered as of 2026-07-22** — three more gaps found and fixed while finishing
   this transform's own worklist item: a real correctness bug in alias-collapsing when
   a masked param is reassigned after being aliased, a length-discovery fallback for
   the common "predictable" case (no truncation statement to read the real param count
   from), and a negative-integer-mask-key blind spot in the shared `safeGetName`. See
   [variable-masking.md](../visitors/jsconfuser/variable-masking.md)'s own "Known
   gaps" section for the two narrower gaps still open from that pass.
9. **StringCompression** (`string-compression.js`) — an LZW-style compressor, removed from
   the encoder at
   [`309adba`](https://github.com/MichaelXF/js-confuser/commit/309adba); no current-version
   equivalent, and no `StringCompression`/`Shuffle`/compression-template trace remains
   anywhere in the pinned source. **Present through 2.0.1, gone from 2.1.2 on** — so it
   shipped in released versions for roughly eighteen months, which is what justifies keeping
   the decoder. Unlike AntiTooling above it was not removed by the 2.0 rewrite; it survived
   into 2.x and was cut separately.
10. **[StringConcealing](../visitors/jsconfuser/string-concealing.md)**
   (`string-concealing.js`, `deStringConcealingInit` — evaluated in an isolated-vm
   sandbox, not structurally parsed). Positioned here (before
   StringSplitting/VariableMasking's second pass) because that second
   `variable-masking.js` pass below depends on strings already being resolved.
11. **[Calculator](../visitors/jsconfuser/calculator.md)** (`calculator.js`) — unwraps
    the `{ph}_calc(operator, a, b)` dispatch call back to a plain `BinaryExpression`;
    relies on the very next step's generic fold to finish reducing it to a literal, no
    arithmetic logic of its own. Must run after StringConcealing above since the
    dispatch function's own operator-key strings get concealed just like any other
    string literal.
12. **StringSplitting** (shared `visitor/calculate-constant-exp.js`) — generic constant
    folding does double duty here (including finishing Calculator's fold, above).
13. **[OpaquePredicates](../visitors/jsconfuser/opaque-predicates.md)**
    (`opaque-predicates.js`, `dePredicateGenInit` for the pinned mechanism, plus shared
    `calculate-constant-exp` + `visitor/prune-if-branch.js`).
14. **[DeadCode](../visitors/jsconfuser/dead-code.md)** (`dead-code.js`) — must run
    *after* OpaquePredicates above: OpaquePredicates' own `IfStatement` wrapping fires
    generically on every if, including ones DeadCode already inserted
    (`if(!(x1 in dummy1) && (x2 in dummy2))`), so OpaquePredicates' fold has to unwrap
    that composed shape back to bare `x2 in dummy2` before DeadCode's own matcher can
    recognize it again.
15. **[GlobalConcealing](../visitors/jsconfuser/global-concealing.md)**
    (`global-concealing.js`). Positioned after StringConcealing since a switch case's
    key or a call site's argument could itself have been string-concealed.
16. **[ControlFlowFlattening](../visitors/jsconfuser/control-flow.md)** — two
    visitors, both from `control-flow-graph.js`/`control-flow.js`, run in this order:
    - `deControlFlowFlatteningGraphInit()` (`control-flow-graph.js`) — the main
      mechanism, and **fully covered**. Finds every CFF application in
      the file (all three entry-harness shapes: Function level, Function level with
      a nested function, and bare Program level) and replaces each with a fully
      decoded body: walks the `while(sum(states)!==END) switch(sum(states)){...}`
      dispatcher into a transition graph, resolves it into a small DAG of real blocks
      in execution order, undoes literal entanglement in place using
      `control-flow.js`'s resolver (every mangled number/boolean/string reduces to
      arithmetic over a known per-block state vector), folds the DAG into plain
      statements, and recursively decodes any "outlined nested functions" CFF
      produces the same way. Confirmed end-to-end against real obfuscated samples,
      including executing the reconstructed code live and comparing its output to
      the original.
    - `deControlFlowFlatteningStateless` (`control-flow.js`) — a separate, minor
      constant-lookup-object decoy sub-case unrelated to the state-vector mechanism
      above. **Legacy, pre-2.0** (targets the `controlVar`
      mechanism introduced in the encoder's `09aef99` and removed by the 2.0 rewrite
      `dd408e8`), same class as AntiTooling/StringCompression below — see
      [control-flow.md](../visitors/jsconfuser/control-flow.md)'s Status section for the
      full citation. Runs after the graph-based pass.

    See [control-flow.md](../visitors/jsconfuser/control-flow.md) for the full
    algorithm, every bug found along the way (including two only surfaced by
    stress-testing fresh, non-frozen `obfuscate()` runs rather than the frozen test
    fixtures), and its own "What this doesn't do yet" section.

    **Every pass from here to the next numbered entry is a re-run**, and for one shared reason: on a
    `high` sample the whole program sits inside the CFF interpreter while the earlier
    passes run, so the shapes they match do not exist yet and they decode nothing at
    all. DuplicateLiteralsRemoval, VariableMasking, the string layer
    (StringCompression + StringConcealing), GlobalConcealing, then OpaquePredicates and
    DeadCode each get a second visit here — each keeps its earlier position too, which
    still fires on whatever is already at Program level. Their individual reasons are on
    their own pages and in the source comments; the ordering constraint they share is that
    everything below reads shapes only these produce.

    **GlobalConcealing's second visit is the one that shows why "after the CFF decode" is
    not a slot.** Its matcher reads four independent properties of the switch function, and
    the CFF decode restores none of them: the function comes back with a rest param, the
    string-decode wrappers standing as extra statements ahead of the switch, a discriminant
    that is not the param, and case tests still spelled as `{ph}_STR_N(a, b)` calls. Those
    are cleared by VariableMasking, then StringConcealing, then the fold after it — so this
    pass sits *after all three*, later than every other member of this block. See
    [global-concealing.md](../visitors/jsconfuser/global-concealing.md)'s Upstream Effects.

    One pass in this block runs *only* here: **`deScopeAnchorCleanupInit()`**
    (`control-flow-graph.js`), which drops the `scope[scopeProperty] = {}` statements
    the CFF decode above orphans when it flattens their readers away. It belongs to
    that decode but cannot run inside it — judging an anchor dead means reading every
    other member key on the same holder, and until the string passes directly above
    have run those keys are unevaluated `{ph}_STR_N(a, b)` calls, which its
    unreadable-key guard correctly refuses to rule out. See
    [control-flow.md](../visitors/jsconfuser/control-flow.md).
17. **[Lock](../visitors/jsconfuser/lock.md)** (`lock.js`) — all six Lock sub-features:
    antiDebug, selfDefending, dateLock, domainLock, tamperProtection, and
    `invokeCountermeasures` dead-code cleanup. Placed late, right before RGF, for
    the same reason as Flatten below: `Order.Lock` runs early on the encode side (right
    after Flatten), so its output is reshaped by nearly every later transform.
18. **[RGF](../visitors/jsconfuser/rgf.md)** (`rgf.js`) — recursively decodes each
    `eval`-wrapped sub-program with this same pipeline (a direct, controlled circular
    import of this file's own default export), then splices the recovered params/body
    back onto the original function. Placed after the index-literal-folding
    `calculate-constant-exp` passes above and right before Dispatcher, for the same
    exposure reason as Lock and Flatten — none of RGF's own inserted scaffolding is
    `path.skip()`-protected on the encode side either.
19. **[Dispatcher](../visitors/jsconfuser/dispatcher.md)** (`dispatcher.js`) — per block
    (`Program` or any function body), rebuilds every dispatched function as a plain
    declaration and rewrites call sites back to direct calls/references. Needs
    `variable-masking.js`'s pass above to have already reversed VariableMasking's
    rest-param masking on the dispatcher function's own signature (see that visitor
    doc's "Upstream Effects", which also covers why this pass drives `unmaskStack`
    itself rather than waiting for it).

    Immediately after it, **`deCffHelperCleanupInit()`** (`control-flow-graph.js`) runs a
    second `cleanupOrphanedCffHelpers` sweep. It belongs to the CFF decode at step 16 but
    cannot finish there: the dispatcher template is routinely the last thing referencing a
    CFF runtime helper, so the sweep inside that decode correctly declines on all four and
    only this one, after the template is gone, can remove them. Same shape as
    `deScopeAnchorCleanupInit()` above — a cleanup that belongs to one pass but is only
    well-defined after a later one. See
    [control-flow.md](../visitors/jsconfuser/control-flow.md).
20. **[Flatten](../visitors/jsconfuser/flatten.md)** (`flatten.js`) — placed after most
    other steps since Flatten runs earliest on the encode side (`Order.Flatten = 2`), so
    its output is reshaped by every later encode transform; decoding it after everything
    else above gives it the most-representative, most-processed input a real sample
    would show.

    Immediately after it, **`deStringConcealingPlaceAssign`**
    ([string-concealing.js](../visitors/jsconfuser/string-concealing.md)) runs the
    `<name> = "literal"` half of the placement reversal, deferred from step 14. Same shape
    as the two cleanups above — a pass that belongs earlier but is only safe once a later
    one has read what it destroys. It inlines the literal into every forward reference and
    deletes the binding, and the Flatten accessor records the outer variable it proxies
    *as an identifier*, so running it at its original slot erased the only record of that
    identity and `deFlatten` then declined on the whole scope object. Its array/object
    siblings stay at step 14, where Dispatcher needs their `StringLiteral`s.
21. **[Finalizer](../../js-confuser/transforms/finalizer.md)** (shared
    `visitor/delete-extra.js`, newly wired in) — re-escapes `hexadecimalNumbers`/
    `stringEncoding`'s raw source text back to plain form; Babel's generator prefers a
    literal's `node.extra.raw` over its parsed `value` when present, so without this the
    escaped/hex form would print back out unchanged even though the parsed value was
    never actually altered. Placed last since Finalizer is the encoder's second-to-last
    stage (`Order.Finalizer = 35`, only `Pack`/`Integrity` run later on the encode side).

Then generate with `comments: false, jsescOption: { minimal: true }`.

## Coverage by encoder stage

Every js-confuser transform is covered, and each has its own decoder-side page. The table
maps the encoder's own `Order` enum (`encoder/js-confuser/src/order.ts`) onto the visitor
that reverses it — the mapping
[encoder-decoder-method.md](../../encoder-decoder-method.md)'s T1 asks you to have before
deciding what to fix first, since the fix order is the *encoder's* order reversed and not
this plugin's pipeline order above. A "none" row is a transform with nothing to reverse;
its page says why.

| Order | Transform | Visitor | Decoder page |
|---|---|---|---|
| 0 | Preparation | none — encode-only setup | [preparation](../visitors/jsconfuser/preparation.md) |
| 1 | ObjectExtraction | none — irreversible on real output | [object-extraction](../visitors/jsconfuser/object-extraction.md) |
| 2 | Flatten | `flatten.js` | [flatten](../visitors/jsconfuser/flatten.md) |
| 3 | Lock | `lock.js` | [lock](../visitors/jsconfuser/lock.md) |
| 4 | RGF | `rgf.js` | [rgf](../visitors/jsconfuser/rgf.md) |
| 6 | Dispatcher | `dispatcher.js` | [dispatcher](../visitors/jsconfuser/dispatcher.md) |
| 8 | DeadCode | `dead-code.js` | [dead-code](../visitors/jsconfuser/dead-code.md) |
| 9 | Calculator | `calculator.js` | [calculator](../visitors/jsconfuser/calculator.md) |
| 12 | GlobalConcealing | `global-concealing.js` | [global-concealing](../visitors/jsconfuser/global-concealing.md) |
| 13 | OpaquePredicates | `opaque-predicates.js` | [opaque-predicates](../visitors/jsconfuser/opaque-predicates.md) |
| 16 | StringSplitting | shared `calculate-constant-exp.js` | [string-splitting](../visitors/jsconfuser/string-splitting.md) |
| 17 | StringConcealing | `string-concealing.js` | [string-concealing](../visitors/jsconfuser/string-concealing.md) |
| 20 | VariableMasking | `variable-masking.js` + `function-length.js` | [variable-masking](../visitors/jsconfuser/variable-masking.md) |
| 22 | DuplicateLiteralsRemoval | `duplicate-literal.js` | [duplicate-literal](../visitors/jsconfuser/duplicate-literal.md) |
| 24 | ControlFlowFlattening | `control-flow.js` + `control-flow-graph.js` | [control-flow](../visitors/jsconfuser/control-flow.md) |
| 25 | MovedDeclarations | `moved-declarations.js` + shared `split-variable-declaration.js` | [moved-declarations](../visitors/jsconfuser/moved-declarations.md) |
| 27 | RenameLabels | none — cosmetic | [rename-labels](../visitors/jsconfuser/rename-labels.md) |
| 28 | Minify | none needed | [minify](../visitors/jsconfuser/minify.md) |
| 29 | AstScrambler | `ast-scrambler.js` | [ast-scrambler](../visitors/jsconfuser/ast-scrambler.md) |
| 30 | RenameVariables | none — unrestorable, and it breaks other transforms' matchers | [rename-variables](../visitors/jsconfuser/rename-variables.md) |
| 35 | Finalizer | shared `delete-extra.js` | [finalizer](../visitors/jsconfuser/finalizer.md) |
| 36 | Pack | `pack.js` | [pack](../visitors/jsconfuser/pack.md) |
| 37 | Integrity | `integrity.js` | [integrity](../visitors/jsconfuser/integrity.md) |

`string-compression.js` and `anti-tooling.js` have no `Order` of their own, and are
**unverified: not active in js-confuser 2.1.3**. `stringCompression` was a 1.1.2 option
(LZW-compressed string blobs) and `antiTooling` a 1.1.8 one; neither survived the 2.0.0
Babel rewrite, and no transform or option of either name exists anywhere in the pinned
encoder's source. Both are kept for real-world legacy samples (items 9 and 3 above), so
nothing exercises either against encoder-generated output — `anti-tooling.js` has
hand-written fixtures, `string-compression.js` has none.

**Two covered passes have no population at all on the current corpus, and that is a property
of the corpus rather than of either pass.** The stage breadcrumb
([probes.md](../probes.md)) reports a zero byte delta and no structural-column movement for
both the `lock` and `rgf` stages across every one of their own samples. A zero delta cannot
discriminate — it reads identically whether the work was already done by an earlier pass or the
pass declines on everything ([encoder-decoder-method.md](../../encoder-decoder-method.md) T6,
which is why it says to establish a population *inside* the pass before working it). Both
outputs are source-sized and runtime-correct, which points at the first, but that is an
inference, not a measurement. **The consequence each doc records is that no gate inside either
pass is measurable against this corpus**, so a suspected defect in one can be closed only as "no
population", never as correct — see [lock.md](../visitors/jsconfuser/lock.md) and
[rgf.md](../visitors/jsconfuser/rgf.md) item 5.

**Three passes were found completely non-functional against the pinned encoder while this
table was being filled in** — `string-concealing.js`, `global-concealing.js` and
`duplicate-literal.js`, each silently, each already marked covered, and `opaque-predicates.js`
was a fourth of the same kind. The general rule that came out of it is
[encoder-decoder-method.md](../../encoder-decoder-method.md)'s T8: an inline `// StageName`
label, a code comment, or a "covered" status describes intent at the time it was written and
is never evidence that a matcher still matches current source. The narratives below are kept
because each names the *shape* the encoder replaced, which is what a legacy sample still
carries.

## Shapes the current encoder replaced

What each silently-dead matcher was actually written against, kept because a real-world
sample predating the 2.0 rewrite still carries these shapes.

**`string-concealing.js` and `global-concealing.js` were both found completely
non-functional against the pinned encoder** (silently, no test coverage existed for
either). Both were rewritten 2026-07-22 (see their own docs for what changed and why); `global.js`, a
shared helper both used, was deleted as dead code superseded by the rewrite — nothing
else referenced it, and its own matcher didn't match the current source either, so there
was nothing left worth preserving for legacy-sample support.

**Same failure mode found again, 2026-07-22, this time in `opaque-predicates.js`.** Its
existing code matched a "Control Object" predicate mechanism that
js-confuser replaced with the much simpler `PredicateGen` (`fbe3449`, 2024-11-10) — the
encoder-side skill docs ([opaque-predicates.md](../../js-confuser/transforms/opaque-predicates.md),
[predicate-gen.md](../../js-confuser/utils/predicate-gen.md)) already correctly described
the *current* mechanism, but the decoder code had never been updated to match its own
docs, so OpaquePredicates was silently non-functional against the pinned commit — verified
empirically (real `opaquePredicates: true` output round-tripped unchanged) before writing
anything. Investigated while checking whether `dead-code.md`'s own hypothesis ("the
existing OpaquePredicates/Calculator/prune-if-branch pipeline already eliminates DeadCode's
dead branches for free, no new decoder needed") held up — it didn't, for the same root
cause: DeadCode's dead-guard predicate is generated by the exact same `PredicateGen`.
Fixed both together: `opaque-predicates.js` gained `dePredicateGenInit` (current
mechanism); a new `dead-code.js` visitor was added; and the shared
`calculate-constant-exp.js` gained a `LogicalExpression` short-circuit fold
(`true && x` -> `x`, etc.) needed to unwrap the `PREDICATE && test` shape both
OpaquePredicates and DeadCode's own OpaquePredicates-wrapped guard leave behind. See
[opaque-predicates.md](../visitors/jsconfuser/opaque-predicates.md) and
[dead-code.md](../visitors/jsconfuser/dead-code.md) for the full mechanism and the
pipeline-ordering interaction this surfaced.

**Same failure mode found a third time, 2026-07-22, in `duplicate-literal.js` — found
while verifying [Calculator](../visitors/jsconfuser/calculator.md), fixed in its own
later pass the same day.** `duplicateLiteralsRemoval: true` output came back completely
undecoded. Traced to the same root cause as the two findings above: `duplicate-literal.js`'s
only matcher (`checkArrayName`) expected an old template — the deduplicated array hidden
behind a getter function, each reference routed through a separate "array warp function" —
but the current pinned encoder (`duplicateLiteralsRemoval.ts`) emits a much simpler direct
`const {ph}_dlrArray = [lit, lit, ...]` with every occurrence (including the first)
replaced by a computed `{ph}_dlrArray[i]` read, no wrapper functions at all. Rewritten
around a direct, evaluation-free array lookup — see
[duplicate-literal.md](../visitors/jsconfuser/duplicate-literal.md) for the full
mechanism, including its interaction with Calculator and StringConcealing (both verified
against real combined encoder output).

## Working facts about this pipeline

Properties of the pipeline as a whole rather than of any one pass — the things that decide
where a new pass goes and how its output should be read.

**Most passes do nothing until the CFF decode has run, because the whole program is still
inside the interpreter until then.** `duplicate-literal`, `variable-masking` and the string
layer each carry a *second*, post-CFF visit for exactly that reason, and those second visits
are worth the most bytes in the pipeline. **A blanket second visit for every remaining pass was
measured and does not work** — each pass needs its own reason for reporting a zero delta at its
first slot, and "schedule it twice" is not one. The instrument that shows which stages report
`+0` is the stage breadcrumb ([probes.md](../probes.md)).

**Transforms whose residue is expected growth, not a decode failure:** `RenameVariables`
(irreversible by design — the original names are gone), `ObjectExtraction`, and dead code left
by `DeadCode`. Judging output size without accounting for these reads a correct decode as a
failed one.

**Orphaned helpers to watch for** when applying
[encoder-decoder-method.md](../../encoder-decoder-method.md)'s S3: a CFF
`cff_hash`/`cff_sum`/`cff_xor`/`cff_slice`/`cff_sequence` function, a string-concealing lookup
table, a duplicate-literals array, and **the `getGlobal` sniffer plus the `bufferToString`
chain it feeds** — the last of these was missing from this list until the two of them turned
out to be the largest single share of decoded output. The removal idiom is reference-count-gated
deletion via `utility/safe-func.js`'s `safeDeleteNode`, as `duplicate-literal.js` already does
for its own array. **Read the count before calling any of them a cleanup bug** — an undeleted
helper here has twice turned out to be held alive by a *different* undecoded layer, so the
residue is a symptom to attribute rather than a sweep to fix.

**The known-clean base combo for CFF work is `{ controlFlowFlattening: 1, dispatcher: true }`.**
Start a CFF investigation from it rather than from a preset, so the shape under test is the only
variable.

**The residual-interpreter count is saturated clean and no longer discriminates.** It was the
gap signature for CFF work and it earned that — but a signature regex once read clean on a
total non-decode, and raw `switch` counts are polluted the moment `dispatcher` is in the combo.
For any new `high` work the live signals are the readability pair, size ratio and orphan
residue. **Don't build another interpreter scoreboard expecting it to find things.**
