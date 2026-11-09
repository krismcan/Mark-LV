# BYOK C1 P125 — genuine Windows named-pipe client exit and original-handle-close negative tests

Date: 9 November 2026 | OM v2.1 | Direct P124 baseline `81dfe545146a0503b33c786e6003a7bd77413bad`

## Actual threat tested

P124 reproduced the specific Windows named-pipe security gap: a **different native Windows process can write a pipe nonce via a duplicated handle**, while `GetNamedPipeClientProcessId` and P114/P115 observations continue to report the *connecting* process. A signed program's name, PID, SID, session, integrity and nonce echo are never proof that the approved human or executable authored that response. There is no positive consent/credential permission in P121–P124.

P125 extends this with a distinct lifecycle test using three unprivileged processes on a real GitHub-hosted Windows x64 runner:

1. An isolated host creates a one-connection current-user ACL pipe and an exact immutable synthetic request.
2. A genuine separate native Windows *opener* process connects, sends one inert handshake byte and reads the 64-byte review-only P120 operation challenge frame.
3. A different *writer* process calls native `OpenProcess(PROCESS_DUP_HANDLE | SYNCHRONIZE)` and `DuplicateHandle` to gain the connected client HANDLE; it signals readiness.
4. In **exit** mode, the original opener exits. The writer calls `WaitForSingleObject` on that process object, proving the opener process is terminated before the writer sends a 32-byte nonce using genuine native `WriteFile`. The writer saves only its PID and number of bytes to an ephemeral per-test file in hosted runner TEMP (no nonce, key, SID or handle).
5. In **close** mode, the opener closes its original `NamedPipeClientStream` handle while its process is still alive; the other process sends the reply using the duplicate. The host must **NEVER** claim signed broker, human consent, protected durable grant or credential effect even if an OS-observed client PID still exists or diagnostic echo matches.
6. In exit mode the host's P121/P123 post-reply OS process/session reobservation is expected to fail closed — a valid echoed nonce must not count as an accepted OS-client diagnostic if the original pipe opener is gone.

## Real unprivileged hosted Windows test plan

12 new focused Windows-native cases: null/unconnected refusal, live original opener handle-duplicate control, actual opener-exit after transfer twice and repeated, wrong/short transfer after opener exit, live opener with original client HANDLE closed twice and repeated, and frozen original P49/P112 native-effect hold. The original P124 **12** actual transferred-writer negative cases and every P123/P122/P121/P120/P118/P117/P116/P115/P114/P113/P112/P110/P109/P108/P106/P99/P96 test driver must run unchanged.

Target genuine native focused total: **337 = 12 new P125 + 325 prior**, including P96's 15 fake-only cases reproducing the check/effect revocation race. All compilation/execution on **unprivileged GitHub Windows-2025 runner only**; never run unsigned native EXE on Kristian. Freeze P49 11 source hashes, candidate source hashes and exact branch diff.

This test uses `Process.GetCurrentProcess`, Win32 `DuplicateHandle`, `WriteFile`, `WaitForSingleObject` and a per-run ephemeral nonsecret proof file only. The real writer receives nonsecret nonce through test command line, illustrating that relay of an untrusted challenge cannot establish approval. The evidence file is deleted after each test. No secret, privileged service, persistent approval, WinCred, registry or protected journal.

## Security interpretation / not a production fix

If the original opener terminates and the post-reply P114/P115 checks refuse even a correct echoed frame, that confirms a **limited denial boundary for exited opener**. It **DOES NOT** fix the much more serious P124 case when opener remains alive or its original handle is closed but some other process still holds a duplicate. Repeated OS PID checks and nonce relays are never proof of reply *author*. A real G1 production system still needs qualified threat model and external independent Windows review of signed installed publisher-pinned broker, service-owned authenticated channel, live image identity, defensible trusted human exact-operation presence and durable protected one-use permission. No such approval can be derived from this driver.

G0 qualified independent native Windows review OPEN; G1 real approved consent broker and writer/authorship/user presence OPEN; G2 original P96 native revocation-to-effect race OPEN; G3 protected journal, antirollback and recovery OPEN; G4 pending-only privileged WinCred real lifecycle OPEN; G5 signing/Smart App Control production approval OPEN; G6 three full Windows product regressions, qualified release and original Google Drive master-first/dashboard reconciliation OPEN.

**P125 development only. BYOK C1 PRODUCTION RELEASE HOLD.**
