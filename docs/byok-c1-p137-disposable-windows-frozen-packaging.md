# Nayeon v1 / BYOK C1 P137 — disposable Windows frozen standalone UI packaging smoke

**10 November 2026 | OM v2.1 | DRAFT | USER-SCOPED RELEASE HOLD**

Direct P136 diagnostic baseline `e9d7a0087700c8d05d8fe4687e2754cf8e0143c3`. P132 built explicit user-scoped offline WinCred key setup; P133 integrated an explicit Connection page launch but refused frozen desktop apps; P134 verified genuine WinCred with ONLY random nonsecret credentials on ephemeral hosted Windows. P135's three full Python Windows regression attempts FAILED due ten-minute timeouts and partial test failures. P136 captured actual Windows live stack traces showing slow nested historical Git-process replay; no full product regression gate was cleared.

## P137 tangible packaging objective

Build on GitHub-hosted disposable Windows-2025 with Python 3.12 and pinned **PyInstaller 6.22.3**. PyInstaller is a packaging tool, **NOT a code-signing authority**. Its Windows packages are unsigned unless signed by an independently authorised key holder, and signed system Python does not make bundled Nayeon code approved.

The workflow constructs TWO separately labelled disposable Windows bundles:
1. **Actual standalone P132 application** frozen directly from `nayeon/desktop_alpha/local_byok_window.py` in onedir/windowed mode; this is the genuine app source, no new feature code, no test-mode arguments. It is scanned structurally as a Windows PE, hashed and **NOT EXECUTED** in unattended CI. Do not upload or distribute its unsigned .exe or submit it to Kristian.
2. **Independent fake-store smoke binary** frozen from `scripts/p137_frozen_byok_fake_tk_smoke.py` in console mode. Only this test binary is run, and only on disposable GitHub-hosted Windows. It requires a genuine `sys.frozen` Python process, exact GitHub Actions Windows repository + synthetic smoke gate, rejects native WinCred, constructs the real Tk local BYOK window with an injected fake user credential adapter, proves import/construction do not touch CredRead, presses review, rejects, confirms all possible native mutations remain zero, and closes.

Only three NEW paths: a bounded build workflow, the smoke-only script and this document. P135/P136, P132/P133 product code, original WinCred native adapter, frozen original P49/P96 and historical test guards are UNCHANGED. Historical branch-specific tests are not falsely reported green. P137 is a **packaging smoke**, NOT the three mandatory full product regressions and NOT an independent security review.

### Important packaging and security limits

- No signing certificate/private key, qualified Windows publisher/signer or Smart App Control owner GO has been supplied. The executable must report **NotSigned**; if a signature appears unexpectedly, investigate rather than claim production status.
- PyInstaller dependencies are version-pinned at the top-level but transitive dependencies may not have a fully hash-locked wheel manifest. This trial is not proof of reproducible supply-chain builds. Actual production must pin full dependencies and verify wheel hashes, SBOM and signing provenance.
- **P133 main desktop Connection launch bridge explicitly refuses `sys.frozen`**, and the source-mode `sys.executable -m ...` command is not production-safe. A reviewed publisher-pinned launcher for packaged main desktop must be designed and authorised before release. P137 does NOT change the bridge or bypass its frozen gate.
- Real standalone setup app is a test build ONLY; unattended execution could reach real WinCred after user input, so it is NEVER launched during P137 automation. Only fake-store separate bundle runs on disposable GitHub runner.
- Building executable with unsigned PyInstaller on isolated hosted Windows is permitted for synthetic tests but NEVER on Kristian under Smart App Control. No real provider API key, WinCred mutation, protected service, registry, TPM, user consent broker or production API call occurs.
- P135 full regression gate remains HOLD: three 600s timeouts; raw logs show 1,637 completed PASS, 37 FAIL, 7 ERROR, then one unfinished historical test, identical three times. The old test remains unchanged, and P136 live stack evidence shows expensive Git history replay not a confirmed deadlock.
- Qualified independent user-scope security review and test-governance acceptance still pending. Old privileged C1 G0–G6 remain OPEN with original P96 race and P124 pipe-transfer trust gap retained in frozen old code.

## Exit criteria

Success requires: exact three-path Git diff, clean checkout, full package build of BOTH app and fake-store smoke, genuine Windows PE headers, actual fake-store Tk smoke PASS, real app binary NOT executed, SHA256 of both executable files, explicit **NotSigned** status and absence of installer/cert changes. CI artifact retention should contain audit text only, never unsigned executables.

**P137 is an unsigned packaging feasibility exercise ONLY. BYOK C1 USER-SCOPED FIRST RELEASE HOLD.**
