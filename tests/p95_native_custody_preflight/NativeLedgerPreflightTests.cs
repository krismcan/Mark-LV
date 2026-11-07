// P95 compiled native C# read-only tests of exact historical CustodyLedger.
// ONLY strings of public nonsecret hex test nonces; no actual credential reads.
using System;
using Nayeon.ByokC1;

internal static class NativeLedgerPreflightTests
{
    private static readonly string A = new string('a', 32);
    private static readonly string B = new string('b', 32);
    private static readonly string C = new string('c', 32);
    private static readonly string D = new string('d', 32);
    private static int passed, failed;

    private static void Require(bool ok, string reason)
    { if (!ok) throw new Exception("Read-only test failed: " + reason); }

    private static void Denied(Action action)
    {
        bool refused = false;
        try { action(); }
        catch (LedgerBlocked) { refused = true; }
        Require(refused, "expected structural LedgerBlocked");
    }

    private static LedgerReadout Observe(string j, string a, bool? pending)
    {
        return NativeLedgerPreflight.InspectUntrustedInputs(
            j, a, pending, true, true, true, true, true);
    }

    private static void Expect(LedgerReadout result, LedgerReadoutDisposition expected)
    {
        Require(result.Disposition == expected, "disposition mismatch");
        Require(!result.EffectPermitted, "effect not allowed");
        Require(!result.RetryPermitted, "retry not allowed");
        Require(!result.CredentialVerified, "not verified");
        Require(!result.RecoveryCleared, "not cleared");
        Require(!result.TrustedAuthorityGranted, "no authority");
        Require(!result.ToString().Contains("key"), "no secret message");
    }

    private static string Initial() { return CustodyLedger.CreateInitial(A); }
    private static string InFlight()
    { return CustodyLedger.AppendIntent(Initial(), LedgerOperation.Save, B); }
    private static string Committed()
    { return CustodyLedger.AppendTerminal(InFlight()); }
    private static string Deleted()
    {
        return CustodyLedger.AppendTerminal(
            CustodyLedger.AppendIntent(Committed(), LedgerOperation.Delete, C));
    }

    private static void Run(string name, Action action)
    {
        try { action(); passed++; Console.WriteLine("PASS " + name); }
        catch (Exception e) {
            failed++; Console.WriteLine("FAIL " + name + " " + e.GetType().Name);
        }
    }

