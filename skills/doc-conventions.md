# Doc Conventions

Read this before writing or editing any skill doc. It says where a fact may be written, how a
package is laid out, how a transform doc is structured, and how a reference crosses between the hub
and a submodule. `SKILL.md` holds the one-line forms of these rules; this file holds their detail.

## Project Boundaries

**Project Independence.** Each skill package documents exactly one submodule, in isolation. Never
cross-reference, assume or depend on another project's code, coverage or status: a skill file
should read the same whichever other submodules exist here. Cross-project observations belong in a
hub study that hosts every project being compared, never in one participant's package. For two
decoders this includes capability comparisons, algorithm-transfer or adoption lineage, readability
conclusions, benchmark summaries, and statements that one informed, outperformed or was generalized
into the other. A decoder package documents only its own mechanism and verified boundary, and never
names, links, summarizes or depends on another decoder.

- **Exception, decoder → encoder only.** A decoder package may link the encoder it decodes, since a
  decode capability means something only in terms of what it reverses. An encoder package never
  references a decoder, and decoder↔decoder or encoder↔encoder references stay forbidden across
  packages (sibling docs within one package link freely). The exception needs a real link;
  name-only text is not a workaround for a forbidden reference.
- **Reversal lives only in the decoder.** An encoder transform doc never says how to reverse
  itself, because the rule above stops it from ever citing the decoder that would correct the
  claim. Two such claims already needed correcting: one predicted an execution order the real
  decoder disproved, one called three normalizations "not applicable" to reverse when they were
  simply unreversed.
- **A corpus is bounded prior art.** Its experiment-specific scripts are re-derived into an editable
  decoder only after transfer evidence and that decoder's own acceptance gates.

## Where Facts Live

**Durable facts live in skill docs.** Never park the only copy of a fact in a commit message or
`checkpoint.md`: a history rebuild rewrites messages, and the checkpoint is scratch. The durable
copy is a skill doc's own text, in its owning section, never a parallel task-documentation tree.
Exact bytes a maintained regression needs (a randomly generated encoder sample, say) are a committed
fixture in the code repository, laid out as its package's `tests.md` specifies, with a row in the
owning doc's `## Fixtures` and no recorded hash. Anything else is regenerated from a pinned or
pushed commit and a checked-in tool. Nothing outside skill docs, committed tests and tools is cited
or depended on, and a claim whose support is gone is narrowed to a historical result.

**Task status is not a fact.** Words such as accepted, pending, reviewed, authorized or
qualified-by-whom describe a task. They live only in `checkpoint.md` and never enter a skill doc,
which states the mechanism, its boundary and the fixtures that pin it.

**Measured figures are diary.** A number produced by running something over a corpus (a byte count,
a ratio, "N of M samples") is void once the corpus regenerates, and obfuscator corpora regenerate
routinely. A skill doc records the axis and the census that reads it, never the value: "this census
should read zero" survives, a byte total decays. The same holds for counts of the tree itself (test
files, cases, lint errors). A figure counts only if it is reproducible: a recorded seed, a checked-in
tool, reachable encoder, decoder and tool commits, and a stated toolchain. Where a decision relies on
one, cite that recipe with the value; for an outcome over a population, prefer a committed census
test. A corrected figure carries the live caveat (a column is not comparable with its neighbour,
say), not the story of its correction; that goes in the commit message.

**Git identifies tracked bytes.** In the hub and every submodule a tracked file's identity is its
Git history, never a recorded hash: no hash sidecar, no hash field in a record describing a tracked
file, and no test, tool or doc comparing a tracked file to a stored digest. A record beside a
tracked file carries only what Git cannot: seed, options, pin, toolchain and observations. A digest
is legitimate only for bytes Git does not hold: a comparison within one run (output against input),
or an untracked artifact's own bytes. A record kept outside Git that stores digests of tracked files
for a later run to compare is the same violation; identify those inputs by commit and a clean
`git status`.

**No machine-local paths.** No tracked file records an absolute machine path (`/Users/…`,
`/home/…`, `/opt/…`, `C:\…`): it is unreachable elsewhere and exposes the author's environment. Name
a file relative to its repository root or the citing file. A tool finds a toolchain through `PATH`
or an argument and makes its paths relative before writing a tracked record; a record names a
toolchain by name and version.

