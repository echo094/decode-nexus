# Dispatcher

Source: [transforms/dispatcher.ts](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/dispatcher.ts) — `Order.Dispatcher = 6`.

## 1. Target

Merge every eligible named function declaration in a block into one shared closure keyed
by a fresh random name, so no separate function declarations remain, the original name is
discarded entirely — unlike Flatten/RGF, no trace of it survives anywhere in the output,
not even as a call-site identifier — and each original call site becomes an indirect
lookup through a dispatch object rebuilt fresh on every invocation.

## 2. Algorithm

Runs independently on **every block** (`Program` and every function body). An eligible
function's params/body become a niladic function expression, params unpacked via array
destructuring, stored as a property of an `fns` object literal keyed by a fresh random
name — rebuilt fresh on **every** dispatcher call, not hoisted. Call sites become calls to
a shared per-block dispatcher function, passing the key plus a payload array for
arguments; a non-call reference instead gets a cached, always-rest-param closure via a
separate flag path. The return value can optionally be wrapped in an object key before
returning and unwrapped again at the call site — a pure round trip, semantically a no-op
either way, existing purely as extra obfuscation.

## 3. Implementation

**Eligibility** ([`dispatcher.ts:94-161`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/dispatcher.ts#L94-L161)):
a function is illegal (skipped, left untouched) if it's unnamed, async/generator, nested
(not a direct child of the block being processed), under a `"use strict"` directive,
already `UNSAFE`/redefined/an internal obfuscator name, or has a default-parameter
(`AssignmentPattern`) anywhere in its param list. **Rest params are fine** — only default
values disqualify a function. Reassigned/redefined names (tracked via `illegalNames`,
including any binding identifier outside a `FunctionDeclaration`) are excluded too.

```js
function {dispatcherName}(name, flagArg, returnTypeArg, fnLengths = {...}) {
  var output;
  var fns = { "{newName}": function(){ var [p1, p2, ...] = {payloadName}; /* body */ } };

  if (flagArg === "{clearPayloadKey}") { {payloadName} = []; }

  if (flagArg === "{nonCallKey}") {
    function createFunction() {
      var fn = function(...args) { {payloadName} = args; return fns[name].apply(this); };
      var fnLength = fnLengths[name];
      if (fnLength) { {ph}_d_fnLength(fn, fnLength); }
      return fn;
    }
    output = {cacheName}[name] || ({cacheName}[name] = createFunction());
  } else {
    output = fns[name]();
  }

  if (returnTypeArg === "{returnAsObjectKey}") {
    return { "{returnAsObjectPropertyKey}": output };
  } else {
    return output;
  }
}
```

**The unpack line is emitted only when the original had parameters**
([`dispatcher.ts:318-329`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/dispatcher.ts#L318-L329)),
and its pattern is `t.arrayPattern([...originalFn.params])` — **a copy of the original
parameter list, whatever shape an earlier transform has already given it.** A niladic
user function therefore does not always yield a zero-parameter entry: `Flatten` (Order 2,
well ahead of this transform's Order 6) replaces such a function with an extracted
top-level `function {new}(flatObj, [ ])` whose second parameter is
`t.arrayPattern([...params])` over an empty list
([`flatten.ts:319-323`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/flatten.ts#L319-L323)).
That extracted function is a plain top-level `FunctionDeclaration`, so it is eligible
here, and the entry it produces opens with a literal empty-pattern element:
`var [flatObj, []] = {payloadName};`. The shape needs both transforms — turning off
either one removes it — so an `fns` entry seen in the wild is frequently Flatten's
extracted function rather than any function the user wrote.

**Call sites** ([`dispatcher.ts:221-257`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/dispatcher.ts#L221-L257)'s
`createDispatcherCall`, shared by both real invocations and non-call references, which is
why both can independently roll the same ~50% "as object" obfuscation):

| site | shape |
|---|---|
| zero-arg call | `{dispatcherName}(newName, clearPayloadKey)` |
| non-zero-arg call | `({payloadName} = [args], {dispatcherName}(newName))` (args copied as-is, spreads included) |
| non-call reference | `{dispatcherName}(newName, nonCallKey)` — returns a cached, always-rest-param closure |
| any of the above, "as object" | wrapped in `["{returnAsObjectPropertyKey}"]` member access, optionally over a `new` expression instead of a call |

**`preserveFunctionLength`** matters only for the **non-call-reference** path: the cached
closure `createFunction()` returns is always a bare `(...args) => ...` (`.length === 0`),
so [`fnLengths[name]`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/dispatcher.ts#L373-L409)
feeds the shared `{ph}_d_fnLength` helper to override it back. Direct calls never go
through this path at all — their arity was never in question. A **Program-level
`{ph}_d_fnLength` helper is inserted unconditionally** on every Program exit, regardless
of whether any block actually dispatches a function — an empty no-op if
`preserveFunctionLength` is off, the real template otherwise.

## 4. Downstream Effects

- **`VariableMasking` (Order 20)** masks this transform's own generated scaffolding too,
  not just user code: `createFunction`'s local `var fnLength = fnLengths[name];`, and this
  transform's own `fns` entries — anonymous `FunctionExpression`s that take zero
  *declared* params by construction (original params are unpacked from the payload array
  inside the body).
  - **A masked `fns` entry carries no `stackName["length"] = N` truncation statement**,
    because this transform marks every entry `PREDICTABLE`
    ([`dispatcher.ts#L361`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/dispatcher.ts#L361))
    and VariableMasking emits that statement only for functions lacking the flag
    ([`variableMasking.ts#L220-L229`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/variableMasking.ts#L220-L229)).
    The emitted shape is therefore anonymous *and* carries no declared arity anywhere in
    it — the count is recoverable only from this transform's own construction rule (always
    zero), not from anything readable at the masked site.
  - Together with [preparation.md](preparation.md)'s `PREDICTABLE` scope note, this is the
    only way an *anonymous* function reaches Order 20 already flagged: Preparation marks
    named `FunctionDeclaration`s only, so a user-source anonymous function always keeps its
    truncation statement.
  - **The unpack line stops being a declaration.** Masking an entry rewrites the pattern's
    defining identifiers into stack member expressions, and a `MemberExpression` cannot be a
    declarator id — so
    [`replaceDefiningIdentifierToMemberExpression`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/utils/ast-utils.ts#L593-L640)'s
    `var id = 1` -> `id = 1` branch replaces the whole `VariableDeclaration` with an
    `ExpressionStatement`, reached from the masking visitor's `isDefiningIdentifier` test
    ([`variableMasking.ts#L200-L206`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/variableMasking.ts#L200-L206)).
    `var [p1, p2] = {payloadName};` becomes `[stk["a"], stk["b"]] = {payloadName};`. Two
    consequences are easy to get wrong from the residue alone: the statement is an
    *assignment*, so the pattern's names are no longer declared by it, and it is now an
    `ExpressionStatement` — which is what lets `MovedDeclarations` below prepend a
    declaration above it rather than merging into it, displacing it off the body's front.
- **`ControlFlowFlattening` (Order 24)** can flatten a function nested inside this
  transform's own dispatch closure, producing an inline interpreter assigned to a local
  rather than the usual `FunctionDeclaration` + entry-harness shape — see
  [control-flow-flattening.md](control-flow-flattening.md)'s note on outlined nested
  functions.
- **`MovedDeclarations` (Order 25)** dismantles the template's own declaration prologue, and
  this is the single largest change to the emitted shape. The dispatcher function is marked
  `PREDICTABLE`
  ([`dispatcher.ts#L411`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/dispatcher.ts#L411)),
  which is exactly the flag that transform's `VariableDeclaration` visitor gates on
  ([`movedDeclarations.ts#L118-L212`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/identifier/movedDeclarations.ts#L118-L212)).
  Every single-declarator `var` in the body is replaced in place by a bare
  `name = init` assignment, and its declaration goes to one of two places:
  - **onto the parameter list** (`functionParameter`), appended after the template's own
    four. Both `var output;` and `var fns = {...}` qualify, so the emitted signature is
    routinely six parameters rather than four, with the template's four still at indices
    0-3 and the extras carrying no caller-supplied value.
  - **into the block's first `var`** (`variableDeclaration`), which *appends a declarator to
    an existing one* rather than adding a statement. This is what produces a merged
    `var output, fns, createFn;` prologue — worth naming because the shape reads like
    `Minify`'s doing and is not.

  Either way the body no longer opens with the two declarations the template emits, and the
  count of leading statements is not fixed.
- **`Minify` (Order 28)** rewrites this template two ways. It can convert a valid-identifier
  string key (an `fns` entry's key, the `returnAsObjectProperty` wrap key) back to dot form.
  It also folds the trailing `if (returnTypeArg === K) { return {...} } else { return output }`
  into a **single conditional return**, `return returnTypeArg === K ? {...} : output`
  ([`minify.ts#L489-L497`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/minify.ts#L489-L497)) —
  so the template's third `if` is not always an `if`, and both keys it carries move into a
  `ConditionalExpression`.

## 5. Known Quirks

None currently documented.
