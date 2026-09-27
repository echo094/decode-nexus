# Handler canonicalization and opcode interpretation

Status: source-inspection only. This page reconstructs the frozen VM-3 handler interpreter at
commit `e90be6ca716e28f4bba91fe39615a665656bd802`; canonical-shape agreement is not a runtime
equivalence or transfer claim.

## 1. Target

Infer the meaning, operand order, and fixed stream width of each computed numeric handler in the
VM descriptor. The target includes two source variants of one operation: operands read with the
runtime operand reader and operands baked as numeric literals into a specialized handler. The
discriminator is the canonical AST plus ordered slot provenance, not the randomized numeric opcode
or function name.

## 2. Algorithm

For one handler, `canonicalize` performs these transformations in order:

1. Clone the handler while dropping locations/comments and number operand-reader calls in AST
   evaluation order. A direct read becomes one stream slot; a one-argument constant-decoder call
   becomes two stream slots for pool index and conceal key.
2. Discover aliases for the VM stack, frame pointer, and register base. Replace known VM members
   with `STACK`, `FP`, `RBS`, `BC`, `POOL`, `GLOBAL`, `SP`, and `CELLS`; turn frame-relative
   offsets into `PC`, `PFP`, `RDST`, `TH`, `TPL`, `FSZ`, `FEND`, and `HND`; and turn register
   accesses into `R[$]`.
3. Replace modeled helper calls and constructors with canonical names (`STR`, `PUSHFRAME`,
   `CLOSE`, `RUN`, `VMCTOR`, `B64`, `TPLCTOR`, `CELLCTOR`, `MKCELL`, `TPLMAP`). Normalize
   template/cell property names. Replace only recognized junk arguments with `_` and remove
   trailing `_` markers.
4. Remove redundant alias declarations. Repeatedly inline a constant single-use temporary,
   except when its reference is inside a loop; stop after forty passes or when no such binding
   remains. Convert every remaining numeric literal to a baked `$` slot, rename residual locals,
   and collect slot metadata in generated traversal order.
5. Match the canonical string in `specFor`. Exact forms and anchored regular expressions map to
   instruction kinds, role positions, and fixed stream-read counts. An unmatched form becomes an
   explicit `{kind:"unknown", fixed:nStream, roles:{}, canon}` spec, carrying the source-derived
   stream width without inventing a semantic kind.

The semantic families are:

| Canonical form or family | Kind and role contract |
| --- | --- |
| `R[$]=R[$] op R[$]`; compound assignments; recognized MBA | `binop`; destination/source roles are `{dst:0,a:1,b:2}` or `{dst:0,a:0,b:1}`. |
| `R[$]=op R[$]` | `unop`; `{dst:0,a:1}`. |
| `R[$]=R[$]`, `R[$]=$`, `R[$]=TH`, `$;R[$]=void $` | `move`, `loadImm`, `loadThis`, `loadUndef`. |
| `R[$]=STR($,$)` | `loadConst`; destination, pool index, key. |
| `R[$]=R[$][R[$]]`, `Reflect.set(...)`, `delete` | `getMember`, `setMember`, `deleteMember`. |
| `GLOBAL[STR($,$)]=R[$]`; anchored global-load/typeof forms | `storeGlobal`, `loadGlobal`, `typeofGlobal`. |
| `PC=$`, `R[$]||(PC=$)`, `R[$]&&(PC=$)`, `PC=R[$]` | `jump`, `branch`, `jumpIndirect`; branch records whether the condition is negated. |
| `throw R[$]`; return prefix containing `CLOSE` | `throw`, `return`. |
| `HND.pop()` and handler-stack pushes | `popHandler`, `pushCatch`, `pushFinally`. |
| Cell ternary read and materialized-cell write | `loadCell`, `storeCell`. |
| For-in iterator setup/next regexes | `forInInit`, `forInNext`. |
| `Object.defineProperty(...);` getter/setter regexes | `defineGetter`, `defineSetter`. |
| Decrypt loop regex | `decrypt`; four range/key roles. |
| Array/object construction loops | `arrayLit`, `objectLit`; counts select variable tails. |
| `PUSHFRAME` call patterns | `call`, `methodCall`, `construct`; headers select fixed or spread tails. |
| Closure-construction loop containing `TPLCTOR` | `makeFunction`; six fixed fields plus capture pairs. |

`buildOpcodeMap` applies this independently to every numeric handler and stores `spec.slots`.
Page 3 is allowed to consume a spec only through those slots and roles; it must not assume that
the printed `$` count equals the number of stream words.

MBA recognition is a separate bounded branch. `identifyMBA` locates two int32 locals normalized
with `~~` and the final member assignment expression. Its interpreter accepts numeric literals,
the two identifiers, unary `~`, `-`, `+`, and supported basic binary operators. It tests fifteen
source-defined int32 pairs against `+`, `-`, `*`, `^`, `&`, `|`, `<<`, `>>`, and `>>>`. Only an
operator matching every sample upgrades the `mba` spec to `binop`; a failed interpreter or no
candidate leaves the handler unrecognized.

## 3. Implementation

The canonical language intentionally erases names while preserving information needed for static
decoding:

| Source detail | Canonical result | Why it matters |
| --- | --- | --- |
| `x(this, junk)` operand read | `$` with `{stream:true, read:n}` | Stream width and role position survive junk removal. |
| `y(this, junk)` constant read | `STR($,$)` with two ordered reads | Pool index/key pair is not collapsed to one operand. |
| Numeric literal in a handler | `$` with `{stream:false, value:n}` | Baked operands consume no word in page 3. |
| Stack/frame alias chain | `R[$]`, frame token, or VM token | Specialized aliases compare with ordinary handlers. |
| One-use constant outside a loop | Inlined AST | Equivalent stream/baked variants can share a canonical form. |
| Residual local binding | `v0`, `v1`, ... before generation | Generated names do not split equivalent shapes. |

`specFor` derives `fixed` from stream slots, except for array/object/call/closure regexes whose
fixed headers are explicit because their remaining words are count-selected. The variable-tail
contracts handed to page 3 are:

| Kind | Fixed operands | Tail discriminator |
| --- | --- | --- |
| `arrayLit` | count plus destination roles | Count element-register words. |
| `objectLit` | pair count plus destination roles | Count key/value register pairs. |
| `call` / `construct` | destination, callee, argc/hint | If `argc === hint`, one spread-array register; otherwise `argc` argument registers. |
| `methodCall` | destination, receiver, callee, argc/hint | Same spread rule, with receiver before callee. |
| `makeFunction` | entry, params, capture count, register count, rest flag, destination roles | Count `(own, index)` capture pairs. |
| `decrypt` | destination, source start, source end, key | Page 3 applies the range to its private word copy. |

The canonicalizer's AST mutations are source-backed and deliberately bounded. `stripJunkArgs`
recognizes strings, `null`, empty arrays/objects, and `void` expressions; it does not prove that
other arguments are junk. Numeric-slot replacement occurs after temporary inlining, so the slot
list is the final canonical traversal order. Alias declaration removal and identifier rewriting
do not execute or evaluate the handler.

The `specFor` fall-through is not a generic interpreter. An `unknown` spec carries
`{kind:"unknown", fixed:nStream, roles:{}, canon}` and is retained in the map. An absent opcode
specification raises during page-3 decoding; a present `unknown` kind can be consumed at its
source-derived width but is rejected by page-4 lifting/emission rather than assigned a semantic
operation.

## 4. Upstream Effects

[Structural detection](vm-3-structural-vm-detection.md) supplies the handler functions, helper
identities, frame offsets, pool decoder identity, and handler table. No earlier decoder pass
rewrites these handler ASTs. This page's output is the only source of fixed widths, operand roles,
stream-versus-baked provenance, and semantic instruction kinds for
[payload disassembly](vm-3-payload-disassembly.md).

The canonicalizer does not import a fixed opcode table: numeric values remain build-specific, and
handlers are matched by structure. Conversely, canonical shape equality does not prove that two
handlers are equivalent outside the modeled AST language. The MBA sample test is an identification
rule for this source, not a proof over all input values.

Material safety edges are:

| Edge | Handling |
| --- | --- |
| Unknown canonical handler | Store `unknown` with the derived `nStream` width and empty roles; never assign a guessed semantic kind. |
| Unsupported MBA AST or disagreement | Keep the `mba`/unknown result; do not use `eval`. |
| Baked operand | Store provenance and consume no stream slot. |
| Specialized helper argument or alias variant | Normalize only the recognized pattern; leave other AST structure visible for the source check. |

## 5. Known Gaps

- The canonicalizer is tied to the VM helper and frame relationships detected by page 1; it is
  not a general JavaScript handler normalizer.
- `specFor` uses exact/anchored source shapes. A semantically equivalent but differently spelled
  handler can remain `unknown`.
- The MBA interpreter has a restricted AST and finite sample set; agreement does not establish
  all-value equivalence or host-effect equivalence.
- `buildOpcodeMap` does not validate that every handler is reachable from a valid payload or that
  every spec's dynamic tail is well formed.
- Source inspection alone makes no behavioral, transfer, or production-coverage claim.

## Source

Canonicalization is [`canonicalize`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-3/vm.js#L515-L755), with junk and temporary helpers at [`stripJunkArgs`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-3/vm.js#L757-L783). Shape matching is [`specFor`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-3/vm.js#L817-L890). MBA identification and map assembly are [`identifyMBA`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-3/vm.js#L892-L963) and [`buildOpcodeMap`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-3/vm.js#L972-L990).

## Fixtures

| Fixture | Claim it could pin | Evidence role |
| --- | --- | --- |
| `VM-3/input.js` | Numeric handler assignments, operand-reader variants, and baked-handler shapes | Source fixture |
| `VM-3/NOTES.md` | Canonicalization and handler-shape rationale | Documentation provenance |
| `VM-3/debug/canon.js`, `VM-3/debug/canon2.js` | Canonicalization inspection tooling | Debug-tool provenance |
| `VM-3/debug/canon.txt`, `VM-3/debug/canon2.txt`, `VM-3/debug/handlers.txt` | Canonical and handler-shape records | Diagnostic artifacts |
| `VM-3/debug/specs.js`, `VM-3/debug/specs.txt`, `VM-3/debug/dump-handlers.js` | Semantic-spec inspection context | Debug-tool provenance |
