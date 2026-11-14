# P225 — Native Windows exact original failure isolation

Nayeon v1 / Mark-LII | 14 November 2026 | OM v2.1

STATUS: DIAGNOSTICS ONLY, not a remediation, full regression pass, independent SEC-03/SEC-04 review or release authorisation.

## Actual P224 source and failure baseline

- Exact P224 parent SHA 43c77651a062a114ded9706a1b5a3731a1d3eed9, draft PR #149, unmerged. Windows run 43637097310 failed with product process exit 124 (600-second timeout) despite no test exclusions. The original raw log is 305723 bytes, SHA-256 FE190CC8C17BEA604EF50D7870956D47F48F97919FF66FEB4DAC05FE0C354E11, artifact 14131046648. Original streamed outcomes: 1828, 46 FAIL, 10 ERROR, with no final unittest summary.
- Last recorded test: tests.test_phase8_byok_b_scope_integrity.ExactBYOKBTests.test_frozen_commit_index_and_disk_stay_bound. The isolated P225 test targets EXACTLY that original method, not the different P135 test in the older stall.
- P135 historical original artifact 13721186316: three identical logs of 276947 bytes and SHA256 31F844EE8C29B9886885303DF983FFA7C0452C2A671866400A9768535C6DD113; 1684 reported outcomes, 37 FAIL, 7 ERROR, no final summary; older stalled test test_missing_or_zero_candidate_pin_and_live_a_adapter_tamper_refused.
- Historical P136 already ran isolated faulthandler on the older distinct P135 stall. P161/P162 tested slow Git process calls and a test-only immutable Git object batch prototype. No historical test, Git reader, or source security assertion is changed in P225.
- Original P96 transaction raw SHA-256 D8B8E4C6D5EA5E035B58C6AD73DD758C16640167C804CCF3305969B12BDF81AB and P95 ledger raw SHA-256 93A5EEEC6EE6CC4F6FFF5146B5709F57CBDD37559D62DE0BD4691BF678D5CE0B stay frozen.

## Exact isolated Windows diagnostic plan

Only three additive paths: this document, scripts/p225_windows_original_failure_isolation.py and .github/workflows/p225-windows-bounded-stall-root-cause.yml. Exact P224 parent, Git HEAD, source immutability and pristine current checkout verified before running.

Each of seven original unchanged tests gets a separate disposable Windows CPython 3.12 process, authentic process exit, stdout/stderr log SHA-256, 12-second repeated faulthandler stack dumps and a bounded process lifetime: (1) exact last P224 BYOK-B test, max 65s; (2) original P132 ancestor/source gate, max 32s; (3) actual owned native Windows temporary-file test, max 32s; (4) P166 class setup and exact original source branch, max 32s; (5) P210 native test-executable class setup, max 32s; (6) P213 WinTrust signing class setup, max 32s; (7) Phase10.2 actual source admission, max 32s.

No weakening of historical tests. No synthetic credential write, production WinCred target, provider secrets, network/provider calls, service installer or Windows policy change. The P134 ephemeral WinCred approval environment flag is expressly omitted from every diagnostic child. Provider/GitHub bearer environment variables are removed from children. Child-tree termination only targets P225-created Windows processes on the disposable runner.

Passing diagnostic CI means seven pieces of real observational evidence collected; failing or timed-out original tests remain FAIL/HOLD. Do not turn the observation into product tests passing or release authorisation. Distinguish single-test timeout (intrinsic or slow Git source reader) from single-test passing but full-suite timeout (global-state, module interaction, original Git call saturation). Read actual stack frames and complete traceback before classifying the cause. Never infer causes solely from missing final unittest footer.

## Security and release gates

Independent GOV-01/02, SEC-03/04 and REL-05/06/07 signoffs 0/7. P222 PR #147 includes owner-assignment request comment 6883594204; no actual independent security decision received. SEC-03 Windows service account/SID/profile/protected store/ACL/rollback and SEC-04 signing/Code Integrity/trusted consent/IPC/native effect actor remain unissued. Original P96 effect/revocation race OPEN; P223 actual candidate CustodyService refusal-only; P132 interactive-user Python WinCred route still source-reachable. G0–G6 OPEN, R0–R4 REAL-KEY NO-GO, P0–P5 PRODUCTION HOLD, 0/3 full unfiltered Windows release regressions, C2 not authorised.

Kristian primary user worktree, all 4 modified and 13 untracked original paths preserved. Google Drive authoritative macro-enabled MASTER and dashboard unchanged. No merge, tag, policy change, privileged service install or real keys.

Next safe stage: use actual P225 stack/error evidence to define ONE source-bound, independent-reviewable causal repair only if supported. Do not rerun a failing full suite three times, remove test assertions, self-approve an external decision or claim a real-key gate.
