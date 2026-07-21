# RGF (Runtime-Generated Functions)

Source: `transforms/rgf.ts`

Upstream docs: [`docs/RGF.md`](../../../encoder/js-confuser/docs/RGF.md)

Eligible functions (no outer-scope references, not async/generator) get their body
compiled as a **separately-obfuscated** sub-program, serialized to a string, and executed
via `{ph}_rgf_eval(code)` → `eval(code)` (gated by a tamper-protection integrity check).
The result is stored in an `{ph}_rgf` array and the original function becomes `return
{ph}_rgf[i].apply(this, [{ph}_rgf, arguments])`. Note the sub-program is **recursively
obfuscated** with (most of) the same pipeline — a nested instance of every other
transform in this reference.

## Reversal

Extract the string literal passed to the eval-wrapper, recursively run the full
js-confuser deobfuscation pipeline on it, then inline the result back as a normal
function body.
