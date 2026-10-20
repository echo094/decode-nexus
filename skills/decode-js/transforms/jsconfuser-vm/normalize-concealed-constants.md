# Normalize concealed VM constants

## 1. Target

Restore referenced constant-pool values and turn their nonzero key operands into ordinary zero-key
references. Passing the input through would leave encrypted strings/XORed integers and make
Packet C refuse those references. Success publishes a copied container and current Packet B;
C and later analyses are built from those values, not retained from before the pool rewrite.

The normalizer reads only the payload: owned [Packet A](extract-container.md) pool values and
[canonical B](read-wordcode.md) key operands. The cipher is the encoder's fixed algorithm, so the
interpreter's constant reader is not read or proved. It does not execute target code, infer an
unknown cipher or restore unreferenced entries. Readers need JavaScript bitwise coercion, UTF-16
units and the encoder's [keyed constants](../../../js-confuser-vm/transforms/keyed-constants.md).

## 2. Algorithm

Collect every constant reference before decryption. One pool entry must use one key, including
zero, at all its references; otherwise replacing that entry globally could change a different
use. Require at least one nonzero key.

Clone A. For each referenced keyed integer, XOR the stored value with its key. For each keyed
string, read canonical base64 as little-endian u16 pairs and regenerate the position-dependent
mask from that entry's key. Advance the mask state before each unit; XOR reverses the emitted
operation. Replace each keyed pool entry once and clear each corresponding key word. Widths,
instruction PCs, register windows and pool indexes stay fixed. Re-read B on the clone and
publish only on success.

```mermaid
flowchart LR
  B[Owned B constant references] --> K[One key per pool index]
  K --> D[Restore copied pool and zero copied key words]
  D --> R[Current B / later C]
```

### Synthetic exact-value example

Main entry 0 with two registers and this private A/B stream:

```text
PC 0: LOAD_CONST r0, index 0, key 1           [0,0,0,1]
PC 4: LOAD_CONST r1, index 1, key 2147483649  [0,1,1,2147483649]
PC 8: RETURN r0                            [45,0]
pool = ["QIg=",2147483640,"%%%%"]
```

Base64 QIg= contains bytes [64,136], unit 34880. From seed 1, the first state is
`(1+0x9e3779b9)|0 = -1640531526`; `(state^(state>>>13))&65535 = 34817`.
`34880^34817 = 65`, giving "A". Integer `2147483640^2147483649 = -7` uses signed int32 XOR.
Output words are `[0,0,0,0,0,1,1,0,45,0]` and pool `["A",-7,"%%%%"]`.
The unreferenced malformed-looking string remains unchanged: no key proves its meaning. PCs
0/4/8 and wordCount 10 remain identical; the changed values/keys fail a passthrough oracle.

## 3. Implementation

### Components and owned inputs

| Component | Consumes -> produces | Consumer invariant |
|---|---|---|
| Pair collector | B semantic constant-ref operands -> keys and key-word PCs | Every reference to an index has the same key. |
| Value recovery (`restoreConcealedValue`) | Referenced pool value/key -> plaintext | Exact int32 or UTF-16 equations; no host target execution. |
| Copy/re-reader | A plus recovery plan -> copied A/current B | Same widths/PCs; changed pool and key words authoritative. |

B owns operand shape and u32 key/index words. Iterate instructions and their semantic `operands`;
for each constant-ref record `{index,concealKey}`, record keyPc=instruction.pc+2 for STORE_GLOBAL,
otherwise pc+3. Those offsets follow B's four constant-bearing rows, not a search for matching
numbers elsewhere. Include zero-key references in the index->key Map. Differing keys decline
concealed-key. No nonzero pair declines no-concealed-constants; ordinary standalone diagnosis
bypasses the adapter in that case.

### Value equations and publication

Structured-clone A. For each collected index require index<pool.length, otherwise
concealed-index. Leave zero-key values untouched. For a nonzero key:

```text
explanatory recovery procedure:
if typeof value == number and Number.isInteger(value): plain = value ^ key
else if typeof value == string:
  require canonical base64 and exact base64 re-encoding
  require even byte length
  state = key; plain = ""
  for byteIndex = 0,2,...:
    state = (state + 0x9e3779b9) | 0
    mask = (state ^ (state >>> 13)) & 0xffff
    stored = bytes[byteIndex] | (bytes[byteIndex+1] << 8)
    append String.fromCharCode(stored ^ mask)
else: decline concealed-value
```

