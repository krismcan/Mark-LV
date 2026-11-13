# P189 — Original full historical BYOK-B physical alias admission verdict

**13 November 2026 | Nayeon v1 / Mark-LII | BYOK C1 | Historical H HOLD | Release R HOLD**

## Why this matters

P188 physically demonstrated that the unmodified historical 8.31 disk-reading component consumed sealed B source bytes while that source had a second hardlink or an extra named NTFS alternate data stream (ADS). That was **not evidence that the complete original BYOK-B historical security gate also admitted them**.

P189 establishes this exact causal distinction using the original historical full B private gate, B._assert_byok_b_historical, executed on a disposable Windows Git worktree whose HEAD is the sealed A parent. All 23 B source files are independently hydrated from genuine sealed B Git bytes and original literal SHA256 pins. The public B entry point delegates to Phase 10 and is neither patched nor replaced; original frozen test and production code never change.

The four physical verdict scenarios are:
1. Unmodified, source-authenticated baseline original B complete-unstaged source admission.
2. A real NTFS hardlink to B.SELF placed **outside the Git worktree** on the same volume, so it cannot be rejected simply as an untracked repository pathname.
3. A real named NTFS stream on the original B.SELF source file, with unchanged main file bytes, ordinary Git index and working tree.
4. Both the off-repository hardlink and named NTFS stream simultaneously.

Each calls the original B full verifier in a fresh native Windows subprocess. The test records the actual original admission, elapsed time, native exit and source-verification reason. Only valid source reasons may count as relevant refusals. Unexpected Git/process failures cannot be relabelled a successful tamper witness. Real admissions, if confirmed, become explicit blocking security findings, not release approvals.

## Historical source custody and new scope

Exact P188 parent: d351c1a968991a14c233e53a566b466e5ffe2d19. Original final P188 run #43409023015, original artifact #14028267868 ZIP SHA256 FD6DF6DC1A79D8A3B6BC3C789741C3A625DE2175F9E83AEF18BE2E3A2D8C6C64. Authenticate all seven original archive members and genuine P184/P185/P186/P187/P188 native selected-case logs/footers/HCR before P189 execution. P188 has 51 selected source-separated original/new cases plus one distinct frozen original diagnostic, not a successful full-product regression.

P189 adds exactly three audit-only paths: this design report, a Python review script and native Windows workflow. Prior source, frozen negative tests, original product and all historical Git objects remain unchanged. Kristian original dirty product worktree must not be opened for writing.

Original exact P188 native Windows nine physical tests rerun under exact P188 branch, separately from the new P189 four actual full gate verdict tests. Each has a separate native OS exit, original complete raw log SHA256 and authenticated source identity.

## Dispositions and next engineering choice

If the **whole original private B gate** admits the physically hardlinked/ADS source, record a confirmed historical full B admission gap (not merely a component weakness). Hardlink rejection must consider original Windows link count and file ID. ADS rejection must enumerate NTFS streams from a verified handle, not just static Git/blob bytes. Win32 CreateFileW share-mode, FILE_FLAG_OPEN_REPARSE_POINT, GetFileInformationByHandleEx FileStreamInfo/FileIdInfo, GetFinalPathNameByHandleW, handle-bound ReadFile and parent-handle trust may be candidate design primitives; none is approved or proved atomic in this checkpoint.

If the gate correctly refuses any scenario for a source-relevant reason, preserve the genuine refusal and revise the risk classification accurately. Synthetic frozen lstat tests do not replace physical evidence. No acceptance is cached, source identity is recomputed every invocation. This is not an approval to integrate into original verifier, WinCred, privileged service or signed installation.

**Unresolved no matter which verdict:** parent replacement/ABA races, signed Git executable and source process identity, independent Win32 HANDLE trust review, earlier P135/P175/P178/P179 full regression failures, PERF-P187-01. All seven qualified GOV/SEC/REL approvals OPEN, G0–G6 privileged OPEN, 0/3 accepted complete unfiltered Windows full-product regressions, no signing/installer/SAC/WDAC GO. No real API keys/provider calls, merge, tag or production dashboard / MASTER release claim.

**P189 can close only as isolated genuine original-full-B physical admission/denial evidence, with original negative security implications kept OPEN and release HOLD.**
