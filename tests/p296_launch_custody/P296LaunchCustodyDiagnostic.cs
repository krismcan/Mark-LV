#if DEBUG && C1_REVIEW_ISOLATED_ASSEMBLY && C1_P296_SOURCE_ONLY && !RELEASE
using System;
using System.IO;
using System.Text;
using System.Threading;
using System.Threading.Tasks;

// Source-only review library. No entry point, Process API, launcher delegate or OS adapter.
namespace P296SourceOnly
{
    [Flags]
    internal enum Fault
    {
        None=0, Disabled=1, Protocol=2, Hash=4, SharingAmbiguity=8,
        LaunchDenied=16, LaunchAmbiguous=32, Identity=64, Deadline=128,
        OutputLimit=256, Stream=512, ExitUnavailable=1024, NonzeroExit=2048,
        Cleanup=4096, Supervisor=8192, Replay=16384
    }
    internal enum Kind
    {
        BeforeHash, SupervisorArmed, Launch, DrainsStarted, Stdout, Stderr,
        StdoutClosed, StderrClosed, Exit, Deadline, Cleanup, AfterHash, SupervisorClosed
    }
    internal enum Actor { Unknown, HashCustodian, ChildCustodian, ExternalSupervisor }
    internal enum LaunchState { Unavailable, Started, PolicyDenied, Ambiguous }

    internal static class FixedCandidate
    {
        // Historical P295 x64 synthetic assembly only, NOT P292/P294 service mode.
        // These literals do not assert this file exists, is installed or approved.
        internal const string Image = @"D:\Nayeon\P296_REVIEW_ONLY\P295PreflightContract.exe";
        internal const string Directory = @"D:\Nayeon\P296_REVIEW_ONLY";
        internal const string Arguments = "";
        internal const string Sha256 = "f95d6ebeb557b54b03100c55e3bf679a617c97ba4c474ae4eb9e6e2ecd8b0544";
        internal const int ChildDeadlineMs=8000, CleanupDeadlineMs=10000,
            TotalDeadlineMs=12000, OutputLimit=4096, MaxEvents=128;
    }

    internal sealed class Identity
    {
        internal readonly int Pid;
        internal readonly long BirthUtcTicks;
        internal readonly string RetainedHandle, Image;
        internal Identity(int pid, long birthUtcTicks, string retainedHandle, string image)
        { Pid=pid; BirthUtcTicks=birthUtcTicks; RetainedHandle=retainedHandle; Image=image; }
        internal bool Valid()
        {
            return Pid>0 && BirthUtcTicks>0 && RetainedHandle=="test-retained-handle-1" &&
                Image==FixedCandidate.Image;
        }
        internal bool Same(Identity other)
        {
            return other!=null && Valid() && other.Valid() && Pid==other.Pid &&
                BirthUtcTicks==other.BirthUtcTicks && RetainedHandle==other.RetainedHandle && Image==other.Image;
        }
    }

    // Immutable in-memory receipt, never authenticated evidence or a launch instruction.
    // Milliseconds are supervisor-relative monotonic observations, not child timestamps.
    internal sealed class Receipt
    {
        internal readonly Kind Kind;
        internal readonly Actor Actor;
        internal readonly int Milliseconds;
        internal readonly Identity Identity;
        internal readonly string Text, Image, Arguments, Directory;
        internal readonly bool Synthetic, Complete, ExclusiveHashRead, SharingAmbiguous,
            HandleRetained, Exited, StreamsDisposed, ProcessDisposed, DescendantsAbsent;
        internal readonly int? RawExit;
        internal readonly LaunchState Launch;
        internal Receipt(Kind kind, Actor actor, int milliseconds, Identity identity,
            string text, string image, string arguments, string directory,
            bool synthetic, bool complete, bool exclusiveHashRead, bool sharingAmbiguous,
            bool handleRetained, bool exited, bool streamsDisposed, bool processDisposed,
            bool descendantsAbsent, int? rawExit, LaunchState launch)
        {
            Kind=kind; Actor=actor; Milliseconds=milliseconds; Identity=identity;
            Text=text; Image=image; Arguments=arguments; Directory=directory;
            Synthetic=synthetic; Complete=complete; ExclusiveHashRead=exclusiveHashRead;
            SharingAmbiguous=sharingAmbiguous; HandleRetained=handleRetained; Exited=exited;
            StreamsDisposed=streamsDisposed; ProcessDisposed=processDisposed;
            DescendantsAbsent=descendantsAbsent; RawExit=rawExit; Launch=launch;
        }
    }

