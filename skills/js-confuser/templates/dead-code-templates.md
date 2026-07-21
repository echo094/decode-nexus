# deadCodeTemplates.ts

Provides `deadCodeTemplates`: an array of roughly twenty large, realistic-looking JS
snippets — a full SHA-256 implementation, a UTF-8 codec library, an RSA class, a jQuery
`curCSS`-style helper, a React-shaped component, serverless-CLI-looking module
boilerplate, cookie/`localStorage` helpers, and a handful of LeetCode-style algorithm
solutions (two-sum-adjacent, N-Queens, LRU cache, string interleaving, ...). One is
chosen at random per insertion.

Used by [DeadCode](../transforms/dead-code.md) — the point isn't obfuscation logic, it's
plausibility: a reverse engineer who stumbles into one of these unreachable branches
finds what looks like genuine, unrelated functionality (complete with realistic variable
names and, in some snippets, third-party attribution comments) rather than an obvious
placeholder, making it harder to immediately recognize as dead code from content alone.
