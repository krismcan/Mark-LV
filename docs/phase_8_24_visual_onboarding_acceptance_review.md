# Phase 8.24 - Independent simulated desktop onboarding review acceptance

Protected baseline Phase 8.23: `e6025475f820f811a45247480fadd29bfd876295`.

One independent, entirely test-only acceptance suite composes the actual
read-only refresh and review Tk callback surfaces, bound credential lifecycle,
trusted operation host, session review, and temporary provider metadata path.
The only credential backend and validator are in-memory fakes. No real
Credential Manager APIs, provider SDK, network, user passwords, API key
material or permanent OS state are involved.

Acceptance cases: no observation or provider activity on either window
construction; explicit refresh; clickable operation proposal; pending button
lockout; real Tk callback rejection; unsupported, changed and unavailable
observations fail-closed; synthetic credential state changes; expiry and
replay; and unchanged metadata after review. The UI's lack of approval and
secret entry is explicitly asserted.

This validates **synthetic integration** only. Formal Phase 8 is **not**
closed, because the normal-user first-run journey cannot yet test, save,
replace or delete a credential from an explicitly consenting interface.
There is still no CAS/transaction boundary spanning the metadata store and
credential backend, no tested real Windows Credential Manager live path,
no independent model entitlement proof, no app packaging/upgrade workflow,
and no qualifying user acceptance evidence for any of the 12 release gates.
Report 5/19 planned phases and 0/12 gates unless formally re-audited.

No new production module, no old production modification and no change to
model-route privileges. Seal only after full targeted, precommit and
postcommit regressions, exact two-file staging, annotated tag and remote
peel checks, Codex handoff, same-ID original workbook update and hash check.
