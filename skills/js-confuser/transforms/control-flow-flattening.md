# ControlFlowFlattening

Source: `transforms/controlFlowFlattening.ts` (~1900 lines, by far the most complex
transform in the pipeline)

Splits a function/program body into "basic blocks" driven by a `while(sum(states) !==
END) switch(sum(states)) { case N: ... }` state machine. Key details:

- State isn't a single int — it's a sum over ~75-100 `states[i]` slots (`stateVars`),
  most values borrowed from a shared `sequence` array for compactness/decoys.
- Each scope gets a `scopeManager` — locals become `scope["propName"]["memberName"]`
  member expressions rather than plain identifiers.
- Numbers, booleans, and strings inside flattened code get "entangled" with state vars
  (`stateVar + literalDiff`) rather than left as plain literals; strings are additionally
  XOR-enciphered (`templates/xorStringTemplate.ts`, position-dependent stream cipher keyed
  off the entangled number) and packed into a shared `{ph}_strings` blob.
- Adds genuinely dead/unreachable fake blocks, fake `goto`s, cloned-but-unreachable
  chunks, and decoy `case` labels on real blocks — pure noise, safe to discard once you
  can prove a case is unreachable from the real path.

## Reversal

This needs a dedicated CFG-recovery pass:

1. Parse the switch into labeled blocks.
2. Symbolically evaluate `stateVars` assignments to build a block transition graph.
3. Walk from the (statically known) start state.
4. Undo the entangled-literal math and XOR string decoding along real edges.
5. Drop unreached cases/scope-init noise.
6. Re-linearize into structured control flow (this is the hard part — flattening
   destroys the original if/loop shape; most decoders stop at "linear list of
   statements" and accept less-readable-but-correct output rather than fully recovering
   `if`/`for`).
