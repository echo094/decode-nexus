# decode-nexus — Unified Skill Hub

All operational expertise, AST transformation rules, and submodule interactions are modularized into skill packages inside `skills/`.

## Universal Non-Negotiables
- **Read-Only Reference:** Code inside any git submodule (currently
  `encoder/javascript-obfuscator`, `encoder/js-confuser`, `decoder/decode-js`) is for
  reading AST patterns only — never alter it.
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

## Active Skill Directory
