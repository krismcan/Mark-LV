#if !DEBUG || RELEASE || !C1_REVIEW_ISOLATED_ASSEMBLY || !C1_P290_MESSAGE_TOKEN_DIAGNOSTIC_ONLY
#error P290_DIAGNOSTIC_ONLY_DEBUG_ISOLATED_OPT_IN_REQUIRED
#endif
// Disposable hosted experiment, never a production issuer. Compile locally; DO NOT RUN locally.
using System;
using System.Diagnostics;
using System.IO.Pipes;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Security.AccessControl;
using System.Security.Principal;
using System.Threading;

internal static class MessageTokenDiagnostic
{
    private static int checks, captures, denials;
    private static string stage = "START";
    private static bool cleanupFailed;
    private static readonly Stopwatch total = Stopwatch.StartNew();
    private static void Check(bool ok) { checks++; if (!ok) throw new InvalidOperationException("P290_CHECK"); }
    private static void Demand(bool ok) { if (!ok) throw new InvalidOperationException("P290_NATIVE"); }
    private static void Pause(Stopwatch wait)
    {
        if (wait.ElapsedMilliseconds > 4000 || total.ElapsedMilliseconds > 40000) throw new TimeoutException("P290_DEADLINE");
        Thread.Sleep(5);
    }
    private sealed class Handle : Microsoft.Win32.SafeHandles.SafeHandleZeroOrMinusOneIsInvalid
    {
        internal Handle(IntPtr raw) : base(true) { SetHandle(raw); }
        protected override bool ReleaseHandle() { bool ok = CloseHandle(handle); if (!ok) cleanupFailed = true; return ok; }
    }
    [StructLayout(LayoutKind.Sequential)] private struct Luid { internal uint Low; internal int High; }
    [StructLayout(LayoutKind.Sequential)] private struct Statistics
    {
        internal Luid TokenId, AuthenticationId;
        internal long Expiration;
        internal uint Type, Level, Charged, Available, Groups, Privileges;
        internal Luid ModifiedId;
    }
    [StructLayout(LayoutKind.Sequential)] private struct Attributes
    { internal int Length; internal IntPtr Descriptor; internal int Inherit; }
    [DllImport("kernel32.dll", ExactSpelling = true, SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)] private static extern bool CloseHandle(IntPtr h);
    [DllImport("kernel32.dll", ExactSpelling = true)] private static extern IntPtr GetCurrentThread();
    [DllImport("kernel32.dll", ExactSpelling = true)] private static extern IntPtr GetCurrentProcess();
    [DllImport("advapi32.dll", ExactSpelling = true, SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)] private static extern bool OpenProcessToken(IntPtr process, uint access, out IntPtr token);
    [DllImport("advapi32.dll", ExactSpelling = true, SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)] private static extern bool OpenThreadToken(IntPtr thread, uint access, [MarshalAs(UnmanagedType.Bool)] bool self, out IntPtr token);
    [DllImport("advapi32.dll", ExactSpelling = true, SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)] private static extern bool GetTokenInformation(IntPtr token, int kind, IntPtr buffer, uint length, out uint returned);
    [DllImport("advapi32.dll", ExactSpelling = true, SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)] private static extern bool ImpersonateNamedPipeClient(IntPtr pipe);
    [DllImport("advapi32.dll", ExactSpelling = true, SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)] private static extern bool RevertToSelf();
    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, ExactSpelling = true, SetLastError = true)]
    private static extern IntPtr CreateNamedPipeW(string name, uint access, uint mode, uint instances, uint output, uint input, uint timeout, ref Attributes attributes);
    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, ExactSpelling = true, SetLastError = true)]
    private static extern IntPtr CreateFileW(string name, uint access, uint sharing, IntPtr security, uint disposition, uint flags, IntPtr template);
    [DllImport("kernel32.dll", ExactSpelling = true, SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)] private static extern bool ConnectNamedPipe(IntPtr pipe, IntPtr overlapped);
    [DllImport("kernel32.dll", ExactSpelling = true, SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)] private static extern bool DisconnectNamedPipe(IntPtr pipe);
    [DllImport("kernel32.dll", ExactSpelling = true, SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)] private static extern bool SetNamedPipeHandleState(IntPtr pipe, ref uint mode, IntPtr count, IntPtr timeout);
    [DllImport("kernel32.dll", ExactSpelling = true, SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)] private static extern bool ReadFile(IntPtr pipe, byte[] buffer, uint size, out uint read, IntPtr overlapped);
    [DllImport("kernel32.dll", ExactSpelling = true, SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)] private static extern bool WriteFile(IntPtr pipe, byte[] buffer, uint size, out uint written, IntPtr overlapped);
    [DllImport("kernel32.dll", ExactSpelling = true, SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)] private static extern bool PeekNamedPipe(IntPtr pipe, IntPtr buffer, uint size, IntPtr read, out uint available, IntPtr remaining);
    [DllImport("kernel32.dll", ExactSpelling = true, SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)] private static extern bool GetNamedPipeClientProcessId(IntPtr pipe, out uint pid);

    private static void NoThreadToken()
    {
        IntPtr token;
        bool ok = OpenThreadToken(GetCurrentThread(), 8, true, out token);
        int error = Marshal.GetLastWin32Error();
        using (Handle h = new Handle(token)) Demand(!ok && error == 1008 && h.IsInvalid);
    }
    private sealed class Snapshot
    {
        internal readonly SecurityIdentifier User;
        internal readonly Statistics Stats;
        internal readonly int Session;
        internal Snapshot(SecurityIdentifier user, Statistics stats, int session) { User = user; Stats = stats; Session = session; }
    }
    // Parsing occurs ONLY under our own identity, with buffer lifetime and SID bounds checked.
    private static Snapshot Parse(IntPtr user, uint userSize, IntPtr stats, uint statsSize, IntPtr session, uint sessionSize)
    {
        int header = IntPtr.Size == 8 ? 16 : 8;
        Demand(userSize >= header + 8 && userSize <= 4096 && statsSize == 56 && sessionSize == 4);
        long offset = Marshal.ReadIntPtr(user).ToInt64() - user.ToInt64();
        Demand(offset >= header && offset <= userSize - 8);
        byte[] bytes = new byte[(int)userSize]; Marshal.Copy(user, bytes, 0, bytes.Length);
        int length = 8 + 4 * bytes[(int)offset + 1];
        Demand(bytes[(int)offset] == 1 && length <= 68 && offset + length <= userSize);
        return new Snapshot(new SecurityIdentifier(bytes, (int)offset),
            (Statistics)Marshal.PtrToStructure(stats, typeof(Statistics)), Marshal.ReadInt32(session));
    }
    private static unsafe Snapshot HostSnapshot()
    {
        byte* u = stackalloc byte[4096]; byte* s = stackalloc byte[4096]; byte* n = stackalloc byte[4096];
        uint ul, sl, nl; IntPtr raw;
        Demand(OpenProcessToken(GetCurrentProcess(), 8, out raw));
        using (Handle token = new Handle(raw))
        {
            Demand(GetTokenInformation(raw, 1, (IntPtr)u, 4096, out ul));
            Demand(GetTokenInformation(raw, 10, (IntPtr)s, 4096, out sl));
            Demand(GetTokenInformation(raw, 12, (IntPtr)n, 4096, out nl));
            Snapshot host = Parse((IntPtr)u, ul, (IntPtr)s, sl, (IntPtr)n, nl);
            Demand(host.Stats.Type == 1); return host;
        }
    }
    private static unsafe Snapshot CaptureNative(IntPtr pipe, out bool impersonationSucceeded)
    {
        impersonationSucceeded = false;
        NoThreadToken();
        // All allocation/pointer preparation and managed framework work precede impersonation.
        byte* ub = stackalloc byte[4096]; byte* sb = stackalloc byte[4096];
        byte* nb = stackalloc byte[4]; byte* tb = stackalloc byte[4]; byte* lb = stackalloc byte[4];
        IntPtr u = (IntPtr)ub, s = (IntPtr)sb, n = (IntPtr)nb, t = (IntPtr)tb, l = (IntPtr)lb;
        IntPtr thread = GetCurrentThread(), token = IntPtr.Zero;
        uint ul = 0, sl = 0, nl = 0, tl = 0, ll = 0;
        bool impersonated = false, opened = false, queried = false, closed = true;
        try
        {
            // NARROW WINDOW: primitive branches plus these native calls only. No throws/logs/
            // parsing, callbacks, providers, IO, managed helpers, async or scheduling here.
            impersonated = ImpersonateNamedPipeClient(pipe);
            if (impersonated)
            {
                opened = OpenThreadToken(thread, 8, true, out token); // TOKEN_QUERY, OpenAsSelf
                if (opened)
                {
                    queried = GetTokenInformation(token, 1, u, 4096, out ul) &&
                        GetTokenInformation(token, 10, s, 4096, out sl) &&
                        GetTokenInformation(token, 12, n, 4, out nl) &&
                        GetTokenInformation(token, 8, t, 4, out tl) &&
                        GetTokenInformation(token, 9, l, 4, out ll);
                }
            }
        }
        finally
        {
            // Close failure must not prevent reversion. Revert even after failed impersonation.
            try { if (opened) closed = CloseHandle(token); }
            finally { if (!RevertToSelf()) Environment.FailFast("P290_REVERT_FATAL"); }
        }
        // No managed processing before successful revert. ERROR_NO_TOKEN is then mandatory.
        NoThreadToken();
        impersonationSucceeded = impersonated;
        Demand(closed);
        if (!impersonated || !opened || !queried) return null; // No primary-token fallback.
        Demand(tl == 4 && ll == 4 && Marshal.ReadInt32(t) == 2 && Marshal.ReadInt32(l) == 1);
        Snapshot result = Parse(u, ul, s, sl, n, nl);
        Demand(result.Stats.Type == 2 && result.Stats.Level == 1); captures++;
        return result; // identity only, never an authority/capability
    }
    private static string PipePath(string name) { return @"\\.\pipe\" + name; }
    private static void Send(IntPtr pipe, byte value)
    { uint count; Demand(WriteFile(pipe, new byte[] { value }, 1, out count, IntPtr.Zero) && count == 1); }
    private static byte Receive(IntPtr pipe)
    {
        Stopwatch wait = Stopwatch.StartNew(); byte[] bytes = new byte[2];
        for (;;)
        {
            uint read; bool ok = ReadFile(pipe, bytes, 2, out read, IntPtr.Zero);
            int error = Marshal.GetLastWin32Error();
            if (ok && read != 0) { Demand(read == 1); return bytes[0]; } // exact complete one-byte message
            Demand((ok && read == 0) || (!ok && error == 232)); Pause(wait);
        }
    }
    private sealed class Observation
    {
        internal readonly object Epoch;
        internal readonly int Sequence;
        internal readonly long Expires;
        internal readonly Snapshot Token;
        internal bool Used, Cancelled;
        internal Observation(object epoch, int sequence, Snapshot token)
        { Epoch = epoch; Sequence = sequence; Token = token; Expires = Stopwatch.GetTimestamp() + 2 * Stopwatch.Frequency; }
    }
    private sealed class Endpoint : IDisposable
    {
        internal readonly string Name = "p290-" + Guid.NewGuid().ToString("N");
        internal readonly Handle Pipe;
        internal object Epoch;
        internal int Sequence;
        internal long ReadExpires;
        private Child peer;
        internal bool Connected, Fresh, Terminal;
        internal Endpoint(SecurityIdentifier user)
        {
            PipeSecurity security = new PipeSecurity(); security.SetAccessRuleProtection(true, false); security.SetOwner(user);
            security.AddAccessRule(new PipeAccessRule(user, PipeAccessRights.FullControl, AccessControlType.Allow));
            byte[] descriptor = security.GetSecurityDescriptorBinaryForm(); GCHandle pin = GCHandle.Alloc(descriptor, GCHandleType.Pinned);
            try
            {
                Attributes a = new Attributes(); a.Length = Marshal.SizeOf(typeof(Attributes)); a.Descriptor = pin.AddrOfPinnedObject();
                // DUPLEX | FIRST_PIPE_INSTANCE; MESSAGE | READMODE_MESSAGE | NOWAIT | REJECT_REMOTE_CLIENTS
                Pipe = new Handle(CreateNamedPipeW(PipePath(Name), 3 | 0x80000, 4 | 2 | 1 | 8, 1, 64, 64, 0, ref a));
                Demand(!Pipe.IsInvalid);
            }
            finally { pin.Free(); }
            try
            {
                using (Microsoft.Win32.SafeHandles.SafePipeHandle wrapper = new Microsoft.Win32.SafeHandles.SafePipeHandle(Pipe.DangerousGetHandle(), false))
                using (NamedPipeServerStream view = new NamedPipeServerStream(PipeDirection.InOut, false, false, wrapper))
                {
                    PipeSecurity actual = view.GetAccessControl();
                    Demand(actual.AreAccessRulesProtected && user.Equals(actual.GetOwner(typeof(SecurityIdentifier))));
                    AuthorizationRuleCollection rules = actual.GetAccessRules(true, true, typeof(SecurityIdentifier)); Demand(rules.Count == 1);
                    PipeAccessRule rule = (PipeAccessRule)rules[0];
                    Demand(!rule.IsInherited && rule.AccessControlType == AccessControlType.Allow && user.Equals(rule.IdentityReference) &&
                        rule.PipeAccessRights == PipeAccessRights.FullControl);
                }
            }
            catch { Pipe.Dispose(); throw; }
        }
        internal void Connect(Child child)
        {
            Stopwatch wait = Stopwatch.StartNew();
            for (;;)
            {
                bool ok = ConnectNamedPipe(Pipe.DangerousGetHandle(), IntPtr.Zero); int error = Marshal.GetLastWin32Error();
                if (!ok && error == 535) break;
                Demand(ok || error == 536); Pause(wait);
            }
            Epoch = new object(); Sequence = 0; Connected = true; Fresh = Terminal = false;
            peer = child; Demand(ExpectedPeer());
        }
        private bool ExpectedPeer()
        {
            uint pid;
            return peer != null && !peer.Process.HasExited && GetNamedPipeClientProcessId(Pipe.DangerousGetHandle(), out pid) &&
                pid == checked((uint)peer.Process.Id);
        }
        internal void Read(byte expected)
        {
            Fresh = false; // also invalidates a previous read if this read fails
            Demand(Connected && !Terminal);
            try { Demand(Receive(Pipe.DangerousGetHandle()) == expected); Sequence++; ReadExpires = Stopwatch.GetTimestamp() + 2 * Stopwatch.Frequency; Fresh = true; }
            catch { Terminal = true; throw; }
        }
        internal Observation Observe(bool invalidHandleFixture)
        {
            if (!Connected || !Fresh || Terminal) { denials++; return null; }
            Fresh = false; // one attempt only; failure is irreversible for this request/epoch
            if (Stopwatch.GetTimestamp() >= ReadExpires || !ExpectedPeer()) { Terminal = true; denials++; return null; }
            bool impersonated;
            Snapshot token = CaptureNative(invalidHandleFixture ? new IntPtr(-1) : Pipe.DangerousGetHandle(), out impersonated);
            if (invalidHandleFixture) Demand(!impersonated); // distinguish impersonation failure from token-query failure
            if (token == null || Stopwatch.GetTimestamp() >= ReadExpires || !ExpectedPeer()) { Terminal = true; denials++; return null; }
            return new Observation(Epoch, Sequence, token);
        }
        internal bool Consume(Observation o, long now)
        {
            if (o == null || o.Used) { denials++; return false; }
            // Every attempted use burns the observation, including stale/cancelled/expired ones.
            o.Used = true;
            if (!Connected || Terminal || o.Cancelled || !Object.ReferenceEquals(Epoch, o.Epoch) ||
                Sequence != o.Sequence || now >= o.Expires || now >= ReadExpires) { denials++; return false; }
            o.Used = true; return true; // test-only diagnostic acceptance, no effect path exists
        }
        internal void Disconnect()
        { Invalidate(); Demand(DisconnectNamedPipe(Pipe.DangerousGetHandle())); }
        private void Invalidate() { Connected = Fresh = false; Terminal = true; Epoch = null; peer = null; }
        public void Dispose() { Invalidate(); Pipe.Dispose(); }
    }
    private sealed class Child : IDisposable
    {
        internal readonly Process Process;
        internal Child(string endpoint)
        {
            ProcessStartInfo si = new ProcessStartInfo(Assembly.GetExecutingAssembly().Location, "--child " + endpoint);
            si.UseShellExecute = false; si.CreateNoWindow = true; si.EnvironmentVariables.Clear();
            foreach (string key in new[] { "SystemRoot", "WINDIR", "GITHUB_ACTIONS", "RUNNER_ENVIRONMENT", "RUNNER_OS", "ImageOS" })
                si.EnvironmentVariables[key] = Environment.GetEnvironmentVariable(key);
            Process = new Process(); Process.StartInfo = si;
            try { Demand(Process.Start()); } catch { Process.Dispose(); throw; }
        }
        public void Dispose()
        {
            try { if (!Process.HasExited) Process.Kill(); if (!Process.WaitForExit(3000)) cleanupFailed = true; }
            finally { Process.Dispose(); }
        }
    }
    private static int ChildMain(string name)
    {
        Guid parsed;
        if (name.Length != 37 || !name.StartsWith("p290-", StringComparison.Ordinal) || !Guid.TryParseExact(name.Substring(5), "N", out parsed)) return 2;
        NoThreadToken(); Stopwatch wait = Stopwatch.StartNew(); Handle pipe;
        for (;;)
        {
            // SECURITY_SQOS_PRESENT | SECURITY_IDENTIFICATION. No act-on-behalf rights requested.
            pipe = new Handle(CreateFileW(PipePath(name), 0xC0000000, 0, IntPtr.Zero, 3, 0x00110000, IntPtr.Zero));
            if (!pipe.IsInvalid) break;
            int error = Marshal.GetLastWin32Error(); pipe.Dispose(); Demand(error == 2 || error == 231); Pause(wait);
        }
        using (pipe)
        {
            uint mode = 2 | 1; Demand(SetNamedPipeHandleState(pipe.DangerousGetHandle(), ref mode, IntPtr.Zero, IntPtr.Zero));
            for (byte frame = 1; frame <= 4; frame++) { Send(pipe.DangerousGetHandle(), frame); Demand(Receive(pipe.DangerousGetHandle()) == frame + 10); }
        }
        NoThreadToken(); return cleanupFailed ? 1 : 0;
    }
    private static bool SameAccount(Snapshot a, Snapshot b)
    { return a.User.Equals(b.User) && a.Session == b.Session && a.Stats.AuthenticationId.Low == b.Stats.AuthenticationId.Low && a.Stats.AuthenticationId.High == b.Stats.AuthenticationId.High; }
    private static void Experiment()
    {
        Check(Marshal.SizeOf(typeof(Statistics)) == 56 && Marshal.OffsetOf(typeof(Statistics), "ModifiedId").ToInt32() == 48);
        Check(Marshal.SizeOf(typeof(Attributes)) == (IntPtr.Size == 8 ? 24 : 12));
        stage = "BASELINE"; NoThreadToken(); Snapshot host = HostSnapshot();
        if (!RevertToSelf()) Environment.FailFast("P290_REVERT_FATAL"); // pre-resolve; same fatal rule even here
        NoThreadToken();
        stage = "INVALID"; bool impersonated;
        Check(CaptureNative(new IntPtr(-1), out impersonated) == null && !impersonated); NoThreadToken(); // real invalid handle must fail
        stage = "ENDPOINT";
        using (Endpoint e = new Endpoint(host.User))
        {
            Check(e.Observe(false) == null); // unconnected: no native impersonation attempt, no authority
            Observation previous = null;
            for (int round = 0; round < 2; round++)
            using (Child child = new Child(e.Name))
            {
                stage = "CONNECT"; e.Connect(child); Check(e.Observe(false) == null); // connected, no read
                if (previous != null) Check(!e.Consume(previous, Stopwatch.GetTimestamp())); // reconnect epoch
                stage = "QUEUED"; Stopwatch wait = Stopwatch.StartNew(); uint available;
                do { Demand(PeekNamedPipe(e.Pipe.DangerousGetHandle(), IntPtr.Zero, 0, IntPtr.Zero, out available, IntPtr.Zero)); if (available == 0) Pause(wait); } while (available == 0);
                Check(e.Observe(false) == null); // queued bytes are data, NOT a successful read
                stage = "READ"; e.Read(1); Check(!e.Consume(null, Stopwatch.GetTimestamp())); // exact bytes alone still no evidence
                stage = "CAPTURE"; Observation first = e.Observe(false); Check(first != null && SameAccount(host, first.Token));
                Check(e.Observe(false) == null); // missing fresh read, no cached-context reuse
                Check(e.Consume(first, Stopwatch.GetTimestamp())); Check(!e.Consume(first, Stopwatch.GetTimestamp()));
                Send(e.Pipe.DangerousGetHandle(), 11);
                e.Read(2); Check(!e.Consume(first, Stopwatch.GetTimestamp()));
                Observation second = e.Observe(false); Check(second != null && SameAccount(host, second.Token));
                // Explicit policy-only fixtures copied from real evidence; no native identity-change claim.
                Observation staleRead = new Observation(e.Epoch, e.Sequence, second.Token);
                Check(second.Sequence == first.Sequence + 1 && Object.ReferenceEquals(first.Epoch, second.Epoch));
                stage = "POLICY"; Check(!e.Consume(second, second.Expires)); // deterministic policy expiry; no OS expiry assertion
                Check(!e.Consume(second, Stopwatch.GetTimestamp())); // expiry cannot be undone by an earlier clock fixture
                Send(e.Pipe.DangerousGetHandle(), 12); e.Read(3);
                Check(!e.Consume(staleRead, Stopwatch.GetTimestamp())); // newer LAST READ invalidates older sequence
                Observation cancelled = e.Observe(false); Check(cancelled != null && SameAccount(host, cancelled.Token));
                cancelled.Cancelled = true; Check(!e.Consume(cancelled, Stopwatch.GetTimestamp()));
                cancelled.Cancelled = false; Check(!e.Consume(cancelled, Stopwatch.GetTimestamp())); // cancellation stays burned
                Observation reconnectFixture = new Observation(e.Epoch, e.Sequence, cancelled.Token);
                Send(e.Pipe.DangerousGetHandle(), 13); e.Read(4);
                if (round == 0)
                {
                    stage = "EXPIRY";
                    Thread.Sleep(2100); // own identity only: real read freshness deadline expires
                    Check(e.Observe(false) == null && e.Terminal); // deny without querying cached OS context
                }
                else { stage = "FAILED_IMPERSONATION"; Check(e.Observe(true) == null && e.Terminal); } // fresh message + injected invalid native handle
                Check(e.Observe(false) == null && !e.Consume(second, Stopwatch.GetTimestamp())); // no fallback despite own token
                stage = "TEARDOWN"; NoThreadToken(); Send(e.Pipe.DangerousGetHandle(), 14); // fixed teardown ACK, no protected request action
                Check(child.Process.WaitForExit(4000) && child.Process.ExitCode == 0);
                e.Disconnect(); Check(e.Observe(false) == null && !e.Consume(second, Stopwatch.GetTimestamp())); previous = reconnectFixture;
            }
        }
        NoThreadToken(); Check(!cleanupFailed && captures == 6 && denials >= 24);
    }
    public static int Main(string[] args)
    {
        // Accident barriers only. These environment strings are not authentication or a sandbox.
        if (Environment.GetEnvironmentVariable("GITHUB_ACTIONS") != "true" || Environment.GetEnvironmentVariable("RUNNER_ENVIRONMENT") != "github-hosted" ||
            Environment.GetEnvironmentVariable("RUNNER_OS") != "Windows" || Environment.GetEnvironmentVariable("ImageOS") != "win22" ||
            String.Equals(Environment.UserName, "krist", StringComparison.OrdinalIgnoreCase) || String.Equals(Environment.UserName, "Kristian", StringComparison.OrdinalIgnoreCase)) return 2;
        try
        {
            if (args.Length == 2 && args[0] == "--child") return ChildMain(args[1]);
            if (args.Length != 0) return 2;
            Experiment();
            Console.WriteLine("P290_DIAGNOSTIC=PASS CAPTURES=" + captures + " DENIALS=" + denials + " CHECKS=" + checks + " BITS=" + (IntPtr.Size * 8));
            Console.WriteLine("P290_TOKEN=IDENTIFICATION LAST_READ=ORDERED REVERT=CHECKED INVALID_HANDLE=DENIED FALLBACK=DENIED");
            Console.WriteLine("P290_AUTHORITY=NONE PRIVILEGE=UNVERIFIED REAL_KEY=NO_GO PRODUCTION=HOLD P96_ORIGINAL=HIGH_OPEN APPROVALS=0/7 FULL_REGRESSIONS=0/3");
            return 0;
        }
        catch (Exception) { if (args.Length == 0) Console.WriteLine("P290_DIAGNOSTIC=HOLD STAGE=" + stage); return 1; }
    }
}
