using System;
using System.Threading.Tasks;
using Nayeon.ByokC1.Service;

// Compile ONLY as P309.ProductService.Tests.exe against the actual product exe.
internal static class P311CrossLanguageHarness
{
    private enum Expectation { Denied, Refused, Idle }

    private static void Check(bool value)
    { if (!value) throw new InvalidOperationException(); }

    private static bool Arguments(string[] args, out Expectation expectation)
    {
        expectation = Expectation.Denied;
        Guid id;
        const string prefix = "P309.Disposable.";
        // All argument validation precedes owner construction and native access.
        if (args.Length != 2 || !args[0].StartsWith(prefix, StringComparison.Ordinal) ||
            !Guid.TryParseExact(args[0].Substring(prefix.Length), "N", out id) ||
            id == Guid.Empty || args[0] != prefix + id.ToString("N")) return false;
        switch (args[1])
        {
            case "Denied": expectation = Expectation.Denied; return true;
            case "Refused": expectation = Expectation.Refused; return true;
            case "Idle": expectation = Expectation.Idle; return true;
            default: return false;
        }
    }

    private static int Main(string[] args)
    {
        Expectation expected;
        if (!Arguments(args, out expected)) return 2;
        try
        {
            using (var owner = new SyntheticTransactionOwner())
            using (var server = new SyntheticIngressServer(owner, args[0]))
            {
                Check(owner.Observe().State == TransactionOwnerState.ActiveDenied);
                Check(!server.Completion.IsCompleted && !server.Refused);
                Console.WriteLine("READY"); // Constructor has created the real OS pipe.
                Console.Out.Flush();
                if (expected == Expectation.Idle)
                {
                    Check(!server.Completion.Wait(3600));
                    Check(!server.Refused && owner.Observe().State == TransactionOwnerState.ActiveDenied);
                    Check(owner.Observe().Epoch == 1);
                }
                else
                {
                    Check(server.Completion.Wait(4000));
                    Check(server.Refused == (expected == Expectation.Refused));
                    Check(owner.Observe().State == (expected == Expectation.Denied ?
                        TransactionOwnerState.ActiveDenied : TransactionOwnerState.Faulted));
                    // Keep the buffered denial alive until the Python client has read it.
                    Task<string> done = Console.In.ReadLineAsync();
                    Check(done.Wait(4000) && done.Result == "DONE");
                }
                server.Dispose();
                Check(server.Completion.IsCompleted);
                Check(owner.Observe().State == (expected == Expectation.Refused ?
                    TransactionOwnerState.Faulted : TransactionOwnerState.Stopped));
                Console.WriteLine(expected == Expectation.Idle ? "IDLE_DISPOSED" :
                    expected == Expectation.Denied ? "DENIED" : "REFUSED");
                return 0;
            }
        }
        catch (Exception) { return 1; } // Never emit exception details or identities.
    }
}
