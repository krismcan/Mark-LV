# Phase 10.2 — Trusted Perception & Privacy Controls (offline synthetic design)

Date: 2026-11-02
State: DESIGN V3 GO; SYNTHETIC PERMISSION SOURCE GO; 13-PATH SOURCE/RELEASE HOLD pending topology-aware rereview and three full regressions. NOT RELEASED.
Parent release: Phase 10.1 commit be6c126dc5f3a6814925bb95009ef2b2e6be80b7.
Branch: phase10-2-trusted-perception-20261102.
Scope source: original same-ID master workbook, Build Plan row 15 (Phase 10 / Vision / Perception; dependencies 3,4,6).

## Goal and precise non-goal

Establish an independently reviewable offline model for scoped visual-observation grants,
revocation, anti-replay and privacy/provenance handling. This is NOT a working permission
broker, screen/camera adapter, redactor, operating-system authorization, UI consent,
provider interface or end-user vision workflow. No production observation is enabled.
The Phase 10.1 request/candidate contracts remain explicitly non-authoritative.
Major Phase 10 and consumer release gates remain open.

## Boundaries and data flow

1. UNTRUSTED request origin declares session, purpose and source, optional target intent.
   This declaration never grants permission.
2. FUTURE user-facing UI presents the exact source and purpose, target, time bounds,
   revocation and risks. UI booleans are claims, not authoritative consent.
3. FUTURE trusted host policy/confirmation broker authenticates the user interaction,
   checks policy, binds a verified session and target, and owns issuance and revocation.
   A caller's time, user ID, app/window ID, policy result, or confirmation bit is not proof.
4. Phase 10.2 models only a **SyntheticGrantLedger**: an in-memory, no-effects state
   machine driven by fake broker evidence and synthetic targets. No method can capture
   pixels, access the camera, grant platform permissions or authorize other services.
   Its results must never be treated as production capture credentials.
5. FUTURE capture adapter must reverify the OS object/window/app identity and session
   before and after acquisition, honor cancellation/revocation, and attest trusted
   provenance. A PID alone, title string or caller-provided target is insufficient.
6. FUTURE trusted redactor applies and verifies masking before any exposure to an
   interpreter/provider/storage subsystem. A producer's `REDACTED` metadata and/or
   image hash prove neither trusted origin nor actual redaction.
7. FUTURE evidence assessment consumes an independently attested provenance envelope,
   then may use Phase 10.1's `assess_observation` only as a *candidate* predicate.
   A candidate is not user consent, trusted redaction or verified task outcome.
8. FUTURE audit records only bounded event *codes*, monotonic sequence and non-secret
   coarse timestamps; no screenshots, OCR, prompts, window titles, secrets, hashes
   of private content, raw capability tokens or automatic object repr.

## Offline synthetic lifecycle — exact state model

Only the future trusted OS broker can establish authenticated user/session/target
incarnations. In the synthetic model, a **test-owned broker fixture**, separate
from untrusted request input, owns monotonically increasing session generation
and target generation, and exposes current/not-current state to the ledger.
A caller echoing the originally bound IDs is insufficient. The ledger stores
immutable (request, session ID, broker session generation, source enum, purpose
enum, target ID, broker target generation) bindings and compares both original
binding and *current broker fixture state* on every grant transition.
Session closure, target replacement and ledger closure atomically invalidate
all matching ISSUED/ACTIVE records. Do not treat a PID or window title as a
target incarnation. A future real broker must authenticate these facts.

