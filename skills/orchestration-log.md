# Orchestration Log

The data companion to [orchestration.md](orchestration.md): that file owns the rules and recording
procedure; this one preserves the completed runs that calibrate them. Read it when setting or
challenging a sizing rule, not during ordinary dispatch.

Dispatch predictions and outcomes are immutable. Measured columns may be recomputed from surviving
session logs when the schema or extractor changes; predictions are never backfilled and outcomes
are never revised. Any guideline derived from this file cites its source rows.

## Obtaining the figures

Metric definitions live in [orchestration.md](orchestration.md); harness arithmetic lives in each
bootloader's extractor. `evidence read` counts artifact content actually loaded by the main agent,
using attributed tokens where available or characters divided by four and marked `~`. Cache
regressions remain part of `total fresh`; classify compaction only from an explicit harness event.

### Each agent writes its own extractor

Transcript formats are per-harness. Each bootloader owns an executable extractor in `tools/`; all
extractors must preserve these invariants:

- Start at the child-targeted dispatch boundary; ignore inherited parent usage.
- Use one per-request usage snapshot per request; ignore zero-valued and completion notifications.
- Respect subset relationships between fields and select the last output-bearing turn for `report`.
- Aggregate transcripts mechanically; never load one into model context.
- Run the extractor against real transcripts and independently check the `report` value.

## Rows

