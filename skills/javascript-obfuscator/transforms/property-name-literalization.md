# Property-name literalization

Three `Converting` (6) transformers with one shape rule between them: **every statically written
property name becomes a string literal**. Member accesses, object-literal keys and class member
keys are three syntactic positions for the same thing, and the encoder rewrites all three the same
way, which is why they are one doc rather than three.

Eras: `E-propname-computed-literal`, `E-propname-ignored-metadata`,
`E-propname-process-env-plain` and `E-propname-reserved-class-plain`
([versions.md](../versions.md)). **None of the three transformers is option-gated**, but later
preparing guards can mark member expressions ignored, and reserved names can exempt class methods.

**One position on this doc's subject is on a different axis**: class *field* keys, which the encoder
cannot process at all below `2.18.0` — `E-classfield-*`. Class *method* keys are on the stable axis
with the other two.

## 1. Target

The `StringArray` stage (8) conceals **string literals** and nothing else. A property name written
as an identifier — `o.foo`, `{ foo: 1 }`, `class C { foo () {} }` — is not a string literal, so
without this stage every property name in the program would survive obfuscation in plain text,
including the names of the encoder's own machinery.

So this transform's job is not concealment. It is to **move a name into a position the concealing
stage can reach**, and it runs four stages earlier for exactly that reason. `MemberExpressionTransformer`
says so in its own comment: *"Literal node will be obfuscated by StringArrayTransformer."*

## 2. Algorithm

One rule, applied at three node kinds: *if the key is a statically written name and the node is not
already computed, replace the key with a string literal and set `computed` wherever the syntax
requires it.*

**`computed` is set in two of the three positions and not the third, and that asymmetry is
syntactic rather than a policy difference.** A member access must become computed to take a string
key (`o.foo` → `o['foo']`), and so must a class member (`foo () {}` → `['foo'] () {}`). An
object-literal key may be a string literal while staying non-computed, so it is left non-computed
(`{ foo: 1 }` → `{ 'foo': 1 }`). The emitted shape therefore differs by position even though the
rule does not, and a matcher keyed on `computed` alone reads the three inconsistently.

**Already-computed nodes are left alone in every case.** `o[x]`, `{ [x]: 1 }` and `['foo'] () {}`
are returned untouched — the transform only ever converts *static* spelling to literal spelling, and
never converts a dynamic key into anything.

**Later eras add deterministic exemptions rather than changing the ordinary conversion.** At
`E-propname-ignored-metadata`, a member whose object or property is ignored stays unchanged; at
`E-propname-process-env-plain`, a preparing guard uses that route for the complete `process.env.*`
chain. At `E-propname-reserved-class-plain`, a class method name matching `reservedNames` stays
non-computed. Ordinary members, object keys and unmatched class methods retain the table's shapes.

## 3. Implementation

| Transformer | Era | Node kinds | Input spelling | Emitted spelling | `computed` after |
|---|---|---|---|---|---|
| `MemberExpressionTransformer` | all | `MemberExpression` | `o.foo` | `o['foo']` | set to `true` |
| `ObjectExpressionTransformer` | all | `ObjectExpression` properties | `{ foo: 1 }` | `{ 'foo': 1 }` | left `false` |
| `MethodDefinitionTransformer` | `– 2.17.0` | `MethodDefinition` | `foo () {}` | `['foo'] () {}` | set to `true` |
| `ClassFieldTransformer` | `2.18.0 –` | `MethodDefinition`, `PropertyDefinition` | `foo () {}`, `foo = 1` | `['foo'] () {}`, `['foo'] = 1` | set to `true` |

**The last two rows are one transformer renamed, and for class *methods* the rename changes
nothing** — same two paths, same `ignoredNames`, same emitted shape across the documented corpus
matrix. What the rename carries is a **widened visitor**:
`PropertyDefinition` joins `MethodDefinition`, so class fields start being literalized at `2.18.0`.
Below that the encoder does not leave a class field alone — it **refuses the input**, as a parse
error at `2.9.6` and a stack overflow at `2.16.0` (`E-classfield-*` in [versions.md](../versions.md)).
This is why the file set moving at `2.18.0` is not by itself the boundary: the boundary is one node
kind in the visitor, and it moves only one of this doc's four positions.

Position-by-position detail:

- **`MemberExpressionTransformer`** acts only when `property` is an `Identifier` and `computed` is
  false. `o[x]` (computed, identifier property) returns unchanged — the guard is an early return on
  `computed`, not a check on what the property is.
