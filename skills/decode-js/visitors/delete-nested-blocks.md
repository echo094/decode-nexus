# delete-nested-blocks.js

Flattens a redundant `BlockStatement` into its parent. Fires only when the parent is
itself a `BlockStatement` or the `Program`, and one of two conditions holds:

- the inner block is the **only** statement in its container (`path.container.length ===
  1`), or
- the inner block's bindings **don't intersect** the parent scope — `isIntersect`
  crawls the parent scope and returns true if any of the inner block's binding names
  already exist there, so flattening is blocked exactly when it would collide/redeclare.

When allowed, `replaceWithMultiple(path.node.body)` splices the inner statements up one
level and the scope is re-crawled. The header notes this is deliberately looser than
`@putout/plugin-remove-nested-blocks`. Only the `common` plugin uses it.
