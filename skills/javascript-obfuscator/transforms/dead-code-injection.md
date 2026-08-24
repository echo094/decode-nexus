# Dead-code injection

One `DeadCodeInjection` (3) transformer, `DeadCodeInjectionTransformer`, gated on
`deadCodeInjection` with a `deadCodeInjectionThreshold` probability. It wraps block statements in a
branch whose test is decidable at a glance, putting a copy of *other* code from the same program
down the path that never runs.

A second file sits in the same directory and is **not** part of this transform:
`DeadCodeInjectionIdentifiersTransformer` declares `RenameIdentifiers` (7), so it belongs to that
stage. Directory membership is not stage membership.

## 1. Target

**Bulk that reads as real code.** Injected filler is only useful if it resists being told apart
from the program, so rather than generating plausible statements the transform *reuses the
program's own*: every candidate block is cloned from somewhere else in the same file. The result
carries the same identifier style, the same call shapes and the same nesting as its host, because
it is the same code.

What it deliberately does not attempt is hiding the *branch*. The test is a comparison of two
string literals, and both operands are constants at the moment they are written, so the taken path
is fixed at encode time — the protection is the reader's cost of following a plausible-looking
branch, not any ambiguity about which way it goes.

## 2. Algorithm

Three phases, the first two in the `DeadCodeInjection` stage traversal and the third in a second
stage that varies by era (item 3).

1. **Collect** (`prepareNode`, on entering the `Program`). Walk the whole program and clone every
   block statement that passes the donor gate; make its identifiers unique so the copy cannot
   collide with the original; keep the clones in a pool.
2. **Inject** (`transformNode`, on leaving each block statement). With probability
   `deadCodeInjectionThreshold`, replace the block with a wrapper holding an `if` whose two
   branches are the original block and a randomly chosen clone.
3. **Restore** (`restoreNode`, in the later stage). The clone is not planted directly — it is
   parked inside a *host* node, a block containing a function declaration, so that intervening
   stages treat it as ordinary in-scope code. The third phase unwraps each host, replacing it with
   the function's body.

**The wrapper's test is built so the taken branch is always the original.** Two independent coin
flips decide the operator and whether the two strings match, and the pair is then ordered to
match:

| operator | right string | test evaluates | branch order |
|---|---|---|---|
| `===` | same as left | true | `[original, clone]` |
| `===` | different | false | `[clone, original]` |
| `!==` | same as left | false | `[clone, original]` |
| `!==` | different | true | `[original, clone]` |

So all four spellings occur, and in every one the clone sits on the dead path. Both operands are
five-character random strings.

**The donor gate is what bounds how much a given program can be injected with.** A block qualifies
only if it is non-empty, nests no deeper than a fixed block count, and contains none of:
a function declaration, `break`, `continue`, `await`, `yield`, `super`, or a `for await`. A program
of small functions with early `return`s therefore donates little, and a program whose blocks all
carry `break`/`continue` — a `switch`-heavy one — can donate nothing at all, at which point the
transform has nothing to inject regardless of threshold.

## 3. Implementation

The host node is `{ function <name>() { <clone> } }`, held in a `Set` on the transformer instance
and recognised later by **object identity** on that block node, not by name or shape.

**Which stage performs the restore is the axis this transform has**, and it moves twice:

| Era | Restore stage | Consequence for what is emitted |
|---|---|---|
| `E-dci-host-finalizing` | `Finalizing` (10) | the restore runs after `StringArray` (8) and `Simplifying` (9). Where an intervening stage has replaced a host block node rather than mutating it, the `Set`'s identity check no longer matches and that host is never unwrapped — so the function declaration survives into the output |
| `E-dci-host-renameidents` | `RenameIdentifiers` (7) | the restore runs before those stages, and the host does not survive |
| `E-dci-host-stringarray` | `StringArray` (8) | outside phase 1's range; not read in output |

Rows, ranges and the commits each was verified at: [versions.md](../versions.md)'s
`E-dci-host-*`.

**The surviving host is observable and specific**: a function declaration with zero references,
nested inside the block the injection wrapped, its body holding the uniquified clone. It sits on
the branch the test does not take, along with the rest of the clone.

`deadCodeInjection` also forces `stringArray: true` through `DeadCodeInjectionRule`, and forces a
non-zero `stringArrayThreshold` when one was not given — so a sample carrying this transform always
carries a string array too.

## 4. Downstream Effects

| Later stage | What it does to this transform's output |
|---|---|
| `RenameIdentifiers` (7) | renames the host function and the clone's already-uniquified identifiers again, so no name emitted here survives |
| `StringArray` (8) | both test operands are five-character strings and go into the array like any other, so the emitted test is a pair of accessor calls rather than two literals. This is the normal spelling: a readable `'abcde' === 'abcde'` reaches the output only where the array's threshold left the string behind |
| `Simplifying` (9) | collapses a single-statement branch, so the emitted `else` is routinely a bare statement (`else return …`) rather than the block this transform built |
| `ControlFlowFlattening` (4) | runs *before* this one, so a block already flattened can be collected as a donor and injected elsewhere — a clone can carry a whole dispatch loop |

## 5. Known Quirks

- **The restore is keyed on node identity, which is why it can fail at all.** At
  `E-dci-host-finalizing` the leak is not a probabilistic effect but a consequence of running the
  identity check after stages that rebuild nodes; upstream moved the stage twice, which is
  consistent with that being the reason, though no changelog entry states it.
- **A leaked host is not a semantic difference.** It is unreferenced and sits on the untaken
  branch, so the program behaves identically either side of the boundary; only the emitted text
  differs.
- **`deadCodeInjectionThreshold` at `1` does not mean every block is wrapped.** The donor gate
  runs first, and injection needs a non-empty pool, so a program that donates nothing emits nothing
  from this transform at any threshold.

## Source

- `src/node-transformers/dead-code-injection-transformers/DeadCodeInjectionTransformer.ts` — the
  three phases, the donor gate, the host set
- `src/custom-nodes/dead-code-injection-nodes/BlockStatementDeadCodeInjectionNode.ts` — the wrapper
  structure and the four test spellings in item 2
- `src/options/normalizer-rules/DeadCodeInjectionRule.ts` — the forced `stringArray`

Item 3's table says why the restore stage is the thing to key an era on rather than either file's
content: both files hold still across the whole of phase 1 except for an `estraverse` import path
and an `override` keyword, neither of which changes what is emitted.

## Fixtures

| Claim | Where it is read |
|---|---|
| the wrapper's test always leaves the clone on the dead path | the corpus's `dead-code` set at every version column — the injected `if`s are all `X === X` or `X !== Y` shaped, with the original on the taken side |
| both operands arrive as string-array accessor calls, not literals | same cells: a census keyed on readable string literals finds none, one keyed on the comparison finds them |
| the host leaks below the boundary and not above it | `2.15.2/control__dead-code.js` against `2.15.3/control__dead-code.js` — two zero-reference function declarations inside `classify` at the former, none at the latter, same seed and same fixture |
| a `switch`-heavy input donates nothing | not covered: all three corpus inputs donate, so the empty-pool case has no cell |

The `2.15.2` column was appended for the third row and holds only the `dead-code` set; the corpus
is append-only, so this added cells without disturbing any that existed
([corpus.md](../corpus.md)).
