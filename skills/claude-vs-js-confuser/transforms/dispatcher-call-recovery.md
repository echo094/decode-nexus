# Dispatcher call recovery

Evidence label: `source-inspection only`.

This page documents the one solution-level transform implemented by the pinned
`Dispatcher/dispatcher.js`: extract the function table carried by a dispatcher function, replace
recognized static uses with direct calls or function references, and remove the dispatcher
scaffolding. The page describes source-backed behavior only. It does not claim that the retained
examples establish runtime equivalence, transfer, reproduction, or production decoder coverage.

## 1. Target

The input is a Babel script AST. `transformOne` searches for the first function declaration whose
function-local traversal contains a first qualifying table: a non-empty object expression assigned
to an identifier, where every property is an `ObjectProperty`, every key is an identifier, string,
or numeric literal accepted by `propName`, and every value is a function expression
([`firstDispatcherTable`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/Dispatcher/dispatcher.js#L18-L85)). The candidate function itself must have an identifier before it can be transformed
([`transformOne`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/Dispatcher/dispatcher.js#L535-L551)).

The table shape alone is not sufficient. `learnDispatcherShape` derives parameter names for the
dispatcher key, mode, and wrapped return value; discovers an argument carrier either from a mode
branch assigning an array or from the first table function's destructuring; and must discover a
return-property name from a mode-comparison branch that returns a one-property object
([`learnDispatcherShape`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/Dispatcher/dispatcher.js#L88-L223)). `transformOne` declines unless the argument carrier and wrapped return property are present
([`shape gate`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/Dispatcher/dispatcher.js#L553-L560)).

The output representation is still JavaScript AST, but the dispatcher table's function expressions
become generated function declarations named `__dispatcher_<sanitized-key>`, and recognized calls,
member-wrapped calls, constructor-shaped calls, and argument-sequence calls become direct calls or
function references. The original dispatcher function is removed after a successful transform
round; unused argument, cache, helper, and object-create bindings are then removed when their fresh
scope binding has no references.

## 2. Algorithm

The transform has one page because extraction, use-site replacement, and cleanup are one dependent
operation: replacement needs the table-key-to-function-name map, and cleanup is safe only after the
dispatcher binding and all recognized uses have been rewritten.

1. **Find and learn the dispatcher contract.** Traverse function declarations in source order and
   retain the first function with a qualifying table. In that function, inspect `if` tests of the
   form `identifier === string`:

   - a branch testing the second parameter and containing an identifier-to-array assignment gives
     the reset marker and argument-carrier name;
   - a branch testing the second parameter and containing a function declaration gives the factory
     marker and records the first identifier-callee call as the helper name; and
   - a branch testing the third parameter whose nested return is a one-property object gives the
     wrapped-return marker and property name.

   Independently, an assignment to `object[keyParam]` can identify a cache name when the object is
   neither the table nor the return parameter. If no argument carrier was found in a marker branch,
   the first table function is inspected for a leading single declarator whose id is an array
   pattern and whose initializer is an identifier; that initializer becomes the carrier
   ([`learnDispatcherShape` fallback and cache scan](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/Dispatcher/dispatcher.js#L182-L220)).

2. **Extract the table into a call map.** For each table property, convert its key into a safe
   generated function name, deep-clone the function-expression body and parameters, and create a
   function declaration. When the cloned function begins with a single array-pattern declaration
   initialized from the learned argument carrier, promote the pattern elements to parameters,
   substitute `_arg<index>` for holes, and remove that unpacking declaration. The resulting map
   associates each table key with its generated declaration name, while the declarations preserve
   the original generator/async flags and cloned body
   ([`extractFunctions`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/Dispatcher/dispatcher.js#L225-L263)).

3. **Recognize a dispatcher use and form a replacement.** A direct call or `new` expression is a
   candidate only when its callee is an identifier resolving to the dispatcher binding and its
   first argument is a static string key. A member expression whose property equals the learned
   return property recursively wraps such an invocation and is marked as a wrapped use. The key
   and optional static mode form the invocation record. A key absent from the extraction map
   declines at this point. A factory-marked mode produces a bare generated function identifier;
   every other recognized mode produces a call to that identifier with cloned arguments
   ([`dispatcherInvocation` and `replacementFor`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/Dispatcher/dispatcher.js#L285-L340)).

4. **Rewrite the three use-site forms.** `replaceDispatcherCalls` traverses the AST with these
   source-backed rules:

   - A sequence with at least two expressions is eligible when its first expression assigns an
     array to the binding of the learned argument carrier and its last expression is a recognized
     dispatcher invocation. The array elements become direct-call arguments, holes become
     `undefined`, the first assignment disappears, and any middle expressions are retained in
     order before the replacement.
   - A member expression containing a recognized wrapped invocation is replaced by its generated
     call/reference with no explicit arguments. This visitor also covers wrapped `new` expressions.
   - A direct call or `new` expression not already serving as the object of a wrapped member
     expression is replaced when its callee is the dispatcher name and binding. Its replacement
     likewise receives no explicit arguments.

   Each successful replacement increments a counter and skips the replaced path
   ([`replaceDispatcherCalls`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/Dispatcher/dispatcher.js#L265-L470)).

5. **Repeat use-site replacement to a local fixpoint, then clean up.** `transformOne` repeats the
   replacement traversal for at most ten passes, stopping early when a pass makes zero
   replacements. It then removes the dispatcher declaration unconditionally for that recognized
   round. `removeBinding` crawls scope state before checking references and removes an unreferenced
   variable declarator or function declaration; the specialized cleanup removes an unreferenced
   `Object.create(null)` variable declarator when it still matches that exact initializer shape
   ([`transformOne` and cleanup helpers](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/Dispatcher/dispatcher.js#L472-L591)).

6. **Expose nested dispatchers through a bounded outer loop.** `transformAst` calls `transformOne`
   for at most fifty rounds. A false result stops the loop; any true result marks the AST changed
   and permits the next round to find a dispatcher nested in an extracted function body
   ([`transformAst`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/Dispatcher/dispatcher.js#L593-L604)).

The compact state flow is:

```text
qualifying table + learned shape
        -> key -> generated function declaration map
        -> static dispatcher invocation record
        -> direct call/reference AST
        -> fresh-binding cleanup
        -> next nested round or stop
```

## 3. Implementation

| Phase | Source anchor | Ownership | Representation and material behavior |
| --- | --- | --- | --- |
| Key and static-value helpers | [`propName`, `staticString`, `safeName`](https://github.com/MichaelXF/claude-vs-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/Dispatcher/dispatcher.js#L18-L34) | Owned helper plumbing | Keys may be identifiers, string literals, or numeric literals; invocation keys and modes require string literals; generated names replace non-ASCII/non-identifier characters with `_`. |
| Table recognition | [`firstDispatcherTable`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/Dispatcher/dispatcher.js#L58-L85) | Owned algorithm | The first direct-function-local qualifying variable declarator is selected; empty tables, non-object initializers, non-function values, and unsupported keys do not qualify. |
| Shape learning | [`learnDispatcherShape`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/Dispatcher/dispatcher.js#L88-L223) | Owned algorithm | A mutable shape record carries parameter names, markers, wrapped return property, cache name, helper name, and argument carrier. Only the argument carrier and wrapped return property are required by the transform gate. |
| Function extraction | [`extractFunctions`](https://github.com/MichaelXF/claude-vs-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/Dispatcher/dispatcher.js#L225-L263) | Owned algorithm | A table entry becomes a cloned `FunctionDeclaration`; a leading carrier destructure is converted to parameters; key-to-name lookup is held in a `Map`. |
| Binding and array records | [`arrayAssignmentTo`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/Dispatcher/dispatcher.js#L265-L283), [`dispatcherInvocation`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/Dispatcher/dispatcher.js#L285-L326) | Owned algorithm | Sequence extraction is binding-aware for the argument carrier; calls are binding-aware for the dispatcher and retain key/mode/wrapped state. |
| Replacement | [`replacementFor`, `replaceDispatcherCalls`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/Dispatcher/dispatcher.js#L328-L470) | Owned algorithm | Direct calls, wrapped members, and sequence-carrier calls are rewritten; unknown keys and non-static keys are left in place. |
| Scope cleanup | [`removeBinding`, `removeUnusedObjectCreateNullBinding`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/Dispatcher/dispatcher.js#L472-L533) | Owned cleanup | Scope is crawled before reference counts are checked. Only unreferenced matching declarations are removed. |
| Round orchestration and emission | [`transformOne`, `transformAst`, `deobfuscate`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/Dispatcher/dispatcher.js#L535-L623) | Shared coordinator for AST I/O; transform page owns scheduling decisions | One successful recognized round is enough to remove its dispatcher even if zero use-site replacements occurred. The outer loop is capped at 50; changed output is generated with comments removed, noncompact formatting, and a newline, while unchanged input is returned byte-for-byte. |

The parser is configured as script input with `allowReturnOutsideFunction: true` and
`optionalCatchBinding` ([`parse`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/Dispatcher/dispatcher.js#L10-L16)). The file wrapper reads UTF-8, optionally writes the generated output, and exports
`deobfuscate`; the CLI requires both input and output paths
([`deobfuscate` and CLI wiring](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/Dispatcher/dispatcher.js#L606-L637)). These are generic interface plumbing rather than an additional
solution-level transform.

## 4. Upstream Effects

This experiment is a standalone script transform, so there is no earlier decoder pass whose AST
rewrite feeds it. Its upstream state is the direct result of Babel parsing; all source-recognized
bindings are obtained from the parsed scope or refreshed with `scope.crawl()` after inserting
extracted declarations. The pass therefore expects script AST nodes and relies on binding identity
for the dispatcher and carrier at replacement sites, while its initial table/shape discovery also
uses identifier names and literal marker values.

The transform's own first round can expose nested dispatcher functions by cloning table bodies into
the surrounding AST. That is an intra-transform dependency, not an upstream plugin dependency:
the bounded outer loop must revisit the modified AST before emission. No other pass is allowed to
be inferred from the supplied examples, and no decoder pipeline order is established by this
source-only page.

## 5. Known Gaps

- Recognition selects the first qualifying table in the first qualifying function. It does not
  prove that the function is a dispatcher by validating every runtime branch, marker relationship,
  cache use, helper role, or table-key/use-site correspondence.
- The transform gate requires only an argument carrier and wrapped return property. Reset and
  factory markers may remain unset; a missing factory marker simply prevents the bare-identifier
  special case. A learned helper name is recorded for cleanup but does not itself validate the
  dispatcher contract.
- Table keys are normalized to generated names without collision detection. Distinct keys that
  sanitize to the same identifier, duplicate object keys, or unsupported computed keys are not
  given a documented disambiguation path.
- Use sites require static string keys. Dynamic key expressions, aliases that do not resolve to
  the dispatcher identifier, computed forms with non-string static values, or table keys absent
  from the map are left behind. Direct call replacement also checks the dispatcher name in addition
  to binding identity.
- `staticString` is consumed through a truthiness check, so an empty-string key or mode is declined
  even though it is syntactically a string literal; this is a source-specific spelling boundary.
- Sequence rewriting discards the first carrier assignment after cloning its array elements and
  converts holes to `undefined`; its correctness depends on the sample's carrier assignment being
  the intended argument source. Direct calls and `new` expressions receive no explicit arguments,
  which is only source-supported for the corresponding sample forms.
- `transformOne` removes a recognized dispatcher declaration even when the replacement count is
  zero. The implementation is therefore not a general proof-producing rewrite and can partially
  transform a false-positive shape. The fifty-round bound can also leave nested dispatchers when
  the nesting exceeds the bound.
- Cleanup re-crawls by identifier name and removes only declarations with zero references. It does
  not establish semantic equivalence or prove that generated declarations preserve all closure,
  constructor, `this`, or side-effect behavior.
- `deobfuscate` propagates parse/read/write/generator failures. Missing CLI arguments print usage
  and exit with status 1. When no transform round succeeds, the file API preserves source bytes;
  after any successful round, formatting and comments are changed by generation.
- The supplied game and nested example are exact retained examples only; no transfer or production
  qualification is claimed.

## Source

The complete owned implementation is the pinned
[Dispatcher/dispatcher.js](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/Dispatcher/dispatcher.js). The algorithm spans are `firstDispatcherTable` at
L58-L85, `learnDispatcherShape` at L88-L223, `extractFunctions` at L225-L263,
`arrayAssignmentTo`/`dispatcherInvocation` at L265-L326, `replacementFor`/`replaceDispatcherCalls`
at L328-L470, cleanup at L472-L533, and orchestration at L535-L623. CLI/module wiring is at
L625-L637. The experiment's intended input/output contract is documented in
[Dispatcher/README.md](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/Dispatcher/README.md).

## Fixtures

The fixtures and outputs below map the supplied sample inputs, outputs, controls, and test intent.
They do not establish behavioral, transfer, reproduction, or production evidence.

| Pinned file | Claim it pins |
| --- | --- |
| [`input.js`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/Dispatcher/input.js) | The supplied game-shaped dispatcher table, marker branches, carrier assignments, wrapped return property, and static use-site forms. |
| [`input2.js`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/Dispatcher/input2.js) | A nested dispatcher arrangement that motivates repeated outer rounds. |
| [`original.js`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/Dispatcher/original.js) | The readable game-shaped provenance/control reference retained by the experiment; the artifact is comparison provenance only. |
| [`output.js`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/Dispatcher/output.js) | Intended generated shape with `__dispatcher_*` declarations and direct calls after extraction. |
| [`output.cli.js`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/Dispatcher/output.cli.js) | A second retained generated-output artifact for the CLI path; provenance only. |
| [`output2.js`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/Dispatcher/output2.js) | Intended nested-round output with dispatcher layers replaced by generated direct functions. |
| [`regular.js`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/Dispatcher/regular.js) and [`regular.output.js`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/Dispatcher/regular.output.js) | The intended non-dispatcher pass-through pair; byte preservation is an implementation claim from the source, not a measured result. |
| [`test.js`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/Dispatcher/test.js) | Intended assertions for generated names, removed wrappers, nested output, runtime comparison, and regular pass-through; no validation result is claimed. |
