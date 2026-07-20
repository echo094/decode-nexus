# GlobalConcealing

Source: `transforms/identifier/globalConcealing.ts`

Global identifier references (`console`, `Math`, etc.) become `{ph}_getGlobal(mappingKey)`
calls; `getGlobal` is a `switch(mapping){ case "key": return globalVar["realName"] }` keyed
by **randomly-generated string names** (`NameGen`), padded with 20-40 fake unused cases.
`globalVar` itself comes from a `getGlobalTemplate` sniff across
`globalThis`/`global`/`window`/`Function("return this")()`.

## Reversal

Parse the switch, build key→realName map, inline call sites.
