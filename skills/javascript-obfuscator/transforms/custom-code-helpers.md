# Custom code helpers

One `Preparing` (2) transformer, `CustomCodeHelpersTransformer`, appends runtime code the source
never contained. It owns no shape of its own: it walks a storage of **helper groups** and asks each
to place its own nodes, so the emitted shapes belong to the groups. Four groups are in phase 1's
scope — self-defending, debug protection, console output, and the **calls controller** the other
three each depend on — every one gated on its own option.

`domain-lock` is a fifth group, gated on `domainLock`, which the encoder refuses against a `node`
target. Its option normalizer is recorded here because its 5.4.1 casing change affects the emitted
domain guard; it has its own `E-domainlock-*` axis. The `string-array/` groups are a separate
subsystem placed at the `StringArray` (8) stage, not this one
([string-array.md](string-array.md) and its siblings). **Directory membership is not stage
membership**, and here it is not even transform membership.

`ObfuscatingGuardsTransformer` shares the `Preparing` stage and is not a helper at all: it marks
nodes as ignored rather than emitting any, so it leaves no residue. Stated because the stage
description names it, and looking for its output is otherwise a wasted search.

## 1. Target

**Protection that has to survive being read, so it is placed as ordinary-looking code rather than
as a preamble.** The three protected behaviours are distinct — detect that the file has been
re-spelled (self-defending), resist being stepped through (debug protection), and deny the reader
the program's own console output (console output) — but the placement problem is shared, and the
placement is where the design effort went.

Two consequences show up in every group:

- **A helper is not a statement you can delete.** Each protection is split into a *definition* and
  a *trigger*, and the trigger goes through a shared indirection — the calls controller — whose own
  contract is that the wrapped function runs on the first call and never again. Removing either
  half alone leaves a program that still references the other.
- **A helper does not sit at the top of the file.** The placement walks the program's call graph
  and buries the code inside a function the program actually calls, so the protection reads as part
  of the program's own body rather than as a prologue.

What the transform does not attempt is concealing the helper's *text*. Every group emits a fixed
template, and the only per-encode variation is the identifier names, the choice among a small set
of alternative templates, and where the code lands.

## 2. Algorithm

**The transformer is a dispatcher and the groups do the work.** On *leaving* the `Program` node in
the `Preparing` stage it runs two analyses and then asks every registered group to append:

1. **Analyse.** Build the calls graph (`ICallsGraphData[]`) and the prevailing kind of variable
   declaration for the program.
2. **Initialize each group.** A group whose option is off registers no helpers at all, so the
   option gate is checked twice — once here and once at the append site — and an option that is off
   contributes nothing to any later step.
3. **Append.** Each group places its helpers relative to the calls graph.

At later stages the same transformer offers a generic `appendOn<Stage>Stage` hook, which is how the
string-array groups place their own code much later. No group in this doc uses it: all four append
at `Preparing`.

**Placement is calls-graph-directed, and the two halves deliberately land in different scopes.**
A random index into the top-level calls graph picks a call chain; then

| what | placement | resulting scope |
|---|---|---|
| the protection helper | `getOptimalBlockScope(callsGraph, i)` with unbounded depth — recurse into the first callee repeatedly | the **deepest** function along that chain |
| the calls controller | the same, with depth `1` — stop immediately | the **first** callee, one level up |

so the controller's binding encloses the helper that calls it. **With an empty calls graph both
fall back to the `Program` body**, which is the only way either lands at top level.

**The calls controller is per group, not per program.** Each group that needs one asks the factory
for its own and generates its own name for it, so a file with two protections enabled carries two
structurally identical controller definitions, and one with three carries three. Nothing
deduplicates them.

**Templates are formatted twice — once for placeholders, once for declaration kind.** Placeholder
substitution fills in the generated names and any nested template; then `formatStructure` walks the
resulting nodes and rewrites every `const`/`let` to `var` when the program's prevailing kind is
`var`. So a helper's declaration kind is a property of the *host program*, not of the template, and
the same template emits two spellings.

## 3. Implementation

**The four helper groups and the domain-lock normalization entry.** Names in `{braces}` are placeholders filled with
generated identifiers; the declaration kind follows the host program per item 2. Each row's era is
a row in [versions.md](../versions.md). The optional interval is separated from its stable defining
function because it has its own output boundary.

