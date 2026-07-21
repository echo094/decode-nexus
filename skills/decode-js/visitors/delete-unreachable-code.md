# delete-unreachable-code.js

Drops statements after the first *unconditional* `ReturnStatement` in a
`BlockStatement`. `checkReturnLocation(body)` DFS-scans for the index of the first
statement that is either a `ReturnStatement` or a nested `BlockStatement` that itself
contains a return (so a return buried one block deep still counts as the cutoff point).

Everything after that index is spliced out — **except `FunctionDeclaration`s**, which
are hoisted and must survive. As a final tidy-up, if the cutoff is at index 0 and that
first statement is a nested block, the block's statements are unshifted inline to the
front. The header notes it is intentionally looser than
`@putout/plugin-remove-unreachable-code`. Only the `common` plugin uses it.
