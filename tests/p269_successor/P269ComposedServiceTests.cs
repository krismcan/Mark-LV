#if !DEBUG
#error P269_TESTS_NO_RELEASE_BUILD
#endif
#if !C1_P265_DEVELOPMENT_ONLY || !C1_P267_DEVELOPMENT_ONLY || !C1_P268_DEVELOPMENT_ONLY || !C1_P269_DEVELOPMENT_ONLY
#error P269_TESTS_ALL_OPT_INS_REQUIRED
#endif
using System;
using System.IO.Pipes;
using System.Security.Principal;
using System.Threading;
using Nayeon.ByokC1;
using Nayeon.ByokC1.P268Development;
using Nayeon.ByokC1.P269Development;

internal static class P269ComposedServiceTests
{
    private static int checks, cases;
    private static void Check(bool condition, string message)
    { Interlocked.Increment(ref checks); if (!condition) throw new Exception(message); }
    private static void Join(Thread thread) { Check(thread.Join(3000), "thread deadline"); }
    private static void Traffic(string endpoint, byte operation, Guid id)
    {
        using (var pipe = new NamedPipeClientStream(".", endpoint, PipeDirection.InOut,
            PipeOptions.Asynchronous, TokenImpersonationLevel.Impersonation))
        {
            pipe.Connect(1000); pipe.ReadMode = PipeTransmissionMode.Message;
            byte[] frame = new byte[28]; frame[0] = 24; frame[4] = 67; frame[5] = 49;
            frame[6] = 80; frame[7] = 53; frame[8] = 1; frame[9] = operation;
            Buffer.BlockCopy(id.ToByteArray(), 0, frame, 12, 16);
            pipe.Write(frame, 0, frame.Length);
            byte[] reply = new byte[8]; int offset = 0;
            while (offset < reply.Length)
            {
                IAsyncResult read = pipe.BeginRead(reply, offset, reply.Length - offset, null, null);
                using (WaitHandle wait = read.AsyncWaitHandle)
                { if (!wait.WaitOne(1500)) { pipe.Dispose(); throw new Exception("reply deadline"); } }
                int count = pipe.EndRead(read); Check(count > 0, "reply not EOF"); offset += count;
            }
            Check(BitConverter.ToString(reply) == "43-31-44-4E-01-01-00-00", "wire is denial only");
            pipe.Write(new byte[] { 165 }, 0, 1);
        }
    }
    private static ControlResult Control(ComposedDevelopmentService host, int kind)
    { return kind == 0 ? host.RevokeDevelopment() : kind == 1 ? host.StopDevelopment() : host.FaultDevelopment(); }
    private static void NoReplay(ComposedDevelopmentService host,
        ServiceOwnedPendingTransaction.Approval ticket, LedgerOperation op)
    {
        int before = host.TestState.PossibleEffects;
        host.TestSubmit(ticket, op);
        Check(host.TestState.PossibleEffects == before && host.TestPrepare(op) == null, "terminal no replay/rearm");
        Check(!host.StartDevelopment(), "cannot restart stopped/used instance");
    }
    private static void Ordering(LedgerOperation op, int kind, bool effectFirst)
    {
        using (var host = ComposedDevelopmentService.TestOnlyCreate(op, true))
        using (var entered = new ManualResetEvent(false))
        using (var release = new ManualResetEvent(false))
        {
            Check(host.TestPrepare(op) == null, "not started");
            Check(host.StartDevelopment(), "developer start");
            var ticket = host.TestPrepare(op); Check(ticket != null, "one-use ticket");
            Check(host.TestPrepare(op) == null, "no double prepare");
            string endpoint = host.Observe().Transport.Endpoint;
            if (!effectFirst)
            {
                Traffic(endpoint, 2, Guid.NewGuid());
                Check(host.TestState.PossibleEffects == 0 && host.TestApproval.ConsumeCount == 0, "wire grants no pending authority");
                ControlResult result = ControlResult.TooLate;
                Exception controlError = null;
                var controlThread = new Thread(() => { try { result = Control(host, kind); } catch (Exception e) { controlError = e; } });
                controlThread.Start(); Join(controlThread);
                Check(controlError == null, "control-first thread completed");
                Check(result == (kind == 0 ? ControlResult.Revoked : kind == 1 ? ControlResult.Stopped : ControlResult.RecoveryRequired), "control first disposition");
                host.TestApproval.Revoke();
                Check(host.TestSubmit(ticket, op) == CustodyOutcome.Denied && host.TestState.PossibleEffects == 0, "control returned first no effect");
            }
            else
            {
                host.TestAdapter.Inject = point => { if (point == "effect-enter")
                    { entered.Set(); if (!release.WaitOne(2000)) throw new Exception("effect deadline"); } };
                CustodyOutcome outcome = CustodyOutcome.Denied;
                Exception writerError = null, controllerError = null;
                ControlResult result = ControlResult.Revoked;
                var writer = new Thread(() => { try { outcome = host.TestSubmit(ticket, op); } catch (Exception e) { writerError = e; } });
                var controller = new Thread(() => { try { result = Control(host, kind); } catch (Exception e) { controllerError = e; } });
                writer.Start(); Check(entered.WaitOne(1500), "effect interface entered");
                // Real worker concurrently denies wire traffic while P268 owns its own gate.
                try
                {
                    Traffic(endpoint, 3, Guid.NewGuid());
                    controller.Start();
                    Check(SpinWait.SpinUntil(() => host.AdmissionClosed, 300), "closed before waiting on pending gate");
                    Check(controller.IsAlive, "control cannot report cancellation across effect");
                }
                finally { release.Set(); }
                Join(writer); Join(controller);
                Check(writerError == null && controllerError == null, "bounded threads succeeded");
                Check(result == ControlResult.TooLate, "effect first always TooLate");
                Check(outcome == (op == LedgerOperation.Delete ? CustodyOutcome.RemovedUnverified : CustodyOutcome.StoredUnverified), "fake effect terminal");
                host.TestApproval.Revoke();
                Check(host.TestState.PossibleEffects == 1 && host.TestState.EffectsAfterRevoke == 0, "one fake effect before control returned");
                Check(host.TestGuard.TerminalMarked && host.TestGuard.LeaseDisposed, "verified terminal cleanup");
                var observation = host.Observe();
                Check(observation.PendingMayHaveEffect && observation.PendingRecoveryRequired, "sticky pending uncertainty");
                Check(!observation.Transport.MayHaveEffect && observation.Transport.Submissions == 0, "transport uncertainty separate");
            }
            var final = host.Observe();
            Check(final.Closed && final.Transport.WorkerExited && !final.CredentialAllowed && !final.ProductionEligible, "closed denial-only worker joined");
            NoReplay(host, ticket, op);
        }
    }
    private static void Restart()
    {
        using (var host = ComposedDevelopmentService.TestOnlyCreate(LedgerOperation.Save, false))
        {
            Check(!host.StartDevelopment() && host.TestPrepare(LedgerOperation.Save) == null, "nonfresh restart refused");
            Check(host.Observe().PendingRecoveryRequired && host.Observe().Transport.Endpoint == null, "no transport on restart");
        }
    }
    private static void FailedEffect()
    {
        using (var host = ComposedDevelopmentService.TestOnlyCreate(LedgerOperation.Delete, true))
        {
            Check(host.StartDevelopment(), "failure fixture start");
            var ticket = host.TestPrepare(LedgerOperation.Delete);
            host.TestState.ThrowDuringEffect = true;
            Check(host.TestSubmit(ticket, LedgerOperation.Delete) == CustodyOutcome.RecoveryRequired, "effect exception preserved");
            Check(host.FaultDevelopment() == ControlResult.TooLate, "failed effect never cancelled");
            Check(host.TestGuard.LeaseDisposed && host.Observe().Transport.WorkerExited, "failure cleanup");
            NoReplay(host, ticket, LedgerOperation.Delete);
        }
    }
    private static void BrokenTransport()
    {
        using (var host = ComposedDevelopmentService.TestOnlyCreate(LedgerOperation.Save, true))
        {
            Check(host.StartDevelopment(), "transport fault start");
            var ticket = host.TestPrepare(LedgerOperation.Save);
            using (var pipe = new NamedPipeClientStream(".", host.Observe().Transport.Endpoint, PipeDirection.InOut))
            { pipe.Connect(1000); pipe.Write(new byte[28], 0, 28); }
            Check(SpinWait.SpinUntil(() => host.Observe().Transport.WorkerExited, 2800), "broken worker exits");
            Check(host.TestSubmit(ticket, LedgerOperation.Save) == CustodyOutcome.Denied, "transport fault fences admission");
            Check(host.TestState.PossibleEffects == 0 && host.Observe().Closed, "no effect after observed transport fault");
        }
    }
    private static void DoubleSubmit()
    {
        using (var host = ComposedDevelopmentService.TestOnlyCreate(LedgerOperation.Save, true))
        using (var go = new ManualResetEvent(false))
        {
            Check(host.StartDevelopment(), "double submit start");
            var ticket = host.TestPrepare(LedgerOperation.Save);
            string endpoint = host.Observe().Transport.Endpoint;
            Guid id = Guid.NewGuid();
            Traffic(endpoint, 1, id); Traffic(endpoint, 4, id); // replay is also identical denial
            Check(host.TestState.PossibleEffects == 0, "all wire operations have no effect");
            CustodyOutcome a = CustodyOutcome.Denied, b = CustodyOutcome.Denied;
            Exception errorA = null, errorB = null;
            var first = new Thread(() => { try { if (!go.WaitOne(1500)) throw new Exception("start deadline"); a = host.TestSubmit(ticket, LedgerOperation.Save); } catch (Exception e) { errorA = e; } });
            var second = new Thread(() => { try { if (!go.WaitOne(1500)) throw new Exception("start deadline"); b = host.TestSubmit(ticket, LedgerOperation.Save); } catch (Exception e) { errorB = e; } });
            first.Start(); second.Start(); go.Set(); Join(first); Join(second);
            Check(errorA == null && errorB == null, "concurrent submit completed");
            Check((a == CustodyOutcome.StoredUnverified) != (b == CustodyOutcome.StoredUnverified), "exactly one successful fake submit");
            Check(host.TestState.PossibleEffects == 1, "no double effect");
            Check(host.TestPrepare(LedgerOperation.Save) == null, "terminal cannot rearm while started");
            Check(host.StopDevelopment() == ControlResult.TooLate, "terminal stop remains uncertain");
            Check(host.Observe().PendingRecoveryRequired && !host.Observe().Transport.MayHaveEffect, "separate sticky evidence");
        }
    }
    private static void ControlTimeoutCleanup()
    {
        using (var host = ComposedDevelopmentService.TestOnlyCreate(LedgerOperation.Save, true))
        using (var entered = new ManualResetEvent(false))
        using (var release = new ManualResetEvent(false))
        {
            Check(host.StartDevelopment(), "timeout start");
            var ticket = host.TestPrepare(LedgerOperation.Save);
            host.TestAdapter.Inject = point => { if (point == "effect-enter")
                { entered.Set(); if (!release.WaitOne(2500)) throw new Exception("timeout release deadline"); } };
            CustodyOutcome outcome = CustodyOutcome.Denied;
            Exception writerError = null, controlError = null;
            var writer = new Thread(() => { try { outcome = host.TestSubmit(ticket, LedgerOperation.Save); } catch (Exception e) { writerError = e; } });
            var controller = new Thread(() => { try { host.StopDevelopment(); } catch (Exception e) { controlError = e; } });
            writer.Start(); Check(entered.WaitOne(1500), "timeout effect entered");
            try
            {
                controller.Start(); Join(controller); // P268's bounded admission fails while effect is held
                Check(controlError is InvalidOperationException, "uncertain control raises, never successful cancellation");
                Check(host.AdmissionClosed, "failed control latches closed");
            }
            finally { release.Set(); }
            Join(writer);
            Check(writerError == null && outcome == CustodyOutcome.RecoveryRequired, "gate admission failure poisons pending result");
            var observation = host.Observe();
            Check(observation.Transport.WorkerExited && observation.PendingMayHaveEffect && observation.PendingRecoveryRequired,
                "finally joined worker despite pending control failure");
            Check(host.RevokeDevelopment() == ControlResult.TooLate, "subsequent control cannot claim cancellation");
        }
    }
    private static int Main()
    {
        try
        {
            foreach (LedgerOperation op in new[] { LedgerOperation.Save, LedgerOperation.Replace, LedgerOperation.Delete })
                for (int kind = 0; kind < 3; kind++)
                    foreach (bool first in new[] { false, true })
                    { Ordering(op, kind, first); cases++; Console.WriteLine("PASS order " + op + " " + kind + " " + first); }
            Restart(); cases++; FailedEffect(); cases++; BrokenTransport(); cases++; DoubleSubmit(); cases++; ControlTimeoutCleanup(); cases++;
            Console.WriteLine("P269_COMPOSITION=PASS CASES=" + cases + " ASSERTIONS=" + checks + " BITS=" + (IntPtr.Size * 8));
            Console.WriteLine("P269_SCOPE=DEVELOPMENT_ONLY DENIAL_ONLY PRODUCTION=HOLD"); return 0;
        }
        catch (Exception error) { Console.WriteLine("P269_FAIL=" + error); return 1; }
    }
}