    internal sealed class DiagnosticResult
    {
        internal readonly Fault Faults;
        internal readonly int? RawExit;
        internal readonly Identity RetainedIdentity;
        internal readonly string Stdout, Stderr;
        internal readonly bool CleanupComplete;
        internal DiagnosticResult(Fault faults, int? rawExit, Identity identity,
            string stdout, string stderr, bool cleanupComplete)
        {
            Faults=faults; RawExit=rawExit; RetainedIdentity=identity;
            Stdout=stdout; Stderr=stderr; CleanupComplete=cleanupComplete;
        }
        internal string Outcome { get { return Faults==Fault.None ? "SYNTHETIC_RECEIPT_ONLY" : "HOLD"; } }
        internal string ExitLabel { get { return RawExit.HasValue ? "RAW_EXIT="+RawExit.Value : "RAW_EXIT=UNAVAILABLE"; } }
        internal bool CanLaunch { get { return false; } }
        internal bool RuntimeQualified { get { return false; } }
        internal bool ProductionOrRealKeyAllowed { get { return false; } }
        internal int AcceptedApprovals { get { return 0; } }
        internal int AcceptedRegressions { get { return 0; } }
    }

    internal static class InertOsBoundary
    {
        // Intentionally no input, launch implementation or opt-in switch. Do not call in this turn.
        internal static DiagnosticResult RequestLaunch()
        { return new DiagnosticResult(Fault.Disabled, null, null, "", "", false); }
    }

