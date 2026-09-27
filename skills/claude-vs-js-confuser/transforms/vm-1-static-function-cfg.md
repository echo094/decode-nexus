# Static function and CFG discovery

Evidence label: source-inspection only. This page is the E3 reconstruction contract for static
function discovery and block splitting over the frozen VM-1 descriptor map. It does not establish
complete control-flow recovery, dynamic-target resolution, runtime handler semantics, or execution.

## 1. Target

Recover the top-level and nested function records from E2 descriptors, then partition each
statically reachable body into basic blocks with ordered instructions and leader addresses. The
result is consumed independently by [reducible register structuring](vm-1-reducible-register-structuring.md)
and [dual emission](vm-1-dual-emission.md).

The discriminator is static target availability under the hard-coded successor rules. Function
zero starts at PC `0`; children are the unique `DEFINE_FUNCTION.fT` targets. `JUMP_DYN` has no
enumerated successor, so it cannot add a dynamic destination to a body. A target absent from the
descriptor map is skipped rather than materialized.

## 2. Algorithm

1. Create a `funcs` array and `byStart` map. Add the top-level record with `start: 0`, no
   parameters, the E1 frame size, no rest flag/captures, and `top: true`.
2. Scan every key in the E2 instruction map. On `DEFINE_FUNCTION`, add one child per unique
   `ins.fT`, retaining `params: ins.fl`, `frameSize: ins.fi`, `rest: ins.fJ`, and `caps: ins.caps`.
3. For every function now in `funcs`, collect a body with a stack worklist. Pop an address, skip
   it if seen or absent, record it, and push all addresses returned by `successors`; sort the
   final set numerically.
4. Seed block leaders with the function start. For each reachable instruction, add the static
   targets and fall-through boundaries required by its opcode, including catch targets,
   `TRY_POP` boundaries, and selected `TRY_FINALLY` continuation addresses.
5. For each sorted leader, walk forward through reachable instructions. Stop after a terminator
   or before a second leader, and store `{ addr: leader, instrs: orderedList }`.

## 3. Implementation

### Function metadata

`discoverFunctions` uses `addFunc(meta)` to deduplicate by `meta.start`, allocate a sequential
`fid`, copy the metadata, and index it by start. The top-level record is added before scanning
`Object.keys(instrs)`. Because all `DEFINE_FUNCTION` records are collected before the body loop,
each child has its own reachability traversal. The capture descriptors are retained; no closure
value is executed or resolved at this boundary.

### Successor policy

`successors(ins, instrs)` computes `next = ins.start + ins.size` and returns the following sets:

| Instruction | Static successors | Consequence |
| --- | --- | --- |
| `JUMP` | `[target]` | No fall-through edge. |
| `JUMP_IF_FALSE`, `JUMP_IF_TRUE` | `[next, target]` | Both branch arms enter the body if present. |
| `FORIN_NEXT` | `[next, target]` | Iteration and exit arms are both represented. |
| `RETURN`, `THROW` | `[]` | Reachability stops. |
| `JUMP_DYN` | `[]` | The register-selected target is unresolved here. |
| `TRY_CATCH` | `[next, catchPc]` | Normal and exception entry are both considered. |
| `TRY_FINALLY` | `[next, W, V, aa]` filtered for non-null | `Z` is decoded but not traversed. |
| Any other operation | `[next]` | Sequential fall-through. |

The `instrs` parameter is accepted by `successors` but is not used to add or validate edges. The
worklist's `seen` set is the termination invariant; only descriptor-derived addresses are pushed.

### Leader and block policy

`buildBlocks` derives `bodySet` from the collected body and starts `leaders` with `f.start`. It
adds the following source-level boundaries:

| Instruction | Leaders added |
| --- | --- |
| `JUMP` | Present target. |
| conditional branch or `FORIN_NEXT` | Present target and present `next`. |
| `RETURN` or `THROW` | Present `next`. |
| `TRY_CATCH` | Present `catchPc` and present `next`. |
| `TRY_POP` | Its own `ins.start` and present `next`. |
| `TRY_FINALLY` | Its own `ins.start`, present `W`, `V`, `aa`, and present `next`; not `Z`. |

