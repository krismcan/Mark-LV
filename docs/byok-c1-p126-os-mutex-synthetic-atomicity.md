# BYOK C1 P126 — Real Windows interprocess custody Mutex with synthetic fixed attempt, NOT a G2 production fix

Date: 9 November 2026 | OM v2.1 | direct exact P125 baseline `2b23a5d703be098cff5a1de24a9ef9c6bf883c81`

## Nonduplication and motivation

Original frozen P49/P61 `PendingCustodyTransaction.Apply()` has the P96-proven revocation/credential-effect check-to-call race and cannot be enabled. P109 modelled one-use decision under a candidate service-owned **in-process** lock. P110 already modelled a **fixed operation-bound synthetic integer effect** under the SAME candidate in-process lock; it has **no native effect and no durable witness** and must NOT be reused as production authority.

P126 specifically adds the **different missing native OS primitive evidence**: genuine **Windows process-shared named `Mutex` acquisition and full in-flight tenure**, including independent Windows processes contending for one lease and Windows kernel abandoned-owner semantics. It does not modify P110 or P49 and cannot claim closure of G2. It is isolated from production credential operations.

## Source implementation

`native_c1_g2_review/WindowsG2SyntheticMutexCustody.cs` is compilation-prohibited unless **BOTH** `C1_REVIEW_ISOLATED_ASSEMBLY` AND `C1_SYNTHETIC_TEST` are explicitly defined. It accepts only unique per-test `Local\\Nayeon-C1-P126-<32 lowercase GUID chars>` mutex names, never the real LocalSystem protected custody mutex or a production target. No protected ACL or user identity proof is claimed; the test name can be precreated by the same user and is NOT an authority.

The review actor holds its single-owner C# monitor over a synthetic fixed operation decision, acquires a real Windows named kernel mutex on the same thread, increments exactly ONE **local integer** as the fake effect under BOTH locks, and releases the native OS mutex from the acquiring thread. Revocation/Stop/Fault lock the same monitor. Any observed fake effect yields only `RecoveryRequired`; no `StoredUnverified` or approved result is possible, and state cannot rearm. Earlier revoke prevents even the integer; late revoke is recorded as too late, not a retroactive cancellation.

A different OS process can hold the exact named kernel mutex; the candidate sees contention and refuses/sets sticky recovery with **zero fake effects**. When a child process exits without releasing its mutex, .NET throws `AbandonedMutexException` *after granting ownership*. P126 catches it, marks sticky recovery, and releases that acquired mutex on the same thread, without creating a fake effect. Unexpected callbacks and arbitrary user-supplied effects are prohibited: no effect interface, injected callback, real key material, WinCred, HKLM, journal, signer, approval or privileged service exists.

## Native test plan

20 new real hosted Windows unprivileged x64 cases: reject production/invalid names; ordinary no-authority state; SAVE/REPLACE/acknowledged DELETE fake integer once; invalid operation and acknowledgment; wrong operation burns admission; before-effect revocation, stop and fault; terminal single-use; 12-thread single-win contention; revoke racing with an in-flight fake OS lease; real independent child **holds** OS named mutex so candidate cannot fake-dispatch; child **abandons** OS mutex by exiting without release, with sticky recovery/zero fake markers; independent child PROBES that an OS mutex remains busy while a different thread's fake effect holds it and is released after completion; simulated unknown result; original P49/P112 no-effect guards. All execution is on an unprivileged GitHub-hosted Windows runner, never unsigned binary on Kristian.

Existing **337** focused native Windows cases from P125/P124/P123/P122/P121/P120/P118/P117/P116/P115/P114/P113/P112/P110/P109/P108/P106/P99/P96 must run unchanged. Expected total: **357 = 20 + 337** genuine native focused cases. Preserve frozen original P49 source SHA256 pins, original P96 15-case race comparator (must continue to reproduce), P112 candidate no-effect gates and correct prior source scope. No full product regression or qualified external review claimed.

## Explicit limitations and remaining G2 production design

This is NOT a secure production native custody mutex: its name is arbitrary per-test, its ACL is not independently protected, there is no cross-boot service identity or exclusive installer owner, no protected durable intent or antirollback journal, no actual native WinCred target, no signed consent/user presence, no real credential success and no crash-safe issuance or recovery witness. A bounded test mutex wait and synthetic integer are NOT production credential-effect proof.

P110's C# monitor and P126's OS mutex are *separate isolated candidate experiments*, not yet a combined, signed reviewed effect-capable transaction actor. To close G2, qualified independent review must first approve an actual service-owned final dispatch/consent revocation barrier, audited OS custody mutex ownership/ACL, protected G3 journal+HKLM historical anchor, one-use service-owned G1 consent source and a separately authorised G4 fixed-target real WinCred adapter. Legacy P96 coordinator must remain disabled; no patch may simply flip the original G2 guard.

G0 qualified native security reviewer OPEN. G1 approved signed installed consent/UI, actual trusted human presence, cryptographically bound operation and durable one-use grant OPEN. G2 original P96 revocation-to-effect check race OPEN. G3 protected antirollback and crash recovery OPEN. G4 privileged WinCred lifecycle pending-only real validation OPEN. G5 production signing and Kristian Smart App Control acceptance OPEN. G6 3 complete Windows product regressions, independent release, and original Google Drive master workbook-first/dashboard sync OPEN.

**P126 SYNTHETIC-ONLY NATIVE TEST. BYOK C1 PRODUCTION RELEASE HOLD.**

Reference: Microsoft `Mutex` / `AbandonedMutexException` API semantics (learn.microsoft.com/dotnet/standard/threading/mutexes).
