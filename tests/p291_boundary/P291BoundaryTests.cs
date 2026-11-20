#if !DEBUG || RELEASE || !C1_REVIEW_ISOLATED_ASSEMBLY || !C1_P291_BOUNDARY_EXPERIMENT_ONLY || !C1_P265_DEVELOPMENT_ONLY || !C1_P267_DEVELOPMENT_ONLY || !C1_P268_DEVELOPMENT_ONLY || !C1_P269_DEVELOPMENT_ONLY
#error P291_TEST_ONLY_DEBUG_ISOLATED_OPT_IN_REQUIRED
#endif
using System;
using System.Diagnostics;
using System.IO;
using System.IO.Pipes;
using System.Reflection;
using System.Security.Principal;
using System.Threading;
using Nayeon.ByokC1;
using Nayeon.ByokC1.P268Development;

namespace Nayeon.ByokC1.P291Development
{
    internal sealed partial class P291DevelopmentAdmissionSeam
    {
        private static int checks, cases;
        private static string nativeReceipt;
        private sealed class Hostile
        { public override string ToString() { throw new Exception("peer callback forbidden"); } }
        private static void Check(bool ok)
        { Interlocked.Increment(ref checks); if (!ok) throw new InvalidOperationException("P291_CHECK"); }
        private static void Join(Thread value) { Check(value.Join(3000)); }
        private static ControlResult Control(P291DevelopmentAdmissionSeam seam, int kind)
        { return kind == 0 ? seam.host.RevokeDevelopment() : kind == 1 ? seam.host.StopDevelopment() : seam.host.FaultDevelopment(); }

