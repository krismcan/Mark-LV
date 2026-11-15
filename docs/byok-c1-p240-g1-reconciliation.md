# P240 source-witness correction; additional transport NOT ADMITTED

15 November 2026. Candidate engineering only; production HOLD.

## Architecture decision before implementation

Use the explicitly permitted **source-equality-only fallback**. Do not add a
transport interceptor or run another instrumented G1 candidate. P240 fixes the
representation comparison in a new independent consumer; it does not modify,
patch at runtime, or reinterpret the exits of P239 or P238. The proposed file
name does not mean an additional safe transport has been admitted.

P234's original `canonical(value)` is the serialization contract:
`(json.dumps(value, sort_keys=True, indent=2) + "\n").encode("utf8")`.
P239's parent instead compares `after == json.loads(source_before_bytes)`.
`historical_tags()` returns tuple-valued mappings, which JSON decodes as lists.
Thus identical serialized witnesses can produce a false Python equality result.
Do not normalize source files, replace source guards, compare only selected
fields, or call JSON structural equality a byte comparison.

The new producer writes the original canonical bytes exclusively. The consumer
retains an immutable `bytes` snapshot and its independent SHA-256, runs the
original complete source verifier again, serializes that fresh result with the
original serializer, and compares the complete byte strings. For file inputs it
also rereads the original witness after verification and rejects changed bytes.
Missing, noncanonical, malformed, foreign-source or structurally changed witnesses
fail closed. There is no remembered positive, cached verdict, exception waiver,
credential input, product import, or machine action. A successful source-only
check returns 0 for that check only; there is no candidate/regression PASS.

The optional reconcile mode consumes a private witness from an original child
with a separately captured expected SHA-256. This is also usable after a failed
or timed-out child, **only after its owner has independently proved quiescence**.
It cannot prove containment, test success, or close a timeout. This harness does
not launch or supervise a G1 child. It provides no candidate mode and therefore
cannot silently schedule an extra G1. The workflow performs source and synthetic
checks only. P239's 180-second whole-child budget, 20-second original request
bounds, Job containment, progress and 3/124/125/1 result history stay unchanged.

## Biggest repeat process cause and rejected scope expansion

User-supplied authentic P239 hosted run **43708920918**: P233 source
`096048db17c7c1f9402dfd16a7deb31e9ebdc81d`, P239 parent of P240
`d8173c3f3345e17389cc3cb646b320abe3610ef3`. Full-history source guard and
65/65 hosted synthetics passed. At the last valid progress sample, 179.765s:
19/23 subtests completed, zero failures; 920 fresh validated B reads;
7,360 completed delegated check_output calls (show 4,233; cat-file 1,070;
ls-tree 456; other 1,601). G1 did not complete by 180s. Job emptiness was
confirmed; classifier 124 and final diagnostic 125 remain historical facts.
These figures are supplied evidence, not a locally replayed or newly validated
run. Both supplied raw witness SHA-256 values were
`BA14720C0861F00EAD2FF47CD4A155601D82755B5891AB1CDD75805C0CFD819`.
The representation defect does not establish mutation, and its repair does not
retroactively change P239's final exit or establish G1 success.

The largest **counted remaining delegated category** is `show` (57.5% of
completed delegated calls); this is not a measured attribution of wall time.
Source tracing identifies repeated historical seal authentication as a cause:

| Original entrypoint | Repeated work and authority seam |
| --- | --- |
| `test_every_candidate_source_byte_is_bound` | 23 targets; each enters `candidate(disk_mutation=tamper)` and requires the exact target hit once and `BYOK B candidate byte mismatch`. |
| B `candidate()` | Before installing seams, authenticates `gate.prior._tree(gate.PARENT)`, `successor._baseline()`, then 23 original B shows. |
| Phase10 `_baseline()` | Tag/commit/tree authentication, B `_parent_tree()`, complete B inventory and 23 pinned B shows. |
| B `_parent_tree()` | Calls A `_parent_tree()`, authenticates A parent/tag/tree, then 11 historical A-pin shows. |
| A `_parent_tree()` and 8.37 `_seal()` | Recursively checks older 8.36, 8.34, 8.33, 8.32 and 8.31/8.30 seals and their per-file source shows. |
| 8.32 `_history()` | Full inventories, normalized 8.30/8.31 pins, ancestry and exact annotated seal reads. |

P238 already replaces only the 23 source-bound B commit/path queries, with a
fresh batch exchange and validation each time. Its allowlist is not an allowlist
for earlier seals. Additional older-seal substitution needs a separately reviewed
finite commit/path/OID/raw-byte/SHA manifest and preservation of each original
normalization/self-pin rule. 8.30/8.31 and 8.33 historical normalization differ
from later raw-byte checks. Constructing that new manifest or returning a stored
`_baseline()`, `_parent_tree()` or `_seal()` success is not proved equivalent by
P239's aggregate counters. Mutable tag/ref/type/peel, ancestry, inventory, index,
branch and HEAD operations must still execute through their original seams.

