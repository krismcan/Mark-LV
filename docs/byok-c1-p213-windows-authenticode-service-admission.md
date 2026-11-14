# P213 — Genuine Windows WinVerifyTrust Signed Service Admission (Read-only)

**14 November 2026 | OM v2.1 | exact P212 parent
`e5d8f5f92a21d7314bf7ef6a7e9b2f9a95bc658f`**

**Classification: ISOLATED engineering/source observation, not trusted
Windows service, consent UI, real-key admission or production release.**
R0–R4 real-key **NO-GO**; P0–P5 production **HOLD**; G0–G6 **OPEN**;
seven GOV/SEC/REL independent decisions **OPEN**; full accepted
unfiltered Windows product regressions **0/3**.

## Why the first Windows observation attempts failed

The original P213 candidate attempted `Get-AuthenticodeSignature`
inside a narrowly sanitised Windows PowerShell environment.
Actual hosted Windows runs **43608172462** and **43608628638**
returned a real OS probe error: the `Microsoft.PowerShell.Security`
module could not be loaded. The second run preserved the exact bounded
stderr excerpt. The first two runs FAILED; they were not declared
passing, and no frozen/native source test was weakened.

Rather than relaxing execution security, installing modules, bypassing
policy or suppressing the failed evidence, the final P213 source uses the
**pre-existing P116 native Windows WinVerifyTrust implementation**,
already written and historically tested in the real C1 programme.
It directly invokes the Windows `wintrust.dll` OS with a read-only
opened file HANDLE, no UI, `WTD_CACHE_ONLY_URL_RETRIEVAL`
and explicit provider-state cleanup. This remains a **file-policy
inspection only**. It does not attest a running signed process image,
independent authenticated publisher trust root or human approval.

## Actual P213 native execution path

The `scripts/p213_windows_signed_service_observation.py` evidence
driver compiles an unprivileged test-only `P213NativeWintrustObservation.cs`
entrypoint under `C1_REVIEW_ISOLATED_ASSEMBLY`, using the exact
original P116 native Windows trust source and its original P113/P114/P115
OS peer dependencies, plus the unchanged P49 original strictly
read-only subset and reviewed native C1 candidate dependencies.
The original P116 source is not edited.

The resulting Windows C# executable accepts only one **absolute
nonsecret local file path**, calls the original P116 WinVerifyTrust
read-only file inspector, prints bounded native policy state and
explicitly refuses publisher, trusted process image, human consent,
real-key and release authority. The P213 Python observer launches
this actual native executable as a separate OS process, verifies exact
fixed output, and reads unprivileged file SHA-256 and filesystem metadata
before/after the native inspection. It observes, on genuine hosted
Windows:

- the existing Microsoft-signed Windows system PowerShell executable
  as a **reference only**. A native policy acceptance is an OS file
  signature observation, not approval to use Microsoft's certificate
  as Nayeon's release identity;
- the actual unsigned P210 test-only C1 native executable compiled
  from current source as the **negative**.

No production signing, installer, credential, service Main, Windows
credential storage or provider API access occurs. Native file-policy
rejection can also indicate unavailable revocation cache or other
non-authenticating conditions; it is NOT equivalent to an independent
publisher identity finding. The P213 observer reports no signer-certificate
thumbprint or enrolled Nayeon publisher, even if Windows accepts a
Microsoft binary. All seven new source-level release identity pins
remain empty and the Code Integrity machine policy owner GO remains false.

## Why WinTrust status cannot unlock BYOK C1

P116 native `NativePolicyAcceptedButUnpinned` means only
that OS signature policy accepted the inspected **file** in this
environment. It is not a binding between the inspected file HANDLE
and a peer's **loaded process image section**. Nor is it an approved
code-signing chain, protected Windows installer, protected service image,
actual consent broker, trusted user presence or monotonic no-retry
credential effect record.

The release architecture needs independently approved immutable
service/main/UI/installer certificate and binary pins, a signed protected
installation with no same-user writeable/side-loaded executable
dependencies, machine Code Integrity/WDAC/SAC enforcement, authenticated
service/client OS identity and transaction-bound consent, and one
service-owned native effect dispatcher with independent antirollback
custody. In particular, the real source-mode P132/P133
`WindowsCredentialBackend` route to Windows CredWriteW/DeleteW is
**still reachable** and not governed by a native C1 denial-only
service. A Python preflight cannot stop same-user independent
Credential Manager calls.

The qualified security and policy owner must first decide between
independently reviewing the reduced user-scope P132 U1–U6 model
and a high-assurance native C1 R0–R4 service/store architecture.
Do not merge their threat models or fabricate signer, reviewer or
Windows policy owner acceptance.

## Test scope and source custody

P213 has exactly **six additive files** (the native entrypoint is the
sixth), while original P49/P96/P132/P133/P140, the P116 WinTrust
implementation, existing native service and prior P208–P212 remain
unchanged. Authentic `windows-2025` push CI verifies exact SHA/event,
P212 parent and six paths, historical P49/P205 pins, original WinTrust
source Git objects, and identical before/after source custody.

The selected inventory is previous **199** original P132–P212 Windows
security tests plus new **20** P213 cases, expected **219/219 selected**
only if the actual hosted native OS run and real signer observations
succeed. These are not full-product Windows regressions (still 0/3).
Retain authentic native compiler/OS exits, raw log SHA-256 and H/C/R
on success or failure; never hide the first failed PowerShell probe runs.

No real credentials, service installation, modified Windows Code Integrity
policy, protected secrets, provider validation, merge/tag/release or
Google Drive MASTER production release record update is authorised.

## Microsoft references

- WinVerifyTrust API: https://learn.microsoft.com/en-us/windows/win32/api/wintrust/nf-wintrust-winverifytrust
- WINTRUST_DATA: https://learn.microsoft.com/en-us/windows/win32/api/wintrust/ns-wintrust-wintrust_data
- App Control for Business code policy: https://learn.microsoft.com/en-us/windows/security/application-security/application-control/windows-defender-application-control/feature-availability
- Managed Installer limitations: https://learn.microsoft.com/en-us/windows/security/threat-protection/windows-defender-application-control/configure-authorized-apps-deployed-with-a-managed-installer

**P213 can close only as a real native WinTrust review observation. No
real-key or production GO can be created by a passing test.**
