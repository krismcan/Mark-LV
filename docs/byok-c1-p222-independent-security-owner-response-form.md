# P222 — Independent Windows SEC-03 / SEC-04 Decision Response Form

**This template is NOT itself a signed approval. It must be completed by real, independent qualified people with verifiable authority.**

Project: Nayeon v1 / Mark-LII · BYOK C1 · OM v2.1
Baseline parent: 429694ca64b38a3957fab462d53afeddcdb298d2 (P221 unmerged)
Source under review: P222 draft branch byok-c1-p222-native-service-owner-architecture-and-security-decision-20261114
Primary design: docs/byok-c1-p222-single-native-service-owner-g0-r3-decision.md
Production C1: HOLD. Real keys: NO-GO. C2: NOT AUTHORISED.

## Identity and independence (mandatory)

- Reviewer legal name / organisation: **NOT ISSUED**
- Role and explicit Windows/credential/signing authority: **NOT ISSUED**
- Independent from implementation author? Evidence and conflicts: **NOT ISSUED**
- Review date, expiry and signed decision method: **NOT ISSUED**
- Exact source branch, SHA and independent verified source digest: **NOT ISSUED**
- Candidate signed binaries, complete dependency versions and SHA-256: **NOT BUILT**
- Target Windows edition/build, patch level and hardware: **NOT SELECTED**
- Approved disposable Windows VM ID/owner/operator/test purpose: **NOT AUTHORISED**

## SEC-03 — Service-account and protected-store owner

Select exactly one independently documented choice, then provide evidence:

- [ ] Qualified distinct least-privilege SCM service account and restricted service SID (specify literal identity; NT SERVICE name is only a proposal)
- [ ] Another reviewed service principal (explain why, exact rights, lifecycle and token)
- [ ] LocalSystem with explicitly documented necessity/risks (not a default)

Required explicit field values:
- SCM service logon account and SID type: **UNDECIDED**
- Actual service process token privileges / impersonation / logon profile / reboot semantics: **UNPROVEN**
- Approved service-only secret target (WinCred under real service principal / DPAPI CurrentUser protected file / alternative): **UNDECIDED**
- Exact ACL/SDDL and installed trusted identity: **UNPROVEN**
- User-profile and DPAPI CurrentUser availability under actual principal: **UNTESTED**
- Ordinary same-user P132 direct CredReadW / CredWriteW / CredDeleteW attempts against **new** target fail by OS enforcement: **UNTESTED**
- Machine-scope DPAPI rejected for cross-user confidentiality: **REQUIRED**
- Durable journal and independent monotonic history/rollback witness and backup/recovery: **UNDECIDED**
- Install, uninstall, service restart/profile loss, re-enrolment, user-vault retention and no silent migration: **UNDECIDED**
- Evidence log location, OS exit values, source/binary hashes: **ABSENT**

**SEC-03 signed verdict: HOLD / NOT ISSUED.**

## SEC-04 — Signed native service, Code Integrity, IPC and P96 consent owner

Select and attest real mechanisms; do not infer from source or CI:

- Publisher/installer signing keys and independently verified certificate chain: **UNISSUED**
- Windows Code Integrity / WDAC / App Control policy ID, actual UMCI enforcement and complete EXE/DLL/script/.NET dependency scope: **NOT REVIEWED**
- Code Integrity signed loaded-image identity and file-ID/rename-race resistance: **UNTESTED**
- Authenticated named-pipe server/client OS token, Windows session, integrity level, signed UI broker and user presence: **UNTESTED**
- Durable one-use operation + target + candidate + session + version consent and anti-replay: **UNIMPLEMENTED**
- One actual service-owned final effect actor (no original P96 callbacks), same in-process revoke/stop/fault/dispatch lock and same native OS mutex tenure: **UNIMPLEMENTED**
- Durable IN_FLIGHT and physically distinct protected anchor before one native pending-only effect; no retry after uncertain effect: **UNIMPLEMENTED**
- Original P96 positive successor test requires revocation winning BEFORE dispatch => 0 effect; dispatch winning => explicitly TOO_LATE/RECOVERY until physical verification: **NOT TESTED**
- Separate signed package excludes old P132/P133 interactive-user effect route; OS store isolation tested against it: **NOT BUILT**
- Stop/watchdog/crash/reboot, code-signature revocation, update and rollback: **UNREVIEWED**
- All tests conducted on approved disposable VM with synthetic non-secret values only: **NOT AUTHORISED**

**SEC-04 signed verdict: HOLD / NOT ISSUED.**

## Other independent gates

- GOV-01 independent threat model, same-user/admin/kernel scope: **UNISSUED**
- GOV-02 legacy credential retention, re-enrolment and delete policy: **UNISSUED**
- REL-05 independent security review of G0–G6 / R0–R4 after implementation: **UNISSUED**
- REL-06 3/3 full unfiltered native Windows product regressions: **0/3**
- REL-07 P0–P5 production install/change/rollback acceptance: **UNISSUED**

## No-go conditions / response handling

1. A security reviewer must actually identify themselves and document authority outside author-only code changes. A GitHub username, draft PR, AI-authored assessment, local test pass or unchecked checkbox does not confer authority.
2. Do not copy real secrets, credentials, private keys, passwords, certificate private material or full user SIDs into a PR. Redact sensitive Windows configuration details; source/compiled-artifact hashes and broad policy options can be shared.
3. If reviewer disputes the account/store approach, record **REJECTED/ALTERNATIVE REQUIRED**, not a forced GO. If ownership/identity ambiguous, remain **HOLD**.
4. A positive SEC-03/SEC-04 signed decision authorises only its explicit scope (for example a no-secret disposable VM trial), never automatically real-key R0–R4 or production P0–P5.
5. Do not update the original macro-enabled Google Drive MASTER production release count for an unapproved architecture review; preserve originals and all historical evidence.

## Next authorised action

Receive and authenticate actual named SEC-03 and SEC-04 independent decisions. Only with authorised source, signer, store, disposable Windows VM and operator may a separate service-owned native actor proceed from architectural design to isolated implementation and fixed synthetic OS experiments.

Current disposition: G0–G6 OPEN, R0–R4 REAL-KEY NO-GO, P0–P5 PRODUCTION HOLD, external independent approvals 0/7, full product regressions 0/3, BYOK C2 NOT AUTHORISED.
