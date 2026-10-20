# Cross-decoder study — bounded JS-Confuser comparison

This is the parent-level comparison of the pinned [read-only decoder corpus](../decoder/claude-vs-js-confuser/)
and the editable [`decode-js` engine](../decoder/decode-js/). It is the only durable home for
capability comparisons, algorithm-transfer or adoption lineage, benchmark conclusions and
readability conclusions involving both projects. Each project's own package remains readable and
valid without this file or the other decoder.

## Purpose and scope

The study answers a bounded question: which observations from the corpus are supported by
same-configuration transfer evidence, which mechanisms the current decoder already handles, and
which external ideas should be adopted, rejected or deferred? It does not turn the corpus README's
success table into coverage, and it does not infer support for an experiment directory that has no
qualified transfer observation.

The accepted comparison slice is:

- String Concealing under the recorded `SC-213` profile;
- Control Flow Flattening under the shape-qualified `CFF-213` population; and
- VM-2 under the recorded hardened `VM2-213` profile, including the aliased-opcode neighbor.

The exact encoder identities and option objects are in the
[experiment registry](claude-vs-js-confuser/experiment-registry.md). This study owns the
qualification and comparison claims. Any new comparison needs retained encoded bytes, their
provenance and a same-input observation from both decoders.

## Evidence boundary

The corpus's exact-example result, a generated positive candidate, a qualified same-configuration
transfer result, a version-drift observation, a negative control and a safe decline are different
claims. An exact success proves only the retained sample. A transfer candidate becomes comparison
evidence only when its encoder provenance and mechanism-specific population are complete. A safe
decline is byte-identical pass-through; behavior-equivalent output that changes bytes remains a
non-comparable canonicalization.

The current VM target supports the numeric, unhardened contract. The registered `VM2-213`
profile is hardened and outside that contract, so its byte-preserving decline is a boundary
observation rather than evidence of a mechanism deficit. The independent layer-pair recipe is
frozen in the [layer-pair contract](vm2-layer-pair-contract.json).

## Capability comparison

| Mechanism | Corpus evidence | Current `decode-js` boundary | Parent-level disposition |
| --- | --- | --- | --- |
| String Concealing | The supplied exact candidate succeeds, but the unchanged corpus script has no qualified unseen transfer result. The accepted comparison cells use the registered `SC-213` profile. | The binding-aware String Concealing visitor succeeds on the accepted same-configuration observations, removes the mechanism residue and preserves bounded behavior. The supplied exact candidate and ordinary negative retain their separate provenance/decline limits. | Retain the source-derived getter/table/decoder binding observation as corroboration of the existing visitor. Add no second algorithm, name table or sample-specific cleanup. |
| Control Flow Flattening | The supplied exact candidate succeeds, but the unchanged corpus script has no qualified unseen transfer result. Qualification requires the repeated state callable, nested switch, case population and break evidence; generic switch/loop text is excluded. | The graph visitor succeeds on the accepted control and closure observations. The switch/while boundary remains ordinary code rather than a flattened shape. Version drift and exact-only flattened shapes remain bounded evidence. | Retain the binding-resolved dispatcher/CFG deductions. No new CFF unit is selected by this gate; that is sequencing only, not a rejection of the documented CFF knowledge. |
| VM-2 | The supplied exact candidate succeeds, but no independently generated VM-2 cell qualifies as unseen transfer evidence. The aliased-opcode row is an explicit unsupported neighbor. | The paired `VM2-213` bytes are hardened and outside the current numeric/unhardened decoder contract; the VM pipeline declines atomically at `container-declined`, preserving exact input bytes. This is not a VM recovery result or a mechanism-deficit observation. | Keep handler and dependency observations as unqualified qualification candidates. Require empirical transfer qualification before adoption or rejection; infer no decoder deficit from the out-of-contract decline. |
| Other corpus experiments | The remaining experiment directories are inventoried and preserved as source-inspection-only plugin/transform documentation, but have no qualified transfer observation in the accepted slice. | No current-decoder comparison is claimed for them. | Do not promote their scripts, README outcomes or model-specific scaffolding into decoder coverage. |

