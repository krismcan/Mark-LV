# P256 current-version source compatibility

16 November 2026. OM v2.1 diagnostic engineering handoff. Sole implementation
writer. Windows-native focused evidence has been captured on Kristian; independent read-only review is pending.
**REAL-KEY NO-GO. PRODUCTION HOLD. RELEASE HOLD.**

## Intake and scope

The requested worktree and branch matched at intake. HEAD was exactly
`a459bbec668c314819041de3fdc2e5d7c1914f6d`, P255, with parent
`4e2a605f6e8a7b079c9430dbf18461c2b2795a77` and tree
`f2f05eb455148d85ad27c13e9798eb8377ef8731`. Tracked, staged and untracked status
was clean. No milestone tag pointed at HEAD. `.codex/CURRENT_STATE.md` begins
with older 3 November Phase 10.2 material. Git and the explicit assignment
govern this bounded diagnostic. The latest completed product phase receives
no change from P256.

The three additions are `tools/byok_c1_p256_source_compatibility.py`,
`tests/test_byok_c1_p256_source_compatibility.py` and this evidence record.
Source inspection covered the six P251 pinned paths, both diagnostic helpers,
their original tests, the failure gate and P250/P251/P255 governance records.
All 1,034 inherited tracked paths must retain their exact base blobs.

## Versioned source admission

The CLI requires Windows CPython 3.12 with `-I -B`. It rejects Git environment
overrides and Python path/home/startup/inspection overrides. Fixed local Git
commands use `C:\Program Files\Git\cmd\git.exe`, disable optional writes,
replacement objects, lazy fetching and fsmonitor, and avoid status/diff filters.
No command requests network access. The interpreter, stdlib, Git installation
and local Git administration remain trusted prerequisites.

Admission requires the exact P256 root, plain ancestors, mutually consistent
linked-worktree pointer/backpointer/common directory, symbolic HEAD, fully
qualified branch ref, exact base/parent/tree, P251 ancestry, nonshallow SHA-1
history and a unique matching worktree registration. Replacement refs and grafts
cause refusal. Index entries must equal the base tree. Every tracked disk file
is read independently and compared to its Git blob, including files flagged
assume-unchanged or skip-worktree. Unexpected tracked changes, aliases,
symlink/reparse paths, hardlinks, missing/unreadable/oversized files, malformed
Git replies and any unexpected untracked file cause UNKNOWN/BLOCKED.
Untracked enumeration includes ignored files. Only these three untracked P256
additions are admitted. Logs belong outside the checkout.

The exact linked Git administration observed at intake is
`D:\Nayeon\P243_FULL_HISTORY_G1_20261115\.git\worktrees\CODEX_P256_PACKAGE_EFFECT_EXCLUSION_20261116`.
Its common directory is the enclosing repository's `.git`. This deliberately
bounded draft contract admits the authorized exact P255 base. Staging, a child
commit, relocation, alternate Git administration or changed source requires a
separately reviewed successor contract and currently yields UNKNOWN. Signing
and package-owner decisions remain pending. Root trust failure yields UNKNOWN.

Before execution, helper bytes must match the inherited raw SHA-256 pins.

| Helper | Raw SHA-256 |
| --- | --- |
| P251 `tools/byok_c1_effect_exposure_gate.py` | `990117324c727662d2909c96b73c135c7278baf69c242f312bdf24782d96330b` |
| P255 `tools/byok_c1_p255_effect_boundary.py` | `f5701e051d1f6c35e5d2261060f2aa1c8f0a3f86dcc92754fe33847f6fec320d` |

The loader executes those verified diagnostic snapshots with P255's project
import bound locally to verified P251. It leaves `sys.path` and `sys.modules`
alone. P255 `assess` reuses P251's six raw pins, scoped AST/text witnesses and
bounded source reader. Their implementations receive zero copied replacements.
Two complete Git/disk snapshots bracket assessment and must agree. Reports
include Git context, a raw tracked-manifest digest, hashes of the three additions,
six source records, selected evidence, six P255 routes and limitations.
No product module is imported and no source credential call is executed.

Quiescent files are required. Sampling cannot prevent hostile replacement or
ABA races. Raw hashes and local Git identity leave source authenticity,
runtime reachability, dependency closure, installed/loaded package identity,
effect telemetry and OS store isolation unresolved. Package-closure correlation
remains an optional follow-on. P211/P220 inventory, P223 host denial and P247
synthetic ordering receive zero new acceptance credit.

## Original P251 and current P256 behavior