The base64 grammar is `^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$`.
Buffer decode/re-encode must reproduce the input exactly. Empty strings pass; surrogate/NUL units
are retained without Unicode normalization or UTF-8 conversion. Bad grammar, noncanonical padding
bits or odd byte length decline concealed-string. Numeric XOR returns int32, including the signed
Weyl increment -1640531527. The [producer's numeric preservation domain](../../../js-confuser-vm/transforms/keyed-constants.md#interning-and-storage-decisions)
does not promise recovery of original integer-valued Numbers outside int32.

Replace each referenced nonzero pool entry, then zero each such keyPc. Re-read B once; failure
becomes concealed-wordcode with the reader's message. The result schema is
jsconfuser-vm-concealed-constants-normalization.v1 with container, wordcode and
concealedPoolEntries (distinct collected nonzero keys by index). It returns no C/D/E, map or
source replacement. The envelope/container are not deeply frozen here; B is an owned frozen record.

`diagnoseNormalizeConcealedConstants(source, container, wordcode)` returns `{ok,result,diagnostic}`;
`source` is accepted for its callers and not read. Typed failures retain the codes above;
unexpected recovery errors become concealed-normalization-error. It publishes no partial recovery
and mutates no A/B. The atomic unit is all referenced keyed entries; independent plaintext and
unused entries carry through unchanged. The runtime's reader stays in source because standalone
emission later replaces the entire VM.

### Testing and acceptance

| Scenario | Oracle / acceptance | Evidence |
|---|---|---|
| V1 values/keys | Exact example pool/zero-key words/current B; unchanged predecessors | Owner scaffold above; retained arithmetic/closure/exception/array tests. |
| V2 pair/value refusal | Malformed string/key conflict reaches concealed-string/concealed-key with no result | Copied-A controls in the normalizer test. |
| V3 no candidate/unused pool | No nonzero pair declines directly; standalone bypasses; unused values stay intact | Owner unused-entry example. |
| V4 downstream state | New B then C agree with changed keys/pool; public output loses VM residue and fresh AST state agrees | Retained combination tests. |

## 4. Input Shapes

[Earlier added-opcode/PATCH producers](read-wordcode.md#4-input-shapes) own expansion/decryption,
compaction, operand layouts and map handoffs. This pass consumes their current canonical B,
not synthetic handler records. If keys remain, [diagnosis](standalone-diagnosis.md#canonical-frontend-retries)
requires this inverse before C, adopts its A/B-only result and discards previous C/D/E.

[Dispatcher](normalize-dispatcher-wordcode.md), [CFF](normalize-cff-wordcode.md) and
[string recovery](normalize-string-concealing.md) need restored constants first. The string trace
admits the signed Weyl increment only at its documented bit-pattern equivalence. Anti's private
flow proof restores values earlier under its own route with `restoreConcealedValue`. Runtime
representations (class, minify, table, encoded payload) do not reach this pass: Packet A
supplies the same payload under each. The [pinned keyed-constant producer](../../../js-confuser-vm/transforms/keyed-constants.md)
explains mandatory pairs before augmentation and late pool resolution.

## 5. Known Gaps

Unreferenced entries have no key and stay emitted. Empty/Unicode arithmetic follows the formula,
but the retained actual-program evidence does not cover every value/host case. Wider option
combinations need their own retained inputs; [historical provenance](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/qualification-provenance.md)
limits exact regeneration claims.

## Source

The decoder is [normalize-concealed-constants.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/normalize-concealed-constants.js),
wired by [diagnose-standalone.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/diagnose-standalone.js)
and the [anti normalizer](normalize-anti-wordcode.md) under the dependencies described in item 4.

The pinned encoder's [constant-pair pass](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/transforms/bytecode/concealConstants.ts)
adds a key operand. Its [constant resolver](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/transforms/bytecode/resolveConstants.ts)
encrypts pool values, and the [runtime reader](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/runtime.ts)
reverses them. The [compiler pass list](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/compiler.ts)
establishes the position described in item 4.

## Fixtures

| Committed fixture or test control | Claim pinned |
|---|---|
| [concealed-constants-arithmetic](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/concealed-constants-arithmetic/encoded.js) and its [qualification record](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/concealed-constants-arithmetic/qualification.json) | Negative integer pool literals and string values normalize through Packet C. |
| [concealed-constants-closures](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/concealed-constants-closures/encoded.js) and its [qualification record](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/concealed-constants-closures/qualification.json) | Constant decoding preserves closure behavior. |
| [concealed-constants-exceptions](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/concealed-constants-exceptions/encoded.js) and its [qualification record](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/concealed-constants-exceptions/qualification.json) | Reused keys and exception control survive normalization. |
| [concealed-constants-repeatedArrays](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/concealed-constants-repeatedArrays/encoded.js) and its [qualification record](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/concealed-constants-repeatedArrays/qualification.json) | Repeated array construction preserves observable behavior. |
| [string-concealing-concealed-constants](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/string-concealing-concealed-constants/encoded.js) and its [qualification record](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/string-concealing-concealed-constants/qualification.json) | Keyed string bank and signed Weyl increment feed the string normalizer. |
| [string-concealing-cff-dispatcher-concealed-constants](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/string-concealing-cff-dispatcher-concealed-constants/encoded.js) and its [qualification record](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/string-concealing-cff-dispatcher-concealed-constants/qualification.json) | Keyed constants transfer through the four-pass stack and its finalizer. |
| [concealed-constants-anti-instrumentation](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/concealed-constants-anti-instrumentation/encoded.js) and its [qualification record](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/concealed-constants-anti-instrumentation/qualification.json) | Keyed constants survive anti instruction normalization. |
| [string-cff-dispatcher-concealed-constants-anti-instrumentation-exceptions](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/string-cff-dispatcher-concealed-constants-anti-instrumentation-exceptions/encoded.js) and its [qualification record](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/string-cff-dispatcher-concealed-constants-anti-instrumentation-exceptions/qualification.json) | Keyed constants survive the full qualified bytecode stack. |
| [string-cff-dispatcher-concealed-constants-anti-specialized-exceptions](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/string-cff-dispatcher-concealed-constants-anti-specialized-exceptions/encoded.js) and its [qualification record](../../../../decoder/decode-js/test/vm/jsconfuser-vm/fixtures/string-cff-dispatcher-concealed-constants-anti-specialized-exceptions/qualification.json) | Keyed constants survive specialized expansion and anti compaction. |
| [normalize-concealed-constants.test.js](../../../../decoder/decode-js/test/vm/jsconfuser-vm/normalize-concealed-constants.test.js) | Direct Packet C refusal before normalization, immutable source container, source/encoded/decoded agreement, no VM residue, derived state, malformed base64 and inconsistent-key decline. |
| [runtime-binding-identities.test.js](../../../../decoder/decode-js/test/vm/jsconfuser-vm/runtime-binding-identities.test.js) | concealed-constants-exceptions decodes to source behaviour after every lexical binding is renamed. |