Every new synthetic grant requires an explicit **fake-only approval event**
from that fixture; the original request is never proof. Approval is an
unforgeable *within this synthetic fixture only*, opaque, immutable handle
bound at creation to the **exact request ID, session ID and fixture-owned session
generation, source enum, purpose enum, target ID and target generation, and an
approved TTL ceiling**. The ledger must reject a mismatch at issuance,
including future TTL enlargement, after consulting current fixture generations.
An approval is atomically consumed in the ledger regardless of successful or
failed issuance attempt; two simultaneous issue calls cannot both succeed.
The fixture may generate an approval only following a distinct fake policy
decision and fake user confirmation event, but both remain test assertions,
not authentication and not OS authority. The original request cannot mint
approval, and a caller-supplied confirmed/policy bool is not accepted.
A request ID (without a session-key escape hatch) is **reserved exactly once
for the entire ledger lifetime** after a fixture-issued, exact-bound approval
has been consumed and its original session/target generations confirmed, but
**before checking the requested TTL or invoking the injectable clock**.
Thus even an over-ceiling TTL or clock fault on a valid approval burns that
request ID; retries require a fresh request ID and fake approval event.
Missing/forged/wrong-scope events may not reserve arbitrary request IDs.
Nested/reentrant fixture clock callbacks may not double-issue a reserved
request, revive a closed model or swap targets mid-issue: after the callback,
repeat the registry-open and current-generation checks under the same lock.
No wildcards, renewals, open-ended TTLs or serializable/portable authority.

Internal grant/lease handles are registry-owned, random opaque and never placed
in logs or dataclass repr; handles from another registry or a restarted instance
always fail. A lock makes every transition linearizable; no method returns raw
pixels or permits a real capture. A successful prior validation creates **no**
continuing permission. The ACTIVE lease must be re-evaluated and committed
under the same lock used for revocation, cancellation and target/session change.

| State / event | Guard | Result |
| --- | --- | --- |
| No grant -> ISSUED via synthetic issue | Fresh fake approval event; current trusted-fixture session/target; valid TTL; request never issued | Create one ephemeral record |
| ISSUED -> ACTIVE on begin | Exact binding, current session/target generations, valid unexpired clock, never begun | Single active lease |
| ISSUED/ACTIVE -> REVOKED on revoke | Same ledger and exact record | All later actions refused |
| ISSUED/ACTIVE -> CANCELLED on cancel/session close/target replace | Current record | Invalidated immediately; never restored |
| ISSUED/ACTIVE -> EXPIRED on time >= expiry | Broker-owned trusted monotonic clock | Invalidated; expiry equality rejects |
| ACTIVE -> USED on complete | **Repeat all grant, lease, binding, current-generation, time and revocation checks atomically** | One successful fake result-release marker, no content |
| ACTIVE -> CANCELLED on simulated operation error / timeout / interrupted work | Abort/finally or lease invalidation before another operation | No synthetic result; no authority recovery |
| Any terminal state -> any action | Always reject | No replay, renewal or resumption |
| Any state -> CLOSED on shutdown/clock failure/rollback | Registry fail-closed transition | Invalidate all outstanding records; refuse further issue |

The synthetic result-release marker is committed under the **same ledger lock**
as final authority checks. If revoke linearizes before `complete`, completion
refuses; if `complete` linearizes first, only that already-authorized fake
marker succeeds and subsequent revocation prevents further access. There are
no actual content bytes to publish. Later real capture must serialize its final
trusted release gate with revocation and discard unpublished frames on a losing
race. Any genuine publication already completed before revocation is not
retroactively undone; the consent UI must explain that limitation.

Time unit is integer **monotonic milliseconds**, strict type (no bool), range
0 .. 2^53-1, MAX_TTL_MS=30_000; valid TTL range 1 .. 30_000 ms. At issuance,
expiry=now+TTL must be in range. A record is valid iff now < expiry (equality
is expired). The ledger owns a monotonic high-water mark. A lower observed
time, clock exception/non-integer, overflow or unavailable broker clock closes
the entire ledger permanently and invalidates all authority. Synthetic tests
may inject a deterministic clock only into a visibly test-only fixture; caller
timestamps, generated Phase 10.1 candidate times and wall-clock input do not
determine grant validity.

In-process interrupted ACTIVE work is terminal on explicit error/timeout; if
an abnormal interruption leaves an orphan ACTIVE record, the ledger must fail
closed on expiry or shutdown, with no second begin and no reusable active
lease after expiration. A fresh process does not restore grants from bytes.
No auto-retry or persistence, no recovery loader and no serialization format.

## Threat model / expected mitigations

