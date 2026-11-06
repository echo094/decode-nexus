# jsconfuser-vm.js

Pipeline stage: `publish` ([map](../pipelines/jsconfuser-vm.md)).

Target-local decoder for proved supported source shapes of the pinned `js-confuser-vm` encoder. It is an
additive `decode-js` target: it does not alter the existing `jsconfuser` plugin or any legacy
plugin's string-or-null contract.

## 1. Target

Recover a complete supported VM container into fresh source-oriented JavaScript through the real
`decode-js` caller. The output is reviewable decompilation, not original-source reconstruction:
generic names and necessary register/capture scaffolding may remain. The target accepts
source-derived numeric, encoded, minified and selected hardened shapes whose current records pass
the static grammar, reference, ownership/control and coverage checks. Unsupported source shapes
or failed checks decline atomically and remain byte-for-byte unchanged. There is no qualification-record
or option-profile admission gate: an untested combination can reach static success, while its
qualification remains an evidence limit.

The goal is recovery of any valid file the pinned encoder release produces (tag `0.1.5`, commit
`20c5b96bf57337c568579352758d7685358650de`), whatever the source program, option vector or
randomized emission. Earlier releases, untested option combinations and repeated or mixed encoders
have no qualification; each finite population the [qualification tool](../vm/jsconfuser-vm/qualify-jsconfuser-vm.md)
generates qualifies only itself. Runtime agreement is a bounded regression guard, not evidence that
VM structure was recovered. A benchmark sample from outside the qualification tool is a separate
acceptance step: it is retained with source, behaviour oracle and provenance, and never defines
recognition rules.

## 2. Algorithm

The adapter is a result-aware boundary around the target-local standalone decoder:

1. Apply the plugin's [source preparation visitors](../vm/jsconfuser-vm/normalize-source.md)
   on a private strict script parse, then pass the prepared source to `diagnoseStandalone` exactly once.
2. On success, return the standalone emitted source and its immutable recovery result.
3. On decline, return the original source and the immutable diagnostic; do not expose partial
   analysis or emission.
4. The CLI writes the selected output and one JSON sidecar from that same record. The direct VM
   path never runs the input or recovered program during extraction, analysis or emission.

The standalone decoder resolves its predecessor analyses before emission; the
[pipeline map](../pipelines/jsconfuser-vm.md) shows their order and inputs.

## 3. Implementation

The decoder's layers, pipeline stages and components, the encoder steps each component undoes
or reads, and the reversibility of every encoder step are in the
[pipeline map](../pipelines/jsconfuser-vm.md).

### Adapter record

The adapter does not reimplement any component or diagnose the source a second time.

`decodeJsconfuserVm(source)` returns a frozen `jsconfuser-vm-adapter.v1` record:

| field | success | decline |
|---|---|---|
| `ok` / `status` | `true` / `success` | `false` / `declined` |
| `input` | exact input source | exact input source |
| `output` | fresh emitted JavaScript | exact input source |
| `result` | standalone result | `null` |
| `diagnostic` | `null` | standalone diagnostic |

The adapter retains the original source while its pre-operation visitors prepare the diagnosis
input; normalization is internal to this consumer, with no repo-wide suitability claim. The adapter
delegates the single call to `diagnoseStandalone`. Its result and diagnostic are
already frozen by the standalone boundary, and the adapter freezes the enclosing record as well.
The CLI registers the adapter under `-t jsconfuser-vm`, reads UTF-8 input, and writes the record's
`output`. The default result path is `<output>.result.json`; `--result` selects an explicit path.
The comparison is exact string equality of `path.resolve(resultPath)` and
`path.resolve(outputPath)`, after decoding but before writing. It rejects lexical path aliases;
it does not resolve symlinks, hard links or filesystem identity. The output and sidecar need
distinct resolved paths.
The target-specific branch reports unknown target, read, decode, output-write, result-write, and
invalid-result-option failures without changing legacy branches. A successful or declined target
record is still a successful CLI operation once both named files are written. Decline prints
`Status: declined` and its diagnostic but does not itself set a failing exit code.

The CLI writes UTF-8 output first, then `JSON.stringify(record,null,2)` plus newline to the
sidecar. Output-write failure leaves the result path unwritten. Result-write or JSON serialization
failure sets exit code 1 after output has already been written; no filesystem rollback is
implemented. This is not a two-file transaction. Ordinary JSON supplies no Map/Set/BigInt tags
here. This documents
the format and error path, not a demonstrated serialization failure for a
current admitted input. These failure branches are source-inspected contracts; current CLI
tests do not exercise result-write or serialization failure.

### Public scenarios and acceptance

| Scenario | Observable result / oracle | Evidence boundary |
|---|---|---|
| Supported input | One diagnosis call; output differs from input and equals result.output; frozen envelope; fresh AST/residue/state checks. | plugin.test reference/focused controls. No general native equivalence. |
| Ordinary or damaged source | Exact original source and same diagnostic, result null; bytes/hash unchanged. | plugin.test ordinary, truncated and encoding-flag damage controls. |
| Registered CLI success | Output and explicit sidecar match direct standalone result; status success and exit 0. | cli.test retained literal-order input; integration.test separate branch/oracle. |
| Registered CLI decline | Original source file and default/explicit sidecar, diagnostic printed, exit 0. | cli.test ordinary and damaged-flag controls. |
| Resolved output/result path equality | Existing output sentinel remains untouched; exit 1. | cli.test lexical alias control; filesystem-identity aliases untested. |
| Unknown type/read/output failure | Exit 1; named paths remain unwritten as asserted. | cli.test selected errors; thrown decode and result/JSON failure lack focused controls. |
| Leading debug comment | Same emitted output and no target execution. | plugin.test synthetic comment; not proof about every comment/transform stack. |

