# split-assignment.js

Hoists an `AssignmentExpression` out of an expression position into a statement of its own just
before the enclosing statement, and leaves its target behind as the value. Turns `if (a = b) {…}`
into `a = b; if (a) {…}`. A readability pass: it reverses nothing an encoder added, so its only
contract is that the program behaves as before, and where that cannot be shown it leaves the
assignment in place.

## Procedure

```text
on each AssignmentExpression `asg`, top-down (Babel key order):
  insert = getInsertPath(asg)          # the statement to insert before, or undefined
  if insert is undefined: leave asg
  insert.insertBefore(ExpressionStatement(asg))
  replace asg with clone(asg.left)     # a clone: asg.left now lives in the new statement
  mark the traversal as having split
on Program exit: if anything split, crawl the program scope once
```

```text
getInsertPath(asg):
  if asg.left is not an Identifier: return undefined          # gate 1
  rightIsPure = scope.isPure(asg.right)
  child = asg; needSplit = false
  for parent = child.parent until a BlockStatement or Program:
    for operand in earlierOperands(parent, child.key):
      if not inert(operand): return undefined                 # gate 2
    if parent/child.key is not an allowed position: return undefined
    if the position sets needSplit: needSplit = true
    child = parent
  return needSplit ? child : undefined

earlierOperands(parent, key):              # evaluated before the child
  AssignmentExpression, key = right:
    left Identifier, `=`        -> none      (resolving `x` reads nothing)
    left Identifier, `op=`      -> [left]    (reads x)
    left member, `=`            -> [object] + [property if computed]
    otherwise                   -> [left]    (`o[k] op=` reads o[k])
  MemberExpression, key = property -> [object]
  otherwise                        -> none

inert(operand):
  Identifier: name != asg.left.name and (rightIsPure or its binding is constant)
  string, numeric, boolean, null or bigint literal, `this`: yes
  anything else: no                         # a member read may run a getter, a call anything
```

An inert operand gives the same value with the same effects whether it runs before or after the
moved assignment, so hoisting past it changes nothing. A variable stays unchanged unless the
assignment writes it: directly (it is the target) or through a call in the right side, which a pure
right side or a never-reassigned binding rules out.

| Parent | Allowed when the child is | Sets `needSplit` |
|---|---|---|
| `AssignmentExpression` | any operand | yes |
| `CallExpression` | the `callee` | yes |
| `ExpressionStatement` | — | no |
| `IfStatement` | the `test` | yes |
| `MemberExpression` | `object` or `property` | yes |
| `VariableDeclarator` | the `init` | yes |
| `VariableDeclaration` | declarator 0 | yes |

The climb succeeds only if some step set `needSplit`; a bare `a = b;` statement is left alone.

## Why the two gates

The rewrite reads the target again after the assignment, and runs the assignment before everything
the statement evaluated ahead of it. Each gate removes one way that changes behaviour (decode-js
issue [#225](https://github.com/echo094/decode-js/issues/225)):

| Gate | Source | Split without the gate | Effect |
|---|---|---|---|
| 1, target not an `Identifier` | `var e = a[a.length] = v` | `a[a.length] = v; var e = a[a.length]` | reads the next, empty slot |
| | `if ([][undefined] = "x")` | `[][undefined] = "x"; if ([][undefined])` | a fresh array: the other branch |
| | `var v = a[i++] = x` | `a[i++] = x; var v = a[i++]` | `i` incremented twice |
| 2, earlier operand not inert | `a[i] = i = 1` | `i = 1; a[i] = i` | writes the new index |
| | `r = o[i][i = 1]` | `i = 1; r = o[i][i]` | reads the new index |
| | `x += x = 1` | `x = 1; x += x` | adds the new `x` |
| | `o.k = t = f()`, `f` sets `o = null` | `t = f(); o.k = t` | `TypeError`: the store goes to the new `o` |
| | `r = o.p[i = 1]`, getter `p` reads `i` | `i = 1; r = o.p[i]` | the getter sees the new `i` |

An identifier target reads back exactly the assigned value, so gate 1 makes the left-behind value
right; gate 2 makes the earlier start harmless. A split that kept behaviour in the declined cases
would need a temporary to hold the old value or the assigned one; this pass never introduces one,
so it leaves those assignments as the source wrote them.

**Worked example** (fixture `call-valid-1`). In
`x[(b = d[(d = _)("1")]("2"))[0][d("3")]()] = …` the outer `b = …` is visited first. Its climb
passes the `property` of `x[…]`; its object `x` is not the target, and although the right side
calls `d`, `x` is a parameter never reassigned, so it is inert and `b = …` is hoisted:
`b = d[(d = _)("1")]("2"); x[b[0][d("3")]()] = …`. The traversal then reaches `d = _` inside the
moved statement; its climb passes the `property` of `d[…]`, whose object is the target `d`, so
gate 2 keeps it in place: the source indexes the old `d`, which the split would have replaced by
`_`.

**The crawl is program-scoped and runs once per traversal.** `insertBefore` re-homes the moved
subtree and registers its references a second time, so a binding can list one live node twice; a
later pass that deletes a binding once "every reference is resolved" would then pass that check
with a reference unhandled ([S6](../../encoder-decoder-method.md#s6-a-passs-contract-is-output-derived-state--verify-both-halves)).
The moved assignment can reference bindings of an enclosing scope, so only the program scope
restores them. Nothing in this pass reads scope state, so deferring the crawl to `Program.exit` is
safe.

Consumed only by the [obfuscator](../plugins/obfuscator.md) plugin's `purifyCode`. Related
statement-splitters: [split-sequence.js](split-sequence.md),
[split-variable-declaration.js](split-variable-declaration.md).

## Source

`src/visitor/split-assignment.js` (default export: the visitor); wired in `src/plugin/obfuscator.js`
`purifyCode`, after the empty-statement removal and before `delete-unused-var`.

## Fixtures

`test/visitor/split-assignment.test.js` over `test/visitor/split-assignment/`. The gate fixtures are
hand-built source shapes; javascript-obfuscator passes such source through unchanged.

| Case | Pins |
|---|---|
| `call-valid-1` | nested hoists through callee and member positions in visit order; gate 2 on a member object (`d[(d = _)…]`) |
| `if-assignment-valid` | an `if` test |
| `if-member-valid` | two hoists from one member's object and property |
| `member-valid-1` | a member object |
| `assignment-member-name-valid` | gate 2 passes: a non-computed property spelled like the target is not an operand |
| `variable-valid` | a first declarator's `init` |
| `if-invalid` | no-op: the `if` sits in a `while` body without a block |
| `variable-invalid` | no-op: a `for` init |
| `variable-member-target-invalid` | gate 1: a member target in a declarator `init` |
| `if-member-target-invalid` | gate 1: a member target in an `if` test |
| `variable-update-key-invalid` | gate 1: a member target whose key has a side effect |
| `assignment-member-left-invalid` | gate 2: the outer assignment's member left reads the target |
| `member-property-invalid` | gate 2: the member object reads the target |
| `compound-left-invalid` | gate 2: a compound outer assignment reads its identifier left |
| `call-right-invalid` | gate 2: a call in the right side may write a reassigned earlier operand |
| `member-getter-invalid` | gate 2: a member read in the earlier operand may run a getter |
