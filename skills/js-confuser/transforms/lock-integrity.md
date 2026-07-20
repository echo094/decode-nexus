# Lock / Integrity / Tamper Protection

Source: `transforms/lock/lock.ts`, `transforms/lock/integrity.ts`

Optional (off by default in all three built-in presets) — date/domain locks,
self-defending `toString()` checks, `debugger;` anti-debug statements, native-function
`toString()` tamper checks (gates `getGlobal`/RGF eval), and per-function body-hash
integrity checks that re-hash the function source at call time and branch to
`countermeasures()` on mismatch.
