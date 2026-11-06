# VM source map

One row per file under the decoder's `src/vm/`, the doc that owns it and the docs that also cite
it in their `## Source`. The two layer folders match the code's: `jsconfuser-vm/` is the frontend,
`switch/` the shared backend. Docs are named for their component, so a file and its doc need not
share a name. This map is derived from the `## Source` sections and checked against them by grep in
both directions: every file has an owner that cites it, and every cited file has a row.

| Source file | Owner | Also cited by |
|---|---|---|
| [`jsconfuser-vm/analyze-anti-register-flow.js`](../../../decoder/decode-js/src/vm/jsconfuser-vm/analyze-anti-register-flow.js) | [anti-runtime-observation](jsconfuser-vm/anti-runtime-observation.md) | [read-wordcode](jsconfuser-vm/read-wordcode.md) |
| [`jsconfuser-vm/analyze-anti-runtime.js`](../../../decoder/decode-js/src/vm/jsconfuser-vm/analyze-anti-runtime.js) | [anti-runtime-observation](jsconfuser-vm/anti-runtime-observation.md) | - |
| [`jsconfuser-vm/container-role-helpers.js`](../../../decoder/decode-js/src/vm/jsconfuser-vm/container-role-helpers.js) | [extract-container](jsconfuser-vm/extract-container.md) | - |
| [`jsconfuser-vm/decode-standalone.js`](../../../decoder/decode-js/src/vm/jsconfuser-vm/decode-standalone.js) | [standalone-decode](jsconfuser-vm/standalone-decode.md) | [lower-switch-model](jsconfuser-vm/lower-switch-model.md), [standalone-diagnosis](jsconfuser-vm/standalone-diagnosis.md), [vm-switch-emit](switch/vm-switch-emit.md) |
| [`jsconfuser-vm/diagnose-standalone.js`](../../../decoder/decode-js/src/vm/jsconfuser-vm/diagnose-standalone.js) | [standalone-diagnosis](jsconfuser-vm/standalone-diagnosis.md) | [normalize-aliased-wordcode](jsconfuser-vm/normalize-aliased-wordcode.md), [normalize-anti-wordcode](jsconfuser-vm/normalize-anti-wordcode.md), [normalize-cff-wordcode](jsconfuser-vm/normalize-cff-wordcode.md), [normalize-concealed-constants](jsconfuser-vm/normalize-concealed-constants.md), [normalize-dispatcher-wordcode](jsconfuser-vm/normalize-dispatcher-wordcode.md), [normalize-macro-wordcode](jsconfuser-vm/normalize-macro-wordcode.md), [normalize-self-modifying-wordcode](jsconfuser-vm/normalize-self-modifying-wordcode.md), [normalize-specialized-wordcode](jsconfuser-vm/normalize-specialized-wordcode.md), [normalize-string-concealing](jsconfuser-vm/normalize-string-concealing.md), [partition-functions](jsconfuser-vm/partition-functions.md), [read-wordcode](jsconfuser-vm/read-wordcode.md), [standalone-decode](jsconfuser-vm/standalone-decode.md) |
| [`jsconfuser-vm/expand-observed-word-stream.js`](../../../decoder/decode-js/src/vm/jsconfuser-vm/expand-observed-word-stream.js) | [normalize-macro-wordcode](jsconfuser-vm/normalize-macro-wordcode.md) | - |
| [`jsconfuser-vm/extract-container.js`](../../../decoder/decode-js/src/vm/jsconfuser-vm/extract-container.js) | [extract-container](jsconfuser-vm/extract-container.md) | [runtime-meaning](jsconfuser-vm/runtime-meaning.md) |
| [`jsconfuser-vm/finally-continuations.js`](../../../decoder/decode-js/src/vm/jsconfuser-vm/finally-continuations.js) | [normalize-macro-wordcode](jsconfuser-vm/normalize-macro-wordcode.md) | [self-modifying-observation](jsconfuser-vm/self-modifying-observation.md) |
| [`jsconfuser-vm/handler-effects.js`](../../../decoder/decode-js/src/vm/jsconfuser-vm/handler-effects.js) | [runtime-meaning](jsconfuser-vm/runtime-meaning.md) | - |
| [`jsconfuser-vm/handler-matchers.js`](../../../decoder/decode-js/src/vm/jsconfuser-vm/handler-matchers.js) | [runtime-meaning](jsconfuser-vm/runtime-meaning.md) | - |
| [`jsconfuser-vm/handler-meaning.js`](../../../decoder/decode-js/src/vm/jsconfuser-vm/handler-meaning.js) | [runtime-meaning](jsconfuser-vm/runtime-meaning.md) | - |
| [`jsconfuser-vm/identify-handlers.js`](../../../decoder/decode-js/src/vm/jsconfuser-vm/identify-handlers.js) | [runtime-meaning](jsconfuser-vm/runtime-meaning.md) | [anti-runtime-observation](jsconfuser-vm/anti-runtime-observation.md), [locate-handlers](jsconfuser-vm/locate-handlers.md), [normalize-aliased-wordcode](jsconfuser-vm/normalize-aliased-wordcode.md), [normalize-macro-wordcode](jsconfuser-vm/normalize-macro-wordcode.md) |
| [`jsconfuser-vm/locate-boot-payload.js`](../../../decoder/decode-js/src/vm/jsconfuser-vm/locate-boot-payload.js) | [extract-container](jsconfuser-vm/extract-container.md) | [locate-handlers](jsconfuser-vm/locate-handlers.md) |
| [`jsconfuser-vm/locate-handlers.js`](../../../decoder/decode-js/src/vm/jsconfuser-vm/locate-handlers.js) | [locate-handlers](jsconfuser-vm/locate-handlers.md) | [normalize-source](jsconfuser-vm/normalize-source.md) |
| [`jsconfuser-vm/materialize-encoded-bytecode.js`](../../../decoder/decode-js/src/vm/jsconfuser-vm/materialize-encoded-bytecode.js) | [extract-container](jsconfuser-vm/extract-container.md) | - |
| [`jsconfuser-vm/minified-runtime-container.js`](../../../decoder/decode-js/src/vm/jsconfuser-vm/minified-runtime-container.js) | [extract-container](jsconfuser-vm/extract-container.md) | - |
| [`jsconfuser-vm/normalize-aliased-wordcode.js`](../../../decoder/decode-js/src/vm/jsconfuser-vm/normalize-aliased-wordcode.js) | [normalize-aliased-wordcode](jsconfuser-vm/normalize-aliased-wordcode.md) | - |
| [`jsconfuser-vm/normalize-anti-wordcode.js`](../../../decoder/decode-js/src/vm/jsconfuser-vm/normalize-anti-wordcode.js) | [normalize-anti-wordcode](jsconfuser-vm/normalize-anti-wordcode.md) | [normalize-specialized-wordcode](jsconfuser-vm/normalize-specialized-wordcode.md) |
| [`jsconfuser-vm/normalize-cff-wordcode.js`](../../../decoder/decode-js/src/vm/jsconfuser-vm/normalize-cff-wordcode.js) | [normalize-cff-wordcode](jsconfuser-vm/normalize-cff-wordcode.md) | - |
| [`jsconfuser-vm/normalize-concealed-constants.js`](../../../decoder/decode-js/src/vm/jsconfuser-vm/normalize-concealed-constants.js) | [normalize-concealed-constants](jsconfuser-vm/normalize-concealed-constants.md) | [normalize-anti-wordcode](jsconfuser-vm/normalize-anti-wordcode.md) |
| [`jsconfuser-vm/normalize-dispatcher-wordcode.js`](../../../decoder/decode-js/src/vm/jsconfuser-vm/normalize-dispatcher-wordcode.js) | [normalize-dispatcher-wordcode](jsconfuser-vm/normalize-dispatcher-wordcode.md) | [normalize-anti-wordcode](jsconfuser-vm/normalize-anti-wordcode.md) |
| [`jsconfuser-vm/normalize-macro-wordcode.js`](../../../decoder/decode-js/src/vm/jsconfuser-vm/normalize-macro-wordcode.js) | [normalize-macro-wordcode](jsconfuser-vm/normalize-macro-wordcode.md) | - |
| [`jsconfuser-vm/normalize-self-modifying-wordcode.js`](../../../decoder/decode-js/src/vm/jsconfuser-vm/normalize-self-modifying-wordcode.js) | [normalize-self-modifying-wordcode](jsconfuser-vm/normalize-self-modifying-wordcode.md) | [self-modifying-observation](jsconfuser-vm/self-modifying-observation.md) |
| [`jsconfuser-vm/normalize-specialized-wordcode.js`](../../../decoder/decode-js/src/vm/jsconfuser-vm/normalize-specialized-wordcode.js) | [normalize-specialized-wordcode](jsconfuser-vm/normalize-specialized-wordcode.md) | - |
| [`jsconfuser-vm/normalize-string-concealing.js`](../../../decoder/decode-js/src/vm/jsconfuser-vm/normalize-string-concealing.js) | [normalize-string-concealing](jsconfuser-vm/normalize-string-concealing.md) | - |
| [`jsconfuser-vm/numeric-to-vm-switch.js`](../../../decoder/decode-js/src/vm/jsconfuser-vm/numeric-to-vm-switch.js) | [lower-switch-model](jsconfuser-vm/lower-switch-model.md) | [standalone-decode](jsconfuser-vm/standalone-decode.md) |
| [`jsconfuser-vm/observe-aliased-runtime.js`](../../../decoder/decode-js/src/vm/jsconfuser-vm/observe-aliased-runtime.js) | [normalize-aliased-wordcode](jsconfuser-vm/normalize-aliased-wordcode.md) | - |
| [`jsconfuser-vm/observe-dispatcher-wordcode.js`](../../../decoder/decode-js/src/vm/jsconfuser-vm/observe-dispatcher-wordcode.js) | [normalize-dispatcher-wordcode](jsconfuser-vm/normalize-dispatcher-wordcode.md) | [read-wordcode](jsconfuser-vm/read-wordcode.md) |
| [`jsconfuser-vm/observe-macro-runtime.js`](../../../decoder/decode-js/src/vm/jsconfuser-vm/observe-macro-runtime.js) | [normalize-macro-wordcode](jsconfuser-vm/normalize-macro-wordcode.md) | - |
| [`jsconfuser-vm/observe-patch-added-opcodes.js`](../../../decoder/decode-js/src/vm/jsconfuser-vm/observe-patch-added-opcodes.js) | [self-modifying-observation](jsconfuser-vm/self-modifying-observation.md) | - |
| [`jsconfuser-vm/observe-self-modifying.js`](../../../decoder/decode-js/src/vm/jsconfuser-vm/observe-self-modifying.js) | [self-modifying-observation](jsconfuser-vm/self-modifying-observation.md) | - |
| [`jsconfuser-vm/observe-specialized-runtime.js`](../../../decoder/decode-js/src/vm/jsconfuser-vm/observe-specialized-runtime.js) | [normalize-specialized-wordcode](jsconfuser-vm/normalize-specialized-wordcode.md) | - |
| [`jsconfuser-vm/opcode-table.js`](../../../decoder/decode-js/src/vm/jsconfuser-vm/opcode-table.js) | [locate-handlers](jsconfuser-vm/locate-handlers.md) | - |
| [`jsconfuser-vm/partition-functions-input.js`](../../../decoder/decode-js/src/vm/jsconfuser-vm/partition-functions-input.js) | [partition-functions](jsconfuser-vm/partition-functions.md) | - |
| [`jsconfuser-vm/partition-functions.js`](../../../decoder/decode-js/src/vm/jsconfuser-vm/partition-functions.js) | [partition-functions](jsconfuser-vm/partition-functions.md) | [normalize-anti-wordcode](jsconfuser-vm/normalize-anti-wordcode.md) |
| [`jsconfuser-vm/read-wordcode.js`](../../../decoder/decode-js/src/vm/jsconfuser-vm/read-wordcode.js) | [read-wordcode](jsconfuser-vm/read-wordcode.md) | [anti-runtime-observation](jsconfuser-vm/anti-runtime-observation.md), [normalize-aliased-wordcode](jsconfuser-vm/normalize-aliased-wordcode.md), [normalize-anti-wordcode](jsconfuser-vm/normalize-anti-wordcode.md), [normalize-macro-wordcode](jsconfuser-vm/normalize-macro-wordcode.md), [normalize-specialized-wordcode](jsconfuser-vm/normalize-specialized-wordcode.md), [self-modifying-observation](jsconfuser-vm/self-modifying-observation.md) |
| [`jsconfuser-vm/runtime-fragment-pattern.js`](../../../decoder/decode-js/src/vm/jsconfuser-vm/runtime-fragment-pattern.js) | [locate-handlers](jsconfuser-vm/locate-handlers.md) | - |
| [`jsconfuser-vm/runtime-source-signature.js`](../../../decoder/decode-js/src/vm/jsconfuser-vm/runtime-source-signature.js) | [qualify-jsconfuser-vm](jsconfuser-vm/qualify-jsconfuser-vm.md) | - |
| [`jsconfuser-vm/standalone-contract.js`](../../../decoder/decode-js/src/vm/jsconfuser-vm/standalone-contract.js) | [standalone-diagnosis](jsconfuser-vm/standalone-diagnosis.md) | - |
| [`jsconfuser-vm/string-concealing-helper-signatures.js`](../../../decoder/decode-js/src/vm/jsconfuser-vm/string-concealing-helper-signatures.js) | [normalize-string-concealing](jsconfuser-vm/normalize-string-concealing.md) | - |
| [`jsconfuser-vm/validate-references-operands.js`](../../../decoder/decode-js/src/vm/jsconfuser-vm/validate-references-operands.js) | [validate-references](jsconfuser-vm/validate-references.md) | - |
| [`jsconfuser-vm/validate-references.js`](../../../decoder/decode-js/src/vm/jsconfuser-vm/validate-references.js) | [validate-references](jsconfuser-vm/validate-references.md) | [normalize-anti-wordcode](jsconfuser-vm/normalize-anti-wordcode.md) |
| [`jsconfuser-vm/wordcode-index.js`](../../../decoder/decode-js/src/vm/jsconfuser-vm/wordcode-index.js) | [read-wordcode](jsconfuser-vm/read-wordcode.md) | - |
| [`switch/vm-switch-control.js`](../../../decoder/decode-js/src/vm/switch/vm-switch-control.js) | [vm-switch-control](switch/vm-switch-control.md) | - |
| [`switch/vm-switch-copy-planning.js`](../../../decoder/decode-js/src/vm/switch/vm-switch-copy-planning.js) | [vm-switch-emit](switch/vm-switch-emit.md) | [vm-switch-control](switch/vm-switch-control.md) |
| [`switch/vm-switch-model.js`](../../../decoder/decode-js/src/vm/switch/vm-switch-model.js) | [vm-switch-boundary](switch/vm-switch-boundary.md) | [standalone-decode](jsconfuser-vm/standalone-decode.md) |
| [`switch/vm-switch-statements.js`](../../../decoder/decode-js/src/vm/switch/vm-switch-statements.js) | [vm-switch-statements](switch/vm-switch-statements.md) | - |
| [`switch/vm-switch-structured-emitter.js`](../../../decoder/decode-js/src/vm/switch/vm-switch-structured-emitter.js) | [vm-switch-emit](switch/vm-switch-emit.md) | [vm-switch-try-region](switch/vm-switch-try-region.md) |
| [`switch/vm-switch-to-source.js`](../../../decoder/decode-js/src/vm/switch/vm-switch-to-source.js) | [vm-switch-emit](switch/vm-switch-emit.md) | [standalone-decode](jsconfuser-vm/standalone-decode.md), [vm-switch-control](switch/vm-switch-control.md), [vm-switch-statements](switch/vm-switch-statements.md) |

## Checking the map

```sh
# explanatory: every src/vm file must appear in this map and in its owner's ## Source
cd decoder/decode-js && ls src/vm/*/*.js | sed 's#src/vm/##' | while read f; do
  grep -q "\`$f\`" ../../skills/decode-js/vm/source-map.md || echo "no row: $f"
done
```
