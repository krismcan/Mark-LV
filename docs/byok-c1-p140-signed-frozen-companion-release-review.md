# Nayeon v1 / BYOK C1 P140 — signed frozen-companion launch architecture

**10 November 2026 | OM v2.1 | USER-SCOPED FIRST RELEASE HOLD | DRAFT**

Direct parent: P139 `052cf4f076d5f2c6e170593cab473d0c8eab7c3a`.
P139 genuine seven original Windows native filesystem tests PASSED on a handle-verified disposable local C-drive temp root (source/test unchanged). P135's full product triad remains HOLD: three 600-second timeouts and genuine partial failures; P136 showed expensive nested original historical Git work. P138 identified three legacy P86/P87 UI assertions still expecting 2 buttons when the user-authorised P133 Connection page now has 3; old assertions are NOT changed.

## A real production-facing architecture change, not an approved signer

P140 modifies **only the existing source/frozen launch boundary**, adding one fail-closed signed-companion policy source, 24 negative/mock-wiring tests, six exact scope-governance tests, this document and a genuine hosted-Windows regression workflow: exactly SIX changed paths. The P132 offline key window, P133 Connection page, original WinCred backend, default offline entry, frozen historical P49/P96 security tests and original filesystem implementation remain **byte-identical**.

**Source mode remains P133:** a user must click the Connection-page button; the fixed child module is invoked through the original absolute Python executable in an allowlisted environment, without an API key on argv, stderr or inherited provider vars. No automatic key access.

**Frozen mode now has a separate candidate-selection path** with the following REQUIRED (but presently UNAVAILABLE) source-embedded authorities:
- Approved immutable SHA-256 of `NayeonDesktop.exe`, and of the adjacent exactly named `NayeonLocalByokOffline.exe`.
- Approved immutable SHA-256 of the actual Windows Authenticode *signer certificate* for **both** files; both must report OS Authenticode `Valid`.
- Explicit independently authorised Code Integrity policy owner GO and signed installer/upgrade trust path.
- Exact local regular files with no visible file reparse point, correct fixed filename and selected packaging layout. Refuse missing/changed/unsigned/wrong-signer or unexpected parent process. No environment/config/CLI input may add release pins, a trusted signer or a helper filename.
- Child argv contains ONLY the canonical approved companion executable, never a key, shell command, downloaded script, `python -m`, arbitrary PATH choice or unsigned fallback; source mode never uses the companion.

**CURRENT STATUS: every immutable authority field is deliberately blank/false.** The actual P137 frozen app is Authenticode **NotSigned**, and the full main packaged NayeonDesktop.exe installer has not been built, signed or reviewed. Therefore the actual P140 frozen launch path must ALWAYS return UNAVAILABLE, and no native key window is run. Positive unit tests use **clearly labelled mock signer/verdict and fake Popen** to establish branch wiring only. They cannot prove real signed publisher trust.

### Important residual risks before ever populating the immutable approvals

- **TOCTOU** between `hashlib.sha256`/Authenticode file inspection and `CreateProcess` still exists if an attacker can replace installation files. A production installed directory must be non-writable by untrusted users and Windows WDAC/Smart App Control must enforce a verified image signature **at actual load time**. Python-level preflight alone is NOT enough to authorize a real key effect.
- Signer `Get-AuthenticodeSignature` from fixed System32 PowerShell is a useful read-only status observation but not a hardware identity, attestation protocol or independently issued security-review certificate. Signer pinning and real vendor certificate custody need an independent qualified Windows review.
- The signed *parent* executable must itself be publisher-approved; a signed helper alongside an unsigned or untrusted parent is NOT permitted. A signed Python system interpreter does not sign editable Nayeon sources.
- Source-level hashes are not tamper-resistant unless the **containing executable and installer themselves** are signed/locked under the authorised image policy. Do not substitute a mutable JSON manifest, environment flag, downloadable SHA or adjacent file for a genuinely approved immutable signer.
- The P137 PyInstaller onedir packaging smoke only froze the **standalone** unsigned Tk app and executed a separate fake-only frozen smoke. No real setup executable or source-mode P133 main desktop executable was launched/installed.
- Actual Windows Credential Manager under current logged-in account is intentionally a reduced threat model, accepting same-user malware as residual risk; no protected privileged journal, TPM antirollback root, signed physical human-presence broker or guaranteed crash/reboot atomicity. C2 provider validation is separate.

## P140 CI and governance

The Windows hosted runner must run the entire preserved **474 native security-focused cases** (including frozen P96 original 15 fake-only race negatives and original P49 pins) plus the relevant P133 Connection real Tk, P132 controller/fake WinCred and P134 genuine disposable UUID-random synthetic WinCred tests, and **30 P140 new policy/scope cases**. It must preserve old exact-branch seal guards without silently rewriting them; only functional classes on the new branch are claimed green. No unsigned EXE on Kristian, no user key, no protected registry, no real provider API.

The P139 seven original Windows native filesystem passes are independently evidenced by [Actions #42772880118](https://github.com/krismcan/Mark-LV/actions/runs/42772880118), not a substitute for three full Windows product regressions. Historical P86/P87 UI two-button expectations must be formally re-scoped under independent test governance, not edited under a source-only launcher change.

## Signing and release-go decision needed

A qualified Windows policy owner + independent user-scope security reviewer must review the exact parent/companion signed installer, publisher and certificate chain, protected install directory ACLs, update/rollback/signing-key rotation, Smart App Control load decision and any legitimate test distribution method. Only then can the immutable release approvals be set in a separately sealed/signed release branch and target images inspected on the authorised machine. **P140 itself cannot meet that requirement or authorise real API key entry.**

Remaining reduced C1 gates: U1 independent review, U3 publisher-signed main desktop and companion launch package, U4 Smart App Control acceptance, U5 *three complete full product Windows regressions* and independent release, U6 original Google Drive master workbook FIRST and dashboard second on actual release. Original privileged G0–G6 still open with P96 race and P124 pipe-writer authorship gap; never enable those old paths.

**P140 = production-facing frozen launch gate implementation with mandatory no-authority defaults; BYOK C1 USER-SCOPED RELEASE HOLD.**
