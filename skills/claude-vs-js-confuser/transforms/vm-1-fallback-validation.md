# Fallback and validation

Evidence label: source-inspection only. This page is the E6 reconstruction contract for VM-1
driver selection, source generation, and the limits of the supplied validation artifacts. It does
not report a validation run, semantic equivalence, production coverage, or host-safety result.

## 1. Target

Select one bounded output path for each input:

- a formatted pass-through for source that does not yield a recognized VM;
- an E4 structured candidate when E2/E3 output fits the structured emitter;
- an E5 explicit-PC candidate when dispatch is forced or structured emission throws; or
- an exception when production E2 disassembly encounters an unknown opcode before the fallback
  catch.

The discriminator is driver branch order, not semantic validation. A recognized `CODE_COPY` is
known to E2, declines in E4, and reaches E5 as an explicit unsupported marker; it is not the
unknown-opcode exception path.

## 2. Algorithm

1. Call E1 inside a broad `try`. Any extraction/parser/constant-evaluation throw sets `vm = null`.
2. If `vm` is falsy, parse with `{ sourceType: "unambiguous" }` and generate with comments. If
   this fallback parse/generation throws, return the original `src` string.
3. For a recognized VM, call E2's `disassemble` and E3's `discoverFunctions` without a catch in
   `deobfuscateSource`.
4. If `process.env.VM_FORCE_DISPATCH` is truthy, call E5's dispatcher and immediately generate
   the result. E4 is not attempted.
5. Otherwise call E4's structured emitter in a broad `try`. If it throws any error, optionally
   log its stack/message when `process.env.VM_DEBUG` is truthy, then call E5's dispatcher.
6. Generate the selected candidate with comments and `{ jsescOption: { minimal: true } }`.
   `deobfuscateFile` resolves and reads a UTF-8 file before calling the source driver; the CLI
   writes a requested output file or writes the result to stdout.

The validation files are not called by this production selection path. They express intended
checks but do not change the algorithm or certify the selected source.

## 3. Implementation

### Branch table

| Ordered condition | Result | Exact distinction |
| --- | --- | --- |
| E1 returns `null` or throws; fallback parse/generate succeeds | Generated reformatted original program | Non-VM/extraction-failure pass-through is not necessarily byte-identical. |
| E1 returns `null` or throws; fallback parse/generate throws | Original `src` | Inner fallback catch returns source unchanged. |
| E1 succeeds, E2/E3 succeed, `VM_FORCE_DISPATCH` is truthy | Generated E5 dispatcher | Force branch precedes the E4 call. |
| E1-E3 succeed and E4 returns | Generated E4 structured program | Normal structured candidate. |
| E1-E3 succeed and E4 throws any error | Generated E5 dispatcher | The catch is broad; source does not check `Unstructurable` type. |
| E2 production disassembly throws unknown opcode | Error escapes the driver | E2 occurs before the structured-emitter `try/catch`. |

If E4 reaches `CODE_COPY`, its `irForInstr` throws `Unstructurable`; E6's broad catch then invokes
E5, whose `lowerSideEffect` emits the marker literal. E6 does not turn that marker into a semantic
replacement. If E5 itself throws or Babel generation fails after a recognized VM path, there is no
second pass-through catch in `deobfuscateSource`.

### Concrete source operations

`deobfuscateSource` exports through `module.exports.deobfuscate`, attempts E1, and handles the
non-VM branch with `parser.parse` plus `generate`. On recognized input it constructs descriptors
and function records, then uses the environment branch and emitter catch described above. Both
candidate paths call Babel generator with comments and minimal escaping.

`deobfuscateFile` resolves relative names against `process.cwd()`, reads UTF-8 synchronously, and
returns `deobfuscateSource(src)`. The CLI requires an input path, calls the file wrapper, writes
to `outFile` when present, or writes the result to stdout. These are file/output wrappers, not
semantic validation.

### Validation artifacts and evidence boundary

`test.js` calls the file wrapper for the encoded input and regular input, checks non-empty output,
decoded string spellings, absence of a large base64 blob and `new Uint32Array`, and then executes
the generated/regular source in Node VM contexts. `verify.js` builds seven deterministic sandbox
scenarios, runs reference and candidate source in fresh VM contexts, and deep-compares captured
console values. Those scripts describe intended checks; no validation result is inferred from their source.

