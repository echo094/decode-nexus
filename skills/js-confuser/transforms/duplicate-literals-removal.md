# DuplicateLiteralsRemoval

Source: `transforms/extraction/duplicateLiteralsRemoval.ts`

Any literal (string/number/boolean/null/`undefined`) appearing ≥2 times gets hoisted into
`const {ph}_dlrArray = [...]`, with all occurrences replaced by `{ph}_dlrArray[i]`.

## Reversal

Resolve the array's static contents, inline at each indexed reference.