| Run | Task | Transcript | Model · effort | Window | `peak context` | `first fresh` | pred `workload` | `total fresh` | `output` | `report` | `workload` | `evidence read` | `workload`/`delegation cost` | `workload`/`main intake` | Cache regressions / replay lower bound | `compactions` | Wall |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-08-16.4 | extend scope-wrapper + property-name release sweeps, read-only | eb825ed7 | gpt-5.6-sol · medium | 258.40k | 71.33k | 4.51k | 45.00k¹ | 77.21k | 14.84k | 0.28k | 87.54k | ~3.62k | ~91.24% | ~22.50× | 0 / 0.00k | 0 | 5m |
| 2026-08-16.5 | extend class-field + object-keys release sweeps, read-only | a4da823f | gpt-5.6-sol · medium | 258.40k | 78.51k | 2.46k | 45.00k¹ | 96.47k | 13.42k | 0.67k | 107.43k | ~3.42k | ~94.25% | ~26.28× | 1 / 14.34k | 0 | 5m |
| 2026-08-16.6 | extend numeric-expression + template release sweeps, read-only | 8c5289a5 | gpt-5.6-sol · medium | 258.40k | 79.36k | 2.46k | 35.00k¹ | 87.13k | 16.33k | 0.18k | 101.00k | ~2.59k | ~95.09% | ~36.54× | 0 / 0.00k | 0 | 6m |
| 2026-08-17.1 | map full subagent startup accounting, read-only | fbe1c1dd | gpt-5.6-sol · medium | 258.40k | 61.87k | 4.48k | 25.00k | 78.80k | 11.24k | 0.11k | 85.56k | ~1.85k | ~93.00% | ~43.74× | 3 / 8.19k | 0 | 4m |
| 2026-08-17.2 | distinguish cache-miss causes, read-only | cae8c630 | gpt-5.6-sol · medium | 258.40k | 81.34k | 2.41k | 30.00k | 83.88k | 14.48k | 0.06k | 95.95k | ~1.76k | ~95.79% | ~52.84× | 0 / 0.00k | 0 | 5m |
| 2026-08-17.3 | survey the `3.0.0`/`3.0.1` corpus append and checks, read-only | 860081f8 | gpt-5.6-sol · medium | 258.40k | 81.65k | 4.98k | 12.00k | 79.55k | 8.37k | 0.24k | 82.94k | ~2.62k | ~91.36% | ~29.00× | 0 / 0.00k | 0 | 3m |
| 2026-08-17.4 | build and classify the `3.1.0`/`3.2.0` boundary; resume after alias install; isolate `stringArrayCallsTransform` | bc8bd49b | gpt-5.6-luna · xhigh | 258.40k | 182.27k | 4.38k | 145.00k² | 354.84k | 51.15k | 0.38k | 401.61k | ~12.13k | ~95.96% | ~32.10× | 1 / 87.04k | 0 | 36m |
| 2026-08-17.7 | pin and repair the `3.2.0` calls-transform composition gap | 08ef9287 | gpt-5.6-luna · xhigh | 258.40k | 222.85k | 4.30k | 55.00k | 530.82k | 43.39k | 0.22k | 569.90k | ~2.59k | ~98.77% | ~202.81× | 1 / 208.90k | 1 | 18m |
| 2026-08-17.8 | build and classify the `3.2.0`/`3.2.2` boundary | 7bdd9c30 | gpt-5.6-luna · xhigh | 258.40k | 130.63k | 4.41k | 120.00k | 161.42k | 26.17k | 0.38k | 183.19k | ~2.77k | ~96.04% | ~58.16× | 0 / 0.00k | 0 | 24m |
| 2026-08-17.10 | build and certify the `4.1.1` high-end control | dac2beb9 | gpt-5.6-luna · xhigh | 258.40k | 147.57k | 4.41k | 145.00k | 182.28k | 27.05k | 0.23k | 204.92k | ~2.26k | ~96.74% | ~82.30× | 0 / 0.00k | 0 | 16m |
| 2026-08-17.11 | repair the `4.0.0` debug-protection interval boundary | 929a9c22 | gpt-5.6-luna · xhigh | 258.40k | 139.02k | 0.28k | 45.00k | 161.19k | 25.99k | 0.20k | 186.90k | ~1.25k | ~99.08% | ~128.90× | 0 / 0.00k | 0 | 10m |
| 2026-08-17.14 | strip the transformed inline interval resolver | 81224c92 | gpt-5.6-luna · xhigh | 258.40k | 226.51k | 4.36k | 35.00k | 294.43k | 32.78k | 0.43k | 322.85k | ~1.30k | ~98.15% | ~186.62× | 0 / 0.00k | 1 | 14m |
| 2026-08-17.15 | finish the `4.1.1` browser-target boundary certification | 84f29c53 | gpt-5.6-luna · xhigh | 258.40k | 209.00k | 4.40k | 120.00k | 259.77k | 34.91k | 0.42k | 290.28k | ~3.13k | ~97.33% | ~81.77× | 0 / 0.00k | 0 | 6m |
| 2026-08-17.16 | close the `4.1.0` service-worker helper boundary | 071e6bf5 | gpt-5.6-luna · xhigh | 258.40k | 173.98k | 0.31k | 55.00k | 207.77k | 39.90k | 0.40k | 247.35k | ~2.57k | ~98.69% | ~83.28× | 0 / 0.00k | 0 | 17m |
| 2026-08-17.17 | repair the service-worker interval resolver at its inverse transform | e88914ca | gpt-5.6-luna · xhigh | 258.40k | 217.26k | 0.30k | 45.00k | 246.34k | 27.99k | 0.30k | 274.03k | ~1.22k | ~99.34% | ~180.28× | 0 / 0.00k | 0 | 10m |
| 2026-08-17.18 | classify the `4.1.1`/`4.2.0` source boundary | b63a1574 | gpt-5.6-luna · xhigh | 258.40k | 224.35k | 4.37k | 105.00k | 248.16k | 34.65k | 0.91k | 278.45k | ~7.98k | ~95.46% | ~31.32× | 0 / 0.00k | 0 | 12m |
| 2026-08-17.19 | build and certify the frozen `4.2.0` ordinary column | cd1b7dd7 | gpt-5.6-luna · xhigh | 258.40k | 205.44k | 0.29k | 135.00k | 262.28k | 47.08k | 0.34k | 309.07k | ~2.49k | ~99.00% | ~109.21× | 0 / 0.00k | 0 | 3m |
| 2026-08-17.20 | build the six focused `4.1.1`/`4.2.0` transform axes | 8cb544bb | gpt-5.6-luna · xhigh | 258.40k | 174.21k | 0.28k | 155.00k | 220.91k | 29.20k | 1.00k | 249.83k | ~2.60k | ~98.47% | ~69.40× | 0 / 0.00k | 0 | 13m |
| 2026-08-17.21 | repair the `4.2.0` optional-call CFF inverse | b1b2c33e | gpt-5.6-luna · xhigh | 258.40k | 147.24k | 0.33k | 75.00k | 181.72k | 24.15k | 0.13k | 205.54k | ~1.47k | ~99.07% | ~128.46× | 0 / 0.00k | 0 | 10m |
| 2026-08-23.1 | audit the global-variable prelude era and `browser-no-eval` coverage, read-only | 25403434 | gpt-5.6-luna · xhigh | 258.40k | 152.16k | 6.12k | 18.00k | 168.56k | 23.17k | 0.38k | 185.61k | ~2.03k | ~95.61% | ~77.02× | 0 / 0.00k | 0 | 10m |
| 2026-08-23.3 | build focused `5.1.0`/`5.2.0` axis controls | 0ea92e83 | gpt-5.6-luna · xhigh | 258.40k | 164.97k | 1.29k | 150.00k | 171.74k | 26.61k | 0.35k | 197.06k | ~1.74k | ~98.31% | ~94.29× | 0 / 0.00k | 0 | 9m |
| 2026-08-23.4 | audit the `5.2.0` directive-removal era, read-only | 0119839a | gpt-5.6-luna · xhigh | 258.40k | 167.21k | 5.96k | —³ | 202.85k | 26.14k | 0.58k | 223.03k | ~1.76k | ~96.41% | ~95.31× | 0 / 0.00k | 0 | 9m |
| 2026-08-23.6 | output-verify the `5.2.1` loop-body object boundary | 8da0b723 | gpt-5.6-luna · xhigh | 258.40k | 114.11k | 1.34k | 190.00k | 115.54k | 28.47k | 0.42k | 142.67k | ~8.19k | ~93.48% | ~16.57× | 0 / 0.00k | 0 | 11m |
| 2026-08-23.7 | build and classify the `5.3.1`/`5.4.0` ordinary boundary | ba9ff977 | gpt-5.6-luna · xhigh | 258.40k | 144.90k | 6.54k | 240.00k | 207.54k | 29.62k | 0.21k | 230.62k | ~4.65k | ~95.29% | ~47.45× | 0 / 0.00k | 0 | 16m |
| 2026-08-23.8 | output-verify the two `5.4.0` reserved-class axes | c595c018 | gpt-5.6-luna · xhigh | 258.40k | 84.27k | 1.41k | 180.00k | 82.94k | 21.94k | 0.52k | 103.47k | ~1.08k | ~95.03% | ~51.84× | 0 / 0.00k | 0 | 7m |
| 2026-08-23.9 | output-verify the `5.4.0` object sequence-position boundary | 9edf93fb | gpt-5.6-luna · xhigh | 258.40k | 58.33k | 1.45k | 190.00k | 52.33k | 14.63k | 0.71k | 65.52k | ~1.05k | ~95.34% | ~37.23× | 0 / 0.00k | 0 | 5m |
| 2026-08-23.10 | build and classify the `5.4.2`/`5.4.3` ordinary boundary | 52225cde | gpt-5.6-luna · xhigh | 258.40k | 178.74k | 1.21k | 240.00k | 213.36k | 28.76k | 0.85k | 240.91k | ~6.55k | ~96.55% | ~32.56× | 0 / 0.00k | 0 | 12m |
| 2026-08-23.11 | output-verify the `5.4.3` optional/plain wrapper-reuse boundary | ae70f711 | gpt-5.6-luna · xhigh | 258.40k | 115.95k | 1.32k | 175.00k | 131.46k | 34.80k | 0.45k | 164.94k | ~1.66k | ~97.96% | ~78.17× | 0 / 0.00k | 0 | 12m |
| 2026-08-24.12 | build and classify the `5.4.4`/`5.4.5` ordinary boundary | 4896392b | gpt-5.6-luna · xhigh | 258.40k | 235.75k | 4.01k | 240.00k | 539.42k | 46.11k | 1.25k | 581.53k | ~8.30k | ~97.72% | ~60.89× | 1 / 134.14k | 1 | 29m |
| 2026-08-24.13 | output-verify the `5.4.5` self-defending newline-bail boundary | 27fd5204 | gpt-5.6-luna · xhigh | 258.40k | 192.68k | 0.94k | 185.00k | 236.17k | 28.43k | 0.27k | 263.67k | ~2.30k | ~98.69% | ~102.60× | 0 / 0.00k | 0 | 13m |
| 2026-08-24.14 | output-verify the `5.4.5` wrapper-shape and generator-parenthesis boundaries | 54c78781 | gpt-5.6-luna · xhigh | 258.40k | 193.29k | 1.04k | 215.00k | 240.81k | 38.78k | 0.21k | 278.55k | ~1.35k | ~99.08% | ~178.56× | 0 / 0.00k | 0 | 17m |
| 2026-08-24.15 | audit every `5.4.0`–`5.4.7` release-note item and repair provenance validation | bf5d85aa | gpt-5.6-luna · xhigh | 258.40k | 253.78k | 0.99k | 230.00k | 315.21k | 41.76k | 0.15k | 355.98k | ~3.20k | ~98.80% | ~106.26× | 0 / 0.00k | 1 | 15m |
| 2026-08-24.16 | add durable decoder regressions for accepted `5.4.3`/`5.4.5` shapes | e1093b5f | gpt-5.6-luna · xhigh | 258.40k | 214.35k | 0.95k | 170.00k | 257.60k | 36.43k | 0.27k | 293.08k | ~1.80k | ~98.97% | ~141.58× | 0 / 0.00k | 0 | 13m |
| 2026-08-24.18 | output-verify the `5.4.6` escape/cache and `5.4.7` lone-surrogate fixes | e0746b4b | gpt-5.6-luna · xhigh | 258.40k | 244.38k | 0.92k | 230.00k | 318.34k | 34.69k | 0.42k | 352.11k | ~1.27k | ~99.26% | ~208.35× | 0 / 0.00k | 1 | 14m |
| 2026-08-24.19 | output-verify the `5.4.1` compact-keyword and domain-lock fixes | 163fc23b | gpt-5.6-luna · xhigh | 258.40k | 233.72k | 0.89k | 210.00k | 274.00k | 31.39k | 0.47k | 304.50k | ~1.09k | ~99.20% | ~195.19× | 0 / 0.00k | 0 | 12m |
| 2026-08-24.20 | output-verify the `5.4.4` RegExp-modifier and boolean-heritage fixes | 9cbd96f7 | gpt-5.6-luna · xhigh | 258.40k | 204.71k | 0.89k | 210.00k | 230.64k | 28.78k | 0.24k | 258.53k | ~3.24k | ~98.31% | ~74.29× | 0 / 0.00k | 0 | 10m |
| 2026-08-24.21 | graduate accepted `5.4.1`–`5.5.0` encoder evidence into durable javascript-obfuscator docs | 4616fc94 | gpt-5.6-luna · xhigh | 258.40k | 242.97k | 0.91k | 190.00k | 418.50k | 48.13k | 0.53k | 465.72k | ~32.00k | ~93.30% | ~14.32× | 0 / 0.00k | 1 | 18m |
| 2026-08-24.22 | graduate accepted 5.4.x decoder evidence into durable decode-js docs | 13a816d1 | gpt-5.6-luna · xhigh | 258.40k | 190.91k | 4.99k | 170.00k | 235.46k | 26.74k | 0.09k | 257.22k | ~3.00k | ~96.86% | ~83.24× | 1 / 5.12k | 0 | 10m |
| 2026-08-24.23 | close the remaining decoder-relevant `5.4.0` release-note backfill | e8da1223 | gpt-5.6-luna · xhigh | 258.40k | 181.95k | 1.11k | 220.00k | 207.92k | 34.05k | 0.38k | 240.86k | ~3.20k | ~98.08% | ~67.28× | 0 / 0.00k | 0 | 12m |
| 2026-08-24.24 | sample stable `2.x` decoder/output compatibility below the corpus floor | 96256c97 | gpt-5.6-luna · xhigh | 258.40k | 189.47k | 1.14k | 250.00k | 227.43k | 32.15k | 0.21k | 258.44k | ~4.00k | ~98.25% | ~61.39× | 0 / 0.00k | 0 | 12m |
| 2026-08-24.25 | repair `merge-object` on object-pattern declarators and add exact static-block regressions | 8a43db4e | gpt-5.6-luna · xhigh | 258.40k | 135.50k | 1.10k | 150.00k | 149.97k | 17.46k | 0.23k | 166.32k | ~5.00k | ~96.33% | ~31.79× | 0 / 0.00k | 0 | 7m |
| 2026-08-24.26 | graduate sampled stable-`2.x` wrapper evidence into durable era docs | 3007a515 | gpt-5.6-luna · xhigh | 258.40k | 219.30k | 1.14k | 140.00k | 259.90k | 27.58k | 0.16k | 286.33k | ~8.00k | ~96.85% | ~35.09× | 0 / 0.00k | 0 | 11m |
| 2026-08-24.27 | graduate remaining `5.4.0` release-note and `merge-object` repair evidence | 57beb06b | gpt-5.6-luna · xhigh | 258.40k | 228.54k | 1.13k | 190.00k | 337.44k | 40.85k | 0.37k | 377.17k | ~12.00k | ~96.56% | ~30.49× | 0 / 0.00k | 1 | 16m |
| 2026-08-24.28 | remove disposable sandbox scripts and specify the generated corpus-builder contract | 4b388d46 | gpt-5.6-luna · xhigh | 258.40k | 240.81k | 5.20k | 210.00k | 304.02k | 30.71k | 0.21k | 329.53k | ~8.00k | ~96.07% | ~40.14× | 0 / 0.00k | 1 | 12m |
| 2026-08-24.29 | regenerate and exercise all five corpus builders from the recipe in a clean room | e1dcbcdd | gpt-5.6-luna · xhigh | 258.40k | 114.95k | 5.33k | 300.00k | 146.10k | 33.79k | 0.43k | 174.56k | ~4.00k | ~94.73% | ~39.41× | 0 / 0.00k | 0 | 13m |
| 2026-08-24.31 | classify the bounded scoped Known Gaps and propose the restart questions | 7c0fe420 | gpt-5.6-luna · xhigh | 258.40k | 74.51k | 0.82k | —³ | 69.52k | 9.24k | 0.26k | 77.93k | ~1.72k | ~96.52% | ~39.36× | 0 / 0.00k | 0 | 3m |
| 2026-08-24.32 | audit the nested one-layer string-array fixture | b3ad0243 | gpt-5.6-luna · xhigh | 258.40k | 87.29k | 6.24k | 12.00k | 171.44k | 21.32k | 0.28k | 186.52k | ~1.06k | ~96.10% | ~139.30× | 1 / 71.68k | 0 | 7m |
| 2026-08-24.33 | remove stale and closed Known Gap wording | 62b06346 | gpt-5.6-luna · xhigh | 258.40k | 137.50k | 6.25k | 28.00k | 145.80k | 11.97k | 0.23k | 151.52k | ~0.50k | ~95.60% | ~207.92× | 0 / 0.00k | 0 | 4m |
| 2026-08-24.34 | add the direct outer-first nested-storage regression | 1388bf0b | gpt-5.6-luna · xhigh | 258.40k | 105.01k | 1.09k | 24.00k | 106.30k | 12.78k | 0.22k | 117.99k | ~0.60k | ~98.40% | ~143.37× | 0 / 0.00k | 0 | 4m |
| 2026-08-24.35 | add one focused class/logical producer cell | a87a4938 | gpt-5.6-luna · xhigh | 258.40k | 142.00k | 1.29k | 85.00k | 169.79k | 27.62k | 0.38k | 196.12k | ~1.43k | ~98.44% | ~108.35× | 0 / 0.00k | 0 | 10m |
| 2026-08-24.36 | remove runtime era reporting and its stale coverage policy | 6010b0de | gpt-5.6-luna · xhigh | 258.40k | 130.41k | 6.32k | 10.00k | 136.81k | 13.35k | 1.11k | 143.84k | ~0.44k | ~94.81% | ~92.80× | 0 / 0.00k | 0 | 5m |
| 2026-08-24.37 | add producer-faithful `browser-no-eval` helper support | f5fb1dac | gpt-5.6-luna · xhigh | 258.40k | 212.22k | 1.44k | 32.00k | 527.36k | 55.04k | 0.17k | 580.96k | ~0.79k | ~99.59% | ~605.17× | 1 / 196.61k | 1 | 22m |

