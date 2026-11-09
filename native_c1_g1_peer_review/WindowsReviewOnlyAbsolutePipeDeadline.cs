// P122 — isolated, unprivileged Windows named-pipe read deadline review.
// A SINGLE monotonic deadline covers the entire 32-byte reply frame.
// Windows cancellation is only REQUESTED by CancelIoEx; EndRead must
// observe terminal completion (or the pipe is closed and the failure
// is explicitly marked unconfirmed). Not a production service read path.
#if !C1_REVIEW_ISOLATED_ASSEMBLY
#error P122 is an ISOLATED REVIEW component, not a deployed service
#endif
using System;
using System.Diagnostics;
using System.IO;
using System.IO.Pipes;
using System.Runtime.InteropServices;
using Microsoft.Win32.SafeHandles;

namespace Nayeon.ByokC1
{
    internal enum OsPipeDeadlineReadState
    {
        InvalidOrUnavailable,
        ExactFrameObserved,
        ClosedOrTruncated,
        DeadlineExpiredAndDrained,
        DeadlineExpiredDrainUnconfirmed
    }

    internal sealed class OsPipeDeadlineReadObservation
    {
        internal readonly OsPipeDeadlineReadState State;
        internal readonly int ActualReceivedBytes;
        internal readonly bool CancelIoExAttempted;
        internal readonly bool EndReadCompletionObserved;
        internal readonly bool HandleQuarantinedOnFailure;

        internal OsPipeDeadlineReadObservation(
            OsPipeDeadlineReadState state,int received,
            bool cancelRequested,bool endReadConfirmed,bool quarantined)
        {
            State=state;
            ActualReceivedBytes=received;
            CancelIoExAttempted=cancelRequested;
            EndReadCompletionObserved=endReadConfirmed;
            HandleQuarantinedOnFailure=quarantined;
        }

        internal bool ExactReviewFrameObserved
        {get{return State==OsPipeDeadlineReadState.ExactFrameObserved;}}
        internal bool RealSignedBrokerAuthenticated {get{return false;}}
        internal bool HumanConsentVerified {get{return false;}}
        internal bool ProtectedDurableGrantIssued {get{return false;}}
        internal bool NativeCredentialEffectAllowed {get{return false;}}

        internal static OsPipeDeadlineReadObservation Unavailable()
        {
            return new OsPipeDeadlineReadObservation(
                OsPipeDeadlineReadState.InvalidOrUnavailable,
                0,false,false,false);
        }
        public override string ToString()
        {return "<P122 review-only bounded pipe read; no consent or credential effect>";}
    }

    internal static class WindowsReviewOnlyAbsolutePipeDeadline
    {
        internal const int ExactReviewFrameBytes=32;
        internal const int MaxReviewDeadlineMs=2000;
        private const int CancellationDrainGraceMs=1500;

        [DllImport("kernel32.dll",SetLastError=true,ExactSpelling=true)]
        [return:MarshalAs(UnmanagedType.Bool)]
        private static extern bool CancelIoEx(
            SafePipeHandle handle,IntPtr overlapped);