The CLI branch catches thrown plugin errors before writes. The adapter itself does not catch
around its call because public standalone returns its supported failures as records. Legacy
plugins retain string-or-null publication and have no automatic result sidecar; `--result`
on an unsupported target exits before input read. The registry does not extend their APIs.

## 4. Input Shapes

The adapter consumes one public immutable success/decline shape from the standalone decoder. The affected
caller behavior is therefore a boundary contract, not another AST pass:

| upstream shape | producer | adapter treatment |
|---|---|---|
| emitted source plus complete recovery result | [standalone decode](../vm/jsconfuser-vm/standalone-decode.md) | expose both in one success record |
| diagnostic with no result | [standalone diagnosis](../vm/jsconfuser-vm/standalone-diagnosis.md) or the [standalone decoder](../vm/jsconfuser-vm/standalone-decode.md) | preserve it and the exact input in one decline record |
| legacy plugin string or `null` | existing `decode-js` plugin branches | leave untouched; no result sidecar is added |

No shared visitor or generic caller is an upstream dependency of this target. The additive registry
and target-specific CLI branch are the only integration shapes, so a failure in this boundary must
not be repaired by widening an existing plugin contract.

## 5. Known Gaps

- [`extract-container`](../vm/jsconfuser-vm/extract-container.md#5-known-gaps) and the
  [handler locator](../vm/jsconfuser-vm/locate-handlers.md#5-known-gaps) list their
  runtime-layer gaps; [timing checks](../vm/jsconfuser-vm/timing-checks.md) and the
  [PATCH added-opcode contract](../vm/jsconfuser-vm/normalize-self-modifying-wordcode.md)
  own their accepted domains and qualification limits.
- Source replacement, generic shared-decoder changes, earlier releases, repeated or mixed
  encoders, and universal runtime equivalence are outside this target's contract.
- Unqualified combinations lack retained evidence; their status alone does not force runtime decline.
- Behavioral checks are bounded regression oracles around static recovery; the adapter does not
  claim production-wide semantic equivalence.
- Readability is gated by the tracked arithmetic, closure/loop, and scale benchmark owned by
  [the standalone decoder contract](../vm/jsconfuser-vm/standalone-decode.md#readability-gate).
  The gate asserts current output is smaller and less scaffold-heavy than its
  recorded baseline; it does not promise recovered original identifiers or universal source
  reconstruction.

## Source

- [`../../../decoder/decode-js/src/plugin/jsconfuser-vm.js`](../../../decoder/decode-js/src/plugin/jsconfuser-vm.js) — the single-call frozen adapter.
- [`../../../decoder/decode-js/src/main.js`](../../../decoder/decode-js/src/main.js) — the additive registry and target-specific CLI/result-sidecar branch.
- [`../vm/jsconfuser-vm/standalone-decode.md`](../vm/jsconfuser-vm/standalone-decode.md) — the standalone producer consumed by the adapter.
- [`../vm/jsconfuser-vm/standalone-diagnosis.md`](../vm/jsconfuser-vm/standalone-diagnosis.md) — its separate pre-emission admission boundary.

## Fixtures

The single-call adapter and current-record caller handoffs were audited statically against source.
The retired frozen verifier supplied a synthetic public wrapper only; it did not execute this
plugin/CLI, reconstruct every frontend component or qualify real source admission or public control-solver outcomes. The integration tests below contain separate public-boundary
assertions over retained inputs; this design does not report their fresh execution. The frozen
executable and the report's frozen metadata/stdout section stay unchanged; postfreeze audit/verdict
remains appendable.

The retired immutable reduced emission/public verifier, built from the documents
before source consultation, and its postfreeze source audit separately pinned adapter exact-original output, call count and freezing with supplied diagnosis.
Their CLI credit is simulated selected ordering/path decisions: resolve-only alias refusal,
decode before alias checking, and output write before result write. They do not execute argv
handling, registry dispatch, a subprocess, filesystem writes, JSON serialization or exact stderr.
Injected I/O/JSON failures are callback decisions, not demonstrated failures on admitted input.
The production integration assertions below remain a separate evidence family.

| test or evidence input | claim pinned |
|---|---|
| [Randomized words](../vm/jsconfuser-vm/extract-container.md#fixtures) | Randomized class and class-plus-minify inputs take their meaning from the handlers and recover with fresh state; a consistent full remapping keeps the meaning. |
| [`../../../decoder/decode-js/test/vm/jsconfuser-vm/integration/plugin.test.js`](../../../decoder/decode-js/test/vm/jsconfuser-vm/public-entry-points/plugin.test.js) | one diagnosis call, frozen success/decline records, exact-input declines, stable diagnostics, and debug independence |
| [`../../../decoder/decode-js/test/vm/jsconfuser-vm/integration/cli.test.js`](../../../decoder/decode-js/test/vm/jsconfuser-vm/public-entry-points/cli.test.js) | registered subprocess reachability, direct standalone result agreement, named output/result paths, target errors, and unchanged legacy behavior |
| [`../../../decoder/decode-js/test/vm/jsconfuser-vm/integration/integration.test.js`](../../../decoder/decode-js/test/vm/jsconfuser-vm/public-entry-points/integration.test.js) | structured branch output agrees across the registered CLI, direct diagnosis, and the fixture oracle |
| [`../../../decoder/decode-js/test/vm/jsconfuser-vm/integration/readability.test.js`](../../../decoder/decode-js/test/vm/jsconfuser-vm/support/readability.test.js) | source-oriented output reduction, preserved bounded behavior, fresh parsing, and required scaffolding |
