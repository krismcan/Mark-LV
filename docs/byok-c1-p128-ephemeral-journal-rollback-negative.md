# BYOK C1 P128 — unprotected ephemeral Windows journal, restart classification and G3 rollback negative

Date: 9 November 2026 | OM v2.1 | Direct exact P127 parent `5e0d869df0a2e27b394481e878fa13529270fa95`

## Why this increment matters

P127 joined the same in-process revocation monitor, a real Windows named OS Mutex and synthetic (integer-only) intent, fake effect and terminal stages. It correctly demonstrated that **new actor instances have no prior transaction history**; real G3 recovery remains OPEN.

P128 tests what can be learned from actual unprivileged Windows filesystem records across distinct process lifetimes, **without using protected storage, registry/HKLM, credentials, real WinCred or a privileged service**. This is a **test-only file-format/diagnostic reader** under Windows `Path.GetTempPath()` with a new random per-test name and immutable compiler guards. It MUST NEVER be promoted as a protected credential ledger.

## Exact isolated implementation

`native_c1_g3_review/WindowsG3EphemeralReviewJournal.cs` requires BOTH `C1_REVIEW_ISOLATED_ASSEMBLY` and `C1_SYNTHETIC_TEST`, and allows only a random canonical 32-hex test ID; no arbitrary target path. All review files use `nayeon-c1-p128-<id>.review` in the disposable hosted runner's TEMP, and tests remove their files after each case.

Three fixed 42-byte binary stages:
1. `Intent` (one synthetic record; no effect attempted).
2. `FakeAttemptStarted` (possible purely synthetic effect; no WinCred).
3. `TerminalDiagnostic` (not durable authenticated success).

Each stage carries a bounded canonical version/magic/sequence and an **UNKEYED** SHA-256 hash of the prior record hash and current header. `FileStream.Flush(true)` and write-through are exercised on real Windows, but **do not establish power-loss durability or G3 compliance**. These hashes detect accidental changes and malformed sequences, but an attacker able to edit the file can recompute them. No HMAC, TPM, protected historical enrollment, security root, service identity or independent register anchor exists.

`InspectUntrusted()` is a read-only classifier: missing/empty, one intent, possible fake attempt, terminal diagnostic, or malformed/truncated/unreadable. **Even a perfectly well-formed full chain has all trust, antirollback, consent, native WinCred and production-admission flags FALSE**. An incomplete or uncertain stage always requires recovery and cannot be replayed as an approved native effect.

## Real Windows hosted test inventory

20 new native cases:
- reject short/uppercase/path-spoof IDs;
- missing/empty file, valid intent-only, possible-attempt, full diagnostic stages;
- out-of-order, duplicate/replay and excess stage attempts denied;
- digest change, truncated mid-frame, counter tamper and trailing junk classified corrupt;
- three **genuine separate Windows child processes** append and `Flush(true)` one, two or three stages, exit with OS exit code, and independent parent process classifies persisted bytes without sharing the child object state;
- **critical G3 negative**: roll back a valid 3-record chain to a previously saved valid 1-record prefix. The unkeyed structural hash still validates, proving structural integrity **cannot detect history rollback without an independent protected witness**. No production admission is possible regardless.

Actual native x64 execution only on unprivileged GitHub Windows runner, **never unsigned EXE on Kristian**. P127 and all older **382** native focused tests must run unchanged, including P96 original 15 fake-only revocation-to-effect race comparator. Expected total **402 native focused cases (20 + 382)**, not full Windows product regression.

## Precise limitations and reviewer decisions

These tests demonstrate post-process-exit visibility and fail-closed parsing of test-only, nonsecret filesystem records. They do **not** simulate physical power loss during `Flush(true)`, abrupt kill mid-WinCred, journal write atomicity across actual protected ACLs, independent anchor rollback/witness, signed service startup trust, transaction history enrollment or native credential semantics. A same-user attacker can replace, truncate, replay, forge or delete these TEMP files. Valid sequential records are diagnostics only, not protected proof or an authoritative lease.

G0 qualified independent native Windows security review OPEN.
G1 trusted signed installed consent broker, verified live loaded image/actual human exact-operation interaction and protected one-use grant OPEN. P124 transferred pipe HANDLE still breaks positive client authorship.
G2 original P96 revocation-to-effect check-to-call race OPEN; old adapter disabled, fixed-target approved native successor absent.
G3 protected file and HKLM anchor, independent historical witness, antirollback and crash/reboot recovery OPEN.
G4 privileged pending-only real WinCred validation OPEN.
G5 trusted signing and Kristian Smart App Control production acceptance OPEN.
G6 triple FULL Windows product regressions, independent release and Google Drive original master workbook-first/dashboard reconciliation OPEN.

No actual API credentials, WinCred/registry/protected journal, privileged install, SAC policy change, historical P62 blocked operation retry, signed production release, GitHub merge/tag or non-release Drive dashboard/workbook change.

**P128 REVIEW-ONLY G3 NEGATIVE EVIDENCE. BYOK C1 PRODUCTION RELEASE HOLD.**
