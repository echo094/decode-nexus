# Checkpoint — javascript-obfuscator study

Working notes for the `docs-javascript-obfuscator` hub branch. **Not a skill doc** — scratch
tracking only: status, decisions, pointers, open questions. Per `SKILL.md` the only copy of a
fact never lives here; anything settled graduates into a skill doc and is pruned from this
file.

Scope spans `encoder/javascript-obfuscator` (read-only) and `decoder/decode-js` (editable),
per the decoder→encoder exception in `SKILL.md`.

**Status: 2026-08-08.** Design complete, hazards retired, phase 1 detailed to executable steps
(F1–F5, U1–U7, Acc in §1) — **not started; F1 is next**. Three commits on this branch, all
`hub`-scoped and unpushed: `d58ecf5` and `852b0b9` (the package-layout convention) and `344b148`
(this file). **No submodule has been touched and no branch cut inside one** — that is F5, and
it carries the `decode-js` sync decision. Full history at the end of this file.

---

## 1. Next actions

Each phase is an era-slice taken **end to end**, and the three behaviors — study the encoder,
verify the existing plugin, write the new decoder — combine **inside each step**, not as
sequential stages (§4.1). Phases 2 and 3 enlarge coverage the same way.

1. **Phase 1** — §4.2. The 2.x eras. **F1 is next.**
2. **Phase 2** — §4.3. The 5.5.0 pin, built via `git archive` out of the submodule.
3. **Version derivation** — §4.5, then phase 3.

### Phase 1 steps

A small foundation, then vertical units. Each names its exit criterion; nothing proceeds past a
step whose criterion is unmet.

| # | Step | Exit criterion |
|---|---|---|
| **F1** | Encoder package root file — foundation, **stage order**, flow diagram, Skill Layout; plus `source-map.md` (§6.2) | the unit order below is derivable from it, not asserted; every `src/` file is either claimed by a doc or listed as unclaimed |
| **F2** | Each version's option surface — probe *and* per-tag source (§8.2, §8.5) | every option name the matrix uses confirmed *known* at every version it is used at |
| **F3** | Three input fixtures; 13 per-feature sets + the 3 shipped preset tiers (§7.5) | tier contents read per version from source, subset semantics not assumed |
| **F4** | Freeze the corpus — 8 × 16 × 3 = 384 samples | frozen; nothing compares across a re-encode |
| **F5** | Sync decision, branch **inside** the submodule, run-harness skeleton | one cell end to end; oracles 1–4 and 6 report |
| **U1** | Normalization — escape sequences, statement/declaration merging, if-simplification | the late-minifier spellings W1 names are handled before any shape matcher runs |
| **U2** | String array — array, rotate function, era detection, first `versions.md` rows | §5.5's names fixed against real output; each 2.x era decodes |
| **U3** | String-array wrappers — scope calls wrapper, string-array control flow | the shape §5.5 has no name for is named and decoded |
| **U4** | Converting — object keys, member expressions, `SplitString`, numerical expressions | and the `decodeObject`-ordering discrepancy is resolved from source |
| **U5** | Control-flow flattening | its census reads zero on its own cells |
| **U6** | Dead-code injection | census says what "done" means for a partly irreversible transform |
| **U7** | Custom code helpers — self-defending, debug protection, console output, domain lock | the strippers, without the interval hang (§8.3) |
| **Acc** | Integrated preset study — assemble the workflow **from scratch**, then climb the ladder | combined cells pass, not only the per-feature ones; the order is justified from §8.6, not inherited |

Every **U** step runs the same seven-part loop (§4.2): keep-or-fork decision → encoder doc →
census defined from it → verify the existing plugin on those cells → `obfuscatorx` pass +
decoder doc → fixtures from the encoder's own test cases → pause, commit, clear context.

**Carry forward:** the shape names in §5.5 are provisional — derived from the decoder's
*description* of those shapes, not from output anyone has looked at. U2 fixes them against real
samples before anything is named on disk.

## 2. Main target

**Design a version-aware decoder for javascript-obfuscator.** Not a patch and not a survey: a
new decode-js entry whose architecture is multi-era by construction — it **detects** which
encoder era produced a sample, then **decodes with that era's strategy**. The doc layout
carries the same multi-era shape. **The phases (§4) each deliver a slice of this target** —
verify, document the encoder, build the decoder — rather than auditing ahead of a separate build.

**Downstream requirement (user):** the result feeds a future js-confuser study, so the
*architecture* must generalize beyond this encoder. That has a Project Independence
consequence — see §6.1.

## 3. Settled decisions

### 3.1 A new entry, not a patch — `obfuscatorx`

The existing `obfuscator` plugin is widely used in the community, so changing it in place
risks breaking people who depend on its behavior. The study's output is an **additive** new
entry; **the existing entry is left untouched**, and fixes land in the new one. This
supersedes the earlier "repair vs. doc-only" question — it is neither.

CLI target `-t obfuscatorx`. A version suffix was ruled out: precedent (`sojson`/`sojsonv7`)
puts the *encoder's* version in the suffix, but this entry's coverage is the phase-1 2.x eras
**plus** 5.5.0 with 3.0.0–4.2.2 absent — non-contiguous and deliberately growing. Any single
version in the name would misdescribe it and go stale once phase 3 extends coverage.
`obfuscatorx` makes no version or generational claim.

**Cost of an entry (verified):** `src/main.js` is a flat registry and a plugin is just a
`(sourceCode) => code | falsy` function (falsy → "Purification failed; no output written").
Adding one means a file in `src/plugin/`, an import, one map key, an npm script alongside
`deob`/`dejsc`, and a README row.

### 3.2 Structure: follow the jsconfuser pattern

Verified — the two existing plugins sit at opposite ends:

- `plugin/obfuscator.js` imports **11 shared flat visitors** and keeps every
  obfuscator-specific detector (`stringArrayV0/V2/V3`, `decodeObject`, `purifyCode`,
  `unlockEnv`, the anti-tamper visitors) **inline in one large file**. No `visitor/obfuscator/`
  exists.
- `plugin/jsconfuser.js` imports **4 shared flat visitors** plus ~20 from
  `visitor/jsconfuser/`, one per transform.

jsconfuser is the refactored shape, obfuscator the legacy monolith. `obfuscatorx` follows
jsconfuser: a thin plugin file plus a new `src/visitor/obfuscator/`.

### 3.3 Visitor reuse — by behavior, not by text

The reuse surface is the plugin-agnostic shared visitors `obfuscator.js` already imports:
`calculate-constant-exp`, `delete-illegal-return`, `delete-unused-var`, `lint-if-statement`,
`merge-object`, `parse-control-flow-storage`, `prune-if-branch`, `remove-control-flow-ob`,
`split-assignment`, `split-sequence`, `split-variable-declaration` (plus `plugin/eval.js` for
the packer path).

**Reuse means importing them unchanged.** The moment `obfuscatorx` needs one to *behave*
differently it gets forked into `visitor/obfuscator/`, never modified in place — a shared
visitor's behavior change reaches every plugin including jsconfuser. Extracting logic *out of*
`plugin/obfuscator.js` into shared files is likewise forbidden: that modifies the widely-used
plugin, which is the thing §3.1 exists to avoid. Obfuscator-specific logic is rewritten, not
lifted.

### 3.4 Detection separated from decoding

Verified — the existing plugin fuses them. `decodeGlobal` is a try-in-order fallback
(`stringArrayV3` → `V2` → `V0`) and each `stringArrayVn` both fingerprints *and* extracts in
one pass. Consequences:

- A fingerprint miss is **indistinguishable from "no string array present"** — all three paths
  converge on `Cannot find string list!` → `return false`, aborting the whole plugin. An
  unobfuscated file, an unknown-era sample, and a known-era sample whose fingerprint drifted
  report identically.
- No way to emit the diagnostic a community user actually needs: *"this looks like 2.15-era,
  but extraction failed."*
- Adding an era means editing the fallback chain every existing user depends on.

**Shape:** `detect(ast) -> { era, signals, confidence }`, then `strategies[era].decode(ast)`. A
new era is a new file plus a registry row — additive, the same property that motivated §3.1.

### 3.5 Era, not version

Emitted output cannot identify an exact version, only an **era**: a maximal version range
emitting the same shape. So the version derivation (§4.5) is an *architectural* input — its
output **is** the era list the detector must distinguish.

