#if !DEBUG || RELEASE || !C1_REVIEW_ISOLATED_ASSEMBLY || !C1_P289_NATIVE_PEER_DIAGNOSTIC_ONLY
#error P289_DIAGNOSTIC_ONLY_DEBUG_ISOLATED_OPT_IN_REQUIRED
#endif
// Standalone disposable-host experiment. No production consumer or transferable issuer.
using System;
using System.Diagnostics;
using System.IO;
using System.IO.Pipes;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Security.AccessControl;
using System.Security.Principal;
using System.Threading;

internal static class NativePeerDiagnostic
{
    private static int checks, realCases, simulatedCases;
    private static bool cleanupFailed;
    private static string stage = "START";
    private static readonly Stopwatch total = Stopwatch.StartNew();
    private static void Check(bool condition)
    { checks++; if (!condition) throw new InvalidOperationException("P289_CHECK"); }
    private static void Demand(bool condition)
    { if (!condition) throw new InvalidOperationException("P289_NATIVE"); }
    private static void Pause(Stopwatch operation)
    {
        if (operation.ElapsedMilliseconds > 4000 || total.ElapsedMilliseconds > 40000)
            throw new TimeoutException("P289_DEADLINE");
        Thread.Sleep(5);
    }
    private sealed class Handle : Microsoft.Win32.SafeHandles.SafeHandleZeroOrMinusOneIsInvalid
    {
        internal Handle(IntPtr raw) : base(true) { SetHandle(raw); }
        protected override bool ReleaseHandle()
        { bool ok = CloseHandle(handle); if (!ok) cleanupFailed = true; return ok; }
    }
    [StructLayout(LayoutKind.Sequential)]
    private struct Luid { internal uint Low; internal int High; }
    [StructLayout(LayoutKind.Sequential)]
    private struct Statistics
    {
        internal Luid TokenId, AuthenticationId;
        internal long Expiration;
        internal uint Type, Impersonation, Charged, Available, Groups, Privileges;
        internal Luid ModifiedId;
    }
    [StructLayout(LayoutKind.Sequential)]
    private struct FileTime
    {
        internal uint Low, High;
        internal long Value { get { return ((long)High << 32) | Low; } }
    }
    [StructLayout(LayoutKind.Sequential)]
    private struct SecurityAttributes
    { internal int Length; internal IntPtr Descriptor; internal int Inherit; }
    [DllImport("kernel32.dll", ExactSpelling = true, SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool CloseHandle(IntPtr handle);
    [DllImport("kernel32.dll", ExactSpelling = true)] private static extern IntPtr GetCurrentProcess();
    [DllImport("kernel32.dll", ExactSpelling = true)] private static extern IntPtr GetCurrentThread();
    [DllImport("kernel32.dll", ExactSpelling = true)] private static extern uint GetCurrentProcessId();
    [DllImport("kernel32.dll", ExactSpelling = true, SetLastError = true)]
    private static extern IntPtr OpenProcess(uint access, [MarshalAs(UnmanagedType.Bool)] bool inherit, uint pid);
    [DllImport("kernel32.dll", ExactSpelling = true, SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool GetProcessTimes(IntPtr process, out FileTime birth, out FileTime exit, out FileTime kernel, out FileTime user);
    [DllImport("kernel32.dll", ExactSpelling = true, SetLastError = true)]
    private static extern uint WaitForSingleObject(IntPtr handle, uint milliseconds);
    [DllImport("advapi32.dll", ExactSpelling = true, SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool OpenProcessToken(IntPtr process, uint access, out IntPtr token);
    [DllImport("advapi32.dll", ExactSpelling = true, SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool OpenThreadToken(IntPtr thread, uint access, [MarshalAs(UnmanagedType.Bool)] bool self, out IntPtr token);
    [DllImport("advapi32.dll", ExactSpelling = true, SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool GetTokenInformation(IntPtr token, int kind, IntPtr buffer, uint size, out uint returned);
    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, ExactSpelling = true, SetLastError = true)]
    private static extern IntPtr CreateNamedPipeW(string name, uint access, uint mode, uint instances,
        uint output, uint input, uint timeout, ref SecurityAttributes attributes);
    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, ExactSpelling = true, SetLastError = true)]
    private static extern IntPtr CreateFileW(string name, uint access, uint share, IntPtr attributes,
        uint disposition, uint flags, IntPtr template);
    [DllImport("kernel32.dll", ExactSpelling = true, SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)] private static extern bool SetNamedPipeHandleState(IntPtr pipe, ref uint mode, IntPtr count, IntPtr timeout);
    [DllImport("kernel32.dll", ExactSpelling = true, SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)] private static extern bool ConnectNamedPipe(IntPtr pipe, IntPtr overlapped);
    [DllImport("kernel32.dll", ExactSpelling = true, SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)] private static extern bool DisconnectNamedPipe(IntPtr pipe);
    [DllImport("kernel32.dll", ExactSpelling = true, SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)] private static extern bool GetNamedPipeClientProcessId(IntPtr pipe, out uint pid);
    [DllImport("kernel32.dll", ExactSpelling = true, SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)] private static extern bool GetNamedPipeClientSessionId(IntPtr pipe, out uint session);
    [DllImport("kernel32.dll", ExactSpelling = true, SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)] private static extern bool ReadFile(IntPtr pipe, byte[] bytes, uint count, out uint read, IntPtr overlapped);
    [DllImport("kernel32.dll", ExactSpelling = true, SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)] private static extern bool WriteFile(IntPtr pipe, byte[] bytes, uint count, out uint written, IntPtr overlapped);

    private static void NoAmbientToken()
    {
        IntPtr raw;
        bool opened = OpenThreadToken(GetCurrentThread(), 8, true, out raw);
        int error = Marshal.GetLastWin32Error();
        using (Handle token = new Handle(raw))
            Demand(!opened && error == 1008 && token.IsInvalid); // ERROR_NO_TOKEN only.
    }
    private static IntPtr Information(IntPtr token, int kind, out uint size)
    {
        bool initial = GetTokenInformation(token, kind, IntPtr.Zero, 0, out size);
        Demand(!initial && Marshal.GetLastWin32Error() == 122 && size >= 4 && size <= 4096);
        IntPtr buffer = Marshal.AllocHGlobal((int)size);
        try
        {
            uint returned;
            Demand(GetTokenInformation(token, kind, buffer, size, out returned) && returned == size);
            return buffer;
        }
        catch { Marshal.FreeHGlobal(buffer); throw; }
    }
    private sealed class TokenSnapshot
    {
        internal readonly SecurityIdentifier User;
        internal readonly Statistics Stats;
        internal readonly uint Session;
        internal TokenSnapshot(SecurityIdentifier user, Statistics stats, uint session)
        { User = user; Stats = stats; Session = session; }
    }
    private static TokenSnapshot Token(IntPtr token)
    {
        uint size; IntPtr buffer = Information(token, 1, out size); // TokenUser
        SecurityIdentifier sid;
        try
        {
            int header = IntPtr.Size == 8 ? 16 : 8;
            Demand(size >= header + 8);
            long offset = Marshal.ReadIntPtr(buffer).ToInt64() - buffer.ToInt64();
            Demand(offset >= header && offset <= size - 8);
            byte[] bytes = new byte[(int)size]; Marshal.Copy(buffer, bytes, 0, bytes.Length);
            int length = 8 + 4 * bytes[(int)offset + 1];
            Demand(bytes[(int)offset] == 1 && length <= 68 && offset + length <= size);
            sid = new SecurityIdentifier(bytes, (int)offset);
        }
        finally { Marshal.FreeHGlobal(buffer); }
        buffer = Information(token, 10, out size); // TokenStatistics: 56 on BOTH architectures.
        Statistics stats;
        try { Demand(size == 56); stats = (Statistics)Marshal.PtrToStructure(buffer, typeof(Statistics)); }
        finally { Marshal.FreeHGlobal(buffer); }
        buffer = Information(token, 8, out size); // TokenType queried independently.
        try { Demand(size == 4 && Marshal.ReadInt32(buffer) == 1 && stats.Type == 1); }
        finally { Marshal.FreeHGlobal(buffer); }
        buffer = Information(token, 12, out size); // TokenSessionId
        uint session;
        try { Demand(size == 4); session = unchecked((uint)Marshal.ReadInt32(buffer)); }
        finally { Marshal.FreeHGlobal(buffer); }
        return new TokenSnapshot(sid, stats, session);
    }
    private static Handle OpenToken(IntPtr process)
    {
        IntPtr raw; bool ok = OpenProcessToken(process, 8, out raw); // TOKEN_QUERY only.
        Handle handle = new Handle(raw);
        if (!ok || handle.IsInvalid) { handle.Dispose(); throw new InvalidOperationException("P289_TOKEN"); }
        return handle;
    }
    private static bool SameLuid(Luid a, Luid b) { return a.Low == b.Low && a.High == b.High; }
    private static bool Same(TokenSnapshot a, TokenSnapshot b)
    {
        return a.User.Equals(b.User) && a.Session == b.Session && a.Stats.Type == 1 && b.Stats.Type == 1 &&
            SameLuid(a.Stats.TokenId, b.Stats.TokenId) && SameLuid(a.Stats.AuthenticationId, b.Stats.AuthenticationId) &&
            SameLuid(a.Stats.ModifiedId, b.Stats.ModifiedId);
    }
    private static long Birth(IntPtr process)
    {
        FileTime birth, exit, kernel, user;
        Demand(GetProcessTimes(process, out birth, out exit, out kernel, out user)); return birth.Value;
    }
    private static bool Alive(IntPtr process)
    {
        // WAIT_TIMEOUT is the ONLY active result. Signaled, WAIT_FAILED and all
        // unexpected statuses deny. Exit code 259 has no role in this decision.
        return WaitForSingleObject(process, 0) == 0x102;
    }
    private static bool Peer(IntPtr pipe, out uint pid, out uint session)
    {
        bool p = GetNamedPipeClientProcessId(pipe, out pid);
        bool s = GetNamedPipeClientSessionId(pipe, out session);
        return p && s && pid != 0;
    }
    private static void Send(IntPtr pipe, byte value)
    {
        uint written; Demand(WriteFile(pipe, new byte[] { value }, 1, out written, IntPtr.Zero) && written == 1);
    }
    private static byte Receive(IntPtr pipe)
    {
        Stopwatch wait = Stopwatch.StartNew(); byte[] bytes = new byte[1];
        for (;;)
        {
            uint read; bool ok = ReadFile(pipe, bytes, 1, out read, IntPtr.Zero);
            int error = Marshal.GetLastWin32Error();
            if (ok && read == 1) return bytes[0];
            Demand((ok && read == 0) || (!ok && error == 232)); // Nonblocking empty pipe only.
            Pause(wait);
        }
    }
    private sealed class Endpoint : IDisposable
    {
        internal readonly string Name = "p289-" + Guid.NewGuid().ToString("N");
        internal readonly Handle Pipe;
        internal object Epoch;
        internal bool Connected, Cancelled;
        internal Endpoint(SecurityIdentifier user)
        {
            PipeSecurity security = new PipeSecurity();
            security.SetAccessRuleProtection(true, false); security.SetOwner(user);
            security.AddAccessRule(new PipeAccessRule(user, PipeAccessRights.FullControl, AccessControlType.Allow));
            byte[] descriptor = security.GetSecurityDescriptorBinaryForm();
            GCHandle pinned = GCHandle.Alloc(descriptor, GCHandleType.Pinned);
            try
            {
                SecurityAttributes attributes = new SecurityAttributes();
                attributes.Length = Marshal.SizeOf(typeof(SecurityAttributes)); attributes.Descriptor = pinned.AddrOfPinnedObject();
                // Duplex + FIRST_PIPE_INSTANCE; byte + NOWAIT + REJECT_REMOTE_CLIENTS; one instance.
                Pipe = new Handle(CreateNamedPipeW(PathFor(Name), 3 | 0x80000, 1 | 8, 1, 64, 64, 0, ref attributes));
                Demand(!Pipe.IsInvalid);
            }
            finally { pinned.Free(); }
            try
            {
                // Read back actual kernel DACL. A matching descriptor is still not service custody.
                using (Microsoft.Win32.SafeHandles.SafePipeHandle wrapper =
                    new Microsoft.Win32.SafeHandles.SafePipeHandle(Pipe.DangerousGetHandle(), false))
                using (NamedPipeServerStream view = new NamedPipeServerStream(PipeDirection.InOut, false, false, wrapper))
                {
                    PipeSecurity actual = view.GetAccessControl();
                    Demand(actual.AreAccessRulesProtected && user.Equals(actual.GetOwner(typeof(SecurityIdentifier))));
                    AuthorizationRuleCollection rules = actual.GetAccessRules(true, true, typeof(SecurityIdentifier));
                    Demand(rules.Count == 1);
                    PipeAccessRule rule = (PipeAccessRule)rules[0];
                    Demand(!rule.IsInherited && rule.AccessControlType == AccessControlType.Allow &&
                        user.Equals(rule.IdentityReference) && rule.PipeAccessRights == PipeAccessRights.FullControl);
                }
            }
            catch { Pipe.Dispose(); throw; }
        }
        internal void Connect()
        {
            Stopwatch wait = Stopwatch.StartNew();
            for (;;)
            {
                bool ok = ConnectNamedPipe(Pipe.DangerousGetHandle(), IntPtr.Zero);
                int error = Marshal.GetLastWin32Error();
                if (!ok && error == 535) break; // ERROR_PIPE_CONNECTED
                Demand(ok || error == 536); // Nonblocking transition/listening.
                Pause(wait);
            }
            Epoch = new object(); Connected = true; Cancelled = false;
        }
        internal void Disconnect()
        {
            Connected = false; Epoch = null; // Invalidate before native transition, including failures.
            Demand(DisconnectNamedPipe(Pipe.DangerousGetHandle()));
        }
        public void Dispose() { Connected = false; Epoch = null; Pipe.Dispose(); }
    }
    private sealed class Observation
    {
        internal readonly object Epoch;
        internal readonly uint Pid, Session;
        internal readonly long Birth;
        internal readonly TokenSnapshot Token;
        internal Observation(object epoch, uint pid, uint session, long birth, TokenSnapshot token)
        { Epoch = epoch; Pid = pid; Session = session; Birth = birth; Token = token; }
        // There are deliberately no positive authority fields/methods or production references.
    }
    private sealed class Child : IDisposable
    {
        internal readonly Process Process;
        internal readonly Handle Query, InitialToken;
        internal readonly uint Pid;
        internal readonly long Started;
        internal Child(string endpoint)
        {
            ProcessStartInfo info = new ProcessStartInfo(Assembly.GetExecutingAssembly().Location, "--child " + endpoint);
            info.UseShellExecute = false; info.CreateNoWindow = true;
            info.EnvironmentVariables.Clear();
            foreach (string key in new[] { "SystemRoot", "WINDIR", "GITHUB_ACTIONS", "RUNNER_ENVIRONMENT", "RUNNER_OS", "ImageOS" })
                info.EnvironmentVariables[key] = Environment.GetEnvironmentVariable(key);
            Process = new Process(); Process.StartInfo = info;
            try
            {
                Demand(Process.Start()); Pid = checked((uint)Process.Id); Demand(Pid != GetCurrentProcessId());
                // QUERY_LIMITED_INFORMATION | SYNCHRONIZE, solely for nonblocking liveness.
                Query = new Handle(OpenProcess(0x101000, false, Pid));
                Demand(!Query.IsInvalid && Alive(Query.DangerousGetHandle()));
                Started = Process.StartTime.ToUniversalTime().ToFileTimeUtc(); // Independent managed process observation.
                Demand(Started == Birth(Query.DangerousGetHandle()));
                InitialToken = OpenToken(Query.DangerousGetHandle());
            }
            catch { Dispose(); throw; }
        }
        internal Observation Observe(Endpoint endpoint)
        {
            NoAmbientToken();
            if (!endpoint.Connected || endpoint.Cancelled || endpoint.Pipe.IsClosed ||
                Query.IsClosed || Query.IsInvalid || InitialToken.IsClosed || InitialToken.IsInvalid ||
                !Alive(Query.DangerousGetHandle())) return null;
            object epoch = endpoint.Epoch; uint pid, session;
            if (!Peer(endpoint.Pipe.DangerousGetHandle(), out pid, out session) || pid != Pid) return null;
            long birth = Birth(Query.DangerousGetHandle());
            using (Handle currentToken = OpenToken(Query.DangerousGetHandle()))
            {
                TokenSnapshot token = Token(currentToken.DangerousGetHandle());
                uint afterPid, afterSession;
                if (birth != Started || token.Session != session || !Same(token, Token(InitialToken.DangerousGetHandle())) ||
                    !Peer(endpoint.Pipe.DangerousGetHandle(), out afterPid, out afterSession) || pid != afterPid || session != afterSession ||
                    !Alive(Query.DangerousGetHandle()) || Birth(Query.DangerousGetHandle()) != birth ||
                    !endpoint.Connected || endpoint.Cancelled || !Object.ReferenceEquals(epoch, endpoint.Epoch)) return null;
                NoAmbientToken(); return new Observation(epoch, pid, session, birth, token);
            }
        }
        public void Dispose()
        {
            try
            {
                if (Process != null)
                {
                    try
                    {
                        if (!Process.HasExited) Process.Kill(); // ONLY our retained disposable child Process.
                        if (!Process.WaitForExit(3000)) cleanupFailed = true;
                    }
                    catch (InvalidOperationException) { cleanupFailed = true; }
                }
            }
            finally
            {
                if (InitialToken != null) InitialToken.Dispose();
                if (Query != null) Query.Dispose();
                if (Process != null) Process.Dispose();
            }
        }
    }
    private static bool Matches(Observation a, Observation b)
    {
        return a != null && b != null && Object.ReferenceEquals(a.Epoch, b.Epoch) && a.Pid == b.Pid &&
            a.Session == b.Session && a.Birth == b.Birth && Same(a.Token, b.Token);
    }
    private static string PathFor(string name) { return @"\\.\pipe\" + name; }
    private static int ChildMain(string name)
    {
        Guid parsed;
        if (name.Length != 37 || !name.StartsWith("p289-", StringComparison.Ordinal) || !Guid.TryParseExact(name.Substring(5), "N", out parsed)) return 3;
        NoAmbientToken();
        using (Handle token = OpenToken(GetCurrentProcess())) { Token(token.DangerousGetHandle()); }
        Stopwatch wait = Stopwatch.StartNew();
        Handle pipe;
        for (;;)
        {
            // SECURITY_SQOS_PRESENT | SECURITY_IDENTIFICATION, no server impersonation performed.
            pipe = new Handle(CreateFileW(PathFor(name), 0xC0000000, 0, IntPtr.Zero, 3, 0x00110000, IntPtr.Zero));
            if (!pipe.IsInvalid) break;
            int error = Marshal.GetLastWin32Error(); pipe.Dispose();
            Demand(error == 2 || error == 231); Pause(wait);
        }
        byte terminal;
        using (pipe)
        {
            uint mode = 1; Demand(SetNamedPipeHandleState(pipe.DangerousGetHandle(), ref mode, IntPtr.Zero, IntPtr.Zero));
            Send(pipe.DangerousGetHandle(), 1);
            Demand(Receive(pipe.DangerousGetHandle()) == 2); NoAmbientToken(); Send(pipe.DangerousGetHandle(), 3);
            terminal = Receive(pipe.DangerousGetHandle());
            Demand(terminal == 4 || terminal == 5); NoAmbientToken();
        }
        // Real adversary: a terminated process may return STILL_ACTIVE's numeric value.
        // Decide only AFTER pipe cleanup so cleanup failure cannot masquerade as the expected exit.
        return cleanupFailed ? 1 : (terminal == 5 ? 259 : 0);
    }
    private static void SimulatedMismatches(Observation original)
    {
        // Pure fixture changes: NEVER label these as kernel mutation/denial evidence.
        Check(!Matches(original, new Observation(original.Epoch, original.Pid ^ 0x80000000, original.Session, original.Birth, original.Token))); simulatedCases++;
        Check(!Matches(original, new Observation(original.Epoch, original.Pid, original.Session ^ 1, original.Birth, original.Token))); simulatedCases++;
        Check(!Matches(original, new Observation(original.Epoch, original.Pid, original.Session, original.Birth ^ 1, original.Token))); simulatedCases++;
        Statistics changed = original.Token.Stats; changed.ModifiedId.Low ^= 1;
        Check(!Matches(original, new Observation(original.Epoch, original.Pid, original.Session, original.Birth,
            new TokenSnapshot(original.Token.User, changed, original.Token.Session)))); simulatedCases++;
        changed = original.Token.Stats; changed.TokenId.Low ^= 1;
        Check(!Same(original.Token, new TokenSnapshot(original.Token.User, changed, original.Token.Session))); simulatedCases++;
        changed = original.Token.Stats; changed.AuthenticationId.Low ^= 1;
        Check(!Same(original.Token, new TokenSnapshot(original.Token.User, changed, original.Token.Session))); simulatedCases++;
        changed = original.Token.Stats; changed.Type = 2;
        Check(!Same(original.Token, new TokenSnapshot(original.Token.User, changed, original.Token.Session))); simulatedCases++;
        Check(!Same(original.Token, new TokenSnapshot(original.Token.User, original.Token.Stats, original.Token.Session ^ 1))); simulatedCases++;
        Check(!Matches(original, new Observation(new object(), original.Pid, original.Session, original.Birth, original.Token))); simulatedCases++;
    }
    private static void Experiment()
    {
        Check(Marshal.SizeOf(typeof(Statistics)) == 56 && Marshal.OffsetOf(typeof(Statistics), "ModifiedId").ToInt32() == 48);
        Check(Marshal.SizeOf(typeof(SecurityAttributes)) == (IntPtr.Size == 8 ? 24 : 12));
        NoAmbientToken();
        TokenSnapshot host;
        using (Handle token = OpenToken(GetCurrentProcess())) { host = Token(token.DangerousGetHandle()); }
        Check(host.User.AccountDomainSid != null); // Current disposable account, not a well-known service identity.
        uint p, s;
        stage = "INVALID";
        Check(!Peer(new IntPtr(-1), out p, out s)); realCases++;
        Check(!Alive(IntPtr.Zero) && WaitForSingleObject(IntPtr.Zero, 0) == 0xFFFFFFFF); realCases++;
        stage = "ENDPOINT";
        using (Endpoint endpoint = new Endpoint(host.User))
        {
            // Raw Windows result recorded without assuming unconnected queries must fail.
            bool unconnectedRaw = Peer(endpoint.Pipe.DangerousGetHandle(), out p, out s);
            Check(!endpoint.Connected && endpoint.Epoch == null); realCases++;
            Observation previous = null;
            for (int round = 0; round < 2; round++)
            {
                stage = round == 0 ? "CONNECTED" : "RECONNECTED";
                using (Child child = new Child(endpoint.Name))
                {
                    Check(child.Observe(endpoint) == null); realCases++;
                    endpoint.Connect(); Check(Receive(endpoint.Pipe.DangerousGetHandle()) == 1);
                    Observation first = child.Observe(endpoint); Check(first != null);
                    Check(first.Token.User.Equals(host.User) && first.Session == host.Session);
                    Check(first.Pid == child.Pid && first.Pid != GetCurrentProcessId() && first.Birth == child.Started);
                    Check(Matches(first, child.Observe(endpoint))); realCases++;
                    // Wrong expected peer values compared with a FRESH real kernel query.
                    Check(Peer(endpoint.Pipe.DangerousGetHandle(), out p, out s));
                    Check(p == child.Pid && s == first.Session && p != (child.Pid ^ 0x80000000) && s != (first.Session ^ 1)); realCases++;
                    Send(endpoint.Pipe.DangerousGetHandle(), 2); Check(Receive(endpoint.Pipe.DangerousGetHandle()) == 3);
                    Check(Matches(first, child.Observe(endpoint))); realCases++;
                    endpoint.Cancelled = true; Check(child.Observe(endpoint) == null); realCases++;
                    endpoint.Cancelled = false; // Diagnostic cancellation latch only, no OS cancellation claim.
                    Check(Matches(first, child.Observe(endpoint)));
                    if (previous != null) { Check(!Matches(previous, first)); realCases++; }
                    if (round == 0) SimulatedMismatches(first);
                    stage = "EARLY_EXIT";
                    Send(endpoint.Pipe.DangerousGetHandle(), round == 0 ? (byte)4 : (byte)5);
                    Check(child.Process.WaitForExit(4000) && child.Process.ExitCode == (round == 0 ? 0 : 259));
                    Check(WaitForSingleObject(child.Query.DangerousGetHandle(), 0) == 0 &&
                        !Alive(child.Query.DangerousGetHandle()) && child.Observe(endpoint) == null); realCases++;
                    child.Query.Dispose(); Check(child.Observe(endpoint) == null); realCases++;
                    endpoint.Disconnect(); Check(child.Observe(endpoint) == null); realCases++;
                    previous = first;
                }
            }
            IntPtr closed = endpoint.Pipe.DangerousGetHandle(); endpoint.Dispose();
            Check(!Peer(closed, out p, out s)); realCases++; // No handle creation between close and query.
            Console.WriteLine("P289_UNCONNECTED_RAW=" + (unconnectedRaw ? "VALUE_WITHOUT_AUTHORITY" : "REJECTED"));
        }
        Check(!cleanupFailed); NoAmbientToken();
        Console.WriteLine("P289_LIVENESS=WAIT_ZERO EXIT_ZERO=REJECTED EXIT_259=REJECTED INVALID_WAIT=DENIED CLOSED_QUERY=DENIED");
    }
    public static int Main(string[] args)
    {
        // Accident barriers, never claims of identity or security isolation.
        if (Environment.GetEnvironmentVariable("GITHUB_ACTIONS") != "true" ||
            Environment.GetEnvironmentVariable("RUNNER_ENVIRONMENT") != "github-hosted" ||
            Environment.GetEnvironmentVariable("RUNNER_OS") != "Windows" ||
            Environment.GetEnvironmentVariable("ImageOS") != "win22" ||
            String.Equals(Environment.UserName, "krist", StringComparison.OrdinalIgnoreCase) ||
            String.Equals(Environment.UserName, "Kristian", StringComparison.OrdinalIgnoreCase)) return 2;
        try
        {
            if (args.Length == 2 && args[0] == "--child") return ChildMain(args[1]);
            if (args.Length != 0) return 2;
            Experiment();
            Console.WriteLine("P289_DIAGNOSTIC=PASS REAL_CASES=" + realCases + " SIMULATED_CASES=" + simulatedCases +
                " CHECKS=" + checks + " BITS=" + (IntPtr.Size * 8));
            Console.WriteLine("P289_AUTHORITY=NONE MESSAGE_TOKEN=UNOBSERVED PRODUCTION=HOLD P96_ORIGINAL=HIGH_OPEN APPROVALS=0/7 FULL_REGRESSIONS=0/3");
            return 0;
        }
        catch (Exception)
        {
            // Do not print exception text, native identifiers, SID, PID, LUID, paths or endpoint.
            if (args.Length == 0) Console.WriteLine("P289_DIAGNOSTIC=HOLD STAGE=" + stage);
            return 1;
        }
    }
}
