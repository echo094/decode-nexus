# Probe Reference (`decoder/decode-js/sandbox-tests/`)

A **probe** is a throwaway script that answers one question about the decoder — how many
samples still carry a shape, which guard rejected them, what a stage emits — by reading real
decoded output or by breadcrumbing a pass from the inside. Probes are how nearly every cause in
this project was actually found ([encoder-decoder-method.md](../encoder-decoder-method.md) T6);
the committed test suite ([tests.md](tests.md)) is what pins a fix once it exists.

**This page is a recipe, not an inventory.** No probe is in git, and none should be: a probe is
cheap to rebuild from the conventions below and expensive to keep honest against a moving
matcher — a stale probe that still runs is worse than no probe, because it answers confidently.
So what is recorded here is how to build one, what data it reads, and the ways a probe lies.
Where a skeleton is worth having verbatim it appears below as a code block; **no script file
belongs in the hub.**

## Where probes live

Under `decoder/decode-js/sandbox-tests/`, untracked, and excluded through the submodule's own
`info/exclude` (`sandbox-tests/`). A submodule's `.git` is a *file* pointing at the real gitdir,
so that path is `<hub>/.git/modules/decode-js/info/exclude`, not
`decoder/decode-js/.git/info/exclude` — `git rev-parse --git-dir` from the submodule prints it.
That exclusion is **local to one working copy** — a fresh clone has neither the probes nor the
exclusion, so re-add the line before rebuilding anything there. The hub's own `.gitignore` is rooted at the hub and has never covered the
submodule, which once left a large frozen corpus sitting one `git add -A` away from the
decoder's history.

Probes are run from the **decoder root** (`decoder/decode-js`), and paths below are relative to
it.

## The two datasets, and how to regenerate them

Every probe reads one of two things: the frozen corpus, or the decodes of it. Neither is
committed, and neither needs to be — both rebuild from committed test-case sources.

1. **`sandbox-tests/high-size/corpus/` — the frozen corpus.**
   Read every `.src.js` under `test/jsconfuser/` **and** `test/jsconfuser/rename-variables/`,
   encode each `RUNS` times (default 3) at `{ target: 'node', preset: 'high' }`, and write an
   `.obf.js`/`.src.js` pair per sample as `<name>.<i>.obf.js`.
   **Derive `<name>` from the source's path, not its basename.** The two directories both
   contain a `control-flow-flattening.src.js`, with *different* contents, so a flat basename
   makes the second silently overwrite the first: a rebuild reported freezing every sample
   while writing three fewer files, one source absent from the corpus and nothing saying so.
   Prefixing the non-primary directory (`rename-variables__<base>`) is enough. **Assert that
   the number of `.obf.js` files equals sources × `RUNS` before trusting a freeze** — that
   equality is what catches this class, and it costs one line.
   **It needs `encoder/js-confuser/dist/` built** (`npm run build` there) — with the encode-side
   probes it is the only kind that requires the encoder at all. This is the long step; run it
   in the background. The encoder ships **CommonJS**, so an ESM probe reaches it through
   `createRequire`, four levels up from `sandbox-tests/<group>/`:

   ```js
   import { createRequire } from 'module'
   const require = createRequire(import.meta.url)
   const { obfuscate } = require('../../../../encoder/js-confuser/dist/index.js')
   ```
2. **`sandbox-tests/mask/dec-cache/` — the decodes.**
   Run every corpus `.obf.js` through the current `PluginJsconfuser` and write
   **`<base>.dec.js`** — that suffix is the contract every static reader filters on, and the
   base name must match the corpus sample so a reader can pair a decode with its `.src.js`.
   Must follow step 1, and must be re-run after **any** change that moves decoded output —
   every static reader is stale until it has. `ONLY=<prefix>` for a subset.
   **It writes, and never prunes.** A decode whose corpus sample no longer exists stays in
   `dec-cache` and every static reader then counts it, silently mixing two freezes. That is not
   hypothetical: a re-freeze after the `rename-variables__` prefix landed left 42 decodes under
   the old flat basenames, and the directory read 159 files for a 117-sample corpus. **Diff the
   two directories after any re-freeze** — `comm` the base names and delete what the corpus no
   longer has — and treat a `dec-cache` count that is not exactly sources × `RUNS` as the same
   class of failure step 1's own assertion catches.

