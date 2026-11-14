# P199 — Trusted Consumer Identity, Signed Loader Provenance and Authenticated Handoff Review

**14 November 2026 | H/C/R: HOLD / isolated synthetic signing and native Windows identity research / HOLD**

## Authoritative source and immutable predecessor

Exact Git parent **9b80021a5a3a5b49c54dcc150d0a5f7f0fff4a83**, P198 experimental draft PR #123 and authentic native Windows run **43570388423**. P198 artifact **14103539000**, ZIP SHA-256 **E11281D520BB5D161A69589152BDAC523BDDEE27DA13BF1D4DDC9E3C39D59696**. Original member SHA-256: p198_native_Windows_admission_consumer_50.log = B76CE4269ED0CCDCAE166920DB051D96F2F8461F2453DCB059CD84DD811A98EE; p198_source_consumer_HCR_ledger.json = 4B3A6375210430969C3222D5CB1565D24E5142CBBEFAC06375504BAB1502FE0D. Original 50/50 selected real Windows tests PASS, genuine OS exit 0, complete OK footer, before/after source identical, H and R both HOLD, full native unfiltered product regressions accepted 0/3.

Only THREE new paths are permitted on P199: scripts/p199_windows_consumer_identity_handoff_review.py, this review, and .github/workflows/p199-windows-consumer-provenance.yml. Source ancestry, exact P198 branch ancestor, original frozen historical Git, P195/196/197/198 witnesses, original tests and nayeon product subtrees must remain untouched. Kristian original Windows worktree D:\Nayeon\BYOK_C1_PRODUCT_20261028 at HEAD e3612279cb972e68e2487702183d5bf5b8f6c4a1, with 17 original changes, must not be written, staged, reset, or cleaned.

## Threat and trust model

P198 confirmed that a path is replaceable after successful validation, that passing previously validated bytes over stdin retains those bytes, and that **a caller who controls both source bytes and claimed digest can persuade a hash-only consumer to accept wrong content**. P199 adds an experimental consumer provenance chain without pretending to possess production signing authority.

**Cryptographic lab manifest:** ephemeral Ed25519 signing fixture, signed assertion over a hardcoded non-executing Python hash-only script's SHA-256, interpreter.exe SHA-256 and path, exact historical P198 commit, source SHA, audience and synthetic floor epoch. The verification public key and anti-rollback epoch floor are trusted inputs supplied independently by the test fixture **only**. No externally authenticated signer distribution, actual installed signed artifact, durable epoch, protected signer or OS-enforced loader binding has been established.

**Real process observation:** Windows API OpenProcess with PROCESS_QUERY_LIMITED_INFORMATION and QueryFullProcessImageNameW used on the real active child PID **before** sending bytes. Child receives a bounded one-line JSON frame via stdin containing a 128-bit random nonce and base64 data. Child computes a SHA-256 over data but **never executes/imports/evals/unpickles** the source. Parent compares the child-reported PID/parent PID, nonce, source SHA and byte count with OS-observed process and authenticated synthetic source bytes. In-memory replay rejection is a local fixture, not durable replay prevention or secure IPC.

**Strong negative finding required:** a malicious inline Python command script launched by the **same** Python interpreter can emit a credible PID, parent PID, nonce, digest and count without actually reading source bytes. It passes all experimental *self-attested* process/digest/nonce checks because Windows process-image identity does not cryptographically bind the Python interpreter to the script passed in its command line. **This deliberate unsafe acceptance is a security finding, NOT a pass to production.** Merely signing a manifest describing intended script bytes does not independently attest the bytes that the OS actually executed.

**Authenticode observation:** actual hosted Windows PowerShell Get-AuthenticodeSignature reports installed Python binary signature status and optional signer subject as read-only review evidence. Even a Valid signature on Python.exe does NOT authenticate the inline script, the surrounding process parent, installed product publisher, privileged service trust, or data consumed. A missing/invalid signature cannot be waived or assumed valid in production. This lab intentionally has no production signed custom consumer/loader, no signing certificate, no Protected Process Light identity, no WDAC/SAC acceptance or WinVerifyTrust-based installation policy.

Official OS API specification: https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-queryfullprocessimagenamew and https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.security/get-authenticodesignature .

## Selected Windows test inventory (60, NOT full-product)

Preserve **50** original P194–P198 Windows security tests and their original failure/assertion semantics. Add exactly **10** P199 cases:
51. real Windows live child PID + QueryFullProcessImageNameW matches observed executable, fresh nonce and approved byte-digest laboratory receipt;
52. modified intended static script SHA vs signed fixture refused prelaunch;
53. alternate ephemeral signing key signature refused;
54. signed wrong historical release, synthetic older epoch and unavailable externally supplied signer/epoch refused;
55. actual Windows reported interpreter image is refused when expected executable path differs;
56. forged PID and forged parent PID in child reply refused;
57. a second use of an accepted nonce acknowledgement refused by bounded in-memory replay set;
58. single-byte mutation of the data the child actually hashes refused against original trusted test digest;
59. malformed JSON, malformed nonce and excessive frame size refused by the child;
60. deliberate malicious alternative script launched via **same** interpreter emits apparently valid self-attested PID, nonce and hash without reading source bytes, **UNSAFE_ACCEPTANCE**.

