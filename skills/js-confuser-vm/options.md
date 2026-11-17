# js-confuser-vm option behavior

## 1. Target

Options select protection and emitted representation changes while core lowering, finalization
and runtime construction remain active. This page specifies the public option gates, stage
positions, observable effects and consequential interactions at the pinned `0.1.5` source.
It is an effect inventory: each optional mechanism's recipe lives on its linked page, and no
claim is made that every combination preserves every source form.

Read [the package prerequisites/workflow](js-confuser-vm.md#prerequisites-and-scope),
[container contracts](container-wordcode.md) and [canonical instructions](instruction-set.md).
The detailed optional recipes are linked from the option table in item 3. Source
links verify the inventory; they do not replace those normative recipes.

`DEFAULT_OPTIONS` is `{}`. The public call's default parameter supplies that object when options
are omitted/undefined; an explicitly supplied object is used directly, without a preset merge.
Boolean options are optional TypeScript fields and their ordinary stage gates use JavaScript
truthiness. The implementation provides no runtime option-schema validation, probability settings
or target-specific preset. `target` accepts `"node" | "browser"` in the type, but nothing reads it
to select compilation/runtime behavior. `timingChecks` has the special numeric/strict-true
serialization rule below. Supplying values outside the typed API is not promised support.

## 2. Algorithm

Construct the compiler with the supplied options before lowering, so instructions and runtime
maps share any chosen randomized values. Compile source into private symbolic IR. Apply enabled
wordcode passes in the actual scheduler order, retaining mandatory constant-pair expansion even
when value concealment is off. Then resolve concrete registers, construct optional PATCH regions,
resolve labels and pool entries, encrypt optional regions, and serialize program data together
with matching maps and runtime text.

Build runtime handlers for added opcodes before changing dispatch representation. Shuffle
case order, lift handlers or reshape classes only after those handlers exist. Generate source,
prepend the instruction comment block, and run final minification last when enabled. These
positions are causal: width-changing passes precede address measurement; PATCH encryption needs
final words; late AST passes consume the completed handler set.

### Worked gate/order example

This **synthetic configuration walkthrough** uses a canonical IR constant load
`LOAD_CONST r0, constant("ok")` and return. It is not a stored encoder-produced specimen.
With explicit `{encodeBytecode:true, shuffleOpcodes:true, profile:true}` and every other protection
flag false, compiler construction keeps canonical opcode numbers, sentinel 65535 and plain frame
layout. Wordcode protection passes skip, but expansion supplies the constant key placeholder.
Resolution gives pool `["ok"]`, key zero and the stream `[0,0,0,0,45,0]`: six words.

Transport packs four little-endian bytes per word, so its byte sequence is 24 bytes: four zero
words, then `[45,0,0,0]`, then four zero bytes. Its base64 string is
`AAAAAAAAAAAAAAAAAAAAAC0AAAAAAAAA`. The mode flag is true; boot restores the six words and the
same PCs (LOAD_CONST at 0, RETURN at 4). Case shuffle changes the handler listing order while the
stream's opcode values remain 0 and 45. Profile enables detailed census/size measurements but
adds no wordcode operation. This example explains effects and their ordering; it does not sample
random shuffle outcomes.

## 3. Implementation

### Component contracts

| Component | Input -> output | Consumer dependency |
|---|---|---|
| Configuration boundary | Supplied typed object/default -> same compiler options | No merge/preset/target dispatch is implied. |
| Construction gates | randomize flag -> opcode/sentinel/frame choices | Compiler emission and serialized runtime agree on the same choices. |
| IR scheduler | Enabled flags and private IR -> transformed IR/handler metadata | Mandatory expansion and exact pass order remain independent of flags. |
| Finalization/serialization gates | Concrete operands/options -> pool, words/base64, timing flag, matching maps | Container owns register/frame/transport interfaces; runtime layout owns randomized allocation; timing rule below is exact. |
| Runtime scheduler | AST plus opcode metadata -> matching handlers/dispatch/classes | Added-opcode handler builders precede case/table/class rewrites. |
| Publication/instrumentation | Generated code/options -> `{code,profileData}` or rejected promise | Comments precede minification; ordinary profile fields exist without profile=true. |

### Option gates and effects

In the table, **truthy** means the scheduler's `if (options.<name>)` gate. A called pass can still
find no eligible payload. Omitted/false flags skip their optional stage; this does not mean the
mandatory layer is skipped. Canonical operation meaning is defined in
[instruction-set.md](instruction-set.md#3-implementation).

| Option / type | Gate and position | Result / consequential effect |
|---|---|---|
| target / node or browser | No use beyond the public type | No target-specific runtime or host fallback. Boot uses the same globals/facilities. |
| randomizeOpcodes / boolean | Truthy, Compiler construction | [Layout recipe](transforms/runtime-layout.md): distinct semantic-role values in 0..65535, sentinel in 65535..4294967295 and randomized header/noise/start; separate from case order. |
| [stringConcealing](transforms/shared-string-bank.md) / boolean | Truthy, first optional IR pass | Replaces eligible string LOAD_CONST values with shared bank/helper calls; threads bank captures through required ancestors. No eligible strings can leave the pass inert. |
| [controlFlowFlattening](transforms/state-control-flow.md) / boolean | Truthy, after string concealment | Per-function block/state dispatch plus virtual helper code; can replace ordinary branch layout and add state/cross-block register lifetimes. |
| [dispatcher](transforms/encoded-branch-dispatch.md) / boolean | Truthy, after CFF | Routes eligible branch targets through per-function decode helper and JUMP_REG; target seeds can be encoded label transforms. Helpers/parameter/result plumbing vary. |
| [concealConstants](transforms/keyed-constants.md) / boolean | Expansion always runs here; truthy value gate later in resolveConstants | Constant operands always occupy index/key pairs. Truthy conceals strings and integer Numbers; other entries/key-zero plain path remain. Integer XOR only guarantees int32 value round trip. |
| [antiInstrumentation](transforms/anti-instrumentation.md) / boolean | Truthy, after pair expansion | Fuses selected real effects with fake steps/register state and operand permutations into ANTI handlers; emits its own constant pairs. Can be inert without eligible real effects. |
| [specializedOpcodes](transforms/specialized-opcodes.md) / boolean | Truthy, after anti | Selects eligible canonical operand tuples; marks baked operands as placeholders so serializer omits those words; adds matching handler metadata. |
| [macroOpcodes](transforms/macro-opcodes.md) / boolean | Truthy, after specialized | Fuses repeated eligible canonical instruction sequences and concatenates operand tails; runtime builder additionally requires nonempty MACRO_OPS. |
| [aliasedOpcodes](transforms/aliased-opcodes.md) / boolean | Truthy, after macro | Replaces eligible original fixed-arity operations with duplicates, potentially permuting operand order; added-opcode operations are not automatically alias candidates. |
| [selfModifying](transforms/self-modifying-wordcode.md) / boolean | Truthy, construction after resolveRegisters; encryption after labels/constants | Emits PATCH routes, moved/encrypted regions and decoys/filler. Opaque words are not instruction headers. Runtime PATCH equation is canonical; linked producer recipe supplies selection, routing, junk and encryption boundaries. |
| encodeBytecode / boolean | Truthy at serialization; emitted mode uses boolean coercion | Raw numeric words become base64 of four LE bytes per u32. Boot decodes before execution; PCs remain word indexes. |
| timingChecks / boolean or number | Serializer: number unchanged; exactly true -> 1000; otherwise false. Runtime truthy flag | Millisecond pause test can poison words/current frame state, including slow synchronous host work. See exact execution effect below. |
| shuffleOpcodes / boolean | Truthy, runtime after specialized/macro/alias/anti builders | [Case-shuffle recipe](transforms/runtime-layout.md): permutes @SWITCH cases, including default; numeric maps and words unchanged. |
| [handlerTable](transforms/handler-table.md) / boolean | Truthy, after case shuffle | Lifts cases to prototype handlers and dynamic dispatch; drops switch default, so an absent handler produces TypeError. Root RETURN still stops outer run through cleared current frame. |
| [classObfuscation](transforms/class-runtime.md) / boolean | Truthy, after handlerTable | Inlines immutable scalar/object bindings, renames internal fields/methods, injects/reorders parameters, shuffles declarations/prototype assignments with declaration-before-method and boot ordering. Plain binding spelling can disappear. |
| [minify](transforms/minify-runtime.md) / boolean | Truthy, after generate and comment prefix | Google Closure Compiler ADVANCED/QUIET processes final source; output renaming/folding can remove visible scaffolding/comments. Nonzero process exit rejects. |
| verbose / boolean | Truthy at compiler log calls | Prints compilation/pass/minification messages; not a runtime instruction or a gate on comment emission. |
| profile / boolean | Truthy for detailed bytecodeCounts / runtime fileSize | Adds expensive detailed measurements to profileData; basic timings, sizes, transform entries and handler counts are already populated without it. |

Construction range/layout equations and register/label/pool/transport interfaces are owned by
[container-wordcode.md](container-wordcode.md#3-implementation). The table inventories optional
produced forms, not all eligibility constants, permutation rules or helper equations. The detailed
recipes are the pages linked from the option names.

### Exact scheduling and mandatory layers

The [root workflow](js-confuser-vm.md#compiler-order) owns the complete sequence; these gate
relationships are the option-specific contract:

| Position | Gate interaction / invariant |
|---|---|
| Construction before source lowering | randomizeOpcodes affects canonical values, sentinel and frame layout together; case shuffle is a separate later flag. |
| string -> CFF -> dispatcher | Later passes see helper functions/instructions introduced earlier, not just original source functions. |
| Mandatory expansion -> anti | Expansion always inserts constant placeholders regardless of concealConstants. Anti constructs its own pairs afterward; re-expanding them would double their width. |
| anti -> specialized -> macro -> alias | Each sees the previous output. Specialized only considers original canonical names; macro eligibility also checks canonical names; aliases consider original base values. The full stack is not independent per-option substitution. |
| resolveRegisters -> selfModifying | PATCH producer consumes concrete frame-relative slots; register allocation is mandatory with every option vector. |
| selfModifying -> labels -> constants -> encryptPatches | Address measurement and pool resolution precede encryption; encryption is called only under selfModifying. Both resolution passes are mandatory. |
| serialize -> runtime specialized -> macro -> alias -> anti | Same option gates install the handlers corresponding to metadata produced earlier; macro gate also tests map nonemptiness. Runtime ordering differs from IR anti-first ordering. |
| shuffle -> handlerTable -> class | Handler lifting sees final cases and, when shuffleOpcodes is also truthy, shuffles the extracted assignments again; class rewriting sees generated prototype handlers. |
| generate -> comment prefix -> minify | Comment generation is unconditional, including when encodeBytecode/verbose/profile are false; minification may alter/remove it. |

Calling `concealConstants` does **only** pair expansion. `resolveConstants` later assigns actual
pool values/keys under the value-concealment flag. With false, every pair uses zero; expansion
itself is not an optional protection. Likewise runtime source construction is core: disabling
all optional flags still parses/generates the interpreter and prepends comments.

The explicit **plain reference vector** sets all boolean protection/representation flags false
and timingChecks false; target may be supplied but has no effect, and instrumentation may be false.
It still performs lowering, constant-pair expansion, register/label/constant resolution,
serialization and runtime building, and retains canonical numeric words, pool/key-zero pairs, root
metadata, opcode/sentinel/frame maps and the interpreter. Omitted typed options have the same disabled stage gates because defaults
are empty; no claim of byte-for-byte output equivalence across independent randomized runs is made.

### Timing checks execution effect

Serializer emits a numeric threshold unchanged when `typeof timingChecks === "number"`; emits
1000 for exactly true; otherwise emits false. Runtime always initializes `lastTime=performance.now()`
even with the flag off. When the emitted flag is truthy, each dispatch iteration reads currentTime,
tests `currentTime-lastTime > TIMING_CHECKS` (strict greater-than), and updates lastTime. A long
host call/finalizer/debugger pause is observed at the next iteration, not in an interrupt timer.
Zero disables the branch through truthiness; negative numbers are not clamped and can trigger
immediately. The typed numeric path has no finite/positive validation.

On a detected pause the runtime performs these operations **before** the handler try/catch:

```text
for i in [0, bytecode.length): bytecode[i] = 0
for i in [currentFrame, regsTop): regs[i] = undefined
op = OP.JUMP
regs[currentFrame + SLOTS.PC] = bytecode.length
continue into the ordinary dispatch try/catch for that forced JUMP
```

This is destructive state poisoning, not an explicit success return or a clean halt primitive.
In the canonical switch, forced JUMP still calls read() at the end of the stream, obtains undefined
and sets PC to undefined. The following fetch can therefore reach the unknown-opcode error with
current-frame handler metadata already erased. Do not restate the source comment's intended
"halt" as a guaranteed normal completion/cleanup contract. There is no ordinary capture-close or
RETURN clearing/result sequence in the poisoning branch. Added/reshaped runtime paths require
separate interaction evidence; timing checks do not promise preservation after their trigger.

### Publication, state and testing

The public call constructs a fresh compiler and returns only after all selected passes and final
source generation/minification succeed. It mutates its private IR/descriptors/maps during the
pipeline; there is no partial code result, resume protocol or speculative rollback. Runtime
parse/generate/minify errors are wrapped as `VM-Runtime final parsing/generation/minification failed`
with their cause. A failure rejects instead of publishing `{code,profileData}`.

Every performed pass populates its transform profile entry. Detailed bytecodeCounts are null when
profile is false, while detailed runtime fileSize is null; other ordinary measurements remain.
The profile reflects compilation rather than generated-program execution. Runtime class/minifier
changes may remove plain names, but their matching data/handler roles must survive. Optional
side effects such as PATCH writes and timing poisoning are runtime behavior, not compilation
profile state.

| Scenario | Observable result / oracle | Acceptance criterion | Fixture |
|---|---|---|---|
| O1: empty / explicit-false configuration | Actual scheduler calls, canonical data and key-zero pool agree with gates above. | Expansion/resolution/runtime building remain; no hidden true defaults or target effect. | none |
| O2: randomize versus shuffle | Canonical-name map/frame values versus physical case order are separate observations. | Values distinct/in range under randomize; case shuffle leaves word semantics unchanged. | randomizedOpcodes, shuffleOpcodes |
| O3: eligible / ineligible IR protection | Payload/handler metadata occurs when pass finds eligible work; result matches declared source oracle. | Enabling a flag does not establish every candidate or every combination; shared helpers/captures stay coherent. | per-option tests (string, CFF, dispatcher, constants, added opcodes, selfModifying) |
| O4: transport / late runtime forms | Selected raw/base64 and switch/table/class/minified source matches stage contract and expected program effects. | LE round trip and matching handlers; final source generation failures publish no successful result. | encodeBytecode, handlerTable, classObfuscation |
| O5: timing / debugger | Controlled clock deltas reach strict threshold check; inspect exact poisoned words/frame/PC. | Equal threshold does not trigger; greater does; observe failure/cleanup rather than presume halt. | none |
| O6: instrumentation | Logs and profile fields agree with gates; program behavior unchanged in a frozen configuration. | profile changes detail fields, verbose changes logs; comments emitted independent of both. | profile |
| O7: combined ordering | Same exact configured program exercises actual added handlers and late representations. | Each tested combination retains source/options/output and matching runtime provenance; no inference from an all-on flag list. | antiInstrumentation, randomizedOpcodes, classObfuscation combined cases |

A control must assert the named decision or representation, not only a successful eval or a
comment signature. Matching comments can outlive runtime changes; the generated data/handlers
and behavior need their own observations.

## 4. Later Stages

| Stage / interaction | Later consumer effect |
|---|---|
| String/control rewriting before augmentation | Added helpers and changed branch instructions influence augmentation eligibility and register lifetimes. |
| Constant pairs before augmentation | Baked/permuted/fused operands include both index and key words; false concealment does not shrink width. |
| Specialized before macro/alias | Consumed original operations may no longer be candidates for later added opcodes; runtime has to install the handlers of every selected option. |
| PATCH after register resolution / encryption last | Final words, including pool keys/addresses, feed encrypted regions; serializer treats opaque words separately from opcode naming. |
| Added runtime handlers before case/table/class passes | Later representations can hide original switch cases and plain data binding names. |
| Class before minify | Inlined maps/scalars and renamed/shuffled methods are input to final ADVANCED compilation; plain source patterns need not survive. |
| DEBUGGER or synchronous host work before next clock check | Can exceed timing threshold; behavior then follows poisoning rather than ordinary source completion. |

These are encoder-emitted alternatives. The canonical contract still explains operations once
supplied their actual operands/values; it does not define added-opcode grammars or every late
AST spelling; the linked mechanism pages own those.

## 5. Known Quirks

- `target` is a no-effect selector. The same runtime requires host facilities such as performance,
  Reflect, WeakMap and base64 support where used; the option does not polyfill them.
- Some transform comments describe an obsolete placement after selfModifying; the scheduler
  order above is authoritative. Specialized comments describe a single integer operand or a
  repetition threshold while actual selection processes eligible operand tuples; no simplified
  comment is used here as a detailed recipe.
- Concealment selects every integer Number but uses signed int32 XOR; values outside that domain
  can change. Timing poisoning is explicitly destructive. No universal preservation claim is made.
- Enabled flag does not mean payload emitted: candidate eligibility, original-name restrictions,
  prior passes and random choices matter.

## Source

All links are pinned. Public default forwarding and the typed/empty-default contract in item 1 are
[index.ts#L7-L13](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/index.ts#L7-L13)
and [options.ts#L1-L100](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/options.ts#L1-L100).
Construction gates are
[compiler.ts#L353-L417](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/compiler.ts#L353-L417)
and [frame-layout.ts#L30-L107](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/utils/frame-layout.ts#L30-L107).
The exact order in items 2-4 is wired by
[compiler.ts#L3276-L3458](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/compiler.ts#L3276-L3458)
and [build-runtime.ts#L17-L124](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/build-runtime.ts#L17-L124).
Serialization gates and timing emission are
[compiler.ts#L3198-L3272](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/compiler.ts#L3198-L3272);
the timing runtime effect is
[runtime.ts#L225-L269](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/runtime.ts#L225-L269)
and [runtime.ts#L546-L548](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/runtime.ts#L546-L548).

The effect inventory is traceable to these producers/consumers:

| Mechanism | Wordcode producer / runtime consumer |
|---|---|
| Mandatory pairs / value concealment | [concealConstants.ts](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/transforms/bytecode/concealConstants.ts), [resolveConstants.ts](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/transforms/bytecode/resolveConstants.ts); [runtime.ts#L182-L203](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/runtime.ts#L182-L203). |
| Shared string bank | [stringConcealing.ts](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/transforms/bytecode/stringConcealing.ts). |
| CFF / dispatcher | [controlFlowFlattening.ts](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/transforms/bytecode/controlFlowFlattening.ts), [dispatcher.ts](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/transforms/bytecode/dispatcher.ts). |
| Anti | [bytecode/antiInstrumentation.ts](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/transforms/bytecode/antiInstrumentation.ts), [runtime/antiInstrumentation.ts](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/transforms/runtime/antiInstrumentation.ts). |
| Specialized | [bytecode/specializedOpcodes.ts](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/transforms/bytecode/specializedOpcodes.ts), [runtime/specializedOpcodes.ts](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/transforms/runtime/specializedOpcodes.ts). |
| Macro | [bytecode/macroOpcodes.ts](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/transforms/bytecode/macroOpcodes.ts), [runtime/macroOpcodes.ts](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/transforms/runtime/macroOpcodes.ts). |
| Aliases | [bytecode/aliasedOpcodes.ts](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/transforms/bytecode/aliasedOpcodes.ts), [runtime/aliasedOpcodes.ts](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/transforms/runtime/aliasedOpcodes.ts). |
| Self-modification | [selfModifying.ts](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/transforms/bytecode/selfModifying.ts), [encryptPatches.ts](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/transforms/bytecode/encryptPatches.ts); [runtime.ts#L879-L892](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/runtime.ts#L879-L892). |
| Case / dispatch / class representation | [shuffleOpcodes.ts](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/transforms/runtime/shuffleOpcodes.ts), [handlerTable.ts](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/transforms/runtime/handlerTable.ts), [classObfuscation.ts](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/transforms/runtime/classObfuscation.ts). |
| Final minification | [minify.ts](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/minify.ts). |

These files verify inventory claims in items 3-5; linked mechanism pages own detailed decisions.

## Fixtures

The encoder's committed option tests below exercise the scenarios in
[Publication, state and testing](#publication-state-and-testing). They generate output at test time through [test-utils.js](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/test/test-utils.js); explicit options replace the global
test profile rather than merge into it. No generated output is retained in this package.

| Committed test | Scenario | What it asserts |
|---|---|---|
| [randomizedOpcodes.test.js](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/test/options/randomizedOpcodes.test.js), [shuffleOpcodes.test.js](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/test/options/shuffleOpcodes.test.js) | O2 | Changed map/case listing; decoy presence and selected combined behavior. |
| [concealConstants.test.js](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/test/options/concealConstants.test.js), [stringConcealing.test.js](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/test/options/stringConcealing.test.js) | O3 | Hidden selected literals and expected values; helper source-location boundary. |
| [controlFlowFlattening.test.js](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/test/options/controlFlowFlattening.test.js), [dispatcher.test.js](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/test/options/dispatcher.test.js) | O3 | Comment markers and selected branch behavior; dispatcher on/off comparison. |
| [antiInstrumentation.test.js](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/test/options/antiInstrumentation.test.js), [specializedOpcodes.test.js](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/test/options/specializedOpcodes.test.js), [macroOpcodes.test.js](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/test/options/macroOpcodes.test.js), [aliasedOpcodes.test.js](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/test/options/aliasedOpcodes.test.js) | O3, O7 | Named added-opcode comments plus selected values; one combined anti stack. |
| [selfModyfing.test.js](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/test/options/selfModyfing.test.js) | O3 | PATCH marker and a selected program result. |
| [encodeBytecode.test.js](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/test/options/encodeBytecode.test.js), [handlerTable.test.js](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/test/options/handlerTable.test.js), [classObfuscation.test.js](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/test/options/classObfuscation.test.js) | O4, O7 | Transport, table/off forms, inlined maps, prototype alias ordering and selected combined behavior. |
| [profile.test.js](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/test/options/profile.test.js) | O6 | Detailed fields and one configured program value. |
| none | O1, O5 | No committed test. |

The item 2 example supplies checkable word/byte/base64 arithmetic; it does not sample shuffling.
