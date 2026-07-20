# Claude Bootloader

See @SKILL.md for complete repository skills and operational directives.

## Commit Identity

A commit's author and any `Signed-off-by` trailer must come only from the `user.name` /
`user.email` set in the `git config` active in the repository being committed to — never
from the assistant's session or environment context. The agent must sign every commit it
authors (`git commit -s`).
