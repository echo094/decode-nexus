# Pack

Source: `transforms/pack.ts`

Final-AST wrapper (always root-level, skips RGF sub-obfuscators): every free/global
identifier reference becomes `{ph}[propName]` against one shared object, and the entire
program becomes `Function(objName, sourceCodeString)(objectLiteral)` — i.e. the real code
ships as a **string literal** passed through the `Function` constructor, only reachable
after this unwrap.

## Reversal

Parse the trailing `Function(...)(...)` call, pull out the `objectName`, `outputCode`
string, and the property-mapping object literal (getters/setters), re-parse `outputCode`
as the real program, substitute `objName[prop]` refs with the real identifiers using the
map, splice back in any preserved `import`s.