Detection is **multi-signal** (string-array wrapper shape, option-artifact shapes such as
post-3.2.0 `stringArrayCallsTransform`, helper templates, codegen quirks) so it can yield a
confidence and degrade gracefully rather than falling through silently.

**Confounder:** options confound version — the same version with rotate disabled emits the V0
shape. The verdict space is **(era × options-profile)**, not era alone. This is the same fact
as "`stringArrayV0` is not a version," restated at the architecture level.

### 3.6 Three architecture decisions

1. **Coverage scope.** `obfuscatorx` covers the versions verified in phases 1 and 2. Extending
   to phase 3 is decided when phase 3 is reached. Initial coverage is therefore
   **non-contiguous** — phase-1 2.x eras plus the 5.5.0 pin, 3.0.0–4.2.2 absent — and the
   detector must treat that gap as **unknown**, never interpolate across it.
2. **Shared visitors: reuse while behavior is unchanged.** See §3.3.
3. **Inconclusive detection: refuse with a diagnostic.** No try-all-and-pick-best. The entry
   reports which signals matched, the nearest era, and why it was rejected, then declines.
   - A deliberate behavior *difference* from the existing plugin, whose silent fallthrough is
     what makes its failures unreadable.
   - Acceptable **only because** the existing entry remains for best-effort users. This
     decision and §3.1 hold each other up.
   - Fits `main.js`'s contract (falsy already prints "Purification failed"), so the diagnostic
     must come from the entry itself, via `src/utility/logger.js` rather than bare
     `console.error`.

## 4. The plan

### 4.1 Phase structure — each phase is an era-slice taken end to end

**A phase is not a verification exercise.** It is one slice of era coverage carried all the way
through — study the encoder, verify the existing plugin, write the new decoder — and phases 2
and 3 enlarge coverage the same way, doc and decoder together. The **boundary** between phases is
what decode-js claims, not the content of a phase. That is what §3.6.1 means by "`obfuscatorx`
covers the versions verified in phases 1 and 2": each phase *produces* coverage, it does not
merely audit it.

**The three behaviors combine inside each step, they are not three sequential stages.** A phase
is a small foundation plus a series of **vertical unit steps**, each of which studies the encoder
for its unit, verifies the existing plugin on it, writes the `obfuscatorx` pass, builds fixtures,
and commits. The unit loop is stated once in §4.2 and not repeated per unit.

Three reasons, each of which a stage-split violates:

- **Each behavior alone is unfalsifiable.** An encoder doc written from reading is a hypothesis
  until something inverts it (T8). A verification verdict rests on the residue census, and S4
  rules out runtime correctness as a substitute — so oracle 5 *is* the verdict. And a fixture
  pins **a claim** (`doc-conventions.md`), so fixtures built before the claims exist are a name
  inventory.
- **A census written before the encoder study is defined by the thing under test.** §7.6's
  oracle 5 counts "string-array/wrapper artifacts" — a subject list that, before the encoder is
  read, can only come from §5.5's provisional names, which are the decoder's own prose. Verifying
  first makes the verdict circular.
- **Anything else forces a rewrite backwards.** A stage's output is only provisional until the
  next stage tests it, so a late finding invalidates a large body of already-written docs. This
  file has been rewritten wholesale twice for exactly that (§13, entries 5 and 16).

**Ordering rationale across phases** is unchanged: a phase-1 failure is *interpretable* — it
means the problem is not version drift, and a phase-2 failure afterwards cannot be read as a
version finding at all. Starting at the pin would lose that.

### 4.2 Phase 1 — the 2.x eras, end to end

Slice boundary: every detector branch decode-js claims below the pin.

decode-js declares **no javascript-obfuscator version anywhere as a dependency**:
`package.json` has no such dep or devDep, and the README's `obfuscator` section lists covered
*features* (stringArray incl. Rotate/Wrappers/ChainedCalls, deadCode, controlFlowFlattening
switch, transformer, customCode) with **no version range at all** — unlike its `jsconfuser`
section, which states one.

The only version claims in the project are those encoded in `src/plugin/obfuscator.js`: the
`version: 0/2/3` markers and the boundary comments. Phase 1 samples each at its **low
boundary** (where a `>=` vs `>` off-by-one surfaces) and its **high end** (just below the next
branch):

| Detector branch | Claimed range | Low boundary | High end |
|---|---|---|---|
| `stringArrayV2`, rotate fp2 | `< 2.10.0` | — | `2.9.6` |
| `stringArrayV2`, fp1 + wrapper `< 2.12.0` | `[2.10.0, 2.12.0)` | `2.10.0` | `2.11.1` |
| `stringArrayV2`, wrapper | `[2.12.0, 2.15.4)` | `2.12.0` | `2.15.3` |
| `stringArrayV2`, wrapper | `[2.15.4, 2.19.0)` | `2.15.4` | `2.18.1` |
| `stringArrayV3` | `>= 2.19.0` (open-ended) | `2.19.0` | — (phase 2) |
| `stringArrayV0` | no rotate function present | options axis, not a version | |

- **`stringArrayV0` is not a version.** It is the "no rotate function present" case, reachable
  at *any* version by disabling rotate — an **options** row exercised across phase 1's
  versions, not a version of its own.
- **V3's range is open-ended**, so it also covers 5.5.0 by its own terms. Phase 1 tests its low
  end, phase 2 its high end: one claim, two phases.

**F — Foundation.** The only work that cannot be done per unit, kept deliberately small. It ends
with a frozen corpus and a branch, and nothing about any single transform.

#### F1 — The package root file and the stage order

`skills/javascript-obfuscator/javascript-obfuscator.md`, per `SKILL.md`'s Root File Scope:
parser/AST foundation, a **verified** source-tree layout, the pipeline/stage order, and an
execution-flow diagram. Everything else moves into its own file once it would bloat the root,
indexed from a "Skill Layout" section.

**The layout is keyed on components — order, options, transforms, templates — not on the
encoder's directories (§6.2)**, and this package needs a `source-map.md` because it is multi-era
and at least one concept spans directories — both triggers the convention names.

It is first because T1 orders every later unit from the encoder's stage order — the unit sequence
below *is* that order, reversed, and cannot be written before it. §8.6's finding is the
substance: the flat `nodeTransformersList` is **not** the execution order; order comes from the
`NodeTransformationStage` sequence plus a per-stage topological sort over declared dependencies.
That currently exists only in this scratch file, which `SKILL.md` says must never hold the only
copy of a fact. Derive it **per era**, not once — a transformer's declared dependency can change
with no trace in the CHANGELOG or the list, which is exactly how an ordering drifts unnoticed.

#### F2 — Each version's option surface

Two independent readings, because reading and probing find different classes of thing (T8):

- **Probe** — the wrong-type enumerator in §8.2, over every option name the matrix wants at every
  one of the eight versions. Answers "does this build accept this name".
- **Source** — `git show <tag>:src/options/Options.ts`, per version. Answers what the option
  *means* and what values it takes, which the probe cannot see.

The second reading is available only because the npm↔tag provenance is proven (§8.5): the
submodule's history is a legitimate source for **every** phase-1 version, not just the pin.

#### F3 — Input fixtures and option sets

Three small self-reporting sources, each printing deterministic lines so runtime equivalence is
an exact stdout comparison. Between them they cover the five axes §7.5 requires:

| fixture | exercises |
|---|---|
| `strings` | string literals, concatenation, member reads — the string-array's own input |
| `control` | branches, a loop, a `switch` — control-flow flattening and dead-code injection |
| `objects` | object literals, computed member access, closures — transformer/`SplitString` |

All thresholds forced to `1`, never a probability (T5 step 2); every set pins the same `seed`
(§7.4). Thirteen per-feature sets — `baseline`, `no-rotate`, `wrappers-variable`,
`wrappers-function`, `chained-calls`, `encoding-base64`, `encoding-rc4`, `dead-code`, `cff`,
`self-defending`, `debug-protection`, `debug-protection-interval`, `console-output`.

