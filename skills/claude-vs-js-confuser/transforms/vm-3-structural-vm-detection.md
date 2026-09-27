# Structural VM detection and payload extraction

Status: source-inspection only. This page reconstructs the frozen VM-3 implementation at commit
`e90be6ca716e28f4bba91fe39615a665656bd802`; it does not claim runtime validation or support for
another VM layout.

## 1. Target

Recognize the VM/payload by its AST relationship graph rather than generated names, comments, or
numeric opcode values, then extract the static word stream, constant pool, and entry template
without executing input code. The accepted near-neighbor discriminator is the conjunction of the
reader, constant decoder, base64 helper, VM/frame/cell/template roles, dispatch loop, closure
accessor, handler table, and bootstrap shapes. The detector is structural, not a proof that the
payload or every descriptor field is complete.

## 2. Algorithm

`detectVM` progressively fills a descriptor. Later recognizers use earlier fields, so the order is
part of the contract:

1. Find a `FunctionDeclaration` with exactly two statements: an assignment followed by a return
   of a computed member whose object is a non-computed member, whose index is an update of a
   computed member, and whose index expression is `FP + numericOffset`. This records the operand
   reader, bytecode property, stack property, frame-pointer property, and PC offset.
2. Find a function containing the 32-bit Weyl increment `2654435769` and a non-computed
   `.fromCharCode` reference. Inside it, identify a computed access over a non-computed member of
   an identifier as the pool property. Independently find a function containing `atob` as the
   base64 helper.
3. Find a non-empty constructor made only of assignments to `this.<property>`, with an array
   assignment to the discovered stack property. Its parameter positions identify bytecode (third),
   pool (second), and global (fifth); a positive numeric assignment identifies the stack pointer,
   and a `null` assignment identifies the cell store.
4. Find an eight-parameter function that pushes a `void` value. Its local aliases identify the
   stack, register-base, template, frame-size, and frame-end values. Writes of the form
   `stackLocal[baseLocal + offset]` identify PC, caller frame, return destination, `this`,
   template, frame size, frame end, and register-base slots. The handler slot is intentionally
   not written here.
5. Find the cell-closing function from a first local initialized from the VM cell property; find
   the dispatch loop from a nested `try` containing one computed call; and find the prototype
   closure accessor whose first assignment adds a numeric offset to `this.stack[this.fp + ...]`.
   The accessor's offset is the register base, with the frame-push result as fallback.
6. Find the three-statement, one-parameter template constructor (info object, capture array,
   prototype) and the four-assignment, two-parameter cell constructor (array, index, materialized
   flag, value). Record the `WeakMap` variable used to associate callable shells with closures.
7. Collect computed numeric member assignments whose right side is a function expression as the
   opcode-handler map. Fewer than ten handlers declines. A handler that both pushes an object and
   touches an otherwise unused frame offset supplies the handler-stack slot.

The static payload extraction then has its own gates:

1. Select a string literal longer than 64 characters passed to the discovered base64 function.
2. In a call to the discovered loop function, find a `new` VM constructor with a non-empty array
   argument and map its elements through `literalValue` to the pool. Find a `new` template
   constructor with an object argument and collect literal object properties as the entry record.
3. If the blob, pool, or entry is absent, return no payload. Otherwise decode the blob as base64,
   allocate `Uint32Array(bytes.length >> 2)`, and read each word with `readUInt32LE`.

`literalValue` accepts string, number, boolean, `null`, the identifier `undefined`, and recursive
`-`, `void`, or `!` unary forms. Other identifiers become marker objects and other expressions
become `undefined`; no arbitrary expression is evaluated. The `makeDecoder` function used later
for pool entries returns an unkeyed value directly, XOR-decodes keyed numbers, and decrypts keyed
strings as base64-decoded little-endian 16-bit characters using the per-character Weyl update.

## 3. Implementation

| Recognized role | Structural discriminator | Descriptor state used downstream |
| --- | --- | --- |
| Operand reader | Two statements; `BC[STACK[FP + offset]++]` return shape | `readFn`, `bcProp`, `stackProp`, `fpProp`, `pcOff` |
| Pool decoder | Weyl constant plus `fromCharCode` and computed pool access | `strFn`, `poolProp` |
| Base64 helper | Function body references `atob` | `b64Fn` |
| VM constructor | All assignments to `this`; stack initialized by array | `vmCtor`, bytecode/pool/global/stack-pointer/cell properties |
| Frame push | Eight params, pushes `void`, writes stack header slots | `pushFrameFn`, `slots`, template PC property |
| Cell/frame helpers | Cell-store initialization, closure accessor, dispatch-loop try/call | `closeFn`, `cellFn`, `regBaseOff`, `loopFn` |
| Template/cell constructors | Exact assignment counts and field roles | `tplCtor`, `tplInfoProp`, `tplCapsProp`, cell field names |
| Closure map | `new WeakMap()` declarator | `tplMapVar` |
| Numeric handler table | Computed numeric member -> function expression | `handlers`, later canonicalized by page 2 |