| Attack/failure | Required reaction |
| --- | --- |
| Forged consent/policy/user claim | No real authority; fake-only model explicitly labelled |
| Stolen/replayed grant/lease | One-use transition, random opaque identity and checked registry ownership |
| Session/request/source/purpose confusion | Exact equality and strict types; no wildcard |
| Window/app/source target swap or PID reuse | Broker-owned target incarnation; fake epoch substitution denied |
| Forged timestamp or monotonic rollback | Broker-owned monotonic clock, rollback invalidation |
| Concurrent begin vs revoke | Atomic transitions; final state non-reusable |
| Cancellation during active work | Lease invalidated, future adapter cleanup mandatory |
| Crash/power loss | No authority replay: ephemeral state discarded on restart |
| `REDACTED` claim or producer digest | Never evidence of verified masking; trusted redactor attestation later |
| Log/repr/diagnostic information leakage | No tokens, IDs that contain content, user content or frame bytes |
| Python runtime tampering or untrusted in-process caller | Explicit non-goal: Python object privacy is not an OS trust boundary |
| Unapproved OS capture/service activation | No adapter, device, network, storage, microphone or provider hooks |

## Synthetic test requirements

- Forged/missing grant and lease, wrong owner registry, malformed identity.
- Wrong request/session/source/purpose/target and target epoch substitution.
- Expired TTL, out-of-range TTL, clock rollback and stale/future state.
- Duplicate begin, duplicate complete, replay after revoke/cancel/expire.
- Concurrent begin/begin; begin/revoke; complete/revoke.
- State history after simulated error/restart: no persisted authority.
- No path for observation request alone to issue or redeem grant.
- No real capture/camera/microphone, OS permission, provider, credential, network or
  image content in production source or tests.
- No accidental token leak through repr, exception text, diagnostics or persistence.
- Existing historical source-seal admission must remain fail-closed; introduce
  a Phase 10.2 *successor* gate after independent review, with exact branch,
  parent commit/tree, diff envelope, static source pins and three live topologies.
- Explicit negative races: revoke between prior validate and final completion,
  complete after target replacement, same original IDs with old generations,
  an orphan ACTIVE operation, fresh registry with old grant/lease handle,
  overlapping issue attempts for the same request, and simultaneous close.
- Clean current-source admission must PASS before causal tamper injections;
  each negative must prove its own intended rejection path, not a prior
  unrelated branch/path failure.
- Fake approval event wrong request/source/purpose/session/target/generation,
  greater-than-approved TTL, event double-spend and concurrent issuance,
  malformed fake confirmation and policy denial.

## Successor exact-source admission design and provisional scope

Protected Phase 10.1 seal: commit
`be6c126dc5f3a6814925bb95009ef2b2e6be80b7`,
tree `e6898712f51a070509929e4f40afe92f06a70b62`,
annotated tag `nayeon-v1-phase-10-1-offline-perception-foundation-01`,
tag object `c96dcea845bbab00a142d69341378d0f07f4b47f`.
Only a single immediate child of this parent may be a release candidate.
The source gate must authenticate raw parent tag, commit, tree and complete
blob inventory, exact index, untracked and ignored paths, raw disk bytes,
canonical path identity, no links/hardlinks, staged/unstaged/child deltas,
and the exact parent/branch. No force/rewritten historical refs.

A new `tests/phase10_2_privacy_scope_migration.py` shall own current live
admission. The existing 10.1 gate becomes a *historical private witness*,
using authenticated raw 10.1 blobs; append-only working-tree route forwards
older public admission, including the BYOK B and Phase 10.1 public wrappers,
to the 10.2 live gate without fallback or recursion. Historical fixture tests
must use sealed snapshots and the private old parsers, not current branch
assumptions. Re-pin exact fixed digests only after source review of the fully
finished candidate. Before that, current admission is expected to FAIL and
expensive full regressions are prohibited.

