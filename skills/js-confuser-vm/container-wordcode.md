# Container and wordcode

## 1. Target

The encoder ships program data together with the runtime that interprets it. This specification
defines how symbolic operands become words, how those words connect to constants and functions,
and how container bindings create runtime frames. The observable result is executable JavaScript
with the virtual program's behavior, subject to the supported lowering forms and selected options.
It describes the pinned `0.1.5` source; it is a source-derived foundation, not a claim of exhaustive
runtime or option-stack verification.

Read the [package prerequisites and workflow](js-confuser-vm.md#prerequisites-and-scope) first.
The plain reference vector disables optional representation changes. Both raw-word and encoded
transport, and randomized maps/layouts, are emitted alternatives described below. Complete
instruction semantics depend on [instruction-set.md](instruction-set.md); optional mechanisms
depend on the detailed recipes linked by [options.md](options.md). Item 5 names remaining
lowering and evidence boundaries.

## 2. Algorithm

Lowering gives each function an instruction list with symbolic register, label and constant
operands. This avoids choosing physical register slots or branch addresses before transforms have
finished adding work. Finalization first expands constants into pairs, then allocates registers,
measures label PCs, and interns constants. Serialization removes bookkeeping records and emits
the numeric sequence, plus the metadata and runtime that interpret it. Program values live in
registers or the heterogeneous constant pool; word operands usually identify those values rather
than contain them.

A **word PC** is an absolute index into the flat word stream. It is neither an instruction number
nor a byte offset. A **register index** is relative to one function's frame register area. A
**pool index** selects one entry of `CONSTANTS`. These three integers may have the same numerical
value while referring to different things. Encoded transport turns each word into four bytes;
boot restores words before interpreting PCs.

### Worked example

This is a **synthetic assembly example** of the meaning of the script
`if (flag) return "ok"; return "no";`. It uses canonical handlers and the plain layout, but omits
the compiler's hidden `this` prologue, reserved locals and implicit trailing undefined return.
It is not asserted to be the exact output of compiling that script. There are no nested functions,
captures, exceptions, hardening or host side effects. Its result oracle concerns `VM.run`; the
normal generated boot ignores that result.

Start with three temporary virtual registers `t0`, `t1`, `t2` belonging to one function. Their
real-operand live ranges are disjoint: `t0` is consumed by the conditional before `t1` starts,
and `t1` is consumed by its return before `t2` starts. Register allocation maps all three to
relative slot `r0`, so `regCount = 1`. Constant expansion changes `constant("flag")` into two
placeholders for its index and key before label measurement. Interning in first-use order gives
`CONSTANTS = ["flag", "ok", "no"]`; all keys are zero. The label `no` denotes PC 13.

| Symbolic step | PC | Final words | Meaning and next PC |
|---|---:|---|---|
| `LOAD_GLOBAL t0, constant("flag")` | 0 | `[2, 0, 0, 0]` | Read host `flag`, using pool entry 0/key 0, into r0; next 4. |
| `JUMP_IF_FALSE t0, label(no)` | 4 | `[40, 0, 13]` | If r0 is false-like, jump to 13; otherwise next 7. |
| `LOAD_CONST t1, constant("ok")` | 7 | `[0, 0, 1, 0]` | Pool entry 1/key 0 into r0; next 11. |
| `RETURN t1` | 11 | `[45, 0]` | Return r0 through the frame/result contract. |
| `defineLabel(no)` | 13 | no words | Bookkeeping position only. |
| `LOAD_CONST t2, constant("no")` | 13 | `[0, 0, 2, 0]` | Pool entry 2/key 0 into r0; next 17. |
| `RETURN t2` | 17 | `[45, 0]` | Return r0. |

The corresponding emitted-data subset is:

```text
CONSTANTS = ["flag", "ok", "no"]
BYTECODE = [2,0,0,0, 40,0,13, 0,0,1,0, 45,0, 0,0,2,0, 45,0]
MAIN_START_PC = 0; MAIN_REG_COUNT = 1; ENCODE_BYTECODE = false
HEADER_SIZE = 8; FRAME_START = 1
SLOTS = { PC:0, CALLER:1, RET_DST:2, THIS:3,
          CLOSURE:4, HANDLERS:5, FRAME_SIZE:6, REG_BASE:7 }
```

This subset needs the matching opcode map, sentinel and interpreter to be a container. Its
instruction widths total `4 + 3 + 4 + 2 + 4 + 2 = 19` words, or `76` transport bytes if encoded.
The false target is `4 + 3 + 4 + 2 = 13` words from the start, not 13 instructions or 13 bytes.
On root push, `fp = 1`, `REG_BASE = 1 + 8 = 9`, `FRAME_SIZE = 8 + 1 = 9`, and the next free
slot is `10`. The register r0 lives at `_regs[9]`, while this frame's PC lives at `_regs[1]`.
With `globals.flag = true`, fetch PCs are `0,4,7,11` and the result cell becomes `"ok"`; with
false, they are `0,4,13,17` and it becomes `"no"`. Normal return closes captures, clears slots
`[1,10)`, resets the frame base to zero and writes `_regs[0]`.

For a separate transport arithmetic example, word `0x12345678` becomes bytes
`[0x78,0x56,0x34,0x12]`. The runtime reconstructs the same unsigned word; this value is not an
opcode in the synthetic program. It shows why a u16 comment cannot define word width.

## 3. Implementation

### Component boundaries

| Component | Consumes -> produces | Consumer invariant |
|---|---|---|
| Lowering and function inventory | Babel statement list -> function descriptors and symbolic instructions | Every virtual register identifies `(fnId,id)`; descriptors carry entry labels; captures identify local registers or parent upvalues. |
| Constant-pair expansion | Symbolic constant operands -> adjacent index/key placeholders | Later width measurement sees both eventual words. |
| Register assignment | Register uses and reserved-leading-local metadata -> resolved relative slots and `regCount` | Captured/local storage is stable; temporary reuse occurs only after a previous lifetime ends. |
| Label assignment | Instruction widths and label definitions -> resolved word addresses/start PCs | Labels are measured in the same filtered widths serialization uses. |
| Constant interning | Constant placeholders/options -> pool and resolved index/key pairs | Repeated values share the first interned entry and its key. Width no longer changes. |
| Serializer and transport | Final operands, maps and layout -> JavaScript declarations and runtime text | Emitted numeric operands have resolved values; raw data are words; encoded data preserve four bytes per word. |
| Runtime builder | Assembled runtime text and handler metadata -> generated JavaScript | Runtime handlers/maps match the chosen word representation. |
| Boot/frame execution | Word stream, pool, host globals and root closure -> program effects/result | Frame metadata determines operand PC and register addresses; captures survive frame release. |

This is a dependency plan, not a source-file layout. Optional passes occupy the positions in the
[workflow](js-confuser-vm.md#compiler-order); their internal algorithms are not supplied by this table.

### Symbolic operands and register assignment

A register operand contains `type:"register"`, `fnId`, `id`, and optional `kind`, `scopeId` or
`pinned` metadata. The identity is `(fnId,id)`, not a JavaScript identifier string. IDs are fresh
within a function. A compiler scope maps local source names to these identities; recursive name
resolution creates upvalue indexes for enclosing locals, and unresolved names become constant
names used by global-access handlers. Cloned operand objects retain that identity.

Register allocation scans operand appearances by instruction-list index and operand order,
separately for each function. The **first register occurrence** of `(fnId,id)` initializes
firstUse, lastUse and poolKey. Compute that occurrence's poolKey as `"local::"` when pinned,
otherwise `(kind ?? "local") + "::" + (scopeId ?? "")`. Later occurrences extend lastUse unless
already freed; they never replace or merge the stored kind/scope/pin decision. A later pinned
occurrence therefore cannot upgrade an identity first seen in a temporary pool. A `freeReg`
pseudo marker clamps lastUse and stops extension. Producers must preserve the required metadata
on the first emitted occurrence; there is no strongest-pin reconciliation. Locals in local:: are
handled first; other pool keys follow lexicographically. The explanatory procedure is:

```text
for each function's collected register identities:
  nextSlot = descriptor.reservedRegisters or 0
  for each pool in priority order:
    if pool is "local::":
      visit ascending virtual IDs
      map id < reservedRegisters to identical slot id
      map every other id to nextSlot; increment nextSlot
    otherwise:
      visit ascending firstUse, retaining encounter order for ties
      reuse the lowest slot in THIS pool with prior lastUse < current firstUse
      if none exists, allocate nextSlot and increment it
  patch every register operand's resolvedValue using this function's map
  regCount = max(mapped slot + 1), or 0 when no slot is mapped
patch fnRegCount(fnId) operands from the corresponding descriptor.regCount
```

The strict `<` condition prevents two registers used in the same instruction from sharing a slot.
Free lists do not cross pool boundaries. `regCount` is the maximum mapped extent, not the virtual
ID count, not the sum of pool populations, and not automatically `reservedRegisters` when no
register is collected. Register operands keep their metadata; resolution sets `resolvedValue`.

Parameters are the leading IDs in source parameter order. Non-arrow functions reserve
`paramCount + 2` leading locals: parameters, `arguments` at `paramCount`, and hidden `this` at
`paramCount + 1`; a `LOAD_THIS` prologue initializes the last. Arrows reserve only their parameters
and capture enclosing `arguments`/`this` when used. The root is compiled as a non-arrow function
with zero parameters. Root push has `args = null`, so it skips argument initialization.

### Word addresses and serialization

Define `width(instr) = 0` when its opcode is null; otherwise count its elements, including the
opcode, except operands marked `placeholder:true`. A label definition records the current sum
of widths. A label reference resolves to `labelPc + (offset ?? 0)`, optionally applying its
operand's transform function. Undefined labels throw `Undefined label: <name>`. Function
`startPc` is patched from its entry label. The optional transform is a declared producer interface;
[encoded branch dispatch](transforms/encoded-branch-dispatch.md#label-identity-and-final-pc-update)
owns its bijection, site identity and delayed encoding mechanism.

Label resolution retains pseudo-instructions for comment generation. Serialization omits all
null-opcode instructions, filters placeholder operands, and chooses `resolvedValue ?? operand`
for each remaining element. Thus the output is one contiguous sequence containing all function
bodies; no per-function byte array or descriptor table is serialized. Root metadata and inline
`MAKE_CLOSURE` operands carry function entry/register information.

The intended word domain is integer `0 <= w <= 0xffffffff`. The serializer checks operand type
`number` and the range, and checks the opcode range; it does **not** assert integrality. Ordinary
compiler finalization supplies integers. Fractional hand-built IR would not receive an integer
validation error from this boundary; it must not be described as an accepted compiler input form.
Unresolved operands and out-of-range values fail serialization assertions. An unresolved
placeholder can also fail this check because operand validation occurs before flat-stream
placeholder filtering.

### Augmentation operand handoff

[Specialized tuples](transforms/specialized-opcodes.md) keep baked operands in private instruction
arrays with `placeholder:true`. They still participate in register scanning/resolution, label
resolution and pool interning, including in the tuple metadata used to build handlers. Their
emitted width is zero; the opcode still contributes one word. Do not copy their unresolved
values into independent metadata: the original operand objects are the late-resolution channel.
Label and constant resolvers use Object.assign to retain object identity while changing type
and resolvedValue; register resolution sets resolvedValue without discarding metadata.

[Aliases](transforms/aliased-opcodes.md) and [macros](transforms/macro-opcodes.md) reorder or
concatenate existing operand references. [Anti-instrumentation](transforms/anti-instrumentation.md)
retains real refs while adding fresh fake occurrence objects and expanded constant pairs.
Instruction-array identity is not this channel: producers/resolvers can replace arrays while
keeping their operand objects. Placeholder mutation makes shared occurrence objects unsafe;
fresh copies with the same `(fnId,id)` keep semantic register identity without shared flags.

After augmentation, emitted widths and handler metadata are settled. Resolve registers before
optional self-modifying region construction; resolve labels/constants afterward. Region sizing
and encryption both ignore placeholders, and opaque ciphertext cannot be interpreted as a
specialized header merely because its first word matches a registered code. Serialization
still validates hidden operands before omitting them. This is the width/identity interface;
PATCH chunk, junk, literal reachability boundaries and encryption are specified by the separate
[self-modifying wordcode recipe](transforms/self-modifying-wordcode.md); its bounded controls do
not establish all composed execution.

### Word transport

For encoded transport, the explanatory equations for word `w[i]` and byte `b[4i+j]` are:

```text
b[4i+j] = (w[i] >>> (8*j)) & 255, for j = 0,1,2,3
BYTECODE = base64(b)
w[i] = (b[4i] | (b[4i+1] << 8) | (b[4i+2] << 16) | (b[4i+3] << 24)) >>> 0
byteLength = 4 * wordCount
```

The encoder uses JavaScript bitwise u32 coercion for packing. Runtime decoding allocates a
`Uint32Array(byteLength/4)` and returns it; the raw mode returns the numeric array unchanged.
`_operand()` reads `bytecode[regs[fp + SLOTS.PC]++]`. Dispatch increments the PC once for the
opcode, then the handler consumes its complete operand grammar. The instruction table's
numeric width column counts **operand words**; total instruction width adds one opcode word.
A value/key constant pair therefore contributes two words even when the key is zero.

### Constant pool and emitted binding relationships

[Keyed constants](transforms/keyed-constants.md) owns mandatory pair expansion, first-value Map
interning, index/key reuse, in-place occurrence updates and exact storage/materialization equations.
Pair expansion precedes width measurement, and later interning changes no width. Hidden operands
still intern; the original operand object carries final index/key values to its consumer. Pool
values are JavaScript values rather than u32 words. The integer concealment gate includes values
outside its int32 preservation domain; the detailed page states the actual coercion and signed-zero
limits instead of an imagined range guard.

Pool source emission writes undefined/null explicitly, strings via Babel string-literal generation,
and other values through `JSON.stringify`. This records the emission rule, not a claim that any
arbitrary JavaScript object or non-finite number can round-trip through the pool.

| Emitted role in plain runtime | Value and binding relationship |
|---|---|
| `CONSTANTS` | Array supplied as VM's constants argument; `_constant` consumes indexed entries and key operands. |
| `BYTECODE`, `ENCODE_BYTECODE` | Numeric word array plus false, or base64 string plus true; `decodeBytecode` supplies VM's bytecode argument. |
| `MAIN_START_PC`, `MAIN_REG_COUNT` | Root `Closure.fn.startPc`/`regCount`; root `paramCount` is zero. |
| `OP` | Operation names mapped to dispatch values; compiler emits matching values. Plain canonical map has keys/values in the instruction table, including `EXP=60`, `PATCH=56`. |
| `SENTINELS.CALL_SPREAD` | Distinguishes spread from count operands in CALL/CALL_METHOD/NEW; plain value 65535. |
| `SLOTS`, `HEADER_SIZE`, `FRAME_START` | Header offsets, block register-area offset, initial allocation position; used by push, operand reads, calls, returns and unwinding. |
| `TIMING_CHECKS` | False, supplied numeric threshold, or 1000 milliseconds when option is true; runtime's pause branch uses it. |
| `globals`, VM, root Closure | Boot supplies host globals, decoded words and pool to VM, then calls `run(root, undefined, null)`. |

The serialized declarations precede the runtime template; constants are emitted before the other
sections. In the plain runtime, `VM` stores `bytecode`, `constants`, `globals`, a flat `_regs` array,
`_regsTop` and current frame base `_f`. `CLOSURE_MAP` associates host callable shells with internal
closures. These relationships, rather than generated name spelling or comments, give a container
its meaning. Later class/minifier rewrites can inline scalars/maps and alter bindings; requiring
all the plain declaration spellings would erase emitted variants.

Boot uses `globalThis`; when `window` exists it assigns its `window` and `document` properties,
and when `module` exists it assigns `module` and `exports`. Even when timing checks are disabled,
`run` initializes its clock through `performance.now()`. Those host facilities are runtime
prerequisites, not a promise that `target` selects a different interpreter.

### Frame and capture state

A frame occupies `[fp, fp + HEADER_SIZE + regCount)` in the single `_regs` array. Header offsets
are relative to `fp`, while register operands are relative to the stored `REG_BASE`:

```text
registerAddress(r) = regs[fp + SLOTS.REG_BASE] + r
push: fp = _regsTop; size = HEADER_SIZE + closure.fn.regCount
      initialize [fp, fp+size) to undefined
      REG_BASE = fp + HEADER_SIZE; FRAME_SIZE = size
      PC = closure.fn.startPc; CALLER = previous _f
      RET_DST = supplied return encoding; THIS = supplied receiver; CLOSURE = closure
      _regsTop = fp + size; initialize arguments when args is non-null; _f = fp
```

| Slot | Plain offset | Meaning |
|---|---:|---|
| PC | 0 | Current absolute word PC. |
| CALLER | 1 | Caller frame base; zero is the host boundary. |
| RET_DST | 2 | `(destinationRegister << 1) | constructorBit`. |
| THIS | 3 | Receiver, including created object for virtual NEW. |
| CLOSURE | 4 | Executing closure and its upvalues. |
| HANDLERS | 5 | Lazily allocated exception-handler stack. |
| FRAME_SIZE | 6 | Total block extent, header plus registers. |
| REG_BASE | 7 | Absolute address of r0. |

Plain `HEADER_SIZE=8`, `FRAME_START=1`; slot zero is outside frames and stores the host result.
For ordinary calls without rest, push copies `args[a]` while `a < args.length && a < regCount`,
then writes the args array at `paramCount` if `paramCount < regCount`. With rest, positions before
`paramCount-1` receive supplied args or undefined, and that final parameter receives
`args.slice(paramCount-1)`; the same args-array write follows. This is the actual positional
interface, not an assertion that the VM has a native JavaScript `arguments` object.

`MAKE_CLOSURE` contains, after its opcode, `dst,startPc,paramCount,regCount,uvCount,hasRest`,
then `uvCount` pairs `(isLocal,index)`: total width is `7 + 2*uvCount` words. A local capture's
index is a relative register in the creating frame; a non-local capture's index selects the
creating closure's upvalue list. Local captures deduplicate by absolute address in
`_openUpvalues`. While open, the shared upvalue reads/writes the frame slot; on close it stores
that slot's value in its own cell. Closing deletes the open-table entry so a later frame reusing
the address cannot inherit the old cell. The capture plan is consumed at creation rather than
kept in the runtime function descriptor.

Normal RETURN obtains the value and closes upvalues before reading caller/return metadata and
clearing the whole returning frame. It resets `_regsTop=fp` and `_f=caller`, then writes to the
caller's relative destination (`retDst >> 1`) or slot zero at the host boundary. The constructor
bit affects which value is returned; full call/constructor behavior belongs to the instruction
semantics dependency. Exception unwinding also closes captures and releases each abandoned frame,
then selects a handler through the caller chain. Catch receives the payload in its exception
register; finally receives a continuation PC and payload. The [instruction contract](instruction-set.md#catch-finally-and-abrupt-completion) specifies
handler installation, abrupt completion and finally routing; this container foundation supplies
the frame/cell interfaces rather than independently guaranteeing every semantic case.

### Emitted forms, failures and publication

| Form or condition | Encoder result |
|---|---|
| Plain reference options | Canonical numeric word array, visible pool/key-zero pairs, canonical maps and plain frame offsets. |
| Encoded transport | Base64 byte string and true mode flag; same word PCs after boot decoding. |
| `randomizeOpcodes` | Distinct canonical opcode values in 0..65535; sentinel chosen in 65535..4294967295; permuted frame offsets with selected noise/junk and shifted first frame. |
| Runtime hardening | Added handlers, case shuffle, handler-table dispatch, class reshaping or minification, in workflow order; plain binding spellings can disappear. |
| Wordcode hardening | Concealed constants/control/string helpers, added opcodes, PATCH/encrypted regions; detailed grammar/effects require their own contracts. |
| Undefined symbolic label | Throws during label finalization. |
| Unresolved/out-of-range numeric operand | Serializer assertion failure; no returned `code`. |
| Unsupported lowering form, runtime parse/generate/minify failure | Throws/rejects the public asynchronous operation; no successful result object. |

Randomized frame construction adds a selected subset of push/dispatch noise names, at least one,
to the eight real names; `HEADER_SIZE = names.length + random(0,4)`. It permutes offsets from
`0..HEADER_SIZE-1`, assigns one distinct offset to each name, shuffles emitted map entries, and
chooses `FRAME_START` in `1..16`. Real slot access still follows SLOTS/REG_BASE. Exact selection/
churn and case-shuffle decisions are owned by
[runtime layout](transforms/runtime-layout.md); late representation recipes live in
[handler table](transforms/handler-table.md), [class runtime](transforms/class-runtime.md) and
[final minification](transforms/minify-runtime.md). Detailed added-opcode recipes live in
[aliases](transforms/aliased-opcodes.md), [macros](transforms/macro-opcodes.md),
[specialized tuples](transforms/specialized-opcodes.md) and
[anti-instrumentation](transforms/anti-instrumentation.md). Their retained synthetic subsets and
remaining direct/generated/state debt are indexed in each page's Fixtures; the plain example
does not certify them. The [PATCH producer recipe](transforms/self-modifying-wordcode.md) closes
its source-derived selection/encryption contract, with a
[bounded cold proof](transforms/self-modifying-wordcode.md#fixtures) for selected mechanics using
supplied finalization/value oracles. Actual resolver/runtime/composed/generated evidence is still missing.
[Keyed constants](transforms/keyed-constants.md), [shared string bank](transforms/shared-string-bank.md),
[state control flow](transforms/state-control-flow.md) and
[encoded branch dispatch](transforms/encoded-branch-dispatch.md) close their producer recipes,
with [shared helper assembly](symbolic-helper-assembly.md) supplying the symbolic integration
contract. Their arithmetic/IR examples do not execute actual lowering/finalizers/runtime or qualify
composed generated output. The [frozen selected proof](symbolic-helper-assembly.md#frozen-selected-mechanics-proof-boundary)
adds bounded operand/route decisions with supplied scaffolds; actual register allocation, full
finalizer/descriptor state and frames remain outside it, including the first-occurrence pool rule.

The compilation unit is the whole supplied source string. It uses a fresh compiler and mutates
its private IR/descriptor state through finalization; there is no partial code publication,
retry/resume protocol or rollback of already executed generated JavaScript. The promise returns
only after runtime generation and optional minification succeed. Source text is immutable input;
pseudo records remain compiler-side for comments, but are absent from runtime words. Returned
profile data describe compilation, not execution. During execution, normal return clears its
frame; exception abandonment releases frames and closes captures but does not use the normal
RETURN clearing loop. Boot/global mutations and host program effects are runtime state.

### Testing and acceptance design

These scenarios identify what would accept the components above. Existing encoder-local test
sources provide behavioral controls where named; they are not frozen generated-output fixtures,
and their presence alone is not a fresh execution result.

| Scenario | Observable result / oracle | Acceptance criterion | Evidence/control |
|---|---|---|---|
| F1: final-word addressing and constant pairs | Worked example takes exactly the true/false PC traces above and returns corresponding pool values. | Label 13, 19 words, zero keys; no pseudo word; both traces consume complete operands. | Synthetic example in item 2; no retained direct finalizer fixture. |
| F2: raw and encoded transport | Word-to-byte round trip equals original stream; source program result agrees in both modes. | Four LE bytes per word, preserved high bit, PCs remain word indexes. | Encode Bytecode test plus transport equations; missing direct retained high-bit/length control. |
| F3: register lifetimes and reserved slots | Disjoint temporaries reuse; overlapping same-instruction uses do not; unused parameters do not shift captured locals. | Per-function/pool maps satisfy the exact allocator and positional frame writes. | Closures/ArrowFunctions behavioral tests; missing direct slot-map/free-marker controls. |
| F4: shared/escaped captures and frame release | Setter and getter share one cell; escaped closure works after outer return; reused frame address gets a new open cell. | Close-before-release preserves values and removes open-table entries; normal frame window is cleared. | Closures variants 3, 6, 7; missing direct frame/open-table state controls. |
| F5: exception release/handler continuation | Catch payload and finally order agree with source expectations. | Unwinding releases abandoned frames and selects the correct handling frame/continuation. | TryCatch/TryFinally behavioral tests; direct state controls still required; canonical semantics are specified in the instruction contract. |
| F6: failure publication | Undefined label/unresolved operand reaches its named finalizer assertion; unsupported syntax rejects. | No successful `{code,...}` result after failure; a fresh compilation has fresh state. | Source-derived failure contracts; missing retained direct negative controls. |
| F7: randomized layout/runtime forms | Maps and matching runtime agree; frame addresses follow chosen offsets; plain and selected variants preserve source result. | Layout offsets are distinct/in-header, frame start is positive, handlers match emitted values. | Options effect inventory; no combined-variant evidence claimed here. |

Behavioral tests for F3-F5 can miss wrong internal state that happens to produce the same output;
the named direct-state controls remain required for component acceptance. F6 controls must reach
the specific finalizer failure rather than an unrelated earlier parser error. Selected optional
variants require actual retained configuration/output provenance and their own scenario design;
neither this synthetic assembly nor a canonical handler table qualifies those interactions.

## 4. Later Stages

| Producer/stage position | Shape emitted or changed | Consequence for this contract |
|---|---|---|
| Constant expansion before register/label resolution | Adjacent value/key placeholders | Word sizing includes both, independent of value concealment. |
| Register resolution -> self-modifying construction -> labels/constants -> encryption | Concrete slots and final encrypted region words | PATCH needs concrete slots before construction and final words before encryption. Its opaque words cannot be counted as ordinary instruction headers. |
| Label resolution followed by constants | Addresses already sized for pair expansion | Interning replaces placeholders without changing emitted widths. |
| Serializer | Null records dropped, placeholders filtered, metadata followed by runtime text | Function labels are word PCs in the single flat stream; bookkeeping survives only outside runtime data. |
| Runtime handler additions -> shuffle -> table -> class -> minify | Switch handlers, reordered cases, lifted dispatch, rewritten/inlined bindings | Core data roles persist through their runtime uses even when plain declarations do not. |
| Generation/comment prefix -> minification | Comments may be reformatted or removed | Comments are not execution metadata or a requirement on final source spelling. |

These are emitted alternatives of this encoder at the pin, regardless of external tooling.
Their internal mechanism details beyond the foundation are declared dependencies, not exclusions
from what the encoder emits.

## 5. Known Quirks

- Several source/type/label comments say u16; executable packing/unpacking is u32. Opcode
  allocation uses `U16_MAX`, while random spread sentinel and keys can occupy the full u32 domain.
- Serializer range assertions do not check integers, stream grammar, target ownership, capture
  indexes or all function boundaries. Do not substitute a stronger imagined validation contract.
- The `Constant` type alias is narrower than values handled by lowering/pool code. Pool emission
  uses JSON for non-strings; arbitrary/non-finite-value preservation is not specified here.
- [Keyed constant concealment](transforms/keyed-constants.md#interning-and-storage-decisions)
  selects every integer Number but preserves only its int32 result; its gate has no range refusal.
- This foundation gives capture/frame interfaces and a bounded instruction example. Full
  lowering/syntax coverage remains outside the recipes; concealment/control helper lowering is
  supplied infrastructure, with direct/generated/composed execution evidence still missing. The
  [PATCH producer/encryption recipe](transforms/self-modifying-wordcode.md) supplies
  its literal selection and state boundaries; its linked bounded proof covers selected private
  decisions, while actual resolver/runtime/publication/composed/generated controls remain owed.
  Added-opcode recipes are linked in the augmentation
  handoff; their state, negative and generated-output controls remain bounded. Runtime layout/table/
  class/minify recipes are linked above; their direct controls and generated-output evidence
  remain bounded independently. The instruction contract specifies canonical call/constructor,
  capture, handler/finally and PATCH execution; the option inventory specifies timing poisoning.
  Their direct edge/state controls remain evidence debt.
  No whole-instruction reconstruction claim is made. The retained synthetic subset proof indexed
  in [instruction-set.md](instruction-set.md#fixtures) does not execute or observe the real runtime.

## Source

All links are frozen at the documented pin. The pipeline wiring forcing the order in items 2,
3 and 4 is [compiler.ts#L3276-L3458](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/compiler.ts#L3276-L3458).
Operand identities and metadata are
[types.ts#L13-L98](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/types.ts#L13-L98);
local/upvalue relationships, descriptors and concatenation are
[compiler.ts#L162-L305](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/compiler.ts#L162-L305),
[compiler.ts#L439-L459](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/compiler.ts#L439-L459),
[compiler.ts#L576-L742](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/compiler.ts#L576-L742)
and [compiler.ts#L847-L873](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/compiler.ts#L847-L873).

Finalization in item 3 is implemented by
[op-utils.ts#L41-L47](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/utils/op-utils.ts#L41-L47),
[concealConstants.ts#L4-L52](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/transforms/bytecode/concealConstants.ts#L4-L52),
[resolveRegisters.ts#L34-L239](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/transforms/bytecode/resolveRegisters.ts#L34-L239),
[resolveLabels.ts#L29-L111](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/transforms/bytecode/resolveLabels.ts#L29-L111)
and [resolveConstants.ts#L45-L142](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/transforms/bytecode/resolveConstants.ts#L45-L142).
The augmentation-to-PATCH width interface (the separate
[self-modifying recipe](transforms/self-modifying-wordcode.md) owns region selection/encryption) is
[selfModifying.ts#L96-L97](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/transforms/bytecode/selfModifying.ts#L96-L97)
and [encryptPatches.ts#L19-L79](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/transforms/bytecode/encryptPatches.ts#L19-L79).
Serializer checks, packing and declarations are
[compiler.ts#L2906-L2911](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/compiler.ts#L2906-L2911)
and [compiler.ts#L3144-L3272](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/compiler.ts#L3144-L3272).
Map/sentinel construction and frame layouts are
[compiler.ts#L390-L417](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/compiler.ts#L390-L417)
and [frame-layout.ts#L30-L107](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/utils/frame-layout.ts#L30-L107).

Runtime transport/frame/capture interfaces are
[runtime.ts#L23-L217](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/runtime.ts#L23-L217),
[runtime.ts#L645-L742](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/runtime.ts#L645-L742)
and [runtime.ts#L908-L976](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/runtime.ts#L908-L976).
Runtime AST order and publication are
[build-runtime.ts#L17-L124](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/build-runtime.ts#L17-L124).
These references verify the container contract; canonical handlers are specified by
[instruction-set.md](instruction-set.md), while runtime representation and
wordcode-producer recipes plus their evidence boundaries are named in items 1, 3 and 5.

## Fixtures

There are no retained generated-container fixtures in this package. The following committed
encoder-local test sources are behavioral evidence designs for the scenarios in
[Testing and acceptance design](#testing-and-acceptance-design). They generate output at test time
via [test-utils.js](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/test/test-utils.js)
using explicit overrides or the test configuration. No fresh execution of this test suite or
combined-option qualification is asserted here.

| Committed source/control | Claim it exercises | What it does not establish |
|---|---|---|
| [IfStatements.test.js](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/test/features/IfStatements.test.js) | F1: true/false branches and nesting preserve expected values. | Exact synthetic stream/PCs or all label widths. |
| [encodeBytecode.test.js](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/test/options/encodeBytecode.test.js) | F2: raw versus encoded representation and the encoded program result. | Direct high-bit word/byte round trip and malformed transport controls. |
| [Closures.test.js](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/test/features/Closures.test.js) | F3/F4: captures, mutable shared cells and escaped closures (variants 3, 6, 7). | Direct slot-map, frame-clearing and open-table invariants. |
| [ArrowFunctions.test.js](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/test/features/ArrowFunctions.test.js) | F3: lexical this/arguments and capture behavior. | Every reserved-local and pool-reuse decision. |
| [TryCatch.test.js](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/test/features/TryCatch.test.js), [TryFinally.test.js](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/test/features/TryFinally.test.js) | F5: payloads, nested handlers and finally completion. | Direct unwinding-state controls; semantic specification lives in the instruction contract. |
| No retained direct control | F1 exact finalizer example; F2 high-bit bytes; F3-F5 internal state; F6 negative publication; F7 combined representations. | These acceptance criteria remain unevidenced by retained fixtures here. |

The item 2 assembly is a durable explanatory example with checkable arithmetic, not a stored
encoder-produced specimen. Source-derived contracts, inspected test intent and empirical execution
are separate evidence levels; none supplies absent generation bytes or option provenance.
