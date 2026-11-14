# P210 — Controlled Python→Native Windows Negative Integration

**14 November 2026 · OM v2.1 · baseline:** exact P209
`fb851c6d19ec7000aab3e56c2db3dd78707933ae`.

**Disposition:** Actual Windows cross-process **test-only** integration candidate,
not trusted IPC, signed service or finished credential architecture.
**Real-key R0–R4 NO-GO · production P0–P5 HOLD · full regressions 0/3.**

## What was integrated (actual code, not just an audit)

Python test code in `tests/test_p210_python_native_synthetic_integration.py`
launches a new Windows x64 C# executable compiled from the **actual original
frozen P49 dependencies, original current native C1 service candidate,
P208 test-only terminal owner and P209 actual DPAPI CurrentUser journal**.

The native entrypoint `P210SyntheticBoundaryExecutable` is included only
when the build explicitly sets `C1_SYNTHETIC_TEST`. It only accepts a fixed
synthetic scenario argument, takes its disposable directory from Windows
`RUNNER_TEMP`, and returns fixed non-secret status strings. It rejects
caller-specified targets, secret arguments, extra approval fields and unknown
operations. It contains **no WinCred/credential API, service Main activation,
named-pipe listener, signer, privileged process, provider/network call,
production source admission or credential value**.

These scenarios execute the unchanged native C1/P208/P209 mechanisms:
- missing owner and forged review → refused with zero fake effects;
- one-time review followed by replay → exactly one integer fake attempt,
  recovery required, no rearm;
- durable synthetic IN_FLIGHT before effect followed by process restart
  → recovery required, zero effect;
- one unknown integer fake effect with actual DPAPI intent and recovery
  persisted → fresh journal observation requires reconciliation;
- same-user **valid historical ciphertext rollback** after completed
  recovery → `PreparedUntrusted` seen but never accepted for effect;
- actual ciphertext tampering → corrupt/refused;
- revocation before attempt, missing journal and delete without destructive
  acknowledgement → refused without any fake attempt.

The **actual Python subprocess** observes source-bound native process OS
exit and exact bounded output. It also injects
`P206LegacyEffectHoldCandidate` to prove in-process Python effect calls
are refused *when explicitly using that candidate*. This is NOT a trusted
Python-to-service API. No corresponding production UI, C1 service or P132
controller is wired to it. That difference is mandatory in review.

## Security finding still open: real source-reachable P132 backend

`nayeon/desktop_alpha/application.py` Connection page →
`local_byok_launch_bridge.py` fixed Python child →
`local_byok_window.py` user approval →
`nayeon/brain/local_byok_user_scope.py::LocalByokController.approve`
→ `WindowsCredentialBackend.put/delete` → actual Windows CredWriteW or
CredDeleteW if real WinCred is used.

This **source-reachable P132/P133 reduced user-scope route** remains
untouched. Its source-mode child is not a signed privileged C1 service,
and same-user callers can use the backend directly. A synthetic native
process from P210 cannot govern that Python DLL path. The P206 permanent
holder cannot be injected into P132 because P132 requires the exact
`WindowsCredentialBackend` type. P210 MUST NOT be interpreted as
closing P0 unified effect ownership or R1/R2 authenticated terminal consent.

## Windows evidence and release governance

Only five **additive** P210 files, no modifications to:
- frozen P49/P96 or prior native C1 source and denial suites;
- P132/P133 original Python backend, UI and launch bridge;
- P206/P207 source/bypass comparators; P208/P209 synthetic source;
- Phase 10.1/10.2/10.3/P76 source identity, frozen historical evidence;
- Kristian's original 17 dirty/untracked paths.

`scripts/p210_windows_python_native_synthetic_integration.py` requires
an authentic GitHub hosted Windows **push**, SHA/branch/repository equality,
exact P209 ancestor and precisely the five approved new paths. It validates
prior Git blobs (including P132 backend/native source), compiles C# with the
old Windows Framework compiler with **zero diagnostics**, and runs
original P132 36, P206 12, P207 14, frozen P49 native 20, current C1
native 24, P208 native 20, P209 DPAPI native 18 and the new P210
Python-to-native **13 cases**.

Expected **157 selected cases** are not the 3 unfiltered full-product Windows
regressions. It logs each native/Python OS exit, unmodified original compiler
logs, SHA-256 original raw logs, exact Git source custody before/after, and
H/C/R on both failure and success. It saves genuine failed runs rather
than resetting historical code or falsely reporting readiness.

## Post-P210 engineering priorities before real-key admission

1. **Select and externally approve a mutually exclusive architecture:**
   P132 reduced user-scoped U1–U6 release OR high-assurance native service
   R0–R4. Avoid quietly merging both trust models. GOV/SEC human
   security/governance owner must sign the choice.
2. For high-assurance route, **implement** signed source identity and
   authenticated service/UI/IPC, not a test-only subprocess protocol.
   Move the **one and only** actual credential effect dispatcher to the
   service with final one-use durable approval and no-retry reconciliation.
3. **Eliminate or isolate** all legacy P132 + direct Python WinCred effect
   paths under enforced OS installer/runtime restrictions. An in-process
   flag, optional callback, or rename cannot defend against same-user direct
   WinCred/DPAPI access. If Windows user-store cannot satisfy high-assurance
   isolation, choose a differently protected store and independently review
   migration.
4. Add independent monotonic antirollback/ABA, file/volume/source identity,
   signed Code Integrity/WDAC/SAC real-environment acceptance; protect
   crash/restart states from missing/journal replay/ACL failures.
5. Clear unwaived P135, P175, P178, P179 and PERF-P187-01 historical
   failures. Obtain **seven genuine external GOV/SEC/REL positive reviews**,
   G0–G6 security proof, production P0–P5 and **three complete** unfiltered
   native Windows product regressions. No real key or C2 provider validation
   until separately approved and consented through the local trusted UI.

## Final classification

If current P210 Windows CI succeeds, P210 closes as a **cross-language
synthetic integration negative**. It DOES NOT close real-key readiness,
production unified effect ownership, protected antirollback, authenticated
service provenance or third-party security review. The GitHub PR must stay
DRAFT and unmerged, and no production GitHub release, Google Drive MASTER
release ledger or dashboard entry is authorised from these tests.
