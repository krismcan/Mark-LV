# P243 — Authenticated Older-Seal Immutable Git Batch Candidate

15 November 2026 · Nayeon v1 / Mark-LII · BYOK C1 · OM v2.1

**Status: ENGINEERING DIAGNOSTIC CANDIDATE ONLY. Original regression unclosed. Real-key NO-GO; production HOLD.**

## Objective and verified identity

P243 follows P240 source commit `f4e352b25d4654ad46e3b56bf40d8be01b7c56d6`, branch `byok-c1-p243-g1-full-history-immutable-20261115`. Authentic historical source under test is frozen P233 `096048db17c7c1f9402dfd16a7deb31e9ebdc81d`; the original G1 body is unchanged. P243 is a single isolated full-history LF-only checkout, completely separate from the dirty Kristian product checkout.

P241 properly STOPPED because its shallow source lacked old sealed objects. P243 recovered full history in a separate clone, with 89 available tags, no alternate objects or grafts, and exact B/A/8.37 commits. Full-history native Git object proof found **131 exact historical commit:path pin preimages** in nine generations: 5 8.30, 3 8.31, 14 8.32, 16 8.33, 20 8.34, 19 8.36, 20 8.37, 11 A and 23 B. Full-history original annotated tag/commit/tree and per-path blob OIDs were authenticated. The original historical source-defined digest methods, including CRLF normalization for 8.30–8.32 and single self-pin literal zeroing, were retained. Immutable trusted data comes from literal values in raw Git-authenticated P233 source, not mutable current refs or test dictionary mutations.

Source manifest derivation digest noted from the independent audit: `691945CEAF90BDB88D02A9A331FE349F082332C0375024F714EAA13573F5A151`. Local independent full-history preflight actually validated all 131 original raw Git show bytes against source pins and tree entries, native Windows Python 3.12 exit 0; external receipt `D:\Nayeon\P243_HOST_EVIDENCE_20261115\p243_scoped_local_manifest_preflight.json`, SHA-256 `BCF3A1C63ECB247DAC11E5F79A47119AAE371CE9DED2DDEC5DB31C9BAB5C4CB4`. This local preflight is **not** the hosted original P234 source guard, which correctly refuses non-GitHub environments and was NOT bypassed.

## Four strictly additive diagnostic files

- `scripts/p243_g1_older_seal_batch.py`: fixed 131-row source-pinned manifest, original Git OID/normalized SHA256/raw `show` witness checks, finite fresh per-call `cat-file --batch` transfer, strict native request signature, nonmatching operations original native delegation, verified source-before/after with original P234 and P240 canonical witness logic, original 180-second whole-child Job Object containment, bounded P239 progress and original test result classifier; no key material.
- `scripts/p243_g1_older_seal_batch_selftest.py`: focused inherited P238/P239/P240 adversaries plus source-normalization and transport-specific tests for all 131 paths, malicious or truncated frames, stale positive, negative-mock causal injections, delegate-unchanged native exceptions, process-tree cleanup and source-witness identity.
- `.github/workflows/p243-g1-older-seal-batch.yml`: `windows-2025`, exact P243 branch push, full-history authentic P233 controller/source checkouts with raw LF bytes, native source and exact one-parent/four-additions gate, synthetic validation **before one** G1 candidate. Fixed-schema JSON evidence always uploaded on failure. Raw sensitive logs and original paths/arguments are not published.
- This documentation.

The candidate never modifies G1's 23 original tamper assertions, P76's wrong-branch refusals or P96 native source. Only exact authenticated historical immutable `git show <literal commit>:<literal path>` requests may be intercepted. Mutable HEAD/branch/ref/tag/index/status/diff, tree inventory, approval and the original transforming negative fixtures still execute through the original native calls. Each accelerated read is a new bounded verified frame; no cached admission, replay, fallback, retry or widened timeout. The original G1 whole-child deadline remains **180 seconds** and per-read bound **20 seconds**. A candidate PASS, if obtained, is **not an unmodified original full-product regression** and must remain a nonzero HOLD (exit 3).