The comparison is intentionally asymmetric where the evidence is asymmetric: a current decoder
success on a matching generated transfer cell is useful coverage evidence even when the corpus
script did not transfer, while an external exact success is not a decoder failure when the current
decoder declines an unqualified, mismatched, or hardened shape. A decline outside the decoder's
configuration contract cannot be used to rank or reject the encoder's mechanism.

## Adoption and rejection ledger

| Observation | Decision | Technical reason |
| --- | --- | --- |
| SC recognizes a live wrapper/table/decoder relationship and resolves constant call sites | Retain as confirmation of the existing `decode-js` design | The same binding-level contract survives helper renaming and is already supported on the accepted transfer population; copying the corpus pass would add no demonstrated capability. |
| CFF evaluates literal state, simulates a complete transition graph and structures reachable blocks | Retain as compatible prior art; do not add a pass | The current graph visitor already owns this dependency and the qualified transfer cells expose no new shape gap. Generic switch/loop matching would be unsafe. |
| VM-2 canonicalizes handler shapes and lifts a concrete machine on its exact sample | Keep as unqualified qualification candidate | The exact sample is not transfer evidence, but the current hardened decline is also not a negative result: it is outside the decoder's visible/unhardened contract. |
| Corpus-local names, state arrays, opcode numbers, expected bytecode, prompt scaffolding and pass order | Reject as implementation inputs | They are sample or experiment artifacts, not shape keys or decoder ownership boundaries. |

No corpus script is copied wholesale. A future implementation may re-derive a mechanism only in the
target-local visitor that owns that reversal, after a new measured deficit and a fresh architecture
gate. Neither decoder package may record the comparison or import the other project's code.

## Readability and behavior conclusion

“Same readability” means comparable recovered semantic operations and structure, no greater
mechanism residue, preserved bounded behavior and a source-oriented output. It does not require
destroyed identifiers, comments or original formatting to be guessed. A byte reduction by itself
is not a readability result, and a behavior-equivalent rewrite of a negative is not a safe decline.

| Comparison slice | Readability conclusion |
| --- | --- |
| SC same-configuration transfer | Comparable or better on the accepted cells: the existing decoder removes the concealed string machinery, preserves the observed operations and matches the bounded behavior oracle. No sample constant is required by the matcher. |
| CFF same-configuration transfer | Comparable on the accepted flattened control/closure cells. The switch/while rows are ordinary code; their residual text does not justify a new decoder algorithm. |
| VM-2 transfer | No readability comparison is claimed. The atomic byte-preserving decline is an expected out-of-contract boundary, not a partial decode and not evidence against the corpus mechanism. |
| Exact examples and negatives | Exact successes remain positive controls with their provenance limits. Conventional byte-changing negatives are non-comparable; VM negatives and the aliased neighbor demonstrate the byte-preserving decline boundary. |

The accepted evidence therefore supports only the bounded claims attached to matching conventional
transfer cells, not a universal claim across every corpus mechanism. The remaining pages and VM
boundaries stay available for qualification; no implementation work is approved from a missing
transfer cell or an out-of-contract decoder decline.

## Layer-paired VM recovery track

The VM-2 quality phase is a separate decoder-owned comparison track for two independent encoders.
Its selected composition is:

    source -> JS-Confuser-VM 0.1.5 -> VM-only source -> JS-Confuser 2.1.3 -> composed source
                                                                          |
                                                        unchanged jsconfuser decoder
                                                                          |
                                                               fresh parse -> VM recovery

The outer decoder receives source text from the unchanged `jsconfuser` target. The VM decoder then
receives a freshly parsed source string; no AST bindings or synthetic VM container cross the stage
boundary. Retain each run's VM-only bytes as the reference for judging its recovered outer
intermediate, and compare the direct VM result with the post-outer VM result. The first control is the
numeric/unhardened arithmetic cell and exact options, revisions, seeds and limits are frozen in the
[layer-pair contract](vm2-layer-pair-contract.json). This contract is an execution specification;
transfer evidence requires retained bytes and the specified comparisons.

