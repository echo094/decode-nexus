# jsconfuser-vm.js

Pipeline stage: none; the entry, which runs `prepare-source` and the standalone decode ([map](../pipelines/jsconfuser-vm.md)).

The `-t jsconfuser-vm` target: the entry to the VM decoder for output of the
[js-confuser-vm](../../js-confuser-vm/js-confuser-vm.md) encoder. Readers need the
[pipeline map](../pipelines/jsconfuser-vm.md); this doc owns only the entry's record and the
CLI's handling of it.

## 1. Target

Given the encoder's output, return the compiled program as fresh JavaScript together with the
decode's result; given anything the decoder refuses, return the input string unchanged together
with the diagnostic. The caller always gets one frozen record and never a partial program
([F2](../../encoder-decoder-method.md#f2-resolve-completely-or-not-at-all)).

The entry differs from every other decode-js plugin, which returns a string or `null`: its
record carries the result or the diagnostic, so the CLI writes a JSON sidecar beside the output.
The other plugins and their contract are untouched.

Nothing here executes the input, the interpreter or the recovered program.

## 2. Algorithm

```text
decodeJsconfuserVm(source):
    prepared  = normalizeVmInput(source)          prepare-source
    diagnosis = diagnoseStandalone(prepared)      the standalone decode, called once
    if diagnosis.ok:  record(success, output = diagnosis.result.output, result = diagnosis.result)
    else:             record(declined, output = source, diagnostic = diagnosis.diagnostic)
```

1. [`normalize-source`](../vm/jsconfuser-vm/source/normalize-source.md) parses the source as a
   script and restores the spellings an outer layer or a minifier changes (computed keys, simple
   control bodies). It prints a new string only if it changed something; source that does not
   parse passes on as given. The original is kept for the record.
2. The [standalone decode](../vm/jsconfuser-vm/standalone-decode.md) runs once on the prepared
   string. It returns a frozen record `{ ok, result, diagnostic }` and never throws for an input
   it refuses.
3. The entry builds its record from that one. On a decline `output` is the original source, not
   the prepared string, so a declined input is byte-identical to what was given.

The entry adds no recognition and no check of its own: every decision belongs to the modules and
transforms behind the standalone decode.

## 3. Implementation

### The adapter record

`decodeJsconfuserVm(source)` (also the module's default export) returns:

```js
{
  schemaVersion: 'jsconfuser-vm-adapter.v1',
  ok,          // true on success
  status,      // 'success' | 'declined'
  input,       // the source as given
  output,      // success: the emitted JavaScript (result.output); decline: the source as given
  result,      // success: the standalone result (jsconfuser-vm-standalone.v3); decline: null
  diagnostic,  // decline: the standalone diagnostic { code, message, ... }; success: null
}
```

The record is frozen; `result` and `diagnostic` arrive deep-frozen from the standalone decode,
which owns their [shape and codes](../vm/jsconfuser-vm/standalone-decode.md#3-implementation).
The entry has no `try` and needs none for an input. The standalone decode turns every exception
of its own run into a diagnostic (`standalone-emission-error` when it is no refusal), and the
preparation catches its parse's `SyntaxError`: source that is not a script reaches the standalone
decode as given and is declined there (`container-declined`). Only an internal error of the
preparation's rewrite or printing would reach the caller, which the CLI reports as
"Cannot decode input".

### The CLI

`src/main.js` registers the entry as `-t jsconfuser-vm` and treats it, with
[`jsconfuser-vm-sequential`](jsconfuser-vm-sequential.md), as result-aware:

```text
unknown -t                                  -> error, exit 1
--result given for any other target         -> error, exit 1 (before the input is read)
read the input (UTF-8)                      -> on failure: error, exit 1
record = plugin(source)                     -> on a thrown error: "Cannot decode input", exit 1
resultPath = --result, or <output>.result.json
path.resolve(resultPath) == path.resolve(output)  -> error, exit 1, nothing written
print "Status: <status>"; on a decline also "Diagnostic: <code>: <message>" (stderr)
write output  <- record.output              -> on failure: error, exit 1, no sidecar
write sidecar <- JSON.stringify(record, null, 2) + "\n"   -> on failure: error, exit 1
```

- A decline is a successful run: both files are written and the exit code is 0. The output file
  then holds the input.
- The path comparison is lexical (`path.resolve`), so a symlink or hard link to the output is not
  detected.
- The two writes are not a transaction: a sidecar failure leaves the output file written.
- The sidecar is the whole adapter record; every field of it is plain JSON.

## 4. Input Shapes

| Shape | Producer | Treatment |
|---|---|---|
| Encoder output as written | the encoder | prepared, decoded |
| Encoder output under a js-confuser outer layer, after the outer decode | the [sequential entry](jsconfuser-vm-sequential.md), which calls this entry | the same; the preparation restores the forms the outer decode leaves ([`normalize-source`](../vm/jsconfuser-vm/source/normalize-source.md)) |
| Standalone record `{ ok, result, diagnostic }` | [standalone decode](../vm/jsconfuser-vm/standalone-decode.md) | copied into the adapter record; never re-derived |

No shared visitor runs before or after this entry, and the entry reads no option.

## 5. Known Gaps

- What the decoder recovers and refuses is each module's and transform's: the map's
  [Reversibility](../pipelines/jsconfuser-vm.md#reversibility-by-encoder-step) table lists it by
  encoder step, and each doc's Known Gaps holds the detail.
- The output is a decompilation: register names, and the scaffolding the
  [backend](../vm/switch/vm-switch-emit.md) keeps where a native form is not proved, stay.
- The CLI's two writes are not atomic, and its path check is lexical (section 3).

## 6. Source

- [jsconfuser-vm.js](../../../decoder/decode-js/src/plugin/jsconfuser-vm.js): `decodeJsconfuserVm`.
- [main.js](../../../decoder/decode-js/src/main.js): the registry row and the result-aware branch.

## 7. Fixtures

The tests are in
[public-entry-points/](../../../decoder/decode-js/test/vm/jsconfuser-vm/public-entry-points/);
their encoded inputs are input cells ([tests.md](../tests.md)).

| Scenario | Expected result | Committed fixture |
|---|---|---|
| Encoder output | `status: 'success'`; `output` equals `result.output` and differs from the input; one standalone call, made with the prepared source; the record is frozen; the output parses, holds no interpreter residue and its derived state matches a fresh parse | plugin.test.js |
| Ordinary JavaScript | `status: 'declined'`, `container-declined`; `output` is the input, byte for byte; `result` is `null` | plugin.test.js |
| Encoder output truncated, so it no longer parses | The same decline: the preparation passes it on and the standalone decode refuses it | plugin.test.js |
| A comment before the container | Same output as without it | plugin.test.js |
| The interpreter's `debugger` statement deleted from the input, over the baseline, class-obfuscated, minified and randomized-opcode runtimes | Same output as with it; the output has no `debugger`, no `void` filler statement and no dispatch `switch` | debugger-policy.test.js |
| A compiled `debugger` between two effects | No statement is left for it and the effects keep their order when the output runs | debugger-policy.test.js |
| CLI, success | Output file and sidecar written; the sidecar's `result` equals a direct `diagnoseStandalone` on the same input; exit 0 | cli.test.js, integration.test.js |
| CLI, a decoded branch program | The output holds an `if` and computes its source's oracle | integration.test.js |
| CLI, decline (ordinary JavaScript; encoder output with its payload renamed) | Output file equals the input, sidecar holds the diagnostic, `Status: declined` printed; exit 0; default and explicit sidecar paths | cli.test.js |
| CLI, sidecar path equal to the output path after resolution | Exit 1; an existing output file is untouched | cli.test.js |
| CLI, unknown target, unreadable input, unwritable output | Exit 1; no file written | cli.test.js |
| CLI, another target | Its output as before, no sidecar | cli.test.js |
| An internal error thrown by the plugin | "Cannot decode input", exit 1, nothing written | |
| CLI, a sidecar write failure | Exit 1; the output file stays written | |
| CLI, `--result` on another target | Exit 1 before the input is read | |
