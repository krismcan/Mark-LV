# P193 — NT RootDirectory Relative Source Admission & Identity Readiness Review

13 November 2026. Nayeon v1 / Mark-LII. BYOK C1. OM v2.1. Experimental only. PRODUCTION RELEASE HOLD.

## Immutable custody

Exact P192 parent: 3541db02537c1b0ec1c7b3b0be4fb925b0271588. P192 successful genuine hosted Windows run #43440810202, artifact #14044379054, ZIP SHA256 F2051FFC5992696EE166F633AAC711E33D96D6C62E8529F26BAF93CD59AE852D. Authenticate all five original members and CRC: original exact-source P189 4/4, P190 10/10, P191 10/10 and P192 12/12 native tests, four true OS exits and raw SHA, original H/C/R HOLD source ledger. P192 PR #117 remains draft/unmerged.

P193 adds exactly three new review-only files: Python Win32/NtCreateFile audit, this risk review and hosted Windows workflow. Existing tests, product, historical private B full gate, original Phase 8.34 hardlink protection, immutable 23 original B source pins, Phase 10 public successor, original prior P180–P192 scripts, Git seals and Kristian original worktree (17 pre-existing dirty paths) are preserved.

## Technical approach: actual relative source opening

Windows NtCreateFile supports OBJECT_ATTRIBUTES.RootDirectory pointing to an existing directory HANDLE, with ObjectName naming a relative component. P193 starts from a RUNNER-OWNED disposable root acquired through Win32 CreateFileW and opens one child directory and one leaf at a time through NtCreateFile using the immediate retained directory HANDLE. Parents are opened with FILE_DIRECTORY_FILE, FILE_OPEN_REPARSE_POINT and sharing that omits FILE_SHARE_DELETE; leaf uses FILE_NON_DIRECTORY_FILE, FILE_OPEN_REPARSE_POINT and exclusive access. Each directory HANDLE is verified by GetFileInformationByHandleEx FileIdInfo, FileStandardInfo, FileAttributeTagInfo and GetFinalPathNameByHandleW; the same leaf HANDLE is read with ReadFile and verified with immutable original B source SHA, FileStreamInfo, link count and FileId reinspection. Siblings can change mtime without false denials. No production full source admission replacement.

Official Microsoft documentation: https://learn.microsoft.com/en-us/windows/win32/api/winternl/nf-winternl-ntcreatefile and https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntifs/nf-ntifs-ntcreatefile. The narrower user-mode documentation does not guarantee all OBJ_DONT_REPARSE combinations; P193 uses FILE_OPEN_REPARSE_POINT and refuses observed reparse attributes.

## Native Windows tests

Four preserved original exact SHA source suites: P189 4, P190 10, P191 10, P192 12. New P193 14 actual Windows tests:
- Sealed original B source read through true NtCreateFile RootDirectory calls.
- Verify each component is opened relative to the previous held parent HANDLE.
- Real separate-process creation of unrelated sibling in source parent and temp root, no false denial.
- Real separate-process NTFS ADS and hardlink additions while leaf HANDLE is open; both allowed by OS but rejected on post-read same-HANDLE metadata.
- Genuine preexisting NTFS junction parent refused.
- Directory junction introduced after root HANDLE acquisition, before relative component opened, refused.
- Corrupt original source SHA refused.
- Existing genuine NTFS ADS refused.
- Real child parent rename refused on this Windows runner.
- ADS/traversal/backslash/unapproved literal B source names refused before NT opening.
- Simulated NT component-open failure refuses, releases all source and parent HANDLEs and allows later proper read.
- Deliberate genuine negative diagnostic: before first relative directory open, substitute a different normal physical directory containing IDENTICAL original B sealed bytes. Current candidate does NOT pin expected child directory FileId from an independent original authority and may accept these identical bytes. Record as UNPROVEN SOURCE ANCESTOR CUSTODY, never as a production security PASS. This does not demonstrate a source SHA bypass or arbitrary execution.