Read the actual B test, B/A/Phase10 migration helpers, 8.30 through 8.37 seal
readers, P238/P239 scripts and adversary/mock shapes before this decision.
No claim is made that all immutable-only acceleration is impossible. It is
**not proved here**; lack of Python and full local history prevents a meaningful
runtime equivalence experiment. Do not invent a speedup from process counts.

## Historical negative-test shapes preserved

All original source, tests, literal pins and negative assertions remain
unchanged. This fallback installs **no mocks, wrappers or substitutions** around
subprocess, Git, disk, integrity functions or original test fixtures. Therefore
there is no native-subprocess expectation it is authorized to intercept.

| Inspected shape | Required preservation / decision |
| --- | --- |
| B fixture captures `actual = gate.prior._git`, then patches that object with a transforming mock | Never replace that seam, precompute admission, or suppress the transform's returned tampered bytes. |
| B target mutation and `hits == [target]` | Every original negative remains literal; no early unrelated refusal is counted as the target canary. |
| B historical A shows transformed after `actual(*args)` | Cached high-level results would suppress the causal mutation; denied. |
| B parent/tag/type/peel, wrong branch/HEAD/object format | Native mutable/identity operations stay original, including failures. |
| Partial/extra stage, merge/wrong parent, ignored aliases, flags, raw deltas and frozen data | No index/tree/disk or verdict caching; no topology spoofing. |
| Missing/zero pins, malformed self-pin, CRLF/binary changes and reparse/link readers | No pin relaxation, newline normalization or source-reader substitution. |
| 8.32 second-read tree injection and historical forged preimage replay; B projected-brain/replay tests | Original read order, reached-call checks and before/after positive admissions stay original. |
| 8.33/8.34 fixtures replace historical pin dictionaries and disk readers for synthetic topologies | A generalized wrapper cannot learn its immutable allowlist from these mutable fixture objects. Denied. |
| 8.36/8.37 frozen readers and forged seal responses | No change to original mock side effects, ref resolution or failure propagation. |
| 8.37 real A-02 fresh subprocess test wraps `subprocess.run` and asserts one actual `-I -B -c` launch | Native subprocess is observable test behavior; no wrapper, emulation or replacement is installed. |

This is source preservation evidence, not execution of the historical negatives.
The new synthetic suite tests the equality consumer and exact source envelope,
without importing original test modules or claiming original regressions passed.

## Validation and handoff

Initial branch and HEAD exactly match the requested worktree and P239 parent;
working tree/index initially clean. No tag points at initial HEAD.
Git reports shallow history and `core.autocrlf=true`; local existing scripts are
CRLF and fail the historical raw LF pins. `.codex/CURRENT_STATE.md` describes an
older November 3 product candidate and is not current P239 status. It is preserved.
No configuration change, checkout normalization or source-pin workaround is made.

Implementation and static checks are recorded below after the four files exist.
Authoritative Python
`C:\Users\krist\AppData\Local\Python\pythoncore-3.12-64\python.exe`
was unavailable (PowerShell command-not-found); `python` and `py` were absent
from PATH. No interpreter/package installation, copying or network workaround.
Host syntax, focused synthetics and compile checks remain required on exact LF
review bytes; no host runtime exit or PASS is fabricated. Do not run full G1 on
Kristian. The workflow has no G1 step. Nayeon can review/publish separately after
host synthetics, without this task staging, committing, pushing, merging or tagging.

## Bounded open issues (no retrospective audit or new product phase)

| Issue | Severity / cause / boundary | Evidence, repair, review and disposition |
| --- | --- | --- |
| P239 witness mismatch | Material diagnostic representation defect; tuple/list equality at parent consumer | Source cause identified; additive canonical-byte correction and adversaries authored. Host execution and independent review pending; diagnostic repair candidate only. |
| G1 and three other original timeouts | Material regression blockers; G1 has high repeated Git process counts, no completed run | No new transport/equivalence or timeout closure; original histories retained; HOLD. |
| Four P76 wrong-branch failures | Material original failures through historical successor entrypoints | No branch spoof/assertion edit; original failures unresolved; HOLD. |
| P96 revoke/effect race | High, terminal-check/effect serialization across service/coordinator actors | No credential/security/service edits, no closure or new effects; HOLD. |
| SEC03/04 | High independent architecture decisions and qualified reviews missing | No approval inferred from synthetic checks; HOLD. |
| Product validation/real keys | Full unfiltered regressions 0/3; real-key and production evidence absent | Real-key NO-GO; production HOLD; no workbook/dashboard update. |

Disposition: authorized additive diagnostic correction only. No release seal,
source-equivalence approval for a new transport, or product phase advancement.

## Final local static receipt

At the first completed static checkpoint, exactly the four requested paths were
untracked additions. All existing tracked files and the index were unchanged;
branch and HEAD remained the exact requested
branch at `d8173c3f3345e17389cc3cb646b320abe3610ef3`.
`git diff --exit-code`, `git diff --cached --exit-code`, and
`git diff --check` each returned native exit **0**. Because those commands do
not check untracked additions, all four new raw files were separately inspected:
LF only, final newline present, zero trailing-whitespace matches. The four
workflow run blocks each passed PowerShell's native parser with zero errors;
this is not Python or YAML validation. `git diff --no-index --check` against
`/dev/null` returned **1** for each added file, with newline-conversion warnings
from existing `core.autocrlf=true`, and no whitespace-error diagnostics. Those
nonzero comparison exits are not presented as test passes.