¹ Predicted against an earlier definition of the column, so the committed value stands as event
history but is not numerically comparable with the `workload` beside it.
² The same child was resumed twice with `followup_task`, so the original task and both continuations
are one dispatch record. The prediction is the arithmetic sum of the three estimates committed
before their respective phases (`60.00k + 50.00k + 35.00k`), not a backfilled estimate. The measured
columns are the extractor's aggregate from the original dispatch boundary through final completion;
`evidence read` likewise sums the three acceptance reads, and wall time sums the completion
durations of the original turn and both resumed turns.
³ No workload prediction was committed before dispatch. It is not backfilled.

### Outcome

Only runs with rejected claims are listed below; every other row was accepted at 100% yield.
`packet` assigns the correction to task framing; `engineer` assigns it to the model, effort, or
task split.

| Run | Outcome | Claims ret → acc | Yield | Cause | Note |
|---|---|---|---|---|---|
| 2026-08-17.3 | accepted | 7 → 5 | 71% | engineer | rejected an over-broad set-membership rule and an invalid zero-tally requirement |
| 2026-08-17.4 | partially accepted | 15 → 13 | 87% | packet + engineer | rejected option-off collapse and generalized name-only-difference claims |
| 2026-08-17.7 | accepted | 12 → 11 | 92% | engineer | rejected mutation-before-gate; follow-up made reference handling transactional |
| 2026-08-17.19 | partially accepted | 8 → 7 | 88% | engineer | append-local immutability remained unproved after the snapshot was overwritten |
| 2026-08-23.1 | accepted | 9 → 8 | 89% | engineer | corrected overlapping era ranges |
| 2026-08-24.14 | accepted after repair | 11 → 10 | 91% | engineer | corrected a machine summary that contradicted its own rows |
| 2026-08-24.15 | accepted after repair | 30 → 29 | 97% | engineer | corrected a truncated commit SHA and added validation |
| 2026-08-24.16 | accepted after repair | 9 → 8 | 89% | engineer | rejected an exact-byte claim for newline-normalized fixtures |
| 2026-08-24.21 | accepted after repair | 14 → 12 | 86% | engineer | closed an era gap and relabeled failure-only rows as unreachable in output |
| 2026-08-24.22 | accepted after repair | 8 → 7 | 88% | engineer | corrected “information loss” to a runtime-semantics defect |
| 2026-08-24.26 | accepted after repair | 8 → 7 | 88% | engineer | relabeled `2.0.0` as a read floor rather than a transition |
| 2026-08-24.27 | accepted after repair | 12 → 10 | 83% | engineer | repaired incomplete era ranges and contradictory fixture prose |
| 2026-08-24.29 | accepted after repair | 10 → 9 | 90% | engineer | corrected a generated builder that scanned the robustness subtree |
| 2026-08-24.31 | accepted with one rejection | 16 → 15 | 94% | engineer | rejected an unsupported contiguous coverage-hole claim |

