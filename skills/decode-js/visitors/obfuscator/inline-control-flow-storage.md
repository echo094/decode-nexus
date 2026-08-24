# obfuscator/inline-control-flow-storage.js

The `obfuscatorx` fork of the shared
[parse-control-flow-storage](../parse-control-flow-storage.md) visitor. It reverses the same
control-flow storage shapes and additionally accepts numeric literal entries emitted by
javascript-obfuscator's `stringArrayCallsTransform` in
`E-cff-storage-stringarray-shared` and `E-cff-storage-stringarray-per-host`.

**It is deliberately not named after the file it forked from, and that is worth not "correcting"
back.** A fork sharing the original's basename makes the name stop identifying one thing, in three
ways that compound: a filename search returns two implementations; a *relative* cross-reference
resolves from either folder, so a link can point at the wrong one and no link checker can tell; and
a commit scope naming the pass cannot separate the two histories under `git log --grep`. Every
other file in this folder is named for what it does in the decoder's vocabulary rather than after an
upstream file, so the fork↔original pairing is carried by this doc's link above — which survives a
rename where a filename does not.

## 1. Target

Inline every supported control-flow storage read and remove the storage declaration once every
reference is resolved. In particular, turn a string-array call argument such as `storage.key` back
into its numeric index before the string-array pass classifies its call sites.

## 2. Algorithm

Match a `VariableDeclarator` whose initializer is a non-empty object and require every property to
belong to the accepted set: the shared visitor's function, string-literal and member-expression
entries, plus a numeric literal. Build one replacement per key, walk the binding's references in
reverse so nested calls resolve inside-out, and remove the declarator only when every reference was
resolved. A partial match stays fail-closed.

The visitor runs in two slots. Before string-array decoding it exposes indexes concealed by the
calls-transform storage eras. It also reconstructs the optional identifier-callee wrapper in
`E-cff-callee-optional-wrapper` without discarding its short-circuit semantics. Inside the existing fixpoint group it retains the older traffic direction,
where string-array decoding exposes storage keys and storage inlining re-opens converting work.
Both slots are shape-driven; neither detects an option or version.

## 3. Implementation

`parseObject` runs on `VariableDeclarator.exit`. Function entries accept the same single-return
binary, logical and ordinary-call wrappers as the shared visitor, plus a direct Babel
`OptionalCallExpression` whose callee is the first identifier parameter. The replacement uses an
optional call as well; optional member callees remain outside the gate. Literal entries clone their primitive
value into a new Babel node; member entries reuse the shared visitor's spelling. Member reads are
resolved only when the storage binding is their object.

Every reference is preflighted before the first replacement. An unsupported member write or read
therefore leaves the entire tree untouched rather than partially freezing an ordinary object's
values. After accepted replacements and removal, the visitor crawls from the Program scope. The
pre-string-array slot changes references used by a later detector, and a local crawl would leave
enclosing bindings describing the tree from before the rewrite.

## 4. Upstream Effects

| Spelling reaching this pass | Produced by | Whose | Era |
|---|---|---|---|
| numeric-valued storage read used as a string-array wrapper argument | the encoder's `StringArrayControlFlowTransformer` | encoder's | `E-cff-storage-stringarray-shared` and successors |
| string/member/function storage exposed after string-array decoding | the decoder's string-array pass | ours | older verified eras |
| optional identifier-callee wrapper | `CallExpressionControlFlowReplacer` and `CallExpressionFunctionNode` | encoder's | `E-cff-callee-optional-wrapper` |

The first row forces the pre-string-array slot; the second keeps the post-string-array fixpoint
slot. Removing either would restore one side of the dependency inversion.

## 5. Known Gaps

- The fork intentionally duplicates the shared visitor's matcher. A future correction to either
  implementation requires an explicit comparison; silently copying one onto the other would widen
  three unrelated plugins again.
- **It is not the shared visitor plus one branch, and reading it as one is the trap.** Three
  behaviours diverge, and only the first is about numerics: the accepted-entry set, the
  all-or-nothing preflight, and the crawl scope. The second and third correspond to **live defects
  in the shared visitor** — it throws on a destructuring declarator whose object passes the gate,
  and its partial application can change program output where a storage read sits beside an
  unsupported write. Those are not fixed there because doing so needs evidence from `sojson` and
  `sojsonv7`, which this corpus cannot supply
  ([the shared visitor's own gaps](../parse-control-flow-storage.md#known-gaps)).
- **The preflight is a narrowing, not only a repair.** Where any reference is unresolvable the fork
  declines the whole storage, including reads the shared visitor still resolves — a dead-code
  reference to a key the storage lacks, a reference passing the storage whole, an unreadable
  computed key. The trade is deliberate (residue is countable, a wrong inline is not), and no
  census has reported the lost coverage. A gate keyed on whether a reference could *write*, rather
  than on whether it resolves, would recover the read cases if one ever does.
- An ordinary all-numeric object whose complete reference set consists of supported member reads is
  structurally indistinguishable from the new storage form. The all-properties and all-references
  gates bound that false-positive surface; no version/name discriminator is added.

## Source

- [`src/visitor/obfuscator/inline-control-flow-storage.js`](https://github.com/echo094/decode-js/blob/6cacb633ceedf0812fe31f951ba8f41ffb431ca1/src/visitor/obfuscator/inline-control-flow-storage.js)
- Wired twice by
  [`src/plugin/obfuscatorx.js`](https://github.com/echo094/decode-js/blob/6cacb633ceedf0812fe31f951ba8f41ffb431ca1/src/plugin/obfuscatorx.js): after
  statement normalization and again inside the fixpoint group. Item 2 explains why both positions
  are required.

## Fixtures

All fixtures live in `test/visitor/obfuscator/inline-control-flow-storage/`, the fork's own
directory. **The wrapper cases are copies of the shared visitor's, not references to them**, and the
duplication is the point: the fork claims to accept everything the shared matcher accepts, and a
claim about one implementation cannot be pinned by fixtures another one is run against. Keeping the
fork's cases in the shared directory also put fixtures the *shared* visitor fails next to the ones
it passes, so a directory glob added to its suite — the natural next step — would have read as a
regression in a visitor nobody had touched.

| Fixture | Claim it pins | Era |
|---|---|---|
| `storage-binary` · `storage-logical` · `storage-call` | the fork resolves every wrapper kind the shared visitor does, byte-identically | no encoder-era claim |
| `object-invalid-1` | an object of the right form whose body is not a single `return` is left exactly as found | hand-built; no encoder-era claim |
| `storage-numeric` | numeric entries inline, the fully consumed declaration is removed, and Babel reference state matches a fresh parse | `E-cff-storage-stringarray-shared` and successors |
| `storage-numeric-write` | an unsupported member write makes the whole candidate a no-op, including reads that would otherwise qualify | hand-built; no encoder-era claim |
| `storage-optional-call` | exact minimized `4.2.0` encoder output reconstructs `?.(…)`, removes the storage and retains `undefined` for a null callee | `E-cff-callee-optional-wrapper` |
| `storage-optional-member` · `storage-optional-reference` | unsupported optional member callees/references leave the entire tree and binding state untouched | hand-built; no encoder-era claim |
| `storage-nested-call` | reverse replacement still resolves nested ordinary calls inside-out | no encoder-era claim |
| `test/obfuscatorx/3.2.0-calls-transform` | a real calls-transform sample resolves storage before string-array decoding and reaches the independently runtime-certified golden | `E-cff-storage-stringarray-shared` |

Not covered: the preflight narrowing above — the read cases the fork declines and the shared
visitor resolves. They are recorded as a trade rather than pinned, because no consumer needs them
today.
