# Minify the completed runtime and container

## 1. Target

Reduce and obscure the final JavaScript source after every wordcode/runtime protection has been
assembled. With `minify` truthy, pass the **whole generated program**, including serialized data,
boot, runtime and prepended instruction comments, through the supplied Closure Compiler at
ADVANCED level. The result is the compiler process's stdout, returned as public `code`.

Read the [workflow/AST foundation](../js-confuser-vm.md),
[container/transport](../container-wordcode.md), [options](../options.md),
[handler table](handler-table.md) and [class runtime](class-runtime.md) for the input alternatives.
The page specifies invocation, sequencing, publication and evidence boundaries. Closure Compiler
is a supplied external optimizer, not an unavailable mechanism reconstructed here. Its complete
optimization/rename algorithm and every possible emitted spelling are outside this package.

## 2. Algorithm

Finish runtime AST rewriting first, then generate text. This makes all chosen opcode handlers,
frame offsets, tables, class parameters and boot dependencies visible to a whole-program optimizer.
Prepend instruction comments after generation so they refer to the finalized instruction identities;
then provide that complete text through stdin to one fresh Closure Compiler process.

Wait for the callback. A nonzero exit rejects with stderr (or an exit-code fallback); zero exit
resolves stdout without further rewriting. The runtime builder replaces its generated string
only after that success and then returns it. Minification failure rejects the public compile
operation, so callers receive no successful partial code result.

### Worked boundary example

This **synthetic dataflow**, not a predicted Closure output, starts with the container example
`LOAD_CONST r0, pool[0], key=0; RETURN r0`, words `[0,0,0,0,45,0]` and pool `["ok"]`.
Generation receives the complete AST: declarations plus matching handlers and boot. The minifier
input is `instructionCommentBlock + "\n" + generatedProgram`. If encodeBytecode is enabled,
the same six words travel as `AAAAAAAAAAAAAAAAAAAAAC0AAAAAAAAA`; its decode flag/helper and
boot relationship accompany that string. PCs still mean words after runtime decoding.

A supplied optimizer could inline a word/pool declaration into a constructor argument, shorten
a lexical binding, or fold a boolean to `!0`/`!1`. That listing is a dependency/evidence question,
not an output template defined by this wrapper. The observable contract checked here is that
the entire assembled source reaches stdin, stdin ends, and successful stdout becomes `code`.
For callback `(exitCode=1, stderr="invalid input")`, the low-level rejection is Error with that
message; the runtime builder wraps it as `VM-Runtime final minification failed` with its cause.
For callback `(0, stdout="...", stderr="warning")`, stdout resolves and stderr does not fail the
operation. No output parse, nonempty check or behavior test is added by the wrapper.

## 3. Implementation

### Components and supplied dependency

| Component | Input -> output | Consequential boundary |
|---|---|---|
| Runtime generation | Final Babel File -> source string | Generation failure wrapped independently before minify. |
| Comment prefix | Instruction comment string and generated source -> joined input | Unconditional prefix; comments do not define runtime roles. |
| External invocation | Full source string -> compiler stdin | Fresh ClosureCompiler configured only as below. |
| Completion | Exit code/stdout/stderr -> resolved string or error | Exact zero-exit decision; no postvalidation. |
| Publication/profile | Successful string and timing -> public code/profile entry | Failure publishes no successful result; measurements are compilation state. |

The supplied `google-closure-compiler` package must expose a constructible default import whose
instance has `run(callback)` returning a process with writable stdin. `run` consumes compiler
output and invokes callback with `(exitCode:number,stdOut:string,stdErr:string)`. The caller
writes the full string and ends stdin. This is a CLI/process dependency, not Babel minification.
The pinned manifest declares `google-closure-compiler` range `^20260216.0.0`; that range alone
does not freeze installed optimizer bytes or prove identical output. No install or fresh run is
required to read this specification.

The only explicitly supplied compiler options are:

```text
compilation_level: "ADVANCED"
warning_level: "QUIET"
```

There are no explicit externs, input/output language, formatting, target, rename seed, source-map,
custom pass, timeout, code-size ceiling or stdin error listener in this wrapper. Defaults and
optimizer behavior come from the supplied dependency and its actual installed distribution.
Do not invent additional flags from an observed emitted form.

`minify(sourceCode)` creates a Promise, constructs the compiler and calls `run`. If callback's
exitCode is not zero, reject `new Error(stdErr || "Closure Compiler exited with code " + exitCode)`.
Otherwise resolve stdOut exactly. Synchronous throws inside the Promise executor reject it;
external process/stream failure handling beyond the callback is not specified here. The runtime
builder catches rejection/throw and wraps it with the fixed minification-failed message and cause.

