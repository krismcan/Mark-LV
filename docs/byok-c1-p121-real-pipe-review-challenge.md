# BYOK C1 P121 — actual unprivileged Windows named-pipe challenge echo, NO consent

Date: 9 November 2026 | OM v2.1 | Direct exact P120 baseline `2795e8bbf6b97b705e854f44b27d2d8e683858c7`

## Purpose

P120 implemented a compile-gated review-only nonauthoritative CSPRNG operation-bound challenge transcript. P121 sends that challenge across **real Windows local named pipes** to genuinely connected same-process and separate unprivileged Windows test clients, with peer fingerprint derived by the host from **OS observed P114 process PID/creation-time/process-token SID/image path and P115 OS pipe/token session and integrity label**. No caller-supplied PID, SID, signed status, claimed user click or session can authorise a positive result.

The host creates a current-user-only ACL one-instance local pipe and receives a single inert handshake byte to anchor the OS impersonated client token. `WindowsReviewOnlyPipeChallengeExchange.RunAfterHandshake` is called only with the connected pipe and host-created P102 immutable request. After P114/P115 OS evidence, it hashes length-delimited OS fields into an **observation fingerprint** and asks P120's test-only challenge issuer for a new random nonce and canonical request digest. It sends a bounded **64-byte** challenge frame. The client echoes up to 32 bytes, with bounded async OS reads. Before comparing the echo, the host reobserves real OS pipe client process/session, comparing the fingerprint; mismatch, disconnect, incomplete frame, modified nonce and expiry are refused. No service install or privileged token needed.

Successful exact echo is **only `EchoObservedWithoutConsent`**, a diagnostic that a client able to read the pipe sent an equivalent response. This is NOT a signed installed UI identity, actual human action, publisher-pinned executable, protected one-use grant or WinCred permission. The peer fingerprint is a SHA-256 digest of OBSERVED state, not an authenticating secret or proof the writer of a transferred pipe handle is trustworthy. No trust can be inferred from same-user SID, current process metadata, an OS signature result or a pipe handle.

## Denial-only engineering constraints

- Both new source and driver have `#error` outside `C1_REVIEW_ISOLATED_ASSEMBLY`.
- Windows pipe ACL limited to current user; no privileged service or persistent network endpoint.
- Request comes from the unprivileged test host, not caller-supplied metadata and does not contain real credentials.
- No actual image-section/publisher pin, signed consent broker, trusted desktop, user click or attested user presence.
- No protected durable one-use grant, journal, WinCred/HKLM or native credential mutation.
- No unsigned native executable launch on Kristian; actual x64 compilation and separate child-process execution only on GitHub-hosted Windows.
- A bounded async read can leave an OS pending read on timeout until the host disposes the test pipe; not accepted as a production service reliability guarantee. Independent reviewer must assess cancellation and service isolation before real installation.
- No P96 old coordinator revive. Original P96 15 fake-only negative cases must continue to reproduce known revocation/effect race.

## Actual hosted-Windows test inventory

14 new P121 cases: null/disconnected pipe and null request; real same-process and distinct OS process valid echoes labelled nonconsent; wrong echoes for each; truncated responses for each; disconnect after handshake; fake application-level PID claim; exact nonce replay across distinct connected pipes; two separate pipe session freshness; real OS process metadata + echoed challenge cannot enable WinCred.

All earlier **267** P120/P118/P117/P116/P115/P114/P113/P112/P110/P109/P108/P106/P99/P96 focused Windows tests must run unchanged. Expected total: **281 native focused cases**, no full product regression certification. Freeze original P49 11 native source hashes and prior candidate/review source hashes.

## Release gate ledger

G0 qualified independent Windows security review OPEN.
G1 signed approved installed broker publisher root and real loaded image trust, privileged service-owned pipe/listener/clock, trusted interactive human click, exact-operation durable one-use grant OPEN. This prototype has none.
G2 original P96 revocation/effect race OPEN and no real native atomic dispatch/revocation replacement.
G3 protected journal/antirollback/HKLM and reboot/crash recovery OPEN.
G4 actual privileged pending-only WinCred lifecycle OPEN.
G5 signing and Kristian Smart App Control production acceptance OPEN.
G6 external production release review, triple Windows product regressions, release/source reconciliation, Google Drive master workbook-first/dashboard release sync OPEN.

No real credentials, installed privileged service, SAC modification, P62 blocked retry, GitHub merge/tag/release or Drive master mutation.

**P121 is real Windows *unprivileged* IPC evidence only — BYOK C1 PRODUCTION RELEASE HOLD.**
