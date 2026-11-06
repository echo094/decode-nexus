# Checkpoint — troubleshoot VM decoder capability gaps

Recover JavaScript where the VM decoder declines; preserve baselines. No delegation.

## Resume here

- Current state (2026-11-06): the export-name review and the unreachable-code drop are committed into both rebuilt
  histories (Validation "Rebuild 2"); unpushed, and the pushed branches need a force-push. Plan 9's vm2-layered/
  outputs predate the drop (their decoded.js still hold `if (false)` blocks); behaviour is unchanged.
- Done (2026-11-06): the vm-switch docs restructured (statements and emit rewritten procedure-first with real
  worked examples at seed 1; boundary section 1 split into named rules, links retargeted; try-region and control
  fixes), squashed into the hub's backend and frontend doc commits; hub pre-squash head kept as
  backup/docs/js-confuser-vm-study-plan-2026-11-06c. Open, not approved: the emitter still reads region fields the
  planner never produces (vm-switch-emit "terminal additions"); standalone-decode's "remain open" control-boundary
  claim cites a list no doc holds.
- Done (2026-11-11): CI run 42289641186's two failures fixed and committed (Validation "Rebuild 3").
  1. all-stages-together/f-finally-abrupt dropped: the encoder's own output fails whenever controlFlowFlattening,
     dispatcher and macroOpcodes are all on (probe and weyl.mjs under troubleshooting/encoder-broken/); tests.md
     states the drop rule; the signed-Weyl proof stands on the other 48 all-stages artifact cells.
  2. distinct-cells' "a stage changes the program" (one test over 418 stage cells, 94 s locally with coverage, over
     180 s on CI) split, by the user's choice, into stage-effect/<suite>.test.js, one per stage suite, plus a
     pairing check in distinct-cells; tests.md documents it.
- Next action: the user reviews vm2-layered/ (regenerate its decoded outputs first if the user wants the current
  rendering); then Plan 10, the supplied VM-2 bytes. CI confirms both fixes on the next push (force-push needs
  the user).
- Why next: the user's order (2026-11-06): the benchmark runs after the layered precondition is reviewed.

## Definition of done

- Prove cause; minimal encoder-generated reproducer; propose owners/options/P4 measures/tests;
  await approval.
- Recover JavaScript and remove VM residue; crash-to-refusal is intermediate. Preserve controls,
  exact refusals and AST/state consistency.

## Constraints and decisions

Test design (suites, categories, checks, open-decoder-gaps, brokenEncodedInput) is owned by
[tests.md](skills/decode-js/tests.md); the try, switch and conditional rules by
[vm-switch-statements.md](skills/decode-js/vm/switch/vm-switch-statements.md).

- User: direct work; read code before proposing; await approval. Design gaps/changes or unexpected
  results: stop, record options with a recommendation, ask. Pause and update this file after each
  procedure step. No unapproved commits; no push.
- Freeze baseline sources/options/seeds. Diagnostics, rechecks and minimal cells go under ignored
  sandbox-tests/decoder-capability-2026-10-12/troubleshooting/. Encoders/evidence read-only. No
  profile narrowing or weakened proofs for positive results.
- User: read pipeline code directly; replay explicit pass order; inspect the input.
- User: per issue, minimal reproducing config first, then fix; prefer revising an existing test;
  no man-made test of a shape no producer emits (F7). A test expecting a valid compiler form to
  decline marks a boundary: list it as a known gap, flip it when the gap closes.