**Freeze before comparing, and don't compare across a re-freeze.** The encoder samples randomly,
so two fresh encodes of the same source are not comparable and a fix can look like a regression
or vice versa ([encoder-decoder-method.md](../encoder-decoder-method.md) S5). A regenerated
corpus is *different obfuscated bytes*, so every figure measured against the old one becomes
anecdote — re-measure rather than compare. This is also why **a measured figure is not worth
recording in a doc**: it dies with the corpus it was taken against. Record the axis and the
probe that reads it.

The A/B loop that works, for regression-checking a landed fix:

```sh
node sandbox-tests/high-size/score.mjs > after.txt
git stash push -- src test
node sandbox-tests/high-size/score.mjs > before.txt
git stash pop
```

## Plumbing conventions

### A static reader over `dec-cache`

The default shape, and the one to reach for first: no decode run, so it costs seconds. It
answers "what survived, and in what spelling".

```js
// node sandbox-tests/mask/<name>.mjs            # tallies
// DUMP=<n> node sandbox-tests/mask/<name>.mjs   # print n full candidates
import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'
import { parse } from '@babel/parser'
import _traverse from '@babel/traverse'
import _generate from '@babel/generator'
import * as t from '@babel/types'

// Babel 8 ships these as default exports; the interop line is required, not decorative.
const traverse = _traverse.default || _traverse
const generate = _generate.default || _generate

const here = path.dirname(fileURLToPath(import.meta.url))
const cache = path.join(here, 'dec-cache')
const DUMP = Number(process.env.DUMP || 0)

for (const f of fs.readdirSync(cache).filter((n) => n.endsWith('.dec.js'))) {
  // Decoded output legitimately carries a top-level `return` (Pack's wrapper), and
  // errorRecovery keeps one malformed sample from ending the census.
  const ast = parse(fs.readFileSync(path.join(cache, f), 'utf-8'), {
    allowReturnOutsideFunction: true,
    errorRecovery: true,
  })
  traverse(ast, {
    /* key on the payload shape, then report which gate each survivor fails */
  })
}
```

**Take the directory from the script, not from `argv`.** Readers that glob their files on the
command line and `catch { continue }` on a read failure print a clean zero when handed a wrong
or forgotten glob, which is indistinguishable from a clean census — see Hazards. Where a
directory does need to vary, take it from an **env var and fail loudly when it is missing**,
rather than defaulting to something plausible.

**A census over decoded output means nothing until the same census has been run over the
`.obf.js` inputs.** The encoder emits dead code of its own, so a shape found in output is only
*ours* if the control run does not also carry it — this is S3's "was it ever live in the input?"
generalized past helpers to any residue. Build the control into the probe from the start (one
`DIR=`/`EXT=` pair, one code path), because a census that cannot be pointed at the input is one
that will be believed without the control.

**Know what the control can actually see, because under `high` it is not the whole input.**
Every `high` sample parses to a single `Function(<payload string>)(<harness object>)` call: the
program is sealed in a string, and only the wrapper and that harness object literal — including
its accessor bodies, which are real code — are visible to a parser. So the control's denominator
is the *outer* program while the census it is compared against sees the *whole* one. It still
discriminates whenever the shape lives in the harness (a real unbound-reference finding was
attributed to the encoder exactly that way, from `get "…"() { return x }`), and it reads a blind
zero for anything inside the payload. That direction is the safe one — a blind control makes an
encoder shape look like ours, costing an investigation rather than hiding a defect — but when
the control reads zero and the finding matters, **unpack the payload and re-run it** before
concluding the shape is the decoder's.

**And when the census is "identifiers that resolve to nothing", carry an explicit host-globals
allowlist.** Babel's `scope.globals` reports every unresolved reference, so without the filter
`console`, `Math` and `Buffer` are unbound on every sample and the probe reports a catastrophe
on clean output. The reverse error is the dangerous one — a name *missing* from the allowlist is
the finding, so keep the list generous and let the control run discriminate.

