// P221: no-secret original P96 coordinator fake-only review experiments.
// A passing test of this fixture shows only that one application monitor
// can serialize its OWN revoke vs the old fake effect. The original P96
// coordinator and independently reachable P132 Python route are NOT fixed.
// No CredRead/CredWrite/CredDelete, P/Invoke, service install, IPC or keys.
#if !C1_REVIEW_ISOLATED_ASSEMBLY || !C1_SYNTHETIC_TEST
#error P221 original P96 race comparison is an isolated native test only
#endif
using System;
using System.Threading;

namespace Nayeon.ByokC1
{
    internal static class P221OriginalP96LinearizerTests
    {
        private static int passed, failed;
        private static void Require(bool condition, string why)
        {
            if (!condition) throw new InvalidOperationException(why);
        }
        private static void Run(string name, Action action)
        {
            try
            {
                action();
                ++passed;
                Console.WriteLine("PASS " + name);
            }
            catch (Exception ex)
            {
                ++failed;
                Console.WriteLine("FAIL " + name + " " + ex.GetType().Name);
            }
        }
        private static void DuringFakeDispatch(string name, Action<P221OriginalP96ReviewLinearizer> transition)
        {
            Run(name, () =>
            {
                var actor = new P221OriginalP96ReviewLinearizer();
                using (var entered = new ManualResetEvent(false))
                using (var release = new ManualResetEvent(false))
                using (var revokeStarted = new ManualResetEvent(false))
                using (var revokeCommitted = new ManualResetEvent(false))
                {
                    CustodyOutcome effectResult = CustodyOutcome.Denied;
                    Exception effectError = null;
                    Exception revokeError = null;
                    Thread effect = new Thread(() =>
                    {
                        try { effectResult = actor.AttemptFakeSave(entered, release); }
                        catch (Exception e) { effectError = e; }
                    });
                    Thread revoker = new Thread(() =>
                    {
                        try
                        {
                            revokeStarted.Set();
                            transition(actor);
                            revokeCommitted.Set();
                        }
                        catch (Exception e) { revokeError = e; }
                    });
                    effect.IsBackground = true;
                    revoker.IsBackground = true;
                    effect.Start();
                    bool enteredBeforeRevoke = entered.WaitOne(2000);
                    if (!enteredBeforeRevoke)
                    {
                        release.Set();
                        effect.Join(2500);
                        throw new InvalidOperationException("Fake effect did not enter gate");
                    }
                    revoker.Start();
                    bool attemptBegan = revokeStarted.WaitOne(2000);
                    bool revokePrematurelyCommitted = revokeCommitted.WaitOne(80);
                    release.Set(); // always unblock before joining both threads
                    Require(effect.Join(2500), "fake effect thread did not finish");
                    Require(revoker.Join(2500), "revoke thread did not finish");
                    Require(attemptBegan, "revocation thread not started");
                    Require(!revokePrematurelyCommitted, "revocation committed across active gate");
                    Require(effectError == null && revokeError == null, "thread fault");
                    Require(effectResult == CustodyOutcome.RecoveryRequired,
                            "test cannot claim physical stored success");
                    Require(actor.FakeEffects == 1, "the original fake-only effect did not happen");
                    Require(actor.FakeEffectsAfterCommittedRevoke == 0,
                            "effect after committed revoke");
                    Require(actor.RecoveryRequired, "sticky unknown/closed outcome required");
                    Require(actor.AttemptFakeSave() == CustodyOutcome.Denied, "replay after effect");
                }
            });
        }

