# Doc Conventions

Read this before writing or editing any skill doc. It says what a package contains (boundaries,
layout, eras), what a doc contains (the three layouts and their sections), and how docs are
written and kept (where facts live, references, revising). `SKILL.md` holds the one-line forms of
these rules; this file holds their detail.

## Project Boundaries

**Project Independence.** Each skill package documents exactly one submodule, in isolation: a
skill file reads the same whichever other submodules exist here, and never cross-references,
assumes or depends on another project's code, coverage or status.

- **One exception: a decoder package may link the encoder it decodes,** since a decode capability
  means something only in terms of what it reverses. It needs a real link; name-only text is not a
  workaround. An encoder package never references a decoder, and decoder↔decoder or
  encoder↔encoder references are forbidden across packages. Sibling docs within one package link
  freely.
- **Comparisons live in a hub study** that hosts every project compared: capability comparisons,
  algorithm-transfer or adoption lineage, readability conclusions, benchmark summaries, and
  statements that one project informed, outperformed or was generalized into another.
- **Reversal lives only in the decoder.** An encoder transform doc never says how to reverse
  itself, because the rule above stops it from ever citing the decoder that would correct the
  claim.
- **A corpus is bounded prior art.** Its experiment-specific scripts are re-derived into an editable
  decoder only after transfer evidence and that decoder's own acceptance gates.

## Package Layout

The layout is ours, built around what the submodule does, and never mirrors its directory tree.

