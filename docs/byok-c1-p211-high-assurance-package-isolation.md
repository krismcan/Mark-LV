# P211 — High-Assurance Production Package Isolation: Deny-Only Candidate

14 November 2026 · OM v2.1 · exact P210 baseline
`11a7cc3c314458e4ed8e482d5d48734d225dbeca`.

**Disposition:** isolated pre-release **packaging intake candidate**, NOT a signed
production package, trusted runtime security boundary or external release
acceptance. Real-key R0–R4 **NO-GO**, production P0–P5 **HOLD**,
G0–G6 open, accepted complete unfiltered product Windows regressions **0/3**.

## Current grounded packaging and effect risks

There is no authorised high-assurance native Windows distribution/installer
or approved machine Code Integrity release identity in the P210 source tree.
`setup.py` and `core/installer.py` are general source-mode dependency
installers, not a signed C1 product installer. The P137 Windows PyInstaller
experiment built a disposable **unsigned standalone user-scope P132**
candidate, never a signed high-assurance privileged C1 release. P140
`frozen_signed_byok_companion.py` still has empty main/helper/signer
SHA pins and `_APPROVED_CODE_INTEGRITY_RELEASE = False`, and production
frozen launch intentionally refuses.

The **real source** P132/P133 user-scope route remains deliberately
reachable in Python source mode on a local Windows user:
`workspace_window.py` button → `application.py` launch handler →
`local_byok_launch_bridge.py` fixed Python child →
`local_byok_window.py` → `compose_user_scope_local_byok` →
`WindowsCredentialBackend` → `_Advapi32Adapter.write/delete` →
`CredWriteW/CredDeleteW`. This is not necessarily a released executable,
and source reachability does not prove actual real-key use. It is a
**different reduced user-scope trust model**, requiring U1–U6 human approval,
not high-assurance native C1 R0–R4.

The native privileged C1 `CustodyService` still always refuses OnStart,
and no production signed service, authenticated human consent IPC, trusted
OS effect owner or protected external antirollback authority has been
accepted. P208/P209/P210 are synthetic test-only candidates.

## P211 code: a conservative packaging boundary, not a Python lock

`nayeon/brain/p211_high_assurance_package_quarantine.py` adds a
**standalone static bundle-intake policy**. It does not import WinCred,
interact with Tk, execute a service, build an installer, read or store
secrets, or mutate preexisting product code.

It derives a source-specific witness from the exact eight source files
covering the backend, P132 factory/effect, P133 launcher, P140 signer denial
and native C1 service refusal. Source is read as text and AST only:
unknown, missing, malformed or reparse-point source is **SOURCE_UNPROVEN**,
not evidence of successful closure. The witness identifies source-reachable
Python effects and explicitly retains HIGH risk.

A package manifest supplied to the P211 intake is validated with strict
Windows-safe canonical relative paths: no drive-relative/absolute names,
UNC/backslash aliases, NTFS ADS colons, traversal, duplicate casefold paths,
trailing spaces/dots, control characters or oversized plans. Every Python
module, compiled extension, DLL, EXE, ZIP, wheel, MSI/MSIX, PowerShell,
script directory or unknown runtime payload is rejected. **Even a sole
harmless `P211_QUARANTINE_README.txt` is NOT a release**: all authority
receipt booleans are permanently false and an attempted forged
`release_eligible=True` constructor raises.

An invented signer name, approval mapping, environment variable, manifest
hash or product filename cannot upgrade the candidate. This means a build
system **could** add it as a mandatory preflight which refuses current
high-assurance builds, but no approved release builder consumes it yet.
The new check does not claim to block a separately installed Python
process, source-mode P132 child or same-user direct CredWriteW: those
require an independently signed and machine-enforced service/store and
runtime isolation. A Python import guard or unused preflight is not
protection against a malicious same-user actor.

## Tests and actual controlled outputs

P211 adds exactly five additive paths:
- `nayeon/brain/p211_high_assurance_package_quarantine.py`
- `tests/test_p211_high_assurance_package_quarantine.py`
- `scripts/p211_windows_package_quarantine_evidence.py`
- `docs/byok-c1-p211-high-assurance-package-isolation.md`
- `.github/workflows/p211-windows-package-isolation.yml`

The new P211 tests exercise actual source risk, reject original P132
sources, Python plugins/extensions and unsigned binaries, reject aliases/
NTFS ADS/absolute/UNC/traversal/case-collisions, deny forged approvals and
unknown code, reject missing source and safe-seeming modified source, and
prevent upgrading a frozen denial receipt. One test creates an isolated
throwaway COPY of original source and intentionally removes the P132
backend factory; despite that superficial edit, a new Python module
remains **UNRECOGNISED** and the release remains denied. Original
Nayeon product source is never modified.

The genuine GitHub-hosted `windows-2025` event collector verifies:
- exact P210 ancestor and only the five additive P211 paths;
- P205 original backend and other preexisting Git blob SHA pins;
- previous native C1/P208/P209/P210/P132 source identity;
- same original Git/source state before and after;
- original 36 P132, 12 P206, 14 P207, 20 P49, 24 C1, 20
  P208, 18 P209 and 13 P210 selected Windows/native cases;
- **22 new P211 candidate security tests** (total **179 selected** when
  green), genuine original OS compiler/runner exits and raw log SHA-256;
- truthful H/C/R evidence archive on both success and failure.

This selected scope never substitutes for the three **complete unfiltered
native Windows product regressions**. The failure ledger for P135,
P175, P178, P179 and PERF-P187-01 remains unwaived, P49/P96
unmodified and original Kristian dirty worktree untouched.

## Exit distinction and next critical owner handoff

**Engineering closure:** validated source-bound deny-only package intake
and regression evidence. **Production gate remains blocked.**

For high-assurance C1 to advance, a qualified policy/security owner must
first sign one architecture (P132 user-scope U1–U6 separately OR
privileged native C1 R0–R4), including store identity. Engineering
must then create an *actually enforced* production installer/source
boundary, signed native-only WinCred effect actor, authenticated signed
local human consent UI/service IPC, protected monotonic antirollback
custody and no-retry recovery. The high-assurance installer must prove that
the P132 Python source/child/general backend cannot mutate the
high-assurance credential target under the **actual authorised Windows
machine Code Integrity policy**, not merely omit Python from one manifest.

All GOV-01/02, SEC-03/04, REL-05/06/07 independent acceptance
decisions, service source authority G0–G6 and production P0–P5
remain OPEN. No real API key, BYOK C2 provider validation, unsigned
installation on Kristian, safety-control bypass, GitHub release/merge/tag,
or Google Drive MASTER/dashboard *production release* update is authorised.
