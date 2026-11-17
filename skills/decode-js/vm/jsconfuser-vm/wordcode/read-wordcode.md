# Read the word stream into instructions

Part of the [`wordcode` module](../wordcode.md). The stage `read-program` calls it through the
[frontend driver](../frontend-driver.md), and every transform that rewrites the words reads its
own output back through it ([map](../../../pipelines/jsconfuser-vm.md#frontend-order)).

## 2. Algorithm

The reader turns the container's words into ordered instructions. It establishes boundaries,
widths and operand roles; it does not check that a register, constant, label or function exists
([validate-references](validate-references.md)).

A word is an unsigned 32-bit integer and a PC indexes words. The first word of an instruction is
its opcode. The opcode's name comes from the container's opcode table
(`roles.op.values`, [container](../source/container.md#the-container-record)), and a call's
argument count is a spread when it equals the container's sentinel
(`roles.sentinels.values.CALL_SPREAD`). Width is decided by the instruction being read, so a
payload word that looks like an opcode is payload.

```text
parseWords(words, names):                       // explanatory pseudocode
  pc = 0; instructions = []
  while pc < words.length:
    opcode = words[pc]; require a u32            else invalid-word
    name = names[opcode], or an added-opcode case the caller supplied
    require one of them                          else unknown-opcode
    require name != PATCH                        else unsupported-hardening-opcode
    read by the row for name; every read is bounded by the stream and checked as a u32
    for a counted row: prove the count fits the remaining words before reading the tail
    instructions += the record; pc = its nextPc
  return instructions                            // nothing is published on a refusal
```

The stream ends exactly where an instruction ends; a suffix is parsed as further instructions.
So an extra word 61 refuses as an unknown opcode, while an appended `DEBUGGER` parses: full
consumption does not prove the code ends where the encoder ended it.

### Operand grammar

Widths below include the opcode word; the encoder's
[instruction table](../../../../js-confuser-vm/instruction-set.md) counts the words after it. `r`
is a register index, `uv` an upvalue index, `t` an absolute word PC, `i` an immediate, and `c, k`
a constant-pool index with its conceal key. Opcode numbers are the canonical ones.

| Opcodes | Words, from the opcode | Width | Operands |
|---|---|---:|---|
| `LOAD_CONST` 0, `LOAD_GLOBAL` 2, `TYPEOF_SAFE` 38 | `op, dst, c, k` | 4 | register; constant `(c, k)` |
| `STORE_GLOBAL` 6 | `op, c, k, src` | 4 | constant `(c, k)`; register |
| `LOAD_INT` 1 | `op, dst, i` | 3 | register; immediate |
| `LOAD_UPVALUE` 3 | `op, dst, uv` | 3 | register; upvalue index |
| `STORE_UPVALUE` 7 | `op, uv, src` | 3 | upvalue index; register |
| `LOAD_THIS` 4 | `op, dst` | 2 | register |
| `MOVE` 5, `FOR_IN_SETUP` 52 | `op, dst, src` | 3 | two registers |
| `GET_PROP` 8, `DELETE_PROP` 10 | `op, dst, obj, key` | 4 | three registers |
| `SET_PROP` 9 | `op, obj, key, value` | 4 | three registers |
| `DEFINE_GETTER` 50, `DEFINE_SETTER` 51 | `op, obj, key, fn` | 4 | three registers |
| `ADD` 11 ... `MOD` 15, `EXP` 60, `BAND` 16 ... `USHR` 21, `LT` 22 ... `INSTANCEOF` 31 | `op, dst, lhs, rhs` | 4 | three registers |
| `UNARY_NEG` 32 ... `VOID` 37 | `op, dst, src` | 3 | two registers |
| `JUMP` 39 | `op, t` | 2 | label |
| `JUMP_IF_FALSE` 40, `JUMP_IF_TRUE` 41 | `op, src, t` | 3 | register; label |
| `RETURN` 45, `THROW` 46, `JUMP_REG` 58 | `op, src` | 2 | register |
| `FOR_IN_NEXT` 53 | `op, dst, iter, exitPc` | 4 | two registers; label |
| `TRY_SETUP` 54 | `op, handlerPc, exceptionReg` | 3 | label; register |
| `FINALLY_SETUP` 59 | `op, finallyPc, contReg, payloadReg, throwPadPc` | 5 | label; two registers; label |
| `TRY_END` 55, `DEBUGGER` 57 | `op` | 1 | none |

Counted rows. `n` and `m` are count words; the sentinel is tested before `n` is read as a count:

| Opcodes | Words | Width | Reading |
|---|---|---:|---|
| `CALL` 42, `NEW` 44 | `op, dst, callee, n, argReg[0..n)` | `4+n` | Fixed arguments, `n` may be 0 |
| `CALL` 42, `NEW` 44 | `op, dst, callee, sentinel, arrayReg` | 5 | Spread: the arguments are one array register |
| `CALL_METHOD` 43 | `op, dst, receiver, callee, n, argReg[0..n)` | `5+n` | Fixed arguments |
| `CALL_METHOD` 43 | `op, dst, receiver, callee, sentinel, arrayReg` | 6 | Spread |
| `MAKE_CLOSURE` 47 | `op, dst, entryPc, params, regs, m, hasRest, (isLocal, index)[0..m)` | `7+2m` | `hasRest` and each `isLocal` are 0 or 1; `isLocal` 1 captures a local register, 0 an enclosing upvalue |
| `BUILD_ARRAY` 48 | `op, dst, n, elementReg[0..n)` | `3+n` | Ordered element registers |
| `BUILD_OBJECT` 49 | `op, dst, m, (keyReg, valueReg)[0..m)` | `3+2m` | Ordered key and value registers |
| `PATCH` 56 | | | Refused before its words are read |

A count is a non-negative safe integer; a single-word tail needs `count <= remaining`, a pair
tail `count <= floor(remaining / 2)`.

### Added-opcode instructions

A recovery transform reads a stream that still holds added opcodes by passing the cases a
[runtime observer](../observe.md) proved from the handlers. Such an opcode is read by its case:

| Case | Instruction name | Reads | Carries |
|---|---|---|---|
| specialized | `SPECIALIZED` | The opcode word only | One step: the original opcode followed by the baked operands |
| macro | `MACRO` | For each step, the operands the step's canonical opcode reads at the cursor | One step per canonical instruction, with its words |
| anti (synthetic), alias | `SYNTHETIC` | `arity` operand words | `canonicalOperands`, the stored operands put in canonical order by `canonicalToStored`; the steps, each a slice of them |

When several case tables hold the opcode, specialized wins over macro, and macro over synthetic.
An alias is a synthetic case with one step spanning all its operands.

### Worked example

A **synthetic** stream, under the canonical table and sentinel 65535:
`[43, 0, 1, 2, 65535, 3, 45, 0]`.

- PC 0 is `CALL_METHOD`: destination r0, receiver r1, callee r2, then 65535, the sentinel, so one
  array register r3 follows. Width 6, next PC 6, `form.kind` `spread`.
- PC 6 is `RETURN` r0, width 2, next PC 8: the end of the stream.

With the fourth operand changed to 2, `CALL_METHOD` reads 3 and 45 as two argument registers and
ends at PC 7. Word 0 at PC 7 is `LOAD_CONST` with no operand left, and the whole stream refuses
with `truncated-instruction`.

## 3. Implementation

### Exports another file imports

| Export | File | Contract | Imported by |
|---|---|---|---|
| `diagnoseWordcode(container)` | `read-wordcode.js` | `{ok, result, diagnostic}`, deeply frozen: the wordcode record or a `wordcode` refusal ([Refusals](../../../pipelines/jsconfuser-vm.md#refusals)); fallback code `word-reader-error`. | the frontend driver, the `normalize-*` transforms, the cell oracle script |
| `readWordcode(container)` | `read-wordcode.js` | The record, or `null`. | the frontend driver, tests |
| `diagnoseAntiWordStream(container, observation)` | `read-wordcode.js` | The stream read with the anti cases (`observation.syntheticCases`); refuses `no-synthetic-instructions` when no `SYNTHETIC` instruction is present. | `normalize-anti-wordcode`, `normalize-specialized-wordcode`, `analyze-anti-register-flow` |
| `diagnoseAliasedWordStream(container, observation, {antiObservation, specializedObservation, macroObservation})` | `read-wordcode.js` | Read with `observation.aliases` and any of the other three; refuses `no-alias-instructions` when no `SYNTHETIC` instruction outside the anti cases is present. | `normalize-aliased-wordcode` |
| `diagnoseMacroWordStream(container, observation, specializedObservation, antiObservation)` | `read-wordcode.js` | Read with `observation.macros`; refuses `no-macro-instructions`. | `normalize-macro-wordcode` |
| `diagnoseSpecializedWordStream(container, observation, antiObservation)` | `read-wordcode.js` | Read with `observation.specialized`; refuses `no-specialized-instructions`. | `normalize-specialized-wordcode` |
| `diagnoseObservedWordcodeInstruction(container, pc, addedOpcodes)` | `read-wordcode.js` | One instruction read at `pc` with the same grammar and the cases in `addedOpcodes` (`anti`, `alias`, `macro`, `specialized`). An alias is renamed `ALIAS` with one full canonical step; its raw words and width stay. It does not show that `pc` is a boundary: the caller proves that. | `analyze-self-modifying-regions` |
| `LABEL_WORD_OFFSETS` | `wordcode-operands.js` | By opcode name, the word offsets (opcode at 0) that hold a code address, derived from the layouts, `MAKE_CLOSURE`'s entry PC included. Every stage that moves code rewrites exactly these words. | [origin-addresses](origin-addresses.md), the `normalize-*` transforms |
| `indexWordcode(wordcode)` | `wordcode-index.js` | `{words, instructions, byPc, boundaries, boundarySet}` over a published record, without parsing it again. | `validate-references.js`, `partition-functions.js` |

The four stream readers publish `{schemaVersion: 'jsconfuser-vm-<kind>-word-stream-observation.v1',
wordCount, instructions}`, `<kind>` one of `anti`, `aliased`, `macro`, `specialized`, with the
fallback code `<kind>-word-stream-error`. They build their case tables from the observations as
given: an observation's own consistency is its observer's proof, and a malformed one is the
stream's refusal.

### Inside the part

| Piece | File | Does |
|---|---|---|
| `FIXED_LAYOUTS`, `FIXED_WORD_WIDTHS`, `fixedOperands` | `wordcode-operands.js` | One layout per fixed-width opcode: operand kinds in word order, a constant two words. Widths and operands are derived from it. |
| `register`, `immediate`, `labelTarget`, `spreadSentinel`, `makeInstruction`, `isWord`, `checkCount`, `checkPairCount`; `decline`, `accepted`, `refused` | `wordcode-operands.js` | Operand constructors, the instruction record, the word and count checks, the `wordcode` refusal. |
| `makeCursor`, `parseInstruction`, `parseWords` | `wordcode-instructions.js` | The bounded cursor, one instruction, the whole stream. |

### Records

```text
wordcode record
  schemaVersion: 'jsconfuser-vm-wordcode.v1'
  encoding:      'numeric-u32'
  words                       // a copy of the container's words
  wordCount, instructionCount
  instructions
  consumedWords, nextPc       // both the word count

instruction
  pc, name
  opcode   { name, value }    // value: the word as found
  operands                    // one object per operand, in word order
  words                       // this instruction's own words
  width, nextPc
```

An operand is `{kind: 'register', index}`, `{kind: 'label-target', pc}`,
`{kind: 'immediate', value}`, `{kind: 'upvalue-index', index}`,
`{kind: 'constant-ref', index, concealKey}`, `{kind: 'spread-sentinel', value}`, or for a closure
capture `{kind: 'local' | 'upvalue', index, isLocal}`. Counted instructions add:

| Instruction | Extra fields |
|---|---|
| `CALL`, `CALL_METHOD`, `NEW` | `form {kind: 'fixed' \| 'spread', argc, sentinel, arrayRegister}`, `arguments` (`{kind: 'fixed', count, registers}` or `{kind: 'spread', sentinel, arrayRegister}`), `callee`, `destination`, `receiver` (null unless `CALL_METHOD`), `serializedArgumentOffset` |
| `MAKE_CLOSURE` | `form {kind: 'closure', ...functionMeta}`, `functionMeta {startPc, paramCount, regCount, captureCount, hasRest}`, `captures`, `capturePairs` (the same list), `destination` |
| `BUILD_ARRAY` | `form {kind: 'array', count, elementRegisters}`, `count`, `destination`, `elementRegisters` |
| `BUILD_OBJECT` | `form {kind: 'object', pairCount, pairs}`, `pairCount`, `destination`, `pairs [{key, value}]` |

Later stages read a call's spread from `form.kind`, never by comparing a word with a constant.
Added-opcode instructions have `pc`, `name`, `opcode`, `words`, `width`, `nextPc` and `steps`
(each with `name` and `words`; a macro or specialized step also `opcode`), a synthetic one also
`canonicalOperands`; they have no `operands`.

### Refusals

Owner `wordcode`. A refusal publishes no partial list; the container and the program are not
changed.

| Code | When |
|---|---|
| `invalid-word` | A word that is not an unsigned 32-bit integer |
| `unknown-opcode` | An opcode word neither the table nor a supplied case names |
| `unsupported-hardening-opcode` | `PATCH` |
| `truncated-instruction` | The stream ends inside an instruction, or a count exceeds the remaining words |
| `invalid-count` | A count that is not a non-negative safe integer |
| `invalid-descriptor` | A `hasRest` that is not 0 or 1 |
| `invalid-capture-pair` | A capture kind that is not 0 or 1 |
| `macro-step-mismatch` | A macro step whose operand words changed between its reading and the cursor's |
| `no-synthetic-instructions`, `no-alias-instructions`, `no-macro-instructions`, `no-specialized-instructions` | A stream reader whose stream holds no instruction of its kind |
| `reader-internal-error` | An instruction that did not consume its declared width |
| `word-reader-error`, `<kind>-word-stream-error` | Any other error |

## 5. Known Gaps

- A parseable suffix passes: the reader cannot tell appended instructions from the program's own.
- `parseWords` ends with a `trailing-word` refusal that its loop cannot reach.
- `PATCH` and the added opcodes are refused by the plain reader; their recovery is the
  [`recover-patch` and `recover-added-opcodes` stages](../../../pipelines/jsconfuser-vm.md#frontend-order).
- No committed test reaches the plain reader's refusals (a truncated, unknown or malformed word)
  directly.

## 6. Source

- [read-wordcode.js](../../../../../decoder/decode-js/src/vm/jsconfuser-vm/wordcode/read-wordcode.js):
  the published record and the stream readers.
- [wordcode-instructions.js](../../../../../decoder/decode-js/src/vm/jsconfuser-vm/wordcode/wordcode-instructions.js):
  the cursor and the rows.
- [wordcode-operands.js](../../../../../decoder/decode-js/src/vm/jsconfuser-vm/wordcode/wordcode-operands.js):
  layouts, operand kinds, label offsets.
- [wordcode-index.js](../../../../../decoder/decode-js/src/vm/jsconfuser-vm/wordcode/wordcode-index.js):
  the index.
- Serialized widths in the pinned encoder:
  [compiler.ts#L56-L159](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/compiler.ts#L56-L159),
  [runtime.ts#L565-L760](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/runtime.ts#L565-L760).

## 7. Fixtures

Suites encode their sources with the pinned encoder and require the decode to behave as the
source ([tests.md](../../../tests.md)).

| Scenario | Expected result | Committed fixture |
|---|---|---|
| Spread calls, method calls and constructions under randomized opcodes | The spread form is recognized by the container's sentinel; dropping the sentinel turns the suite red | [compiled-forms](../../../../../decoder/decode-js/test/vm/jsconfuser-vm/cell-suites/compiled-forms/suite.js) |
| A for-in loop whose exit is a label; an iterator register holding a number | `FOR_IN_NEXT`'s third operand is a label; removing its layout turns both cases red | `for-in-exit-label`, `for-in-iterator-number` in [single-payload-stage-conditions](../../../../../decoder/decode-js/test/vm/jsconfuser-vm/cell-suites/single-payload-stage-conditions/suite.js) |
| Closures capturing an enclosing upvalue, in moved regions | A capture kind 0 is an upvalue; dropping the kind turns the case red | `self-modifying-try-and-closures` in single-payload-stage-conditions |
| Alias opcodes with permuted operands | Operands are restored to canonical order; reading them as stored turns the suite red | [added-opcodes-chain](../../../../../decoder/decode-js/test/vm/jsconfuser-vm/cell-suites/added-opcodes-chain/suite.js) |
| A hand-written container | Read without changing it; the record is deeply frozen | [read-wordcode.test.js](../../../../../decoder/decode-js/test/vm/jsconfuser-vm/single-component/read-wordcode.test.js) |
| A truncated call; an unknown opcode; a non-integer word | `truncated-instruction`, `unknown-opcode`, `invalid-word` | |
