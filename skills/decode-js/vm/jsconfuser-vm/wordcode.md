# The `wordcode` module

Module of the jsconfuser-vm decoder ([map](../../pipelines/jsconfuser-vm.md#modules)); code in
[`src/vm/jsconfuser-vm/wordcode/`](../../../../decoder/decode-js/src/vm/jsconfuser-vm/wordcode/).

## 1. Target

`wordcode` reads the word stream: the program the interpreter runs.

It reads:

- the [container record](source/container.md#the-container-record): the words, the pool, the
  opcode table, the spread sentinel and the frame scalars;
- its own records, each stage reading the one before;
- the added-opcode cases a [runtime observer](observe.md) proved, when a caller supplies them.

It provides:

- the wordcode record: the stream as ordered instructions with typed operands;
- the references record: pool, label and capture references checked against the whole stream,
  and the frame arithmetic;
- the functions record: each instruction's function, closure sites and parents, labels by owner,
  and shared-parent suspects;
- the stream read with added-opcode cases, one instruction read at a given PC, and the expansion
  of added opcodes into canonical words;
- the address rules every code-moving stage shares: which words hold an address, PC maps and
  their composition, continuation loads.

It never:

- reads the interpreter or the source text; it imports nothing from `source/`, `handlers/` or
  `observe/` and receives the container as data;
- gives an opcode value its name: the container's table does;
- decides control flow, reachability or what a register holds (the
  [model](../switch/vm-switch-boundary.md));
- repairs a stream. A record is published whole or refused, and no input is changed; rewriting
  the words is the `normalize-*` transforms' work.

## 4. Dependencies

| Imports | For |
|---|---|
| `src/vm/decline.js` (`declines`, `deepFreeze`) | The refusals owned by `wordcode`, `references`, `partition` and `observed-expansion` ([Refusals](../../pipelines/jsconfuser-vm.md#refusals)); record freezing |

The rule is one-way: `wordcode/` imports no other module and no Babel package. The frontend
driver and the `normalize-*` transforms import it
([imports chart](../../pipelines/jsconfuser-vm.md#imports)). Inside the module the records build
on each other in one direction: instructions, then references, then functions; the address rules
read only the operand layouts.

## Index

| Sub-doc | Responsibility | Files | Entry points |
|---|---|---|---|
| [`read-wordcode`](wordcode/read-wordcode.md) | The instruction grammar; the wordcode record; streams with added opcodes | `read-wordcode.js`, `wordcode-instructions.js`, `wordcode-operands.js`, `wordcode-index.js` | `readWordcode`, `diagnoseWordcode`; `diagnoseAliasedWordStream`, `diagnoseMacroWordStream`, `diagnoseSpecializedWordStream`, `diagnoseAntiWordStream`; `LABEL_WORD_OFFSETS` |
| [`validate-references`](wordcode/validate-references.md) | Pool, label and capture references; the frame; the references record | `validate-references.js` | `validateReferences`, `diagnoseReferences` |
| [`partition-functions`](wordcode/partition-functions.md) | Function intervals, owners, closure parents, suspects; the functions record | `partition-functions.js` | `diagnoseFunctionPartition`, `functionIndexAt` |
| [`origin-addresses`](wordcode/origin-addresses.md) | Addresses across code-moving stages; added-opcode expansion | `expand-observed-word-stream.js`, `finally-continuations.js` | `expandObservedWordStream`, `composePcMaps`, `selectContinuationLoads` |
