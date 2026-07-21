# Template Engine (`templates/template.ts`)

Upstream docs: [`docs/Template.md`](../../encoder/js-confuser/docs/Template.md)

The base class every `templates/*.ts` file — and most transforms directly, via ad-hoc
`new Template(...)` calls — builds AST fragments from. Not a pipeline stage itself; the
scaffolding underneath every file in [templates/](templates/), referenced throughout
this reference as `Template.compile()`/`.single()`/`.expression()`.

**Constructing:** `new Template(...templates)` takes one or more template-string
variants (a random one is chosen per `compile()` call, letting a single logical
template render as visibly different code each time it's instantiated — e.g.
[DeadCode](transforms/dead-code.md)'s decoy snippets). `{name}` placeholders inside the
string are auto-detected as `requiredVariables` by scanning the first variant.
`.setDefaultVariables(vars)` supplies fallback values so not every `compile()` call
needs to pass every variable; `.addSymbols(...)` tags every top-level statement the
template produces with the given [`NodeSymbol`](constants.md) flags (e.g.
[RGF](transforms/rgf.md) tags its inserted `eval` wrapper `UNSAFE`).

**Filling in variables (`compile(variables)`):**
1. `interpolateTemplate` — string-substitutes every `{name}` placeholder. A `string`/
   `number` variable is inlined directly into the source text; anything else (an AST
   node, a `Template` instance, or a `() => Node` thunk) is instead substituted with a
   unique placeholder identifier (`__t_<random>_<name>`) so the template string still
   parses as valid JS.
2. The result is parsed with `@babel/parser` into a `File`.
3. `interpolateAST` — traverses the parsed AST for those placeholder identifiers and
   `path.replaceWith()`s each one with the real value: a literal node as-is, a thunk's
   return value (called lazily, so side effects only happen if the variable is actually
   used), or another `Template`'s own `.compile()` output (templates can nest). Reusing
   the same non-string variable twice throws (`"Duplicate node inserted"`) unless it was
   provided as a thunk or nested `Template` — Babel nodes aren't safely shareable
   between two AST locations (see [`deepClone`](utils/node.md) for the usual workaround
   when a caller *does* need the same value twice).

**Reading the result back out:** `.compile()` returns the full statement list;
`.single()` asserts exactly one non-empty statement and returns it; `.expression()`
further asserts that statement is an `ExpressionStatement` and unwraps its expression —
the three call shapes seen throughout every transform doc in this reference.