Raw Git blob SHA-256 values for the three original dependencies were computed
through Git's binary stdout stream and match the literal P240 pins. Local CRLF
copies were neither executed nor converted. Raw new-file receipts:

| File | SHA-256 |
| --- | --- |
| `scripts/p240_g1_safe_transport.py` | `794D8B6C80E44A5DA379359D3DBAA6CE96D21AE96B0F97BA11949759EE4515F3` |
| `scripts/p240_g1_safe_transport_selftest.py` | `DD011D785E317B1397423743BA209F97487931D81942D3C02192B9413ADE6002` |
| `.github/workflows/p240-g1-safe-transport.yml` | `CDE8F8CF82198AAF2A89D1682732F0F6FE5AF3F0CFE9DFB528CDF67520BF0047` |

The selftest contains **22 authored methods, zero executed here**. Python AST,
compileall, synthetics, original negative execution, source-check execution,
hosted execution and independent source review remain pending. Existing genuine
original negative assertions are **100% untouched**, not claimed 100% passing.
No original G1 or candidate G1 ran, and no speedup is claimed.

On Nayeon's separate exact-LF validation copy, preserving the raw three pinned
dependencies and the four new paths:

```powershell
& 'C:\Users\krist\AppData\Local\Python\pythoncore-3.12-64\python.exe' -B scripts/p240_g1_safe_transport_selftest.py
```

Record the actual exit, log hash and structured synthetic report; direct any
compile output to private temporary data outside the source checkout. Do not
normalize this checkout's historical files to make a pin pass. Following host
synthetics and review, the separately approved publication must be exactly one
child of P239 with only these four added paths for the branch-push workflow to
admit it. The workflow uses full-history raw controller/authentic checkouts,
Python 3.12, exact P239/P238/P234 dependency pins, original full P233 verification,
then synthetics before the fresh source-only equality check. Fixed JSON and
private log SHA-256 receipts are the only uploads. No raw witness or log upload,
G1 candidate, production deployment or service installation is added.

This session issued no staging, commit, tag, merge, push, external network,
credential-inspection or Google workbook/dashboard operation. All preexisting
P76, timeout, P96, SEC03/04 and production HOLDs remain unresolved; full unfiltered
product regressions remain **0/3**, real-key **NO-GO**.

Final index discrepancy: a subsequent check observed all four additions staged,
with the last documentation corrections unstaged. No staging command was issued
by this implementation session; the origin of the index change is unknown.
The staged path list is exactly the four requested additions, staged whitespace
check returned native exit 0, and HEAD/branch remain unchanged. This index state
was preserved rather than resetting another actor's staging. The earlier
clean-index receipt above describes its actual observation time, not the final
index state. No original tracked source/test/pin path is in the staged delta.

## Independent Nayeon Windows host validation — actual executed results

On Kristian, Nayeon independently executed the **final four-addition P240
source** from a separate LF-preserving `D:\Nayeon\P240_HOST_EVIDENCE_20261115\validation_only_lf`
directory without modifying this Codex or any historical/product worktree.
Tracked P234, P238 and P239 dependencies were reconstructed as **exact raw Git
blob bytes** from P239 parent `d8173c3f3345e17389cc3cb646b320abe3610ef3`
and matched all three P240 raw SHA-256 pins. The two additive P240 scripts
were copied unchanged and validated there; no source-pin bypass, original G1
or service effect was executed.

**Windows Python 3.12 focused adversarial suite: 22/22 PASS, native exit 0,
zero failures/errors/skips.** Final combined log
`D:\Nayeon\P240_HOST_EVIDENCE_20261115\host_p240_synthetic.log`
SHA256 `B25904F02BE6831631DCEB8E4CC5FD6C1CE795458C4152063E098FA1D5E062FB`.
Structured receipt `host_p240_synthetic.json` SHA256
`0DE51BBDD0EE81DB34C10ACC23B89E41FD1597DE1B7E3379D70F31B8955E0D69`.
Both P240 scripts passed independent Windows Python AST syntax parsing
(native exit 0), AST log SHA256
`B2276F908D24CB53EB7A91A017020295C103C4DAEDA9D02D2DDA9D8E1670803E`.
This supersedes the implementation sandbox's statement that Python was
unavailable; these are genuine focused host results, **not** full unfiltered
regressions or an actual G1 pass.

No original source, pins, negative tests, WinCred service, historical commits,
prior worktrees, product configuration or Google workbook/dashboard were changed.
The P240 workflow deliberately contains **no G1 step** and can only verify
source equality. All seven qualified approvals remain outstanding; four
original P76 branch refusals, original G1/three other timeouts, P96 native race,
SEC03/04 and full unfiltered product Windows regressions 0/3 remain OPEN/HOLD.
