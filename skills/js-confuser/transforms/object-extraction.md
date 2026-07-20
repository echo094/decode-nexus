# ObjectExtraction

Source: `transforms/extraction/objectExtraction.ts`

`var obj = { a: 1, b: 2 }` (never reassigned, no `this`-referencing methods, no dynamic
property access) gets split into independent `{ph}_obj_a = 1; {ph}_obj_b = 2;`
declarations; all `obj.a`/`obj["a"]` references become the flat identifier.

## Reversal

Mostly cosmetic once split — re-merging isn't necessary for readability, but if wanted:
find all `{ph}_objName_*` siblings introduced together and re-pack into an object
literal.
