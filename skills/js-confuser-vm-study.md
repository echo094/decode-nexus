# js-confuser-vm encoder/decoder study

This parent-level note applies the general [encoder/decoder method](encoder-decoder-method.md)
to the pinned JS-Confuser-VM encoder and its target-local `decode-js` reversal. Encoder
mechanisms live in [the encoder package](js-confuser-vm/js-confuser-vm.md); decoder
mechanisms and acceptance live in [the decoder package](decode-js/decode-js.md). This page
owns their pairing, evidence boundaries and future qualification dependencies; it does not
replace either participant's specification.

## Scope

The plugin's goal is recovery of any valid file produced by the pinned JS-Confuser-VM
release, regardless of source program, encoder option vector, or randomized emission.
The reference spine is tag `0.1.5`, encoder revision
`20c5b96bf57337c568579352758d7685358650de`, with optional hardening disabled. The historical
decoder baseline reference is revision `66f79bd3b6335e2b002a94ddefca919305ea19dd`; the current
decoder's finite minified-class qualification boundary is in the
[test index](decode-js/tests.md#finite-minified-class-qualification). The baseline is a
starting representation, not the goal's boundary. The current decoder also has source-defined
routes for selected hardened representations. Retained fixtures support only their asserted
controls; their historical option-effect records are not a fresh all-option qualification.
Earlier releases, untested option combinations, repeated or mixed encoders, and cross-encoder
generalization have no qualification from that spine. Other releases need separate shape and behavior qualification. Runtime
correctness is a bounded regression guard, not evidence that VM structure was recovered.

Build coverage from the encoder outward: inventory compiler/runtime shapes and option
interactions, generate source-feature cases across options and seeds, record provenance,
and compare encoded behavior with executable step-one and recovered step-two output.
Check structural coverage, complete semantic recovery, residue, and atomic decline as
separate axes. Fresh generated cases challenge the implementation beyond committed
fixtures. Finite generated samples do not prove the universal goal by themselves.
An independent VM-2 decoder benchmark remains a separate acceptance step. Generate and
retain its source, encoded input, expected behavior and provenance alongside its test.
Report recovery quality and measured runtime separately; that sample must not define
the plugin's recognition rules or replace generated encoder coverage.

## Fresh qualification tool

The [finite minified-class qualification](decode-js/tests.md#finite-minified-class-qualification)
states the baseline/minify/class/pair axes, per-cell behavior, effect, projection and
state/structure/residue oracles, the mandatory exception trace and the census that re-reads them. The
[finite randomized-class qualification](decode-js/tests.md#finite-randomized-class-qualification)
does the same for randomization with class and final minification, with opcode meaning taken
from the handlers by [Packet A](decode-js/transforms/jsconfuser-vm/extract-container.md).
[Finite PATCH added-opcode qualification](decode-js/tests.md#finite-patch-added-opcode-qualification)
adds the original-width recovery boundary for all subsets of PATCH/alias/macro/specialized/anti
under known source cases and fresh seeds. Its separate emitted/reached census supplies component
credit only with passing one-option-removed peers; specialization can remove macro candidates
from short sources, so the longer array source challenges the surviving-window boundary.
The [finite timing/finalizer boundary](decode-js/tests.md#finite-timing-and-finalizer-qualification)
qualifies recovery for every timing value. Slow host work and process suspension can poison the
encoded program's words, lose parent handlers and leave captures open; timing is interpreter-only
anti-debugging ([timing checks](decode-js/transforms/jsconfuser-vm/timing-checks.md)), so the
decoded program carries none of it and behaves as the source.
Broader stacks and other source/release domains need their own evidence. A tool profile alone is not a qualified population.

The tool is the decoder's own [qualifier](../decoder/decode-js/scripts/qualify-jsconfuser-vm/qualify.mjs), run from the decoder root: the
question it answers is whether the decoder recovers what the encoder emits. It reaches the encoder
through `JSCONFUSER_VM_ENCODER`, any checkout of it, or else through a clone that
[fetch-encoder.mjs](../decoder/decode-js/scripts/qualify-jsconfuser-vm/fetch-encoder.mjs) makes into the decoder's ignored qualification
workspace. Its `PIN` must equal the hub's encoder pin, and every snapshot refuses a checkout at
another commit or with a dirty worktree.

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
  actual coverage/simplification totals, emitted function bindings, an input/output AST difference
  and independent residue checks. A renamed passthrough runtime, surviving dispatcher or fallback,
  or altered coverage refuses; an ordinary user `switch` does not.
- **Input identity.** Tracked inputs are named through Git, never by stored digests: the run
  snapshot records the clean encoder pin, the decoder commit, its `src` tree and `src` status, and
  the qualifier files' status, digesting only uncommitted changes. The qualifier shares the
  decoder's repository, so recovery compares the `src` tree rather than the decoder commit. A run compares
  its start and end snapshots, so a change during the run refuses publication.

[retain_evidence.py](../decoder/decode-js/scripts/qualify-jsconfuser-vm/retain_evidence.py) packs a run's inputs and results into
bounded tar parts and reads every part and member back, refusing missing, extra, duplicate or
changed members and checking exact symlink targets. The archive is not self-contained: Node/JDK
binaries and symlink-target bytes outside the retained trees must be supplied separately.

The recipe below describes tool interfaces; their existence is not permission to run
generation or native tests.

```sh
node scripts/qualify-jsconfuser-vm/qualify.mjs --audit-only
npx vitest run test/scripts/qualify-jsconfuser-vm/qualify.test.js
```

The audit reads source/import bodies, current source/dependency manifests (including symlink
identity and external targets), Node executable, encoder pin/worktree, installed Java release/
executable and Closure jar bytes. It imports trusted Babel dependencies to parse source data;
it neither imports encoder source nor invokes Java. Start/end snapshots detect changed bytes
and relevant worktree state. They do not prove an atomic snapshot or catch a change restored
between checks. Retain these exact input/dependency bytes alongside their manifests for replay.

After independent candidate review and Main's execution gate acceptance, select an explicit
population and physically absent exclusive paths. Uppercase path arguments below are placeholders
for new population/replay directories and a separately verified frozen population. Generation
needs a JDK, taken from `JAVA_HOME` or the first `java` on `PATH` that resolves into one:

```sh
node scripts/qualify-jsconfuser-vm/qualify.mjs --output NEW_POPULATION --cases all --profiles baseline,minify,classObfuscation,minifyClassObfuscation --seeds 172,173,174
node scripts/qualify-jsconfuser-vm/qualify.mjs --replay VERIFIED_FROZEN_POPULATION --output NEW_REPLAY --replay-mode native
npx vitest run test/scripts/qualify-jsconfuser-vm/replay.test.js
```

These are core invocations. Use the reviewed
[capture wrapper](../decoder/decode-js/scripts/qualify-jsconfuser-vm/capture_native_replay.py) and its outer-capture contract
for replay: separate exclusive/noclobber stdout/stderr/start/completion records outside output,
actual argv/UTC/host/runtime/input identities and observed exit/signal/timeout/interruption, including
failure before output creation. Per-cell journals cannot replace outer completion. The wrapper
has no outer timeout of its own; it relies on the core's worker/VM watchdogs. Its signal handling
finalizes records under repeated SIGINT/TERM/HUP with bounded TERM-then-KILL waits on the core's
process group only, not detached worker groups ([fake-process tests](../decoder/decode-js/scripts/qualify-jsconfuser-vm/test_capture_native_replay.py)).
A fatal uncatchable termination of the wrapper itself leaves its metadata unavailable, which is
reported as a failed run and never reconstructed. A long run must also survive the controlling
session being interrupted: start the capture in a new session with stdin closed and inherited
descriptors closed, and reserve its launch record exclusively before spawning, so a record
collision or an early exit cannot lose the launch identity. An interrupted session with no
observed completion record earns no credit, whatever stdout's test summary says. Verify the
summary/manifest pair and all frozen members before/after; partial publication receives no success
and its paths cannot be reused. Original aborted-generation output is not a successful replay root.

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

The CLI retains general defaults: all source cases/profiles and seeds 1–3, with explicit
comma-separated selections or all. Interface compatibility authorizes no additional execution.
The accepted dated matrix qualifies only its explicit four-profile/fresh-seed population; every
selected cell, including a valid baseline decline in any future population, must remain attributable.
The mandatory exceptionRoutes case exercises native JSON.parse SyntaxError, null property
TypeError, explicit Error, return, captured state and finally; it has an independent ordered
expected result. Pair-minus-class is minify; pair-minus-minify is classObfuscation, same
source/seed with every other option explicit. Native known-source observations use a fresh
browser-like context (window/self, performance, atob/btoa; no Buffer/process/require), VM10s and
parent12s. Generation workers have parent65s and Closure60s limits; parser workers have20s.
Node's vm context separates globals but is not a security sandbox, so native observation (and
`--replay` of a frozen population) is only for populations generated from known source cases,
never for untrusted encoded input.

Each exclusive output directory retains sources/options, raw and comment-stripped emissions,
RNG seed/draws/algorithm, process command/exit/stdout/stderr, current public result/output,
raw A/B/C and downstream first refusal, lossless analysis/projection, behavior, state, residue,
effects, and manifests. Tagged serialization/equality preserve undefined/null/NaN/-0 in behavior,
analysis and normalized constant pools. Source-oracle failure, encoder mismatch, generation
error and timeout cannot provide effect controls. `accepted` still needs normalized baseline
agreement and both actual emitted effects before `qualified:true`.

Class effects use constructor/receiver bindings, payload-role permutation and connected
optional-slot scaffold erasure; missing/disconnected evidence is null and an observed absent
component is false. Isolated class is credited by a `payload-role-permutation` witness; the pair
by `connected-optional-slots-erased` against its minify-only control. To reach the payload through
numeric transport, layout follows only a stable, top-level, once-used decoder with the pinned
complete body, a stable disabled mode, the connected base64 helper and a numeric payload used only
by that call; each mismatch refuses with a named `numeric-transport-*` diagnostic rather than
resolving arbitrary array calls. Minify compares byte length with the one-option-removed class control.
Compression cannot supply the class component. Semantic limits in E/H exception routes and
F/G call projection remain explicit even when behavior/coverage agree.

Replay verifies frozen source/encoded inputs, calls the **current** public decoder, and retains
new output/current analysis in a separate revision directory. Historical good decoded output
is comparison data only. Explicit `--replay-mode parser` runs no target behavior and always
leaves qualification false. Native replay rechecks source/encoded/current-output behavior;
current decline or stale-good-output substitution cannot inherit earlier success.

## Method dispositions

| Rule | Durable application or boundary |
|---|---|
| [D2](encoder-decoder-method.md#d2-verify-claims-before-acting-on-them), [D3](encoder-decoder-method.md#d3-instrument-one-real-failure) | Challenge source-derived mechanisms with focused generated behavior and the actual static decoder; instrument the failing layer before assigning cause. Source reading alone is not decoder proof. |
| [F5](encoder-decoder-method.md#f5-one-fix-is-never-the-whole-fix) | Check compiler definitions against runtime handlers in both directions, consume each word exactly, and assert complete recovery and residue inventories. Add equivalent checks for each new representation. |
| [P1](encoder-decoder-method.md#p1-work-in-reverse-encoder-stage-order-each-stage-placed-by-its-last-write) | Follow compiler finalization and serialization dependencies: symbolic register, label and constant forms become numeric words and constant pairs. Decoder dependency order belongs to the target-local recovery contract; opcode number, source order and output size do not order work. Repeated or mixed-encoder virtualization is unexercised and outside this boundary. |
| [P2](encoder-decoder-method.md#p2-attribute-era-boundaries-outward-from-a-closed-version) | One frozen release supports no earlier-release or era claim. Open a version axis only when studying another release. |
| [F7](encoder-decoder-method.md#f7-a-shared-pass-needs-off-path-cases), [F6](encoder-decoder-method.md#f6-revise-the-owning-rule-never-patch-beside-it) | A target-local adapter preserves other callers' contracts. Any shared change requires a consumer and workaround inventory, off-target negatives and a cluster-level design decision. |
| [D4](encoder-decoder-method.md#d4-fix-the-producer-not-the-consumer), [F4](encoder-decoder-method.md#f4-keep-a-guard-only-where-a-real-case-needs-it) | Source admission and semantic/coverage decisions belong to their proof owners; successful immutable records are trusted within the [owned chain](decode-js/transforms/jsconfuser-vm/standalone-diagnosis.md#owned-record-boundary). Diagnose a new residue at its producer, schedule, information route and consumer before widening a matcher. |
| [F1](encoder-decoder-method.md#f1-select-what-the-program-cannot-run-without), [F2](encoder-decoder-method.md#f2-resolve-completely-or-not-at-all), [F3](encoder-decoder-method.md#f3-keep-tree-and-derived-state-consistent) | Structural identity, complete predecessor reconstruction, coverage and atomic preflight precede fresh emission. Compare live derived state with a fresh parse wherever a pass mutates a tree. Partial function, CFG, closure, handler or interpreter state is not published. |
| [M2](encoder-decoder-method.md#m2-measure-residue-what-an-encoder-stage-added-and-the-decode-left) | Size is secondary. Census instruction, operand, target, function, CFG, closure, exception, semantic and VM residue axes; supported output has no VM runtime or wordcode residue. Helper removal needs the complete static proof. |
| [M1](encoder-decoder-method.md#m1-judge-an-output-by-how-it-reads-against-its-source), [M3](encoder-decoder-method.md#m3-freeze-the-corpus) | Keep behavior oracles bounded and freeze generated bytes before comparisons. Ratios, counts and hashes belong to the evidence for that run. |
| [D3](encoder-decoder-method.md#d3-instrument-one-real-failure), combo gaps | Use an isolation matrix only for a combination gap with no place for a [D3](encoder-decoder-method.md#d3-instrument-one-real-failure) breadcrumb. Each hardening combination needs its own representation population and effect controls; source admission is not profile qualification. |

## Pairing and dependency map

Read the encoder's forward dependencies to understand emitted shapes, then the decoder's own
producer/consumer dependencies to understand their recovery. Opcode numbers and option names
are not a recovery schedule. The decoder has no option-profile or qualification-record admission
gate: an untested shape can reach static success, and that success still lacks qualification.

| Concern | Encoder home | Decoder home and dependency |
|---|---|---|
| Program/runtime and serialization | [Compiler order and runtime foundation](js-confuser-vm/js-confuser-vm.md), [container/wordcode](js-confuser-vm/container-wordcode.md) | [A container and representation routes](decode-js/transforms/jsconfuser-vm/extract-container.md), then [B word grammar](decode-js/transforms/jsconfuser-vm/read-wordcode.md) |
| Numeric meanings and ownership | [Instruction set](js-confuser-vm/instruction-set.md) | [C references](decode-js/transforms/jsconfuser-vm/validate-references.md), [D functions](decode-js/transforms/jsconfuser-vm/partition-functions.md), [E CFG](decode-js/transforms/jsconfuser-vm/build-cfg.md) |
| Table/class/minified runtime and encoded payload | [Runtime mechanisms](js-confuser-vm/js-confuser-vm.md#skill-layout) and [source map](js-confuser-vm/source-map.md) | [A producer inventory](decode-js/transforms/jsconfuser-vm/extract-container.md#4-input-shapes); observers/materializers own their complete returned source proof and state |
| Added opcodes and PATCH | [Allocator and opcode mechanisms](js-confuser-vm/transforms/runtime-layout.md), [PATCH producer](js-confuser-vm/transforms/self-modifying-wordcode.md) | [Canonical frontend retries](decode-js/transforms/jsconfuser-vm/standalone-diagnosis.md#canonical-frontend-retries); expansion/compaction and PC maps precede ordinary references/ownership |
| Constants, dispatcher, CFF and strings | [Mechanism directory](js-confuser-vm/js-confuser-vm.md#skill-layout) and [options](js-confuser-vm/options.md) | [B-E producer handoffs](decode-js/plugins/jsconfuser-vm.md#decoder-stage-dependency-map); returned current analyses are reused and absent analyses are filled |
| Calls, captures, exceptions, scalar/property descriptors | [Runtime instruction semantics](js-confuser-vm/instruction-set.md) | [F-J semantic handoff](decode-js/transforms/jsconfuser-vm/standalone-diagnosis.md#semantic-record-handoff) |
| Control, completion and closure/exception plans | [Control/runtime meanings](js-confuser-vm/instruction-set.md) | [K-M plan handoff](decode-js/transforms/jsconfuser-vm/standalone-diagnosis.md#k-m-plan-handoff); sibling analyses with distinct direct inputs |
| Source emission and public output | Encoder output is the source relation to be proved | [Shared typed boundary](decode-js/vm-switch-boundary.md), [standalone publication](decode-js/transforms/jsconfuser-vm/standalone-decode.md), [direct adapter/CLI](decode-js/plugins/jsconfuser-vm.md), [sequential coordination](decode-js/plugins/jsconfuser-vm-sequential.md) |

The [owned-record boundary](decode-js/transforms/jsconfuser-vm/standalone-diagnosis.md#owned-record-boundary)
places source recognition and semantic/coverage decisions with their producer. Successful owned
records are consumed without repeated hypothetical schema checks. A separately supplied typed
switch model crosses its own validation boundary. That validator checks represented consistency;
it does not establish that source implements the model or that native emission is equivalent.

The numeric adapter consumes B/C/D/K and selected L call-target facts. I/J are retained family
projections, not dynamic value stores; M is required at selected completeness gates and retained
internally, but the adapter does not read its rows. The numeric path supplies K controls; the shared
backend requires a supplied plan and never retries a declining function as dispatch. The owning [handoff](decode-js/transforms/jsconfuser-vm/standalone-diagnosis.md#handoff-model)
and [shared emission specification](decode-js/vm-switch-boundary.md) define these limits.

Direct and sequential publication are distinct. The sequential coordinator trusts its two
producers, shares source strings rather than AST state, and adds no strict intermediate parse.
Returned declines publish the original outer string; direct thrown producer errors propagate,
while the CLI catches decode errors before writing. Output and JSON sidecar writes occur in
sequence and have no two-file rollback. These are the [current public contracts](decode-js/plugins/jsconfuser-vm-sequential.md#state-and-cli-boundary),
not the stronger prospective publication obligations of a new frontend.

## Evidence and remaining qualification

The [test index](decode-js/tests.md#testvm--vm-recovery) maps claims to actual assertions;
transform Fixtures sections own the precise evidence boundary. The retained
[qualification metadata](../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/qualification-provenance.md)
binds historical source/encoded byte pairs to recorded observations. Unknown generation dates,
RNG, revisions or dependencies stay unknown; a current pin cannot reconstruct them. Historical
option-effect records without complete retained controls are observations rather than independently
reproducible qualification. Current tests and finite prior corpora do not establish universal support.

| Evidence family | Retained provenance and limitation |
|---|---|
| Encoder container/instructions/runtime | Retired instruction verifier, retired runtime verifier: selected document-first reconstructions plus static source checks; the container foundation has no verifier; no encoder-output or full optimizer qualification |
| Opcode/PATCH and value/control mechanisms | Retired opcode verifier, retired PATCH verifier, retired value/control verifier: bounded synthetic recipes and source checks, with declared supplied infrastructure |
| Decoder frontend and representations | Retired CFG verifier, retired representation verifier, retired normalizer verifier: bounded reduced reconstructions/retained controls; no complete A-M or fresh representation matrix |
| Decoder control mechanisms | Retired control-normalizer verifier, committed [normalizer tests](../decoder/decode-js/test/vm/jsconfuser-vm/) (`normalize-concealed-constants`, `-dispatcher-wordcode`, `-cff-wordcode`, `-string-concealing`): frozen proof, source corrections and selected existing fixtures are distinct evidence |
| F-J semantic records | Retired record verifier, retired field verifier, committed [F-J analysis tests](../decoder/decode-js/test/vm/jsconfuser-vm/) (`build-call-frames`, `analyze-closure-lifetimes`, `-exception-finally`, `-scalar-values`, `-property-collections`): selected projections with supplied scaffolds, not whole source/public/native behavior |
| K-M plans | Retired plan verifier, retired field verifier, committed [K-M emission tests](../decoder/decode-js/test/vm/jsconfuser-vm/) (`emit-structured-control`, `-call-completion`, `-closure-exception`): precise selected fields and permanent original exclusions, not whole-plan/native proof |
| Current finite native qualification | [Qualification boundary](decode-js/tests.md#finite-minified-class-qualification), re-read by the local mandatory fixture test and a fresh tool run; the dated run itself is historical: complete baseline/minify/class/pair population, removed-option effects, current public output/state/residue, normalized comparison and independent mandatory trace. Focused generic shared/local/trusted native regressions and oracle controls pass within their recorded hosts; arbitrary stacks and global equivalence remain excluded. |
| Shared emission and public boundaries | Retired emission/public verifier, retired field verifier: reduced gates, supplied controls and static audits; no production validator/compiler/native/CLI execution qualification |

The retired verifiers were one-off document-first reconstructions, retired once their accepted
findings graduated into the docs; a claim citing one is a historical result with no maintained check.
They did not prove novice readability, full compiler reconstruction, universal source admission,
all-option support or arbitrary host semantics beyond their declared assertions. No new reconstruction or
runtime observation follows from this parent documentation reconciliation; the dated native
record supplies the separate current finite qualification.

Source-defined limitations remain actionable knowledge, not repaired behavior: E/H do not supply
an exhaustive native-operation exception graph; F's returned-target register lookup, G's static
precision/receiver heuristics, J's accessor-step projection and M's terminal-kind overwrite remain
in the [semantic/plan owners](decode-js/transforms/jsconfuser-vm/standalone-diagnosis.md).
The [shared native-semantic gaps](decode-js/vm-switch-boundary.md#5-known-gaps), including
EXP/Math.pow, delete, object publication and host apply differences, preserve
`finalJavaScriptSemantics:false`. Source-only contrasts are not executed counterexamples or new
admission gates.

Remaining work has a dependency order, separate from accepted documentation and retained controls:

The complete-only minified-class admission, bounded acyclic exception region and studied finite
minify/class matrix are accepted in the dated run. Combined selected-suite completion and final
integration have their own captured acceptance boundary; interrupted output earns no suite credit.
Randomized inlined class and its final-minified interaction take their opcode meaning from the
handlers ([Packet A](decode-js/transforms/jsconfuser-vm/extract-container.md)) and have the
separate qualification above. Other layouts and optimizer spellings remain unqualified.
Future implementation requires a separate assignment and gate:

1. Recheck the implemented [PATCH added-opcode source proof](decode-js/transforms/jsconfuser-vm/self-modifying-observation.md)
   through its [finite subset census](decode-js/tests.md#finite-patch-added-opcode-qualification) when
   changing that frontend; other representations and general computed routes remain unqualified.
2. Recheck the [timing/finalizer source proof and finite controls](decode-js/tests.md#finite-timing-and-finalizer-qualification)
   when changing that boundary. Wider stacks and host-clock domains require their own
   qualification.
3. Audit remaining source features and option interactions, recording accepted, valid-declined or
   untested with the first rejecting boundary. Require actual representation populations and
   one-option-removed effect controls; finite success still does not prove every output.
4. Evaluate a fresh independent VM-2 benchmark only after that general numeric qualification.
   Retain its bytes, source, behavior oracle and provenance; recognition may not depend on the sample.
   Integrate accepted decoder changes and update the decoder pin last under the hub pin procedure.

The [future layer-pair architecture](vm2-layer-pair-architecture.md) and
[target-local exact-inner proposal](decode-js/transforms/jsconfuser-vm/exact-inner-recovery.md)
add no active frontend, adapter or admitted benchmark. Cross-decoder comparison/transfer and
reference-output boundaries stay in the [parent comparison](cross-decoder-study.md). Its historical
comparison contract does not qualify the expanded numeric representations documented here.
New production work and further qualification require their own reviewed boundary; the current
handoff remains the main coordinator's checkpoint rather than a duplicate task diary here.

Update a disposition only when qualifying evidence changes its mechanism or scope. Keep
`unexercised`, `not applicable` and `outside scope` distinct. A general method change belongs in
the general method and its keyed incident.
