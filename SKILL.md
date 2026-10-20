# decode-nexus — Skill Hub

**This file is the must-read.** Every agent reads it completely at session start. Everything else
under `skills/` is read when a rule here sends you there.

## Gates

Break none of these. Each one cost real work when it was missing.

1. **Ask before deciding.** When the plan leaves a design open, when work would change a design,
   or when a result departs from what the plan predicted: stop that line of work, write the
   finding and two or three options with a recommendation into `checkpoint.md`'s Open questions,
   ask the user, and wait. Independent work may continue meanwhile. Each option cites, by label,
   the [decoding rules](#decoding-rules) that support it and those it violates, or says none.
   - *Design gap:* the plan does not fix the algorithm, representation, interface, component
     boundary or tool. Do not fill it from your own experience.
   - *Design change:* reversing a recorded decision or rule; changing an interface, ownership or
     layer boundary; adding a deliverable, tool, population or phase the plan does not name;
     adopting a new mechanism to get past a failure.
   - *Unexpected result:* a failed or partial run, a decline or regression the plan did not
     anticipate, a review finding that widens scope.
   - A review, an architect's acceptance or an earlier "go" is not the user's decision. A subagent
     escalates to Main; Main escalates to the user.
2. **Read budget.** This file stays within 1,500 words, and the must-read (bootloader, this file,
   `checkpoint.md`) within 5,000. The decoding rules table stays here, so every agent sees it.
   The binding limit is the smallest compaction point among agents that read it (Codex logs
   `auto_compact_scope_limit` per model), and rules lost to compaction stop being followed.
3. **Re-read after compaction.** After a compaction or handoff, re-read this file and
   `checkpoint.md`'s Resume here before the next action.
4. **Read-only submodules.** Encoders and the evidence corpus are never modified, branched or
   committed. An encoder pin moves only after the decoder has run against output built from the
   new commit.
5. **Evidence matches the claim.** Build no harness, snapshot, archive or digest beyond what the
   claim needs. A tracked file is identified by its Git commit, never by a stored hash. A figure
   counts only if a recorded seed, a checked-in tool and reachable commits reproduce it.
6. **Facts in skill docs, status in the checkpoint.** Never park the only copy of a fact in a
   commit message or `checkpoint.md`. Never write task status (accepted, pending, reviewed) into
   a skill doc. `checkpoint.md` holds no rules; a rule that matters goes into a skill doc with the
   user's approval.
7. **Commit by the conventions.** `type(scope): subject`, type one of `docs fix feat chore
   refactor test build`; one scope and one concern per commit; `git commit -s` with the
   repository's own git identity.

## Hub rules

| Submodule | Role | Mutability |
| --- | --- | --- |
| `encoder/javascript-obfuscator`, `encoder/js-confuser`, `encoder/js-confuser-vm` | Encoder | Read-only (gate 4); read for AST patterns |
| `decoder/claude-vs-js-confuser` | Evidence corpus | Read-only (gate 4) |
| `decoder/decode-js` | Decoder engine | Editable: on a branch inside its own repository, never from a detached HEAD |

- **Project Independence:** each skill package documents one submodule. No cross-package
  references, except a decoder package linking the encoder it decodes; comparisons live in a hub
  study. An encoder doc never says how to reverse itself.
  [Details](skills/doc-conventions.md#project-boundaries).
- **Measured figures are diary:** a skill doc records the axis and the census that reads it,
  never the value. [Details](skills/doc-conventions.md#where-facts-live).
- **No machine-local paths** (`/Users/…`, `/home/…`, `C:\…`) in any tracked file.
- **English only** for everything newly written or edited; leave existing non-English as it is.
- **Revise by evolution:** a new incident sharpens, merges or replaces an existing item; never
  append a near-duplicate. [Details](skills/doc-conventions.md#revising-a-doc).
- **Read on a trigger:**

  | When you are about to… | Read first |
  |---|---|
  | write or edit a skill doc | [doc-conventions.md](skills/doc-conventions.md) |
  | write `checkpoint.md` | [checkpoint-format.md](skills/checkpoint-format.md) |
  | delegate to a subagent | [orchestration.md](skills/orchestration.md) |
  | commit or move a pin | [git-workflow.md](skills/git-workflow.md) |
  | apply a decoding rule below | its section in [encoder-decoder-method.md](skills/encoder-decoder-method.md) |
  | question or extend a decoding rule | [encoder-decoder-incidents.md](skills/encoder-decoder-incidents.md) |
  | study an encoder/decoder pair new here | [encoder-decoder-newpair.md](skills/encoder-decoder-newpair.md) |

## Decoding rules

Apply these to every change to a decoder or its docs. **P**lan, **D**iagnose, **F**ix, **M**easure.

| Label | Rule |
|---|---|
| [P1](skills/encoder-decoder-method.md#p1-work-in-reverse-encoder-stage-order-each-stage-placed-by-its-last-write) | Work in reverse encoder stage order, each stage placed by its last write: fix the last stage first and peel the outermost first; a later stage silently breaks earlier matchers. |
| [P2](skills/encoder-decoder-method.md#p2-attribute-era-boundaries-outward-from-a-closed-version) | Attribute era boundaries outward from one fully closed version, nearest boundary first. |
| [P3](skills/encoder-decoder-method.md#p3-each-decoder-removes-only-its-own-additions-by-its-own-encoders-facts) | Each decoder removes only what its own layer or stage added, using only what that encoder used; an addition whose deciding fact only a later decoder can read stays in place as a suspect, read past by every decoder in between and settled by the owner's own rule once that decoder has run. |
| [P4](skills/encoder-decoder-method.md#p4-every-work-item-names-its-output-measure) | Every work item names the decoded-output measure it should move. |
| [D1](skills/encoder-decoder-method.md#d1-read-the-tree-and-its-docs-before-you-probe-or-propose) | Read the tree, its owning docs and the encoder stage that added the shape before you probe or propose; what already works or is already decided beats any experiment. |
| [D2](skills/encoder-decoder-method.md#d2-verify-claims-before-acting-on-them) | A comment, doc, status or spec is a claim; verify it before you act on it. |
| [D3](skills/encoder-decoder-method.md#d3-instrument-one-real-failure) | Instrument one real failure; never root-cause from reading alone. |
| [D4](skills/encoder-decoder-method.md#d4-fix-the-producer-not-the-consumer) | Fix the operation that produced the bad shape, not the consumer that tripped on it. |
| [D5](skills/encoder-decoder-method.md#d5-use-what-earlier-steps-established) | Use what earlier steps established: a proved fact narrows and serves as reference for every later step; never re-derive it from defaults or spelling. |
| [F1](skills/encoder-decoder-method.md#f1-select-what-the-program-cannot-run-without) | Select what the program cannot run without, never how it is spelled: names, declarators, layout, statement shape, distances and allocated values are spelling; a location is identity to whatever jumps to it. |
| [F2](skills/encoder-decoder-method.md#f2-resolve-completely-or-not-at-all) | Resolve a matched structure completely or leave it untouched. |
| [F3](skills/encoder-decoder-method.md#f3-keep-tree-and-derived-state-consistent) | After a pass, derived state must equal what a fresh parse of its output gives. |
| [F4](skills/encoder-decoder-method.md#f4-keep-a-guard-only-where-a-real-case-needs-it) | Keep a refusal guard or fallback only where an encoder-produced case reaches it. |
| [F5](skills/encoder-decoder-method.md#f5-one-fix-is-never-the-whole-fix) | Grep for the defect's shape everywhere, and turn the audit into a harness assertion. |
| [F6](skills/encoder-decoder-method.md#f6-revise-the-owning-rule-never-patch-beside-it) | Revise the rule that owns the behaviour; a special case beside it is a patch the next variant pays again. |
| [F7](skills/encoder-decoder-method.md#f7-a-shared-pass-needs-off-path-cases) | A pass shared by several decoders needs hand-built cases off every encoder's path that the source language can express, and its normal form must reach both sides of every comparison. |
| [M1](skills/encoder-decoder-method.md#m1-judge-an-output-by-how-it-reads-against-its-source) | Judge an output by how it reads against its source: a passing run proves nothing, and neither does a changed output, or a count of them, until it is read. |
| [M2](skills/encoder-decoder-method.md#m2-measure-residue-what-an-encoder-stage-added-and-the-decode-left) | Measure residue, what an encoder stage added and the decode left: size ratios, characteristic construct counts, leftover helpers. |
| [M3](skills/encoder-decoder-method.md#m3-freeze-the-corpus) | Freeze the corpus before comparing; encoder output is random. |
| [M4](skills/encoder-decoder-method.md#m4-a-control-must-reach-its-mechanism) | A control proves something only if it reaches the mechanism it names. |

## Skill directory

Governance and method docs are in the trigger table above.

- Encoders: [javascript-obfuscator](skills/javascript-obfuscator/javascript-obfuscator.md)
  (parser foundation, per-era transformer order, era registry);
  [js-confuser](skills/js-confuser/js-confuser.md) (transform-by-transform AST patterns);
  [js-confuser-vm](skills/js-confuser-vm/js-confuser-vm.md) (VM compiler/runtime order,
  serialization, options).
- Decoders: [decode-js](skills/decode-js/decode-js.md) (Babel and isolated-vm decode passes);
  [claude-vs-js-confuser](skills/claude-vs-js-confuser/claude-vs-js-confuser.md) (read-only corpus:
  algorithms, examples, experiment registry).
- Hub studies: [cross-decoder study](skills/cross-decoder-study.md),
  [js-confuser-vm study](skills/js-confuser-vm-study.md),
  [layer-pair architecture](skills/vm2-layer-pair-architecture.md).
- VM decoding contracts: [VM switch boundary](skills/decode-js/vm-switch-boundary.md),
  [exact inner VM recovery](skills/decode-js/transforms/jsconfuser-vm/exact-inner-recovery.md)
  (unimplemented proposal).
