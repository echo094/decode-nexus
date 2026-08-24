# unflatten-switch-dispatch.js

`obfuscatorx`'s reversal of javascript-obfuscator's block-statement control-flow flattening — the
`while (true) { switch (order[index++]) { … } break; }` whose execution order is carried by a
`"|"`-joined string of case indexes.

A fork of the shared [remove-control-flow-ob.js](../remove-control-flow-ob.md), not an import. The
reason is in item 5.

## 1. Target

Restore a flattened block's statements to source order, or leave the block exactly as found. There
is no partial outcome: the statements are not rewritten by the encoder, only reordered, so a
correct reversal returns the original list and a refusal costs only legible residue.

## 2. Algorithm

**A permutation read, in one step.** The controller string holds, for each original statement
position, the index of the case that now carries it — the encoder builds it as
`originalKeys.map((k) => shuffledKeys.indexOf(k))`
([control-flow-block-flattening.md](../../../javascript-obfuscator/transforms/control-flow-block-flattening.md)).
So reading it left to right and indexing the case list recovers the original order directly. No
scanning, no walking forward, no state.

Every invariant is checked **before any mutation**. `match()` either returns everything the rewrite
needs or returns `null`, and only then are the two control declarations removed and the loop
replaced. That is what makes a decline safe: there is no point at which the pass has half-applied
itself and then found a reason to stop.

## 3. Implementation

The gates, in the order `match()` applies them:

| Gate | Accepts |
|---|---|
| loop test | `true` **only** — a `BooleanLiteral`, never a general prefix unary |
| loop body | exactly `[SwitchStatement, BreakStatement]`, the `break` unlabelled |
| discriminant | `<identifier>[<identifier>++]`, verified in full before any field is read |
| case tests | `'0' … 'n-1'`, ascending, no `default` |
| consequents | each exactly `[statement, continue]`, a lone `return`, or a bare `continue` — the third being an **empty** case, see below; a leading string statement is omitted only when it matches an already-emitted scope directive in source-prologue position |
| control declarations | both found as declarators in a **preceding sibling declaration** in the same block |
| index initialiser | numeric `0` |
| order string | `'…'.split('|')` after folding; a permutation of the case indexes, same length, no repeats |
| liveness | neither control name is mentioned anywhere outside the loop |

**The loop test admits only a literal `true`, which makes the boolean fold a precondition.** The
encoder emits `while (!![])`, so this pass cannot run before the `Converting` reversal has folded
it. That is deliberate: the alternative — accepting any prefix unary, as the shared visitor does —
also accepts `while (!done)`, and rewriting that destroys an ordinary loop.

**Declarations are resolved by scanning previous siblings, not through `scope.getBinding()`.** Two
separate reasons, and both were paid for:

- **Dominance.** A binding lookup happily resolves `if (x) { var C = …; var I = 0; }` because `var`
  hoists — but the *initialisation* is conditional, and rewriting the block then runs statements
  the original does not. Requiring the declaration to precede the loop as a sibling is a cheap
  sufficient condition.
- **Staleness.** `scope.getBinding()` returns a path recorded at the last crawl, and every pass
  scheduled before this one replaces nodes. The binding then points at a detached node that still
  prints identically to the live one, so identity comparisons against it fail silently. Measured:
  a binding-based version accepted every hand-built case and rejected **all 108** live corpus
  blocks, because only the hand-built trees had never been rewritten.

The `simplify` option fuses the two declarations into one statement with two declarators; the
sibling scan walks each declaration's declarator list, so that spelling needs no special case.

**An empty case is a third accepted consequent, and the encoder produces it without help.**
Control-flow flattening runs at stage 4 and puts a function's leading `'use strict'` into a case
like any other statement; `DirectivePlacementTransformer` then re-emits that directive at the top
of the scope during `Finalizing`, leaving the case it came from holding nothing but its `continue`.
**Any flattened function whose body opens with a directive lands here**, which is a large slice of
real-world input rather than a corner.

- **Omitting the slot is the entire reversal.** The order string is a permutation, so the case is
  visited exactly once, and executing it does nothing but return to the loop.
