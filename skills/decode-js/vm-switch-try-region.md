# Try-statement regions in structured emission

The shared switch backend's structured emitter recovers every try statement through one rule.
Read [vm-switch-boundary.md](vm-switch-boundary.md) for the backend this rule is part of.

## 1. Target

Recover every try statement the pinned js-confuser-vm compiler emits as a native JavaScript
`try` statement: catch only, finally only, catch and finally, nested in any combination, and
left by any completion: normal, `return`, `break`, `continue`, a caught or an uncaught throw.
The rule reads blocks only. It never asks whether a jump target is a loop header, a loop exit or
a switch exit; such a target is handed to the enclosing construct unchanged. A model that is not
compiler grammar (a damaged target, a carrier captured by a closure, an edge with a wrong state,
code after a pop that is not a transfer) declines atomically with `unemittable-structured-control`.

Readers need the [region grammar the compiler emits](../js-confuser-vm/instruction-set.md#catch-finally-and-abrupt-completion),
stage E's [exception edges](transforms/jsconfuser-vm/build-cfg.md) and K's
[structured control](transforms/jsconfuser-vm/structured-control.md).

## 2. Algorithm

### Regions are delimited by their head and tail instructions

Only the compiler's region code produces these instructions, and it produces them at fixed
places, so a region's boundaries are read from block heads and tails instead of from the
region's overall shape.

| Boundary | Signature (typed operation) | Meaning |
|---|---|---|
| Region head | block ending in `catch-setup(target, exceptionRegister)` | catch region opens; catch entry is `target` |
| Region head | block ending in `finally-setup(target, continuation, payload, throwPad)` | finally region opens; in try/catch/finally it encloses one catch head |
| Catch head | the catch-setup target | entered by an exception raised inside the region, by its own setup (the try statement is one unit, so the armed handler is reachable with it even when no program operation in the body can throw; [build-cfg.md](transforms/jsconfuser-vm/build-cfg.md)), or, for an empty catch body, by the region's own exit jumps, since it is then the continuation |
| Finalizer head | the finally-setup target | entered by every exit of the finally region |
| Exit tail, catch | `handler-pop`, then a transfer | leaves the catch region: to its continuation (normal completion) or to an outer target |
| Exit tail, finally | optional `assign payload = value`, then `assign continuation = literal` and `handler-pop`, then `jump` to the finalizer head; [jump steps](vm-switch-boundary.md#1-target) may sit between any two | leaves the finally region; the literal names the exit. Normal completion pops first, a routed exit loads the literal first |
| Finalizer tail | `indirect-jump` on `continuation` | resumes at one of E's finite targets |
| Throw pad | `throw payload` | rethrows the pending exception |
| Return pad | `return payload` | completes a routed return |
| Other pad | a transfer in the enclosing context | continues a routed break/continue |

A `break`, `continue` or `return` that crosses several regions emits one catch tail per crossed
catch region and stops at the first finally region, whose pad continues the unwind outward. So
reading tails region by region consumes the unwind exactly as the compiler built it.

### One region, one rule

1. **Exits.** Walk the protected body as ordinary structured code until every path ends in this
   region's exit tail, in a return or throw, or in a nested region (handled by this same rule).
   With a catch, also walk the catch from its head the same way. With a finally, the protected
   part is the try and catch together; the finalizer is walked from its head to its tail.
2. **Every exit stays native.** JavaScript's own `try` statement already runs the finalizer and
   rethrows for every abrupt completion, so each exit is rendered where it leaves the region:
   - a `return` becomes `return x;`; a routed return renders `payload = value` then its pad's
     `return payload;`;
   - an uncaught throw, and the throw pad, need no code;
   - a `break`, `continue` or other jump to an outer target is handed to the enclosing walk, from
     inside the `try` or `catch` block. The enclosing construct decides how it is written.
   A finally region's pads are the compiler's re-issue of an exit after the finalizer, so each
   is walked in place at the exit whose literal names it and is not emitted again. Code after a
   pop is no longer protected but sits inside the native `try` block, so it must be a transfer.
3. **Continuation.** The statement continues at its normal completion block: after-catch for a
   catch-only try, after-finally with a finally. The end comes from the planner's
   [try row](vm-switch-statements.md#region-rows): its continuation, or for a catch whose block
   always throws its layout end. A finally exit tail whose literal names another block is a routed
   exit, walked as its pad. A region with neither end ends the walk there, and its catch keeps the
   code only it reaches.

### Worked example: continue through a finally

Real encoder output (VM default options) for
`for (var i = 0; i < 3; i++) { try { if (i === 1) { continue; } f(); } finally { g(1); } g(i); }`:

| PC lines | Instructions | Reading |
|---|---|---|
| 7 | `FINALLY_SETUP finally_4, r3, r4, finally_throw_6` | region head |
| 8-10 | `i === 1`, `JUMP_IF_FALSE if_else_7` | body |
| 11-13 | `LOAD_INT r3 = finally_cont_8; TRY_END; JUMP finally_4` | routed exit (literal first) |
| 14-15 | `f()` | body |
| 16-18 | `TRY_END; LOAD_INT r3 = after_finally_5; JUMP finally_4` | normal completion (pop first) |
| 19-22 | `g(1); JUMP_REG r3` | finalizer, tail |
| 23 | `THROW r4` | throw pad |
| 24 | `JUMP for_update_3` | pad finally_cont_8 |
| 25-26 | `g(i)` | after_finally_5 |

The routed exit's pad `JUMP for_update_3` is walked in place; the statement continues at
`after_finally_5`:

```js
try {
  if (i === 1) { <jump to for_update_3>; }
  f();
} finally {
  g(1);
}
g(i);
```

The enclosing loop writes `<jump to for_update_3>`: the update is the loop's
[continue target](vm-switch-statements.md#2-algorithm), so the loop reads `for (; ; i++)` and the
jump is `continue`.

## 3. Implementation

### Components

| Component | Input -> output | Invariant |
|---|---|---|
| Region reader (`renderTry`) | setup block and its planner try row -> region record `{kind, setupPc, entryId, record, continuation, payload, normalEnd}` | fields come from the typed setup; `record` is the handler record K must show for blocks inside the region; `normalEnd` is the row's continuation |
| Exit finder | region -> stop | the row's continuation, or a catch's layout end; a region's pops are blocks ending in handler-pop whose K `handlerStateIn` stack top is this setup |
| Body, catch and finalizer walks | region -> lines | `sequence()` with the region pushed on `context.regions`; the finalizer walk bars its own carriers |
| Exit renderer (`renderRegionExit`) | an exit tail -> lines and the next block | catch: what follows the pop is walked in the enclosing context; finally: the tail is consumed, a literal naming the row's continuation returns it, any other literal's pad is walked in place |
| Conditional mapping | K conditional whose merge is a finalizer head | its arms meet at that region's normal completion, or do not meet when it has none |

### Decisions and boundaries

- **Catch exits.** The statement continues at the row's continuation; the body and the catch walks
  must end there, or terminate. When the body never completes normally the row has none, and the
  frontend's layout end, accepted by the planner, places it. JavaScript cannot enter a catch from
  outside its try: a reachable edge that does is refused where it starts (an exceptional edge must
  name the innermost region's own catch or finalizer), and an unreachable one is dead code, kept
  as such, that never decides what runs.
- **Finally exits.** Normal completion is the tail whose literal names the row's continuation (the
  planner takes the first normal tail when several remain). Any other literal names a pad, which
  may only transfer control, a return reading the region's payload.
- **Resume and throw pad.** The resume is the `indirect-jump` on the region's continuation
  reachable from the finalizer head; the throw pad must be one `throw payload`. Both are
  consumed.
- Exception edges come from E, including native-throw edges from protected instructions, so a
  catch head is reachable whenever its body can throw.

Semantic checks, each with its decline message:

| Check | Hazard prevented | Message |
|---|---|---|
| Every walked block's handler stack equals the records of the enclosing regions | a catch delivering into the wrong register, or code outside its region | `Try region target state at <pc>` |
| A pop's outgoing edge leaves exactly the outer stack | a boundary that removes the wrong records | `Try region edge state at <pc>` |
| Ordinary code, and a finalizer, never read or write an enclosing finally region's continuation or payload; a closure never captures them | native `try/finally` keeps the pending completion itself | `Try region completion register used at <pc>`, `has captured completion registers` |
| An exceptional edge from an ordinary leaf names an uncaught throw or the innermost region's own catch or finalizer | an exception delivered to a catch outside its region, such as a finalizer's into its own catch | `<operation> at <pc> has an unstructured successor` |
| Code after a pop, including a pad, is a single transfer (jump or return) | unprotected code would run inside the native `try` | `Try region exit at <pc> is not a transfer` |
| A pad's return reads the region's payload | a pad runs before the finalizer, so another register could change | `Try region return payload at <pc>` |
| A call has exactly one exceptional route | an edge inventory that is not the producer's | `Try region effect edges at <pc>` |
| Tail, resume and throw pad have their grammar shape | a damaged routing | `breaks the exit tail`, `has no finalizer resume`, `has no payload throw pad` |

### Testing and acceptance

| Scenario | Oracle | Criterion |
|---|---|---|
| Every try form, without and with an exception | the source's own execution under the same host | decoded `TEST_OUTPUT` equals the source's; no VM residue; consistent derived state |
| Exceptions in body, catch and finalizer against pending returns and throws | the source's own execution | equal |
| Damaged real data, one property at a time | named decline, model unchanged | declines with the check's message |
| Code after a pop that is not a transfer | named decline | declines |
| Corpus and frozen recheck | oracle, byte comparison | no regression |

## 4. Input Shapes

| Producer | Shape consumed |
|---|---|
| [E edges](transforms/jsconfuser-vm/build-cfg.md) | handler/finally edges from calls, THROW and native-throwing protected instructions; finite `indirect-jump` targets |
| [K structured control](transforms/jsconfuser-vm/structured-control.md) | blocks with `handlerStateIn` |
| [Statement planner](vm-switch-statements.md) | normal-edge conditional regions with a named merge; loop bodies that keep a contained try's parts |
| Copy planning ([vm-switch-boundary.md](vm-switch-boundary.md#copy-simplification)) | retargeted assignments inside walked blocks |

## 5. Known Gaps

A try's parts that never reach its loop's back edge (a throw pad, a routed exit's tail, a catch
ending in `break`) are inside the loop: K's loop body is the header's [statement region](transforms/jsconfuser-vm/structured-control.md).

## Source

[vm-switch-structured-emitter.js](../../decoder/decode-js/src/vm/switch/vm-switch-structured-emitter.js):
`renderTry`, `renderRegionExit`, `startsRegionExit`, `checkState`, `carriers`,
`regionProtects`, and the finally-merge mapping in `renderConditional`.

## Fixtures

| Committed test or fixture | Claim pinned |
|---|---|
| [try-region.test.js](../../decoder/decode-js/test/vm/jsconfuser-vm/try-region.test.js) with [try-region/routes and forms](../../decoder/decode-js/test/vm/switch/fixtures/vm-switch-structured-emitter/try-region/generation.json) | every try form and every exception route recovers with the source's behaviour, including try statements inside loops; a catch whose try body cannot throw keeps its handler body |
| [exception-region-parser.test.js](../../decoder/decode-js/test/vm/jsconfuser-vm/exception-region-parser.test.js) | frozen exceptionRoutes output recovers; each damage reaches its named check |
| [vm-switch-to-source.test.js](../../decoder/decode-js/test/vm/switch/vm-switch-to-source.test.js) | code after a handler-pop that is not a transfer declines |
| corpus raw f-global-resolution, f-instanceof-errors, composition-finally-abrupt-return; runtime-finalizers top-level-finally | empty catch, call inside a call-free try's catch, routed returns on both arms, top-level finally fall-through recover |
