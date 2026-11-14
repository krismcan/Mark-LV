# P212 — Actual Windows High-Assurance Build-Entry Denial Integration

14 November 2026 · OM v2.1 · Exact P211
`50ecfa99bf34dacb248c21c29afe221a194ec204`

**Scope:** a real executable, source-custodied Windows build-entry workflow
that definitively refuses to produce a high-assurance product distribution.
This is an **ISOLATED NONDEPLOYABLE engineering checkpoint**, not a
production signer/installer, an enforced device-level security policy,
WinCred/secret storage implementation or trusted C1 service.

**Real-key R0–R4 NO-GO. Production P0–P5 HOLD. G0–G6 OPEN.
Seven independent GOV/SEC/REL reviews OPEN. Full-product Windows 0/3.**

## What P212 really implements

`scripts/p212_high_assurance_build_gate.py` is an explicit Python
**build entrypoint**. It makes `P211` source review mandatory before
any high-assurance product build is allowed. The P211 preflight's
source-grounded decisions never convey positive release permission.
The candidate intentionally supports NO production build function:

- `python -B -m scripts.p212_high_assurance_build_gate
  --attempt-ha-release` invokes P211 with actual real-repo legacy
  backend/P132/P133/native C1 paths, returns original Windows OS exit **41**
  and `P212_BUILD=DENIED_LEGACY_EFFECT_PATH`. It must not create any
  product/installer files. Attempted environment overrides such as
  `NAYEON_P212_RELEASE_GO=true` are ignored; no human or model input can
  promote this to release GO.
- `--emit-review-only`, available only during actual source-bound
  GitHub-hosted Windows push tests, emits a single exclusive-created
  **plain UTF-8 .txt** receipt named
  `P212_QUARANTINE_REVIEW_NO_GO.txt` in a disposable
  non-reparse runner temp directory, after P211 returns
  `ABSENT_RELEASE_AUTHORITY` and the real P132/C1 source-risk witness
  remains present. The receipt explicitly states no release, no signer,
  no machine policy, no real key and zero accepted full regressions.
  It is NOT a package or a positive build approval. Re-running it
  cannot overwrite the review note.
- Unknown or extra CLI arguments return refusal without side effects.
  An invalid source/manifest, missing P132 source, tamper, traversal,
  NTFS ADS path or attempted binary payload never becomes a safe
  high-assurance product. No PyInstaller, actual .exe/.dll/.msi/.zip,
  service installation, real WinCred, credential value, network access,
  C2 provider validation or change to Smart App Control/WDAC occurs.

The workflow `.github/workflows/p212-windows-high-assurance-build-denial.yml`
**actually executes the candidate CLI using a separate genuine Windows
Python process** and independently requires its DENIED exit 41,
the exact refusal text and zero product files before continuing.
It then checks the fixed review-only note is the SOLE file in its
staging directory, has the prescribed HOLD classification and no
binary/package extension. This makes the prior P211 preflight part of
the P212 job's executable build path rather than merely an unused helper.
CI success means **the build was successfully blocked**, NOT built.

**Critical scope:** P212's job is isolated and experimental; it is
NOT called by an authorised production package builder, installer or
distribution workflow. A future production build cannot inherit its
authority. A separate Windows process running as the same user can still
call Python's original `WindowsCredentialBackend` / Advapi32 directly.
A manifest name check or Python builder exit code is not OS-enforced
isolation of WinCred or independent trusted code signing.

## Actual source and evidence custody

P212 contributes precisely five additive files and changes no previous
product, historical test, Windows C1 service or native frozen code.
The GitHub-hosted `windows-2025` runner authenticates the event SHA,
repo, branch, exact P211 parent, five new paths, original 13 Git blob
pins and other old source identities, before/after. It captures actual
Windows OS exit 41 from the refused product attempt, OS exit 0 from
review-only metadata creation, SHA-256 of original stdout/stderr,
review note, native compiler and prior original security logs. It retains
the original H/C/R ledger and failed-run logs.

The selected Windows scope is P132 original 36, P206 12, P207 14,
frozen P49 native 20, current C1 native 24, P208 20, P209 real
DPAPI 18, P210 Python/native 13, P211 22, plus **20 P212**
build/refusal/nonsecret metadata cases: **199 selected cases** if green.
The 3 complete unfiltered Windows product regressions are **still 0/3**.
P135/P175/P178/P179/PERF-P187-01 are unwaived and P96 original
approval/effect race is not fixed.

## Remaining real-key / production admission blockers

1. GOV/SEC policy owners must choose and independently approve the
   narrower user-scope P132 U1–U6 or high-assurance native C1 R0–R4
   threat model. Do not combine their approvals or risk statements.
2. To pursue high-assurance R0–R4, implement a signed native service
   with a **single actual effect owner** and signed local consent UI,
   kernel-authenticated fixed IPC, source/installer identity, one-use
   durable terminal admission and independent antirollback authority.
   Source-mode Python CredWrite/Delete bypasses must be **actually
   eliminated or isolated** by approved machine policy/store
   architecture, not merely refused in one script.
3. Obtain actual code-signing authority, Windows Code Integrity
   / Smart App Control / WDAC administrator GO, installed-file
   provenance, rollback/recovery proof, the seven external
   GOV/SEC/REL approvals, original historical issue resolutions and
   three full unfiltered Windows product regressions.
4. Real key entry, provider C2 validation, signed installation on
   Kristian, real service activation, merging/releasing and updating
   the original Drive MASTER workbook/dashboard as a release remain
   prohibited before those independent conditions pass.

**P212 can close only as an isolated Windows-enforced build-step
refusal test, not as completed production package isolation.**
