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
