# jsconfuser/global-concealing.js

## 1. Target

Reverses js-confuser's [GlobalConcealing](../../../js-confuser/transforms/global-concealing.md):
inlines every `{ph}_getGlobal("key")` call site back to the bare global identifier it
stands for.

## 2. Algorithm

Match the dispatch function structurally: one param, a body that is exactly one
`switch(param) {...}` on that param, where **every** case is the identical shape (real
and decoy alike — nothing here needs to tell them apart). Building the `key -> realName`
map is the entire decode step — no evaluation needed, unlike
[string-concealing.js](string-concealing.md), since every real name is already a plain
string literal sitting right there in the switch body. Every matched call site is then
inlined as the bare `realName` identifier.

**`tamperProtection`'s `checkNative` wrapping is not handled here, and by design never
will be.** When `lock.tamperProtection` is on, this transform's own native call sites are
wrapped in a `checkNative(fn)` / `checkNative(obj, "prop")` guard around the *outermost*
member expression (see the encoder doc). This visitor still correctly inlines the
`getGlobal("console")` piece inside the wrapper, and leaves the `checkNative(...)` call
itself in place — unwrapping *that* is [lock.js](lock.md)'s job, since `checkNative` is
tamperProtection's own machinery, not this transform's; this visitor only ever sees it as
an opaque wrapper around the calls it does own.

**Resolve the switch function's binding from `fnPath.scope.parent`** — [babel.md](../../babel.md)'s
first section has the mechanism. Hardened here **defensively**: no empirical run has triggered a
live collision on this pass, but the vulnerable shape already broke
[calculator.js](calculator.md) outright, and the non-collision is an artifact of this encoder's
current declaration ordering rather than a documented guarantee.

## 3. Implementation

`matchGlobalConcealingSwitch` matches a function with exactly one param and a
body that is exactly one `switch(param) { ... }`, where every case is
`case "key": return globalVar["realName"];` — a member access on one shared `globalVar`
identifier, consistent across every case, **in either spelling**: computed with a string
literal key, or `Minify`'s dot form with an identifier key (item 4).

