# Nayeon v1 BYOK C1 — P146 original Windows unittest failure-object / Tk-root lifetime

**10 November 2026 — OM v2.1 — DIAGNOSTIC ONLY — USER-SCOPED PRODUCTION HOLD**

## Verified predecessor and real problem

Exact P145 source SHA `7dc6e5377b2e9c4c2533c4a7dc99a262267d02aa`, draft PR #70.
P145 ran 19 original Phase8.31 test methods individually on real GitHub Windows:
18 PASS, 1 HOLD, 0 timeouts. The sole original failing method was
`test_static_production_import_closure_forbids_test_and_effect_routes`.
The unchanged original test rejects a `nayeon.brain` import in the later
Connection UI source. The same original method's `tearDownModule` additionally
reports one destroyed-but-retained Tk root.

This is a **test failure and an independently observable root-retention
report**, not proof that a deployed desktop leaks Tk roots. The failed
`self.subTest` assertion may cause unittest's `TestResult.failures` list
to retain a `_SubTest` carrier pointing at the test case which owns
`self.root`. This causal hypothesis requires genuine Windows evidence.

## P146 source-preserving diagnostic

A fresh isolated branch adds only this review, a hosted Windows audit workflow
and one probe script. No original test is modified; no failure is skipped,
erased or classified as a PASS, no production code, WinCred, source seal,
P139 strict native opened-handle verifier or P140 signed-launch safety gate
is modified.

The disposable Windows-2025 Python 3.12 workflow verifies exact P145
ancestry and only three added audit files. It verifies a freshly created,
owned fixed C-drive path through the **unchanged P139 handle guard**.
Only the isolated child TEMP/TMP/TMPDIR are redirected there; no global
Windows policy, registry, service, signed binary or Windows credential is
changed.

**Two independent subprocesses:**

1. Execute the **exact unchanged original test** via
   `python -B -m unittest -v <exact historical test ID>`, capturing genuine
   negative native exit and full original combined stdout/stderr SHA-256.
2. Run the **same original unittest test and original module teardown**
   inside an observational runner, without modifying any original test
   assertion, fixture or `unittest.TestResult`. Read whether
   `TestResult.failures[0][0]` is a `unittest._SubTest` owning
   `test_case.root`, whether the retired root has been destroyed, and
   whether its weakref becomes dead **after the original result object
   falls out of scope and Python GC runs**. Only the probe's result object
   is released normally; no original pass is produced or fabricated.

The diagnostic collector records both native process exit codes, original
negative outcome, observed reference ownership, root survival before and
after result release, genuine log SHA-256/byte counts and an explicit
classification in JSON. Even when CI concludes SUCCESS, the historical
original test remains FAIL/HOLD; that is the *expected* baseline, not a
product regression pass. Any unproven mechanism remains HOLD.

## Scope and release blockers

Do not infer that a later source import is safe simply because the old static
assertion may be stale. Its current migration needs independent qualified
test-governance/security review; one must verify import boundaries and no
automatic secrets/provider effects. Original P135 three full-product Windows
regressions never completed, P142 has nine timed-out modules, and P144 still
has additional historical source and UI claims requiring triage.

User-scoped first release still lacks real publisher-signed/pinned main and
companion images, protected update/installer ownership, Smart App Control
policy-owner GO, named qualified independent security review and three
complete accepted full-product Windows regressions. Original privileged
C1 G0–G6 remain separately open (including P96 and P124). Never use real
API keys or WinCred on Kristian, change protected HKLM/TPM, run unsigned EXEs
on Kristian, weaken Smart App Control, retry historically blocked operations,
merge/release, or update the Google Drive release workbook/dashboard before
a genuine authorised product release.

**P146 conclusion must be evidence-specific, not production GO.**