The implementation is intentionally permissive in several local recognizers: for example, the
descriptor starts with nullable fields and the final handler-count check is the only explicit
global rejection in `detectVM`. The output contract is therefore a descriptor that downstream
pages must use defensively, not a validated schema.

`extractPayload` returns `{ words, pool, entry }`. `words` are decoded static 32-bit words, not
bytes; `pool` is the literal subset returned by `literalValue`; `entry` carries the template's
literal fields, including the entry PC/register count fields consumed by disassembly. `makeDecoder`
is a delegated static helper for page 2's constant forms and page 4's lifted constant values.

The driver invokes these phases after parsing with `sourceType: "unambiguous"`; a missing result
is converted into a pass-through reason by the fallback page. No helper found in the input is
called, and no `Uint32Array` or pool value is used to execute the protected program.

## 4. Upstream Effects

The only upstream producer is Babel's parsed AST. No earlier decoder pass supplies names,
normalization, or frame knowledge. Page 2 consumes the descriptor's handler functions, helper
bindings, frame offsets, and property names. Page 3 consumes the extracted `words`, `pool`, and
`entry`; page 4 later consumes the pool through `makeDecoder`.

The producer's emitted contract explains why extraction keeps values as role-based fields rather
than generated names: the VM uses a flat word stream, pool, entry metadata, frame headers, and
runtime handler bindings, while optional hardening can rename or randomize those bindings. This
page does not inspect generated output to infer semantics beyond the source-shaped relationships.

Material exits are:

| Condition | Result | Safety meaning |
| --- | --- | --- |
| Reader or string decoder absent | `detectVM` returns `null` | Do not reinterpret ordinary code as a VM. |
| Fewer than ten numeric handlers | `detectVM` returns `null` | Do not build an opcode map from a tiny table. |
| Missing blob, pool, or entry bootstrap | `extractPayload` returns `null` | Do not disassemble an incomplete payload. |
| Unsupported literal expression | `literalValue` returns marker/`undefined` | No code execution or guessed value. |
| Trailing base64 bytes | Word allocation truncates by `bytes.length >> 2` | The source does not add a separate alignment validation. |

The detector does not claim a complete binding graph, payload identity, handler completeness, or
transfer to another VM family. The next page must still preserve an explicit `unknown` spec for
unmatched handlers.

## 5. Known Gaps

- `detectVM` can leave descriptor fields unresolved because its final global check is limited;
  malformed near-neighbors may fail later rather than at recognition.
- The base64 literal search and bootstrap scans do not establish that a selected literal is the
  only or intended payload beyond the source shape they match.
- `literalValue` is a narrow static subset; arbitrary computed pool/entry expressions are not
  evaluated.
- Payload lengths, pool element types, entry field presence, and word target ranges are not
  fully validated here.
- Source inspection alone makes no behavioral, transfer, or production-coverage claim.

## Source

The recognition implementation is [`detectVM`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-3/vm.js#L76-L395). The recursive traversal helper is [`traverseNode`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-3/vm.js#L398-L406). Payload extraction and word construction are [`extractPayload`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-3/vm.js#L412-L456), [`literalValue`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-3/vm.js#L458-L473), and [`makeDecoder`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-3/vm.js#L475-L493). The parse-to-extract gate is in [`deobfuscateSource`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-3/vm.js#L3344-L3356).

## Fixtures

| Fixture | Claim it could pin | Evidence role |
| --- | --- | --- |
| `VM-3/input.js` | Source-shaped VM declarations, bootstrap, pool, payload, and handler table | Source fixture |
| `VM-3/regular.js` | Ordinary source for the no-VM pass-through branch | Negative-control fixture |
| `VM-3/test.js` | Intended deobfuscation, pass-through, syntax, determinism, and behavior checks | Test-intent evidence |
| `VM-3/NOTES.md` | Description of helper roles, frame slots, and static decoding | Documentation provenance |
| `VM-3/debug/extract.js`, `VM-3/debug/vmshape.js` | Extraction and shape inspection aids | Debug-tool provenance |