## Historical baseline and real unresolved blockers

P237 original unmodified G1 on hosted Windows had **4,154 Git Trace2 sessions**, timed out in 180 seconds, cleanup uncertain. P239 one instrumented G1 reached **19/23 subtest completions**, 920 B verified reads and 7,360 delegated calls, with 4,233 `show` calls, then timed out at 180 seconds, cleanup `JOB_EMPTY_CONFIRMED`. P240 full hosted Windows source-only source-witness equality correction and 22/22 focused synthetics passed in run `43712004087`; its success did not execute G1 or prove speedup. The P243 outcome may demonstrate only an instrumented-candidate improvement if valid original subtests and source witnesses complete; it cannot replace the historical unfiltered regression.

**P96 actual legacy native check/effect revoke race still open.** Current native `CustodyService` has no active signed service/terminal effect and denies all. Separate P132/P133 current-user Python code can still reach WinCred `CredWriteW/CredDeleteW`. Independently qualified SEC-03 Windows service principal/protected store and SEC-04 signed installed broker/CI/IPC/one-use consent owners have not approved any actual effect or disposable privileged test VM. Review intake: [GitHub PR #147](https://github.com/krismcan/Mark-LV/pull/147).

Original four P76 branch-refusal regressions, G1 and three other timeout regressions, 0/7 qualified external approvals, 0/3 full unfiltered Windows product regression passes remain unwaived. No real keys, credential operations, privileged service installs, signing-policy changes, product merges, tags, seals, deployment or provider probe. Do not update the Google master workbook or dashboard until BYOK C1 is fully complete; retrospective sealed-phase audit deferred.

## Test and publication discipline

Codex primary engineer assembled the candidate in one isolated writer session; Nayeon independently verifies final staged additive diff and executes genuine Windows Python adversarial tests before any draft PR publication. The initial host test completed **116/116** with native exit **0** on Kristian (diagnostic synthetics only). Final source-byte/test-log SHA256 receipts are appended after final rerun. Original G1 itself must run only on an isolated GitHub-hosted Windows runner with authenticated P233 source, never on Kristian. Expected red CI from deliberate HOLD must be evaluated alongside the uploaded `observe.json` and original native exit; no fabricated availability or passing results.

## Final independent Kristian Windows focused host result

The final four-addition source was verified against exact P240 parent
`f4e352b25d4654ad46e3b56bf40d8be01b7c56d6` in a separate full-history
`core.autocrlf=false` checkout. Actual Windows Python 3.12
`scripts/p243_g1_older_seal_batch_selftest.py` ran **122/122 focused synthetic
tests PASS**, **native exit 0**, zero failures, zero errors, zero skips.
The initial earlier 116/116 pass was superseded after six further adversarial
cases were authored. The external wrapper initially expected 116 and returned
exit 1 **after** the real 122/122 native Python PASS; this was corrected to
match 122 and final wrapper **native exit 0**. No test or historical source
was changed to accommodate the wrapper.

Final host log `D:\Nayeon\P243_HOST_EVIDENCE_20261115\p243_host_synthetic_final.log`
SHA256 `937E8A42A9CDFE0036C2EB32CFD6610F5630A6E268F5A48B8A7E6B705ABBE4CC`.
Structured synthetic JSON `p243_host_synthetic_final.json` SHA256
`C2F8F9300882911C0C70C8CE681806B017D4A8D40890C814BD67713BFC3EE903`.
Both new Python files AST parsed under Python 3.12, native exit 0,
AST log SHA256 `1CB8DA2CA5EF23FD656B0B9CF9FFE1E8105142D981846F180C6A9EDDFF71D910`.
The local exact full-history original 131-preimage proof separately exited 0;
receipt SHA256 `BCF3A1C63ECB247DAC11E5F79A47119AAE371CE9DED2DDEC5DB31C9BAB5C4CB4`.

**These results are focused candidate tests, not the original G1/full-product
regression passes, service security signoff or C1 release authority.**
