# BYOK C1 P105 — Original native J2/A2 recovery-format compatibility

Date: 8 November 2026 | OM v2.1 | **NONDEPLOYABLE ORIGINAL-SOURCE INTEGRATION TEST / RELEASE HOLD**

## Exact parent, scope and preservation
Based on P104 draft PR #29, commit `941e938d8f9a3bd576990df0ee9cfaae12683ee5`. This branch adds only a native C# test harness, review note and pinned x64 CI workflow. No original P49 C# source is edited and no new credential-capable service or runtime implementation is proposed. The original P49 11 native source units are compiled and linked with an alternate test Main, but the original service Main is not invoked. P96's real legacy consent-to-effect flaw remains open; G0–G6 independent security approval remains missing.

## Concrete source compatibility issue
- Original native `CustodyLedger.cs`: `FrameText()` writes `J2|`-prefixed, newline-delimited append-only records; `Anchor()` creates an `A2|` anchor. `CustodyLedger.Verify(journal,anchor)` parses those exact formats and can return `Initial`, `InFlight`, `CommittedUnverified`, or `CommittedAbsent`. This is still only **structural** evidence until actual OS custody security and enrollment trust are verified.
- Original `RecoveryReader.cs`: `Assess()` expects a single `J1|` frame and an `A1|` anchor; its `StructuralAnchorForSyntheticTest()` generates only that old format. Even when passed trusted-namespace=true, it returns `RecoveryRequired` for valid J2/A2 original native initial, intent, and terminal records. The formats are **not interchangeable**. A positive J1 structural parse does not imply a genuine J2 native custody enrollment.
- Review of the 11 original P49 service files shows the current transaction coordinator uses `CustodyLedger.Verify()`, and there is no deployed production routing from the old `RecoveryReader.Assess()` to the disabled native effects. This is an **integration hazard**, not proof that a deployed service currently misreads its journal (the service is not installed).

## Native Windows evidence
On Kristian a real x64 .NET Framework C# executable, compiled with **all eleven unchanged original P49 source files plus the new test driver**, passed **19/19** focused cases with native compiler exit **0** (zero diagnostics) and executable exit **0**. Evidence log:
`D:\Nayeon\BYOK_C1_P105_NATIVE_J2_EVIDENCE_20261108\P105_NATIVE_X64_20261108.log`
SHA-256: `93A376E9A18C38076723447BD01CB6954D9CB12AEAFCC673664DAAC1366EE7A7`.

Tests use only nonsecret deterministic J2 structural nonces and original source classes: initial, SAVE, REPLACE and DELETE ledger transitions, intent/terminal structural verification, old-reader rejection of real J2 records, missing/mismatched/truncated evidence refusal, J1-vs-J2 separation, and all three original production denial switches. They do not call `PendingCustodyTransaction.Apply()`, WinCred API, service install/start, registry writes, provider validation, IPC or real credentials.

## Required G3 integration decision (external reviewer)
The reviewed production successor must specify *one* authoritative schema/version and exclusive codec owner for the actual LocalSystem protected journal+HKLM anchor. It must never infer readiness by parsing J2 data as J1, accept old J1 as a native J2 enrollment, or fall back to an untrusted structural reader. Incompatible versions, missing protected enrollment, failed flush/readback, rollback, `IN_FLIGHT` and unknown native effects must remain **persistent RECOVERY_REQUIRED** without reseeding or auto-retry.

No version migration, conversion, fallback, automatic enrollment, credential dispatch or direct WinCred effect has been implemented by P105. Qualified independent G0/G1/G2/G3/G4 review and approved Windows signing G5 are still needed. P85 source gate, P62 platform restriction and x86 Code Integrity denial remain intact. Three complete product regressions and approved production release remain pending.

**P105 authentic native-source J2/A2 compatibility test only. BYOK C1 production HOLD. No API key required.**
