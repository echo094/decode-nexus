# Git Workflow

How to commit, and how to move a submodule's pin. Read it before committing; [`SKILL.md`](../SKILL.md#gates)'s commit
gate 7 is the short form.

## Before every commit

- **Commit compliance:** follow Commit Conventions below in full; format, type, scope and sign-off
  are not optional.
- **Language check:** run `grep -nP '[^\x00-\x7F]' <changed files>` for [English Only](../SKILL.md#hub-rules) and read what
  it reports. It also flags the typographic characters (`…`, `—`, `→`) both trees use throughout,
  which are not a language violation.
- **Read budget:** if the change touches `SKILL.md`, a bootloader or `checkpoint.md`, run
  `wc -w SKILL.md AGENTS.md checkpoint.md` and keep `SKILL.md` within 1,500 words and the total
  within 5,000 ([`SKILL.md` gate 2](../SKILL.md#gates)).
- **Link verification:** verify links; skill docs cross-reference each other constantly and renames
  drift them silently. When a change documents a Later Stages entry by citing the decoder that
  explains it, grep the touched encoder docs for `decode-js`: a stray cross-package link is easy to
  leave by reflex, and the encoder-side fact must stand without it.

- **Branch inside the editable submodule first.** Create the branch in that submodule's own
  repository and commit every change on it there. Never hold submodule work on a hub branch,
  never commit it in the hub, never commit from a detached HEAD.

## Commit Conventions

Use [Conventional Commits](https://www.conventionalcommits.org/), scoped by skill:

```
type(scope): subject
```

- **type:** one of the following — this list is closed; a commit using any other type
  is non-compliant, and adding a new type here is required before it can be used:
  - `docs` — skill-file writing/editing
  - `fix` — correcting a decoder/encoder behavior
  - `feat` — new decoder capability
  - `chore` — repo/hub maintenance, `.gitmodules`, tooling
  - `refactor` — restructuring without behavior change
  - `test` — adding or changing tests, fixtures, or the test harness
  - `build` — automated dependency bumps (e.g. Dependabot); platform-generated commit
    style, not for manual use
- **scope:** the skill/submodule the commit belongs to — e.g. `js-confuser`,
  `decode-js`, `javascript-obfuscator` — or `hub` for hub-wide files (`SKILL.md`, bootloaders, hub studies, governance docs).
  - When the commit is made inside a submodule (not the hub), that submodule's own
    skill entry file (e.g. `skills/decode-js/decode-js.md`) may define a more
    detailed, module-level scope convention for that project specifically — check
    there first if one exists.
  - One scope per commit; if a change spans multiple skills, split the commit (this
    also keeps commits aligned with [Project Independence](doc-conventions.md#project-boundaries)).
- **subject:** imperative, no trailing period, ~72 cols.
- **One concern per commit.** Don't bundle an unrelated pre-existing fix discovered in passing
  into a feature's own commit — give it its own, so neither can be reverted without the other.
- **Don't fix what a planned rewrite redoes.** Where a history rebuild is already scheduled over a
  range, a defect inside it — a missing sign-off, a non-conventional subject — is recorded for the
  rebuild to absorb rather than patched in place: the patch is work the rebuild repeats, and it
  adds a commit the rebuild then has to destroy.
- Body (optional): explain why, not what.
- Footer: `Signed-off-by: Name <email>` is **required** (use `git commit -s`); issue
  refs are optional.
- **Commit identity.** The agent **must sign every commit it authors** (`git commit -s`).
  The author and any `Signed-off-by` trailer come only from the `user.name` /
  `user.email` set in the `git config` active in the repository being committed to —
  never from the agent's session or environment context.

Example:
```
docs(js-confuser): document control-flow-flattening transform

Signed-off-by: Jane Doe <jane@example.com>
```

## Updating a Submodule's Commit Pin

The bump is the *last* step, gated on everything below ([`SKILL.md` gate 4](../SKILL.md#gates)) — not a first step that gets reconciled afterward:

1. **Diff the as-is pin against the to-be pin before touching anything.** Read the
   actual upstream changes between the two SHAs — a pin bump is a reviewed decision, not
   a blind fast-forward.
2. **Check the corresponding skill package for drift.** Anything the diff touches that
   the docs describe — transform logic, plugin behavior, file/line references — needs
   re-verifying against the new commit.
3. **Follow up the decoder before moving the pin.** Run it against real output built from
   the new commit; fix whatever the diff broke, and re-verify anything the diff touched.
   Only once the decoder holds against the new commit is the pin allowed to move — this
   is what makes step 4 a description of already-verified behavior rather than a
   prediction of it.
4. **Decide whether the new commit is still the same era, and never erase the old
   behavior.** Samples already obfuscated/encoded in the wild were produced by the
   *previous* version's algorithm, so its description must stay on record alongside the
   new one, never replaced. Which of the two happened decides the work:
   - **Same era** (emitted shape unchanged) — nothing to add. The era's recorded SHA may
     advance to the new commit, but only on the strength of step 3's re-verification;
     absent that it stays where it was, since the SHA names the commit that proved the
     claims, not the newest one available.
   - **New era** (emitted shape changed) — open a new registry row and leave the previous
     row untouched, so both remain describable. The mechanics, and when a registry is
     required at all, are in [doc-conventions.md](doc-conventions.md)'s
     "Documenting Multiple Eras."
5. **Land the pin bump last, in its own commit.** It lands in the hub repo as
   `chore(hub)` (stage only the submodule gitlink); any decoder fixes from step 3 and any
   doc updates from step 4 are their own commits, scoped to their own submodule, and land
   *before* it — not "follow" after.