| Helper | Era | Emitted shape | Placement |
|---|---|---|---|
| calls controller | `E-callsctl-firstcall` | `{cc} = (function(){ let firstCall = true; return function(context, fn){ const rfn = firstCall ? function(){ if(fn){ const res = fn.apply(context, arguments); fn = null; return res } } : function(){}; firstCall = false; return rfn } })()` | prepended to the shallow scope |
| self-defending | `E-selfdef-*` | a `{sd} = {cc}(this, function(){ … })` definition plus a bare `{sd}()` call; the callback body is the one shape here that moves | prepended to the deep scope |
| console output | `E-consoleout-bound-stubs` | `{cod} = {cc}(this, function(){ <globalVariableTemplate> … })` plus `{cod}()`; the body rebinds seven `console` methods to a bound stand-in whose `toString` is taken from the original | prepended to the deep scope |
| debug protection | `E-dbgprot-recursive-counter` | three stable pieces: the `{dp}` **function declaration**, an IIFE calling it through `{cc}`, and the controller | the function is **appended to the `Program` body**; the call goes to the deep scope |
| debug-protection interval | `E-dbgprot-interval-*` | through `3.2.7`, `setInterval(function () { dp(); }, 4000)`; from `4.0.0`, a global-resolver IIFE ending in `that.setInterval(dp, milliseconds)` | the old call is inserted at a random `Program` index; the new IIFE is inserted there instead |
| domain-lock option normalization | `E-domainlock-*` | `DomainLockRule` extracts each configured domain and, from `5.4.1`, lowercases the extracted value before helper generation | option normalization precedes helper placement; this row does not claim a new template |

**Debug protection is the group that does not follow the placement rule**, and it is worth stating
separately because its defining function declaration is appended at top level regardless of the
calls graph, and its optional interval effect is spliced into a random position among the program's
own top-level statements.

**The interval changes independently at `4.0.0`.** Before that release the option is boolean and
the template hard-codes both the global `setInterval` identifier and `4000`; afterwards the option
is a millisecond value, the function is passed directly, and the call is qualified through the
same global-object resolver used by other helpers. The recursive protection function and its
calls-controller trigger do not move. This is why the interval has its own two-row era axis rather
than widening `E-dbgprot-recursive-counter` into a row that describes two incompatible outputs.

