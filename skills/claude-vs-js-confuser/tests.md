# Corpus example checks

The pinned corpus contains experiment scripts, supplied examples and regular controls. The
[experiment registry](experiment-registry.md) identifies each entry point and control. Run an
experiment only after preparing the pinned project's dependencies according to its own README.
The corpus scripts are sample-specific; a successful run on their supplied input is an exact-example
result.

## Review procedure

1. Record the exact source file, input bytes, options and corpus revision. Mark any missing encoder
   commit, options or random seed as unavailable.
2. Run the experiment's supplied example and named regular or pass-through control with its own
   test harness. Record process status and the output bytes before interpreting success.
3. Parse the result afresh. Inspect the claimed mechanism's structure and recovered semantic
   operations. Check bounded behavior against a separately specified oracle.
4. For a negative input, check whether the result is byte-identical. Syntax and behavior
   preservation alone do not establish a safe decline.
5. Keep a newly generated input separate from the supplied exact example. A transfer claim requires
   the same encoder configuration, a verified mechanism population and retained evidence for the
   particular result.

## Evidence boundaries

| Input | Claim permitted by a passing check |
| --- | --- |
| Supplied exact example | The script handled those retained bytes under their known provenance. |
| Regular or pass-through control | The script's observed treatment of that control, including whether bytes were preserved. |
| Independently generated input | Only the named encoder, configuration, mechanism population and observed result. |

A process exit, output digest or behavior check by itself does not prove recovered structure. The
source-inspection-only plugin and transform pages document algorithms without implying a run or
transfer result.
