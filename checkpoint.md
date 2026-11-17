# Checkpoint — awsc (fireyejs) decoder work

Decode `fireyejs.js` (fireyejs / bx-ua) by the new VM method, a frontend for this VM feeding the
shared switch backend, in place of the present `awsc` plugin, which was written for an old version
and is incomplete (user, 2026-11-17: "we will try to switch"). Then merge it together with the
pending CONTRIBUTING change. Its encoder is unknown, so this sample is the real exam of
the hub docs (user, 2026-11-17): the method and the new-pair guide must carry the work without an
encoder to read. Not in it: the js-confuser VM decoder, which is merged; its one leftover item is
under Plan.

## Resume here

- Current state (2026-11-17): the VM decoder work is closed and merged in both repositories
  (hub origin/main 28e7593 pins decode-js main bdd37f2). Local branches cleaned; hub work branch
  `docs/awsc-vm` created; decode-js `awsc` rebased onto main.
- Next action: read [encoder-decoder-newpair.md](skills/encoder-decoder-newpair.md) and the method
  sections it sends to; the VM method's contract, the
  [VM switch boundary](skills/decode-js/vm/switch/vm-switch-boundary.md), and the
  [pipeline map](skills/decode-js/pipelines/jsconfuser-vm.md) as the one worked frontend; then
  [plugins/awsc.md](skills/decode-js/plugins/awsc.md), `src/plugin/awsc.js`, the `awsc` branch's
  difference from main and `fireyejs.js` itself; propose
  the work items with their P4 measures and list where the docs gave no answer; wait for approval.
- Why next: the docs are what is examined, so the plan is derived from them first; every place
  they assume an encoder source is a finding for the user (gate 1), not a gap to fill from
  experience.

## Definition of done

- The decoded-output measure and the stopping point are to be set with the user (Open questions).
- Carried over from the VM work as the default shape: prove the cause on the real input, propose
  owners, options, P4 measures and tests, and wait for approval before implementing.
- Each place the hub docs failed, misled or stayed silent on this encoder-less target is reported;
  a doc change is proposed to the user, never made unasked.

## Constraints and decisions

- User: direct work, no delegation; read the code before proposing; await approval. A design gap,
  a design change or an unexpected result stops that line: record options with a recommendation
  and ask. Update this file after each step.
- User: no commit and no push without approval. The user answers one choice per message; present
  a list and its open choices, then wait.
- User (2026-11-17): the present `awsc` plugin and branch describe an old fireyejs version and
  are incomplete; they are a source of shape hints, not the base to finish. The work tries the VM
  method: only the frontend may know this VM, the backend reads only the model
  ([pipeline map layout](skills/doc-conventions.md#pipeline-map-layout)).
- User (2026-11-17): the awsc work and the CONTRIBUTING branch are merged together; the
  CONTRIBUTING branch gets no PR of its own.
- User (2026-10-31): outside a pre-commit measure, one test batch runs at most 5 minutes and
  covers only what the change can affect.
- decode-js PRs are rebase-merged, so a commit ID is settled only on main: the hub pin and any
  commit link wait for the merged hash
  ([doc-conventions.md](skills/doc-conventions.md#reference-direction-and-form)).
- Diagnostics and scratch tools go under the ignored `sandbox-tests/` of the repository they
  exercise; a tool a later step depends on is checked in
  ([doc-conventions.md](skills/doc-conventions.md#where-facts-live)). Encoders stay read-only.
- Before building a probe, read its [hazards](skills/decode-js/probes.md#hazards--the-ways-a-probe-lies).
- Cross-plugin prior art: only encoder-agnostic normalization transfers, and the `awsc` branch
  is incomplete ([newpair](skills/encoder-decoder-newpair.md#use-incumbent-and-preset-evidence)).

## Plan

| Step | Work | Unblocks |
|---|---|---|
| 1 | Derive the approach from the hub docs alone (new-pair guide, method, VM switch boundary); read `fireyejs.js`, then the awsc plugin, its doc and the `awsc` branch for hints | 2 |
| 2 | Propose the work items, their measures and the list of doc shortfalls; get the user's decisions | 3 |
| 3 | The approved awsc work, on a decode-js branch that carries the CONTRIBUTING commit | 4 |
| 4 | Merge in decode-js; move the hub pin to the merged hash; publish the hub branch | none |

No dependency sets where the hub branch's publication falls; it can happen before step 4 with
the pin it has now.

Not scheduled (user, 2026-11-15; to be scheduled after the VM merge): VM decoder code no cell
reaches, each candidate checked against the encoder (D1) and then removed (F4) or given a cell.
The candidates are the Known Gaps entries of the docs under `skills/decode-js/vm/` worded "no
input that reaches it", "no committed cell reaches", "no committed test asserts"; the literal
forms are in [vm-switch-emit.md](skills/decode-js/vm/switch/vm-switch-emit.md#5-known-gaps).

## Validation

- decode-js main at the pin bdd37f2: CI's Unit Tests and CodeQL green (2026-11-17).
- Hub rebuilt branch (2026-11-17): tree equals the pre-rebuild tip plus the graduated doc edits,
  minus `checkpoint.md`; every commit signed off; relative links resolve at every commit except
  within the VM docs, which link each other in a cycle.
- Owed: nothing for the VM work. The proof census's `cross` command
  (`decoder/decode-js/scripts/proof-census.mjs`) has never been run.

## Repository state

- decode-js: checkout on `awsc` (the hub pin stays bdd37f2, main). Local branches: `main` and `awsc`, rebased
  locally onto main (2026-11-17, no conflicts; 5 commits, all in `src/plugin/awsc.js`) with the
  CONTRIBUTING commit cherry-picked on top as 8345969; its source branch is deleted. Force-pushed
  to origin (2026-11-17, user's instruction); local and origin agree. Backup and merged `codex/...` branches deleted.
  Untracked and to keep: `fireyejs.js`. The first local VM test run fetches the encoder
  (`scripts/jsconfuser-vm-cells/fetch-encoder.mjs`) and regenerates the cells, and needs a JDK.
- Hub: origin/main (28e7593) carries the VM work. Work branch `docs/awsc-vm` from main,
  nothing on it yet. Local backups and `docs/js-confuser-vm-study-plan` deleted; that branch
  still exists on origin. Untracked and to keep: `check-git-email.sh`. This file is committed
  on the work branch (user, 2026-11-17) and leaves when the work merges.
- Nothing is pushed without the user.

## Open questions

- Whether the VM method fits is itself the trial: can a frontend for the fireyejs VM hand the
  shared backend its model unchanged, or does the boundary need to change (a design change, the
  user's decision)? Step 1 answers what it can from the sample and the boundary doc.
- What decoded-output measure should move (P4), and where the first deliverable stops (admitting
  and reading the VM's program, or a full decode)? No recommendation before step 1's reading.
- Does the new target replace the `awsc` entry or sit beside it under a new name? The plugin doc
  and the roster in decode-js.md change either way.
- The method's encoder-reading rules (P1, P3, D1, the stage order) have no encoder source here.
  Whether the sample's own structure stands in for it, and which doc says how, is the first thing
  step 1 must find or report as missing.

## Assets

- `decoder/decode-js/fireyejs.js` (untracked): the user's fireyejs sample.
- [plugins/awsc.md](skills/decode-js/plugins/awsc.md): the plugin's ten rewrites and the warning
  that they are shape hints, not behaviour-preserving proof.
