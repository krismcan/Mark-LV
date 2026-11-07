// Nayeon C1 P49: native Windows service host. No credential authority yet.
// Never register this unfinished binary as a live service.
using System;
using System.ServiceProcess;

namespace Nayeon.ByokC1
{
    internal sealed class CustodyService : ServiceBase
    {
        internal CustodyService()
        {
            this.ServiceName = ServiceGate.ServiceName;
            this.CanStop = true;
            this.AutoLog = false;
        }

        protected override void OnStart(string[] arguments)
        {
            // Unreviewed/incorrect security context must REFUSE SERVICE START.
            // No effect, secret, journal, IPC or background task occurs.
            if (!ServiceGate.LiveEligible())
                throw new InvalidOperationException("Custody service is unavailable");
        }

        protected override void OnStop()
        {
            // No mutable state or work exists in the incomplete chassis.
        }

        private static void Main()
        {
            ServiceBase.Run(new CustodyService());
        }
    }
}
