# calculate-rstring.js

Folds "reverse-string" constructions: `"sh".split("").reverse().join("")` → `"hs"`.

Visits `StringLiteral` nodes whose `path.key === 'object'` — i.e. the string sits at the
head of a member/call chain. From there it climbs up to **exactly 6** parent levels,
each of which must be a `MemberExpression` or `CallExpression` (`.split` `(` `"")`
`.reverse` `()` `.join` `("")` — six wrapping nodes). If the chain isn't a full 6 deep
(`count` didn't reach 0), it bails. Otherwise it `generator`s the whole chain, runs it
through the **host `eval`**, and replaces the chain with `t.stringLiteral(result)`;
any `eval` throw is swallowed.

Only the `common` plugin uses it. Narrower than
[calculate-constant-exp.js](calculate-constant-exp.md) — it matches one fixed
string-manipulation shape rather than general literal arithmetic.
