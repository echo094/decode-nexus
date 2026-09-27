# Structural bytecode extraction

Evidence label: source-inspection only. This page is a reconstruction contract for the E1
boundary in the frozen VM-1 corpus. It documents a sample-shaped AST recognizer and intermediate
representation; it is not a generalized VM detector, an executed extraction result, or a safety
claim about the input program.

## 1. Target

Recognize the observed VM-1 construction ingredients and recover the encoded word stream, constant
pool, and frame size without invoking the embedded VM. The exact production output is
`{ words, consts, frameSize }`, which is the sole input representation promised to
[fixed-opcode disassembly](vm-1-fixed-opcode-disassembly.md).

The discriminator is syntactic and deliberately incomplete: a Babel `script` AST must contain a
qualifying long base64-like string literal and a first qualifying `NewExpression` with an array
argument and at least three total arguments. Overall success additionally requires that this
selected constructor contains a numeric argument. The source does not prove that these
observations belong to the same constructor or interpreter.

## 2. Algorithm

1. Parse `src` with `@babel/parser` using `{ sourceType: "script" }`.
2. Traverse the AST. For every `StringLiteral`, if its value has length greater than 800 and
   matches `/^[A-Za-z0-9+/=]+$/`, assign it to `base64`. Because this assignment is repeated,
   the final qualifying literal in traversal order wins; there is no first-match guard.
3. For every `NewExpression`, find its first array argument. If one exists, the expression has at
   least three arguments, and no earlier qualifying expression stored a pool, store that array in
   `constArrayNode`. Independently find the first numeric argument of that same expression and
   store its value as `frameSize` when present. The callee name and relationship to the string are
   not checked.
4. If any of `base64`, `constArrayNode`, or `frameSize` is still null, return `null`. Otherwise
   map the array elements through `evalConstNode` in source order.
5. Decode `base64` with Node `Buffer`, allocate `Math.floor(bytes.length / 4)` 32-bit words, and
   pack byte offsets `4i..4i+3` as little-endian values, applying `>>> 0`. Return the three
   extracted values.

This produces a bounded data record, not a runtime object. It does not inspect the constructor
body, interpreter loop, handler table, or opcode meanings.

## 3. Implementation

### Recognizer state and constant subset

| State or operation | Concrete source behavior | Invariant or failure |
| --- | --- | --- |
| `base64` | Starts `null`; each qualifying string literal overwrites it | The last qualifying literal is selected; any decoy satisfying the predicate can win. |
| `constArrayNode` | Starts `null`; first qualifying `NewExpression` with an array and at least three arguments stores its first array argument | The pool is not data-flow-linked to `base64`; later qualifying constructors are ignored. |
| `frameSize` | Set from the first `NumericLiteral` argument found on the stored constructor candidate | It can be any numeric argument; no semantic position or value range is checked. |
| `evalConstNode(null)` | Returns `undefined` for a null array element | Sparse/empty pool entries become `undefined`. |
| Literal nodes | String, numeric, and boolean literals return `.value`; `NullLiteral` returns `null` | Values are copied without executing expressions. |
| Unary nodes | `void` returns `undefined`; unary `-` and `+` recursively evaluate the argument | Other unary operators fall through to failure. |
| Identifier nodes | `undefined`, `NaN`, and `Infinity` are recognized | Other identifiers are not resolved. |
| Other nodes | Throws `Cannot statically evaluate constant node: <type>` | In production the driver catches this extraction throw and enters its pass-through branch. |

`words` is a `Uint32Array`; byte groups are packed as
`(b0 | b1 << 8 | b2 << 16 | b3 << 24) >>> 0`. A trailing one-to-three bytes is not represented,
because the allocation floors the decoded byte length. `consts` contains JavaScript primitive
values from the accepted subset, not AST nodes.

### Source ownership

