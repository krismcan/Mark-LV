# Nayeon v1 / BYOK C1 P130 — G3 independent-history-witness architecture decision packet

**9 November 2026 | OM v2.1 | REVIEW ONLY | PRODUCTION RELEASE HOLD**

Direct verified starting point: P129 `10902771b06d3f78ec40f08f5093b089b6d5fa8f`.
Change scope: ONE new `native_c1_g3_review` source, ONE 24-case Windows native test driver, ONE hosted-Windows CI workflow, this reviewer packet. No mutation to original P49/P96, P109/P110/P126/P127, P128/P129, protected machine state or Google Drive master.

## Executive security decision

**A journal and a second ordinary file controlled by the same security principal are NOT two independent trusted records.** A SHA-256 chain can detect accidental damage or an *isolated* file rollback when an unaffected snapshot remains, but cannot prevent a same-user adversary from restoring BOTH an older journal and matching witness. Deletion followed by locally recreating the witness is also not secure enrollment.

P128/P129 already proved single-file bounded parsing, staged process exit and actual `Process.Kill` negative outcomes. P130 is **intentionally adversarial architectural evidence**, not a workaround: it adds a second **UNPROTECTED Windows TEMP file** to show exactly where a local independent history witness would help *if it were truly independent*, and where that assumption fails when both are controlled by one account.

### Scope of P130 source and native tests

`WindowsG3UnprotectedWitnessReview` requires BOTH `C1_REVIEW_ISOLATED_ASSEMBLY` and `C1_SYNTHETIC_TEST`. It reuses P128 random canonical 32-hex test ID, synthetic nonsecret 1–3 stage TEMP journal and `InspectUntrusted`. A separate `nayeon-c1-p130-<id>.witness` file stores a **70-byte** review record: exact versioned header, 1–3 stage count, SHA-256 of actual journal bytes, and a further **UNKEYED** SHA-256 check of the witness header. Both are disposable, same-user files. Both `FileStream.Flush(true)`/write-through and genuine cross-process exit are exercised. There is no secure service signer/ACL, HKLM/TPM, antirollback guarantee, independent authenticated enrollment, user presence, credential or real native WinCred call.

The reader returns `BothMissingUnsafe`, `JournalWithoutWitness`, `WitnessWithoutJournal`, `JournalMalformed`, `WitnessMalformed`, `HistoryMismatch`, or `ConsistentButUntrusted`. All branches have **permanently FALSE** protected journal, independent witness, antirollback, authentic human consent, durable grant, native effect and release-admission flags. A matching witness does not turn into any approval.

24 real Windows native cases: missing/partial and corrupted witness; earlier valid journal prefix replacement with witness intact (DETECTED), future journal with stale witness (DETECTED), corrupt journal and witness (DENIED), witness deletion/re-creation (untrusted reenrollment), **both journal and witness restored to old valid pair (UNDETECTABLE)**, genuine separate Windows child writing and exiting with matching files, second child advancing only journal and creating disagreement, frozen P49/P112 real-effect denials. Full inherited P129–P96 **416-case** focused suite must stay unchanged; target **440 named Windows native PASS** on unprivileged hosted Windows only. This is NOT the three required full product regressions.

## Proposed real PROTECTED production trust boundary — NOT IMPLEMENTED

The following is a design for a **qualified native Windows security reviewer** to approve or reject before privileged code, real keys, installer operations or protected writes. It is not equivalent to having implemented the controls.

### Roles and ownership

- The only transaction writer is a **signed, installed, publisher-pinned privileged service** with an explicit approved service SID and controlled installation/update chain. Neither an untrusted desktop UI nor a non-service process can directly edit journal, anchor or WinCred.
- The service owns a non-delegable per-request one-use admission decision under ONE revocation/Stop/Failure gate and an OS-level exclusive custody lease. The original P96 `StillCurrent()` then effect-call gap must NOT be re-enabled. P127 tests only show fake integer sequencing, not actual WinCred safety.
- A **separately protected journal** has a canonical exact-operation identity, service generation, historical service enrollment identity, monotonic sequence, prior-entry chain, attempt/witness markers, service signer/owner and clear fail-closed unknown/recovery state; secrecy and integrity are distinct requirements.
- An **independent historical witness** MUST be outside the journal writer's unilateral rollback domain. A second file, and potentially even a second HKLM value writable by the same LocalSystem service, is not automatically independent. External trusted monotonic counter, TPM NV monotonic / authenticated antirollback (where support and authorization permit), or independently administered append-only audit/witness service may be considered. Review must verify actual deployment support, lifecycle, escrow/backup, restoration, lost witness, factory reset and cloud/offline semantics. **No such mechanism is selected, provisioned or approved here.**
- Windows ACLs can reduce access by ordinary local users but cannot, by themselves, guarantee rollback resistance to compromised administrators or the writer itself. Service SID, owner, DACL/SACL and integrity-level checks must be verified on **opened handles** and repeated when relevant. Neither `GetNamedPipeClientProcessId` nor a relayed nonce authenticates actual human approval (P124/P125).
- A client consent window must prove exact transaction operation, target, signed installed mapped-image identity, genuine user physical action, monotonic grant consumption and protected service-owned binder before any irreversible native effect. G1 remains a separate blocking dependency.