- User (2026-11-06), VM-2 benchmark: precondition A, generated layered cells (pinned JS-Confuser over the VM output,
  VM-2's option profile, recorded seeds) decode through `jsconfuser-vm-sequential` to source behaviour before the
  supplied VM-2 bytes run. Keep every input and output under sandbox-tests for the user's review.
- User (2026-11-05): a fixed case moves to its natural suite, or to a chain of its stages when none holds them; an
  encoder-broken cell is dropped, not listed.
- User (2026-10-31): outside the pre-commit measure, one test batch runs at most 5 minutes and covers
  only what the change can affect and what matters to the decision.
- User (2026-10-29), generated fixtures: commit source, options, seed and pin only; encoded inputs regenerate from
  recipes into ignored paths; Node and JDK unpinned, majors in the cache key; CI artifact of src+encoded+config+decoded
  kept 90 days.
- User (2026-10-25), history: squash churn into the commit it corrects; no standalone refactor or fix survives;
  decode-js first, then the hub on the settled IDs.
- User (2026-10-24): corpus rows from encoder builds outside the pin are ignored: VM-1 (boot
  before 0.1.4) and VM-3..8 (unmerged upstream `mba` branch). VM-2 direct's decline is correct
  (outer JS-Confuser layer; direct mode runs no outer decoder, P3).
- User (2026-10-18): existing code that violates a revised rule is fixed, never accommodated.
- User (2026-10-19): the per-change measure set is vitest, fixture parity, the frozen recheck and
  the residue census (troubleshooting/measure.sh); the other censuses are retired.
- User (2026-10-15): delete a man-made test that loses its value through a design change.
- User (2026-10-30): the 13 stale qualification records stay as they are and retire with the rest.
- User (2026-10-17): identify added handlers statically first; isolated-vm only if a real handler
  stays ambiguous after behaviour matching and effects.
- Before building a probe, read its [hazards](skills/decode-js/probes.md#hazards--the-ways-a-probe-lies).

### Procedure per issue

1. **Baseline/owners.** Frozen artifacts, Git status, public entries, owner docs/tests.
2. **Reproduce.** Public child replay: 90-second deadline, full streams/exit, actual site.
3. **Trace producer.** Replay existing exports in actual order; locate the exact mutation or
   non-mutation. New instrumentation mechanisms need approval.
4. **Prove cause/reach.** Vary only the implicated operation with a reaching control; audit
   similar shapes; pause before fix design.
5. **Minimal encoder reproducer.** Encoder's own call; minimize source/options; record source,
   options, seed, encoder commit; confirm the unfixed decoder fails at the same site.
6. **Propose/wait.** Two/three remedies with a recommendation, owners, P4 measures, tests.
7. **Implement.** Regression red first; apply the approved change; measure output.
8. **Validate/report.** Focused and full suite; recheck the frozen 47 decodes; keep recoveries
   and exact refusals; update owner docs; commit only on approval.

## Plan

| Step | Issue | Owner | Cause | Reproducer | Procedure next |
|---|---|---|---|---|---|
| 9 | VM-2 precondition: layered VM2-213 cells (13 chain sources + VM-2 original.js, seeds 251-253) decode through `jsconfuser-vm-sequential` to source behaviour | sequential, outer, VM | - | vm2-layered/cells | user review |
| 10 | VM-2 benchmark: the supplied bytes, after 9 | - | - | - | - |

## Validation

- 9 layered (2026-11-06, vm2-layered/gen.mjs over sources.txt, seeds 251-253, run.jsonl): 42 of 42 encode in both
  stages and decode `success` through `jsconfuser-vm-sequential` (3-4 s each). The 39 chain-source cells equal source
  behaviour at every stage (VM, layered, outer-decoded, decoded). VM-2's original.js (3 cells): decoded equals source
  (ReferenceError `document`); the VM output and every stage before the VM decode throw TypeError reading
  `createElement`, because the VM runtime sets `globals.document = undefined` when the host has `window` but no
  `document` (host artifact, encoder side). direct.mjs (direct.jsonl): every layered decoded.js is byte-identical to
  the VM decoder run on that cell's vm.js, so the outer decode leaves nothing the VM decode reads; no dispatch residue,
  no labeled blocks, only the for-in enumeration helper where the source enumerates.
- Measure s37 (2026-11-06, `measure.sh s37 recheck-s36`; recheck rerun after a probe overlapped it): vitest 1404,
  1403 passed, 0 failed, 1 todo; recheck 47 of 47 same status, every output equal to s36's with its `if (false)`
  blocks stripped; parity 179 files: 126 identical to HEAD, 53 differ only by dropped blocks (one also drops a
  register declared only for them); residue census equal to s36 with bytes and deadBlocks set aside, deadBlocks
  897 -> 0. The next measure compares with recheck-s37.
- Measure s36 (2026-11-06, `measure.sh s36 recheck-s35`, with the Plan 8 fix, 10 min): vitest 1403, 1402 passed, 0
  failed, 1 todo; recheck 47 of 47 identical to s35; parity 179 files, 2 differ from HEAD (corpus/raw
  f-expression-mutation and program-cash, only their delete line, as remedy A writes it); census equal to s35's as a
  multiset (198 entries). The next measure compares with recheck-s36.
- Gap recheck (2026-11-01, troubleshooting/gap/, seeds 251-253): where encoded differs and decoded equals source
  (strict host this, BigInt `**`, host getters on safe globals) the encoder, not the decoder, differs.
- Rebuild 2 (2026-11-06): decode-js 17 commits on main, head 412dec4: today's changes squashed into e09b518, f739d1e,
  11512b1, c45d5b8, 4ed2cff, 5eb7772 (now c6b33e3, 082e3a5, 09965d6, cd0c531, a0944eb, 74a0b91) plus one refactor
  for the main-only modules; every rewritten commit imports all src modules, lints clean and passes its visitor,
  single-component and switch tests; tree equal to the s37 measured tree. Hub: fixups into fd566ae, e700818,
  23ce53e, cd10054, e2295a4, bf75742, dfc87e7, one docs commit for the main-only visitor docs, the pin and this file.
- Rebuild (2026-11-06): decode-js 16 commits on main 627fd96, head d0f13d5, tree equal to the pre-rebuild head
  9929e95; full vitest (`--coverage.enabled=false`, JDK on PATH) passes on every commit (1-12 in 5 s each; 13-16 in
  7 min each with the warm cell cache; head 1403, 1402 passed, 1 todo). Hub 23 commits on main 27076b9, tree equal to
  fb2099a except the decode-js gitlink and this file; no doc cited a rewritten decode-js ID.
- Rebuild 3 (2026-11-11): both fixes squashed into the generated-cell suites commit 74a0b91, now ebdac97; head
  8f27ab4, tree equal to 412dec4 minus the dropped cell plus the stage-effect split. Each of the 5 rewritten
  commits imports all 115 src modules and lints clean; its own tests pass (JDK on PATH): ebdac97 and head
  stage-effect + distinct-cells 15 of 15; e3aa79a 46 of 46; 939695b 53 of 53; the
  all-stages-together suite 36 of 36 before the split. With coverage, stage-effect + distinct-cells run in 36 s
  wall, largest file 34 s (single-payload-stage); removing a stage-effect file fails the pairing check.
  Hub: tests.md fixups into its doc commit, the pin and this file.
- Owed: the cold cache path of the cell split, first run by CI.

## Repository state

- Hub docs/js-confuser-vm-study-plan and decode-js codex/jsconfuser-vm-two-step-decoder: rebuilt from main
  2026-11-06, so their origin copies diverge; publishing needs a force-push, and nothing is pushed without the user.
  Pre-rebuild heads kept as backup/<branch>-2026-11-06 (decode-js 9929e95, hub fb2099a).
  Pre-rebuild-2 heads kept as backup/<branch>-2026-11-06b (decode-js d0f13d5, hub 8b7bb73).
  Pre-rebuild-3 heads kept as backup/<branch>-2026-11-11 (decode-js 412dec4, hub 1b76c1e); decode-js 0de2cf9
  (drop only) as backup/codex/jsconfuser-vm-two-step-decoder-2026-11-11b.
- A fixture's encoded.js regenerates only when missing: delete it after editing its source.js.
- Preserve: hub check-git-email.sh, decode-js fireyejs.js (untracked), decode-js scripts/
  leftovers, evidence .DS_Store, ignored sandbox-tests. Encoders clean.
- decode-js sandbox-tests/ (ignored): js-confuser-vm/ (encoder clone, keep); vm-cells/ (cell cache, regenerable,
  pruned to the current suites' cells 2026-11-06); new `s*-var` scratch copies and `<tag>-head` archives are disposable.
- A local test run needs JSCONFUSER_VM_ENCODER (or the decode-js encoder clone) and a JDK on PATH
  (Homebrew's openjdk here) for minify cells.

## Assets

- sandbox-tests/decoder-capability-2026-10-12/ (ignored; troubleshooting/ keeps only what is listed here, with
  measure-s37 and tools/recheck-s37; measure-s36 and tools/recheck-s36 are superseded): frozen evidence (generated/, corpus,
  results JSON, observe-one.mjs). troubleshooting/: measure.sh <tag> <prev recheck> (outputs in
  measure-<tag>/; runs tools/fixture-parity-s2.mjs, tools/recheck.py and residue-census/census.mjs;
  minify needs a JDK on PATH); tools/ (encode.mjs: encoder defaults plus options, mulberry32 seed;
  gen-fixture.mjs, gen-listing.mjs, around.mjs, compare.mjs, behave.mjs, exercise.mjs, sweep.mjs;
  DJ_SRC selects another decoder src); shared/ (register.mjs, redirect-hooks.mjs, edges.mjs). A
  `<tag>-head` archive needs node_modules linked before the census runs on it.
- troubleshooting/step8/ (the latest tool copies, run from decode-js): repro.mjs <source> <profile> <seeds> (the
  suites' generate call, public decode in a child, behaviour; cells/), trace.mjs <encoded> <fn> (export replay; DJ
  selects a src), var.mjs <cell dirs> (SRC, OUT), audit.mjs (SEL source regex, VARENV variation, ALL=1 behaviour on
  every success; out/), match.mjs, summ.py <jsonl>; the last step's cells/ and min/.
  Earlier step dirs were deleted (2026-11-06); their facts are in the skill docs and commits.
- troubleshooting/vm2-layered/: gen.mjs <seeds> <source.js>... (run from decode-js; VM2-213 VM encode, outer
  JS-Confuser encode, sequential decode, behaviour per stage); cells/<source>/<seed>/ keeps source.js, vm.raw.js,
  vm.js, encoded.js, outer-decoded.js, decoded.js, decode.json, behaviour.json, cell.json, vm-generation.ndjson;
  run.jsonl one row per cell; direct.mjs writes vm-direct-decoded.js per cell and direct.jsonl. encoder/js-confuser/dist is byte-identical to a babel build of its pin 31c5a47
  (js-confuser-31c5a47/ there).
- troubleshooting/gap/ (the gap recheck's sources and tools); troubleshooting/n1/pops.js and pops.cff (seed 1): the
  cell behind the first decision below.

## Decisions not to re-make

- Removing CFF's split jumps (placing a block entered by one transition after it): CFF cannot
  tell a split from the compiler's identical exit jump, and the backend's catch-pop rule needs
  that jump (cff-loop-return and troubleshooting/n1/pops.js declined).
- A backend catch-exit rule without the jump: a try has one pop per exit crossing it, so "the
  block after the pop" is not unique.
- CFF publishing its unproved jumps for the string inverse: byte-identical on all 238 inputs to
  the committed N1, which publishes none; a split jump is spelling (M2), so the set carries no
  information.
