# The `handlers` module

Module of the jsconfuser-vm decoder ([map](../../pipelines/jsconfuser-vm.md#modules)); code in
[`src/vm/jsconfuser-vm/handlers/`](../../../../decoder/decode-js/src/vm/jsconfuser-vm/handlers/).

## 1. Target

`handlers` reads the interpreter: the code in the input that executes each opcode.

It reads:

- the parsed program, entered from the [boot skeleton](source/container.md);
- the interpreter's constructor, run loop, operand and constant readers, and each opcode's handler
  body.

It provides:

- the handler view: the dispatch, every handler with its label and body, the two payload field
  names, the reader predicates, and a lowering that makes equal operations compare equal on
  clones;
- the opcode table of this decode by behaviour, and the spread sentinel;
- for each handler the encoder added, its class against the canonical handlers: specialized,
  alias, macro or anti;
- the split of a view's handlers into canonical and added.

It never:

- reads the word stream. A handler is named from the interpreter alone, so the module imports
  nothing from `wordcode/`;
- reads a label for meaning. A label is only the value a handler answers to;
- executes target code or changes the supplied tree; comparison works on clones;
- rewrites the program. What an added handler's class implies for the words is the runtime
  observers' and the `normalize-*` transforms' work ([observe](observe.md)).

## 4. Dependencies

| Imports | For |
|---|---|
| `@babel/parser`, `@babel/traverse`, `@babel/types` | Parsing the catalogue templates, traversing and building clones |
| [`source`](source.md): `locateBootSkeleton`; `makeContext`, `topLevelDeclarations`, `isStableDeclaration`, `prototypeMethods`, `propertyName`, `numberValue`; `decline`, `refused`; `createOpcodeTable`, `CANONICAL_OPCODES`; `simpleControlBody`, `isControlBodyKey` | The entry into the interpreter, the node context and declarations, the `container` refusal, the opcode table, the statement view |

The rule is one-way: `handlers/` imports only `source/`. `observe/` and the driver's composing
call import it ([imports chart](../../pipelines/jsconfuser-vm.md#imports)). It does not import
`src/vm/decline.js`; its refusals are the `container` refusals `source` hands it.

## Index

| Sub-doc | Responsibility | Files | Entry points |
|---|---|---|---|
| [`locate-handlers`](handlers/locate-handlers.md) | Finding the dispatch, the readers and each handler; decoy layouts; the lowering; table handlers | `locate-handlers.js`, `handler-table.js`, `handler-calls.js`, `handler-lowering.js`, `normalize-handler-statements.js`, `runtime-callables.js`, `runtime-fragment-pattern.js` | `locateHandlers`, `requireHandlers`, `partitionHandlers` |
| [`identify-handlers`](handlers/identify-handlers.md) | Naming each canonical handler by its effects; classifying the added handlers | `identify-handlers.js`, `handler-meaning.js`, `handler-effects.js`, `handler-matchers.js` | `behaviourTable`, `requireIdentifiedHandlers` |
