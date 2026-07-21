# merge-object.js

Reverses javascript-obfuscator's **ObjectExpressionKeysTransformer**: an object built up
by a sequence of member assignments after an empty (or partial) literal is folded back
into a single object literal.

```javascript
// From
var _0xb28de8 = {};
_0xb28de8["abcd"] = function (a, b) { return a == b; };
_0xb28de8.dbca = function (f, x, y) { return f(x, y); };
_0xb28de8["bbb"] = "eee";
var _0x15e145 = _0xb28de8;
// To
var _0x15e145 = {
  "abcd": function (a, b) { return a == b; },
  "dbca": function (f, x, y) { return f(x, y); },
  "bbb": "eee"
};
```

Visits `VariableDeclarator` with an `ObjectExpression` init. Key steps:

- **Merge window** — if the binding isn't `constant`, the first later
  `VariableDeclarator`/`AssignmentExpression` `constantViolation` (by source position)
  becomes the `end` bound; references and merges past it are ignored. Other violation
  kinds abort.
- **Collect existing keys** into `keys{}` to forbid redefinition.
- **Merge loop** over references in source order: each must be the `object` of a
  `MemberExpression` that is the `left` of an `AssignmentExpression`, whose enclosing
  statement chain (through `SequenceExpression`/declarator/declaration/expression-
  statement wrappers) reaches the declaration's container. The property (string or
  identifier) is pushed as a new `t.ObjectProperty(valueToNode(key), right)`; a duplicate
  key or unresolvable property sets `valid = false` and stops.
- **Remove merged assignments** (replacing with `left` when nested in a
  declarator/assignment, else removing), then—if the object's sole remaining reference is
  a `var x = obj` initializer—**move the object definition into that reference** and drop
  the original (or null its init if the violation was an assignment).

Logs `尝试性合并: <name>` ("tentative merge"). Consumed by the `obfuscator` plugin.
Closely related to [parse-control-flow-storage.js](parse-control-flow-storage.md), which
consumes the *same* reassembled object shape and inlines its call sites.
