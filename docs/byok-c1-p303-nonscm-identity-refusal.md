# P303 hosted nonSCM identity refusal — packaging review

Date: 2026-11-22. Codex sole writer; OM v2.1.
Disposition: hosted evidence pending; production HOLD; real-key NO-GO.

## Exact scope and custody

Parent: `6b5afa18e24d771c604f3f760eca5b5637904478` (P302).
Base branch: `byok-c1-p302-cross-phase-retirement-acceptance-20261122`.
Head branch: `byok-c1-p303-nonscm-identity-refusal-20261122`.
The next hosted head must be exactly one repair commit above initial failed P303
`ffa25bb1aa2b0c771fe9ba4a55ea5cb095b89d18`, whose sole parent is the P302 SHA above.
Checkout fetch-depth is 3; both exact sole-parent links and rev-list count 2
from P302 to the new head are required. This does not authorize a local commit.
The same-repository pull request must remain a draft with the exact base SHA.
The cumulative change against P302 must remain exactly three additions:

- `tests/p303_nonscm_refusal/P303NonScmIdentityRefusalTests.cs`
- `.github/workflows/p303-windows-nonscm-identity-refusal.yml`
- `docs/byok-c1-p303-nonscm-identity-refusal.md`

All 1,218 inherited regular Git files must retain their blobs and modes.
This repair modifies only the existing workflow and this document; the P303 C#
test and all P301/older frozen sources remain unchanged. No local Python,
compiled binary execution, SCM action, staging, commit, or push is authorized here.
No credentials or security policy changes are included.
No workbook or dashboard update is due until C1 is complete.

Frozen SHA256 pins, over source bytes:

```text
P303NonScmIdentityRefusalTests.cs
9FA2A1A5CF4B4EB923D6B4A5B6BF6B877C48D1BECD78A0AE8FF377AEB5C6E72B
P301DispatcherOwnedSyntheticService.cs
5D129C8FB908A281B493587F850E2A4012078EA03B4A4948C66AACE8E380B48D
```

The workflow verifies these pins and the exact Git head/parent/addition shape.
Pre/post SHA256 manifests cover every tracked file's actual checkout bytes.
The manifest digest and individual hashes are retained outside the checkout.
Index, worktree, untracked, and ignored paths must remain clean.
Git receives argument arrays; event data is never inserted into shell code.
Checkout disables credential persistence, submodules, LFS, and autocrlf conversion.
Checkout and artifact actions are pinned to the requested immutable commits.

## Hosted build and execution boundary

Windows-2022 has independent x64 and x86 jobs, each limited to eight minutes.
Framework64 and Framework respectively supply .NET Framework `csc.exe`.
The exact ten-source closure comprises the three P95/P96 custody fixtures,
P265, P267, P268, P269, P301, P301 source review, and the frozen P303 test.
No additional product source is included.
All ten original allowlisted source names remain in `$sources` for hash pins.
Each compiler input is independently joined to the verified GITHUB_WORKSPACE
checkout root, resolved with `Resolve-Path -LiteralPath`, and required to be an
absolute ordinary file within that checkout with no reparse path components.
Both positive and negative compiler invocations receive `$absoluteSources`.
Every compiler/test child receives explicit ProcessStartInfo.WorkingDirectory
equal to the retained verified root. Source allowlist, pins, compiler guards,
timeouts, output caps, cleanup and error handling remain enforced.
References are System.dll, System.Core.dll, and System.ServiceProcess.dll.
Builds use `/noconfig /warn:4 /warnaserror+ /target:exe` and the matrix platform.
The complete DEBUG/TEST_ONLY/isolated/P265/P267/P268/P269/P301/P303 flags are required.
Only `P301SourceReviewTests` and `P303NonScmIdentityRefusalTests` are entrypoints.
Both positive compilations must return raw 0 with zero diagnostics.
Missing C1_P303 and RELEASE builds must return raw 1, CS1029, and no binary.

