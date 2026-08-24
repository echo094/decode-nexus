# normalize-converting.js

Reverses javascript-obfuscator's **`Converting` (6)** stage: every literal, property name and
object literal that stage re-spelled is put back into the form it was written in.

## 1. Target

Recover the spelling, not the meaning. Nothing this stage reverses changed what the program does —
`!![]` is `true`, `0x1` is `1`, `o['foo']` is `o.foo` — so the goal is legibility **and**, more
importantly, restoring the shapes that every later matcher navigates by. A branch test spelled
`!![]` is not recognisably constant to a pass looking for a boolean literal, and a property read
spelled `o[k]` is invisible to a matcher keyed on `o.foo`.

## 2. Algorithm

**Ten of the encoder's eleven `Converting` transformers rewrite one node in place, so ten of the
reversals are single-node rewrites too — and none of them is specific to this obfuscator.** They
therefore live as plain visitors under `src/visitor/`, composable by any plugin, and this file holds
only the scheduling. That division is the same one
[normalize-statements.md](normalize-statements.md) draws.

What is obfuscator-specific is not how to fold a constant. It is knowing that these particular
reversals **unlock each other**, in which order, and that the group must run to a **fixpoint**.

**Why iteration is required rather than tidy.** The encoder's own transforms compose, so a shape
one reversal needs may not exist until another has run. With `splitStrings` enabled a property name
is emitted as a chain — `o['\x66\x6c' + '\x61\x67']` — which is not a string literal at all, so a
member-un-computing pass looking for a string key finds nothing. Folding the chain first creates the
key. This is measured rather than argued: see `## Fixtures`.

**Order within a round, and what each step feeds:**

1. **strip numeric `raw`** — no dependencies, cheapest first
2. **fold constant expressions** — `!![]` → `true`, arithmetic trees → numbers, chunk chains →
   whole strings. This is what *creates* the string keys steps 3 and 4 need
3. **un-compute member reads** — `o["foo"]` → `o.foo`
4. **un-compute property keys** — `["foo"](){}` → `foo(){}`
5. **merge extracted objects** — reassemble `var t = {}; t.a = 1; …` into one literal
6. **collapse shorthand** — last, because it only ever acts on what step 4 produced

**Termination is decided by comparing the tree between rounds, not by counting reported changes.**
Two of the six passes are shared visitors with no change signal to offer, and a shared visitor may
not be edited to add one. Counting only the passes that *can* report would exit a round early
whenever those two were the only ones to fire.

## 3. Implementation

| Reversal | Where it lives | Reuse decision |
|---|---|---|
| numeric `raw` strip | inline here | `NumberLiteralTransformer` changes no AST node — it writes `raw` and leaves `value` — so discarding `extra` **is** the whole reversal. Scoped to numbers: a string literal's `raw` holds escape spelling, which is a different transform's business |
| constant folding | [calculate-constant-exp](../calculate-constant-exp.md) | **imported unchanged.** Covers four residue axes at once — boolean disguises, arithmetic trees, string-chunk chains |
| member un-computing | [atomic/uncompute-member.js](../atomic/uncompute-member.md) | new; the approach is adopted from the existing plugin's inline `FormatMember` |
| key un-computing | [atomic/uncompute-property-key.js](../atomic/uncompute-property-key.md) | new, and a **deliberate improvement** — see below |
| object merging | [merge-object](../merge-object.md) | shared visitor; its Identifier-and-existing-binding gate is fail-closed for ObjectPattern/ArrayPattern declarators, while Identifier merging remains active |
| shorthand collapse | [atomic/collapse-property-shorthand.js](../atomic/collapse-property-shorthand.md) | new; no prior art exists for it |

`E-objkeys-loopbody-prohibited` marks an information boundary rather than a new reversal. Below it,
the encoder can hoist a fresh object out of a non-block loop and thereby lose per-iteration object
identity; this pass may normalize the extracted spelling but cannot reconstruct evaluation
placement that is absent from the emitted program. From that era onward the intact object literal
already occupies the loop body and needs no merge. Exact-tag positive and block-body controls for
all loop forms show that the same era-invariant schedule accepts both shapes while preserving their
different runtime semantics.

**The deliberate improvement, and it is a real semantic defect avoided.** The existing plugin's
inline `FormatComputed` sets `computed = false` for any string-literal key with **no exclusion
list**. Three keys change meaning when un-computed, and this repository's own shared
`safeFunc.uncomputeStringKey` already refuses all three: `{ ["__proto__"]: v }` defines an own
property where `{ "__proto__": v }` sets the prototype; `class C { ["constructor"](){} }` is an
ordinary method where `"constructor"(){}` **is** the class constructor; `static ["prototype"]` is a
runtime error un-computed. So this pass calls the shared guard rather than reimplementing the list.