| Invocation | Expected exact P256 checkout behavior |
| --- | --- |
| Original P251 `--report` | Exit 0, UNKNOWN/HOLD, `unintended_repository_root`. Its intended root remains `D:\Nayeon\CODEX_P251_EFFECT_PATH_RELEASE_GATE_20261116` |
| Original P251 `CheckoutTests.test_report_cli` | Original assertion still expects KNOWN_EFFECT_EXPOSURE and fails on the unmatched current root. The inherited host result was 26 PASS / 1 FAIL, exit 1 |
| Original P255 CLI | Exit 3, UNKNOWN/BLOCKED because its intended root remains the P255 worktree |
| New P256 CLI, fully admitted source | Exit 3, OPEN/BLOCKED, `source_context_admitted=true`, effect-owner exclusivity NOT_ESTABLISHED |
| New P256 CLI, any uncertainty | Exit 3, UNKNOWN/BLOCKED, `source_context_admitted=false` |

Both P256 outcomes keep release, real-key and independent-approval booleans
false. Invalid CLI arguments retain argparse exit 2. Additive tests demonstrate
the distinct old-root refusal alongside admitted current-source observations.
The original CLI failure remains unwaived and independent of P256 test results.

## Open Failures & Prior-Issues Review

| Issue / severity | Root cause, affected boundary and evidence | Repair, tests, independent review and disposition |
| --- | --- | --- |
| Version-root compatibility, material | P251 freezes its original worktree. Current-descendant CLI assertion receives UNKNOWN. P255 Windows receipt records 26 PASS / 1 FAIL | P256 adds a versioned diagnostic with adversarial admission tests. Original contract/failure retained. Native focused results are documented below; original P251 FAIL remains unwaived, and independent review is pending. Current diagnostic candidate only, acceptance HOLD |
| Python alternate effects, High | Native write/delete at backend lines 113/120, direct backend wrappers at 169/177, controller approval at 175/181, factory at 207, source launcher at 98 and window dispatch at 243 remain present | Six P255 route obligations and all P251 evidence reused. Reads/presence and buffer release remain inventoried too. Production-package effect exclusion and qualified SEC-03/04 decisions OPEN. HOLD |
| Original P76, material | Four original current-product failures reach incompatible historical admission before required downstream causal assertions. P253/P254 historical witnesses cover separate historical source | Original 4 FAIL remain unwaived. Historical tests/guards retain exact bytes. GOV-01/REL-06 qualified current-versus-historical acceptance required. HOLD |
| Original P96, High | Approval-current and lease-ownership observations precede separate effect callbacks. Revocation-to-effect race remains OPEN across ownership/process/restart obligations | Original race/fixtures retain exact bytes. Actual service-owner repair and adversarial/native evidence remain pending. P247 synthetic model supplies separate evidence. HOLD |
| P247 runtime, material missing evidence | Windows policy/Application Control blocked execution. x64 0/54 and x86 0/54 executed | Qualified environment owner required. Runtime acceptance OPEN. HOLD |
| Whole-product acceptance, High missing evidence | Qualified approvals 0/7 and full unfiltered regressions 0/3 | SEC-03, SEC-04, GOV-01, GOV-02, REL-05, REL-06 and REL-07 require actual qualified owners and authenticated evidence. Independent P256 review pending. RELEASE HOLD |

The engineering failure gate disposition remains HOLD for production progression
and seals. User-authorized work here is effect-free diagnostic containment.
Existing product/native credential entrypoints, signed-service code, protection
gates and original test/tool sources retain their exact base bytes.

## Inherited receipts and validation handoff

The preserved P255 governance record has raw SHA-256
`f1e81e593e595be4fcbdbd24cf7463cdf242fbef061ddbc27623d7b20368e87e9`.
Its Windows receipt SHA-256 is
`55B306D54418F3D873C84C3540AA7BFD659C5FFDD798DEC4420E9052E15AF23F`.
It records P255 17/17 PASS, source OPEN/BLOCKED exit 3, and original P251
26 PASS / 1 FAIL. The raw stderr/stdout hashes remain recorded there. External
receipts were read through inherited documentation. P256 performs no rehash
or rerun of those external receipts. The six inherited raw source pins remain
literal in P251 and in the preserved P251/P255 records.

Original P251 test raw SHA-256 remains
`e943659eebecc8cc9c84f74e711b243fc1e44024ae9e442ae08fbb169ce873aa`.
Original P255 test raw SHA-256 remains
`6dbc629017494c585c00ca6aed081b31ff5168eadc9472fe681adb4ce8a3ba32`.

No Windows Python execution was performed in this sandbox. Native host executions have subsequently run and are documented below. Static
inspection independently compared all 1,034 raw tracked files to the exact base
Git blobs and found zero drift. Git registration matched the requested branch,
root and HEAD. The added files have final LF and zero trailing whitespace.
Tracked/staged diffs and `git diff --check` are empty. These inspections supply
bounded evidence only. The new suite contains 29 test methods, including the
real isolated checkout CLI and synthetic adversarial cases. Run each
command separately from the exact P256 checkout and preserve its actual exit
and streams outside the repository.

