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

- **Candidate gate** — the declarator id must be an `Identifier`, and its binding must exist in
  the current Babel scope. A missing binding, `ObjectPattern`, `ArrayPattern`, or any other
  non-Identifier id is left untouched before binding state is read. This is a safe fail-closed
  refusal; it does **not** decode or merge destructuring declarators.
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

Logs `尝试性合并: <name>` ("tentative merge"). Closely related to
[parse-control-flow-storage.js](parse-control-flow-storage.md), which consumes the *same*
reassembled object shape and inlines its call sites.

## Source

- [`src/visitor/merge-object.js`](https://github.com/echo094/decode-js/blob/6cacb633ceedf0812fe31f951ba8f41ffb431ca1/src/visitor/merge-object.js)
- Consumed by the `obfuscator` plugin, and by `obfuscatorx` through
  [normalize-converting](obfuscator/normalize-converting.md), where it is scheduled fourth in the
  round. **That position is a convenience, not a constraint** — it accepts both string and
  identifier properties, so it does not in fact require the un-computing passes to have run; it is
  placed after them only so the merged output reads dotted. That doc's item 4 records it so nobody
  inherits it as a rule.

## Fixtures

**The older coverage was indirect; focused direct and entry regressions now name this pass.** It
still runs in every case that drives [normalize-converting](obfuscator/normalize-converting.md) —
that pass's own four goldens, plus `unlock-env-pipeline` and the four `era-below-2-16` cases — but
those nine committed cases exercise it only through the surrounding pipeline. The focused direct
visitor cases and the exact static-block entry case below assert the new gate and its repair.

| Claim | What checks it today | Gap |
|---|---|---|
| the merge fires on real encoder output | the nine cases above, and the corpus runs: this pass is what reassembles the control-flow storage object that `parse-control-flow-storage` then inlines, so a storage cell that decodes is evidence it fired | indirect — a failure here reads as a failure of the composition or of the storage pass, one level away from its cause |
| non-Identifier declarators are refused safely | [`test/visitor/merge-object.test.js`](https://github.com/echo094/decode-js/blob/6cacb633ceedf0812fe31f951ba8f41ffb431ca1/test/visitor/merge-object.test.js) leaves ObjectPattern and ArrayPattern declarators unchanged | direct gate coverage; this is a safe refusal, not destructuring reconstruction |
| an Identifier merge remains active | [`test/visitor/merge-object.test.js`](https://github.com/echo094/decode-js/blob/6cacb633ceedf0812fe31f951ba8f41ffb431ca1/test/visitor/merge-object.test.js) asserts the existing Identifier merge path | direct focused coverage; broader merge-window behavior remains unpinned |
| the static declaration entry path avoids the old TypeError | [`test/obfuscatorx/static-top-level-declaration.test.js`](https://github.com/echo094/decode-js/blob/6cacb633ceedf0812fe31f951ba8f41ffb431ca1/test/obfuscatorx/static-top-level-declaration.test.js) covers exact 5.3.1/5.4.0 declaration outputs and preserves their patterns | entry coverage; surrounding normalization decodes, but `merge-object` does not decode a pattern |
| the merge window closes at the first constant violation | nothing | a window that never closed would merge across a reassignment and silently change meaning |
| a duplicate key aborts the merge | nothing | — |
| an unresolvable property aborts the merge | nothing | — |

**The three abort paths are the part worth pinning first.** This pass rewrites rather than
declines after a candidate has passed the gate, so its failure mode is corruption rather than
legible residue — and corruption is only loud when it happens to throw. The initial
Identifier/binding gate is different: it is deliberately a safe refusal. The direct regression
cases in [`test/visitor/merge-object.test.js`](https://github.com/echo094/decode-js/blob/6cacb633ceedf0812fe31f951ba8f41ffb431ca1/test/visitor/merge-object.test.js)
pin both halves — ObjectPattern/ArrayPattern are unchanged, while an Identifier merge remains
active.

The exact top-level static-block declaration outputs from the 5.3.1/5.4.0 encoder pair are also
covered through the entry by
[`test/obfuscatorx/static-top-level-declaration.test.js`](https://github.com/echo094/decode-js/blob/6cacb633ceedf0812fe31f951ba8f41ffb431ca1/test/obfuscatorx/static-top-level-declaration.test.js).
That regression proves the guard prevents the old TypeError and preserves the destructuring
pattern while the surrounding normalization decodes; it is not evidence that `merge-object`
reconstructs a destructuring pattern. The permanent test links above pin both the focused evidence
and the repair qualification.

**Its log line is the only channel it has.** `尝试性合并` is pre-existing non-English output and is
left as it stands; what matters here is that the pass reports nothing structured, so a caller
cannot tell a merge from a decline without diffing the tree.