The decoder-owned [exact-inner transform](decode-js/transforms/jsconfuser-vm/exact-inner-recovery.md)
records the future source-derived mechanism and fail-closed boundary. The supported runtime
scope is [ordinary Node/browser execution](vm2-layer-pair-architecture.md#supported-runtime-scope).
The machine root, producer, call/return, completion and
source-emission proofs remain open. Compare actual recovered source with a retained reference output only
after those gates close; the corpus output supplies neither semantics nor replacement source.

Layer-pair qualification must use the pinned public builds in fresh workers, retain every attempt and verify actual CFF and
String Concealing populations. A direct VM success plus a post-outer failure localizes a handoff or
inner-recognition discrepancy; two inner declines do not establish an outer failure. The arithmetic
oracle expects one `window.TEST_OUTPUT` write of `7` in a bounded fresh context. Outer helper
execution through the existing plugin remains stage-scoped; VM recovery remains static. The
coordinator and final-output rollback contract require an accepted unchanged-outer comparison.
`VM2-213` generation or execution remains gated on exact VM-2 acceptance.

## Reopening and capability-expansion rule

An existing-contract mechanism fix can reopen only after a new, reproducible, non-original
same-configuration positive reaches the relevant matcher and exposes a live deficit under that
decoder's actual configuration contract. An out-of-contract or mismatched-profile decline is not a
live deficit. The evidence must include the exact control, at least two unseen positives, a targeted
near-miss negative, the relevant version or hardening neighbor, a complete shape key, an all-or-
nothing mutation contract, fresh-parse and behavior checks, and a readability census. A new
architect decision is required before any decoder write scope is opened.

An explicitly authorized capability expansion may open a new shape or configuration boundary
without first satisfying the existing-contract deficit test. It still requires a declared
source-backed representation and ownership contract, decoder-owned fixtures, fail-closed negatives,
independently reviewed evidence and an explicit boundary on claims about transfer and production
support. The layer-paired VM recovery track is such an expansion; it does not relabel the prior
safe decline of the hardened `VM2-213` profile as a regression. Neither rule permits a prior exact
example or a corpus-local name/constant to stand in for new evidence.

## Sources

- [Pinned corpus project](../decoder/claude-vs-js-confuser/) — read-only experiment source at the accepted revision.
- [Corpus algorithm package](claude-vs-js-confuser/claude-vs-js-confuser.md) — source citations, boundaries and registry for the pinned experiments.
- [Corpus experiment registry](claude-vs-js-confuser/experiment-registry.md) — configurations, entry points and controls for every experiment.
- [Editable `decode-js` project](../decoder/decode-js/) — the implementation and test target.
- [Layer-pair contract](vm2-layer-pair-contract.json) — the frozen first control, producer pins,
  options, seed schedule and stage limits for the independent VM recovery track.
- [`decode-js` plugin reference](decode-js/plugins/jsconfuser.md) — current conventional pipeline ownership and ordering.
- [`decode-js` VM plugin reference](decode-js/plugins/jsconfuser-vm.md) — current VM container and standalone boundaries.

## Reproducibility

The accepted comparison is bounded by the registered encoder profiles and the retained exact
examples. For a new paired observation, record the source, encoder revision, options, generated
bytes and mechanism population. Pass the same encoded bytes to both decoder entry points, then
record parse and bounded behavior results, recovered structure and operations, and exact-byte
decline where claimed. Retain the bytes with their provenance before treating the observation as
evidence. Outputs from different randomized encodes cannot form a paired comparison.

A controlled replacement for `Math.random()` is harness control, not public encoder seed support.
Repeat a seed and include native-random attempts to expose population variance. The ordinary SC
control may change formatting and therefore cannot be called a byte-preserving decline. CFF and
VM safe-decline claims require exact input and output bytes. The hardened `VM2-213` profile
remains outside the current numeric VM contract.

| Recipe or source | Claim it supports |
| --- | --- |
| [Layer-pair contract](vm2-layer-pair-contract.json) | Producer and stage configuration; it does not claim generated evidence. |
| Pinned corpus submodule | Supplied exact examples, source notes, regular controls and experiment entry points. |
| [`decode-js` plugin tests](../decoder/decode-js/test/) | Decoder-owned fixed regressions for the conventional and VM pipelines. |

New encodes or decoder revisions require separately retained evidence before changing these
bounded comparison claims.
