# BYOK C1 P316: actual service startup recovery boundary

Date: 2026-11-24. OM v2.1. Source candidate only; CTO independent review and publication pending. Codex is the sole source writer. Parent: `1e1c0f80e75d1d3e49f1e3135ea3546c77e65a14`; branch: `byok-c1-p316-service-recovery-boundary-20261124`.

## Startup integration

Actual `CustodyService.OnStart` retains both existing restricted virtual-account primary-token, session-zero and no-impersonation checks. A single inserted call then invokes `ServiceRecoveryBoundary.RequireDenialOnlyStart(VerifyExecutingIdentity)` before `BeginStart`, transaction ownership or either pipe constructor. The boundary reuses the existing identity verifier before profile resolution/observation and after observation. A refusal enters the existing terminal lifecycle catch, sets failure exit status, closes any pipes and faults the coordinator. No owner or pipe has been created on this refusal route. Token validation, lifecycle and denial protocol bodies are unchanged.

The service resolves only `Environment.SpecialFolder.LocalApplicationData` using `SpecialFolderOption.DoNotVerify`, without creating it. Its only recovery location is the immediate fixed child `NayeonV1ByokCustody.Recovery.v1`. No argument, environment flag, configuration or caller path selects the startup location. The internal observation helper accepts a profile solely to allow testing against disposable fixtures; it has no startup effects or credential API. The internal decision helper allows only the defined `MissingLeaf` outcome; unknown enum values refuse.

The observer rejects noncanonical, relative, UNC, device, ambiguous and non-fixed-drive paths. Every ancestor through the root must exist, be a directory, be accessible to attribute inspection and have no reparse attribute. It inspects child attributes without opening content. Any existing child type yields `RecoveryRequired`, including files, directories and reparse entries. Only `FileNotFoundException` at the immediate child can indicate absence; `DirectoryNotFoundException` and all other uncertainty yield `Unknown`. Ancestors are checked before and after child observation, with a second child absence observation and final ancestor check for the missing case. An inaccessible or unavailable profile refuses. Unexpected exceptions refuse without a temporary-directory or LocalSystem fallback.

This code creates no directories, enumerates nothing, opens no content, writes/deletes nothing, calls no DPAPI or native credential store and never enables effects. Denial-only startup remains NOT AUTHORIZED and release HOLD.

## Limits and qualification

This is a read-only observation, not protected persistent authority, atomic antirollback, proof of absence against races, authorization or authorized profile qualification. Path replacement, ACL/profile provisioning, profile mapping and concurrent changes are not qualified by attribute checks. Repeated observations do not eliminate TOCTOU. No durable production journal writer exists yet; this fixed marker is not a newly enabled journal. Existing journal and hosted fixture implementations remain unchanged and are not called by this startup boundary. Actual service installation/startup, SCM teardown, production profile access and real keys are untested and unauthorized here.

## Open Failures & Prior-Issues Review

Bounded review: supplied P315 checkpoint (hosted 4/4 PASS, run 45260494638, draft PR #234), P304 lifecycle tests, P307 service denial/closure tests, P312 assembly/source topology, P315 workflow, actual startup/coordinator/project and engineering failure gate. No broad historical review or claim that those supplied hosted results were independently rerun.

| Issue / source | Severity and evidence | Boundary / containment | Repair, review, disposition |
| --- | --- | --- | --- |
| P96, supplied current status | HIGH OPEN; root cause and reproduced closure evidence unavailable in this bounded task | Production custody/real keys remain NO-GO; read-only boundary grants no authority | No repair claimed; independent closure absent; HOLD |
| P292, supplied current status | x86 SCM teardown UNKNOWN; root cause/closure unproven | No service install, OnStart execution or teardown tests; denial owners and cleanup unchanged | No repair claimed; independent review pending; HOLD |
| Profile/ACL/races | Qualification missing; attribute observations cannot establish persistent authority | Only missing leaf under observed valid ancestry permits existing denial-only mode; uncertainty refuses | No authorized profile qualification or antirollback claim; HOLD for effects |
| Local toolchain | Legacy framework MSBuild rejects `/warnaserror`; retry using project warning property reports missing .NET 4.8 reference assemblies (MSB3644) and toolset 15 fallback | No download/install/retarget; that build is not qualified evidence | Direct installed CSC compilation used for bounded source checks; modern hosted MSBuild remains pending |
| Local harness invocation | Relative CSC source paths were interpreted as options; initial P307 output name mismatched existing friend identity | Compile commands only; no test execution or product defect | Absolute paths and existing `P307.ProductService.Tests` identity corrected; final compile matrix passed |

GO only for the expressly requested read-only source candidate review. Production/release disposition HOLD. P96 HIGH OPEN, P292 UNKNOWN, approvals 0/7, full product regressions 0/3 remain unchanged. Independent CTO review and hosted validation are pending; no milestone seal is claimed.

## Validation

Local compile-only: installed framework CSC, warning level 4 and warnings as errors, actual service sources selected from the actual csproj, x64/x86 Debug/Release. Service plus P304, P307, P312, P313, P314, P315 and P316 friends compile. These direct compiler checks do not qualify the missing .NET 4.8 targeting pack or replace modern MSBuild. No local executable was run. No native vault test, service invocation, product pipe, real key or OS-policy change occurred.

The new Windows-2022 workflow admits only the exact same-repository draft head/base refs and fixed P315 base SHA, uses SHA-pinned checkout without persisted credentials, checks the exact six-path delta and minimal startup/project insertion, freezes prior sources/tests/workflows, hashes source witnesses before/after, and builds the actual service with MSBuild plus CSC friends in all four matrix cells. Fixed markers and bounded process/output watchdogs fail closed. It runs P316 metadata tests and frozen P312 `--readonly` only, never native vault cases, service Main/OnStart or installation. It downloads no tools. Workflow publication/execution is reserved for the CTO.

P316 tests cover pure decisions including unknown values; static ordering of actual OnStart before owners/pipes and terminal catch; absence of secret/mutation APIs in the helper; invalid paths; actual observation of harness-created disposable empty fixtures for missing leaf, existing directory, existing file and missing parent; metadata/entry preservation and explicit cleanup. Tests do not resolve the service profile or invoke the startup wrapper. They prove bounded source/fixture behavior only, not actual service startup success.

Only the six requested files are changed. `.codex/CURRENT_STATE.md` predates this Git branch and is intentionally untouched under the exact scope. No staging, commit, tag, push, merge, workbook or dashboard update.

Final local static checks PASS: both workflow PowerShell blocks parse; exact parent-to-candidate OnStart/project insertions match; P304/P307/P312-P315 tests and P315 workflow remain unchanged; six-path inventory and whitespace checks pass. Hosted execution and independent review remain pending.
