# BYOK C1 P129 — real Windows forced process termination and torn ephemeral journal negative tests

Date 9 November 2026 | OM v2.1 | direct exact P128 parent `1413a526c4f7572876dcda0d15a05b0a8a65599a`

## Why P129 follows P128

P128 proved that disposable unprotected, nonsecret Windows TEMP journal records written with `FileStream.Flush(true)` are visible when a separate Windows child process exits **normally** after writing, and that an attacker can roll back an older valid hash-chain prefix undetected without an independently protected history witness. P128 did NOT actually kill a live writer. This distinction must not be hidden.

P129 uses actual **`System.Diagnostics.Process.Kill()` and `WaitForExit()`** on genuinely separate unprivileged Windows child processes. Each child uses ONLY the P128 ephemeral nonsecret test-file path, Flush(true) where applicable, signals it remains alive after creating a target state, and sleeps. The parent then forcibly terminates that genuine native OS process before reopening the file. This is stronger evidence of process-lifetime failure handling than a normal child exit, but still **NOT** a physical power-cut, hardware cache persistence guarantee or real protected G3 journal.

## Native test design

Exactly 14 new hosted-Windows focused cases:
- actual forcibly terminated child holding an empty file, 7-byte partial record, 41-byte torn frame or syntactically invalid full frame; after OS termination the review classifier must fail closed;
- actual forced death following one valid synthetic Intent, two Intent/FakeAttemptStarted stages or all three diagnostic stages; independent parent reopens real bytes and still **NEVER** grants native-effect authority, protected journal or true historical trust;
- actual child holding a live `FileShare.None` Windows handle on an intent file; after forced termination Windows closes the handle so an independent process can reopen and classify the record (still no positive authorization);
- child killed after one or two valid stages plus a partially appended invalid record; parsing refuses malformed journal;
- repeated actual OS terminations across four different stage states with no positive admission;
- original strict frozen P49 and candidate P112 no-effect guards still deny all credential operations;
- a full flushed three-record file after forced death is still no evidence of independently anchored history/antirollback.

No arbitrary process ID or user file is touched. Only children launched by the test itself on an isolated unprivileged GitHub-hosted Windows runner are ever terminated. The P128 ephemeral files are under runner TEMP with strict random 32-hex naming and deleted per test. No real credential, Windows service, HKLM/protected journal, key, native WinCred, signed UI or production installation.

P128's previous **402 genuine focused native cases** are preserved unmodified, including the original P96 15 fake-only negative tests demonstrating the old revocation-to-effect race. Target **416 = 14 new + 402 existing actual Windows native focused cases**, not full product regressions. Freeze source hashes and changed-file scope. This increment adds only a driver, hosted Windows workflow and documentation; P128 and prior implementation remains unchanged.

## Threat model and audit limitations

These tests do not force termination at precisely the operating system write/flush syscall boundary; rather, they create selected complete or intentionally partial in-memory/file states, flush them, and then kill the live child. They cannot simulate torn NTFS metadata, storage controller cache power loss, volume corruption or protected historical-witness compromise. The P128 chain is unkeyed and can be rolled back; all structurally valid observations remain **untrusted diagnostic states**, never a service-owned signed approval.

A real production G3 must combine protected file+registry anchor under independently verified Windows service ownership, antirollback/historical enrollment witness and explicit negative recovery for missing/uncertain/corrupt states, reviewed ACLs and signed service binary. G2 must couple real native fixed-effect dispatch and revocation under one admitted actor and real OS custody lease, with G1 signed approved human one-use consent. None are implemented in P129.

G0 qualified independent Windows security reviewer OPEN. G1 signed installed broker, trusted real human presence, authenticated process and durable one-use consent OPEN. G2 original P96 race open and no approved real WinCred actor. G3 protected/anchored journal and actual crash/reboot/power-loss recovery OPEN. G4 real privileged WinCred pending-only lifecycle OPEN. G5 signing/SAC production acceptance OPEN. G6 three complete native Windows product regressions, independent release and original Drive master workbook-first/dashboard release sync OPEN.

No historical P62 safety-block retry, Smart App Control bypass, unsigned EXE on Kristian, GitHub merge/tag/release or nonrelease Google Drive changes.

**P129 review-only negative proof. BYOK C1 PRODUCTION RELEASE HOLD.**
