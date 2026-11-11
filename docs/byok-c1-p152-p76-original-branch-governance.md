# Nayeon v1 — P152 original P76 exact-branch security contract and regression governance

**11 November 2026 | OM v2.1 | SOURCE-PRESERVING AUDIT | PRODUCTION RELEASE HOLD**

## Starting provenance

P151 exact commit `6d393b78c349bc07d9110e15f222e26f1dbe05f7`, draft PR #76,
genuine Windows run #42975449717. Three unchanged original BYOK scope
tests each ran in a separate Windows interpreter. The historical synthetic
topology test passed (native exit 0), while two live admission tests returned
native exit 1 with explicit original P76 exact-branch refusals. Two native
Python stack snapshots appear in the retained raw Windows logs, even though
P151's naive line-prefix summary counted zero. P150 full historical BYOK
module previously timed out at 190s and remains HOLD.

P152 records the *exact source fact* behind those refusals. Original
`tests/phase8_byok_c1_p76_scope.py` freezes:

`BRANCH = "byok-c1-p80-sealed-historical-fixture-20261106"`

Its `assert_p76_offline_integrity()` checks the real Git branch identity
**before any historical parent tree, authenticated seal, source/index/disk
proof or source-only success**. It is an isolated, non-privileged P76
historical prototype, not a general-purpose security admissibility
verdict for every later BYOK branch. An ordinary P151/P152 branch must
correctly REFUSE. Do not substitute/pretend the historical branch,
change this gate to accept all branches, or treat a refusal as a passed
original current-branch admission test.

## P152 exact two-run audit

P152 begins directly from exact P151 Git SHA and creates precisely three
new review-only paths: this doc, one Windows workflow and one reporter
script. No original production, WinCred, original tests, signed companion
guard, P139 Win32 native opened-handle checker, historical Git refs or
security authority are changed. GitHub CI requires exact parent ancestry,
only three new source paths, clean Git source, and intact test-source
SHA-256 against `git show <P151>:` for both frozen P76 gate and its
test module.

On a **genuine disposable GitHub Windows-2025 Python 3.12 runner**,
require P139's UNCHANGED fixed local C: owned random temporary root
no-reparse and opened-handle identity verification. Only subprocess
environment TEMP/TMP/TMPDIR point to this verified test root. Never
change system policy or run a test on Kristian's production credentials.

Two independently logged native child processes (no monkey-patching of
the actual gate or test source):

1. Call the *real* original `assert_p76_offline_integrity()` on the
   actual P152 Git branch, expect exact negative native return **1**
   with `P76ScopeRefused: wrong exact P76 prototype branch`.
   An unexpected acceptance is an audit failure, not a release GO.
2. Run `python -B -m unittest -v
   tests.test_phase8_byok_c1_p76_scope` with ALL original **10**
   historical tests, no filters, skips, xfails or assertion edits. Keep
   genuine native exit, full original combined log SHA-256, final
   unittest footer/count, real FAIL/ERROR method IDs and complete
   raw Windows source provenance. A successful CI *collection* is NOT
   the same as a passing original historical suite.

The original suite has a negative `test_wrong_branch_refused_before_other_work`
control as well as positive legacy real-branch acceptance cases.
Those positive cases may rightly fail when executed on a newer P152
branch. Their result is preserved unmodified and must be assessed by
an independently approved historical governance policy, not hidden
from the product regression count.

## Review decision needed (external qualified reviewer)

1. Verify the exact original P76 source and legitimate, reviewable
   historical branch/reference lineage, annotated seals, negative
   controls, provenance and current-source migration coverage.
2. Decide and record whether the exact historical acceptance suite
   belongs to the older P80 frozen topology, and what **separately
   named, newly approved** production-current branch negative/positive
   test suite must replace its branch-specific *positive* claims.
   Preserve every old negative denial and historical Git-seal test.
   A new suite needs proof that real untrusted branch admits nothing,
   includes no credential/provider side effect, and provides explicit
   threat-model coverage; never mock or weaken an actual security gate.
3. Obtain a named independent qualified security reviewer and
   explicit current-user WinCred scope decision for the narrowed
   P132/P133 offline manual Review→Approve product. Same-user malware,
   same-presence ABA, crash uncertainty, copy/clipboard risks and
   synthetic test limits remain openly documented.
4. Complete three genuine unfiltered current-product Windows
   regressions under an independently accepted, versioned inventory,
   with full native zero exit, complete footers, raw log hashes and
   original old-suite negative evidence. Scoped triad P141 and these
   additive source audits are not substitutes.
5. Obtain real publisher-signed, hash-pinned main/helper installation,
   protected update/ACL policy, Smart App Control/WDAC code-integrity
   owner GO and explicit production admission. P140 pins must stay
   empty and release approval FALSE until legitimate authority acts.

Original privileged BYOK C1 G0–G6 remain separately OPEN, including P96
and P124. No real API key, production WinCred on Kristian, provider live
validation, privileged service, protected registry/TPM change, unsigned
EXE run on Kristian, security-policy bypass, GitHub merge/tag/release
or Google Drive release master/dashboard update is authorised now.

**P152 audit DONE only after genuine Windows evidence. All original
historical failure holds and BYOK C1 user-scope production HOLD persist.**
