# Randomize runtime layout and shuffle dispatch cases

## 1. Target

Make opcode values and live frame locations vary between builds, and optionally vary the physical
listing of handlers, while keeping the emitted words and interpreter coupled. `randomizeOpcodes`
selects canonical opcode values, the spread-call sentinel and the frame layout during compiler
construction. `shuffleOpcodes` later reorders complete switch cases. These are independent gates:
changing a handler's position does not change its numeric opcode.

Read the [workflow and AST foundation](../js-confuser-vm.md#prerequisites-and-scope),
[container units/frame interface](../container-wordcode.md) and
[canonical instruction semantics](../instruction-set.md). This page owns allocation and runtime
noise, not new added-opcode selection, PATCH production or source lowering. Transport remains
specified by [word addresses and serialization](../container-wordcode.md#word-addresses-and-serialization).
The algorithms below are source-derived at the package pin; retained test intent is narrower
than complete generated-output or state qualification.

## 2. Algorithm

Choose a map before emitting instructions, so every symbolic operation is lowered to its chosen
value and the serializer embeds the same map for case tests. Repeated draws are retried until
each canonical operation has a distinct value. Choose the spread sentinel separately: it occurs
in an argument-count operand, where it cannot be mistaken for an opcode header.

Build a frame header with the eight real roles and selected decoy roles. Give each role its own
offset within the header; any unused offsets remain junk. Registers follow the entire header,
so a register's address is obtained through the stored REG_BASE rather than inferred from a
fixed PC offset. Seed/churn selected noise slots during execution without using them as program
values or control targets. The real header relationships remain those in the container contract.

After all added handlers exist, shuffle entire `SwitchCase` nodes, including default. Cases have
no intentional cross-case fallthrough; each ordinary case exits the switch. Reordering these
nodes therefore changes listing position while retaining each test/body pairing. Lifting,
class rewriting and minification subsequently consume this completed dispatch representation.

### Worked example

This **synthetic allocation**, not a generated specimen, chooses `LOAD_CONST=400`, `RETURN=9`,
`CALL_SPREAD=70000`, `FRAME_START=4` and `HEADER_SIZE=12`. Select NOISE_END and NOISE_COUNTER,
use two junk offsets, and assign:

| Role | Offset | Role | Offset |
|---|---:|---|---:|
| PC | 5 | CALLER | 0 |
| RET_DST | 8 | THIS | 2 |
| CLOSURE | 11 | HANDLERS | 1 |
| FRAME_SIZE | 3 | REG_BASE | 7 |
| NOISE_END | 9 | NOISE_COUNTER | 4 |

For a one-register root starting at word PC zero, `fp=4`, `size=13`, `end=17`, and r0 is at
`4+12=16`. PC is at slot `4+5=9`, REG_BASE at slot 11, and NOISE_END at slot 13 stores 17.
The canonical synthetic stream `LOAD_CONST r0, pool[0], key=0; RETURN r0` becomes
`[400,0,0,0,9,0]`, six words (24 bytes if transported). Dispatch advances the real PC from 0
to 1; LOAD_CONST consumes three operands to PC 4; RETURN consumes its operand to PC 6 and
completes through the normal root/result-cell contract. NOISE_COUNTER starts at zero and reaches
two after these two dispatches. Reordering the cases as `RETURN, default, LOAD_CONST` changes
none of those words, addresses or results. Slot zero remains the host result cell.

The example omits other canonical map entries, call/spread execution, optional added handlers,
other noise kinds, exception release and actual random sampling. Its chosen offsets are distinct
and lie in `[0,12)`; unused offsets are 6 and 10.

## 3. Implementation

### Components and exact allocation

| Component | Input -> output | Required coupling |
|---|---|---|
| Canonical allocator | OP_ORIGINAL and flag -> OP, OP_NAME, JUMP_OPS | Lowering/IR passes and serialized case map use the same values. |
| Added-opcode allocator | Current OP_NAME and randomize flag -> free code or -1 | Added-opcode caller immediately reserves successful value in OP_NAME. |
| Sentinel allocator | Flag -> SENTINELS.CALL_SPREAD | All call forms compare argc with that emitted operand value. |
| Header allocator | Flag -> SLOTS, HEADER_SIZE, FRAME_START | Push/fetch/operand/capture/return access the same offsets. |
| Runtime noise | Layout and frame/dispatch state -> decoy slot writes | Never supplies real PC/register/capture roles. |
| Case shuffle | Completed marked switch -> permuted same cases | Test/body identity and numeric word values unchanged. |

The shared random primitive draws `int(lo,hi) = floor(Math.random()*(hi-lo+1))+lo`, inclusive
at both endpoints. `choice` indexes `floor(Math.random()*length)` and asserts nonempty input.
`chance(p) = Math.random() < p/100`, where p is a percentage rather than a 0..1 fraction.
The comparison is strict: a supplied draw equal to p/100 yields false. The helper does not
clamp or validate p; callers here supply the documented percentages.
`shuffle` mutates an array in place using Fisher-Yates: for `i=length-1..1`, choose
`j=floor(Math.random()*(i+1))` and swap positions i and j. No seed or reproducibility API is supplied.

Canonical construction copies OP_ORIGINAL. With randomization truthy, visit that object's keys
in enumeration order; repeatedly draw `int(0,65535)` until the value is absent from a fresh
used-value set, then reserve it and assign OP[key]. There is no bounded retry/fallback in this
canonical allocator. Without the flag retain the canonical values. OP_NAME is the inverse
numeric-value-to-name object; JUMP_OPS contains the actual mapped values of JUMP, JUMP_IF_FALSE,
JUMP_IF_TRUE, FOR_IN_NEXT, TRY_SETUP and FINALLY_SETUP. Added values use the shared allocator below.
Template-compiled
helper code constructs a child with randomization off, then copies the parent's OP, OP_NAME,
JUMP_OPS and SENTINELS before compilation. Thus helper instructions do not draw an independent
map/sentinel. Full helper compilation, label/descriptor and capture recipes remain with their
wordcode producers; frame layout is runtime-only and is not encoded into register operands.

CALL_SPREAD is 65535 without randomization, otherwise `int(65535,4294967295)`. It has no collision
check against OP, because its role is an argc operand, not an opcode. Ordinary source call/new
argument counts must be less than 65535; the sentinel is consequently outside that count domain.
Both opcode and sentinel values serialize as u32 **words**; a 16-bit opcode range does not imply
a two-byte transport or a byte PC.

### Added-opcode allocation

The [anti](anti-instrumentation.md), [specialized](specialized-opcodes.md),
[macro](macro-opcodes.md) and [alias](aliased-opcodes.md) producers share `nextFreeSlot`.
Unlike canonical construction's unbounded rejection sampling, this operation has a bounded
random attempt phase and a complete wraparound fallback. It consumes private compiler maps,
not an externally supplied arbitrary set. Exact explanatory procedure:

```text
keys = Object.keys(OP_NAME)
used = Set(keys.map(k => parseInt(k,10)).filter(v => !isNaN(v)))
if used.size > 65535: return -1
if options.randomizeOpcodes:
  repeat at most 512 times:
    candidate = int(0,65535)
    if candidate not in used: return candidate
start = keys.length
for i = 0 through 65535 inclusive:
  candidate = (start+i) & 65535
  if candidate not in used: return candidate
return -1
```

The fallback starts at the key count, not a random position despite its source comment.
The function does not mutate OP_NAME: the caller writes the new added opcode's name immediately
before requesting the next slot. Otherwise two requests can return the same value. It reserves
all existing canonical and synthetic OP_NAME keys, without adding sentinel/frame roles to the
used set. Exhaustion returns -1 for the producer to stop allocation; zero is a valid result.
Successful allocation does not extend OP or JUMP_OPS, and its 16-bit domain still emits one u32
word. A synthetic deterministic check with keys 0 and 2, random draws 0 then 1, returns 1;
after caller reservation and 512 colliding draws, fallback starts at key count 3 and returns 3.
This illustrates reservation and fallback, not randomness distribution or encoder execution.

### Frame allocation

Plain layout uses role order `PC,CALLER,RET_DST,THIS,CLOSURE,HANDLERS,FRAME_SIZE,REG_BASE`,
offsets 0 through 7, header size 8 and first frame base 1. Randomized construction is exactly:

```text
pushCandidates = [NOISE_END, NOISE_PARAMS, NOISE_ARGS]
dispatchCandidates = [NOISE_PC, NOISE_COUNTER, NOISE_MIRROR, NOISE_ACC]
picked = shuffle(copy(pushCandidates))[0:int(0,2)]
       + shuffle(copy(dispatchCandidates))[0:int(0,2)]
if picked is empty: append choice(pushCandidates + dispatchCandidates)
names = realRoles + picked
HEADER_SIZE = length(names) + int(0,4)
offsets = shuffle([0,...,HEADER_SIZE-1])
entries = [(names[i],offsets[i]) for each i]
SLOTS = objectFromEntries(shuffle(entries))
FRAME_START = int(1,16)
```

The selection has one to four distinct decoys. Header size is 9 through 16, with zero through
four unassigned junk slots. Offsets are injective and in-header; object-entry shuffle changes
listing order separately from offset assignment. FRAME_START never uses zero. Neither the
random process nor plain mode promises different choices on every build.

### Noise and emitted spellings

Push first clears the entire frame window to undefined. Each following write is guarded by
`typeof SLOTS.<role> === "number"`, so a missing role performs no write. Dispatch churning occurs
after opcode fetch/PC increment and before timing checks and the handler try/catch.

| Noise role | Push value | Per-dispatch update |
|---|---|---|
| NOISE_END | `fp + HEADER_SIZE + regCount` | None |
| NOISE_PARAMS | `closure.fn.paramCount` | None |
| NOISE_ARGS | Supplied args, including null for root | None |
| NOISE_PC | `closure.fn.startPc` | `(old + 1) % bytecode.length` |
| NOISE_COUNTER | 0 | `old++` |
| NOISE_MIRROR | Remains undefined after clear | Fetched `op` |
| NOISE_ACC | Remains undefined after clear | `(old ^ fetchedPc) | 0` |

The first ACC XOR uses JavaScript's int32 coercion of undefined to zero. NOISE_PC's modulus uses
word count; it is unrelated to jumps or variable instruction widths. MIRROR copies op before
possible timing poisoning. These values may contain genuine runtime objects (ARGS), but the
interpreter never consumes them as real state.

Case shuffle locates the first SwitchStatement whose **leading** comment contains `@SWITCH`,
asserts it exists, then assigns its shuffled cases array. It does not validate terminal breaks,
uniqueness or arbitrary fallthrough. Marker presence is a build-time contract of the assembled
runtime, not a condition on final minified text.

### State, failure and acceptance

Construction mutates a fresh compiler's maps/layout; shuffle mutates its private runtime AST.
The compilation publication boundary is the [container's whole-source unit](../container-wordcode.md#emitted-forms-failures-and-publication).
A missing marked switch throws, rather than returning a partially transformed successful code
result. There is no per-case transaction or generic rollback. Runtime slot cleanup remains the
canonical return/unwind contract; decoys are included in the same frame extent.

| Scenario | Observable result / oracle | Acceptance criterion | Retained control |
|---|---|---|---|
| L1: mapped emission | Actual words, OP tests and reverse map agree | Distinct values 0..65535; original identities preserved | randomizedOpcodes test intent; bounded three-name retry/coupling proof; full canonical-map generation missing |
| L2: frame/noise allocation | Addresses derive from chosen header and stored REG_BASE | Injective offsets, positive frame start, decoy subset/junk bounds | Synthetic example and deterministic allocation proof; randomized test decoy/behavior assertions; real slot-state controls missing |
| L3: real versus decoy PC | Branch/return PC follows canonical handlers while noise churns | Noise never becomes real state; frame clear includes noise | No retained direct churn/clear control |
| L4: numeric values versus case order | Same test/body pairs and words before/after shuffle | Whole-node permutation includes default, preserves terminal behavior | shuffleOpcodes listing test; direct same-input AST/word control missing |
| L5: combined representations/failure | Table/class consume completed handlers; missing marker throws | Matching numeric keys/offsets; no successful publication on missing marker | Selected randomized combined test; negative marker control missing |
| L6: added-opcode space | Scripted draws and OP_NAME reservation trace | Collision retry, 512-attempt fallback, wrap, zero and exhaustion agree with procedure; no duplicate after caller reservation | Retained added-opcode verifier reconstructs this bounded allocator; distributions/full compiler generation remain excluded |

The retired bounded verifier, built from the documents before source consultation, reconstructed a bounded document-only subset. For L1 it
uses supplied deterministic draws and three operation names to check duplicate retry, sentinel
endpoints and numeric emission coupling. For L2 it checks selected header extrema, decoy fallback,
injective offsets and address bounds; the synthetic table execution checks a chosen frame/result
extent. This does not sample the complete canonical map, random distribution or compiler emission,
or execute real noise, capture or unwind state. L3-L5's wider criteria remain open. L6's
deterministic added-space subset is retained separately in the added-opcode verifier below;
it does not reconstruct canonical randomized construction or recent-read chance sampling.

The examples permit arithmetic/state checks independent of encoder execution. The named test
sources are finite behavioral/shape oracles, not stored output bytes. A non-random comparison
must assert coupling and set equality; requiring two random draws to differ can fail by chance.

## 4. Later Stages

| Later producer | Emitted shape | Effect on this contract |
|---|---|---|
| Added opcode handlers | Extra numeric case tests | Same mapped canonical values; later allocations need unique free slots. The added-opcode transforms remain separately specified. |
| [Handler table](handler-table.md) | `VMPrototype[OP.X]` or numeric keys, `this[op]()` | Lifts current case order; optional second assignment shuffle still does not remap words. |
| [Class reshaping](class-runtime.md) | Literal case/key values and offsets; absent noise -> `void 0` | Inlines matching maps and removes their declarations only when all references are safe. |
| [Final minification](minify-runtime.md) | Optimized source and potentially dead-noise removal | No stable declaration, marker or case-order spelling follows solely from this layout recipe. |

## 5. Known Quirks

- Canonical opcode rejection sampling has no attempt cap. Repeated choices are possible; there
  is no guarantee that every build changes a particular value or offset.
- The spread sentinel may numerically equal a canonical opcode. Its operand role distinguishes it.
- Noise and junk are runtime-only frame slots; compiler register operands remain function-relative.
- Shuffling arbitrary fallthrough switches would change behavior. The pass relies on the completed
  pinned runtime's terminal cases and does not enforce that precondition for arbitrary ASTs.
- Complete real-map/noise/churn/cleanup controls and retained generated variants remain missing;
  the document-only allocation proof covers only the deterministic subset above.

## Source

Allocation and map coupling in items 2-3:
[compiler.ts#L377-L431](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/compiler.ts#L377-L431),
[op-utils.ts#L5-L39](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/utils/op-utils.ts#L5-L39),
[frame-layout.ts#L30-L107](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/utils/frame-layout.ts#L30-L107),
[random-utils.ts#L7-L39](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/utils/random-utils.ts#L7-L39).
The percentage/strict-comparison chance primitive is specifically
[random-utils.ts#L16-L18](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/utils/random-utils.ts#L16-L18).
Helper map propagation is
[template.ts#L73-L88](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/template.ts#L73-L88).
Serializer maps are [compiler.ts#L3228-L3267](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/compiler.ts#L3228-L3267);
noise consumers are [runtime.ts#L109-L155](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/runtime.ts#L109-L155)
and [runtime.ts#L232-L269](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/runtime.ts#L232-L269).
Call-count boundaries are [compiler.ts#L1907-L1913](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/compiler.ts#L1907-L1913)
and [compiler.ts#L2352-L2358](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/compiler.ts#L2352-L2358).
Case permutation is [shuffleOpcodes.ts#L10-L24](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/transforms/runtime/shuffleOpcodes.ts#L10-L24),
wired after handler additions in [build-runtime.ts#L58-L95](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/build-runtime.ts#L58-L95),
forcing the item 4 interactions.

## Fixtures

| Retained source/control | Scenario / bounded intent | Missing evidence |
|---|---|---|
| [randomizedOpcodes.test.js](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/test/options/randomizedOpcodes.test.js) | L1/L2/L5: selected changed opcode, decoy presence/plain absence, calls/loops/exceptions and table/class combination | Complete encoder allocation/churn/cleanup and frozen generated bytes |
| [shuffleOpcodes.test.js](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/test/options/shuffleOpcodes.test.js) | L4: first portion of case listing differs from plain, two plain listings agree | Same-AST set/body/default and numeric-map invariants |
| Retired bounded verifier | L1/L2: deterministic three-name rejection sampling/map coupling, selected header/decoy/address bounds and chosen synthetic frame arithmetic | Full map/distribution/compiler emission and real noise/state/generated-output evidence |
| Retired added-opcode verifier | L6: collision retry, caller reservation, 512-draw fallback, wrap, zero/exhaustion and bounded identity retry using deterministic draws | Full canonical map/distribution/compiler output; chance/recent-write sampling was not reconstructed |
| No retained direct control | L3, shuffle marker failure and missing criteria above | Proposed acceptance criteria remain unqualified |

Encoder-local option tests generate through [test-utils.js](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/test/test-utils.js).
The frozen document-only subset is not full-runtime reconstruction. No fresh encoder execution,
full-stack qualification or novice study is claimed.
