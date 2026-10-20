# VM source preparation

## 1. Target

Prepare JavaScript for VM recognition through visitors called by the VM plugin. The separate
internal file owns the VM consumer's initial requirements; it is not a public plugin or a
repo-wide normalization contract. Other consumers must assess the operations and their ordering
against their own input grammar. Read the [Babel foundations](../../decode-js.md) and
[VM plugin boundary](../../plugins/jsconfuser-vm.md) first.

Preparation runs on a private strict script parse. It never executes target code or publishes
intermediate source. A successful VM diagnosis publishes fresh emitted JavaScript; a decline
publishes the exact original input, including when preparation changed its spelling.

## 2. Algorithm

The ordered visitors restore literal property spelling and simple control bodies. Each addresses an
ordinary JavaScript shape; none identifies VM roles by names or synthesizes opcode, pool or sentinel
references.

Declaration placement is not prepared. The outer decoder can leave `var f, data;` followed by
`f = function hidden(x) { return x; }; data = [1];`; preparation keeps that spelling, and Packet A
reads each role from its single top-level defining write
([extract-container.md](extract-container.md)). Joining such assignments back into declarators,
and promoting function expressions to declarations, is rejected: a join also rewrites
per-handler function bodies, whose complete class comparison then sees a different statement
count, and an enclosing-scope binding lookup lets a nested function's write absorb an outer
declaration.

## 3. Implementation

### Components and admission

`normalizeVmInput(source)`, the default export, passes non-strings through to the existing
diagnosis. For strings, it uses `errorRecovery:false` and `sourceType:'script'`; a syntax error returns the original
string for the existing refusal path, without repairing malformed input or admitting modules
and outside-function returns. An unchanged traversal returns the exact original string; a
changed traversal generates source once for standalone diagnosis.

`normalizeVmAst(ast)` applies these passes on one AST, in order:

| Component | Rewrite and boundary |
|---|---|
| Existing [uncompute-member](../../visitors/atomic/uncompute-member.md) (`createUncomputeMember`) | Restore dotted static string members where the key is an identifier; preserve numeric/non-identifier keys and optional access semantics. Imported unchanged. |
| Existing guarded [uncompute-property-key](../../visitors/atomic/uncompute-property-key.md) (`createUncomputePropertyKey`) | Restore ordinary property keys; preserve computed object `__proto__`, class `constructor` and static class `prototype`. Imported unchanged. |
| Normalize simple control bodies (`createNormalizeControlBodies`) | In `if` branches and loop bodies, a singleton block containing only an expression, return, throw, break or continue can become that statement. Keep lexical declarations, directives, nested conditionals and function bodies intact. |

### Atomicity, state and comparison

Each candidate is checked before mutation. Refusal leaves that candidate untouched; independent
candidates may normalize. Replacement subtrees are cloned rather than shared across positions.
Each mutating visitor crawls the Program scope on exit, so subsequent
visitors see live declarations, writes and references. The tests invoke the shared
`expectConsistentState` oracle on the same AST, before serialization can hide stale state.

The [handler locator's lowering](locate-handlers.md#2-algorithm) uses `simpleControlBody` on
cloned handler statements, only for the conditional/loop body fields that
`isControlBodyKey(type, key)` selects.
Recognition reads the normalizer's output grammar: a simple body has the same comparison form
whether it arrived bare or in a singleton block. The view returns existing nodes, preserving
context binding identities and reference layout tags. Lexical or multi-statement blocks are not
erased; operation, literal, statement-count, captured-binding and complete-effect checks remain
strict. The producer's output inventory above, rather than template brace style, defines the
forms these consumers must read.
The class observer's earlier decoder-return, conditional-jump and iterator-exit readers also
consume that view. Complete comparison alone is insufficient when a preliminary clause rejects
the prepared form first. Direct observer tests pin both canonical and randomized admission;
container fallback cannot stand in for that consumer-contract check.

### Acceptance

| Scenario | Oracle and fixture |
|---|---|
| Declaration placement and function-expression form | Left as written, with same-AST scope consistency and bounded execution equality; normalize-source.test.js. |
| Keys and lexical control bodies | Special keys retain meaning; lexical blocks and dangling-else grouping survive; same test. |
| Adapter call and rollback | One standalone diagnosis of prepared source; public input and declined output remain original; plugin.test.js. |
| Complete wrapped samples | With and without outer string concealing: sequential success, no dispatch/payload arrays/method installations, and source/encoded/current TEST_OUTPUT equality; sequential.test.js. |

## 4. Input Shapes

The outer decoder can produce a source string whose function definitions and initializers are
assignments beside a hoisted `var` list. Packet A reads that spelling directly; the VM plugin
prepares only member and key spelling and control bodies before standalone recognition; the sequential coordinator itself continues to call outer then VM and retains the
outer result as stage evidence. Direct VM-plugin callers receive the same preparation.

Constant-value simplification can also leave `argc === 65535` in place of a sentinel-map read.
Preparation preserves that ordinary literal; the [handler locator's lowering](locate-handlers.md#2-algorithm)
reads a stable numeric map, or a top-level binding stably holding a number, as its value, so every
form compares equal. No visitor recreates map reads.

Standalone/component entry points remain unchanged; preparation is a plugin operation, not a
new outer-specific dialect inside the container recognizer. Public common and the existing imported
visitors are unchanged.

## 5. Known Gaps

This evidence does not establish repo-wide normalization suitability, arbitrary reflection
semantics or every outer-encoded VM shape. Class/minified and hardened inputs retain their own
source contracts; this preparation has no independent qualification population for them.

## Source

- [normalize-source.js](../../../../decoder/decode-js/src/visitor/jsconfuser-vm/normalize-source.js)
  — visitors, strict script wrapper and read-only control-body view in section 3.
- [jsconfuser-vm.js](../../../../decoder/decode-js/src/plugin/jsconfuser-vm.js) — preparation before
  its one standalone call, with original-string rollback.
- [locate-handlers.js](../../../../decoder/decode-js/src/vm/jsconfuser-vm/locate-handlers.js)
  — lowering reads the same simple-body view on handler clones.
- [uncompute-member](../../visitors/atomic/uncompute-member.md) and
  [uncompute-property-key](../../visitors/atomic/uncompute-property-key.md) — unchanged reused visitors.

## Fixtures

- [normalize-source.test.js](../../../../decoder/decode-js/test/visitor/jsconfuser-vm/normalize-source.test.js)
  — transformation/refusal, execution, idempotence and same-AST state oracles in section 3.
- [plugin.test.js](../../../../decoder/decode-js/test/vm/jsconfuser-vm/integration/plugin.test.js)
  — single prepared diagnosis, immutable public records and exact-input rollback.
- [sequential.test.js](../../../../decoder/decode-js/test/vm/jsconfuser-vm/integration/sequential.test.js)
  — complete wrapped recovery with and without outer string concealing.
