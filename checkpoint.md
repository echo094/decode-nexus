# Checkpoint — javascript-obfuscator study

Working notes for the `docs-javascript-obfuscator` hub branch. **Not a skill doc** — scratch
tracking only: status, decisions, pointers, open questions. Per `SKILL.md` the only copy of a
fact never lives here; anything settled graduates into a skill doc and is pruned from this
file.

Scope spans `encoder/javascript-obfuscator` (read-only) and `decoder/decode-js` (editable),
per the decoder→encoder exception in `SKILL.md`.

**Status: 2026-08-07.** Planning and design complete; hazards retired against real installs.
Nothing committed, no tracked file changed. Full history at the end of this file.

---

## 1. Next actions

In order.

1. ~~Apply the multi-era convention revision~~ — **done 2026-08-07**, `1871f23`
   (`doc-conventions.md`) and `49d0fde` (`SKILL.md`).
2. **Phase 1** — §4.2. Per-feature *and* combined-option samples across the eight 2.x
   versions, run against the existing plugin. **Next.**
3. **Phase 2** — §4.3. The 5.5.0 pin, built via `git archive` out of the submodule.
4. **Version derivation** — §4.5, then phase 3.

The convention now expects an era registry (`versions.md`) once a package documents a second
era. `skills/javascript-obfuscator/` does not exist yet, so its registry gets written when
phase 1 produces the first real shape evidence — not before, since a registry row carries a
verified SHA and a shape signature, neither of which is known yet.

**Carry forward:** the shape names in §5.5 are provisional — derived from the decoder's
*description* of those shapes, not from output anyone has looked at. Confirm against phase 1's
real samples before anything is named on disk.

## 2. Main target

**Design a version-aware decoder for javascript-obfuscator.** Not a patch and not a survey: a
new decode-js entry whose architecture is multi-era by construction — it **detects** which
encoder era produced a sample, then **decodes with that era's strategy**. The doc layout
carries the same multi-era shape. The verification phases (§4) serve this target: they
establish what the eras are and where the existing plugin's claims fail.

**Downstream requirement (user):** the result feeds a future js-confuser study, so the
*architecture* must generalize beyond this encoder. That has a Project Independence
consequence — see §6.5.

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

### 4.1 Phase structure

Split by **what decode-js claims**, not by version number.

Ordering rationale: a phase-1 failure is *interpretable* — it means the problem is not version
drift, and a phase-2 failure afterwards cannot be read as a version finding at all. Starting at
the pin would lose that.

### 4.2 Phase 1 — every detector branch decode-js claims

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

### 4.3 Phase 2 — the pin, 5.5.0

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

## 6. Doc layout — multi-era

Designed and **applied** 2026-08-07 — `doc-conventions.md` in `1871f23` (new "Documenting
Multiple Eras" section, plus era rules folded into items 2–5, `## Fixtures`, and the
reference form) and `SKILL.md` in `49d0fde` (pin-bump step 4). The rest of this section is
the reasoning behind those edits, kept until it graduates into the encoder package.

### 6.1 Why the existing convention is not enough

Item 4 of the transform-doc structure (Downstream Effects / Upstream Effects) describes *edges*
between passes, so a single ordering change rewrites many transforms' item 4 at once — which
version-tagged prose cannot absorb.

**Verified mechanism:** the encoder's flat `nodeTransformersList`
(`src/JavaScriptObfuscator.ts:64`) is **not** the execution order. Order comes from the
`NodeTransformationStage` sequence (Initializing → Preparing → DeadCodeInjection →
ControlFlowFlattening → RenameProperties → Converting → RenameIdentifiers → StringArray →
Simplifying → Finalizing), and *within* a stage from a topological sort built by
`nodeTransformerNamesGroupsBuilder.build()` (`NodeTransformersRunner.ts:80`) out of each
transformer's declared dependencies. So effective order can drift two ways: the stage enum
changes, **or one transformer's declared dependency changes — which appears in neither the
CHANGELOG nor the list.** That is how era-varying downstream effects arise unnoticed.

### 6.2 Where era divergence resolves, per item

