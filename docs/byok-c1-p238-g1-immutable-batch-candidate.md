# P238 G1 immutable Git batch candidate

15 November 2026. **INSTRUMENTED CANDIDATE; UNEXECUTED; all C1 gates HOLD.**
No release authorization, independent security decision, original regression
PASS, source-equivalence runtime proof or measured speedup is claimed.

Only checkout used for writes:
`D:\Nayeon\CODEX_P238_G1_BATCH_EQUIVALENCE_20261115`, branch
`byok-c1-p238-g1-immutable-batch-equivalence-20261115`, clean starting HEAD
`f66358de30fcb451e660e500df6a7843c6bbf0a6`. Four additive files only: this
document, the P238 script, its synthetic selftest, and its workflow. No staging,
commit, tag, push or merge; other worktrees were neither inspected nor changed.
The stale CURRENT_STATE header describes 3 November Phase 10.2, whereas Git
identifies P237. It stays unchanged: this task completes no product phase.
Local history is shallow, no HEAD milestone tag is present, and local
core.autocrlf is true. Local disk bytes are not original historical admission.

## Source and immutable boundary

Reviewed P162/P227, P234 controller/workflow, P235/P236 evidence and causal map,
P237 observer/workflow/docs, original G1/candidate fixture, B guard, Phase10
historical baseline, and the Phase8.30 check_output transport. Exact source is
P233 `096048db17c7c1f9402dfd16a7deb31e9ebdc81d`; original test module Git blob
`c482792ab2503d379f4ca32bbcf7906032a5a0dd`, raw SHA256
`65DAD89298A587D6BB5DDE5455DF4D701BB1A1FD9A7A96CECF3E647800E3AE8B`.
P234 controller remains blob `0c5781a28187bd5eddb5f7a3ff0d85c1a5430d6c`.

The sole immutable commit is B `e3612279cb972e68e2487702183d5bf5b8f6c4a1`,
tree `99624a766e864addf5d096bb1a907c85d11401dc`. The exact **23** paths,
fixed blob OIDs and original normalized SHA256 pins are literal `MANIFEST`
entries in [the candidate](../scripts/p238_g1_immutable_batch_candidate.py).
They are never learned from HEAD, worktree bytes or admission success.

