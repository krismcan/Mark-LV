# P269 bounded development service composition (OM v2.1)

Base: `a7519059710fe5720dc55334e83d273ee8627e61` (P268), branch
`byok-c1-p269-service-owned-p96-composition-20261118`. Exactly five additions;
no historical implementation or workflow changes. Single writer: Codex.
Independent testing and Git/PR operations remain with Nayeon.

The new SCM-shaped `ServiceBase` owner constructs the actual P267 local P265
Windows denial-only named-pipe worker and the repaired P268 coordinator backed
only by frozen P96 approval/state/guard fixtures. Its test-only preparation and
submission methods accept no caller data payload: saves/replaces use only the
disposable literal `31 32 33 34`; delete supplies null. No production factory,
SCM dispatcher, installation, credentials, or trusted issuer is connected.
All five debug/development symbols are mandatory; private Main returns 64.

## Failure and architecture gate

| Prior issue / boundary | Evidence / disposition |
| --- | --- |
| Material P96 post-check revocation race | User-supplied P268 run 44211248673: x64/x86 33 cases, 341 assertions each; original negative 15/15 reproduced. P96 remains frozen; new host invokes only repaired P268. No claim that historical P96 was repaired. |
| Separate transport and coordinator locks | Preserved. Atomic host admission closure precedes P268 Revoke/Stop/Fault outside every host lock; finally terminates/joins P267. No common owner lock or cross-subsystem transaction is claimed. |
| Effect/control ordering | If control returns first, subsequent submit is denied. Once P268 effect entry wins, control reports TooLate, with sticky pending MAY_HAVE_EFFECT and recovery; never successful cancellation. |
| Worker failure / cleanup | Admission checks observe failed/exited transport and close both owners. Worker failure can occur after an admission observation: transport denial and local fake effect have independent ordering. No wire approval/effect route exists. Cleanup exceptions propagate; no retry, success masking or automatic re-enrollment. |
| Restart / recovery | fresh=false refuses startup and preparation. Stop is terminal. No durable recovery, real pending store or service identity exists. Production HOLD. |
| Independent closure evidence | Local compile only completed; Python and hosted runtime pending. GO only for bounded review/testing, HOLD for seal/production until independent x64/x86 evidence is reviewed. |

P267 transport uncertainty and P268 pending uncertainty are separate observation
fields. A pending read admission exception yields conservative pending uncertainty
and closes host admission; it is not evidence of an effect or successful cleanup.
There is no callback from P268 into the host. Test fixture hooks inject only
bounded test synchronization/failures. Existing P267 and P268 implementation
locks, one-use bindings, ledger checks and cleanup remain authoritative.

## Tests and evidence

The hosted runner specifies 23 cases: 18 deterministic combinations of
save/replace/delete, revoke/stop/fault, and control-first/effect-first ordering;
nonfresh restart refusal; failed effect with lease cleanup; broken pipe worker;
simultaneous double submit; and pending control admission failure with worker cleanup. Effect-first cases exchange actual Windows
named-pipe denials while the P268 fake effect interface is entered. Wire operations
1–4 and replay yield only the fixed denial, with zero transport submissions.
Tests check no wire authority/effect, no rearm/replay, terminal lease cleanup,
sticky pending uncertainty, and worker termination. Waits are bounded. No SCM
registration or service launch is involved.

Python checks source invariants, frozen SHA256 bytes for P95/P96/P265/P267/P268,
and deliberately negative source mutations. These are structural checks, not a
substitute for the native races. The pinned Actions workflow requires the exact
branch, exact P268 base, a single child commit, exactly five additions, source
hash custody, x64/x86 debug warning-as-error builds, missing-symbol compiler
failures, and the actual native runner under a 40-second process watchdog.
Artifacts contain only text logs, raw exits and SHA256 records, never executables.

Local evidence (2026-11-18): x64 and x86 compile-only builds succeeded with
`/noconfig /debug+ /optimize- /warn:4 /warnaserror+` and all required symbols.
All six missing-guard configurations were refused on both architectures. Compiled programs were **not run on Kristian**. Authoritative Python access was
denied by the sandbox; no workaround/install was attempted. Hosted runtime and
Python results must be supplied by independent validation; no milestone seal is
claimed. No Git commit/push or workbook/dashboard update was performed.

Production service, real WinCred, issuer trust, and durable recovery remain HOLD.