| Part | Encoder package | Decoder package |
|---|---|---|
| Root file `<skill>.md` | parser/AST foundation, a "Skill Layout" section, the pipeline order, an execution-flow diagram | foundation, a "Skill Layout" section, the source layout, the roster of entries |
| Order | in the root file | one doc per entry under `plugins/`; a [pipeline map](#pipeline-map-layout) under `pipelines/` for a target built from modules and transforms |
| Options | `options.md`, `validate-options.md` | none |
| Transforms | `transforms/<name>.md`, one [transform doc](#transform-doc-layout) each | one transform doc per pass or recovery, in a folder per group |
| Modules | helper folders (`utils/`, `templates/`), as [module docs](#module-doc-layout) | `<module>.md` and `<module>/`, beside the transforms that cite them |
| Tests | `tests.md`, where the package has its own fixtures | `tests.md`: how inputs are generated and what the suites prove |

The root file carries the workflow, not the plumbing: plugin APIs, constants, helpers and result
types move into their own files once they would bloat it.

- **Name files and folders for what they own, never for the task that created them.** Task IDs,
  phase numbers and chronology mislead once work moves between tasks. Use a number in a name only
  when it is part of the subject (a protocol version, an opcode) and say so in the doc. A letter
  code is no name either. A rename
  updates executable references and links in the same change.
- **Name a doc for the transform, shape or responsibility, never for a source file.** One concept
  can be one file at one era and two at another, and a file-keyed tree churns where nothing moved
  and stays silent where the shape did. A relocated file is an era-tagged row; only a divergent
  algorithm earns a new doc. The exceptions are stated under
  [Module Doc Layout](#module-doc-layout).
- **One file-to-doc table, where the reverse lookup is hard** (more than one era, or a concept
  spanning directories): `source-map.md`, or the Code layout of a pipeline map where the target has
  one, never both for the same files. It answers which doc covers a source file and which files no
  doc claims. It is generated from the docs' Source sections, or checked against them by grep in
  both directions, never maintained independently.

## Documenting Multiple Eras

An **era** is a maximal version range over which some named thing about an encoder holds still.
Output can identify an era, never an exact version, so eras are the unit.

- **Eras belong to encoder packages.** An encoder package keeps them so that older versions stay
  documented. A decoder package has no eras of its own: it reflects only the decoder repository
  at its pinned commit, and cites an encoder era where that code handles one.
- **The era registry is the single definition.** A package documenting more than one era has a
  `versions.md`; how axes, rows, commits and IDs work is stated at the head of that file.
- **Docs cite era IDs, never inline version ranges.** One registry edit then corrects every citation.
- **An era ID names the signature** (`P-rotate-helper`, `E-fn-wrapped`), never a position (`P1`) or a
  version (`P2.9.6`).
- **Where divergence resolves:**

  | Section | If it differs by era |
  |---|---|
  | Target | Never; a changed purpose is a different transform |
  | Algorithm | Separate doc and code file |
  | Implementation | Era-tagged rows |
  | Later Stages | Era column in the spellings table |
  | Known Quirks | Era-scoped entry |
  | Fixtures | Era column |

  A different algorithm earns its own file; different parameters stay in one, as rows, never as
  prose duplicated per era.

## Transform Doc Layout

A transform doc specifies one pipeline item, a step that reverses or reads an encoder step. Encoder
and decoder docs share this structure so a pair is easy to cross-check. Each section is defined
under [Doc Sections](#doc-sections).

1. Target
2. Algorithm
3. Implementation
4. Later Stages (encoder) / Input Shapes (decoder)
5. Known Quirks (encoder) / Known Gaps (decoder)
6. Source
7. Fixtures

## Module Doc Layout

Code that several transforms use and that reverses or adds no encoder step itself (a VM decoder's
reading of the word stream, an encoder's AST helpers) forms a **module**: a set of files with one
responsibility. A module gets module docs that the transform docs cite. In a good design each
module is kept in its own folder; a folder is not thereby a module. "File" means one source
file. The transforms themselves are not a module and have no module doc.

- **Stated once.** A fact about a module's record or export lives in the module's doc; a transform
  doc links it.
- **Head doc and sub-docs.** The head doc is `<module>.md`. A module with several parts has one
  sub-doc per part under `<module>/`; the head doc then holds sections 1 and 4 and an index, and
  each sub-doc sections 2, 3 and 5 to 7 for its part.
- **What a sub-doc is keyed on.** Where we own the code layout (an editable decoder), the
  responsibility; a sub-doc is never named for a file. In a read-only package, a helper folder
  (`utils/`, `templates/`) is documented as one module although we cannot regroup it by
  responsibility, so its sub-docs are keyed on the source file, against the pinned commit.

1. Target
2. Algorithm
3. Implementation
4. Dependencies
5. Known Gaps
6. Source
7. Fixtures

This is the transform layout with Dependencies in place of Input Shapes: a module receives its
callers' arguments, not shapes from an encoder stage or an earlier pass.

## Pipeline Map Layout

A decoder target built from modules and transforms has a pipeline map, `pipelines/<target>.md`:
the decoder's architecture, how it maps to the encoder steps it reverses, and the index of its
docs. The map owns what holds across docs: the layers, the code layout, the order the drivers run,
the records that cross docs and the refusal protocol. A transform or module doc owns its mechanism
and links the map for the rest, a transform doc from its first line:
`Pipeline stage: <stage> ([map](<path to the map>))`.

| Term | Meaning |
|---|---|
| Layer | One side of the model. The frontend needs knowledge of the encoder: it admits the input, undoes the encoder's steps and converts the program into the model. The backend reads only that model. |
| Driver | A function that decides which pipeline stages run and in what order, and passes records between them. |
| Pipeline stage | One step a driver runs, named in kebab-case for what it does (`read-program`, `recover-control`). Stage names are hub labels; the source names its own functions, and the map's order tables give the function behind each stage. |
| Transform, module | The two kinds of doc below the map, labeled by the doc's filename in backticks (`read-wordcode`); never called a stage, never labeled by a letter. |
| Record | The data one doc's code hands another's, with a named shape. The producer's doc owns the shape; the map lists producer and consumers. |
| Encoder step | One numbered row of the encoder's order table, cited by its number and the name the encoder's code gives the pass (`4 controlFlowFlattening`). |

1. **Target.** What the decoder takes and produces, what it refuses, and its entries.
2. **Layers.** One chart of the whole decode: entries, drivers, layers and the model between them;
   what each layer may know.
3. **Code layout.** The mapping between the hub's names and the code's, naming every file once:
   a modules table (Module | Reads and provides | Sub-docs | Files | Called through), a transforms table
   (Pipeline stage | Transform | Files | Modules used | Called through) and the entries and
   drivers. Then the chart of the
   folders' imports and the rules lint checks on them. Every later section uses these names.
4. **One order section per driver.** The driver's calls in their real order as explanatory
   pseudocode, using the code's names, where stages nest or interleave. Then one chart, a box per
   pipeline stage: solid arrows are the path every input takes, dashed arrows runs that depend on
   a shape, each labeled with its trigger. Then a table, one row per stage in call order: the
   stage, the function behind it, when it runs, what it does and what happens when it cannot.
5. **Records.** Record | Producer | Consumers, one row per record that crosses a doc.
6. **Refusals.** The protocol, the owners, and which codes reach the public result.
7. **Encoder steps each doc undoes or reads.** Pipeline stage | Doc | Undoes | Reads, in pipeline
   order. *Undoes*: removes what the step added. *Reads*: needs the step's output to interpret the
   program. Steps nothing reads are named in prose.
8. **Reversibility by encoder step.** # | Encoder step | Reversal | How, or what is lost. The
   verdict is `reversible` (restored through the named doc, whose Undoes cell lists the step),
   `discarded` (the step changes only the interpreter or decoration, which the decoder drops),
   `irreversible` (information no decoder can restore; "in part" names the part) or `unverified`
   (not yet derived from source).
9. **Doc index.** Doc | Owns, one row per doc of the target.

Each mapping and verdict is derived from the encoder source and the decoder's docs and code
([D2](encoder-decoder-method.md#d2-verify-claims-before-acting-on-them)), never copied from a
doc's claim. Which populations have been shown to recover is evidence, kept in the suites; the map
states only what each step permits.

## Doc Sections

The sections the two layouts above are built from. Both kinds of doc are design specifications:
the intended result, the main algorithm, its components and contracts, and the evidence that would
accept an implementation. They record durable decisions, never task ownership, status or a diary.

A doc stands on its own, without the implementation at hand. It is:

- **Understandable.** It explains the purpose, the main steps and why they preserve behaviour, with
  a readable explanation before the exact specification; precise tables alone do not teach.
- **Behaviourally complete.** It gives the result and the refusal for every documented input form,
  including state effects.
- **Sufficient for reconstruction.** It states every consequential decision, though not source
  text or helper layout. An omitted equation that changes the result is a defect; missing
  knowledge is stated explicitly, never left blank or filled with an invented mechanism.

State the reader's prerequisites, link the package's shared parser/AST and scope foundations
instead of re-teaching them, and explain transform-specific terms in context. Label fenced
pseudocode as explanatory; never put untested runnable code or a copy of the live implementation
in a doc. Where a doc stands in for probes, tools or an implementation that are unavailable, write
it as a build recipe: inputs, naming and interface contracts, prerequisites, and the failure modes
that can falsely report success.

**A record is a code block.** A record shape or literal that is nested or has five or more fields
goes in a fenced block, one field per line where a field carries a note (the note as a comment); the
sentence or table cell names the record rather than spelling it. Short flat records stay inline, and
so do field lists in a table built to compare rows (per-opcode or per-kind fields, outcome matrices),
where a block would break the comparison.

### Target

Lead with the purpose and observable result:

- **Encoder:** the protection added and the behaviour it preserves. Describe the output in the
  encoder's own terms (admission, decline and fixture vocabulary is decoder framing) and, with no
  encoder-local fixture, say so rather than citing decoder evidence.
- **Decoder:** what decoding produces and how that differs from passthrough.
- **Module:** what it reads, what it provides to its users, and what it never does (the limits
  they rely on: "never reads the word stream", "never executes the target").

State the input and output boundaries and the important exclusions, and distinguish a verified
contract from a proposal.

### Algorithm

Explain the solution as a causal progression: what each step learns, why the next needs it, and why
the restrictions preserve semantics. On the decoder side this is the only place a reversal strategy
is asserted. An era divergence here earns a separate doc (Documenting Multiple Eras).

Include an annotated worked example from input through its meaning to output, explaining the
significant operands and intermediate values; mark a synthetic example and what it omits. Use
diagrams where execution, data flow, capture or stage relationships carry the reasoning, and explain
them in prose. One reasoning unit per paragraph; tables for comparisons, with short cells.

### Implementation

The granular design beneath the algorithm: components, input/output contracts, representations and
consequential decisions, enough to derive units, order and tests. A component
need not match a source file. Where the transform uses a [module](#module-doc-layout), name the
module and link the record or export read; the module's doc owns their description. Name every
export another module, test or script imports, verbatim, beside the component it implements, so a
search for a code name finds its doc; internal helpers need not be listed. An export nothing
imports is not interface: in an editable decoder, stop exporting it; in a read-only encoder, leave
it unnamed. Name AST forms to aid verification. Era differences here are tagged rows.

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

### Dependencies

What the module imports, and the one-way rule it keeps.

### Later Stages (encoder) / Input Shapes (decoder)

Where a shape this pass handles comes from, or goes to, outside the pass. The two sides record one
interaction from opposite ends: an encoder doc says what later stages do to its output; a decoder
doc says what it receives that it did not make.

- **Encoder, Later Stages:** what later encoder stages do to this transform's output (a minifier
  moving a store this transform wrote, say), derived from the stage order per era
  ([P1](encoder-decoder-method.md#p1-work-in-reverse-encoder-stage-order-each-stage-placed-by-its-last-write)).
  Record interactions as rows.
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

### Known Quirks (encoder) / Known Gaps (decoder)

Unresolved limitations, with their era once there is more than one. A superseded encoder era's quirk
is permanent and descriptive. A decoder gap is usually fail-closed incompleteness and can close:
state its boundary and missing evidence without turning a guess into a mechanism. When a gap closes,
move its lasting fact into the Algorithm, Implementation or Input Shapes section (if another
pass's shape blocked it, the lasting fact is the producer dependency) and delete the gap. No dates, discovery narrative or before/after figures.

### Source

The file paths, code references and where the pass is wired, citing the section that explains a
forced position. Code references verify the spec; they never hold the only copy of a mechanism.

### Fixtures

The evidence, as one table keyed by scenario: the scenario, its expected result and oracle, and
the committed fixture or control that pins it, named so the mapping greps both ways (an era column
where needed). A scenario with no fixture keeps its row with the cell empty, so the table shows
which claim has no evidence; with no fixtures at all, say so and why.

- **What to cover.** Supported variants, real combined producer output, refusals and negative
  controls, atomicity, cleanup and derived state.
- **What counts.** A decoder recovery assertion must fail for passthrough. A negative control must
  reach the decision it claims to test
  ([M4](encoder-decoder-method.md#m4-a-control-must-reach-its-mechanism)). Synthetic examples test
  the mechanism and real encoder output qualifies admission; neither stands in for the other.
- **A pinned decline is a boundary, not coverage.** A test that expects a valid encoder-produced
  form to decline passes for as long as the decoder fails. Name it in the owning doc's Known Gaps
  with its cause; a change that handles the form first flips the test to expect recovery, so it
  fails before the fix. Damage controls and inputs outside the encoder's grammar keep declining.
- **Before adding a fixture,** search the Fixtures tables and the test tree for one targeting the
  same input and decision, and extend it instead of adding a second.

## Where Facts Live

`SKILL.md` states these rules (gates 5 and 6, the hub rules); this section holds only their detail.

**Durable facts live in skill docs,** in the owning section's own text, never in a parallel
task-documentation tree: a history rebuild rewrites commit messages, and the checkpoint is scratch.
A maintained regression's encoder input is regenerated, not committed: its fixture commits the
source, options and seed, and the test setup regenerates the bytes from the pinned encoder (the
package's `tests.md` says how). Only an input no checked-in recipe reproduces is a committed
fixture, laid out as `tests.md` specifies, with a row in the owning doc's `## Fixtures`. Nothing
outside skill docs, committed tests and tools is cited or depended on, and a claim whose support
is gone is narrowed to a historical result. A fact graduating from scratch into a skill doc leaves
the scratch copy behind in the same change. Before a practice graduates into a cross-project doc,
ask what input made it right here and whether a new project would have that input; the half that
depended on this project's circumstances stays out.

**Executable tools are checked-in files.** A runnable tool lives in the repository of the project
it exercises; a decoder's harness lives in the decoder even when it drives the encoder. The hub
carries specifications, not code; only a tool no single submodule can own (one comparing two
decoders) lives at the hub.

**Task status is not a fact.** Accepted, pending, reviewed, authorized, qualified-by-whom: these
describe a task and live only in `checkpoint.md`. A skill doc states the mechanism, its boundary
and the fixtures that pin it.

**Measured figures are diary.** A number from running something over a corpus (a byte count, a
ratio, "N of M samples") is void once the corpus regenerates; so are counts of the tree itself
(test files, cases, lint errors). Record the axis and the census that reads it: "this census
should read zero" survives, a byte total decays. Where a decision relies on a figure, cite its
recipe with the value (seed, checked-in tool, reachable encoder, decoder and tool commits,
toolchain); for an outcome over a population, prefer a committed census test. A corrected figure
carries the live caveat (a column not comparable with its neighbour, say), not the story of its
correction.

**Git identifies tracked bytes.** No hash sidecar, no hash field in a record describing a tracked
file, and no test, tool or doc comparing a tracked file to a stored digest, inside Git or kept
outside it; identify such inputs by commit and a clean `git status`. A record beside a tracked
file carries only what Git cannot: seed, options, pin, toolchain and observations. A digest is
legitimate only for bytes Git does not hold: a comparison within one run (output against input),
or an untracked artifact's own bytes.

**No machine-local paths.** Name a file relative to its repository root or the citing file. A tool
finds a toolchain through `PATH` or an argument and makes its paths relative before writing a
tracked record; a record names a toolchain by name and version.

## Reference Direction and Form

- **While a target is still edited, a hub doc cites it by plain relative path;** a permalink into a
  moving tree breaks on the next commit.
- **Once the source is frozen, a hub doc cites it by commit-pinned permalink, never a line number.**
  Example:
  [`calculator.ts#L26-L58`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/calculator.ts#L26-L58).
  The pin is the SHA of the era the passage describes: for a single-era package the hub `main`
  gitlink, otherwise the era's registry row. A passage citing the live gitlink describes one commit
  and points at another after the next pin bump. Verify each link resolves before committing
  (`curl -s -o /dev/null -w '%{http_code}'` → `200`).
- **A permalink can only be written once its commit is final.** Where history will be rebuilt:
  rebuild the submodule, take its settled commit IDs, update the hub's references, then rebuild the
  hub.
- **Submodule source never references the hub:** no path, doc name, section title or worklist
  label. A submodule ships alone, so such pointers are unresolvable and rot unseen. State the
  invariant locally, or move it to the doc.

## Revising a Doc

**Revise by evolution, not addition.** A new incident changes an existing item, across files as
well as within one: sharpen it, merge two, or supersede one. State a point once and cite it
elsewhere; drop an entry once its incident teaches nothing the survivors don't. When a doc is long
but nothing in it is redundant, separate what is read every session from what is read only when a
rule is challenged, keyed on the same labels.

**A changed mechanism is rewritten whole.** Its section, or the doc, is written again as one
procedure in execution order, to the layout under [Doc Sections](#doc-sections), never as
amendments in the order they were made. The text alone answers what one step does, in what order,
and why it terminates.

**After a restructure, derive before revising.** When folders, architecture or protocols change,
derive the doc layout from the code as if nothing were documented, compare it with the existing
docs, then revise doc by doc. Fixing links, renamed names and stale rows is the end check; alone,
it leaves the docs describing the old relationships.