| Item | If it differs by era | Why |
|---|---|---|
| 1. Target | never diverges | if the purpose changed it is a different transform |
| 2. Algorithm | **split into a separate doc + code file** | this *is* §5.1; item 2 is where the split is decided |
| 3. Implementation | era-tagged table rows | node shapes, helper names, thresholds — parameter-level |
| 4. Downstream/Upstream Effects | **era column on the spelling table** | edges change wholesale when order changes |
| 5. Known Quirks / Gaps | era-scoped entry | a quirk can exist in only some eras |
| `## Fixtures` | era column | a fixture pins a claim *at an era* |

Item 2 is the hinge: an algorithm-level divergence never becomes a tagged section, it becomes a
new file; everything below it stays in one doc as rows.

**Tables, never duplicated prose** — not a new principle, the existing one generalized.
`doc-conventions.md` already requires spellings as a table because prose "hides the only thing
worth knowing: which spelling nobody implemented." Era-tagged prose hides *which era nobody
covered*. Same failure, same fix.

### 6.3 New artifact: the era registry

`versions.md` in the encoder package. One row per era: **era ID, version range, verified commit
SHA, observable shape signature.**

- **Docs cite era IDs, never inline version ranges.** Twenty docs saying "≥ 2.19.0" means twenty
  edits and some misses when the boundary turns out to be 2.18.0; twenty docs saying
  `E-fn-wrapped` means one edit. Same reasoning as §5.4, applied to prose.
- **Required only once a package documents more than one era**, so existing single-era packages
  are not retroactively non-compliant.

### 6.4 Permalinks: every era uses its own SHA, including the newest

The current rule pins hub→submodule citations to the hub's `main` gitlink. That special-cases
"current" — and *"current" is a property of when a doc was written, not of what it describes* —
so such a doc goes wrong at the next pin bump without anyone editing it. Uniform rule: every
era, newest included, is cited by the SHA in its registry row.

- That SHA is **the commit the era's claims were verified against**, not whatever the pin
  happens to be — consistent with the Pin Gate, where a recorded claim always names the commit
  that proved it. It does not drift on a pin bump by default; it moves only on re-verification.
- The old rule's real guard — *don't cite whatever your local checkout happens to be at* —
  survives, restated as "the SHA comes from the registry."
- **This supersedes** the earlier note in this file that encoder docs could only ever use
  version-tagged sections "because the submodule is pinned to one commit." Era rows with their
  own SHAs reach into submodule *history*, so a pinned checkout is no longer the limit.

### 6.5 Where the generalizable pattern lives

`SKILL.md`'s Project Independence rule forbids a skill package from referencing another project
but states that **cross-project observations belong in a separate note**. The reusable parts —
detect-then-dispatch, the era concept, era IDs, era-tagged tables — are exactly that, so they go
in **hub-level docs** (`doc-conventions.md`, or a note sibling to `encoder-decoder-method.md`),
never inside `skills/javascript-obfuscator/` or `skills/decode-js/`. The future js-confuser
study then reads the hub doc and neither package references the other. **The convention revision
is itself the cross-project note** for the doc half.

### 6.6 Compatibility check against js-confuser (read-only, 2026-08-07)

- The encoder package holds **153 permalinks, all pinned to `31c5a47…` — exactly the hub's
  gitlink**. Under this design that SHA simply becomes the era's registry SHA: same value,
  different reason. **Zero URL edits**, and essentially no version-range prose to convert.
- The **decoder** side already does era handling ad hoc across at least four files with informal
  vocabulary (`pre-2.0`, `1.x`, `legacy`): `anti-tooling.js` targets legacy 1.x output,
  `control-flow.md` carries a pre-2.0 legacy path, `plugins/jsconfuser.md` runs
  pre-2.0-vs-current naming throughout. The revision formalizes practice rather than adding
  work.
- Independent corroboration for §5.4: `plugins/jsconfuser.md` already keeps legacy visitors
  because each "names the *shape* the encoder replaced, which is what a legacy sample still"
  needs.

