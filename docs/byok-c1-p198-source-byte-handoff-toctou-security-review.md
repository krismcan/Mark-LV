# P198 — Source Admission-to-Consumer Byte Integrity & Post-Validation TOCTOU

**14 November 2026 | Isolated native Windows security lab | H/C/R = HOLD / research / HOLD**

## Exact source evidence and permitted paths

Start from exact P197 commit d881936573813d8cd76107cbe67e1297b983d5bf, draft PR #122, genuine Windows Actions run 43495699244 and evidence artifact 14071452154. ZIP SHA-256 91A22E87BBBAB407EC1EDD83AE59AD923F6D33A0D70026A31AA63FB1B7FE3CE0, original Windows 40-case raw log SHA-256 92B884C4E0178A0E369DAD3E6F8971E9BE4824B021EFD5AA5290797400985787, ledger SHA-256 D9F75760A140DA961CA624BC9638B509DDE496DB51ABB552DBC4454B834A8D13. Source_before equals source_after; OS exit 0, complete 40/40 selected test OK footer; original full-product native Windows accepted 0/3.

P198 adds only three new audit-only files: scripts/p198_windows_source_byte_handoff_toctou_review.py, this review document, and .github/workflows/p198-windows-source-byte-handoff.yml. Exact P197 Git ancestor and prior immutable P195, P196 and P197 source witnesses are required. Original product and tests/nayeon Git subtrees must be unchanged. Kristian original worktree D:\Nayeon\BYOK_C1_PRODUCT_20261028, original HEAD e3612279cb972e68e2487702183d5bf5b8f6c4a1 and 17 pre-existing working changes must be preserved without edits.

## Threat: validation ends before execution

The P194–P197 experimental reader only established original signed/prebound fixture provenance, original file physical FileId, USN and journal continuity at the instant of read, then returned approved bytes and released the source HANDLE. Another actor can replace the path AFTER successful validation. A later separate consumer that reopens the same filename can receive substituted bytes. This is not contradicted by a correct earlier FileId or USN comparison; it crosses a new trust boundary.

P198 compares two diagnostic consumer designs. One ordinary independent Python process receives the already-validated bytes directly over stdin and hashes them; it never receives a path or executes those bytes. Another ordinary Python process reopens a path after a separate Windows child has replaced the original synthetic disposable source through os.replace. The validated original digest correctly refuses the substituted bytes. Critically, the path reopener can also ACCEPT untrusted substituted bytes if its caller supplies a fraudulent expected digest — an explicitly preserved UNSAFE ACCEPTANCE control. A digest passed in a command-line argument by an untrusted caller is not an independent security authority. No production trusted execution/loader identity is established.

No source bytes are executed as code, imported, unpickled, interpreted as scripts, loaded as DLLs or dynamically compiled. All subprocess code is hardcoded audit-only hash/fixture logic. Mutations target a random synthetic C: test directory on a hosted Windows runner and never Kristian's product tree, a live credential, a privileged service or a real source installation.

## Selected authentic native Windows matrix

Retain the 40 original source-era P194–P197 tests unchanged. Add exactly ten selected P198 cases (50 total, NOT full-product tests):
- P198 41: exact validated bytes provided to genuine independent process stdin and original SHA observed;
- P198 42: separate Windows process replaces source after read, later path reopen with original SHA REFUSED;
- P198 43: the prevalidated original bytes passed through stdin after replacement remain byte-identical;
- P198 44: malicious caller changes both path bytes and claimed SHA, path consumer accepts UNSAFE SOURCE — explicitly observable review risk;
- P198 45: one-byte tampered stdin REFUSED;
- P198 46: truncated stdin REFUSED;
- P198 47: missing or malformed claimed SHA REFUSED;
- P198 48: oversized stdin REFUSED;
- P198 49: two independent actual Windows consumers receive the identical original stdin source;
- P198 50: a fresh source validation after replacement REFUSED by the original physical pinned FileId policy.

The input digest to the hash-only child is supplied by the caller; it is not independently enrolled. Passing these cases does NOT prove loader signing, host/executor identity, inherited/duplicated HANDLE security, trusted process chain, sealed IPC, anti-replay, TOCTOU after the consumer starts, malware-level tamper resistance, actual original product source or Phase 10 production integration.

## Required security decisions, not granted by the experiment

SEC-P198-BYTES-01: use a trust-preserving byte stream or independently verified held file object, never rely on stale approval before a different path lookup.

SEC-P198-EXEC-02: production must establish signed consumer/loader/helper/installer identity, exact launch path, caller provenance, version, Code Integrity/WDAC/SAC policy and mitigations; a static Python digest program is NOT a trusted loader.

