#if !DEBUG || RELEASE || !C1_REVIEW_ISOLATED_ASSEMBLY || !C1_P292_EPHEMERAL_SCM_ONLY
#error P292_DEBUG_ISOLATED_EPHEMERAL_ONLY
#endif
using System;
using System.Runtime.InteropServices;
using System.Security.Principal;
using System.Text;
using System.Text.RegularExpressions;

// Independent READ-ONLY test runner. No ServiceBase or SCM mutation imports.
// Kernel observations never become a product admission/credential capability.
internal static class P292ServiceIdentityProbe
{
    internal static bool ClientAdmissionAllowed { get { return false; } }
    internal static bool CredentialEffectAllowed { get { return false; } }
    internal static bool ApprovedServiceProvenance { get { return false; } }
    internal static bool ProductionReleaseAllowed { get { return false; } }

    [StructLayout(LayoutKind.Sequential)]
    private struct Luid { internal uint Low; internal int High; }
    [StructLayout(LayoutKind.Sequential)]
    private struct Statistics
    {
        internal Luid TokenId, AuthenticationId;
        internal long Expiration;
        internal uint Type, Level, Charged, Available, Groups, Privileges;
        internal Luid ModifiedId;
    }
    [StructLayout(LayoutKind.Sequential)]
    private struct SidEntry { internal IntPtr Sid; internal uint Attributes; }
    [StructLayout(LayoutKind.Sequential)]
    private struct GroupHeader { internal uint Count; internal SidEntry First; }
    [StructLayout(LayoutKind.Sequential, Pack = 4)]
    private struct Status
    {
        internal uint Type, State, Controls, Win32Exit, SpecificExit, Checkpoint, Hint, Pid, Flags;
    }
    [StructLayout(LayoutKind.Sequential)]
    private struct Config
    {
        internal uint Type, Start, Error;
        internal IntPtr Binary, Group;
        internal uint Tag;
        internal IntPtr Dependencies, Account, Display;
    }
    private sealed class Snapshot
    {
        internal SecurityIdentifier User;
        internal Statistics Stats;
        internal uint Session;
        internal string Restricted; // Private canonical byte evidence; never output.
    }
    [DllImport("advapi32.dll", CharSet = CharSet.Unicode, ExactSpelling = true, SetLastError = true)]
    private static extern IntPtr OpenSCManagerW(string machine, string database, uint access);
    [DllImport("advapi32.dll", CharSet = CharSet.Unicode, ExactSpelling = true, SetLastError = true)]
    private static extern IntPtr OpenServiceW(IntPtr manager, string name, uint access);
    [DllImport("advapi32.dll", ExactSpelling = true, SetLastError = true)]
    private static extern bool CloseServiceHandle(IntPtr handle);
    [DllImport("advapi32.dll", ExactSpelling = true, SetLastError = true)]
    private static extern bool QueryServiceStatusEx(IntPtr service, uint level, out Status status, uint size, out uint needed);
    [DllImport("advapi32.dll", CharSet = CharSet.Unicode, ExactSpelling = true, SetLastError = true)]
    private static extern bool QueryServiceConfigW(IntPtr service, IntPtr buffer, uint size, out uint needed);
    [DllImport("advapi32.dll", CharSet = CharSet.Unicode, ExactSpelling = true, SetLastError = true)]
    private static extern bool QueryServiceConfig2W(IntPtr service, uint level, IntPtr buffer, uint size, out uint needed);
    [DllImport("kernel32.dll", ExactSpelling = true, SetLastError = true)]
    private static extern IntPtr OpenProcess(uint access, bool inherit, uint pid);
    [DllImport("kernel32.dll", ExactSpelling = true)]
    private static extern IntPtr GetCurrentProcess();
    [DllImport("kernel32.dll", ExactSpelling = true)]
    private static extern IntPtr GetCurrentThread();
    [DllImport("kernel32.dll", ExactSpelling = true, SetLastError = true)]
    private static extern bool CloseHandle(IntPtr handle);
    [DllImport("kernel32.dll", ExactSpelling = true, SetLastError = true)]
    private static extern bool GetProcessTimes(IntPtr process, out long creation, out long exit, out long kernel, out long user);
    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, ExactSpelling = true, SetLastError = true)]
    private static extern bool QueryFullProcessImageNameW(IntPtr process, uint flags, StringBuilder name, ref uint size);
    [DllImport("kernel32.dll", ExactSpelling = true, SetLastError = true)]
    private static extern uint WaitForSingleObject(IntPtr handle, uint milliseconds);
    [DllImport("advapi32.dll", ExactSpelling = true, SetLastError = true)]
    private static extern bool OpenProcessToken(IntPtr process, uint access, out IntPtr token);
    [DllImport("advapi32.dll", ExactSpelling = true, SetLastError = true)]
    private static extern bool OpenThreadToken(IntPtr thread, uint access, bool openAsSelf, out IntPtr token);
    [DllImport("advapi32.dll", ExactSpelling = true, SetLastError = true)]
    private static extern bool GetTokenInformation(IntPtr token, int kind, IntPtr buffer, uint size, out uint returned);
    [DllImport("advapi32.dll", ExactSpelling = true, SetLastError = true)]
    private static extern bool IsTokenRestricted(IntPtr token);

    private static void Demand(bool value) { if (!value) throw new InvalidOperationException(); }
    private static void Layouts()
    {
        Demand(IntPtr.Size == 4 || IntPtr.Size == 8);
        Demand(Marshal.SizeOf(typeof(Statistics)) == 56 && Marshal.SizeOf(typeof(Status)) == 36);
        Demand(Marshal.SizeOf(typeof(Config)) == (IntPtr.Size == 8 ? 64 : 36));
        Demand(Marshal.OffsetOf(typeof(Config), "Account").ToInt32() == (IntPtr.Size == 8 ? 48 : 28));
        Demand(Marshal.SizeOf(typeof(SidEntry)) == (IntPtr.Size == 8 ? 16 : 8));
        Demand(Marshal.OffsetOf(typeof(GroupHeader), "First").ToInt32() == (IntPtr.Size == 8 ? 8 : 4));
        Demand(Marshal.OffsetOf(typeof(Statistics), "ModifiedId").ToInt32() == 48);
    }
    private static void NoThreadToken()
    {
        IntPtr token;
        bool opened = OpenThreadToken(GetCurrentThread(), 8, true, out token);
        int error = Marshal.GetLastWin32Error();
        bool closed = token == IntPtr.Zero || CloseHandle(token);
        Demand(!opened && error == 1008 && token == IntPtr.Zero && closed);
    }
    private static int Offset(IntPtr start, int length, IntPtr pointer, int needed)
    {
        long difference = pointer.ToInt64() - start.ToInt64();
        Demand(needed >= 0 && difference >= 0 && difference <= length - needed);
        return checked((int)difference);
    }
    private static SecurityIdentifier Sid(IntPtr buffer, int length, IntPtr pointer)
    {
        Offset(buffer, length, pointer, 8);
        int count = Marshal.ReadByte(pointer, 1);
        Demand(Marshal.ReadByte(pointer) == 1 && count <= 15);
        int bytes = 8 + count * 4;
        Offset(buffer, length, pointer, bytes);
        byte[] copy = new byte[bytes];
        Marshal.Copy(pointer, copy, 0, bytes);
        return new SecurityIdentifier(copy, 0);
    }
    private static string Text(IntPtr buffer, int length, IntPtr pointer)
    {
        int offset = Offset(buffer, length, pointer, 2);
        Demand((offset & 1) == 0);
        for (int n = 0; n <= (length - offset - 2) / 2; n++)
            if (Marshal.ReadInt16(pointer, n * 2) == 0) return Marshal.PtrToStringUni(pointer, n);
        throw new InvalidOperationException();
    }
    private static IntPtr TokenBuffer(IntPtr token, int kind, out int length)
    {
        uint needed;
        bool sizing = GetTokenInformation(token, kind, IntPtr.Zero, 0, out needed);
        Demand(!sizing && Marshal.GetLastWin32Error() == 122 && needed >= 4 && needed <= 65536);
        IntPtr buffer = Marshal.AllocHGlobal(checked((int)needed));
        try
        {
            uint returned;
            Demand(GetTokenInformation(token, kind, buffer, needed, out returned) && returned >= 4 && returned <= needed);
            length = checked((int)returned);
            return buffer;
        }
        catch { Marshal.FreeHGlobal(buffer); throw; }
    }
    private static SecurityIdentifier User(IntPtr token)
    {
        int length;
        IntPtr buffer = TokenBuffer(token, 1, out length);
        try { Demand(length >= Marshal.SizeOf(typeof(SidEntry))); return Sid(buffer, length, Marshal.ReadIntPtr(buffer)); }
        finally { Marshal.FreeHGlobal(buffer); }
    }
    private static string Restricted(IntPtr token, SecurityIdentifier expected)
    {
        Demand(IsTokenRestricted(token));
        int length;
        IntPtr buffer = TokenBuffer(token, 11, out length);
        try
        {
            int count = Marshal.ReadInt32(buffer);
            int offset = Marshal.OffsetOf(typeof(GroupHeader), "First").ToInt32();
            int stride = Marshal.SizeOf(typeof(SidEntry));
            Demand(count > 0 && count <= 1024 && offset + count * stride <= length);
            bool found = false;
            StringBuilder canonical = new StringBuilder();
            for (int i = 0; i < count; i++)
            {
                IntPtr entry = IntPtr.Add(buffer, offset + i * stride);
                SecurityIdentifier sid = Sid(buffer, length, Marshal.ReadIntPtr(entry));
                found |= sid.Equals(expected);
                canonical.Append(sid.Value).Append(':').Append(Marshal.ReadInt32(entry, IntPtr.Size)).Append(';');
            }
            Demand(found);
            return canonical.ToString();
        }
        finally { Marshal.FreeHGlobal(buffer); }
    }
    private static Snapshot Capture(IntPtr process, SecurityIdentifier expected, SecurityIdentifier runner)
    {
        NoThreadToken();
        IntPtr token = IntPtr.Zero;
        try
        {
            Demand(OpenProcessToken(process, 8, out token) && token != IntPtr.Zero);
            Snapshot result = new Snapshot();
            result.User = User(token);
            Demand(result.User.Equals(expected) && !result.User.Equals(runner) &&
                !result.User.IsWellKnown(WellKnownSidType.LocalSystemSid));
            int length;
            IntPtr buffer = TokenBuffer(token, 10, out length);
            try { Demand(length == 56); result.Stats = (Statistics)Marshal.PtrToStructure(buffer, typeof(Statistics)); }
            finally { Marshal.FreeHGlobal(buffer); }
            Demand(result.Stats.Type == 1);
            buffer = TokenBuffer(token, 12, out length);
            try { Demand(length == 4); result.Session = unchecked((uint)Marshal.ReadInt32(buffer)); }
            finally { Marshal.FreeHGlobal(buffer); }
            Demand(result.Session == 0);
            result.Restricted = Restricted(token, expected);
            NoThreadToken();
            return result;
        }
        finally { if (token != IntPtr.Zero) Demand(CloseHandle(token)); }
    }
    private static bool Equal(Luid a, Luid b) { return a.Low == b.Low && a.High == b.High; }
    private static bool Same(Snapshot a, Snapshot b)
    {
        return a.User.Equals(b.User) && a.Session == b.Session && a.Restricted == b.Restricted &&
            Equal(a.Stats.TokenId, b.Stats.TokenId) && Equal(a.Stats.AuthenticationId, b.Stats.AuthenticationId) &&
            Equal(a.Stats.ModifiedId, b.Stats.ModifiedId) && a.Stats.Type == b.Stats.Type;
    }
    private static Status Running(IntPtr service, uint pid)
    {
        Status value;
        uint needed;
        Demand(QueryServiceStatusEx(service, 0, out value, 36, out needed));
        Demand(value.Type == 0x10 && value.State == 4 && value.Pid != 0 && value.Pid == pid && value.Flags == 0);
        return value;
    }
    private static void Configuration(IntPtr service, string name, string command)
    {
        uint needed;
        bool sizing = QueryServiceConfigW(service, IntPtr.Zero, 0, out needed);
        Demand(!sizing && Marshal.GetLastWin32Error() == 122 && needed >= Marshal.SizeOf(typeof(Config)) && needed <= 8192);
        int length = checked((int)needed);
        IntPtr buffer = Marshal.AllocHGlobal(length);
        try
        {
            Demand(QueryServiceConfigW(service, buffer, (uint)length, out needed));
            Config config = (Config)Marshal.PtrToStructure(buffer, typeof(Config));
            Demand(config.Type == 0x10 && config.Start == 3 && config.Error == 1 &&
                Text(buffer, length, config.Account) == "NT SERVICE\\" + name &&
                Text(buffer, length, config.Binary) == command);
        }
        finally { Marshal.FreeHGlobal(buffer); }
        buffer = Marshal.AllocHGlobal(4);
        try { Demand(QueryServiceConfig2W(service, 5, buffer, 4, out needed) && Marshal.ReadInt32(buffer) == 3); }
        finally { Marshal.FreeHGlobal(buffer); }
    }
    private static long Birth(IntPtr process)
    {
        long creation, exit, kernel, user;
        Demand(WaitForSingleObject(process, 0) == 258);
        Demand(GetProcessTimes(process, out creation, out exit, out kernel, out user) && creation > 0 && exit == 0);
        return creation;
    }
    private static void Witness(IntPtr service, string[] args)
    {
        uint pid = UInt32.Parse(args[2], System.Globalization.CultureInfo.InvariantCulture);
        long birth = Int64.Parse(args[3], System.Globalization.CultureInfo.InvariantCulture);
        Demand(pid != 0 && birth > 0);
        Configuration(service, args[1], args[5]);
        Running(service, pid);
        IntPtr process = IntPtr.Zero, second = IntPtr.Zero, runnerToken = IntPtr.Zero;
        bool clean = true;
        try
        {
            process = OpenProcess(0x1000 | 0x100000, false, pid);
            Demand(process != IntPtr.Zero && Birth(process) == birth);
            StringBuilder image = new StringBuilder(32768); uint chars = 32768;
            Demand(QueryFullProcessImageNameW(process, 0, image, ref chars) &&
                String.Equals(image.ToString(), args[4], StringComparison.OrdinalIgnoreCase));
            Demand(OpenProcessToken(GetCurrentProcess(), 8, out runnerToken) && runnerToken != IntPtr.Zero);
            SecurityIdentifier runner = User(runnerToken);
            SecurityIdentifier expected = (SecurityIdentifier)new NTAccount("NT SERVICE", args[1]).Translate(typeof(SecurityIdentifier));
            Snapshot before = Capture(process, expected, runner);
            Running(service, pid);
            second = OpenProcess(0x1000 | 0x100000, false, pid);
            Demand(second != IntPtr.Zero && Birth(second) == birth && Birth(process) == birth);
            Snapshot after = Capture(second, expected, runner);
            Demand(Same(before, after));
            Configuration(service, args[1], args[5]);
            Running(service, pid);
            Demand(Birth(process) == birth && Birth(second) == birth);
            NoThreadToken();
            Demand(!ClientAdmissionAllowed && !CredentialEffectAllowed && !ApprovedServiceProvenance && !ProductionReleaseAllowed);
        }
        finally
        {
            if (runnerToken != IntPtr.Zero) clean &= CloseHandle(runnerToken);
            if (second != IntPtr.Zero) clean &= CloseHandle(second);
            if (process != IntPtr.Zero) clean &= CloseHandle(process);
            Demand(clean);
        }
    }
    private static int Main(string[] args)
    {
        bool passed = false, clean = true;
        IntPtr manager = IntPtr.Zero, service = IntPtr.Zero;
        try
        {
            Demand(Environment.GetEnvironmentVariable("GITHUB_ACTIONS") == "true" &&
                Environment.GetEnvironmentVariable("RUNNER_ENVIRONMENT") == "github-hosted" &&
                Environment.GetEnvironmentVariable("RUNNER_OS") == "Windows" &&
                Environment.GetEnvironmentVariable("ImageOS") == "win22" &&
                Environment.GetEnvironmentVariable("P292_DISPOSABLE_SCM_WITNESS") == "1");
            Demand(args.Length == 2 || args.Length == 6);
            Demand(Regex.IsMatch(args[1], "\\ANayeonP292_[0-9a-f]{12}\\z"));
            Layouts(); NoThreadToken();
            manager = OpenSCManagerW(null, null, 1); Demand(manager != IntPtr.Zero);
            service = OpenServiceW(manager, args[1], 1 | 4);
            if (args[0] == "absent" && args.Length == 2)
                Demand(service == IntPtr.Zero && Marshal.GetLastWin32Error() == 1060);
            else
            {
                Demand(args[0] == "witness" && args.Length == 6 && service != IntPtr.Zero);
                Witness(service, args);
            }
            passed = true;
        }
        catch (Exception) { passed = false; }
        finally
        {
            if (service != IntPtr.Zero) clean &= CloseServiceHandle(service);
            if (manager != IntPtr.Zero) clean &= CloseServiceHandle(manager);
        }
        passed &= clean;
        Console.WriteLine(passed ? "P292_PROBE=PASS" : "P292_PROBE=HOLD");
        return passed ? 0 : 1;
    }
}
