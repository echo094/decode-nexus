# Shuffle-GPT-5.5: binding-aware AST subtree rotation

**Evidence status: source-inspection only.** This page documents only the pinned
`Shuffle-GPT-5.5` implementation. It records source-backed mechanism and safety boundaries;
it does not claim execution, transfer, decoder coverage, or production support.

## 1. Target

Replace calls to a recognized shuffle `FunctionDeclaration` with an `ArrayExpression` whose
element subtrees have been rotated by the statically known count, then remove the recognized
declaration if its lexical binding has no remaining references. The target function implements
the push/shift rotation loop and returns its first parameter. Unlike the other sample, this
transform preserves each array element as an AST subtree instead of requiring primitive
literal materialization.

The successful output representation is therefore a generated array literal containing deep
clones of the original element nodes in rotated order. The implementation can carry nested
expressions, spreads, calls, and other AST element forms through this representation after
the only explicit array-element rejection—a sparse hole.

## 2. Algorithm

The transform proceeds as follows:

1. Parse with `sourceType: "unambiguous"`, `allowReturnOutsideFunction: true`, and the
   listed syntax plugins. Traverse `FunctionDeclaration` nodes. `matchShuffleFunction`
   accepts at least two identifier parameters, exactly two body statements, a `for` loop,
   and a return of parameter 0. The loop may initialize its index with `var i = 0` (without
   restricting declaration kind) or `i = 0`, increment with `i++` or `i += 1`, and use a
   direct or one-statement-block `array.push(array.shift())` body. Store the Babel binding of
   each accepted named declaration.
2. Traverse calls. Require a direct identifier callee whose binding is in the collected map.
   Require at least two arguments, an `ArrayExpression` first argument, and a count whose
   path Babel evaluates confidently to a finite integer. Reject sparse arrays. Deep-clone
   every element AST node, compute a modulo-normalized left-rotation offset, and concatenate
   the two slices. Replace the call with the rotated array expression.
3. Crawl scopes and remove each collected declaration whose binding has zero references.
   Generate the AST with comments retained and minimal escaping. Calls that fail any gate
   remain unchanged; their reference prevents normal cleanup of the declaration.

The state crossing the rewrite boundary is:

| State | Construction | Invariant and consumer |
| --- | --- | --- |
| `shuffleBindings: Map<Binding, info>` | Recognized declaration bindings from the first traversal | Call recognition is lexical-binding-aware rather than name-only. |
| `arrayArgumentPath.node.elements` | Original `ArrayExpression` element node list | Holes decline; all other element node kinds are cloned deeply, so the state is AST, not evaluated values. |
| `count: integer` | `finiteIntegerFromPath` over argument 1 | Must be confident, finite, and integral; `rotateLeft` reduces it modulo array length and normalizes negative offsets. |
| replacement `ArrayExpression` | `t.arrayExpression(rotateLeft(clonedElements, count))` | The call disappears and the cloned element subtrees are re-emitted in rotated order. |

The solution-level pseudocode is:

```text
ast = parseJavaScript(source)
bindings = { lexical binding of each named FunctionDeclaration accepted by matcher }
for each call:
    if callee binding not in bindings: continue
    if fewer than two args or arg0 is not ArrayExpression: continue
    count = confident finite integer evaluation of arg1; if absent: continue
    if array has a hole: continue
    elements = deep clones of array element AST nodes
    offset = ((count mod length) + length) mod length, or zero for empty array
    replace call with elements[offset:] + elements[:offset]
crawl and remove recognized declarations with zero binding references
return generate(ast, comments=true)
```

## 3. Implementation

The source-owned phases and their concrete decisions are:

| Phase | Source-backed implementation and representation | Material branch or boundary |
| --- | --- | --- |
| Parsing substrate | [`parseJavaScript`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/Shuffle-GPT-5.5/Shuffle-GPT-5.5.js#L7-L28) uses `sourceType: "unambiguous"`, permits returns outside functions, and enables the listed modern syntax plugins. | A parser failure propagates; the transform entry has no catch/fallback. |
| Matcher normalization | [`unwrapSingleStatementBlock`, `bindingNameMatches`, `isZero`, and `isOne`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/Shuffle-GPT-5.5/Shuffle-GPT-5.5.js#L30-L48) provide shape helpers. [`getForLoopIndexName`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/Shuffle-GPT-5.5/Shuffle-GPT-5.5.js#L50-L69) accepts declaration or assignment initialization; [`isIndexIncrement`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/Shuffle-GPT-5.5/Shuffle-GPT-5.5.js#L79-L93) accepts `++` or `+= 1`; `isPushShiftStatement` and `isReturnArray` enforce the operation and return shapes at lines 95–116. | The function must have at least two identifier parameters and exactly two body statements. Extra parameters are tolerated; only the first two participate in matching. Any mismatch declines the declaration. |
| Recognition and binding state | [`matchShuffleFunction`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/Shuffle-GPT-5.5/Shuffle-GPT-5.5.js#L118-L153) returns parameter names for accepted declarations. The first traversal in `deobfuscateShuffle` stores the declaration's parent-scope Babel binding in `shuffleBindings` at lines 174–195. | A declaration without an identifier is ignored. The later call matcher must resolve to the same binding, preventing a merely same-spelled unrelated function from being rewritten. |
| Count state | [`rotateLeft`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/Shuffle-GPT-5.5/Shuffle-GPT-5.5.js#L155-L162) handles an empty list and computes `((count % length) + length) % length`. [`finiteIntegerFromPath`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/Shuffle-GPT-5.5/Shuffle-GPT-5.5.js#L164-L172) accepts only a confident, finite, integral Babel evaluation. | The source permits statically evaluable count expressions, not just numeric literal syntax. An unconfident, non-finite, or fractional result declines the call. |
| AST state and rewrite | The call traversal at [`deobfuscateShuffle`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/Shuffle-GPT-5.5/Shuffle-GPT-5.5.js#L197-L231) resolves the callee binding, requires at least two arguments and an array expression, rejects holes, deep-clones each element with `t.cloneNode(element, true)`, rotates the node list, and replaces the call with `t.arrayExpression(...)`. | There is no element-literal or purity gate. Expression nodes and spread nodes can be reordered, so source inspection does not establish runtime equivalence where evaluation order or side effects matter. |
| Cleanup and emission | After replacement, [`deobfuscateShuffle`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/Shuffle-GPT-5.5/Shuffle-GPT-5.5.js#L233-L255) crawls scope, iterates collected declarations, removes bindings with zero references, and calls Babel `generate` with comments and minimal escaping. | Cleanup looks up each recorded name from `Program` scope. Nested recognized declarations may not be found by that program-scope lookup even after their own binding becomes unused; this is an implementation gap, not a generalized cleanup guarantee. |
| CLI and exports | [`runCli`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/Shuffle-GPT-5.5/Shuffle-GPT-5.5.js#L257-L279) is guarded by `require.main === module`; lines 281–284 export `deobfuscateShuffle` and `matchShuffleFunction`. | Missing CLI input sets `process.exitCode` and returns. The page documents the exported static transform; it does not claim that the CLI or any caller executes transformed source. |

The implementation is source-local: parser and matcher helpers, `rotateLeft`,
`finiteIntegerFromPath`, and the `deobfuscateShuffle` coordinator are owned by this page.
There is no delegated helper page.

## 4. Upstream Effects

There is no earlier sample-local decoder pass. The parser configuration in
[`parseJavaScript`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/Shuffle-GPT-5.5/Shuffle-GPT-5.5.js#L7-L28) establishes the AST accepted by all later traversals. The transform's first traversal establishes `shuffleBindings`; the call traversal is downstream of that map and cannot use name-only association without changing the source-defined target boundary.

The pass does not consume a prior recovered array/order table. Its intermediate state is the
original element-node list plus a count from confident static evaluation. The cleanup crawl
and generator are downstream stages in the same function. No other sample-local pass is
specified.

## 5. Known Gaps

- The call target is binding-aware, but the matcher itself compares parameter and member
  identifier spellings and does not prove built-in `push`/`shift` methods or protect against
  unusual binding/property effects beyond the exact AST shape.
- Array holes decline, but arbitrary non-hole AST elements—including calls, member access,
  spreads, assignments, and other expression forms—are accepted and reordered. Reordering
  those nodes can change evaluation order, side effects, iterator behavior, or exceptions;
  no purity or semantic-equivalence guard is present.
- `finiteIntegerFromPath` relies on Babel's confidence result and returns only the numeric
  value. The source does not document or independently validate every expression class that
  `path.evaluate()` may accept.
- Calls with extra arguments are accepted because only arguments 0 and 1 are inspected. This
  follows the matched function body but is still an unmodeled input-shape extension.
- The cleanup loop re-queries each recognized name from `Program` scope rather than removing
  the exact stored binding object. Nested declarations can therefore remain even when their
  local binding has no references.
- Only `FunctionDeclaration` targets with direct identifier calls are recognized. Function
  expressions, member/computed callees, optional calls, and other equivalent spellings are
  outside the documented match.
- The supplied tests and output files are not execution evidence here. Runtime equivalence,
  unseen-input transfer, and production decoder coverage remain unresolved.

## Source

All algorithm claims in this page come from the pinned corpus revision
`e90be6ca716e28f4bba91fe39615a665656bd802`:

| Pinned source | Ownership and anchors |
| --- | --- |
| [`Shuffle-GPT-5.5/Shuffle-GPT-5.5.js`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/Shuffle-GPT-5.5/Shuffle-GPT-5.5.js) | Parser/helpers at lines 7–116; `matchShuffleFunction` at 118–153; `rotateLeft` and `finiteIntegerFromPath` at 155–172; three-pass `deobfuscateShuffle` at 174–255; CLI and exports at 257–284. |

The source is frozen corpus input. The line spans above are implementation anchors, not
execution or qualification evidence.

## Fixtures

| Pinned fixture | Claim it pins | Evidence boundary |
| --- | --- | --- |
| [`Shuffle-GPT-5.5/README.md`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/Shuffle-GPT-5.5/README.md#L1-L12) | Sample provenance, prompt, and explicit “own work only” scope | Provenance only; not an independent algorithm or runtime result. |
| [`Shuffle-GPT-5.5/Shuffle.js`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/Shuffle-GPT-5.5/Shuffle.js#L1-L5) | The supplied push/shift function shape and numeric-array input | Exact input provenance and intended-check evidence. |
| [`Shuffle-GPT-5.5/Shuffle-GPT-5.5.test-shuffle-input.js`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/Shuffle-GPT-5.5/Shuffle-GPT-5.5.test-shuffle-input.js#L1-L5) | The shuffle test input used by the sample runner | Intended-check provenance; no transfer result is claimed. |
| [`Shuffle-GPT-5.5/Shuffle-GPT-5.5.output-from-sample.js`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/Shuffle-GPT-5.5/Shuffle-GPT-5.5.output-from-sample.js) | Empty generated-output artifact retained in the pinned sample | Provenance only; the empty file supplies no algorithm or behavioral claim. |
| [`Shuffle-GPT-5.5/Shuffle-GPT-5.5.test-pass-through-input.js`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/Shuffle-GPT-5.5/Shuffle-GPT-5.5.test-pass-through-input.js#L1-L7) | An alternate `pop`-based function intended as a non-target | Intended safe-decline check; no behavior result is claimed. |
| [`Shuffle-GPT-5.5/Shuffle-GPT-5.5.test-pass-through-output.js`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/Shuffle-GPT-5.5/Shuffle-GPT-5.5.test-pass-through-output.js#L1-L5) | The retained pass-through output paired with that input | Intended-check provenance; no measured result is claimed. |
| [`Shuffle-GPT-5.5/Shuffle-GPT-5.5.test-runner.js`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/Shuffle-GPT-5.5/Shuffle-GPT-5.5.test-runner.js#L1-L60) | Intended assertions for transformed text, cleanup, and pass-through behavior | Test intent only; no validation result is claimed. |