**Provisional explicit path envelope for scope review (not yet source GO):**
Added: `docs/phase10_2_trusted_perception_privacy_rfc.md`,
`nayeon/perception/permissions.py`,
`tests/test_phase10_2_permission_ledger.py`,
`tests/phase10_2_privacy_scope_migration.py`,
`tests/test_phase10_2_privacy_scope_integrity.py`.
Modified (14 explicit paths; SCOPE AMENDMENT PROPOSED, REVIEW REQUIRED):
`.codex/CURRENT_STATE.md`,
`tests/phase10_perception_scope_migration.py`,
`tests/test_phase10_perception_scope_integrity.py`,
`tests/phase8_byok_b_scope_migration.py`,
`tests/test_phase8_byok_b_scope_integrity.py`,
`tests/phase_8_30_scope_migration.py`,
`tests/test_phase8_byok_scope_integrity.py`,
`tests/test_phase_830_scope_integrity.py`,
`tests/test_phase_831_scope_integrity.py`,
`tests/test_phase_832_scope_integrity.py`,
`tests/test_phase_833_scope_integrity.py`,
`tests/test_phase_834_scope_integrity.py`,
`tests/test_phase_836_scope_integrity.py`,
`tests/test_phase_837_scope_integrity.py`.
This is exactly 5 ADDED + 14 MODIFIED, **not source approval**.
The eight newly proposed historical test paths were identified in the
independent prototype source review as potentially dependent on old
branch/parent identity or live-reader mocks. They are bounded only to:
authentic historical fixture preimages, exact current-source admission,
canonical negative tamper reach and causal current-parent assertions.
Each must be proven necessary from focused native failures before editing;
unneeded entries should be removed by an independently reviewed scope
reduction. Do not weaken frozen pins, accept synthetic positives as live
proof, skip tests, or add generic mocking. Original `contracts.py` and
`__init__.py` remain FROZEN and excluded. No prior 26-path patch is copied.
Any other necessary path requires a **fresh explicit review amendment**.
Never mutate the sealed 10.1 checkout or Phase 9 worktree.

## Open Failures & Prior-Issues Review — issue-level closure ledger

Authority: `docs/engineering_failure_review_gate.md` §§ Pre-phase retrospective
and Evidence/sign-off. Date/source, severity, affected callers, symptom,
reproduction, root cause, repair, evidence and reviewer disposition are recorded
below. Historical evidence is identified, not newly rerun here.

**P10-LEGACY-BRANCH / 2026-11-01 / MEDIUM / CLOSED for Phase 10.1.**
Affected: public BYOK B, 8.30–8.37 historical source admission, direct legacy
test callers and production projection. Symptom/repro: the original B public
gate rejected a new branch with `Wrong BYOK B product branch`; old tests assumed
the original branch/parent. Cause: valid newer exact-source child had different
topology, not a permission weakness. Repair: private authenticated B historical
witness, new strict Phase 10.1 branch gate; exact old fixtures from sealed B
blobs; seven obsolete historical test assertions explicitly repaired, never
disabled. Evidence: `tests/phase10_perception_scope_migration.py`,
`tests/test_phase10_perception_scope_integrity.py`, independent final
`C:\Users\krist\AppData\Local\Temp\nayeon_p10_exact32_final_source_review.md`
(SOURCE GO) and native full regression records 3 × 3,108 PASS (reported
exit 0). Disposition: independent SOURCE GO and later release assurance GO;
Phase 10.2 must introduce a new successor route, not reuse the old live branch.

**P10-30FILE-SOURCE-HOLD / 2026-11-01 / MEDIUM / CLOSED for sealed 10.1.**
Affected: 30-file source review and seven frozen history assertions. Symptom:
independent SOURCE HOLD for test expectations no longer reflecting the current
branch. Repro: the seven exact historical reader/injection tests failed under
the honest new route. Cause: source-identity test-migration gap. Repair: two
additional review-bounded historical test modifications -> exact 32-path
candidate (6 adds, 26 mods); static repin and causal negative expectations.
Evidence: same exact32 SOURCE GO above, plus final release readback
`C:\Users\krist\AppData\Local\Temp\nayeon_p10_final_postcommit_release_review_20261102.md`
(original HOLD on evidence, not source) and supplemental GO below.
Outcome: no unresolved source HIGH/MEDIUM in final 32-path review; 10.1
sealed at `be6c126dc5f3a6814925bb95009ef2b2e6be80b7`.