        public static int Main()
        {
            Run("P221-original-P96-fake-effect-under-monitor-returns-RECOVERY", () =>
            {
                var actor = new P221OriginalP96ReviewLinearizer();
                Require(actor.AttemptFakeSave() == CustodyOutcome.RecoveryRequired,
                        "not an unverified key success");
                Require(actor.FakeEffects == 1, "original P96 fixture was actually executed");
                Require(actor.FakeEffectsAfterCommittedRevoke == 0, "unexpected revoke");
                Require(actor.RecoveryRequired, "recovery latch");
                Require(actor.AttemptCount == 1, "single attempt");
            });
            Run("P221-revoke-wins-before-effect-zero-original-fake-effects", () =>
            {
                var actor = new P221OriginalP96ReviewLinearizer();
                actor.Revoke();
                Require(actor.IsRevoked, "revoke committed");
                Require(actor.AttemptFakeSave() == CustodyOutcome.Denied, "early revoke did not deny");
                Require(actor.FakeEffects == 0, "effect after committed revoke");
                Require(actor.AttemptCount == 0, "no admitted attempt");
            });
            Run("P221-stop-wins-before-effect-zero-original-fake-effects", () =>
            {
                var actor = new P221OriginalP96ReviewLinearizer();
                actor.Stop();
                Require(actor.IsStopped && actor.IsRevoked, "stop must revoke");
                Require(actor.AttemptFakeSave() == CustodyOutcome.Denied, "stopped");
                Require(actor.FakeEffects == 0, "effect after stop");
            });
            Run("P221-fault-wins-before-effect-zero-original-fake-effects", () =>
            {
                var actor = new P221OriginalP96ReviewLinearizer();
                actor.Fault();
                Require(actor.AttemptFakeSave() == CustodyOutcome.RecoveryRequired,
                        "fault must remain sticky");
                Require(actor.FakeEffects == 0, "effect after fault");
                Require(actor.RecoveryRequired, "recovery latch after fault");
            });
            Run("P221-replay-refused-after-one-original-fake-effect", () =>
            {
                var actor = new P221OriginalP96ReviewLinearizer();
                Require(actor.AttemptFakeSave() == CustodyOutcome.RecoveryRequired,
                        "first attempt uncertain");
                for (int i = 0; i < 9; ++i)
                    Require(actor.AttemptFakeSave() == CustodyOutcome.Denied, "one-use consumed");
                Require(actor.FakeEffects == 1 && actor.AttemptCount == 1, "one fake effect total");
            });
            Run("P221-untrusted-original-fake-journal-never-permits-effect", () =>
            {
                var actor = new P221OriginalP96ReviewLinearizer();
                actor.MakeFakeCustodyUntrustedBeforeAttempt();
                Require(actor.AttemptFakeSave() == CustodyOutcome.RecoveryRequired,
                        "untrusted state must not become real success");
                Require(actor.FakeEffects == 0, "untrusted fixture used effect");
                Require(actor.RecoveryRequired, "uncertain state remains held");
            });
            Run("P221-original-fake-effect-throws-uncertainty-and-no-retry", () =>
            {
                var actor = new P221OriginalP96ReviewLinearizer();
                actor.MakeFakeEffectUncertainBeforeAttempt();
                Require(actor.AttemptFakeSave() == CustodyOutcome.RecoveryRequired,
                        "fake exception must never claim success");
                Require(actor.FakeEffects == 1, "fake effect might have occurred");
                Require(actor.AttemptFakeSave() == CustodyOutcome.Denied, "no retry after uncertain");
            });
            Run("P221-test-signal-timeout-no-fake-effect-recovery", () =>
            {
                var actor = new P221OriginalP96ReviewLinearizer();
                using (var neverSignalled = new ManualResetEvent(false))
                {
                    Require(actor.AttemptFakeSave(null, neverSignalled) ==
                            CustodyOutcome.RecoveryRequired, "timeout must hold");
                }
                Require(actor.FakeEffects == 0, "timeout before effect");
                Require(actor.AttemptFakeSave() == CustodyOutcome.Denied, "no retry after timeout");
            });
            DuringFakeDispatch("P221-revoke-during-effect-must-linearize-after-not-before",
                actor => actor.Revoke());
            DuringFakeDispatch("P221-stop-during-effect-must-linearize-after-not-before",
                actor => actor.Stop());
            DuringFakeDispatch("P221-fault-during-effect-must-linearize-after-not-before",
                actor => actor.Fault());
            Run("P221-no-privileged-consent-service-store-or-code-integrity-granted", () =>
            {
                var actor = new P221OriginalP96ReviewLinearizer();
                Require(!actor.ActualTrustedConsentIssuerAvailable &&
                        !actor.ServiceAccountStoreVerified &&
                        !actor.OriginalP96ProductionFixImplemented &&
                        !actor.NativeCredentialEffectEnabled &&
                        !actor.CodeIntegrityReleaseApproved &&
                        !actor.ProductionReleaseEligible,
                        "review fixture must never mint Windows service authority");
            });
            Run("P221-native-review-signature-has-no-credential-candidate-parameter", () =>
            {
                var method = typeof(P221OriginalP96ReviewLinearizer).GetMethod(
                    "AttemptFakeSave",
                    System.Reflection.BindingFlags.NonPublic |
                    System.Reflection.BindingFlags.Instance);
                Require(method != null, "test method absent");
                var ps = method.GetParameters();
                Require(ps.Length == 2 &&
                        ps[0].ParameterType == typeof(ManualResetEvent) &&
                        ps[1].ParameterType == typeof(ManualResetEvent),
                        "unexpected arbitrary effect or key input added");
            });
            Console.WriteLine("P221_ORIGINAL_P96_FAKE_COORDINATOR_REVIEW_PASSED=" + passed);
            Console.WriteLine("P221_ORIGINAL_P96_FAKE_COORDINATOR_REVIEW_FAILED=" + failed);
            Console.WriteLine("P221_P96_ORIGINAL_SECURITY_RACE=STILL_OPEN");
            Console.WriteLine("P221_REVIEW_MONITOR=TEST_ONLY_NOT_ACTUAL_SERVICE_BOUNDARY");
            Console.WriteLine("P221_REAL_NATIVE_CREDENTIAL_EFFECTS=NONE");
            Console.WriteLine("P221_QUALIFIED_SECURITY_APPROVAL=NOT_RECEIVED");
            Console.WriteLine("P221_REAL_KEY=NO_GO");
            Console.WriteLine("P221_C1_PRODUCTION_RELEASE=HOLD");
            return failed == 0 && passed == 13 ? 0 : 1;
        }
    }
}
