using System;
using System.IO;
using System.Linq;
using Nayeon.ByokC1.Service;

internal static class P316ServiceRecoveryTests
{
    private static void Check(bool value) { if (!value) throw new Exception("P316 assertion failed"); }
    private static void Observe(string profile, RecoveryObservation expected)
    {
        // Test harness snapshots only its fixture; invalid/missing paths have no snapshot.
        bool snapshot = expected != RecoveryObservation.Unknown && profile != null && Directory.Exists(profile);
        string[] entries = snapshot ? Directory.GetFileSystemEntries(profile) : null;
        DateTime written = snapshot ? Directory.GetLastWriteTimeUtc(profile) : default(DateTime);
        FileAttributes attributes = snapshot ? File.GetAttributes(profile) : default(FileAttributes);
        Check(ServiceRecoveryBoundary.ObserveProfile(profile) == expected);
        if (snapshot)
            Check(entries.SequenceEqual(Directory.GetFileSystemEntries(profile)) &&
                written == Directory.GetLastWriteTimeUtc(profile) && attributes == File.GetAttributes(profile));
    }
    private static void Source()
    {
        string root = Directory.GetCurrentDirectory();
        string service = Path.Combine(root, "src", "Nayeon.ByokC1.Service");
        string text = File.ReadAllText(Path.Combine(service, "CustodyService.cs"));
        int start = text.IndexOf("protected override void OnStart", StringComparison.Ordinal);
        int end = text.IndexOf("internal SyntheticTransactionResult", start, StringComparison.Ordinal);
        string body = text.Substring(start, end - start);
        int identity = body.IndexOf("VerifyExecutingIdentity();", StringComparison.Ordinal);
        int second = body.IndexOf("VerifyExecutingIdentity();", identity + 1, StringComparison.Ordinal);
        int recovery = body.IndexOf("ServiceRecoveryBoundary.RequireDenialOnlyStart(VerifyExecutingIdentity);", StringComparison.Ordinal);
        int begin = body.IndexOf("coordinator.BeginStart();", StringComparison.Ordinal);
        Check(identity >= 0 && second > identity && recovery > second && begin > recovery);
        foreach (string creation in new[] { "new SyntheticTransactionOwner(", "new SyntheticIngressServer(", "new StatusPipeServer(" })
            Check(body.IndexOf(creation, StringComparison.Ordinal) > begin);
        Check(body.Contains("catch (Exception)") && body.Contains("terminal = true;") &&
            body.Contains("ExitCode = 1;") && body.Contains("ClosePipes();") && body.Contains("coordinator.Fault();"));
        string helper = File.ReadAllText(Path.Combine(service, "ServiceRecoveryBoundary.cs"));
        foreach (string forbidden in new[] { "DllImport", "CredRead", "CredWrite", "ProtectedData", "File.Open", "File.Read", "File.Write",
            "Directory.Create", "Directory.Delete", "Enumerate", "GetEnvironmentVariable", "LocalSystem", "GetTempPath" })
            Check(!helper.Contains(forbidden));
        Check(helper.Contains("SpecialFolder.LocalApplicationData") && helper.Contains("SpecialFolderOption.DoNotVerify"));
        Check(helper.Split(new[] { "verifyExecutingIdentity();" }, StringSplitOptions.None).Length == 3);
        Check(!helper.Contains("catch (DirectoryNotFoundException)"));
    }
    private static int Main(string[] args)
    {
        string fixture = null;
        try
        {
            Check(args.Length == 0 && Environment.OSVersion.Platform == PlatformID.Win32NT);
            Source();
            foreach (RecoveryObservation value in new[] { RecoveryObservation.Unknown, RecoveryObservation.RecoveryRequired,
                (RecoveryObservation)(-1), (RecoveryObservation)99 })
                Check(!ServiceRecoveryBoundary.AllowsDenialOnlyStart(value));
            Check(ServiceRecoveryBoundary.AllowsDenialOnlyStart(RecoveryObservation.MissingLeaf));
            foreach (string invalid in new[] { null, "", "relative", "C:relative", "\\\\server\\share", "\\rooted", "C:\\a\\..\\b",
                "C:\\a.", "C:\\a ", "C:/a", "C:\\a:stream", "\\\\?\\C:\\a", "C:\\a\\\\b", "C:\\a\\*", "C:\\CON", "C:\\NUL.txt", "C:\\COM1", "C:\\LPT9.ext" })
                Observe(invalid, RecoveryObservation.Unknown);
            // Harness alone creates/deletes empty metadata fixtures. Product observer never mutates.
            fixture = Path.Combine(Path.GetTempPath(), "p316-" + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(fixture);
            string leaf = Path.Combine(fixture, ServiceRecoveryBoundary.Leaf);
            FileAttributes before = File.GetAttributes(fixture);
            Observe(fixture, RecoveryObservation.MissingLeaf);
            Check(Directory.GetFileSystemEntries(fixture).Length == 0 && File.GetAttributes(fixture) == before);
            Directory.CreateDirectory(leaf);
            Observe(fixture, RecoveryObservation.RecoveryRequired);
            Check(Directory.Exists(leaf) && Directory.GetFileSystemEntries(leaf).Length == 0);
            Directory.Delete(leaf);
            using (File.Create(leaf)) { }
            Observe(fixture, RecoveryObservation.RecoveryRequired);
            Check(new FileInfo(leaf).Length == 0 && Directory.GetFileSystemEntries(fixture).Single() == leaf);
            Observe(leaf, RecoveryObservation.Unknown);
            File.Delete(leaf);
            Observe(Path.Combine(fixture, "missing-parent"), RecoveryObservation.Unknown);
            Check(Directory.GetFileSystemEntries(fixture).Length == 0 && File.GetAttributes(fixture) == before);
            Directory.Delete(fixture); fixture = null;
            Console.WriteLine("P316 SERVICE RECOVERY TESTS PASS cleanup=verified"); return 0;
        }
        catch { Console.Error.WriteLine("P316 FAIL; HOLD"); return 1; }
        finally
        {
            // Only this newly created immediate fixture and its known empty leaf are cleanup targets.
            if (fixture != null)
            {
                string leaf = Path.Combine(fixture, ServiceRecoveryBoundary.Leaf);
                if (File.Exists(leaf)) File.Delete(leaf);
                if (Directory.Exists(leaf)) Directory.Delete(leaf);
                if (Directory.Exists(fixture)) Directory.Delete(fixture);
            }
        }
    }
}
