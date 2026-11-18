#if !DEBUG || !C1_P272_DEVELOPMENT_ONLY || !C1_REVIEW_ISOLATED_ASSEMBLY
#error P272_TESTS_ISOLATED_DEVELOPMENT_REQUIRED
#endif
using System;
using System.IO;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Security.AccessControl;
using System.Security.Cryptography;
using System.Security.Principal;
using System.ServiceProcess;
using System.Text;
using System.Threading;
using Nayeon.ByokC1;
using Nayeon.ByokC1.P270Development;
using Nayeon.ByokC1.P271Development;
using Nayeon.ByokC1.P272Development;

internal static class P272OsCustodyAdmissionTests
{
    private static int cases, assertions;
    private static string current = "hosted-entry";
    private static void Check(bool value)
    { Interlocked.Increment(ref assertions); if (!value) throw new Exception("P272_ASSERT"); }
    private static void Run(string name, Action test)
    { current = name; test(); cases++; Console.WriteLine("PASS " + name); }
    private static void Block(Action test)
    { bool refused = false; try { test(); } catch (LedgerBlocked) { refused = true; } Check(refused); }
    private static void Denied(CustodyAdmissionResult result)
    {
        Check(!result.ProductionEligible && !result.RealKeyEligible && !result.MayInvokeWinCred);
        Check(result.Required.IndependentMonotonicAuthority == DependencyState.NotWired &&
            result.Required.AuthenticatedExactOperationConsent == DependencyState.NotWired &&
            result.Required.QualifiedPrincipalDecision == DependencyState.NotValidated &&
            result.Required.IsolatedRunningTokenAndSigner == DependencyState.NotValidated &&
            result.Required.ProtectedStoreRoot == DependencyState.NotValidated &&
            result.Required.CustodyFreshness == DependencyState.NotValidated &&
            result.Observation.RunningIdentityProof == DependencyState.NotValidated);
        Check(result.Observation.ServiceName == ServiceGate.ServiceName);
        Check(result.Observation.DerivedVirtualAccount == "NT SERVICE\\" + ServiceGate.ServiceName);
    }
    private sealed class Scope : IDisposable
    {
        internal readonly string Root = Path.Combine(Path.GetTempPath(), "nayeon-p270-" + Guid.NewGuid().ToString("N"));
        internal Scope()
        {
            Check(!Directory.Exists(Root));
            SecurityIdentifier sid = WindowsIdentity.GetCurrent().User;
            DirectorySecurity acl = new DirectorySecurity();
            acl.SetOwner(sid); acl.SetAccessRuleProtection(true, false);
            acl.AddAccessRule(new FileSystemAccessRule(sid, FileSystemRights.FullControl,
                InheritanceFlags.ContainerInherit | InheritanceFlags.ObjectInherit,
                PropagationFlags.None, AccessControlType.Allow));
            Directory.CreateDirectory(Root, acl);
        }
        public void Dispose()
        {
            Check(Path.GetDirectoryName(Root).TrimEnd('\\') == Path.GetTempPath().TrimEnd('\\'));
            Check((File.GetAttributes(Root) & FileAttributes.ReparsePoint) == 0);
            foreach (string path in Directory.GetFiles(Root)) File.Delete(path);
            Directory.Delete(Root, false);
        }
    }
    private static void Account(string account, bool expected)
    {
        int header = Marshal.SizeOf(typeof(P261ScmReadOnlyAdmission.QueryServiceConfig));
        Check(header == (IntPtr.Size == 8 ? 64 : 36));
        IntPtr buffer = Marshal.AllocHGlobal(512);
        try
        {
            bool match;
            var config = new P261ScmReadOnlyAdmission.QueryServiceConfig();
            config.ServiceStartName = IntPtr.Add(buffer, header);
            Marshal.StructureToPtr(config, buffer, false);
            for (int i = 0; i < account.Length; i++) Marshal.WriteInt16(buffer, header + i * 2, (short)account[i]);
            Marshal.WriteInt16(buffer, header + account.Length * 2, 0);
            Check(P261ScmReadOnlyAdmission.TryReadAccountMatch(buffer, 512, out match) && match == expected);
            config.ServiceStartName = IntPtr.Add(buffer, header + 1);
            Marshal.StructureToPtr(config, buffer, false);
            Check(!P261ScmReadOnlyAdmission.TryReadAccountMatch(buffer, 512, out match));
            Check(!P261ScmReadOnlyAdmission.TryReadAccountMatch(buffer, 8193, out match));
            Check(!P261ScmReadOnlyAdmission.TryReadAccountMatch(buffer, header - 1, out match));
            Check(!P261ScmReadOnlyAdmission.TryReadAccountMatch(IntPtr.Zero, 512, out match));
            config.ServiceStartName = IntPtr.Add(buffer, header);
            Marshal.StructureToPtr(config, buffer, false);
            for (int i = header; i < 512; i += 2) Marshal.WriteInt16(buffer, i, 65);
            Check(!P261ScmReadOnlyAdmission.TryReadAccountMatch(buffer, 512, out match));
        }
        finally { Marshal.FreeHGlobal(buffer); }
    }
    // A same-user writer can construct either valid history with the same DPAPI
    // scope/entropy. This is a counterexample, never an authority implementation.
    private static void ReplaySameUser(Scope scope, string name, string value)
    {
        byte[] entropy = Encoding.UTF8.GetBytes("NAYEON:P270:DISPOSABLE-CUSTODY:V1:" +
            WindowsIdentity.GetCurrent().User.Value + ":" + scope.Root + ":" + name);
        byte[] plain = Encoding.UTF8.GetBytes(value);
        try
        {
            byte[] blob = ProtectedData.Protect(plain, entropy, DataProtectionScope.CurrentUser);
            using (var file = new FileStream(Path.Combine(scope.Root, name), FileMode.Truncate, FileAccess.Write, FileShare.None))
            { byte[] length = BitConverter.GetBytes(blob.Length); file.Write(length, 0, 4); file.Write(blob, 0, blob.Length); file.Flush(true); }
        }
        finally { Array.Clear(plain, 0, plain.Length); }
    }
    public static int Main()
    {
        try
        {
            OsBoundCustodyAdmission.RequireHostedTests();
            using (var deadline = new Timer(delegate(object ignored) {
                Console.Error.WriteLine("P272_HOLD DEADLINE"); Environment.Exit(124);
            }, null, 55000, Timeout.Infinite))
            using (var owner = OsBoundCustodyAdmission.CreateReadOnly())
            {
                Run("real-scm-missing-no-service-created", () => {
                    var result = owner.AttemptProduction(CustodyOperation.Save); Denied(result);
                    Check(result.Observation.Status == ScmSampleState.Missing && result.Observation.ServiceAbsentInBothConfigurationSamples);
                    Check(owner.TestEffects == 0);
                });
                foreach (CustodyOperation op in new[] { CustodyOperation.Save, CustodyOperation.Replace, CustodyOperation.Delete, (CustodyOperation)999 })
                {
                    CustodyOperation selected = op;
                    Run("operation-denied-" + op, () => {
                        var result = owner.AttemptProduction(selected); Denied(result);
                        Check(result.Operation == selected && result.Decision == (selected == (CustodyOperation)999 ?
                            AdmissionDecision.DeniedUnknownOperation : AdmissionDecision.DeniedDevelopmentAssembly));
                    });
                }
                Run("wrong-service-name", () => Account("NT SERVICE\\NayeonByokCustody", false));
                Run("LocalSystem-conflict", () => {
                    Account("LocalSystem", false);
                    Check(!ServiceGate.EligibleForService("x", "x", false, true, true, true));
                    Denied(owner.AttemptProduction(CustodyOperation.Save));
                });
                Run("derived-name-missing-isolated-token", () => {
                    Account("NT SERVICE\\" + ServiceGate.ServiceName, true);
                    Check(P261ScmReadOnlyAdmission.ClassifyConfiguration(true, 3) == P261ScmStatus.ConfigObserved);
                    Denied(owner.AttemptProduction(CustodyOperation.Save));
                });
                Run("restricted-SID-semantics-malformed-config", () => {
                    foreach (uint sid in new uint[] { 0, 1, 2, 3, UInt32.MaxValue })
                        Check(P261ScmReadOnlyAdmission.ClassifyConfiguration(true, sid) == (sid == 3 ?
                            P261ScmStatus.ConfigObserved : sid == 0 || sid == 1 ? P261ScmStatus.Mismatch : P261ScmStatus.MalformedBuffer));
                });
                Run("query-denied-resize-delete-races", () => {
                    foreach (int error in new[] { 5, 1060, 122, 1072, 6 })
                        Check(OsCustodyObservation.ClassifyError(error) == (error == 5 ? ScmSampleState.Denied :
                            error == 1060 ? ScmSampleState.Missing : ScmSampleState.Unverified));
                    var missing = new P261ScmEvidence(P261ScmStatus.Missing, false, false, false, null);
                    var config = new P261ScmEvidence(P261ScmStatus.ConfigObserved, true, true, true, 3);
                    Check(OsCustodyObservation.ClassifySamples(missing, config, ScmSampleState.Sampled, null, null) == ScmSampleState.Changed);
                    Check(OsCustodyObservation.ClassifySamples(config, config, ScmSampleState.Sampled,
                        ServiceControllerStatus.Running, ServiceControllerStatus.Stopped) == ScmSampleState.Changed);
                    Check(OsCustodyObservation.ClassifySamples(config, config, ScmSampleState.Sampled,
                        (ServiceControllerStatus)999, (ServiceControllerStatus)999) == ScmSampleState.Unverified);
                });
                Run("parallel-claimants-cannot-promote", () => {
                    Exception failure = null; object sync = new object(); Thread[] threads = new Thread[8];
                    for (int i = 0; i < threads.Length; i++)
                    {
                        int selected = i;
                        threads[i] = new Thread(delegate() {
                            try {
                                var claim = P261ScmReadOnlyAdmission.RefuseUntrustedClaim(selected % 2 == 0 ?
                                    "NT SERVICE\\" + ServiceGate.ServiceName : "S-1-5-18", true);
                                Check(!claim.EffectAllowed && !claim.RealKeyEligible);
                                Denied(owner.AttemptProduction(CustodyOperation.Save));
                            } catch (Exception e) { lock (sync) { failure = e; } }
                        });
                        threads[i].IsBackground = true; threads[i].Start();
                    }
                    foreach (Thread thread in threads) Check(thread.Join(5000));
                    Check(failure == null && owner.TestEffects == 0);
                });
                Run("consent-provenance-environment-no-opt-in", () => {
                    const string name = "P272_PRODUCTION_APPROVED"; string prior = Environment.GetEnvironmentVariable(name);
                    try { Environment.SetEnvironmentVariable(name, "1"); Denied(owner.AttemptProduction(CustodyOperation.Delete)); }
                    finally { Environment.SetEnvironmentVariable(name, prior); }
                    Check(typeof(OsBoundCustodyAdmission).GetConstructors().Length == 0);
                    foreach (MethodInfo method in typeof(OsBoundCustodyAdmission).GetMethods(BindingFlags.Public | BindingFlags.Instance | BindingFlags.Static | BindingFlags.DeclaredOnly))
                        foreach (ParameterInfo parameter in method.GetParameters()) Check(parameter.ParameterType == typeof(CustodyOperation));
                });
                Run("actual-P271-owned-production-denial-zero-effects", () => {
                    Check(typeof(DurableDevelopmentBridge).IsNotPublic);
                    foreach (MethodInfo method in typeof(DurableDevelopmentBridge).GetMethods(BindingFlags.Public | BindingFlags.Instance | BindingFlags.Static | BindingFlags.DeclaredOnly))
                        Check(method.Name == "Dispose");
                    using (var scope = new Scope()) using (var live = OsBoundCustodyAdmission.TestOnlyCreate(scope.Root, LedgerOperation.Save))
                    {
                        Denied(live.AttemptProduction(CustodyOperation.Save)); Check(live.TestEffects == 0);
                        Check(live.TestOnlySubmit() == CustodyOutcome.StoredUnverified && live.TestEffects == 1);
                        Denied(live.AttemptProduction(CustodyOperation.Replace)); Check(live.TestEffects == 1);
                    }
                });
                Run("uncertain-custody-zero-effects", () => {
                    using (var scope = new Scope()) using (var live = OsBoundCustodyAdmission.TestOnlyCreate(scope.Root, LedgerOperation.Save))
                    {
                        live.TestUntrust(); Denied(live.AttemptProduction(CustodyOperation.Save));
                        Check(live.TestOnlySubmit() == CustodyOutcome.RecoveryRequired && live.TestEffects == 0);
                    }
                });
                Run("same-user-rollback-equivocation-stale-restart", () => {
                    using (var scope = new Scope())
                    {
                        string oldJournal, oldAnchor;
                        using (var witness = new DurableWitness(scope.Root, true))
                        {
                            oldJournal = witness.ReadJournal(); oldAnchor = witness.ReadAnchor();
                            string next = CustodyLedger.AppendIntent(oldJournal, LedgerOperation.Save, CustodyLedger.NewNonce());
                            witness.WriteJournal(oldJournal, next); witness.WriteAnchor(oldAnchor, CustodyLedger.Anchor(next));
                            Check(witness.InspectConsistent() && witness.ReadJournal() != oldJournal);
                        }
                        ReplaySameUser(scope, DurableWitness.JournalName, oldJournal);
                        ReplaySameUser(scope, DurableWitness.AnchorName, oldAnchor);
                        using (var reopened = new DurableWitness(scope.Root, false))
                            Check(reopened.InspectConsistent() && reopened.RecoveryRequired && reopened.ReadJournal() == oldJournal);
                        Denied(owner.AttemptProduction(CustodyOperation.Save));
                        Block(() => { using (var ignored = OsBoundCustodyAdmission.TestOnlyCreate(scope.Root, LedgerOperation.Save)) {} });
                    }
                });
                Run("hosted-synthetic-factory-refusal", () => {
                    string prior = Environment.GetEnvironmentVariable("P272_HOSTED_DISPOSABLE");
                    try { Environment.SetEnvironmentVariable("P272_HOSTED_DISPOSABLE", null); Block(() => OsBoundCustodyAdmission.TestOnlyCreate(null, LedgerOperation.Save)); }
                    finally { Environment.SetEnvironmentVariable("P272_HOSTED_DISPOSABLE", prior); }
                    Denied(owner.AttemptProduction(CustodyOperation.Save));
                });
                Run("final-missing-no-created-service", () => {
                    var result = owner.AttemptProduction(CustodyOperation.Save); Denied(result);
                    Check(result.Observation.Status == ScmSampleState.Missing && result.Observation.ServiceAbsentInBothConfigurationSamples && owner.TestEffects == 0);
                });
                Console.WriteLine("P272_ADMISSION=PASS CASES=" + cases + " ASSERTIONS=" + assertions + " BITS=" + (IntPtr.Size * 8));
                Console.WriteLine("P272_PRODUCTION=HOLD REAL_KEYS=NO_GO P76=HOLD FULL_PRODUCT=0/3");
                return 0;
            }
        }
        catch (Exception error)
        { Console.Error.WriteLine("P272_HOLD=" + error.GetType().Name + " CASE=" + current); return 1; }
    }
}