| Source span | Ownership | What it owns |
| --- | --- | --- |
| [`vm.js#L94-L125`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-1/vm.js#L94-L125) | owned algorithm | Production parse/traversal, slot selection, pool evaluation call, base64 decoding, and word packing. |
| [`vm.js#L128-L149`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-1/vm.js#L128-L149) | owned algorithm | Complete production constant evaluator and its throw boundary. |
| [`disasm.js#L14-L49`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-1/disasm.js#L14-L49) | delegated diagnostic helper | Standalone extraction duplicate; it uses the same independent observations but is not called by the production driver. |
| [`disasm.js#L52-L71`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-1/disasm.js#L52-L71) | delegated diagnostic helper | Diagnostic constant evaluator, whose identifier support is narrower than production's. |
| [`vm.js#L434-L449`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-1/vm.js#L434-L449) | shared coordinator owned by [fallback](vm-1-fallback-validation.md) | Catches extraction errors and turns null/throw into non-VM pass-through. |

### Output shape

```text
extractVM(source) -> {
  words: Uint32Array,       // little-endian complete 4-byte groups
  consts: JavaScriptValue[],// statically evaluated pool, original order
  frameSize: number
}
```

The record contains no association proof, opcode mapping, function starts, or control-flow graph.

## 4. Upstream Effects

E1 is the first decoder-side boundary, so it has no earlier decoder producer. The input must still
be parseable as a Babel script and must retain the qualifying AST observations until this stage.
The production driver may call E1 on arbitrary source; a parser or evaluator throw is swallowed by
the driver before E2 is attempted.

E2 consumes `words` and `consts` and independently uses its fixed numeric grammar to construct
descriptors. E1 must not be described as producing a runtime handler table or opcode map. The
frame size is carried in the VM record for E3/emitter setup; E2's disassembler itself reads only
the words and constants.

The driver-level output effect belongs to [fallback and validation](vm-1-fallback-validation.md):
when extraction returns null or throws, it attempts an unambiguous parse/generation and returns
the original source only if that fallback also fails.

## 5. Known Gaps

- Recognition is not data-flow based. The selected payload literal, pool array, numeric argument,
  and constructor need not be the components of one VM.
- A later qualifying long string overwrites an earlier one, while only the first qualifying pool
  constructor is retained. Decoy ordering and multiple candidate sites are outside the contract.
- The constructor callee, argument positions, numeric frame-size meaning, and `>800`/base64
  predicate are observations of this sample shape, not an alternate-layout interface.
- The constant evaluator rejects computed expressions, bindings, calls, arrays/objects, and all
  unlisted unary/identifier forms. Its error is caught at the driver boundary, not recovered by
  E1.
- Word packing truncates trailing incomplete bytes and performs no payload-length or checksum
  validation.
- The page does not establish behavior, safety, or transfer for unseen extraction layouts.

## Source

The frozen source commit is
[`e90be6ca716e28f4bba91fe39615a665656bd802`](https://github.com/MichaelXF/claude-vs-js-confuser/tree/e90be6ca716e28f4bba91fe39615a665656bd802).

| File | Pinned source | Role |
| --- | --- | --- |
| `VM-1/vm.js` | [`extractVM`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-1/vm.js#L94-L149) | Production extraction and constant evaluation. |
| `VM-1/disasm.js` | [`extract` and `evalNode`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-1/disasm.js#L14-L71) | Diagnostic duplicate only. |

## Fixtures

No independent regression fixture isolates extraction. The pinned artifacts below provide sample
provenance and map the source shapes to the claims they can support.

| Corpus artifact | Claim it pins | Evidence status |
| --- | --- | --- |
| `VM-1/input.js` | Long payload, static pool, and constructor-shaped input | Source fixture. |
| `VM-1/NOTES.md` | Description of `extractVM` ordering and constructor form | Documentation provenance only. |
| `VM-1/README.md` | AST-based deobfuscator interface and sample context | Documentation provenance only. |
| `VM-1/regular.js` | Non-VM driver input | Negative-control fixture. |
