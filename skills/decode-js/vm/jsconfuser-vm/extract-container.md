# Extract the target-local container

Pipeline stage: `admit-container` ([map](../../pipelines/jsconfuser-vm.md)).

## 1. Target

`extract-container` locates the VM payload the program cannot run without: the word stream, the
constant pool and the root function's register count, with this decode's opcode table, which gives
the words their meaning. Success produces copied, deeply frozen `jsconfuser-vm-container.v1` data;
decline produces no partial record and leaves the supplied source/AST untouched. This is analysis,
not emitted JavaScript or runtime execution.

A locates the payload from the boot, never the interpreter. Runtime-layer options (class
obfuscation, minify, handler table, opcode shuffle) re-spell the interpreter and leave the payload
literal, so `extract-container` reaches them without recognizing the runtime. The opcode table comes
from the handlers' behaviour ([runtime meaning](runtime-meaning.md)), canonical by default. A names
nothing: every role name is `null`.

The runtime readers find runtime code through the [handler locator](locate-handlers.md), which
enters the interpreter from the same boot skeleton.

Readers need JavaScript arrays, `new` expressions and virtual registers, the
[Babel binding foundation](../../babel.md), and the encoder's
[container/word units](../../../js-confuser-vm/container-wordcode.md). The canonical grammar is
[read-wordcode.md](read-wordcode.md); the root register count is the encoder's own, read and not
checked against the words ([a correct model](../switch/vm-switch-boundary.md#a-correct-model)).

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
  return container record {words unchanged, pool, table, sentinel, slots,
                   root {startPc 0, regCount N}, frame {8, 1}}
```

`reach` follows what the value is built from, never a callee: a stable binding's value, the
arguments of a call or construction, a member's object, both sides of a binary/logical
expression, both arms of a conditional, and the last expression of a sequence (depth 8). It
collects numeric u32 arrays as word streams, a canonical base64 u32 string as an encoded word
stream, and any other non-empty array as a pool: a class runtime's holder also reaches `[]`. So the encoded-payload decoder call
`decode("BAAAAA…")` and a constructor that stores its arguments both reach the same literals.
Word stream or not is the whole test: the encoder ends every function with `return undefined` from
the pool, so a pool always holds a value no word array can hold, and a program without a string
constant has a pool like any other: `var a = 1;` gives `[1, undefined]`.

A stable binding is a top-level variable's initializer with no other write, or for a bare
`var name` its only write when that write is a top-level `name = value` statement. Anything
else has no value and stops the walk.

Opcode meaning comes from the handlers: [runtime meaning](runtime-meaning.md) walks the words and
names each instruction's opcode from the handler with that label, overwriting the canonical default,
and gives the spread sentinel; the words keep their values. A never reads an opcode map, so a
randomized map that survives in the source, or none, makes no difference. When the walk cannot read
every instruction (added opcodes, say) or the handlers are not located, `extract-container`
publishes the canonical table: without randomize, added-opcode values sit above the canonical range
and `read-wordcode`'s unknown-opcode retries handle them; randomized words that the walk cannot name
decline at `read-wordcode`.

### Worked example: a class and minify runtime

The `loop-sum` source (`f(4)` summing 0..3) under classObfuscation and minify, seed 324508639,
ends in this boot, abbreviated:

```text
R(new B(S, ["window","TEST_OUTPUT",4,void 0,0,1], [4,1,47,3,39,1,7,0,0,5,2,3,…,45,5]),
  new A(void 0, {k:0, j:7, x:0}), void 0, null)
```

`{k:0, j:7, x:0}` has values {0, 0, 7}: a root descriptor with N = 7. Its `new A(…)` is an argument
of the call `R(…)`, whose other arguments include `new B(S, pool, words)`. Reaching from `new B`
finds one pool (`void 0` is no word) and one u32 word array. The runtime's own
`new A([], {k:la, j:ma, x:ka, c:na})` in MAKE_CLOSURE has four properties and is no descriptor. No
61-key opcode map exists, `read-wordcode` reads the canonical words, and `extract-container`
publishes words, pool and N = 7. `validate-references` then derives the root's highest register
before the first nested start (r6) and accepts 7 = 6 + 1.

## 3. Implementation

### `extract-container` components

| Component | Input -> output | Decision |
|---|---|---|
| Stable value (`stableValue`, `resolve`) | Identifier -> the expression it always holds | Initializer with no write, or the single top-level `name = value` of a bare `var`. |
| Literal value (`literalValue`) | Expression -> constant | String/numeric/boolean/null literals, unbound `undefined`, `void literal`, `!number`, `-number`. |
| Payload reach (`reach`) | Holder expression -> word streams and pools | Rules in item 2; a string that is not canonical base64 u32 is not a payload. |
| Encoded words (`decodeCanonicalBytecodeWords`) | String -> words | Canonical base64 (re-encoding the bytes gives the same string) of a non-empty byte stream whose length is a multiple of 4, read as u32 little-endian; otherwise `encoded-bytecode`, which `reach` treats as no payload. |
| Descriptor (`descriptorCount`) | Object -> N or none | Exactly three noncomputed properties, literal numeric values sorting to 0, 0, N; N a positive safe integer. |
| Boot locator (`locateBoots`) | Program -> boots | Descriptor `new` is a call argument; holders are other `new` expressions among the receiver and arguments. |
| Boot skeleton (`locateBootSkeleton`) | Program -> call, holder, words and pool argument positions | Exactly one boot; exactly one holder argument reaches each payload. The handler locator's entry. |
| Handler meaning (`meaningFromHandlers`) | Program -> `extract-container` with the matched table and sentinel, or none | [runtime-meaning.md](runtime-meaning.md); none when the runtime is not located or a word cannot be read. |
| Publisher (`locateBootPayload`, `diagnoseContainer`) | Located values -> frozen `extract-container` | Through the common container builder. |

[container-role-helpers.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/container-role-helpers.js)
holds what the container, boot and handler locators and the runtime observers share:

| Helper | Contract | Read by |
|---|---|---|
| `EXPECTED_SENTINELS`, `EXPECTED_SLOTS` | The canonical `CALL_SPREAD` sentinel and frame slot indexes the record publishes. | extract-container, locate-boot-payload |
| `PARSER_OPTIONS` | Script parse, `return` outside a function allowed, no error recovery. | extract-container, the runtime observers |
| `ContainerDecline`, `decline(code, message)` | The named refusal every locator throws; publishers turn it into a diagnostic. | the locators and runtime observers |
| `deepFreeze` | Freezes a published record and everything in it. | the publishers |
| `propertyName`, `numberValue`, `isWordArray` | Identifier or string key name; finite numeric literal; non-empty array of u32 literals. | locate-handlers, locate-boot-payload |
| `makeContext(ast)` | One traversal: node -> path map, binding lookup and reference test over the Program. | locate-handlers |
| `topLevelDeclarations`, `isStableDeclaration` | Top-level `var` and function declarations with their bindings; a bare `var` takes its single top-level `name = value` write, made before any top-level read, as its value, and a stable var holding a function expression counts as a function. Stable: no write other than that defining one. | locate-handlers |
| `prototypeMethods(context, owner)` | The `owner.prototype.name = function` assignments at top level. | locate-handlers |
| `referenceCount(context, binding, root)` | References to a binding inside a subtree. | the qualification layout script |

`extract-container`'s record: `encoding: "numeric-u32"` and `roles`. `pool`/`words` carry copied
`values`; `op` carries this decode's opcode table (`createOpcodeTable`,
[opcode-table.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/opcode-table.js)), which
`read-wordcode` reads to name each word; `sentinels` and `slots` carry the canonical tables;
`scalars` holds `MAIN_START_PC = 0`, `MAIN_REG_COUNT = N`, `HEADER_SIZE = 8`, `FRAME_START = 1`,
`ENCODE_BYTECODE = false` and `TIMING_CHECKS = false`; `constructors`, `methods` and `roots` keep
their keys with `name: null`. Every `name` is `null`. Subsequent analyses read values only.

| Input | Disposition |
|---|---|
| No `new` with a {0, 0, N} descriptor feeding a call with a payload holder | `missing-role`, "No boot call carries a payload and root descriptor". |
| Boots that disagree on words, pool or N | `ambiguous-role`. |
| Unparsable input, a bare `Program` without its `File`, or an unexpected error | `extractor-error`. |

The atomic unit is one whole location: A reads the supplied tree and copies values, so no AST
mutation or scope repair reaches its caller. `extract-container` does not check that the words parse
(`read-wordcode`), that N covers the root's registers (`validate-references`), or that the runtime
matches the encoder's: hand-made runtime damage that keeps the payload decodes by the payload.

### Testing and acceptance

| Scenario | Oracle | Criterion | Fixture |
|---|---|---|---|
| S1: runtime layers | `extract-container` succeeds; public decode behaves as the source. | Payload located without runtime recognition. | `runtime-rewrites-chain`, `interpreter-rewrite-fixed`, `minify-over-aliased-opcodes`. |
| S2: baseline, renaming, comments, moved declarations | Same record as the reference; recovered output equal. | Spelling never changes the record. | `transport-patch-chain` and every cell. |
| S3: sentinel spellings | Map reads and literals yield the same record and output. | Unchanged AST and scope state. | No committed case. |
| S4: payload damage | Named decline, no partial record. | Missing root scalar, malformed word array, near-miss source. | No committed case; the unit test declines ordinary and malformed input. |
| S5: no string constant | Public decode behaves as the source, by the value it throws. | The pool is located without a string in it. | `no-string-pool` in `single-payload-stage`. |
| S6: randomized values | The table `read-wordcode` reads gives the words their baseline meaning; public decode recovers. | Same canonical instruction names and operands as the baseline, with and without a surviving map, with class and minify; a consistent remapping of every label and word keeps that meaning. | `interpreter-rewrite-seeded` and every cell (randomized by default). |

## 4. Input Shapes

| Input spelling | Producer | `extract-container` route |
|---|---|---|
| Numeric word array, literal pool, direct boot | Pinned [container builder](../../../js-confuser-vm/container-wordcode.md), encoder | Boot locator. |
| Payload arrays as constructor arguments, renamed/inlined runtime | classObfuscation, minify, handlerTable, shuffleOpcodes, encoder | Boot locator; the runtime is not read. |
| Pool of numbers, booleans, null and undefined | A program with no string constant, encoder | Boot locator; every pool holds `undefined`, so the word test tells it from the words. |
| Base64 payload string through a decoder call | encodeBytecode, encoder | `reach` decodes the canonical u32 string. |
| Randomized values, with or without a surviving map | randomizeOpcodes, encoder | Handler meaning; the map is not read. |
| Bare `var` plus `name = value` | Outer moved-declarations pass | Stable value. |

The plugin's [source preparation](normalize-source.md) runs first. `read-wordcode` trusts the owned
values and does not repeat `extract-container`'s checks.
[Diagnosis](standalone-diagnosis.md#owned-record-boundary) owns orchestration and replacement of
these records when a wordcode normalizer changes the stream.

## 5. Known Gaps

- An outer ObjectExtraction over the runtime is unmeasured against handler meaning.

## Source

[locate-boot-payload.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/locate-boot-payload.js)
implements the boot locator (`locateBootPayload`, `locateBootSkeleton`), decoding an encoded payload
with `decodeCanonicalBytecodeWords`
([materialize-encoded-bytecode.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/materialize-encoded-bytecode.js))
and publishing the located boot through `minifiedRuntimeContainer`
([minified-runtime-container.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/minified-runtime-container.js)):
a `jsconfuser-vm-container.v1` record of its words, pool and handler-named opcodes, every role
name null and `ENCODE_BYTECODE`/`TIMING_CHECKS` false;
[extract-container.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/extract-container.js)
exports `diagnoseContainer`, `extractContainer` and `extractContainerFromSource`, with
[container-role-helpers.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/container-role-helpers.js).
[Standalone diagnosis](standalone-diagnosis.md) wires `extract-container` before `read-wordcode`.
The boot shape is the pinned
[runtime.ts#L956-L976](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/runtime.ts#L956-L976).

## Fixtures

Each suite encodes its sources with the pinned encoder and requires the decode to behave as the
source ([tests.md](../../tests.md#suites)); a Proved line names the code whose break turns the case
red.

| Suite, test or fixture | Claims | Proved |
|---|---|---|
| [runtime-rewrites-chain](../../../../decoder/decode-js/test/vm/jsconfuser-vm/generated-cells/runtime-rewrites-chain/suite.js) | S1: the payload is located without runtime recognition under shuffled, table, class and minified runtimes | The payload is the boot call's single word stream and pool |
| [interpreter-rewrite-fixed](../../../../decoder/decode-js/test/vm/jsconfuser-vm/generated-cells/interpreter-rewrite-fixed/suite.js) | S1: one interpreter rewrite at a time (minify, handler table, timing, encoded bytecode); the decode equals the plain decode | No break of its own |
| [minify-over-aliased-opcodes](../../../../decoder/decode-js/test/vm/jsconfuser-vm/generated-cells/minify-over-aliased-opcodes/suite.js) | S1: minify over aliased cases | No break of its own |
| [transport-patch-chain](../../../../decoder/decode-js/test/vm/jsconfuser-vm/generated-cells/transport-patch-chain/suite.js) | S2: the payload is reached by structure through bindings minify renamed | The payload is reached by structure through renamed bindings |
| [interpreter-rewrite-seeded](../../../../decoder/decode-js/test/vm/jsconfuser-vm/generated-cells/interpreter-rewrite-seeded/suite.js) | S6: randomized and shuffled words take their meaning from the handlers, with and without class | The opcode table is the one matched from the runtime |
| [single-payload-stage](../../../../decoder/decode-js/test/vm/jsconfuser-vm/generated-cells/single-payload-stage/suite.js), `no-string-pool` in `conceal-constants` | S5: a program with no string constant is located and decoded | No break of its own |
| [extract-container.test.js](../../../../decoder/decode-js/test/vm/jsconfuser-vm/single-component/extract-container.test.js) (unit) | A2-A4 on a hand-written boot: ordinary JavaScript declines first, malformed input gets a stable diagnostic, the AST is unchanged and the record deeply frozen | Not a suite |
| [encoded-bytecode-arithmetic](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/encoded-bytecode-arithmetic/encoded.js) | A base64 `encodeBytecode` payload is located and decoded to words. | Not a suite: a committed fixture |

S3 and S4 have no committed case: the old sentinel and payload-damage controls edited input by
hand. Every cell runs under randomized opcodes (S6).
