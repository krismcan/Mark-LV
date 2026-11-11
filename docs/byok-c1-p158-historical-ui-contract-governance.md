# Nayeon v1 — P158 immutable historical UI regression governance and post-P133 successor

**11 November 2026 | OM v2.1 | ISOLATED DRAFT | PRODUCTION RELEASE HOLD**

## Predecessor and exact source authority

The exact verified P157 head SHA is 061888b3515a2923dc44eb2f17eb46e768266761, PR #82 open, draft, unmerged. P157 used actual hosted Windows-2025 Python 3.12, original test source unchanged. The new adverse real Tk proof processed 63 bounded view states and 63 actual UI writes, with 0 forbidden service/storage/native/network/process effects. Of 41 unmodified historical tests, 38 passed and three **failed**; they are NOT cured.

P158 uses a new isolated branch at that exact SHA and introduces only four additive files: this report, a **new** post-P133 unittest module, a raw original Windows ledger driver and a hosted Windows workflow. It does NOT change P86/P87, Phase8.31, P76/P85, product UI, user-scope Credential Manager source, P139 native opened-handle trust or P140 signed launch gate.

## What changed and why a versioned successor is justified for review (not yet approved)

P86 and P87 originally asserted exactly two ttk.Button controls on ConnectionWindow. P133 later deliberately introduced a third, manually launched, user-scoped offline key setup button; P133's original 25/25 genuine Windows tests were observed passing in P156. The three original P86/P87 assertions (two in P86, one in P87) are *legitimate failures against the newer source*. Removing the button to satisfy those older assertions would undo intended product functionality; rewriting the originals would destroy regression evidence.

A post-P133 successor **must therefore be versioned and traceable**, not retroactively called the original test passing.

## Genuine Windows acceptance design

The P158 runner requires exact P157 base ancestry, clean clone and a four-path additive-only diff. It uses unchanged original P139 native Windows opened-handle trust checks for a new, owned disposable C: temp root. The process does not modify Kristian's original 17-dirty-path product worktree.

It enforces byte-level Git blob identity for 17 source and test paths including old P86/P87/P88/P133, Phase8.31, P76/P85 frozen original tests, current-user credential backend, original UI, launch bridge, P139 native handle guard and P140 frozen signed companion admission.

A **new** P158 Windows-only positive test suite checks: the exactly named three buttons and unchanged legacy buttons; default NOT OBSERVED and no startup launcher; explicit fake child only after human-click callback; child command/environment secret scrubbing; previous offline preview blocks concurrent setup; a synthetic custody view never launches a key setup; stale pane/foreign-thread callbacks never launch; no launcher callback leaves button disabled; original two-button assertions remain present and distinct. All subprocess launching is FAKE; no real child executable, WinCred write, provider request or real key is used.

Eight independently invoked original/new child suites preserve honest native exit codes, complete stdout/stderr hashes and genuinely reported unittest counts:
- New P158 successor: expected 9 PASS
- Original P133 manual launch: expected 25 PASS
- Original P132 user-scope fake WinCred/Tk: expected 36 PASS
- Original P84 typed pending view: expected 6 PASS
- Original P86 historical: expected 7 run, precisely two original FAIL/HOLD with native exit 1
- Original P87 historical: expected 18 run, precisely one original FAIL/HOLD with native exit 1
- Original P88 synthetic lease: expected 10 PASS
- Original Phase8.31 import-closure: expected original one FAIL/HOLD and one original tearDownModule ERROR, native exit 1

An unanticipated new failure, unexpected PASS of an original historical failure, changed failed-test identity/count, timeout, source checksum drift or source-policy mismatch causes **audit failure**. A green audit collector indicates truthful observation of positive **and negative** evidence. It NEVER counts a negative old test as an accepted PASS.

## Review request and explicit limitations

**Reviewer decision pending:** a qualified independent security and regression-governance reviewer must evaluate whether a branch-aware, versioned post-P133 three-button contract is equivalent in security to the original pre-P133 two-button contract, and what historical test graduation/migration process is acceptable. This engineering packet cannot self-appoint that reviewer or waive P86/P87 failures. P157 also identified 13-module imported view-to-service/persistence coupling for subsequent architecture governance.

The original Phase8.31 source import-closure and teardown are not fixed. P76/P85 original branch-specific refusals remain untouched. P132 current-user WinCred has a deliberately narrower threat model, including untrusted same-user processes, transient Python/Tk key residence and non-durable uncertain-effect recovery.

Production signed/pinned main, helper and installer are not approved; Smart App Control/WDAC owner GO remains false; privileged C1 G0–G6, including P96 and P124, remain open. No real credentials, production WinCred activity, network provider validation, HKLM/TPM mutation, unsigned Kristian executable, merge, release or Drive MASTER release update.

