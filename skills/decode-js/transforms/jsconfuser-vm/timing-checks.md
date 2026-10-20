# Timing checks

## 1. Target

Timing checks are interpreter-only anti-debugging: between instructions the interpreter reads the
host clock and poisons its own state when execution was slow
([encoder execution effect](../../../js-confuser-vm/options.md#timing-checks-execution-effect)).
The words and the pool carry none of it. Decoding removes the interpreter, so every timing value
decodes to the program the disabled runtime decodes to, and the decoded program behaves as the
source under fast, slow and paused execution. Timing is decoded, never refused.

Readers need the [container roles](extract-container.md) and the encoder's timing effect above.
This is not a claim about native operation, call, capture or terminal-kind limits in E/H/F/G/J/M;
`finalJavaScriptSemantics` stays false.

## 2. Algorithm

No decode stage reads the timing scalar or the clock. Packet A locates the payload by the boot
skeleton, the [handler locator](locate-handlers.md) enters the interpreter from the same skeleton,
and neither selects the dispatch shell, the timing comparison or the frame finalizers that the
check sits beside. Only the interpreter changes with the threshold, so the payload, and with it
the decode, is the disabled one.

For example, a virtual function captures r0=7 in an escaped closure and calls a host pause while
its parent has installed a finally region. With threshold 100 ms and a single 250 ms pause, the
encoded program poisons its current frame at the next instruction: the capture's backing register
reads undefined, caller traversal loses the parent, the finally marker is never set, and an
unknown-opcode error reaches the host. With timing disabled the same source returns 7, runs
finally and closes the cell with 7. The decoded program has no interpreter, so it returns 7 and
runs finally under the same pause: the protection is removed, which is the decoder's purpose.

## 3. Implementation

| Source shape | Public decode |
|---|---|
| `false`, `0`, `-0` | Decodes. |
| Any other threshold the serializer emits (finite, negative, `true` as 1000) | Decodes to the disabled program. |

**Host and state boundary.** Even disabled timing calls `performance.now` once per run, including
host-entered closure sub-VMs; recovered JavaScript omits that bookkeeping. Native qualification
assumes a callable, nonthrowing host clock whose reads have no source-visible side effects.
Missing or throwing clocks, clock getters or counters visible to the program and adversarial clock
globals are excluded from equivalence.

### Testing and acceptance

| Scenario | Oracle | Criterion | Fixture |
|---|---|---|---|
| T1: every timing value | Output equals the disabled decode. | Values false, 0, -0, 100, 1000, -1 on the reference. | runtime-finalizers.test.js. |
| T2: active timing with transport or table | Output equals the disabled decode. | Encoded payload and handler table. | runtime-finalizers.test.js. |
| T3: behaviour under real pauses | Decoded output behaves as the source under fast, slow and supervised pause; the encoded active program poisons. | Equal threshold does not trigger; a single greater delta does. | runtime-finalizers.test.js, runtime-finalizers.behavior.test.js. |
| T4: fresh population | Every cell recovers; triggers observed where timing is on. | [Finite timing qualification](../../tests.md#finite-timing-and-finalizer-qualification). | timing.mjs. |

## 4. Input Shapes

| Input spelling | Producer | Handling |
|---|---|---|
| Numeric threshold or `false` in a top-level binding | timingChecks, encoder | Not read. |
| Timing with encodeBytecode, handlerTable, PATCH stacks | encoder | Payload and handlers as without timing. |

## 5. Known Gaps

- A top-level normal-continuation try/finally around a child call is outside the emission proof
  (`unemittable-structured-control`: FINALLY_SETUP has no proved return continuation). It is
  independent of timing; the retained `top-level-finally` input pins it.
- Minified, class and randomized timing stacks are not in the timing population.

## Source

No decoder module reads timing. The pinned interpreter source is
[runtime.ts](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/runtime.ts#L202-L279)
and scalar serialization
[compiler.ts](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/compiler.ts#L3233-L3242).
The qualification tools are
[timing.mjs](../../../../decoder/decode-js/scripts/qualify-jsconfuser-vm/timing.mjs) and
[timing-observation.mjs](../../../../decoder/decode-js/scripts/qualify-jsconfuser-vm/timing-observation.mjs).

## Fixtures

| Committed fixture or test | Claim pinned |
|---|---|
| [runtime-finalizers.test.js](../../../../decoder/decode-js/test/vm/jsconfuser-vm/runtime-finalizers.test.js), on the reference, encoded arithmetic and handler-table boot fixtures | T1, T2; a renamed Upvalue close method still decodes and behaves as the source; T3 thresholds on the encoded program. |
| [retained timing inputs](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/runtime-finalizers/generation.json), [source](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/runtime-finalizers/finalizers.src.js) and [oracle](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/runtime-finalizers/oracle.json) | Seed 231 baseline/timing, full PATCH pair, base64 pair and handler-table pair. |
| [runtime-finalizers.behavior.test.js](../../../../decoder/decode-js/test/vm/jsconfuser-vm/runtime-finalizers.behavior.test.js) | T3 on every retained profile, with an independent PATCH B-E rebuild. |
| [top-level-finally.js](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/runtime-finalizers/top-level-finally.js) and its [source](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/runtime-finalizers/top-level-finally.src.js) | The known gap: A admits, public decode declines with the exact input and the named FINALLY_SETUP continuation. |