    internal sealed class LaunchCustodyDiagnostic
    {
        private bool consumed;
        private DiagnosticResult previous;
        internal DiagnosticResult Review(Receipt[] input)
        {
            if (consumed)
                return new DiagnosticResult((previous==null ? Fault.Protocol : previous.Faults)|Fault.Replay,
                    previous==null ? null : previous.RawExit, previous==null ? null : previous.RetainedIdentity,
                    "", "", false);
            consumed=true;
            if (input==null || input.Length==0 || input.Length>FixedCandidate.MaxEvents)
            {
                previous=new DiagnosticResult(Fault.Protocol|Fault.ExitUnavailable|Fault.Cleanup,
                    null,null,"","",false);
                return previous;
            }
            // Clone the sequence before interpreting it; Receipt and Identity have readonly fields.
            Receipt[] events=(Receipt[])input.Clone();
            Fault faults=Fault.None;
            Identity identity=null;
            int? raw=null;
            int stage=0, last=-1;
            bool outClosed=false, errClosed=false, exitSeen=false, timedOut=false, cleanup=false;
            StringBuilder stdout=new StringBuilder(), stderr=new StringBuilder();
            int count=events.Length;
            for (int index=0; index<count; index++)
            {
                Receipt r=events[index];
                if (r==null) { faults|=Fault.Protocol; continue; }
                if (!r.Synthetic || !r.Complete) faults|=Fault.Protocol;
                if (!r.Complete && (r.Kind==Kind.Stdout || r.Kind==Kind.Stderr ||
                    r.Kind==Kind.StdoutClosed || r.Kind==Kind.StderrClosed)) faults|=Fault.Stream;
                if (r.Milliseconds<last || r.Milliseconds<0 || r.Milliseconds>FixedCandidate.TotalDeadlineMs)
                    faults|=Fault.Deadline;
                last=Math.Max(last,r.Milliseconds);
                Actor expected=(r.Kind==Kind.BeforeHash || r.Kind==Kind.AfterHash) ? Actor.HashCustodian :
                    (r.Kind==Kind.SupervisorArmed || r.Kind==Kind.Deadline || r.Kind==Kind.SupervisorClosed) ?
                    Actor.ExternalSupervisor : Actor.ChildCustodian;
                if (r.Actor!=expected) faults|=Fault.Supervisor;
                // Every child observation must bind the original retained identity, including cleanup.
                if (expected==Actor.ChildCustodian && r.Kind!=Kind.Launch &&
                    (identity==null || !identity.Same(r.Identity) ||
                    (r.Kind!=Kind.Cleanup && !r.HandleRetained))) faults|=Fault.Identity;
                if (r.RawExit.HasValue && r.Kind!=Kind.Exit) faults|=Fault.Protocol;
                switch (r.Kind)
                {
                    case Kind.BeforeHash:
                        if (stage!=0) faults|=Fault.Protocol;
                        faults|=CheckHash(r); stage=1; break;
                    case Kind.SupervisorArmed:
                        if (stage!=1 || r.Milliseconds>=FixedCandidate.ChildDeadlineMs) faults|=Fault.Supervisor;
                        // Must be outside the child/launch host failure domain in a future adapter.
                        stage=2; break;
                    case Kind.Launch:
                        if (stage!=2) faults|=Fault.Protocol;
                        if (r.Image!=FixedCandidate.Image || r.Arguments!=FixedCandidate.Arguments ||
                            r.Directory!=FixedCandidate.Directory) faults|=Fault.Protocol;
                        if (r.Launch==LaunchState.PolicyDenied) faults|=Fault.LaunchDenied;
                        else if (r.Launch!=LaunchState.Started) faults|=Fault.LaunchAmbiguous;
                        if (r.Identity==null || !r.Identity.Valid() || !r.HandleRetained) faults|=Fault.Identity;
                        identity=r.Identity;
                        if (r.Milliseconds>=FixedCandidate.ChildDeadlineMs) faults|=Fault.Deadline;
                        stage=3; break;
                    case Kind.DrainsStarted:
                        if (stage!=3 || r.Milliseconds>=FixedCandidate.ChildDeadlineMs) faults|=Fault.Protocol;
                        stage=4; break;
                    case Kind.Stdout:
                    case Kind.Stderr:
                        if (stage!=4 || (r.Kind==Kind.Stdout ? outClosed : errClosed)) faults|=Fault.Stream;
                        if (r.Milliseconds>=FixedCandidate.ChildDeadlineMs) faults|=Fault.Deadline;
                        AppendBounded(r.Kind==Kind.Stdout ? stdout : stderr,r.Text,ref faults);
                        break;
                    case Kind.StdoutClosed:
                    case Kind.StderrClosed:
                        if (stage!=4 || (r.Kind==Kind.StdoutClosed ? outClosed : errClosed)) faults|=Fault.Stream;
                        if (r.Kind==Kind.StdoutClosed) outClosed=true; else errClosed=true;
                        break;
                    case Kind.Exit:
                        if (stage!=4 || exitSeen) faults|=Fault.Protocol;
                        // Never replace the original raw code with a cleanup/supervisor exit.
                        if (!exitSeen) raw=r.RawExit;
                        exitSeen=true;
                        if (!r.Exited || !r.RawExit.HasValue) faults|=Fault.ExitUnavailable;
                        if (r.RawExit.HasValue && r.RawExit.Value!=0) faults|=Fault.NonzeroExit;
                        if (r.Milliseconds>=FixedCandidate.ChildDeadlineMs) faults|=Fault.Deadline;
                        break;
                    case Kind.Deadline:
                        if (stage!=4 || timedOut || r.Milliseconds!=FixedCandidate.ChildDeadlineMs)
                            faults|=Fault.Supervisor;
                        timedOut=true; faults|=Fault.Deadline; break;
                    case Kind.Cleanup:
                        if (stage!=4 || (!exitSeen && !timedOut)) faults|=Fault.Protocol;
                        cleanup=r.Complete && r.Synthetic && r.Actor==Actor.ChildCustodian &&
                            r.Exited && r.StreamsDisposed && r.ProcessDisposed &&
                            r.DescendantsAbsent && outClosed && errClosed &&
                            r.Milliseconds<=FixedCandidate.CleanupDeadlineMs &&
                            (faults&(Fault.Identity|Fault.Stream))==0;
                        if (!cleanup) faults|=Fault.Cleanup;
                        stage=5; break;
                    case Kind.AfterHash:
                        if (stage!=5) faults|=Fault.Protocol;
                        faults|=CheckHash(r); stage=6; break;
                    case Kind.SupervisorClosed:
                        if (stage!=6 || index!=count-1) faults|=Fault.Supervisor;
                        stage=7; break;
                    default: faults|=Fault.Protocol; break;
                }
            }
            if (stage!=7) faults|=Fault.Protocol;
            if (!exitSeen || !raw.HasValue) faults|=Fault.ExitUnavailable;
            if (!cleanup) faults|=Fault.Cleanup;
            previous=new DiagnosticResult(faults,raw,identity,stdout.ToString(),stderr.ToString(),cleanup);
            return previous;
        }
        private static Fault CheckHash(Receipt r)
        {
            Fault f=Fault.None;
            if (r.Image!=FixedCandidate.Image || r.Text!=FixedCandidate.Sha256) f|=Fault.Hash;
            // Equal digest is insufficient if open/read/close exclusivity was ambiguous.
            if (!r.ExclusiveHashRead || r.SharingAmbiguous) f|=Fault.SharingAmbiguity;
            return f;
        }
        private static void AppendBounded(StringBuilder target, string chunk, ref Fault faults)
        {
            if (chunk==null) { faults|=Fault.Stream; return; }
            int remaining=FixedCandidate.OutputLimit-target.Length;
            if (chunk.Length>remaining) faults|=Fault.OutputLimit;
            target.Append(chunk,0,Math.Min(chunk.Length,remaining));
        }
    }

