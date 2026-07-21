# ast-utils.ts

By far the largest and most widely imported `utils/` file — nearly every transform
(`astScrambler`, `calculator`, `controlFlowFlattening`, `deadCode`, `dispatcher`,
`duplicateLiteralsRemoval`, `objectExtraction`, `flatten`, `globalConcealing`,
`movedDeclarations`, `renameVariables`, `lock`, `minify`, `pack`, `plugin`,
`preparation`, `rgf`, `stringConcealing`, `stringEncoding`, `stringSplitting`,
`variableMasking`) pulls at least one helper from here. Grouped by purpose:

## Identifier classification

Predicates that answer "is this identifier path a *variable* reference/binding, and
what kind" — used to gate rename/replace logic so transforms don't touch labels, object
keys, or non-variable identifiers by mistake:

- **`isVariableIdentifier(path)`** — true for any referenced or binding identifier that
  isn't a label. The base filter [RenameVariables](../transforms/rename-variables.md),
  [Pack](../transforms/pack.md), [Dispatcher](../transforms/dispatcher.md), and most
  other identifier-touching transforms run before considering a node further.
- **`isDefiningIdentifier(path)`** — narrower: true only for identifiers that actually
  *declare* a variable (`var`/`let`/`const` id, function/param id, destructuring
  targets), false for plain assignment/call targets. Used wherever a transform needs to
  find the declaration site specifically (e.g.
  [VariableMasking](../transforms/variable-masking.md),
  [Pack](../transforms/pack.md)).
- **`isStrictIdentifier(path)`** — true only for a function or class's own `id`. Exported
  but currently unused — no transform imports it.
- **`isExportedIdentifier(path)`** — true if the identifier sits directly inside an
  `export` declaration/specifier (named, default, or `export const x = ...`). Used by
  [RenameVariables](../transforms/rename-variables.md) to avoid renaming a binding whose
  external name is part of the module's public API.