### Source ownership

| Source span | Ownership | What it owns |
| --- | --- | --- |
| [`vm.js#L434-L468`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-1/vm.js#L434-L468) | owned algorithm | Extraction catch, pass-through, E2/E3 ordering, force dispatch, broad structured catch, and source generation. |
| [`vm.js#L470-L474`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-1/vm.js#L470-L474) | delegated file wrapper | UTF-8 file read and source-driver call. |
| [`vm.js#L479-L484`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-1/vm.js#L479-L484) | shared coordinator owned by [dual emission](vm-1-dual-emission.md) | Common dependency injection into E4/E5. |
| [`vm.js#L489-L502`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-1/vm.js#L489-L502) | delegated CLI plumbing | Argument check and file/stdout output. |
| [`test.js#L23-L70`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-1/test.js#L23-L70) | delegated evidence harness | Intended smoke, string, execution, and regular pass-through checks; not production selection. |
| [`verify.js#L1-L118`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-1/verify.js#L1-L118) | delegated evidence harness | Seven-scenario comparison design; no validation result is claimed. |

## 4. Upstream Effects

E6 consumes E1's null/throw boundary, E2's descriptors, E3's function/block records, and E4/E5's
AST outputs. E1 must be attempted before non-VM pass-through can be selected; E2 and E3 must
complete before either emitter is called. The E2 unknown-opcode throw remains outside the E4
catch, so the dispatcher is not a universal error sink.

E4's structured error is the upstream condition that selects E5 in the ordinary path. E5 supplies
the selected Babel program; E6 alone generates source and selects whether to return a candidate or
pass-through. The dispatcher is a bounded representation for structured-shape declines, not an
E6 validation verdict.

Production `vm.js` does not execute input or candidate source. The Node VM execution and deep
comparison described by `test.js`/`verify.js` are separate evidence harnesses, not part of driver
selection or validation evidence for this source-inspection contract.

## 5. Known Gaps

- The driver has no semantic validator, syntax reparse, runtime comparison, or idempotence check.
  The evidence boundary here does not establish transfer coverage.
- Extraction/parser/evaluation failures receive a best-effort parse/generate pass-through; that is
  source-observed behavior, not a claim that arbitrary malformed JavaScript is safely preserved.
- Production unknown opcodes escape before fallback. The diagnostic decoder's size-one unknown
  descriptor does not alter this production boundary.
- The structured catch is broad and may route errors other than `Unstructurable` to E5; E5 or
  generation errors are not covered by an additional recognized-VM pass-through catch.
- `CODE_COPY` remains an explicit unsupported marker in E5, and structured declines for dynamic,
  irreducible, or unsupported shapes preserve VM-like control rather than recovering source code.
- File I/O, Babel generation, generated helpers, host globals, and candidate execution are not
  safety-qualified by this source-only contract.

## Source

| File | Pinned source | Role |
| --- | --- | --- |
| `VM-1/vm.js` | [`driver and file wrapper`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-1/vm.js#L434-L474) | Selection and source/file boundaries. |
| `VM-1/vm.js` | [`emitter wiring`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-1/vm.js#L479-L484) | Common emitter dependencies. |
| `VM-1/vm.js` | [`CLI`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-1/vm.js#L489-L502) | File/stdout output plumbing. |
| `VM-1/test.js` | [`intended smoke checks`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-1/test.js#L23-L70) | Evidence-only harness. |
| `VM-1/verify.js` | [`intended comparison harness`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-1/verify.js#L1-L118) | Evidence-only harness. |

## Fixtures

The retained input/output and test artifacts map the recognized and non-VM branches:

| Corpus artifact | Claim it pins | Evidence status |
| --- | --- | --- |
| `VM-1/regular.js`, `regular.out.js` | Released non-VM pass-through pair | Source-fixture provenance. |
| `VM-1/input.js` | Released recognized VM input | Source fixture. |
| `VM-1/output.js`, `output.dispatch.js` | Existing structured and dispatcher outputs | Generated-output provenance only. |
| `VM-1/test.js` | Intended decoded-string, execution, and regular-file checks | Test-intent evidence; no validation result is claimed. |
| `VM-1/verify.js` | Seven-scenario comparison design | Test-intent evidence; no validation result is claimed. |
