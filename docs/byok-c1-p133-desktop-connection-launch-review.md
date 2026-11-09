# Nayeon v1 — P133: explicit desktop Connection-page local BYOK entry

9 November 2026 | OM v2.1 | BYOK C1 user-scope first release | **DRAFT, NOT RELEASED**

## Direct baseline / approved intent

Direct parent P132 exact `29c6065c3e04d7af03d97496259e113341994c49`, first offline current-user Windows Credential Manager setup with 474/474 prior native focused and 117/117 Python focused tests on Windows (synthetic / fake native only).

The user's approved narrower C1 objective is a **usable local Windows user-scoped key setup** without privileged key-writing service or provider validation. P133 integrates the previously standalone P132 setup as an **explicit button on the existing main desktop Connection page**, without starting a credential backend when Nayeon launches or navigates.

## Product-facing operation

1. Start Nayeon in its normal offline mode. Default `__main__.py` remains untouched and imports NO local BYOK/WinCred.
2. Open **Connection** page. Existing `Manage provider (offline preview)` button and synthetic-first connection journey stay unmodified in meaning.
3. A distinct button **Open local key setup (offline, not connected)** is visible. Only a human-clicked callback from the CURRENT Connection pane is allowed to attempt an external child-process launch.
4. The trusted parent loads `LocalByokLaunchBridge` **lazily on that click**, verifies the current view/token/generation, refuses pending reply workers, stale pages, old synthetic preview child, closed/offline root, duplicate opening or non-creator-thread callback.
5. A fixed, separately launched **current-user** Python module `python -B -m nayeon.desktop_alpha.local_byok_window` owns the P132 masked-entry, manual Review → Confirm → Approve dialog. This is a developer/source launch, **not a signed executable or a production distribution**.
6. Launch command is a fixed Python `[sys.executable, "-B", "-m", "nayeon.desktop_alpha.local_byok_window"]` list with `shell=False`, bounded source-root working directory, no user-supplied argv or arbitrary file path; standard input/output/error redirected to OS null handles. Only a narrow allowlist of Windows operating/profile environment variables crosses into the child — no ambient `OPENAI_API_KEY`, provider credentials, Python injection variables or Nayeon runtime secrets.
7. One active child per parent UI instance: pressing the button again sees the existing child via `poll()` and refuses duplicate spawning. Unknown child process identity or status refuses further launch. A normally exited child may be started again only by another deliberate click. Parent navigation/shutdown does NOT force-kill the separate user-owned credential window mid-write. This is intentional, documented lifecycle.
8. Main app Connection page only displays fixed non-secret status **"separate local key setup requested"** or unavailable/already-running. It never infers connection, key validity, stored blob content, provider entitlement or proof of human consent from a child PID. No automatic provider C2 call or startup credential access.

## Security model and candid limitations

- Current user WinCred is *not* high-assurance signed service custody; malware/another process running as that user can read/write generic credentials, and `sys.executable`/source installation path can be substituted under an attacker-controlled user profile. No signed binary identity, TPM, protected event journal or one-use service grant is claimed.
- A fixed Python module path and minimal environment reduce accidental command/secret injection but are **not** an OS publisher-signed executable, firmware/driver attestation or cryptographic human-presence proof. Packaged/frozen builds are deliberately refused by the source-mode launcher until a reviewed signed launcher exists.
- The child may exist after the main UI navigates or exits; avoid killing it while Credential Manager could be updating. App restart may permit another child instance and the P132 cooperative Windows mutex only serialises participating same-session processes; this is not a durable cross-process approval record.
- P132 itself has process-local uncertainty, not persistent crash journal; only slot presence (never exact secret content) is re-observed after an attempt, and external same-user writers/ABA are not proven safe.
- No real API key or live provider validation performed. **Do not use this draft setup with a real key on Kristian until independent security review, genuine WinCred synthetic acceptance, signed packaging/SAC and triple full product regressions.**
- The old privileged service G0–G6 holds and original P96 check-to-effect race remain OPEN. The historical P124 handle-transfer authorship gap remains. P133 is an **alternative reduced user-account threat model**, not a silent repair or merge of the high-assurance production path.

## Source scope, CI and historical integrity

P133 modifies only the two main desktop UI/navigation source files `nayeon/desktop_alpha/application.py`, `nayeon/desktop_alpha/workspace_window.py`, and ADDS a launch bridge, Windows GUI/process fake-only test module, explicit P133 source-governance migration test, CI workflow and this document. Exactly **SEVEN paths** compared with P132.

The P132 actual credential controller, local Tk key-entry window, fixed WinCred backend, all prior P132 tests, legacy Phase8/Phase10/P76/P96 security seals and historical branches remain byte-identical.

New P133 acceptance uses Windows-hosted Tk real callback exercises but fakes **all** `subprocess.Popen` calls: no unattended second process, real key or native WinCred mutation during CI. It proves explicit-click-only, no import/startup child, no duplicate spawn, fixed argv, minimal env, stale callback and foreign-thread refusal, previously existing preview unchanged, new page navigation, source allowlist and non-secret status.

Run the prior P132 **36 functional tests** unchanged (P132's five exact-branch governance tests are retained on their historical branch, NOT falsely marked green on P133). Run the prior **76 historical WindowsCredentialBackend/first-run Tk/host/lifecycle functional tests**, P133 security migration and UI tests, PLUS **all 474** frozen native Windows focused security tests. Formal P133 scope governance is tested separately and MUST pass. None of these focused suites are the three mandatory OM v2.1 full product Windows regressions.

No real CredWrite/CredDelete/TPM/HKLM, privileged service install, Smart App Control change, unsigned binary launched on Kristian, historical blocked P62 action, GitHub merge/tag/release or Google Drive master/dashboard nonrelease update.

## Next narrower-release steps

1. Qualified independent user-scope threat/governance review, including process launching, same-user malware, environment, symlink/source identity and in-memory key handling.
2. Actual **synthetic-only** Windows Credential Manager lifecycle under a separately authorised disposable test profile and signed Windows acceptance environment (not Kristian's real user credential slot).
3. Signed packaged launcher and verified Windows Smart App Control acceptance. For production, replace source-mode `sys.executable -m` with a pinned signed packaging route, not a hidden Python bypass.
4. Three complete Windows product regressions + OS restart and ambiguous failure recovery tests, independent release approval.
5. Only after real release: update the original master Google Drive workbook **FIRST**, then the dashboard.

**P133 TARGET = genuine app navigation integration review and hosted Windows fake-only tests. BYOK C1 USER-SCOPED FIRST RELEASE HOLD.**
