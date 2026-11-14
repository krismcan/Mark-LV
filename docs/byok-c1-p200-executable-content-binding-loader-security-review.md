# P200 — Executable Content Binding and Trusted Loader Architecture

**14 November 2026 | Experimental native Windows source-content security review | H/C/R = HOLD / audit research / HOLD**

## Immutable predecessor and evidence authority

P199 final exact Git ancestor c42ecd83b5277acf5cd42b22fa140600665b0943, draft PR #124. Original genuine Windows run 43571915894 on exact parent HEAD, artifact 14104875946. Authentic complete ZIP SHA-256 AD3A76B216956A8FE7D17C82C608FACE0AC7798FA4A2145FC463BF62B7859A1F. Original member hashes: p199_native_Windows_consumer_provenance_60.log SHA C8F558B663E437E85D5FC552242B8E35C8DD66C24E80644F54F4819B6ACBF4FD; p199_process_provenance_HCR_ledger.json SHA DFE38D4138074ED41637B8BA67B90BB42148A20761B79BD1E99A8A08BC003691. ZIP CRC and two-member inventory authenticated. Genuine Windows P199 selected 60/60 tests, OS exit 0, complete unittest OK, source before=after, production H and R HOLD, full-product native Windows accepted 0/3.

P200 MUST descend exactly from P199 and change/add exactly three audit-only paths: scripts/p200_windows_executable_content_binding_review.py, this review, and .github/workflows/p200-windows-executable-content-binding.yml. Original historical product, frozen tests, prior P195–P199 security experimental scripts and their negative findings may not be changed. On Kristian original product worktree D:\Nayeon\BYOK_C1_PRODUCT_20261028 at original HEAD e3612279cb972e68e2487702183d5bf5b8f6c4a1, preserve all 17 existing changes and no write/reset/clean/stage.

## Security boundary under review

P199 showed that even with a valid Authenticode signature on the Windows Python interpreter.exe, the executing inline Python script could be substituted and could self-report convincing PID, parent PID, nonce, SHA and content receipts without consuming the original bytes. **Executable image identity is not equivalent to interpreted script/module content identity.**

P200 tests **on-disk executable-script content** as a separate principal from interpreter image. The P200 script fixtures are three tiny, hardcoded benign programs authored only for this test, under each test's random self-owned C: Windows temporary folder. There is no real code module, downloaded user script, Credential Manager key, or privileged loader. Every fixture either reads and hashes base64 standard-input bytes or prints a harmless fixed marker. One negative fixture reads but intentionally does not hash the delivered byte stream and instead reports a caller-supplied digest via benign environment variables. **No arbitrary untrusted code is introduced to execution.**

- Ephemeral lab Ed25519 signature binds intended static script SHA-256, intended disposable path, interpreter.exe SHA-256 and path, original synthetic source SHA, exact P199 predecessor commit, audience and a synthetic epoch floor. The trusted public key/floor are supplied within the test fixture; they are **not independently trusted** in the product.
- Native Windows actual observed interpreter identity via parent OpenProcess / QueryFullProcessImageNameW on the child process. This identifies the interpreter image, NOT the script bytes interpreted.
- A real separate ordinary Windows process performs os.replace on the disposable script after the original lab-signed manifest and script hash validation. The next Windows child Python process opens the same pathname and executes a **different static harmless script**; its output is observed. This proves the post-approval path-to-execution TOCTOU remains open when a script path is reopened.
- An additional test has the parent pass the exact validated static script bytes through Python -c rather than reopen the replaced script path; this preserves the **parent's chosen command string** in that test, but is NOT OS-backed code-execution attestation, mutually authenticated IPC, signed custom binary, or kernel-protected loader integrity. A compromised parent/OS can still substitute execution.
- The wrong-code script can also self-report the original approved marker, source hash and source length, even while ignoring actual bytes. This is a mandatory **UNSAFE ACCEPTANCE** review result, NOT a secure runtime identity proof.
- A fresh prelaunch hash comparison refuses already-replaced code. However **read/compare followed by a subsequent filename-based launch is itself non-atomic** and cannot close the between-guard-and-exec race; it is NOT accepted as a production solution.
- Interpreted source modules, script path names, command-line flags, live child image paths, claimed digests, signed JSON manifest, and stdout are all different security objects. A signed interpreter and a signed assertion of an intended script SHA do not prove what a different process actually executed.

## P200 native Windows selected cases (70; NOT full product)

