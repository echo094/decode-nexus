# bufferToStringTemplate.ts

Provides `BufferToStringTemplate`: decodes a byte array into a UTF-8 string, trying (in
order) `TextDecoder`, then `Buffer.from(buffer).toString("utf-8")`, then falling back to
a hand-rolled `utf8ArrayToStr` decoder if neither global is available. The global lookups
themselves go through [`getGlobalTemplate.ts`](../transforms/global-concealing.md)'s
sniff (`__globalObject = {getGlobalFnName}()`).

Used by [StringConcealing](../transforms/string-concealing.md)'s base91 decoder — the
decoded byte array from the base91 alphabet still needs converting to a real string,
which is what this template's generated function does.
