# StringConcealing

Source: `transforms/string/stringConcealing.ts`

All string literals ≥3 chars in a block get pulled into one giant decoy-padded string
constant per scope (`{ph}_array`), replaced with `{ph}_STR_N(start, length)` calls into a
per-block decode function. Default codec is a shuffled base91 alphabet
(`string/encoding.ts::createDefaultStringEncoding`); custom encodings are pluggable via
`options.customStringEncodings`.

## Reversal

Locate the decode function template, `eval`/interpret it (base91 decode is short and
side-effect-free), then constant-fold every call site using the literal `start`/`length`
args.
