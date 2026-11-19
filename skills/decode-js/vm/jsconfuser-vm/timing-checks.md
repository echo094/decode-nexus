# Timing checks

Pipeline stage: none; nothing reads the timing scalar
([map](../../pipelines/jsconfuser-vm.md#frontend-order)).

Readers need the encoder's
[timing checks](../../../js-confuser-vm/options.md#timing-checks-execution-effect) and the
[container record](source/container.md#the-container-record).

## 1. Target

Timing checks are a protection of the interpreter alone. With the option on, the interpreter reads
the host clock before every instruction and, when more time passed than the threshold allows,
zeroes its own word stream and the current frame. The compiled program is not changed: the words
and the constant pool are those of the same build without the option.

The decoder reads the words and the pool and writes no interpreter, so an input with timing checks
decodes to the program its build without them decodes to. The check is removed with the
interpreter, not inverted. The decoded program has no clock read, and behaves as the source
whether it runs fast, slowly or under a debugger's pause.

This doc has no code. It records why none is needed, and which inputs show it.

## 2. Algorithm

The option adds three things to the encoded source, all in the interpreter:

```text
var TIMING_CHECKS = 1000;                        // the threshold in ms; false when the option is off
lastTime = performance.now()                     // once per run, also with the option off
if (TIMING_CHECKS) {                             // in the dispatch loop, before each handler
  isTamper = currentTime - lastTime > TIMING_CHECKS
  ...                                            // on tamper: zero the words and the frame,
                                                 // force a JUMP past the end
}
```

The decoder touches none of them:

1. **The container.** The payload is found from the boot skeleton and the opcode table from the
   handlers ([`container`](source/container.md)). The `TIMING_CHECKS` binding is not a role
   the search looks for, and no code names it. The record's
   `scalars.TIMING_CHECKS` is the constant `false`, whatever the source holds.
2. **The handlers.** [`locate-handlers`](handlers/locate-handlers.md) enters the dispatch and
   takes each opcode's handler body. The timing comparison stands in the loop before the
   dispatch, outside every handler, so no handler's behaviour changes and every opcode is named
   as without the option.
3. **Everything after** reads the container, the words and the pool only.

The result is that the decode cannot depend on the threshold. Its value (a number, or `true`
written as 1000) is spelling to the decoder
([F4](../../../decoding-method/rules.md#f4)), and
dropping the check is the purpose of decoding, not a loss
([Reversibility](../../pipelines/jsconfuser-vm.md#reversibility-by-encoder-step), step 16).

### Worked example

The committed cell `composition-finally-abrupt-return` of suite `interpreter-rewrite-fixed`
(profile `randomizeOpcodes+timingChecks`, seed 251), beside the same source and seed under
`randomizeOpcodes` alone (suite `compiled-forms`, file `control-try`).

| | `randomizeOpcodes` | `randomizeOpcodes+timingChecks` |
|---|---|---|
| The binding in the encoded source | `var TIMING_CHECKS = false;` | `var TIMING_CHECKS = 1000;` |
| Words and pool of the container | | equal to the left, word for word |
| `scalars.TIMING_CHECKS` of the container | `{ name: null, value: false }` | `{ name: null, value: false }` |
| Decoded output | | equal to the left, byte for byte |

With one seed the two builds have the same opcode values and the same words; only the
interpreter text differs.

## 3. Implementation

### Exports another file imports

None. No file of the decoder names the timing scalar except
`source/minified-runtime-container.js`, which writes the constant `TIMING_CHECKS: false` into
every container record; nothing reads that field.

### Decisions

| Threshold in the source | Decode |
|---|---|
| `false`, `0`, `-0` (the check is off) | the program |
| Any other number the serializer writes (positive, negative, `true` as 1000) | the same program |

- **Never refused.** A threshold is no reason to decline: nothing the decoder needs depends on it.
- **The host clock.** The interpreter calls `performance.now` once per run even with the option
  off, and once per instruction with it on. The decoded program calls it never. The two agree
  for a host whose clock is callable, does not throw and has no effect the program can see; a
  missing or throwing clock, or one the program instruments, is outside the equivalence the
  decoder claims.
- **After a trigger.** Once the check fires, the encoded program's behaviour is the
  interpreter's poisoning, which the source never had. The decode keeps the behaviour source and
  encoded program share ([F8](../../../decoding-method/with-encoder.md#f8)),
  which is the run where the check does not fire.

### Refusals

None.

## 4. Input Shapes

| Shape | Producer | Treatment |
|---|---|---|
| `var TIMING_CHECKS = <number or false>;` at the top of the runtime | encoder step 16 `serializer.serialize` | not read |
| The clock read and the comparison in the dispatch loop | the runtime template | outside every handler; not read |
| The same under `handlerTable`, `classObfuscation`, `minify`, `encodeBytecode` or a PATCH stack | encoder steps 12, 15, 16, 22, 23, 25 | each is read as without timing, by its own doc |

## 5. Known Gaps

- No committed test compares a timing cell's decode with its plain decode; the cells assert
  behaviour, which holds for either. The worked example's equality is read by hand.
- Only the threshold 1000 has a cell. Other values rest on the argument above: the scalar is not
  read.
- No test runs a decoded program under a slow or paused clock. The cell tests run the encoded
  program on the real clock and expect the source's behaviour, so they rely on no pause above
  the threshold during a run.

## 6. Source

No decoder file. The encoder's
[interpreter loop](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/runtime.ts#L202-L279)
holds the check, and its
[serializer](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/compiler.ts#L3233-L3242)
writes the scalar.

## 7. Fixtures

Each suite encodes its sources with the pinned encoder and requires the decode to behave as the
source ([tests.md](../../tests.md#suites)). Suites are under
[cell-suites/](../../../../decoder/decode-js/test/vm/jsconfuser-vm/cell-suites/). None has a
proof for timing, since there is no timing code to break.

| Scenario | Expected result | Committed fixture |
|---|---|---|
| Timing on, nothing else | Decodes; behaves as the source | `interpreter-rewrite-fixed`, the `randomizeOpcodes+timingChecks` cell (the worked example) |
| Timing under a rewritten interpreter (handler table, class, minify) | Decodes; behaves as the source | `timing-runtime-chain` (its proof is [`lower-switch-model`](lower-switch-model.md)'s) |
| Timing with every other option | Decodes; behaves as the source | `all-stages-together` |
| The decode equals the decode without timing | Equal output | |
| A threshold other than 1000 | The same decode | |
| The decoded program under a pause longer than the threshold | Behaves as the source | |