- **The sentinel is distinct from the reject signal**, deliberately: `readConsequent` returns
  `null` to mean "do not touch this block" and a separate `EMPTY_CASE` to mean "skip this slot".
  Collapsing the two would turn a directive-bearing function into a decline again, silently.
- **Empty cases are filtered after the permutation check**, not at the gate, so that check still
  sees every index and an order string disagreeing with the case list is still refused.
- **Every case empty removes the loop outright.** `replaceWithMultiple([])` is not a removal, so
  that path asks for one explicitly. The encoder has no reason to flatten a body holding only a
  directive, so this branch is ours rather than the encoder's, and is pinned by a hand-built case.

**From `5.2.0`, the same producer leaves the original directive inside the case instead.**
`DirectivePlacementTransformer` still prepends its clone, but its new direct-body filter cannot
reach the identity after flattening nested it. The permutation therefore reconstructs an ordinary
string expression beside a real scope directive unless this pass recognizes the duplicate.

- The pass reads the enclosing scope's directive list before mutation and consumes a matching
  reconstructed string only while it is still in the original directive-prologue prefix.
- A later identical string expression is preserved. Matching by value everywhere would corrupt
  ordinary executable content, so source position is part of the gate.
- The old empty spelling and the new retained spelling converge on the same reconstruction; there
  is no version branch.

## 4. Upstream Effects

| Shape | Producing pass | Ours or the encoder's | Era |
|---|---|---|---|
| `while (!![])` instead of `while (true)` | the encoder's `Converting` stage | encoder's — folded by [normalize-converting.md](normalize-converting.md), which **must** run first | all read eras — `E-boolean-double-negation-array`, one era over the whole range |
| the order string as `S['k']['split']('\|')` | the encoder's own sibling transformer, which lifts any string of length ≥ 3 into the control-flow storage | encoder's — resolved by the storage pass, which **must** run first | all read eras — `E-cff-storage-object` spans `2.9.6 – 3.1.0` in one era. Its **upper bound is inside phase 2's reach**, so this is the row to re-read at `5.5.0` rather than carry forward |
| the order string as a `+` chain | the encoder's `splitStrings` | encoder's — folded by constant folding | all read eras — `E-splitstring-two-pass`, one era over the whole range. Its transformer's *content* moves three times inside phase 1 and none of the three moves a node, which is why the row exists rather than being inferred |
| `case '\x30'` | the encoder's `Finalizing` escape sequences | encoder's — the parser decodes it; the pass compares `value`, never `raw` | all read eras, **and past them**: comparing `value` makes this row indifferent to `E-escape-from-value` (`2.9.6 – 5.4.3`) versus `E-escape-from-raw` (`5.4.6 – 5.5.0`), since the two differ only in which spelling the encoder starts from |
| one `var C = …, I = 0;` instead of two declarations | the encoder's `Simplifying` stage | encoder's — handled by the declarator scan | all read eras, on a single-era axis: `E-adjacent-merge-pairwise` spans `2.9.6 – 5.5.0` entire |
| a leading directive case is empty, or retains the same string beside a prepended scope directive | the encoder's `Finalizing` directive placement | encoder's — both converge by omitting only the matching reconstructed prologue copy | `E-directive-rehoist-no-residual` through `5.1.0`; `E-directive-rehoist-nested-residual` from `5.2.0` |
| a flattened block inside an unreachable branch, whose controller storage was left behind in the scope the branch was copied *from* | the encoder's `DeadCodeInjection` stage | encoder's — removed by [prune-if-branch](../prune-if-branch.md) once the predicate is folded | **two eras, and this is the row the column exists for.** `E-dci-host-*` moves at `2.15.3`: below it the restore runs late enough to strand a zero-reference function declaration holding the clone, above it no host survives. Both are in the corpus and the `flattened-block` axis reads zero at every column, so the removal covers both — but the shape reaching this pass is genuinely not the same on the two sides |

**`prune-if-branch` is load-bearing in the group, not tidying.** Dead-code injection copies a block
into a scope whose storage does not hold its controller, so this pass — correctly — declines those
copies: the order string is unresolvable there, and there is nothing to read. They are removed
instead, as unreachable code, by folding the injected predicate and pruning the branch. Measured by
re-running the composition with the prune omitted: the residue census then stays non-zero on
`flattened-block`, on exactly the copies whose storage was stranded. **So this axis's zero is
earned two ways at once** — live blocks are un-flattened, unreachable copies are deleted — and only
the first is this pass's work. Anything reading the zero as "every flattened block was reversed"
is reading it wrong.