## Open blocking review findings

SEC-P193-ROOT-01 OPEN: first trusted root HANDLE is only a runner-owned absolute-path directory, not a signed provenance admission. Need trusted OS root identity, expected child-directory FileIds or independent durable source authority, process ACL and privilege/reparse analysis. A RootDirectory relative open does not alone prove the original physical ancestor was authorized.

SEC-P193-IDENT-02 OPEN: demonstrated normal alternate directory with the SAME original static B bytes is admitted by separate isolated prototype when ancestor expected FileId is not pre-pinned. Do not integrate without independently reviewed source ancestry identity equivalence, even though immutable bytes remain unchanged.

SEC-P193-ABA-03 OPEN: reversible fast named-stream and hardlink add/removal between metadata snapshots, privileged drivers and cross-filesystem races not excluded by one Windows run.

SEC-P193-FULLGATE-04 OPEN: actual original full historical private BYOK-B verifier admitted a named NTFS ADS in P189; no original verifier or current public Phase10 successor patched. New prototype lacks complete Git worktree/index/tree/tag and privileged launch admission.

PERF-P187-01 and historical native failures still OPEN: P135 3 x 600s original suite timeout, P175 five source-era FAILs, P178 165s B timeout and two old FAILs, P179 130s pin timeout. No waiver, suppression, mutation or deferral is a passing original regression.

H/C/R = HOLD / isolated NT rooted-source test / HOLD. Full-product unfiltered native Windows accepted regressions 0/3; independent GOV-01/GOV-02/SEC-03/SEC-04/REL-05/REL-06/REL-07 reviews OPEN; privileged G0–G6 OPEN; signed main/helper/installer, cert SAC/WDAC Code Integrity authorization absent. No real key, WinCred operation, provider validation, production service, source seal modification, merge, tag, release or Google Drive MASTER/dashboard production success assertion.

P193 may close only as an independently inspectable source-preserving narrow genuine Windows audit, with all original failed and passing raw logs and proven unresolved identity gap. BYOK C1 PRODUCTION RELEASE HOLD.


## Actual initial Windows failure preserved — P193 handle lifecycle security review

The first real hosted Windows run #43451379768 at source HEAD 7a246e356c741702d2a8c43f32c409696e81af2d returned FAIL with original evidence artifact #14050337137 ZIP SHA256 511212CEC8B7DFD356E513F681AFB9BCC70AEE7E61F55BC3A47421A9047A83A1. All 36 original source-separated P189/P190/P191/P192 tests passed; the P193 14 new native Windows tests had 12 passing and 2 with primary ERROR, plus 2 extra cleanup ERROR entries.

The genuine primary errors occurred on test_07 preexisting junction and test_08 junction substitution before NT relative component open. The native reader **correctly denied both reparse/junction source paths**, but the new NtCreateFile call had already returned an open HANDLE for the reparse directory. The code then called _parent_snapshot before appending that HANDLE to its cleanup list. A raised SourceDenied left the HANDLE open; Windows **WinError 32** then prevented deleting the rejected junction and caused temporary directory cleanup to fail. This is an actual **SEC-P193-HANDLE-01 resource-leak and denial-of-cleanup finding**, distinct from any original source verification failure.

An audit-only repair to the new P193 prototype closes the returned NT relative directory HANDLE in an exception handler if the directory snapshot fails, before propagating the exact original SourceDenied. Historical sources, all original tests, the reparse-denial security assertion, original 8.34 guard, product and Phase 10 unchanged. Retain all first-run authentic logs and failure SHA evidence; require a fresh native Windows successful test run before P193 may close as experimental evidence.

The separately demonstrated alternate physically different ancestor with identical literal original sealed B source bytes **remains accepted by the test candidate** without independently pinned trusted parent FileIds. The repair does not attempt to disguise or close this provenance finding. H/C/R remain HOLD / experimental / HOLD.
