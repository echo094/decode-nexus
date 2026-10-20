# Reshape runtime classes, constants and boot dependencies

## 1. Target

Hide plain runtime maps/member names and fixed parameter/declaration positions while preserving
the connected VM data, methods and shared cells. With `classObfuscation` truthy, the pass consumes
the completed runtime AST, inlines eligible constants, injects/permutes constructor and named
method parameters, renames internal class/record members, and shuffles pre-boot statements.

Read the [AST dependency contract](../js-confuser-vm.md#runtime-ast-dependency-contract),
[container](../container-wordcode.md), [instruction semantics](../instruction-set.md),
[layout](runtime-layout.md) and [optional table representation](handler-table.md). This page
specifies the pinned transformation of that closed runtime file. It does not provide generic
JavaScript alias, purity, points-to or arbitrary declaration-dependency analysis. Source-derived
selection rules and absent checks are distinguished from demonstrated behavior below.

## 2. Algorithm

First rebuild Babel's scope information so references installed by prior raw AST edits are visible.
Inline stable scalar values and safe literal-object property reads. Remove a declaration only
after its complete reference set is replaced; an escaped/mutated/unknown object read keeps the
entire object unchanged. Optional missing noise properties become undefined, allowing later
optimization to eliminate their guarded writes.

Discover constructor-shaped functions and their prototype methods. Before renaming members,
find calls using their original names. Add fake parameters and corresponding dummy arguments,
then apply the same positional permutation to parameters and registered calls. This keeps the
real parameter-to-value relationships despite changed positions. Fake parameters are stashed
into fresh-looking this fields, so they are used but never consumed by the original runtime logic.

Build one field/method rename map for all classes and plain record literals. Apply that map to
member reads and record keys together, keeping runtime descriptor/upvalue/handler record writes
coupled to reads. Finally shuffle declaration-like statements independently of prototype method
assignments, keeping declarations before assignments and the boot suffix last. Shared lexical
helpers/maps remain in the same file environment; this pass changes spellings and positions,
not closure-cell ownership.

### Worked example

This **synthetic positional example** chooses one fake parameter, its insertion point, a
permutation and rename outcomes. It is not an encoder-produced specimen:

```text
input:
  var HEADER_SIZE = 8;
  function VM(words, pool, globals) {
    this.bytecode = words; this.constants = pool; this.globals = globals;
  }
  /* @BOOT */ var vm = new VM([45,0], ["ok"], host);

after inserting fake_1 at index 1:
  params = [words, fake_1, pool, globals]
  args   = [[45,0], "x", ["ok"], host]

permutation = [2,0,3,1]:
  params = [pool, words, globals, fake_1]
  args   = [["ok"], [45,0], host, "x"]
```

Each new parameter position receives the same paired value as before: words receives `[45,0]`,
pool receives `["ok"]`, globals receives host. A body stash `this._fake1=fake_1` reads only the
dummy. A chosen rename map `bytecode->a, constants->b, globals->c, _fake1->d` must rewrite all
corresponding member accesses and the stash. HEADER_SIZE's safe references become literal 8
and its declaration disappears. The two arrays remain arrays, so their contents are not scalar
inlining candidates. No fixed VM-constructor argument position can be assumed after this pass.

The example uses effect-free arguments; moving an arbitrary call expression could change its
evaluation order. It omits named methods, skipped candidates, shared captures, noise, statement
sampling and final minification. The exact choices are illustrative; the recipe below defines
the actual allowed ranges and decisions.

## 3. Implementation

### Components and order

| Component | Input -> output | Consequential dependency |
|---|---|---|
| Constant inliner | Fresh binding graph and top-level declarations -> literal uses/removals | Earlier added/table references must be included before deciding removal. |
| Class/record model | Constructor/function/prototype shapes -> fields, methods, record keys | Named methods drive call matching; alias table handlers remain independent functions. |
| Parameter rewrite | Model, calls and random choices -> fake stashes and paired permutation | Uses original member names; runs before renaming. |
| Member rewrite | Updated model/records -> global spelling bijection | New fake fields included; keys and reads use same map. |
| Statement partition | Pre-boot body/aliases -> shuffled A then B then unchanged boot | Alias/constructor availability precedes prototype installation. |

### Constant inlining

Crawl Program scope once on entry, then iterate a copy of top-level body statements. A candidate
is a VariableDeclaration with exactly one declarator, Identifier id and initializer. It is not
restricted to `var` by the AST test. Resolve the Program binding by that id; require its binding
path node to be exactly this declarator, `binding.constant` true and no constantViolations.
Scalar initializers admitted are NumericLiteral, StringLiteral, BooleanLiteral and NullLiteral.
Deep-clone the initializer into every binding.referencePath, then splice its entire declaration
statement out of Program.body. Arrays, functions and `undefined` Identifier initializers do not
qualify as scalars.

An ObjectExpression qualifies only if every property is a noncomputed, nonmethod ObjectProperty
with Identifier or StringLiteral key and one of those four scalar literal values; spreads,
methods, numeric keys or nonliteral values abort the candidate. Empty objects pass this shape
test; duplicate keys overwrite earlier entries in the temporary property map.

Validate **every** binding reference before applying any replacement. The reference must be the
object of its immediate parent MemberExpression. Its key must be a noncomputed Identifier or
computed StringLiteral. Reject other/bare uses, computed expressions, or a missing key unless
that key starts with `NOISE_`. Also reject a member used as the left side of assignment, the
argument of update, or the argument of `delete`. If all pass, collect/deep-clone values into
those member paths and remove the declaration. Missing NOISE_ values become UnaryExpression
`void 0`; this exception is based on the property prefix, not a special SLOTS binding check.
A failed object check leaves all its references and declaration untouched.

Typical outcomes are literal OP/SENTINELS/SLOTS/header/root values, and absent-noise guards
`typeof void 0 === "number"`. In encoded mode BYTECODE's base64 string also qualifies, moving
into its `decodeBytecode(...)` use; in raw mode its ArrayExpression stays. CONSTANTS likewise
stays an array. This pass does not evaluate false branches or remove dead noise blocks itself.

### Class model and matched calls

Discover only top-level named FunctionDeclarations containing at least one assignment
`this.<Identifier> = ...` with noncomputed member access and operator `=`. Field harvesting
traverses their body with no scope analysis and does not exclude nested functions. Discover
methods only from top-level `Name.prototype.<Identifier> = FunctionExpression`, with both
member accesses noncomputed and operator `=`. Name must identify a discovered class. Methods
are stored by name (later assignments to the same name replace the earlier model entry).
Computed numeric table handlers through VMPrototype are not discovered methods.

A reorder candidate has only Identifier parameters (zero/one parameter is allowed). All such
constructors qualify. A method qualifies only if exactly one discovered class defines that
method name. Its metadata holds original name, constructor/method flag, function, original
parameter count, matched call list, unsafe flag and class-field set.

Register `new Identifier(...)` by constructor **name**; register CallExpressions whose callee
is a noncomputed MemberExpression with a matching Identifier property by method **name**,
regardless of receiver. There is no binding or receiver-type resolution and no escaped-method
call census. Any matched call with SpreadElement/ArgumentPlaceholder or an argument count other
than zero or the original parameter count marks the entire candidate unsafe. Unsafe candidates
receive no fake parameters or permutation. Register full-arity calls, including zero args when
the original parameter count is zero. For a positive-arity candidate, zero-argument calls are
allowed but not registered: they stay zero-argument after rewriting.

### Fake parameters and coupled permutation

The [random primitive](runtime-layout.md#components-and-exact-allocation) is shared. For each safe
candidate, draw fakeCount in 1..4. For each fake create a pass-global successive `fake_<n>` id;
draw insertion point in `0..currentParams.length`, splice it into parameters and splice a fresh
dummy expression at that same index in each registered call; increment the parameter count.
No existing-local collision check is made for these generated parameter identifiers.

Each dummy draws a kind uniformly from 0..5: `{}`, `[]`, integer 0..99, StringLiteral chosen
from `x,y,z,q,k`, Identifier `undefined`, or NullLiteral respectively. They have no intrinsic
side effects in the closed runtime environment; this is not a generic shadowed-undefined proof.

Shuffle fake names, partition them into groups of `min(int(1,2),remaining)` and stash each group:
for one name use its Identifier; for two, chance(50) selects ArrayExpression of the names,
otherwise combine them using a randomly chosen `||` or `&&`. Assign the expression to
`this._fake<n>`, with a separate pass-global field counter; add that field to the class model.
Insert each stash at `int(0,currentBody.length)` in the function body. It can land after a return
and be unreachable. The fields are never read by original logic; stashes are still real writes,
not dead no-op expressions. No existing-field collision scan occurs before assigning the prefix.

Draw a permutation p by shuffling `[0,...,newParamCount-1]`. Using snapshots after all insertions:

```text
newParams[j] = oldParams[p[j]]
newArgs_at_each_registered_call[j] = oldArgs_at_that_call[p[j]]
```

This establishes parameter/value pairing, but physically reorders argument expressions. The pass
has no side-effect/purity or `arguments`-use guard. Its pinned runtime call sites are the intended
input; these rules alone do not prove preservation for arbitrary call graphs or argument effects.
Calls left at zero args bind every real parameter to undefined as before; fake stashes may also
receive undefined. Methods remain ordinary functions called with the same receiver expression.

### Global member spelling

Skip **all property renaming**, while allowing other class stages, when the File contains any
ObjectPattern; SpreadElement inside ObjectExpression/ObjectPattern; or CallExpression whose
callee has Identifier object `Object` and Identifier property keys/values/entries/assign, or
Identifier object `JSON` and property stringify. This syntactic unsafe test has no binding
resolution and does not require callee.computed=false. It is not comprehensive alias analysis.

Candidates combine modeled fields/methods and nonempty key spellings harvested from every
nonempty plain ObjectExpression whose properties are all noncomputed, nonmethod ObjectProperties
with Identifier/StringLiteral keys (values need not be literals). An empty StringLiteral key
passes that object-shape test, but harvesting skips it through `if (key) names.add(key)`.
Exclude these exact protected names from both old candidates and generated replacements:

```text
prototype constructor length name call apply bind toString valueOf then catch finally
value get set writable enumerable configurable
```

Shuffle candidate order and assign successive distinct names from the supplied name generator.
Its alphabet is `a..z,A..Z` (52 characters); for positive index n repeatedly choose
`t=(n-1)%52`, prepend alphabet[t], then set `n=((n-t)/52)|0` until zero. The sequence starts
`a,...,z,A,...,Z,aa,...`; generator index starts at 1 and increments even on skipped names.
Skip the protected names above and this exact reserved set (duplicates in source have no effect):

```text
if in do for let new try var case else null with break catch class const super throw while
yield delete export import public return switch default finally private continue debugger
function arguments protected instanceof await async NaN undefined true false typeof this
static void of Infinity eval toString valueOf constructor __proto__ hasOwnProperty
isPrototypeOf propertyIsEnumerable toLocaleString
```

The generator does not reserve every existing noncandidate runtime property spelling. Apply the
one map globally to noncomputed Identifier members and computed StringLiteral members. Rewrite
noncomputed/nonmethod ObjectProperty keys too; Identifier keys mutate their name, StringLiteral
keys become the new Identifier. Computed/numeric/dynamic keys and other AST forms remain as-is.
This is a by-spelling transformation, not a per-instance or lexical-variable rename. The shared
map keeps plain descriptor/handler/upvalue record keys coupled with their member reads.

### Statement order, captures and derived state

Find the first top-level statement whose leading/inner/trailing comments contain `@BOOT`; if
none exists take body.length. Keep that statement and everything after it in original order.
Collect prototype aliases from all top-level VariableDeclarations: Identifier id initialized
with a noncomputed MemberExpression whose Identifier property is `prototype`; there is no
restriction on its object expression.

Partition the prefix. Group B contains ExpressionStatements with an AssignmentExpression whose
left is a MemberExpression and either its object is an Identifier alias, or its object is a
MemberExpression with Identifier property `prototype`. This classification does not require
operator `=` or test computed on that inner prototype member. Everything else goes to A.
Shuffle A and B independently; output A then B then the unchanged boot suffix. Thus constructors
(function declarations) and aliases precede table/prototype assignments. The pass does not sort
other initializer dependencies within A or method dependencies within B.

Keep CLOSURE_MAP as one shared WeakMap, the base64 helper as the same captured function, and
VM/Closure/Upvalue call relationships in the same outer environment. Fields/record keys and call
positions change together; open/closed upvalue cells, shell-captured closure/VM references and
receiver semantics remain governed by the [instruction contract](../instruction-set.md#closures-receiver-capture-and-upvalue-lifetime).
No helper/map is cloned per class/handler. Babel paths provide inliner replacements; raw removal,
parameter/property changes and body reorder mutate the private File. The pass explicitly crawls
scope before inlining but does not recrawl at completion or promise a fresh final binding cache.
The next normal publication step generates source from the AST; the compiler does not expose that
AST as a public cached-state record.

### Testing and acceptance

| Scenario | Observable result / oracle | Acceptance criterion | Retained control |
|---|---|---|---|
| C1: scalar/object inlining | Maps/root constants disappear; safe uses literal; unsafe object wholly survives | All binding references accounted for; NOISE missing -> void 0 | Class variants 2/3 and randomized test; bounded atomic inlining/refusal/binding controls; real pass controls missing |
| C2: real/fake parameter pairing | All full calls pair values with actual parameter uses; zero/default and skipped candidates follow rules | Exact coupled permutation; candidate refusal unchanged | Synthetic example and chosen-permutation pairing proof; complete class/arity/ambiguous/spread/purity/fake-collision controls missing |
| C3: shared property map | Class and record keys/reads use one bijection, protected names remain | New fake fields included; global unsafe forms skip rename only | Class variants 1/6 behavioral intent; direct record/denylist/unsafe controls missing |
| C4: installation/boot | Prototype alias defined before its assignments; boot suffix last | A before B, suffix ordered; no unsupported general topological claim | Class variants 4/5; direct missing-marker/initializer controls missing |
| C5: captures/representations/state | Same cell/map/helper and behavior across selected class/table/encoded forms | Real receiver/capture ownership retained; generation publishes only whole success | Class variants 1/3/5/6; direct lexical graph/cache/full-stack controls missing |

The retired bounded verifier, built from the documents before source consultation, actually rebuilt scalar/object constant replacement and
removal on synthetic Babel trees. C1 controls assert changed safe output, missing NOISE_ -> void 0,
shadowed binding preservation, exact refusal reasons and unchanged complete output for object
escape, member assignment/update/delete, unknown key and computed key. The proof explicitly
recrawls scope to check consumed bindings disappear and remaining bindings survive; that supplied
consumer check does not assert the source transform promises a final recrawl. C2 is only a chosen
insertion/permutation arithmetic check of paired values and changed evaluation order. It does
not reconstruct class discovery, empty-key harvesting, property renaming, fake stash selection or
statement shuffling, nor execute the actual class pass or generated runtime. The empty-key rule
is source evidence outside this frozen subset.

Variant 4 directly exercises the prototype-alias ordering defect boundary on a synthetic runtime.
It does not test arbitrary A-group initializer dependencies. Behavioral tests do not certify
complete binding, fake-field or call-site coverage; missing direct controls remain required.

## 4. Later Stages

| Later producer | Emitted shape | Effect on this contract |
|---|---|---|
| Babel generation | Literal maps/scalars, renamed members, paired calls, shuffled declarations | Comments can still name old members; textual search must distinguish comments from actual AST. |
| Comment prefix | Instruction descriptions prepended after class generation | They do not restore removed map declarations or define capture roles. |
| [Final minification](minify-runtime.md) | Whole-runtime optimization including rewritten boot/calls/helpers | Parameter positions, helper placement, fake stashes and method boundaries need not retain the unminified shape. |

## 5. Known Quirks

- Class discovery, call matching and property rewriting are syntactic/by name. No general binding,
  points-to, escaped-method or computed-call proof is performed.
- Parameter pairing does not itself preserve evaluation order of effectful argument expressions.
  The source supplies no purity/arguments guard or fake-name/field collision scan. These are
  inspection limits, not claims of observed failures in the pinned runtime without controls.
- Group ordering protects prototype initialization but does not enforce every declaration
  dependency. Missing boot appends no protected suffix; arbitrary runtime ASTs are not promised.
- Constant-object replacement is all-or-none per binding, whereas unsafe property renaming skips
  only that substage. The whole class transform has no rollback/refusal transaction; compilation
  failures publish no successful code, as the container contract states.
- Full-class and real-pass selection/negative/state controls, retained generated class variants
  and empirical coverage beyond the named test intent remain missing. The document-only proof
  covers only atomic constants and chosen permutation arithmetic.

## Source

Constant decisions and scope repair in item 3:
[classObfuscation.ts#L33-L175](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/transforms/runtime/classObfuscation.ts#L33-L175).
Class/member discovery and renaming:
[classObfuscation.ts#L184-L437](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/transforms/runtime/classObfuscation.ts#L184-L437);
nonempty record-key harvesting is specifically
[classObfuscation.ts#L360-L373](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/transforms/runtime/classObfuscation.ts#L360-L373).
Parameter selection/injection/permutation:
[classObfuscation.ts#L447-L683](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/transforms/runtime/classObfuscation.ts#L447-L683).
Statement groups and substage order:
[classObfuscation.ts#L688-L789](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/transforms/runtime/classObfuscation.ts#L688-L789),
[name-utilts.ts#L1-L100](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/utils/name-utilts.ts#L1-L100)
and [random-utils.ts#L7-L39](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/utils/random-utils.ts#L7-L39).
Shared map/constructors and closure shell:
[runtime.ts#L15-L109](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/runtime.ts#L15-L109)
and [runtime.ts#L681-L754](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/runtime.ts#L681-L754).
The pass is wired after table and before generation/minification by
[build-runtime.ts#L84-L124](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/build-runtime.ts#L84-L124),
forcing items 2 and 4's order.

## Fixtures

| Retained source/control | Scenario / bounded intent | Missing evidence |
|---|---|---|
| [classObfuscation.test.js](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/test/options/classObfuscation.test.js) | C1/C3/C5: fields gone from actual code, numeric map inlining, encoded BYTECODE scalar inlining, selected capture/combined behavior; C4: direct alias ordering and table/class result | Complete selection/negative/paired-argument/record/capture/state and frozen output controls |
| [randomizedOpcodes.test.js](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/test/options/randomizedOpcodes.test.js) | C1/C5: SLOTS removed, missing-noise void 0 guards and selected randomized table/class behavior | Exact noise/offset/field invariants |
| [handlerTable.test.js](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/test/options/handlerTable.test.js) | C5: specialized table/class recursion with numeric keys | All added opcodes and class selection rules |
| Retired bounded verifier | C1: actual synthetic atomic replacement/refusal and explicit consumed-state recrawl; C2: chosen permutation/value-pair arithmetic only | Full class discovery/record harvesting/rename/fake/order reconstruction, real pass/VM state and generated-output evidence |
| No retained direct real-pass control | C2 and other missing criteria above | Proposed acceptance criteria remain unqualified |

Encoder-local option tests generate through [test-utils.js](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/test/test-utils.js).
The frozen document-only subset is not full class or runtime reconstruction. No fresh encoder
execution, minified-stack qualification or novice study is claimed.