**The combined sets are the encoder's own shipped presets, not a mix we invent.** The method doc
is explicit: when an obfuscator ships named complexity tiers, climb *that* hierarchy as the combo
ladder. javascript-obfuscator ships four — `default`, `low-obfuscation`, `medium-obfuscation`,
`high-obfuscation` (`src/options/presets/`), all four accepted at 2.9.6 / 2.12.0 / 2.19.0
(measured 2026-08-08). Smallest first; `high-obfuscation` is reserved for the final integration
check, since a gap found directly against the largest is far harder to shrink to a minimal repro.

Two things the ladder must not assume:

- **Not subset semantics.** A smaller tier can be a genuinely distinct shape rather than a
  subset — in js-confuser `low` skips control-flow flattening entirely. Read each tier's contents
  per version from `git show <tag>:src/options/presets/<Tier>.ts` and verify the relationship.
- **Not constant across versions.** A preset's *contents* can drift between 2.9.6 and 2.19.0
  independently of any option rename, silently changing what a tier tests. Whether they do is
  itself a finding, readable from the same per-tag source.

#### F4 — Freeze the corpus

The encode script — matrix × option sets × fixtures → `sandbox-tests/out/`. Disposable, recipe
tracked as `skills/javascript-obfuscator/corpus.md` (§7.2). 8 versions × 16 sets × 3 fixtures =
**384 samples**; expect tens of minutes, so background it.

**Encoding needs no decoder**, which is why the corpus is immune to any defect in the plugin
under test. **Freeze it before anything compares against it**: the encoder samples randomly (S5),
so two fresh encodes are not comparable and a re-encode turns every figure measured against the
old corpus into anecdote. `seed` makes a rebuild reproducible (§8.3); it does not make two
differently-seeded corpora comparable.

#### F5 — Branch, and the run harness skeleton

The first step that touches the decoder. `decoder/decode-js` is on `main`, one commit behind
`origin/main`; the sync decision comes before the branch, and the branch is cut **inside the
submodule's own repository** — never a hub branch, never a detached HEAD. The encoder submodule
is not touched at all.

The run/score script is disposable, its recipe a section in `skills/decode-js/probes.md`. Built
from what `probes.md` already solves — subprocess timeout, `.cjs` because decoded output carries
a top-level `return`, reading a result global as well as stdout, worker-pool shape — plus §7.6's
two mechanisms (console markers, one subprocess per decode). It ships with oracles 1–4 and 6;
**oracle 5's subject list is filled in per unit**, which is the whole reason units are vertical.

Exit on **one** cell end to end before any unit runs. A run script that silently drops an oracle
produces a report that reads complete.

### The unit loop — every unit step does all three

Stated once here; the unit list below does not repeat it. This is
`encoder-decoder-method.md`'s loop for studying a pair, with the verification stage folded in at
the point where it is answerable:

1. **Stop first if a decoder file already exists that reuses a *shared* visitor.** Keep-or-fork
   is a decision for whoever is driving, not a default (§3.3).
2. **Document the encoder side** for this unit, at the eras in scope, from `src/` at each tag.
3. **Define this unit's residue census** from step 2 — the construct list is encoder knowledge,
   never the decoder's description of what it removes. This is oracle 5 for these cells.
4. **Run the existing plugin** over the corpus cells that exercise this unit, and record the
   verdict. Now it means something, because step 3 defined the census from source.
5. **Write the `obfuscatorx` pass**, and its decoder-side doc.
6. **Build fixtures from the encoder's own test cases** for this unit — 155 `.spec.ts` files
   under `encoder/javascript-obfuscator/test/` (`functional-tests`, `unit-tests`,
   `runtime-tests`, `fixtures/`), a free and authoritative case list, not cases we invent.
7. **Pause for review, then commit, then clear context** before the next unit's research.

**Why all three in one step.** Each of the three alone produces something unfalsifiable. An
encoder doc written from reading is a hypothesis until something inverts it (T8). A verification
verdict rests on a census, and a census written before the encoder study is defined by the thing
under test — S4 rules out runtime correctness as the fallback, so oracle 5 *is* the verdict. And
a fixture pins **a claim** (`doc-conventions.md`), so fixtures built before the claims exist are
a name inventory. Folded together, each step ends with an encoder claim, a measured verdict and a
decoder pass that proves both — and a commit.

**Two artifacts accrete across units** rather than belonging to one: `versions.md` (a row per era
as its shape gets named) and `test/obfuscator/`, the existing plugin's first regression baseline.
A cell graduates into the latter only when step 3's census certifies it — pinning a
buggy-but-plausible decode as `.fix.js`-expected is worse than no fixture, since exact string
equality makes it look authoritative. Failing cells are the repair worklist.

### The units, in reverse encoder-stage order

**Derived from the encoder, not from the decoder.** An earlier draft of this list was taken from
`plugin/obfuscator.js`'s own pass order and then described as "corroborated" by it — circular, and
exactly what W4's corollary forbids: *our own pipeline position never sets priority*. The table
below comes from `JavaScriptObfuscator.ts`'s stage sequence and each transformer's declared
`NodeTransformationStage`, read at the pin.

**The sequence is the encoder's stage order, traversed backwards** — T1: fix in reverse encoder
order, asking of each unit what its matcher needs its input to already look like. A stage the
encoder ran *late* is the one whose residue hides everything earlier, so it is reversed first.
The direction matters because units are vertical: a unit cannot be *verified* while a later
encoder stage's residue is still sitting in its input, so a forward order would make each unit's
own verdict unreadable — the premature-troubleshooting corollary of T1, one unit at a time.

| # | Unit | Encoder stage (position) | Existing plugin, for reference only |
|---|---|---|---|
| U1 | Normalization — escape sequences, statement merging, if-simplification, declaration merging, directive placement | Finalizing (10), Simplifying (9) | `splitVarDeclaration`, `lintIfStatement`, `deleteIllegalReturn`, the `node.extra` strip, `splitSequence`, `splitAssignment` |
| U2 | String array — the array, the rotate function, era detection | StringArray (8) | `decodeGlobal` → `stringArrayV3`/`V2`/`V0`, `stringArrayLite` |
| U3 | String-array wrappers — scope calls wrapper, string-array control flow | StringArray (8) | the calls-wrapper branches inside `stringArrayV2`; `parseControlFlowStorage` |
| U4 | Converting — object-expression keys, member expressions, `SplitString`, numerical expressions, literal transformers | Converting (6) | `decodeObject`, `mergeObject`, `calculateConstantExp` |
| U5 | Control-flow flattening — block-statement and function control flow | ControlFlowFlattening (4) | `decodeCodeBlock`, `removeControlFlowOb` |
| U6 | Dead-code injection | DeadCodeInjection (3) | `cleanDeadCode`, `pruneIfBranch`, `deleteUnusedVar` |
| U7 | Custom code helpers — self-defending, debug protection, console output, domain lock, obfuscating guards | Preparing (2) | `unlockEnv` → `deleteSelfDefendingCode`, `deleteDebugProtectionCode`, `deleteConsoleOutputCode` |