Do not weaken or delete historical negative cases to reach green. Successful tests in cases 51–59 are bounded observational lab behavior. Test 60 MUST show the untrusted code identity gap. The test's observable success is proof of the *failure mode*, not authenticated production execution.

## Required independent design decisions and unreleased work

1. Root signer trust: provision independently authenticated vendor/enterprise certificate policy and revocation, original installed executable/hardcoded module provenance **before** admission; establish durable anti-rollback policy, WDAC/SAC/Code Integrity review and signed release chain.
2. Image to executed code binding: same executable path and process PID do **not** prove inline script, DLL, imported module, bytecode, runtime or subsequently JIT-loaded component identity. Require reviewed code-signing/loader policy that constrains all executable content and refuses arbitrary alternate Python command code. No self-asserted script digest acceptance.
3. Producer/consumer identity: independent mutually authenticated trust anchor; verify OS peer token, SID, integrity level, process creation provenance, authorized service, transport ACL, session lifetime and injected/compromised code risk. Test-only random nonce and stdin are NOT authenticated IPC.
4. Exact validated data binding: preserve exact approved bytes, SHA from independent source authority, framing/size/replay protection and source FileId/USN/journal evidence up to the execution/use boundary; post-load changes require explicit policy.
5. Original system integration: current Git/index/tree/HEAD, 23 original BYOK-B literal source envelope, historical full-gate named ADS gap **UNPATCHED**, current Phase 10 paths, installer/helper trust and privileged G0–G6 remain excluded.
6. Independent qualified review: GOV-01, GOV-02, SEC-03, SEC-04, REL-05, REL-06, REL-07 are all OPEN. P135, P175, P178, P179 and PERF-P187-01 actual Windows product test failures/timeouts remain UNWAIVED. Native full unfiltered full-product regression acceptance remains **0/3**.

The preparatory review authored here is **not an independent security sign-off**. No actual production signer, credentials, real provider validation, Windows Credential Manager write, privileged operation, main/helper/installer release, merge/tag/release, or Google Drive MASTER/dashboard production release reconciliation is authorised. H/C/R remains **HOLD / isolated signed-fixture and native process experiment / HOLD**.


## Authenticated initial native Windows evidence — 14 November 2026

**Initial P199 test source HEAD:** aaaa709caf4a6da7b8ba3e7483f6b38db46ad2ee.
Genuine Windows Actions run **43571789945**, artifact **14105010422**, original ZIP SHA-256 **0446F87C67517A1B10600DF9A812F7FC4D37D0FA42849B4A28832E344B263814**, exactly two original members with valid CRC.
- p199_native_Windows_consumer_provenance_60.log SHA-256 **7541DC054019952F65E7B5DB2567DA3795B1BA0A16C5548BDA875644F9C50B32**.
- p199_process_provenance_HCR_ledger.json SHA-256 **ED39CEB85D6E967A1ADFB444A56192E878F349AA515AE83A190D441145B377A6**.

**Native selected tests:** 60/60 PASS, actual Windows process exit 0, complete unittest footer OK, total selected test duration 5.262 seconds (NOT a full-product performance benchmark); source_before == source_after; original P198 ZIP and prior 50 selected native cases authenticated before this run; H and R production release both HOLD, original full product 0/3.

**Actual hosted Windows Authenticode observation:** Get-AuthenticodeSignature on sys.executable returned **Valid**. This is genuine OS evidence for the interpreter binary only, not evidence of independently signed or pinned source-consuming inline code. Test 60 conclusively demonstrates the danger: the same signed interpreter.exe launched a different static inline script which did not inspect the delivered source but fabricated plausible PID/parent/nonce/digest fields. The lab parent **incorrectly admitted the forged receipt**, a deliberate unsafe negative test. An independently signed and enforced loader/content policy remains entirely unimplemented.

Original failed P199 Windows run **43571680392** is retained with artifact **14105005223**, ZIP SHA-256 **26E2B7EB807BC858848C4F9DC422E69A8819D6506E6AF587C6270C652272C4AA**. It ran 60 selected Windows cases, 58 passed and two new cases failed solely because the hash-only child returned lowercase hex SHA-256 while its strict parent protocol expected uppercase. The fix changed child output to uppercase, **without relaxing any original or new security refusal assertions**. Original failures remain in the raw log and H/C/R HOLD ledger.

This is **source identity and test-only signing research**, not a production signed loader, independent root CA, production authenticated process, actual safe privileged handoff, product fix, original historical BYOK-B ADS repair, all-Phase10 integration or external security acceptance. Source is audit-only. Independent qualified reviews and G0–G6 privileged admission remain OPEN. A new documentation-inclusive commit must be proven by its own source-matched genuine Windows run before experimental closure.
