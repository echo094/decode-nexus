# obfuscator.js

> **Frozen (user decision).** This entry is not modified again — no bug fixes, no new coverage, no
> refactors. Everything further for this target goes to `obfuscatorx`
> ([decode-js.md](../decode-js.md#obfuscator-is-frozen-obfuscatorx-is-where-its-target-is-worked-on)).
>
> **So every defect below is a permanent description, not a worklist.** They are worth reading for
> exactly two reasons: they say what a user of this entry will actually experience, and each is a
> claim `obfuscatorx` has to beat. Anything phrased here as a gap to close means *closed in the
> other entry*.

Target: **javascript-obfuscator / obfuscator.io**. The largest and fullest plugin,
integrating ideas from `cilame/v_jstools` and `Cqxstevexw/decodeObfuscator`. It
is the canonical example of the [sandbox-assisted partial
evaluation](../decode-js.md#babel--isolated-vm-foundation) technique: it extracts the
obfuscator's own string-array + decoder functions, runs them in an `isolated-vm` isolate
(`virtualGlobalEval`), and substitutes evaluated results back into the AST.

## Pipeline (default export)

1. `PluginEval.unpack` — peel an `eval()` packer if present (see [eval](eval.md)); sets
   `global_eval` so `pack` re-wraps at the end.
2. `parse(code, { errorRecovery: true })`.
3. [delete-illegal-return](../visitors/delete-illegal-return.md),
   [lint-if-statement](../visitors/lint-if-statement.md),
   [split-variable-declaration](../visitors/split-variable-declaration.md), then strip
   `node.extra` from string/number literals (inline visitor).
4. **`decodeObject`** ("还原数值") — fold a `var o = { k: <literal> }` that is only ever read
   as `o.k` (non-computed): inline each literal at its use and remove the object. **It has no
   candidates in stock javascript-obfuscator output** — see below.
5. **`decodeGlobal`** ("处理全局加密") — the string-array decoder; see below. Returns `false`
   (aborting the whole plugin) if no string array is found.
6. **`purifyCode`** ("提高代码可读性") — readability pass: `lintIfStatement`,
   [prune-if-branch](../visitors/prune-if-branch.md), normalize `for`/`while` bodies to
   blocks, drop `EmptyStatement`s, [split-assignment](../visitors/split-assignment.md),
   [delete-unused-var](../visitors/delete-unused-var.md), `FormatMember`
   (`o["ab"]` → `o.ab`), method/property key de-computing and string→identifier, and
   [split-sequence](../visitors/split-sequence.md).
7. **`stringArrayLite`** — inline a constant literal array read only by numeric index.
8. **`decodeCodeBlock`** ("处理代码块加密") —
   [calculate-constant-exp](../visitors/calculate-constant-exp.md),
   [merge-object](../visitors/merge-object.md),
   [parse-control-flow-storage](../visitors/parse-control-flow-storage.md),
   `calculate-constant-exp` again.
9. **`cleanDeadCode`** — `calculate-constant-exp`, `prune-if-branch`,
   [remove-control-flow-ob](../visitors/remove-control-flow-ob.md).
10. Reparse the generated code (refresh bindings), run `purifyCode` again.
11. **`unlockEnv`** ("解除环境限制") — strip anti-tamper traps (below).
12. Generate; `PluginEval.pack` if `global_eval`.

### `decodeObject` reverses nothing this encoder emits

**Its matcher is keyed on exactly the two spellings the `Converting` stage guarantees absent.** It
requires an object literal whose every key is an `Identifier`, and it only removes that object if
every reference is the `object` of a **non-computed** `MemberExpression` with an `Identifier`
property. Property-name literalization eliminates both, unconditionally and at every phase-1 era:
identifier object keys become string literals and `o.foo` becomes `o['foo']`
([property-name-literalization.md](../../javascript-obfuscator/transforms/property-name-literalization.md)).

Measured as well as read. A census keyed on the **payload** — every `var x = { … }` with at least
one property, then reporting which of `decodeObject`'s gates each candidate fails — reads **zero**
identifier-keyed objects and **zero** non-computed identifier member accesses over the whole frozen
corpus, at every version column and every option set. The same census reads non-zero on the
pre-obfuscation fixtures, and a hand-written `var o = {a: 1}; o.a` drives every axis including the
full-candidate one, so the zero is not a blind probe
([probes.md](../probes.md)'s mirror-probe hazard).

**What this settles about the pipeline order.** `decodeObject` running *before* `decodeGlobal` looks
like `Converting`-reversal scheduled ahead of string-array-reversal, which would be the reverse of
the encoder's stage order. It is not: `decodeObject` reverses no `Converting` transformer. This
plugin's actual `Converting` reversal is `mergeObject` and `calculateConstantExp` inside
`decodeCodeBlock` (step 8), which runs *after* `decodeGlobal` and is therefore consistent with
reverse stage order. The apparent discrepancy came from attributing `decodeObject` to that stage.

Two consequences for anything reading this plugin as prior art:

- **It is prior art for a constant-object inliner, not for `Converting` reversal.** The shape it
  folds is hand-written code — plausibly reached through the `common`/`eval` targets or a partly
  decoded sample, but never through this one on stock output.
- **Its abort guard is dead.** `decodeObject` returns `ast` on every path, so
  `if (!decodeObject(ast)) return null` can never fire. Unlike `decodeGlobal`'s identical-looking
  guard, which aborts the whole plugin routinely.

Bounded honestly: this is measured across phase 1's range. Both transformers predate it (`0.9.0`
and `0.15.0`) but their content below `2.9.0` is unswept, and at `5.5.0`
`MemberExpressionTransformer` gains an ignored-node escape that lets some `.name` accesses survive —
so the claim is not automatically true at the pin
([versions.md](../../javascript-obfuscator/versions.md), `E-propname-*`).

## String-array detection (`decodeGlobal`)

**The algorithm in one sentence: it does not reimplement the string array, it re-executes it.**
Each detector locates the subsystem structurally and captures its **source text**; that text is
evaluated in the isolate; then every call site is decoded by evaluating *that call* and
substituting the string it returns. Nothing here models rotation, index arithmetic, base64 or rc4 —
the encoder's own prelude does all of it.

That is why the plugin is indifferent to things a static reversal would have to handle separately:
the per-item encoding (`none`/`base64`/`rc4`), the index shift, the rotation amount, and the
rotator's own era. It pays for that with a hard dependency on being able to run the extracted code,
which is what every failure mode below is ultimately about.

Tries three detectors in order, newest first, until one returns a `stringArrayName`:

- **`stringArrayV3`** (obfuscator **≥ 2.19.0**) — the string array lives inside a
  wrapper function `function aaa(){ const bbb=[…]; aaa=function(){return bbb}; return
  aaa() }`, matched with a `checkPattern` fingerprint. References are classified into
  `func2` (the rotate call) and `func3` (calls-wrapper functions).
- **`stringArrayV2`** (**< 2.19.0**, single array) — locate the **rotate function** by
  fingerprint (`fp1` for ≥ 2.10.0, `fp2` for < 2.10.0), then handle the
  calls-wrapper across four sub-version shapes (`2.12.0 ≤ v < 2.15.4`, `v < 2.12.0`,
  `2.15.4 ≤ v < 2.19.0`).
- **`stringArrayV0`** — no rotate function present; the array can only be confirmed via
  the StringArrayCallsWrapper. **Reads as an options case but is version-bounded in practice**, and
  the bound is not written anywhere in the branch: `check_wrapper` requires the wrapper *function*
  to be a declarator's init (`ref.key !== 'init'` → `null`), which is the
  [`E-sa-wrapper-var-fn-expression`](../../javascript-obfuscator/versions.md) shape alone. So a
  rotation-disabled sample is detected at `2.9.6`–`2.11.1`, and from `2.12.0` — where the wrapper
  becomes a hoisted function declaration — **all three detectors miss it** and the plugin aborts at
  `Cannot find string list!`. Swept over the corpus's rotation-disabled set at every column: `V0`
  fires at `2.9.6`/`2.10.0`/`2.11.1`, nothing fires at `2.12.0` through `2.18.1`, and `V3` takes it
  from `2.19.0` because that detector keys on the accessor rather than the rotator. The gap is a
  whole era wide and is invisible to a reader of the branch.

The detected function sources are `virtualGlobalEval`'d into the isolate, then **`dfs`**
walks each decoder's `referencePaths`: a call that evaluates to a string is replaced with
`t.StringLiteral`; a call that throws is treated as a *chained/nested* decoder and
recursed into, accumulating parent definitions first. Four chained-call reference kinds
are handled: `VariableDeclarator` and `FunctionDeclaration` (original), plus
`AssignmentExpression` (issue #50) and `FunctionExpression` (issue #94).

**Throwing is the classifier, not an error path.** `dfs` distinguishes "this call returns a string"
from "this identifier is an intermediate wrapper" purely by whether evaluating it throws. Cheap and
era-agnostic; also unfalsifiable in the other direction — a call that throws for an unrelated
reason is silently reclassified as a chained wrapper, and `getChild` then rejects it with
`Unexpected chained call`.

**Every era branch here is about the *root* wrapper's definition site**, never about the per-scope
wrappers and never about index arithmetic: `v < 2.12.0` (declarator), `2.12.0 ≤ v < 2.15.4`
(named function declaration), `2.15.4 ≤ v < 2.19.0` (self-replacing), plus `stringArrayV3` at
`≥ 2.19.0`. The scope wrappers are handled by the same `dfs` recursion at every version, with no
version test anywhere in it. That is the practical consequence of re-executing rather than
modelling, stated at the point where a reader would otherwise go looking for the missing branch:
the encoder changed how a scope wrapper computes the index it passes upward, and an evaluating
reversal never had to notice.

### Where it is weak

Recorded because this plugin is the prior art any replacement reads first, and adopting an
algorithm is not the same as adopting its gates. None of these is a defect report: the plugin
reverses the whole 2.19.0 corpus column cleanly.

| Weakness | What it is |
|---|---|
| `checkPattern` is a **subsequence** test, not a substring test | it walks `code` and `pattern` together and passes if every pattern character is met *in order*, however far apart. So a fingerprint can match code that merely contains its characters scattered across unrelated statements. Loose by construction, and the looseness is invisible at the call site. It is also the named mechanism behind the fail-open class W6 describes: a fingerprint this loose stops separating "my layer" from the one beneath it, which is what [#142](https://github.com/echo094/decode-js/issues/142) hit in a sibling plugin that shares this helper — a risk here, not a measured failure |
| `stringArrayV3` gates on statement count | `body.length < 2 \|\| > 3` on the holder function, whose statements the encoder's own adjacent-statement merging fuses — its own comment notes the assignment "is merged into the ReturnStatement" in some cases. It accommodates two spellings rather than reading the shape, so a third merge outcome fails it closed |
| `stringArrayV2` gates on how many code fragments it collected, and **the count can be inflated by its own extraction** | `stringArrayCodes.length < 3` → `Essential code missing!`. An arity heuristic standing in for "did I find the array, the wrapper and the rotator" — so more fragments always reads as healthier, and the one failure mode it cannot see is duplicates. It walks *every* reference to the string array and pushes the enclosing function once per reference, having emptied that function's body after the first push. Where the accessor names the array more than once — any non-`none` `stringArrayEncoding` does, because the accessor writes its decoded value back into the array — the extracted text ends with empty redefinitions of the accessor. **The trigger is the encoding being enabled at all, not rc4**: swept across the matrix, the plain and `preset-default` cells resolve one reference and emit no duplicate, while `base64`, `rc4` and the multi-encoding sets each resolve three and emit two — so `encoding-base64` and `preset-medium`, which carry no rc4, hang exactly as the rc4 sets do. Under the `2.12.0 ≤ v < 2.15.4` branch the accessor is a hoisted **function declaration**, so the last definition wins and the accessor becomes a no-op; the rotator's checksum can then never match and its `while(!![])` search **never returns**. Attributed on three legs, not one: the **undecoded sample itself runs to completion** and prints its fixture's lines at this era and its neighbours, so nothing in the emitted code loops; evaluating all extracted fragments never returns; and evaluating the same fragments minus the emptied redefinitions returns immediately. The loop exists only in the extraction. **Bisected against this plugin's own pre-passes** — gating `deleteIllegalReturn`, `lintIfStatement`, `splitVarDeclaration`, the `node.extra` strip and `decodeObject` one at a time — the duplicate and the non-termination are both present with **none** of them applied, so the defect is `stringArrayV2`'s alone; what the bisect does add is that `splitVarDeclaration` **aggravates** it, taking the extraction from one emptied redefinition to two. The same bisect run against the plain cell at the same version reads one fragment per piece at every level, which is the control that makes the rc4 reading a finding rather than a count. **The failing range is exact and it coincides with this plugin's own branch boundary**: swept across every corpus column, the affected sets hang at `2.12.0` and `2.15.3` and complete at `2.11.1` and `2.15.4` — the `2.12.0 ≤ v < 2.15.4` row of the era table above, which is the only branch that empties the matched function's body. **Regeneration is not the cause, tested rather than assumed**: the plugin's own regenerated fragments terminate when the emptied redefinitions alone are removed, holding the regenerated text constant. And the wrapper's inline `selfDefending` guard — the other thing that plausibly loops on re-spelled code — is present in `preset-high` at **every** column and hangs at none outside that range, so it is not implicated either. It needs both halves — the declaration spelling *and* an accessor that names the array twice — which is why the baseline cell at the same version decodes and the rc4 cell at neighbouring eras does too. This is [encoder-decoder-method.md](../../encoder-decoder-method.md)'s **W5** tell arriving for real: self-validating machinery cannot terminate on an incomplete extraction, so a hang here means the extraction, never a hostile sample |
| detection and extraction are fused | each `stringArrayVn` fingerprints *and* mutates the tree. A fingerprint miss and "no string array present" both arrive at `Cannot find string list!` → `return false`, aborting the entire plugin, so the diagnostic a user needs cannot be produced |
| the isolate is module-scope | one global object shared by every decode in the process, so two samples decoded in one process contaminate each other. This is a correctness constraint on anything scoring it — [probes.md](../probes.md) |
| only `ReferenceError` is recovered | the `catch` around the prelude eval handles issue #31 by hoisting the missing binding and retrying; any other throw is swallowed and the call-site walk then fails in a less legible place |
| `stringArrayLite` requires every reference to be a numeric-index read | one non-conforming reference disqualifies the whole array, all-or-nothing. Correct per W5, and worth knowing it is a separate, simpler pass from `decodeGlobal` rather than a fallback of it |
| it **throws** on a function-form scope wrapper below `E-sa-scope-wrapper-fn-declaration` | scored over the whole matrix: every option set carrying one completes at `2.16.0` and above and throws `Cannot read properties of undefined` at `2.15.4` and below — after detection has *committed*, so it is a `TypeError` mid-decode rather than a clean decline, which is the fail-open direction. The boundary is exact, not bracketed: the same sets complete 3/3 at `2.16.0` and 0/3 at `2.15.4`. It coincides with the shape boundary on [versions.md](../../javascript-obfuscator/versions.md)'s `E-sa-scope-wrapper-*` axis, found by an unrelated instrument — the function form is a declarator below it and a hoisted declaration from it. So this plugin is prior art for the **declaration era only**; for the era below there is no working reversal here to read |
| the `AssignmentExpression` chained-call branch is **self-flagged incomplete** | its own comment says the case is not yet complete and may produce extra replacements, and the branch is the only one that re-enters `dfs` on the same item after rewriting it to a bare identifier. It is one of the four chained-call spellings, so anything adopting this recursion inherits the weakest of them unless it re-derives that case |
| **`decodeGlobal` runs exactly once** | the default export calls it a single time and aborts on failure. A source obfuscated **more than once** carries nested string-array layers, and nothing re-detects after the outer one is decoded — see below |
| `purifyCode`'s inline **`FormatComputed` un-computes a string key unguarded** | it sets `computed = false` for any `Method\|Property` whose key is a string literal, with no exclusion list. Three keys change meaning when un-computed, and the repository's own shared helper `safe-func.js` ([decode-js.md](../decode-js.md#source-layout-decoderdecode-jssrc))'s `uncomputeStringKey` already refuses all three: `{ ["__proto__"]: v }` defines an own property while `{ "__proto__": v }` sets the prototype; `class C { ["constructor"](){} }` is an ordinary method while `'constructor'(){}` **is the class constructor**; and `static ["prototype"]` is a runtime error un-computed. Confirmed by running both class forms — the quoted one is invoked by `new`. **Not reachable from stock encoder output**, which exempts `constructor` from literalization and never emits the other two, so this is a latent defect rather than a measured failure: it needs a *source* that already wrote the computed form. It is the clearest case in this stage where the shared visitor is better than the plugin's inline copy |

### Repeated obfuscation, and why it defeats shape matching specifically

A source can be run through the obfuscator more than once. The second pass treats the first pass's
**output** as its input, so the inner layer's holder, wrapper and rotator are themselves
obfuscated: the inner rotator's `'push'` and `'shift'` keys become calls into the *outer* string
array, its numeric constants become arithmetic trees, and its identifiers are renamed again.

The general rule — layers stack rather than merge, peeling is outermost-first, and crossing a layer
boundary is a defect rather than a shortcut, fail-open — is
[encoder-decoder-method.md](../../encoder-decoder-method.md)'s **W1 limiting case**, and is not
restated here; this plugin's own exposure to the fail-open half is the `checkPattern` row above.
What is specific to this plugin:

- **Both halves of its technique are layer-ordered, and neither sees through a layer.** The
  fingerprints fail on an inner layer, and so does evaluation: an inner prelude extracted verbatim
  throws `ReferenceError` on the *outer* wrapper it references, because its own array elements are
  outer-encoded calls. So re-encoding costs a **loop** — the shortfall is scheduling (T9 case 2),
  not matcher reach — and it costs nothing else, since by the adds-wraps-only invariant each layer
  is exactly a single-encode sample once it is outermost.
- **Measured: on a stock double encode it peels exactly one layer per run and does not corrupt.**
  Every cell of the nested set decodes, and the census signature drops from the two-layer reading
  to precisely the one-layer reading; a second run takes it to zero on every axis, with output
  matching the pre-obfuscation fixtures' reported lines. So the field practice of running it twice
  is not a workaround for a defect here — it is the loop, and each turn of it is clean. Recipe:
  [corpus.md](../../javascript-obfuscator/corpus.md)'s nested section.

  **The intermediate is checkable against a derived expectation, not just eyeballed.** A second
  encode's *input* is the first encode's *output*, so peeling the outer layer must reproduce that
  input. It does: the once-peeled result has the same holder / wrapper / rotator signature as a
  separately built singly-encoded sample, it runs and prints the fixture's lines, and its array
  literal is the inner array restored to plain string literals. Only local identifier names and
  formatting differ — the first because the outer encode renamed them irreversibly, the second
  because this plugin pretty-prints. **Emitting still-obfuscated code is therefore the correct
  result of a one-layer decode**, not a partial one.
- **The recovered inner layer arrives canonical, however heavily the outer layer re-spelled it.**
  Measured with the inner layer fixed at the string-array base set and the outer layer varied
  across the robustness sets — `numbersToExpressions`, control-flow flattening, dead-code
  injection, `splitStrings` and `high-obfuscation`: **every** cell peels, still runs, and carries
  one string-array shape signature, the pristine single-encode one. Only local identifier names
  differ.

  The mechanism points somewhere non-obvious: robustness comes from the peel being **complete**,
  not from any matcher being lenient. The outer `numbersToExpressions` rewrote the inner wrapper's
  index shift into an arithmetic tree, and this plugin's own constant folding restored the literal
  shift before anything examined it. So an inner layer that does *not* look canonical is evidence
  the outer decode was incomplete — a producer-side diagnosis (T9 case 1), not a reason to widen
  the matcher (case 4).

**The discriminator, and it is structural rather than heuristic.** The outermost layer is the one
whose own machinery is spelled in **plain string literals**; every inner layer has its
string-valued parts routed through an outer layer's calls wrapper. At `2.19.0`, doubly encoded, the
inner array's elements are `outerWrapper(0xNN)` calls rather than literals, and the inner rotator's
`push`/`shift` member keys are too:

```js
// inner rotator, under an outer layer — no string literal anywhere in it
_0x314b2f[_0x1bd7de(0xa2)](_0x314b2f[_0x1bd7de(0x9f)]())
```

A useful consequence for any census over this plugin's input or output: matchers keyed on **string
literals** (the array holder, the rotator) are layer-*blind* and see only the outermost layer,
while matchers keyed on **numeric shape** (the calls wrapper — `index = index - N`, `arr[index]`)
are layer-*transparent* and see every layer, because re-encoding hides strings and not numbers. So
**the excess of wrapper count over holder count is the number of layers still underneath** — equal
counts mean one layer, and a census reading both at zero means done. That relation is what makes a
one-layer peel checkable without expected output.

**The working answer today is the user's hands, and the recorded procedure is more than "run it
twice."** For one real sample,
[#138](https://github.com/echo094/decode-js/issues/138#issuecomment-2940324016) records:
`obfuscator` → `common` → `common` → *hand-edit the source* → `sojsonv7` → `common`. Six
invocations across **three targets**, on a branch cut for that sample's modified obfuscator. It is
the worked instance of W6's "the layers need not come from the same encoder", and the three
verdicts a plugin owes the driver are stated there rather than here. What is specific to this
plugin and this package:

- **This plugin can express none of those three verdicts** — every one of them arrives as
  `Cannot find string list!`.
- **Normalization is re-run between layers**, twice consecutively at one point. A decode of decoded
  output being well-defined is what the whole procedure rests on.
- **An implicit global defeats binding resolution.** The hand edit was `_ = i;` → `var _ = i;`:
  undeclared, `_` becomes a global and the tool cannot handle it. Any pass resolving aliases or
  call sites through
  `scope.getBinding` reads nothing on that shape — and reads it as *absence*, not as failure.
- **Real samples come from modified obfuscators.** Hence the `variant_128` branch, and the
  maintainer's position that per-variant adaptation is not realistic. Shape claims describe the
  stock encoder.

Nothing in the frozen corpus exercises any of this: every cell is encoded exactly once
([corpus.md](../../javascript-obfuscator/corpus.md) builds one encode per cell), so the behaviour
is **unmeasured in this repository** even though it is well attested in the field.

## Anti-tamper removal (`unlockEnv`)

Three fingerprint-matched (`checkPattern`) visitors, each removing both the guard and its
call-func binding:

- **`deleteSelfDefendingCode`** — the self-defending formatter guard (`this`, function
  expr; patterns `@7920538`, `@7135b09`, `#94`).
- **`deleteDebugProtectionCode`** — the `debugger` infinite-loop protection, including its
  `setInterval` variants (`@e8e92c6`, `@51523c0`) and call form, with `#95` exceptions.
- **`deleteConsoleOutputCode`** — the console-disabling guard.

The header comment warns `unlockEnv` "may mistakenly delete some code" and can be disabled.

**All three share one removal strategy, and it is sound for a reason the source does not state.**
Each matches the guard, deletes the reference that triggers it, deletes the guard's own definition,
then resolves the *calls controller* from the guard's callee and deletes that too. That last step
is only safe because a controller serves exactly one guard — which is a property of the encoder,
not of this code: each helper group emits its own controller rather than sharing one
([custom-code-helpers.md](../../javascript-obfuscator/transforms/custom-code-helpers.md)). Resolved
over the decoded corpus, every controller has exactly one guard, so the strategy never deletes a
controller another guard still needs.

**The order inside that strategy is load-bearing, and reads as arbitrary.** The definition is
removed *before* the controller's binding is re-crawled and tested for references. It has to be:
the console-output callback references its own controller several times in its body
(`{cc}.constructor.prototype.bind({cc})` and `{cc}.bind({cc})`), so testing first would find live
references on every console-output cell. Measured on decoded output, the controllers carrying
references beyond their own guard-call are exactly the console-output ones. Anything reimplementing
this must either keep the order or check liveness a different way.

**Where the strippers actually reach, measured.** Run over the 243 corpus cells that enable at
least one helper, then read with a residue census defined from the encoder rather than from these
visitors: on **every** cell the plugin completes, all four helper shapes are driven to zero *and*
the output still runs and reproduces its fixture's lines — so the strip is both total and
non-destructive despite the header warning. The cells it does not complete fail before
`unlockEnv` ever runs, and the failures land exactly on the two defects recorded above: the
extraction hang across `2.12.0 – 2.15.3`, and the function-form scope-wrapper throw at `2.15.4`
and below. The four single-helper option sets and `preset-low` complete at every version column.
**So this pass's reach is bounded by the string-array stage, not by its own matchers** — which is
what makes it prior art worth adopting rather than merely reading.

**The weak part is the matching, not the removal.** `checkPattern` is the subsequence test above,
applied to generated code, so each guard is identified by characters appearing in order rather than
by shape — and the three self-defending patterns are really two emitted eras crossed with the two
declaration kinds the encoder's prevailing-kind rewrite produces, a correspondence nothing in the
source names. It also logs `Call func … unexpected ref!` when the controller still has references
and then deletes it anyway, which is the fail-open direction on the one check that could have
declined.
