# decode-nexus — Unified Skill Hub

All operational expertise, AST transformation rules, and submodule interactions are modularized into skill packages inside `skills/`.

## Universal Non-Negotiables
- **Read-Only Encoders:** Code inside encoder submodules (currently
  `encoder/javascript-obfuscator`, `encoder/js-confuser`) is for reading AST patterns
  only — never alter it.
- **Editable Decoders:** Decoder submodules (currently `decoder/decode-js`) may be
  modified — linting, fixes, and new decode capabilities are allowed — subject to:
  - **Branch inside the submodule first.** Before any change to a decoder submodule,
    create a new branch *in that submodule's own repository*. Never create a branch in
    the hub repo to hold submodule work, and never commit submodule edits from a detached
    HEAD.
  - Every change follows the Commit Conventions below and is committed on that branch, in
    the submodule's own repository — never in the hub.
- **Project Independence:** Each skill package documents exactly one submodule, in
  isolation. Never cross-reference, assume, or depend on another project's code,
  coverage, or status — a skill file should read the same regardless of which other
  submodules exist in this repo. Cross-project observations belong in a separate note,
  not inside a single-project skill file.
- **Commit Compliance:** Every commit must follow the Commit Conventions section below
  in full — format, type, scope, and sign-off are not optional.

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
- **scope:** the skill/submodule the commit belongs to — e.g. `js-confuser`,
  `decode-js`, `javascript-obfuscator` — or `hub` for changes to this file itself.
  One scope per commit; if a change spans multiple skills, split the commit (this
  also keeps commits aligned with the Project Independence rule above).
- **subject:** imperative, no trailing period, ~72 cols.
- Body (optional): explain why, not what.
- Footer: `Signed-off-by: Name <email>` is **required** (use `git commit -s`); issue
  refs are optional.

Example:
```
docs(js-confuser): document control-flow-flattening transform

Signed-off-by: Jane Doe <jane@example.com>
```

## Studying a New Encoder/Decoder

When building a skill package for a new submodule, follow the process used for
`js-confuser` (see [js-confuser.md](skills/js-confuser/js-confuser.md) and its
supporting files as a worked example):

- **Verify against source, always.** Never document a mechanism from memory, naming
  conventions, or inference — read the actual file before writing a claim about it.
  If an earlier draft turns out wrong after reading the real source, correct it
  immediately rather than leaving a stale guess in place.
- **Go incrementally.** Explore and document one transform/module at a time instead of
  attempting the whole surface in one pass; let whoever is driving the session direct
  which piece to tackle next rather than front-running unrequested sections.
- **Keep the root file about the workflow, not the plumbing.** Name the package's root
  file after the skill itself (e.g. `js-confuser.md`), not the literal `SKILL.md` — a
  subfolder full of files all named `SKILL.md` becomes impossible to tell apart. That
  root file should cover only what's needed to understand the core encode/decode
  workflow and algorithm: the underlying parser/AST foundation, a verified source-tree
  layout, the pipeline/stage order, and a runtime execution-flow diagram. Move
  everything else — option/config surfaces, shared plugin APIs, constants, helper
  utilities, template/codegen engines, result types — into their own files once they'd
  otherwise bloat the root file, and index all of it from a "Skill Layout" section.
- **Mirror the source tree in supporting docs.** One file per source file for large
  helper folders (e.g. `utils/<name>.md`, `templates/<name>.md`), flat and distinctly
  named.
- **Summarize the test suite.** A `tests.md` covering the test framework, project/config
  structure, and directory breakdown pins down exact before/after behavior in a way
  prose can't, and gives readers somewhere to go when the docs need more precision than
  they provide.
- **Cross-reference upstream docs, but verify them too.** If the submodule ships its own
  `docs/`, link the matching page from the corresponding skill file — but confirm it
  still matches the pinned source commit first; note (don't silently drop) any upstream
  doc that describes a feature absent from the pinned version.
- **Verify links before every commit.** Skill docs cross-reference each other
  constantly; a quick broken-link/anchor check before committing catches drift from
  renames and reorganizations.
- **Respect Project Independence throughout** (see Universal Non-Negotiables above) — a
  new skill package should never compare against, assume, or link to another
  submodule's code or docs.

## Active Skill Directory

- [js-confuser](skills/js-confuser/js-confuser.md) — Transform-by-transform reference
  for the `encoder/js-confuser` obfuscator's AST patterns.
- [decode-js](skills/decode-js/decode-js.md) — Plugin-by-plugin reference for the
  `decoder/decode-js` deobfuscator's Babel + isolated-vm decode passes.
