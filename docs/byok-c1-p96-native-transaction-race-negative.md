# P96 – Unmodified native C1 transaction coordinator: deterministic post-approval revocation proof

**Status:** TEST-ONLY NEGATIVE SECURITY EVIDENCE. **Finding OPEN, production release HOLD.** This is not a demonstration that a Windows native key operation actually occurred.

## Source identity

- Actual unchanged disabled native service source: `D:\Nayeon\BYOK_C1_P49_PRIVILEGED_SERVICE_20261029\src\PendingCustodyTransaction.cs`.
- Exact SHA-256 of original and test copy: `D8B8E4C6D5EA5E035B58C6AD73DD758C16640167C804CCF3305969B12BDF81AB`.
- Actual unchanged native custody ledger imported at P95: SHA-256 `93A5EEEC6EE6CC4F6FFF5146B5709F57CBDD37559D62DE0BD4691BF678D5CE0B`.
- Test harness uses ONLY disposable in-memory C# interfaces, never the actual `PendingWinCredStore`, service installation, live keys, elevated UI, native mutex or protected registry/file store.
- Source copy is under `tests/`, not production or an installed executable.

## Confirmed design-level negative finding

The exact unmodified `PendingCustodyTransaction.Apply` checks `approval.StillCurrent` on its final pre-effect predicate, then evaluates `lease.IsOwned` and calls `state.SaveOrReplace` or `state.DeletePending` without holding a shared service-owned admission lock covering consent revocation and that final effect.

**Deterministic injection:** The fake lease's fourth `IsOwned` probe occurs after the coordinator's last `StillCurrent` check and before the effect interface invocation. During that probe a **separate .NET/Windows thread** revokes the fake approval and synchronously completes. The original C# coordinator then **still invokes the fake effect** after the revocation. This is reproducible for SAVE, REPLACE and DELETE.

A *passing* P96 negative test therefore means we **reproduced the old interface's security design gap**, not that the coordinator is secure. It does not establish that the currently blocked real native effect can be reached: the actual adapter and service still contain literal release holds.

The reproducible ordering is:
1. Coordinator sees `StillCurrent == true` and holds its separate custody tenure.
2. Separate thread commits consent revocation before dispatch (during final IsOwned getter).
3. Actual unchanged coordinator invokes its effect interface with consent now revoked.
4. Only the fake test adapter increments an integer; **no WinCred API runs**.

## Additional native negative and positive tests

The harness asserts early revocation before Consume denies, malformed candidate denies, untrusted state denies, faulted lease denies, in-flight journal denies, missing history never bootstraps, mismatched anchor denies, unexpected pending-present denies, failed fake effect is recovery-required with no retry, and success remains unverified/replay denied.

Both the original coordinator and ledger are SHA-pinned in GitHub Windows CI. Native Windows x64 and x86 C# test executables each run 15 focused cases, with explicit `P96_SECURITY_FINDING=OPEN` and `P96_C1_PRODUCTION_RELEASE=HOLD`. This source and test suite **must not** be shipped as a privileged service.

## Actual fix still required (P61)

A separately reviewed successor service-owned admission section must:
- Authenticate an elevated local user's one-use operation/candidate/session-bound consent; do not trust a caller-supplied `StillCurrent` interface alone.
- Place service-owned consent revocation/fault publication and final dispatch under the **same non-reentrant admission lock** with a precise linearisation point; maintain the existing exact thread-owned native OS custody mutex for the full write/terminal lifecycle.
- Durably record and verify pending journal/anchor `IN_FLIGHT` before a single native pending-only effect. No invocation of arbitrary callbacks across the final barrier. Revocation winning before dispatch must cause **zero effects**; if dispatch wins first, preserve possible-effect uncertainty and block retries after a failed/delayed native result.
- Keep `ServiceGate.LiveEligible()` release proof false and `PendingServiceState.LegacyEffectEntryDisabled()` / `PendingWinCredStore.NativeMutationAdmissionPending()` true until independent qualified security review and a distinct production-release gate. Never reuse P85/P90 read-only source checks as production permission.
- Explicitly prove protected OS storage/anchor, authenticated IPC, consent provenance, proper service principal/ACL and Windows recovery under actual native methods **before** release. External Windows CI executing developer-written tests does not count as independent source sign-off.

Historical P62 safety restriction and OpenAI Support case #18729810 remain untouched. No P62 rerun/reconstruction/bypass, no real API key or key-handling in chat, no service deployment, no actual WinCred operation, no mandatory three complete product regressions and no same-ID Google Drive master/dashboard update.

**Disposition:** test-ready reproducible security finding; production native C1 still HOLD.