        // Frozen P265 expects Impersonation here; P290 separately proves Identification.
        // Neither token level is consent. No P290 token handle leaves its executable.
        private static void Wire(string endpoint)
        {
            using (var pipe = new NamedPipeClientStream(".", endpoint, PipeDirection.InOut,
                PipeOptions.Asynchronous, TokenImpersonationLevel.Impersonation))
            {
                pipe.Connect(1000); pipe.ReadMode = PipeTransmissionMode.Message;
                byte[] frame = new byte[28]; frame[0] = 24; frame[4] = 67; frame[5] = 49;
                frame[6] = 80; frame[7] = 53; frame[8] = 1; frame[9] = 2;
                Buffer.BlockCopy(Guid.NewGuid().ToByteArray(), 0, frame, 12, 16);
                pipe.Write(frame, 0, frame.Length);
                byte[] reply = new byte[8]; int offset = 0;
                while (offset < reply.Length)
                {
                    IAsyncResult read = pipe.BeginRead(reply, offset, reply.Length - offset, null, null);
                    using (WaitHandle wait = read.AsyncWaitHandle)
                    {
                        bool completed = wait.WaitOne(1500); int count;
                        try { if (!completed) pipe.Dispose(); }
                        finally
                        {
                            try { count = pipe.EndRead(read); }
                            catch (Exception) { if (completed) throw; count = 0; }
                            finally { if (!completed) throw new Exception("P291_READ_DEADLINE"); }
                        }
                        Check(count > 0); offset += count;
                    }
                }
                Check(BitConverter.ToString(reply) == "43-31-44-4E-01-01-00-00");
                pipe.Write(new byte[] { 165 }, 0, 1);
            }
        }
        private void Refusals(object ticket)
        {
            // Receipt originates in unchanged separately executed P290, but is NOT a capability.
            // Neither these fields nor a genuine ticket cause even TestPrepare to be called.
            int pid;
            using (Process current = Process.GetCurrentProcess()) { pid = current.Id; }
            object[] evidence = { null, nativeReceipt, new Hostile(), pid,
                "S-1-5-claimed", "pipe-name-claimed", new byte[] { 0x31, 0x32, 0x33, 0x34 },
                "P290_DIAGNOSTIC=PASS FORGED", new IntPtr(-1),
                new ServiceOwnedPendingTransaction.Approval(LedgerOperation.Save), ticket };
            foreach (object value in evidence)
            {
                Check(RefusePeer(value, new Hostile(), ticket) == PeerAdmission.Denied);
                Check(RefusePeer(value, value, value) == PeerAdmission.Denied); // replay/borrow
            }
        }
        private static void Surface()
        {
            Type type = typeof(P291DevelopmentAdmissionSeam);
            Check(type.GetConstructors(BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic).Length == 1);
            foreach (ConstructorInfo constructor in type.GetConstructors(BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic))
                Check(constructor.IsPrivate);
            foreach (MethodInfo method in type.GetMethods(BindingFlags.DeclaredOnly | BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.Static))
                Check(method.IsPrivate || method.Name == "RefusePeer");
            // Whitelist compiler's constant-return IL. No call/field access/branch to host is allowed.
            byte[] il = type.GetMethod("RefusePeer", BindingFlags.Instance | BindingFlags.NonPublic).GetMethodBody().GetILAsByteArray();
            for (int i = 0; i < il.Length; i++)
            {
                byte op = il[i];
                if (op == 0x2b) { Check(i + 1 < il.Length && il[++i] == 0); continue; }
                Check(op == 0x00 || op == 0x16 || op == 0x0a || op == 0x06 || op == 0x2a);
            }
        }
        private static void Unprepared(LedgerOperation operation)
        {
            var seam = new P291DevelopmentAdmissionSeam(operation);
            using (seam.host)
            {
                Check(seam.host.StartDevelopment());
                Wire(seam.host.Observe().Transport.Endpoint);
                Check(SpinWait.SpinUntil(() => seam.host.Observe().Transport.Requests == 1, 300));
                Check(!seam.host.Observe().Closed && seam.host.Observe().Transport.Submissions == 0);
                seam.Refusals(null);
                Check(seam.host.TestAdapter.JournalWrites == 0 && seam.host.TestAdapter.AnchorWrites == 0 &&
                    seam.host.TestAdapter.SaveCalls == 0 && seam.host.TestAdapter.DeleteCalls == 0 &&
                    seam.host.TestState.PossibleEffects == 0 && seam.host.TestApproval.ConsumeCount == 0);
                // TEST_ONLY positive control: only private in-process fixture invokes TestPrepare.
                var ticket = seam.host.TestPrepare(operation); Check(ticket != null);
                seam.Refusals(ticket);
                Check(seam.host.TestSubmit(ticket, operation) == (operation == LedgerOperation.Delete ?
                    CustodyOutcome.RemovedUnverified : CustodyOutcome.StoredUnverified));
                Check(seam.host.TestState.PossibleEffects == 1 && seam.host.TestGuard.LeaseDisposed);
                Check(seam.host.StopDevelopment() == ControlResult.TooLate);
                Check(seam.host.Observe().PendingMayHaveEffect && seam.host.Observe().PendingRecoveryRequired);
            }
        }
        private static void CrossHost()
        {
            var first = new P291DevelopmentAdmissionSeam(LedgerOperation.Save);
            var second = new P291DevelopmentAdmissionSeam(LedgerOperation.Save);
            using (first.host) using (second.host)
            {
                Check(first.host.StartDevelopment() && second.host.StartDevelopment());
                var ticket = first.host.TestPrepare(LedgerOperation.Save); Check(ticket != null);
                second.Refusals(ticket); first.Refusals(ticket);
                Check(first.host.TestState.PossibleEffects == 0 && second.host.TestState.PossibleEffects == 0);
                Check(second.host.TestSubmit(ticket, LedgerOperation.Save) == CustodyOutcome.Denied);
                Check(first.host.RevokeDevelopment() == ControlResult.Revoked);
                Check(first.host.TestSubmit(ticket, LedgerOperation.Save) == CustodyOutcome.Denied);
                Check(first.host.TestState.PossibleEffects == 0 && second.host.TestState.PossibleEffects == 0);
            }
        }
        private static void Contention(LedgerOperation operation, int kind, bool effectFirst)
        {
            var seam = new P291DevelopmentAdmissionSeam(operation);
            using (seam.host)
            using (var entered = new ManualResetEvent(false))
            using (var release = new ManualResetEvent(false))
            {
                Check(seam.host.StartDevelopment());
                var ticket = seam.host.TestPrepare(operation); Check(ticket != null);
                if (!effectFirst)
                {
                    seam.Refusals(ticket);
                    ControlResult result = Control(seam, kind);
                    Check(result == (kind == 0 ? ControlResult.Revoked : kind == 1 ? ControlResult.Stopped : ControlResult.RecoveryRequired));
                    seam.Refusals(ticket);
                    Check(seam.host.TestSubmit(ticket, operation) == CustodyOutcome.Denied);
                    Check(seam.host.TestState.PossibleEffects == 0 && seam.host.TestAdapter.SaveCalls == 0 && seam.host.TestAdapter.DeleteCalls == 0);
                }
                else
                {
                    seam.host.TestAdapter.Inject = point => { if (point == "effect-enter")
                        { entered.Set(); if (!release.WaitOne(2000)) throw new Exception("P291_EFFECT_DEADLINE"); } };
                    Exception writeError = null, peerError = null, controlError = null;
                    CustodyOutcome outcome = CustodyOutcome.Denied; ControlResult result = ControlResult.Revoked;
                    var writer = new Thread(() => { try { outcome = seam.host.TestSubmit(ticket, operation); } catch (Exception e) { writeError = e; } });
                    var peer = new Thread(() => { try { seam.Refusals(ticket); } catch (Exception e) { peerError = e; } });
                    var controller = new Thread(() => { try { result = Control(seam, kind); } catch (Exception e) { controlError = e; } });
                    writer.IsBackground = peer.IsBackground = controller.IsBackground = true;
                    writer.Start();
                    try
                    {
                        Check(entered.WaitOne(1500));
                        // Actual effect gate held: refusal must finish without waiting on it.
                        peer.Start(); Check(peer.Join(200) && peerError == null);
                        controller.Start(); Check(SpinWait.SpinUntil(() => seam.host.AdmissionClosed, 200));
                    }
                    finally { release.Set(); }
                    Join(writer); Join(peer); Join(controller);
                    Check(writeError == null && controlError == null && result == ControlResult.TooLate);
                    Check(outcome == (operation == LedgerOperation.Delete ? CustodyOutcome.RemovedUnverified : CustodyOutcome.StoredUnverified));
                    seam.Refusals(ticket);
                    var view = seam.host.Observe();
                    Check(view.PendingMayHaveEffect && view.PendingRecoveryRequired && view.Closed && view.Transport.WorkerExited);
                    Check(seam.host.TestState.PossibleEffects == 1 && seam.host.TestGuard.LeaseDisposed);
                    Check(seam.host.TestSubmit(ticket, operation) == CustodyOutcome.Denied);
                    Check(Control(seam, kind) == ControlResult.TooLate);
                }
            }
        }
        private static int Main(string[] arguments)
        {
            try
            {
                if (Environment.GetEnvironmentVariable("GITHUB_ACTIONS") != "true" ||
                    Environment.GetEnvironmentVariable("RUNNER_ENVIRONMENT") != "github-hosted" ||
                    Environment.GetEnvironmentVariable("RUNNER_OS") != "Windows" ||
                    Environment.GetEnvironmentVariable("ImageOS") != "win22" || arguments.Length != 1) return 64;
                Check(new FileInfo(arguments[0]).Length < 2048);
                nativeReceipt = File.ReadAllText(arguments[0]);
                Check(nativeReceipt.Contains("P290_DIAGNOSTIC=PASS CAPTURES=6 ") &&
                    nativeReceipt.Contains("P290_TOKEN=IDENTIFICATION LAST_READ=ORDERED REVERT=CHECKED") &&
                    nativeReceipt.Contains("P290_AUTHORITY=NONE"));
                Surface(); cases++;
                LedgerOperation[] operations = { LedgerOperation.Save, LedgerOperation.Replace, LedgerOperation.Delete };
                foreach (LedgerOperation operation in operations) { Unprepared(operation); cases++; }
                for (int kind = 0; kind < 3; kind++) foreach (bool first in new[] { false, true })
                    { Contention(operations[kind], kind, first); cases++; }
                CrossHost(); cases++;
                Console.WriteLine("P291_BOUNDARY=PASS CASES=" + cases + " ASSERTIONS=" + checks + " BITS=" + (IntPtr.Size * 8));
                Console.WriteLine("P291_NATIVE_RECEIPT=UNTRUSTED PEER=DENIED PREPARE_ROUTE=NONE POSITIVE=TEST_ONLY");
                Console.WriteLine("P291_ISSUER=ABSENT REAL_CONSENT=ABSENT NONDEPLOYABLE PRODUCTION=HOLD P96_ORIGINAL=STILL_VULNERABLE APPROVALS=0/7 FULL_REGRESSIONS=0/3");
                return 0;
            }
            catch (Exception) { Console.WriteLine("P291_BOUNDARY=HOLD"); return 1; }
        }
    }
}