### A corpus-wide run: the worker-pool shape

When a probe has to *decode*, it is worth a pool: the work is embarrassingly parallel, and the
same skeleton is used by `score.mjs`, `redec.mjs`, `sc-warn.mjs` and `mask/bc.mjs` (which every
`*-instrument.py` runs through). **A worker is the same file re-invoked with a slice**, so there
is one implementation and no separate worker script.

```js
const workerOut = process.env.WORKER_OUT
const bases = workerOut ? JSON.parse(process.env.WORKER_BASES) : selected

if (workerOut) {
  // Results go to a FILE, never stdout: the plugin's own progress logging shares that
  // stream whenever it is enabled, and re-parsing results out of it is a bug farm.
  fs.writeFileSync(workerOut, JSON.stringify(bases.map(scoreOne)))
  process.exit(0)
}

const jobs = Math.max(1, Math.min(+(process.env.JOBS || os.cpus().length), bases.length))
const chunks = Array.from({ length: jobs }, () => [])
bases.forEach((b, i) => chunks[i % jobs].push(b))

const results = await Promise.all(
  chunks.map((chunk, i) => new Promise((resolve, reject) => {
    if (!chunk.length) return resolve([])
    const out = path.join(tmp, `worker-${i}.json`)
    const child = spawn(process.execPath, [process.argv[1]], {
      stdio: ['ignore', 'ignore', 'inherit'],
      env: { ...process.env, WORKER_OUT: out, WORKER_BASES: JSON.stringify(chunk) },
    })
    child.on('error', reject)
    child.on('exit', (code) =>
      code === 0
        ? resolve(JSON.parse(fs.readFileSync(out, 'utf-8')))
        : reject(new Error(`worker ${i} exited ${code}`)))
  })),
)
```

The env contract every probe here honours, so they are interchangeable at the command line:

| var | means |
|---|---|
| `ONLY=<prefix>` | restrict to samples whose base name starts with the prefix |
| `JOBS=n` | worker count; default is core count, `JOBS=1` runs in-process |
| `DUMP=<n>` / `DUMP=1` | print candidates instead of (or as well as) tallying them |

**Verify a new pool against `JOBS=1` once** — every pooled probe here was confirmed tally- or
byte-identical to its sequential result before being trusted. **And use `JOBS=1` for a *dump*
instrument:** dumps cap their output with a per-process counter, so N workers means up to N
times the cap, in no particular order, with interleaved stderr.

**Narrow before you widen.** `ONLY=`, or a single-sample probe, answers "did this fix the
thing?" in seconds. Only "did this break anything else?" needs the whole corpus — a pre-commit
question, not an iteration one.

**Background a whole-corpus run, and don't wait on it with `pgrep -f <script>`.** The waiting
shell's own command line contains that string, so `pgrep` matches the waiter itself and the loop
never exits — reporting "still running" long after the job finished. Match on `node .*<script>`,
or wait on the output file.

### Running decoded output

Any probe that *runs* what the decoder produced needs a hard timeout, and it is required rather
than defensive: a sample whose decode fails closed keeps the obfuscator's own machinery,
including anti-debug loops that can simply never return.

```js
execFileSync(process.execPath, [file], {
  encoding: 'utf-8',
  stdio: ['ignore', 'pipe', 'pipe'],
  timeout: 20000,
  killSignal: 'SIGKILL',
})
```

Two harness details are what make the comparison valid at all — capture output by patching the
real `console.log`, and parse with `allowReturnOutsideFunction`. Both are in
[tests.md](tests.md), which owns the encode → decode → run loop.

**A child-process scorer needs neither, and needs a third thing instead.** Those two exist for
an *in-process* harness; run the file in its own process and `console.log` already goes to a
pipe and the parser is never involved. What replaces them is how the result is observed at all:
the fixture sources record theirs as an undeclared **`TEST_OUTPUT = [...]` global**, not on
stdout, so a stdout-only comparison is **vacuous on most of the corpus** — it compared empty
against empty and reported every sample matching, tests.md's own guard failing in the one place
nothing enforced it. Compare stdout *and* the global, and count the samples that observe
neither rather than scoring them as passes.