Each process receives 30 seconds for natural exit; success requires raw exit 0.
Timeout cleanup uses the owned Process object, never PID-based taskkill.
Cleanup has a separate five-second wait and separately recorded exit result.
Asynchronous managed stdout/stderr handlers cap each captured stream at 64 Ki characters.
Each stream has a bounded five-second event-drain wait; overflow or missing EOF fails.
Timeout, cleanup success, or partial output can never substitute for natural success.
Any failure means HOLD, with no retry.
Artifacts contain bounded text evidence and manifests, never executables.

P301 runs first with exactly the checkout path as its sole argument.
Required output: `P301_SOURCE_CHECKS=17; runtime refusal=NOT RUN`.
Its optional hosted refusal mode is not used.
P303 then runs with no arguments and must naturally return 0 with:

```text
P303_NONSCM_REFUSAL=PASS CHECKS=17 BITS=32/64 OWNER_CREATED=NO SCM_USED=NO PRODUCTION=HOLD
```

BITS must match the respective job, rather than the literal `32/64` notation.
The guarded harness verifies the actual non-service Windows OS token first.
Only then may ephemeral private reflection invoke the negative OnStart scenarios.
The identity mismatch prevents reaching P269 worker construction.
The frozen P301 source-order baseline must pass before any P303 execution.
Owner-null terminal observations prove no surviving owner, not zero transient allocation.
No service Main executable or complete valid four-argument ImagePath vector is run.
There is no ServiceBase.Run, SCM install/start/stop/delete, or service runtime proof.
There is no IPC, WinCred, DPAPI, network, provider, or real-key effect.

## Evidence and unresolved gates

First real hosted run `45043952896` on draft PR #222 remains RED, 2/2 jobs:
x64 `137274308042`, x86 `137274308456`. User-supplied independently downloaded
original artifacts are `p303-nonscm-x64` id `14762408818` and
`p303-nonscm-x86` id `14762222952`. In both, the original
`compile-P301SourceReviewTests.txt` records RAW=1, DRAIN=BOUNDED and exactly
10 CS1504 missing-source errors. For example, the compiler attempted
`d:/a/Mark-LV/Mark-LV/CustodyLedger.cs` while the tracked input is
`tests/p95_native_custody_preflight/CustodyLedger.cs`.
The workflow's relative compiler source arguments resolved incorrectly;
failure occurred before any P301/P303 executable test, proving no security behavior.
The targeted repair supplies verified absolute compiler inputs and an explicit
child working directory, with the exact two-link repair ancestry above.
Original RED evidence is preserved; repaired hosted validation remains PENDING
on both architectures. Local validation is limited to offline PowerShell AST
parsing and static diff inspection; it cannot establish compiler/runtime success.

Supplied local evidence: x64/x86 C# compiler-only, warnaserror+, raw 0, diagnostics 0.
No local binary was executed; this packaging step does not rerun those builds.
P301 17/17 hosted source checks already pass in the supplied baseline.
P301 compiles; P302 current acceptance is 77 checks on each architecture.
New P303 hosted direct OnStart rejection evidence is still PENDING on both architectures.
No hosted success is claimed by creating this workflow or document.

P268/P269 already test synthetic atomic revoke; repeating it is not P303's purpose.
P303 uniquely adds real Windows OS negative identity refusal at the OnStart boundary.
It does not close the original P96 race or qualify protected production service behavior.
No redundant P292-DIAG run is included.
Original P96 race severity remains HIGH and unwaived.
P292 x86 teardown/deletion-absence evidence remains UNKNOWN.
Protected service/IPC/WinCred profile and real consent remain unqualified.
Approvals remain 0/7; accepted complete original Windows product regressions remain 0/3.
These material gates remain HOLD; this bounded negative test grants no waiver.
Real-key NO-GO and production HOLD remain in force after any P303 pass.