Each leader is filtered back through `bodySet`. The inner walk appends while the PC is in the
instruction map and body set, then stops when `TERMINATORS` contains the opcode or the next PC is
a leader. `TERMINATORS` contains `JUMP`, both conditional branches, `RETURN`, `THROW`,
`FORIN_NEXT`, and `JUMP_DYN`. A block has no computed semantic end field at this stage; downstream
structured modeling derives its end from the last instruction's `start + size`.

### Source ownership

| Source span | Ownership | What it owns |
| --- | --- | --- |
| [`vm.js#L278-L307`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-1/vm.js#L278-L307) | owned algorithm | Top-level/child records, start deduplication, and metadata retention. |
| [`vm.js#L312-L324`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-1/vm.js#L312-L324) | owned algorithm | Body worklist, absent-target skip, and sorted reachable PCs. |
| [`vm.js#L326-L340`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-1/vm.js#L326-L340) | owned algorithm; shared downstream coordinator | Opcode-specific static edge policy, reused by the structured emitter's dependency wiring. |
| [`vm.js#L345-L400`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-1/vm.js#L345-L400) | owned algorithm | Leader rules, terminator boundaries, and raw block construction. |
| [`vm.js#L85-L89`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-1/vm.js#L85-L89) | shared coordinator | Terminator set used by block construction; it does not add edges itself. |

## 4. Upstream Effects

E3 consumes E2's PC-keyed descriptors, `size` values, static targets, opcode identity, and
`DEFINE_FUNCTION` metadata. If E2 throws on an unknown opcode, E3 is never entered. If a descriptor
target is absent, E3 omits it without creating a placeholder block.

E4 assumes E3's blocks can be modeled as contiguous ranges and may reject shapes that are not
reducible or well nested. E5 uses the same raw block partition to make one dispatcher case per
leader and can preserve `JUMP_DYN` as an explicit register-based PC assignment. E3 itself does
not choose between those emitters, infer a handler meaning, or perform register liveness.

The selected `TRY_FINALLY` addresses are an important downstream limitation: both reachability and
leaders carry `W`, `V`, and `aa`, while omitting `Z`. E4 rejects `TRY_FINALLY` structurally, and
E5's handler lowering receives whatever blocks E3 represented; neither page may describe E3 as a
complete finally-state graph.

## 5. Known Gaps

- `JUMP_DYN` contributes no static successor. Indirect control is not resolved or conservatively
  expanded into all possible blocks.
- `TRY_FINALLY` is only partially represented: `W`, `V`, and `aa` are selected, while decoded `Z`
  is omitted from both successor and leader rules.
- Reachability is tied to the fixed E2 descriptor map and its sample register/frame conventions;
  no abstract VM state, handler analysis, indirect-target recovery, or graph completeness check
  is present.
- A function starts at every unique child entry descriptor even if its entry is absent from the
  instruction map; its body then becomes empty through the absent-target skip.
- The source-backed static graph description does not establish graph completeness, behavior, or
  transfer.

## Source

| File | Pinned source | Role |
| --- | --- | --- |
| `VM-1/vm.js` | [`function discovery and successors`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-1/vm.js#L278-L340) | Function records and static reachability. |
| `VM-1/vm.js` | [`block construction`](https://github.com/MichaelXF/claude-vs-js-confuser/blob/e90be6ca716e28f4bba91fe39615a665656bd802/VM-1/vm.js#L345-L400) | Leaders, terminators, and raw block lists. |

## Fixtures

No maintained fixture is created or decoded here.

| Corpus artifact | Claim it pins | Evidence status |
| --- | --- | --- |
| `VM-1/input.js` | Instruction-bearing sample whose blocks are the documented input | Fixture evidence only; not decoded. |
| `VM-1/output.dispatch.js` | Existing output retaining explicit block/PC control | Generated-output provenance only. |
| `VM-1/NOTES.md` | Reported entry-0, child scan, BFS, and block pipeline | Documentation evidence only. |
| `VM-1/verify.js` | Intended comparison context for recovered graph behavior | Test-intent evidence; no result is claimed. |
