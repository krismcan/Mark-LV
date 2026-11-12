# P180 — Isolated sealed Git blob transport equivalence prototype

**12 November 2026 | BYOK C1 OM v2.1 | Prototype only | PRODUCTION RELEASE HOLD**

## Verified P179 performance problem

The untouched original historical BYOK-B pin-witness test timed out after 130 seconds on real Windows in P179 [run 43298597044](https://github.com/krismcan/Mark-LV/actions/runs/43298597044), GitHub [artifact #13979748295](https://github.com/krismcan/Mark-LV/actions/runs/43298597044/artifacts/13979748295), ZIP SHA-256 \`B85BCB8B33DC979AEF805C2C7CCD4EDB1001F06B42A7A8CAFA7FDD23B9162BAB\`. Original uninstrumented adjacent test 1/1 PASS, native exit 0. The profiled original witness native exit 124, no unittest footer, 3888 genuine completed Git subprocess calls including 2391 \`git show\` (79.527s cumulative). The original two FAILs from P178 full-module test, P135 three 600s full-discovery timeouts and P154 23/83 unresolved suffix modules remain genuine and unwaived.

## Hypothesis and experimental boundary

Repeated *new process startup* for an immutable pinned historical \`git show COMMIT:PATH\` object read dominates Windows regression overhead. A single **ephemeral Git \`cat-file --batch\` process** can return the same immutable full SHA-1 Git blob payload for each requested object without any cache or historical source/test rewrite.

**P180 does NOT apply this transport to historical verifier code.** It is a separate, isolated benchmark/protocol negative experiment, comparing direct real \`git show <40-hex-commit>:<canonical-path>\` to fresh \`git cat-file --batch\` requests. No original test is substituted, monkeypatched, bypassed, muted, sped up by artificial cached verification, or reclassified as a pass.

### P180 actual Windows acceptance for diagnostic ONLY

- Exact P179 HEAD \`8e74b5c075c5bf110618c9cca6af7fdda39a56dd\`; only three new paths (this doc, \`scripts/p180_windows_sealed_blob_transport_equivalence.py\`, \`.github/workflows/p180-windows-sealed-blob-transport-equivalence.yml\`). Complete tracked original \`nayeon/\` and \`tests/\` trees and 171 original Python test modules remain identical.
- Direct original P179 Windows ZIP SHA256/CRC/member inventory, original native control PASS and historical witness TIMEOUT exit 124, original native log SHA256, 3888 Git commands/2391 real \`show\` commands, seven unsigned qualified review decisions and H/C/R preserved.
- Genuine GitHub-hosted Windows Server 2025/Python 3.12 with source-verified SHA-1 object format. Construct each immutable object ID by a fresh \`git ls-tree <exact commit> -- <canonical source path>\` with exact \`100644 blob <40-hex-ID>\tpath\` response; reject link modes and omitted/ambiguous path records.
- **Eight separately versioned original P180 adversarial unit tests**: rejects non-hex OIDs, unsafe/ambiguous path aliases, mismatched OID/type/header/oversize responses, payload tampering/missing terminator, and verifies preserved original frozen Code Integrity false + source tree. A real two-request round-trip for the same object proves it is **not cached** and has byte equality to \`git show\`.
- Read-only direct-versus-batch test makes at least 9 immutable genuine repo objects from historical P140 and current P179 source. Repeat every actual object exactly **three fresh times** in each transport. Every direct Git \`show\` and batch response is rehashed as a Git blob SHA-1, then response SHA-256 arrays compared in the exact same order. No Git object ID, content or source pin is learned from a supposed current C1 production authority.
- Publish original genuine Windows complete eight-case stdout/stderr, process exit, SHA-256, full Git byte-equivalence and timing ledger; diagnostic collector succeeds only if every expected native case completes and each byte matches. Timing is **prototype-only**: runner variance, batch-stream process overhead and object selection do not prove an equivalent production change is approved.

### Security and integration exclusion

Any proposal to integrate a persistent batch Git process in a historical verifier changes security-critical read semantics: immutable source/version authority, object-type acceptance, path policy, reparse/mode/symlink protections, error propagation, process lifetime, tamper race prevention, exact every-invocation verification and negative canary coverage must be independently reviewed **before** a source change. Fail-closed security must remain the same or stronger. This P180 prototype does **not** authorize implementation in original source or tests, real API key operations, native WinCred effects, provider validation, C1 privileged G0–G6, signing/SAC/WDAC, merge/tag/release or Google Drive MASTER/dashboard production-release status change.

**Seven qualified GOV/SEC/REL independent approvals OPEN. Three genuine complete full-product Windows regression passes 0/3. Frozen release signer pins unissued. BYOK C1 production release HOLD.**