# Result & Profiling (`obfuscationResult.ts`)

`obfuscationResult.ts` has no logic of its own — just four type-only declarations that
define the entry points' return shapes (the `N` node in
[Execution Flow](js-confuser.md#execution-flow-encoderjs-confusersrcobfuscatorts)) and
the optional profiler hook. Only `index.ts` and `obfuscator.ts` reference it.

- **`ObfuscationResult`** — what `obfuscate()`/`obfuscateAST()` resolve to: `code`
  (the generated string), plus optional `map` (a `@babel/generator` source map, present
  when `options.sourceMap` is on) and `ast` (the final `File` node).
- **`ProfileData`** — what `obfuscateWithProfiler()` additionally returns alongside
  `code`, as `{ ...ObfuscationResult, profileData }`: overall `obfuscationTime` /
  `parseTime` / `compileTime`, `totalTransforms` (plugins actually registered for this
  run) vs. `totalPossibleTransforms` (every transform module that exists, gated or
  not — tracked on `Obfuscator.totalPossibleTransforms`), and a `transforms` map keyed
  by transform name holding each one's `transformTime` and `changeData` — the
  `{ [key: string]: number }` counters a transform increments itself (e.g.
  [RenameVariables](transforms/rename-variables.md) does `me.changeData.variables++`
  per renamed binding) via `PluginInstance.changeData`
  (see [plugin-api.md](plugin-api.md)).
- **`ProfilerCallback`** — the `(log, transformEntry?, ast?) => void` shape passed as
  `obfuscateWithProfiler(code, options, { callback })`. Invoked once per transform, right
  after that transform's traversal finishes but before the next one starts, with the
  in-progress AST — lets a caller (the type's doc comment specifically calls out
  js-confuser.com's own benchmark page) inspect or time individual pipeline stages
  without forking the library.
- **`ProfilerLog`** — the `log` argument above: `index`/`totalTransforms` (position in
  the pipeline), `currentTransform` (the one that just finished), `nextTransform` (the
  one about to run).

`obfuscateWithProfiler()` (in `index.ts`) is the only place these are assembled: it
times `Obfuscator.parseCode()` and `Obfuscator.generateCode()` directly, and threads a
`profiler` callback through `obfuscator.obfuscateAST(ast, { profiler })` — a second,
optional argument to `obfuscateAST` not shown in the
[Execution Flow](js-confuser.md#execution-flow-encoderjs-confusersrcobfuscatorts)
diagram — to time everything in between.