    internal sealed class DrainReceipt
    {
        internal readonly string Prefix;
        internal readonly bool Eof, Overflow, Cancelled, ReadError, DisposeError;
        internal DrainReceipt(string prefix, bool eof, bool overflow, bool cancelled, bool readError, bool disposeError)
        { Prefix=prefix; Eof=eof; Overflow=overflow; Cancelled=cancelled; ReadError=readError; DisposeError=disposeError; }
    }

    internal static class BoundedAsyncDrain
    {
        // Future adapter must start two concurrent drains BEFORE any exit wait.
        // No ReadToEndAsync: bounded prefix retained; excess drained/discarded to avoid pipe deadlock.
        // Cancellation cannot interrupt Framework TextReader.ReadAsync reliably. An EXTERNAL
        // supervisor must close pipes/terminate the retained child by the fixed deadline.
        // This helper alone is not a deadline or cleanup guarantee. No caller exists here.
        internal static async Task<DrainReceipt> CollectAsync(TextReader reader, CancellationToken cancellation)
        {
            StringBuilder prefix=new StringBuilder();
            char[] buffer=new char[256];
            bool eof=false, overflow=false, cancelled=false, error=false, disposeError=false;
            if (reader==null) return new DrainReceipt("",false,false,false,true,false);
            try
            {
                while (true)
                {
                    if (cancellation.IsCancellationRequested) { cancelled=true; break; }
                    int read=await reader.ReadAsync(buffer,0,buffer.Length).ConfigureAwait(false);
                    if (read==0) { eof=true; break; }
                    int retain=Math.Min(read,FixedCandidate.OutputLimit-prefix.Length);
                    prefix.Append(buffer,0,retain);
                    if (retain<read) overflow=true;
                }
            }
            catch (OperationCanceledException) { cancelled=true; }
            catch (Exception) { error=true; } // Classified, never interpreted as EOF/success.
            finally
            {
                try { reader.Dispose(); }
                catch (Exception) { disposeError=true; }
            }
            return new DrainReceipt(prefix.ToString(),eof,overflow,cancelled,error,disposeError);
        }
    }
}
#else
#error P296_DEBUG_ISOLATED_SOURCE_ONLY_REQUIRED
#endif