**The last column is a reading aid, not an authority.** It says where to look for prior art on the
same shape — often the fastest way to find a matcher that is already right (T8's "look for a
matcher that already does it correctly"). It does **not** set the unit order, does not imply the
existing pass is correct, and does not imply `obfuscatorx` should be shaped like it. The mapping
is approximate by construction, since one plugin function can span several encoder stages and one
transformer declares several.

**Two stages get no unit.** `RenameIdentifiers` (7) and `RenameProperties` (5) are irreversible by
design — nothing restores an original name. They are a census concern (residue that no decode can
remove, S1) and a matcher constraint (T2: never key on name text), never a decode unit. Scheduling
one would be the mistake of treating unremovable residue as a gap.

**A transformer is not confined to one stage**, so the units are not a partition of the
transformer list. `StringArrayRotateFunctionTransformer` declares five stages (Converting,
Finalizing, Preparing, RenameIdentifiers, StringArray) and `DeadCodeInjectionTransformer` three.
A unit is a **shape to reverse**, and one transformer can contribute to several — which is also
how an ordering drifts unnoticed (F1).

**One discrepancy to resolve in U4, not to assume.** The existing plugin runs `decodeObject`
*before* `decodeGlobal` — Converting-reversal ahead of string-array-reversal, the opposite of the
order above. Either `decodeObject` addresses something other than the Converting transformers, or
the existing plugin's ordering is itself a defect. W4's third corollary says name the stage only
from its source, so U4 reads `decodeObject` and the Converting transformers before concluding
either.

**U2 carries the era work** because the eras *are* string-array shapes: §5.5's provisional names
get fixed against real samples here (named for the AST shape, never the version or the legacy
`V0/V2/V3` labels, §5.4), and each confirmed shape opens a `versions.md` row. Two rules bind that
naming — confirm each shape at **both ends** of its claimed range rather than at one version, and
treat §5.5's two axes as provisional too, since they came from the same prose.

**A registry range between two probed versions is an interpolation and must be marked as one.**
Phase 1 measures eight versions; if 2.12.0 and 2.15.3 both show one shape, 2.13.x and 2.14.x were
never built. §3.6.1 forbids the detector interpolating across the 3.0.0–4.2.2 gap; the same rule
applies at finer grain inside phase 1's own range.

**The detector (§3.4) lands with U2 and is extended by each later unit** — `detect(ast) ->
{ era, signals, confidence }`, multi-signal so it degrades gracefully rather than falling through
silently (§3.5). A strategy file never sniffs its own era, it assumes it. Inconclusive detection
**refuses with a diagnostic** naming which signals matched, the nearest era and why it was
rejected, via `src/utility/logger.js` (§3.6.3).


### Acc — the integrated preset study: build the workflow from scratch

The per-unit fixtures prove each unit in isolation, which W1 says is exactly what a real sample
does not look like. So phase 1 closes on the **preset ladder**, smallest first: a matcher
validated only against an isolated single-transform fixture is not proven robust to combined
output, because that fixture omits precisely the later stages that would break it. A unit that
passes its own cells and fails under `medium-obfuscation` is a phase-1 finding, not a phase-2 one.

**This step assembles `obfuscatorx`'s pipeline from scratch — it is not required to follow the
existing plugin's workflow, and should not start from it.** Until here each unit has produced a
pass in isolation; the integrated study is where they become an *order*. Four reasons the order
is designed rather than inherited:

- **The existing 12-step sequence is prior art, not a specification.** It predates the era split
  (§3.4), and one of its orderings already contradicts the encoder's stage order — U4's
  `decodeObject` discrepancy. Copying it would import that question rather than answer it.
- **A defect can live in the pipeline ordering rather than in any matcher** (W4). The recorded
  instance was fixed by scheduling a pass **twice**, not by improving it — so the workflow must
  be free to schedule a pass more than once, which a copied linear sequence forecloses.
- **The pipeline stays era-invariant** (§5.2): same slots, same order, for every era; eras differ
  only in which strategy fills a slot. That is a property of a designed order, and it is what
  lets Upstream Effects be stated once per slot instead of once per (slot × era).
- **Our own pipeline position is not the encoder's stage order** (W4's second corollary). The
  slots come from §8.6, and each slot's placement is justified by what its matcher needs its
  input to already look like — not by where the equivalent pass sits today.

The preset ladder is the instrument that judges the assembled order: a pass that worked in
isolation and fails under a preset is usually mis-scheduled rather than wrong, which is T9's case
2 and is invisible to any per-unit fixture.

Before the phase is called done: verify every link resolves, run `grep -nP '[^\x00-\x7F]'` over
the changed files, and grep the new encoder package for `decode-js` — Project Independence forbids
the encoder side naming the decoder, and that link goes in by reflex (§11).


### 4.3 Phase 2 — the pin, 5.5.0

Same structure (§4.1), enlarging coverage to the pin: its own foundation steps (a 5.5.0 corpus
built from the submodule, its stage order re-derived) and then unit steps that document 5.5.0's
shapes, verify the open-ended `V3` claim, and extend `obfuscatorx` to decode them. A new era row
without a strategy behind it is a claim nothing has tried to invert, so they land together.

Its own phase for two independent reasons:

- **Conceptual.** A different question. Phase 1 asks "are the claims true where written";
  phase 2 asks "does the open-ended `V3 >= 2.19.0` claim still hold ~3 major versions later."
  Between them sits `stringArrayCallsTransform` (3.2.0), which changes the calls-wrapper shape.
- **Mechanical.** 5.5.0 is the **only version built from the submodule**, per the Encoder Pin
  Gate's "real output built from the new commit"; every other version is a prebuilt npm
  tarball. Different toolchain, different failure modes — mixing it into an npm-based phase
  would confuse a build problem with a decode problem.

Phase 2's result is exactly what the Pin Gate requires before the pin could ever move.

**Expected split:** if phase 1 passes and phase 2 fails, the open-ended claim's upper end is
stale — the likely outcome. If **phase 1** fails, the problem is not version drift and phase 2
must not be read as a version finding.

### 4.4 Phase 3 — the range decode-js is silent about: 3.0.0 – 4.2.2

No detector claims anything here. Not "leftover versions" but a distinct question: where
between V3's floor and the pin does its open-ended claim actually stop holding?

Its unit steps therefore have no claim table to verify against — the derivation (§4.5) produces
this slice's era set instead, and the "verify" third of each unit becomes "verify the derivation
predicted the shape correctly." Closing the gap is what makes `obfuscatorx`'s coverage
contiguous; until then the detector treats it as **unknown** and never interpolates across it
(§3.6.1). Whether the slice is worth taking at all is a prevalence question, not a completeness
one (§4.6).

### 4.5 Version derivation from encoder history

Runs **after phases 1 and 2** — their outcome likely reshapes it, since if V3 breaks between
2.19.0 and 5.5.0, locating that break becomes the derivation's central question rather than a
side one. Sequence: phase 1 → phase 2 → derivation → phase 3.

Safe in that order *because* the decoder's boundaries are sample-derived evidence, not guesses
(see §4.6) — phase 1 rests on something already grounded. What the derivation can still change
is **completeness**: a shape change it finds would *add* versions, not invalidate covered ones.

- **a.** Read the encoder's history for changes that alter *emitted output shape* —
  `CHANGELOG.md` (breaking changes, option renames, string-array/transformer entries), tags,
  and transformer sources. Encoder-side evidence is what the version set rests on.
- **b.** **Then** compare against the decoder's existing boundaries — see §4.6. Two *different
  kinds* of evidence answering different questions, not a claim checked against a truth.
- **c.** Treat the decoder's set as **sound but possibly incomplete**. **The derivation's job is
  completeness, not correctness.** A change in encoder history but absent from the decoder's
  set is most likely a version rarely met in the wild, not a decoder error.
- **d.** Produce a table: one row per version, the reason it earns a slot, and which kind of
  evidence puts it there (encoder history, report stream, or both).

Its rationale is encoder knowledge and belongs in the encoder package; the decoder's detector
boundaries stay decoder-side (Project Independence).

### 4.6 The boundary set is evidence, and encodes prevalence

The decoder's boundaries are **not** unverified claims: they accumulated from many real samples
submitted by users over years, and the plugin's source cites the issue numbers (#31, #50, #94,
#95) at the points where shapes diverged.

Because they came from user reports rather than from reading encoder source, they carry a
second signal: **which versions people actually encounter.** Encoder history says what changed;
the report stream says what is in use. For a community-facing decoder these are different
questions, and the second should drive prioritization.

- **Phase 3's scope is a prevalence question**, not only a completeness one. Whether 3.0.0–4.2.2
  deserves coverage depends on whether those versions are met in practice.
- **Era granularity should follow prevalence.** Encoder source may reveal shape changes finer
  than anything worth a separate strategy. Eras earn a strategy by being *met*, not by existing.
- **Prevalence predicts which refusals fire.** Given §3.6.3, uncovered eras determine the
  real-world refusal rate — so prevalence tells us whether refusing is cheap or costly.
- **"No samples seen" and "no change occurred" are different findings** and must never be
  recorded as the same one.

## 5. Code layout

### 5.1 File-splitting rule: strategy vs. parameters

A **different strategy** gets its own file; **different parameters** stay incremental in one
file. This formalizes what the existing plugin already does: `stringArrayV0/V2/V3` are three
separate functions (three algorithms), while V2's four calls-wrapper sub-shapes are branches
inside one function (one algorithm, parameterized).

**Split when any of these fire:**

- the era check sits at the top of the function and the two bodies are disjoint;
- the eras need different *inputs* — e.g. one requires sandbox eval and the other does not;
- changing one era's path could regress another's and tests cannot cheaply prove it did not;
- more than about two nested era conditionals accumulate in one function.

