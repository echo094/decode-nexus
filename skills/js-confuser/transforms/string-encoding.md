# StringEncoding

Source: `transforms/string/stringEncoding.ts`

Cosmetic: string literals become `\x`/`\u` escaped identifier-looking tokens. No real
obfuscation — Babel's generator/parser round-trips this for free, nothing to build.