The sealed B object is absent locally. Read-only GitHub connector GETs obtained
the [fixed B tree](https://api.github.com/repos/krismcan/Mark-LV/git/trees/99624a766e864addf5d096bb1a907c85d11401dc?recursive=1)
(471 entries, not truncated) and
[original B guard](https://github.com/krismcan/Mark-LV/blob/e3612279cb972e68e2487702183d5bf5b8f6c4a1/tests/phase8_byok_b_scope_migration.py).
PowerShell/.NET independently reconstructed the seven raw trees on all manifest
ancestor paths and matched each Git SHA1, including the fixed root. The guard
bytes hash to blob `78733fe16623be018161e272286cf06afe820484`; its exact original
self-pin normalization matches
`7aa013c3400b4032087ad6f769d5ce0cb727d628586bb4f4cc4fdbca5c6f246c`.
These are static object checks, not a fresh local full-history Git authentication
or validation of all 23 blob bodies. The hosted preflight must perform both.

Before interception, the child runs unchanged P234 `verify_source`: authentic
full-history P233, every raw tracked file, 15 historical tags and hook-free test
inventory. It then runs original Phase10 `_baseline()` with native Git,
authenticating B's annotated tag, raw commit/tree, ancestry, prior seals and
original pins. It requires all 23 tree entries to equal the fixed literal OIDs
and obtains 23 separate native `git show` byte witnesses. Every batch response
must independently match its SHA1 blob identity, original B `_digest` pin and
exact original-show bytes. Only B guard's original self-pin is canonicalized;
no new line-ending normalization is introduced. Byte witnesses are comparison
data; they are never returned as transport results or admission decisions.

The isolated child's check_output interception accepts only this exact shape:

```python
subprocess.check_output(["git", "show", B + ":" + literal_manifest_path],
                        cwd=authentic_root, stderr=subprocess.DEVNULL, timeout=20)
```

Other argument types, spellings, options, cwd values, timeouts, commands and
paths delegate with the exact original arguments; native bytes/exceptions/exit
codes propagate. HEAD, branch/tag resolution, complete trees, index, status,
ancestry, raw tag/commit authentication and old historical snapshots remain
native. Consent, effects, original assertion bodies/pins and P76 wrong-branch
refusal have no replacement. The patch is removed before post-verification.
Original fixture seams and its existing immutable-only cache are unchanged;
there is no new admission cache. The test body still performs all 23 targeted
tamper cases, requires the same rejection message, and checks each exact hit.

Each intercepted request writes one fixed OID and reads a new bounded batch
frame. A short pipe read is accumulated; truncation, oversized or malformed
frames, wrong OID/type/bytes/pin/delimiter, failed/late exchange or stale internal
ticket poisons the reader. No retry/fallback-to-witness follows corruption.
The serial caller does not prefetch responses. Identical valid immutable bytes
for the same OID are intentionally equal: no cryptographic age/nonce attestation
from Git or hostile-transport replay impossibility is claimed. Synthetic tests
check fresh exchanges, stale tickets, foreign objects and poisoning after a
positive read. This remains a trusted-Git transport experiment, not a new trust
authority or proof against an arbitrarily compromised Git executable.

## Execution, limits and evidence

The workflow uses only a push to the exact P238 branch, windows-2025, Python
3.12, full history/tags, core.autocrlf=false and no persisted checkout
credentials. P237's HOST_IDENTITY restriction is not monkeypatched or invoked;
P238 has its own exact host/branch/push guard. Default-branch dispatch is not
required. A single reviewed child of P237 must contain exactly four additions,
with clean controller source and unchanged original paths; later children or
extra changes are refused. Source guard and synthetic selftests precede the
single candidate. No original full suite, original G1 rerun, retries or later
methods are scheduled.

The child blocks on a one-byte stdin handshake before loading P234, source or
Git. A Win32 Job Object is assigned before that byte is sent, with kill-on-close,
32 active-process and 1 GiB aggregate job-memory limits; breakaway is not enabled.
The supervisor starts the **180-second whole-child** clock before spawn,
including handshake, original source verification, imports, provenance setup,
one original G1 body and post-verification. This adds setup cost inside that
budget; it never extends it. Each fresh batch wait is at most 20 seconds, blobs
at most 2,000,000 bytes, headers 128 bytes and requests at most 4,096. Other
original Git reads retain their original bounds; external provenance Git calls
have 45-second subprocess bounds. The workflow outer deadline is 12 minutes.

The private combined log has a sampled 4 MiB abort threshold every 0.1s, not an
OS disk quota; writes can overshoot between samples. Public reads reject files
above the cap. Teardown terminates owned descendants even after root exit and
queries Job Object active-process count for up to five seconds.
A root that exits while owned descendants remain is classified as an
instrumentation failure (exit 125), even if job cleanup subsequently empties
the tree. A successful cleanup never retroactively makes that run a PASS.
Root waits are bounded at five seconds. Query/termination/handle failures stay UNCERTAIN; a
root exit alone is insufficient. Win32 structure layout, nested jobs on the
hosted image, scheduling/timeout races and actual containment are **UNVERIFIED**
until synthetic native execution, including the tiny descendant test.

Unchanged P234 result/journal classification is reused within explicitly
candidate-labelled evidence. Candidate FAIL stays FAIL (exit 1); TIMEOUT stays
TIMEOUT, exit 124 only with confirmed empty job, otherwise 125. Instrumentation,
missing results, skip/expected failure, provenance or verification gaps return
125. A verified candidate-only PASS returns **3**, never product GO/exit 0.
The test outcome is saved before batch teardown so a teardown failure cannot
erase a recorded failure. The controller publishes source/manifest hashes,
per-path fresh-read counts, bounded process measurements and raw-log receipts.
Raw stdout/stderr, tracebacks, arbitrary argv and user/runner paths stay in
private disposable runner-temp files and are never uploaded. Uploaded artifacts
contain fixed-schema JSON only. Raw deep forensics requires separately reviewed
retention/redaction; hashes do not preserve retrievable raw logs after disposal.
No recursive cleanup/deletion traverses the original checkout or private data.

P237 hosted run **43704008072** remains the user-supplied unmodified comparator:
original G1 TIMEOUT/uncertain cleanup, observer exit 125; 4,154 Git sessions,
2,524 show, 560 cat-file, sum completed process t_abs about 105.883s, no completed
Git process above 0.085s. P238 does not reauthenticate those raw run artifacts or
rerun the original. Counts support repeated-process overhead as the candidate
motivation; sums exclude OS/Python startup and are not critical-path fractions.
No original baseline duration ratio or speedup is manufactured from a timeout.
Only B's 23-path shows are batched; older immutable work and all other native
Git work remain. A candidate can still time out or fail.

## Open Failures & Prior-Issues Review

| Issue / source | Severity, affected boundary, evidence and cause | Repair/containment, review, disposition |
| --- | --- | --- |
| P237 G1 / P234 G1-G3-G6 | Material original regression/containment blockers; original 180s timeouts and uncertain cleanups. P237 supports process amplification; exact deadline operation and surviving-tree history remain unproved. | This additive experiment changes one transport scope only; historical failures remain. Job containment is an unvalidated candidate. Independent review pending; HOLD. |
| Four P76 branch failures | Material historical regression; P236 traces original successor routes to genuine exact-branch refusal. | All branch/ref queries and assertions untouched, no automatic waiver; HOLD. |
| Other three original timeouts | Material regression blockers, individual causes unresolved. | Not executed, fixed or inferred from this G1 experiment; HOLD. |
| Original P96 revoke/effect race | High security blocker across old coordinator and alternate native actors; P236/P219/P221 document terminal-check/effect gaps. | No coordinator, custody, consent, service or policy change; HOLD. |
| SEC03/SEC04 / unsigned broker-service | High architecture blockers; qualified independent decisions missing. | No self-signoff, credentials, install, signing or live authority; HOLD. |
| P162/P227 transport assumptions | Prior prototypes cover a different 19-path commit; blocking pipe reads and weak taskkill evidence do not prove this boundary. | New exact B manifest, bounded response queue and job containment; authored adversaries only, no inherited runtime/independent GO; HOLD. |
| P231/P232 lifetime / P233 repair | Historical retained test-owner defect; P233 recovery preserved, these modules are hook-free. No proven causal link to G1 timeout. | Only one stdlib suite owns the original case; no wrapper test or retained extra owners; no new closure claim. |
| Local validation | Missing runtime evidence; host Python inaccessible, no Python/py on PATH, shallow Git and CRLF disk. | No install/copy/network runtime workaround; host synthetic validation required; HOLD. |

Authorized disposition: bounded source preparation for review only. No failure
waiver or product progression; full unfiltered regressions remain **0/3**.

## Validation and next safe step

Executed: exact branch/parent/initial clean checks; local immutable source OID
inspection; seven Git-tree SHA1 reconstructions and original B guard SHA1/self-pin
checks described above; unchanged tracked diff and empty index; whitespace checks;
four workflow PowerShell blocks parse with zero errors. These are static checks,
not Python syntax, YAML/GitHub validation or a source/security signoff.

The authoritative host Python invocation was unavailable in this sandbox. The
**32 authored synthetic test methods have NOT RUN**. Python compile/compileall,
candidate G1, native Job containment, hosted workflow and independent validation
have NOT RUN. No expensive original or candidate G1 was run on Kristian.

Nayeon's next safe step is source review plus host-only synthetic execution:

```powershell
& 'C:\Users\krist\AppData\Local\Python\pythoncore-3.12-64\python.exe' -B scripts/p238_g1_batch_selftest.py
```

Compile just the two additive Python files on the host without writing pyc;
retain native exits and raw hashes. Do not launch `observe` or the original G1
on Kristian. After synthetic evidence and source/containment review, Nayeon may
publish exactly one reviewed four-addition child under their authority. Its
branch push can execute one hosted candidate. Inspect real exit, timeout/cleanup,
unchanged-source witness, all 23 fresh-read counts and receipts together. Any
candidate PASS is only an unchanged original body with **instrumented original
Git transport**; independent architecture review is required before considering
any production-path change. SEC03/SEC04 and every C1 release hold remain open.

## Nayeon host review and independently executed focused validation

After Codex completed the four-file additive draft, Nayeon reviewed the Windows
Job Object outcome boundary. One narrow safety correction in the same P238
candidate makes a cleanly exited parent with still-active owned descendants
**INSTRUMENTATION_ERROR / exit 125**, even when the job subsequently terminates
the children successfully. The added adversarial test reproduces that condition
and prevents a false-positive candidate PASS. This does not alter the 180-second
deadline or any historical source/test/security file.

On Kristian, Python 3.12 executed the final **33/33** P238 synthetic adversaries:
native process exit **0**, **zero failures/errors/skips**. Source: exact uncommitted
P237 parent `f66358de30fcb451e660e500df6a7843c6bbf0a6` in isolated P238
worktree; no original G1 or credential effect invoked. Host log:
`D:\Nayeon\P238_HOST_EVIDENCE_20261115\p238_host_synthetic.log`,
SHA256 `71A7AA4B9F60F608B76000932B3EDF85B97F25EC8C01D68D8C63D593A66E5790`.
Structured host receipt `p238_host_synthetic.json` SHA256
`1E43F820AFB45FCEE6C0B52F2717716B1B1575B6EF506AC5E04C283C3524D2EB`.
Both additive Python files passed host Python AST parse (exit 0); AST log SHA256
`F1DD83ABE3576DE388B998C5F3ED3613ABE66D7377313EB07DA20426433B3DA5`.
The earlier Codex-only no-interpreter and 32-authored-not-run statements remain
historical descriptions of its sandbox, superseded by these independent real-host
focused validations.

**Still unverified:** candidate actual original G1 body execution on a hosted
Windows full-history P233 checkout, batch byte-parity at runtime, G1 duration,
original four P76 failures, other three historical timeouts, real service P96
race, qualified SEC03/SEC04 decisions, and mandatory complete regressions 0/3.
No candidate PASS, product readiness or release eligibility inferred.
