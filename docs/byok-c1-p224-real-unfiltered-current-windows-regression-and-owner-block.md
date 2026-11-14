# P224 — Genuine Current-Branch Full Unfiltered Windows Product Regression

Nayeon v1 / Mark-LII · BYOK C1 · 14 November 2026 · OM v2.1

**Scope: ONE unfiltered Windows full regression attempt, not a production seal or independent reviewer decision.**

## Baseline

- Exact parent P223: 7083432a3e751d76f1e7d8824bd11903c5c54156, draft PR #148 unmerged. Verified genuine Windows run 43635866908 and artifact 14129793286 (native exact-host refusal and 33 original Python security cases only).
- Only P224 additions: this document, scripts/p224_current_windows_full_regression.py and .github/workflows/p224-windows-current-full-product-regression.yml. No production code, historic tests, security guards or native credential effect source changed.
- Frozen original P96 coordinator SHA256 D8B8E4C6D5EA5E035B58C6AD73DD758C16640167C804CCF3305969B12BDF81AB. Original ledger SHA256 93A5EEEC6EE6CC4F6FFF5146B5709F57CBDD37559D62DE0BD4691BF678D5CE0B. Verify from raw Git HEAD blobs, independent of Windows CRLF checkout.
- Kristian local original source D:\Nayeon\BYOK_C1_PRODUCT_20261028, branch nayeon-v1, HEAD e3612279cb972e68e2487702183d5bf5b8f6c4a1, all four modified and thirteen untracked paths must remain untouched.

## Why execute

P135 historical genuine hosted Windows unfiltered product discovery exposed inherited historic Git/branch seal failures and stalls, as recorded in P154. P221/P223 focused success (89/89 and 57/57) is NOT a full product pass. With additional current branch code and tests, new exact-HEAD full discovery can identify the current failure frontier. Repeated full runs on a known failing unchanged source are not warranted; this is ONE attempt and stops on HOLD.

The exact UNFILTERED command is:

    python -B -m unittest discover -s tests -t . -p test_*.py -v

No -k filters, excluded modules, rewritten test cases, skips added, or passing result invented. Native Windows hosted GitHub runner, Python 3.12, repository HEAD verified; standalone log stream to RUNNER_TEMP, 600-second upper bound. If timeout/exception/nonzero process exit, outcome HOLD; record full log SHA-256, original failing test IDs, genuine exit and observed count. A complete successful attempt means one provisional current SHA functional pass, not release.

Original P134 genuine Windows WinCred tests only have a random namespaced synthetic target and verified cleanup; only on a disposable GitHub-hosted Windows runner using P134_NATIVE_WINCRED_EPHEMERAL_AUTH=EPHEMERAL_GITHUB_WINDOWS_ONLY. No real keys, current-user production target, real provider call, service installation or Windows policy change permitted.

## Security and external review blocker

P222 qualified independent SEC-03/SEC-04 architecture/reviewer decision PR #147 remains DRAFT, unmerged. A real owner-assignment request was posted in PR discussion comment 6883594204; not itself reviewer approval. No CODEOWNERS found, GitHub Issues disabled (410). At P224 intake: 0/7 actual independent GOV-01/02, SEC-03/04, REL-05/06/07 approvals. The original native P96 consent/effect race remains open; P223 actual host remains DENIAL-ONLY; P132 interactive-user direct WinCred path remains reachable in source.

SEC-03 requires real service principal/profile/SID/token and protected store/ACL/recovery/antirollback decision. SEC-04 requires signed installed image/WDAC/Code Integrity, authenticated Windows IPC and real one-use human consent, native single-owner P96 remediation, and a genuine independent reviewer. No automatic migration from old P132 credentials.

G0–G6 OPEN, R0–R4 REAL-KEY NO-GO, P0–P5 PRODUCTION HOLD, full product regressions 0/3 until verified passing whole-product release-candidate runs, BYOK C2 NOT AUTHORISED. No merge, native privileged service, credential changes, policy mutation, production release, or authoritative macro-enabled Google Drive MASTER/dashboard release status change.

## Next actions after actual logs

If failure: preserve real Windows logs, exit code, original failing test IDs, then find causal category and source-bound fixes WITHOUT changing sealed historical assertions. If success: one provisional functional baseline only, and keep separate independent security and remaining full product acceptance gates open.

Do not mistake this regression run or a self-authored reviewer form for an independent SEC-03/SEC-04 decision.
