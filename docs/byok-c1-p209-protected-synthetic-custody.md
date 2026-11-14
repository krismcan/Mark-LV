# P209 — Windows-Protected Synthetic Custody and Restart Recovery Candidate

14 November 2026 · exact P208 parent `0ade464c0e0d51a03e9cdb976f36f2351f8ed900`

**Scope:** disposable unprivileged GitHub-hosted Windows user, synthetic non-key metadata only. Real-key R0–R4 NO-GO; production P0–P5 HOLD; original G0–G6 and seven independent decisions OPEN.

## Implementation

`native_c1_candidate/P209SyntheticDurableCustody.cs` is compiled only with
`C1_SYNTHETIC_TEST`, never in a normal signed/released native binary. It
uses **real Windows DPAPI CurrentUser** to protect a tiny, explicitly nonsecret
test record (fixed Nayeon target, version, operation, synthetic GUID epoch,
generation, phase) and an explicit current-user-only file DACL. Write-through
`FileStream` plus file replacement in one disposable directory models
durable PREPARED → IN_FLIGHT → RECOVERY_REQUIRED transitions.

There is NO WinCred, API key, signed service, IPC, signer, provider call,
privileged access or install action in this candidate. Original P49/P96,
P132 backend and the native C1 service remain byte-identical.

A **fresh instance may observe protected existing state but never use a file as
effect permission**: the previous instance's synthetic advancement tenure
does not survive restart. IN_FLIGHT reload, uncertain error and completed
recovery all return *recovery-required*. Original valid historic PREPARED
DPAPI ciphertext restored by a same-user attacker is reported as
`PreparedUntrusted` rather than authorising any effect. Missing, corrupt,
wrong-target or truncated records refuse. No automatic retries or rearm.

The same source deliberately exposes:
- `RealCredentialEffectAllowed == false`
- `AutomaticRetryAllowed == false`
- `ExternalAntirollbackWitnessAvailable == false`

These are permanent holds, not toggles. G3 is **NOT satisfied**.

## Important remaining weaknesses (P209 is NOT durable authority admission)

1. DPAPI CurrentUser verifies a record's integrity for that Windows user but
   cannot stop another same-user process with DPAPI access from producing
   valid records or restoring old valid ciphertext. No independent protected
   antirollback witness exists. The *test* can visibly restore an older valid
   PREPARED record. It never permits an effect from that record.
2. A user-writable disposable directory and its path can be deleted, renamed
   or replaced by another same-user process. A DACL/WriteThrough alone
   neither authenticates the installed service image nor provides kernel
   file/ancestor/volume identity binding against TOCTOU.
3. `File.Replace` and write-through are best-effort Windows file persistence;
   crash and power-loss ordering must be independently proven with the
   eventual protected journal, filesystem/volume and actual installer policy.
   The test does not prove stable physical media flush or dual-fault survival.
4. The candidate has a process-local test tenure and does not hold a
   protected cross-process mutex or a trusted signed service identity.
5. The test-only P208 actor and P209 ledger are joined by one synthetic
   integration test in the correct order: write IN_FLIGHT, attempt one integer
   fake effect, record RECOVERY_REQUIRED. They **do not share an atomic
   production transaction lock**, and no real effect is permitted.
6. P132/P133 remain separately source-reachable for real WinCred use after
   manual source-mode launch. P209's file does NOT govern or close that route.
7. BYOK C2 live provider validation is not authorised, regardless of P209 result.

## Genuine native Windows negative tests

`native_c1_candidate/P209SyntheticDurableCustodyTests.cs` executes
18 actual Windows-native C# cases using RUNNER_TEMP and deletes disposable
nonsecret fixtures afterwards. Cases cover absent/malformed states, delete
ack, real DPAPI encryption, current-user file ACL, duplicate init, durable
IN_FLIGHT, restart after unknown, no rearm, durable recovery, ciphertext
tamper, torn/truncated data, authenticated *but historic* rollback, deleted
journal, wrong-target DPAPI forgery, P208 one-fake-effect after journal intent,
and permanent real-effect/antirollback holds.

The `scripts/p209_windows_protected_synthetic_custody.py` workflow must
authenticate exact P208 ancestry and five additive file paths; preserve source
SHA blobs, exact native compiler and OS exit codes, raw SHA256 logs, and before/
after Git custody. It additionally re-runs P132 36, P206 12, P207 14,
original P49 native 20, current native C1 24 and P208 native 20 test cases.
These are **selected experiments**. The mandatory 3 full unfiltered Windows
product regressions remain 0/3.

## Next P210 engineering

The next step is **true negative integration** between current P132/P133 Python,
signed-source design and a native recovery-only candidate under an
independent file/transaction authority proposal. P210 must prove:
- every direct legacy Python WinCred mutation path has either been eliminated
  from a controlled build or explicitly isolated by a policy owner;
- authenticated peer, source identity and terminal actor cannot be forged;
- power-loss and rollback source/custody faults cannot rearm an effect;
- immutable P49/P96 negatives, old current-branch failures and native Windows
  source identity are preserved;
- no experimental pass is misrepresented as real-key R0–R4 or P0–P5 GO.

Qualified independent Windows-native security reviewer, approved signer and
machine Code Integrity/WDAC/SAC administrator are external authority gates.
P135/P175/P178/P179/PERF-P187-01 remain unwaived. No merge/tag/release;
no Google Drive MASTER production release entry or dashboard mutation.