## Revising a Doc

**Revise by evolution, not addition.** A new incident changes an existing item, across files as
well as within one: sharpen it, merge two, or supersede one. State a point once and cite it
elsewhere; drop an entry once its incident teaches nothing the survivors don't. A doc that grows by
one entry per incident stops being read. When a doc is long but nothing in it is redundant, separate
what is read every session from what is read only when a rule is challenged, keyed on the same
labels; that is how the method's rules and incidents are split.

## Package Layout

**Name files and folders for what they own, never for the task that created them.** Task IDs, phase
numbers and chronology mislead once work moves between tasks. Use a number in a name only when it is
part of the subject (a protocol version, an opcode) and say so in the doc. A rename updates
executable references and links in the same change.

**The layout is ours, built around the components every encoder has:** order, options, transforms,
templates. It never mirrors the submodule's directory tree; where the two need relating, use a
mapping (below). `skills/js-confuser/` is the reference: the root file carries the pipeline order,
`options.md` and `validate-options.md` the option surface, `transforms/<name>.md` one per transform,
`templates/<name>.md` plus `template-engine.md` the templates.

**The root file carries the workflow, not the plumbing.** Name it after the skill (`js-confuser.md`).
It covers the parser/AST foundation, the package's own layout in a "Skill Layout" section, the
pipeline order and an execution-flow diagram. Option surfaces, plugin APIs, constants, helpers,
templates and result types move into their own files once they would bloat the root.

- **Name a doc for the transform or shape, never for a source file.** One concept can be one file at
  one era and two at another (a rotate function is a code helper at 2.9.6, and a helper plus a
  transformer in another directory by 2.19.0), so a file-keyed doc must be renamed or split for
  reasons unrelated to its subject.
- **Source-tree mirroring applies only inside large helper folders** (`utils/<name>.md`,
  `templates/<name>.md`): one file per source file, flat, against the pinned commit.
- **Structural drift and shape drift are independent.** Across `2.15.3 → 2.15.4` of one obfuscator
  no file is added, removed or renamed, yet every modified file is a string-array helper and the
  decoder distinguishes two wrapper shapes there. Across `2.18.1 → 2.19.0` the file set moves in
  three places, none string-array, while the string-array transformers change in place. A
  file-keyed tree churns where nothing moved and stays silent where the shape did. (Measured with
  `git diff --name-status --diff-filter=ADR` against `--diff-filter=M`; "changes zero files" means
  the file set, not the contents.)
- **A moved file never splits a doc.** A relocation is an era-tagged row; only a divergent algorithm
  earns a new file (Documenting Multiple Eras).

### The source map, where one is necessary

`source-map.md` lists one row per submodule source file, the doc that claims it, and the era where
those differ. It is required only when the reverse lookup is otherwise hard: a package with more
than one era, or a concept spanning directories. It answers what per-doc `## Source` sections
cannot: which doc covers a given source file, and which source files no doc claims. Each doc keeps
its own `## Source`, and the map is verified by grep against those sections in both directions,
never maintained independently; a map that drifts silently is worse than none.

## Transform Doc Layout

A transform doc is a design specification: the intended result, the main algorithm, its components
and contracts, and the evidence that would accept an implementation. It must stay useful when the
implementation is unavailable. Encoder and decoder docs share the numbered structure below so a pair
is easy to cross-check; `## Source` and `## Fixtures` close the doc, in that order.

Write for three readers: a newcomer learning the algorithm without opening source; a product manager
deriving an implementation plan from components, dependencies and acceptance criteria; an agent
drafting a runnable proof of concept for an unfamiliar sample. A proof of concept is an experiment;
it does not establish that the sample is supported. A design records durable decisions, never task
ownership, status or a diary.

State the reader's prerequisites (functions, arrays, control flow, basic VM concepts where
relevant). Link the package's shared parser/AST and Babel scope/binding foundations instead of
re-teaching them, and explain transform-specific terms in context. Put a readable explanation before
the exact specification.

