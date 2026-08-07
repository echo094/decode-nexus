# StringConcealing

Source: [`transforms/string/stringConcealing.ts`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/string/stringConcealing.ts#L122-L268) — `Order.StringConcealing = 17`.

## 1. Target

Hide every string literal of any real length behind an opaque decode call reading from
one shared, decoy-padded blob, using a pluggable per-block encoding algorithm — so even
the decode mechanism itself isn't fixed or predictable across blocks, not just the data.

## 2. Algorithm

All string literals ≥3 chars get pulled into **one** decoy-padded string constant shared
by the whole program (`{ph}_array`), and replaced with `{ph}_STR_N(start, length)` calls.
Each block that ends up owning strings (the Program itself always does; nested blocks get
their own with ~probability `chance(75 - blocks.length)`) gets its **own** retrieval
function pair:

```js
function {ph}_STR_N(start, length) {
  return {ph}_STR_N_decode({ph}_array["slice"](start, start + length));
}
```

`{ph}_STR_N_decode` is one *encoding*, picked randomly per block from
`options.customStringEncodings` (default: a single shuffled-alphabet base91 codec).
Multiple blocks can share the same encoding *implementation* but never the same compiled
function — each gets its own pair with its own shuffled table.

## 3. Implementation

The base91 decoder's last line calls a shared, program-wide `{ph}_bufferToString(bytes)`
helper ([`templates/bufferToStringTemplate.ts`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/templates/bufferToStringTemplate.ts#L1-L57)),
prepended once regardless of block count — itself built on a
[`getGlobalTemplate.ts`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/templates/getGlobalTemplate.ts#L39-L76)
sniff for `globalThis`/`global`/`window`/`Function("return this")()`, used to locate
`TextDecoder`/`Buffer` if present (falling back to a hand-rolled `utf8ArrayToStr`).

## 4. Downstream Effects

- **`RenameVariables` (Order 30)** renames every declaration independently, and can
  coincidentally collide two unrelated declarations onto the identical name — a block's
  own decode-function local and its enclosing function, or a Program-level alias in the
  shared `bufferToString` chain and a deeply-nested wrapper. Legitimate and unambiguous in
  the real program (disambiguated by actual scope nesting), but a hazard for any consumer
  that flattens multiple declarations' source into one shared scope.

- **`ControlFlowFlattening` (Order 24)** rewrites the callee of a direct call into a member
  expression through its own state/scope objects, then wraps the result as `(1, <member>)(…)`
  so the call still runs with `this === undefined` instead of acquiring that object as a
  receiver
  ([`transforms/controlFlowFlattening.ts`](https://github.com/MichaelXF/js-confuser/blob/31c5a47a79f97e4b4c2d4b2a8552c11a8b548fb0/src/transforms/controlFlowFlattening.ts#L1305-L1311)).
  A wrapper emitted here as `wrapperName(start, length)` therefore reaches the finished
  output with its callee spelled as a sequence expression at the call sites
  ControlFlowFlattening reached, and plainly at the ones it did not — one wrapper, two
  spellings, decided per call site. This is the only place in the pipeline that emits a
  literal-`1`-prefixed sequence expression.

## 5. Known Quirks

None currently documented.