**Un-computing and de-literalizing are separated for that reason**, and only the first is dangerous.
Once a key is non-computed the rest is pure spelling — `{ "__proto__": v }` and `{ __proto__: v }`
are both the prototype setter, `"constructor"(){}` and `constructor(){}` are both the constructor —
so step 2 needs no exclusion list, only the identifier-form gate.

**`export { foo as foo }` has no pass and needs none.** It parses to the *same* AST as
`export { foo }` — an `ExportSpecifier` whose `local` and `exported` names match — so there is no
node to rewrite, and the generator already prints the short form.

## 4. Upstream Effects

| Earlier pass | What this one inherits | Era |
|---|---|---|
| the string-array decode | **a hard dependency, not a preference.** Until concealed strings are substituted, a property key is a *call* (`o[_0x1a(0x0)]`) rather than a string, so nothing here can match it. Measured: with the string-array pass omitted, two axes stay non-zero over the corpus; with it in place, all ten reach zero | all read eras. The array, wrapper and rotator shapes each move inside the range, but every one of those eras conceals property-name literals the same way, so the dependency is on the subsystem existing rather than on any of its shapes |
| [normalize-statements](normalize-statements.md) | statement boundaries. Object-key extraction's assignment run is emitted *merged* into one sequence expression by the encoder's `Simplifying` stage, so the merge reversal needs those sequences split first | all read eras, and **on a single-era axis** — `E-adjacent-merge-pairwise` spans `2.9.6 – 5.5.0` entire, so this row cannot be era-scoped without the registry gaining a boundary first |
| [inline-control-flow-storage](inline-control-flow-storage.md) | **new input, not merely rearranged input** — and it arrives from a pass this one is normally scheduled *before*. The encoder lifts any string of length ≥ 3 out of a function body into the control-flow storage, and a computed member key qualifies, so `x[S['k']]` becomes `x['length']` only once that storage has been inlined. Member un-computing then has a key that did not exist as a string on the first pass | all read eras — `E-cff-storage-object` spans `2.9.6 – 3.1.0`, covering the whole of phase 1's range in one era. Phase 2's pin is past its upper bound, so this row is the one here that **has** to be re-read at `5.5.0` rather than assumed |

**What the era column does *not* say here, and it is the reason this pass has one at all.** Every
row above reads "all read eras", which is a result rather than a formality: the four `E-objkeys-*`
eras and the two `E-numexpr-*` eras that this pass reverses all sit inside phase 1's range, so the
*subjects* are thoroughly era-varying while the *dependencies* are not. A row that changed with an
era would be a scheduling constraint only some samples impose, and there is none — which is what
lets `obfuscatorx` keep one pass order for every era instead of branching on the detected one.

**So this pass and the control-flow storage reversal are one fixpoint group, not two ordered
stages.** Scheduling Converting once and control flow after it leaves that class of key computed,
and no census axis of *this* pass's own can see it — the shape is created by a later pass, after
this one has already reported clean. The composition that holds is: string array, then
`{ this pass; the storage pass; folding; the block un-flattener }` repeated until the tree stops
moving. The census that reads whether the extra round was needed is the U5 residue census over the
composed output, and cells that use a second round do exist; the run is recorded in `checkpoint.md`
rather than here, because a count of them dies with the corpus.

**This pass's own folding subsumes the shared `calculate-constant-exp` slots**, measured the same
way as the group above: disabling that pass changes the pipeline's output on **no** option profile
of the spine column, because whatever it would fold this pass has already folded. Both slots are
kept anyway — they cost a traversal that finds nothing, and the group is scheduled for shapes this
encoder emits rather than for the ones it happens not to (W7). What the measurement does rule out
is treating the fold slots as *evidence* of anything: a change that appears to depend on them is
depending on something else.

**The one ordering here that is a convenience rather than a constraint**, recorded so nobody
inherits it as a rule: `merge-object` accepts both a string and an identifier property, so it does
not in fact require member and key un-computing to have run. It is scheduled after them because the
merged output then reads dotted. Anything asserting a stricter dependency should reverse the two and
measure.

**The merge guard is not a seventh normalization.** It protects the shared visitor from reading
binding state on an `ObjectPattern` or `ArrayPattern` declarator and leaves those declarators
unchanged. The repair therefore makes the existing schedule safe; it does not add a destructuring
reversal or change the fixpoint's order.

## 5. Known Gaps

- **Two of the residue axes are unreachable against this encoder, for two different reasons**, and
  neither is a gap in coverage that more fixtures would close:
  - **shorthand collapse** — the encoder expands `{ foo }` so renaming can separate the property
    from the binding, and renaming then does, at every setting of `renameGlobals`. Key and value
    differ permanently, so the shape never appears. The pass is kept because the atomic layer is
    plugin-agnostic ([collapse-property-shorthand.md](../atomic/collapse-property-shorthand.md)).
  - **`export { foo as foo }`** — it parses to the same AST as `export { foo }`, so there is nothing
    to detect or rewrite, and the generator prints the short form already.
- **`calculate-constant-exp` folds via `eval` of generated code**, inherited unchanged. Its failure
  mode is a silent `catch`, so a fold that throws is indistinguishable from one that declined.