**Design gap found by that check, and closed.** The registry was specified as *encoder-package*
content since eras are encoder knowledge — but js-confuser's encoder package has **no** era
content precisely because those shapes were **removed** from the encoder; the knowledge survives
only decoder-side, attached to samples still met in the wild. A package pinned at current source
cannot describe a shape that no longer exists in it. **Resolution:** era rows carry their own
SHA (§6.4), so a removed era is documented by pointing into submodule history. The per-era-SHA
rule earns its keep twice — future-proofing was the stated reason; enabling removed-era
documentation at all is the larger one.

### 6.7 Scope

Applying this touches `SKILL.md` as well as `doc-conventions.md`: pin-bump step 4 becomes
"decide whether the new pin is still the same era — if yes, optionally re-verify and advance
that era's SHA; if no, open a new era row." Both are `docs(hub)` commits, separate from the
study's own scope.

## 7. Sandbox & harness

Designed 2026-08-07; hazards retired (§8.3). Not yet built beyond the encoder installs.

### 7.1 Governing principle: the harness is tracked, the artifacts are disposable

`/sandbox-tests/` is gitignored, so anything living only there evaporates on a clean checkout.
Split by *durability*: **tracked** — harness code, input fixtures, option-set definitions, the
version matrix, graduated fixtures. **Disposable** — `node_modules`, encoder builds,
encoded/decoded samples, run reports.

### 7.2 Where each piece lives

- **decode-js (tracked, branch inside the submodule)** — the **generic runner**: takes encoded
  samples, runs a named plugin, applies the oracles, emits a report. Encoder-agnostic, so
  js-confuser can reuse it unchanged. Plus `test/obfuscatorx/` for graduated fixtures.
- **hub (tracked)** — the **recipe**: version matrix, per-version option keys *and values*,
  plaintext input fixtures, and the script that materializes encoders into the sandbox.
- **`sandbox-tests/` (gitignored)** — everything generated.

```
sandbox-tests/
  encoders/
    package.json        # npm aliases, one install for all phase-1 versions
    node_modules/
    5.5.0-pin/          # git archive of the pin, built in place
  out/<version>/<fixture>__<optionset>.js       # encoded
  decoded/<version>/<fixture>__<optionset>.js   # decoded
  report/<timestamp>.json
```

**Open:** the hub's `.gitignore` header calls it a "Pure Spec Hub," which argues against
executable recipe code living there. If that reading wins, the recipe moves into decode-js
beside the runner and the hub keeps only the matrix as data.

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

Fixtures are small, deterministic and **self-reporting** — each prints a deterministic result so
runtime equivalence is checkable by comparing stdout. Between them they must exercise string
literals (string array), branching (control-flow flattening), object literals and member access
(transformer/`SplitString`), dead code, and functions/closures.

Option sets are keyed **per version**, because names *and types* drift (§8.2): `baseline`,
`no-rotate` (reaches the V0 shape), `wrappers`, `chained-calls`, `dead-code`, `cff`,
`self-defending`, `debug-protection`, `console-output`.

**Plus combined-option sets, per era** — a `high-obfuscation`-preset-style mix.
`encoder-decoder-method.md`'s W1 is explicit that a later stage invalidates an earlier matcher
*silently and totally*, and that "a matcher validated only against an isolated single-transform
fixture is not proven robust to real combined output." If pipeline order varies by era (§6.1), a
matcher validated at one era fails closed at another for reasons unrelated to its own transform.
Per-feature sets structurally cannot detect that.

### 7.6 Oracles, recorded separately per (version × option set × fixture)

1. **Detection** — which era/detector fired, or none. For the existing plugin: which of
   V3/V2/V0 matched, or `false`. Recorded even when later stages fail, since this is the
   diagnostic the current design cannot produce.
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

**Execution rule (measured, not assumed — §8.3):** only `debugProtectionInterval` samples are
excluded from execution in encoded form. Plain `debugProtection` and `selfDefending` run
normally as emitted. The subprocess timeout is mandatory for every run regardless, and this rule
is re-measured per era rather than generalized from 2.19.0.

### 7.7 Graduation to permanent fixtures