**P10-VERIFIER-HASH-CONTINUITY / 2026-11-02 / MEDIUM evidence / CLOSED.**
Affected: independent verifier self-pin audit and final source assurance.
Symptom: earlier reviewed raw/self hashes differed from final 10.1 hashes.
Repro: compare SOURCE GO against final review report. Cause: reviewed
subsequent two-path historical-test repair and repin, not silent drift;
the independent supplement confirms reconstructed old/new verifier hashes.
Repair: reconcile normalized/raw verifier continuity and same 30 other pins.
Evidence: `C:\Users\krist\AppData\Local\Temp\nayeon_p10_final_postcommit_release_review_20261102.md`
(HOLD explicitly identifying gap), then
`C:\Users\krist\AppData\Local\Temp\nayeon_p10_final_release_gap_closure_20261102.md`
(`SUPPLEMENTAL_RELEASE_ASSURANCE=GO`). Disposition: supplemental
independent GO within bounded scope. No new 10.2 verifier assertion is implied.

**P10-PHASE9-PRESERVATION-EVIDENCE / 2026-11-02 / MEDIUM evidence / CLOSED for 10.1.**
Affected: release worktree separation, Phase 9 memory candidate preservation.
Symptom: source reviewer could not directly inspect Phase 9 due to Git ownership
restriction; preservation not proved from initial review. Cause: host ownership
barrier, not observed Phase 10 source damage. Repair: authoritative read-only
host snapshot (SHA-256 `DB1115F1…A36AAFD` as recorded by reviewer), confirming
B HEAD, branch, 20 modified/7 untracked files, no ignored paths; reviewed
worktree registry; this session independently inspected same branch/HEAD and
visible status without trust-setting change. Evidence: exact supplemental GO
report above. Disposition: independent GO for bounded release topology; **not**
a claim of historical byte-for-byte Phase 9 preservation. Phase 9 is separately
HOLD and remains out of this worktree; its source must not be migrated.

**P8-TK-ASYNCDELETE / 2026-10-17 / MEDIUM historical / CLOSED for prior
bounded Tk suites, NOT APPLICABLE to fake-only 10.2.**
Affected: prior UI test-created Tk roots and worker-thread GC. Symptom/repro:
native test worker GC caused intermittent Tcl interpreter deallocation (19/54
roots initially still live; 0x80000003 observed). Root cause: root lifetime
outlived owner-thread cleanup. Repair: explicit main-thread lifetime/GC
teardown and survivor assertions, earlier 10/10, 18/18 and combined 54/54
bounded tests plus prior 2,565-test suite as recorded in the unchanged
historical `.codex/CURRENT_STATE.md`. No new Tk, thread, camera handle or
OS resource introduced here. Disposition: historical bounded closure, **not**
an assurance for untested future threads or capture adapters.

**P10-RELEASE-EVIDENCE-GATE / 2026-11-02 / MEDIUM / CLOSED for 10.1.**
Affected: compileall proof, final release reviewer, remote publication and
same-ID records. Symptom: initial precommit/release reviews reported HOLD for
missing compileall record and the two gaps above. Cause: incomplete evidence
collation, not an asserted functional test failure. Repair: existing native
compileall evidence reconciled, supplemental release assurance GO, authorized
Git push and annotated tag; source tree/commit/tag verified locally AND
again remotely in this session; same-ID 16-sheet macro workbook SHA-256
`5f4c3aefc40e909c70609d4173373c3d03f4d9e9673284d96aef3b22e7808502`.
Evidence: `C:\Users\krist\AppData\Local\Temp\nayeon_p10_exact32_precommit_seal_review.md`
(HOLD before evidence completed),
`C:\Users\krist\AppData\Local\Temp\nayeon_p10_final_release_gap_closure_20261102.md`
(GO), and remote refs:
branch `phase10-perception-foundation-20261101` -> `be6c126d...`,
annotated tag object `c96dcea845bbab00a142d69341378d0f07f4b47f`
peels to same commit. Full stderr hashes in prior final report:
FULL1 `7597EC4AD369FAFCA7C866F72EA5FD8987AA54C0EACEF1E1FD300364E554C895`,
FULL2 `E98A9388262912B0E2A9B1465B9EAB1FD61E1EB83638558980B5306EE79A39E4`,
FULL3 `A03880998665A219FDD079AA01069B3A33390AC306EDDAC3D9D5B65998245DE8`.
Those hashes and native exit claims are historical evidence from reviewer/host
reports, **not** recomputed native executions in this session.
Disposition: published 10.1 verified; no production capture acceptance implied.