Read the global from a **runner that requires the file**, never from a trailer appended to it:

```js
// runner.cjs — invoked as: node runner.cjs <file.cjs>
require(process.argv[2])
process.stdout.write(' TEST_OUTPUT:' + JSON.stringify(globalThis.TEST_OUTPUT ?? null))
```

Two reasons the indirection is required, not stylistic. Decoded output carries `Pack`'s
legitimate top-level `return`, which **ends the module** — an appended trailer never runs, and
reads as a sample that produced nothing. And the whole run must be **CommonJS**: the decoder
package is `"type": "module"`, under which that same top-level `return` is a syntax error, so
write each sample to a `.cjs` file.

**A failure line from such a probe is not a correctness regression until it is attributed.** The
timeout above turns a merely-slow sample into a failure indistinguishable from a wrong one, and
a kill arrives with no error message in the line where a thrown error would carry one. Re-run
that one sample on its own, with a generous ceiling, and read the actual error before believing
the corpus-wide verdict.

## Instrumenting a fail-closed matcher

The bail breadcrumb is the instrument for "which guard rejected this shape?"
([encoder-decoder-method.md](../encoder-decoder-method.md) T6 picks between it and the other
three). It is three files: a Python patcher, a shell runner, and a `.orig.js` copy of the pass.

**Tag every `return null` with its own source line** rather than a hand-written list of named
bail points — the tags then survive a matcher rewrite instead of going stale silently. Add
success counters in the same patch, so the declines have a denominator.

```py
import re
p = 'src/visitor/jsconfuser/<pass>.js'
orig = open('sandbox-tests/mask/<pass>.orig.js').read().split('\n')

# Anchor on syntactic forms, never on a line number: a hand-written line anchor is what
# made one of these assert and refuse to patch after an unrelated edit.
start = next(i for i, l in enumerate(orig) if l.startswith('function targetFn('))
end = next(i for i in range(start + 1, len(orig)) if orig[i] == '}')

out = []
for i, line in enumerate(orig):
    if not (start <= i <= end):
        out.append(line); continue
    indent = line[: len(line) - len(line.lstrip())]
    crumb = "{ bc('tag:L%d'); return null }" % (i + 1)
    if re.match(r'^\s*return null\s*$', line):
        out.append(indent + crumb); continue
    m = re.match(r'^(\s*)(if \(.*\)) return null\s*$', line)   # one-liners, else invisible
    if m:
        out.append(m.group(1) + m.group(2) + ' ' + crumb); continue
    out.append(line)

s = '\n'.join(out).replace('function <anchor>(', 
    "const BC = (globalThis.__BC ||= {})\n"
    "const bc = (k) => (BC[k] = (BC[k] || 0) + 1)\n\n"
    'function <anchor>(', 1)
# Success counters, so a decline tally has a denominator.
s = s.replace('  return { ...ok }', "  bc('tag:ok')\n  return { ...ok }", 1)
open(p, 'w').write(s)
print('instrumented')
```

**`<pass>.orig.js` is the instrument's INPUT, not a backup it writes.** The runner refreshes it
from `src/` immediately before patching — the only correct moment — and restores from it through
a `trap`, because a timeout kills the run before any trailing restore line:

```sh
#!/bin/sh
cd "$(dirname "$0")/../.."
trap 'cp sandbox-tests/mask/<pass>.orig.js src/visitor/jsconfuser/<pass>.js' EXIT INT TERM
cp src/visitor/jsconfuser/<pass>.js sandbox-tests/mask/<pass>.orig.js
python3 sandbox-tests/mask/<pass>-instrument.py >/dev/null || exit 1
node sandbox-tests/mask/bc.mjs
```

Four rules this pattern exists to enforce, each bought by an incident:

- **Refresh `.orig.js` inside the runner, never by hand.** A backup taken a step early, then a
  source edit, then the restoring `trap`, equals the edit silently reverted. Scripts that only
  *said* "refresh it from src/ first" in a comment are how that happened.
- **Restore from `.orig.js`, never `git checkout --`.** The latter reverts to HEAD rather than
  to "before my experiment", and it silently discarded an uncommitted matcher rewrite.
- **Assert on the edit sites.** If a `replace` finds no anchor, exit loudly. An instrument that
  patches nothing and runs anyway reports a stale matcher's behaviour as current.
- **Two instruments that patch different files share one corpus pass.** Give them disjoint key
  prefixes (`fns:` / `graph.`) and run them together; the corpus pass is the expensive part.
  Running two such scripts concurrently instead just contends for cores while each `trap`
  restores under the other's feet.

**Delete any generated copy that lands inside `src/`.** A probe-built variant of a pass (written
there so its relative imports resolve) is not covered by the `.orig.js` discipline and will be
committed by accident.

## Hazards — the ways a probe lies

- **A probe that mirrors a matcher gate-for-gate is blind to the population that matters.** It
  finds only near-misses — shapes the matcher almost accepts — and by construction cannot see a
  whole missing holder kind or a wrong visitor key. One such census reported zero corpus-wide
  while more than a third of samples carried the live shape, because the matcher keyed on
  `FunctionDeclaration` and every survivor was an assigned `FunctionExpression`; its replacement
  then inherited the same trap from a *different* gate. **Key the census on the payload, then
  report which gate each survivor fails** — that keeps the decline detail a mirror buys without
  the blind spot. A zero from a mirror probe is evidence about the accepted shape only.
- **A static read of a `high` corpus `.obf.js` sees one `Function(…)` call and nothing else.**
  `Pack` puts the whole program inside a string literal, so a shape census over the obfuscated
  *input* reports a clean zero for every shape — indistinguishable from "the encoder didn't emit
  it". Unpack it to a real file first, or read `dec-cache`, which is post-decode. The corollary
  that cost a session: **"packed" is not "unknowable"** — cutting the pipeline at `pack` and
  reading the tree there answers origin questions statically that were assumed unreachable.
- **A silent zero from a missed input.** Readers that take files from `argv` and `catch` a read
  failure print `0` when handed a wrong or empty glob, which reads exactly like a clean census.
  Prefer reading the directory in the script; when a probe does report zero, sanity-check it
  against something known non-zero in the same pass — the cheapest check there is.
- **A copy-pasted pipeline list drifts.** Several probes replay the plugin's stage list to
  attribute a shape to a stage, and each keeps its own copy — so one renamed pass breaks all of
  them at once, and an *added* stage drifts just as silently as a renamed one. Both have
  happened repeatedly, and once the stage whose behaviour was in question was the one the probe
  omitted. **Diff the list against `src/plugin/jsconfuser.js` before quoting any per-stage
  reading** — extract the stage names and `diff`; positionally, not by eye.
- **An orphaned child outlives its parent.** The run timeout above is enforced by the parent, so
  an interrupted probe leaves the child running and nothing reaps it. Check before trusting any
  timing: `ps -eo pid,ppid,etime,pcpu,command | grep '[d]ec.cjs'`, and kill anything with
  `PPID 1`. Tallies are deterministic and unaffected; wall-clock is not.
- **A bail tally measures the pipeline's interior, not its output.** Read the residue in the
  output before treating a decline count as a gap — a gate that declines can be load-bearing.
  This one is general enough to live in
  [encoder-decoder-method.md](../encoder-decoder-method.md) T6, along with the name-filter trap
  (never gate a breadcrumb on an identifier; renamed output reuses names across scopes) and the
  catch-block blind spot (a pass can fail *after* a successful match, and the guard tally then
  actively reassures).

## The axes worth censusing, and what each should read

Every row is a *spec for building a census*, not a script that exists. All but the suite need a
current `dec-cache`; the expected value is what a clean decode produces, so a non-zero is the
finding.