| Quality | The doc must let a reader |
|---|---|
| Understandable | Explain the purpose, main steps and why they preserve behaviour |
| Behaviourally complete | Determine the result and refusal for every documented input form, including state effects |
| Sufficient for reconstruction | Implement the consequential decisions without the unavailable implementation |

Reconstruction need not reproduce source text or helper layout. A readable summary is not enough if
an omitted equation changes the result, and precise tables alone do not teach the algorithm. State
missing knowledge explicitly; a blank or an invented mechanism is not a spec.

**Validating a revision of this guideline.** Apply it to one new doc written by someone given only
the instructions, the guideline and the target. An independent reviewer reads the guideline and that
doc before opening source, and attributes each defect to a missing requirement, an unclear
instruction, writer noncompliance or a source/evidence gap. Only the first two change the guideline.
One pilot shows the guideline conveyed its requirements for that doc, nothing broader.

### 1. Target

Lead with the purpose and observable result. Encoder: the protection added and the behaviour it
preserves. Decoder: what decoding produces and how that differs from passthrough. State the input
and output boundaries and the important exclusions, and distinguish a verified contract from a
proposal. An encoder doc describes its output in the encoder's own terms (admission, decline and
fixture vocabulary is decoder framing) and, with no encoder-local fixture, says so rather than citing
decoder evidence.

### 2. Algorithm

Explain the solution as a causal progression: what each step learns, why the next needs it, and why
the restrictions preserve semantics. On the decoder side this is the only place a reversal strategy
is asserted. An era divergence here earns a separate doc (Documenting Multiple Eras).

Include an annotated worked example from input through its meaning to output, explaining the
significant operands and intermediate values; mark a synthetic example and what it omits. Use
diagrams where execution, data flow, capture or stage relationships carry the reasoning, and explain
them in prose. One reasoning unit per paragraph; tables for comparisons, with short cells.

### 3. Implementation

The granular design beneath the algorithm: components, input/output contracts, representations and
consequential decisions, enough for a product manager to derive units, order and tests. A component
need not match a source file. Name every function a component's module exports, verbatim, beside the
component it implements, so a search for a code name finds its doc; internal helpers need not be
listed. Name AST forms to aid verification. Era differences here are tagged rows.

- **Components and representations.** What each consumes and produces, which invariants its consumer
  relies on, and why the order matters. Define fields, operands, indexes, units, numeric
  interpretation and binding/capture relationships where they affect the result. The normative chain
  closes in docs and declared contracts, never only in code.
- **Decisions and boundaries.** Pseudocode and equations for nontrivial recognition, recovery and
  emission. Exact constants, thresholds, operand and update order, coercions, widths. "Mix the
  state" is not enough when different formulas give different programs. Explain each restriction.
  Tabulate supported and rejected input forms with AST spellings, eras, reasons and behaviour. Never
  infer broad option or version coverage from one success.
