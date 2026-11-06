# Try-statement regions in structured emission

Pipeline stage: `emit-source` ([map](../../pipelines/jsconfuser-vm.md)).

The shared switch backend's structured emitter recovers every try statement through one rule.
Read [source emission](vm-switch-emit.md) for the emitter this rule is part of.

## 1. Target

Recover every try statement the pinned js-confuser-vm compiler emits as a native JavaScript
`try` statement: catch only, finally only, catch and finally, nested in any combination, and
left by any completion: normal, `return`, `break`, `continue`, a caught or an uncaught throw.
The rule reads blocks only. It never asks whether a jump target is a loop header, a loop exit or
a switch exit; such a target is handed to the enclosing construct unchanged. A model that is not
compiler grammar (a damaged target, a carrier captured by a closure, an edge with a wrong state,
code after a pop that is not a transfer) declines atomically with `unemittable-structured-control`.

Readers need the
[region grammar the compiler emits](../../../js-confuser-vm/instruction-set.md#catch-finally-and-abrupt-completion),
the [control solver](vm-switch-control.md)'s successors and handler stacks, and the
[statement planner](vm-switch-statements.md)'s try rows.

## 2. Algorithm

### Regions are delimited by their head and tail instructions

Only the compiler's region code produces these instructions, and it produces them at fixed
places, so a region's boundaries are read from block heads and tails instead of from the
region's overall shape.

| Boundary | Signature (typed operation) | Meaning |
|---|---|---|
| Region head | block ending in `catch-setup(target, exceptionRegister)` | catch region opens; catch entry is `target` |
| Region head | block ending in `finally-setup(target, continuation, payload, throwPad)` | finally region opens; in try/catch/finally it encloses one catch head |
| Catch head | the catch-setup target | entered by an exception raised inside the region, by its own setup (the try statement is one unit, so the active handler is reachable with it even when no program operation in the body can throw; [control solver](vm-switch-control.md#2-algorithm)), or, for an empty catch body, by the region's own exit jumps, since it is then the continuation |
| Finalizer head | the finally-setup target | entered by every exit of the finally region |
| Exit tail, catch | `handler-pop`, then a transfer | leaves the catch region: to its continuation (normal completion) or to an outer target |
| Exit tail, finally | optional `assign payload = value`, then `assign continuation = literal` and `handler-pop`, then `jump` to the finalizer head; [jump steps](vm-switch-boundary.md#jump-steps) may sit between any two | leaves the finally region; the literal names the exit. Normal completion pops first, a routed exit loads the literal first |
| Finalizer tail | `indirect-jump` on `continuation` | resumes at one of the control solver's finite targets |
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
   always throws its layout end, or for a finally with no reachable normal tail where its routed
   exits land. A finally exit tail whose literal names another block is a routed exit, walked as
   its pad; a pad landing on the end stops there, so the exit is rendered as completing. A region
   with no end ends the walk there, and its catch's block and catch close at the enclosing walk's
   stop, the catch keeping the code only it reaches.

### Worked example: continue through a finally

Encoder output, js-confuser-vm at the pin, options `{}`, `Math.random` replaced by mulberry32 seed
1, for `function f() {} function g(x) {}` followed by
`for (var i = 0; i < 3; i++) { try { if (i === 1) { continue; } f(); } finally { g(1); } g(i); }`;
PCs from the encoder's listing:

| PC | Instructions | Reading |
|---|---|---|
| 40 | `FINALLY_SETUP finally_6 (72), r5, r6, finally_throw_8 (83)` | region head |
| 45-53 | `i === 1`, `JUMP_IF_FALSE if_else_9 (62)` | body |
| 56-60 | `LOAD_INT r5 = finally_cont_10 (85); TRY_END; JUMP finally_6` | routed exit (literal first) |
| 62 | `f()` | body |
| 66-70 | `TRY_END; LOAD_INT r5 = after_finally_7 (87); JUMP finally_6` | normal completion (pop first) |
| 72-81 | `g(1); JUMP_REG r5` | finalizer, tail |
| 83 | `THROW r6` | throw pad |
| 85 | `JUMP for_update_5 (92)` | pad finally_cont_10 |
| 87 | `g(i)` | after_finally_7 |

The routed exit's pad 85 is walked in place, at the exit whose literal names it; the normal tail's
literal 87 is the row's continuation, where the statement continues. The pad's jump to 92 is the
loop's [continue target](vm-switch-statements.md#trailing-run-and-continue-target), so the loop is
written `for (; ; update)` and the jump is `continue`. Rendered (registers folded into the values
they hold; the test keeps the compiled polarity):

```js
for (; ; i++) {
  if (i < 3) {
    try {
      if (!(i === 1)) {
        f();
      } else {
        continue;
      }
    } finally {
      g(1);
    }
    g(i);
    continue;
  }
  break;
}
```

### Worked example: a finalizer that never completes

The same recipe for `function f() { try { } finally { return 2; } }
window.TEST_OUTPUT = f();`; function 1 starts at PC 34:

| PC | Instructions | Reading |
|---|---|---|
| 34 | `LOAD_THIS r1` | |
| 36 | `FINALLY_SETUP finally_2 (47), r2, r3, finally_throw_4 (55)` | region head; `r2` is this region's alone |
| 41-45 | `TRY_END; LOAD_INT r2 = after_finally_3 (57); JUMP finally_2` | normal completion of the empty body |
| 47-51 | `LOAD_CONST r4 = 2; RETURN r4` | finalizer; it never completes |
| 53 | `JUMP_REG r2` | the resume, by its register; unreachable |
| 55 | `THROW r3` | throw pad; unreachable |
| 57-61 | `LOAD_CONST r4 = undefined; RETURN r4` | after_finally_3; unreachable |

The finalizer walk terminates, so the statement has no end, and PCs 53-61 are unreachable and
dropped (`provenUnreachable` counts their 4 cases; register names shortened):

```js
try {
} finally {
  r4 = 2;
  return r4;
}
```

## 3. Implementation

### Components

| Component | Input -> output | Invariant |
|---|---|---|
| Region reader (`renderTry`) | setup block and its planner try row -> region record (below) | fields come from the typed setup; `setupPc` names the handler record the [control solver](vm-switch-control.md) must show for blocks inside the region; `normalEnd` is the row's continuation |
| Exit finder | region -> stop | the row's continuation, or a catch's layout end; a region's pops are `handler-pop` cases whose solver stack top is this setup |
| Body, catch and finalizer walks | region -> lines | `sequence()` with the region pushed on `context.regions`; the finalizer walk bars its own carriers |
| Tail reader (`finallyTailStep`) | one typed operation and the setup's `continuation` and `target` -> pop, continuation write, jump step, jump into the finalizer, or none | the one reading of a finally tail's steps; the exit renderer (`renderRegionExit`, `startsRegionExit`) and the normal landing (`normalLanding`) use it |
| Exit renderer (`renderRegionExit`) | an exit tail -> lines and the next case | catch: what follows the pop is walked in the enclosing context; finally: the tail is consumed one case at a time over the solver's successors, each a tail step or a jump step, a literal naming the row's continuation returns it, any other literal's pad is walked in place |
| Conditional mapping | planner conditional whose merge is a finalizer head | its arms meet at that region's normal completion, or do not meet when it has none |

The region record:

```js
{ kind, setupPc, entryId, continuation, payload, normalEnd }
```

### Decisions and boundaries

- **Catch exits.** The statement continues at the row's continuation; the body and the catch walks
  must end there, or terminate. When the body never completes normally the row has none, and the
  frontend's layout end, accepted by the planner, places it. The backend reads no unreachable case
  for it: the end is a supplied model field, and only the frontend, which knows its compiler's
  layout, may read it from dead code ([why](../jsconfuser-vm/lower-switch-model.md#the-catch-layout-hint)).
  Without it, the Continuation step says what holds.
  JavaScript cannot enter a catch from
  outside its try: a reachable edge that does is refused where it starts (an exceptional edge must
  name the innermost region's own catch or finalizer), and an unreachable one is dead code, never
  emitted, that never decides what runs.
- **Rejoining at a finally's tail.** Inside a finally, a try's row may end at that finally's normal
  tail while its catch ends in a routed exit that lands at the finally's normal end, past the tail.
  Both complete alike, so `normalLanding` reads where the tail leads and the two walks are compared
  there; when either walk stops at the tail the statement continues there, so it is rendered once.
- **Finally exits.** Normal completion is the tail whose literal names the row's continuation (the
  planner takes the first normal tail when several remain). Any other literal names a pad, which
  may only transfer control, a return reading the region's payload.
- **Resume and throw pad.** The compiler gives each try/finally its own continuation register, from
  a pool whose slots are never reused, and ends the finalizer with the one `indirect-jump` that
  reads it. So the resume is selected by that register, not by reachability. A finalizer that never
  completes (it returns, throws, breaks or continues outward) leaves the resume and the throw pad
  unreachable: the statement has no normal end, and both are
  [dropped](vm-switch-emit.md#unreachable-code). A finalizer that completes must reach the
  resume, and the throw pad must be one `throw payload`; both are then consumed.
- Every successor the walk follows is the control solver's edge from the case's PC, including the
  abrupt route of each protected operation that can throw; an unreachable case has none, so no
  walk meets one. The solver routes every setup to its own handler, so a catch head is reachable
  whenever its try is entered, and gives every call exactly one abrupt route.

Semantic checks, each with its decline message:

| Check | Hazard prevented | Message |
|---|---|---|
| Every walked case's solver stack holds the enclosing regions' setups, innermost last | a catch delivering into the wrong register, or code outside its region | `Try region target state at <pc>` |
| The solver's stack after a pop is exactly the outer regions' | a boundary that removes the wrong records | `Try region edge state at <pc>` |
| Ordinary code, and a finalizer, never read or write an enclosing finally region's continuation or payload; a closure never captures them | native `try/finally` keeps the pending completion itself | `Try region completion register used at <pc>`, `has captured completion registers` |
| An exceptional edge from an ordinary operation names an uncaught throw or the innermost region's own catch or finalizer | an exception delivered to a catch outside its region, such as a finalizer's into its own catch | `<operation> at <pc> has an unstructured successor` |
| Code after a pop, including a pad, is a single transfer (jump or return) | unprotected code would run inside the native `try` | `Try region exit at <pc> is not a transfer` |
| A pad's return reads the region's payload | a pad runs before the finalizer, so another register could change | `Try region return payload at <pc>` |
| Tail, resume and throw pad have their grammar shape | a damaged routing | `breaks the exit tail`, `has no finalizer resume`, `has no payload throw pad` |

### Testing and acceptance

| Scenario | Oracle | Criterion |
|---|---|---|
| Every try form, without and with an exception | the source's own execution under the same host | decoded `TEST_OUTPUT` equals the source's; no VM residue; consistent derived state |
| Exceptions in body, catch and finalizer against pending returns and throws | the source's own execution | equal |
| A finalizer that never completes | the source's own execution | equal; native `try/finally`, no `if (false)` block, resume and throw pad counted in `provenUnreachable` |
| Code after a pop that is not a transfer | named decline | declines |

## 4. Input Shapes

| Producer | Shape consumed |
|---|---|
| [Control solver](vm-switch-control.md) | which cases run; each case's successors (handler and finally routes from setups, calls, throws and protected operations that can throw; finite `indirect-jump` targets); the handler stack at each case and after each pop |
| [Statement planner](vm-switch-statements.md) | normal-edge conditional regions with a named merge; loop bodies that keep a contained try's parts |
| Copy planning ([vm-switch-emit.md](vm-switch-emit.md#copy-simplification)) | retargeted assignments and removed moves among the walked cases |

## 5. Known Gaps

None of its own; the control boundaries are the planner's
[known gaps](vm-switch-statements.md#5-known-gaps).

## Source

[vm-switch-structured-emitter.js](../../../../decoder/decode-js/src/vm/switch/vm-switch-structured-emitter.js):
`renderTry`, `normalLanding`, `finallyTailStep`, `renderRegionExit`, `startsRegionExit`, `checkState`, `carriers`,
`regionProtects`, and the finally-merge mapping in `renderConditional`.

## Fixtures

Each suite encodes its sources with the pinned encoder and requires the decode to behave as the
source ([tests.md](../../tests.md#suites)); a Proved line names the code whose break turns the case
red.

| Suite and cases | Claims | Proved |
|---|---|---|
| [compiled-forms](../../../../decoder/decode-js/test/vm/jsconfuser-vm/generated-cells/compiled-forms/suite.js), `control-try`: f-throw-catch, f-finally-abrupt, composition-finally-abrupt-return, return-through-finally, caught-return-through-finally, protected-conditional-catch, f-instanceof-errors, dead-code, top-level-finally, abrupt-finally-return; f-global-resolution in `host-effect` | Every try form and exception route recovers with source behaviour: empty catch, routed returns on both arms, top-level finally fall-through, try statements inside loops, a finalizer that never completes | Catch setups are read as protected regions; a finally's throw pad is its own operand; the resume selected by its register |
| [try-arm-exits](../../../../decoder/decode-js/test/vm/jsconfuser-vm/generated-cells/try-arm-exits/suite.js), and `try-routed-ends`, plain and in `single-payload-stage-conditions` under flattening | Try ends in arms and routed ends, also with the catches the flattener moves | The try end in a conditional's arm; the routed tails |
| `compiled-forms`, `control-switch`: try-in-switch-catch-break, try-in-switch-both-break, switch-catch-break-falling-tail | A try in a switch clause whose block or catch breaks out of the switch renders inside the clause, its tail falling into the next clause | The try's end in [vm-switch-statements](vm-switch-statements.md) (S8) |
| [vm-switch-to-source.test.js](../../../../decoder/decode-js/test/vm/switch/single-component/vm-switch-to-source.test.js) (unit) | code after a handler-pop that is not a transfer declines; a finalizer that never completes stays native | Not a suite; the resume selected by its register |

The damaged continuation-write and resume-register controls have no committed test: they edited
input by hand. A try nested in a catch under flattening has no case of its own.
