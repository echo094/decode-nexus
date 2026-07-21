# validateOptions.ts

Two functions, both called once in the `Obfuscator` constructor before anything else
happens (the `validateOptions.ts` node in
[Execution Flow](js-confuser.md#execution-flow-encoderjs-confusersrcobfuscatorts)):

- **`validateOptions(options)`** — throws on any unrecognized top-level or `lock.*` key
  (checked against a hardcoded allow-list), a missing/invalid `target`, or — when the
  caller passed effectively no options — prints a friendly "you provided zero
  obfuscation options" hint pointing at the presets. Notably, its allow-list includes
  two keys, `debugComments` and `sourceFileName`, that aren't declared on the
  `ObfuscateOptions` TypeScript interface in `options.ts` — the runtime validator
  accepts them even though [options.md](options.md) (derived from that type) doesn't
  document them.
- **`applyDefaultsToOptions(options)`** — merges a chosen `preset` in as a base (any
  option the caller set explicitly still wins), turns on
  `compact`/`renameGlobals`/`renameLabels` by default if unset, normalizes
  `lock.startDate`/`lock.endDate` from `number` to `Date`, defaults `lock.customLocks`
  to `[]`, and — if the caller didn't supply `globalVariables` — seeds it with a large
  built-in list: environment-specific globals (`window`/`document`/`alert`/... for
  `target: "browser"`, `global`/`Buffer`/`require`/`process`/... for `target: "node"`)
  plus a long list of universally-available globals (`Math`, `JSON`, `Promise`, `Set`,
  `Map`, `TextDecoder`, `Symbol`, ...). This default list is what
  [GlobalConcealing](transforms/global-concealing.md), [Pack](transforms/pack.md), and
  [VariableMasking](transforms/variable-masking.md) check against via
  `options.globalVariables.has(name)` whenever the caller hasn't supplied their own.