- **`ObjectExpressionTransformer`** splits on `property.computed`:
  - *non-computed* (`transformBaseProperty`) — clears `shorthand` first, then rewrites an
    `Identifier` key to a string literal. **The shorthand clear happens even when the key rewrite
    does not**, so `{ foo }` becomes `{ 'foo': foo }` in one step.
  - *computed* (`transformComputedProperty`) — rewrites a **string-literal** key to a fresh literal
    node, which is a normalization rather than a change of shape, and returns early for any other
    key. `{ [x]: 1 }` is untouched.
- **The class-member transformer** splits on what the key already is: an `Identifier` key is
  replaced with a string literal *and* marked computed; a key that is **already a string literal** is
  only marked computed, since the literal is already there. Both paths refuse a node that is already
  computed. Which node kinds it visits is the era-tagged part above — methods at every era, fields
  from `2.18.0`.

**`constructor` is always exempt**, checked on both class-key paths. At
`E-propname-reserved-class-plain`, the same paths also exempt names matching `reservedNames`.
The constructor exemption is semantic, not cosmetic: a computed key never designates a class
constructor, so literalizing it would change what the class does rather than how it reads.

## 4. Downstream Effects

**The three positions do not share a downstream fate.** A literal in a **computed** position is
eligible for concealment; a **non-computed
object-literal key is prohibited from it outright**, by `NodeLiteralUtils.isProhibitedLiteralNode` —
which returns true for a literal that is the key of a non-computed `Property`, and is consulted by
both `StringArrayTransformer` and `SplitStringTransformer`.

So the two transformers that look like one rule have opposite purposes downstream:

| Position | After literalization | `StringArray` (8) | Emitted |
|---|---|---|---|
| member access | `o['foo']` — computed | eligible | `o[_0x1a2b(0x0)]` |
| class member key | `['foo'] () {}` — computed | eligible | `[_0x1a2b(0x0)] () {}` |
| object-literal key | `{ 'foo': 1 }` — **not** computed | **prohibited** | `{ 'foo': 1 }`, plain and readable |

Measured on the corpus at `2.19.0`: `var config={'name':_0x4d59fe(0x136),'size':0x3,'nested':{'flag':!![]}}`
— every **key** is a plain string literal while the string **value** is concealed, and the member
reads of the same object elsewhere in the program are concealed too.

**`ObjectExpressionTransformer` is therefore not a concealment enabler at all**, unlike
`MemberExpressionTransformer`, whose own comment says its literal "will be obfuscated by
StringArrayTransformer". It is a normalization: it makes every key a string literal and nothing more.

| Later stage | What it does to this transform's output |
|---|---|
| `StringArray` (8) | takes the literals in **computed** positions, per the table above. Whether a given eligible literal is taken also depends on that stage's own threshold and length gates, so **some computed names still survive as plain literals** |
| `Finalizing` (10), escape sequences | a surviving literal is escaped like any other, so a property name can appear as `o['\x66\x6f\x6f']` ([escape-sequences.md](escape-sequences.md)) |
| `Converting` (6), `ObjectExpressionKeysTransformer` | consumes object literals whose keys this transform has already literalized; the extracted assignments it emits are member writes, which are themselves literalized. The relative order inside the stage is [order.md](../order.md)'s |
| `RenameProperties` (5) | runs **earlier** in the stage order, so it renames property names before they are literalized; a renamed name arrives here as an ordinary identifier and is literalized identically |

**The stage-order consequence worth stating on its own:** because this transform is unconditional
and runs at stage 6, **no `Converting`-stage output from any phase-1 era carries a non-computed
member access or an identifier-keyed object literal.** That is a property of every emitted sample
regardless of which options were set, and it is the strongest single structural claim this stage
supports.

**No site-level randomness anywhere in the stage.** Checked across all eleven `Converting`
transformers at `2.19.0`: none consults a threshold, a probability, or an ignored-node marker. So
each is all-or-nothing — the option is off and it never runs, or it runs at every matching site.
That is unlike `DeadCodeInjection` and `ControlFlowFlattening`, which are threshold-gated, and it
means **there is no partial application to reason about in this stage.** The only exemptions are
positional and deterministic: `isProhibitedLiteralNode`'s three cases — a non-computed property key,
an import declaration, and an export declaration.

## 5. Known Quirks

- **The three positions emit two different `computed` values for one rule** (item 2). Read as a
  quirk from the outside; it is forced by what each syntax admits.
- **`ObjectExpressionTransformer` rewrites a computed string-literal key to an equal literal node.**
  A no-op on the emitted shape, and the only branch in the three that changes nothing observable.
