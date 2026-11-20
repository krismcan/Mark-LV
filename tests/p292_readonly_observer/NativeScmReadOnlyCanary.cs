#if !DEBUG || !C1_REVIEW_ISOLATED_ASSEMBLY || !C1_P292_READONLY_DIAG_ONLY || RELEASE
#error P292_DEBUG_ISOLATED_READONLY_DIAG_ONLY
#endif
using System;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Text.RegularExpressions;

// Standalone review assembly. No product references. Raw configuration stays in
// private memory, including when this assembly is loaded into the CIM child.
public sealed class NativeScmReadOnlyCanary
{
    [DllImport("advapi32.dll", CharSet = CharSet.Unicode, ExactSpelling = true, SetLastError = true)]
    private static extern IntPtr OpenSCManagerW(string machine, string database, uint access);
    [DllImport("advapi32.dll", CharSet = CharSet.Unicode, ExactSpelling = true, SetLastError = true)]
    private static extern IntPtr OpenServiceW(IntPtr manager, string name, uint access);
    [DllImport("advapi32.dll", ExactSpelling = true, SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool CloseServiceHandle(IntPtr handle);
    [DllImport("advapi32.dll", CharSet = CharSet.Unicode, ExactSpelling = true, SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool QueryServiceConfigW(IntPtr service, IntPtr buffer, uint size, out uint needed);
    [DllImport("advapi32.dll", ExactSpelling = true, SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool QueryServiceStatusEx(IntPtr service, int level, out Status status, uint size, out uint needed);

    [StructLayout(LayoutKind.Sequential)]
    private struct Config
    {
        public uint Type, Start, Error;
        public IntPtr Binary, Group;
        public uint Tag;
        public IntPtr Dependencies, Account, Display;
    }
    [StructLayout(LayoutKind.Sequential)]
    private struct Status
    {
        public uint Type, State, Controls, Win32Exit, ServiceExit, Checkpoint, Wait, Pid, Flags;
    }

    private string label, absent, account, binary;
    private uint state;
    private string outcome = "ERROR", detail = "INTERNAL", latency = "LT100MS";
    private int error;
    private NativeScmReadOnlyCanary() { }

    private static bool Hosted()
    {
        return Environment.GetEnvironmentVariable("GITHUB_ACTIONS") == "true" &&
            Environment.GetEnvironmentVariable("RUNNER_ENVIRONMENT") == "github-hosted" &&
            Environment.GetEnvironmentVariable("RUNNER_OS") == "Windows" &&
            Environment.GetEnvironmentVariable("ImageOS") == "win22" &&
            Environment.GetEnvironmentVariable("P292_READONLY_DIAG_ONLY") == "1";
    }
    public static string Bucket(long milliseconds)
    {
        return milliseconds < 100 ? "LT100MS" : milliseconds < 1000 ? "LT1S" :
            milliseconds < 5000 ? "LT5S" : milliseconds < 12000 ? "LT12S" : "GE12S";
    }
    private static string Name(string label, string absent)
    {
        if (label == "A" && absent == "") return "EventLog";
        if (label == "B" && absent == "") return "Schedule";
        if (label == "X" && absent != null && Regex.IsMatch(absent, @"\ANayeonP292_[0-9a-f]{12}\z")) return absent;
        throw new ArgumentException();
    }
    private static string Text(IntPtr buffer, uint length, IntPtr pointer)
    {
        long offset = pointer.ToInt64() - buffer.ToInt64();
        if (offset < Marshal.SizeOf(typeof(Config)) || offset >= length || (offset & 1) != 0)
            throw new InvalidOperationException();
        int available = checked((int)((length - offset) / 2));
        for (int i = 0; i < available; i++)
            if (Marshal.ReadInt16(pointer, checked(i * 2)) == 0) return Marshal.PtrToStringUni(pointer, i);
        throw new InvalidOperationException();
    }
    private void Fail(string stage, int code)
    {
        outcome = "ERROR"; error = code;
        detail = code == 5 ? "ACCESS_DENIED" : stage;
    }
    public static NativeScmReadOnlyCanary Begin(string label, string absent)
    {
        NativeScmReadOnlyCanary result = new NativeScmReadOnlyCanary();
        Stopwatch watch = Stopwatch.StartNew();
        IntPtr manager = IntPtr.Zero, service = IntPtr.Zero, buffer = IntPtr.Zero;
        try
        {
            if (!Hosted()) { result.Fail("GUARD", 0); return result; }
            string name = Name(label, absent);
            result.label = label; result.absent = absent;
            // SC_MANAGER_CONNECT only; SERVICE_QUERY_CONFIG | SERVICE_QUERY_STATUS only.
            manager = OpenSCManagerW(null, null, 0x0001);
            if (manager == IntPtr.Zero) { result.Fail("MANAGER", Marshal.GetLastWin32Error()); return result; }
            service = OpenServiceW(manager, name, 0x0001 | 0x0004);
            if (service == IntPtr.Zero)
            {
                int code = Marshal.GetLastWin32Error();
                if (label == "X" && code == 1060)
                { result.outcome = "PASS"; result.detail = "ABSENT_1060"; result.error = code; }
                else result.Fail("OPEN", code);
                return result;
            }
            if (label == "X") { result.outcome = "MISMATCH"; result.detail = "UNEXPECTED_PRESENT"; return result; }
            uint needed;
            bool sizing = QueryServiceConfigW(service, IntPtr.Zero, 0, out needed);
            int sizingError = Marshal.GetLastWin32Error();
            if (sizing || sizingError != 122) { result.Fail("CONFIG_SIZE", sizingError); return result; }
            if (needed < Marshal.SizeOf(typeof(Config)) || needed > 8192) { result.Fail("LAYOUT", 0); return result; }
            uint capacity = needed;
            buffer = Marshal.AllocHGlobal(checked((int)capacity));
            if (!QueryServiceConfigW(service, buffer, capacity, out needed))
            { result.Fail("CONFIG", Marshal.GetLastWin32Error()); return result; }
            Config config = (Config)Marshal.PtrToStructure(buffer, typeof(Config));
            result.account = Text(buffer, capacity, config.Account);
            result.binary = Text(buffer, capacity, config.Binary);
            if (result.account.Length == 0 || result.binary.Length == 0) { result.Fail("EMPTY_CONFIG", 0); return result; }
            Status status;
            uint statusSize = checked((uint)Marshal.SizeOf(typeof(Status)));
            if (!QueryServiceStatusEx(service, 0, out status, statusSize, out needed))
            { result.Fail("STATUS", Marshal.GetLastWin32Error()); return result; }
            if (needed != statusSize || status.State < 1 || status.State > 7) { result.Fail("LAYOUT", 0); return result; }
            result.state = status.State;
            result.outcome = "PASS"; result.detail = "EXISTS";
        }
        catch (ArgumentException) { result.Fail("INPUT", 0); }
        catch (Exception) { result.Fail("INTERNAL", 0); }
        finally
        {
            if (buffer != IntPtr.Zero) Marshal.FreeHGlobal(buffer);
            if (service != IntPtr.Zero && !CloseServiceHandle(service)) result.Fail("CLOSE", Marshal.GetLastWin32Error());
            if (manager != IntPtr.Zero && !CloseServiceHandle(manager)) result.Fail("CLOSE", Marshal.GetLastWin32Error());
            result.latency = Bucket(watch.ElapsedMilliseconds);
        }
        return result;
    }
    public string Report()
    {
        return "NATIVE=" + outcome + ";DETAIL=" + detail + ";WIN32=" + error + ";LAT=" + latency +
            ";ARCH=" + (IntPtr.Size == 8 ? "x64" : "x86");
    }
    public bool Passed() { return outcome == "PASS"; }
    // Called only inside the isolated CIM child; no raw field leaves that process.
    // No alias, case, environment, quoting, slash or account normalization.
    public string Compare(NativeScmReadOnlyCanary after, int count, string name,
        string startName, string pathName, string cimState)
    {
        if (!Passed() || after == null || !after.Passed()) return "COMPARE=ERROR;DETAIL=NATIVE";
        if (label != after.label || absent != after.absent) return "COMPARE=ERROR;DETAIL=INPUT";
        if (label == "X") return count == 0 ? "COMPARE=PASS;DETAIL=ABSENT" : "COMPARE=MISMATCH;DETAIL=PRESENCE";
        if (count != 1) return "COMPARE=MISMATCH;DETAIL=PRESENCE";
        if (!String.Equals(name, Name(label, absent), StringComparison.Ordinal)) return "COMPARE=MISMATCH;DETAIL=NAME";
        if (!String.Equals(account, after.account, StringComparison.Ordinal) ||
            !String.Equals(binary, after.binary, StringComparison.Ordinal) || state != after.state)
            return "COMPARE=MISMATCH;DETAIL=NATIVE_DRIFT";
        if (!String.Equals(account, startName, StringComparison.Ordinal)) return "COMPARE=MISMATCH;DETAIL=ACCOUNT_FORMAT";
        if (!String.Equals(binary, pathName, StringComparison.Ordinal)) return "COMPARE=MISMATCH;DETAIL=PATH_FORMAT";
        string[] states = { "", "Stopped", "Start Pending", "Stop Pending", "Running", "Continue Pending", "Pause Pending", "Paused" };
        if (!String.Equals(states[state], cimState, StringComparison.Ordinal)) return "COMPARE=MISMATCH;DETAIL=STATE";
        return "COMPARE=PASS;DETAIL=EXACT";
    }
    public static int Main(string[] args)
    {
        if (args.Length != 2) { Console.WriteLine("CONTROL=ERROR;DETAIL=INPUT"); return 2; }
        NativeScmReadOnlyCanary result = Begin(args[0], args[1]);
        Console.WriteLine(result.Report());
        return result.Passed() ? 0 : 1;
    }
}