**Default incremental, split on evidence** — not because incremental is better, but because the
directions are not equally reversible: splitting an over-branched file is mechanical, whereas
merging two files that have drifted requires *proving* them equivalent.

**What makes splitting cheap here:** because detection is separated from decoding (§3.4), era
knowledge concentrates in the detector. A strategy file never sniffs its own era — it assumes
it.

### 5.2 Keep the decoder pipeline era-invariant

Same slots, same order, for every era; eras differ only in which strategy fills a slot. Then
Upstream Effects are stated once per slot rather than once per (slot × era). The era-variance we
cannot control is the encoder's; the era-variance we *choose* should be zero.

### 5.3 Proposed tree

```
src/plugin/obfuscatorx.js          # thin: detect → dispatch → shared post-passes
src/visitor/obfuscator/
  detect.js                        # multi-signal era detection
  <shape>.js                       # one file per string-array strategy — see §5.5
  unlock-env.js                    # anti-tamper strippers
test/obfuscatorx/                  # graduated fixtures
```

### 5.4 Naming: by shape, not by version

Files are named for the **AST shape they match**, not the version or the legacy `V0/V2/V3`
labels. A version-derived name goes stale the moment a later era turns out to use the same
strategy — the same failure that ruled out a version-suffixed entry name. The era *range* is
documented inside the file, where it can be corrected.

### 5.5 Provisional shape names — confirm in phase 1

Two orthogonal axes: how the array is held, and whether a standalone rotator exists.

| Legacy label | Shape | Provisional file |
|---|---|---|
| `stringArrayV0` | array in a variable, no rotate function | `string-array-var-plain.js` |
| `stringArrayV2` | array in a variable + standalone rotate function | `string-array-var-rotated.js` |
| `stringArrayV3` | array in a self-replacing accessor function | `string-array-fn-wrapped.js` |

**Provisional.** Derived from the decoder's *description* of the shapes, not from observed
encoder output — naming a shape before looking at it is the mistake this plan warns against
everywhere else. Phase 1 produces the real samples; the names get fixed against them.

## 6. Doc layout — the two convention revisions

Both **applied**. The era revision landed 2026-08-07 as `1871f23` (`doc-conventions.md`) and
`49d0fde` (`SKILL.md`); the package-layout revision landed 2026-08-08 as `d4b898e` and
`ff9de57`. Their rules now live in `doc-conventions.md` and are not restated here — what
remains is only what has not graduated: the constraint on where the generalizable pattern may
live, and the measurements the layout revision rests on.

### 6.1 Where the generalizable pattern lives

`SKILL.md`'s Project Independence rule forbids a skill package from referencing another project
but states that **cross-project observations belong in a separate note**. The reusable parts —
detect-then-dispatch, the era concept, era IDs, era-tagged tables — are exactly that, so they go
in **hub-level docs** (`doc-conventions.md`, or a note sibling to `encoder-decoder-method.md`),
never inside `skills/javascript-obfuscator/` or `skills/decode-js/`. The future js-confuser
study then reads the hub doc and neither package references the other. **The convention revision
is itself the cross-project note** for the doc half.

### 6.2 The structure-drift measurements

The evidence the package-layout revision rests on; the rules it produced live in
`doc-conventions.md` and `SKILL.md` and are not restated here. Measured 2026-08-08 over adjacent
tags in `encoder/javascript-obfuscator`.

**Structural drift and shape drift are independent axes** — the finding that decided it:

- **`2.15.3 → 2.15.4` changes zero files under `src/`**, yet the claim table has an era boundary
  exactly there, distinguishing two wrapper shapes. An era boundary can have **no structural
  footprint at all**.
- **`2.18.1 → 2.19.0` changes three files, none of them string-array** —
  `SelfDefendingUnicodeCodeHelper.ts` and `SelfDefendingNoEvalTemplate.ts` consolidate into
  `SelfDefendingCodeHelper.ts`. The `stringArrayV3` shape change that names this boundary happened
  entirely *inside* existing files.

**Consequences specific to this encoder**, which the convention now covers generically:

- **The rotate function relocates and splits.** Only a code helper at 2.9.6
  (`custom-code-helpers/string-array/StringArrayRotateFunctionCodeHelper.ts`); from 2.19.0 that
  **plus** `node-transformers/string-array-transformers/StringArrayRotateFunctionTransformer.ts`,
  in a different directory.
- **Five files exist in 2.x and are gone at the pin** — `SelfDefendingUnicodeCodeHelper.ts`,
  `SelfDefendingNoEvalTemplate.ts`, `string-array-rotate-function/SelfDefendingTemplate.ts`,
  `CryptUtilsSwappedAlphabet.ts`, `StringLiteralNode.ts`. All inside phase 1's scope, so the
  removed-era mechanism (an era row citing its own SHA) is exercised immediately.
- **This package needs a `source-map.md`**: it is multi-era *and* a concept spans directories,
  both of the triggers the convention names.

**Where the churn is, and it is not where you would guess.** Across eleven sampled tags the major
bumps are near structural no-ops — 2.19.0 → 3.0.0 is +1/−1, 3.2.0 → 4.0.0 is +2/−1 — though
3.0.0 is the breaking-rename release (§8.2). The concentration is *inside* phase 1's own range
and at 3.2.0.


## 7. Sandbox & harness

Designed 2026-08-07; hazards retired (§8.3). Not yet built beyond the encoder installs.

### 7.1 Governing principle: the recipe is tracked, the harness and its artifacts are not

`/sandbox-tests/` is gitignored, so anything living only there evaporates on a clean checkout.
Split by *durability*: **tracked** — the two recipe pages (§7.2), which carry the version matrix,
the option-set definitions and the input-fixture specs as their own content, plus the graduated
fixtures (§7.7). **Disposable** — the encode and run scripts themselves, `node_modules`, encoder
builds, encoded/decoded samples, run reports.

**Why the scripts are on the disposable side**, per `probes.md`: "a stale probe that still runs
is worse than no probe, because it answers confidently." The test that keeps a recipe honest is
regenerating its script from it cold.

### 7.2 Where each piece lives — scripts are disposable, recipes are tracked

Both scripts live in the gitignored sandbox; the hub tracks *how to rebuild them*, following
`skills/decode-js/probes.md`'s rule — "this page is a recipe, not an inventory… no script file
belongs in the hub."

This is also the only arrangement that stays legal. Any tracked runner that reads a matrix out of
the hub is a submodule referencing the hub, which `doc-conventions.md` forbids outright; with no
code in the hub there is nothing to reference.

| piece | script (disposable, `sandbox-tests/`) | recipe (tracked) |
|---|---|---|
| encode | matrix × option sets × fixtures → samples | `skills/javascript-obfuscator/corpus.md` |
| run + score | subprocess per decode, six oracles → JSON report | a section in `skills/decode-js/probes.md` |

The split is the Project Independence line: the encode recipe is pure encoder knowledge and
**never names decode-js**; the run recipe is decoder knowledge and *may* name the encoder, under
the one-directional decoder→encoder exception. Durable output is the two recipe pages plus the
graduated fixtures (§7.7) — nothing else survives a clean checkout, by design.

```
sandbox-tests/            # gitignored, everything here regenerable from the two recipes
  encoders/               # npm-alias install, the 5.5.0 archive, encode script
  out/<version>/<fixture>__<optionset>.js       # encoded
  decoded/<version>/<fixture>__<optionset>.js   # decoded
  report/<timestamp>.json
```

### 7.3 Version materialization

- **Phase 1 (npm).** A *single* `package.json` using npm aliases
  (`"jso-2-9-6": "npm:javascript-obfuscator@2.9.6"`), so one `npm install` provides all eight,
  importable by alias. Subfolders remain for **outputs**; installs collapse to one tree.
- **Phase 2 (the pin).** `git archive 45ad03b | tar -x` into `sandbox-tests/encoders/5.5.0-pin/`
  and build *there*. **Never build inside the submodule** — its `.gitignore` does cover `/dist`
  and `/node_modules`, so an in-place build would be mostly invisible, but exporting keeps the
  read-only checkout provably untouched and ties provenance to the SHA.

### 7.4 Determinism: a fixed `seed` is mandatory