Convention verified from `test/jsconfuser/`: a case is the triple `<name>.src.js` (plaintext),
`<name>.js` (encoded input), `<name>.fix.js` (expected decode), driven by
`getPluginResult(plugin, fix, input)` in `test/helper.js` with **exact string equality**.
Graduated cases land in `test/obfuscatorx/` following that triple, named `<era>-<optionset>`.

Since the plugin has **no existing fixtures at all** (§8.4), graduation is not optional polish —
it is the first regression baseline this target has ever had.

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

  **This corrected an earlier note in this file that claimed the opposite.** The conclusion — a
  shared options file cannot span the matrix — holds, but the reason inverts and is worse than a
  loud failure: `stringArrayRotate` on a 2.x build does not error, it silently encodes with
  rotate at its default, yielding a sample that does not test what the matrix says it tests.
  Forces oracle 6 (§7.6).
- **3.2.0 added `stringArrayCallsTransform`**, post-dating every fingerprint the decoder holds —
  the main reason phase 3's range is a candidate blind spot rather than a safe interpolation.

### 8.3 Hazards — all retired

Probed empirically against real installs before building anything. Scripts in
`sandbox-tests/encoders/` (`smoke.cjs`, `hazard2.cjs`, `seedcheck.cjs`, `optcheck.cjs`);
disposable, rerunnable after `npm install` there.

**1. Old versions under Node 26 — no issue.** All eight phase-1 versions installed from one
npm-alias tree and encoded successfully under Node v26.5.0. No pinned older runtime needed; the
npm-alias approach works as designed.

**2. Execution hazard — retired, and it had been recorded too broadly.** Measured at 2.19.0:

| Option set | Result |
|---|---|
| baseline | ran, stdout matches |
| `selfDefending` | ran, stdout matches |
| `debugProtection` | **ran, stdout matches** |
| `debugProtection` + `debugProtectionInterval` | **timed out (~5 s bound)** |
| `disableConsoleOutput` | ran, stdout matches |

Corrections: plain `debugProtection` does **not** hang — a `debugger` statement is a no-op
without an inspector attached; only the **interval** variant hangs, via a `setInterval` holding
the event loop open. `selfDefending` is safe to execute as emitted; it only misbehaves when the
code is reformatted. `disableConsoleOutput` did **not** suppress stdout, so the
runtime-equivalence oracle survives for it. The timeout mechanism caught the runaway cleanly.

**3. `seed` reproducibility — confirmed.** Same seed gives byte-identical output, different
seeds differ, on 2.9.6 / 2.12.0 / 2.15.4 / 2.19.0 — including with `deadCodeInjection` and
`controlFlowFlattening` enabled, the most randomness-heavy settings.

### 8.4 No existing baseline

`decoder/decode-js/test/` contains `jsconfuser/`, `sojsonv7/`, `utility/`, `visitor/`,
`helper.js` — and **nothing for `obfuscator`**, despite it being the largest plugin. There are
no regression fixtures for it.

## 9. Open items

- **Phase 2's core question**, unanswerable by reading: does 5.5.0 still emit a string array
  that `stringArrayV3`'s `checkPattern` fingerprint matches? The probe, applied per phase: build
  real output at the target version, run the plugin, observe whether `decodeGlobal` finds a
  `stringArrayName` or returns `false` — which aborts the whole plugin, not just that detector.
  Forks the work the same way at every phase: **detector matches** → documentation job on a
  working decoder; **detector misses** → repair job, and doc work follows the fix rather than
  describing something broken.
- **Recipe placement** — hub vs. decode-js, given the "Pure Spec Hub" framing (§7.2).
- **Shape names** are provisional until phase 1 (§5.5).

## 10. Required reads

From `SKILL.md`'s Standing Rules — **not from memory of a previous session**:

- [skills/doc-conventions.md](skills/doc-conventions.md) — **read in full, 2026-08-07**, before
  the doc-layout design.
- [skills/encoder-decoder-method.md](skills/encoder-decoder-method.md) — **partially read**
  2026-08-07: section index and T1·W1·W4 in full. The rest is unread and must be read before
  touching a submodule or its skill docs.

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

All 2026-08-07, oldest first. Kept short — the durable content is above.

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