    public static int Main()
    {
        Run("native-exact-genesis", () => {
            string j = Initial();
            Require(CustodyLedger.Decode(j).Length == 1, "initial sequence");
            Require(CustodyLedger.Verify(j, CustodyLedger.Anchor(j)) ==
                    LedgerPhase.Initial, "initial phase");
        });
        Run("native-exact-inflight", () => {
            string j = InFlight();
            Require(CustodyLedger.Decode(j).Length == 2, "inflight sequence");
            Require(CustodyLedger.Verify(j, CustodyLedger.Anchor(j)) ==
                    LedgerPhase.InFlight, "inflight phase");
        });
        Run("native-exact-terminal-unverified", () => {
            string j = Committed();
            Require(CustodyLedger.Decode(j).Length == 3, "terminal sequence");
            Require(CustodyLedger.Verify(j, CustodyLedger.Anchor(j)) ==
                    LedgerPhase.CommittedUnverified, "unverified phase");
        });
        Run("native-exact-delete-absent", () => {
            string j = Deleted();
            Require(CustodyLedger.Decode(j).Length == 5, "delete sequence");
            Require(CustodyLedger.Verify(j, CustodyLedger.Anchor(j)) ==
                    LedgerPhase.CommittedAbsent, "absent phase");
        });
        Run("native-replace-terminal-unverified", () => {
            string j = CustodyLedger.AppendTerminal(
                CustodyLedger.AppendIntent(Committed(), LedgerOperation.Replace, C));
            Require(CustodyLedger.Verify(j, CustodyLedger.Anchor(j)) ==
                    LedgerPhase.CommittedUnverified, "replace phase");
        });
        Run("native-inflight-never-retries", () => {
            string j = InFlight();
            Denied(() => CustodyLedger.AppendIntent(j, LedgerOperation.Save, C));
            Expect(Observe(j, CustodyLedger.Anchor(j), false),
                   LedgerReadoutDisposition.RecoveryRequired);
        });
        Run("native-terminal-cannot-repeat", () =>
            Denied(() => CustodyLedger.AppendTerminal(Committed())));
        Run("native-initial-cannot-finish", () =>
            Denied(() => CustodyLedger.AppendTerminal(Initial())));
        Run("native-replace-before-save-refused", () =>
            Denied(() => CustodyLedger.AppendIntent(
                Initial(), LedgerOperation.Replace, B)));
        Run("native-delete-before-save-refused", () =>
            Denied(() => CustodyLedger.AppendIntent(
                Initial(), LedgerOperation.Delete, B)));
        Run("native-duplicate-nonce-refused", () =>
            Denied(() => CustodyLedger.AppendIntent(
                Initial(), LedgerOperation.Save, A)));
        Run("native-initial-no-presence-not-authority", () =>
            Expect(Observe(Initial(), CustodyLedger.Anchor(Initial()), false),
                   LedgerReadoutDisposition.StructuralInitialUntrusted));
        Run("native-initial-unexpected-pending-recovery", () =>
            Expect(Observe(Initial(), CustodyLedger.Anchor(Initial()), true),
                   LedgerReadoutDisposition.RecoveryRequired));
        Run("native-saved-present-still-unverified", () =>
            Expect(Observe(Committed(), CustodyLedger.Anchor(Committed()), true),
                   LedgerReadoutDisposition.StructuralPendingUnverified));
        Run("native-saved-missing-credential-recovery", () =>
            Expect(Observe(Committed(), CustodyLedger.Anchor(Committed()), false),
                   LedgerReadoutDisposition.RecoveryRequired));
        Run("native-deleted-absent-still-unverified", () =>
            Expect(Observe(Deleted(), CustodyLedger.Anchor(Deleted()), false),
                   LedgerReadoutDisposition.StructuralAbsentUnverified));
        Run("native-deleted-but-present-recovery", () =>
            Expect(Observe(Deleted(), CustodyLedger.Anchor(Deleted()), true),
                   LedgerReadoutDisposition.RecoveryRequired));
        Run("native-unknown-pending-presence-recovery", () =>
            Expect(Observe(Committed(), CustodyLedger.Anchor(Committed()), null),
                   LedgerReadoutDisposition.RecoveryRequired));
        Run("native-no-journal-no-bootstrap", () =>
            Expect(Observe(null, null, false),
                   LedgerReadoutDisposition.RecoveryRequired));
        Run("native-missing-anchor-refused", () =>
            Expect(Observe(Committed(), null, true),
                   LedgerReadoutDisposition.RecoveryRequired));
        Run("native-wrong-anchor-refused", () =>
            Expect(Observe(Committed(), CustodyLedger.Anchor(Initial()), true),
                   LedgerReadoutDisposition.RecoveryRequired));
        Run("native-crlf-corruption-refused", () => {
            string j = Committed().Replace("\n", "\r\n");
            Expect(Observe(j, CustodyLedger.Anchor(Committed()), true),
                   LedgerReadoutDisposition.RecoveryRequired);
            Denied(() => CustodyLedger.Decode(j));
        });
        Run("native-missing-newline-refused", () => {
            string j = Committed().TrimEnd('\n');
            Denied(() => CustodyLedger.Decode(j));
        });
        Run("native-trailing-frame-junk-refused", () => {
            string j = Committed() + "junk";
            Denied(() => CustodyLedger.Decode(j));
        });
        Run("native-uppercase-nonce-refused", () => {
            string j = Initial().Replace(A, new string('A', 32));
            Denied(() => CustodyLedger.Decode(j));
        });
        Run("native-modified-frame-predecessor-refused", () => {
            string j = Committed();
            int offset = j.LastIndexOf('|');
            Require(offset >= 0, "predecessor exists");
            string mutated = j.Substring(0, offset + 1) +
                new string('0', 64) + "\n";
            Denied(() => CustodyLedger.Decode(mutated));
        });
        Run("native-recomputed-full-forgery-is-not-authority", () => {
            string j = CustodyLedger.CreateInitial(new string('f', 32));
            Require(CustodyLedger.Verify(j, CustodyLedger.Anchor(j)) ==
                    LedgerPhase.Initial, "forgery parses structurally");
            Expect(Observe(j, CustodyLedger.Anchor(j), false),
                   LedgerReadoutDisposition.StructuralInitialUntrusted);
        });
        Run("native-valid-prefix-rewind-still-no-authority", () => {
            string j = Committed();
            Require(CustodyLedger.Decode(j).Length == 3, "has history");
            string older = Initial();
            Require(CustodyLedger.Verify(older, CustodyLedger.Anchor(older)) ==
                    LedgerPhase.Initial, "rewind valid structurally");
            Expect(Observe(older, CustodyLedger.Anchor(older), false),
                   LedgerReadoutDisposition.StructuralInitialUntrusted);
        });
        Run("native-untrusted-service-principal-refused", () => {
            var result = NativeLedgerPreflight.InspectUntrustedInputs(
                Committed(), CustodyLedger.Anchor(Committed()), true,
                false, true, true, true, true);
            Expect(result, LedgerReadoutDisposition.Unavailable);
        });
        Run("native-untrusted-os-journal-refused", () => {
            var result = NativeLedgerPreflight.InspectUntrustedInputs(
                Committed(), CustodyLedger.Anchor(Committed()), true,
                true, false, true, true, true);
            Expect(result, LedgerReadoutDisposition.Unavailable);
        });
        Run("native-untrusted-os-anchor-refused", () => {
            var result = NativeLedgerPreflight.InspectUntrustedInputs(
                Committed(), CustodyLedger.Anchor(Committed()), true,
                true, true, false, true, true);
            Expect(result, LedgerReadoutDisposition.Unavailable);
        });
        Run("native-no-enrollment-witness-refused", () => {
            var result = NativeLedgerPreflight.InspectUntrustedInputs(
                Committed(), CustodyLedger.Anchor(Committed()), true,
                true, true, true, false, true);
            Expect(result, LedgerReadoutDisposition.Unavailable);
        });
        Run("native-uncleared-persistent-fault-refused", () => {
            var result = NativeLedgerPreflight.InspectUntrustedInputs(
                Committed(), CustodyLedger.Anchor(Committed()), true,
                true, true, true, true, false);
            Expect(result, LedgerReadoutDisposition.Unavailable);
        });
        Run("native-no-production-authority-even-when-claims-all-true", () =>
            Expect(Observe(Committed(), CustodyLedger.Anchor(Committed()), true),
                   LedgerReadoutDisposition.StructuralPendingUnverified));

        Console.WriteLine("P95_NATIVE_LEDGER_READONLY_PASSED=" + passed);
        Console.WriteLine("P95_NATIVE_LEDGER_READONLY_FAILED=" + failed);
        Console.WriteLine("P95_NATIVE_CREDENTIAL_EFFECTS=NONE");
        Console.WriteLine("P95_PRODUCTION_RELEASE=HOLD");
        return failed == 0 && passed == 34 ? 0 : 1;
    }
}
