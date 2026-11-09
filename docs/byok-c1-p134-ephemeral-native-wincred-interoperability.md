# Nayeon v1 — P134 genuine native Windows Credential Manager interoperability (synthetic only)

**9 November 2026 | OM v2.1 | USER-SCOPED RELEASE HOLD | DRAFT UNMERGED**

Direct exact P133 parent `e79b8c12168cd5869cdb2d7feea6656baf4c0624`. The user selected narrower BYOK C1: current-user Windows Generic Credential Manager with explicit human-triggered local UI, no privileged service and no provider validation until C2. P133 already integrated the separate offline setup into Nayeon's desktop Connection page with explicit click and no automatic startup access.

## What P134 adds — first real operating-system Credential Manager interoperability

Only a new **native synthetic Windows test harness**, exact source-scope migration test, hosted CI workflow and this report (FOUR added paths). There are **zero production source changes**. Reuse the historical, source-pinned `WindowsCredentialBackend` and its real Win32 `CredWriteW`, `CredReadW`, `CredDeleteW` adapter without changes.

P134 tests genuine Windows APIs on **only a disposable GitHub-hosted Windows runner current-user profile**, never on Kristian, not another user account and not a real OpenAI credential. Every native test:
- starts with a new `uuid.uuid4().hex` identity bound to `SecretIdentifier("p134.synthetic.<32-lowercase-hex>")`, which resolves to the exact distinct target `nayeon-v1/secret/p134.synthetic.<uuid>`. This is explicitly NOT the production `nayeon-v1/secret/openai.api_key`.
- verifies the unique test target is ABSENT before any write. If it already exists, tests fail WITHOUT touching that target.
- uses only fixed nonsecret strings `P134-SYNTHETIC-NONKEY-...`; **NO real API key** or provider call, import, network or model consumer.
- tests direct OS native write/read/presence, replacement in the same target, deletion/absence, UTF-8 characters, max blob rejection before effect and native cleanup.
- launches a separate Windows child Python process ONLY for controlled cross-process observation of that random synthetic target; passes only the nonsecret test ID and version in argv, never a key value; restricts child environment and forbids provider API secret variables.
- registers a `finally`/unittest cleanup that deletes the freshly allocated test target and re-verifies its absence even after a test failure. The runner VM/account itself is disposable and discarded after the GitHub Actions job.

Native tests must refuse non-Windows environments, missing `GITHUB_ACTIONS=true`, unexpected `GITHUB_REPOSITORY`, missing disposable `RUNNER_TEMP` or absent exact opt-in environment `P134_NATIVE_WINCRED_EPHEMERAL_AUTH=EPHEMERAL_GITHUB_WINDOWS_ONLY`. That flag gates **test execution only**, not user authority or credential operations in production. Native test execution and cleanup is permitted ONLY on disposable GitHub-hosted Windows, **NOT Kristian**. Normal default app, current-user setup window and launch bridge remain byte-identical.

12 genuine WinCred Python tests target the synthetic random slot, plus six P134 governance/scope tests. All 474 prior hosted Windows native security-focused tests and 154 prior P133/P132/P8 Python functional tests remain in the P133 workflow, unchanged. Historical exact-branch scope tests remain untouched and are never falsely declared successful on P134.

## What this genuinely verifies, and what it cannot prove

Passing these tests would establish that the existing Python ctypes WinCred adapter interoperates with actual Windows Generic Credential storage in a disposable login profile; the saved nonsecret value is visible in a different process of that user and replace/delete semantics behave as expected. It would NOT validate a human API key, signed publisher or production packaging, Smart App Control acceptance, cross-account protection, malicious same-user process defence, credential durability across real power loss, or reliable repair after a crash.

Windows Generic Credential `CRED_PERSIST_LOCAL_MACHINE` means a credential for the CURRENT logon/user context on that machine; it does **not** make a LocalSystem protected service or independently keyed vault. A transient direct `CredReadW` native buffer can contain plaintext in process memory; the existing adapter copies and frees it. Tests use fake nonkeys and no key content should be emitted into GitHub logs.

No single test may enumerate user credentials or read/write the production `openai.api_key` target. There is no credential migration, provider connection, system registry, HKLM, TPM, service install, user secret on Kristian, Smart App Control change or signed packaging.

## Review and release dependencies

- Original high-assurance privileged BYOK C1 G0–G6 remain OPEN, including P96 original check/effect race and P124 transferred-pipe-handle author gap. These legacy effect paths are NOT used in reduced current-user feature.
- U1 independent reviewer acceptance for current-user, same-user-malware and source-launch risk; separate signoff of source-scope migration, true human review/click and in-memory handling.
- U2 genuine Windows native OS test on disposable random synthetic credential slot; review exact test evidence/results; no old key touched.
- U3 user-experience: P133 Connection-page explicit launch exists but is still developer source mode and not a pinned/signed production package.
- U4 signed packaging, verification on supported Windows + Kristian Smart App Control, no unsigned exe or native synthetic test on Kristian without specific separate signed acceptance.
- U5 three full Windows PRODUCT regressions, cross-process/crash/unknown outcome review, exact release gates and independent approval.
- U6 when a REAL production milestone releases, reconcile original Google Drive master workbook FIRST and then dashboard. Do NOT update on draft PR.

**P134 test code is a separate native OS interoperability proof, not a signed package, independent reviewer signoff, finished security model or permission to enter real API credentials. USER-SCOPED RELEASE HOLD.**
