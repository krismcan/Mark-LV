// P99: compile ALL ELEVEN original unmodified P49 C# native service sources.
// Execute ONLY immutable admission REFUSALS with no BYOK_TEST symbol.
// No SCM registration/start, P/Invoke execution, WinCred reads/writes,
// credential blob, journal creation, HKLM access/mutation, or real key.
// The exact source SHA-256 is independently pinned before compilation.
// Do not repackage this harness as a credential-bearing installed service.
using System;
using System.Reflection;
using System.Runtime.Serialization;
using Nayeon.ByokC1;

internal static class P99FullOriginalNativeDenialTests
{
    private static int passed, failed;

    private static void Assert(bool ok)
    { if (!ok) throw new InvalidOperationException("P99 guard assertion failed"); }

    private static void Run(string name, Action test)
    {
        try { test(); passed++; Console.WriteLine("PASS " + name); }
        catch (Exception e)
        { failed++; Console.WriteLine("FAIL " + name + " " + e.GetType().Name); }
    }

    private static void ExpectBlocked(Action operation)
    {
        bool stopped = false;
        try { operation(); }
        catch (LedgerBlocked) { stopped = true; }
        Assert(stopped);
    }

    private static void BeforeAnyNativeAdapterCall()
    {
        // Contract invariant, not an authorization attempt: tests must throw
        // BEFORE calling a credential adapter if ANY release guard differs.
        Assert(!ServiceGate.LiveEligible());
        Assert(PendingServiceState.LegacyEffectEntryDisabled());
        Assert(PendingWinCredStore.NativeMutationAdmissionPending());
    }

    private static PendingServiceState InertStateWithoutConstruction()
    {
        // No constructor or protected object is invoked. This is an inert
        // instance solely to invoke the *actual original* method prologue.
        // Its native references remain null, and must NEVER be dereferenced.
        BeforeAnyNativeAdapterCall();
        return (PendingServiceState)FormatterServices.GetUninitializedObject(
            typeof(PendingServiceState));
    }

    private static void OnStartCannotActivate()
    {
        BeforeAnyNativeAdapterCall();
        using (CustodyService service = new CustodyService())
        {
            MethodInfo m=typeof(CustodyService).GetMethod(
                "OnStart", BindingFlags.NonPublic | BindingFlags.Instance);
            Assert(m != null);
            bool refused = false;
            try { m.Invoke(service, new object[] {new string[0]}); }
            catch (TargetInvocationException e)
            {
                refused = e.InnerException is InvalidOperationException &&
                    e.InnerException.Message == "Custody service is unavailable";
            }
            Assert(refused);
        }
    }

