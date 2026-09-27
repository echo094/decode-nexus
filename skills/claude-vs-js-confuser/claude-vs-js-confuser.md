# Claude vs. JS-Confuser corpus

This package records bounded, source-cited knowledge from a read-only corpus of
agent-generated, experiment-specific JavaScript deobfuscators. It preserves the experiments as
prior art and graduates mechanism observations with an explicit source, configuration, result and
boundary. It does not claim universal coverage, recover destroyed names or comments, or turn an
exact-example script into a maintained decoder.

## Scope and boundary

The corpus is pinned in the hub at
[`e90be6ca716e28f4bba91fe39615a665656bd802`](https://github.com/MichaelXF/claude-vs-js-confuser/tree/e90be6ca716e28f4bba91fe39615a665656bd802).
The complete experiment inventory is in [experiment-registry.md](experiment-registry.md), and
the reverse coverage map is in [source-map.md](source-map.md).

The pinned corpus supplies experiment scripts, exact examples and regular controls. The
[experiment registry](experiment-registry.md) records the available encoder profiles and missing
provenance. Generated examples are temporary unless a specific claim requires retained bytes.

## Evidence model

| Evidence layer | What it establishes | Boundary |
| --- | --- | --- |
| Pinned corpus source | The experiment script, test and note at the reviewed revision | Source inspection alone does not prove execution or transfer. |
| Supplied exact example | A result on the retained input and its named control | The result does not establish another source shape or encoder configuration. |
| Bounded behavior oracle | Equivalence of specified deterministic observables | Behavior does not prove structural readability or full source reconstruction. |

The primary oracle for a recovered result is fresh parse validity, mechanism-specific structure,
and a source-operation census. Behavior is a separate bounded check. A positive claim must retain
its input provenance and name the exact example or qualified population it covers.

### Document-level evidence labels

Every algorithm-bearing plugin or transform page in this package carries one of these labels near
its scope statement:

| Label | Required content | Boundary |
| --- | --- | --- |
| `source-inspection only` | Pinned source paths, implementation symbols, the solution-level algorithm, concrete input/output shapes and known assumptions | Source and notes support the documented deduction; no execution, transfer, decoder coverage or production-adoption claim is implied |
| `empirical` | Source/configuration identity, exact example or transfer population, named oracle, observed result and retained-evidence rule | The label is incomplete without its stated boundary; it applies only to the named evidence cell and does not imply another configuration, broad correctness or production coverage |

An empirical page must say whether its result is exact-example, same-configuration transfer,
qualified decline or another bounded cell. A harness-controlled random source is verification
input, not encoder seed support. A source-inspection-only page remains valuable when execution is
unavailable or transfer is unqualified; those are independent statuses rather than reasons to
discard the algorithm.

## Working procedure

1. Read the plugin or transform page and registry row for the relevant experiment.
2. Inspect the pinned source, exact example and regular control. Confirm the source paths and
   configuration boundary cited by the algorithm page.
3. Record parse validity, mechanism residue, recovered operations and bounded behavior separately.
   Keep exact-example results distinct from results on newly generated inputs. A byte-changing
   rewrite of a negative input is not a byte-preserving decline.
4. Add a reviewed registry and source-map entry when an experiment or option boundary changes.
   Plugin roots describe composition; transform pages own the algorithm and implementation.

## Package layout

| Path | Purpose |
| --- | --- |
| `claude-vs-js-confuser.md` | Scope, evidence model and use of the package |
| `plugins/<plugin>.md` | One root per graduated corpus plugin; ordered transform links, composition, plugin-level inputs/outputs and boundaries |
| `transforms/<transform>.md` | One solution-level algorithm page per genuinely distinct transform, with source, implementation, dependencies, assumptions, evidence and fixtures |
| [`plugins/vm-1.md`](plugins/vm-1.md) | VM-1 source-inspection-only plugin composition and bounded emission/fallback boundary |
| [`plugins/vm-2.md`](plugins/vm-2.md) | VM-2 plugin composition and bounded execution/fallback boundary |
| [`plugins/vm-3.md`](plugins/vm-3.md) | VM-3 source-inspection-only plugin composition and bounded specialization/fallback boundary |
| [`plugins/vm-4.md`](plugins/vm-4.md) | VM-4 source-inspection-only plugin composition and bounded handler-recovery boundary |
| [`plugins/vm-5.md`](plugins/vm-5.md) | VM-5 source-inspection-only plugin composition and bounded live-probing boundary |
| [`plugins/vm-6.md`](plugins/vm-6.md) | VM-6 source-inspection-only plugin composition and bounded site-fitting boundary |
| [`plugins/vm-7.md`](plugins/vm-7.md) | VM-7 source-inspection-only plugin composition and bounded abstract-state boundary |
| [`plugins/vm-8.md`](plugins/vm-8.md) | VM-8 source-inspection-only plugin composition and bounded partial-evaluation boundary |
| [`plugins/vm-glm-1.md`](plugins/vm-glm-1.md) | VM-GLM-1 sample-specific plugin; handler-effects/path-dissolution variation of VM-3 |
| [`plugins/vm-gpt-1.md`](plugins/vm-gpt-1.md) | VM-GPT-1 sample-specific plugin; sandboxed trace-guided recovery boundary |
| [`plugins/vm-kimi-1.md`](plugins/vm-kimi-1.md) | VM-Kimi-1 sample-specific plugin; static-decrypt/hashed-dispatch boundary |
| [`plugins/control-flow-flattening.md`](plugins/control-flow-flattening.md) | Control Flow Flattening sample-specific plugin; state-dispatch recovery boundary |
| [`plugins/string-concealing.md`](plugins/string-concealing.md) | String Concealing sample-specific plugin; static getter recovery boundary |
| [`plugins/dispatcher.md`](plugins/dispatcher.md) | Dispatcher sample-specific plugin; bounded table extraction and call recovery boundary |
| [`plugins/flatten.md`](plugins/flatten.md) | Flatten sample-specific plugin; context-wrapper inlining boundary |
| [`plugins/shuffle-claude.md`](plugins/shuffle-claude.md) | Shuffle-Claude sample-specific plugin; primitive rotation boundary |
| [`plugins/shuffle-gpt-5-5.md`](plugins/shuffle-gpt-5-5.md) | Shuffle-GPT-5.5 sample-specific plugin; binding-aware AST rotation boundary |
| [`plugins/string-compression-gpt-5-5.md`](plugins/string-compression-gpt-5-5.md) | StringCompression-GPT-5.5 sample-specific plugin; LZ table recovery boundary |
| [`plugins/variable-masking.md`](plugins/variable-masking.md) | VariableMasking sample-specific plugin; rest-parameter recovery boundary |
| `experiment-registry.md` | One row per corpus experiment and its configuration boundary |
| `tests.md` | Corpus example checks and evidence boundaries |
| `source-map.md` | Reverse map from every top-level corpus experiment to a claim or an explicit gap |


## Graduated plugin navigation

| Plugin | Ordered transform navigation |
| --- | --- |
| [String Concealing](plugins/string-concealing.md) | [static getter recovery](transforms/string-concealing-static-getter-recovery.md) |
| [Control Flow Flattening](plugins/control-flow-flattening.md) | [state-dispatch recovery](transforms/control-flow-flattening-state-dispatch-recovery.md) |
| [VM-3](plugins/vm-3.md) | [structural detection](transforms/vm-3-structural-vm-detection.md) → [handler canonicalization](transforms/vm-3-handler-canonicalization.md) → [payload disassembly](transforms/vm-3-payload-disassembly.md) → [state-specialized lifting](transforms/vm-3-state-specialized-lifting.md) → [Reloop/cleanup/emission](transforms/vm-3-reloop-cleanup-emission.md) → [fallback](transforms/vm-3-fallback-validation.md) |
| [VM-1](plugins/vm-1.md) | [bytecode extraction](transforms/vm-1-structural-bytecode-extraction.md) → [fixed-opcode disassembly](transforms/vm-1-fixed-opcode-disassembly.md) → [function/CFG discovery](transforms/vm-1-static-function-cfg.md) → [reducible structuring](transforms/vm-1-reducible-register-structuring.md) → [dual emission](transforms/vm-1-dual-emission.md) → [fallback](transforms/vm-1-fallback-validation.md) |
| [VM-2](plugins/vm-2.md) | [O1 outer recognition](transforms/outer-recognition-evaluation.md) → [O4 trampoline specialization](transforms/outer-trampoline-specialization.md) → [O2 outer state CFG](transforms/outer-state-cfg-recovery.md) → [O3 outer CFG structuring](transforms/outer-cfg-structuring.md) → [O5 static strings](transforms/outer-static-string-recovery.md) → [O6 observed strings](transforms/outer-observed-string-recovery.md) → [O7 outer cleanup](transforms/outer-cleanup.md) → [I1 container extraction](transforms/vm-container-extraction.md) → [I2 handler classification](transforms/handler-classification.md) → [I3 wordcode disassembly](transforms/wordcode-disassembly.md) → [I4 state-aware lifting](transforms/state-aware-lifting.md) → [I5 local SSA](transforms/local-ssa.md) → [I6 inner control](transforms/inner-control-structuring.md) → [I7 inner cleanup](transforms/inner-cleanup.md) → [V1 validation/fallback](transforms/validation-fallback.md) |
| [VM-4](plugins/vm-4.md) | [static handler observation and frame-aware operation recovery](transforms/vm-4-static-handler-recovery.md) |
| [VM-5](plugins/vm-5.md) | [live handler probing and frame-aware fit recovery](transforms/vm-5-live-handler-fit-recovery.md) |
| [VM-6](plugins/vm-6.md) | [site-salted handler fitting and hash-dispatch recovery](transforms/vm-6-site-salted-handler-fitting.md) |
| [VM-7](plugins/vm-7.md) | [behavioral abstract-state lifting](transforms/vm-7-behavioral-abstract-state-lifting.md) |
| [VM-8](plugins/vm-8.md) | [oracle classification and partial evaluation](transforms/vm-8-oracle-classification-partial-evaluation.md) |
| [VM-GLM-1](plugins/vm-glm-1.md) | [handler-effects variation](transforms/vm-glm-1-handler-effects-variation.md) → shared VM-3 structural/lifting/cleanup references |
| [VM-GPT-1](plugins/vm-gpt-1.md) | [trace-guided recovery](transforms/vm-gpt-1-trace-guided-recovery.md) → delegated cleanup/generation |
| [VM-Kimi-1](plugins/vm-kimi-1.md) | [static decrypt and hashed dispatch](transforms/vm-kimi-1-static-decrypt-dispatch.md) → delegated lifting/cleanup |
| [Dispatcher](plugins/dispatcher.md) | [call recovery](transforms/dispatcher-call-recovery.md) |
| [Flatten](plugins/flatten.md) | [context inlining](transforms/flatten-context-inlining.md) |
| [Shuffle-Claude](plugins/shuffle-claude.md) | [static primitive rotation](transforms/shuffle-claude-static-primitive-rotation.md) |
| [Shuffle-GPT-5.5](plugins/shuffle-gpt-5-5.md) | [binding-aware AST subtree rotation](transforms/shuffle-gpt-5-5-ast-subtree-rotation.md) |
| [StringCompression-GPT-5.5](plugins/string-compression-gpt-5-5.md) | [LZ table recovery](transforms/string-compression-gpt-5-5-lz-table-recovery.md) |
| [VariableMasking](plugins/variable-masking.md) | [rest-parameter recovery](transforms/variable-masking-rest-parameter-recovery.md) |

The package layout is concept-oriented and namespaced to this pinned corpus. Each experiment has
its own plugin root. A plugin may contain multiple ordered transforms, as VM-2 does; a helper file
or experiment folder does not automatically receive a transform page. The registry owns encoder
configuration profiles and exact-example provenance.

## Read-only rule

The corpus submodule is evidence input. Its files, branches and history are not edited by this
package. Each algorithm page records the source-derived mechanism and its limits.

## Source

The source boundary is the pinned corpus root and the inventoried experiment directories:
[corpus root](https://github.com/MichaelXF/claude-vs-js-confuser/tree/e90be6ca716e28f4bba91fe39615a665656bd802),
[StringConcealing](https://github.com/MichaelXF/claude-vs-js-confuser/tree/e90be6ca716e28f4bba91fe39615a665656bd802/StringConcealing),
[ControlFlowFlattening](https://github.com/MichaelXF/claude-vs-js-confuser/tree/e90be6ca716e28f4bba91fe39615a665656bd802/ControlFlowFlattening),
and [VM-2](https://github.com/MichaelXF/claude-vs-js-confuser/tree/e90be6ca716e28f4bba91fe39615a665656bd802/VM-2),
[VM-1](https://github.com/MichaelXF/claude-vs-js-confuser/tree/e90be6ca716e28f4bba91fe39615a665656bd802/VM-1),
and [VM-3](https://github.com/MichaelXF/claude-vs-js-confuser/tree/e90be6ca716e28f4bba91fe39615a665656bd802/VM-3),
[VM-GLM-1](https://github.com/MichaelXF/claude-vs-js-confuser/tree/e90be6ca716e28f4bba91fe39615a665656bd802/VM-GLM-1),
[VM-GPT-1](https://github.com/MichaelXF/claude-vs-js-confuser/tree/e90be6ca716e28f4bba91fe39615a665656bd802/VM-GPT-1),
and [VM-Kimi-1](https://github.com/MichaelXF/claude-vs-js-confuser/tree/e90be6ca716e28f4bba91fe39615a665656bd802/VM-Kimi-1),
[VM-4](https://github.com/MichaelXF/claude-vs-js-confuser/tree/e90be6ca716e28f4bba91fe39615a665656bd802/VM-4),
[VM-5](https://github.com/MichaelXF/claude-vs-js-confuser/tree/e90be6ca716e28f4bba91fe39615a665656bd802/VM-5),
[VM-6](https://github.com/MichaelXF/claude-vs-js-confuser/tree/e90be6ca716e28f4bba91fe39615a665656bd802/VM-6),
[VM-7](https://github.com/MichaelXF/claude-vs-js-confuser/tree/e90be6ca716e28f4bba91fe39615a665656bd802/VM-7),
and [VM-8](https://github.com/MichaelXF/claude-vs-js-confuser/tree/e90be6ca716e28f4bba91fe39615a665656bd802/VM-8),
[Dispatcher](https://github.com/MichaelXF/claude-vs-js-confuser/tree/e90be6ca716e28f4bba91fe39615a665656bd802/Dispatcher),
[Flatten](https://github.com/MichaelXF/claude-vs-js-confuser/tree/e90be6ca716e28f4bba91fe39615a665656bd802/Flatten),
[Shuffle-Claude](https://github.com/MichaelXF/claude-vs-js-confuser/tree/e90be6ca716e28f4bba91fe39615a665656bd802/Shuffle-Claude),
[Shuffle-GPT-5.5](https://github.com/MichaelXF/claude-vs-js-confuser/tree/e90be6ca716e28f4bba91fe39615a665656bd802/Shuffle-GPT-5.5),
[StringCompression-GPT-5.5](https://github.com/MichaelXF/claude-vs-js-confuser/tree/e90be6ca716e28f4bba91fe39615a665656bd802/StringCompression-GPT-5.5),
and [VariableMasking](https://github.com/MichaelXF/claude-vs-js-confuser/tree/e90be6ca716e28f4bba91fe39615a665656bd802/VariableMasking).
All source-backed experiment algorithms are now owned by package-local plugin roots and transform
pages; encoder-side files and exact wiring are cited by each plugin/transform page or registry
profile.

## Reproduction assets

| Asset | Claim it supports |
| --- | --- |
| Pinned corpus submodule | Supplied exact examples, experiment source, notes and regular controls at the reviewed commit |
| [Corpus tests](tests.md) | Input, output and control checks for bounded corpus claims |
