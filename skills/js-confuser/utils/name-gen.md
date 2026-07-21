# NameGen.ts

`NameGen` generates unique, collision-free identifier names. One shared instance lives
on `Obfuscator.nameGen` (constructed from `options.identifierGenerator`); several
transforms also create their own private instance — sometimes forcing a different mode
than the user's option (e.g. VariableMasking's property names always use `new
NameGen("mangled")`, GlobalConcealing defaults to `new NameGen()` i.e. `"randomized"`).

## `identifierGenerator` modes (`attemptGenerate()`)

If the option is a function, it's called directly (must return a string) — otherwise
the value is resolved through `Obfuscator.prototype.computeProbabilityMap` (the same
`ProbabilityMap` mechanism documented in [options.md](../options.md)), so a mode can
also be a weighted mix. Each built-in mode, given a random length of 6–8:

| Mode | Shape | Notes |
|---|---|---|
| `"randomized"` (default) | `_Ab3Cd9` | letters/underscore first char, alphanumeric+`_` after |
| `"hexadecimal"` | `_0xCA96BF` | `_0x` prefix + [getRandomHexString](random-utils.md) |
| `"mangled"` | `a`, `b`, ... `z`, `aa`, ... | [`alphabeticalGenerator`](gen-utils.md), shortest-first, skips reserved keywords |
| `"number"` | `var_1`, `var_2`, ... | plain incrementing counter |
| `"zeroWidth"` | invisible | [`createZeroWidthGenerator`](gen-utils.md) — real keyword + zero-width joiners |
| `"chinese"` | `涭鿄...` | [`getRandomChineseString`](random-utils.md) — CJK codepoint range |

## `generate(isSafeForReuse = true)`

Retries `attemptGenerate()` until the name is both unique (not in `generatedNames`) and
passes the constructor's `options`: `avoidReserved` (skip `reservedKeywords`) and
`avoidObjectPrototype` (skip `reservedObjectPrototype`), both from
[constants.ts](../constants.md). The accepted name is added to
`generatedNames`; if `isSafeForReuse` is `false`, it's also added to
`notSafeForReuseNames`.

[ControlFlowFlattening](../transforms/control-flow-flattening.md) calls
`nameGen.generate(false)` for its per-scope discriminant variable names — these must
never be handed back out by a *different* NameGen's reuse logic. That's what
`notSafeForReuseNames` guards: [RenameVariables](../transforms/rename-variables.md),
when reusing a name already generated in an outer scope, checks the candidate isn't in
`me.obfuscator.nameGen.notSafeForReuseNames` before reusing it, alongside the ordinary
`scope.hasGlobal()` collision check.
