# P191 — Concurrent Real Windows Source-HANDLE, ADS and Ancestry-Race Evidence

**13 November 2026 • Nayeon v1 / Mark-LII • BYOK C1 • OM v2.1 • PRODUCTION RELEASE HOLD**

## Exact source authority

Begin from closed experimental P190 source HEAD 8a94be2670610048416cf6832831a14073a635f5, draft PR #115 unmerged. Original successful native Windows run #43421816900, artifact #14033988074 original ZIP SHA256 D353B1AEDC136528EAA301C14848A94EF13B61F89C90A0F17541158126A14036. First re-authenticate all original three ZIP members and CRC, exact original P189 4/4 source test log, original P190 10/10 handle-source tests log, raw SHA-256 and unchanged historical H/C/R hold ledger.

P191 adds **exactly three audit-only paths**: a Python Windows evidence runner, this security record and an isolated hosted Windows workflow. Nothing in original product, frozen tests, sealed historical B source, original 8.34 hardlink guard, P180-P190 witness scripts, current Phase 10 verifier or Kristian's local product worktree is changed.

## Why these are actual concurrency tests

P190 established static Win32 HANDLE-based integrity properties with an experiment. P191 opens the P190 candidate source HANDLE with share mode zero, **holds it open**, launches a **distinct native Windows Python process** with a bounded request (no shell and no network), collects that process's real Win32 success/errno/winerror, then allows the already-held handle to finish its ReadFile and metadata check. It therefore tests actual process separation and OS sharing semantics; it is not a mock of stat() or a single-process synthetic response.

Each fixture is a unique newly created disposable hosted Windows temp directory. Source bytes are obtained from the actual historical sealed B Git commit and verified against the original literal B source hash. Only self-owned synthetic non-executing test bytes are ever created. Child processes receive no real tokens, provider credentials or business data.

| Physical interleaving | Security interpretation |
|---|---|
| Sealed B baseline | Same handle reads original literal pinned source |
| Separate process writes main stream while exclusive HANDLE held | Win32 sharing refusal expected, no mutated source |
| Separate process creates named NTFS ADS while held | Win32 sharing refusal expected; no added stream |
| Separate process renames current source leaf | OS refuses, or if rename permitted the source reader must **refuse**, never silently approve an altered path |
| Separate process deletes leaf | OS refuses, or reader must detect loss of authority before admission |
| Separate process replaces source with different staged bytes | OS refuses, or reader must refuse the displaced/changed path |
| Separate process creates hardlink to source | OS refuses or reopened HANDLE link-count observation refuses change |
| Separate process renames parent directory and restores it (ABA) while HANDLE held | **Observe both real OS outcomes**; if an ABA completes and candidate returns bytes, mark explicitly **unproven ancestry** — not a security approval |
| Separate process writes independent sibling file | Should succeed; leaf source lock is not a global directory lock |
| After exclusive HANDLE closes, child adds ADS then new read attempts | ADS creation succeeds, next new handle admission refuses; deletion permits fresh valid read |

All cases are **real Win32** with documented error details. Unexpected unrelated process failure, missing child outcome, false reason or silently successful source alias replacement fails the evidence gate. The ABA experiment is deliberately observational; a green test must not be misrepresented as proving an atomic rooted/ancestor-handle admission transaction.

Each of original P189 four genuine full B gate cases and P190 ten genuine Win32 handle-source cases is rerun against its own **exact original source commit** in independent Windows clones, with source-bound native OS exit, complete original raw log footer and SHA-256. P191 ten new actual cross-process scenarios are separate exact P191 HEAD tests. Source HEAD/status and original frozen paths must remain identical before/after.

## Actual initial native Windows evidence and retained failures

The **first** P191 native runner, HEAD 31f9071d9e1542501a1326db600aa8f0a00eed52, run #43424682107, authentic artifact #14036670756 SHA256 5BAAB3207F85F6D8E61E3FBFC306D0E1C8EC45896C54D1C9E5F7FF575FEA8D95, returned native FAIL. Original exact P189 four and P190 ten selected tests individually PASS; new P191 ten ran with 7 PASS, 1 FAIL, 2 ERROR because the new harness hypothesised incorrectly that exclusive source open blocks NTFS ADS creation and that an unrelated sibling write never affects pre/post ancestor metadata.

Real OS observations from the native failed P191 log:
- Separate process **successfully created a named NTFS ADS while the source's zero-share GENERIC_READ HANDLE remained open**. P190 post-read FileStreamInfo inspection **refused** with HANDLE_HAS_UNAPPROVED_NTFS_STREAM. This disproves the hypothesised OS sharing ban on ADS creation but supports candidate's *specific post-read detection*.
- Separate process **created a hardlink while source exclusive HANDLE remained open**. P190 post-inspection refused the changed hardlink count; this is not an OS hardlink creation ban.
- An independent sibling file was **successfully written**, but P190's pre/post parent lstat tuple changed due parent mtime and the candidate refused PARENT_PATH_IDENTITY_DRIFT. This is an **availability false positive and performance risk**, not a proven authentication bypass.
- Separate process source rename and delete were **OS-refused with WinError 32**. Source replace and ancestor directory rename were OS-refused with WinError 5 on this particular Windows runner. This is bounded observational evidence, not proof of all-version or elevated/privileged race freedom.
- The Python built-in attempted main-file write produced PermissionError errno 13 with no exposed winerror, so it cannot substantiate the intended precise native Win32 rejection reason. P191 audit-only repair switches to native CreateFileW GENERIC_WRITE and reads ctypes.WinError(GetLastError), **without writing** source content.

Preserve the first true Windows run, error footers and original immutable artifact. A corrected source-preserving **P191 audit-only** rerun must capture actual corrected outcomes. No original P190 code, original historical security guards or product components are changed to achieve passing results.

## Blocking security and release decisions

**SEC-P191-ABA / OPEN:** a zero-share HANDLE protects the **leaf it opened** according to normal Windows sharing semantics. It does not by itself pin all ancestor directories, prove race-safe relative opens, or give an immutable relationship to historical Git index/tree authority. Observe actual parent rename-and-restore; if it succeeds during leaf open, verify no false release claim is made. Even a denied parent rename on one runner does not prove the race impossible on all Windows versions, privilege contexts or filesystems.

**SEC-P191-ADS / OPEN IN ORIGINAL CODE:** P189 proved the **complete historical private BYOK-B gate admits named NTFS ADS**; P190's different, unintegrated handle-bound candidate refuses ADS. No original or current production admission has been repaired or signed off.

**SEC-P191-SHARE / OPEN:** native share-mode experiments are conditional on local NTFS and ordinary user-level rights. They are not a formal claim against privileged process manipulation, malware filter drivers, backup/restore privileges or kernel-level adversaries.

**PERF-P187-01, P135, P175, P178, P179 OPEN:** no original source-witness caching, skipping or weakening. Historic full-product Windows 3x600s timeouts, source-era negative FAILs and historical pin performance remain unwaived.

**H/C/R = HOLD / isolated concurrency witness ONLY / HOLD.** Qualified GOV-01/GOV-02/SEC-03/SEC-04/REL-05/REL-06/REL-07 external reviewer decisions OPEN. Privileged G0-G6 admission OPEN. Complete unfiltered original native Windows full-product acceptance 0/3. No signed main/helper/installer, certificate/SAC/WDAC GO, WinCred/real keys/providers, privileged service, original source edits, merge, tag, release or false Google Drive MASTER/dashboard release status.

**P191 may close only as authentic real-Windows concurrency evidence with original full H/C/R and immutable SHA logs, never as production safety signoff.**
