# P182 — Fail-closed bounded Git batch transport candidate

**12 November 2026 | OM v2.1 | Experimental isolated candidate; PRODUCTION RELEASE HOLD**

## Exact authorised work

P182 is based directly on original P181 commit \`0e4cd7065eb2ebd0d3eb247813b52c0fcd75cb00\` (PR #106 remains draft, unmerged). Only three P182 candidate/documentation/workflow files may be created. No modifications to original \`nayeon/\`, historical \`tests/\`, original P180 experimental prototype or P181 adversarial review; original Kristian product worktree is left as-is.

Original P181 authentic Windows [run #43313585744](https://github.com/krismcan/Mark-LV/actions/runs/43313585744), [artifact #13987327101](https://github.com/krismcan/Mark-LV/actions/runs/43313585744/artifacts/13987327101), ZIP SHA256 \`E64841054B845A7B2012BA33B48A36F6376BCB191F4F2AD9474C5685118869D4\`: 20/20 original native P180+P181 tests PASS as internal negative evidence, including two tests that **demonstrate** serious P180 limitations, not approval. Their exact original source and original six-finding register remain immutable.

## New experimental design — two immediate mitigations

P181 SEC-P181-01: \`stdout.readline\` and \`stdout.read\` had no deadline. The **new isolated** \`FailClosedGitBatch\` serialises each read behind a lock and executes the entire Git request/write/response read/content-hash verification in a daemon worker thread with one bounded monotonic \`join(timeout)\` budget. If any step blocks, the control thread irrevocably marks the session retired and calls \`kill\`/bounded \`wait\` on the child before returning a timeout **failure**. Neither success nor another request is accepted on the poisoned instance. The worker is daemon-only to protect even a malicious blocked synthetic pipe from preventing diagnostics from finishing.

P181 SEC-P181-02: the earlier prototype accepted another synthetic valid response **after** a malformed header. P182 instead marks the session retired after **any** invalid caller OID, wrong object mode/type, mismatched Git SHA1, truncated data, malformed header, missing trailer, pipe error, unexpected child exit or deadline expiry. A stream cannot be reused after an exception. There is **no caching** of Git data or security decisions.

Git process launch is explicit and sanitises common \`GIT_*\` process overrides for the experiment, disables global/system configuration and uses an absolute resolved executable. This is a *candidate* hardening step, not a complete independent signer/peer/trust proof.

### Genuine native Windows evidence criteria

1. Authenticate exact branch ancestry, clean source, only three new paths and all 171 untouched historical \`tests/test_*.py\` modules. Original P180/P181 scripts and original \`nayeon/\` and \`tests/\` trees must match P181 byte-for-byte.
2. Download P181 original 20/20 real Windows evidence using ephemeral read-only GitHub token; verify ZIP SHA256 and member CRC, original log SHA256, full unittest footer, original six OPEN findings, source head and H/C/R release hold.
3. Run the original P180 **eight** cases and P181 **twelve** adversarial/detection cases unchanged, plus P182's **twelve** separate candidate security cases, using genuine Windows Server 2025/Python 3.12 on an isolated hosted runner. Expected 32/32 complete tests with real native exit 0. These are candidate/diagnostic tests, **not full-product regression acceptance**.
4. P182 synthetic negatives test malformed headers, wrong Git object type, altered payload/hash, premature EOF, absent/malformed trailer, dead child, invalid OIDs, cross-response mix-up and a child that never responds; timeout must retire and kill the fake child within the configured deadline. A genuine isolated Git batch process separately reads the same actual immutable historic blob twice and matches each fresh response to \`git show\` bytes.
5. Archive true raw stdout/stderr, native process exit, test counts, SHA256 and source-bound machine-readable original P181 findings. P181 HIGH findings remain **OPEN** pending qualified independent review and original full-product regressions, even when this new candidate passes a narrow adversarial suite.

### Still outside this experiment

The P182 batch candidate is NOT integrated into any historical security verifier. It is not evidence that the P135 original triple 600-second full-suite Windows timeouts, P178 original two FAIL cases, P179 pin-witness timeout or P175 frozen security source-era conflicts are resolved. It does not demonstrate every-call live Win32 disk/index/HEAD/tag seal and source impersonation/tamper negative equivalence, process-parent provenance, full fail-closed C1 key handling, signed install policy, or original user-scope/privileged-service admission.

Qualified decisions GOV-01, GOV-02, SEC-03, SEC-04, REL-05, REL-06, REL-07 all **OPEN**; P181 six independent security findings remain OPEN for product integration; no qualified external review signoff, original 3 complete native full-product Windows regressions **0/3**, G0–G6 OPEN, Windows main/helper/installer signer/SAC/WDAC approval absent.

**Never enter a real credential, touch native WinCred/provider network, privileged service, publish/merge/tag/release or falsely reconcile Google Drive MASTER/dashboard as a released product. BYOK C1 PRODUCTION RELEASE HOLD.**