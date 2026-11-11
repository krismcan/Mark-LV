# Nayeon v1 — P161 original Phase8.37 Git-subprocess cost and source-seal latency profile

**11 November 2026 | OM v2.1 | exact-parent isolated draft | PRODUCTION RELEASE HOLD**

## Immutable source authority and root cause hypothesis

P161 begins strictly at genuine P160 verified Git SHA 725181149b7bb3f1002c9d36b7fc8e86c78020d7 (open draft PR #85). P160 genuine hosted Windows Python 3.12 run 43076701416, artifact 13880234908 (ZIP SHA-256 331CB6E742CEAE749AD832C1C17A87C789A1A28E91DB7E325F2C63D50E18E0CC), ran five individual unchanged original historical Phase8.31/32/33/34/37 tests. Real 4 original focused PASS, one original Phase8.37 80-second TIMEOUT without footer. Raw P160 faulthandler stack snapshots show the 8.37 method spending wall time inside Windows subprocess.check_output and historic phase_8_30_scope_migration._git, called by nested Phase8.32, Phase8.34, Phase8.36 and Phase8.37 seal readers.

The original Phase8.37 method loops over nineteen distinct pinned historical 8.36 source files. For each candidate it exercises an adversarial tamper injection and re-executes an entire historical source-integrity path. This is security-important deliberate negative testing. Its complete native behaviour cannot be replaced by an elapsed-time guess, an unapproved caching layer, a skipped test or a synthetic green.

P161 creates exactly three additive files on a separate draft branch: this document, one diagnostic runner and a hosted Windows workflow. **No product source, frozen original tests, historical P76/P85 refusal, source pin, P139 Win32 native opened-handle integrity, P140 signed frozen admission, Code Integrity policy, real credentials or Kristian's original worktree are changed.**

## Real Windows diagnostic design

1. Hosted GitHub Actions **windows-2025 Python 3.12**; exact P160 parent, clean checkout, Git SHA/event check, only three additive paths, 170 current tracked unittest modules and pinned original test SHA-256 A95A967BA892FECADF0811B38C51AE61CD268159766A91B1DC448CF4B1B5C426. Confirm original source blobs for the five historical Git readers, P139 native trust guard and original P76 test are byte-identical with P160.
2. Reuse the **unchanged** P139 native Windows opened-handle canonical fixed-local C: TEMP proof before any child. Run only the one unresolved original fully qualified Phase8.37 case under 105-second hard cap. It executes via genuine original unittest in a disposable separate Windows process with no API keys, WinCred/provider operations or privileged changes.
3. Outside original frozen code, wrap Python **subprocess.check_output** in the diagnostic child, delegating all arguments, returns, exceptions and source bytes **unchanged**. Capture actual Git invocation ordinal, duration, timing, error kind, Git verb, argument count, *hash of complete command arguments*, output byte count and bounded historical call-chain file:function labels. Do **not** retain raw Git args, passwords, source contents, API keys or actual stdout/stderr. Every recorded call is emitted/flushed to an append-only JSONL receipt; timeouts preserve completed calls and the real child unittest output.
4. Original test executed unchanged with real native exit 0, nonzero or 124; record any genuine unittest footer, original failure identifiers, elapsed duration, ordered per-call raw JSONL and its SHA-256, full original unittest stdout/stderr and SHA-256, aggregated count and cumulative measured milliseconds by Git verb and by repeated hashed command pattern. Distinguish **completed calls** from in-flight time on test timeout, and from subprocess spawning time and all other overhead; do not exaggerate what the profile proves.
5. A successful CI evidence collector means complete, source-bound and internally consistent evidence, not that original test or module passed, much less a full-product acceptance. A killed child at hard cap still retains *TIMEOUT*, no footer. No original security test can be marked PASS unless genuine native exit zero and full original unittest footer say so. Even a PASS for this isolated case does not clear the original full Phase8.37 module.

## Decision criteria

P161 should establish the authentic command count and dominant Git commands so a future source-preserving, independently reviewed performance solution can be scoped. Before changing any historical fixture, inventory, Git adapter, code source pins or any security mechanism, require independent qualified reviewer and explicit branch-aware historical governance. A safe future optimisation must prove byte-identical authentic Git results under adversarial tag/ref/index/worktree/aliases and genuine native negatives, without caching/memoising untrusted mutable state.

No automatic migration of the current branch into old exact P76/P85 acceptance or any test bypass is permitted.

**Still unsatisfied:** P135 three whole-product Windows runs all TIMEOUT at 600s, 0/3 accepted complete product regressions; P150 original BYOK scope TIMEOUT after 190s; P159 complete Phase8.30 original failure and five original full-module timeouts; P86/P87 old assertions, Phase8.31/8.32 old static contracts and WinCred import-closure hold; independent named user-scope security review NOT OBTAINED; P140 signed/pinned actual main/helper/installer and SAC/WDAC policy-owner GO missing; privileged C1 G0–G6 including P96/P124 OPEN. No Git merge, tag, signed release, production WinCred, provider API validation, user API key, Windows protected machine mutation or original Google Drive MASTER release workbook/dashboard update.

**P161 is focused native evidence only, not production authorisation.**
