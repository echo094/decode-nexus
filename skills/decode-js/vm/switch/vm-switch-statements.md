# Recover statements from a VM switch model

Pipeline stage: `plan-statements` ([map](../../pipelines/jsconfuser-vm.md#backend-order)).

Readers need the [VM switch model](vm-switch-boundary.md#model-fields) with its
[typed operations](vm-switch-boundary.md#typed-operation-grammar), the
[solved control](vm-switch-control.md) (edges, reachability, handler stacks), and directed graphs
with dominance (a block A dominates B when every path from the entry to B passes A).

## 1. Target

The compiler lowers every statement to jumps, branches, handler setups and pops. The planner reads
one function's cases and its solved control and finds where each source statement opens and
closes: loops, tries, switches, conditionals and labeled blocks. Its result is a list of region
rows, plain data the [emitter](vm-switch-emit.md#structured-rendering) renders as native
statements. Without it a function could only be written as a dispatch loop over its cases.

`planStatements(functionRecord, cases, solved)` returns the rows. The backend driver calls it as
the first step of a function's rendering and publishes every function's rows as the result's
`statements`. By the [ownership test](vm-switch-boundary.md#ownership-test) the planner needs no
encoder knowledge: it reads only the typed operations and the solver's result. It never changes
the model, decides nothing from an unreachable case, and a plan can still be declined by the
emitter.

### Terms

| Term | Meaning |
|---|---|
| Block | One case, named `${functionId}:b@${pc}`; its operation is the case's typed operation. |
| Edge | The solver's (`edges`: kind, route, condition). A *normal* edge is any whose route is not `exceptional`. Which blocks run (`reachablePcs`) and the handler stack each case runs under (`stateIn`) are the solver's too. |
| Jump step | A block whose operation is an unconditional `jump`: it runs nothing, so every reader here looks through it ([boundary](vm-switch-boundary.md#jump-steps)). |
| Statement region, members | The blocks a statement holds: those its head dominates, less those its end (or a cut) dominates without dominating the head. A region is *closed* when every edge into a member other than the head comes from a member; the head may be entered from outside it, and a try's setup from anywhere. |
| End (continuation) | The block where control goes on after the statement completes normally. |
| Transfer, stop | A jump out of a statement to an enclosing statement's head or end (`continue`, `break`), or a `return`/`throw`. The blocks such a jump reaches are *stops*: a walk inside the statement does not pass them. |
| Later end | A block outside a statement that one of its exits reaches past code its own end runs: what `break L` leaves behind. |
| Labeled block | The row that holds later ends: `__recovered_block_...: { statement; tail; }`. |
| Trailing run | The code that ends at a loop's only back edge, where several paths enter it: a `for` update or a do-while test, when a jump proves it one. |
| Layout end | The frontend's hint, on a `catch-setup`, of where the source closed a try whose block always throws ([`lower-switch-model`](../jsconfuser-vm/lower-switch-model.md#the-catch-layout-hint)). |

## 2. Algorithm

### Pass order

A statement closes by its own edges, never by how the function ends: a source function need not end
in `return`, and `for (...) { if (x) return a; } return b;` closes its `for` where the loop's test
exits. Each pass finds one kind of statement and hands the next the ends it found, which are that
pass's stops.

```text
planStatements(functionRecord, cases, solved)               (explanatory pseudocode)
  blocks = one per case, in PC order
  if every edge is fallthrough or return and no block is a catch-setup or finally-setup:
    return [linear over every block]                        the empty edge list satisfies this
  view = FunctionGraph(entry, blocks, edges, solved)        built once
  statements = findStatementRegions(view)                   loop and try regions, outermost first
  loops      = findNaturalLoops(view, statements)
  switches   = findSwitchRegions(..., loops)
  if a try's setup is a member of a switch row with an end:
    run the three again, findStatementRegions given switchEnds(head)
  labeled = the statements' block ends as rows + the switches' labeled rows
  (conditionals, labeled) = closeConditionals(...)          repeats until labeled stops growing
  publishContinueTargets(loops, conditionals and switches)
  return conditionals, switches, loops, one opaque row, try rows, labeled rows
```

1. **Linear shortcut.** A function whose edges are all `fallthrough` or `return` and which sets up
   no try is one linear region; nothing else runs. A function with a call has a `call` edge and
   goes on.
2. **Statement regions** of loops and tries, outermost first (fewest dominators): each loop's end
   and later ends, each try's end and later ends, each loop's trailing run.
3. **Natural loops**: one row per loop header, its body the header's statement region.
4. **Switches**: chains of `===` tests on one register, given the loops' stops.
5. **Re-plan** when a try's setup is a member of a switch row with an end: steps 2-4 run again with
   the ends of the switches holding each try, which are its `break` targets. A switch's end is
   known only once the switch rows are found, after the statements.
6. **Labeled-block rows** from step 2 and step 4.
7. **Conditionals**, given every earlier end as a stop. A test whose arms meet without a first block
   adds a labeled block. That block's end becomes a stop for the tests inside it, so the pass
   repeats until it adds no row.
8. **Continue targets**: a loop whose trailing run a statement jumps to publishes it.
9. **Opaque row**: the blocks that are no conditional test, switch test or loop header.

```mermaid
flowchart TD
  M["One function's cases + solved control"] --> FT{"Only fallthrough / return edges, no try?"}
  FT -- Yes --> LN["Linear region"]
  FT -- No --> SR["Statement regions: loop and try ends, later ends, trailing runs (outermost first)"]
  SR --> NL["Natural-loop rows"]
  NL --> SW["Switch rows"]
  SW --> RP{"A try inside a switch with an end?"}
  RP -- Yes --> SR2["Statement regions, loops, switches again, with switch ends as breaks"]
  RP -- No --> LB
  SR2 --> LB["Labeled-block rows from tries, loops and switches"]
  LB --> CR["Conditional rows"]
  CR -- "a new labeled block" --> CR
  CR --> CT["Continue targets"]
  CT --> OP["Opaque row; then try rows and labeled-block rows"]
```

The repetition in step 7 ends: a test that gains a labeled block closes on every later pass, since
its block's end is then one of its stops, so each test adds at most one row.

### Loop end

A **loop** is entered at a back-edge target, an edge whose target dominates its source. Its *cycle*
is the header and every block that reaches a back edge.

1. Walk the header's straight run over normal edges. The first `branch` or `for-in-next` with
   exactly one target outside the cycle is the loop's test (while, for, for-in); its outside target
   is the end.
2. A branch whose arms close inside the cycle is nested in the test, a short-circuit operand of
   `p != null && !(stop && f(p))`, say. It is closed by the conditional rule, its stops being the
   loop's head and the enclosing loops' heads and ends, and the walk continues where it closes.
3. Otherwise, with one back edge, the branch that back edge falls from is the test (a do-while).
4. The end is followed through jump steps while it stays outside the cycle.
5. The test is the loop's **exit test**, published with the row. A test found by step 1 whose staying
   arm is the loop's only back edge (directly or through a jump step), and that is not the header,
   is a bottom test like step 3's: `do { s += i; i++; } while (i < a)` has a straight body, so step 1
   reaches its test first. Any other test from step 1 is a top test, and the blocks the walk passed
   before it, a nested short-circuit with its arms included, are its run: what a native
   `while (run..., test)` evaluates before each iteration.

The body is the loop's statement region: the blocks the header dominates and the end does not. So a
try inside the loop keeps its throw pad, the `handler-pop` a `break` runs before its jump, and a
catch ending in `break`. A loop whose test cannot be found has no end; its row is still published
and emission declines it.

### Try end

A **try** is entered at its setup (`catch-setup`, `finally-setup`) and ends where its own normal exit
leads. The compiler pops the try (`handler-pop`) on every exit that does not throw: its normal end,
and each `return`, `break` or `continue` crossing it. The rule depends on what the try has.

**A catch that completes normally** ends where its block's normal end and its catch's normal end
meet, as a native `try` statement completes:

1. Follow each pop of this try through the jump steps only its own route enters, to the block it
   leads to. A jump step several routes enter is where they meet, a location
   ([F4](../../../decoding-method/rules.md#f4)): a try
   nested in a catch ends at the jump its own pops and its catch share, not at the outer try's end
   behind it.
2. Keep the blocks the catch's own normal walk reaches. The walk never passes the setup again, so a
   loop's next iteration is not the catch completing. Drop an enclosing loop's head or end and an
   enclosing switch's end: those are `continue` and `break`. A catch that leaves by a `break` of
   the switch holding the try reaches only that end: `case 1: try { if (x) break; f(); } catch (e)
   { break; } g(); case 2: ...` ends its try at `g()`.
3. The end is the one the catch reaches first: it dominates the others over the catch's walk. A
   `break` crossing the try leads to a block a completing catch reaches only through the normal end,
   so the layout never decides.

**A catch that never completes normally** ends at the target of the `jump` after a pop. A pop that
falls into code ends nothing, since a `return` crossing the try has that graph too
([Known Gaps](#5-known-gaps)).

**A finally** ends at the literal its tail assigns to its continuation register after a pop and
before jumping to its finalizer. Jump steps may sit between any two of these and before the literal's
block: control flow flattening places steps there, and a routed pad may land on a different step
before the same block.

**A finally with no reachable normal tail**, whose every non-throwing exit is routed, ends where
those exits land: `a: try { throw 1; } catch (e) { break a; } finally {}` and `for (;;) { try {
throw 1; } catch (e) { break; } finally {} }` have only the routed tail. A pad that jumps, or that
opens the enclosing finally's tail, runs what follows the statement, so the try ends there. A routed
return's pad reads the pending payload and stays at its exit, so its try has no end.

**Several tails.** A `break` or `continue` crossing a try has the same tail as its normal end. Among
several tail targets, an enclosing loop's head or end and an enclosing switch's end are transfers
and are dropped; so is a `continue` to an enclosing loop's trailing run, unless every target is one.
The compiler emits one normal tail per try; when several remain (a reachable injected copy, say),
the first in program order ends the try and the others are walked as routed exits. An end that
leaves the try's region open is dropped.

**A try without an end** reaches the code after it only through its catch. The frontend's layout end
then places the end, when the catch's own normal walk reaches that block inside the catch; otherwise
the catch keeps the code only it reaches. Both layouts behave the same. The frontend reads the hint
from its compiler's dead normal exit
([why only there](../jsconfuser-vm/lower-switch-model.md#the-catch-layout-hint)); the planner reads
no unreachable case for it. The layout end serves as the try's end for labeled exits and for the
tests inside the try: `L: { try { throw 1; } catch (e) { if (c) break L; } tail(); }` reads with its
`break L` and the tail after the try.

### Labeled exits

`break L` and `continue L` compile to a plain `jump`. The encoder's labels exist only while it
compiles ([compiler](../../../js-confuser-vm/js-confuser-vm.md)): any statement can carry one, and
the jumps are the same whichever did, so the planner never reads a label. The graph keeps their
limit: a `break` goes only to the end of a statement holding it, a `continue` only to the continue
point of a loop holding it, and neither leaves its function. Most such jumps are transfers. The rest
leave a statement for a **later end**, past code another route runs: in `L: { while (t) { if (x)
break L; } tail; } end;` the loop's end is `tail`, and the jump to `end` is no transfer of it.

A later end is found by walking forward from each exit of the statement and from its end, without
passing a transfer; where an exit's walk first meets the end's walk is that exit's landing. A
landing that is neither the end nor a transfer is a later end. Later ends are placed in this order,
since a label makes code hard to trace:

1. Statements close by their own rules.
2. A loop with exactly one later end moves its end there, when the code it skips holds no loop and
   its test is no `for-in`: the skipped code goes into the arm of the test that leaves,
   `while (true) { if (!t) { tail; break; } if (x) break; }`, with no label beyond the loop's. A
   do-while reads this way already, since its `break` is the first branch leaving its cycle. A
   `for-in` must leave at the loop's end to advance, so it cannot.
3. Otherwise the statement gets a **labeled block** ending at each later end, nearest innermost:
   - *Loop:* every later end, as in `twoLabels` of the
     [labeled-exit-forms](../../../../decoder/decode-js/test/vm/jsconfuser-vm/sources/labeled-exit-forms/source.js)
     source, `A: { B: { for (...) { if (i === a) break A; if (i === b) break B; ... } t.push("b"); }
     t.push("a"); } t.push("end");`: the loop's end is `t.push("b")`, `break B` lands at
     `t.push("a")`, `break A` at `t.push("end")`, and the output nests two blocks.
   - *Try:* always, since its tail runs after the finalizer and outside the handler, so the try
     never moves its end: `L: { try { if (c) break L; x(); } finally { f(); } tail(); } end;`. Also
     where another route reaches the end from before the try: `L: { if (d) break L; try { if (c)
     break L; } finally { } tail(); } end;`. A loop's exit to the try's own end takes one too, since
     a `break` leaves only the loop: `a: try { for (...) { if (i) break a; ... } ... } finally { ... } end;`
     reads `L: { try { ... break L; ... } finally { ... } } end;`.
   - *Switch:* always, since every clause body reaches its end: `L: { switch (n) { case 1: if (c)
     break L; break; default: d(); } tail(); } end;` keeps `tail()` after the switch.
   - *Conditional* whose arms meet without a first block (see [Conditional](#conditional)).

An exit lands where it runs nothing on the way: handler pops, jumps and, through a finalizer, its own
pad, never the finalizer's resume that every exit shares. So a `break A` that leaves through two
finally statements to an enclosing loop's end takes no label, and an exit to an enclosing loop's
trailing run is a `continue`, never a later end.

A labeled source statement gets no block where a statement's own rules hold. The block's name is
never the source's, and its placement need not be: `L: if (x) { ... }` and `L: { if (x) { ... } }` are
one graph, and only behaviour is the oracle
([M1](../../../decoding-method/rules.md#m1)).

### Trailing run and continue target

A loop's **trailing run** is walked back from its only back edge, or, for a do-while, from its test
(so the run is the test). The walk crosses straight blocks and a conditional that is one expression
(an update `i = x ? i + 2 : i + 1` or `x && n++`): its arms first meet at the block walked back from,
hold no statement, and are the only way into it. It stops at a block several paths enter; that block
starts the run. A walk that reaches the header, or a block whose single predecessor branches, finds no
run. An `if` whose arms meet earlier is a statement before the run.

The run is a stop like the loop's head and end, so no statement inside the loop takes it as a member.
Whether it is the loop's **update** (entered by every `continue`) or plain body code that a merge
explains (`while (t) { if (c) a; else b; z }` closes its `if` at `z`) is read after the statements
close. It is the update when a statement jumps there without closing there:

- a try that closes elsewhere while one of its blocks jumps to the run (a `continue` routed through
  a finally re-issues the jump from its pad), or
- a conditional or switch with an arm that reaches the run while it closes elsewhere, unless an
  inner loop ends at the run, which explains that jump as its own `break`.

Only then does the loop publish the run as its continue target, which the emitter writes as a `for`
update or a do-while's `while (test)`, so that a native `continue` runs it.

### Switch

A **switch** is a chain of two-way tests that compare one register, the discriminant, with `===`
against each case's value in turn, while nothing in the chain writes the discriminant. A test's match
route enters its case body; its miss route runs the next case's value into the next test; the last
miss enters the default body, or the end when there is none. That is how a native `switch` selects
its clause, so its bodies may share routes as clauses do: fallthrough into the next clause, grouped
labels entering one body, a default between cases. A body may hold a try whose catch or finalizer
belongs to it.

1. A chain becomes a switch only when one of its tests has no first meeting block; a chain whose arms
   all meet stays a chain of conditionals, which behaves the same.
2. The switch ends at the nearest block every body's normal exit reaches (`break` or the last body
   running out). Code every route runs is therefore after the switch, even where the source wrote it
   as the last clause, and a case entered there is an empty last clause.
3. A labeled exit past that block (`L: { switch (n) { case 1: if (c) break L; ... } tail(); } end;`)
   reaches it by no other route, so the switch still ends at `tail()` and the exit becomes a later
   end.
4. Clause order keeps every fallthrough: a body that runs into another clause's body is followed by
   that clause, and the default goes where that holds.

For `switch (x) { case 1: out.push(1); case 2: out.push(2); } return out;` the encoder emits the
tests `x === 1` and `x === 2`, each jumping to its case body, and the bodies in order. The first
test's arms both reach case 2's body and the return, but the second test's miss reaches the return
without case 2's body, so neither dominates the other: no first meeting block. Both tests compare
`x`, which nothing in the chain writes, so `x` is the discriminant; the end is the return, and case
1's body falls into case 2's, so the clauses keep that order.

### Conditional

A **conditional** is a block whose operation has a conditional and a fallthrough edge. Each arm walks
forward from one target over normal edges, stopping at a stop: the head, end and trailing run of
each loop holding the test, the end and clause entries of a holding switch, the ends of a holding
labeled block, the end of the innermost holding try, and the layout end of each holding try without
an end. An arm in a catch therefore stops where the try completes. A try is one statement, so an arm also walks a
`catch-setup`'s own route into its catch: `if (x) { try { throw 1; } catch (e) { a(); } } b();`
meets at `b()`, reached only through the catch. Any other exceptional route leaves the statement and
is not followed.

The test closes at the first of these that applies:

1. **The arms meet.** The merge is the first block both reach, by dominance over the paths from the
   test through its arms only, so code they share with paths from outside (a catch rejoining after a
   try) does not hide where they meet. A jump step on a single route into that block does not hide
   it either.
2. **The arms meet only at one stop** (both run into a loop's trailing run, say): they close there.
3. **One arm leaves the innermost try.** A fallthrough arm that reaches the end of the innermost try
   holding the test, while the other does not, closes the test at that end: `a: try { if (c) break
   a; x(); throw 1; } finally {}` reads `try { if (!c) { x(); throw 1; } } finally {}`. A layout end
   never closes a test this way.
4. **One arm is a transfer.** The fallback is the fallthrough target when it is a stop (the loop's
   test leaving it), else the branch target, the else-or-end, followed through jump steps to a stop.
   So `if (v < 0) throw ...; return v + 1;` reads as a guard, a `switch` whose cases all return as a
   chain of guards, and a loop's test closes at the loop's end, which lets the emitter write it in the
   loop's head ([loop end](#loop-end)). Inside a labeled
   block, when the fallback is the block's end and the arms reach the block's inner stop, the test
   closes at the inner stop instead and the arm reaching the end breaks: `L1: { if (a) { if (x)
   t(); else break L1; } else e(); f(); }` closes `if (x)` at `f()`.
5. **The arms meet without a first block** and the test is no switch's: a labeled exit skips code
   another route runs. The test gets a labeled block around itself, ending at the nearest shared
   block whose removal gives the arms a first block and that a route skipping that first block
   reaches, past the code it skips. Its further exits are later ends, so `L1: { L2: { if (a) { if
   (x) break L2; if (y) break L1; } ... } ... }` nests a block for each. In `L: { if (a) { if (b) break
   L; } e(); f(); } end;` only `end` is reached past `e()`.

A `break` guard, `if (c) break L; rest;`, keeps its guard reading: only the fallback gives way to an
inner stop.

### Worked example: three loops

The committed cell `f-loop-forms` of suite `compiled-forms` (file `control-branch`, profile
`randomizeOpcodes`, seed 251). The source:

```js
var sum = 0; for (var i = 1; i <= 5; i++) sum += i;
var j = 0; var doCount = 0; do { doCount++; j++; } while (j < 2);
var w = 0; while (w < 3) w++;
window.TEST_OUTPUT = [sum, doCount, w];
```

The root function, by the lowered cases (`r` a register):

| PC | Cases | Role |
|---|---|---|
| 0-13 | `this`, `sum = 0`, `i = 1` | entry run |
| 16-20 | `r7 = 5; r8 = i <= r7` | back-edge target: the first loop's header and its test's run |
| 24 | `branch r8, when false -> 50` | the first branch with one target outside the cycle |
| 27-31 | `sum += i` | body |
| 34-45 | `i++` | the update |
| 48 | `jump 16` | the back edge |
| 50-61 | `j = 0; doCount = 0` | the first loop's end |
| 64-96 | `doCount++; j++; r8 = j < 2` | the second loop: header 64, a straight body |
| 100 | `branch r8, when false -> 105` | its test |
| 103 | `jump 64` | the back edge, a jump step |
| 105-109 | `w = 0` | the second loop's end |
| 112-116 | `r8 = w < 3` | the third loop's header and run |
| 120 | `branch r8, when false -> 139` | its test |
| 123-137 | `w++; jump 112` | body and back edge |
| 139-161 | the global write, `return` | the third loop's end |

1. **Not linear.** The function has conditional edges.
2. **Loop at 16.** The back edge 48 -> 16 makes 16 a header. Its run 16, 20 reaches the branch 24,
   whose target 50 is outside the cycle: 50 is the end. The staying arm 27 is no back edge, so 24
   is a top test with the run 16, 20.
3. **Loop at 64.** The run 64 ... 96 is straight and reaches the branch 100, whose target 105 is
   outside the cycle. Its staying arm 103 is the loop's only back edge, a jump step, and 100 is not
   the header: a bottom test, the do-while.
4. **Loop at 112.** As the first: end 139, top test 120 with the run 112, 116.
5. **Trailing runs.** Walking back from 48 over 45 ... 27 meets 27, whose single predecessor 24
   branches: no run. The same holds for the third loop. The second loop's walk reaches its header:
   no run. No loop has a continue target.
6. **Conditionals.** Each test's arms never meet before a stop. For 24 the fallthrough 27 is no
   stop and the branch target 50 is the loop's end, so the test closes at 50; likewise 100 at 105
   and 120 at 139.

The rows (the `proof` and `condition` fields left out):

```js
{ kind: 'conditional', testBlockId: '0:b@24', branchTargetPc: 50, fallthroughTargetPc: 27, mergeBlockId: '0:b@50' }
{ kind: 'conditional', testBlockId: '0:b@100', branchTargetPc: 105, fallthroughTargetPc: 103, mergeBlockId: '0:b@105' }
{ kind: 'conditional', testBlockId: '0:b@120', branchTargetPc: 139, fallthroughTargetPc: 123, mergeBlockId: '0:b@139' }
{ kind: 'natural-loop', headerBlockId: '0:b@16', bodyBlockIds: [/* 16 ... 48 */], continuationBlockId: '0:b@50',
  exitTestBlockId: '0:b@24', exitTestAtBottom: false, exitTestRunBlockIds: ['0:b@16', '0:b@20'],
  continueBlockId: null, updateBlockIds: null, testBlockIds: null }
{ kind: 'natural-loop', headerBlockId: '0:b@64', bodyBlockIds: [/* 64 ... 103 */], continuationBlockId: '0:b@105',
  exitTestBlockId: '0:b@100', exitTestAtBottom: true, exitTestRunBlockIds: null,
  continueBlockId: null, updateBlockIds: null, testBlockIds: null }
{ kind: 'natural-loop', headerBlockId: '0:b@112', bodyBlockIds: [/* 112 ... 137 */], continuationBlockId: '0:b@139',
  exitTestBlockId: '0:b@120', exitTestAtBottom: false, exitTestRunBlockIds: ['0:b@112', '0:b@116'],
  continueBlockId: null, updateBlockIds: null, testBlockIds: null }
{ kind: 'opaque', blockIds: [/* every block but the three tests and the three headers */] }
```

The emitter writes (registers named after the source):

```js
sum = 0;
for (i = 1; i <= 5; i = i + 1) { sum = sum + i; }
j = 0; doCount = 0;
do { doCount = doCount + 1; j = j + 1; } while (j < 2);
for (w = 0; w < 3; w = w + 1) {}
window["TEST_OUTPUT"] = [sum, doCount, w];
```

### Worked example: a catch with a labeled exit

The committed cell `catch-exit-past-tail` of suite `compiled-forms` (file `control-label`, profile
`randomizeOpcodes`, seed 251):

```js
function f(c, b) { var t = []; L: { try { if (b) throw 1; t.push("b"); } catch (e) { if (c) break L; t.push("c"); } t.push("tail"); } t.push("end"); return t; }
```

Function 1 starts at PC 78:

| PC | Cases | Role |
|---|---|---|
| 86 | `catch-setup -> 119, r5` | the try's setup |
| 89 | `branch r1, when false -> 98` | test `b` |
| 92-96 | `throw 1` | the throwing arm |
| 98-110 | `t.push("b")` | |
| 116 | `handler-pop` | the try's only pop |
| 117 | `jump 142` | a jump step only the pop's route enters |
| 119 | `branch r0, when false -> 124` | the catch entry: test `c` |
| 122 | `jump 160` | `break L` |
| 124-136 | `t.push("c")` | |
| 142-154 | `t.push("tail")` | |
| 160-178 | `t.push("end"); return t` | |
| 180-184 | `return undefined` | unreachable |

1. **Try end.** The try is catch-only. Its pop 116 leads through the jump step 117 to 142. The catch's
   walk from 119 reaches 142 (and 160), so 142 is the end.
2. **Later ends.** The end's walk is 142 onward, 160 included. The members the end's walk does not
   reach are 86-136. Their exit 122 -> 160 lands at 160 without passing 142, so 160 is a later end;
   the try never moves its end, so a labeled block headed by 86 ends at 160.
3. **Test 89.** Stops: the try's end 142 and the block's end 160. The fallthrough arm 92-96 ends at
   the throw; the branch arm 98-117 reaches 142. They never meet, the fallthrough arm does not reach
   the try's end, and 92 is no stop, so the test closes at its branch target 98: a guard.
4. **Test 119.** Same stops. The fallthrough arm 122 reaches 160; the branch arm 124-136 reaches
   142. No shared stop, and the fallback 124 is no block end, so it closes at 124: a guard whose
   consequent is `break`.

```js
{ kind: 'conditional', testBlockId: '1:b@89', branchTargetPc: 98, fallthroughTargetPc: 92, mergeBlockId: '1:b@98' }
{ kind: 'conditional', testBlockId: '1:b@119', branchTargetPc: 124, fallthroughTargetPc: 122, mergeBlockId: '1:b@124' }
{ kind: 'opaque', blockIds: [/* every block but 89 and 119 */] }
{ kind: 'try', setupBlockId: '1:b@86', continuationBlockId: '1:b@142', layoutEndBlockId: null,
  memberBlockIds: [/* 86 ... 136 */] }
{ kind: 'labeled-block', headBlockId: '1:b@86', endBlockIds: ['1:b@160'], innerStopBlockIds: [] }
```

The emitter writes (registers named after the source):

```js
__recovered_block_1_0: {
  try {
    if (b) { throw 1; }
    t["push"]("b");
  } catch (__recovered_error) {
    if (c) { break __recovered_block_1_0; }
    t["push"]("c");
  }
  t["push"]("tail");
}
t["push"]("end");
return t;
```

## 3. Implementation

### Exports another file imports

| Export | File | Importers | Role |
|---|---|---|---|
| `planStatements(functionRecord, cases, solved)` | `plan-statements.js` | `to-source.js` | the rows of one function |
| `FunctionGraph`, `normalAdjacency`, `armAdjacency`, `successorMap`, `jumpStepResolver`, `dominators`, `reachableBlockIds`, `walkForward`, `laterEnds` | `graph.js` | the other files of the folder | the block graph and the shared walks |
| `findStatementRegions(view, switchEnds)` | `statement-regions.js` | `plan-statements.js` | loop and try regions |
| `LoopEnds`, `transfersFrom`, `enclosingLoopStops` | `loop-ends.js` | `statement-regions.js`, `try-ends.js` | where a loop closes |
| `TryEnds` | `try-ends.js` | `statement-regions.js` | where a try closes |
| `findSwitchRegions(blocks, edges, graph, loops, control)` | `switches.js` | `plan-statements.js` | switch rows and their labeled rows |
| `twoWayTests`, `enclosingStops`, `armWalk`, `closeConditionals` | `conditionals.js` | `plan-statements.js` | conditional rows |
| `closeConditional`, `loopStops` | `conditionals.js` | `loop-ends.js`, `switches.js` | one test's close; a block's loop stops |

Only `planStatements` leaves the folder. The folder imports `model/` alone (`decline`,
`isJumpStep`).

### Region rows

```js
{ kind: 'linear', blockIds, proof }   // every block, in PC order
{ kind: 'opaque', blockIds, reason }  // every block that is no conditional test, switch test or loop header
{
  kind: 'conditional',
  testBlockId, condition,               // condition: the solver edge's own object
  branchTargetPc, fallthroughTargetPc,  // the emitter starts the arms here
  mergeBlockId,                         // always named by the planner
  proof,
}
{
  kind: 'natural-loop',
  headerBlockId, bodyBlockIds, continuationBlockId,
  exitTestBlockId,            // the test the loop closes at (loop end step 5); null with no end
  exitTestAtBottom,           // true for a bottom test
  exitTestRunBlockIds,        // a top test's run, header first, in walk order; else null
  continueBlockId,            // null unless the loop publishes a continue target
  updateBlockIds,             // the trailing run, for a loop tested at its header; else null
  testBlockIds,               // the trailing run, for a do-while; else null
  proof,
}
{
  kind: 'try',
  setupBlockId,
  continuationBlockId,        // the reachable end; null when the block never completes normally
                              // or its region does not close
  layoutEndBlockId,           // the accepted frontend hint for a catch without one; else null
  memberBlockIds,             // in startPc order, excluding what either end dominates
  proof,
}
{
  kind: 'switch',
  testBlockId,                // the chain's head
  discriminant,
  cases: [{ testBlockId, value, runBlockIds, stepBlockIds, entryBlockId }], // the head's run is empty
  defaultEntryBlockId, defaultStepBlockIds,
  clauses: [{ caseIndex, entryBlockId }],  // caseIndex null for the default
  continuationBlockId,        // null when every clause leaves by a transfer
  memberBlockIds,
  proof,
}
{
  kind: 'labeled-block',
  headBlockId,                // a loop's header, a try's setup, a switch's head or a conditional's test
  endBlockIds,                // nearest first; each ends one block, the farthest outermost
  innerStopBlockIds,          // a conditional's merge; empty otherwise
  proof,
}
```

A loop's trailing run ends at the back edge's source; a do-while's ends with the test's branch and the
latch. The rows describe the function with overlap, not a disjoint partition of its operations. They
are plain data for the emitter and for inspection; the planner does not freeze them.

### Graph and dominators

`blockGraph` makes one block per case, in PC order, and an adjacency row per solver edge from its
source PC's block to its target PC's block, keeping parallel rows and the solver's edge order. Every
edge needs a source block and, for a non-null target, a target block; otherwise
`invalid-structured-control`. A null target has no successor. A block is reachable when the solver
reaches its case. `dominators` computes, over the reachable blocks from the entry
`${functionRecord.id}:b@${functionRecord.startPc}`,
`dom(v)` as `v` with the blocks common to `dom(p)` of every reachable predecessor `p`.

`FunctionGraph(entry, blocks, edges, solved)` is built once per plan and read by every region
finder: the blocks, `blockGraph`'s graph, the reachable blocks and handler stacks from the solver,
`dominators` over them, the normal edges (`normalAdjacency`, no exceptional route) with their
successor ids by block (`normalSuccessors`), and the jump-step resolver. Its read-only questions:
`dominates`, `membersOf`, `closed`, `normalNext`, `normalPredecessors`, `latchesOf`, `cycleOf`,
`sortedByPc`.

Shared walks read successors as data: `successorMap(adjacency)` gives each block's successor ids.
`walkForward(start, successors, inside, stops)` is breadth-first, never entering `inside` and not
expanding a stop; a block with no entry has no successor. `laterEnds(inside, end, successors,
transfers)` walks from the end (outside `inside`, up to a transfer); for each edge from `inside` to outside it walks from the target the same
way, and the first block also on the end's walk is a landing; landings other than the end or a
transfer are returned, ordered by the end's walk.

### Statement regions

`findStatementRegions(view, switchEnds)` (explanatory pseudocode) over a `FunctionGraph`; the loop
ends are `LoopEnds`', the try ends `TryEnds`', each given the regions found so far:

```text
entries = [loop at each back-edge target, once] + [try at each reachable catch-setup/finally-setup]
sort entries by dominator-set size (stable), so a holding statement is solved first
for each entry:
  if loop:
    end = loopEnd(head)
    if end: (end, blockEnds) = closeLaterExits(head, end); cuts = blockEnds
  if try:
    enclosing = heads and ends of holding loops + switchEnds(head)
    tails = [catchEnd(head, enclosing)] or exitTails(head)
    if no tails and finally-setup: tails = routedEnds(head) minus enclosing
    if several tails: drop enclosing
    cuts = first trailing-run block of each holding loop whose run does not dominate head
    if several tails: drop those leading to such a run through jump steps, unless all do
    end = the remaining tail with the lowest startPc
    if no end: layoutEnd = catchLayoutEnd(head)
    if end or layoutEnd: later ends over the members the end's walk does not reach,
        transfers = transfersFrom(head) + cuts + switchEnds(head);
        if some and the members cut at them close: blockEnds = them; cuts += them
  if end and membersOf(head, end, cuts) does not close: end = null
  if try, end, no blockEnds and loopExitsTo(end, members): blockEnds = [end]
  if try and no end and no layoutEnd: layoutEnd = catchLayoutEnd(head)
  if try with an end: each holding loop cut at its run records the try when a member has a
      normal edge into the run and the run is not the end
  push { head, end, blockEnds, members: membersOf(head, end ?? layoutEnd, cuts), layoutEnd,
         and for a loop: trailingRun(head) }
```

- `membersOf(head, end, cuts)`: reachable blocks the head dominates, less those a cut or the end
  dominates without dominating the head. `closed`: every reachable predecessor of a member is a
  member, except that a head may be entered from outside it, and a try's setup from anywhere.
- `loopEnd`: collects the latches (blocks the header dominates with a normal edge to it) and the
  cycle (the header plus every reachable predecessor chain from a latch). It walks the header's run
  over normal edges; at a block with several normal next steps, a `branch` or `for-in-next` with two
  normal targets, exactly one outside the cycle, gives the exit. Any other branch is closed by
  `closeConditional` with the loop's head and the enclosing loops' heads and ends as stops, and the
  walk resumes at a merge other than the head; with none it stops. Otherwise, with one latch whose
  only in-cycle predecessor gives an exit, that branch is the loop's bottom test. The exit is
  followed through jump steps while it stays outside the cycle. The exit branch is recorded as the
  loop's exit test: at the bottom when it came from the latch, or when its in-cycle target is the
  header or the single latch as a jump step and it is not the header; otherwise at the top, with the
  blocks walked before it (each nested branch with the blocks `walkForward` reaches from its targets
  before its merge) as its run. Only the latch case feeds `trailingRun`.
- `closeLaterExits`: `laterEnds` over the cycle, the transfers being `transfersFrom(head)`: the ends,
  block ends and heads of the regions holding the loop, and a holding try's handler or finalizer
  entry. With exactly one later end, no back-edge target on the walk from the end to it, and no
  `for-in-next` leaving the cycle, it becomes the loop's end; otherwise the loop keeps its end and
  the later ends become its block ends.
- `popsOf`: the `handler-pop` cases whose solver stack (`stateIn`) has the setup's record on top.
- `catchEnd`: for a `catch-setup`, each pop's fallthrough block is followed through jump steps with
  exactly one reachable normal predecessor (`ownSteps`). The catch's walk is every block reached
  from the catch target over normal edges without entering the setup. Of the followed blocks in
  that walk and not in `enclosing`, the end is the one that dominates every other, by `dominators`
  over the walk entered at the target; with none, null.
- `exitTails`: for each pop, a catch record takes the target of the `jump` that follows it. A finally
  record, skipping jumps that do not enter its finalizer, takes the block of the literal of a
  following `assign` whose destination is the record's continuation, through jump steps, when the
  next operation jumps to the finalizer.
- `routedEnds`: for each `assign` of a literal to the setup's continuation with its record on top of
  the stack, the literal's pad through jump steps, when the pad is a jump step or the block reached
  assigns the continuation of the record then on top.
- `catchLayoutEnd`: a `catch-setup`'s `layoutEnd` block, when it is reachable and the catch target
  dominates it and reaches it over normal edges.
- `loopExitsTo(end, members)`: whether a loop whose head is a member leaves its cycle, other than to
  its own `loopEnd`, by an exit landing at `end`: `walkForward` over `exitNext` (each block's exit successors, built once), which passes a
  `handler-pop` or `jump` to its normal successors, takes a literal write to the top finally record's
  continuation straight to that pad, and stops at anything else. An exit that runs code first (a
  `break` to a labeled block's end inside the try) lands there, not at the try's end.
- `trailingRun`: with exactly one latch, start at the latch (for a loop with a bottom test, at that
  test with the latch after it) and walk back. A block with one reachable normal predecessor whose
  only normal next step it is extends the run; a predecessor with several next steps, or reaching
  the header, gives no run. At a block with several normal predecessors, `expressionConditional`
  asks for its immediate dominator: a two-way test other than the header whose arms reach only
  blocks it dominates, share none, leave only to that block, supply all of its normal predecessors,
  are entered only from the test, and contain no `catch-setup`, `finally-setup`, `handler-pop`,
  `indirect-jump`, `return`, `throw` or `for-in-next`. Such a conditional joins the run and the walk
  continues before its test; otherwise the run starts at that block.

### Natural loops

`findNaturalLoops`: for each adjacency edge source -> header with reachable endpoints, header in
dom(source) and source != header, the body is the header's statement region. Exit edges have a body
source and a null or outside-body target; header edges a header source and a body target; both must
be nonempty. One row per header plus body set (the first back edge kept). `bodyBlockIds` are sorted
by startPc; `continuationBlockId` is the region's end or null; the exit-test fields are the region's
recorded test (null, false, null without one). Self-loops are not recognized.

### Switches

`findSwitchRegions`, after loops:

1. **Tests and comparisons.** A test is a block whose last operation is a `branch` with a conditional
   and a fallthrough edge; its match route is the fallthrough when the branch jumps on false, else
   the branch target. Its comparison is the last operation writing the branch's condition: an
   `assign` of a `binary` `===`, after which nothing writes the condition or either operand.
2. **Chains.** A chain's head finds its comparison in its own block or the straight run entering it.
   Each next case is the straight run from a test's miss route to the next test, every run block and
   that test entered only from the one before, with no `branch`, `indirect-jump`, `for-in-next`,
   `return`, `throw`, `catch-setup`, `finally-setup` or `handler-pop`, its comparison inside the run.
   The chain continues while some register is an operand of every comparison. The discriminant is
   the one such register no run operation writes; a captured one also needs runs of `assign` only,
   since a call could run a function that writes it. Without exactly one, the chain drops its last test until it
   has one; fewer than two tests is no chain. A chain another test's chain continues into is not a
   head.
3. **Admission.** A head becomes a switch when a test of its chain gets no merge from
   `closeConditional` over `armAdjacency`.
4. **Entries.** Each case's entry is its match target followed through jump steps (recorded as step
   blocks); the last miss, followed the same way, is the default entry unless it is the end.
5. **End.** Members for a candidate end are the blocks reached from the entries over normal edges,
   and from a `catch-setup` or `finally-setup` also over its own exceptional edge, without entering
   the end or a stop of the loops holding the head; they must exclude the chain and be entered only
   from members or the chain. The end is the candidate (a successor of a member, or an entry) whose
   members exist, exclude it and are fewest; with none, the end is null and the members are
   everything reached, which must still be closed.
6. **Nearer end.** A labeled exit past the tail leaves the tail's members open, so that end lies past
   it. A candidate other than that end or a stop is tried when every entry's walk over normal edges,
   entering neither a stop nor that end, reaches it (an entry equal to it reaches it). Its later
   ends are `laterEnds` over the blocks the entries reach before it that its own walk does not
   reach, the transfers being the stops; with some, and its members closed with them as stops, it
   is a nearer end. The one with fewest members becomes the end, and its later ends a labeled-block
   row headed by the chain's head, nearest first, returned beside the switch rows. Without the
   every-entry condition a block inside a clause, or a clause entry, would take an ordinary `break`
   for a labeled exit.
7. **Clauses.** An entry falls into another when its walk reaches exactly that one other entry before
   the end; reaching two declines the row. Clauses are the cases in chain order, with the default
   inserted at the last position, scanning from the end, where every falling entry's clause group
   (consecutive clauses with one entry) is followed by the group it falls into and no entry forms
   two groups; with no such position, no row.

### Conditionals

Over the two-way tests (`twoWayTests`), in startPc order, skipping switch tests; each test's stops
are `enclosingStops`, its arms walked by `armWalk`, and `closeConditionals` closes each one
(`closeConditional`) until the labeled set stops growing. For each test:

- **Stops**: the heads, ends and trailing-run heads of every loop whose body holds the test; for a
  test among a switch's members, its end and clause entries; for each labeled block whose head
  dominates the test, its ends and (for a test other than its head) its inner stops, those the test
  does not dominate; the end of the innermost try whose members hold the test and not that end; the
  layout end of every try without an end whose members hold the test and not the layout end.
- **Arms** (`armAdjacency`: normal edges plus each `catch-setup`'s edge to its target): the blocks
  reached from each target without entering a stop; an arm starting at a stop is empty and reaches
  that stop.

`closeConditional` (explanatory pseudocode):

```text
common = blocks in both arms
if no common:
  if the arms' reached stops share exactly one: return it
  if the fallthrough arm reaches tryEnd and the branch arm does not: return tryEnd
  fallback = fallthrough target if it is a stop, else the branch target through jump steps
             when that is a stop, else the branch target
  if fallback is an end of a holding labeled block and the arms reach exactly one of its
     inner stops: return that inner stop
  return fallback
dom = dominators over {test} union both arms, entered at the test, normal edges only
return the common block dominating every other common block
    ?? the same among the common blocks that are no jump step
    ?? null
```

A test still without a merge tries each block the branch arm reaches, in breadth-first order, that
the fallthrough arm reaches too. The first one that, added to the stops, closes the test at some
other block, and that a walk from either arm target entering neither a stop nor that merge reaches,
ends a new labeled-block row headed by the test, with that merge as its inner stop. Its further ends
are `laterEnds` over the blocks those walks reach, entering neither a stop, the merge nor the end,
less what the end's own walk reaches, the transfers being the stops. These walks, like the arms,
follow a `catch-setup` into its catch. With no such block the test gets no row.

### Continue targets

`publishContinueTargets`, after conditionals: a loop publishes its trailing run when it recorded a
try, or when a conditional or switch in its body has an arm that reaches the run's first block over
normal edges without entering the holding loops' stops or its merge, where its merge is no such stop
and no other loop holding it ends at the run. A switch's arms are its clause entries and its merge its
end. A published run is `updateBlockIds`, or `testBlockIds` for a do-while.

### Refusals

| Code | When |
|---|---|
| `invalid-structured-control` | a solver edge names a source or target PC no case of the function has (`blockGraph`) |

It is thrown as a `vm-switch` refusal and reaches the public result as thrown
([map](../../pipelines/jsconfuser-vm.md#refusals)). The solver builds its edges from the same
cases, so a [correct model](vm-switch-boundary.md#a-correct-model) never reaches it. Everything else the planner cannot read is not refused
here: a loop without an end, a try without one, a test without a merge are published as they are
(a null field, or no row), and the emitter declines what it cannot write.

## 4. Input Shapes

| Shape | Producer | Treatment |
|---|---|---|
| Cases with typed operations; a `catch-setup` may carry `layoutEnd` | [`lower-switch-model`](../jsconfuser-vm/lower-switch-model.md) | one block per case; the hint places a try without a reachable end |
| `edges` (kind, route, condition), `reachablePcs`, `stateIn` | [`vm-switch-control`](vm-switch-control.md) | the graph, which blocks run, and the handler record on top of each pop; control is not solved again |
| `TRY_END; JUMP` as a catch's exit tail; a finally's tail of pop, literal write and jump to the finalizer; routed pads | encoder step 2 `compiler.compile` ([catch and finally](../../../js-confuser-vm/instruction-set.md#catch-finally-and-abrupt-completion)) | read as typed operations, by position on the solver's stacks |
| Jump steps between any two blocks, and a different step before the same pad | [`normalize-cff-wordcode`](../jsconfuser-vm/normalize-cff-wordcode.md), which keeps every transition it cannot prove a fallthrough as a jump | looked through; a step several routes enter is a location |
| A try whose dead `handler-pop` was dropped, so no `layoutEnd` | [`normalize-self-modifying-wordcode`](../jsconfuser-vm/normalize-self-modifying-wordcode.md#5-known-gaps) | the catch keeps the code only it reaches |

## 5. Known Gaps

- Arbitrary conditional structuring and all-path equivalence are unqualified. Reducible opaque
  regions are intentional output.
- Natural-loop deduplication keeps one back edge per header; self-loops are outside the described
  proof.
- The emitter ends a try where its row does, but reads a try's exit tails and a finally's pads in its
  own try rendering.
- A catch that never completes normally, laid out with the code after the try right behind the pop
  and its jump dropped, declines: "pop, then jump" and "pop, falling through" are the same edge, and
  a pop that falls into code is also how a `return` crosses the try, so it ends nothing
  ([F4](../../../decoding-method/rules.md#f4)). The
  compiler emits that jump, and the CFF frontend keeps every transition it cannot prove a
  fallthrough as a jump, so no frontend hands over the dropped jump.
- The linear row and the opaque row have no case of their own: every cell decodes the same without
  the linear shortcut, and nothing asserts the opaque row's contents.
- `compiled-forms` keeps the switch, label and try sources below by their behaviour; only its loop
  proof breaks this code.

## 6. Source

| File | Holds |
|---|---|
| [plan-statements.js](../../../../decoder/decode-js/src/vm/switch/statements/plan-statements.js) | `planStatements`; `linearRegion`, `findRegions`, `findNaturalLoops`, `findConditionals`, `publishContinueTargets`, `continueStatements`, `opaqueRow`, `tryRows`, `labeledRows` |
| [graph.js](../../../../decoder/decode-js/src/vm/switch/statements/graph.js) | `blockGraph`, `dominators`, `reachableBlockIds`, `walkForward`, `laterEnds`, `successorMap`, `normalAdjacency`, `armAdjacency`, `jumpStepResolver`, `FunctionGraph` |
| [statement-regions.js](../../../../decoder/decode-js/src/vm/switch/statements/statement-regions.js) | `findStatementRegions` (`collectEntries`, `regionOf`, `markContinues`) |
| [loop-ends.js](../../../../decoder/decode-js/src/vm/switch/statements/loop-ends.js) | `LoopEnds` (`bounds`, `loopEnd`, `loopExit`, `nestedClose`, `trailingRun`, `expressionConditional`, `closeLaterExits`), `transfersFrom`, `enclosingLoopStops` |
| [try-ends.js](../../../../decoder/decode-js/src/vm/switch/statements/try-ends.js) | `TryEnds` (`bounds`, `popsOf`, `catchEnd`, `exitTails`, `routedEnds`, `exitNext`, `loopExitsTo`, `catchLayoutEnd`, `tryTails`, `tryLaterEnds`) |
| [conditionals.js](../../../../decoder/decode-js/src/vm/switch/statements/conditionals.js) | `twoWayTests`, `enclosingStops`, `armWalk`, `closeConditional`, `closeConditionals`, `loopStops` |
| [switches.js](../../../../decoder/decode-js/src/vm/switch/statements/switches.js) | `findSwitchRegions` (`SwitchFinder`, `SwitchBodies`) |

Called by `render` in [to-source.js](../../../../decoder/decode-js/src/vm/switch/to-source.js),
after the control solve and before the function's closures are rendered
([backend order](../../pipelines/jsconfuser-vm.md#backend-order)).

## 7. Fixtures

Each suite encodes its sources with the pinned encoder and requires the decode to behave as the
source; a proof is a break of the named code that turns the suite red
([tests.md](../../tests.md#suites)). Suites are under
[cell-suites/](../../../../decoder/decode-js/test/vm/jsconfuser-vm/cell-suites/). The unit files
are in [statements/](../../../../decoder/decode-js/test/vm/switch/single-component/statements/):
each builds a model by hand, renders it through `emitVmSwitchProgram`, runs the output and reads
its form.

| Scenario | Expected result | Committed fixture |
|---|---|---|
| A loop closes where its test exits, whatever ends the function | Decodes; behaves as the source | `compiled-forms`, proof "Natural loops become structured loops, with protected throws, returns through finalizers and compound tests." (removes the loop entries in `statement-regions.js`) |
| A loop's exit test is published: a top test with its run, a short-circuit run, a jump-if-true exit, a do-while with a straight body, a for-in step | The test in the loop's head, no `while (true)` | `loop-ends.test.js`, "a loop is written with its test in its head" |
| A loop whose header run holds a statement, or whose exit arm runs code | `while (true)` kept | `loop-ends.test.js`, "a loop keeps `while (true)` where its test cannot lead it" |
| A do-while's bottom test; a continue through a finally enters it | `do { } while (test)`; behaves as the source | `try-do-while-continue`, its proof (removes `bottomTests.set` in `loop-ends.js`) |
| A loop's update published as the continue target of a `for` | `for (; ; update)` with a native `continue` | |
| Labeled exits past a loop's own exit: several ends, a tail that is a loop, a for-in | A labeled block only where nothing else holds the exit | `labeled-exit-forms`, its proof (the loop's `blockEnds` in `closeLaterExits`); under flattening `single-payload-stage-conditions`, proof `labeled-exit-forms` |
| A nested exit past a tail of several blocks | The labeled block ends where the exit lands | `loop-ends.test.js` |
| A completing catch ends its try where it first reaches a pop's target | Decodes; behaves as the source | `compiled-forms` file `control-try`, by behaviour |
| A catch that never completes ends its try at the jump after the pop, also where the flattener cannot tell the pop's jump from an exit jump | Decodes; behaves as the source | `single-payload-stage-conditions`, proof `cff-loop-return` (removes the catch tail target in `try-ends.js`) |
| A finally with no reachable normal tail ends where its routed exits land | No label; behaves as the source | `try-routed-ends`, its proof (removes `routedEnds` in `tryTails`); under flattening `single-payload-stage-conditions`, proof `try-routed-ends` |
| A try that never completes normally inside a conditional's arm; an arm leaving for the holding try's end | No label; behaves as the source | `try-arm-exits`, its proof (removes the try-end test in `closeApart`); under flattening `single-payload-stage-conditions`, proof `try-arm-exits` |
| Labeled exits out of a try, from its block or its catch, past its tail; from a loop in the try to the try's end; with a layout end | A labeled block around the try; behaves as the source | `try-ends.test.js`; `compiled-forms` file `control-label` (try-exit-past-tail, try-exits-two-ends, catch-exit-past-tail, catch-else-exit-past-tail, exit-before-and-from-try, catch-exit-before-and-from-try, loop-exit-to-try-end, loop-exit-to-completing-try-end, catch-exit-past-throwing-try), by behaviour |
| A try in a switch clause whose block or catch breaks out of the switch | The try inside the clause, a native `break` | `try-ends.test.js`, "a catch's break out of a switch is no end of a try whose tail falls into the next clause"; `compiled-forms` file `control-switch` (try-in-switch-catch-break, try-in-switch-both-break, switch-catch-break-falling-tail), by behaviour |
| A chain with a test lacking a first meeting block is one switch; clauses keep every fallthrough | `switch (`, a `case` per test, no `===` | `switches.test.js`; `compiled-forms` file `control-switch` (f-switch-flow, switch-no-default), by behaviour |
| A switch's own `break` past a later clause | No labeled block | `switches.test.js` |
| A labeled exit past a switch's tail | A labeled block around the switch | `compiled-forms` source `switch-exit-past-tail`, by behaviour |
| A switch whose cases all return | A chain of guards | `compiled-forms` source `terminal-switch-arms`, by behaviour |
| Arms that exit to two nested ends; an inner test breaking a labeled block; a `break` guard in a labeled block | A labeled block for each end; the guard keeps its reading, no `else` | `conditionals.test.js` |
| The worked examples' rows | The rows above | `compiled-forms` cells `f-loop-forms` and `catch-exit-past-tail`; read by hand, nothing asserts a row |
| A function of fallthrough and return edges only | One linear row | |
| An edge naming a PC no case has | `invalid-structured-control` | |