**P10.2-DESIGN-V1/V2 / 2026-11-02 / HIGH+MEDIUM design / HOLD pending
independent revision-3 review.**
Affected: proposed fake-only grant lifecycle and future trusted capture boundary.
V1 independent HOLD found atomic complete/revoke, generation/target, clock,
successor-route and closure gaps. V2 independently marks the first three
RESOLVED in design and successor routing CONDITIONALLY DEFERRED; remaining
MEDIUM gaps: issue-level evidence closure and exact approval-event scope.
This revision addresses them with the ledger and authorization event contract.
Evidence: `D:\Nayeon\phase10_2_independent_design_review.md` (V1 HOLD) and
`D:\Nayeon\phase10_2_independent_design_review_v2.md` (V2 HOLD).
Disposition: **HOLD until an independent reviewer returns explicit design GO.**

**P10.2-SYNTHETIC-SOURCE-HOLD / 2026-11-02 / MEDIUM+LOW /
REPAIR CANDIDATE, RE-REVIEW REQUIRED.**
Source: `D:\Nayeon\phase10_2_synthetic_source_review.md`.
Defect 1: issuance used (session ID, request ID) replay key instead of
ledger-wide request ID; distinct sessions could reuse the same request.
Defect 2: fake clock callback invoked under an RLock after the duplicate check
could issue a second valid grant or close the ledger before the outer request
was committed. Defects reproduced through newly added adversarial tests.
Repair candidate: exact-scope fake event required before request-wide
reservation, reservation before TTL and clock, fail-closed post-clock
open/target-generation checks, finite 256-record lifetime caps with replay
tombstones, and expanded negative tests for callback reentrancy, session
reuse, duplicate approvals, close/complete, begin/revoke, orphan expiry,
restart handles, clock overflow/fault and causal AST effects. Native combined
57/57 PASS, exit0 and log evidence
`D:\Nayeon\phase10_2_focused_affected_20261102.log`, SHA-256
`AE33662A95F259B2B8A9B544330168D52DFD5731FDDAE07842C8180B91FDB539`.
No independent repair GO yet; **SOURCE HOLD remains**. Its recommendation
of eight additional bounded historical-test paths is a proposed exact-scope
amendment, not permission to alter those files without review.

**Pre-phase gate decision:** historical material Phase 10.1 issues above are
CLOSED within their documented bounds (not re-certified by fresh tests here).
Separate Phase 9, BYOK C1 and PRC work remains independently HOLD.
At this earlier design checkpoint Phase 10.2 design remained HOLD; revision 3
subsequently received independent synthetic-only design GO. The current
source/release gate remains HOLD, as detailed in the evidence update below.
Dependency path for later implementation: fake fixture -> approval event ->
synthetic ledger -> fake lease -> fake result marker; separately trusted
future UI -> policy/confirmation broker -> OS adapter -> trusted redactor ->
provenance -> Phase10.1 candidate assessment -> task verifier. No bypass across
process/restart is asserted by the Python fake.

## Phase 10.2 current independent and native evidence (2 November 2026)

- Design revision 3 independently **DESIGN GO** for synthetic-only boundaries:
  `D:\Nayeon\phase10_2_independent_design_review_v3.md`.
- Final terminal-state replay and reentrant-clock repair independently
  **SOURCE_PROTOTYPE GO** (two synthetic files only):
  `D:\Nayeon\phase10_2_final_prototype_review.md`.
- Source changes are **exactly 5 additions + 8 modifications** in the
  independently approved narrower subset of the provisional 5+14 envelope.
  The Phase 10.1 parent tag/tree/451 frozen inventory and Phase 9 checkout
  remain protected. Native COMPLETE_UNSTAGED live source admission PASS,
  1/1 exit 0, plus 29/29 legacy/source tests, 7/7 repaired integrity
  cases, and 3/3 cross-phase route tests (all native exit 0).
