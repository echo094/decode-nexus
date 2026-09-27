# decode-nexus — Unified Skill Hub

All operational expertise, AST transformation rules, and submodule interactions are modularized into skill packages inside `skills/`.

## Standing Rules
- **Read `encoder-decoder-method.md` Before Touching Anything:** Before any change to an
  encoder/decoder submodule or its skill docs, read
  [encoder-decoder-method.md](skills/encoder-decoder-method.md) — not after hitting trouble,
  and not from memory of a previous session. It carries both halves of this work in one place
  (how to study a new encoder/decoder pair, how to diagnose an existing decoder) precisely so
  a fix isn't rediscovered from scratch. Skipping it once cost two runs of probing to confirm
  an ordering fact its own T1 already stated. Its rules are the required read; the incidents
  behind them live in [encoder-decoder-incidents.md](skills/encoder-decoder-incidents.md), read
  when a rule is being questioned or extended rather than every session.
- **Doc Conventions:** Package layout, transform-doc structure (the numbered items,
  `## Source`, `## Fixtures`), and the form of any reference crossing between hub and
  submodule live in [doc-conventions.md](skills/doc-conventions.md). Read it before writing
  or editing a transform doc; the rules below apply to every change regardless.
- **Orchestration Gate:** Your bootloader decides the session's shape — its default, and the
  test for departing from it. Whenever a session will delegate to subagents, read
  [orchestration.md](skills/orchestration.md) before the first packet; a session working
  directly never opens it.
- **Checkpoint Is Scratch, and Its Layout Is Specified:** `checkpoint.md` at the hub root is the
  restart interface between sessions and agents, ordered important-first with history last, and
  updated after each step rather than at each milestone. Its required sections, its exclusions
  (no rebuildable-history SHAs, no fact that has a durable home, no bare measured figure) and the
  handoff it owes are in [checkpoint-format.md](skills/checkpoint-format.md). Read it before
  writing to the file; a fact settled there graduates into a skill doc and is pruned in the same
  change.
- **Read-Only Encoders:** Code inside encoder submodules (currently
  `encoder/javascript-obfuscator`, `encoder/js-confuser`) is for reading AST patterns
  only — never alter it.
- **Encoder Pin Gate:** Never advance an encoder submodule's pinned commit until the decoder
  has followed up on it — run against real output built from the new commit and confirmed to
  still hold, not merely diffed and read. Moving the pin first and reconciling afterward
  records an encoder claim nothing has verified, which is the gap a decode attempt exists to
  close. Full process: "Updating a Submodule's Commit Pin."
- **Decoder Role Does Not Determine Mutability:** A decoder submodule may be an editable reusable
  engine or a read-only evidence corpus; the role must be explicit in the hub registry and its
  skill package.
- **Read-Only Decoder Corpora:** Evidence submodules (currently
  `decoder/claude-vs-js-confuser`) must not be modified, branched, or committed. Their
  experiment-specific scripts are bounded prior art; useful deductions must be re-derived into an
  editable decoder only after transfer evidence and the decoder's own acceptance gates.
- **Editable Decoder Engine:** Decoder submodules (currently `decoder/decode-js`) may be
  modified — linting, fixes, and new decode capabilities are allowed — subject to:
  - **Branch inside the submodule first.** Create the branch *in that submodule's own
    repository*. Never hold submodule work on a hub branch, never commit from a detached HEAD.
  - Every change follows the Commit Conventions below and is committed on that branch, in
    the submodule's own repository — never in the hub.
- **Project Independence:** Each skill package documents exactly one submodule, in isolation.
  Never cross-reference, assume, or depend on another project's code, coverage, or status — a
  skill file should read the same regardless of which other submodules exist here.
  Cross-project observations belong in a parent-level hub study that hosts every project being
  compared, never in one participant's own package. **For two decoders this includes capability
  comparisons, algorithm-transfer or adoption lineage, readability conclusions, benchmark
  summaries, and statements that one informed, outperformed, or was generalized into the other.**
  Each decoder package documents only its own mechanism and independently verified boundary; it
  must not name, link, summarize, or depend on the other decoder inside its own durable scope.
  - **Exception — decoder → encoder**, one-directional and narrow: a decoder package may
    reference the encoder it actually decodes, since a decode capability is only meaningful in
    terms of what it reverses. An encoder package must never reference a decoder, and
    decoder↔decoder or encoder↔encoder cross-references stay forbidden — **across** packages,
    not *within* one, where sibling docs may freely link each other. The exception requires a real
    link; name-only text is not a workaround for a forbidden cross-project reference.