- **Only one of `E-objkeys`'s four in-range boundaries reaches this pass, and the rest are
  invisible to it.** Object-keys extraction has four eras inside the studied range, but measured by
  sabotage — removing this pass and reading what breaks — the profile moves at **`2.16.0` alone**
  (`E-objkeys-call-prohibited`, where an object containing a call stops being extracted). The
  `2.15.2` boundary turns the axis over *inside* a group of columns whose profiles are byte-for-byte
  identical, so it changes nothing this pass has to do. **That is not a contradiction and is worth
  stating**: an era boundary is a claim about the encoder's emitted shape, not a claim that any
  particular reversal has to care — and reading a registry boundary as automatically decode-relevant
  is how an attribution gets assigned to the wrong axis.
- **A cap of ten rounds is a runaway guard**, not a tuning knob; hitting it is reported and means
  either pathological nesting or two rewrites oscillating.

## Source

- `src/visitor/obfuscator/normalize-converting.js` — the scheduling
- `src/visitor/atomic/uncompute-member.js`, `uncompute-property-key.js`,
  `collapse-property-shorthand.js` — the new single-purpose rewrites
- `src/visitor/calculate-constant-exp.js` — imported unchanged
- `src/visitor/merge-object.js` — shared merge with the Identifier-and-binding refusal gate
- `src/utility/safe-func.js` — `uncomputeStringKey`, the guard the key pass delegates to

Wired as the first pass of each round of
[`src/plugin/obfuscatorx.js`](https://github.com/echo094/decode-js/blob/6cacb633ceedf0812fe31f951ba8f41ffb431ca1/src/plugin/obfuscatorx.js)'s fixpoint
group. That it is a group rather than a line, and why this pass is inside it, is item 4.

## Fixtures

Four golden cases under `test/visitor/obfuscator/normalize-converting/`, each real encoder output
for a source shape taken from upstream's own converting-transformer fixtures, plus three unit cases
that need no fixture. **The goldens were written by a builder that refuses**: it emits nothing
unless the decoded output runs and reproduces the pre-obfuscation source's output exactly, so a
wrong decode cannot be frozen into a golden that exact string equality then makes look
authoritative.

| Fixture / case | The claim it pins |
|---|---|
| `class-member-keys` | computed and quoted class-member keys are restored, and `constructor` stays the constructor. From upstream's `class-field-transformer` fixtures |
| `test/obfuscatorx/2.19.0-class-logical` | the focused producer cell reaches a computed quoted class-method key in real 2.19.0 output and the entry restores it exactly |
| `object-keys-getset` | key extraction is reversed through getter/setter members. From `get-set-property-kind` |
| `literals-and-members` | booleans, hex, numerical expressions, split strings and member reads together, **asserted on the tree**: the three axis counts are zero *and* the values survive |
| `object-pattern-shorthand` | the pass leaves a renamed pattern alone rather than corrupting it — and pins that shorthand collapse is unreachable here |
| dangerous keys are never un-computed | `["__proto__"]`, `["constructor"]`, `static ["prototype"]` all keep their brackets |
| ordinary keys **are** un-computed | the guard above is not vacuous — a safe key in the same positions is rewritten |
| `__proto__` is never collapsed to shorthand | the mirror-image hazard, with a safe sibling in the same literal that *is* collapsed |

**A text-level residue assertion does not work on this decoder's output**, and the first version of
`literals-and-members` proved it: `/0x[0-9a-f]/i` fails on a correct decode because renaming leaves
`_0x185301` identifiers everywhere. Assert on the shape the census reads, not on the text.

Corpus-wide evidence, which no fixture replaces:

| Claim | What checks it |
|---|---|
| all ten residue axes reach zero on every cell | the U4 census over the whole corpus after this pass, against the same census on the inputs as a paired control |
| the string-array dependency is real | the same census with the string-array pass omitted — two axes stay non-zero |
| the reversals unlock each other | the count of un-computable member reads on one `splitStrings` cell, before and after folding: it rises by roughly an order of magnitude |
| the output still runs | each decoded cell executed against its fixture's own reported lines, excluding cells carrying anti-tamper, which is a later unit's |

The shared guard and its exact static-block consumer are pinned outside the four normalization
goldens: [`merge-object.test.js`](https://github.com/echo094/decode-js/blob/6cacb633ceedf0812fe31f951ba8f41ffb431ca1/test/visitor/merge-object.test.js)
asserts the two safe refusals and the unchanged Identifier merge, while
[`static-top-level-declaration.test.js`](https://github.com/echo094/decode-js/blob/6cacb633ceedf0812fe31f951ba8f41ffb431ca1/test/obfuscatorx/static-top-level-declaration.test.js)
drives the exact 5.3.1/5.4.0 declaration outputs through direct and plugin pipelines. Those tests
prove safety and surrounding normalization; they do not claim that this schedule decodes an
ObjectPattern.
