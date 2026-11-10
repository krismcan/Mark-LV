# Nayeon v1 — P136 first full Windows regression stall triage

**10 November 2026 | OM v2.1 | USER-SCOPE FIRST RELEASE HOLD**

## P135 evidence, not speculation

Direct P135 source HEAD `57f9485315479e22887ccb62d9f76e06d064d7ae`, [Windows Action #42717686606](https://github.com/krismcan/Mark-LV/actions/runs/42717686606), job `129503338552`. P135 whole-project Python source and tests compileall passed; three sequential **unfiltered** `python -B -m unittest discover -s tests -t . -p test_*.py -v` attempts each timed out at 600 seconds with native exit **124**. Each failed to emit a `Ran N tests` completion marker. **Do NOT call these a full product regression pass.**

All three original complete raw test logs were preserved in GitHub Actions artifact `p135-windows-triple-full-discovery-raw-logs`, ID `13721186316`, SHA256 archive `aa179e18e3aa39fc3254a6c44d8654ffe93685dd792d84ba1e79049a96f86856`.

Actual first pass raw stream: **1,637 `ok` statuses**, **37 `FAIL` statuses**, **7 `ERROR` statuses**, with one final unfinished test after these **1,681 completed outcomes**. The last current test being executed in ALL THREE IDENTICAL 276,947-byte logs was:
`tests.test_phase8_byok_b_scope_integrity.ExactBYOKBTests.test_missing_or_zero_candidate_pin_and_live_a_adapter_tamper_refused`.

This case constructs historical exact-branch Git fixtures via the unmodified `candidate()` context, repeatedly loading actual historical blobs, frozen pins and static seals. The identical raw outputs do not prove a deadlock; a slow subprocess call, Git object traversal, expensive replay or blocked OS call remains possible. **P136 will diagnose before ANY additional full triad run**. P135 full test failures already include historical branch/topology seals incompatible with the later P134–P135 branch and seven native filesystem tests; individual error messages must be reviewed without weakening existing safeguards.

## P136 surgical diagnosis

Exactly three new P136 audit-only paths versus P135: a 42-second standalone Windows test harness, hosted Windows workflow and this report. P135/P134 original product and tests remain byte-identical; no rewriting old frozen tests, source branch pins or expected values. The Windows harness runs ONLY that exact old test ID in a new Python subprocess with `faulthandler.dump_traceback_later(10,repeat=True)`. On timeout the child is terminated by native Python timeout; prints only safe source/test stack line summaries, native exit, raw SHA256 and hold disposition. Complete raw diagnostic log retained as private GitHub Actions artifact even if CI fails.

Standalone pass, fail or timeout only explains the historical bottleneck; it **does NOT clear P135 37 failures/7 errors or the three required full regressions**. Any final regression suite selection must be transparently divided into (1) full runnable current-branch product functional tests and (2) frozen historical seal tests verified on their native branches, with independent reviewer authorization of the separation. Never silently skip a failing full-suite assertion and pretend all product tests passed.

## Signing and packaging reality

Read-only Kristian preflight from P135 reported existing Python interpreter Authenticode signature valid, but **no signed Nayeon application build**. `signtool.exe`, `pyinstaller.exe` and `makeappx.exe` absent from **PATH**, not proof of global absence. No signing certificate/private key has been supplied or approved. Do not use the signed Python interpreter as a substitute for signed publisher-pinned Nayeon packaging or deliberately modify Smart App Control.

**Next design gate:** identify a trustworthy published Windows packaging and signing route with an installed/update trust chain, review no bundled source/credential leaks, and run a signed distributable in a controlled Windows profile. None of those are completed by this P136 diagnostic.

No real API key, provider validation, protected storage/HKLM/TPM, native WinCred mutation on Kristian, unsigned EXE launch on Kristian, SAC bypass, historical P62 blocked step retry, GitHub merge/tag/release, or nonrelease Google Drive master/dashboard update.

**P136 security-neutral historical full-suite failure analysis only. BYOK C1 USER-SCOPED RELEASE HOLD.**
