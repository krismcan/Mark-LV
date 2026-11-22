#if DEBUG && C1_REVIEW_ISOLATED_ASSEMBLY && C1_P296_SOURCE_ONLY && !RELEASE
using System;
using System.Collections.Generic;

// Pure in-memory fixtures only. No Main, test framework initialization, launcher or IO.
// RunAll is supplied for a separately authorized future harness; DO NOT invoke this turn.
namespace P296SourceOnly
{
    internal static class LaunchCustodyDiagnosticTests
    {
        private static readonly Identity Original=new Identity(296,123456789,"test-retained-handle-1",FixedCandidate.Image);
        private static Receipt R(Kind kind, int ms, string text="", int? raw=null)
        {
            Actor actor=(kind==Kind.BeforeHash || kind==Kind.AfterHash) ? Actor.HashCustodian :
                (kind==Kind.SupervisorArmed || kind==Kind.SupervisorClosed || kind==Kind.Deadline) ?
                Actor.ExternalSupervisor : Actor.ChildCustodian;
            return new Receipt(kind,actor,ms,Original,text,FixedCandidate.Image,FixedCandidate.Arguments,
                FixedCandidate.Directory,true,true,true,false,true,true,true,true,true,raw,LaunchState.Started);
        }
        // Copy immutable receipts, with explicit adversarial replacements.
        private static Receipt Change(Receipt r, Kind? kind=null, Actor? actor=null, int? ms=null,
            Identity identity=null, string text=null, string image=null, string args=null, string directory=null,
            bool? synthetic=null, bool? complete=null, bool? exclusive=null, bool? sharing=null,
            bool? retained=null, bool? exited=null, bool? streams=null, bool? process=null,
            bool? descendants=null, LaunchState? launch=null, bool removeRaw=false, int? raw=null)
        {
            return new Receipt(kind??r.Kind,actor??r.Actor,ms??r.Milliseconds,identity??r.Identity,
                text??r.Text,image??r.Image,args??r.Arguments,directory??r.Directory,
                synthetic??r.Synthetic,complete??r.Complete,exclusive??r.ExclusiveHashRead,
                sharing??r.SharingAmbiguous,retained??r.HandleRetained,exited??r.Exited,
                streams??r.StreamsDisposed,process??r.ProcessDisposed,descendants??r.DescendantsAbsent,
                removeRaw ? null : raw??r.RawExit,launch??r.Launch);
        }
        private static Receipt[] Good()
        {
            return new[] {
                R(Kind.BeforeHash,0,FixedCandidate.Sha256), R(Kind.SupervisorArmed,1),
                R(Kind.Launch,2), R(Kind.DrainsStarted,3), R(Kind.Stdout,4,"out"),
                R(Kind.Stderr,5,"err"), R(Kind.StdoutClosed,6), R(Kind.StderrClosed,7),
                R(Kind.Exit,8,raw:0), R(Kind.Cleanup,9),
                R(Kind.AfterHash,10,FixedCandidate.Sha256), R(Kind.SupervisorClosed,11) };
        }
        private static void Require(bool value, string name)
        { if (!value) throw new InvalidOperationException("P296_ASSERT_"+name); }
        private static void Denials(DiagnosticResult r, string name)
        {
            Require(!r.CanLaunch && !r.RuntimeQualified && !r.ProductionOrRealKeyAllowed &&
                r.AcceptedApprovals==0 && r.AcceptedRegressions==0,name+"_authority");
        }
        private static void Reject(string name, Action<Receipt[]> mutate, Fault expected)
        {
            Receipt[] data=Good(); mutate(data);
            DiagnosticResult r=new LaunchCustodyDiagnostic().Review(data);
            Require(r.Outcome=="HOLD" && (r.Faults&expected)==expected,name); Denials(r,name);
        }
        internal static int RunAll()
        {
            int cases=0;
            DiagnosticResult good=new LaunchCustodyDiagnostic().Review(Good());
            Require(good.Outcome=="SYNTHETIC_RECEIPT_ONLY" && good.RawExit==0 && good.CleanupComplete &&
                good.Stdout=="out" && good.Stderr=="err" && good.RetainedIdentity.Same(Original),"control");
            Denials(good,"control"); cases++;
            // No test calls InertOsBoundary.RequestLaunch or BoundedAsyncDrain.CollectAsync.
            Reject("before_hash_mismatch",a=>a[0]=Change(a[0],text:new string('a',64)),Fault.Hash); cases++;
            Reject("after_hash_mismatch",a=>a[10]=Change(a[10],text:new string('b',64)),Fault.Hash); cases++;
            Reject("hash_sharing_before",a=>a[0]=Change(a[0],sharing:true),Fault.SharingAmbiguity); cases++;
            Reject("hash_sharing_after",a=>a[10]=Change(a[10],sharing:true),Fault.SharingAmbiguity); cases++;
            Reject("hash_shared_read",a=>a[0]=Change(a[0],exclusive:false),Fault.SharingAmbiguity); cases++;
            Reject("hash_image_drift",a=>a[10]=Change(a[10],image:@"D:\other.exe"),Fault.Hash); cases++;
            Reject("arbitrary_image",a=>a[2]=Change(a[2],image:"cmd.exe"),Fault.Protocol); cases++;
            Reject("arbitrary_arguments",a=>a[2]=Change(a[2],args:"/c anything"),Fault.Protocol); cases++;
            Reject("working_directory_drift",a=>a[2]=Change(a[2],directory:@"D:\other"),Fault.Protocol); cases++;
            Reject("application_control_denial",a=>a[2]=Change(a[2],launch:LaunchState.PolicyDenied),Fault.LaunchDenied); cases++;
            Reject("reported_success_ambiguous",a=>a[2]=Change(a[2],launch:LaunchState.Ambiguous),Fault.LaunchAmbiguous); cases++;
            Reject("launch_unavailable",a=>a[2]=Change(a[2],launch:LaunchState.Unavailable),Fault.LaunchAmbiguous); cases++;
            Reject("no_retained_handle",a=>a[2]=Change(a[2],retained:false),Fault.Identity); cases++;
            Reject("pid_reuse",a=>a[8]=Change(a[8],identity:new Identity(297,123456789,"test-retained-handle-1",FixedCandidate.Image)),Fault.Identity); cases++;
            Reject("birth_drift",a=>a[8]=Change(a[8],identity:new Identity(296,123456790,"test-retained-handle-1",FixedCandidate.Image)),Fault.Identity); cases++;
            Reject("handle_drift",a=>a[9]=Change(a[9],identity:new Identity(296,123456789,"other-handle",FixedCandidate.Image)),Fault.Identity|Fault.Cleanup); cases++;
            Reject("image_identity_drift",a=>a[8]=Change(a[8],identity:new Identity(296,123456789,"test-retained-handle-1","other.exe")),Fault.Identity); cases++;
            Reject("retention_lost",a=>a[5]=Change(a[5],retained:false),Fault.Identity); cases++;
            Reject("stdout_overflow",a=>a[4]=Change(a[4],text:new string('x',4097)),Fault.OutputLimit); cases++;
            Reject("stderr_overflow",a=>a[5]=Change(a[5],text:new string('x',4097)),Fault.OutputLimit); cases++;
            Reject("drains_not_started",a=>a[3]=Change(a[3],kind:Kind.Stdout),Fault.Stream); cases++;
            Reject("stdout_not_closed",a=>a[6]=Change(a[6],kind:Kind.Stdout),Fault.Cleanup); cases++;
            Reject("stderr_not_closed",a=>a[7]=Change(a[7],kind:Kind.Stderr),Fault.Cleanup); cases++;
            Reject("stream_read_error",a=>a[4]=Change(a[4],complete:false),Fault.Stream|Fault.Cleanup); cases++;
            Reject("exit_unavailable",a=>a[8]=Change(a[8],removeRaw:true),Fault.ExitUnavailable); cases++;
            Reject("not_signaled",a=>a[8]=Change(a[8],exited:false),Fault.ExitUnavailable); cases++;
            Reject("raw11_not_success",a=>a[8]=Change(a[8],raw:11),Fault.NonzeroExit); cases++;
            Reject("raw1062_not_success",a=>a[8]=Change(a[8],raw:1062),Fault.NonzeroExit); cases++;
            Reject("exit_at_deadline",a=>a[8]=Change(a[8],ms:8000),Fault.Deadline); cases++;
            Reject("clock_rollback",a=>a[5]=Change(a[5],ms:3),Fault.Deadline); cases++;
            Reject("negative_clock",a=>a[0]=Change(a[0],ms:-1),Fault.Deadline); cases++;
            Reject("cleanup_late",a=>a[9]=Change(a[9],ms:10001),Fault.Cleanup); cases++;
            Reject("supervisor_total_overrun",a=>a[11]=Change(a[11],ms:12001),Fault.Deadline); cases++;
            Reject("child_self_supervision",a=>a[1]=Change(a[1],actor:Actor.ChildCustodian),Fault.Supervisor); cases++;
            Reject("supervisor_missing",a=>a[1]=null,Fault.Protocol); cases++;
            Reject("supervisor_not_joined",a=>a[11]=null,Fault.Protocol); cases++;
            Reject("process_not_disposed",a=>a[9]=Change(a[9],process:false),Fault.Cleanup); cases++;
            Reject("streams_not_disposed",a=>a[9]=Change(a[9],streams:false),Fault.Cleanup); cases++;
            Reject("cleanup_receipt_incomplete",a=>a[9]=Change(a[9],complete:false),Fault.Cleanup); cases++;
            Reject("cleanup_wrong_collector",a=>a[9]=Change(a[9],actor:Actor.Unknown),Fault.Cleanup); cases++;
            Reject("child_still_alive",a=>a[9]=Change(a[9],exited:false),Fault.Cleanup); cases++;
            Reject("late_child",a=>a[9]=Change(a[9],descendants:false),Fault.Cleanup); cases++;
            Reject("not_synthetic",a=>a[2]=Change(a[2],synthetic:false),Fault.Protocol); cases++;
            Reject("duplicate_launch_no_retry",a=>a[3]=Change(a[2],ms:3),Fault.Protocol); cases++;
            Reject("unexpected_raw_code",a=>a[9]=Change(a[9],raw:0),Fault.Protocol); cases++;
            Reject("unknown_event",a=>a[4]=Change(a[4],kind:(Kind)999),Fault.Protocol); cases++;
            Reject("stdout_after_eof",a=>a[7]=Change(a[7],kind:Kind.Stdout),Fault.Stream); cases++;

            Receipt[] historic=Good(); historic[8]=Change(historic[8],raw:11);
            DiagnosticResult original=new LaunchCustodyDiagnostic().Review(historic);
            Require(original.RawExit==11 && original.CleanupComplete && original.Outcome=="HOLD","raw11_cleanup_pass");
            Denials(original,"raw11_cleanup_pass"); cases++;
            Receipt[] timeout=Good(); timeout[8]=R(Kind.Deadline,8000);
            timeout[9]=Change(timeout[9],ms:8001); timeout[10]=Change(timeout[10],ms:8002);
            timeout[11]=Change(timeout[11],ms:8003);
            DiagnosticResult timed=new LaunchCustodyDiagnostic().Review(timeout);
            Require(timed.RawExit==null && timed.ExitLabel=="RAW_EXIT=UNAVAILABLE" && timed.CleanupComplete &&
                timed.Outcome=="HOLD" && (timed.Faults&Fault.Deadline)!=0,"timeout_cleanup_pass");
            Denials(timed,"timeout_cleanup_pass"); cases++;
            timeout[9]=Change(timeout[9],exited:false);
            DiagnosticResult held=new LaunchCustodyDiagnostic().Review(timeout);
            Require(!held.CleanupComplete && (held.Faults&Fault.Cleanup)!=0,"timeout_cleanup_hold");
            Denials(held,"timeout_cleanup_hold"); cases++;

            Receipt[] duplicate=Good(); List<Receipt> expanded=new List<Receipt>(duplicate);
            expanded.Insert(9,Change(duplicate[8],raw:0)); expanded[8]=Change(expanded[8],raw:11);
            DiagnosticResult preserved=new LaunchCustodyDiagnostic().Review(expanded.ToArray());
            Require(preserved.RawExit==11 && preserved.Outcome=="HOLD","duplicate_cannot_overwrite_exit");
            Denials(preserved,"duplicate_cannot_overwrite_exit"); cases++;
            LaunchCustodyDiagnostic once=new LaunchCustodyDiagnostic(); once.Review(historic);
            DiagnosticResult replay=once.Review(Good());
            Require(replay.RawExit==11 && (replay.Faults&Fault.Replay)!=0 && replay.Outcome=="HOLD","sticky_replay");
            Denials(replay,"sticky_replay"); cases++;
            DiagnosticResult empty=new LaunchCustodyDiagnostic().Review(null);
            Require(empty.Outcome=="HOLD" && empty.RawExit==null,"empty"); Denials(empty,"empty"); cases++;
            DiagnosticResult excessive=new LaunchCustodyDiagnostic().Review(new Receipt[129]);
            Require(excessive.Outcome=="HOLD","event_bound"); Denials(excessive,"event_bound"); cases++;
            Receipt[] cap=Good(); cap[4]=Change(cap[4],text:new string('x',5000));
            DiagnosticResult bounded=new LaunchCustodyDiagnostic().Review(cap);
            Require(bounded.Stdout.Length==4096 && bounded.Outcome=="HOLD","bounded_prefix");
            Denials(bounded,"bounded_prefix"); cases++;
            return cases;
        }
    }
}
#else
#error P296_DEBUG_ISOLATED_SOURCE_ONLY_REQUIRED
#endif
