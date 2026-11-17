# The `source` module

Module of the jsconfuser-vm decoder ([map](../../pipelines/jsconfuser-vm.md#modules)); code in
[`src/vm/jsconfuser-vm/source/`](../../../../decoder/decode-js/src/vm/jsconfuser-vm/source/).

## 1. Target

`source` reads the input program as JavaScript text and tree, before any word is given a meaning.

It reads:

- the source string the plugin was handed;
- the parsed program: its top-level declarations, the boot call, and the literals the boot's
  arguments are built from.

It provides:

- the normalized source the standalone decode parses, and the statement view that lets a reader
  treat a braced and an unbraced simple body alike;
- the boot skeleton (the boot call, the VM construction and the positions of its words and pool
  arguments), which is where the handler locator enters the interpreter;
- the container record `jsconfuser-vm-container.v1`: the words, the pool, the root register count
  and the opcode table of this decode;
- the canonical opcode table and a per-decode copy of it;
- the top-level declaration index, the node context and the `container` refusal that the handler
  locator and the runtime observers share.

It never:

- recognizes the interpreter. The payload is found from the boot call alone; the interpreter's
  code is read by [`handlers`](handlers.md) and [`observe`](observe.md);
- decides what an opcode value means. It carries a table; behaviour matching in
  [`handlers`](handlers.md) supplies the values of a build;
- checks that the words parse or that the register count covers the root
  ([`wordcode`](wordcode.md));
- executes target code, changes a tree a caller supplied, or publishes a partial record.

## 4. Dependencies

| Imports | For |
|---|---|
| `@babel/parser`, `@babel/traverse`, `@babel/generator`, `@babel/types` | Parsing, the node context, regenerating normalized source |
| [`uncompute-member`](../../visitors/atomic/uncompute-member.md), [`uncompute-property-key`](../../visitors/atomic/uncompute-property-key.md) (`src/visitor/atomic/`) | The two shared key rewrites the input normalization composes, imported unchanged |
| `src/vm/decline.js` (`declines`, `deepFreeze`) | The refusal protocol ([Refusals](../../pipelines/jsconfuser-vm.md#refusals)) and record freezing |

The rule is one-way: `source/` imports nothing else from `src/vm/`. `handlers/`, `observe/` and
the drivers import it ([imports chart](../../pipelines/jsconfuser-vm.md#imports)). The call that
composes the boot payload with handler meaning is therefore outside the module, in the
[frontend driver](frontend-driver.md).

## Index

| Sub-doc | Responsibility | Files | Entry points |
|---|---|---|---|
| [`normalize-source`](source/normalize-source.md) | The input normalization (stage `prepare-source`) and the statement view | `normalize-source.js` | `normalizeVmInput`; `simpleControlBody`, `isControlBodyKey` |
| [`container`](source/container.md) | The boot skeleton, the boot payload, the encoded transport, the container record, the opcode table, and the shared role helpers | `locate-boot-payload.js`, `container-role-helpers.js`, `materialize-encoded-bytecode.js`, `minified-runtime-container.js`, `opcode-table.js` | `locateBootPayload`, `locateBootSkeleton`; `createOpcodeTable`, `CANONICAL_OPCODES`; `runtimeAst` |