        // The review harness alone owns the per-test pipe and issues only
        // ONE read at a time. CancelIoEx(NULL) requests cancellation of
        // every pending operation on this HANDLE; never reuse in a shared
        // production endpoint. Caller MUST abandon a refused pipe.
        internal static OsPipeDeadlineReadObservation ReadExactFrame(
            NamedPipeServerStream ownedExclusivePipe,byte[] output,
            int totalDeadlineMs)
        {
            if(ownedExclusivePipe==null || output==null ||
                output.Length!=ExactReviewFrameBytes ||
                totalDeadlineMs<25 || totalDeadlineMs>MaxReviewDeadlineMs)
                return OsPipeDeadlineReadObservation.Unavailable();

            try
            {
                if(!ownedExclusivePipe.IsConnected ||
                    !ownedExclusivePipe.IsAsync)
                    return OsPipeDeadlineReadObservation.Unavailable();
            }
            catch(Exception)
            {return OsPipeDeadlineReadObservation.Unavailable();}

            int offset=0;
            bool allReadsEnded=true;
            bool attemptedCancel=false;
            bool forcedClose=false;
            bool deadlineReached=false;
            var clock=Stopwatch.StartNew();

            // No reset of elapsed time after each partial reply.
            while(offset<ExactReviewFrameBytes)
            {
                long remaining=totalDeadlineMs-clock.ElapsedMilliseconds;
                if(remaining<=0)
                {
                    deadlineReached=true;
                    break;
                }

                IAsyncResult pending=null;
                bool endReadCalled=false;
                try
                {
                    pending=ownedExclusivePipe.BeginRead(
                        output,offset,ExactReviewFrameBytes-offset,null,null);

                    int boundedWait=(int)Math.Min(
                        remaining,Int32.MaxValue);
                    if(!pending.AsyncWaitHandle.WaitOne(boundedWait))
                    {
                        deadlineReached=true;
                        attemptedCancel=true;
                        try
                        {
                            // This is NOT proof that the read ended.
                            CancelIoEx(ownedExclusivePipe.SafePipeHandle,
                                IntPtr.Zero);
                        }
                        catch(Exception)
                        { /* Closed/invalid pipe: still no success */ }

                        // Cancellation is asynchronous. Wait for completion
                        // before releasing the IAsyncResult and buffer.
                        if(!pending.AsyncWaitHandle.WaitOne(
                            CancellationDrainGraceMs))
                        {
                            forcedClose=true;
                            try{ownedExclusivePipe.Dispose();}
                            catch(Exception){}
                        }

                        if(!pending.AsyncWaitHandle.WaitOne(
                            CancellationDrainGraceMs))
                        {
                            // Explicitly UNCONFIRMED; NEVER reuse this pipe.
                            allReadsEnded=false;
                            break;
                        }
                    }

                    int count;
                    try
                    {
                        endReadCalled=true;
                        count=ownedExclusivePipe.EndRead(pending);
                    }
                    catch(IOException)
                    {
                        if(deadlineReached)
                            break;
                        return new OsPipeDeadlineReadObservation(
                            OsPipeDeadlineReadState.ClosedOrTruncated,
                            offset,attemptedCancel,true,true);
                    }
                    catch(ObjectDisposedException)
                    {
                        if(deadlineReached)
                            break;
                        return new OsPipeDeadlineReadObservation(
                            OsPipeDeadlineReadState.ClosedOrTruncated,
                            offset,attemptedCancel,true,true);
                    }
                    catch(OperationCanceledException)
                    {
                        if(deadlineReached)break;
                        return new OsPipeDeadlineReadObservation(
                            OsPipeDeadlineReadState.ClosedOrTruncated,
                            offset,attemptedCancel,true,true);
                    }

                    // Even if the IO completed normally during cancellation
                    // it must NOT turn a timed-out reply into success.
                    if(deadlineReached)break;
                    if(count<=0)
                        return new OsPipeDeadlineReadObservation(
                            OsPipeDeadlineReadState.ClosedOrTruncated,
                            offset,attemptedCancel,true,true);
                    offset+=count;
                }
                catch(Exception)
                {
                    return new OsPipeDeadlineReadObservation(
                        OsPipeDeadlineReadState.InvalidOrUnavailable,
                        offset,attemptedCancel,allReadsEnded,true);
                }
                finally
                {
                    if(pending!=null)
                    {
                        try
                        {
                            if(endReadCalled || !allReadsEnded)
                            {
                                // On the unconfirmed path, the pipe has
                                // already been disposed and the caller
                                // cannot reuse it. Never claim a drain.
                            }
                            pending.AsyncWaitHandle.Close();
                        }
                        catch(Exception){}
                    }
                }
            }

            if(deadlineReached)
            {
                try{ownedExclusivePipe.Dispose();}
                catch(Exception){}
                return new OsPipeDeadlineReadObservation(
                    allReadsEnded?
                        OsPipeDeadlineReadState.DeadlineExpiredAndDrained:
                        OsPipeDeadlineReadState.DeadlineExpiredDrainUnconfirmed,
                    offset,attemptedCancel,allReadsEnded,true);
            }
            if(offset!=ExactReviewFrameBytes)
                return new OsPipeDeadlineReadObservation(
                    OsPipeDeadlineReadState.ClosedOrTruncated,
                    offset,attemptedCancel,allReadsEnded,true);

            return new OsPipeDeadlineReadObservation(
                OsPipeDeadlineReadState.ExactFrameObserved,
                offset,false,true,false);
        }
    }
}
