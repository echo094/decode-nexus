# unlock-env

Strips javascript-obfuscator custom-code helpers: self-defending, console-output disabling, debug
protection, domain lock, and the calls controllers through which those helpers are installed.
Reverses [custom-code-helpers.md](../../../javascript-obfuscator/transforms/custom-code-helpers.md).

## 1. Target

Produce output without recognized runtime protections while preserving every unrelated effect.
The pass must remove a helper completely or leave it untouched: a partial removal can create an
unbound reference while still looking cleaner.

## 2. Algorithm

The protections share one removal strategy because the encoder gives them the same controller
shape:

1. Find an immediately invoked calls-controller function that returns a two-parameter selector.
2. Partition its references into guard-building calls and other uses.
3. Require exactly one guard, a recognized callback, and no external controller use.
4. Prove the complete callback and binding graph before mutating.
5. Remove the trigger, definition, and controller as one unit.

A second phase removes a proven debug-protection function and every accepted interval that invokes
it. Intervals may use the global-call or resolved-global member-call spelling. Every remaining
reference to the protection function must belong to an accepted interval before removal begins.

Domain lock is detected statically. The pass proves the resolver, encoded-domain extraction,
property-discovery graph, suffix comparison, and redirect assignment; it does not need a browser to
identify the helper. Runtime fixtures use a Node-hosted browser-like location object only to check
the on-domain and off-domain effects.

## 3. Implementation

Callback classification is ordered from specific to broad:

| Protection | Recognized shape | Era |
|---|---|---|
| self-defending | search-chain callback, with or without the newline bail | `E-selfdef-search`; `E-selfdef-search-newline-bail` |
| domain lock | complete resolver, domain/property discovery, suffix-match, and redirect graph | `E-domainlock-case-preserved`; `E-domainlock-lowercase`; `E-helper-global-default` |
| debug protection | repeated `new RegExp` construction | `E-dbgprot-recursive-counter` |
| console output | method-name array containing the console methods | `E-consoleout-bound-stubs` |
| self-defending | nested-function callback | `E-selfdef-regexp` |

The domain-lock candidate check is a firewall before the broader RegExp heuristic. A candidate
that fails any domain proof declines; it cannot fall through and be misclassified as debug
protection merely because it contains RegExp construction.

Static member keys accept identifier, non-computed, and computed-string spellings. Dynamic keys
and unrelated properties decline. Removal targets are effects, not enclosing statements: when the
encoder merges an interval or guard into a sequence expression, only its sequence element is
removed.

The resolved-global interval supports these complete resolver forms:

- a function resolver declaration, its one-use result, and the interval;
- an uninitialized holder assigned through the encoder's `Function(... return this ...)` or
  `window` try/catch resolver;
- the service-worker `typeof global === 'object' ? global : this` resolver;
- the browser-no-eval `window`/`process`/`require`/`global` fallback.

Each proof fixes the local statement shape, host-name bindings, holder references, and protection
references. If the wrapper contains an unrelated effect, only the proven interval effect is
removed. After guard removal the Program scope is crawled before debug-protection references are
read, keeping Babel's derived binding state consistent with the live tree.

## 4. Upstream Effects

| Input spelling | Producer | Era | Requirement |
|---|---|---|---|
| decoded method strings | [string-array.md](string-array.md) | relevant string-array eras | console names and search members must be literals before classification |
| folded constants and static member keys | [normalize-converting.md](normalize-converting.md) | all supported eras | exposes `debugger`, `search`, and static interval keys |
| direct guard calls restored from storage | [inline-control-flow-storage.md](inline-control-flow-storage.md) | `E-cff-storage-stringarray-shared` and related storage eras | restores the controller call shape before reference partitioning |
| unreachable donated helper copies removed | [prune-if-branch.md](../prune-if-branch.md) | all supported eras | prevents dead injected copies from being treated as live guards |
| sequence elements retained as separate effects | encoder adjacent-statement merging | all supported eras | removal must not delete neighboring program effects |
| fresh bindings after phase-one removals | this pass | all supported eras | phase two reads reference sets only after a scope crawl |
| member-qualified interval | encoder | `E-dbgprot-interval-global-member` | accept a static `setInterval` member and prove its resolver |
| service-worker resolver | encoder | `E-helper-global-serviceworker` | remove the exact direct-holder wrapper when it has no other use |
| browser-no-eval fallback | encoder | `E-helper-global-default` | accept the fixed host-test chain; altered chains decline |

The console-output callback refers to its own controller. Liveness checks therefore partition
references before deletion and exclude uses inside the guard being removed.

## Source

- [`src/visitor/obfuscator/unlock-env.js`](https://github.com/echo094/decode-js/blob/6cacb633ceedf0812fe31f951ba8f41ffb431ca1/src/visitor/obfuscator/unlock-env.js),
  scheduled last by
  [`src/plugin/obfuscatorx.js`](https://github.com/echo094/decode-js/blob/6cacb633ceedf0812fe31f951ba8f41ffb431ca1/src/plugin/obfuscatorx.js).

The protections remain in one pass because they share controller discovery, proof-before-mutation,
and effect removal. Debug protection's non-controller phase is the natural seam if those mechanics
later diverge.

## Fixtures

| Claim | Fixture | Era |
|---|---|---|
| Program- and function-scoped self-defending placement | `self-defending-global`; `self-defending-function` | `E-selfdef-search` |
| newline-bail and nested-function self-defending bodies | `self-defending-newline-bail`; `self-defending-regexp-era` | `E-selfdef-search-newline-bail`; `E-selfdef-regexp` |
| console controller self-reference | `console-output` | `E-consoleout-bound-stubs` |
| debug function and global interval | `debug-protection`; `debug-protection-interval` | `E-dbgprot-recursive-counter`; `E-dbgprot-interval-global-call` |
| member interval and function/try-catch resolvers | `debug-protection-interval-member`; `debug-protection-interval-member-inline` | `E-dbgprot-interval-global-member` |
| service-worker direct resolver | `debug-protection-interval-member-service-worker` | `E-helper-global-serviceworker` |
| browser-no-eval consumers and altered-chain decline | `browser-no-eval-self-defending`; `browser-no-eval-debugger`; `browser-no-eval-console`; `browser-no-eval-decline-condition` | applicable helper/protection eras |
| domain helper in nested and browser-no-eval resolver forms | `domain-lock-5.4.1`; `domain-lock-browser-no-eval` | `E-domainlock-lowercase`; `E-helper-global-default` |
| independent controllers and unsafe-controller declines | `two-protections`; `decline-two-guards`; `decline-controller-used-elsewhere`; `decline-unrecognised-guard` | applicable helper era or hand-built near-miss |
| interval callee and extra-reference declines | `decline-member-non-interval`; `decline-member-dynamic-property`; `decline-member-with-other-reference` | hand-built near-miss |
| resolver proof and wrapper-effect declines | `decline-inline-resolver-extra-effect`; `decline-inline-resolver-signature`; `decline-service-worker-resolver-condition`; `decline-service-worker-holder-reference`; `decline-service-worker-non-static-member` | hand-built near-miss |

Removing fixtures compare runtime behavior with their source and audit live binding state after the
visitor. Hand-built near-misses pin fail-closed behavior for shapes the encoder cannot emit.
