# BYOK C1 P123 — integrate absolute Windows IPC read deadline into actual P121 review exchange

Date: 9 November 2026 | OM v2.1 | direct exact parent P122 `6d88b22e0790babc9aa161a11d79538244590b1f`

## Real problem and implementation

The verified P121 review-only IPC exchange had a 3-second timer reset after every partial `BeginRead` and a possible outstanding asynchronous operation on timeout. P122 proved an isolated one-owner Windows `CancelIoEx`/completion/EndRead and monotonic deadline candidate without altering P121. **P123 integrates that tested candidate into P121's actual named-pipe challenge/echo pathway**, on a **new P123 branch**, preserving all prior P121/P122 Git source commits.

P123 removes the old P121 `ReadExactBounded` helper and calls `WindowsReviewOnlyAbsolutePipeDeadline.ReadExactFrame` to read **exactly 32 bytes with one 850ms monotonic overall budget**. The new component requests native `CancelIoEx` on deadline, observes `EndRead` completion, quarantines/disposes a refused pipe and explicitly reports a possible unconfirmed drain. An exact read is still only input to the unchanged P121/P120 review-only diagnostic echo; the source does not issue a grant, elevate, install a listener, write WinCred or treat Windows process/session observation as signed app authentication.

**Important qualification:** P123 deliberately **changes** one P121 review source file within its new branch, while the P121 historical branch and original P49/P96 source hashes remain unchanged. P121's original 14-test **driver is unchanged**, and is recompiled against the integrated source and rerun. P122's original 16-test driver and implementation are also unchanged. Claim source-preserved only for the original Git commits, not that P121's source byte hash is identical in the P123 integrated branch.

## Genuine native hosted Windows test plan

16 new P123 test cases: null/unconnected request/pipe, real same-process and separate native Windows child full-response diagnostics, valid split response, wrong echo, truncated response, premature disconnect, **silent client**, **partial 2-byte stall**, **slowloris one-byte-at-a-time partials**, late 32-byte reply, subsequent clean connection after a timeout, and original P49/P112 native-effect guards. The four stall/late cases require the actual integrated exchange to reject within a bounded time and the test-owned pipe to be closed/quarantined, preventing late response resurrection.

The P121 14 original tests must run against the **integrated** source, with the P122 implementation linked, to verify backward behaviour. All previous test drivers P120/P118/P117/P116/P115/P114/P113/P112/P110/P109/P108/P106/P99/P96 remain unchanged. The P96 original 15 fake-only negative comparator must still reproduce the revocation/effect race.

Target **313 native focused tests = 16 new P123 + 297 prior P122/P121/.../P96 cases**. This is not a full native product regression certification or G0 independent security review.

## Limitations and remaining review

All P121/P122/P123 code is compile gated for isolated `C1_REVIEW_ISOLATED_ASSEMBLY` only. The current native read path owns one pipe; `CancelIoEx(NULL)` can cancel all outstanding I/O for the handle and is not approved for a shared production endpoint. The timeout and success states are review diagnostics, not production guarantees. A same-user malicious process could relay an echo or transfer a pipe handle. OS SID, PID, session, integrity and challenge echo never prove a trusted signed installed consent app or actual approving human.

G0 qualified independent Windows security review OPEN.
G1 publisher-pinned signed installed application, trusted live process image, secure desktop/user intent, service-owned IPC and durable protected operation-bound one-use consent OPEN.
G2 P96 original check-to-effect race OPEN, legacy native coordinator excluded.
G3 protected antirollback journal/HKLM + crash recovery OPEN.
G4 privileged pending-only real WinCred validation OPEN.
G5 production signing / Smart App Control compatibility OPEN.
G6 three complete native Windows product regressions, independent release approval and Google Drive master workbook-first dashboard reconciliation OPEN.

No real key, installed privileged service, WinCred/HKLM write, signed UI approval, Kristian unsigned native execution, Smart App Control bypass, GitHub merge/release/tag or historical P62 safety-block retry.

**P123 INTEGRATED REVIEW-ONLY IPC. BYOK C1 PRODUCTION RELEASE HOLD.**