- **`isModifiedIdentifier(identifierPath)`** — true if the identifier is the target of
  an update (`x++`) or assignment (`x = ...`) — explicitly excludes member-expression
  targets (`obj.x = ...`, where `x` isn't a variable). Used by
  [Flatten](../transforms/flatten.md) and [Pack](../transforms/pack.md) to detect
  variables that get reassigned (as opposed to only read) when deciding how to
  rewrite/relocate them.
- **`isUndefined(path)`** — true for the literal identifier `undefined` or `void 0`.
  Used by [Minify](../transforms/minify.md) and
  [DuplicateLiteralsRemoval](../transforms/duplicate-literals-removal.md) to recognize
  both spellings as the same static value.
- **`isModuleImport(path)`** — true if a string literal is an import source (static
  `import ... from "..."`, or the first argument to `require()`/dynamic `import()`).
  Checked by every string-rewriting transform
  ([StringEncoding](../transforms/string-encoding.md),
  [StringSplitting](../transforms/string-splitting.md),
  [StringConcealing](../transforms/string-concealing.md),
  [DuplicateLiteralsRemoval](../transforms/duplicate-literals-removal.md)) so module
  specifiers are never encoded/concealed — that would break module resolution.
- **`isVariableFunctionIdentifier`** — actually lives in
  [function-utils.ts](function-utils.md), not here; listed there since it's
  function-specific.

## Scope / structure queries

- **`getPatternIdentifierNames(path)`** — collects every binding-identifier name
  introduced by a pattern (destructuring, parameters, ...) belonging to the *same*
  enclosing function as `path`. Used by [Preparation](../transforms/preparation.md) and
  [MovedDeclarations](../transforms/moved-declarations.md) to know which names a
  relocated declaration would shadow.
- **`getFunctionName(path)`** — best-effort human-readable name for a function (its own
  `id`, the variable it's assigned to, its object/class property key, `"[Program]"`, or
  `"anonymous"`/`"anonymous*"`/`"async anonymous"`) — debugging/logging only, e.g.
  [RGF](../transforms/rgf.md)'s and [VariableMasking](../transforms/variable-masking.md)'s
  verbose output.
- **`getBlock(path)`** — nearest enclosing block ancestor. Exported but currently
  unused — no transform imports it.
- **`getParentFunctionOrProgram(path)`** — nearest enclosing function, or the `Program`
  if there is none; asserts one is always found. Used by
  [Preparation](../transforms/preparation.md),
  [ControlFlowFlattening](../transforms/control-flow-flattening.md),
  [Lock](../transforms/lock-integrity.md), [Minify](../transforms/minify.md),
  [RenameVariables](../transforms/rename-variables.md), and
  [ObjectExtraction](../transforms/object-extraction.md) to find the right scope to
  operate in or insert helpers into.
- **`getObjectPropertyAsString(property)`** / **`getMemberExpressionPropertyAsString(member)`**
  — resolve an object/class member's or a `MemberExpression`'s property key to a plain
  string when statically knowable (identifier name, string literal, or numeric literal
  stringified), else `null`. Used by
  [ObjectExtraction](../transforms/object-extraction.md) and
  [GlobalConcealing](../transforms/global-concealing.md) to match property/global names
  against known lists.

## Insertion helpers

- **`append(path, ...nodes)`** — appends statements to the end of the nearest enclosing
  function/block/switch-case body (special-cased for `Program`: inserts before a
  trailing bare expression statement rather than after it, so a script's final
  "return value" expression stays last). Used by [RGF](../transforms/rgf.md) and
  [AstScrambler](../transforms/ast-scrambler.md).
- **`prepend(path, ...nodes)`** / **`prependProgram(path, ...nodes)`** — unshift
  statements to the start of the nearest enclosing function/block/switch-case body (or
  the containing `Program` for the latter), preserving leading `import` declarations by
  inserting after the last one instead of before it, and converting a concise-body arrow
  function to a block body first if needed. The single most common insertion primitive
  in the codebase — used by nearly every transform that lazily inserts a helper
  function/variable (`prepend` in
  [DeadCode](../transforms/dead-code.md), `plugin.ts`'s `me.getPlaceholder`-adjacent
  helpers, [RGF](../transforms/rgf.md),
  [ControlFlowFlattening](../transforms/control-flow-flattening.md),
  [VariableMasking](../transforms/variable-masking.md),
  [Flatten](../transforms/flatten.md), [Dispatcher](../transforms/dispatcher.md),
  [GlobalConcealing](../transforms/global-concealing.md),
  [MovedDeclarations](../transforms/moved-declarations.md),
  [StringConcealing](../transforms/string-concealing.md),
  [DuplicateLiteralsRemoval](../transforms/duplicate-literals-removal.md); `prependProgram`
  in [Calculator](../transforms/calculator.md), `plugin.ts`,
  [Flatten](../transforms/flatten.md), [Dispatcher](../transforms/dispatcher.md),
  [Lock](../transforms/lock-integrity.md), [StringConcealing](../transforms/string-concealing.md)).
- **`ensureComputedExpression(path)`** — flips a non-computed object/class member key
  (`{ foo: 1 }`) to computed (`{ ["foo"]: 1 }`) in place, as a prerequisite before
  replacing that key with a more complex expression (a computed key accepts any
  expression; a non-computed one only accepts an identifier). Called immediately before
  a key-rewrite by [ControlFlowFlattening](../transforms/control-flow-flattening.md),
  [Flatten](../transforms/flatten.md), [VariableMasking](../transforms/variable-masking.md),
  [Minify](../transforms/minify.md),
  [DuplicateLiteralsRemoval](../transforms/duplicate-literals-removal.md),
  [StringConcealing](../transforms/string-concealing.md), and
  [StringSplitting](../transforms/string-splitting.md).
- **`replaceDefiningIdentifierToMemberExpression(path, memberExpression)`** — rewrites a
  declaration site (`function id(){}`, `class id{}`, `var id = 1`) into an assignment to
  a member expression instead (`id = function(){}`, `id = class{}`, `id = 1`, with the
  declaration keyword stripped), so the binding effectively becomes a property instead
  of a local variable. Used by
  [ControlFlowFlattening](../transforms/control-flow-flattening.md) and
  [VariableMasking](../transforms/variable-masking.md) — both relocate variables into a
  shared state/mask object and need their declaration sites converted to plain
  assignments against that object.

## Misc

- **`isStrictMode(path)`** — true if `path` is a class (always strict), a block/program
  with a `"use strict"` directive, or a function whose body is such a block. Checked by
  [RGF](../transforms/rgf.md), [ControlFlowFlattening](../transforms/control-flow-flattening.md),
  [Flatten](../transforms/flatten.md), [VariableMasking](../transforms/variable-masking.md),
  [Dispatcher](../transforms/dispatcher.md), and
  [MovedDeclarations](../transforms/moved-declarations.md) — several of their rewrites
  (e.g. adding a default parameter value, or a `with`-like scope trick) are invalid or
  behave differently in strict mode.
- **`nodeListToNodes`** — private helper normalizing `append`/`prepend`'s rest-or-single-array
  argument shape; not exported.