- The old presentation delta tests first reproduced 2/2 genuine failures
  (log `D:\Nayeon\phase10_2_presentation_delta_pre_repair.log`,
  SHA-256 `BC6936CBEE595068261FD5DA2F8EB985E78941DCF8B3BE1161402D7C2A435AA9`).
  A stricter COMPLETE_UNSTAGED-only full Git-view adapter then achieved
  **4/4 native PASS, exit 0** including both previously red presentation
  contracts; log `D:\Nayeon\phase10_2_delta_r1_native.log`,
  SHA-256 `A1C5E818E505D0AFDD29317AE96745C2DEAC7805666DA7E12DC137C3FE5AA23D`.
- Independent 13-path review `D:\Nayeon\phase10_2_delta_r1_review.md`
  returned **DELTA_ADAPTER=GO**, but **EXACT_SOURCE_SECURITY=HOLD** and
  **HISTORICAL_COMPATIBILITY=HOLD** solely because two new tests assumed
  unstaged topology. Those tests have since been made topology-aware;
  their new bytes, pins and fresh independent rereview remain mandatory.
- No actual perception capture, user consent broker, Windows permission,
  redaction attestation, credential, provider or network capability exists.
  The fake model cannot authorize production actions.
- Three full native Windows regressions (unstaged, exactly staged, immediate
  committed child), independent release assurance, non-force remote publication,
  same-ID macro workbook reconciliation and dashboard verification remain
  **OPEN**. This increment is **NOT RELEASED**; no gate may be inferred GO.

## Historical Phase 8.30 full-regression compatibility repair (3 November 2026)

Full native unstaged regression 1 on the prior 13-path candidate: 3165
tests in 16927.532 seconds, native exit 1, two failures in
`tests/test_phase_830_scope_integrity.py`; all other cases passed.
Preserved log `D:\Nayeon\phase10_2_full1_unstaged.stderr.log`
SHA-256 `8C91232E33DC5A9C05FEFD83236DDECA46A08C726FBA22D1BA91DEDB45BF26A3`.
Neither failure established a production permission defect. Both historical
negative tests witnessed genuine refusal of forged Git input, but their
expected messages were tied to the pre-Phase10.2 routing.

Independent scoped review `D:\Nayeon\phase10_2_full1_legacy_failures_scope_review.md`
returned PROPOSED_SCOPE_AMENDMENT=GO and HISTORICAL_TEST_REPAIR_DESIGN=GO,
without granting final source/release GO. Authorised source is now EXACTLY
5 added + 9 modified, adding only this previously frozen historical test
to the thirteen-path envelope. The staged entrypoint tamper test requires
the exact Phase10.2 rejection per current admitted Git topology and verifies
that the injected protected entrypoint is not newly authorised. The committed
application tamper test verifies the *second* Git tree query is the historical
8.29 ancestor, that this ancestor originally lacked the injected
application module, and that the single injected reply is rejected with
the exact historical ancestor-change error. Both tests retain their causal
reader-reach assertion and current admission before and after the injection.

This fourteen-path repair remains RELEASE HOLD until new source hashes,
native focused red-to-green tests, independent source rereview and three
complete Windows regressions (unstaged, exactly staged, committed child).
No modification to historical guard bodies, sealed Phase10.1 source,
permission implementation, production capture, OS access, credentials,
or provider interfaces is authorised by this amendment.

## Mandatory independent design review questions

1. Does the proposed API accidentally make a forged boolean or public token sufficient
   to receive a grant or pass a real capture boundary?
2. Can a grant or lease be reused after revoke, expiry, target change or process restart?
3. Is any identity or clock supplied by untrusted callers silently treated as truth?
4. Are logs, exception messages, persisted data and dataclass repr content-safe?
5. Does a fake-only permission state improperly claim verified consent/redaction?
6. Does the proposed source-seal migration preserve Phase 10.1 and older tags exactly?

## Release dependencies / stop lines

Only proceed to code implementation once an *independent* reviewer issues design GO
and blockers are resolved. Focused and adversarial native tests precede full regressions.
The final exact candidate needs independent source/security review, three full native
Windows regressions (unstaged, exact staged, immediate child), verified source seals,
a non-force GitHub branch/tag publication, and same-ID workbook/dashboard readback.
Do not run costly full regressions on a known-failing historical admission gate.
No capture, OS permission prompts, real credentials or network provider calls.
