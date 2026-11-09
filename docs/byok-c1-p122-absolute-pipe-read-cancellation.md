# BYOK C1 P122 — native Windows pipe read absolute deadline and cancellation drain (review-only)

9 November 2026 | OM v2.1 | exact P121 base `31210194fc0f65cd5e7584c566cce1a70598ba0a`

## Problem exposed by P121 source review

P121's local named-pipe review helper uses `BeginRead` with a new 3-second timeout for every partial read, and returns on timeout **without completing its outstanding `BeginRead` through `EndRead`**. A client that sends one byte at a time could extend the overall frame read, and timeout can leave asynchronous operations unresolved. This matters even for a denial-only prototype; do not mistake a successful ordinary positive test for robustness.

Microsoft explicitly documents:
- `PipeStream.BeginRead` requires one `EndRead` per completed `BeginRead`.
- `CancelIoEx` requests cancellation but is not itself proof of completion. Native completion may race normal I/O; the code must observe the result and distinguish unknowns.
- A native cancel request with NULL OVERLAPPED affects **all outstanding operations on the handle**, so this cannot be used blindly on a shared production pipe.

References:
https://learn.microsoft.com/en-us/dotnet/api/system.io.pipes.pipestream.beginread
https://learn.microsoft.com/en-us/windows/win32/fileio/cancelioex-func
https://learn.microsoft.com/en-us/windows/desktop/FileIO/canceling-pending-i-o-operations

## P122 implementation scope

`WindowsReviewOnlyAbsolutePipeDeadline` is a **NEW independent, compile-guarded, one-owner read primitive**, not a hot patch of verified P121. It accepts exactly one 32-byte review reply frame, requires a real connected asynchronously configured Windows named-pipe stream owned by the isolated test, permits only a 25–2000ms budget and uses `System.Diagnostics.Stopwatch` for **one monotonic deadline across all partial reads**.

- An entire correctly sized frame before the deadline is only a `ExactFrameObserved` diagnostic, never an authority.
- Zero-length/disconnected/truncated/malformed inputs refuse.
- On deadline with pending OS read, request native `CancelIoEx` for that **exclusive owned handle**, wait for the asynchronous completion, invoke `EndRead` after completion and **quarantine/dispose** the pipe.
- If cancellation cannot be observed as completed after bounded cleanup, the state explicitly becomes `DeadlineExpiredDrainUnconfirmed`. Never infer that CancelIoEx success implies completed I/O, never reuse the handle and never claim the buffer or operation is safe for continued service use.
- Even a normally completed read racing with cancellation cannot become a success once the deadline has elapsed.
- A terminal failure does not invoke P120 admission or any native credential action.

**Known limitations:** This P122 primitive is **NOT integrated into P121's exchange** and therefore does not yet repair that historical branch's helper. It is a test-only candidate for later independent review and explicit integration. A real production service would need pipe ownership and cancellation design, a secure user-present broker, durable protected one-use grant, stronger PID/handle-transfer attack defences and G2 dispatch authority. A driver failing to honor cancel is an explicit fail-closed *unknown*, not proof of drained IO; unsafe concurrency/callback interaction remains a reviewer topic.

## Real hosted Windows test gate

16 new native Windows cases: null input/invalid buffer/invalid deadline/unconnected fail-closed; 32-byte full and 7+25 byte partial positive diagnostic reads; short/closed denial; actual silent, partial-stall, slowloris and late reply timeout, native `CancelIoEx` request plus observed `EndRead` drain and quarantine; genuine distinct unprivileged Windows test child process; original P49/P112 no-effect guards. The source and test driver refuse compilation outside `C1_REVIEW_ISOLATED_ASSEMBLY`.

Must retain **281** earlier P121/P120/P118/P117/P116/P115/P114/P113/P112/P110/P109/P108/P106/P99/P96 native focused cases unchanged, and original P96 15 fake-only test must still reproduce the known revocation/effect race. Total targeted focused cases **297 = 16 + 281**. Tests on unprivileged hosted Windows only, no unsigned executable launched on Kristian.

## Security gates

G0 external qualified native Windows security review OPEN.
G1 signed trusted installed human-consent broker, approved publisher/live image provenance, authenticated service-owned IPC, actual user click and durable protected one-use permission OPEN.
G2 original P96 check/effect revocation race OPEN; old coordinator excluded from safe candidate.
G3 protected journal/HKLM antirollback and crash recovery OPEN.
G4 actual privileged pending-only WinCred lifecycle OPEN.
G5 production signing and Kristian Smart App Control production acceptance OPEN.
G6 three complete product Windows regressions, qualified release approval and original Drive master workbook-first/dashboard synchronization OPEN.

No real keys, WinCred/registry effects, privileged installation, historical P62 safety replay, SAC bypass, merge or release. **BYOK C1 PRODUCTION RELEASE HOLD.**
