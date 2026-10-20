# Extract the target-local container

## 1. Target

Packet A locates the VM payload the program cannot run without: the word stream, the constant
pool and the root function's register count, with this decode's opcode table, which gives the
words their meaning.
Success produces copied, deeply frozen `jsconfuser-vm-container.v1` data; decline produces no
partial record and leaves the supplied source/AST untouched. This is analysis, not emitted
JavaScript or runtime execution.

A locates the payload from the boot, never the interpreter. Runtime-layer options (class
obfuscation, minify, handler table, opcode shuffle) re-spell the interpreter and leave the payload
literal, so A reaches them without recognizing the runtime. The opcode table comes from the
handlers' behaviour ([runtime meaning](runtime-meaning.md)), canonical by default. A names nothing:
every role name is `null`.

The runtime readers find runtime code through the [handler locator](locate-handlers.md), which
enters the interpreter from the same boot skeleton.

Readers need JavaScript arrays, `new` expressions and virtual registers, the [Babel binding
foundation](../../babel.md), and the encoder's [container/word units](../../../js-confuser-vm/container-wordcode.md).
The canonical grammar is [read-wordcode.md](read-wordcode.md); the root register count is checked
against the code E reaches in [build-cfg.md](build-cfg.md#owner-ranges-and-handler-records).

## 2. Algorithm

The encoder boots the root function with one call: the VM instance (constructed from the words,
the pool and the global object) and a `new Closure(descriptor)` whose descriptor holds
`startPc: 0`, `paramCount: 0` and the root register count N. That call is the skeleton. Names,
declarators, the call's receiver form and argument order are spelling.

```text
locate(program):
  boots = []
  for each  new X(... d ...)  where d resolves to a three-property object with values {0, 0, N>0}:
    call = parent of that new; require the new is one of call's arguments
    for each holder in [call's receiver object, ...call's arguments], resolved, that is another new:
      found = reach(holder)              // payload literals the holder's value is built from
      if found has exactly one word stream and one pool: boots += {words, pool, N}
  require boots non-empty                  else missing-role
  require every boot equal (words, pool, N) else ambiguous-role
  table, sentinel = runtime meaning while B walks the words      // runtime-meaning.md
  if the walk reads every instruction: table, sentinel as matched
  else: the canonical table and sentinel
  return Packet A {words unchanged, pool, table, sentinel, slots,
                   root {startPc 0, regCount N}, frame {8, 1}}
```

`reach` follows what the value is built from, never a callee: a stable binding's value, the
arguments of a call or construction, a member's object, both sides of a binary/logical
expression, both arms of a conditional, and the last expression of a sequence (depth 8). It
collects numeric u32 arrays as word streams, a canonical base64 u32 string as an encoded word
stream, and literal arrays containing a string as pools. So the encoded-payload decoder call
`decode("BAAAAA…")` and a constructor that stores its arguments both reach the same literals.

A stable binding is a top-level variable's initializer with no other write, or for a bare
`var name` its only write when that write is a top-level `name = value` statement. Anything
else has no value and stops the walk.

Opcode meaning comes from the handlers: [runtime meaning](runtime-meaning.md) walks the words and
names each instruction's opcode from the handler with that label, overwriting the canonical
default, and gives the spread sentinel; the words keep their values. A never reads an opcode map,
so a randomized map that survives in the source, or none, makes no difference. When the walk
cannot read every instruction (added opcodes, say) or the handlers are not located, A publishes
the canonical table: without randomize, added-opcode values sit above the canonical range and B's
unknown-opcode retries handle them; randomized words that the walk cannot name decline at B.

### Worked example: a class and minify runtime

The runtime-layers `class-minify` fixture (source `f(4)` summing 0..3, classObfuscation and
minify) ends in this boot, abbreviated:

```text
R(new B(S, ["window","TEST_OUTPUT",4,void 0,0,1], [4,1,47,3,39,1,7,0,0,5,2,3,…,45,5]),
  new A(void 0, {k:0, j:7, x:0}), void 0, null)
```

`{k:0, j:7, x:0}` has values {0, 0, 7}: a root descriptor with N = 7. Its `new A(…)` is an
argument of the call `R(…)`, whose other arguments include `new B(S, pool, words)`. Reaching
from `new B` finds one pool (it contains strings) and one u32 word array. The runtime's own
`new A([], {k:la, j:ma, x:ka, c:na})` in MAKE_CLOSURE has four properties and is no descriptor.
No 61-key opcode map exists, B reads the canonical words, and A publishes words, pool and
N = 7. C then derives the root's highest register before the first nested start (r6) and
accepts 7 = 6 + 1.

## 3. Implementation

### Packet A components

| Component | Input -> output | Decision |
|---|---|---|
| Stable value (`stableValue`, `resolve`) | Identifier -> the expression it always holds | Initializer with no write, or the single top-level `name = value` of a bare `var`. |
| Literal value (`literalValue`) | Expression -> constant | String/numeric/boolean/null literals, unbound `undefined`, `void literal`, `!number`, `-number`. |
| Payload reach (`reach`) | Holder expression -> word streams and pools | Rules in item 2; a string that is not canonical base64 u32 is not a payload. |
| Encoded words (`decodeCanonicalBytecodeWords`) | String -> words | Canonical base64 (re-encoding the bytes gives the same string) of a non-empty byte stream whose length is a multiple of 4, read as u32 little-endian; otherwise `encoded-bytecode`, which `reach` treats as no payload. |
| Descriptor (`descriptorCount`) | Object -> N or none | Exactly three noncomputed properties, literal numeric values sorting to 0, 0, N; N a positive safe integer. |
| Boot locator (`locateBoots`) | Program -> boots | Descriptor `new` is a call argument; holders are other `new` expressions among the receiver and arguments. |
| Boot skeleton (`locateBootSkeleton`) | Program -> call, holder, words and pool argument positions | Exactly one boot; exactly one holder argument reaches each payload. The handler locator's entry. |
| Handler meaning (`meaningFromHandlers`) | Program -> A with the matched table and sentinel, or none | [runtime-meaning.md](runtime-meaning.md); none when the runtime is not located or a word cannot be read. |
| Publisher (`locateBootPayload`, `diagnoseContainer`) | Located values -> frozen Packet A | Through the common container builder. |

Packet A's record: `encoding: "numeric-u32"` and `roles`. `pool`/`words` carry copied `values`;
`op` carries this decode's opcode table (`createOpcodeTable`, [opcode-table.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/opcode-table.js)),
which B reads to name each word; `sentinels` and `slots` carry the canonical tables; `scalars` holds `MAIN_START_PC = 0`,
`MAIN_REG_COUNT = N`, `HEADER_SIZE = 8`, `FRAME_START = 1`, `ENCODE_BYTECODE = false` and
`TIMING_CHECKS = false`; `constructors`, `methods` and `roots` keep their keys with
`name: null`. Every `name` is `null`. Subsequent analyses read values only.

| Input | Disposition |
|---|---|
| No `new` with a {0, 0, N} descriptor feeding a call with a payload holder | `missing-role`, "No boot call carries a payload and root descriptor". |
| Boots that disagree on words, pool or N | `ambiguous-role`. |
| Unparsable input, a bare `Program` without its `File`, or an unexpected error | `extractor-error`. |

The atomic unit is one whole location: A reads the supplied tree and copies values, so no AST
mutation or scope repair reaches its caller. A does not check that the words parse (B), that N
covers the root's registers (C), or that the runtime matches the encoder's: hand-made runtime
damage that keeps the payload decodes by the payload.

### Testing and acceptance

| Scenario | Oracle | Criterion | Fixture |
|---|---|---|---|
| A1: runtime layers | Packet A succeeds; public decode behaves as the source. | Payload located without runtime recognition. | `runtime-layers` class-minify, class-minify-table-shuffle and minify-aliased. |
| A2: baseline, renaming, comments, moved declarations | Same record as the reference; recovered output equal. | Spelling never changes the record. | `reference`, `f-literals-order`, extract-container.test.js. |
| A3: sentinel spellings | Map reads and literals yield the same record and output. | Unchanged AST and scope state. | extract-container.test.js sentinel masks. |
| A4: payload damage | Named decline, no partial record. | Missing root scalar, malformed word array, near-miss source. | extract-container.test.js negatives. |
| A5: root count against the words | E declines a reachable root register at or above N (register-range). | See [build-cfg.md](build-cfg.md#owner-ranges-and-handler-records). | None: no encoder writes a short count, and the hand-tampered control was retired. |
| A6: randomized values | The table B reads gives the words their baseline meaning; public decode recovers. | Same canonical instruction names and operands as the baseline, with and without a surviving map, with class and minify; a consistent remapping of every label and word keeps that meaning. | randomized-class.test.js, randomized-minified-class.test.js, `randomized-runtime-exceptions`, `runtime-layers` minify-randomized. |

## 4. Input Shapes

| Input spelling | Producer | Packet A route |
|---|---|---|
| Numeric word array, literal pool, direct boot | Pinned [container builder](../../../js-confuser-vm/container-wordcode.md), encoder | Boot locator. |
| Payload arrays as constructor arguments, renamed/inlined runtime | classObfuscation, minify, handlerTable, shuffleOpcodes, encoder | Boot locator; the runtime is not read. |
| Base64 payload string through a decoder call | encodeBytecode, encoder | `reach` decodes the canonical u32 string. |
| Randomized values, with or without a surviving map | randomizeOpcodes, encoder | Handler meaning; the map is not read. |
| Bare `var` plus `name = value` | Outer moved-declarations pass | Stable value. |

The plugin's [source preparation](normalize-source.md) runs first. B trusts the owned values and
does not repeat A's checks. [Diagnosis](standalone-diagnosis.md#owned-record-boundary) owns
orchestration and replacement of these records when a wordcode normalizer changes the stream.

## 5. Known Gaps

- An outer ObjectExtraction over the runtime is unmeasured against handler meaning.

## Source

[locate-boot-payload.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/locate-boot-payload.js)
implements the boot locator (`locateBootPayload`, `locateBootSkeleton`), decoding an encoded
payload with `decodeCanonicalBytecodeWords`
([materialize-encoded-bytecode.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/materialize-encoded-bytecode.js));
[extract-container.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/extract-container.js)
exports `diagnoseContainer`, `extractContainer` and `extractContainerFromSource`, with
[container-role-helpers.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/container-role-helpers.js).
[Standalone diagnosis](standalone-diagnosis.md) wires A before B. The boot shape is the pinned
[runtime.ts#L956-L976](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/runtime.ts#L956-L976).

## Fixtures

| Committed fixture or test | Claim pinned |
|---|---|
| [runtime-layers](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/runtime-layers/generation.json) | A1: class+minify, class+minify+handlerTable+shuffleOpcodes and minify+aliasedOpcodes (seed 324508639) locate the payload by the boot skeleton and decode to source behaviour. |
| [extract-container.test.js](../../../../decoder/decode-js/test/vm/jsconfuser-vm/extract-container.test.js) | A2-A4: pinned reference values, renaming, debug comments, moved declarations, sentinel masks, payload negatives; a raw Program declines with the AST unchanged. |
| [reference/encoded.js](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/reference/encoded.js) and [f-literals-order](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/raw/f-literals-order/encoded.js) | A2: canonical baseline record; a program-specific root count. |
| [ordinary-near-miss](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/negative/ordinary-near-miss/encoded.js) and [missing-container-role](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/corpus/negative/missing-container-role/encoded.js) | A4: decline without a partial record. |
| [encoded-bytecode-arithmetic](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/encoded-bytecode-arithmetic/encoded.js) | A base64 `encodeBytecode` payload is located and decoded to words. |
| [randomized-runtime-exceptions](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/randomized-runtime-exceptions/encoded.js), [randomized-class.test.js](../../../../decoder/decode-js/test/vm/jsconfuser-vm/randomized-class.test.js) and [randomized-minified-class.test.js](../../../../decoder/decode-js/test/vm/jsconfuser-vm/randomized-minified-class.test.js) | A6: randomized words take their meaning from the handlers, with a surviving map, with class and with class plus minify; consistent remapping keeps it. |
| [minified-class-admission.test.js](../../../../decoder/decode-js/test/vm/jsconfuser-vm/minified-class-admission.test.js) and its [behaviour test](../../../../decoder/decode-js/test/vm/jsconfuser-vm/minified-class-admission.behavior.test.js) | A1: class plus minify fixtures pass A, B and public decode with consistent state; public output qualification bounded by the [finite minified-class qualification](../../tests.md#finite-minified-class-qualification). |
