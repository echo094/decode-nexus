# decode-nexus

A **specification hub** for JavaScript obfuscation and deobfuscation: it carries no
engine code of its own. The tools live as git submodules, pinned to exact commits, and
what this repository actually maintains is a set of *skill packages* — structured,
source-cited references describing what each obfuscator emits and how each decoder
reverses it, written to be read by an AI coding agent and a human alike.

## What it's for

- **Recovering source you no longer have.** When the original is gone and only the
  obfuscated build survives, decoding gets you back to readable, maintainable code.
  Expect an *equivalent*, not the original: identifier names and comments are destroyed
  by obfuscation rather than encoded, so no decoder can return them. Everything
  else — control flow, string literals, program structure — is recoverable.
- **Getting a shippable baseline back.** Obfuscation multiplies code size, and the
  multiple is large. If the obfuscated bundle is the only artifact you have, decoding
  recovers a baseline you can minify normally instead of shipping the obfuscated one.
- **Analyzing hostile code.** Skimmers, malicious npm packages, and phishing kits are
  delivered obfuscated as a matter of course; reading them starts with undoing that.
- **Testing your own obfuscator config.** Obfuscate, decode, and measure with this
  repository's decode-quality signals how much protection the settings actually bought.

Intended for code you own or are authorized to analyze.

## Goals

What the project is built toward — directions the skill packages are converging on, not
finished capabilities:

- **Agent-driven deobfuscation.** A provider-agnostic skill architecture any AI coding
  agent can load, so a decode runs as a multi-pass analysis guided by domain judgment
  rather than a fixed script.
- **A domain-specific knowledge base.** Program-analysis expertise written down as
  structured skills instead of held in an expert's head: quantitative decode-quality
  metrics, a taxonomy of the popular obfuscation algorithms, and troubleshooting
  protocols indexed by symptom.
- **Baseline mechanics research.** AST generation mechanics isolated from each reference
  obfuscator's own source, so every documented shape is verified behavior rather than
  inferred.
- **Transferable deduction.** Unknown encoder variants approached through their
  structural AST characteristics — decoded case by case with custom scripts first, then
  generalized into a reusable plugin once enough samples accumulate.

## Getting started

```sh
git clone --recurse-submodules https://github.com/echo094/decode-nexus.git
cd decode-nexus

# already cloned without submodules?
git submodule update --init --recursive

# which commit each tool is pinned to
git submodule status
```

The pinned commit is the whole point: every source permalink in a skill package targets
the same SHA the submodule names, so a citation and a `git submodule update` always show
the same tree. Nothing is built or installed at the hub level — build and run each
submodule per its own README.

### Loading the skills into an agent

The packages are plain Markdown with no agent-specific syntax, so any coding agent can
read them. Only the entry point differs:

- **Claude Code** picks up [`CLAUDE.md`](CLAUDE.md) automatically when started from the
  repository root, and that file chains straight to `SKILL.md`.
- **Any other agent** — point it at [`SKILL.md`](SKILL.md) yourself, as the first thing
  it reads. It carries the standing rules and indexes every package.

Then load the *root* of the package for the tool at hand —
[`skills/decode-js/decode-js.md`](skills/decode-js/decode-js.md) or
[`skills/js-confuser/js-confuser.md`](skills/js-confuser/js-confuser.md) — rather than the
whole tree. Each root indexes its own supporting docs under a **Skill Layout** section, so
a per-transform or per-visitor file gets pulled in only when the work actually reaches it.

## Submodules

| Path | Upstream | Role |
| --- | --- | --- |
| `encoder/javascript-obfuscator` | [javascript-obfuscator/javascript-obfuscator](https://github.com/javascript-obfuscator/javascript-obfuscator) | Obfuscator — read-only |
| `encoder/js-confuser` | [MichaelXF/js-confuser](https://github.com/MichaelXF/js-confuser) | Obfuscator — read-only |
| `decoder/decode-js` | [echo094/decode-js](https://github.com/echo094/decode-js) | Deobfuscator — editable |

Each submodule keeps its own license; this repository's terms cover the hub's own
documentation only.

## Contributing

[`SKILL.md`](SKILL.md) is the single source for how work is done here — standing rules,
commit conventions, and the submodule pin-bump procedure. Read it before changing
anything.

## License

[CC BY-SA 4.0](LICENSE).
