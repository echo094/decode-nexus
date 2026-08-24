# obfuscatorx.js

Target: **javascript-obfuscator / obfuscator.io**, shape-driven and era-invariant. This is the
entry where that target is actively developed; the legacy
[obfuscator](obfuscator.md) entry is
[frozen](../decode-js.md#obfuscator-is-frozen-obfuscatorx-is-where-its-target-is-worked-on).
Dispatch it with `-t obfuscatorx`.

The plugin is intentionally additive. It does not change the established `obfuscator` entry, and
the two may produce different results. Its thin entry schedules focused visitors under
`src/visitor/obfuscator/`, following the same composition style as
[jsconfuser](jsconfuser.md).

## Pipeline

1. [normalize-statements](../visitors/obfuscator/normalize-statements.md) restores statement
   boundaries before visitors that navigate by them.
2. [obfuscator/inline-control-flow-storage](../visitors/obfuscator/inline-control-flow-storage.md)
   exposes numeric string-array indexes introduced by string-array calls transformation.
3. [string-array](../visitors/obfuscator/string-array.md) resolves the string-array subsystem in a
   fresh isolate. Its result controls the refusal contract below.
4. A fixpoint group runs
   [normalize-converting](../visitors/obfuscator/normalize-converting.md),
   [calculate-constant-exp](../visitors/calculate-constant-exp.md), storage inlining, constant
   folding, [prune-if-branch](../visitors/prune-if-branch.md), and
   [unflatten-switch-dispatch](../visitors/obfuscator/unflatten-switch-dispatch.md). The group is
   capped because storage inlining can expose converting work that has already run.
5. [unlock-env](../visitors/obfuscator/unlock-env.md) removes recognized anti-tamper helpers after
   their string and storage dependencies are readable. [delete-extra](../visitors/delete-extra.md)
   performs final spelling cleanup before generation.

The storage visitor appears on both sides of string-array decoding because the dependency reverses
across encoder shapes. Calls-transform storage can conceal a wrapper index and must resolve first;
older storage can itself contain strings and resolves after the array. The same visitor handles
both without a version branch.

`prune-if-branch` is also a dependency, not cosmetic cleanup. It removes unreachable injected
copies that lack their controller storage and supplies the un-flattener with reachable dispatch
structures. `unlock-env` stays outside the fixpoint because it deletes helpers after all of its
inputs are normalized.

## Return contract

Refusal means one thing: the plugin recognized a layer it owns but could not read it safely.
String-array outcomes map to the plugin result as follows:

| Outcome | Plugin behavior |
|---|---|
| `decoded` | continue |
| `absent` | continue; other transforms remain decodable |
| `unowned` | return the partial decode and log the foreign residue |
| `unreadable` | refuse with a diagnostic naming the rejected shape |

Returning an `unowned` partial decode preserves the target-chaining workflow: a successfully
removed outer layer remains available to another decoder. Diagnostics use
`src/utility/logger.js`; the plugin does not silently fall through or select among guessed results.

## Architecture

- Detection and decoding are separate. Matchers resolve AST shapes and bindings; no runtime era
  report or era-keyed strategy registry participates in decoding.
- The pass sequence is era-invariant. Era knowledge documents which emitted shapes a strategy
  accepts; it does not select a different pipeline.
- Files are named for the AST shape or operation they handle, not for a version or ordinal era.
  Different algorithms may split; parameter differences stay in one implementation.
- Shared visitors are imported unchanged. Target-specific behavior is implemented under
  `src/visitor/obfuscator/` instead of widening a visitor used by unrelated plugins.

Era evidence belongs in the encoder's [registry](../../javascript-obfuscator/versions.md) and in
each visitor's implementation and fixture tables. In particular,
`E-cff-storage-stringarray-shared` requires storage inlining before string-array decoding. Changes
in an encoder release do not create a decoder branch unless they change a supported decoding
algorithm.

## Source

- [`src/plugin/obfuscatorx.js`](https://github.com/echo094/decode-js/blob/6cacb633ceedf0812fe31f951ba8f41ffb431ca1/src/plugin/obfuscatorx.js), registered in
  [`src/main.js`](https://github.com/echo094/decode-js/blob/6cacb633ceedf0812fe31f951ba8f41ffb431ca1/src/main.js).
- Target-specific visitors:
  [`src/visitor/obfuscator/`](https://github.com/echo094/decode-js/tree/6cacb633ceedf0812fe31f951ba8f41ffb431ca1/src/visitor/obfuscator).
- The cited visitor docs own the reason for each pipeline position.

## Fixtures

[`test/obfuscatorx/`](https://github.com/echo094/decode-js/tree/6cacb633ceedf0812fe31f951ba8f41ffb431ca1/test/obfuscatorx) exercises the entry through
`getPluginResult`, so pass order, refusal, and generation failures are visible at plugin level.

| Fixture | Claim | Era |
|---|---|---|
| `2.9.6-baseline-strings` | the oldest supported array, wrapper, and rotate shapes decode together | `E-sa-array-declaration`; `E-sa-wrapper-var-fn-expression`; `E-sa-rotate-counter-loop` |
| `2.19.0-all-on-objects` | the spine's maximal profile composes through the entry | `E-sa-array-self-replacing-fn`; `E-sa-wrapper-array-fn-call`; `E-sa-rotate-compare-loop-fn-arg` |
| `2.19.0-dead-code-control` | dead-code injection is isolated from unrelated pipeline failures | same string-array eras as the spine row |
| `2.19.0-class-logical` | computed class keys and top-level logical statements are populated before exact-output comparison | no string-array era claim |
| `3.2.0-calls-transform` | numeric storage resolves before a string-array wrapper index | `E-cff-storage-stringarray-shared` |
| `4.2.0-optional-cff` | an optional identifier-callee wrapper preserves short-circuit behavior | `E-cff-callee-optional-wrapper` |
| `5.4.4-cff-spread-plain-reuse` | the recoverable spread/plain reuse shape restores the source result | `E-cff-callee-reuse-kind` |
| `5.4.5-cff-spread-plain-same-plain-first`; `5.4.5-cff-spread-plain-same-spread-first` | encounter order does not merge plain and spread wrapper shapes | `E-cff-callee-reuse-shape-kind` |
| `5.4.5-issue-1419-arrow-in-for` | concise-arrow `in` syntax remains parseable and runtime-equivalent | `E-generator-arrow-noin-parentheses` |
| `static-top-level-declaration/*` | shorthand and expanded static-block declarations remain parseable; destructuring is left alone | `E-shorthand-static-global-shorthand`; `E-shorthand-static-expanded` |
| string-array refusal cases | `unreadable` refuses, while `absent` does not | the era attached to each visitor fixture |

The shared harness must check both emitted output and live Babel-derived state. A golden alone does
not satisfy the Encoder/Decoder Method's S6 contract; plugin cases require the one-AST consistency
oracle described in [tests.md](../tests.md).