The runtime transform entry re-exports this function as applyMinify. The runtime builder calls
it only after handler additions, shuffle, table, class, generation and comment prefix, under
ordinary minify truthiness. Record `profileData.transforms.applyMinify.transformTime` after
success; generation timing was recorded before the comment prefix/minifier. No handler/map
rebuilding occurs after the optimizer returns; the returned code is not parsed again by the
encoder. `handlerCount` reflects the earlier AST switch count, not a census of final stdout.

### Emitted shape and state boundary

The actual output grammar is whatever the supplied optimizer emits for the supplied whole program.
The wrapper preserves no lexical-name, declaration-placement, comment, function-boundary,
parameter-position or helper-call-layout contract. Earlier stages still define runtime meaning:
words/pool/map/frame/receiver/capture relationships must remain connected in executable output.
ADVANCED requests optimization; this wrapper does not prove preservation or coverage for arbitrary
host code/facilities or option stacks.

Source inspection establishes that raw data can enter as ArrayExpressions, encoded data as a
base64 string, table dispatch as a computed member call and class output with literal maps,
renamed fields, fake stashes and permuted calls. It does **not** determine one universal minified
boot signature. In particular, the class stage's random fake/permutation choices give the
optimizer different AST inputs. Array relocation, helper inlining/movement, boolean/undefined
spellings and retained dummy arguments need bounded emitted-byte evidence for any concrete claim.
There is no encoder-local retained minified output index in this package; no such shape is
asserted as exhaustively supported from the invocation recipe alone.

Compilation mutates only its private strings/profile records at this stage. It does not execute
the generated program, rewrite runtime word state or supply runtime cleanup. The whole-source
[publication boundary](../container-wordcode.md#emitted-forms-failures-and-publication) applies;
there is no partial result or retry protocol. Runtime effects/cleanup stay in canonical semantics.

### Testing and acceptance

| Scenario | Observable result / oracle | Acceptance criterion | Retained control |
|---|---|---|---|
| M1: input/order/configuration | Stub records complete commented source and exactly ADVANCED/QUIET | One fresh invocation after all runtime rewrites; one write then end | Synthetic boundary example; no dedicated retained stub control |
| M2: success/publication | Zero exit stdout equals public code; earlier profile retained | No extra parse/rewrite and success timing recorded | No dedicated retained control |
| M3: failure | Nonzero stderr/fallback reaches wrapped minification error/cause | No successful code result; controls reach minifier rather than parser | No dedicated retained negative control |
| M4: actual shape/effects | Freeze source/options/optimizer bytes/output; compare program oracle and AST roles | Changed shape plus word/frame/receiver/capture semantics verified per profile | No encoder-local retained minified-output/control here |
| M5: combined transport/table/class | Assert actual named option effects in frozen output and behavior | Each concrete stack has independent output/provenance; no all-options inference | No dedicated minified stack control |

M1-M3 can use a supplied dependency stub without executing the encoder's real optimizer. M4-M5
require actual retained emitted bytes, exact configuration/dependency provenance and behavioral
oracles covering the chosen source features. Smaller output or successful execution alone cannot
establish preservation of every runtime role or arbitrary output coverage. These remain designs,
not a fresh qualification report.

## 4. Later Stages

No later encoder transformation runs. Returned `code` is stdout directly; callers/host JavaScript
engines interpret that program. Profile/log generation does not rewrite it. Runtime boot still
materializes encoded words where needed and executes the connected root, under the container
and instruction contracts. Instruction comments may disappear and carry no execution metadata.

## 5. Known Quirks

- The only requested optimizer behavior is ADVANCED/QUIET. Dependency defaults and exact version
  matter; an encoder pin alone is not an exact installed-optimizer provenance claim.
- Zero exit does not imply nonempty, parsable or behaviorally verified stdout in this wrapper.
- No dedicated minify test file or minify project is supplied in the pinned encoder option-test
  matrix. The matrix's all-options profile also omits minify. Other option tests cannot fill this
  evidence gap by inference.
- This page closes the invocation/interface recipe, not the external optimizer's own design,
  all emitted AST shapes, cold reconstruction or novice/full-stack qualification.

## Source

External invocation/callback in items 2-3:
[minify.ts#L1-L21](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/minify.ts).
Runtime entry alias is [runtime/minify.ts](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/transforms/runtime/minify.ts).
Generation, comments, final minify/profile/error wrapping and terminal publication in items 3-4:
[build-runtime.ts#L84-L124](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/src/build-runtime.ts#L84-L124).
The supplied dependency range is in
[package.json](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/package.json).
The absence of a minify project/all-profile flag is visible in
[jest.config.js](https://github.com/MichaelXF/js-confuser-vm/blob/20c5b96bf57337c568579352758d7685358650de/jest.config.js).

## Fixtures

No dedicated encoder-local minification fixture, test or emitted-byte artifact is indexed here.
M1-M5 above remain proposed acceptance scenarios, not empirical results. The other representation
pages index their own finite option-test intent, which does not qualify minification. The
synthetic boundary example checks input/callback reasoning only. No encoder execution, fresh
qualification, cold reconstruction or novice study is claimed.
