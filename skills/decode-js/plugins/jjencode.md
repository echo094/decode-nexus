# jjencode.js

Target: **jjencode** (http://utf-8.jp/public/jjencode.html). The header notes jjencode is
an *encoder*, not an obfuscator — it's reversible and doesn't alter the original program —
so this plugin fully recovers the source. Uniquely among the plugins it does **no AST
work**: it's pure string surgery plus the host `eval`.

`getCode(code)`:

1. Split the input on `;` into non-empty blocks; there must be **exactly 6**.
2. Block 0 must be `<var> = …~[]…`; the left side gives the global variable name (`~[]`
   is jjencode's signature).
3. Reconstruct the payload from block 5 by trimming a fixed prefix
   (`<var>.$(<var>.$(<var>.$$+"\""+`) and suffix (`"\"")())()`) via **subsequence
   matching** from both ends, extracting the inner `selected` substring, then rebuilding
   block 5 as `<var>.$(<var>.$$+"\""+selected+"\"")()`.
4. `eval(blocks.join(';'))` with the **host `eval`** → the decoded source string.

Returns `null` (with a logged reason) on any shape mismatch — wrong block count, missing
`~[]`, or unfindable payload bounds. No sandbox and no `eval`-packer unwrap; the whole
decode *is* the single host `eval`.