- **The shorthand clear is not conditional on the key rewrite**, so an object literal that carries
  only shorthand properties is still changed by this transform even when no key needed literalizing.
- **`constructor` is exempt but `'constructor'` written as a string is too** — the exempt-name check
  runs on the literal path as well, so a class member spelled `'constructor' () {}` is left
  non-computed.
- **A class field is refused, not skipped, below `2.18.0`** — the encoder errors rather than
  emitting the field unchanged, which is a quirk of the encoder's *input* range rather than of this
  transform's output. `E-classfield-rejected` in [versions.md](../versions.md).
- **The modern DOM/API reserved-name update is not this transform.** It belongs to the
  irreversible `RenameProperties` stage and is recorded as
  [`E-renameprops-reserved-modern-*`](../versions.md). The focused plain-object controls show
  `at`, `toSorted` and `findLast` preserved at the high adjacent tag while an ordinary property
  still renames; they do not establish browser-wide compatibility.

## Source

- [`MemberExpressionTransformer.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/node-transformers/converting-transformers/MemberExpressionTransformer.ts)
- [`ObjectExpressionTransformer.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/node-transformers/converting-transformers/ObjectExpressionTransformer.ts)
- [`ClassFieldTransformer.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/node-transformers/converting-transformers/ClassFieldTransformer.ts)
  — `2.18.0` and above
- Later member and class-method exemptions at the pin:
  [`MemberExpressionTransformer.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/45ad03b8335bee095b17c0d29b0a78bff158c93a/src/node-transformers/converting-transformers/MemberExpressionTransformer.ts),
  [`ClassFieldTransformer.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/45ad03b8335bee095b17c0d29b0a78bff158c93a/src/node-transformers/converting-transformers/ClassFieldTransformer.ts)
- [`MethodDefinitionTransformer.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/1985c39d51e36464cd12286e288a43d9b960095f/src/node-transformers/converting-transformers/MethodDefinitionTransformer.ts)
  — the same transformer below `2.18.0`, pinned at `2.17.0`, its last version
- All are registered unconditionally in `JavaScriptObfuscator.ts`'s static `nodeTransformersList`;
  their stage and level are [order.md](../order.md)'s.

Read at `2.19.0`, the spine, except the class-member rows, which are read at both `2.17.0` and
`2.19.0` because the transformer is renamed between them; the extension was read at every release
tag through `5.5.0`.

## Fixtures

**None committed yet** — this doc is U4's encoder side and the unit's fixtures are built from
upstream's own `.spec.ts` cases at step 7. What already stands behind it is a corpus census rather
than a fixture.

| Claim | What checks it | Gap |
|---|---|---|
| no non-computed identifier member access survives in phase 1 | a corpus-wide census of `MemberExpression` with `computed === false` and an `Identifier` property, which should read **zero** on every phase-1 cell | pinned by no committed fixture; later ignored-member eras deliberately permit survivors |
| no identifier-keyed object literal survives | the same census over `ObjectExpression` properties with an `Identifier` key, likewise **zero** | as above |
| the census can read non-zero | the same census over the pre-obfuscation fixtures, and over a hand-written positive control | — |
| all three are ungated | source read: no `this.options` reference in any of the three | — |
| one era across phase 1's range, for the three stable positions | per-tag content hash at every release tag in range, one hash per file | classified by content identity, not by output at every tag |
| class **method** keys literalized identically at every era | a throwaway class-method encode at the sampled era tags | not pinned by a committed fixture |
| `constructor` exemption | the same encode leaves `constructor(…)` untouched | as above |
| a string-literal method key is only re-marked computed | the same encode — `'quoted'()` emits as `['quoted']()` | as above |
| class **fields** literalized from `2.18.0`, refused below it | the same encode with a field added: emits `['size']=0x3` at `2.18.1`/`2.19.0`, parse error at `2.9.6`, stack overflow at `2.16.0` | as above |
| ignored metadata, `process.env.*`, and reserved class methods open the three later rows | per-tag source diffs at `4.2.0`, `5.2.0`, and `5.4.0`; exact-tag focused method/field discriminators for the last | `process.env.*` remains source-only |
| modern DOM/API names are preserved by the 5.4.0 reserved list | focused `5.3.1`/`5.4.0` release-note cases | belongs to `RenameProperties`, not this Converting transformer; plain-object harness only |

**Every class row is a throwaway encode rather than a fixture, because no corpus input declares a
class.** A corpus class fixture must carry methods only because `E-classfield-rejected` does not
accept class fields; field evidence belongs only to eras that support them.
