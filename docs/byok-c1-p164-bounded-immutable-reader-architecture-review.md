# Nayeon v1 — P164 Bounded Immutable Git Reader Architecture and Windows Lifecycle Review

**11 November 2026 | OM v2.1 | Non-integrated defensive prototype | PRODUCTION RELEASE HOLD**

## Scope and authority

Exact predecessor P163 SHA **51ecaa8eaf2e3f092d1006cf2ffba4f402c1de87**, draft PR #88 (unmerged). P163 genuine Windows evidence run 43090896372 passed 25/25 selected actual unchanged original security cases and rejected 16/16 synthetic corrupt candidate objects, while retaining historical P76/P85 refusal and P140 unapproved signer/Code Integrity gates. A qualified independent external reviewer has **NOT** signed off.

P162's separate Windows research measured 95 exact immutable Git blob reads at 2.99228 seconds using individual original Git show calls versus 0.05729 seconds through a long-lived Git cat-file --batch process, with all 95 byte-identical. P161 traced 2,470 original Git subprocess calls accounting for 93.892 seconds in one authentic historical Phase8.37 negative source-pin method. These are research findings, **not** authorization to install an optimiser into original security readers.

P164 is a **new isolated branch** from that exact P163 commit and adds **only three evidence files**: this design/reviewer dossier, one native Windows bounded-lifecycle candidate runner, and one hosted Windows Actions workflow. No product code, original historical test, original security policy, git-ref guardian, P139 opened-handle verifier, P140 signed companion, or credential/UI code is changed. Kristian's original dirty product worktree must remain untouched.

## Typed immutable-object interface and dependency graph

Input to a future approved reader can only be the tuple of **canonical literal original trusted path** and **literal SHA-1 Git blob object ID** already derived from the exact frozen historical protected commit tree. It cannot accept caller-provided branch, tag, HEAD, commit selector, arbitrary path or mutable file system state. This candidate validates the complete path/OID pair against the independently authenticated fixed historical tree and canonical 19-path SHA-256 pin map *before any IPC*. A case-changing alias, Windows backslash spelling, parent traversal, unknown path, wrong OID, missing OID, or mutable HEAD expression is rejected with zero requests sent.

For each actual fixed-OID response, verify the **exact** Git batch header, raw object type blob, expected object ID, bounded length, full native-pipe byte count with partial-read accumulation, delimiter, computed Git SHA-1 blob identity and original path-specific SHA-256 pin using unmodified 8.36 digest rules. Compare real candidate bytes against genuine original Git show bytes for each of all 19 pinned historical paths; no stale result/pin cache and no runtime test monkeypatch.

All mutable trust assertions remain in their **original** source functions, without any change to their read order, semantics, branch/tag/ref assertions, ancestry, worktree/index enumeration or adversarial reachability. A fresh immutable object reader by itself cannot validate these changing Git claims. Production credential storage, WinCred, provider/network access, signed executable admission, protected Windows filesystem actions and release are outside P164's authority.

## Bounded Windows process lifecycle and native adversarial matrix

The isolated candidate opens one disposable Git child for actual Git cat-file and one test-owned child for each synthetic fault. It enforces one active pipe request per process with a non-blocking per-session mutex; a real child read runs in a bounded daemon thread and the parent owns the request deadline. A timeout must irreversibly retire/terminate **only the owned test child** and refuse subsequent requests. On malformed, short, invalid, missing, substituted, oversized, tampered, or improperly framed reply, session fails closed and also refuses reuse. Never automatically retry a timed-out identity or switch to a permissive source.

All tests are confined to a genuine GitHub-hosted Windows Server 2025 Python 3.12 runner, with the unchanged P139 native opened Win32 handle/no-reparse policy proving a fresh self-owned C: temp root, short-lived locally scrubbed environment and no actual API credentials or production WinCred operations.

Real Git test: **19/19** immutable source OID-to-path, original SHA256-pinned byte equality against unchanged original Git show, within one reusable process. Pre-IPC test: **7** mutable-ref/path/alias/wrong-ID requests must all fail without sending a request to the child.

Native child protocol cases:
- Two correct / partial Windows pipe replies that must match authentic original source bytes.
- Nine negative cases: wrong Git object OID; forged non-blob type; oversized announced object rejected before allocation; changed blob bytes; truncated stream; early EOF; child stalled before header; child stalled mid-body; corrupt final delimiter. Each failure must retire the child and a second request must be refused. The two hang cases must hit an actual bounded deadline and terminate only the owned disposable child.

These focused design tests are NOT equivalent to actual historical P76/P85 branch positives, negative branch adversaries, a full original Phase8.37 module, or the full Windows product regression triad. A Windows Actions job green means ONLY that its source-bound diagnostic measurements and negative outcomes were recorded.

## Qualified independent security reviewer decisions — still OPEN

Before integrating a real reader, require an identified, qualified reviewer who is independent of the author and can sign a dated verdict covering: fixed-OID/tree/path provenance and Git SHA1 collision/content identity considerations; mutable branch/ref/index/worktree race and TOCTOU boundaries; protocol desynchronization on extra/trailing output, unexpected exit or same-user process interference; pipe deadlocks, process tree lifetime, Windows job objects/ACL and deadline guarantees; original P76/P85 exact branch and original historical tests; robust negative equivalence under tamper/race/alias; repro with full unfiltered product regressions. This P164 bounded process prototype is a reviewer aid, not an approved production implementation; a daemon thread with parent killing the child cannot be automatically assumed sufficient for production thread lifecycle under arbitrary Windows failures.

Reviewer name and qualification: NOT OBTAINED. Signed review: NOT OBTAINED. Source-governance/versioned current-branch security contract: NOT OBTAINED. Real signed/pinned main/helper/installer, protected load-time Code Integrity policy and independent policy-owner GO: NOT OBTAINED.

## Historical release HOLD remains mandatory

P135: 0/3 accepted whole-product Windows regressions after three 600-second incomplete genuine runs. P150 BYOK original scope 190-second timeout. P159 full original 8.30 21-test execution with genuine old failures and five full-module timeouts. P161 focused original Phase8.37 passed with 95.75s but its whole module not cleared. Historical P76/P85 exact branch positives, P86/P87 old two-button UI assertion, old Phase8.31/8.32 AST/source shape and WinCred consumer allowlist remain HOLD. Privileged BYOK C1 G0–G6 incl P96 and P124 OPEN, no live user key or provider/WinCred consent.

**No GitHub merge, tag, release, original Google Drive MASTER workbook/dashboard release update, production signed launch or protected Kristian policy changes. P164 = diagnostics and integration design ONLY. Production RELEASE HOLD.**