### Proposed commit/recovery protocol (subject to review)

1. **Startup enrollment:** require qualified independently signed/protected historical witness; refuse missing, corrupt, rolled-back, duplicated, unexpected-future or unenrolled state. No automatic create, repair, resync or initial enrollment by the same caller that requested an effect.
2. **One writer and mutex:** hold a secured service-owned OS custody mutex through the accepted operation, protected intent, exact pending-only WinCred attempt, protected terminal recording and witness reconciliation. Service generation and request identity must be bound to the monotonic history anchor.
3. **Before effect:** admit only a fresh service-side consumed one-use operation grant with trusted signed human presence, same monitor as revoke/Stop. Write/flush `Prepared` and `EffectPossiblyStarted` *before* the native call, and anchor in a separately reviewed ordering. If anchoring fails or ordering is uncertain, do NOT issue effect. Do not trust an ordinary flushed file as proof of power-loss durability.
4. **Effect boundary:** invoke ONLY a reviewed fixed pending-only native WinCred adapter. The WinCred call's returned status is not an independent durable witness of what persisted; treat crash or ambiguous result as **recovery required** and prohibit replay. No callback or secondary writer.
5. **Terminal:** write a protected terminal record and advance the external authoritative witness in an order reviewed for all crash windows. Crash after effect but before terminal/witness update is UNKNOWN, never grant success. Stage names alone do not make native operation atomic.
6. **Reboot/recovery:** begin read-only, acquire verified service identity and history witness, compare journal/witness/WinCred pending-only observation, retain any possible-effect uncertainty, fail closed and require explicit approved recovery. Unexpected empty state or lost witness cannot be silently initialized; same-user restoration of both records must not be accepted as original history.
7. **Revocation:** before the single actor's irreversible effect decision, revocation prevents effect. After the possible-effect start, revocation cannot retroactively assert that a native write was cancelled. Preserve monotonic audit of unknown state and report conservatively.

### Required reviewer adversarial cases before any G3 closure

| Case | Must be addressed by production review |
|---|---|
| Missing journal or missing historical witness | Refuse, no automatic enrollment |
| Journal older than witness | Detect rollback, refuse |
| Witness older than journal | Refuse or independently reconcile under explicit authority; no automatic forward acceptance |
| Journal and witness BOTH rolled back together | **Must** be detectable through independent protected history; unprotected P130 specifically fails |
| Journal+anchor both deleted and re-created | Detect enrollment history loss; refuse until externally approved recovery |
| Non-atomic cross-media witness update | Every possible cut order mapped to denial/unknown or independently justified safe state |
| Power loss while storage flushes | Actual crash consistency testing required; Process.Kill is insufficient |
| Same-user injection, admin tampering, service binary replacement | Explicit attacker model and hardening; verify actual opened file and process/image provenance |
| Multiple service instances / token changes | Single writer by privileged OS lease, signed binary and service generation |
| WinCred effect returns success then process dies before terminal | Never retry blindly; original P96 race must stay disabled |
| Witness unavailable offline, TPM reset, backup restore | Fail closed; defined operator recovery, no implicit re-enrollment |
| Untrusted consent UI relays a challenge via duplicated pipe handle | G1 still OPEN — PID/session/nonce alone cannot approve |

## Review requests and authority boundary

The qualified reviewer must identify a defensible **independent trust root** for monotonic history, scope attacker/admin assumptions, sign/approve the exact protected-storage and service-owned WinCred dispatcher interfaces, and provide a crash-window/injection test plan. **Do not describe this architecture as independently reviewed or implement privileged journal/HKLM/TPM/WinCred mutations solely from a review-only PR.**

G0 qualified independent native Windows security review OPEN.
G1 actual signed installed mapped-image-bound human consent and durable one-use grant OPEN.
G2 original P96 revocation/effect race OPEN; fixed production actor absent.
G3 production protected journal/HKLM + truly independent historical witness and crash/reboot antirollback OPEN.
G4 privileged pending-only real WinCred lifecycle not approved.
G5 production signing / Kristian Smart App Control acceptance OPEN.
G6 triple FULL Windows product regressions, independent release and original Google Drive master workbook-FIRST / dashboard reconciliation OPEN.

No real API key, protected journal, actual registry, service installer, TPM provisioning, WinCred, SAC change, unsigned EXE on Kristian, GitHub merge/tag/release or historical P62 safety-block reproduction.

**P130 ISOLATED SECURITY-NEGATIVE DESIGN REVIEW. BYOK C1 PRODUCTION RELEASE HOLD.**