Retain all 60 historical source-bound P194–P199 cases and exact original failure/refusal expectations. Add 10 P200 selected native Windows cases:

61. An approved hardcoded benign script file on disposable C: is validated and actually executes in a separate Python process; real interpreter image observed, input hash and source length match.
62. After valid signed manifest and file SHA validation, a separate genuine Windows process atomically replaces the disposable code path, and later actual Python file-script execution runs the **different benign script**. Preserve explicit post-validation **UNSAFE** event.
63. Already-changed script detected by a fresh prelaunch hash guard; fail closed, without claiming this closes subsequent races.
64. Source-path replacement cannot change exact prevalidated parent-supplied inline script bytes in a lab Python -c invocation. Document this as test-only producer-controlled invocation, NOT actual trusted execution.
65. Manifest signed by the lab signer but binding alternate script SHA is refused.
66. The same manifest signed under a different ephemeral key is refused.
67. Signed wrong release commit and lower synthetic epoch are refused.
68. Missing lab trusted signer or epoch floor fail closed.
69. Signed wrong admitted source SHA and corrupt/incomplete manifest fail closed.
70. Replaced static script self-reports original marker and hash without hashing the delivered data; naive caller acceptance is **UNSAFE SELF-ATTESTATION**, preserved as an explicit negative finding.

All selected tests are genuinely executed on Windows 2025 hosted runners with original P199 artifact SHA/auth, source-before/source-after Git pin, genuine native OS return codes, full raw unittest log and H/C/R JSON. Preserve failed runs, raw traces, OS exits, log hashes, ZIP CRC and source identity; never change original assertions for green. Use a disposable autocrlf-disabled exact-HEAD clone, not Kristian product source. No real journals changed or privileged/disk operations executed.

## Production trust controls which P200 does NOT deliver

SEC-P200-EXEC-01: A production executable loader must be independently Authenticode-signed by an approved publisher and validated under actual WDAC/SAC/Code Integrity policy. Signature verification, revocation, pinned publisher, release and installation trust cannot be supplied by an ephemeral fixture. A product Python script cannot rely on the signature of python.exe.

SEC-P200-CODE-02: Bind all possible interpreted scripts, modules, DLLs, command-line content, dynamic imports, dependency trees and JIT/plugin paths to a trusted release and OS-enforced execution code identity. An OS process image alone cannot prove dynamic or inline code provenance.

SEC-P200-RACE-03: Hold or otherwise OS-enforce immutable source/executable identity through load, prevent path reopen after approval, handle reparse/hardlink/ADS, ACL and privileged mutation, remapping and post-load tampering, and separately prove true cross-process HANDLE/security token binding. A prelaunch file hash is non-atomic and not a substitute.

SEC-P200-IPC-04: Require independently trusted producer and consumer identity, secure transport/handle/object custody, replay/size framing and authorization. Self-reported hashes, nonce, parent PID or environment variables are spoofable and not independently authenticated.

SEC-P200-ROOT-05: Establish independent initial signer trust and crash-safe durable anti-rollback/epoch, revocation and recovery. Local Windows Credential Manager, DPAPI, local hashes, simulated Ed25519 fixture and per-file USN observations do not independently establish this.

SEC-P200-PRODUCT-06: Original historical full private BYOK-B named ADS source admission gap remains **UNPATCHED**, as do the original live Phase 10 source, 23 literal original B pins, installer/helper/main and privileged G0–G6 trusted service integration. Prior P195 reversible ADS/hardlink ABA, P198 source-to-consumer path substitution, P199 signed-interpreter spoof negatives all preserved.

SEC-P200-REG-07: P135 original full Windows native timeouts, P175 five historical native failures, P178 B gate timeout + two failures, P179 pinned source timeout and PERF-P187-01 remain unwaived. Accepted completed unfiltered native Windows full product regressions **0/3**. External GOV-01, GOV-02, SEC-03, SEC-04, REL-05, REL-06, REL-07 reviews are OPEN, not replaced by this author review. G0–G6 and signed binary Code Integrity/WDAC/SAC GO are OPEN.

**Release prohibition:** No real credentials, key entry, Credential Manager production writes, live provider validation, privileged service deployment, PR merge, Git tag/release, or Google Drive MASTER/dashboard *production release reconciliation*. PR DRAFT and UNMERGED, H/C/R always HOLD / experimental audit / HOLD. An actual signed-loader product implementation and three full Windows acceptance runs need separate trustworthy evidence and qualified independent review.
