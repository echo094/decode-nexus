# parse-control-flow-storage.js

Reverses javascript-obfuscator's **FunctionControlFlowTransformer**, which routes
expressions through a "controlFlowStorage" object of tiny wrapper functions. This visitor
recognizes such an object and inlines every call site back to the original expression.

```javascript
// storage object
var _0xb28de8 = {
  "abcd": function (a, b) { return a == b; },   // BinaryExpression
  "dbca": function (f, x, y) { return f(x, y); }, // CallExpression (callee = first param)
  "aaa":  function (g) { return g(); },
  "bbb":  "eee",                                 // Literal
  "ccc":  A[x][y]                                // MemberExpression
};
// From                              // To
_0xb28de8["abcd"](123, 456);   -->   123 == 456;
_0xb28de8["dbca"](bcd, 11, 22); -->  bcd(11, 22);
_0xb28de8["bbb"];               -->  "eee";
```

Runs on `VariableDeclarator` **`exit`**. Each property must match one of: a
`FunctionExpression` with exactly one `return` of a `BinaryExpression`,
`LogicalExpression`, or `CallExpression` (the call's callee must be the function's first
param), a `StringLiteral`, or a `MemberExpression`. Every qualifying key gets a
`repfunc` that rebuilds the corresponding node from the call's arguments.

**Completeness gates:** if *no* property qualifies it bails; if only *some* qualify it
logs `不完整替换` (incomplete replacement) and bails — a partial match usually means it's an
ordinary object, not a storage object. Reference rewriting walks `referencePaths`
**in reverse** so nested `storage[k](storage[j](…))` calls resolve inner-first; a key
missing from `objKeys` is assumed dead code and skipped. The storage `VariableDeclarator`
is removed only if `usedCount` equals the reference count, otherwise it logs `不完整使用`
and is kept.

**The property gate is all-or-nothing; the *reference* gate is not, and that asymmetry is where
both defects below live.** `不完整使用` reports a partial reference set *after* every resolvable
reference has already been rewritten — the log describes what was kept, not what was skipped.

`test/visitor/parse-control-flow-storage/` holds a decline and a focused traversal-order case —
read Fixtures below before treating the visitor's full resolving surface as pinned. Consumed by
the `obfuscator`, `sojson`, and `sojsonv7` plugins. Feeds on objects reassembled by
[merge-object.js](merge-object.md).

## What it emits, for passes scheduled after it

Inlining substitutes a storage entry's **value** at the read site, so this visitor puts shapes back
into the tree that were not there when earlier passes ran. One of them routinely re-opens work a
caller thought finished: a stored **string literal** inlined into computed-member-key position
yields `x['foo']`, which a member-un-computing or key-normalizing pass owns and has already had its
chance at. A pipeline that runs property-spelling normalization once, before this visitor, leaves
exactly those keys computed — and no census of *that* pass can see it, because the shape is created
after it reported clean. Schedule the two as a group that repeats until the tree stops moving. The
worked instance is
[obfuscator/normalize-converting.md](obfuscator/normalize-converting.md)'s Upstream Effects.

## Known Gaps

- **It has no branch for a *delegating* wrapper, and works anyway only because of traversal
  order.** javascript-obfuscator re-enters its own output: an inner storage's entries can be
  `function (x, y) { return OUTER[k](x, y); }`, a call whose callee is a **MemberExpression**. The
  `CallExpression` branch requires `isIdentifier(callee)`, so such a property never qualifies — and
  the completeness gate should then abort the entire storage. It does not, because the encoder
  prepends an inner storage to an *enclosing* function body, so the outer storage's declarator is
  always an earlier statement in source order; `exit` resolves it first and rewrites
  `OUTER[k](x, y)` into `x <op> y` inside the inner wrapper bodies before the inner declarator is
  ever visited. **Measured:** a corpus cell carrying 46 delegating wrappers logs zero
  `不完整替换` and processes 13 storages. **This is a correctness dependency on outer-first
  visiting** — the focused regression now pins the current traversal order, but running this
  visitor over a subtree, innermost-first, or on a tree whose storages have been reordered would
  abort every nested storage, silently and completely, with the only signal being a log line.
- **It is blind to the extracted storage form on its own.** The encoder's object-keys extraction
  rewrites a storage into `var S = {}` plus one assignment per property, and this visitor requires
  `init` to be an `ObjectExpression` with at least one property — an empty one returns immediately.
  So on every sample below the era where extraction stops refusing storages, the visitor sees
  nothing at all. `obfuscator.js` gets away with it by running
  [merge-object.js](merge-object.md) immediately before, in the same `decodeCodeBlock`. That is a
  hard dependency rather than a convenience, and it is the same class of ordering fact as the
  string-array one below.

