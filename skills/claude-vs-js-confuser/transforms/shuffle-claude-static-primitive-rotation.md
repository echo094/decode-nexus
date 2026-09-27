# Shuffle-Claude: static primitive rotation

**Evidence status: source-inspection only.** This page documents only the pinned
`Shuffle-Claude` implementation. It records source-backed mechanism and safety boundaries;
it does not claim execution, transfer, decoder coverage, or production support.

## 1. Target

Replace calls to a narrowly recognized two-parameter shuffle function with the statically
rotated array that the function would return, then remove the shuffle declaration when its
outer binding has no remaining references. The target function is a `FunctionDeclaration`
whose two-statement body is a rotation loop followed by `return` of its first parameter. The
target call has the function name as an identifier callee, a dense static array argument, and
a numeric count.

The output representation is a Babel `ArrayExpression` containing newly constructed literal
nodes for the recovered primitive sequence. It is not a runtime call and it does not retain
the original function when cleanup finds no references.

## 2. Algorithm

The transform uses three ordered AST traversals:

1. Parse the input as a Babel script. Traverse every `FunctionDeclaration` and add its name
   to `shuffleNames` only if `isShuffleFunction` accepts the exact shape described below.
   If the set is empty, return the original source immediately.
2. Traverse every `CallExpression`. A direct identifier callee whose name is in
   `shuffleNames` is a candidate. The first two arguments must be an `ArrayExpression` and
   a `NumericLiteral`; extra arguments are ignored. Every array element must be dense and
   must convert through `extractLiteral` to a number, string, boolean, `null`, or
   `undefined`. Copy those primitive values into a working list, apply the original loop's
   repeated `arr.push(arr.shift())` operation exactly `countArg.value` times, convert the
   resulting values back to Babel nodes with `valueToNode`, and replace the call.
3. Crawl the parent scope for each recognized declaration after call replacement. Remove the
   declaration only when its binding has zero remaining references. Generate the resulting
   AST with Babel; recognized-but-unhandled calls remain in the tree and therefore normally
   keep their function declaration alive.

The state crossing the rewrite boundary is:

| State | Construction | Invariant and consumer |
| --- | --- | --- |
| `shuffleNames: Set<string>` | Names of accepted function declarations | Call matching and cleanup are by spelling, not binding identity. |
| `elements: primitive[]` | `extractLiteral` over every non-hole array element | Every item is one of the five supported primitive categories plus numeric/string/boolean values; `evaluateShuffle` mutates only a shallow working copy. |
| `rotations: number` | The call's `NumericLiteral.value` | The loop uses the raw number in `i < rotations`; there is no modulo, finiteness, or integer guard. |
| replacement `ArrayExpression` | `result.map(valueToNode)` | The call is replaced by fresh literal nodes; unsupported values are outside the accepted gate. |

The core transformation can therefore be reconstructed as:

```text
names = { fn.id.name | isShuffleFunction(fn) }
if names is empty: return source
for each call with identifier name in names:
    if first arg is not ArrayExpression or second is not NumericLiteral: continue
    values = extractLiteral for each dense element; if any fails: continue
    repeat count.value times: values.push(values.shift())
    replace call with ArrayExpression(valueToNode(values))
crawl and remove each recognized declaration whose outer binding has no references
return generate(ast)
```

## 3. Implementation

The source-owned phases and their concrete decisions are:

| Phase | Source-backed implementation and representation | Material branch or boundary |
| --- | --- | --- |
| Recognition | [`isShuffleFunction`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/Shuffle-Claude/Shuffle-Claude.js#L34-L97) requires exactly two parameters, exactly two body statements, a second-statement return of parameter 0, and a first-statement `for` loop. The loop must be `var counter = 0`, `counter < param1`, `counter++`, and one direct or single-statement-block expression `param0.push(param0.shift())`. | Any mismatch declines the function. The matcher compares identifier names and does not obtain a lexical binding for the function or call. |
| Name collection | The first traversal of [`deobfuscate`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/Shuffle-Claude/Shuffle-Claude.js#L150-L167) records the declaration name in `shuffleNames`. | With no accepted declaration, the function returns the original `code` without generation. |
| Literal state | [`extractLiteral`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/Shuffle-Claude/Shuffle-Claude.js#L110-L128) accepts numeric, string, and boolean literals, `null`, the identifier spelling `undefined`, and unary-minus numeric literals. Sparse slots and all other AST element kinds decline the individual call site. | The `undefined` test is spelling-based; no binding check is performed. |
| Ordering state | [`evaluateShuffle`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/Shuffle-Claude/Shuffle-Claude.js#L100-L108) shallow-copies the primitive list and repeats `push(shift())` while `i < rotations`. | Negative counts perform no iterations; fractional or unusually large numeric values are not normalized or bounded by an explicit guard. |
| Rewrite | The second traversal in [`deobfuscate`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/Shuffle-Claude/Shuffle-Claude.js#L169-L193) requires a direct identifier name, reads only arguments 0 and 1, checks array density/literals, and replaces the call. [`valueToNode`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/Shuffle-Claude/Shuffle-Claude.js#L130-L144) reconstructs primitive AST nodes. | The visitor's `return` skips the current unsupported call, not the whole traversal; other call sites can still be rewritten. The source does not test purity or side effects because accepted elements are materialized primitives. |
| Cleanup and emission | The third traversal crawls the parent scope and counts references before removing a recognized declaration at [`deobfuscate`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/Shuffle-Claude/Shuffle-Claude.js#L195-L215). | The parent-scope lookup is intentional because the parameter shadows the function name inside the body. A declaration with a remaining reference is retained. Babel generation uses `retainLines: false` and minimal escaping. |
| CLI adapter | The unguarded command-line wrapper reads an input path, calls `deobfuscate`, and writes or prints output at [`Shuffle-Claude.js#L221-L236`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/Shuffle-Claude/Shuffle-Claude.js#L221-L236). | Missing CLI input exits with an error. The transform entry point itself has no parse-error catch, and the file does not export `deobfuscate` as a library API. |

The implementation is source-local: `isShuffleFunction`, `extractLiteral`, `valueToNode`,
and `evaluateShuffle` are owned helpers for this page; `deobfuscate` is the sample's
coordinator and owns the three-pass ordering and cleanup decision. No delegated helper from
another page is required.

## 4. Upstream Effects

There is no earlier sample-local decoder pass. Babel's [`parser.parse`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/Shuffle-Claude/Shuffle-Claude.js#L150-L152) is the only input substrate: it must accept the source under `sourceType: "script"` before the AST traversals can run. The parser is configured without the broader syntax-plugin list used by the other sample, so syntax outside this parser configuration is an input decline through an uncaught parse error rather than a documented fallback.

The pass does not consume a prior recovered array/order table. Its ordering state is created
at each matched call site from the array's primitive AST elements and the raw numeric count,
then immediately consumed by the replacement. No later sample-local pass is specified; the
cleanup traversal and generator are the remaining stages of this same transform.

## 5. Known Gaps

- The declaration set and call-site match are name-based. A same-spelled identifier in another
  lexical scope or an unrelated call can be treated as a target; cleanup also reasons from
  the recognized name. The source does not use Babel binding identity.
- The accepted array model is intentionally narrow: holes, spread elements, object/array
  expressions, template literals, BigInt, and other non-primitive element nodes decline the
  individual call. A dynamic array or dynamic count is left unchanged without a diagnostic.
- The count gate accepts any Babel `NumericLiteral` but does not explicitly require a finite
  integer or impose a work bound. The evaluator follows the original loop comparison rather
  than a modulo reduction.
- The `undefined` literal case is recognized by identifier spelling, not by checking the
  binding. A script that shadows that spelling is outside the proven safety boundary.
- If no recognized declaration exists, the exact input string is returned; if a declaration
  exists but no call is rewritten, Babel generation may still reformat the source while the
  declaration remains. No output-format preservation guarantee is source-backed.
- The CLI wrapper is unguarded and has no library export. This page documents the
  `deobfuscate` body, not safe importing or host-environment behavior.
- The supplied tests and generated example are not execution evidence here. Runtime
  equivalence, unseen-input transfer, and production decoder coverage remain unresolved.

## Source

All algorithm claims in this page come from the pinned corpus revision
`e90be6ca716e28f4bba91fe39615a665656bd802`:

| Pinned source | Ownership and anchors |
| --- | --- |
| [`Shuffle-Claude/Shuffle-Claude.js`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/Shuffle-Claude/Shuffle-Claude.js) | Owned matcher `isShuffleFunction` at lines 34–97; ordering helper `evaluateShuffle` at 104–108; literal/state helpers `extractLiteral` and `valueToNode` at 114–144; three-pass coordinator `deobfuscate` at 150–215; CLI adapter at 221–236. |

The source is frozen corpus input. The line spans above are implementation anchors, not
execution or qualification evidence.

## Fixtures

| Pinned fixture | Claim it pins | Evidence boundary |
| --- | --- | --- |
| [`Shuffle-Claude/README.md`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/Shuffle-Claude/README.md#L1-L14) | Sample provenance, prompt, and stated AST-deobfuscator intent | Provenance only; not an independent algorithm or runtime result. |
| [`Shuffle-Claude/Shuffle.js`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/Shuffle-Claude/Shuffle.js#L1-L5) | The supplied dense numeric array, push/shift function shape, and intended rotation example | Exact input provenance and intended-check evidence. |
| [`Shuffle-Claude/test_multi.js`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/Shuffle-Claude/test_multi.js#L1-L11) | Two static call-site examples and comments naming intended ordered arrays | Test-intent provenance; comments state expected ordered arrays. |
| [`Shuffle-Claude/test_passthrough.js`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/Shuffle-Claude/test_passthrough.js#L1) | A non-shuffle pass-through input | Intended safe-decline check; no behavioral result is claimed. |