## What the rows have shown

Treat findings from one wave as hypotheses and revise them when later rows disagree.

- **Estimate release sweeps by transitions and indirect dependencies, not expected findings**
  (2026-08-16.4–.6). A sweep with no new output era still processed a full workload.
- **Use peak context and compactions to judge packing headroom** (2026-08-16.4–.6). Workload can
  exceed peak context; combine related tasks only with room for synthesis and spikes.
- **Measure launch cost from the child's first request, not packet size** (2026-08-17.1–.2).
  Harness framing and tool instructions dominate the visible spawn text.
- **Count main intake, not only the report** (2026-08-16.4–.6, 2026-08-17.1–.2). Evidence read from
  the shared filesystem is part of delegation cost.
- **Bounded questions can conceal unbounded evidence sweeps** (2026-08-17.1–.2); size the required
  source scan, not the wording of the question.
- **Report cache replay without assigning a cause** (2026-08-16.5, 2026-08-17.2). Only an explicit
  harness event establishes compaction.
- **A clean boundary comparison is vacuous without positive population** (2026-08-17.4). Pair the
  broad matrix with a same-version discriminator that activates the claimed axis.
- **Follow-ups on one child remain one dispatch record** (2026-08-17.4). Create a new row only for
  a fresh child with its own transcript and startup boundary.
