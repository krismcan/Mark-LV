using System;
using System.IO;
using System.Runtime.CompilerServices;

[assembly: InternalsVisibleTo("P316.ServiceRecovery.Tests")]

namespace Nayeon.ByokC1.Service
{
    internal enum RecoveryObservation { Unknown, MissingLeaf, RecoveryRequired }

    // Metadata observations are not durable authority, authorization or race protection.
    internal static class ServiceRecoveryBoundary
    {
        internal const string Leaf = "NayeonV1ByokCustody.Recovery.v1";

        internal static void RequireDenialOnlyStart(Action verifyExecutingIdentity)
        {
            try
            {
                verifyExecutingIdentity();
                string profile = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData,
                    Environment.SpecialFolderOption.DoNotVerify);
                RecoveryObservation observation = ObserveProfile(profile);
                verifyExecutingIdentity();
                if (!AllowsDenialOnlyStart(observation)) throw new InvalidOperationException();
            }
            catch (Exception) { throw new InvalidOperationException("Recovery boundary refused; HOLD."); }
        }

        internal static bool AllowsDenialOnlyStart(RecoveryObservation observation)
        { return observation == RecoveryObservation.MissingLeaf; }

        // Parameterized observation exists for disposable metadata tests only. Startup supplies
        // only the fixed special-folder result; no caller path, flags or configuration.
        internal static RecoveryObservation ObserveProfile(string profile)
        {
            try
            {
                ValidatePath(profile);
                VerifyAncestors(profile);
                string child = Path.Combine(profile, Leaf);
                RecoveryObservation result;
                try { File.GetAttributes(child); result = RecoveryObservation.RecoveryRequired; }
                catch (FileNotFoundException) { result = RecoveryObservation.MissingLeaf; }
                // DirectoryNotFoundException is deliberately NOT absence evidence.
                VerifyAncestors(profile);
                if (result == RecoveryObservation.MissingLeaf)
                {
                    try { File.GetAttributes(child); return RecoveryObservation.RecoveryRequired; }
                    catch (FileNotFoundException) { }
                    VerifyAncestors(profile);
                }
                return result;
            }
            catch (Exception) { return RecoveryObservation.Unknown; }
        }

        private static void ValidatePath(string path)
        {
            if (String.IsNullOrEmpty(path) || path.Length < 3 ||
                !((path[0] >= 'A' && path[0] <= 'Z') || (path[0] >= 'a' && path[0] <= 'z')) ||
                path[1] != ':' || path[2] != '\\' || path.IndexOf('/') >= 0 ||
                path.IndexOf(':', 2) >= 0 || path.IndexOfAny(new[] { '*', '?', '\0' }) >= 0 ||
                !String.Equals(Path.GetFullPath(path), path, StringComparison.OrdinalIgnoreCase))
                throw new InvalidOperationException();
            foreach (string component in path.Substring(3).Split('\\'))
            {
                if (component.Length == 0 || component == "." || component == ".." ||
                    component.IndexOfAny(Path.GetInvalidFileNameChars()) >= 0 ||
                    component.TrimEnd(' ', '.').Length != component.Length)
                    throw new InvalidOperationException();
                string stem = component.Split('.')[0].ToUpperInvariant();
                if (stem == "CON" || stem == "PRN" || stem == "AUX" || stem == "NUL" ||
                    (stem.Length == 4 && (stem.StartsWith("COM", StringComparison.Ordinal) ||
                    stem.StartsWith("LPT", StringComparison.Ordinal)) &&
                    ("123456789\u00b9\u00b2\u00b3".IndexOf(stem[3]) >= 0)))
                    throw new InvalidOperationException();
            }
            if (new DriveInfo(path.Substring(0, 3)).DriveType != DriveType.Fixed)
                throw new InvalidOperationException();
        }

        private static void VerifyAncestors(string profile)
        {
            for (string current = profile; current != null; current = Path.GetDirectoryName(current))
            {
                FileAttributes attributes = File.GetAttributes(current);
                if ((attributes & FileAttributes.Directory) == 0 ||
                    (attributes & FileAttributes.ReparsePoint) != 0) throw new InvalidOperationException();
            }
        }
    }
}