**There is a third way, and for three of the four inputs it accounts for all of this pass's
remaining work: the block it un-flattens is then deleted by [unlock-env](unlock-env.md).** Measured
by removing this pass from the composed pipeline and diffing final output — on the `strings`,
`control` and `objects` flattening cells at every column the output is **byte-identical once the
strip has run** and **differs if the strip is omitted**, while the pass reports exactly one rewrite
per cell. So it is doing real work there: not declining, not candidate-less. But every trace of
that work lands inside anti-tamper machinery the strip removes wholesale, so on those cells it has
**no observable effect on final output**. It reads *inert* to any instrument measuring the pipeline
through its output, and that is a true reading of those cells rather than a broken probe.

**That inertness used to hold corpus-wide, and no longer does — the prediction this paragraph made
has been met.** It said: *a sample whose program blocks are flattened outside a stripped helper is
the case the corpus does not contain, and it is the one this pass exists for.* The corpus gained a
fourth input, and `directives__cff` is exactly that sample — a flattened **program** function, not
a helper. Removing this pass from the pipeline changes that cell's final output at every column
where it exists, so the pass is measurably load-bearing there and the attribution ladder's `-` no
longer describes the whole matrix.

**The lesson is about the instrument, not the pass.** An inert reading was correct, stable across
twenty-two option sets and ten columns, and was a fact about **what those three inputs contain**
rather than about the pass or the encoder. Nothing in the option axis could have disturbed it,
because options decide which transforms are *enabled* and inputs decide which have anything to act
on. So a pass can look dead across an entire frozen matrix and be doing the work it exists for on
the first input that reaches it.

**The hard ordering constraint is the storage pass**, and it is not a preference: across the frozen
corpus, **no** flattened block's controller reaches this pass as a bare string literal until the
storage read has been inlined. Scheduling this pass first makes it inert, not wrong.

