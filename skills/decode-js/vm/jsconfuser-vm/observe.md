# The `observe` module

Module of the jsconfuser-vm decoder ([map](../../pipelines/jsconfuser-vm.md#modules)); code in
[`src/vm/jsconfuser-vm/observe/`](../../../../decoder/decode-js/src/vm/jsconfuser-vm/observe/).
It has no sub-docs.

## 1. Target

`observe` turns the [classes](handlers/identify-handlers.md#exports-another-file-imports) of the
handlers an added-opcode option put into the interpreter into the definitions a stream reader
needs: for each added opcode, how many words it takes and which canonical instructions it stands
for.

It reads:

- the input program, as source text or a parsed tree, through the
  [identified handler view](handlers/identify-handlers.md);
- the observations of the options allocated before the one being observed, when the caller
  passes them.

It provides, one observer per option:

- **anti**: each synthetic case's stored operand order and its steps as operand spans;
- **specialized**: each specialized opcode's original opcode and baked operands;
- **macro**: each macro opcode's canonical steps;
- **aliased**: each alias opcode's original opcode and operand order;
- for a stream that PATCH decoding has yet to read, all four at once.

It never:

- reads the word stream. Whether an added opcode is used, and where, is the stream reader's
  question ([read-wordcode](wordcode/read-wordcode.md#added-opcode-instructions)); the module
  imports nothing from `wordcode/`;
- decides which step of a synthetic case is real: that needs the registers in the stream and
  belongs to [normalize-anti-wordcode](normalize-anti-wordcode.md);
- rewrites words. The `recover-added-opcodes` transforms do, each from its observation;
- proves the canonical handlers right. Added handlers are compared with the interpreter's own
  canonical handlers, so damage copied into both is not seen here.

## 2. Algorithm

The encoder allocates the added opcodes in a fixed order: anti, specialized, macro, alias
([compiler order](../../../js-confuser-vm/js-confuser-vm.md#compiler-order)). Each later option
builds its handlers from the earlier ones' output, so one interpreter can hold handlers of
several kinds, and an observer must say what it does with handlers that are not its own.

```text
observe<Kind>(input, options):                       // explanatory pseudocode
  ast  = input parsed, or taken as a tree            else invalid-input
  view = the identified handler view                 else <kind>-runtime-container
  canonical, extra = view.handlers split by the opcode table
  require every table entry has a canonical handler, and extra is non-empty
  mine = the extra handlers the classifier gave this kind
  for each: require it leaves the dispatch (`ends`); apply the kind's own checks; make its record
  require mine is non-empty
  require the other extra handlers are accounted for:
    by the earlier observations passed in (their counts), or
    by an option that says a later observer will prove the rest
                                                     else "Unproved extra opcode cases remain"
  publish the observation, deeply frozen
```

Labels and their order are never read: a handler's kind comes from its effects alone.

| Observer | Its handlers | Own checks | Handlers it may leave |
|---|---|---|---|
| anti | Class `anti`: canonical steps in sequence, all operands read up front into one array | At least 3 steps | With `allowSpecializedTail`, any; otherwise none |
| specialized | Class `specialized`: one canonical handler, every operand a literal | Every baked operand is an integer in 0..0xffffffff, since it becomes a word | With `allowAntiPrefix`, the handlers of class `anti`; with `allowMacroTail`, any; otherwise none |
| macro | Class `macro`: canonical steps in sequence, operands read as used | 2 to 5 steps; reads in order 0, 1, 2, ...; no step is `PATCH`, `TRY_SETUP`, `TRY_END`, `DEBUGGER` or `MAKE_CLOSURE`; `RETURN`, `CALL`, `CALL_METHOD`, `NEW`, `THROW`, `JUMP`, `JUMP_IF_FALSE`, `JUMP_IF_TRUE`, `FOR_IN_NEXT` and `FINALLY_SETUP` only as the last step | As many as the anti and specialized observations passed in hold; with `allowAliasTail`, any |
| aliased | Class `alias`: one canonical handler, its operands read in another order | None | Exactly as many as the anti, specialized and macro observations passed in hold |

The macro exclusions are the encoder's own selection rule; `JUMP_REG` is absent from both lists
because the encoder omits it. The anti observer derives its record from the classifier's steps:
because every operand is read up front, a step's reads are stored positions, so
`canonicalToStored` is the steps' reads in order and each step owns the next contiguous span of
canonical operands.

**All four for a PATCH-decoded stream.** Decrypting self-modifying regions needs every added
opcode's width before any stream can be read whole, so `diagnosePatchAddedOpcodes` runs the
observers in allocation order, each allowed to leave a tail, and passes each result to the next:

```text
anti        = observe anti, tail allowed
specialized = observe specialized, anti prefix if anti was found, tail allowed
macro       = observe macro with (anti, specialized), tail allowed
alias       = observe aliased with (anti, specialized, macro)
complete    = alias if it succeeded; else the innermost of macro, specialized, anti that
              succeeded, observed again with no tail allowed
if complete refused: that refusal
if nothing was observed and the interpreter still has added handlers:
    refuse patch-added-opcode-runtime                // an unproved handler is not forgotten
return {anti, specialized, macro, alias}             // null where an option is absent
```

The last observer in the chain must account for every remaining handler; an earlier one may stop
at a later option's handlers.

### Worked example

Cell `minify-over-aliased-opcodes`: source `composition-finally-abrupt-return`, profile
`randomizeOpcodes+aliasedOpcodes+minify`, seed 251. The interpreter has 76 handlers: 61 canonical
and 15 added, all classified `alias`. The handler labelled 48718 is the alias of `LOAD_GLOBAL`
(label 35951) worked through in
[identify-handlers](handlers/identify-handlers.md#worked-example-load_global-and-its-alias-under-minify).
`diagnoseAliasedRuntime(source)` publishes:

```text
schemaVersion: 'jsconfuser-vm-aliased-runtime-observation.v1'
antiPrefixCount: 0, specializedPrefixCount: 0, macroPrefixCount: 0
aliases: 15 records, among them
  { opcode: 48718, originalOpcode: 35951, originalName: 'LOAD_GLOBAL', arity: 3,
    canonicalToStored: [1, 0, 2] }
```

A stream word 48718 therefore takes three operand words, and `LOAD_GLOBAL`'s operands 0, 1, 2
are the stored words 1, 0, 2. On the same source the anti observer refuses, "No synthetic opcode
prefix was emitted", and `diagnosePatchAddedOpcodes` returns
`{anti: null, specialized: null, macro: null, alias: <the observation>}`.

## 3. Implementation

### Exports another file imports

| Export | File | Options | Imported by |
|---|---|---|---|
| `diagnoseAntiRuntime(input, options)` | `observe-anti-runtime.js` | `allowSpecializedTail = false` | `normalize-anti-wordcode`, `normalize-specialized-wordcode`, `normalize-macro-wordcode`, `normalize-aliased-wordcode` |
| `diagnoseSpecializedRuntime(input, options)` | `observe-specialized-runtime.js` | `allowAntiPrefix = false`, `allowMacroTail = false` | `normalize-specialized-wordcode`, `normalize-macro-wordcode`, `normalize-aliased-wordcode` |
| `diagnoseMacroRuntime(input, options)` | `observe-macro-runtime.js` | `antiObservation = null`, `specializedObservation = null`, `allowAliasTail = false` | `normalize-macro-wordcode`, `normalize-aliased-wordcode` |
| `diagnoseAliasedRuntime(input, options)` | `observe-aliased-runtime.js` | `antiObservation = null`, `specializedObservation = null`, `macroObservation = null` | `normalize-aliased-wordcode` |
| `diagnosePatchAddedOpcodes(source)` | `observe-patch-added-opcodes.js` | none; `source` is text | `normalize-self-modifying-wordcode` |

Each returns `{ok, result, diagnostic}`; the four per-option results are deeply frozen. `input`
is source text or a Babel `File` or `Program` (`runtimeAst`,
[container](source/container.md#exports)).

### Observations

Every schema name has the prefix `jsconfuser-vm-`.

```text
anti-runtime-observation.v1
  syntheticCases [{ opcode, arity, canonicalToStored,
                    steps [{ name, operandStart, operandCount }] }]

specialized-runtime-observation.v1
  antiPrefixCount
  specialized [{ opcode, originalName, originalOpcode, operands }]

macro-runtime-observation.v1
  antiPrefixCount, specializedPrefixCount
  macros [{ opcode, steps [{ name, opcode }] }]

aliased-runtime-observation.v1
  antiPrefixCount, specializedPrefixCount, macroPrefixCount
  aliases [{ opcode, originalOpcode, originalName, arity, canonicalToStored }]
```

`opcode` is the added handler's label; `originalOpcode`, and a macro step's `opcode`, are the
label of the canonical handler in this build. `arity` is the number of operand words after the
opcode. `canonicalToStored[j]` is the stored position canonical operand `j` takes. A specialized
case's `operands` are the baked words in the original's operand order.

### Refusals

Owner `container` ([Refusals](../../pipelines/jsconfuser-vm.md#refusals)); `<kind>` is `anti`,
`specialized`, `macro` or `alias`.

| Code | When |
|---|---|
| `invalid-input` | The input is neither text nor a tree |
| `<kind>-runtime-container` | The interpreter's handlers are not located |
| `<kind>-runtime` | A table entry without a canonical handler; no added handler; none of this kind; a handler of this kind that does not leave the dispatch; a specialized operand that is not a word; a macro breaking its checks; "Unproved extra opcode cases remain" |
| `anti-runtime-steps` | A synthetic case with fewer than 3 steps |
| `<kind>-runtime-error` | Any other error |
| `patch-added-opcode-runtime` | From `diagnosePatchAddedOpcodes`: no option was observed and added handlers remain; or the locator's own code when it refuses there |

## 4. Dependencies

| Imports | For |
|---|---|
| [`handlers`](handlers.md): `requireIdentifiedHandlers`, `partitionHandlers`; `locateHandlers`, `behaviourTable` | The identified view and its split; the PATCH observer's check for left-over added handlers |
| [`source`](source.md): `runtimeAst`, `decline`, `accepted`, `refused`, `PARSER_OPTIONS` | The input, the `container` refusal |
| `src/vm/decline.js` (`deepFreeze`), `@babel/parser` | Freezing; the PATCH observer's parse |

The rule is one-way: `observe/` imports `handlers/` and `source/` and nothing from `wordcode/`
or the transforms; the `normalize-*` transforms of the `recover-patch` and
`recover-added-opcodes` stages import it
([imports chart](../../pipelines/jsconfuser-vm.md#imports)).

## 5. Known Gaps

- Each observer parses the input and identifies the handlers again; a route that runs four
  observers builds four views.
- A tail option says only that some later observer will prove the rest; the observer that sets
  it cannot check that one does. The transform that sets it owns that proof.
- The macro observer's step limits restate the encoder's selection rule; a macro outside them
  refuses even though the classifier decomposed it.
- No committed case damages an added handler: every refusal above is reached only by inputs the
  encoder does not emit.

## 6. Source

- [observe-anti-runtime.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/observe/observe-anti-runtime.js),
  [observe-specialized-runtime.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/observe/observe-specialized-runtime.js),
  [observe-macro-runtime.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/observe/observe-macro-runtime.js),
  [observe-aliased-runtime.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/observe/observe-aliased-runtime.js):
  one observer each.
- [observe-patch-added-opcodes.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/observe/observe-patch-added-opcodes.js):
  all four in allocation order.
- The encoder's added handlers:
  [anti-instrumentation](../../../js-confuser-vm/transforms/anti-instrumentation.md),
  [specialized opcodes](../../../js-confuser-vm/transforms/specialized-opcodes.md),
  [macro opcodes](../../../js-confuser-vm/transforms/macro-opcodes.md),
  [aliased opcodes](../../../js-confuser-vm/transforms/aliased-opcodes.md).

## 7. Fixtures

Suites encode their sources with the pinned encoder and require the decode to behave as the
source ([tests.md](../../tests.md)). No unit test enters the module directly.

| Scenario | Expected result | Committed fixture |
|---|---|---|
| Anti handlers whose operands are stored permuted | `canonicalToStored` is the stored order; sorting it turns the suite red | `anti-instrumentation` in [single-payload-stage](../../../../decoder/decode-js/test/vm/jsconfuser-vm/cell-suites/single-payload-stage/suite.js) |
| Anti handlers with several steps | Each step owns its own operand span; giving every step span 0 turns the suite red | `anti-instrumentation` in single-payload-stage |
| Specialized handlers | The baked operands become the expanded instruction's words; zeroing them turns the suite red | `specialized-opcodes` in single-payload-stage |
| A specialized operand above 0x7fffffff, under the anti and concealed-constant stack | Accepted as a word; a 31-bit limit turns the suite red | [all-stages-together](../../../../decoder/decode-js/test/vm/jsconfuser-vm/cell-suites/all-stages-together/suite.js) |
| Anti, specialized, macro and alias handlers in one interpreter | Only handlers of class `alias` count as aliases; counting every added handler turns the suite red | [added-opcodes-chain](../../../../decoder/decode-js/test/vm/jsconfuser-vm/cell-suites/added-opcodes-chain/suite.js) |
| An added handler of no class | "Unproved extra opcode cases remain" | |
| A macro whose non-final step is a jump | `macro-runtime` | |
