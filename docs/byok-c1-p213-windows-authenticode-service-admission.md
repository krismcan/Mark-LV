# P213 — Actual Windows Signed-Service and Installer Admission: Read-Only Proof

**14 November 2026 · OM v2.1 · exact P212 parent
`e5d8f5f92a21d7314bf7ef6a7e9b2f9a95bc658f`.**

**Classification:** Engineering read-only Windows Authenticode/source observation
candidate. NOT a signed service, protected installed image, actual UI consent
or code-integrity policy admission. **R0–R4 real-key NO-GO, P0–P5
production HOLD, G0–G6 OPEN, seven independent GOV/SEC/REL decisions OPEN,
0/3 full accepted Windows product regressions.**

## What is materially new compared with P212

P212 genuinely refused a high-assurance build through an isolated test
pipeline. P213 probes the **actual Windows Authenticode OS implementation**,
not a simulated signer. Its `p213_readonly_windows_signer_observer.py`
runs built-in `Get-AuthenticodeSignature -LiteralPath` inside a known
Windows PowerShell system executable with one separately passed path,
no shell interpolation or profile loading, a restricted environment and
bounded timeout. It re-observes ordinary file metadata and SHA-256
before/after the signature call. These are **observations**, not
TOCTOU-resistant loaded-image binding or Windows Code Integrity evidence.

Genuine hosted Windows compares:
- the **real Microsoft-signed Windows PowerShell system binary** (the
  *reference*: valid OS-issued Authenticode status, SHA and public signer
  certificate thumbprint) with
- the **real native C# P210 C1 test-only executable** rebuilt from original
  historical/native sources (unsigned Authenticode status, SHA, no signer).

Even a valid signature **does not prove it belongs to an independently
enrolled Nayeon publisher** or an installer/consent broker; this reference
must NEVER be adopted as a future authorised Nayeon trust root.
The named release-time pins for service, local consent UI, installer
and Windows Code Integrity policy are all deliberately blank. No
runtime values, flags or fake signer claims can set authority.
The observation receipt is immutable, with all release/service/
real-key/Code Integrity authority flags permanently false.

This is grounded in Microsoft's documented distinction between file
Authenticode signature inspection (which can use catalog signatures)
and App Control for Business policy enforcement of user-mode executables,
DLLs and scripts. Signature success is not a proof of an exact Windows
process loaded-image section, independent human presence, protected
installer ACL, or protected credential effect owner. A future signed
native service requires all those controls plus a qualified reviewer.

References:
- Microsoft Get-AuthenticodeSignature:
  https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.security/get-authenticodesignature
- Microsoft App Control for Business file/policy rules:
  https://learn.microsoft.com/en-us/windows/security/application-security/application-control/windows-defender-application-control/feature-availability
- Microsoft App Control installer caveats:
  https://learn.microsoft.com/en-us/windows/security/threat-protection/windows-defender-application-control/configure-authorized-apps-deployed-with-a-managed-installer

## Trusted architecture candidate: authority boundaries required

| Layer | Actual required verified authority | Current P213 result |
| --- | --- | --- |
| Release signing | approved independent publisher/certificate, revocation and rotation, exact service/UI/installer binary pins | NONE: Nayeon pins blank |
| Protected install | signed staged MSI/installer, machine-owned protected directory, no user-writable DLLs or symlink/junction substitution | NONE |
| Service admission | installed signed service image, dedicated OS principal, verified loaded image, OS-protected startup and upgrade | NO deployable service Main; denial only |
| Broker consent | signed installed interactive broker, exact user-presence mechanism and operation challenge, authenticated OS peer and IPC | NONE |
| Credential effect | single trusted service-owned WinCred/store effect, P132 Python legacy route genuinely eliminated or isolated by OS policy | NO; P132 still source-reachable |
| Durable state | independently protected antirollback/counter/witness, same-owner effect lock, restart reconciliation | P209 synthetic user DPAPI only |
| Machine policy | actual WDAC/SAC/App Control UMCI enforced machine-specific signed load admission | NO policy owner GO |
| Independent reviews | GOV-01/02, SEC-03/04, REL-05/06/07 positive source-bound decisions, G0–G6 | SEVEN OPEN |

Do not confuse a Microsoft-signed `powershell.exe` with an authorised
Nayeon `CustodyService.exe`; nor the compiled P210 unsigned C# test
executable with a deployable Windows Service. Windows policy and signer
decisions require a real human authority and actual authorised machine.
The P132 reduced user-scope model has *separate* U1–U6 acceptance; its
direct Python WinCred capability cannot be silently incorporated into
this high-assurance model.

## Genuine Windows evidence and repository custody

P213 adds exactly five additive paths:
1. `nayeon/brain/p213_readonly_windows_signer_observer.py`;
2. `tests/test_p213_real_windows_authenticode_service_admission.py`
   (20 actual signed OS vs unsigned native candidate tests);
3. `scripts/p213_windows_signed_service_observation.py`;
4. this document;
5. `.github/workflows/p213-windows-authenticode-service-admission.yml`.

Authentic GitHub-hosted `windows-2025` push CI requires exact
`GITHUB_SHA`, P212 ancestor, original source pin readback, exactly five
additive paths and unchanged original source identity before/after.
It compiles actual historical P49/current C1 native sources into
test-only executable, actually queries Windows Authenticode twice,
persists public status/file hashes to H/C/R, runs the same 199 selected
P132–P212 security tests plus the new **20 P213 cases**,
and archives original native compiler OS exits and log SHA-256.

A **219/219 selected PASS** means only focused source/native signing
observation. It is **not** any of the three complete unfiltered Windows
product regressions (0/3). The old P135/P175/P178/P179/PERF-P187-01
issues remain unwaived and historical P96 old race remains frozen.
Kristian's original worktree remains untouched. No signing key,
real credential, native effect, installer build, service install,
WDAC/SAC setting or provider C2 validation is used.

**Next P214:** source-bound Windows signed service/consent IPC
and installer threat-model review decision, then implement an actual
non-deployable native integration candidate only after independent
architecture choice; do not interpret another deny-only proof as real
service authorisation.
