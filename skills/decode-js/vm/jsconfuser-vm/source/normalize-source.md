# Input normalization and the statement view

Part of the [`source` module](../source.md). Pipeline stage: `prepare-source`
([map](../../../pipelines/jsconfuser-vm.md#frontend-order)).

## 2. Algorithm

The normalization gives the standalone decode one spelling of property access and of simple
control bodies. It addresses ordinary JavaScript shapes only: it identifies no VM role and
creates no opcode, pool or sentinel reference.

```text
normalizeVmInput(source):                      // explanatory pseudocode
  if source is not a string: return source     // the decode refuses it itself
  ast = parse(source) as a script, no error recovery, no return outside a function
  if the parse throws: return source           // the decode reports the syntax error
  changed = normalizeVmAst(ast)
  return changed ? generate(ast) : source      // unchanged input is returned as the same string

normalizeVmAst(ast):                           // three traversals, in this order
  1. uncompute-member         o["name"]      -> o.name
  2. uncompute-property-key   { ["k"]: v }   -> { k: v }
  3. simple control bodies    if (c) { return x; }  ->  if (c) return x;
  return whether any of them changed a node
```

The two key rewrites are the shared atomic visitors with their own guards: numeric and
non-identifier keys, optional access, a computed object `__proto__`, a class `constructor` and a
static class `prototype` keep their spelling.

A **simple control body** is a block with no directive whose single statement is an expression,
`return`, `throw`, `break` or `continue` statement. Step 3 replaces such a block by its statement
where it is an `if` branch or the body of a `for`, `for-in`, `for-of`, `while` or `do-while`.
Every other block stays: one holding a declaration (its lexical scope), one holding a nested `if`
(an unbraced nested `if` would capture the outer `else`), one with several statements, and every
function body.

**Declaration placement is not normalized.** An outer decoder can leave `var f, data;` followed by
`f = function hidden(x) { return x; }; data = [1];`. The normalization keeps that spelling, and
the readers take a bare `var` from its single top-level defining write
([container](container.md#2-algorithm)). Joining the assignments back into declarators would also
rewrite the interpreter's handler bodies, whose statement count behaviour matching compares, and a
join by enclosing-scope lookup would let a write inside a nested function absorb an outer
declaration.

**The statement view.** A reader that compares statements must see the same form whether a simple
body arrived braced or bare. `simpleControlBody(node)` returns the single statement of a simple
control body and any other node as it is; `isControlBodyKey(type, key)` says which fields are
control bodies. The view returns the existing node, so bindings and node identity are kept; it
erases no lexical or multi-statement block. Its one user is the
[handler locator's statement lowering](../handlers/locate-handlers.md), on cloned handler
statements.

### Worked example

A hand-written input, not encoder output:

```js
function h(r, x, y) { if (r["a"] === 65535) { return x["length"]; } else { y = { ["k"]: 1 }; } while (x) { let z = y; } }
```

`normalizeVmInput` returns:

```js
function h(r, x, y) {
  if (r.a === 65535) return x.length;else y = {
    k: 1
  };
  while (x) {
    let z = y;
  }
}
```

Both `if` branches were simple bodies. The `while` body holds a `let` and keeps its block. The
literal `65535` is left as written.

## 3. Implementation

| Export | Contract | Imported by |
|---|---|---|
| `normalizeVmInput(source)` (default) | The algorithm above. Never throws on a string; returns the input string itself when nothing changed or it does not parse. | the [plugin](../../../plugins/jsconfuser-vm.md), which passes the result to the one standalone decode |
| `normalizeVmAst(ast)` | Runs the three traversals on one tree in place; returns whether any changed it. | the test |
| `normalizeControlBodies` | The visitor of step 3. On exit of an `if` or loop it replaces each simple body by a clone of its statement and counts the change in `state.changes`; on Program exit, if it changed anything, it re-crawls the Program scope. | the test |
| `simpleControlBody(node)` | The statement view. | `handlers/normalize-handler-statements.js` |
| `isControlBodyKey(type, key)` | `IfStatement` `consequent`, `alternate`; the five loop types' `body`. | `handlers/normalize-handler-statements.js` |

The parse is `sourceType: 'script'`, `errorRecovery: false`, with a `return` outside a function a
syntax error; a module or such a return therefore reaches the decode unprepared and is refused
there. Each visitor checks a candidate before it mutates; a candidate it refuses is left
untouched and the others still normalize. A replacement is a clone, never a node shared between
two positions. All three visitors count into the same `state.changes`.

What the plugin publishes is the plugin's decision: fresh emitted JavaScript on success, and the
exact original input on a decline, including when the normalization had changed its spelling
([plugin](../../../plugins/jsconfuser-vm.md)).

## 5. Known Gaps

- The normalization is fitted to the VM decoder's readers. Nothing establishes it as a
  normalization for another consumer; one that reuses it must check the three rewrites and their
  order against its own input.
- A constant simplifier upstream can leave `argc === 65535` where the encoder wrote a
  sentinel-map read. The normalization keeps the literal and recreates no map read; the
  [handler locator](../handlers/locate-handlers.md) reads both forms as the number.

## 6. Source

- [normalize-source.js](../../../../../decoder/decode-js/src/vm/jsconfuser-vm/source/normalize-source.js):
  the whole part.
- [uncompute-member.js](../../../../../decoder/decode-js/src/visitor/atomic/uncompute-member.js) and
  [uncompute-property-key.js](../../../../../decoder/decode-js/src/visitor/atomic/uncompute-property-key.js):
  the two reused visitors, documented under
  [uncompute-member](../../../visitors/atomic/uncompute-member.md) and
  [uncompute-property-key](../../../visitors/atomic/uncompute-property-key.md).

## 7. Fixtures

Tests: [normalize-source.test.js](../../../../../decoder/decode-js/test/vm/jsconfuser-vm/single-component/normalize-source.test.js)
and [plugin.test.js](../../../../../decoder/decode-js/test/vm/jsconfuser-vm/public-entry-points/plugin.test.js).
No cell suite names this part; every cell passes through it.

| Scenario | Expected result | Committed fixture |
|---|---|---|
| A hoisted `var` list with later assignments, one a function expression | Left as written; scope state equals a fresh parse; the program runs as before | normalize-source.test.js |
| Computed `["__proto__"]` object key and class `["constructor"]` | Kept computed; ordinary computed keys become plain | normalize-source.test.js |
| Blocks holding a lexical declaration; an inner `if` under an outer `else` | Blocks kept, `else` still bound to the outer `if`; simple bodies unbraced; the program runs as before | normalize-source.test.js |
| Normalizing a normalized source | The same string | normalize-source.test.js |
| `function (`, a top-level `return 5;`, `export const x = 3;` | The input string, unchanged | normalize-source.test.js |
| The plugin's call | One standalone decode, of `normalizeVmInput(input)`; the record's `input` is the original | plugin.test.js |
| A non-string input | Passed through | |
