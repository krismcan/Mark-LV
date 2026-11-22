# P302 dual-contract cross-phase regression arbitration

22 November 2026; BYOK C1; OM v2.1; Codex sole implementation writer.
**REAL KEY NO-GO. PRODUCTION HOLD. Hosted P302 evidence PENDING.**
Qualified approvals: **0/7**. Accepted full product regressions: **0/3**.
This is evidence preparation, not acceptance, a product phase seal or migration.

## Custody and authorized scope

Supplied exact clean P301 HEAD: `1aab175d00dbb7cdcdccb1438e9fadc2d04b9a7d`.
Branch: `byok-c1-p302-cross-phase-retirement-acceptance-20261122`.
Static Git ref reads match that branch and HEAD; no local Git was executed.
Clean index/worktree and milestone-tag custody are not independently proven here.
Hosted admission must prove cleanliness and the exact one-parent successor.
The inherited `.codex/CURRENT_STATE.md` describes Phase 10.2 on 3 November;
that stale state mismatch is recorded without altering the inherited file.
Exactly two ADD paths are authorized, in this writing order:

1. `.github/workflows/p302-windows-dual-contract-cross-phase.yml`
2. `docs/byok-c1-p302-dual-contract-regression-arbitration.md`

No inherited source, original test, source witness, hash pin or tag is rewritten.
No staging, commit, push, local Python/SCM/service/native binary execution occurs.
No key inspection, real WinCred, provider call or OS/service mutation is authorized.
No Google workbook or dashboard update occurs until C1 is fully complete.

## Open Failures & Prior-Issues Review: HOLD

Original P275 hosted run **44398320658** is supplied historical evidence.
Both authentic Windows x64 and x86 runs were RED, not waived or repaired here.
Original NativeAdapterTests: `Ran 8 tests`, `FAILED (failures=2, errors=5)`;
there were two FAIL, five ERROR and one pass on each architecture.
Original P211: `Ran 22 tests`, `FAILED (failures=14)`.
Original P216: `Ran 18 tests`, `FAILED (failures=2)`.
Old BackendTests passed 12; original P132 fake controller tests passed 28.
These historical counts are not newly executed or independently retrieved here.

P275 retired native read/write/delete effects in `_Advapi32Adapter`.
`read` remains only an inert compatibility shim raising fixed SecretStorageError.
Default backend mutation stays denied; fake injection retains its limited seam.
The old tests encode the former native effect contract, causing this conflict.
Restoring effects to satisfy those tests would reverse the approved containment.

The following are exact exception/assertion text and relevant source frames;
they are bounded traceback excerpts, not reconstructed complete hosted logs.
P302 artifacts must retain the original newly observed failure tracebacks.

```text
test_credential_layout_and_api_declarations
    self.assertEqual(dll.CredWriteW.argtypes, [pointer, ctypes.c_uint32])
AttributeError: 'FakeFunction' object has no attribute 'argtypes'
test_native_write_fields_and_cleanup_on_success_or_failure
    adapter.write(TARGET, b"a\x00b", 1, 2, "nayeon-v1")
AttributeError: '_Advapi32Adapter' object has no attribute 'write'
test_native_delete_success_uses_generic_and_zero_flags
    self.assertTrue(self.adapter(dll).delete(TARGET))
AttributeError: '_Advapi32Adapter' object has no attribute 'delete'
test_native_read_copies_exact_size_before_single_free
    self.assertEqual(adapter.read(TARGET), b"abc\x00tail")
    raise SecretStorageError(_FAILURE)
nayeon.secrets.contracts.SecretStorageError: Secret storage operation failed
```

The two NativeAdapterTests assertion failures expect read/free events now absent.
The remaining read/missing/error-mapping errors encounter the same denial shim.
P211's source witness no longer sees the retired native effect:

```text
test_02_actual_python_wincred_effect_proven_source_reachable
    self.assertTrue(found.python_direct_native_credential_effect)
AssertionError: False is not true
test_03_real_repository_code_plan_refused
    self.assertEqual(receipt.reason,P211Refusal.LEGACY_EFFECT_PATH)
```

The old expected reason is `LEGACY_EFFECT_PATH`; the current refusal reason is
`UNRECOGNISED_PAYLOAD`. Release denial remains; reason drift is still RED.
Other P211 failures share obsolete native-source predicates/reason expectations.
P216's two old native-source expectations are now false:

```text
test_02_p132_live_Python_direct_WinCred_effect_still_reachable
    self.assertTrue(self.receipt.direct_effect_source_reachable)
AssertionError: False is not true
test_06_actual_native_credential_adapter_appears_in_scan
    self.assertTrue(a[0].wincred_native_adapter)
AssertionError: False is not true
```

Contract conflict severity: material acceptance blocker; disposition HOLD.
Containment: retain retirement and default denial; never waive original RED.
Impacted callers include P132 controller/default composition, P211 package intake
and P216 store inventory; in-process fake injection is not an OS boundary.
P96 **HIGH** remains unresolved; current denial does not repair its original race.
P292 x86 teardown remains unverified; P301 is source-only, not service acceptance.
Independent qualified approval for closing these gates is absent: **0/7**.

## Versioned replacements and hosted arbitration

P276's 12 tests cover current package refusal; P277's 10 cover current store source.
P298's 15 cover the current effect boundary; they are versioned, limited checks.
Together with BackendTests 12 and LocalOfflineControllerTests 28, current total
is exactly **77 per architecture**. This is not full Windows product acceptance.
Formal test migration is **NOT APPROVED**; original suites remain authoritative RED.
No test rewrite, suppression, retry, expected-failure decoration or waiver is used.

The workflow admits only a same-repository DRAFT pull_request on Windows-2022,
with the exact P301 base branch/SHA and exact P302 head branch stated above.
Checkout, setup-python and artifact upload use the requested immutable SHAs.
Read-only contents permission and credential-free checkout grant no product authority.
Raw recursive Git entries must preserve every inherited mode/type/blob/path.
Only the two named regular blobs may be added; source must start and end clean.
Pre/post SHA256 manifests include source files; receipts live outside checkout.
Each group uses `python -I -B -m unittest <module>` on hosted Python 3.12 only.
Each child has a 40-second bound, fixed log cap and no retries.
Original natural exit and cleanup exit are separate; timeout/truncation is HOLD.
Sanitized logs have SHA256 receipts; metadata retains the bounded raw-output hash.
Current groups require raw exit 0, exact Ran count and bare OK, with no skips.
Historical groups require raw exit 1 and the exact original FAILED counts above.
Unexpected results fail the audit; successful RED reporting is not acceptance PASS.
Postsource custody is checked even after unexpected test evidence.

Only after all hosted checks match may this evidence marker be emitted:

`P302_CROSS_PHASE_CURRENT=PASS CASES=77 HISTORICAL_ORIGINAL=RED_UNWAIVED REAL_KEY=NO_GO PRODUCTION=HOLD FULL_REGRESSIONS=0/3 APPROVALS=0/7`

No such hosted result is claimed by this source-writing task. Disposition: **HOLD**.
