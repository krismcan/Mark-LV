#if !C1_P264_DEVELOPMENT_ONLY
#error P264_DEVELOPMENT_ONLY_EXPLICIT_OPT_IN_REQUIRED
#endif
#if !DEBUG
#error P264_NO_RELEASE_BUILD
#endif
// DEVELOPMENT ONLY. No installer, listener, credential or persistent-store code.
using System;
using System.ServiceProcess;
using System.Threading;

namespace Nayeon.ByokC1.P264Development
{
    internal enum Lifecycle { Created, RunningDenied, Revoked, Stopped, Faulted, Disposed }
    internal enum Refusal { DevelopmentHold, NotStarted, Revoked, Stopped, Faulted, Disposed, Reentrant }

    // Coarse, immutable denial evidence only; never a permit or a secret carrier.
    internal sealed class Denial
    {
        internal readonly Lifecycle State;
        internal readonly Refusal Reason;
        internal readonly bool StopRecorded;
        internal readonly bool RevokeRecorded;
        internal readonly bool FaultRecorded;
        internal bool CredentialAllowed { get { return false; } }
        internal bool IpcAllowed { get { return false; } }
        internal bool StoreAllowed { get { return false; } }
        internal bool ProductionEligible { get { return false; } }

        internal Denial(Lifecycle state, Refusal reason, bool stop, bool revoke, bool fault)
        { State = state; Reason = reason; StopRecorded = stop; RevokeRecorded = revoke; FaultRecorded = fault; }
    }

    internal sealed class DevelopmentCustodyService : ServiceBase
    {
        // Source-linked projection of frozen P99 ServiceGate.ServiceName. The static
        // test compares both declarations. Do NOT compile/call its LocalSystem gate.
        internal const string FrozenServiceName = "NayeonV1ByokCustody";
        private readonly CustodyOwner owner = new CustodyOwner();

        internal DevelopmentCustodyService()
        {
            ServiceName = FrozenServiceName;
            CanStop = true;
            CanShutdown = true;
            CanPauseAndContinue = false;
            AutoLog = false;
        }

        protected override void OnStart(string[] arguments)
        {
            // Running means denial-only lifecycle availability, NOT custody admission.
            Denial result = owner.Apply(Command.Start);
            if (result.State != Lifecycle.RunningDenied)
                throw new InvalidOperationException("P264_START_REFUSED");
        }

        protected override void OnStop() { owner.Apply(Command.Stop); }
        protected override void OnShutdown() { owner.Apply(Command.Stop); }
        protected override void OnCustomCommand(int command)
        {
            // No custom SCM protocol or operation dispatch exists.
            owner.Apply(Command.RejectIpc);
        }

        // Fixed internal lifecycle ingress; no caller callbacks, claims or payloads.
        internal Denial Revoke() { return owner.Apply(Command.Revoke); }
        internal Denial Fault() { return owner.Apply(Command.Fault); }
        internal Denial RejectCredential() { return owner.Apply(Command.RejectCredential); }
        internal Denial RejectIpc() { return owner.Apply(Command.RejectIpc); }
        internal Denial RejectStore() { return owner.Apply(Command.RejectStore); }
        internal Denial ObserveDenial() { return owner.Apply(Command.Observe); }

        protected override void Dispose(bool disposing)
        {
            // Close admission before framework cleanup, including repeated disposal.
            owner.Apply(Command.Dispose);
            base.Dispose(disposing);
        }

        private enum Command { Start, Stop, Revoke, Fault, Dispose, RejectCredential, RejectIpc, RejectStore, Observe }

        private sealed class CustodyOwner
        {
            private readonly object sync = new object();
            private bool started, stopped, revoked, faulted, disposed;

            internal Denial Apply(Command command)
            {
                // Monitor is recursive: explicitly reject same-thread reentry before
                // any requested mutation. This path already owns sync; fault is sticky.
                if (Monitor.IsEntered(sync))
                {
                    faulted = true;
                    return View(Refusal.Reentrant);
                }
                lock (sync)
                {
                    switch (command)
                    {
                        case Command.Start:
                            if (!started && !stopped && !revoked && !faulted && !disposed)
                                started = true;
                            else
                                faulted = true; // a repeated or stale start never reopens
                            break;
                        case Command.Stop:
                            stopped = true;
                            break;
                        case Command.Revoke:
                            revoked = true;
                            break;
                        case Command.Fault:
                            faulted = true;
                            break;
                        case Command.Dispose:
                            stopped = true;
                            disposed = true;
                            break;
                        case Command.RejectCredential:
                        case Command.RejectIpc:
                        case Command.RejectStore:
                        case Command.Observe:
                            break; // validation returns denial; it performs no action
                        default:
                            faulted = true;
                            break;
                    }
                    return View(null);
                }
            }

            // Called only under sync. No external dependency or effect entrypoint.
            private Denial View(Refusal? overrideReason)
            {
                Lifecycle state = disposed ? Lifecycle.Disposed : faulted ? Lifecycle.Faulted :
                    stopped ? Lifecycle.Stopped : revoked ? Lifecycle.Revoked :
                    started ? Lifecycle.RunningDenied : Lifecycle.Created;
                Refusal reason = disposed ? Refusal.Disposed : faulted ? Refusal.Faulted :
                    stopped ? Refusal.Stopped : revoked ? Refusal.Revoked :
                    started ? Refusal.DevelopmentHold : Refusal.NotStarted;
                return new Denial(state, overrideReason ?? reason, stopped, revoked, faulted);
            }
        }

        private static int Main(string[] arguments)
        {
            // A build flag and a CLI token acknowledge development scope; neither is
            // security approval. Default invocation never contacts the SCM dispatcher.
            if (arguments == null || arguments.Length != 1 ||
                !String.Equals(arguments[0], "--development-only-no-effects", StringComparison.Ordinal))
                return 64;
            using (var service = new DevelopmentCustodyService())
            {
                try { ServiceBase.Run(service); }
                catch
                {
                    service.Fault();
                    throw; // preserve the framework failure; never report a successful start
                }
            }
            return 0;
        }
    }
}
