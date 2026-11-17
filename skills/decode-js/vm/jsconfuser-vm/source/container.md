# The container: boot skeleton, payload and opcode table

Part of the [`source` module](../source.md). The stage `admit-container` calls it through the
[frontend driver](../frontend-driver.md); the handler locator and the runtime observers call its
skeleton and helpers directly ([map](../../../pipelines/jsconfuser-vm.md#frontend-order)).

## 2. Algorithm

The payload is what the program cannot run without: the word stream, the constant pool and the
root function's register count. The encoder boots the root function with one call whose arguments
include the VM instance, constructed from the words and the pool, and a closure constructed from a
descriptor holding start PC 0, parameter count 0 and the root register count N
([container and wordcode](../../../../js-confuser-vm/container-wordcode.md)). That call is the
**boot skeleton**. It is located by structure; names, declarators, the callee's form and the
argument order are spelling. Class obfuscation, minify, the handler table and the opcode shuffle
re-spell the interpreter and leave the boot's literals in place, so the payload is found without
reading the interpreter.

```text
locateBoots(program):                                  // explanatory pseudocode
  boots = []
  for each  new X(... d ...)  where d resolves to a descriptor:
    call = the parent of that new; require the new to be one of call's arguments
    for each holder in [the object of call's member callee, ...call's arguments],
        resolved, that is another new:
      found = reach(holder)
      if found has exactly one word stream and exactly one pool:
        boots += {words, pool, regCount: N, call, holder}
  return boots

locateBootPayload(program, meaning = none):
  require a Program                                   else missing-role
  boots = locateBoots(program)
  require boots non-empty                             else missing-role
  require every boot equal in words, pool and N       else ambiguous-role
  return container record {
    words, pool, root {startPc 0, regCount N}, frame {headerSize 8, frameStart 1},
    opcodes   = a copy of the canonical table, overlaid by meaning.opcodes,
    sentinels = meaning.sentinels, or the canonical CALL_SPREAD,
    slots     = the canonical frame slots }

locateBootSkeleton(program):
  require exactly one boot                            else missing-role
  require exactly one argument of its holder to reach one word stream and no pool,
      and exactly one to reach one pool and no word stream   else missing-role
  return {call, holder, wordsIndex, poolIndex}
```

**Descriptor.** An object expression with exactly three non-computed properties whose values
resolve to numeric literals that sort to 0, 0, N, with N a positive safe integer. Which key holds
which value is not read.

**Resolve.** An identifier stands for its stable value, repeatedly. A binding is stable when it is
a top-level variable declarator with an initializer and no other write, or a bare `var name` whose
only write is a top-level `name = value` statement. Any other identifier has no value.

**Reach** collects the payload literals a value is built from, to depth 8, and never follows a
callee:

| Node | Followed |
|---|---|
| Identifier | Its stable value, once per binding |
| Array of u32 numeric literals, non-empty | Collected as a word stream |
| Any other non-empty array | Collected as a pool; its elements read as literal values |
| String literal | Collected as a word stream if it decodes as the encoded transport; otherwise nothing |
| Call or `new` | Its arguments |
| Member expression | Its object |
| Binary or logical expression | Both sides |
| Conditional expression | Both arms |
| Sequence expression | Its last expression |

So a constructor that stores its arguments, and a decoder call around an encoded string, both
reach the same literals. Whether an array is a word stream is the whole test between words and
pool: the encoder ends every function by returning `undefined` from the pool, so a pool always
holds a value no word array can hold. A program without a string constant has a pool like any
other.

**Pool values.** A pool element is read as a string, numeric or boolean literal, `null`, an
unbound `undefined`, `void <literal>`, `!<number>` or `-<number>`.

**Encoded transport.** A string is a word stream when it is canonical base64 (decoding and
re-encoding gives the same string), non-empty, and its byte length is a multiple of 4; the bytes
are read as u32 little-endian words.

**Opcode table.** `CANONICAL_OPCODES` is the encoder's unrandomized numbering and is never
changed. Each decode takes its own copy; behaviour matching ([handlers](../handlers.md)) overlays
the values of the build, which the driver passes back in as `meaning`. No opcode map in the source
is read, so a randomized map that survives there, or none, makes no difference. The words are
published as found; the table is what gives them names.

### Worked example

Cell `runtime-rewrites-chain`: source `composition-finally-abrupt-return`, profile
`randomizeOpcodes+shuffleOpcodes+handlerTable+classObfuscation+minify`, seed 251. The encoded
program ends in this boot, abbreviated:

```text
z(new t(B, [9566,1,13628,5,55,1,9,1,0,...,25854,5], null,
        [!0,"window","TEST_OUTPUT",void 0,"push","try-","returned","normal","finally-"]),
  null, void 0, new q(void 0, {m:0, l:8, q:0}));
```

- `{m:0, l:8, q:0}` sorts to 0, 0, 8: a descriptor with N = 8. The interpreter's own
  `new q({}, {m:h, l:k, q:f, r:p})` has four properties and non-literal values, and is none.
- `new q(...)` is an argument of the call `z(...)`. Among that call's other arguments, `new t(...)` is
  the one `new`: the holder.
- Reaching from the holder: `B` resolves to `globalThis` and reaches nothing; the second argument
  is a u32 array, the word stream, in randomized opcode values; `null` reaches nothing; the fourth
  is the pool, read as `true, "window", "TEST_OUTPUT", undefined, ...`.
- One word stream and one pool: one boot. The skeleton is `{call: z(...), holder: new t(...),
  wordsIndex: 1, poolIndex: 3}`, and the record carries the words, the pool and `regCount` 8.

## 3. Implementation

### Exports

| Export | File | Contract | Imported by |
|---|---|---|---|
| `locateBootPayload(ast, meaning = null)` | `locate-boot-payload.js` | The container record, or a `container` refusal. `meaning` is `{opcodes, sentinels}`. | `extract-container.js` (the driver's composing call) |
| `locateBootSkeleton(ast)` | `locate-boot-payload.js` | `{call, holder, wordsIndex, poolIndex}`: nodes of the supplied tree and argument positions in the holder. | `handlers/locate-handlers.js` |
| `CANONICAL_OPCODES` | `opcode-table.js` | The frozen canonical table, 61 names, `LOAD_CONST` 0 to `EXP` 60. | `handlers/identify-handlers.js`, `handlers/handler-meaning.js` |
| `createOpcodeTable()` | `opcode-table.js` | A fresh mutable copy. | `handlers/identify-handlers.js`, `handlers/locate-handlers.js` |
| `decodeCanonicalBytecodeWords(value)` | `materialize-encoded-bytecode.js` | The encoded transport's words, or the refusal `encoded-bytecode`, which `reach` takes as no payload. | inside the module only |
| `minifiedRuntimeContainer(observation)` | `minified-runtime-container.js` | Builds and deep-freezes the record below. Every container is built here, whatever the interpreter's form. | inside the module only |

`container-role-helpers.js` holds what the locators here, the handler locator and the runtime
observers share:

| Export | Contract | Imported by |
|---|---|---|
| `EXPECTED_SENTINELS` | `{CALL_SPREAD: 65535}`, the canonical spread sentinel. | `extract-container.js` |
| `EXPECTED_SLOTS` | The frame slot indexes: `PC` 0, `CALLER` 1, `RET_DST` 2, `THIS` 3, `CLOSURE` 4, `HANDLERS` 5, `FRAME_SIZE` 6, `REG_BASE` 7. | inside the module |
| `decline(code, message)`, `accepted`, `refused` | The refusal owned by `container`, and the records a publisher makes of a result ([Refusals](../../../pipelines/jsconfuser-vm.md#refusals)). | `extract-container.js`, `handlers/` (`decline`, `refused`), the runtime observers |
| `PARSER_OPTIONS` | Script parse, `return` outside a function allowed, no error recovery. | `extract-container.js`, `observe/observe-patch-added-opcodes.js`, tests |
| `runtimeAst(input)` | A source string parsed with `PARSER_OPTIONS`, or a `File` or `Program` taken as given; otherwise `invalid-input`. | the runtime observers |
| `propertyName(node)` | The name of an identifier or string key. | `handlers/` |
| `numberValue(node)` | The value of a finite numeric literal. | `handlers/runtime-callables.js` |
| `isWordArray(node)` | A non-empty array of numeric literals, each a safe integer in 0..0xffffffff. | the cell layout script |
| `makeContext(ast)` | One traversal: the node-to-path map, `bindingFor`, `isReference`, `nodes` and `sameRef`; no Program is `malformed-input`. | `handlers/locate-handlers.js`, the cell layout script |
| `topLevelDeclarations(context)` | Top-level `var` declarators and named function declarations with their bindings. A bare `var` takes its defining write as its value: the single write, a top-level `name = value` statement, with no top-level read before it. A stable `var` holding a function expression is listed as a function. | `handlers/locate-handlers.js` |
| `isStableDeclaration(declaration)` | No write other than the defining one. | `handlers/` |
| `prototypeMethods(context, owner)` | The top-level `owner.prototype.name = function` assignments. | `handlers/locate-handlers.js` |
| `referenceCount(context, binding, root)` | References to a binding inside a subtree. | the cell layout script |

### The container record

```text
schemaVersion: 'jsconfuser-vm-container.v1'
encoding:      'numeric-u32'
roles:
  pool       { name, values }            // literal values, in pool order
  words      { name, values }            // u32 words as found; never renumbered
  op         { name, values }            // this decode's opcode table: name -> value
  sentinels  { name, values: { CALL_SPREAD } }
  slots      { name, values: { PC, CALLER, RET_DST, THIS, CLOSURE, HANDLERS, FRAME_SIZE, REG_BASE } }
  scalars    { MAIN_START_PC: 0, MAIN_REG_COUNT: N, HEADER_SIZE: 8, FRAME_START: 1,
               ENCODE_BYTECODE: false, TIMING_CHECKS: false }      // each { name, value }
  constructors { Upvalue, Closure, VM }
  methods      { upvalue { read, write, close },
                 vm { operand, pushFrame, captureUpvalue, constant, closeUpvalues, run } }
  roots        { globals, vm, decoder, bootMethod }
```

Every `name` is `null`: the container names nothing in the source, and its readers read values
only. The record is copied data, deeply frozen; the supplied tree is not changed. A refusal
publishes no partial record.

### Refusals

| Input | Refusal (owner `container`) |
|---|---|
| No Program | `missing-role`, "Input has no program" |
| No `new` with a descriptor feeding a call that also carries a payload holder | `missing-role`, "No boot call carries a payload and root descriptor" |
| Boots that differ in words, pool or N | `ambiguous-role`, "Boot payload is not unique" |
| For the skeleton: no boot, or more than one | `missing-role`, "Boot call is missing or not unique" |
| For the skeleton: the holder's arguments do not reach the words and the pool one each | `missing-role`, "VM construction payload arguments are not unique" |

Unparsable input and any other error become `extractor-error` in the driver's composing call
([frontend driver](../frontend-driver.md)), not here.

## 5. Known Gaps

- A pool element that is none of the literal forms is carried as an internal marker instead of
  refusing the pool. The pinned encoder emits only the literal forms.
- Two definitions of a bare `var`'s value exist: `topLevelDeclarations` requires that no
  top-level read precede the defining write, and the payload's own resolve does not.
- The payload is taken by structure alone, so interpreter damage that keeps the boot is not seen
  here; the words and register count are checked by [`wordcode`](../wordcode.md).
- No committed case has two boots that disagree, or a holder whose arguments reach the payload
  ambiguously.

## 6. Source

- [locate-boot-payload.js](../../../../../decoder/decode-js/src/vm/jsconfuser-vm/source/locate-boot-payload.js):
  resolve, reach, the descriptor, the boots, the skeleton and the payload.
- [container-role-helpers.js](../../../../../decoder/decode-js/src/vm/jsconfuser-vm/source/container-role-helpers.js):
  the shared helpers.
- [materialize-encoded-bytecode.js](../../../../../decoder/decode-js/src/vm/jsconfuser-vm/source/materialize-encoded-bytecode.js):
  the encoded transport.
- [minified-runtime-container.js](../../../../../decoder/decode-js/src/vm/jsconfuser-vm/source/minified-runtime-container.js):
  the record.
- [opcode-table.js](../../../../../decoder/decode-js/src/vm/jsconfuser-vm/source/opcode-table.js):
  the canonical table.
- The boot's shape in the pinned encoder:
  [runtime.ts#L956-L976](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/runtime.ts#L956-L976).

## 7. Fixtures

Suites encode their sources with the pinned encoder and require the decode to behave as the
source ([tests.md](../../../tests.md)). The unit test is
[extract-container.test.js](../../../../../decoder/decode-js/test/vm/jsconfuser-vm/single-component/extract-container.test.js),
which enters through the driver's composing call.

| Scenario | Expected result | Committed fixture |
|---|---|---|
| Encoded transport over a minified interpreter | The base64 string is reached through the decoder call and read as little-endian words; reading it big-endian turns the suite red | [transport-patch-chain](../../../../../decoder/decode-js/test/vm/jsconfuser-vm/cell-suites/transport-patch-chain/suite.js) |
| Shuffled handlers, handler table, class obfuscation and minify together | The payload is located from the boot; the decode behaves as the source | [runtime-rewrites-chain](../../../../../decoder/decode-js/test/vm/jsconfuser-vm/cell-suites/runtime-rewrites-chain/suite.js) (coverage, no break of its own) |
| A program with no string constant | The pool of numbers and `undefined` is told from the words | `no-string-pool` in [single-payload-stage](../../../../../decoder/decode-js/test/vm/jsconfuser-vm/cell-suites/single-payload-stage/suite.js) |
| Ordinary JavaScript (`var answer = 42;`) | `missing-role`, no record | extract-container.test.js |
| A hand-written boot given as a tree | The record's words are read; the tree is unchanged; the record is deeply frozen | extract-container.test.js |
| Two boots that disagree | `ambiguous-role` | |
| A holder whose arguments reach two word streams | `missing-role` from the skeleton | |
