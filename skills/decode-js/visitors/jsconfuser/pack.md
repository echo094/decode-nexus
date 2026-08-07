# jsconfuser/pack.js

## 1. Target

Reverses js-confuser's [Pack](../../../js-confuser/transforms/pack.md): recover the real
program from `Function({objectName}, {outputCode})({objectExpression})` and splice it back
in as a normal top-level script, with every `{objectName}["{propName}"]` reference restored
to the real identifier (or `typeof` expression) it stands for.

## 2. Algorithm

**Match the wrapper structurally, then re-parse its string payload as a fresh program.**
`outputCode` is not embedded AST — it's a string literal holding real source text — so
recovering it means parsing that string, not just matching shapes already in the tree.

Parse the trailing `Function(...)(...)` call to pull out `objectName`, the `outputCode`
string, and the property map: for each property in the object-literal argument, a `get`
method's `return` argument *is* the real reference — a plain `Identifier` for a normal
global, or a `typeof` `UnaryExpression` for a `typeof`-mapped one, both left as-is rather
than distinguished, since the same "read the return argument" step recovers the correct
expression either way; a `set` method's body assigns back to the same identifier, read off
the assignment's left side. A property with both ends up read twice, once each way, but
both reads resolve to the identical `Identifier` node, so processing order between them
doesn't matter.

Re-parse `outputCode` as the real program's body, then substitute every
`{objectName}["{propName}"]` `MemberExpression` with the mapped expression directly (not a
clone — every occurrence of one property ends up referencing the *same* AST node object,
which prints correctly regardless, since generation walks structure rather than caring
about node identity).

Finally, reverse the encoder's trailing-return rewrite (see encoder doc's Algorithm):
`outputCode` was generated as a function body, so Pack's own encoder unconditionally turns
the program's last `ExpressionStatement` into a `return` to keep the wrapper call's
completion value. A trailing top-level `ReturnStatement` is illegal in a script spliced
back to real top level, so it becomes an `ExpressionStatement` again — a bare `return;` is
dropped entirely, since there's no value to preserve.

## 3. Implementation

**`checkNode(node)`** matches the fixed wrapper shape structurally: unwraps an
`ExpressionStatement` if present, then requires a `CallExpression` whose own callee is
*another* `CallExpression` to an `Identifier` named `Function` with exactly two
`StringLiteral` arguments, itself called with exactly one `ObjectExpression` argument.
Builds the property map by walking that object's `properties`: a `get`-kind method's
`obj[key] = item.body.body[0].argument` (the `return`'s argument node directly); a
`set`-kind method's `obj[key] = item.body.body[0].argument.left` (the assignment
expression's left side). Returns `{ objectName, outputCode, objectExpression }`, or
`undefined` if the shape doesn't match at all.

**`parseOutputCode(code, objName, objValue)`** parses `outputCode` fresh
(`errorRecovery: true`) and traverses once, replacing every `Identifier` named `objName`'s
*parent* `MemberExpression` (`objValue[path.parentPath.node.property.value]`) with the
mapped node. Then reverses the trailing-return rewrite on the parsed body's own last
statement: a `ReturnStatement` with an argument becomes an `ExpressionStatement` wrapping
that argument; a bare `return;` (`last.argument` absent) is popped off entirely.

**`dePack(ast)`** is the exported entry: reads the Program's own last statement through
`checkNode`; if it doesn't match, the whole `ast` is returned completely unchanged (a
non-pack program is inert input, not an error). On a match, pops that last statement and
pushes the unpacked body's statements in its place. Any `prependNodes` (hoisted `import`s)
the encoder placed *before* the wrapper are untouched by construction, since only the last
statement is ever read or replaced — verified empirically with a leading `import`
statement ahead of the wrapper.

## 4. Upstream Effects

**None inbound** — Pack is the pipeline's first pass, so no decoder pass of ours has
touched its input. What it owes the rest of the pipeline is the inventory of what it
*emits*, per [doc-conventions.md](../../../doc-conventions.md)'s home rule: the payload is
re-parsed from a string literal (item 3's `parseOutputCode`), so every statement Pack
splices in belongs to a **freshly parsed AST**, and its `node.start`/`node.end` are offsets
into the payload text rather than into the outer program. Any later pass that reasons about
containment or document order has to ask the path ancestry instead — see
[babel.md](../../babel.md)'s "Source positions are meaningless after an earlier pass
rebuilds a subtree", which this pass is one of the producers behind.

## 5. Known Gaps

None currently open. The `pack-payload` fixture ([tests.md](../../tests.md)) puts four
transforms inside a Function-constructor payload and pins the trailing-return reversal and
the multi-reference substitution above under a real encode→decode→run check, so neither
rests on unit coverage alone.

## Source

[`src/visitor/jsconfuser/pack.js`](https://github.com/echo094/decode-js/blob/6c974fb5720518fac9c6b3d4cf558ba90ef9f8e7/src/visitor/jsconfuser/pack.js), wired into
[plugin/jsconfuser.js](../../plugins/jsconfuser.md) as step 1 — **must run first**, since
everything else in the pipeline operates on the unwrapped AST.

## Fixtures

`test/visitor/jsconfuser/pack.test.js` — the trailing-return's three shapes (an expression, a
bare `return;`, no trailing return at all), one property-mapping substitution, and the
non-pack passthrough case.
