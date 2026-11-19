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
   `checkpoint.md`) within 5,000. The general decoding rules table stays
   here, so every agent sees it; the rules that need an encoder are listed in `with-encoder.md`.
   The binding limit is the smallest compaction point among agents that read it (Codex logs
   `auto_compact_scope_limit` per model), and rules lost to compaction stop being followed.
3. **Re-read after compaction.** After a compaction or handoff, re-read this file and
   `checkpoint.md`'s Resume here before the next action.
4. **Read-only submodules.** Encoders are never modified, branched or committed. An encoder pin
   moves only after the decoder has run against output built from the new commit.
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
  | apply a decoding rule below | its section in [rules.md](skills/decoding-method/rules.md) |
  | question or extend a decoding rule | [incidents.md](skills/decoding-method/incidents.md) |
  | decode with an encoder you can run | the rules table of [with-encoder.md](skills/decoding-method/with-encoder.md) |
  | study an encoder/decoder pair new here | [P7](skills/decoding-method/with-encoder.md#p7) |
  | decode a target with no encoder available | [without-encoder.md](skills/decoding-method/without-encoder.md) |
  | accept a transform doc | [doc-conventions.md](skills/doc-conventions.md#transform-doc-acceptance) |

## Decoding rules

Apply these to every change to a decoder or its docs; with an encoder you can run, add
[with-encoder.md](skills/decoding-method/with-encoder.md)'s. **P**lan, **D**iagnose, **F**ix,
**M**easure.

- [P1](skills/decoding-method/rules.md#p1) Before a work item starts, name the decoded-output
  measure it should move and the samples it is read on.
- [P2](skills/decoding-method/rules.md#p2) When you budget a unit, count the questions it must
  answer, not the code it should produce; a unit can close with no new code.
- [D1](skills/decoding-method/rules.md#d1) Read the decoder's code and its owning docs before you
  probe or propose; what already works or is already decided beats any experiment.
- [D2](skills/decoding-method/rules.md#d2) A comment, doc, status or spec is a claim; verify it
  before you act on it.
- [D3](skills/decoding-method/rules.md#d3) When you look for the cause of a failure, instrument one
  real failure; never root-cause from reading alone.
- [D4](skills/decoding-method/rules.md#d4) When a pass cannot read the shape it receives, find our
  own operation that produced that shape and fix it there, not in the consumer.
- [D5](skills/decoding-method/rules.md#d5) When a later step needs a fact an earlier step proved,
  use the proved fact; never re-derive it from a default or from how the code is written (names,
  layout, statement shape).
- [F1](skills/decoding-method/rules.md#f1) When a pass matches a structure, resolve it completely or
  leave it untouched.
- [F2](skills/decoding-method/rules.md#f2) When you fix a defect, grep for its shape everywhere, and
  turn the audit into a harness assertion.
- [F3](skills/decoding-method/rules.md#f3) After a pass rewrites the syntax tree, its derived state
  (cached paths, scope bindings, reference sets) must equal what a fresh parse of its output gives.
- [F4](skills/decoding-method/rules.md#f4) When a matcher picks out a role or structure, select it
  by what the program cannot run without, never by how the code is written (names, declarations,
  layout, statement shape, distances, allocated values); a location is identity to whatever jumps to
  it.
- [F5](skills/decoding-method/rules.md#f5) When a defect shows our decoder deciding wrongly, revise
  the code that owns that decision; a special case beside it is a patch the next variant pays again.
- [F6](skills/decoding-method/rules.md#f6) When a pass is shared by several decoders, test it on
  hand-built cases off every decoder's input path, each a shape its producer could hand it from real
  input; its normal form must reach both sides of every comparison.
- [M1](skills/decoding-method/rules.md#m1) When you judge a decode or a design change, read the
  outputs: a passing run proves nothing, and neither does a changed output, or a count of them,
  until it is read.
- [M2](skills/decoding-method/rules.md#m2) When you measure what a decode removed, count what the
  obfuscation left that a decoder can tell apart (characteristic constructs, leftover helpers) and
  compare decoded size with the input's; what no decoder can tell apart and what changes nothing the
  program does is how the code is written, not residue.
- [M3](skills/decoding-method/rules.md#m3) When you build a control or check, make sure it reaches
  the mechanism it names; one that misses still reads as expected.

## Skill directory

Governance and method docs are in the trigger table above.

- Encoders: [javascript-obfuscator](skills/javascript-obfuscator/javascript-obfuscator.md)
  (parser foundation, per-era transformer order, era registry);
  [js-confuser](skills/js-confuser/js-confuser.md) (transform-by-transform AST patterns);
  [js-confuser-vm](skills/js-confuser-vm/js-confuser-vm.md) (VM compiler/runtime order,
  serialization, options).
- Decoder: [decode-js](skills/decode-js/decode-js.md) (Babel and isolated-vm decode passes; the
  VM decoder starts at its [pipeline map](skills/decode-js/pipelines/jsconfuser-vm.md)).
- VM decoding contract: [VM switch boundary](skills/decode-js/vm/switch/vm-switch-boundary.md).