- **Atomicity.** A matched unit recovers completely or stays untouched ([F2](encoder-decoder-method.md#f2-resolve-completely-or-not-at-all)). State when retry is
  possible and how intermediate mutations are avoided or rolled back; define any partial boundary.
  Distinguish no candidate, recognized-but-unsupported, and recovered where a caller acts on the
  difference; uncertain recognition stays a hypothesis.
- **Output, state and cleanup.** Define the emitted output and the derived state later components
  read, which operation updates it and the invariant restored ([F3](encoder-decoder-method.md#f3-keep-tree-and-derived-state-consistent)); which consumed helpers are
  removed, what survives, and when cleanup is safe.
- **Testing and acceptance.** Map scenarios to observed results and oracles, acceptance criteria and
  committed fixtures or controls (columns: scenario, oracle, criterion, fixture), with era columns
  where needed. A decoder recovery assertion must fail for passthrough. Cover supported variants,
  real combined producer output, refusal and negative controls, atomicity, cleanup and derived state.
  A negative control must reach the decision it claims to test ([M4](encoder-decoder-method.md#m4-a-control-must-reach-its-mechanism)). Synthetic examples test the
  mechanism; real encoder output qualifies admission; neither stands in for the other.

### 4. Later Stages (encoder) / Input Shapes (decoder)

Where a shape this pass handles comes from, or goes to, outside the pass. The two sides record one
interaction from opposite ends: an encoder doc says what later stages do to its output; a decoder
doc says what it receives that it did not make.

- **Encoder, Later Stages:** what later encoder stages do to this transform's output (a minifier
  moving a store this transform wrote, say), derived from the stage order per era
  ([P1](encoder-decoder-method.md#p1-work-in-reverse-encoder-stage-order-each-stage-placed-by-its-last-write)). Harvest a
  source-verified fact from a decoder bug writeup, but keep decoder references out of the encoder
  package. Record interactions as rows.
- **Decoder, Input Shapes:** every shape in this pass's input that the pass did not make: what
  encoder stages left there (and what later encoder stages made of it), and what our earlier passes
  emitted. Each row names its producer, encoder stage or our pass. Encoder order says which encoder
  residue remains, not which shapes our own pipeline emits. State the interface and gate each
  shape affects, and explain any forced schedule in the numbered design.
- **Home rule.** The affected pass owns the dependency and what its gates do with it; the producing
  pass owns one inventory of emitted shapes that consumers link to.
- **Spellings table.** Accepted spellings, producing pass, whether ours or the encoder's, and era.
  Write the row when the branch is written. Example:
  [decode-js/visitors/jsconfuser/dispatcher.md](decode-js/visitors/jsconfuser/dispatcher.md).
- **Remedy is a separate decision.** An encoder's effects can only be accommodated. For a shape our
  own pass emits, prefer fixing the producer ([D4](encoder-decoder-method.md#d4-fix-the-producer-not-the-consumer)).

### 5. Known Quirks (encoder) / Known Gaps (decoder)

Unresolved limitations, with their era once there is more than one. A superseded encoder era's quirk
is permanent and descriptive. A decoder gap is usually fail-closed incompleteness and can close:
state its boundary and missing evidence without turning a guess into a mechanism. When a gap closes,
move its lasting fact into items 2–4 (if another pass's shape blocked it, the lasting fact is the
producer dependency) and delete the gap. No dates, discovery narrative or before/after figures.

### Closing evidence sections

**`## Source` then `## Fixtures`, both required and unnumbered.** Source gives the file path, code
references and where the pass is wired, citing the numbered item that explains a forced position.
Code references verify the spec; they never hold the only copy of a mechanism.

Fixtures maps each committed fixture to the claim it pins, named so the mapping greps both ways; use
a table once there are more than a few, with an era column where needed. Link back to the testing
scenarios so the table shows which claim has no evidence. With no fixtures, say so and why; proposed
criteria without fixtures stay unverified. Before adding a fixture, search the Fixtures tables and
the test tree for one targeting the same input and decision, and extend it instead of adding a
second.

## Marking something done

**Marking a step done means re-reading every place that names it.** A status lives in a table, a
summary line and an action list at once, and updating one leaves the others asserting the opposite;
this is the most repeated mistake here. Grep for the step's identifier before committing. A fact
graduating from scratch into a skill doc leaves the scratch copy behind in the same commit. The same
holds for open questions: an answered item left in a worklist reads like an open one and is
re-opened at full price, so grep the packages for an item's subject before working it ([D1](encoder-decoder-method.md#d1-read-the-tree-and-its-docs-before-you-probe-or-propose)).

## A Doc That Replaces an Artifact

Where a doc stands in for unavailable probes, tools or an implementation, write it as a build recipe:
inputs, naming and interface contracts, prerequisites, and the failure modes that can falsely report
success. Separate generic prerequisites and supplied infrastructure from the algorithm the reader
must rebuild. A deleted draft or former implementation is not a dependency; its knowledge must
survive in the spec.

**Cold rebuild.** Declare the allowed docs and dependencies first and keep the unavailability
boundary; if it cannot be kept, narrow the claim. Freeze the rebuilt artifact and its results before
comparing with a reference, so corrections stay distinguishable from independent reconstruction.
Check actual recovery, refusal and state consistency, not just execution. Use it when a new recipe or
a substantive mechanism change makes reconstruction part of acceptance; editorial fixes do not need
one. A rebuild proves neither novice readability nor admission of real encoder output; any reconstruction
claim states its participants, permitted resources and tested boundary, and affected checks repeat
after corrections. Once its
findings graduate into their owning sections it is retired, and claims citing it become historical.

**Executable tools are checked-in files; pseudocode belongs in the design.** A runnable tool lives in
the repository of the project it exercises; a decoder's harness lives in the decoder even when it
drives the encoder. The hub carries specifications, not code; only a tool no single submodule can own
(one comparing two decoders) lives at the hub. Label fenced pseudocode as explanatory, and never
bury untested runnable code or duplicate live implementation in a doc.

## Documenting Multiple Eras

An **era** is a maximal version range over which some named thing about the encoder holds still.
Output can identify an era, never an exact version, so eras are the unit throughout.

- **Two levels of change.** Global change (which stages run, in what order) has one axis for the
  whole encoder. Local change (one transform's algorithm rewritten) has one axis per component; a
  single global timeline would shift every doc's era for reasons unrelated to its subject. A
  component with no axis is unstudied, not unchanged.
- **Per-component axes make partial verdicts possible.** A sample whose option was off says nothing
  about that transform, so its era there is unknown, not wrong. A sample's version range is the
  intersection of its per-component verdicts.
- **The era registry is the single definition.** A package documenting more than one era has a
  `versions.md` with one table per axis, in version order: era ID, version range, verified commit SHA,
  signature. A row never spans axes; a coincidence between axes is written in prose.
- **The registry states version → shape; a detector reads shape → version,** which is not a function,
  because an encoder can revert a change. A detector's verdict per axis is the union of ranges
  consistent with what matched, and the sample's range is the intersection across axes. So two
  same-shape eras stay separate rows; merging them makes a false hull or a non-range. If two eras
  would share a signature name, either find the difference the signature missed or record that the
  axis cannot separate them. The era↔decoder mapping is documentation, not code: item 3 rows in the
  decoder doc, grep-checked both ways against the registry.
- **Docs cite era IDs, never inline version ranges.** One registry edit then corrects every citation.
- **An era ID names the signature** (`P-rotate-helper`, `E-fn-wrapped`), never a position (`P1`) or a
  version (`P2.9.6`). Ordinal IDs renumber whenever an era is found between two others; version IDs
  lie once a boundary moves.
- **An era's SHA is the commit its claims were verified against,** not the current pin; it moves only
  on re-verification, which lets a package describe shapes the current source no longer has.
- **Where divergence resolves:**

  | Item | If it differs by era |
  |---|---|
  | 1. Target | Never; a changed purpose is a different transform |
  | 2. Algorithm | Separate doc and code file |
  | 3. Implementation | Era-tagged rows |
  | 4. Effects | Era column in the spellings table |
  | 5. Quirks/Gaps | Era-scoped entry |
  | `## Fixtures` | Era column |

  A different algorithm earns its own file; different parameters stay in one, as rows, never as
  prose duplicated per era.

## Reference Direction and Form

- **Submodule source never references the hub:** no path, doc name, section title or worklist label.
  A submodule ships alone, so such pointers are unresolvable and rot unseen (one pass removed 46
  from `decoder/decode-js`). State the invariant locally, or move it to the doc.
- **A hub doc citing frozen submodule source uses a commit-pinned permalink, never a line number.**
  Example:
  [`calculator.ts#L26-L58`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/calculator.ts#L26-L58).
  The pin is the SHA of the era the passage describes: for a single-era package the hub `main`
  gitlink, otherwise the era's registry row. There is no "current era" exemption: a passage citing
  the live gitlink describes one commit and points at another after the next pin bump. Verify each
  link resolves before committing (`curl -s -o /dev/null -w '%{http_code}'` → `200`).
- **While a target is still edited, use plain relative paths;** a permalink into a moving tree breaks
  on the next commit. Convert to permalinks once the source is frozen at a release commit.
- **A permalink can only be written once its commit is final.** Where history will be rebuilt:
  rebuild the submodule, take its settled commit IDs, update the hub's references, then rebuild the
  hub.