**Two templates are chosen at random, per encode, unless the target fixes the choice.** In
`E-helper-global-default`, the console-output body normally opens with a global-object prelude
picked with `pickone` from two alternatives — one using
`let that; try { … } catch(e){ that = window }`, the other a `getGlobal` function expression —
while `browser-no-eval` forces its own `typeof`-based form. `E-helper-global-serviceworker` retains
those arms and adds `const that = typeof global === 'object' ? global : this;` for the new
`service-worker` target, used by both console output and the member-qualified debug interval.
Domain lock requests the same template in source, but its validator rejects the service-worker
target. The default helper still has two seeded shapes at any one era on the corpus's targets
([encoder-decoder-method.md](../../encoder-decoder-method.md)'s S5).

The debugger body has the same structure: an eval-based form using `.constructor('debu' + 'gger')`
for the default targets, and a literal `debugger;` form for `browser-no-eval`.

**The self-defending body is the one shape in this doc that changes inside phase 1**, at
`E-selfdef-search`'s lower bound ([versions.md](../versions.md)); a third era,
`E-selfdef-search-newline-bail`, opens above the phase-1 range:

| Era | Callback body |
|---|---|
| `E-selfdef-regexp` | declares a **nested** function that builds a `RegExp` through `constructor` and returns `!regExp.test({sd})`, then calls it — plus a separate no-eval template of the same shape using `new that.RegExp` |
| `E-selfdef-search` | a **single** `return` of a member-call chain: `{sd}.toString().search(<re>).toString().constructor({sd}).search(<re>)`, and the no-eval template is gone |
| `E-selfdef-search-newline-bail` | the same search chain, preceded by an early return when `{sd}.bind().toString()` contains a newline |

The distinguishing feature survives renaming and string extraction: the earlier era's callback
contains a nested function, the later era's contains none.

**Domain-lock normalization is an input-shape boundary, not a helper-template boundary.** Through
`5.4.0`, the emitted guard retains mixed-case extracted domains. From `E-domainlock-lowercase`,
`DomainLockRule` applies `.toLowerCase()` after `Utils.extractDomainFrom`, so the guard list is
lowercase before the domain-lock group places its helper. Focused `5.4.0`/`5.4.1` cases check the
changed and control forms; their browser-like harness is not a browser-platform claim.

## 4. Downstream Effects

**Everything in this doc is emitted at stage 2, so eight later stages rewrite it.** That is the
defining fact about these shapes: unlike a transform that runs late, a custom code helper is
present in the tree for almost the whole pipeline and is transformed exactly like the program's own
code.

| Later stage | What it does to helper code |
|---|---|
| `DeadCodeInjection` (3) | builds its donor pool from *every* qualifying block in the program, helper blocks included — see below |
| `ControlFlowFlattening` (4) | helper function bodies are ordinary blocks and can be flattened; their string literals can be lifted into an expression storage. **It also re-spells the guard trigger itself** — see below |
| `Converting` (6) | member reads become computed, property names become string literals, `'debu' + 'gger'` is a concatenation like any other |
| `RenameIdentifiers` (7) | every helper-internal name is renamed; the generated outer names were already opaque |
| `StringArray` (8) | every helper string of length ≥ 3 moves into the array, so the regexes, the `console` method list and the `'debu'`/`'gger'` fragments are accessor calls in the emitted file |
| `Simplifying` (9) | helper `if`/`else` bodies collapse into expressions like any other statement |

**The donor-pool interaction is the one worth stating precisely**, because it can copy a helper
into a branch that never runs. The donor gate rejects any block containing a function declaration,
`break`, `continue`, `await`, `yield`, `super` or `for await`, or nesting more than four blocks
deep ([dead-code-injection.md](dead-code-injection.md)):

| Helper block | Eligible as a donor | Why |
|---|---|---|
| debug protection function body | **no** | contains a nested function declaration, which disqualifies the whole block |
| self-defending callback body | **yes** | a single block with none of the prohibited nodes, at either era |
| calls controller's `if (fn) { … }` | **yes** | same |
| console-output callback body | **borderline** | its nesting depends on which global-variable prelude was picked, against the four-block limit |

So a sample can carry a renamed copy of helper code on a dead branch, and the copy is structurally
identical to the original apart from renaming. **This is measured, not merely permitted by the
gates**: read on output where the injected branches are still present, self-defending and
console-output guard statements and the console method list all appear inside dead branches, on
every option profile that enables both features at full strength. The debug-protection function
body never does, which is the gate above behaving as written.

Reading it takes some care, and the two obstacles are worth stating because they are what makes the
question look unanswerable at first. The shapes are keyed on strings the `StringArray` stage has
already swallowed, so they are unreadable on the emitted file; and the injected branch's test folds
to a constant, so anything that evaluates it removes the branch before it can be inspected. The
measurement therefore has to be taken on output whose strings have been resolved and whose
constant branches have *not* been folded away.

**The guard trigger has two emitted spellings, and which one appears is decided by a later stage.**
Item 2's trigger is written `C(this, function () { … })`, but `ControlFlowFlattening`'s call wrapper
treats it as any other call: the callee is displaced into a new first argument and the call is made
through an expression storage entry, so the emitted form becomes
`storage[k](C, this, function () { … })` — three arguments, with `this` at index 1 rather than 0.

| Spelling | Argument list | Appears when |
|---|---|---|
| direct | `(this, fn)` — `this` at index 0 | control-flow flattening is off, or the trigger's own host block was not selected |
| call-wrapped | `(C, this, fn)` — `this` at index 1 | control-flow flattening reaches the trigger's host block |

**Anything keyed on the two-argument form is blind on a flattening profile**, which covers every
preset from `medium` upward. Measured over the corpus's maximal cells at every version column: the
call-wrapped form is the *only* one present there, the direct form appearing zero times — so this
is the common spelling on combined profiles rather than an edge case. It is also why the trigger
cannot be counted on emitted output alone without accounting for both.

## 5. Known Quirks

- **The placement asymmetry is unexplained by the source.** The helper recurses to the deepest
  callee and the controller stops at the first, with no comment saying why. The effect is that the
  controller's binding encloses the helper's, which is necessary — but the code expresses it as two
  different depth arguments rather than as a relationship.
- **The console-output helper names seven methods and replaces all of them with the same stand-in.**
  `log`, `warn`, `info`, `error`, `exception`, `table`, `trace` — `exception` is not a standard
  console method, and `console.exception` is `undefined` in the corpus's runtimes, so that entry
  binds the fallback rather than an original.
- **The stand-in's `__proto__` is assigned**, and its `toString` is rebound to the original
  method's, which is what makes `console.log.toString()` still look native. A deliberate oddity
  rather than a bug, and the reason the block is larger than replacing seven methods requires.
- **The interval helper is the only piece placed at a random *index*** rather than prepended or
  appended, so its position among the program's own top-level statements varies per seed.
- **A group's option is checked in two places** — `initialize` and `appendOnPreparingStage` — and
  the second check is unreachable given the first, since a group with no registered helpers appends
  nothing. Harmless duplication, but it makes the option gate look like it has two meanings.

## Source

Read at `2.19.0` (`314855eb8bb65653b8c292e7a65ffcdc6c39761b`) except where an era row says
otherwise; the pre-`2.19.0` self-defending passages are read at `2.18.1`
(`18f5210871a6574f256938d4ad56e2ac19ac8884`).

- `src/node-transformers/preparing-transformers/CustomCodeHelpersTransformer.ts` — the dispatcher,
  the two analyses, the per-stage append hook
- `src/custom-code-helpers/AbstractCustomCodeHelper.ts` — the template/format/cache protocol and
  the random pick among global-variable templates
- `src/custom-code-helpers/CustomCodeHelperFormatter.ts` — placeholder substitution and the
  prevailing-kind rewrite in item 2
- `src/node/NodeAppender.ts` — `getOptimalBlockScope` and the placement primitives in item 3
- `src/custom-code-helpers/{self-defending,console-output,debug-protection}/group/*.ts` — the three
  groups' option gates and placement
- [`DomainLockRule.ts` at the normalized-domain boundary](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/dd62feadaea6de64eb743eea6ea475949f1c4974/src/options/normalizer-rules/DomainLockRule.ts)
  — the 5.4.1 lowercasing step
- `src/custom-code-helpers/calls-controller/CallsControllerFunctionCodeHelper.ts` and
  `src/custom-code-helpers/common/templates/SingleCallControllerTemplate.ts` — the shared
  indirection
- the `templates/` directory under each group — the emitted bodies quoted in item 3
- [`DebugProtectionFunctionIntervalTemplate.ts` at `E-dbgprot-interval-global-member`'s recorded commit](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/828a190cf80a86227ef77be38e99aad9838aed70/src/custom-code-helpers/debug-protection/templates/debug-protection-function-interval/DebugProtectionFunctionIntervalTemplate.ts) — the member-qualified interval, unchanged from where the era's source opens ([versions.md](../versions.md))
- [`AbstractCustomCodeHelper.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/custom-code-helpers/AbstractCustomCodeHelper.ts),
  [`GlobalVariableTemplate1.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/custom-code-helpers/common/templates/GlobalVariableTemplate1.ts),
  [`GlobalVariableTemplate2.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/custom-code-helpers/common/templates/GlobalVariableTemplate2.ts),
  [`GlobalVariableNoEvalTemplate.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/custom-code-helpers/common/templates/GlobalVariableNoEvalTemplate.ts), and
  [`ConsoleOutputDisableCodeHelper.ts`](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/314855eb8bb65653b8c292e7a65ffcdc6c39761b/src/custom-code-helpers/console-output/ConsoleOutputDisableCodeHelper.ts)
  at `E-helper-global-default`'s recorded commit — the ordinary random selector, its templates,
  and one consumer's target-specific no-eval selection
- [`GlobalVariableServiceWorkerTemplate.ts` at `E-helper-global-serviceworker`'s recorded commit](https://github.com/javascript-obfuscator/javascript-obfuscator/blob/1000402f10f61bd367cd971d55f0f832d940d60e/src/custom-code-helpers/common/templates/GlobalVariableServiceWorkerTemplate.ts) — the target-specific direct resolver

**The file set is not the axis.** Across all 25 release tags in phase 1's range these files change
fourteen times and only **one** change moves an emitted shape: an internal method rename at
`2.10.1`, a type annotation at `2.12.0`, an `estraverse` import path at `2.13.0`, `override`
keywords at `2.14.0`, and at `2.19.0` both a helper-class rename and the self-defending template
rewrite — of which only the template is a boundary.

## Fixtures

| Claim | Where it is read | Era |
|---|---|---|
| the self-defending callback contains a nested function below the boundary and none at it | the corpus's `self-defending` set, all three fixtures, at every column | both |
| the newline bail precedes the search chain and prevents the reserialization hang | focused `5.4.4`/`5.4.5` raw/beautified cases, including no-newline and upstream reserialization controls | `E-selfdef-search-newline-bail` |
| the calls controller is emitted once per enabled group, not once per program | the `preset-low` cells, which enable two protections and no dead-code injection: their only duplicated blocks are the controller's | `E-selfdef-regexp` |
| helper placement is inside a called function, not at `Program` level | the same cells — the helpers sit in the fixtures' own function bodies | both |
| the debug-protection function is appended at `Program` level | the `debug-protection` set at every column | both |
| the interval statement's position varies with the seed | not covered: the corpus fixes one seed per cell, so a position *distribution* has no cell |
| the interval's global-call/member-call boundary | the `debug-protection-interval` set and every interval-bearing shipped/maximal profile at `3.2.2` and `4.1.1` | both `E-dbgprot-interval-*` eras |
| the service-worker direct resolver in both reachable consumers | focused console-output and debug-interval encodes at `4.1.0` and `4.1.1` populate the direct resolver | `E-helper-global-serviceworker` |
| domain-lock extraction lowercases mixed-case domains | focused encoder outputs on both sides of the registry boundary, with mixed-case, URL-like, leading-dot, subdomain and multiple-domain inputs | `E-domainlock-case-preserved`, `E-domainlock-lowercase` |
| the two randomly selected global-variable preludes both occur | not covered as a *pair*: nothing asserts that both alternatives appear across the corpus, only that each cell carries one | both `E-helper-global-*` eras |
| the `browser-no-eval` templates | not covered: the ordinary corpus contains browser and node targets only | `E-helper-global-default` |
