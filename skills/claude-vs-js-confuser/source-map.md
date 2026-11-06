# Corpus file-level reverse source map

This map preserves the pinned corpus inventory as the coverage unit. The file inventory below has
one row for each POSIX-relative corpus path, including root metadata and every
evidence-bearing descendant. VM-1, VM-2, VM-3, VM-4, VM-5, VM-6, VM-7, VM-8, VM-GLM-1,
VM-GPT-1, VM-Kimi-1, ControlFlowFlattening, StringConcealing, Dispatcher, Flatten, Shuffle-Claude,
Shuffle-GPT-5.5, StringCompression-GPT-5.5 and VariableMasking source files map to package-local
plugin/transform pages; other rows retain their existing explicit-gap or package-owned destination.
The `.git` row is checkout-only metadata and is excluded from the pinned inventory population.
All links below are durable package-relative destinations.

## File inventory

| Pinned corpus path | File kind | Owning page or index | Claim scope |
| --- | --- | --- | --- |
| `.git` | metadata | `experiment-registry.md` — checkout-only metadata; excluded from pinned inventory | inventory metadata only |
| `.gitignore` | metadata | `experiment-registry.md` — explicit documentation gap; package metadata only | inventory metadata only |
| `.prettierignore` | metadata | `experiment-registry.md` — explicit documentation gap; package metadata only | inventory metadata only |
| `ControlFlowFlattening/README.md` | documentation | [plugins/control-flow-flattening.md](plugins/control-flow-flattening.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `ControlFlowFlattening/cff.js` | algorithm-source | [transforms/control-flow-flattening-state-dispatch-recovery.md](transforms/control-flow-flattening-state-dispatch-recovery.md) — source-backed distinct algorithm | source-backed documentary claim; no transfer |
| `ControlFlowFlattening/controlFlowFlattening.js` | algorithm-source | [transforms/control-flow-flattening-state-dispatch-recovery.md](transforms/control-flow-flattening-state-dispatch-recovery.md) — source-backed wrapper and emission boundary | source-backed documentary claim; no transfer |
| `ControlFlowFlattening/debug_compare.js` | debug-source | [plugins/control-flow-flattening.md](plugins/control-flow-flattening.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `ControlFlowFlattening/debug_explore.js` | debug-source | [plugins/control-flow-flattening.md](plugins/control-flow-flattening.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `ControlFlowFlattening/debug_output.js` | debug-source | [plugins/control-flow-flattening.md](plugins/control-flow-flattening.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `ControlFlowFlattening/debug_run.js` | debug-source | [plugins/control-flow-flattening.md](plugins/control-flow-flattening.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `ControlFlowFlattening/debug_sim.js` | debug-source | [plugins/control-flow-flattening.md](plugins/control-flow-flattening.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `ControlFlowFlattening/input.js` | fixture-source | [plugins/control-flow-flattening.md](plugins/control-flow-flattening.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `ControlFlowFlattening/original.js` | fixture-source | [plugins/control-flow-flattening.md](plugins/control-flow-flattening.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `ControlFlowFlattening/output.js` | generated-output | [plugins/control-flow-flattening.md](plugins/control-flow-flattening.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `ControlFlowFlattening/regular.js` | fixture-source | [plugins/control-flow-flattening.md](plugins/control-flow-flattening.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `ControlFlowFlattening/regular_out.js` | generated-output | [plugins/control-flow-flattening.md](plugins/control-flow-flattening.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `ControlFlowFlattening/test.js` | fixture-source | [plugins/control-flow-flattening.md](plugins/control-flow-flattening.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `Dispatcher/README.md` | documentation | [plugins/dispatcher.md](plugins/dispatcher.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `Dispatcher/dispatcher.js` | algorithm-source | [transforms/dispatcher-call-recovery.md](transforms/dispatcher-call-recovery.md) — source-backed distinct algorithm | source-backed documentary claim; no transfer |
| `Dispatcher/input.js` | fixture-source | [plugins/dispatcher.md](plugins/dispatcher.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `Dispatcher/input2.js` | fixture-source | [plugins/dispatcher.md](plugins/dispatcher.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `Dispatcher/original.js` | fixture-source | [plugins/dispatcher.md](plugins/dispatcher.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `Dispatcher/output.cli.js` | generated-output | [plugins/dispatcher.md](plugins/dispatcher.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `Dispatcher/output.js` | generated-output | [plugins/dispatcher.md](plugins/dispatcher.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `Dispatcher/output2.js` | generated-output | [plugins/dispatcher.md](plugins/dispatcher.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `Dispatcher/regular.js` | fixture-source | [plugins/dispatcher.md](plugins/dispatcher.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `Dispatcher/regular.output.js` | generated-output | [plugins/dispatcher.md](plugins/dispatcher.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `Dispatcher/test.js` | fixture-source | [plugins/dispatcher.md](plugins/dispatcher.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `Flatten/NOTES.md` | documentation | [plugins/flatten.md](plugins/flatten.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `Flatten/README.md` | documentation | [plugins/flatten.md](plugins/flatten.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `Flatten/flatten.js` | algorithm-source | [transforms/flatten-context-inlining.md](transforms/flatten-context-inlining.md) — source-backed distinct algorithm | source-backed documentary claim; no transfer |
| `Flatten/input.js` | fixture-source | [plugins/flatten.md](plugins/flatten.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `Flatten/output.js` | generated-output | [plugins/flatten.md](plugins/flatten.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `Flatten/regular.js` | fixture-source | [plugins/flatten.md](plugins/flatten.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `Flatten/test.js` | fixture-source | [plugins/flatten.md](plugins/flatten.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `LICENSE` | metadata | `experiment-registry.md` — explicit documentation gap; package metadata only | inventory metadata only |
| `README.md` | metadata | `experiment-registry.md` — explicit documentation gap; package metadata only | inventory metadata only |
| `Shuffle-Claude/README.md` | documentation | [plugins/shuffle-claude.md](plugins/shuffle-claude.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `Shuffle-Claude/Shuffle-Claude.js` | algorithm-source | [transforms/shuffle-claude-static-primitive-rotation.md](transforms/shuffle-claude-static-primitive-rotation.md) — source-backed distinct algorithm | source-backed documentary claim; no transfer |
| `Shuffle-Claude/Shuffle.js` | fixture-source | [plugins/shuffle-claude.md](plugins/shuffle-claude.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `Shuffle-Claude/test_multi.js` | fixture-source | [plugins/shuffle-claude.md](plugins/shuffle-claude.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `Shuffle-Claude/test_passthrough.js` | fixture-source | [plugins/shuffle-claude.md](plugins/shuffle-claude.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `Shuffle-GPT-5.5/README.md` | documentation | [plugins/shuffle-gpt-5-5.md](plugins/shuffle-gpt-5-5.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `Shuffle-GPT-5.5/Shuffle-GPT-5.5.js` | algorithm-source | [transforms/shuffle-gpt-5-5-ast-subtree-rotation.md](transforms/shuffle-gpt-5-5-ast-subtree-rotation.md) — source-backed distinct algorithm | source-backed documentary claim; no transfer |
| `Shuffle-GPT-5.5/Shuffle-GPT-5.5.output-from-sample.js` | generated-output | [plugins/shuffle-gpt-5-5.md](plugins/shuffle-gpt-5-5.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `Shuffle-GPT-5.5/Shuffle-GPT-5.5.test-pass-through-input.js` | fixture-source | [plugins/shuffle-gpt-5-5.md](plugins/shuffle-gpt-5-5.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `Shuffle-GPT-5.5/Shuffle-GPT-5.5.test-pass-through-output.js` | generated-output | [plugins/shuffle-gpt-5-5.md](plugins/shuffle-gpt-5-5.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `Shuffle-GPT-5.5/Shuffle-GPT-5.5.test-runner.js` | fixture-source | [plugins/shuffle-gpt-5-5.md](plugins/shuffle-gpt-5-5.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `Shuffle-GPT-5.5/Shuffle-GPT-5.5.test-shuffle-input.js` | fixture-source | [plugins/shuffle-gpt-5-5.md](plugins/shuffle-gpt-5-5.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `Shuffle-GPT-5.5/Shuffle.js` | fixture-source | [plugins/shuffle-gpt-5-5.md](plugins/shuffle-gpt-5-5.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `StringCompression-GPT-5.5/StringCompression-GPT-5.5.js` | algorithm-source | [transforms/string-compression-gpt-5-5-lz-table-recovery.md](transforms/string-compression-gpt-5-5-lz-table-recovery.md) — source-backed distinct algorithm | source-backed documentary claim; no transfer |
| `StringCompression-GPT-5.5/StringCompression-GPT-5.5.output.js` | generated-output | [plugins/string-compression-gpt-5-5.md](plugins/string-compression-gpt-5-5.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `StringCompression-GPT-5.5/StringCompression-GPT-5.5.pass-through.input.js` | fixture-source | [plugins/string-compression-gpt-5-5.md](plugins/string-compression-gpt-5-5.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `StringCompression-GPT-5.5/StringCompression-GPT-5.5.pass-through.output.js` | generated-output | [plugins/string-compression-gpt-5-5.md](plugins/string-compression-gpt-5-5.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `StringCompression-GPT-5.5/StringCompression-GPT-5.5.test-runner.js` | fixture-source | [plugins/string-compression-gpt-5-5.md](plugins/string-compression-gpt-5-5.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `StringCompression-GPT-5.5/StringCompression.js` | fixture-source | [plugins/string-compression-gpt-5-5.md](plugins/string-compression-gpt-5-5.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `StringConcealing/README.md` | documentation | [plugins/string-concealing.md](plugins/string-concealing.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `StringConcealing/input.js` | fixture-source | [plugins/string-concealing.md](plugins/string-concealing.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `StringConcealing/output.js` | generated-output | [plugins/string-concealing.md](plugins/string-concealing.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `StringConcealing/regular.js` | fixture-source | [plugins/string-concealing.md](plugins/string-concealing.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `StringConcealing/regular.out.js` | fixture-source | [plugins/string-concealing.md](plugins/string-concealing.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `StringConcealing/sample.deobf.js` | generated-output | [plugins/string-concealing.md](plugins/string-concealing.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `StringConcealing/sample.obf.js` | fixture-source | [plugins/string-concealing.md](plugins/string-concealing.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `StringConcealing/stringConcealing.js` | algorithm-source | [transforms/string-concealing-static-getter-recovery.md](transforms/string-concealing-static-getter-recovery.md) — source-backed distinct algorithm | source-backed documentary claim; no transfer |
| `StringConcealing/test.js` | fixture-source | [plugins/string-concealing.md](plugins/string-concealing.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-1/NOTES.md` | documentation | [plugins/vm-1.md](plugins/vm-1.md) — fixture/provenance evidence only | supporting evidence only; no algorithm claim |
| `VM-1/README.md` | documentation | [plugins/vm-1.md](plugins/vm-1.md) — fixture/provenance evidence only | supporting evidence only; no algorithm claim |
| `VM-1/disasm.js` | algorithm-source | [vm-1-structural-bytecode-extraction](transforms/vm-1-structural-bytecode-extraction.md), [vm-1-fixed-opcode-disassembly](transforms/vm-1-fixed-opcode-disassembly.md) — diagnostic extraction and fixed decoding | source-backed documentary claim; no transfer |
| `VM-1/emit-dispatcher.js` | algorithm-source | [vm-1-dual-emission](transforms/vm-1-dual-emission.md) — explicit-PC emitter | source-backed documentary claim; no transfer |
| `VM-1/emit-structured.js` | algorithm-source | [vm-1-reducible-register-structuring](transforms/vm-1-reducible-register-structuring.md), [vm-1-dual-emission](transforms/vm-1-dual-emission.md) — structured emitter and shared output wiring | source-backed documentary claim; no transfer |
| `VM-1/input.js` | fixture-source | [plugins/vm-1.md](plugins/vm-1.md) — fixture evidence only | supporting evidence only; no algorithm claim |
| `VM-1/original.js` | fixture-source | [plugins/vm-1.md](plugins/vm-1.md) — fixture evidence only | supporting evidence only; no algorithm claim |
| `VM-1/output.dispatch.js` | generated-output | [vm-1-dual-emission](transforms/vm-1-dual-emission.md) — generated-output provenance only | supporting evidence only; no algorithm claim |
| `VM-1/output.js` | generated-output | [vm-1-reducible-register-structuring](transforms/vm-1-reducible-register-structuring.md) — generated-output provenance only | supporting evidence only; no algorithm claim |
| `VM-1/regular.js` | fixture-source | [vm-1-fallback-validation](transforms/vm-1-fallback-validation.md) — non-VM pass-through fixture | supporting evidence only; no algorithm claim |
| `VM-1/regular.out.js` | fixture-source | [vm-1-fallback-validation](transforms/vm-1-fallback-validation.md) — non-VM pass-through fixture | supporting evidence only; no algorithm claim |
| `VM-1/test.js` | fixture-source | [vm-1-fallback-validation](transforms/vm-1-fallback-validation.md) — intended checks only | supporting evidence only; no algorithm claim |
| `VM-1/verify.js` | debug-source | [vm-1-fallback-validation](transforms/vm-1-fallback-validation.md) — verification context only | supporting evidence only; no algorithm claim |
| `VM-1/vm.js` | algorithm-source | [plugins/vm-1.md](plugins/vm-1.md), [vm-1-structural-bytecode-extraction](transforms/vm-1-structural-bytecode-extraction.md), [vm-1-fixed-opcode-disassembly](transforms/vm-1-fixed-opcode-disassembly.md), [vm-1-static-function-cfg](transforms/vm-1-static-function-cfg.md), [vm-1-reducible-register-structuring](transforms/vm-1-reducible-register-structuring.md), [vm-1-dual-emission](transforms/vm-1-dual-emission.md), [vm-1-fallback-validation](transforms/vm-1-fallback-validation.md) — source spans the driver and all six boundaries | source-backed documentary claim; no transfer |
| `VM-2/NOTES.md` | documentation | [VM-2 plugin root](plugins/vm-2.md) — provenance/notes only | V1/provenance evidence only |
| `VM-2/README.md` | documentation | [VM-2 plugin root](plugins/vm-2.md) — provenance/notes only | V1/provenance evidence only |
| `VM-2/devirt.js` | algorithm-source | [I1](transforms/vm-container-extraction.md), [I2](transforms/handler-classification.md), [I3](transforms/wordcode-disassembly.md), [I4](transforms/state-aware-lifting.md), [I5](transforms/local-ssa.md), [I6](transforms/inner-control-structuring.md), [I7](transforms/inner-cleanup.md) — source spans multiple package boundaries | VM-2 source detail across package boundaries |
| `VM-2/input.js` | fixture-source | [V1 validation and fallback](transforms/validation-fallback.md) — evidence/fixture only | V1/provenance evidence only |
| `VM-2/original.js` | fixture-source | [V1 validation and fallback](transforms/validation-fallback.md) — evidence/fixture only | V1/provenance evidence only |
| `VM-2/output.js` | generated-output | [V1 validation and fallback](transforms/validation-fallback.md) — evidence/fixture only | V1/provenance evidence only |
| `VM-2/regular.js` | fixture-source | [V1 validation and fallback](transforms/validation-fallback.md) — evidence/fixture only | V1/provenance evidence only |
| `VM-2/test.js` | fixture-source | [V1 validation and fallback](transforms/validation-fallback.md) — evidence/fixture only | V1/provenance evidence only |
| `VM-2/vm.js` | algorithm-source | [plugins/vm-2.md](plugins/vm-2.md), [O1](transforms/outer-recognition-evaluation.md), [O4](transforms/outer-trampoline-specialization.md), [O2](transforms/outer-state-cfg-recovery.md), [O3](transforms/outer-cfg-structuring.md), [O5](transforms/outer-static-string-recovery.md), [O6](transforms/outer-observed-string-recovery.md), [O7](transforms/outer-cleanup.md), [V1](transforms/validation-fallback.md) — source spans multiple package boundaries | VM-2 source detail across package boundaries |
| `VM-3/NOTES.md` | documentation | [plugins/vm-3.md](plugins/vm-3.md) — fixture/provenance evidence only | supporting evidence only; no algorithm claim |
| `VM-3/README.md` | documentation | [plugins/vm-3.md](plugins/vm-3.md) — fixture/provenance evidence only | supporting evidence only; no algorithm claim |
| `VM-3/debug/bytecode.json` | diagnostic-data | [plugins/vm-3.md](plugins/vm-3.md) — diagnostic evidence only | supporting evidence only; no algorithm claim |
| `VM-3/debug/canon.js` | debug-source | [plugins/vm-3.md](plugins/vm-3.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-3/debug/canon.txt` | diagnostic-data | [plugins/vm-3.md](plugins/vm-3.md) — diagnostic evidence only | supporting evidence only; no algorithm claim |
| `VM-3/debug/canon2.js` | debug-source | [plugins/vm-3.md](plugins/vm-3.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-3/debug/canon2.txt` | diagnostic-data | [plugins/vm-3.md](plugins/vm-3.md) — diagnostic evidence only | supporting evidence only; no algorithm claim |
| `VM-3/debug/combinecheck.js` | debug-source | [plugins/vm-3.md](plugins/vm-3.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-3/debug/compare-plain.txt` | diagnostic-data | [plugins/vm-3.md](plugins/vm-3.md) — diagnostic evidence only | supporting evidence only; no algorithm claim |
| `VM-3/debug/compare.js` | debug-source | [plugins/vm-3.md](plugins/vm-3.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-3/debug/disasm.js` | debug-source | [plugins/vm-3.md](plugins/vm-3.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-3/debug/disasm.txt` | diagnostic-data | [plugins/vm-3.md](plugins/vm-3.md) — diagnostic evidence only | supporting evidence only; no algorithm claim |
| `VM-3/debug/dump-handlers.js` | debug-source | [plugins/vm-3.md](plugins/vm-3.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-3/debug/extract.js` | debug-source | [plugins/vm-3.md](plugins/vm-3.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-3/debug/families.txt` | diagnostic-data | [plugins/vm-3.md](plugins/vm-3.md) — diagnostic evidence only | supporting evidence only; no algorithm claim |
| `VM-3/debug/foldcheck.js` | debug-source | [plugins/vm-3.md](plugins/vm-3.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-3/debug/handlers.txt` | diagnostic-data | [plugins/vm-3.md](plugins/vm-3.md) — diagnostic evidence only | supporting evidence only; no algorithm claim |
| `VM-3/debug/plain-output.js` | debug-source | [plugins/vm-3.md](plugins/vm-3.md) — generated/debug evidence only | supporting evidence only; no algorithm claim |
| `VM-3/debug/plain.js` | debug-source | [plugins/vm-3.md](plugins/vm-3.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-3/debug/pool.json` | diagnostic-data | [plugins/vm-3.md](plugins/vm-3.md) — diagnostic evidence only | supporting evidence only; no algorithm claim |
| `VM-3/debug/specs.js` | debug-source | [plugins/vm-3.md](plugins/vm-3.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-3/debug/specs.txt` | diagnostic-data | [plugins/vm-3.md](plugins/vm-3.md) — diagnostic evidence only | supporting evidence only; no algorithm claim |
| `VM-3/debug/ssacheck.js` | debug-source | [plugins/vm-3.md](plugins/vm-3.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-3/debug/stages.js` | debug-source | [plugins/vm-3.md](plugins/vm-3.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-3/debug/trace-pcs.json` | diagnostic-data | [plugins/vm-3.md](plugins/vm-3.md) — diagnostic evidence only | supporting evidence only; no algorithm claim |
| `VM-3/debug/trace.js` | debug-source | [plugins/vm-3.md](plugins/vm-3.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-3/debug/vmshape.js` | debug-source | [plugins/vm-3.md](plugins/vm-3.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-3/input.js` | fixture-source | [plugins/vm-3.md](plugins/vm-3.md) — fixture evidence only | supporting evidence only; no algorithm claim |
| `VM-3/output.js` | generated-output | [vm-3-reloop-cleanup-emission](transforms/vm-3-reloop-cleanup-emission.md) — generated-output provenance only | supporting evidence only; no algorithm claim |
| `VM-3/regular.js` | fixture-source | [vm-3-fallback-validation](transforms/vm-3-fallback-validation.md) — non-VM pass-through fixture | supporting evidence only; no algorithm claim |
| `VM-3/test.js` | fixture-source | [vm-3-fallback-validation](transforms/vm-3-fallback-validation.md) — intended checks only | supporting evidence only; no algorithm claim |
| `VM-3/vm.js` | algorithm-source | [plugins/vm-3.md](plugins/vm-3.md), [vm-3-structural-vm-detection](transforms/vm-3-structural-vm-detection.md), [vm-3-handler-canonicalization](transforms/vm-3-handler-canonicalization.md), [vm-3-payload-disassembly](transforms/vm-3-payload-disassembly.md), [vm-3-state-specialized-lifting](transforms/vm-3-state-specialized-lifting.md), [vm-3-reloop-cleanup-emission](transforms/vm-3-reloop-cleanup-emission.md), [vm-3-fallback-validation](transforms/vm-3-fallback-validation.md) — source spans the driver and all six boundaries | source-backed documentary claim; no transfer |
| `VM-4/NOTES.md` | documentation | [plugins/vm-4.md](plugins/vm-4.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-4/README.md` | documentation | [plugins/vm-4.md](plugins/vm-4.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-4/debug-blocks.txt` | diagnostic-data | [plugins/vm-4.md](plugins/vm-4.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-4/debug-bytecode.txt` | diagnostic-data | [plugins/vm-4.md](plugins/vm-4.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-4/debug-classify.js` | debug-source | [plugins/vm-4.md](plugins/vm-4.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-4/debug-classify.txt` | diagnostic-data | [plugins/vm-4.md](plugins/vm-4.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-4/debug-consts.txt` | diagnostic-data | [plugins/vm-4.md](plugins/vm-4.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-4/debug-disasm.js` | debug-source | [plugins/vm-4.md](plugins/vm-4.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-4/debug-disasm.txt` | diagnostic-data | [plugins/vm-4.md](plugins/vm-4.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-4/debug-explore.js` | debug-source | [plugins/vm-4.md](plugins/vm-4.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-4/debug-handlers.txt` | diagnostic-data | [plugins/vm-4.md](plugins/vm-4.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-4/debug-ops-summary.txt` | diagnostic-data | [plugins/vm-4.md](plugins/vm-4.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-4/debug-ops.js` | debug-source | [plugins/vm-4.md](plugins/vm-4.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-4/debug-ops.txt` | diagnostic-data | [plugins/vm-4.md](plugins/vm-4.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-4/debug-passthrough.js` | debug-source | [plugins/vm-4.md](plugins/vm-4.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-4/debug-profile.js` | debug-source | [plugins/vm-4.md](plugins/vm-4.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-4/debug-profile.txt` | diagnostic-data | [plugins/vm-4.md](plugins/vm-4.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-4/debug-trace-ops.txt` | diagnostic-data | [plugins/vm-4.md](plugins/vm-4.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-4/debug-trace.js` | debug-source | [plugins/vm-4.md](plugins/vm-4.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-4/debug-trace.txt` | diagnostic-data | [plugins/vm-4.md](plugins/vm-4.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-4/input.js` | fixture-source | [plugins/vm-4.md](plugins/vm-4.md) — fixture evidence only | supporting evidence only; no algorithm claim |
| `VM-4/output.js` | generated-output | [plugins/vm-4.md](plugins/vm-4.md) — generated-output provenance only | supporting evidence only; no algorithm claim |
| `VM-4/regular.js` | fixture-source | [plugins/vm-4.md](plugins/vm-4.md) — fixture evidence only | supporting evidence only; no algorithm claim |
| `VM-4/test.js` | fixture-source | [plugins/vm-4.md](plugins/vm-4.md) — fixture evidence only | supporting evidence only; no algorithm claim |
| `VM-4/vm.js` | algorithm-source | [plugins/vm-4.md](plugins/vm-4.md), [transforms/vm-4-static-handler-recovery.md](transforms/vm-4-static-handler-recovery.md) — source-backed sample driver and algorithm spans | source-backed documentary claim; no transfer |
| `VM-5/NOTES.md` | documentation | [plugins/vm-5.md](plugins/vm-5.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-5/README.md` | documentation | [plugins/vm-5.md](plugins/vm-5.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-5/debug/analyze-section.js` | debug-source | [plugins/vm-5.md](plugins/vm-5.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-5/debug/attack-fitter.js` | debug-source | [plugins/vm-5.md](plugins/vm-5.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-5/debug/blocks.js` | debug-source | [plugins/vm-5.md](plugins/vm-5.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-5/debug/cfg.js` | debug-source | [plugins/vm-5.md](plugins/vm-5.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-5/debug/cfg1.txt` | diagnostic-data | [plugins/vm-5.md](plugins/vm-5.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-5/debug/classify-section.js` | debug-source | [plugins/vm-5.md](plugins/vm-5.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-5/debug/constprop.js` | debug-source | [plugins/vm-5.md](plugins/vm-5.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-5/debug/decode-section.js` | debug-source | [plugins/vm-5.md](plugins/vm-5.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-5/debug/disasm.js` | debug-source | [plugins/vm-5.md](plugins/vm-5.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-5/debug/disasm.txt` | diagnostic-data | [plugins/vm-5.md](plugins/vm-5.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-5/debug/driver-section.js` | debug-source | [plugins/vm-5.md](plugins/vm-5.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-5/debug/dump.js` | debug-source | [plugins/vm-5.md](plugins/vm-5.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-5/debug/emit-section.js` | debug-source | [plugins/vm-5.md](plugins/vm-5.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-5/debug/equiv.js` | debug-source | [plugins/vm-5.md](plugins/vm-5.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-5/debug/exec-pcs.json` | diagnostic-data | [plugins/vm-5.md](plugins/vm-5.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-5/debug/fit.js` | debug-source | [plugins/vm-5.md](plugins/vm-5.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-5/debug/framelayout-section.js` | debug-source | [plugins/vm-5.md](plugins/vm-5.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-5/debug/handlers.js` | debug-source | [plugins/vm-5.md](plugins/vm-5.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-5/debug/handlers.txt` | diagnostic-data | [plugins/vm-5.md](plugins/vm-5.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-5/debug/lift-section.js` | debug-source | [plugins/vm-5.md](plugins/vm-5.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-5/debug/linear.js` | debug-source | [plugins/vm-5.md](plugins/vm-5.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-5/debug/linear.txt` | diagnostic-data | [plugins/vm-5.md](plugins/vm-5.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-5/debug/load.js` | debug-source | [plugins/vm-5.md](plugins/vm-5.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-5/debug/new-analyze.js` | debug-source | [plugins/vm-5.md](plugins/vm-5.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-5/debug/old-analyzeFunction.js` | debug-source | [plugins/vm-5.md](plugins/vm-5.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-5/debug/patch-dup.js` | debug-source | [plugins/vm-5.md](plugins/vm-5.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-5/debug/patch-fit.js` | debug-source | [plugins/vm-5.md](plugins/vm-5.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-5/debug/patch-gdce.js` | debug-source | [plugins/vm-5.md](plugins/vm-5.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-5/debug/patch-inline.js` | debug-source | [plugins/vm-5.md](plugins/vm-5.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-5/debug/patch-polish.js` | debug-source | [plugins/vm-5.md](plugins/vm-5.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-5/debug/patch-seed.js` | debug-source | [plugins/vm-5.md](plugins/vm-5.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-5/debug/patch1.js` | debug-source | [plugins/vm-5.md](plugins/vm-5.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-5/debug/pathexp.js` | debug-source | [plugins/vm-5.md](plugins/vm-5.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-5/debug/roles.txt` | diagnostic-data | [plugins/vm-5.md](plugins/vm-5.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-5/debug/stage1.js` | debug-source | [plugins/vm-5.md](plugins/vm-5.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-5/debug/stage2.js` | debug-source | [plugins/vm-5.md](plugins/vm-5.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-5/debug/stage3.js` | debug-source | [plugins/vm-5.md](plugins/vm-5.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-5/debug/stage3b.js` | debug-source | [plugins/vm-5.md](plugins/vm-5.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-5/debug/stage4.js` | debug-source | [plugins/vm-5.md](plugins/vm-5.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-5/debug/stepstate-new.js` | debug-source | [plugins/vm-5.md](plugins/vm-5.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-5/debug/struct-section.js` | debug-source | [plugins/vm-5.md](plugins/vm-5.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-5/debug/sym-section.js` | debug-source | [plugins/vm-5.md](plugins/vm-5.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-5/debug/trace-order.json` | diagnostic-data | [plugins/vm-5.md](plugins/vm-5.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-5/debug/trace.js` | debug-source | [plugins/vm-5.md](plugins/vm-5.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-5/debug/trace.json` | diagnostic-data | [plugins/vm-5.md](plugins/vm-5.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-5/debug/trace2.js` | debug-source | [plugins/vm-5.md](plugins/vm-5.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-5/debug/unres.js` | debug-source | [plugins/vm-5.md](plugins/vm-5.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-5/input.js` | fixture-source | [plugins/vm-5.md](plugins/vm-5.md) — fixture evidence only | supporting evidence only; no algorithm claim |
| `VM-5/output.js` | generated-output | [plugins/vm-5.md](plugins/vm-5.md) — generated-output provenance only | supporting evidence only; no algorithm claim |
| `VM-5/vm.js` | algorithm-source | [plugins/vm-5.md](plugins/vm-5.md), [transforms/vm-5-live-handler-fit-recovery.md](transforms/vm-5-live-handler-fit-recovery.md) — source-backed sample driver and algorithm spans | source-backed documentary claim; no transfer |
| `VM-6/NOTES.md` | documentation | [plugins/vm-6.md](plugins/vm-6.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-6/README.md` | documentation | [plugins/vm-6.md](plugins/vm-6.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-6/debug/analyze.js` | debug-source | [plugins/vm-6.md](plugins/vm-6.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-6/debug/assemble.js` | debug-source | [plugins/vm-6.md](plugins/vm-6.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-6/debug/blocks.txt` | diagnostic-data | [plugins/vm-6.md](plugins/vm-6.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-6/debug/bytecode.json` | diagnostic-data | [plugins/vm-6.md](plugins/vm-6.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-6/debug/cfg.txt` | diagnostic-data | [plugins/vm-6.md](plugins/vm-6.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-6/debug/cfg2.txt` | diagnostic-data | [plugins/vm-6.md](plugins/vm-6.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-6/debug/classify.js` | debug-source | [plugins/vm-6.md](plugins/vm-6.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-6/debug/disasm.js` | debug-source | [plugins/vm-6.md](plugins/vm-6.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-6/debug/disasm.txt` | diagnostic-data | [plugins/vm-6.md](plugins/vm-6.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-6/debug/dump.js` | debug-source | [plugins/vm-6.md](plugins/vm-6.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-6/debug/dump2.js` | debug-source | [plugins/vm-6.md](plugins/vm-6.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-6/debug/explore.js` | debug-source | [plugins/vm-6.md](plugins/vm-6.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-6/debug/extract.js` | debug-source | [plugins/vm-6.md](plugins/vm-6.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-6/debug/handlers.txt` | diagnostic-data | [plugins/vm-6.md](plugins/vm-6.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-6/debug/layout.json` | diagnostic-data | [plugins/vm-6.md](plugins/vm-6.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-6/debug/listing.txt` | diagnostic-data | [plugins/vm-6.md](plugins/vm-6.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-6/debug/load.js` | debug-source | [plugins/vm-6.md](plugins/vm-6.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-6/debug/opcodes.js` | debug-source | [plugins/vm-6.md](plugins/vm-6.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-6/debug/ops.js` | debug-source | [plugins/vm-6.md](plugins/vm-6.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-6/debug/probe.js` | debug-source | [plugins/vm-6.md](plugins/vm-6.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-6/debug/trace.js` | debug-source | [plugins/vm-6.md](plugins/vm-6.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-6/input.js` | fixture-source | [plugins/vm-6.md](plugins/vm-6.md) — fixture evidence only | supporting evidence only; no algorithm claim |
| `VM-6/output.js` | generated-output | [plugins/vm-6.md](plugins/vm-6.md) — generated-output provenance only | supporting evidence only; no algorithm claim |
| `VM-6/regular.js` | fixture-source | [plugins/vm-6.md](plugins/vm-6.md) — fixture evidence only | supporting evidence only; no algorithm claim |
| `VM-6/test-features.js` | fixture-source | [plugins/vm-6.md](plugins/vm-6.md) — fixture evidence only | supporting evidence only; no algorithm claim |
| `VM-6/test.js` | fixture-source | [plugins/vm-6.md](plugins/vm-6.md) — fixture evidence only | supporting evidence only; no algorithm claim |
| `VM-6/vm.js` | algorithm-source | [plugins/vm-6.md](plugins/vm-6.md), [transforms/vm-6-site-salted-handler-fitting.md](transforms/vm-6-site-salted-handler-fitting.md) — source-backed sample driver and algorithm spans | source-backed documentary claim; no transfer |
| `VM-7/NOTES.md` | documentation | [plugins/vm-7.md](plugins/vm-7.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-7/README.md` | documentation | [plugins/vm-7.md](plugins/vm-7.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-7/debug/analyze.js` | debug-source | [plugins/vm-7.md](plugins/vm-7.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-7/debug/beautify.js` | debug-source | [plugins/vm-7.md](plugins/vm-7.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-7/debug/cfg.js` | debug-source | [plugins/vm-7.md](plugins/vm-7.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-7/debug/cfg.txt` | diagnostic-data | [plugins/vm-7.md](plugins/vm-7.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-7/debug/compare-run.js` | debug-source | [plugins/vm-7.md](plugins/vm-7.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-7/debug/count-oracle.js` | debug-source | [plugins/vm-7.md](plugins/vm-7.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-7/debug/diag-states.js` | debug-source | [plugins/vm-7.md](plugins/vm-7.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-7/debug/disasm.js` | debug-source | [plugins/vm-7.md](plugins/vm-7.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-7/debug/dispatch-test.js` | debug-source | [plugins/vm-7.md](plugins/vm-7.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-7/debug/dom-shim.js` | debug-source | [plugins/vm-7.md](plugins/vm-7.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-7/debug/dump-handlers.js` | debug-source | [plugins/vm-7.md](plugins/vm-7.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-7/debug/dump-lib-ir.js` | debug-source | [plugins/vm-7.md](plugins/vm-7.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-7/debug/fit.js` | debug-source | [plugins/vm-7.md](plugins/vm-7.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-7/debug/fit2.js` | debug-source | [plugins/vm-7.md](plugins/vm-7.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-7/debug/fold-flaky.js` | debug-source | [plugins/vm-7.md](plugins/vm-7.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-7/debug/fold-probe.js` | debug-source | [plugins/vm-7.md](plugins/vm-7.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-7/debug/handlers.js` | debug-source | [plugins/vm-7.md](plugins/vm-7.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-7/debug/harness.js` | debug-source | [plugins/vm-7.md](plugins/vm-7.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-7/debug/input.pretty.js` | debug-source | [plugins/vm-7.md](plugins/vm-7.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-7/debug/ir-1758.txt` | diagnostic-data | [plugins/vm-7.md](plugins/vm-7.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-7/debug/ir-37.txt` | diagnostic-data | [plugins/vm-7.md](plugins/vm-7.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-7/debug/ir-dump.js` | debug-source | [plugins/vm-7.md](plugins/vm-7.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-7/debug/ir-nodes.js` | debug-source | [plugins/vm-7.md](plugins/vm-7.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-7/debug/ir-nodes.txt` | diagnostic-data | [plugins/vm-7.md](plugins/vm-7.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-7/debug/ir.txt` | diagnostic-data | [plugins/vm-7.md](plugins/vm-7.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-7/debug/junk-test.js` | debug-source | [plugins/vm-7.md](plugins/vm-7.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-7/debug/keycheck.js` | debug-source | [plugins/vm-7.md](plugins/vm-7.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-7/debug/lift-1758.txt` | diagnostic-data | [plugins/vm-7.md](plugins/vm-7.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-7/debug/lift-trace.js` | debug-source | [plugins/vm-7.md](plugins/vm-7.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-7/debug/norm.err` | diagnostic-data | [plugins/vm-7.md](plugins/vm-7.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-7/debug/normalize-handlers.js` | debug-source | [plugins/vm-7.md](plugins/vm-7.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-7/debug/print-cfg.js` | debug-source | [plugins/vm-7.md](plugins/vm-7.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-7/debug/print-disasm.js` | debug-source | [plugins/vm-7.md](plugins/vm-7.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-7/debug/probe.js` | debug-source | [plugins/vm-7.md](plugins/vm-7.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-7/debug/run-input.js` | debug-source | [plugins/vm-7.md](plugins/vm-7.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-7/debug/semantics.js` | debug-source | [plugins/vm-7.md](plugins/vm-7.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-7/debug/sweep.err` | diagnostic-data | [plugins/vm-7.md](plugins/vm-7.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-7/debug/sweep.js` | debug-source | [plugins/vm-7.md](plugins/vm-7.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-7/debug/sweep.txt` | diagnostic-data | [plugins/vm-7.md](plugins/vm-7.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-7/debug/test-classify.js` | debug-source | [plugins/vm-7.md](plugins/vm-7.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-7/debug/trace-exec.js` | debug-source | [plugins/vm-7.md](plugins/vm-7.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-7/debug/trace-values.js` | debug-source | [plugins/vm-7.md](plugins/vm-7.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-7/debug/trace.js` | debug-source | [plugins/vm-7.md](plugins/vm-7.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-7/debug/validate-cfg.js` | debug-source | [plugins/vm-7.md](plugins/vm-7.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-7/debug/validate2.js` | debug-source | [plugins/vm-7.md](plugins/vm-7.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-7/debug/vmmodel.js` | debug-source | [plugins/vm-7.md](plugins/vm-7.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-7/debug/vmmodel2.js` | debug-source | [plugins/vm-7.md](plugins/vm-7.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-7/debug/widen-metrics.js` | debug-source | [plugins/vm-7.md](plugins/vm-7.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-7/debug/widen-trace.js` | debug-source | [plugins/vm-7.md](plugins/vm-7.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-7/input.js` | fixture-source | [plugins/vm-7.md](plugins/vm-7.md) — fixture evidence only | supporting evidence only; no algorithm claim |
| `VM-7/lib/analyze.js` | library-source | [transforms/vm-7-behavioral-abstract-state-lifting.md](transforms/vm-7-behavioral-abstract-state-lifting.md) — source-backed distinct algorithm detail; plugin-owned | source-backed documentary claim; no transfer |
| `VM-7/lib/emit.js` | library-source | [transforms/vm-7-behavioral-abstract-state-lifting.md](transforms/vm-7-behavioral-abstract-state-lifting.md) — source-backed distinct algorithm detail; plugin-owned | source-backed documentary claim; no transfer |
| `VM-7/lib/fit.js` | library-source | [transforms/vm-7-behavioral-abstract-state-lifting.md](transforms/vm-7-behavioral-abstract-state-lifting.md) — source-backed distinct algorithm detail; plugin-owned | source-backed documentary claim; no transfer |
| `VM-7/lib/lift.js` | library-source | [transforms/vm-7-behavioral-abstract-state-lifting.md](transforms/vm-7-behavioral-abstract-state-lifting.md) — source-backed distinct algorithm detail; plugin-owned | source-backed documentary claim; no transfer |
| `VM-7/lib/machine.js` | library-source | [transforms/vm-7-behavioral-abstract-state-lifting.md](transforms/vm-7-behavioral-abstract-state-lifting.md) — source-backed distinct algorithm detail; plugin-owned | source-backed documentary claim; no transfer |
| `VM-7/lib/polish.js` | library-source | [transforms/vm-7-behavioral-abstract-state-lifting.md](transforms/vm-7-behavioral-abstract-state-lifting.md) — source-backed distinct algorithm detail; plugin-owned | source-backed documentary claim; no transfer |
| `VM-7/lib/structure.js` | library-source | [transforms/vm-7-behavioral-abstract-state-lifting.md](transforms/vm-7-behavioral-abstract-state-lifting.md) — source-backed distinct algorithm detail; plugin-owned | source-backed documentary claim; no transfer |
| `VM-7/output.js` | generated-output | [plugins/vm-7.md](plugins/vm-7.md) — generated-output provenance only | supporting evidence only; no algorithm claim |
| `VM-7/regular.js` | fixture-source | [plugins/vm-7.md](plugins/vm-7.md) — fixture evidence only | supporting evidence only; no algorithm claim |
| `VM-7/test.js` | fixture-source | [plugins/vm-7.md](plugins/vm-7.md) — fixture evidence only | supporting evidence only; no algorithm claim |
| `VM-7/vm.js` | algorithm-source | [plugins/vm-7.md](plugins/vm-7.md), [transforms/vm-7-behavioral-abstract-state-lifting.md](transforms/vm-7-behavioral-abstract-state-lifting.md) — source-backed sample driver and algorithm spans | source-backed documentary claim; no transfer |
| `VM-8/NOTES.md` | documentation | [plugins/vm-8.md](plugins/vm-8.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-8/README.md` | documentation | [plugins/vm-8.md](plugins/vm-8.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-8/debug/allops.js` | debug-source | [plugins/vm-8.md](plugins/vm-8.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-8/debug/assemble.js` | debug-source | [plugins/vm-8.md](plugins/vm-8.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-8/debug/beautify.js` | debug-source | [plugins/vm-8.md](plugins/vm-8.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-8/debug/chk61767.js` | debug-source | [plugins/vm-8.md](plugins/vm-8.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-8/debug/classify.js` | debug-source | [plugins/vm-8.md](plugins/vm-8.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-8/debug/dbg-forin.js` | debug-source | [plugins/vm-8.md](plugins/vm-8.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-8/debug/dbg-mcall.js` | debug-source | [plugins/vm-8.md](plugins/vm-8.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-8/debug/disasm.txt` | diagnostic-data | [plugins/vm-8.md](plugins/vm-8.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-8/debug/dump1.js` | debug-source | [plugins/vm-8.md](plugins/vm-8.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-8/debug/dumph.js` | debug-source | [plugins/vm-8.md](plugins/vm-8.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-8/debug/equiv.js` | debug-source | [plugins/vm-8.md](plugins/vm-8.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-8/debug/exp1.js` | debug-source | [plugins/vm-8.md](plugins/vm-8.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-8/debug/exp2.js` | debug-source | [plugins/vm-8.md](plugins/vm-8.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-8/debug/exp3.js` | debug-source | [plugins/vm-8.md](plugins/vm-8.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-8/debug/features.js` | debug-source | [plugins/vm-8.md](plugins/vm-8.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-8/debug/fit.js` | debug-source | [plugins/vm-8.md](plugins/vm-8.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-8/debug/fit.json` | diagnostic-data | [plugins/vm-8.md](plugins/vm-8.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-8/debug/fit2.js` | debug-source | [plugins/vm-8.md](plugins/vm-8.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-8/debug/fit2.json` | diagnostic-data | [plugins/vm-8.md](plugins/vm-8.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-8/debug/fit3.js` | debug-source | [plugins/vm-8.md](plugins/vm-8.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-8/debug/fit3.json` | diagnostic-data | [plugins/vm-8.md](plugins/vm-8.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-8/debug/fns.json` | diagnostic-data | [plugins/vm-8.md](plugins/vm-8.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-8/debug/gen/encoded_bytecode.js` | debug-source | [plugins/vm-8.md](plugins/vm-8.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-8/debug/gen/encoded_bytecode.out.js` | debug-source | [plugins/vm-8.md](plugins/vm-8.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-8/debug/gen/for_in.js` | debug-source | [plugins/vm-8.md](plugins/vm-8.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-8/debug/gen/for_in.out.js` | debug-source | [plugins/vm-8.md](plugins/vm-8.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-8/debug/gen/objects.js` | debug-source | [plugins/vm-8.md](plugins/vm-8.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-8/debug/gen/objects.out.js` | debug-source | [plugins/vm-8.md](plugins/vm-8.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-8/debug/gen/try_catch.js` | debug-source | [plugins/vm-8.md](plugins/vm-8.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-8/debug/gen/try_catch.out.js` | debug-source | [plugins/vm-8.md](plugins/vm-8.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-8/debug/gen/try_join.js` | debug-source | [plugins/vm-8.md](plugins/vm-8.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-8/debug/gen/try_join.out.js` | debug-source | [plugins/vm-8.md](plugins/vm-8.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-8/debug/handlers.txt` | diagnostic-data | [plugins/vm-8.md](plugins/vm-8.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-8/debug/input.pretty.js` | debug-source | [plugins/vm-8.md](plugins/vm-8.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-8/debug/loader.js` | debug-source | [plugins/vm-8.md](plugins/vm-8.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-8/debug/opsummary.json` | diagnostic-data | [plugins/vm-8.md](plugins/vm-8.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-8/debug/permute.js` | debug-source | [plugins/vm-8.md](plugins/vm-8.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-8/debug/permuted.js` | debug-source | [plugins/vm-8.md](plugins/vm-8.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-8/debug/permuted.out.js` | debug-source | [plugins/vm-8.md](plugins/vm-8.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-8/debug/peval.txt` | diagnostic-data | [plugins/vm-8.md](plugins/vm-8.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-8/debug/probe.js` | debug-source | [plugins/vm-8.md](plugins/vm-8.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-8/debug/run-analyze.js` | debug-source | [plugins/vm-8.md](plugins/vm-8.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-8/debug/run-orig.js` | debug-source | [plugins/vm-8.md](plugins/vm-8.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-8/debug/run-orig2.js` | debug-source | [plugins/vm-8.md](plugins/vm-8.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-8/debug/run-orig3.js` | debug-source | [plugins/vm-8.md](plugins/vm-8.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-8/debug/run-peval.js` | debug-source | [plugins/vm-8.md](plugins/vm-8.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-8/debug/shim.js` | debug-source | [plugins/vm-8.md](plugins/vm-8.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-8/debug/slots.js` | debug-source | [plugins/vm-8.md](plugins/vm-8.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-8/debug/sweep.js` | debug-source | [plugins/vm-8.md](plugins/vm-8.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-8/debug/sweep.json` | diagnostic-data | [plugins/vm-8.md](plugins/vm-8.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-8/debug/trace.js` | debug-source | [plugins/vm-8.md](plugins/vm-8.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-8/debug/trace.json` | diagnostic-data | [plugins/vm-8.md](plugins/vm-8.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-8/debug/trace2.js` | debug-source | [plugins/vm-8.md](plugins/vm-8.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-8/debug/trace3.js` | debug-source | [plugins/vm-8.md](plugins/vm-8.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-8/debug/trace3.json` | diagnostic-data | [plugins/vm-8.md](plugins/vm-8.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-8/debug/tricky.js` | debug-source | [plugins/vm-8.md](plugins/vm-8.md) — debug evidence only | supporting evidence only; no algorithm claim |
| `VM-8/input.js` | fixture-source | [plugins/vm-8.md](plugins/vm-8.md) — fixture evidence only | supporting evidence only; no algorithm claim |
| `VM-8/lib-analyze.js` | library-source | [transforms/vm-8-oracle-classification-partial-evaluation.md](transforms/vm-8-oracle-classification-partial-evaluation.md) — source-backed distinct algorithm detail; plugin-owned | source-backed documentary claim; no transfer |
| `VM-8/lib-classify.js` | library-source | [transforms/vm-8-oracle-classification-partial-evaluation.md](transforms/vm-8-oracle-classification-partial-evaluation.md) — source-backed distinct algorithm detail; plugin-owned | source-backed documentary claim; no transfer |
| `VM-8/lib-codegen.js` | library-source | [transforms/vm-8-oracle-classification-partial-evaluation.md](transforms/vm-8-oracle-classification-partial-evaluation.md) — source-backed distinct algorithm detail; plugin-owned | source-backed documentary claim; no transfer |
| `VM-8/lib-disasm.js` | library-source | [transforms/vm-8-oracle-classification-partial-evaluation.md](transforms/vm-8-oracle-classification-partial-evaluation.md) — source-backed distinct algorithm detail; plugin-owned | source-backed documentary claim; no transfer |
| `VM-8/lib-emit.js` | library-source | [transforms/vm-8-oracle-classification-partial-evaluation.md](transforms/vm-8-oracle-classification-partial-evaluation.md) — source-backed distinct algorithm detail; plugin-owned | source-backed documentary claim; no transfer |
| `VM-8/lib-extract.js` | library-source | [transforms/vm-8-oracle-classification-partial-evaluation.md](transforms/vm-8-oracle-classification-partial-evaluation.md) — source-backed distinct algorithm detail; plugin-owned | source-backed documentary claim; no transfer |
| `VM-8/lib-peval.js` | library-source | [transforms/vm-8-oracle-classification-partial-evaluation.md](transforms/vm-8-oracle-classification-partial-evaluation.md) — source-backed distinct algorithm detail; plugin-owned | source-backed documentary claim; no transfer |
| `VM-8/lib-polish.js` | library-source | [transforms/vm-8-oracle-classification-partial-evaluation.md](transforms/vm-8-oracle-classification-partial-evaluation.md) — source-backed distinct algorithm detail; plugin-owned | source-backed documentary claim; no transfer |
| `VM-8/lib-probe.js` | library-source | [transforms/vm-8-oracle-classification-partial-evaluation.md](transforms/vm-8-oracle-classification-partial-evaluation.md) — source-backed distinct algorithm detail; plugin-owned | source-backed documentary claim; no transfer |
| `VM-8/output.js` | generated-output | [plugins/vm-8.md](plugins/vm-8.md) — generated-output provenance only | supporting evidence only; no algorithm claim |
| `VM-8/regular.js` | fixture-source | [plugins/vm-8.md](plugins/vm-8.md) — fixture evidence only | supporting evidence only; no algorithm claim |
| `VM-8/test.js` | fixture-source | [plugins/vm-8.md](plugins/vm-8.md) — fixture evidence only | supporting evidence only; no algorithm claim |
| `VM-8/vm.js` | algorithm-source | [plugins/vm-8.md](plugins/vm-8.md), [transforms/vm-8-oracle-classification-partial-evaluation.md](transforms/vm-8-oracle-classification-partial-evaluation.md) — source-backed sample driver and algorithm spans | source-backed documentary claim; no transfer |
| `VM-GLM-1/NOTES.md` | documentation | [plugins/vm-glm-1.md](plugins/vm-glm-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-GLM-1/README.md` | documentation | [plugins/vm-glm-1.md](plugins/vm-glm-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-GLM-1/RESUME.md` | documentation | [plugins/vm-glm-1.md](plugins/vm-glm-1.md) — development log, excluded from durable algorithm claims | documentation classification only |
| `VM-GLM-1/RESUME_2.md` | documentation | [plugins/vm-glm-1.md](plugins/vm-glm-1.md) — development log, excluded from durable algorithm claims | documentation classification only |
| `VM-GLM-1/RESUME_3.md` | documentation | [plugins/vm-glm-1.md](plugins/vm-glm-1.md) — development log, excluded from durable algorithm claims | documentation classification only |
| `VM-GLM-1/debug/01_run_input.js` | debug-source | [plugins/vm-glm-1.md](plugins/vm-glm-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-GLM-1/debug/01_trace.txt` | diagnostic-data | [plugins/vm-glm-1.md](plugins/vm-glm-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-GLM-1/debug/01b_trace_input.js` | debug-source | [plugins/vm-glm-1.md](plugins/vm-glm-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-GLM-1/debug/02_extract.js` | debug-source | [plugins/vm-glm-1.md](plugins/vm-glm-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-GLM-1/debug/03_records.js` | debug-source | [plugins/vm-glm-1.md](plugins/vm-glm-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-GLM-1/debug/04_disasm.js` | debug-source | [plugins/vm-glm-1.md](plugins/vm-glm-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-GLM-1/debug/05_trace_input.txt` | diagnostic-data | [plugins/vm-glm-1.md](plugins/vm-glm-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-GLM-1/debug/05_trace_output.txt` | diagnostic-data | [plugins/vm-glm-1.md](plugins/vm-glm-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-GLM-1/debug/05_verify_output.js` | debug-source | [plugins/vm-glm-1.md](plugins/vm-glm-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-GLM-1/debug/06_real_call.js` | debug-source | [plugins/vm-glm-1.md](plugins/vm-glm-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-GLM-1/debug/07_probe_log.js` | debug-source | [plugins/vm-glm-1.md](plugins/vm-glm-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-GLM-1/debug/blocks_dump.txt` | diagnostic-data | [plugins/vm-glm-1.md](plugins/vm-glm-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-GLM-1/debug/blocks_predissolve.txt` | diagnostic-data | [plugins/vm-glm-1.md](plugins/vm-glm-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-GLM-1/debug/bytecode.json` | diagnostic-data | [plugins/vm-glm-1.md](plugins/vm-glm-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-GLM-1/debug/disasm.txt` | diagnostic-data | [plugins/vm-glm-1.md](plugins/vm-glm-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-GLM-1/debug/dissolve_dbg.txt` | diagnostic-data | [plugins/vm-glm-1.md](plugins/vm-glm-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-GLM-1/debug/dissolve_dbg2.txt` | diagnostic-data | [plugins/vm-glm-1.md](plugins/vm-glm-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-GLM-1/debug/dissolve_dbg3.txt` | diagnostic-data | [plugins/vm-glm-1.md](plugins/vm-glm-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-GLM-1/debug/handler_records.txt` | diagnostic-data | [plugins/vm-glm-1.md](plugins/vm-glm-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-GLM-1/debug/handlers_dump.js` | debug-source | [plugins/vm-glm-1.md](plugins/vm-glm-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-GLM-1/input.js` | fixture-source | [plugins/vm-glm-1.md](plugins/vm-glm-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-GLM-1/output.js` | generated-output | [plugins/vm-glm-1.md](plugins/vm-glm-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-GLM-1/regular.js` | fixture-source | [plugins/vm-glm-1.md](plugins/vm-glm-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-GLM-1/test.js` | fixture-source | [plugins/vm-glm-1.md](plugins/vm-glm-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-GLM-1/vm.js` | algorithm-source | [`transforms/vm-glm-1-handler-effects-variation.md`](transforms/vm-glm-1-handler-effects-variation.md) — source-backed distinct variation; plugin-owned | source-backed documentary claim; no transfer |
| `VM-GPT-1/NOTES.md` | documentation | [plugins/vm-gpt-1.md](plugins/vm-gpt-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-GPT-1/README.md` | documentation | [plugins/vm-gpt-1.md](plugins/vm-gpt-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-GPT-1/debug/analyze.js` | debug-source | [plugins/vm-gpt-1.md](plugins/vm-gpt-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-GPT-1/debug/compare.js` | debug-source | [plugins/vm-gpt-1.md](plugins/vm-gpt-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-GPT-1/debug/lifted-output.js` | debug-source | [plugins/vm-gpt-1.md](plugins/vm-gpt-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-GPT-1/debug/lower.js` | debug-source | [plugins/vm-gpt-1.md](plugins/vm-gpt-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-GPT-1/debug/regular-output.js` | debug-source | [plugins/vm-gpt-1.md](plugins/vm-gpt-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-GPT-1/debug/trace.js` | debug-source | [plugins/vm-gpt-1.md](plugins/vm-gpt-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-GPT-1/input.js` | fixture-source | [plugins/vm-gpt-1.md](plugins/vm-gpt-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-GPT-1/lifter.js` | algorithm-source | [`transforms/vm-gpt-1-trace-guided-recovery.md`](transforms/vm-gpt-1-trace-guided-recovery.md) — source-backed distinct recovery boundary; plugin-owned | source-backed documentary claim; no transfer |
| `VM-GPT-1/output.js` | generated-output | [plugins/vm-gpt-1.md](plugins/vm-gpt-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-GPT-1/regular.js` | fixture-source | [plugins/vm-gpt-1.md](plugins/vm-gpt-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-GPT-1/test.js` | fixture-source | [plugins/vm-gpt-1.md](plugins/vm-gpt-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-GPT-1/vm-core.js` | algorithm-source | [`transforms/vm-gpt-1-trace-guided-recovery.md`](transforms/vm-gpt-1-trace-guided-recovery.md) — source-backed distinct recovery boundary; plugin-owned | source-backed documentary claim; no transfer |
| `VM-GPT-1/vm.js` | algorithm-source | [`plugins/vm-gpt-1.md`](plugins/vm-gpt-1.md) — source-backed plugin composition and admission boundary | source-backed documentary claim; no transfer |
| `VM-Kimi-1/NOTES.md` | documentation | [plugins/vm-kimi-1.md](plugins/vm-kimi-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-Kimi-1/README.md` | documentation | [plugins/vm-kimi-1.md](plugins/vm-kimi-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-Kimi-1/debug/blocks.clean.txt` | diagnostic-data | [plugins/vm-kimi-1.md](plugins/vm-kimi-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-Kimi-1/debug/blocks.json` | diagnostic-data | [plugins/vm-kimi-1.md](plugins/vm-kimi-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-Kimi-1/debug/blocks.txt` | diagnostic-data | [plugins/vm-kimi-1.md](plugins/vm-kimi-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-Kimi-1/debug/blocks.utf8.txt` | diagnostic-data | [plugins/vm-kimi-1.md](plugins/vm-kimi-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-Kimi-1/debug/build.js` | debug-source | [plugins/vm-kimi-1.md](plugins/vm-kimi-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-Kimi-1/debug/bytecode.json` | diagnostic-data | [plugins/vm-kimi-1.md](plugins/vm-kimi-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-Kimi-1/debug/cases.js` | debug-source | [plugins/vm-kimi-1.md](plugins/vm-kimi-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-Kimi-1/debug/checkpayload.js` | debug-source | [plugins/vm-kimi-1.md](plugins/vm-kimi-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-Kimi-1/debug/cleanup.js` | debug-source | [plugins/vm-kimi-1.md](plugins/vm-kimi-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-Kimi-1/debug/core.js` | debug-source | [plugins/vm-kimi-1.md](plugins/vm-kimi-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-Kimi-1/debug/detect.js` | debug-source | [plugins/vm-kimi-1.md](plugins/vm-kimi-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-Kimi-1/debug/disasm.js` | debug-source | [plugins/vm-kimi-1.md](plugins/vm-kimi-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-Kimi-1/debug/disasm.json` | diagnostic-data | [plugins/vm-kimi-1.md](plugins/vm-kimi-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-Kimi-1/debug/drive.js` | debug-source | [plugins/vm-kimi-1.md](plugins/vm-kimi-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-Kimi-1/debug/dumpblocks.js` | debug-source | [plugins/vm-kimi-1.md](plugins/vm-kimi-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-Kimi-1/debug/explore.js` | debug-source | [plugins/vm-kimi-1.md](plugins/vm-kimi-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-Kimi-1/debug/extract.js` | debug-source | [plugins/vm-kimi-1.md](plugins/vm-kimi-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-Kimi-1/debug/graph.js` | debug-source | [plugins/vm-kimi-1.md](plugins/vm-kimi-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-Kimi-1/debug/graphlog.txt` | diagnostic-data | [plugins/vm-kimi-1.md](plugins/vm-kimi-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-Kimi-1/debug/graphlog2532.txt` | diagnostic-data | [plugins/vm-kimi-1.md](plugins/vm-kimi-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-Kimi-1/debug/handlers.js` | debug-source | [plugins/vm-kimi-1.md](plugins/vm-kimi-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-Kimi-1/debug/handlers.json` | diagnostic-data | [plugins/vm-kimi-1.md](plugins/vm-kimi-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-Kimi-1/debug/harness.js` | debug-source | [plugins/vm-kimi-1.md](plugins/vm-kimi-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-Kimi-1/debug/innerblocks.json` | diagnostic-data | [plugins/vm-kimi-1.md](plugins/vm-kimi-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-Kimi-1/debug/lift.js` | debug-source | [plugins/vm-kimi-1.md](plugins/vm-kimi-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-Kimi-1/debug/mainblocks.json` | diagnostic-data | [plugins/vm-kimi-1.md](plugins/vm-kimi-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-Kimi-1/debug/ordered.js` | debug-source | [plugins/vm-kimi-1.md](plugins/vm-kimi-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-Kimi-1/debug/out.js` | debug-source | [plugins/vm-kimi-1.md](plugins/vm-kimi-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-Kimi-1/debug/payloads.txt` | diagnostic-data | [plugins/vm-kimi-1.md](plugins/vm-kimi-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-Kimi-1/debug/printdis.js` | debug-source | [plugins/vm-kimi-1.md](plugins/vm-kimi-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-Kimi-1/debug/probe.js` | debug-source | [plugins/vm-kimi-1.md](plugins/vm-kimi-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-Kimi-1/debug/run_orig.txt` | diagnostic-data | [plugins/vm-kimi-1.md](plugins/vm-kimi-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-Kimi-1/debug/run_out.txt` | diagnostic-data | [plugins/vm-kimi-1.md](plugins/vm-kimi-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-Kimi-1/debug/showtrace.js` | debug-source | [plugins/vm-kimi-1.md](plugins/vm-kimi-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-Kimi-1/debug/simtrace.json` | diagnostic-data | [plugins/vm-kimi-1.md](plugins/vm-kimi-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-Kimi-1/debug/simulate.js` | debug-source | [plugins/vm-kimi-1.md](plugins/vm-kimi-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-Kimi-1/debug/sweep.js` | debug-source | [plugins/vm-kimi-1.md](plugins/vm-kimi-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-Kimi-1/debug/sweep2532.txt` | diagnostic-data | [plugins/vm-kimi-1.md](plugins/vm-kimi-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-Kimi-1/debug/testcleanup.js` | debug-source | [plugins/vm-kimi-1.md](plugins/vm-kimi-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-Kimi-1/debug/testcleanup2.js` | debug-source | [plugins/vm-kimi-1.md](plugins/vm-kimi-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-Kimi-1/debug/testcleanup3.js` | debug-source | [plugins/vm-kimi-1.md](plugins/vm-kimi-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-Kimi-1/debug/testdetect.js` | debug-source | [plugins/vm-kimi-1.md](plugins/vm-kimi-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-Kimi-1/debug/testuf.js` | debug-source | [plugins/vm-kimi-1.md](plugins/vm-kimi-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-Kimi-1/debug/trace.js` | debug-source | [plugins/vm-kimi-1.md](plugins/vm-kimi-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-Kimi-1/debug/trace_ops.json` | diagnostic-data | [plugins/vm-kimi-1.md](plugins/vm-kimi-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-Kimi-1/debug/trace_reads.json` | diagnostic-data | [plugins/vm-kimi-1.md](plugins/vm-kimi-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-Kimi-1/debug/trace_strs.json` | diagnostic-data | [plugins/vm-kimi-1.md](plugins/vm-kimi-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-Kimi-1/debug/unflatten.js` | debug-source | [plugins/vm-kimi-1.md](plugins/vm-kimi-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-Kimi-1/input.js` | fixture-source | [plugins/vm-kimi-1.md](plugins/vm-kimi-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-Kimi-1/output.js` | generated-output | [plugins/vm-kimi-1.md](plugins/vm-kimi-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-Kimi-1/regular.js` | fixture-source | [plugins/vm-kimi-1.md](plugins/vm-kimi-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-Kimi-1/test.js` | fixture-source | [plugins/vm-kimi-1.md](plugins/vm-kimi-1.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VM-Kimi-1/vm.js` | algorithm-source | [`transforms/vm-kimi-1-static-decrypt-dispatch.md`](transforms/vm-kimi-1-static-decrypt-dispatch.md) — source-backed distinct recovery boundary; plugin-owned | source-backed documentary claim; no transfer |
| `VariableMasking/README.md` | documentation | [plugins/variable-masking.md](plugins/variable-masking.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VariableMasking/debug-pattern.json` | diagnostic-data | [plugins/variable-masking.md](plugins/variable-masking.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VariableMasking/input.js` | fixture-source | [plugins/variable-masking.md](plugins/variable-masking.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VariableMasking/original.js` | fixture-source | [plugins/variable-masking.md](plugins/variable-masking.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VariableMasking/output.js` | generated-output | [plugins/variable-masking.md](plugins/variable-masking.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VariableMasking/regular.js` | fixture-source | [plugins/variable-masking.md](plugins/variable-masking.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VariableMasking/regular.output.js` | generated-output | [plugins/variable-masking.md](plugins/variable-masking.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VariableMasking/test.js` | fixture-source | [plugins/variable-masking.md](plugins/variable-masking.md) — sample-owned evidence-only | supporting evidence only; no algorithm claim |
| `VariableMasking/variableMasking.js` | algorithm-source | [transforms/variable-masking-rest-parameter-recovery.md](transforms/variable-masking-rest-parameter-recovery.md) — source-backed distinct algorithm | source-backed documentary claim; no transfer |
| `package.json` | metadata | `experiment-registry.md` — explicit documentation gap; package metadata only | inventory metadata only |

## Package-page to source reverse index

Each package page is listed once here with the pinned source path and stable symbol/line anchor that
owns its algorithm. The file inventory above supplies the reverse source-to-page direction.

| Package page | Boundary | Pinned source path and anchor |
| --- | --- | --- |
| [plugins/control-flow-flattening.md](plugins/control-flow-flattening.md) | plugin composition | `ControlFlowFlattening/cff.js` and `controlFlowFlattening.js` — source-inspection-only driver and emission boundary |
| [control-flow-flattening-state-dispatch-recovery.md](transforms/control-flow-flattening-state-dispatch-recovery.md) | source-backed CFF transform | `ControlFlowFlattening/cff.js#detect,makeEval,makeFolder,deobfuscate,simulate,tryStructure,emitFunction,cleanup@32-1363` |
| [plugins/string-concealing.md](plugins/string-concealing.md) | plugin composition | `StringConcealing/stringConcealing.js` — source-inspection-only getter, decoder, cleanup, and CLI boundary |
| [string-concealing-static-getter-recovery.md](transforms/string-concealing-static-getter-recovery.md) | source-backed String Concealing transform | `StringConcealing/stringConcealing.js#base91Decode,constIndex,extractTable,extractArray,analyzeGetter,cleanupSweep,deobfuscate@49-252` |
| [plugins/vm-2.md](plugins/vm-2.md) | plugin composition | `VM-2/vm.js` — pipeline comments and Deobfuscator.run; `VM-2/README.md` — provenance only |
| [outer-recognition-evaluation.md](transforms/outer-recognition-evaluation.md) | O1 | `VM-2/vm.js#pathOf,asDispatcher,findSumName,buildHelpers,Env,ev@79-94,139-232,250-282,405-538` |
| [outer-trampoline-specialization.md](transforms/outer-trampoline-specialization.md) | O4 | `VM-2/vm.js#specialise,asTrampolineFactory,callTarget,resolveCall,trySpecialiseTrampoline@856-999,1601-1645` |
| [outer-state-cfg-recovery.md](transforms/outer-state-cfg-recovery.md) | O2 | `VM-2/vm.js#run,pass,caseFor,execStatements,applyStateWrites,learnBindings,rewrite@747-852,1003-1290,1515-1645` |
| [outer-cfg-structuring.md](transforms/outer-cfg-structuring.md) | O3 | `VM-2/vm.js#structure,emitSeq,emitTerm,loopOf,computeDominators,dominates,collectLoopBody,computePostDominators@1302-1511,2390-2477` |
| [outer-static-string-recovery.md](transforms/outer-static-string-recovery.md) | O5 | `VM-2/vm.js#buildStaticDecoders,inlineConcealedStrings@1668-1957` |
| [outer-observed-string-recovery.md](transforms/outer-observed-string-recovery.md) | O6 | `VM-2/vm.js#inlineConcealedStrings,evaluate,makeSandbox,unwrapRecorders@1726-1957,2263-2359` |
| [outer-cleanup.md](transforms/outer-cleanup.md) | O7 | `VM-2/vm.js#postProcess,simplifyThisGuards,aliasScopePaths@1960-2257` |
| [vm-container-extraction.md](transforms/vm-container-extraction.md) | I1 | `VM-2/devirt.js#extractMachine,decodeWords@60-134` |
| [handler-classification.md](transforms/handler-classification.md) | I2 | `VM-2/devirt.js#makeConstantReader,shapeOf,TEMPLATES,classify,buildOpcodeTable@136-491` |
| [wordcode-disassembly.md](transforms/wordcode-disassembly.md) | I3 | `VM-2/devirt.js#SPREAD_MARK,VARIADIC,bind,disassemble@498-642` |
| [state-aware-lifting.md](transforms/state-aware-lifting.md) | I4 | `VM-2/devirt.js#stateRegisters,liftFunction,joinValue,joinInto,analyseFunction@678-996` |
| [local-ssa.md](transforms/local-ssa.md) | I5 | `VM-2/devirt.js#localSSA@1010-1140` |
| [inner-control-structuring.md](transforms/inner-control-structuring.md) | I6 | `VM-2/devirt.js#succOf,structure,dispatchLoop,dominators,meet,dominates,postDominators@1153-1435` |
| [inner-cleanup.md](transforms/inner-cleanup.md) | I7 | `VM-2/devirt.js#cleanup,declareRegisters,foldMethodCalls,copyPropagate,inlineTemporaries,dropUnreachable,normaliseLoops,dropUnusedResults,mergeDeclarations,dropDeadStores@1472-1888` |
| [validation-fallback.md](transforms/validation-fallback.md) | V1 | `VM-2/vm.js#deobfuscateSource,removeVirtualMachine,runTrace@2483-2577`; `VM-2/test.js#behavior equivalence,keep VM,independent sample,passthrough/edge cases@269-282,356-509` |
| [plugins/vm-3.md](plugins/vm-3.md) | plugin composition | `VM-3/vm.js` — driver pipeline and six source-inspection-only boundaries |
| [vm-3-structural-vm-detection.md](transforms/vm-3-structural-vm-detection.md) | VM-3 structural detection | `VM-3/vm.js#detectVM,extractPayload,literalValue,makeDecoder@76-493` |
| [vm-3-handler-canonicalization.md](transforms/vm-3-handler-canonicalization.md) | VM-3 handler canonicalization | `VM-3/vm.js#canonicalize,specFor,identifyMBA,buildOpcodeMap@515-989` |
| [vm-3-payload-disassembly.md](transforms/vm-3-payload-disassembly.md) | VM-3 payload disassembly | `VM-3/vm.js#disassemble,decodeAt,successorsOf@992-1187` |
| [vm-3-state-specialized-lifting.md](transforms/vm-3-state-specialized-lifting.md) | VM-3 state specialization/lifting | `VM-3/vm.js#createLifter,buildGraph,liftInner,emit,controlRegisters,specializeFunction,runSpecialize@1867-2698` |
| [vm-3-reloop-cleanup-emission.md](transforms/vm-3-reloop-cleanup-emission.md) | VM-3 graph structuring/cleanup | `VM-3/vm.js#Block,reloop,renderShape,pruneLabels,combineExpressions,peephole,dropDeadRegisters,renameRegisters,simplifyMBA,collapseDispatch,tidyStatements,cleanupProgram@1202-3299` |
| [vm-3-fallback-validation.md](transforms/vm-3-fallback-validation.md) | VM-3 fallback boundary | `VM-3/vm.js#deobfuscateSource,topLevelIsPlain@3344-3413` |
| [plugins/vm-1.md](plugins/vm-1.md) | plugin composition | `VM-1/vm.js` and `VM-1/emit-*.js` — driver pipeline and six source-inspection-only boundaries |
| [vm-1-structural-bytecode-extraction.md](transforms/vm-1-structural-bytecode-extraction.md) | VM-1 extraction | `VM-1/vm.js#extractVM,evalConstNode@94-149`; `VM-1/disasm.js#extract,evalNode@14-71` |
| [vm-1-fixed-opcode-disassembly.md](transforms/vm-1-fixed-opcode-disassembly.md) | VM-1 fixed decoding | `VM-1/vm.js#OP,BINOP,UNOP,VOID_OP,SPREAD_SENTINEL,decodeConst,disassemble,decodeInstr,readArgs@35-272`; `VM-1/disasm.js#decodeConst,decode@74-252` |
| [vm-1-static-function-cfg.md](transforms/vm-1-static-function-cfg.md) | VM-1 function/CFG discovery | `VM-1/vm.js#discoverFunctions,collectBody,successors,buildBlocks@278-400` |
| [vm-1-reducible-register-structuring.md](transforms/vm-1-reducible-register-structuring.md) | VM-1 reducible structuring | `VM-1/emit-structured.js#buildModel,computeLiveness,emitSeq,emitTryRegion,emitLoop,emitTerminator,foldBlock,irForInstr@86-537` |
| [vm-1-dual-emission.md](transforms/vm-1-dual-emission.md) | VM-1 structured/explicit-PC emission | `VM-1/emit-structured.js#emitProgram,beautify@28-80,669-693`; `VM-1/emit-dispatcher.js#emitProgram,emitFunc,emitBlock,lowerSideEffect,lowerControl@28-251` |
| [vm-1-fallback-validation.md](transforms/vm-1-fallback-validation.md) | VM-1 fallback boundary | `VM-1/vm.js#deobfuscateSource,deobfuscateFile@434-474` |
| [plugins/vm-4.md](plugins/vm-4.md) | VM-4 plugin composition | `VM-4/vm.js` — driver pipeline, static handler observation, fit, path recovery, and bounded fallbacks |
| [vm-4-static-handler-recovery.md](transforms/vm-4-static-handler-recovery.md) | VM-4 static handler observation and frame-aware operation recovery | `VM-4/vm.js#locateVM,runHandler,probeStructure,classify,fitInstr,disassemble,explorePaths,liftInstr,generateBody,deobfuscateSource@56-3559` |
| [plugins/vm-5.md](plugins/vm-5.md) | VM-5 plugin composition | `VM-5/vm.js` — driver pipeline, live capture, probing, fit, and bounded fallbacks |
| [vm-5-live-handler-fit-recovery.md](transforms/vm-5-live-handler-fit-recovery.md) | VM-5 live handler capture, probing, and frame-aware fit recovery | `VM-5/vm.js#findBootstrap,captureVM,makeMock,probeRoles,discoverFrameLayout,fitDataOpcodeInner,exploreFunction,liftInstruction,deobfuscate@39-3289` |
| [plugins/vm-6.md](plugins/vm-6.md) | VM-6 plugin composition | `VM-6/vm.js` — driver pipeline, site fitting, state cloning, audit, and fallback |
| [vm-6-site-salted-handler-fitting.md](transforms/vm-6-site-salted-handler-fitting.md) | VM-6 site-salted handler fitting and hash-dispatch recovery | `VM-6/vm.js#findBootstrap,loadVM,probeLayout,structuralKind,fitSite,decodeAt,exploreAll,liftFunction,auditRecovery,run@36-2215` |
| [plugins/vm-7.md](plugins/vm-7.md) | VM-7 plugin composition | `VM-7/vm.js` and `VM-7/lib/*` — admission, behavioral model, abstract-state analysis, lifting, and fallback |
| [vm-7-behavioral-abstract-state-lifting.md](transforms/vm-7-behavioral-abstract-state-lifting.md) | VM-7 behavioral abstract-state lifting | `VM-7/lib/machine.js,fit.js,analyze.js,lift.js,structure.js,emit.js,polish.js; VM-7/vm.js` |
| [plugins/vm-8.md](plugins/vm-8.md) | VM-8 plugin composition | `VM-8/vm.js` and `VM-8/lib-*` — extraction, probing, site classification, partial evaluation, and fallback |
| [vm-8-oracle-classification-partial-evaluation.md](transforms/vm-8-oracle-classification-partial-evaluation.md) | VM-8 oracle classification and partial evaluation | `VM-8/lib-extract.js,lib-probe.js,lib-disasm.js,lib-classify.js,lib-analyze.js,lib-peval.js,lib-emit.js,lib-codegen.js,lib-polish.js; VM-8/vm.js` |
| [plugins/vm-glm-1.md](plugins/vm-glm-1.md) | VM-GLM-1 plugin composition; explicit variation of VM-3 | `VM-GLM-1/vm.js#extractVM,analyze,prepareFn,buildFunction,deobfuscateSource@39-198,1317-1990,2150-2593,2623-3313` |
| [vm-glm-1-handler-effects-variation.md](transforms/vm-glm-1-handler-effects-variation.md) | VM-GLM-1 symbolic handler effects, archetypes and path-sensitive dispatcher dissolution | `VM-GLM-1/vm.js#interpretHandler,matchArchetype,classifyHandlers,liftProgram@246-1306,2117-2141` |
| [plugins/vm-gpt-1.md](plugins/vm-gpt-1.md) | VM-GPT-1 plugin composition and sandbox/trace admission boundary | `VM-GPT-1/vm.js,vm-core.js,lifter.js` — driver and delegated helper composition |
| [vm-gpt-1-trace-guided-recovery.md](transforms/vm-gpt-1-trace-guided-recovery.md) | VM-GPT-1 trace-guided recovery and observed CFG lifting | `VM-GPT-1/vm-core.js#collectDecodedConstants,findDecodeFunction@218-324`; `VM-GPT-1/lifter.js#lift,traceProgram,classify,lower,findFlattening,branchCondition,buildLiftedFunction,compileRoot@9-15,33-140,177-224,271-421,425-469,478-656,661-677` |
| [plugins/vm-kimi-1.md](plugins/vm-kimi-1.md) | VM-Kimi-1 plugin composition and fixed-layout admission boundary | `VM-Kimi-1/vm.js#extractFromAst,decodeAll,explore,unflatten,deobfuscate@70-266,387-824,1423-1508` |
| [vm-kimi-1-static-decrypt-dispatch.md](transforms/vm-kimi-1-static-decrypt-dispatch.md) | VM-Kimi-1 static decrypt and hashed state/accumulator dispatch | `VM-Kimi-1/vm.js#applyStaticDecrypts,runDispatcher,explore,detectFlow,stateUpdate,unflatten@210-824` |
| [plugins/dispatcher.md](plugins/dispatcher.md) | Dispatcher plugin composition | `Dispatcher/dispatcher.js#transformAst,transformOne,deobfuscate@535-637` |
| [dispatcher-call-recovery.md](transforms/dispatcher-call-recovery.md) | Dispatcher bounded table extraction and call recovery | `Dispatcher/dispatcher.js#firstDispatcherTable,learnDispatcherShape,extractFunctions,replaceDispatcherCalls@58-470` |
| [plugins/flatten.md](plugins/flatten.md) | Flatten plugin composition | `Flatten/flatten.js#collectHandlers,inlineHandler,deobfuscate@337-423` |
| [flatten-context-inlining.md](transforms/flatten-context-inlining.md) | Flatten context-wrapper inlining | `Flatten/flatten.js#buildContextMap,getHandlerInfo,getWrapperInfo,inlineHandler@7-308` |
| [plugins/shuffle-claude.md](plugins/shuffle-claude.md) | Shuffle-Claude plugin composition | `Shuffle-Claude/Shuffle-Claude.js#deobfuscate,isShuffleFunction,evaluateShuffle@34-215` |
| [shuffle-claude-static-primitive-rotation.md](transforms/shuffle-claude-static-primitive-rotation.md) | Shuffle-Claude static primitive rotation | `Shuffle-Claude/Shuffle-Claude.js#isShuffleFunction,evaluateShuffle,extractLiteral,deobfuscate@34-215` |
| [plugins/shuffle-gpt-5-5.md](plugins/shuffle-gpt-5-5.md) | Shuffle-GPT-5.5 plugin composition | `Shuffle-GPT-5.5/Shuffle-GPT-5.5.js#deobfuscateShuffle,matchShuffleFunction@7-284` |
| [shuffle-gpt-5-5-ast-subtree-rotation.md](transforms/shuffle-gpt-5-5-ast-subtree-rotation.md) | Shuffle-GPT-5.5 binding-aware AST subtree rotation | `Shuffle-GPT-5.5/Shuffle-GPT-5.5.js#matchShuffleFunction,rotateLeft,deobfuscateShuffle@118-255` |
| [plugins/string-compression-gpt-5-5.md](plugins/string-compression-gpt-5-5.md) | StringCompression-GPT-5.5 plugin composition | `StringCompression-GPT-5.5/StringCompression-GPT-5.5.js#transform,decodeTable@178-347` |
| [string-compression-gpt-5-5-lz-table-recovery.md](transforms/string-compression-gpt-5-5-lz-table-recovery.md) | StringCompression-GPT-5.5 LZ table recovery | `StringCompression-GPT-5.5/StringCompression-GPT-5.5.js#findLzStringHelper,analyzeDecoderIife,decodeTable,replaceLookupCalls@60-235` |
| [plugins/variable-masking.md](plugins/variable-masking.md) | VariableMasking plugin composition | `VariableMasking/variableMasking.js#transformVariableMaskedFunction,deobfuscateSource@160-304` |
| [variable-masking-rest-parameter-recovery.md](transforms/variable-masking-rest-parameter-recovery.md) | VariableMasking rest-parameter recovery | `VariableMasking/variableMasking.js#memberInfo,collectIndexUses,findLocalIndexSlots,transformVariableMaskedFunction@16-267` |

## Selected related sources

These declared sources are used for producer comparison or explicit residue boundaries. They are
not additional corpus-path rows and do not widen the VM-2 evidence boundary.

| Related source path | Package use | Boundary |
| --- | --- | --- |
| `ControlFlowFlattening/cff.js` | [CFF transform](transforms/control-flow-flattening-state-dispatch-recovery.md), [O1](transforms/outer-recognition-evaluation.md), [O2](transforms/outer-state-cfg-recovery.md), [O3](transforms/outer-cfg-structuring.md) | Own sample transform; related O1/O2/O3 CFF-shape comparison only |
| `StringConcealing/stringConcealing.js` | [String Concealing transform](transforms/string-concealing-static-getter-recovery.md), [O5](transforms/outer-static-string-recovery.md) | Own sample transform; related O5 string-shape comparison only |
| `encoder/js-confuser/src/order.ts` | [plugins/vm-2.md](plugins/vm-2.md) | outer producer ordering context only |
| `encoder/js-confuser/src/transforms/controlFlowFlattening.ts` | [O2](transforms/outer-state-cfg-recovery.md), [O3](transforms/outer-cfg-structuring.md) | related outer producer divergence only |
| `encoder/js-confuser/src/transforms/string/stringConcealing.ts` | [O5](transforms/outer-static-string-recovery.md) | related outer producer divergence only |
| `encoder/js-confuser-vm/src/compiler.ts` | [plugins/vm-2.md](plugins/vm-2.md), [I3](transforms/wordcode-disassembly.md) | serializer/order and hardening residue boundary |
| `encoder/js-confuser-vm/src/transforms/bytecode/controlFlowFlattening.ts` | [O3](transforms/outer-cfg-structuring.md) | VM producer control encoding; not an accepted decoder transform |
| `encoder/js-confuser-vm/src/transforms/bytecode/resolveRegisters.ts` | [I3](transforms/wordcode-disassembly.md) | encoded/register residue axis |
| `encoder/js-confuser-vm/src/transforms/bytecode/resolveLabels.ts` | [I3](transforms/wordcode-disassembly.md) | label/PC residue axis |
| `encoder/js-confuser-vm/src/transforms/bytecode/resolveConstants.ts` | [I1](transforms/vm-container-extraction.md), [I3](transforms/wordcode-disassembly.md) | constant operand residue axis |
| `encoder/js-confuser-vm/src/transforms/bytecode/stringConcealing.ts` | [O5](transforms/outer-static-string-recovery.md) | distinct VM bytecode string-bank axis |
| `encoder/js-confuser-vm/src/transforms/bytecode/specializedOpcodes.ts` | [I2](transforms/handler-classification.md), [I3](transforms/wordcode-disassembly.md) | synthetic opcode axis; deferred |
| `encoder/js-confuser-vm/src/transforms/bytecode/macroOpcodes.ts` | [I2](transforms/handler-classification.md), [I3](transforms/wordcode-disassembly.md) | macro opcode axis; deferred |
| `encoder/js-confuser-vm/src/transforms/bytecode/aliasedOpcodes.ts` | [I2](transforms/handler-classification.md), [I3](transforms/wordcode-disassembly.md) | aliased opcode axis; explicit unsupported near-neighbor |
| `encoder/js-confuser-vm/src/transforms/bytecode/antiInstrumentation.ts` | [plugins/vm-2.md](plugins/vm-2.md) | optional hardening residue; deferred |
| `encoder/js-confuser-vm/src/transforms/bytecode/selfModifying.ts` | [plugins/vm-2.md](plugins/vm-2.md), [I3](transforms/wordcode-disassembly.md) | PATCH/self-modifying residue; deferred |
| `encoder/js-confuser-vm/src/transforms/bytecode/encryptPatches.ts` | [plugins/vm-2.md](plugins/vm-2.md), [I3](transforms/wordcode-disassembly.md) | encrypted patch residue; deferred |
| `encoder/js-confuser-vm/src/transforms/runtime/handlerTable.ts` | [I2](transforms/handler-classification.md) | related runtime registration shape only |
| `encoder/js-confuser-vm/src/transforms/runtime/shuffleOpcodes.ts` | [plugins/vm-2.md](plugins/vm-2.md), [I3](transforms/wordcode-disassembly.md) | opcode permutation residue; deferred |

## Coverage boundary

The inventory is the complete pinned corpus coverage claim. Algorithm-bearing VM-1 through
VM-8 rows are source-backed documentation; notes, README files, fixtures, generated output, debug
material and diagnostics remain evidence-only. The exact-example and pass-through evidence is owned
by V1; no row promotes an exact sample to unseen transfer or production support. VM-1 through VM-8
source-inspection-only pages do not widen the accepted empirical slice.
