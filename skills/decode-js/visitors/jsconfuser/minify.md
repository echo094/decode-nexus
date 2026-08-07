# jsconfuser/minify.js — no dedicated decoder needed

## 1. Target

No decode target of its own. Reversing Minify would mean reproducing the pre-minified
spelling, but per the encoder doc's Algorithm none of its behavior groups obscure program
logic the way an actual obfuscation transform does — each either resolves for free through
a shared, non-jsconfuser-specific pass, or is destructive/already-clearer with nothing
meaningful to recover.

## 2. Algorithm

Every one of Minify's behavior groups (see the [encoder doc](../../../js-confuser/transforms/minify.md))
falls into one of three buckets, none of which need a jsconfuser-specific file:

- **Literal shortenings** (`!0`/`!1`, `void 0`, `1/0`) are already undone by the
  shared, non-jsconfuser-specific `calculate-constant-exp.js` pass
  (`calculateUnaryExpression`'s `!`/`void` branches, `calculateBinaryExpression`
  for `1/0`), which [plugin/jsconfuser.js](../../plugins/jsconfuser.md) already
  traverses several times for other transforms' own literal cleanup. It runs
  unconditionally over the whole AST each time, so it catches Minify's
  shortenings for free regardless of where in the pipeline it happens to fire.
- **`var a; var b;` → `var a, b;`** merging is already undone by the shared
  `split-variable-declaration.js` (wired in for MovedDeclarations, order 25 — see
  the coverage table in
  [plugins/jsconfuser.md](../../plugins/jsconfuser.md#coverage-by-encoder-stage)),
  which splits any multi-declarator
  `VariableDeclaration` back apart regardless of which transform produced it.
- **Everything else** (constant folding, dead-code elimination, `a["key"]`→`a.key`,
  single-statement block unwrap, `if`/ternary collapsing, simple destructuring
  collapse) is either genuinely destructive (the pre-minified form is gone, same
  as after running any minifier, and there's nothing to recover since the
  remaining code is still semantically complete) or already reads *more* clearly
  than an unminified equivalent would.

## 3. Implementation

Verified empirically (not just by reading source) against the actual pinned encoder:
obfuscating `var a=!0,b=!1,c=void 0,d=1/0;` with `minify: true` and running the result
through `plugin/jsconfuser.js` recovers
`var a = true; var b = false; var c = undefined; var d = Infinity;` — one
`var` statement per declarator, all four literals restored — using only the two
generic passes above, with no jsconfuser-specific Minify code at all.

`deMinifyArrow`, this file's one-time sole mechanism, targeted a stale arrow-forwarding
wrapper template absent from the pinned encoder (the real `preserveFunctionLength`
mechanism, [`set-function-length-template.md`](../../../js-confuser/templates/set-function-length-template.md),
sets `.length` directly with no forwarding wrapper at all). Confirmed dead against real
samples (its own match log never fired; `function-length.js`'s already handled both call
shapes) and removed along with the now-meaningless `arrowFunc` plumbing it fed into
`function-length.js`, same "stale template from before an encoder rewrite"
failure mode as [DuplicateLiteralsRemoval](duplicate-literal.md) and
[StringConcealing/GlobalConcealing](string-concealing.md) hit before it.

## 4. Upstream Effects

**None of its own — there is no pass here to have any.** No dedicated visitor exists (see
Source), so nothing in this pipeline has an input for an earlier pass to reshape. The two
generic passes that absorb Minify's reversible half —
[`calculate-constant-exp.js`](../calculate-constant-exp.md) and
[`split-variable-declaration.js`](../split-variable-declaration.md) — own their own upstream
dependencies in their own docs.

This is not the same slot as what Minify does to *other* decoders' input. That is a
Downstream Effect of an encoder stage, it is item 2's whole subject here, and the sweep item
3 records is how far it was chased.

## 5. Known Gaps

Minify needing no decoder of its own doesn't mean its output is inert for every *other*
decoder — its rewrites still run before/alongside whatever transform a given decoder
targets, so that decoder's matchers see Minify's output, not the pre-minify shape they were
likely written and tested against. Two of its rewrites are confirmed hazards that already
broke a real decoder and are now tolerated — the encoder-side fact lives in
[control-flow-flattening.md](../../../js-confuser/transforms/control-flow-flattening.md)'s
Downstream Effects, the current tolerance in [control-flow.md](control-flow.md)'s
`parseWhileSwitch`/`readScopeMemberKey` (brace-stripping + computed-to-dot member rewrite)
and `parseReturnValue` (`return undefined` → bare `return`):

Two further rewrites were checked and are **not** hazards, so nothing needs to consume
them: `if`/`else` single-statement unwrap is always superseded by the same visitor call
replacing or removing the `IfStatement` itself before anything downstream can observe a
residual braceless form; the object-literal key rewrite (`{"key": 1}` → `{key: 1}`) touches
CFF's own scope-object literal but that literal's keys are never inspected by the CFF
decoder.

**Swept the rest of the decoder codebase for the two confirmed-hazard shapes**
(`grep -rn "isWhileStatement\|isForStatement\|isWithStatement\|WhileStatement\|ForStatement\|WithStatement"`
and separately `.get('body.body')` off a non-function node, for the brace-strip;
`grep -rn "computed: true"` for the member rewrite, both over `src/visitor/jsconfuser/*.js`):
every hit outside `control-flow-graph.js` either doesn't read into the exposed shape's
contents
([`string-compression.js#L24-L25`](https://github.com/echo094/decode-js/blob/6c974fb5720518fac9c6b3d4cf558ba90ef9f8e7/src/visitor/jsconfuser/string-compression.js#L24-L25)
walks *up* through `parentPath` to an enclosing `for`,
never into its own body) or keys on a shape (`states[i]`, a runtime-computed
`CallExpression`) `t.isValidIdentifier` gating could never touch. Contained to CFF's own
matchers as of this check — re-run these greps before adding any future decoder that
pattern-matches a loop/`with` body or a computed member.

**Aside, not minify-related:** the bare-return sweep (`grep -rn
"isReturnStatement\|ReturnStatement"` then `grep -rn "\.argument\."`) turned up one
pre-existing unguarded dereference,
[`pack.js#L34`](https://github.com/echo094/decode-js/blob/6c974fb5720518fac9c6b3d4cf558ba90ef9f8e7/src/visitor/jsconfuser/pack.js#L34)'s
`item.body.body[0].argument.left`,
reached only inside an already-narrowed Pack accessor-pair object. Noted rather than fixed
here since it's outside this transform's scope; revisit when Pack's own pair migrates.

## Source

`decoder/decode-js` has no `src/visitor/jsconfuser/minify.js` file — nothing is wired into
[plugin/jsconfuser.js](../../plugins/jsconfuser.md) for this transform beyond a comment at
that point explaining why.

## Fixtures

`test/visitor/jsconfuser/function-length.test.js` — the `deMinifyArrow`-removal aftermath:
both call shapes, the omitted-second-argument default, and a structural negative case.