```powershell
Set-Location 'D:\Nayeon\CODEX_P256_PACKAGE_EFFECT_EXCLUSION_20261116'
$p256Python = 'C:\Users\krist\AppData\Local\Python\pythoncore-3.12-64\python.exe'
& $p256Python -B -m unittest discover -s tests -p test_byok_c1_p256_source_compatibility.py -v
& $p256Python -I -B tools/byok_c1_p256_source_compatibility.py
& $p256Python -B -m unittest discover -s tests -p test_byok_c1_p255_effect_boundary.py -v
& $p256Python -B -m unittest discover -s tests -p test_byok_c1_p251_effect_exposure_gate.py -v
& $p256Python -B tools/byok_c1_effect_exposure_gate.py --report
@'
from pathlib import Path
for name in ('tools/byok_c1_p256_source_compatibility.py', 'tests/test_byok_c1_p256_source_compatibility.py'):
    compile(Path(name).read_bytes(), name, 'exec')
'@ | & $p256Python -I -B -
```

The last command compiles both additions in memory under the host Python.
Compiling to `.pyc` inside this checkout introduces
unexpected files and blocks source admission. Focused synthetic success grants
zero full-regression credit. Full unfiltered product regressions remain 0/3.
Independent read-only review follows host validation. This handoff leaves exactly
three additions unstaged and uncommitted at the requested starting HEAD.

## P256 actual Windows-native focused evidence ? 16 November 2026

The following native host evidence was captured on Kristian in
`D:\Nayeon\P256_VERSIONED_EFFECT_BOUNDARY_EVIDENCE_20261116`.

- First six-job runner receipt: `p256-windows-focused-receipt.json`, SHA256 `2EC6210AE62E47C93C0C6DCC004128860C658F418A8434DAEAD56E3A03CAB766`. Seven source files were unchanged before and after. Runner exit 1 from its sixth, wrong CLI invocation is preserved; this was not an all-green run.
- New P256 synthetic: 29/29 PASS, native exit 0, 3.485 seconds; stderr SHA256 `71FE17AB3C7B9998EB6B2823DAFF457A0276213BE11BC112769A777772242CC9`.
- P256 REAL source diagnostic, `python -I -B tools/byok_c1_p256_source_compatibility.py`: exit 3, 2.156 seconds, valid JSON OPEN/BLOCKED, `source_context_admitted=true`, `effect_owner_exclusivity=NOT_ESTABLISHED`, `real_key_admitted=false`, `release_admitted=false`, 6 routes, 0 issues; stdout SHA256 `FF7B46793DAC6F53B8A4E379848CBCF1C6A862A2B102C20202262CEDF6277082`.
- P255 original focused synthetic: 17/17 PASS, exit 0, 0.359 seconds; stderr SHA256 `599177F7F37F8C6D875D3EBFC8A92163315E82C48B68DC82167C8EF5E12EE149`.
- P251 original suite: 26 PASS / 1 FAIL (`test_report_cli` historical-root expectation), native exit 1, 0.532 seconds; stderr SHA256 `21351E027EB2E1C9EF8E4F73EA0D8E3BC572D11978A06F3A5AA08864566416C6`. Failure remains unmodified and unwaived.
- P251 original `--report` on P256: exit 0, UNKNOWN/HOLD, 0.062 seconds; stdout SHA256 `A446BCC6D7AE34AF3AE3DC674536AEA4E8DB61BD77ADAB8A740BC8DB4F8BE596`.
- First runner INVOCATION ERROR: executed the P255 tool as a filename, exit 1 during the project import, before P255 assessment, `ModuleNotFoundError: No module named 'tools'`; native stderr SHA256 `ED72C30C4414229E462BA60DFC0B2915BA6F18599B1E99DEA646F704BACBC7F0`. This is an invocation error, not a P255 code failure. The original receipt and stream are preserved.
- Separate corrected P255 module invocation, `python -B -m tools.byok_c1_p255_effect_boundary`: genuinely exit 3, UNKNOWN/BLOCKED. Supplemental receipt `p256-p255-corrected-invocation-receipt.json`, SHA256 `DFB2AE2C2510D0CC323DD1BB5B7C67682A47D6513CA849EC95C2B1650C8E13DE`; stdout SHA256 `6E80E2F3C1C7B8CC6E0550F18185AC3A5464B17C4A963C8594D84AEB2B055AC4`. Its separate host controller exited 0; the prior runner error remains preserved.
- Source/test SHA256 unchanged: probe `8DE6A25C64B1F557352D229767676F6174B97C2370A605C756B2A873EADB1816`, tests `28E70F30507F379BD5B8DA4FB0EDE63E56D884AA5DCAE3800EC122B7E829F7A2`. Production code unchanged. P96 OPEN; P76 current originals 4 FAIL; P247 x64 0/54 and x86 0/54; qualified signoffs 0/7; full-product regressions 0/3. Independent read-only review is pending. Real-key NO-GO and production release HOLD remain: this is NOT acceptance or security owner GO.