**Accepted full-product unfiltered Windows regressions = 0/3. Status: RELEASE HOLD.**


## Genuine Windows execution and source-bound evidence — 11 November 2026

The first real GitHub hosted Windows-2025 / Python 3.12 evidence collection run is https://github.com/krismcan/Mark-LV/actions/runs/43060868599 at tested exact source SHA 2e34ee05119cbda4922e8e44dbecd64ac2300637. Source verification passed for exact P157 parent, four additive P158 paths, and all 17 original security/test/product Git blob objects unchanged. Unchanged original P139 Win32 opened native handle policy accepted the owned disposable test TEMP root.

Real Windows job 130662755884 completed SUCCESS as a **negative-plus-positive evidence collector**. Artifact ID 13874121076 contains eight native child combined stdout/stderr logs and a JSON ledger. Archive SHA256 3819E30D49D8902810DF5151C9E2730AC8B1EA6627D2A97998AE1FAC390C6749; artifact expiry 25 November 2026.

| Genuine Windows child | Native exit | Actual tests | Original disposition | Combined raw log SHA-256 |
| --- | ---: | ---: | --- | --- |
| New P158 versioned post-P133 UI successor | 0 | 9 | 9 PASS | 01793A34EAC143BE1FE658084C104BDE806C47736CCC6330CEFD206D77AECD44 |
| Original P133 explicit manual launch | 0 | 25 | 25 PASS | A24FB3A24E8EAC5CF34AF17D8A1D96E309F67A99840481F57201F67B9640F0F4 |
| Original P132 fake WinCred/Tk | 0 | 36 | 36 PASS | F2028C68501DB3437051AE3B46683DA333DB072AE333B8860B67AE899B8BBEB0 |
| Original P84 bounded pending view | 0 | 6 | 6 PASS | 792C90AB6F23A7129780DE95A18731650EA569327C61016F3231E7F4B59738F9 |
| Original pre-P133 P86 | 1 | 7 | 5 PASS / exactly 2 original FAIL/HOLD | 956E936425FD63B9E1C8E82D8E9630AE948F52F42FCFDBA83DD8558FB82A6B6B |
| Original pre-P133 P87 | 1 | 18 | 17 PASS / exactly 1 original FAIL/HOLD | F8A4B6C7326D7F2C42C891E02043A0878CA6E667EB83F6B520B768704B9199F2 |
| Original P88 synthetic lease | 0 | 10 | 10 PASS | 38DB50CDA20C72B90A5A4D0C7307A496A2C4DF680E2A7D1CA8EB2E9BA70329BB |
| Original Phase8.31 static import closure | 1 | 1 | 1 original FAIL/HOLD + 1 teardown ERROR/HOLD | F248D042A57597EE8872F0E491273EFA9AE8998D472E7902AC8EE07055E83D17 |

Exact unchanged original failed method identities are:
- P86 test_live_connection_page_default_is_explicitly_unobserved
- P86 test_no_credential_action_and_no_implicit_refresh
- P87 test_production_default_remains_not_observed_without_any_session
- Phase8.31 test_static_production_import_closure_forbids_test_and_effect_routes
- Phase8.31 original tearDownModule error remains separately recorded.

**Totals: 112 actual unittest methods, 108 PASS, 4 unchanged original FAIL/HOLD and one extra original teardown ERROR/HOLD.** A green workflow is not a regression pass: all four historical negative results are required to remain red for this versioned evidence collector to succeed, and a change in their identity or counts makes the collector fail.

## Pending qualified reviewer decision; no release

Independent qualified reviewer must specifically answer:
1. Does the new P133 third manually launched button preserve the original P86/P87 non-authoritative custody, no-implicit-effect and creator-thread security expectations under its narrowed current-user threat model?
2. Is the versioned successor a legitimate, branch-aware new test while pre-P133 exact two-button assertions remain a frozen historical anchor? How will later release regressions report both instead of quietly excluding negatives?
3. Is the Phase8.31 import-closure migration permitted, and must the transitive P157 13-module view-to-service/persistence dependency be refactored into a pure type-only boundary?
4. What independent signed/pinned production main/helper/installer and SAC/WDAC Code Integrity owner evidence, Native WinCred synthetic separate-profile validation, and three accepted full-product Windows regressions remain required?

No qualified independent reviewer has approved the answers. No historical test was changed or suppressed; no security exception has been authorised. This PR remains draft/unmerged, and production release remains HOLD with original privileged G0–G6 separately OPEN.
