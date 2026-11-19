# Checkpoint — awsc (fireyejs) decoder work

Decode `fireyejs.js` (fireyejs / bx-ua) by the VM method, a frontend for this VM feeding the
shared switch backend, in place of the present `awsc` plugin, which was written for an old version
and is incomplete (user, 2026-11-17: "we will try to switch"). Then merge it together with the
pending CONTRIBUTING change. Its encoder is unavailable, so this sample is the real exam of the hub
docs. Not in it: the js-confuser VM decoder, which is merged; its one leftover item is under Plan.

## Resume here

- Current state (2026-11-19): the decoding method docs are reorganized and committed on the hub
  branch: `skills/decoding-method/` holds `rules.md` (general rules), `with-encoder.md` (rules
  that need a runnable encoder, tagged *stages* or *options*), `without-encoder.md` (no rules
  yet) and `incidents.md`; transform-doc acceptance is in `doc-conventions.md`; SKILL.md lists
  the general rules as a list (1,286 words); links and same-file anchors resolve.
- Next action: ask Open question 0b (graduate the review's conventions), then Open questions 1–5.
- Why next: the conventions have no doc yet, and the fireyejs decisions are taken under these docs.

## Definition of done

- The decoded-output measure and the stopping point are set with the user (Open questions).
- Default shape: prove the cause on the real input, propose owners, options, P1 measures and
  tests, and wait for approval before implementing.
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
  method: only the frontend may know this VM, the backend reads only the model.
- User (2026-11-17): the awsc work and the CONTRIBUTING branch are merged together; the
  CONTRIBUTING branch gets no PR of its own.
- User (2026-10-31): outside a pre-commit measure, one test batch runs at most 5 minutes and
  covers only what the change can affect.
- User (2026-11-19): eras without an encoder need a method of their own; out of scope here, since
  this work has one fireyejs version.
- Conventions the user set in the method-doc review (2026-11-19), held here until Open question 0b
  places them in a doc:
  - A rule belongs in `rules.md` only if neither its text nor any rule it cites needs the encoder;
    otherwise it starts in `with-encoder.md`. (The entry condition is already written in
    `rules.md`.)
  - A rule's title (its bold line) states the scenario it applies to, clearly enough to stand
    alone, since a fresh session sees only the titles; every term means one thing there.
  - A label lives in one doc. Within a category, `rules.md`'s rules come first, then a rule
    follows any rule it cites as more general; a citation of an exception sets no order.
  - A rule heading is its label only (`### P3`), so a reference is a short `#p3` link.
  - A split rule's encoder half takes the next free number in its category.
  - Overlapping rules are merged into their owner, never kept beside it.
- decode-js PRs are rebase-merged, so a commit ID is settled only on main: the hub pin and any
  commit link wait for the merged hash
  ([doc-conventions.md](skills/doc-conventions.md#reference-direction-and-form)).
- Diagnostics and scratch tools go under the ignored `sandbox-tests/` of the repository they
  exercise; a tool a later step depends on is checked in
  ([doc-conventions.md](skills/doc-conventions.md#where-facts-live)). Encoders stay read-only.
- Before building a probe, read its [hazards](skills/decode-js/probes.md#hazards--the-ways-a-probe-lies).

## Plan

| Step | Work | Unblocks |
|---|---|---|
| 2 | Decide Open questions 1–6, one per message | 3 |
| 3 | The approved awsc work, on a decode-js branch that carries the CONTRIBUTING commit | 4 |
| 4 | Merge in decode-js; move the hub pin to the merged hash; publish the hub branch | none |

0b may land at any point before step 4. No dependency sets where the hub branch's publication
falls; it can happen before step 4 with the pin it has now.

Not scheduled (user, 2026-11-15): VM decoder code no cell reaches, each candidate checked against
the encoder (D6) and then removed (F7) or given a cell. The candidates are the Known Gaps entries of
the docs under `skills/decode-js/vm/` worded "no input that reaches it", "no committed cell
reaches", "no committed test asserts"; the literal forms are in
[vm-switch-emit.md](skills/decode-js/vm/switch/vm-switch-emit.md#5-known-gaps).

## Validation

- decode-js main at the pin bdd37f2: CI's Unit Tests and CodeQL green (2026-11-17).
- Hub working tree (2026-11-19): every relative link and every same-file anchor in the hub's
  Markdown resolves (scratch checker; its 30 remaining hits are code spans shaped like links).
  SKILL.md 1,324 words; must-read under 5,000.
- Owed: the proof census's `cross` command (`decoder/decode-js/scripts/proof-census.mjs`) has
  never been run.

## Repository state

- decode-js: checkout on `awsc` (the hub pin stays bdd37f2, main). Local branches `main` and
  `awsc`, rebased onto main (5 commits in `src/plugin/awsc.js`) with the CONTRIBUTING commit on
  top; local and origin agree. Untracked and to keep: `fireyejs.js`.
- Hub: branch `docs/awsc-vm` from main: the checkpoint commit, then the method-doc
  reorganization. Untracked and to keep: `check-git-email.sh`. This file leaves when the work merges.
- Nothing is pushed without the user.

## Findings (to graduate to the plugin doc once the user approves a doc change)

Read 2026-11-19 from `fireyejs.js` by a Babel traverse (scratch, not kept) and by reading the
pretty-printed text.

- **Outer layer, flattening over register arrays.** The whole program is one IIFE. The top level
  and each of seven large functions (`l[6]`, `l[11]`, `l[10]`, `l[3]`, `l[4]`, `l[5]`, `b`) run as
  `for (state = N; void 0 !== state;) { switch (mask & state) { case i: r(function () {
  <nested ternaries on (mask & state >> shift)> }, this); break; … } }`. Their locals live in an
  array (`v[i]`, top level `l[i]`), and the state is one of its slots (`v[37]`, `l[54]`). A
  transition is an assignment to the state slot, a branch is `state = c ? A : B`, and an exit is
  `state = void 0`, a `return` or a `throw`. `r` and `n` are `Function.prototype.call` bound:
  `r(f, this)` only calls the case body. 304 such loop/switch pairs in all.
- **Inner layer, 40 bytecode islands.** 40 numeric `push` literals (17,152 words, 448 non-literal
  operands such as `i("10001", 2)`), each inside an IIFE in one flattened case, each with its own
  copy of an interpreter (37 by the fetch shape `$ = m[I = 4 * h]`). An instruction is 4 words:
  word 0 is a flag set decoded by a decision tree, words 1–3 are operands. The handlers read and
  write three storages: the island's own `r[]`, the host function's `v[]` and the global `l[]`;
  they keep call stacks and make JS closures that re-enter the interpreter at an entry PC.
- **One observed nesting, not a stage order.** The interpreter copies are themselves flattened in
  the same template (masks 7/3 and 1/1 bits, `n(function(){…}, this)` wrappers), so the flattening
  rewrote the islands' interpreters. This orders those two mechanisms only; P3's stage order is the
  encoder's full defined sequence, which no sample gives.
- **Strings.** The top level holds shifted-character string literals decoded into `l[]` tables
  (`charCodeAt(…) - key`), read through helper calls such as `n(l[11], null, 11, 34)`.
- **Incumbent verdict (2026-11-19).** The `awsc` branch's plugin throws `TypeError` in
  `FlattenSwitch` (`src/plugin/awsc.js:768`) on the sample. It handles the outer layer only
  (ternary chains to switches, case merging, `eval` folding of strings) and has no notion of the
  islands.
- **Prior art in decode-js.** No flattening pass for this shape. The js-confuser and
  javascript-obfuscator control-flow visitors are encoder-specific and do not transfer; the
  `src/visitor/atomic/` normalizations (conditional-assign, conditional-if, logical-if, if-test
  sequence) do, and the plugin has private copies of them (D1).

## Doc shortfalls left open

- The [VM switch boundary](skills/decode-js/vm/switch/vm-switch-boundary.md) assumes one VM
  program per input: one model, root frame 0, emission as a whole-program shell. It is silent on
  islands embedded in host code, host storage the VM reads and writes, emitting a fragment back
  into a host, and a host that is itself flattened. Settled with Open questions 1 and 2.
- `without-encoder.md` has no rules: the sample-only workflow, guard bounds, measures and the
  behaviour oracle are the hypotheses below until this work proves them.
- [doc-conventions.md](skills/doc-conventions.md#pipeline-map-layout) derives a pipeline map's
  "Encoder steps" and "Reversibility" sections from the encoder source; neither can be written
  for a sample-only target, and Project Independence expects a decoder package to link its
  encoder.

## Hypotheses for `without-encoder.md` (unproved; each graduates only once this work proves it)

- Counterpart of P5 (user): each stage's target (what it added and what it uses) is proposed from
  observing the sample, and the stage's decoder follows that stated target exactly.
- Counterpart of P6 (user): with only samples, the study runs outer to inner; the sample is the
  full combination, so the outermost visible mechanism is peeled first.
- Not P3: nesting in a sample gives a partial order over observed mechanisms only; untouched pairs
  and traceless stages stay unordered.
- The shipped runtime's own reading (a dispatcher's state decode) is the fact a stage's decoder
  uses.
- Counterpart of F7 and D8: a census of every instance in the sample bounds the variants a matcher
  accepts.
- Counterpart of F8: no divergence can be proved, so keep the encoded behaviour everywhere and
  write a native form only where it equals the handler's.
- Each collected sample is a version point, frozen as a committed fixture.
- A behaviour check runs the original and the decoded program, or one unit of each, under one
  recorded environment.
- Pipeline map: "encoder steps" become observed mechanisms in their observed order.

## Open questions

Asked one per message, in this order.

0b. **Graduate the review's conventions** (Constraints and decisions) into `doc-conventions.md`, or
   leave them here until the work merges. Recommendation: graduate them; this file leaves at merge.
1. **The outer flattening (first by P3): how is it undone?**
   - A. A frontend lowers each flattened function to the switch model, every JS expression in a
     case body lowered to typed operations. Supports F5 (one structured recovery); a large grammar
     extension (gate 1) and loses the names the host keeps.
   - B. Extend the model with a statement-block operation: a case carrying a JS statement list
     with the register slots it reads and writes, so the shared control solve and statement
     planning recover the structure. Supports F5 and the ownership test; needs F6 off-path cases
     for the backend; a boundary change (gate 1).
   - C. A Babel de-flattener of its own, the incumbent's approach redone. Violates F5 (a second
     structured recovery beside the backend's); outside the VM method.
   - Recommendation: B.
2. **The islands: how do they reach the backend?** They read and write host `v[]` and global
   `l[]`, and hand closures to the host.
   - A. Extend the model with host storage and a fragment emission that replaces the island in
     its host. Supports the ownership test and F5; a boundary change (gate 1); F6 cases.
   - B. Map host slots onto `global-read`/`global-write` with synthetic names and patch the
     emitted program back. Violates "a correct model" and F4 (a post-pass matching the backend's
     spelling).
   - C. Leave the islands intact in the first deliverable; defers the boundary.
   - Recommendation: C now, A once the outer layer is peeled (its residue is the islands' input).
3. **Measure and corpus (P1).** Proposed axes on the frozen sample: flattened loop/switch pairs
   (304 to 0); `r(function(){…}, this)` case wrappers; islands and interpreter copies (40 to 0,
   once question 2 opens them); string helper calls; the size ratio only beside them (M2's VM
   caveat). Open: whether to commit the sample as a frozen fixture, and whether to build a
   behaviour oracle (a Node shim with fixed `navigator`, `document`, time and randomness comparing
   the token the program produces), a tool the plan does not name (gate 1). Recommendation: commit
   it if its licence allows, and build the oracle as M1's regression guard.
4. **Stopping point of the first deliverable.** Recommendation: the outer layer fully undone (and
   the strings if they sit in it), the islands intact; a full decode is a second deliverable.
5. **Name.** Replace the `awsc` entry or sit beside it under a new name. Recommendation: replace
   it, since the user retires the old plugin.

## Assets

- `decoder/decode-js/fireyejs.js` (untracked): the user's fireyejs sample.
- [plugins/awsc.md](skills/decode-js/plugins/awsc.md): the plugin's ten rewrites and the warning
  that they are shape hints, not behaviour-preserving proof.
