# Lock / Integrity / Tamper Protection

Source: `transforms/lock/lock.ts`, `transforms/lock/integrity.ts`

Upstream docs: [`docs/Countermeasures.md`](../../../encoder/js-confuser/docs/Countermeasures.md),
[`docs/Integrity.md`](../../../encoder/js-confuser/docs/Integrity.md),
[`docs/TamperProtection.md`](../../../encoder/js-confuser/docs/TamperProtection.md)

Optional (off by default in all three built-in presets) — date/domain locks,
self-defending `toString()` checks, `debugger;` anti-debug statements, native-function
`toString()` tamper checks (gates `getGlobal`/RGF eval), and per-function body-hash
integrity checks that re-hash the function source at call time and branch to
`countermeasures()` on mismatch. The hash algorithm (`cyrb53`) is cataloged in
[integrity-template.md](../templates/integrity-template.md); the native-function
`toString()` check and strict-mode detector are in
[tamper-protection-templates.md](../templates/tamper-protection-templates.md).