**That constraint makes this pass a member of a fixpoint group rather than a stage in a line.** The
storage reversal re-opens Converting work when it inlines a string into computed-member-key
position ([normalize-converting.md](normalize-converting.md)'s Upstream Effects), so the group —
Converting, storage, folding, this pass — repeats until the tree stops moving. Two of this pass's
own preconditions are why it has to sit *inside* that loop rather than after it: an un-flattened
outer block can expose an inner one that was not a `while { switch; break }` when the round began,
and the loop test admits only a folded literal `true`.

## 5. Known Gaps

- **It declines a block whose control declarations are not preceding siblings.** Legitimate — see
  the dominance argument in item 3 — but it does mean a tree some earlier pass has restructured can
  fall out of scope. Nothing in the corpus does this.
- **It has no branch for a `default` case or for genuine fallthrough**, by choice. Both are shapes
  this encoder never emits, and accepting them is what makes the shared visitor duplicate
  statements.

**This pass fires and is still invisible in the pipeline's output, on every option profile of the
spine column.** Measured by disabling one pass at a time and diffing that profile's own output:
removing it changes nothing anywhere, even though it demonstrably resolves dispatches. Two other
passes cover its work here — **`prune-if-branch` removes the dead-code clones** (the encoder copies
flattened blocks into scopes that do not hold their controller storage, so this pass rightly
declines them and the prune deletes them as unreachable), and **`unlock-env` deletes the anti-tamper
regions wholesale**, taking any dispatch inside them with it. On one maximal cell that is 3 clones
pruned and 1 resolved dispatch sitting inside machinery the strip removes.

**That is not an argument for deleting it**, and the distinction is W7's: the measurement is
evidence about this encoder's corpus, not about the pass. It would be load-bearing wherever
flattening lands on live code that survives both — which these fixtures do not produce, and which
nothing guarantees a real sample will not. The pass's own coverage is its fixtures, not the corpus.
**Anyone re-measuring this must run the whole pipeline including the strip:** a probe cut off before
`unlock-env` shows a dispatch surviving and contradicts the result.

**Why this is a fork rather than an import.** The shared visitor reaches byte-identical output on
this encoder — verified on all 567 corpus cells — so the fork buys nothing on the corpus. It buys
behaviour off it: three of the shared visitor's four off-path behaviours corrupt or crash rather
than decline, and §3.3 forbids narrowing a shared visitor, since two other plugins consume it. The
decision and its evidence are recorded in
[remove-control-flow-ob.md](../remove-control-flow-ob.md)'s Known Gaps.

## Source

- `src/visitor/obfuscator/unflatten-switch-dispatch.js` — the pass
- `test/visitor/obfuscator/unflatten-switch-dispatch/` — the fixtures below

Exports `createUnflattenSwitchDispatch(onChange)` plus a default instance. The `onChange` channel
lets a caller run a pipeline to a fixpoint without re-serializing the tree, which the shared
visitor cannot offer. Wired as the **last pass of each round** of
[`src/plugin/obfuscatorx.js`](https://github.com/echo094/decode-js/blob/6cacb633ceedf0812fe31f951ba8f41ffb431ca1/src/plugin/obfuscatorx.js)'s fixpoint
group — after the control-flow storage pass, after constant folding and after `prune-if-branch`;
item 4 says why that position is forced.

## Fixtures

| Claim | Fixture |
|---|---|
| a flattened block is restored to source order | `baseline` |
| the `simplify`-fused declaration is handled | `merged-declaration` |
| an ordinary `while (!done)` loop is declined, not rewritten | `not-always-true` |
| a case without `continue`/`return` is declined, not duplicated | `fallthrough-case` |
| a discriminant without `++` is declined, not thrown on | `no-increment` |
| a conditionally-initialised controller is declined | `conditional-declaration` |
| an order string disagreeing with the case list is declined | `order-mismatch` |
| a case emptied by directive re-hoisting **drops out** rather than blocking the rewrite | `directive-empty-case` |
| a directive retained in a case from `5.2.0` drops out, while a later identical ordinary string survives | `directive-retained-case` |
| a dispatch whose every case is empty removes the loop outright | `all-cases-empty` |

Files live under `test/visitor/obfuscator/unflatten-switch-dispatch/` and are driven through the
shared `test/helper.js` by `unflatten-switch-dispatch.test.js`. **Only rewriting cases have a
`<name>.fix.js`**; a declining case is `<name>.js` alone, because the helper's no-fix branch
compares the generated tree against the *input source* — for a decline the input is its own
expected output. Both branches compare by exact string equality, which is why every input is stored
without a trailing newline.

**Five fixtures pin a decline**, which is unusual for this fixture set and is the point: the
shared visitor passes the two original rewrite cases and mishandles every decline case — two by corrupting
output silently, one by throwing — so a suite covering only the happy path would not distinguish
the two implementations at all.

**Each case carries two assertions, and neither substitutes for the other.** The tree comparison
says what the pass did to the input; the `onChange` count says what it *reported*, which is the
channel a fixpoint driver schedules on. A decline case asserts both because a zero count means only
that nothing was reported — mutate-then-decline, the shared visitor's own failure mode, reports
nothing either. The rewriting cases additionally get the helper's reference-state comparison, which
matters for this pass specifically: it removes two declarations, so a stale binding left behind for
`order` or `index` fails the case even though the printed output is identical.

**Corpus evidence the fixtures do not carry**, recorded here because it is what justifies the
fixture set being this small: over the frozen corpus the pass un-flattens every live flattened
block, its output is byte-identical to the shared visitor's on all 567 cells, and the decoded
result runs and matches each fixture's own reported lines on every non-anti-tamper cell of all
nine version columns.

**Verified twice, and the second run is the one that means something for a shipped pipeline.** The
first drove each pass as its own probe stage, printing and re-parsing between them; the second ran
the whole composition on **one AST per cell, with no serialization boundary**. That distinction is
not stylistic here: a print/re-parse silently repairs stale scope state, which is precisely the
defect item 3 records this pass having had — so a staged probe is the one instrument guaranteed not
to catch it. Both readings agree, on the residue census and on runtime equivalence.