**Which functions it is offered, and why that is not a node type.** The visitor takes both
`FunctionDeclaration` and `FunctionExpression`, reads the holder's name from whichever of the
three spellings holds it (`readHolderName`: a declaration's own id, a declarator's id, or an
`=` assignment's left), and then requires that name to resolve *back to this same function
node* through `utility/binding-def.js`'s `resolveBindingFunction` — the identity check
[string-concealing.md](string-concealing.md) makes for the same reason. Both properties this
relies on (a definition the declaration form hides is still found; a binding written more than
once fails closed) are the helper's, not a guard written here —
[babel.md](../../babel.md) owns them. Keying on `FunctionDeclaration` instead is what made this pass fire on
nothing at all — not decline, *never run* — for every `high` sample, where item 4's holder is
what actually arrives.

```mermaid
flowchart TD
    A[FunctionDeclaration or FunctionExpression<br/>whose binding defines it] --> B{1 param,<br/>body = switch on it?}
    B -- no --> Z[leave untouched]
    B -- yes --> C{every case:<br/>return globalVar['name']?}
    C -- no --> Z
    C -- yes --> D[build key -> realName map]
    D --> E["for each call site fn('key'):<br/>replace with bare Identifier(realName)"]
    E --> F[queue fn name + globalVar name<br/>for Program-exit cleanup]
```

**Cleanup** is deferred to `Program: exit`, transitive, three links long: the switch
function itself → the `var globalVar = getGlobalVarFn()` declaration it's the only
referrer of → the `getGlobalVarFn` sniffer that declaration is the only referrer of. Each
is only removed once `safeDeleteNode` confirms zero remaining references — same reasoning
as [integrity.js](integrity.md)'s hash-utility cleanup, just a fixed 3-link chain instead
of an open-ended one.

**The third link is reached through `readSnifferName`, not through the declarator alone.**
The sniffer is identifiable only as the callee of `globalVar`'s own initializer, and
MovedDeclarations (encoder Order 25) splits `var globalVar = getGlobalVarFn()` into a bare
declarator plus a `globalVar = getGlobalVarFn()` assignment elsewhere — Mechanism 1, the
same split [control-flow.js](control-flow.md)'s `readHarnessSlot` reads for the CFF harness.
Read `node.init` alone and it is `null` on every sample that stage touched, so the chain
stops one link short and the sniffer survives as a sizeable zero-reference orphan. So
this reads the initializer from the declarator *or* from a single `=` write to the binding,
before `safeDeleteNode` removes those writes. More than one write and it declines: there is
then no one initializer to read.

## 4. Upstream Effects

**This pass matches nothing at its early slot on a `high` sample, and the second visit that
fixes that cannot sit where the obvious argument puts it.** The switch function is inside the
ControlFlowFlattening interpreter when the early pass runs, so the population there is zero —
not a declining matcher, no candidate at all. But what the CFF decode hands back is still not
matchable:

```js
function f(...rest) { var a, b; a = function () {…}; b = function (…) {…};
                      switch (<member>) { case <call>: … } }
```

which fails every gate this matcher has at once — a rest param rather than one identifier,
the string-decode wrappers standing as extra statements ahead of the switch, a discriminant
that is not the param, and case tests that are still `{ph}_STR_N(a, b)` calls and
concatenations. Three later passes clear those in order: VariableMasking unmasks the rest
param and its wrappers, StringConcealing's own second visit turns the case tests into
strings, and the constant fold after it collapses what is left into plain `StringLiteral`s.
Measured per stage on a `high` sample, the *candidate* shape first exists after
StringConcealing's second visit and the full match only after that fold — so the second
visit is scheduled there, and anywhere earlier is another pass with a zero population.

**A fourth pass had to change before the body gate cleared, and it is the one that unmasks
the rest param.** Restoring a single identifier parameter is not the whole of what
VariableMasking owes this matcher: the stack it unmasks arrives from the CFF decode as a
bare `var stk;` plus a separate `[...stk] = rest;`, and un-masking used to remove only the
assignment. The declaration then stood as a second statement ahead of the switch, so
`body.length !== 1` declined the samples that had cleared every other gate. The fix is
in the pass that emits the deadness ([variable-masking.md](variable-masking.md) item 4),
not a relaxation here — this matcher is one of several consumers of that declarator, and
teaching each of them to look past it is the same fix re-paid per consumer
([encoder-decoder-method.md](../../../encoder-decoder-method.md) T9).

**The holder the switch function arrives in is the CFF decode's own spelling, not the
encoder's.** `globalConcealing.ts` emits a `FunctionDeclaration`; ControlFlowFlattening then
swallows it, and what the encoder's output actually carries is a scope-anchor property,
`X.Y.name = function (…){…}`, with no declaration anywhere — a `CUT=pack` read finds the
anchor property and no declaration on every sample carrying the layer, and the
`assigned-holder` fixture pins the spelling. The `var f;` plus separate `f = function (…){…}` this matcher sees
is [control-flow.md](control-flow.md)'s reconstruction of that property, and the resemblance
to a MovedDeclarations split is a coincidence that has misattributed this three times.

**This pass absorbed the shape rather than waiting for it to be normalized**, by identifying
the holder through its binding (item 3). That is the cheaper of the two remedies and the one
with no blast radius: it changes no output, so it cannot disturb any other pass, whereas
normalizing the emission is constrained by the producing pass's own consumers — item 4 there
has the measurements. The census that reads the effect is the residual-switch-function count,
which **should read zero** once the shape is absorbed, against a size ratio that drops and a
runtime-correctness axis that must not move ([probes.md](../../probes.md) builds all three).

**The same split reaches the cleanup sweep, and there it failed silently instead of
declining.** The sniffer (`getGlobalVarFn`, the getGlobal template) is a `FunctionDeclaration`
as `globalConcealing.ts` writes it, and the sweep's last step gated its deletion on
`binding.path.isFunctionDeclaration()`. The CFF decode re-emits it the same way it re-emits
the switch function's holder — merged hoisted `var s, …;` plus a separate
`s = function (…) {…}` — so the gate read false while the two deletions *above* it, both
already binding-resolved, succeeded. **The failure mode is what makes this worth recording:
it is not a declined match.** The switch function and `globalVar` came out, the layer decoded,
every correctness and interpreter signal read clean, and what was left behind was a sizeable
helper at **zero references** — indistinguishable from an encoder-emitted dead helper
([encoder-decoder-method.md](../../../encoder-decoder-method.md) S3's first caveat) unless
someone asks whether it was live in the *input*. It was, on a large share of the corpus and a
substantial share of all decoded bytes — and **no census found it**: three separate ones had
reported the pass clean. It was found instead by ranking decoded output by residue size and
reading the worst sample. The fix is the one already in this file two lines up,
`resolveBindingFunction`, regression-guarded by the `assigned-sniffer` fixture.

The generalisation, which is the durable half: **a decoder pass has two ways to depend on a
spelling, and only one of them is visible.** A matcher that keys on a spelling declines, and a
decline is at least countable by a breadcrumb. A *cleanup* that keys on one deletes nothing
and reports nothing, and its residue then reads as somebody else's dead code. Audit a sweep's
gates whenever the pass's own matcher is taught to resolve through a binding — the two were
changed a session apart here, and the gap between them cost the larger of the two effects.

**"The input exists after the CFF decode" and "the input is matchable after it" are different
claims**, and only the first follows from the interpreter being unwound — the timing form of
[encoder-decoder-method.md](../../../encoder-decoder-method.md) T6's pair. A matcher reading
several independent properties of a shape needs every one restored, and different passes restore
them at different points, which is what forced this pass's second slot as late as it sits.

**One reference can be registered twice, and it is the earlier passes' tree that makes it so** —
[babel.md](../../babel.md) has the mechanism and the failed `crawl()` remedy. It reaches this
pass because call-site inlining replaces each reference: the second replacement finds the
parent's `callee` slot already holding what the first put there, so **a duplicate here is a
crash, not a declined match**, and it is guarded by node identity rather than left to the
fail-closed reflex covering the rest of this pass.

**One dependency here is the encoder's, not ours, and it is a case key's member spelling.**
`Minify` (encoder Order 28, later than GlobalConcealing's Order 12) rewrites
`globalVar["Math"]` to `globalVar.Math` wherever the key is a valid identifier, so
`case "k": return globalVar.Math;` and the computed form mean the same thing and **both have to
be read** (item 3). This matcher is all-or-nothing, which is what makes missing one expensive
rather than partial: a single minified case among the rest leaves the entire GlobalConcealing
layer undecoded on every sample carrying one. It sits here rather than among the passes above
because the spellings a matcher must accept are one list regardless of who produced them —
which is the whole point of keeping that list rather than describing the intent behind it
([dispatcher.md](dispatcher.md) item 4 is the worked example).

**Censusing this pass needs a payload-keyed probe, never one mirroring its matcher** — the gate
list in item 3 is all a mirror can see, and both this pass's holder-kind bug and its minified-key
bug were invisible to one. The mechanism and both incidents are
[probes.md](../../probes.md)'s first Hazard bullet; it is not repeated here.

## 5. Known Gaps

None currently open.

## Source

[`src/visitor/jsconfuser/global-concealing.js`](https://github.com/echo094/decode-js/blob/6c974fb5720518fac9c6b3d4cf558ba90ef9f8e7/src/visitor/jsconfuser/global-concealing.js), wired into
[plugin/jsconfuser.js](../../plugins/jsconfuser.md) **twice** — both slots forced, for the
reasons in item 4.

## Fixtures

`test/visitor/jsconfuser/global-concealing/`, one fixture per claim this doc makes:

| fixture | what it pins |
|---|---|
| `simple` | a single concealed global amid decoy cases — item 2's "every case is the identical shape", decoys needing no telling apart |
| `multiple-refs` | call-site inlining is per reference, not per key |
| `minified-member-key` | item 4's `Minify` dependency — a `globalVar.Math` case key alongside the computed form, the all-or-nothing gate that leaves the whole layer undecoded when missed |
| `moved-declaration-split` | the split must not cost the sniffer — expected output byte-identical to the unsplit case (item 3's third link) |
| `assigned-holder` | how the holder is spelled cannot change what the pass produces — byte-identical again (item 4's holder dependency) |
| `assigned-sniffer` | the sweep resolves the sniffer through its binding, not its declaration form (item 4) |
| `not-a-wrapper` | fails closed — a mismatched `globalVar` identity between cases |
| `reassigned-holder` | fails closed — differs from `assigned-holder` by that second write alone |

`test/jsconfuser/rename-variables/global-concealing.*` pins item 2's parent-scope binding
lookup — that the pass survives `RenameVariables` giving the switch function and its own
param the same name.