| axis | the census | expected |
|---|---|---|
| runtime correctness | decode each sample, run it and its `.src.js` in child processes, compare **stdout and `TEST_OUTPUT`** | every sample matches, and none vacuously |
| total decoded bytes / size ratio | sum decoded vs. source bytes over the corpus | no expected value — comparative only, within one corpus |
| unit + fixture suite | `npx vitest run` — the one axis needing no probe, and the only one a reviewer can reproduce | all pass |
| Flatten's scope-object layer | wrapper/inner function pairs surviving in decoded output | 0 |
| severed functions with no wrapper | `(obj, [pattern])` signatures with a computed `obj["k"]` access — the case a wrapper/inner *pair* census is blind to | 0 |
| decoder-introduced unbound refs | identifiers resolving to nothing, **against the same census over the `.obf.js` inputs** | 0 |
| dead bare `var` declarators | declarators with no init, no reads and no writes | 0 |
| `_cff_*` orphans, surviving scope anchors | `X.prop = {}` anchors whose property is read nowhere else | 0 |
| empty-bodied zero-reference functions | exactly that — an empty body has no semantics to argue about | 0 |
| `arr[n]` reads | computed member reads with a numeric key | 0, and **saturated** — per S2 it no longer discriminates, so don't build a scoreboard on it |

**A size figure is comparable only within one corpus**, so it belongs in the output of the run
that produced it and is anecdote anywhere else.

## When every census says clean

**Rank the decoded output by residue size and read the top of it.** This is the one signal no
probe's assumptions can filter, because it asks nothing and sorts everything — and it has paid
better than any census here. Three separate times it found a layer larger than anything a
census had reported, and **not one of the three was a declining matcher**: a deletion gate keyed
on a declaration form, a reference-gated sweep scheduled before the last reference died, and a
pass with no candidates at its only slot. Every census of every one of those passes read clean,
correctly, because each was asking about a *matcher*.

Two habits follow from that:

- **Cut the pipeline at a stage and read the tree there.** A `CUT=<stage>` dump — generate the
  AST as it stands after that stage — answers "is this shape ours or the encoder's?" faster
  than any argument, and it is what attributes a shape to the pass that *emits* it rather than
  to the encoder stage it resembles. Cutting at `pack` gives the encoder's own output with
  nothing of ours applied yet.
- **A pass's schedule is part of its correctness.** Audit *when* a reference-gated sweep runs
  and *when* a matcher's only slot runs, not only what either accepts. All three closures above
  were scheduling or gating, none was a matcher — which is why reading the pass and reading its
  census both missed them.

## Answering "is this residue actually dead?"

The S3 question ([encoder-decoder-method.md](../encoder-decoder-method.md)) needs a liveness
oracle, and the naive one gives the wrong answer for Program-level scaffolding: seeding a
fixpoint from *every* Program-level statement marks the whole cluster live by construction,
because the cluster is held up by Program-level assignments of its own. Build the top-level
binding dependency graph, then **seed only from observable statements** — writes to undeclared
globals, calls, anything not merely feeding another top-level binding — and report what never
gets marked.

**A census over this decoder's output must handle `var a, b, c;` before it can see anything.**
The encoder's MovedDeclarations emits merged declarations and the decoder's own
`declareIntroducedVariables` emits them again; an oracle that treats a merged declaration as one
opaque statement reads every name in it as a root. That single bug took one census from
reporting a handful of affected files to reporting dozens.

## What belongs here, and what belongs in the method doc

- **Here:** how to build a probe against *this* decoder — the datasets and their recipe, the
  plumbing conventions, the instrumenting pattern, and the construction hazards above.
- **[encoder-decoder-method.md](../encoder-decoder-method.md):** which instrument to reach for
  and how to read what it says — T6's four instruments, the bail-tally-vs-output-census ordering,
  S3's liveness caveats, S5's randomization, T8's "validate a premise before implementing
  against it".
- **[tests.md](tests.md):** anything that becomes committed coverage. A probe finds a bug; a
  fixture is what keeps it fixed, and it is the only coverage a fresh clone inherits.