- **Ignored Evidence Is Never Durable:** Any ignored generated, probe, corpus, or task-session
  tree is session-local staging only. Skills, checkpoints, reports, tests, and other tracked
  documents must not name or link any path in that tree or depend on it for resumption. Promote
  the accepted fact to tracked documentation/tests, or retain the bytes in a verified archive
  identified by stable session metadata and a manifest digest; a later session must receive that
  archive explicitly rather than resolving an old local path.
- **Root File Scope:** Keep a skill package's root file about the workflow, not the plumbing,
  and name it after the skill (e.g. `js-confuser.md`) — a subfolder of files all named
  `SKILL.md` is unnavigable. It covers the parser/AST foundation, the package's own verified
  layout (a "Skill Layout" section, not the submodule's directory tree — see the next rule),
  the pipeline/stage order, and an execution-flow diagram. Everything else — option
  surfaces, plugin APIs, constants, helpers, templates, result types — moves into its own file
  once it would bloat the root, indexed from a "Skill Layout" section. **This file is subject
  to the same rule**, which is why the doc specifications sit in `doc-conventions.md`.
- **The Package Layout Is Ours:** A package is laid out around the components every
  encoder/decoder has — order, options, transforms, templates — never around the
  submodule's own directory habit, and a doc is named for the transform or shape it
  describes, never for a source file. Structural drift and shape drift are independent
  axes: one obfuscator has an era boundary across which *no* source file changes at all,
  and another boundary whose only file changes are in an unrelated subsystem. So a
  file-keyed layout churns where nothing moved and stays silent where the shape did.
  Source-tree mirroring survives only *inside* large helper folders (`utils/<name>.md`,
  `templates/<name>.md`), one file per source file, flat and distinctly named. Full
  specification, and when a `source-map.md` is required to cross between the two:
  [doc-conventions.md](skills/doc-conventions.md).
- **Reversal Lives Only in the Decoder:** An encoder transform doc never asserts how to
  reverse itself. Project Independence forbids it from ever correcting that claim later — it
  can't cite the decoder that would prove it wrong — and two already needed correcting, one
  predicting an execution order the real decoder disproved, one calling three normalizations
  "not applicable" to reverse when they were simply unreversed. New encoder docs are not
  exempt.
- **Measured Figures Are Diary:** Any number produced by running something over a corpus — a
  byte count, a ratio, "N of M samples" — is void the moment that corpus is regenerated, and
  obfuscator corpora regenerate routinely because the encoder samples randomly. A skill doc
  records **the axis and the census that reads it, never the value**: "this census should read
  zero" survives; a byte total decays into a claim nobody can check. Same for counts of the
  tree itself — test files, cases, lint errors — which drift with every edit and have been
  wrong here more than once. Where a figure genuinely matters, cite the run that produced it.
  **A corrected figure carries the live caveat, not the story of its correction.** When a value is
  recomputed under a better definition, replace it and keep only what a reader would act on — that
  a column is not comparable with the one beside it, say. When it was corrected, what the old
  extraction did, and that the row was re-verified are all diary: they have no reader, since anyone
  who wants them has git, and the re-verification is worth stating in the commit message instead.
- **Revise by Evolution, Not Addition:** A new incident changes an existing item — across
  files, not just within one — rather than earning a new entry: sharpen it, merge two, or
  supersede one outright. State a point once and cite it from elsewhere; drop an entry once
  its incident teaches nothing the survivors don't. A doc that grows by one entry per incident
  stops being read, the few items that decide a plan diluted by near-duplicates — the fate
  `encoder-decoder-method.md` has three times avoided, once merging fourteen tips to eight, once
  folding five defect-source entries into the tips that act on them, and once splitting its
  incident narratives into a companion file so the rules stay scannable, every time losing no
  fact. **The third is the move to reach for when a doc is long but nothing in it is
  redundant:** separate what is read every session from what is read only when a rule is
  challenged, and keep the two keyed on the same labels. **Never park the only copy of a fact in a commit message or `checkpoint.md`** — a
  release rebuild rewrites history, and `checkpoint.md` is scratch. The durable copy is a
  skill doc's own text.
- **Commit Compliance:** Every commit must follow the Commit Conventions section below
  in full — format, type, scope, and sign-off are not optional.
- **English Only:** Everything newly written or edited — code comments, log strings, doc
  prose, commit messages — is English. Pre-existing non-English content stays as-is rather
  than being translated as a side effect of unrelated work (e.g. `obfuscator.js`'s Chinese
  labels), so this constrains what you write, not what you find. Check with
  `grep -nP '[^\x00-\x7F]' <changed files>` and read what it reports: the same grep flags the
  typographic characters (`…`, `—`, `→`) both trees use throughout, which are not a language
  violation.
- **Link Verification:** Verify links before every commit — skill docs cross-reference each
  other constantly, and renames drift them silently. When a change documents a Downstream
  Effect by citing the decoder that explains the mechanism, also grep the touched encoder
  doc(s) for `decode-js`: easy to leave a stray cross-package link in by reflex, and the
  encoder-side fact should stand without it.

## Commit Conventions

Use [Conventional Commits](https://www.conventionalcommits.org/), scoped by skill:

```
type(scope): subject
```

- **type:** one of the following — this list is closed; a commit using any other type
  is non-compliant, and adding a new type here is required before it can be used:
  - `docs` — skill-file writing/editing
  - `fix` — correcting a decoder/encoder behavior
  - `feat` — new decoder capability
  - `chore` — repo/hub maintenance, `.gitmodules`, tooling
  - `refactor` — restructuring without behavior change
  - `test` — adding or changing tests, fixtures, or the test harness
  - `build` — automated dependency bumps (e.g. Dependabot); platform-generated commit
    style, not for manual use
- **scope:** the skill/submodule the commit belongs to — e.g. `js-confuser`,
  `decode-js`, `javascript-obfuscator` — or `hub` for changes to this file itself.
  - When the commit is made inside a submodule (not the hub), that submodule's own
    skill entry file (e.g. `skills/decode-js/decode-js.md`) may define a more
    detailed, module-level scope convention for that project specifically — check
    there first if one exists.
  - One scope per commit; if a change spans multiple skills, split the commit (this
    also keeps commits aligned with the Project Independence rule above).
- **subject:** imperative, no trailing period, ~72 cols.
- **One concern per commit.** Don't bundle an unrelated pre-existing fix discovered in passing
  into a feature's own commit — give it its own, so neither can be reverted without the other.
- **Don't fix what a planned rewrite redoes.** Where a history rebuild is already scheduled over a
  range, a defect inside it — a missing sign-off, a non-conventional subject — is recorded for the
  rebuild to absorb rather than patched in place: the patch is work the rebuild repeats, and it
  adds a commit the rebuild then has to destroy.
- Body (optional): explain why, not what.
- Footer: `Signed-off-by: Name <email>` is **required** (use `git commit -s`); issue
  refs are optional.
- **Commit identity.** The agent **must sign every commit it authors** (`git commit -s`).
  The author and any `Signed-off-by` trailer come only from the `user.name` /
  `user.email` set in the `git config` active in the repository being committed to —
  never from the agent's session or environment context.

Example:
```
docs(js-confuser): document control-flow-flattening transform

Signed-off-by: Jane Doe <jane@example.com>
```

## Updating a Submodule's Commit Pin

The bump is the *last* step, gated on everything below (Standing Rules: Encoder Pin
Gate) — not a first step that gets reconciled afterward:

1. **Diff the as-is pin against the to-be pin before touching anything.** Read the
   actual upstream changes between the two SHAs — a pin bump is a reviewed decision, not
   a blind fast-forward.
2. **Check the corresponding skill package for drift.** Anything the diff touches that
   the docs describe — transform logic, plugin behavior, file/line references — needs
   re-verifying against the new commit.
3. **Follow up the decoder before moving the pin.** Run it against real output built from
   the new commit; fix whatever the diff broke, and re-verify anything the diff touched.
   Only once the decoder holds against the new commit is the pin allowed to move — this
   is what makes step 4 a description of already-verified behavior rather than a
   prediction of it.
4. **Decide whether the new commit is still the same era, and never erase the old
   behavior.** Samples already obfuscated/encoded in the wild were produced by the
   *previous* version's algorithm, so its description must stay on record alongside the
   new one, never replaced. Which of the two happened decides the work:
   - **Same era** (emitted shape unchanged) — nothing to add. The era's recorded SHA may
     advance to the new commit, but only on the strength of step 3's re-verification;
     absent that it stays where it was, since the SHA names the commit that proved the
     claims, not the newest one available.
   - **New era** (emitted shape changed) — open a new registry row and leave the previous
     row untouched, so both remain describable. The mechanics, and when a registry is
     required at all, are in [doc-conventions.md](skills/doc-conventions.md)'s
     "Documenting Multiple Eras."
5. **Land the pin bump last, in its own commit.** It lands in the hub repo as
   `chore(hub)` (stage only the submodule gitlink); any decoder fixes from step 3 and any
   doc updates from step 4 are their own commits, scoped to their own submodule, and land
   *before* it — not "follow" after.

## Active Skill Directory

- [doc-conventions](skills/doc-conventions.md) — Package layout, transform-doc structure, and
  the form of a hub↔submodule reference. The specifications Standing Rules points at.
- [checkpoint-format](skills/checkpoint-format.md) — The layout `checkpoint.md` must hold, what
  never goes in it, and what a handoff owes. Read before writing to that file, in any session.
- [orchestration](skills/orchestration.md) — Roles, write ownership, direct recording into the
  current partial bundle, evidence graduation, and wave integration for multi-agent work. Read
  **only** when the Orchestration Gate says the mode applies.
- [encoder-decoder-method](skills/encoder-decoder-method.md) — How to diagnose an existing
  decoder: the labelled rules, tiered by how often a session needs them. The required read.
- [encoder-decoder-incidents](skills/encoder-decoder-incidents.md) — The bug or wrong plan
  behind each of those rules, keyed on the same labels. Read when a rule is questioned.
- [encoder-decoder-newpair](skills/encoder-decoder-newpair.md) — The workflow for taking on an
  encoder/decoder pair with no package here yet. Read once per pair, not per session.
- [javascript-obfuscator](skills/javascript-obfuscator/javascript-obfuscator.md) — Reference
  for the `encoder/javascript-obfuscator` obfuscator: parser/generator foundation, the
  per-era transformer execution order, and the era registry the package's docs cite.
- [js-confuser](skills/js-confuser/js-confuser.md) — Transform-by-transform reference
  for the `encoder/js-confuser` obfuscator's AST patterns.
- [decode-js](skills/decode-js/decode-js.md) — Plugin-by-plugin reference for the
  `decoder/decode-js` deobfuscator's Babel + isolated-vm decode passes.
- [claude-vs-js-confuser](skills/claude-vs-js-confuser/claude-vs-js-confuser.md) — Read-only decoder
  corpus algorithms, supplied examples, controls, and experiment registry.
- [cross-decoder study](skills/cross-decoder-study.md) — Parent-level comparison of the pinned
  corpus and editable decoder, including transfer boundaries, adoption decisions, and readability.
- [js-confuser-vm study](skills/js-confuser-vm-study.md) — Target-specific cross-project method
  dispositions, Phase-1 scope, and remaining acceptance debt for the pinned virtualization study.
- [exact inner VM recovery](skills/decode-js/transforms/jsconfuser-vm/exact-inner-recovery.md) —
  Proposed source-derived transform for a future independent VM-2 benchmark.