SEC-P198-IPC-03: authenticate producer/consumer relationship, object/handle ownership, message framing, replay resistance, source digest from independent authority, and lifecycle error closure.

SEC-P198-LIFECYCLE-04: explicitly cover post-verification path replace, ADS/hardlink races, parent rename, consumer process restart/crash, privilege escalation, mutable module imports, and post-load memory replacement. A time-bounded USN observation is not an indefinite source seal.

SEC-P198-HISTORICAL-05: original historical full private BYOK-B ADS admission gap remains UNPATCHED, P195 unguarded ABA admissions preserved. Original Git/index/tree/HEAD, all 23 literal B source pins, current Phase 10 privileged gate and genuine complete Windows full-product execution remain unintegrated.

Original P135, P175, P178, P179 and PERF-P187-01 failures/timeouts remain UNWAIVED. External qualified GOV-01, GOV-02, SEC-03, SEC-04, REL-05, REL-06, REL-07 reviewer decisions OPEN; privileged G0–G6 OPEN; full original Windows acceptance 0/3. Do not label assistant-prepared review an independent qualified signoff.

No actual credentials, live provider network validation, Credential Manager production writes, privileged admission, PR merge/tag/release or Google Drive MASTER/dashboard release reconciliation. H/C/R remains HOLD / isolated synthetic Windows process custody experiment / HOLD.


## Authenticated initial P198 Windows outcome — 14 November 2026

**Source SHA** 5343bd95b7d46ba8fff28902a011dfd8188deb5e. Actual hosted native Windows Actions run 43570270939, artifact 14103897827; ZIP SHA-256 **249D467ECC6CB3EE45D219481A6BCA671180369C0569A91AF0045A0610B8E361**, member inventory exactly two, ZIP CRC passed:
- p198_native_Windows_admission_consumer_50.log, SHA-256 **DEE6F0F5217EDB827A5332CC594948354D41985A42A948710DCFC5C8CD492C49**.
- p198_source_consumer_HCR_ledger.json, SHA-256 **4A7D81591F6056A8E3946B6AF67E39BCC627A354A8B78A7559F81BCF920DF3DA**.

Actual Windows selected test outcome **50/50 PASS**, native OS exit 0, complete 4.700s unittest OK footer; source_before == source_after; original genuine P197 ZIP and inherited 40 selected source-era cases reauthenticated. H/C/R = HOLD / experimental source-to-consumer bytes review / HOLD; accepted complete genuine full-product regression count 0/3. The 4.700s is a **narrow test duration, not a production performance measurement**.

**Original failed P198 runs preserved, not rewritten:** Run 43570128344 source-custody/workflow setup completed but audit script had a Python line-continuation syntax error before tests; no raw test files were uploaded. Run 43570223941 (archived artifact 14103736928, SHA **0AB19DD33F02B346A85EC6726F13BB1B9D2E069DDC44364229FF4359C5B5E49B**) ran 50 actual Windows tests and failed 9 new consumer cases because the static hash-only child caught its own normal SystemExit via BaseException; native log and HOLD ledger were retained. The child exception contract was corrected, not any historical test or security expectation. These diagnostic failures do not count toward accepted regressions.

Native success demonstrated the security issue:
- Real independent Windows child replaced a disposable C: test-source path after earlier pre-bound validation ended and the HANDLE was closed.
- Another independent child reopened that original path and saw changed bytes. Given the **original** expected approved source hash, it refused.
- The original approved byte content held in memory was still correctly transferred through standard input to a new hash-only child after the path replacement.
- **Critically unsafe control:** if a caller can change both the replacement path file and the hash presented to the consumer, the consumer admits the substituted bytes. This is not safe admission and must not be mistaken for signer/authority trust.
- Fresh original pre-bound P194 source revalidation after the path replacement refused the changed leaf FileId.
- Separate-process tamper, truncation, missing/malformed digest and oversize cases all refused. Two fresh subprocesses observed identical prevalidated byte payloads.

**Important claim limit:** The validated source was never executed. No trusted code loader, process signing, real Windows HANDLE transfer, protected parent-child IPC, trusted independent digest authority, code signing, dynamic import, service launch or production BYOK admission was demonstrated. Source-byte transfer between ordinary Python processes with untrusted caller-supplied digest is a diagnostic, not a production execution-security mechanism. The historical full private BYOK-B ADS gate remains unpatched. Qualified independent security reviews, actual original full product native Windows regressions and signed installer/helper/main process admission remain OPEN.

**Experimental closure:** A final documentation-inclusive source commit requires its own real Windows run before P198 can close as an experimental checkpoint. All original product and historical code remain unchanged; PR remains DRAFT and UNMERGED, production release HOLD. No authoritative Google Drive release workbook/dashboard reconciliation is appropriate without an actual release.