- **It cannot run before the string array is decoded, and its scheduling in `obfuscator.js`
  reflects that.** The storage that actually appears in javascript-obfuscator output is
  `FunctionControlFlowTransformer`'s, built at the encoder's ControlFlowFlattening stage — and the
  later StringArray stage then rewrites its call-site *keys* into wrapper calls
  (`_0x10fac4[_0x3e19(0x13a)]`). This visitor reads a key only as a string literal or an
  identifier, so a call expression in key position hits the unexpected-call branch and is skipped.
  That is why `obfuscator.js` runs it inside `decodeCodeBlock`, *after* `decodeGlobal`, rather than
  earlier — the position is load-bearing, not incidental.
- **No branch for a numeric-literal property**, which
  javascript-obfuscator's `stringArrayCallsTransform` (`≥ 3.2.0`) produces. Its replacer stores the
  string array *index* and rewrites the site to `storage.key`, so under the default index type the
  stored value is a bare **numeric** literal. The property list above has a function expression, a
  string literal and a member expression and none for that, so the completeness gate aborts the
  whole object on the one property. **Observed at the `3.2.0` lower bound:** the focused
  `calls-transform` cells populate the numeric-valued storage. This remains an intentional gap in
  the shared visitor: widening it would change `obfuscator`, `sojson` and `sojsonv7` on evidence
  from a producer only `obfuscatorx` owns. The
  [obfuscator-specific fork](obfuscator/inline-control-flow-storage.md) adds the numeric branch and
  closes the composition gap without changing these consumers.

- **That fork diverges on two further behaviours, and both are defects here — recorded as
  descriptions of this visitor, not as a worklist.** Verified on hand-built cases:

  - `var {a} = {a: "s"}` — a destructuring declarator whose object passes the property gate —
    **throws** a `TypeError`. `node.id.name` is undefined on a pattern, so the binding lookup
    returns undefined and the reference count is read off it.
  - a storage read sitting beside an unsupported **write** is inlined to the pre-write value:
    `var s={x:"p"}; s.x="OVERWRITTEN"; return s.x` becomes `return "p"`. The replacements land
    before `不完整使用` is decided, so the log reassures while the output has already changed.
    This is T2 · W5's all-or-nothing contract, unmet.

  **Neither is fixed here, and the reason is evidence rather than effort:** the repair is only safe
  if it holds for `sojson` and `sojsonv7`, and no corpus, encoder or field sample for either exists
  in this tree — so it would be verified against `javascript-obfuscator` output and shipped to two
  consumers that output says nothing about, which is what W7 forbids. Same standing as the frozen
  `obfuscator` entry's defects: a permanent description of what a consumer of this visitor
  experiences.

## Source

- `src/visitor/parse-control-flow-storage.js` — the whole visitor.

Wired by `src/plugin/obfuscator.js` inside `decodeCodeBlock`, after `decodeGlobal`, and reused by
`sojson` and `sojsonv7`. That position is forced rather than conventional: the Known Gaps above say
why it cannot run before the string array is decoded or before object-keys extraction has been
merged back.

## Fixtures

| Claim | Fixture |
|---|---|
| an object of the right form whose body is not a single `return` is left exactly as found | `object-invalid-1` |
| **every resolving path** — binary, logical and call wrappers, and the string-literal entry | **not covered here.** See below |
| the delegating-wrapper dependency on outer-first visiting | `nested-delegating-wrapper-outer-first` directly places an outer binary wrapper before an inner wrapper that delegates through it, then asserts the inner use resolves exactly |
| the extracted `var S = {}` form | not covered: it needs `merge-object` to have run first, so a case for it belongs to whatever composes the two |
| a numeric-literal property (`≥ 3.2.0`) | intentionally not accepted here; the local fork's fixture and composition coverage are mapped in [its own doc](obfuscator/inline-control-flow-storage.md#fixtures) |
| the destructuring-declarator throw, and the write-adjacent inline | not covered: both are Known Gaps above rather than behaviours to pin, and a fixture would assert output this visitor should not be relied on to produce |

**The focused nested case pins one resolving path and the load-bearing outer-first order, not the
visitor's whole accepted surface.** The binary, logical, call, and string-literal producer cases
built from real `2.19.0` output still live with the
[fork](obfuscator/inline-control-flow-storage.md), which is the implementation whose corpus can
actually exercise them. The direct case is intentionally narrower: it records current shared
behavior without claiming javascript-obfuscator evidence establishes safety for every consumer.

The reason is ownership, not indifference. This visitor's consumers are `sojson`, `sojsonv7` and
the frozen `obfuscator`; no corpus, encoder or field sample for the first two exists in this tree,
so a case committed here would be `javascript-obfuscator` output asserting the behaviour of a pass
two other encoders drive. That is evidence about the fork, and it is filed where it is evidence.
**Coverage for the resolving path here is owed to whoever brings a sojson or sojsonv7 sample**, and
until then the honest record is that a corpus backed it — and a corpus is rebuildable, so it is not
coverage.
