# jsconfuser/preparation.js — no dedicated file

## 1. Target

Two of [Preparation](../../../js-confuser/transforms/preparation.md)'s three concerns have
no decode target at all: safety metadata (`UNSAFE`/`PREDICTABLE`) is an AST-only tag with
no runtime trace in emitted code, and the `@js-confuser-var` escape hatch is fully consumed
on the encode side (either by Preparation itself or by `RenameVariables`/
[Finalizer](finalizer.md)) before any output is generated. The third — AST normalization —
is a different story: it's genuinely undecoded residue for three of its five rewrites, just
not yet in scope. See Known Gaps.

## 2. Algorithm

Nothing to reverse for safety metadata or the escape hatch — both are gone from the tree
(or already resolved to their final form) by the time any decoder would see the output.
The AST-normalization rewrites are semantics-preserving syntax choices, not concealment,
so in that sense they're not a decoder's job the way an actual obfuscation mechanism is —
but "not concealment" is a different claim from "already reversed," and no current
decode-js pass reverses any of the three rewrites that leave less-readable output behind.

## 3. Implementation

Nothing jsconfuser-specific implemented.

## 4. Upstream Effects

**Preparation rewrites every non-computed member access to a computed string-keyed one
(`object.foo` → `object["foo"]`), and that spelling is what the rest of this pipeline reads.**
It is Order 0 on the encode side, so it has already run on everything any of our passes sees.
This is the shape inventory the consumers key against — a matcher written for `obj.foo` finds
nothing on real output.

| spelling | where it comes from | who has to accept it |
|---|---|---|
| `obj["foo"]` | Preparation, unconditionally | every visitor matching a member key — most gate on `computed: false`, a few on `computed: true` |
| `obj.foo` | `Minify` (Order 28) flips it back — but only while the key is still a plain valid-identifier string | the same matchers, which is why both spellings are accepted |

**It is deliberately not reversed, and that is settled rather than pending.** The site census
reads a large count against a `.src.js` baseline of zero — so every one is encoder residue
rather than authored code, which is what makes the count look worth acting on. The byte
census is what settles it: three characters per site, a low single-digit percentage of
decoded output, and no correctness dimension at all, since `obj["foo"]` and `obj.foo` are the
same expression. The site census counts computed string-key member reads, split by whether
the key is a valid identifier; a second pass applies the reversal in memory to turn that into
a byte delta. Both are static reads of decoded output, no decode run
([probes.md](../../probes.md)).
**Re-opening this needs a new argument, not a fresh count** — the site count alone was
what put it on a worklist once, and measuring it is what took it back off.

**If it were ever reversed it could only run last, which is a structural constraint rather
than a preference.** Rewriting the spelling earlier changes what those matchers key on
— [encoder-decoder-method.md](../../../encoder-decoder-method.md) W1/W5 with one of our own
passes as the agent, which is exactly the failure mode W5 describes. A terminal pass over
finished output cannot affect any of them, and equally cannot unblock anything: nothing in
this pipeline waits on this shape.

**This doc used to claim `Minify` mostly self-heals it, and measurement disproves that.** The
reasoning was that Minify's own `a["key"] → a.key` rewrite (Order 28, see
[minify.md](../../../js-confuser/transforms/minify.md)) flips the access back whenever the key
is still a plain valid-identifier string. Under `high` it almost never is: StringConcealing
(Order 17) has already replaced the key with a call by the time Minify runs, so Minify sees
nothing it can rewrite, and our own string layer only resolves it back to a StringLiteral long
after. Self-healing is the exception under a string-concealing preset, not the rule — the
surviving population is the whole population.

## 5. Known Gaps

**Two of Preparation's five normalizations have no decoder and are not self-healed by anything
later in the encoder's own pipeline either.** Both are unconditional residue: Preparation is
Order 0, so nothing in this project is blocked on them, but nothing removes them and they land
in every decoded file that contains the construct.

- **Template literals → string concatenation** and **regex literals → `new RegExp(...)`
  calls** are never reversed by anything in this codebase (checked: no
  `TemplateLiteral`-reconstruction or `RegExp`-literal-reconstruction visitor exists anywhere
  under `decoder/decode-js/src`).
- **Their size is unmeasured, and measuring it is not worth a corpus re-freeze.** The reason
  it is unmeasured is the instrument, not the decoder: the corpus contains **zero** of either
  construct in its `.src.js` sources, so both read zero in decoded output for want of
  input, not for want of residue
  ([encoder-decoder-method.md](../../../encoder-decoder-method.md) S5 — verify the denominator
  before reading a zero). Getting a number needs the corpus re-frozen, which voids every
  baseline figure measured against the current one. **That trade was declined:** the byte cost
  of a construct nobody is blocked on does not buy back a whole set of A/B baselines. Anyone
  re-freezing for another reason gets the measurement for free — the corpus builds from
  committed fixture sources and the `high-template-regex` source is already among them.
- **Their behaviour under decode is pinned even though their size is not.** The
  `high-template-regex` fixture ([tests.md](../../tests.md)) is the only committed sample
  carrying either, and it holds that both survive *intact* — the regex pattern source and
  flags round-trip, and the concatenation is folded rather than left in pieces. So a
  regression in handling is caught; only the byte cost is unknown.

**A gap being genuine is not an argument that it blocks anything.** Which of these gets done,
and when, is a priority decision rather than something to assume in either direction
([encoder-decoder-method.md](../../../encoder-decoder-method.md) T1). The member-access item
that used to sit here is the worked example, and it is now item 4: real, measured, attributable
entirely to the encoder, and still not worth doing — recording that judgement is what lets it
be made once rather than re-litigated from a fresh site count.

## Source

No dedicated visitor file. None of Preparation's three concerns is currently addressed by
anything in `decoder/decode-js`.

## Fixtures

None, and none would pass — see item 5 for what each unaddressed concern would need.
