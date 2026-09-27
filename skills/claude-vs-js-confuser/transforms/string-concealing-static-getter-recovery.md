# String Concealing static getter recovery

Evidence label: `source-inspection only`.

This page documents the one solution-level transform implemented by the pinned
`StringConcealing/stringConcealing.js`: resolve a getter's decoder and encoded-array bindings,
decode only constant indexes, replace those call sites with string literals, and sweep the
unreferenced scaffolding to a fixpoint. The basE91 routine is part of the transform's local
constant decoder and is not a general program-execution facility.

## 1. Target

The input is JavaScript source accepted by `parse`, which uses Babel `sourceType: "unambiguous"`
and `allowReturnOutsideFunction: true`. A target getter is a function with exactly one identifier
parameter, exactly one return statement, and a return call whose sole argument is a computed member
`array[param]`. The call callee, the array identifier, and the getter must resolve through Babel
scope bindings to a function containing a literal `table` declaration and an array declarator
whose elements are string literals ([`analyzeGetter`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/StringConcealing/stringConcealing.js#L92-L171)).

The output is generated JavaScript source. A call with a numeric literal index or a unary-minus
numeric literal index becomes a fresh string literal when the selected array element is a string.
After replacement, unreferenced declarations whose identifiers begin with `__` or equal
`utf8ArrayToStr` are removed through repeated reparsing and generation. The file API always returns
generated source after parsing, including when no target call is changed.

## 2. Algorithm

1. **Parse once into a Babel AST.** `parse` accepts an unambiguous program and keeps return-outside-
   function syntax available for the sample. No source program is executed during parsing or any
   subsequent pass ([`parse`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/StringConcealing/stringConcealing.js#L182-L187)).

2. **Define the static decoder inputs.** `constIndex` accepts a `NumericLiteral` directly or a
   unary `-` applied to one. `extractTable` traverses a bound decoder function for the first
   variable declarator named `table` with a string initializer. `extractArray` accepts only a
   variable declarator initialized by an array expression and maps each element to its string value
   or `null` ([`constIndex`, `extractTable`, and `extractArray`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/StringConcealing/stringConcealing.js#L79-L116)).

3. **Analyze a getter by binding identity.** `analyzeGetter` first validates the exact one-parameter,
   one-return, one-call, computed-member shape. It then resolves the decoder and array names from
   the getter's scope, requires a function binding for the decoder, extracts its table, extracts the
   array values, and caches either the `{ table, values }` record or `null` for that function node
   ([`analyzeGetter`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/StringConcealing/stringConcealing.js#L118-L171)).

4. **Replace constant getter calls.** Traverse every call expression. Require an identifier callee,
   exactly one argument, a supported constant index, a bound function callee, a successful getter
   analysis, and a string at the selected array index. Decode that string with `base91Decode(table,
   encoded)`, build a Babel string literal, and replace only the call path. Holes, non-string array
   elements, dynamic indexes, unrelated functions, and non-getter calls remain in the AST
   ([`base91Decode` and replacement traversal](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/StringConcealing/stringConcealing.js#L43-L77) and [`deobfuscate` replacement pass](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/StringConcealing/stringConcealing.js#L209-L235)).

5. **Reparse and sweep dead scaffolding.** Generate the changed-or-unchanged AST once and parse
   that output again so Babel bindings reflect the current tree. `cleanupSweep` visits function
   declarations and variable declarators, and removes an identifier binding only when its name is
   scaffold-shaped and its binding is unreferenced. If a sweep removes anything, generate and
   reparse again; stop at the first stable sweep ([`isScaffoldName`, `cleanupSweep`, and fixpoint](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/StringConcealing/stringConcealing.js#L173-L245)).

6. **Generate and expose the result.** Generate with comments retained and minimal escaping. The
   module exposes a file wrapper, `deobfuscate`, and `base91Decode`; the CLI reads UTF-8 input and
   either writes a requested output file or writes generated source to stdout
   ([`generation`, file wrapper, and CLI](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/StringConcealing/stringConcealing.js#L247-L283)).

The transform's state flow is:

```text
getter call + constant index
  -> getter binding -> decoder table + encoded-array binding
  -> basE91/UTF-8 string value
  -> string-literal replacement
  -> reparse + scaffold cleanup fixpoint
  -> generated source
```

## 3. Implementation

| Phase | Source anchor | Representation and material behavior |
| --- | --- | --- |
| Byte decoder | [`base91Decode`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/StringConcealing/stringConcealing.js#L43-L77) | The source's table-indexed basE91 pairs accumulate bits into bytes and decode the resulting buffer as UTF-8. Invalid characters are skipped; a trailing half-pair contributes one byte. |
| Constant index | [`constIndex`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/StringConcealing/stringConcealing.js#L79-L89) | Direct numeric literals and unary-negative numeric literals become JavaScript numeric indexes; all other expressions return `null`. |
| Table and array extraction | [`extractTable`, `extractArray`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/StringConcealing/stringConcealing.js#L92-L116) | A decoder table is a string initializer in a variable named `table`; the source array must be an array expression, and non-string elements are recorded as `null`. |
| Getter recognition | [`analyzeGetter`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/StringConcealing/stringConcealing.js#L118-L171) | The exact one-parameter return-call shape is joined to decoder and array bindings; results are cached per function node. |
| Scaffold predicate | [`isScaffoldName`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/StringConcealing/stringConcealing.js#L173-L177) | Only `__`-prefixed names and the exact `utf8ArrayToStr` spelling are eligible for dead-binding removal. |
| Replacement | [`deobfuscate` pass 1](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/StringConcealing/stringConcealing.js#L209-L235) | A valid constant call is replaced by a fresh `StringLiteral`; unsupported calls are left in place without a diagnostic. |
| Cleanup fixpoint | [`cleanupSweep` and reparse loop](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/StringConcealing/stringConcealing.js#L189-L245) | Dead scaffold declarations are removed one sweep at a time, with Babel reparsing between sweeps to refresh reference counts. |
| Output boundary | [`generate`, file API, and CLI](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/StringConcealing/stringConcealing.js#L247-L283) | Comments and minimal escaping are retained in generated output; file reads are UTF-8 and CLI errors/IO failures propagate. |

The implementation is a static AST pass with a local byte decoder. It does not call the bound
decoder function, execute a getter, or inspect runtime values.

## 4. Upstream Effects

There is no earlier decoder pass. The parsed AST is the sole upstream representation, and the
getter analysis, call replacement, and cleanup fixpoint all operate on it. The reparse between
cleanup sweeps is an internal dependency: without it, Babel's reference counts would describe the
pre-removal tree.

On the producer side, String Concealing is scheduled at order 17 before Variable Masking,
duplicate-literal removal, Control Flow Flattening, moved declarations, renaming, and minification
([`src/order.ts`](https://github.com/MichaelXF/JS-Confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/order.ts#L16-L36)). Later producer stages can re-spell or rename the helper and array. The `SC-213`
profile disables those later conventional transforms; that configuration does not establish
transfer coverage for this source-only page.

## 5. Known Gaps

- Getter recognition requires the exact one-parameter/one-return/computed-member spelling. Arrow
  functions, additional statements, aliases that do not resolve from the getter scope, noncomputed
  accesses, multiple getter arguments, and alternate decoder wrappers decline.
- The decoder table is found by the identifier spelling `table` inside the resolved function, and
  the string array is accepted only from a variable declarator with an array-expression
  initializer. The source does not validate table length, alphabet uniqueness, decoder semantics,
  or array/data-flow provenance beyond those checks.
- Index evaluation accepts only numeric literal syntax. Negative indexes are passed to JavaScript
  array lookup and normally yield no string; dynamic arithmetic, bindings, calls, and computed
  indexes remain unchanged.
- Any sparse or non-string array element is represented as `null` and declines the individual call.
  The source does not prove that the encoded value is valid basE91 or that UTF-8 decoding matches a
  target host outside Node's `Buffer` behavior.
- Cleanup is name-gated and declaration-level. It may leave non-scaffold residue, does not prove
  side-effect freedom, and removes a declaration whenever Babel reports its binding unreferenced;
  this is not semantic dead-code proof.
- The file API reparses and generates even when no call is changed, so formatting can change on an
  ordinary input. Parse, read, write, and generation failures propagate through the wrapper.
- Exact success, `SC-213` transfer evidence, runtime equivalence, unseen coverage, and production
  support remain separate bounded claims.

## Source

The source of record is the pinned
[`StringConcealing/stringConcealing.js`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/StringConcealing/stringConcealing.js)
at revision `e90be6ca716e28f4bba91fe39615a665656bd802`. The source spans are summarized in the
[String Concealing plugin root](../plugins/string-concealing.md) and the reverse
[source map](../source-map.md).

## Fixtures

| Pinned file | Claim it pins | Evidence boundary |
| --- | --- | --- |
| [`StringConcealing/input.js`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/StringConcealing/input.js) | Shared encoded array, decoder/getter shape, and constant call sites | Source-fixture provenance. |
| [`StringConcealing/output.js`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/StringConcealing/output.js) | Retained deobfuscated output shape | Generated-output provenance only. |
| [`StringConcealing/regular.js`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/StringConcealing/regular.js) and [`regular.out.js`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/StringConcealing/regular.out.js) | Ordinary-input control pair | Intended negative evidence only. |
| [`StringConcealing/sample.obf.js`](https://github.com/MichaelXF/claude-vs-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/StringConcealing/sample.obf.js) and [`sample.deobf.js`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/StringConcealing/sample.deobf.js) | Small retained obfuscated/deobfuscated pair | Provenance only; not rerun. |
| [`StringConcealing/test.js`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/StringConcealing/test.js) | Intended rewrite, cleanup, and behavior checks | Test-intent evidence; no result is claimed. |
