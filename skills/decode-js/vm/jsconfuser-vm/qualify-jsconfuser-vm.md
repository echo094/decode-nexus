# Qualification tool for js-confuser-vm recovery

## 1. Target

The tool is the decoder's own
[qualifier](../../../../decoder/decode-js/scripts/qualify-jsconfuser-vm/qualify.mjs), run from the decoder
root: the question it answers is whether the decoder recovers what the encoder emits. It reaches the
encoder through `JSCONFUSER_VM_ENCODER`, any checkout of it, or else through a clone that
[fetch-encoder.mjs](../../../../decoder/decode-js/scripts/qualify-jsconfuser-vm/fetch-encoder.mjs) makes
into the decoder's ignored qualification workspace, installing the encoder's dependencies from the
committed `encoder-lock.json` with `npm ci`. Its `PIN` must equal the hub's encoder pin, and
every snapshot refuses a checkout at another commit or with a dirty worktree.

The goal it serves is recovery of any valid file the pinned encoder release produces (see the
[plugin target](../../plugins/jsconfuser-vm.md#1-target)). The tool builds that evidence from the encoder
outward: inventory compiler/runtime shapes and option interactions, generate source-feature cases
across options and seeds, record provenance, and compare encoded behaviour with the step-one
review rendering and the recovered step-two output. Structural coverage, complete semantic
recovery, residue and atomic decline are separate axes. Fresh generated cases challenge the
decoder beyond its committed fixtures; finite generated samples do not prove the universal goal,
and historical option-effect records without complete retained controls are observations, not
reproducible qualification.

The populations it has qualified are stated as axes under
[Qualified populations](#qualified-populations): the
[finite minified-class qualification](#finite-minified-class-qualification)
states the baseline/minify/class/pair axes, per-cell behavior, effect, projection and
state/structure/residue oracles, the mandatory exception trace and the census that re-reads them.
The
[finite randomized-class qualification](#finite-randomized-class-qualification)
does the same for randomization with class and final minification, with opcode meaning taken from
the handlers by [`extract-container`](extract-container.md).
[Finite PATCH added-opcode qualification](#finite-patch-added-opcode-qualification)
adds the original-width recovery boundary for all subsets of PATCH/alias/macro/specialized/anti
under known source cases and fresh seeds. Its separate emitted/reached census supplies component
credit only with passing one-option-removed peers; specialization can remove macro candidates from
short sources, so the longer array source challenges the surviving-window boundary. The
[finite timing/finalizer boundary](#finite-timing-and-finalizer-qualification)
qualifies recovery for every timing value. Slow host work and process suspension can poison the
encoded program's words, lose parent handlers and leave captures open; timing is interpreter-only
anti-debugging ([timing checks](timing-checks.md)), so the
decoded program carries none of it and behaves as the source. Broader stacks and other
source/release domains need their own evidence. A tool profile alone is not a qualified population.

## 2. Algorithm

Generation uses the pinned encoder **source** through Node type stripping;
it imports neither encoder nor native target execution when loaded as a pure library.
Five instrument decisions bound what the tool can certify:

- **Lossless codec.** Every own string-keyed data property is serialized with its descriptor,
  including array/Map/Set extras and nonenumerable undefined. Accessors, symbol keys, opaque
  prototypes/values and cycles throw rather than being dropped, and getters are never invoked.
  Equality follows the own-key/value grammar, so frozen records compare with ordinary ones.
- **Replay containment.** The output path resolves its existing ancestors with realpath and keeps
  the nonexistent suffix; replay refuses an output physically inside the frozen input before
  writing anything, so a symlink alias cannot reach frozen bytes.
- **Generation journal.** A synchronous NDJSON journal records events before imports, every RNG
  draw, each Closure attempt/stream/error/close and the parent watchdog's intent. A Closure child
  killed with its worker may have no close event; its exit is then recorded as unavailable, never
  inferred.
- **Output-structure oracle.** Credit needs byte correspondence with the current public output,
  actual coverage/simplification totals (`emitted + safelyEliminated + provenUnreachable` equals
  the instruction count), one emitted function binding and one `statements` entry per function
  less the summary's `unreachableFunctions`, an input/output AST difference and independent
  residue checks. A renamed passthrough runtime, surviving dispatcher or fallback,
  or altered coverage refuses; an ordinary user `switch` does not.
- **Input identity.** Tracked inputs are named through Git, never by stored digests: the run
  snapshot records the clean encoder pin, the decoder commit, its `src` tree and `src` status, and
  the qualifier files' status, digesting only uncommitted changes. The qualifier shares the
  decoder's repository, so recovery compares the `src` tree rather than the decoder commit. A run
  compares its start and end snapshots, so a change during the run refuses publication.

Replay verifies frozen source/encoded inputs, calls the **current** public decoder, and retains
new output/current analysis in a separate revision directory. Historical good decoded output
is comparison data only. Explicit `--replay-mode parser` runs no target behavior and always
leaves qualification false. Native replay rechecks source/encoded/current-output behavior;
current decline or stale-good-output substitution cannot inherit earlier success.

## 3. Implementation

### Evidence retention

[retain_evidence.py](../../../../decoder/decode-js/scripts/qualify-jsconfuser-vm/retain_evidence.py) packs
a run's inputs and results into bounded tar parts and reads every part and member back, refusing
missing, extra, duplicate or changed members and checking exact symlink targets.

### Audit, generation and replay recipes

The recipe below describes tool interfaces; their existence is not permission to run
generation or native tests.

```sh
node scripts/qualify-jsconfuser-vm/qualify.mjs --audit-only
npx vitest run test/scripts/qualify-jsconfuser-vm/qualify.test.js
```

The audit reads source/import bodies, current source/dependency manifests (including symlink
identity and external targets), Node executable, encoder pin/worktree, installed Java release/
executable and Closure jar bytes. It imports trusted Babel dependencies to parse source data; it
neither imports encoder source nor invokes Java. Start/end snapshots detect changed bytes and
relevant worktree state. Retain these exact input/dependency bytes alongside their manifests for
replay.

Select an explicit
population and physically absent exclusive paths. Uppercase path arguments below are placeholders
for new population/replay directories and a separately verified frozen population. Generation
needs a JDK, taken from `JAVA_HOME` or the first `java` on `PATH` that resolves into one:

```sh
node scripts/qualify-jsconfuser-vm/qualify.mjs --output NEW_POPULATION --cases all --profiles baseline,minify,classObfuscation,minifyClassObfuscation --seeds 172,173,174
node scripts/qualify-jsconfuser-vm/qualify.mjs --replay VERIFIED_FROZEN_POPULATION --output NEW_REPLAY --replay-mode native
npx vitest run test/scripts/qualify-jsconfuser-vm/replay.test.js
```

These are core invocations. Use the reviewed
[capture wrapper](../../../../decoder/decode-js/scripts/qualify-jsconfuser-vm/capture_native_replay.py)
and its outer-capture contract for replay: separate exclusive/noclobber
stdout/stderr/start/completion records outside output, actual argv/UTC/host/runtime/input identities
and observed exit/signal/timeout/interruption, including failure before output creation. Per-cell
journals cannot replace outer completion. The wrapper has no outer timeout of its own; it relies on
the core's worker/VM watchdogs. Its signal handling finalizes records under repeated SIGINT/TERM/HUP
with bounded TERM-then-KILL waits on the core's process group only, not detached worker groups
([fake-process tests](../../../../decoder/decode-js/scripts/qualify-jsconfuser-vm/test_capture_native_replay.py)).
A fatal uncatchable termination of the wrapper itself leaves its metadata unavailable, which is
reported as a failed run and never reconstructed. A long run must also survive the controlling
session being interrupted: start the capture in a new session with stdin closed and inherited
descriptors closed, and reserve its launch record exclusively before spawning, so a record collision
or an early exit cannot lose the launch identity. An interrupted session with no observed completion
record earns no credit, whatever stdout's test summary says. Verify the summary/manifest pair and
all frozen members before/after; partial publication receives no success and its paths cannot be
reused. Original aborted-generation output is not a successful replay root.

A generation whose aggregate publication aborted can be finalized without regeneration by
`--recover RAW --raw-manifest MANIFEST --recovery-boundary BOUNDARY --output NEW`. It is pure
finalization: no worker, encoder import, Java or target execution. It requires the external raw
manifest's exact digest and a pre-edit boundary proving the original abort and absent
publication; the current execution boundary must match except the three recovery tool files,
which it reads from `git diff` against the original run's commit, so that run's qualifier tools
must have been committed.
Rows stay compact and cells are finalized one case/seed group at a time, so memory is bounded by
one group rather than the population. Each recomputed disposition must equal the stored one
exactly (`assertStoredDisposition`) or nothing is published. The summary is labelled
`recovered-finalization-of-aborted-run` with `currentNativeReplayRequired: true`: recovered
dispositions are history, never current qualification, and only a native replay of the
recovered inputs can qualify them. Summary and manifest are a publication pair, not an atomic
transaction, so a partial pair marks the directory failed and unusable.

### Defaults, limits and the mandatory case

The CLI retains general defaults: all source cases/profiles and seeds 1–3, with explicit
comma-separated selections or all. Interface compatibility authorizes no additional execution. The
accepted dated matrix qualifies only its explicit four-profile/fresh-seed population; every selected
cell, including a valid baseline decline in any future population, must remain attributable. The
mandatory exceptionRoutes case exercises native JSON.parse SyntaxError, null property TypeError,
explicit Error, return, captured state and finally; it has an independent ordered expected result.
Pair-minus-class is minify; pair-minus-minify is classObfuscation, same source/seed with every other
option explicit. Native known-source observations use a fresh browser-like context (window/self,
performance, atob/btoa; no Buffer/process/require), VM10s and parent12s. Generation workers have
parent65s and Closure60s limits; parser workers have20s.


### Retained outputs

Each exclusive output directory retains sources/options, raw and comment-stripped emissions, RNG
seed/draws/algorithm, process command/exit/stdout/stderr, current public result/output, raw
`extract-container`, `read-wordcode` and `validate-references` and downstream first refusal,
lossless analysis/projection, behavior, state, residue, effects, and manifests. Tagged
serialization/equality preserve undefined/null/NaN/-0 in behavior, analysis and normalized constant
pools. Source-oracle failure, encoder mismatch, generation error and timeout cannot provide effect
controls. `accepted` still needs normalized baseline agreement and both actual emitted effects
before `qualified:true`.

### Effect witnesses

Class effects use constructor/receiver bindings, payload-role permutation and connected
optional-slot scaffold erasure; missing/disconnected evidence is null and an observed absent
component is false. Isolated class is credited by a `payload-role-permutation` witness; the pair by
`connected-optional-slots-erased` against its minify-only control. To reach the payload through
numeric transport, layout follows only a stable, top-level, once-used decoder with the pinned
complete body, a stable disabled mode, the connected base64 helper and a numeric payload used only
by that call; each mismatch refuses with a named `numeric-transport-*` diagnostic rather than
resolving arbitrary array calls. Minify compares byte length with the one-option-removed class
control. Compression cannot supply the class component. Semantic limits in the [control solver's](../switch/vm-switch-control.md) exception routes
remain explicit even when behavior/coverage agree.

### Qualified populations

Each population is stated as axes rather than as a run, with the census that re-reads it.

#### Finite minified-class qualification

This is the qualification boundary for final runtime minification and class obfuscation, stated
as axes rather than as a run. Each cell is one source case, one profile and one seed, encoded by
the pinned encoder and decoded by the current public adapter.

| Axis | Covered |
|---|---|
| Source cases | The fourteen qualifier cases arithmetic, branches, closures, nestedStrings, collections, repeatedArrays, switch, forIn, methods, tryCatch, throwCatch, tryFinally, exceptions and the mandatory exceptionRoutes (spread is outside this boundary) |
| Profiles | baseline, minify, classObfuscation and minifyClassObfuscation; every other representation option explicitly false, target browser |
| Seeds | 172, 173, 174 |
| Per-cell oracle | Source, encoded and current decoded output agree in a fresh browser-like VM context; normalized projection agrees with the same-seed baseline; public parse/state/coverage/structure/residue checks pass; each enabled option's emitted effect is observed, the pair crediting both components against its one-option-removed controls |
| Mandatory trace | Every exceptionRoutes cell reproduces the independent expected trace (`exceptionExpected` in [qualify.mjs](../../../../decoder/decode-js/scripts/qualify-jsconfuser-vm/qualify.mjs)) for source, encoded and current output |
| Required controls | The [replay oracle controls](../../../../decoder/decode-js/test/scripts/qualify-jsconfuser-vm/replay.test.js) fail a wrong current output despite good historical bytes and never observe a current decline |
| Excluded | Missing native property/coercion exception edges, other option stacks and global JavaScript equivalence; `finalJavaScriptSemantics` stays false |

**Census and expected outcome.** No committed test re-reads this population; the suites
`minify-over-*`, `class-rewrite-over-*`, `interpreter-rewrite-*` and `runtime-rewrites-chain` decode
minified and class runtimes at their own seeds ([tests.md](../../tests.md#suites)). The whole population is re-read by a fresh generation and native
replay with the [qualification tool](../../../../decoder/decode-js/scripts/qualify-jsconfuser-vm/qualify.mjs) (`--profiles baseline,minify,classObfuscation,minifyClassObfuscation --seeds 172,173,174`, then `--replay-mode native`);
every cell must be accepted and qualified, with both pair components observed. One such run
qualified every cell on the decoder at that time; it is a historical result, because its decoder
branch was unpushed and its Node/Java/Closure toolchain unpinned, so its counts are not
reproducible and its frozen population is not maintained evidence.

#### Finite randomized-class qualification

This is the qualification boundary for opcode/layout randomization combined with class
obfuscation and final minification, with opcode meaning from the handlers
([`extract-container`](extract-container.md)). Cells are
formed as in the minified-class boundary above.

| Axis | Covered |
|---|---|
| Source cases | arithmetic, spread (under randomization its payload carries a noncanonical CALL_SPREAD sentinel) and the mandatory exceptionRoutes |
| Profiles | baseline, randomizeOpcodes, minify, classObfuscation, randomizeOpcodesClassObfuscation, randomizeOpcodesMinify, minifyClassObfuscation and randomizeOpcodesClassObfuscationMinify; every other representation option and timingChecks explicitly false, target browser. The single- and two-option profiles are the removal controls of the pair and the triple |
| Seeds | 191, 192, 193 |
| Accepted-cell oracle | Complete `extract-container` and `read-wordcode` admission; `read-wordcode` consumes every canonical word; the canonical instruction/operand/root/pool projection equals the same-case/seed baseline; the input AST and bindings are unchanged; public output is fresh, differs from the input, parses, has consistent consumed derived state, fresh simplification state and zero VM residue; source, encoded and decoded output agree in a fresh browser-like VM context. Every enabled option's emitted effect is observed independently of recovery, and each pair/triple has all its one-option-removed counterparts |
| Declined-cell oracle | Enabled effects observed and source/encoded behavior agreeing; public decoding returns the exact input with the first declining component's diagnostic named; no recovery or decoded-behavior credit |
| Mandatory trace | Every exceptionRoutes cell, accepted decoded output included, reproduces the independent expected trace (`exceptionExpected` in [qualify.mjs](../../../../decoder/decode-js/scripts/qualify-jsconfuser-vm/qualify.mjs)) |
| Required controls | Every cell runs under randomized opcodes, and `interpreter-rewrite-seeded` proves the opcode table is the one matched from the runtime under randomized and shuffled opcodes; no case remaps the disabled-timing `op = JUMP` literal. This supplies no timing qualification |
| Recorded declines | None: randomizeOpcodesMinify, where no randomized map survives minify, is accepted because the handlers name the words |
| Excluded | Other layouts, option stacks and optimizer spellings; added opcodes under PATCH, timing/finalizers; CLI, subprocess backend and sequential pipeline families; [control solver](../switch/vm-switch-control.md) semantic limits and global JavaScript equivalence. `finalJavaScriptSemantics` stays false |

**Census and expected outcome.** Regenerate with the
[qualification tool](../../../../decoder/decode-js/scripts/qualify-jsconfuser-vm/qualify.mjs) (`--cases arithmetic,spread,exceptionRoutes --profiles <the eight above> --seeds 191,192,193`,
then `--replay-mode native`). Every pair/triple cell must be accepted with all its
components observed; every other cell must be accepted, and a decline is a finding. A run on the
decoder with handler meaning matched this outcome. It is a historical result for the same reasons
as above: unpushed decoder branch, unpinned Node/Java/Closure toolchain.

#### Finite PATCH added-opcode qualification

A change to the PATCH or added-opcode frontend reruns this census; other representations and
general computed routes remain unqualified.

This boundary qualifies original-width PATCH recovery through aliases, macros, specialized
and anti-instrumentation instructions. It is separate from the earlier representation matrices.
The maintained [PATCH qualifier](../../../../decoder/decode-js/scripts/qualify-jsconfuser-vm/patch.mjs)
writes its protocol before generation and applies the current public adapter to each new input.

No committed test re-reads this population; `patch-widths-chain` and `self-modifying-patch-stack`
hold PATCH regions over the added-opcode stages ([tests.md](../../tests.md#suites)).

| Axis | Required census / oracle |
|---|---|
| Source cases | arithmetic, closures, tryFinally and patchArrays from the maintained config; the longer array case preserves repeated canonical windows after specialization takes its first four signatures per opcode |
| Profiles | Every subset of selfModifying, aliasedOpcodes, macroOpcodes, specializedOpcodes and antiInstrumentation, including baseline and all one-option-removed controls; target browser, all other representation/timing options explicitly false |
| Seeds | 211, 212, 213, using the checked-in mulberry32 generator |
| Recovery | Source, encoded and current decoded output agree in fresh browser-like VM contexts; output differs, parses, passes independent residue/coverage/simplification checks and consumed derived-state checks; input AST/bindings stay unchanged |
| Effects | Separate emitted handler counts from reached PATCH/added-opcode headers and kinds inside decrypted regions. Each enabled option must be reached in an effect-qualified cell and absent from its same-source/seed removal peer, which must itself pass recovery. A requested option without a reached instruction supplies no component credit |
| Population acceptance | Every cell passes recovery; every subset has at least one cell reaching all enabled components with qualifying removal peers. Short-source cells may recover without full effect credit; profileWitnesses must not be empty. A new decline is a finding with public and PATCH-normalizer diagnostics, not an invalid-encoder verdict |
| Required controls | The named-diagnostic oracle must reject success and a different diagnostic, and the behavior oracle must reject wrong current output. The width-removal, source-damage and nonterminal JUMP_REG controls have no committed test |
| State | Retained pairs, arithmetic/finally stacks and counted-array macros compare the PATCH stage's returned `read-wordcode` (null while added opcodes remain) to a fresh parse of its container, plus public fresh output/binding/residue checks |
| Limits | Numeric nonminified runtime in this population; dispatcher, CFF and string-concealing layers are covered only by the `flattened-self-modifying`, `flattened-self-modifying-dispatcher` and `self-modifying-dispatcher-anti` suites; no added-opcode minified/class/randomized/transport qualification, timing/finalizer hardening, arbitrary host semantics or [control solver](../switch/vm-switch-control.md) gap closure. finalJavaScriptSemantics remains false |

From the decoder root, run the focused controls, then use a physically absent output directory:

```sh
npx vitest run --coverage.enabled=false test/vm/jsconfuser-vm/generated-cells/patch-widths-chain test/vm/jsconfuser-vm/generated-cells/self-modifying-patch-stack
node scripts/qualify-jsconfuser-vm/patch.mjs NEW_POPULATION
```

Toolchain: Node 26.10.0, JDK 27 and Closure 20260216.0.0. The tool requires the encoder at its explicit PIN, a JDK supplied through
JAVA_HOME or PATH, and the installed Closure dependency. Its protocol records Node/JDK/dependency identities and
the starting encoder/source/tool/dependency snapshot and requires an equal snapshot at completion. Do not edit those inputs or run tools that
write dependency caches during qualification. Each worker must complete with exit zero and no
signal/timeout; native VM execution is limited to 10 seconds, its parent to 12 seconds,
inspection to 20 seconds and generation to 65 seconds (Closure has 60 seconds). Native
execution is restricted to these known generated sources. Process completion and unchanged
snapshot are required; partial output receives no population credit.

The short arithmetic source can emit no macros when specializedOpcodes is enabled without anti.
Specialization selects even single-occurrence signatures and admits four signatures per opcode;
macro selection then sees only surviving canonical windows. patchArrays supplies enough distinct
constant-load sites to leave repeated eligible windows after that cap. The census decides which
cells reach macros; anti insertion can preserve eligible windows but does not guarantee macro
emission for every seed. Requesting the option or comparing serialized bytecode is insufficient.
A finite generated run and retained controls do not establish universal option support.

#### Finite timing and finalizer qualification

A change to the timing or finalizer boundary reruns these controls; wider stacks and host-clock
domains need their own qualification.

The [timing-checks contract](timing-checks.md) qualifies
recovery for every timing value: timing checks live in the interpreter only, so the decoded
program must behave as the source under fast, slow and paused execution, while the encoded
active program poisons. Interpreter RETURN, capture-close and exception unwind are the finalizers
at issue.
Compiler and qualifier finalization are separate mechanisms.

| Axis | Required census / oracle |
|---|---|
| Known source cases | arithmetic and finalizers from [timing.mjs](../../../../decoder/decode-js/scripts/qualify-jsconfuser-vm/timing.mjs); finalizers exposes a captured value, calls a controlled host pause inside a child frame with a parent finally region, and independently expects `[7,true,7]` |
| Profiles | baseline/timing; full selfModifying+aliasedOpcodes+macroOpcodes+specializedOpcodes+antiInstrumentation stack with/without timing; base64 encodeBytecode with/without timing; handlerTable with/without timing. Every other representation option explicitly false; target browser |
| Seeds / thresholds | 231, 232, 233, mulberry32; enabled threshold 100 ms. The decode controls additionally cover false, 0, -0, 1000 (strict-true serialization) and -1; NaN and infinities are untested |
| Emitted / reached effects | Observe scalar value, numeric transport and table scaffold independently. PATCH census distinguishes emitted added-opcode handlers from reached PATCH/added-opcode words on an observation-only disabled clone. Each active cell has a timing-disabled peer with the same seed. A missing requested option gives no full PATCH component credit; the prior PATCH subset census owns those added-opcode claims |
| Controlled clocks | Every successive delta exactly 100 ms preserves the independent source behavior; one initial delta 101 ms followed by a frozen clock poisons and reaches the unknown-opcode error. Repeated above-threshold deltas may keep forcing JUMP and time out instead; no guaranteed halt is claimed |
| Real clocks | Fresh browser-like VM (window/self, atob/btoa, nonthrowing performance.now). Fast source/encoded behavior agrees. Finalizers additionally uses 250 ms synchronous host work and child SIGSTOP/parent SIGCONT after 250 ms. Completion, signal records and measured blocked duration are required |
| Recovery | Every cell: current public output differs, parses, passes coverage/residue/fresh simplification and consumed binding checks, input AST/bindings unchanged; decoded behavior equals source for fast/slow/paused modes. Disabled cells: encoded behavior also agrees. Passthrough fails recovery |
| Active encoded effect | Slow/paused encoded execution differs from source: words zero, parent finally marker absent, current frame lost, an open current-frame scalar capture with undefined backing; surviving root callable captures are type-only census. This confirms the requested effect was emitted |
| Decode / oracle controls | `timing-runtime-chain` and `interpreter-rewrite-fixed` decode timing through the rewritten runtime and alone; the other timing values, threshold equality and a renamed close method have no committed test. [Timing instrument controls](../../../../decoder/decode-js/test/scripts/qualify-jsconfuser-vm/timing.test.js) pin present/absent/active/damaged table effects, observed real stop/resume and wrong-behavior rejection |
| Retained replay | None: the seed 231 replay and its fixture are not kept; `timing-runtime-chain` proves finalizer throw pads under timing, patch, encoded and table runtimes |
| Top-level finally | `compiled-forms` decodes the `top-level-finally` source as it behaves, plain compiled code only; no clock is applied to it |
| Excluded | Arbitrary side-effecting/throwing performance globals; minified/class/randomized timing stacks, other option combinations/releases, CLI/sequential/subprocess backends and [control solver](../switch/vm-switch-control.md) gap closure. finalJavaScriptSemantics stays false |

Run focused controls before generation, then use a physically absent population path:

```sh
npx vitest run --coverage.enabled=false test/vm/jsconfuser-vm/generated-cells/timing-runtime-chain test/scripts/qualify-jsconfuser-vm/timing.test.js
node scripts/qualify-jsconfuser-vm/timing.mjs NEW_POPULATION
```

Generation uses the explicit encoder PIN and installed Node/JDK/Closure supplied through PATH or
JAVA_HOME. Protocol is written before generation and records the complete input/tool/dependency
snapshot; it must equal the final snapshot. Per-worker completion must have exit zero, no signal
and no timeout. The native VM limit is 10 seconds and its parent 12 seconds; generation is 65
seconds (Closure 60 seconds) and inspection 20 seconds. An outer
[capture command](../../../../decoder/decode-js/scripts/qualify-jsconfuser-vm/capture_command.py) records
actual whole-tool exit/signal/timeout. Cell and summary readbacks must equal the just-produced
records. Do not edit consumed source/tools or change dependencies during qualification. Native
execution is only for these known generated sources. A failed/partial run earns no population credit.

The generation tool owns the population axes and process checks.

Disabled timing still reads performance.now once per runtime invocation. The recovered program
omits that host bookkeeping; callable, nonthrowing, observationally inert clock reads are a stated
native assumption, not a globally proved source property. Static input admission and a finite
successful run cannot establish arbitrary JavaScript host equivalence.

## 5. Known Gaps

- The archive is not self-contained: Node/JDK binaries and symlink-target bytes outside the retained
  trees must be supplied separately.
- The audit's start/end snapshots do not prove an atomic snapshot or catch a change restored between
  checks.
- Node's vm context separates globals but is not a security sandbox, so native observation (and
  `--replay` of a frozen population) is only for populations generated from known source cases,
  never for untrusted encoded input.
- Each finite population qualifies only itself; other option stacks, releases and representations
  need their own populations ([qualified populations](#qualified-populations) states each
  boundary).

## Source

All under
[`scripts/qualify-jsconfuser-vm/`](../../../../decoder/decode-js/scripts/qualify-jsconfuser-vm/):
`qualify.mjs` (CLI: audit, generation, replay, recovery), `fetch-encoder.mjs` (pinned encoder
checkout), `audit.mjs`, `generation.mjs`, `worker.mjs`, `codec.mjs`, `oracles.mjs`, `effects.mjs`,
`layout.mjs`, `patch.mjs`, `timing.mjs`, `timing-observation.mjs`, `finalize.mjs`, `config.mjs`,
`retain_evidence.py`, `capture_native_replay.py` and
`capture_command.py`.

The numeric-transport layout in `layout.mjs` identifies the pinned base64 helper by
`runtimeSignature`, compared with `BASE64_SHA256`
([runtime-source-signature.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/runtime-source-signature.js)):
a digest of the helper's parameters and body with positions and comments dropped and bindings
numbered. The module sits under the decoder's `src/vm/` but no decoder component imports it.

## Fixtures

| Committed test | Claim pinned |
|---|---|
| [qualify.test.js](../../../../decoder/decode-js/test/scripts/qualify-jsconfuser-vm/qualify.test.js) | Compound effects need every observed component and its controls; class witnesses follow bindings and compression cannot supply them; encoder failures supply no controls; publication refuses changed bytes, revisions, pin or worktree; codec and journal retention; output structure rejects surviving dispatch; finalization and recovery refuse changed or incomplete cells |
| [oracles.test.js](../../../../decoder/decode-js/test/scripts/qualify-jsconfuser-vm/oracles.test.js) | Lossless codec keeps nonenumerable keys; output oracle refuses a renamed dispatcher passthrough; replay containment resolves symlink ancestors |
| [replay.test.js](../../../../decoder/decode-js/test/scripts/qualify-jsconfuser-vm/replay.test.js) | Historical good output cannot hide wrong current behaviour; a current decline cannot inherit historical success |
| [frontend.test.js](../../../../decoder/decode-js/test/scripts/qualify-jsconfuser-vm/frontend.test.js) | Every enabled component has its frozen removed-option control; numeric transport is followed only through its exact bindings |
| [timing.test.js](../../../../decoder/decode-js/test/scripts/qualify-jsconfuser-vm/timing.test.js) | Transport/table effect detection with and without active timing; a real pause's stop/resume |
| [test_capture_native_replay.py](../../../../decoder/decode-js/scripts/qualify-jsconfuser-vm/test_capture_native_replay.py) | Capture records under completion, launch failure, races, repeated signals and bounded termination |
| [test_retain_evidence.py](../../../../decoder/decode-js/scripts/qualify-jsconfuser-vm/test_retain_evidence.py) | Multipart archive bytes and symlink targets read back exactly |
