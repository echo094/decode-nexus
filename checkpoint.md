# Checkpoint — qualify general jsconfuser-vm decoding

The objective is a reusable two-step decoder for valid outputs of the pinned
`js-confuser-vm` encoder. An independent VM-2 benchmark follows general encoder
qualification; it cannot define matcher rules or establish general coverage.

## Resume here

- **Current state:** The numeric frontend, typed switch model, shared source backend, step-one review script, and co-located VM tests are implemented. The transform docs reflect the current module layout. A future independent benchmark will retain its fixture beside its test.
- **Next action:** Audit fresh outputs of the pinned encoder across source features, representation-changing options, and seeds; record accepted, declined, and untested shapes. Establish a maintained generator because the old corpus generator is absent.
- **Why next:** The fixed numeric corpus cannot establish general coverage. The shape audit identifies the first real decoder gap.

## Definition of done

- Fresh generated encoder qualification covers source features, representation-changing options, and seeds. Accepted, declined, and untested shapes are recorded with an executable generator.
- Valid-output gaps are closed by source-derived dependency order. Step one preserves admitted input behavior; step two structures and simplifies only proved facts; atomic decline is retained.
- The independent VM-2 benchmark is evaluated after the general frontend is qualified.

## Constraints and decisions

- No new tasks or subagents. Keep unrelated root `check-git-email.sh`, decoder `fireyejs.js`, `.DS_Store`, and the user's unstaged punctuation edit in [the switch boundary](skills/decode-js/vm-switch-boundary.md) out of commits.
- Ordinary Node/browser execution with standard built-ins is the supported runtime scope. Historical host-state reconstruction is unnecessary. The [switch boundary](skills/decode-js/vm-switch-boundary.md) and [benchmark architecture](skills/vm2-layer-pair-architecture.md) own the durable design.
- The removed exact-inner audit had no public decoder import. Its historical refusal and frozen trial files no longer form an active acceptance gate. Generate a fresh, provenance-backed VM-2 benchmark fixture alongside its future test.
- Name test files and folders by behavior, not by task ID or attempt number; [doc conventions](skills/doc-conventions.md) own this rule.

## Plan

1. Audit encoder source features and emitted option/seed shapes against generated cases. The old corpus generator is absent, so establish a maintained generator for fresh qualification. This identifies valid outputs the decoder still declines.
2. Close generated valid-output gaps by source-derived dependency order; check step-one execution, step-two behavior, residue and atomic rollback.
3. Generate and retain an independent VM-2 benchmark with its decoder test, then evaluate output quality and runtime after a source-derived frontend is implemented.

## Validation

- On 2026-09-27, `npx vitest run --coverage.enabled=false` passed 84 files, 630 tests, and one existing todo after the VM module refactor. Focused ESLint on `src/vm` passed. The moved top-level declarations were compared against the original source and were unchanged. A local-link scan found no missing real links in changed docs.
- Fresh generated encoder qualification remains open; the current suite is a bounded regression set.

## Repository state

- Hub branch: `docs/js-confuser-vm-study-plan`. Editable decoder branch: `codex/jsconfuser-vm-two-step-decoder`. Their housekeeping history was rebuilt locally with sign-off; no push. Encoder and read-only decoder corpus pins remain fixed.
- The decoder keeps only local `main`, `awsc`, and the current branch. Remote branches were not changed. The unrelated untracked files and user's punctuation edit remain outside commits.

## Open questions

- Which valid shapes and option combinations emitted by the pinned encoder are untested or currently declined?
- What source relationships identify independently generated VM-2 machines and their operations without fixture-specific constants?

## Assets

- The read-only corpus keeps [VM-2 input and references](decoder/claude-vs-js-confuser/VM-2/) as prior art; it is not the future benchmark fixture.
- [Current test layout](skills/decode-js/tests.md), [VM stage dependency map](skills/decode-js/plugins/jsconfuser-vm.md#decoder-stage-dependency-map), and [encoder options](skills/js-confuser-vm/options.md) support the next coverage audit.

## Decisions not to re-make

- A benchmark reference output is a readability target, never decoder input or a recognition rule.
- A finite successful corpus or the single VM-2 benchmark cannot establish support for every encoder output.
- Rendered switch JavaScript is a review artifact; the typed model carries semantics into step two.