The encoder exposes `seed` (`src/options/Options.ts:439`, `string | number`). Every option set
pins one. Without it, identifier names and string-array order vary per run, and since graduated
fixtures compare by **exact string equality** (§7.7) no fixture could ever be stable. A
correctness requirement of the fixture format, not a nicety. Verified — §8.3.

### 7.5 Input fixtures and option sets

The requirements they must meet, independent of any one phase — the phase-1 instances are F3
and F4 in §4.2 and are not restated here.

- **Fixtures are small, deterministic and self-reporting**, so runtime equivalence is a stdout
  comparison. Between them they must exercise string literals (string array), branching
  (control-flow flattening), object literals and member access (transformer/`SplitString`), dead
  code, and functions/closures.
- **Option sets are keyed per version**, because names *and types* drift (§8.2). Keying is the
  check that produces the finding, whether or not the surface turns out to vary.
- **A combined ladder is mandatory, and it is the encoder's own presets.** W1 is explicit that a
  later stage invalidates an earlier matcher *silently and totally*, and that "a matcher
  validated only against an isolated single-transform fixture is not proven robust to real
  combined output." If pipeline order varies by era (§8.6), a matcher validated at one era fails
  closed at another for reasons unrelated to its own transform. Per-feature sets structurally
  cannot detect that.

### 7.6 Oracles, recorded separately per (version × option set × fixture)

**Read entirely from captured stdout/stderr — the plugin is never edited.** Verified 2026-08-08:
`src/plugin/obfuscator.js` does **not** route through `utility/logger.js`; it prints
unconditionally. That gives oracle 1 and `encoder-decoder-method.md` T6's per-stage instrument
for free, which matters because §3.3 forbids touching that file and instrumentation was the one
thing that looked like it might force a violation.

| marker | reports |
|---|---|
| `Try v3 mode...` / `Try v2 mode...` / `Try v0 mode...` | which detector was attempted |
| `String List Name: <name>` | which one committed, and to what |
| `Cannot find string list!` | all three missed — the whole plugin aborts |
| `Essential code missing!` (V2) / `Unexpected reference` (V0, V3) | a detector matched partly and gave up |
| the seven stage markers, `还原数值...` … `净化完成` | how far the pipeline got before aborting |

1. **Detection** — which era/detector fired, or none. For the existing plugin: which of
   V3/V2/V0 matched, or `false`, read from the markers above. Recorded even when later stages
   fail, since this is the diagnostic the current design cannot produce.
2. **Completion** — plugin returned non-falsy.
3. **Parse** — decoded output parses.
4. **Runtime equivalence** — original vs decoded stdout, in a subprocess **with a timeout**.
5. **Residue census** — decoded output still containing string-array/wrapper artifacts. The
   census that should read zero; per Measured Figures a skill doc records the census, never the
   count.
6. **Option efficacy** — the option set actually changed output versus that version's baseline.
   Not bookkeeping: unknown option names are silently ignored (§8.2), so a mis-spelled or
   version-inappropriate option yields a sample that quietly tests the default. Acceptance by
   the encoder proves nothing.

**One subprocess per decode is a correctness requirement, not a timeout guard.** Verified
2026-08-08: `src/plugin/obfuscator.js` creates its isolated-vm `isolate` and `globalContext` at
**module scope**, so every `virtualGlobalEval` in a process shares one global object. Decode two
samples in one process and the second evaluates its string-array code into a context still
holding the first's bindings — a name that should be missing resolves, the `ReferenceError`
recovery path never fires, and the cell passes for the wrong reason. Process isolation is what
makes the oracles mean anything; the timeout below is a separate, additional requirement.

**Execution rule (measured, not assumed — §8.3):** only `debugProtectionInterval` samples are
excluded from execution in encoded form. Plain `debugProtection` and `selfDefending` run
normally as emitted. The subprocess timeout is mandatory for every run regardless, and this rule
is re-measured per era rather than generalized from 2.19.0.

### 7.7 Graduation to permanent fixtures

Convention verified from `test/jsconfuser/`: a case is the triple `<name>.src.js` (plaintext),
`<name>.js` (encoded input), `<name>.fix.js` (expected decode), driven by
`getPluginResult(plugin, fix, input)` in `test/helper.js` with **exact string equality**.

**Decided 2026-08-08 (user): phase 1's passing cells graduate into a new `test/obfuscator/`,
now** — not held back for `test/obfuscatorx/`. Since the plugin has **no existing fixtures at
all** (§8.4), graduation is not optional polish; it is the first regression baseline this target
has ever had, and it exists before `obfuscatorx` is written rather than after. Adding tests is
additive and changes no plugin behavior, so §3.1's concern is untouched. Cases are named
`<version>-<optionset>-<fixture>`; the same samples are reusable for `obfuscatorx` later.

## 8. Verified findings

### 8.1 Current state of the tree

- **Hub branch** `docs-javascript-obfuscator`, off `main` (`e294cba`). No commits on it.
- **No encoder-side skill package exists** for javascript-obfuscator; `skills/` has
  `js-confuser/` and `decode-js/` only. That gap is why the branch exists.
- **The decoder already targets this encoder** — `src/plugin/obfuscator.js`, documented at
  [skills/decode-js/plugins/obfuscator.md](skills/decode-js/plugins/obfuscator.md): a 12-step
  pipeline, three version-keyed detectors, three anti-tamper strippers under `unlockEnv`. The
  work is **not** greenfield.
- **Encoder pin:** `45ad03b` (tag `5.5.0`).
- **Upstream ships its own `CLAUDE.md`** in the encoder submodule — tracked upstream (last
  touched by `notaphplover` in `4ebced3`, 2026-04-27), clean against the pin.
  - Inside a read-only submodule: never edit it, including as a side effect.
  - It **auto-loads as project instructions** whenever a tool runs with cwd inside that
    submodule. Third-party content aimed at the obfuscator's own developers — reference
    material, not directives. `SKILL.md` remains authoritative; on conflict `SKILL.md` wins.
  - Its headings skew to build/test/CLI invocation, not transform patterns, and **it states
    "Version: 5.0.0" while the pin is 5.5.0** — live evidence that it is a map into `src/`,
    every claim to be confirmed at source.

### 8.2 Encoder constraints (verified against the pin)

- `rotateStringArray` was **renamed to `stringArrayRotate` in 3.0.0** (CHANGELOG v3.0.0,
  breaking change) — inside phase 3's range, so phase 3 needs both spellings.