    internal static int Main()
    {
        // Assert the entire immutable-denial chain BEFORE optional exercises.
        BeforeAnyNativeAdapterCall();

        Run("full-native-linked-live-service-denied", () =>
            Assert(!ServiceGate.LiveEligible()));
        Run("full-native-service-name-fixed", () =>
            Assert(ServiceGate.ServiceName == "NayeonV1ByokCustody"));
        Run("full-native-executable-name-fixed", () =>
            Assert(ServiceGate.ExecutableName == "Nayeon.ByokC1.CustodyService.exe"));
        Run("full-native-service-onstart-refuses", OnStartCannotActivate);
        Run("full-native-service-onstart-refuses-repeat", OnStartCannotActivate);
        Run("full-native-request-null-refuses", () =>
            Assert(ServiceGate.HandleUntrustedRequest(null) == "UNAVAILABLE"));
        Run("full-native-request-fake-key-refuses", () =>
            Assert(ServiceGate.HandleUntrustedRequest("NOT_A_REAL_KEY") == "UNAVAILABLE"));
        Run("full-native-request-long-text-refuses", () =>
            Assert(ServiceGate.HandleUntrustedRequest(new String('x', 65536)) == "UNAVAILABLE"));
        Run("full-native-pure-helper-may-approve-only-its-claims", () =>
        {
            string exact=ServiceGate.ExpectedImage();
            Assert(ServiceGate.EligibleForService(exact,exact,true,true,true,true));
            Assert(!ServiceGate.LiveEligible());
        });
        Run("full-native-pure-helper-wrong-path-refuses", () =>
            Assert(!ServiceGate.EligibleForService(
                @"C:\Temp\untrusted.exe",ServiceGate.ExpectedImage(),true,true,true,true)));
        Run("full-native-installed-protected-state-construction-refused", () =>
        {
            BeforeAnyNativeAdapterCall();
            ExpectBlocked(() => PendingServiceState.ForInstalledService());
        });
        Run("full-native-legacy-effect-switch-disabled", () =>
            Assert(PendingServiceState.LegacyEffectEntryDisabled()));
        Run("full-native-wincred-mutation-switch-disabled", () =>
            Assert(PendingWinCredStore.NativeMutationAdmissionPending()));
        Run("full-native-pending-target-is-constant", () =>
            Assert(PendingWinCredStore.FixedTarget ==
                   "nayeon-v1/byok-c1/pending/openai"));
        Run("full-native-wincred-save-prologue-refuses-before-pinvoke", () =>
        {
            BeforeAnyNativeAdapterCall();
            var store = new PendingWinCredStore();
            // Dummy one-byte invalid payload. The first line of the
            // original method rejects it; it cannot reach CredWriteW.
            ExpectBlocked(() => store.SaveOrReplace(new byte[] {0x00}));
        });
        Run("full-native-wincred-delete-prologue-refuses-before-pinvoke", () =>
        {
            BeforeAnyNativeAdapterCall();
            var store = new PendingWinCredStore();
            ExpectBlocked(() => store.DeletePending());
        });
        Run("full-native-state-save-prologue-refuses-before-native-dependency", () =>
        {
            BeforeAnyNativeAdapterCall();
            PendingServiceState state=InertStateWithoutConstruction();
            ExpectBlocked(() => state.SaveOrReplace(new byte[] {0x00}));
        });
        Run("full-native-state-delete-prologue-refuses-before-native-dependency", () =>
        {
            BeforeAnyNativeAdapterCall();
            PendingServiceState state=InertStateWithoutConstruction();
            ExpectBlocked(() => state.DeletePending());
        });
        Run("full-native-native-mutation-guard-repeatably-stable", () =>
        {
            for(int i=0;i<100;i++) BeforeAnyNativeAdapterCall();
        });
        Run("full-native-no-effect-on-legacy-test-coordinator-presence", () =>
        {
            // The old coordinator remains linked but is deliberately NOT
            // invoked: P96 proved its caller-supplied dependency flaw.
            Assert(typeof(PendingCustodyTransaction).Assembly ==
                   typeof(PendingWinCredStore).Assembly);
            Assert(typeof(PendingCustodyTransaction).Assembly ==
                   typeof(CustodyService).Assembly);
            BeforeAnyNativeAdapterCall();
        });

        Console.WriteLine("P99_ORIGINAL_NATIVE_11_SOURCE_LINK=TRUE");
        Console.WriteLine("P99_ORIGINAL_NATIVE_DENIAL_TESTS_PASSED=" + passed);
        Console.WriteLine("P99_ORIGINAL_NATIVE_DENIAL_TESTS_FAILED=" + failed);
        Console.WriteLine("P99_P49_SERVICE_HOST_STILL_DISABLED=TRUE");
        Console.WriteLine("P99_P49_SERVICE_STATE_LEGACY_EFFECT_DISABLED=TRUE");
        Console.WriteLine("P99_P49_WINCRED_MUTATION_DISABLED=TRUE");
        Console.WriteLine("P99_NATIVE_CREDENTIAL_APIS_EXECUTED=NONE_BY_TEST");
        Console.WriteLine("P99_NATIVE_SERVICE_INSTALLED_OR_STARTED=NONE");
        Console.WriteLine("P99_P96_CONSENT_TO_EFFECT_DEFECT=OPEN");
        Console.WriteLine("P99_X86_APP_CONTROL_POLICY=BLOCKED_NOT_RETRIED");
        Console.WriteLine("P99_C1_PRODUCTION_RELEASE=HOLD");
        return failed == 0 && passed == 20 ? 0 : 1;
    }
}