- **Option *types* drift too, not only names:** `debugProtectionInterval` changed from boolean
  to a millisecond number in **4.0.0** (CHANGELOG v4.0.0, issue #1031) — also inside phase 3's
  range. The matrix must carry per-version option **values**, not just spellings.
- **Unknown option names are silently accepted and ignored** (measured across 2.9.6 / 2.12.0 /
  2.19.0: a bogus name produced output identical to baseline with no error; a *known* name with
  the wrong type throws a validation `ReferenceError`).

  **Silent acceptance is worse than a loud failure**, and it is why a shared options file cannot
  span the matrix: `stringArrayRotate` on a 2.x build does not error, it silently encodes with
  rotate at its default, yielding a sample that does not test what the matrix says it tests.
  Forces oracle 6 (§7.6).

  **That asymmetry is also an enumerator, which is how F2 derives the matrix rather than
  guessing it.** Pass a *known* name an object value and validation throws; pass an unknown name
  anything and it is silently accepted. So "is this option name valid at this version" is a
  mechanical probe. Measured 2026-08-08 across 2.9.6 / 2.12.0 / 2.19.0: `rotateStringArray`,
  `stringArrayWrappersCount`/`Type`/`ChainedCalls` and `debugProtectionInterval` are known at all
  three; `stringArrayRotate` and `stringArrayCallsTransform` at none — both post-date 2.x, as
  above. So the wrappers axis exists as far back as 2.9.6, not from 2.12.0, and the phase-1
  option surface is expected to come back **uniform** across the eight. Per-version keying stays
  in the design as the *check* that produces that finding, not as an assumption of drift.
- **3.2.0 added `stringArrayCallsTransform`**, post-dating every fingerprint the decoder holds —
  the main reason phase 3's range is a candidate blind spot rather than a safe interpolation.

### 8.3 Hazards — all retired

Probed empirically against real installs before building anything. Scripts in
`sandbox-tests/encoders/` (`smoke.cjs`, `hazard2.cjs`, `seedcheck.cjs`, `optcheck.cjs`);
disposable, rerunnable after `npm install` there.

**1. Old versions under Node 26 — no issue.** All eight phase-1 versions installed from one
npm-alias tree and encoded successfully under Node v26.5.0. No pinned older runtime needed; the
npm-alias approach works as designed.

**2. Execution hazard — retired, and it is narrower than it sounds.** Measured at 2.19.0:

| Option set | Result |
|---|---|
| baseline | ran, stdout matches |
| `selfDefending` | ran, stdout matches |
| `debugProtection` | **ran, stdout matches** |
| `debugProtection` + `debugProtectionInterval` | **timed out (~5 s bound)** |
| `disableConsoleOutput` | ran, stdout matches |

Plain `debugProtection` does **not** hang — a `debugger` statement is a no-op without an
inspector attached; only the **interval** variant hangs, via a `setInterval` holding the event
loop open. `selfDefending` is safe to execute as emitted; it only misbehaves when the code is
reformatted. `disableConsoleOutput` did **not** suppress stdout, so the runtime-equivalence
oracle survives for it. The timeout mechanism caught the runaway cleanly.

**3. `seed` reproducibility — confirmed.** Same seed gives byte-identical output, different
seeds differ, on 2.9.6 / 2.12.0 / 2.15.4 / 2.19.0 — including with `deadCodeInjection` and
`controlFlowFlattening` enabled, the most randomness-heavy settings.

### 8.4 No existing baseline

`decoder/decode-js/test/` contains `jsconfuser/`, `sojsonv7/`, `utility/`, `visitor/`,
`helper.js` — and **nothing for `obfuscator`**, despite it being the largest plugin. There are
no regression fixtures for it.

### 8.5 npm provenance — each phase-1 build is proven against a submodule commit

Measured 2026-08-08. `npm view javascript-obfuscator@<v> gitHead` returns the commit the tarball
was published from, and for all eight phase-1 versions it is **byte-identical to the encoder
submodule's own tag for that version**:

| version | gitHead = tag |
|---|---|
| 2.9.6 | `0afcf7a5b2f56ba7c31246928f8f1b485a0a030a` |
| 2.10.0 | `86fe1df40c8a391f909375cb7ebec552fea781fa` |
| 2.11.1 | `99194f145698a378b14114cbb4bec89d3cdc34f2` |
| 2.12.0 | `36ea9c08f3244533b466b3031824da6493aa2d4e` |
| 2.15.3 | `993cf7a2a850365baf105e54a09a761724d47da9` |
| 2.15.4 | `08aad1b7069e9f8b510765dcbf01c88aa741378d` |
| 2.18.1 | `18f5210871a6574f256938d4ad56e2ac19ac8884` |
| 2.19.0 | `314855eb8bb65653b8c292e7a65ffcdc6c39761b` |

Two consequences beyond the registry:

- **Submodule history is a legitimate source for every phase-1 version**, not just the pin. Each
  version's option definitions, preset contents and transformer sources are readable at
  `git show <tag>:<path>` without building anything — which is what F2 and F3 use.
- **The 5.5.0 pin stops being special for provenance reasons.** §4.3 keeps phase 2 separate for
  its other reason (a different toolchain, so a build failure cannot be confused with a decode
  failure), but "the only version traceable to a commit" is no longer one of them.

### 8.6 Stage order and transformer-to-stage mapping (read at the pin)

Read 2026-08-08 from `src/JavaScriptObfuscator.ts` (the stage sequence),
`src/enums/node-transformers/NodeTransformationStage.ts`, and each transformer's declared stages.
It is the input to the unit order in §4.2, and its durable home is F1's root file — recorded here
only until that exists.

The sequence, in encoder order: Initializing → Preparing → DeadCodeInjection →
ControlFlowFlattening → RenameProperties → Converting → RenameIdentifiers → StringArray →
Simplifying → Finalizing.

**But the flat `nodeTransformersList` (`src/JavaScriptObfuscator.ts:64`) is *not* the execution
order** — a trap worth stating first, since it is the list a reader finds. Order comes from that
stage sequence, and *within* a stage from a topological sort built by
`nodeTransformerNamesGroupsBuilder.build()` (`NodeTransformersRunner.ts:80`) out of each
transformer's declared dependencies. So the effective order drifts two ways: the stage sequence
changes, **or one transformer's declared dependency changes — which appears in neither the
CHANGELOG nor the list.** That is how an era-varying order arises with nothing to notice, and it
is why item 4 (Downstream Effects) is carried as era rows: it describes *edges* between passes, so
one reordering rewrites it for many transforms at once.

Three facts the mapping produced, none of them readable from the stage list alone:

- **The anti-tamper trio is injected at `Preparing`**, the second-earliest stage, via
  `CustomCodeHelpersTransformer` — `SelfDefending`, `DebugProtectionFunction`(`Call`/`Interval`),
  `ConsoleOutputDisable`, plus domain-lock and the string-array helpers, all under
  `src/custom-code-helpers/`. So every later stage obfuscates the helpers themselves, and their
  strings live in the string array. That is *why* they are reversed last, rather than because a
  decoder happens to run `unlockEnv` at the end.
- **`Converting` (6) precedes `StringArray` (8).** `ObjectExpressionKeysTransformer`,
  `MemberExpressionTransformer`, `SplitStringTransformer`, `NumberToNumericalExpressionTransformer`
  and the literal transformers are all Converting — so they reverse *after* the array, not last.
- **A transformer can declare several stages.** `StringArrayRotateFunctionTransformer` declares
  five (Converting, Finalizing, Preparing, RenameIdentifiers, StringArray);
  `DeadCodeInjectionTransformer` three. So units cannot be a partition of the transformer list,
  and a per-stage reading of "what runs here" must be taken from the declarations, not from where
  a file sits in the tree.

## 9. Open items

- **Phase 2's core question**, unanswerable by reading: does 5.5.0 still emit a string array
  that `stringArrayV3`'s `checkPattern` fingerprint matches? The probe, applied per phase: build
  real output at the target version, run the plugin, observe whether `decodeGlobal` finds a
  `stringArrayName` or returns `false` — which aborts the whole plugin, not just that detector.
  Forks the work the same way at every phase: **detector matches** → documentation job on a
  working decoder; **detector misses** → repair job, and doc work follows the fix rather than
  describing something broken.
- **Shape names** are provisional until phase 1 (§5.5).
- **The `decodeObject` ordering discrepancy** — the existing plugin reverses Converting before
  StringArray, the opposite of the encoder's stage order. Resolved in U4 by reading both, not by
  assuming either is wrong (§4.2).
- **Which unit runs next** is still whoever is driving to pick; U1–U7 is a dependency order, not
  a mandate to run them back to back.

## 10. Required reads

From `SKILL.md`'s Standing Rules — **not from memory of a previous session**:

- [skills/doc-conventions.md](skills/doc-conventions.md) — **read in full, 2026-08-07**, and
  **revised 2026-08-08** (`d58ecf5`). A new session reads the current file, not this summary of
  it: its "Package Layout" section is what F1 writes against.
- [skills/encoder-decoder-method.md](skills/encoder-decoder-method.md) — **read in full,
  2026-08-08**, before detailing phase 1.
- [skills/decode-js/probes.md](skills/decode-js/probes.md) — **read in full, 2026-08-08**. It is
  the precedent §7.2 now follows, and its plumbing conventions (subprocess timeout, `.cjs` for
  top-level `return`, reading a result global as well as stdout, worker-pool shape) are what
  F5's run script is built from rather than reinvented.

## 11. Standing constraints that bite on this branch

- **Encoder is read-only** — for reading AST patterns only, including its `CLAUDE.md`.
- **Project Independence.** An encoder skill package must never reference the decoder.
  `obfuscator.md`'s version thresholds are decoder-side knowledge *about* the encoder, which the
  decoder→encoder exception permits — but a new `skills/javascript-obfuscator/` package must
  establish the 5.5.0 shapes from `src/` independently, without citing the plugin. Grep the
  encoder package for `decode-js` before considering any doc pass done.
- **Reversal lives only in the decoder.** Encoder transform docs never assert how to reverse
  themselves.
- **Decoder work branches inside the submodule**, never on this hub branch, never from a
  detached HEAD.
- **Pin gate.** The 5.5.0 pin does not move until the decoder has been run against real 5.5.0
  output and confirmed to hold.
- **Measured figures are diary.** Counts and ratios belong here with their date and the command
  that produced them, never in a skill doc as a bare value.

## 12. Loose ends (unrelated, untouched)

- `encoder/javascript-obfuscator` is checked out **on branch `master`, one commit behind
  `origin/master`**, rather than detached at the 5.5.0 tag. HEAD still matches the hub's gitlink,
  so nothing is inconsistent now — but a stray `git pull` there would move the encoder out from
  under the pin gate silently. Worth tightening separately.
- Untracked `check-git-email.sh` at the hub root, carried onto this branch from `main`. Not part
  of any skill package. Left alone; keep it out of any commit unless the user says otherwise.

## 13. History

Oldest first; 1–17 are 2026-08-07. Kept short — the durable content is above.

1. Branch created; prior art surveyed. Found the decoder already targets this encoder and that
   upstream ships its own `CLAUDE.md`.
2. Work plan opened; "determine the version set" agreed as the first item.
3. Two-phase structure agreed; resolved that decode-js has no dependency pin, so the claim under
   test is the plugin source's own `stringArrayV3 >= 2.19.0`. Found there are no obfuscator test
   fixtures at all.
4. 5.5.0 split into its own phase — the only submodule-built version, and the one the Pin Gate
   reads.
5. Work plan rewritten whole after four rounds of patching left it disjointed.
6. Deliverable settled: a **new** entry, since the existing plugin is widely used.
7. Main target stated: a version-aware decoder. Verified the existing plugin fuses detection and
   decoding.
8. Three architecture decisions (coverage scope, shared-visitor reuse, refuse-on-unknown-era);
   version-suffixed entry name ruled out.
9. Entry named `obfuscatorx`; derivation sequenced after phases 1–2.
10. **Correction:** the decoder's version boundaries are sample-derived evidence, not unverified
    claims — so the derivation's job is completeness, not correctness. Recorded the prevalence
    signal they also carry.
11. Sandbox/harness layout designed.
12. **First execution work.** Eight encoder versions installed; all three hazards retired.
    **Two corrections:** option *types* drift as well as names, and unknown option names are
    silently ignored rather than validated — forcing the option-efficacy oracle.
13. Code/doc layout: splitting rule, naming by shape, doc layout falling out of code layout.
14. Multi-era doc layout designed after the era-varying Downstream/Upstream Effects problem;
    verified the encoder's real ordering mechanism; per-era SHAs including the newest.
15. Read-only compatibility check against js-confuser: clean, zero URL edits. Closed a design gap
    — removed eras cannot be documented from a pinned tree, which per-era SHAs resolve.
16. This file reorganized: important-first ordering, one doc-layout section instead of three,
    heading levels made consistent, and the 123-line `Last updated` blob replaced by this log.
    Resolved a contradiction it had been carrying — that encoder docs could only use
    version-tagged sections because the submodule is pinned — which per-era SHAs supersede.
17. Convention revision landed: `1871f23` (`doc-conventions.md`), `49d0fde` (`SKILL.md`).
    Design work is finished; phase 1 is the next thing to run.
18. **2026-08-08.** Phase 1 first detailed into ordered steps. Read `encoder-decoder-method.md` in full,
    closing §10's partial read. Four findings from grounding the plan against the tree: the
    plugin's unconditional console trace supplies the detection *and* per-stage instruments with
    no source edit (§7.6); its module-scope isolated-vm context makes one-subprocess-per-decode a
    correctness requirement (§7.6); the known/unknown option asymmetry is an enumerator, and the
    2.x option surface looks uniform (§8.2); every phase-1 version has a submodule tag, exposing
    an era-SHA provenance question. Two decisions (user): scripts disposable with tracked
    recipes, which also removes a submodule→hub reference the old §7.2 design required; and
    passing cells graduate to `test/obfuscator/` now rather than waiting for `obfuscatorx`.
19. **2026-08-08.** Provenance question closed by measurement — npm's published `gitHead` equals
    the submodule tag for all eight versions (§8.5), so submodule history is readable per
    version and era rows carry real SHAs. Two plan corrections followed: the combined-option sets
    become the encoder's own shipped presets rather than mixes we invent, and every phase-1 step
    got the detail the middle ones already had. Superseded bookkeeping pruned throughout — this
    log is where a change belongs, not an annotation beside the rule.
20. **2026-08-08. Structural correction (user).** A phase is **not** a verification exercise: it
    is one era-slice carried end to end — study the encoder, verify, write the decoder — and
    phases 2 and 3 enlarge coverage the same way. §3.6.1 had said this all along ("`obfuscatorx`
    covers the versions verified in phases 1 and 2"); §4.1's "split by what decode-js claims" was
    misread as phase *content* when it describes the phase *boundary*.
21. **2026-08-08. Second structural correction (user), on the same section.** The three behaviors
    combine **inside each step** rather than as sequential stages, so each step's outcome is
    solid and a late finding cannot force a backwards rewrite. Two defects in the stage-split it
    replaced, both caught by the user's challenge rather than by review: oracle 5's subject list
    is encoder knowledge, so verifying before studying defines the census from the thing under
    test; and a fixture pins a *claim*, so graduating fixtures before the encoder study yields a
    name inventory. The encoder's own 155 `.spec.ts` files — the method doc's "free and
    authoritative case list" — were unused by the plan until this pass. Phase 1 is now a small
    foundation (F1–F5) plus vertical units on one seven-part loop, closing on the preset ladder.
22. **2026-08-08. Unit order corrected (user).** The unit list had been taken from
    `plugin/obfuscator.js`'s own pass order and then cited the same plugin as corroboration —
    circular, and the exact mistake W4's corollary names. Re-derived from
    `JavaScriptObfuscator.ts` and each transformer's declared stage (§8.6): a normalization unit
    for `Simplifying`/`Finalizing` was missing entirely though it reverses first and is W1's own
    failure class; `Converting` sits *before* `StringArray`, so object/member decoding is fourth
    rather than last; the anti-tamper trio is injected at `Preparing`, which is the real reason
    it reverses last. Also found: a transformer declares several stages, so units are not a
    partition, and the existing plugin's `decodeObject`-before-`decodeGlobal` ordering
    contradicts the stage order — logged for U4 to resolve from source rather than assumed.
    Two clarifications landed with it: the existing plugin's decode functions are a **reading
    aid** per unit, never the source of order; and the integrated preset step builds
    `obfuscatorx`'s workflow **from scratch** rather than following the existing 12-step
    sequence, since a defect can sit in the ordering itself and a copied linear order forecloses
    scheduling a pass twice.
23. **2026-08-08.** Repo-structure drift raised (user) and measured across eleven tags. The doc
    tree mirrors **the pin only**, docs are keyed on shape, and per-era file paths are item-3
    rows — §6.2, landed as `d4b898e`/`ff9de57`. The measurement that decided it: `2.15.3 → 2.15.4`
    changes **zero** files yet is an era boundary, and `2.18.1 → 2.19.0` changes three files none
    of which are string-array, though it is the `stringArrayV3` boundary. Structural drift and
    shape drift are independent axes, so a file-keyed doc tree tracks the wrong one. Also found:
    major bumps are near no-ops structurally (3.0.0 is +1/−1), and the churn concentrates inside
    phase 1's own range. **Correction:** an earlier reading of this drift compared only 2.9.6
    against the pin and reported per-version deltas that were cumulative over sampled gaps.
24. **2026-08-08.** Generalized (user): a package's layout is keyed on the components every
    encoder has — order, options, transforms, templates — not on any encoder's directory habit,
    with an optional `source-map.md` crossing between them. `skills/js-confuser/` had already
    converged on exactly that, and its Skill Layout section already justified departing from its
    source tree, so the revision writes down settled practice. Landed as `d4b898e`
    (`doc-conventions.md`) and `ff9de57` (`SKILL.md`), which also fixed the ambiguity that caused
    the question: Source-Tree Mirroring opened with a broad clause and narrowed afterwards, and
    Root File Scope's "verified source-tree layout" read as the submodule's tree.
