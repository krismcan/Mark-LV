#if !DEBUG || RELEASE || !C1_P286_ASYNC_PIPE_REVIEW_ONLY || !C1_P265_DEVELOPMENT_ONLY
#error P286_FOCUSED_TEST_ONLY_DEBUG_AND_OPT_IN_REQUIRED
#endif
using System;
using System.Diagnostics;
using System.IO;
using System.Reflection;
using System.Security.Cryptography;
using System.Threading;
using Nayeon.ByokC1.P265Development;

// Managed completion fakes only; no pipe, credential, ACL or provisioning action.
internal static class AsyncPipeLifetimeTests
{
    private const BindingFlags Hidden = BindingFlags.Instance | BindingFlags.NonPublic;
    private static readonly Type completion = typeof(DevelopmentPipeAdapter).GetNestedType("Completion", BindingFlags.NonPublic);
    private static void Check(bool value) { if (!value) throw new InvalidOperationException("P286_ASSERT"); }
    private sealed class Result : IAsyncResult, IDisposable
    {
        internal readonly ManualResetEvent Event = new ManualResetEvent(false);
        internal bool Signaled;
        internal int Requests;
        public object AsyncState { get { return null; } }
        public bool CompletedSynchronously { get { return false; } }
        public bool IsCompleted { get { return Signaled; } }
        public WaitHandle AsyncWaitHandle
        {
            get { Check(Signaled); Interlocked.Increment(ref Requests); return Event; }
        }
        internal void Signal() { Event.Set(); Signaled = true; }
        public void Dispose() { Event.Dispose(); }
    }
    private static object New(Func<IAsyncResult, int> end)
    { return Activator.CreateInstance(completion, Hidden, null, new object[] { end }, null); }
    private static void Callback(object owner, Result result)
    { completion.GetMethod("Callback", Hidden).Invoke(owner, new object[] { result }); }
    private static int Wait(object owner, Stopwatch elapsed, int timeout)
    {
        try { return (int)completion.GetMethod("Wait", Hidden).Invoke(owner, new object[] { elapsed, timeout }); }
        catch (TargetInvocationException error)
        { System.Runtime.ExceptionServices.ExceptionDispatchInfo.Capture(error.InnerException).Throw(); throw; }
    }
    private static void Timeout(object owner)
    {
        bool timedOut = false;
        try { Wait(owner, Stopwatch.StartNew(), 50); }
        catch (TimeoutException) { timedOut = true; }
        Check(timedOut);
    }
    private static void CompletionSchedules()
    {
        // Deterministic model of P265's observed disposed-pipe precheck: End*
        // throws before waiting, then caller-side using closes the pending event.
        // Capture the later Set failure here; never throw on a thread-pool thread.
        using (var pending = new ManualResetEvent(false))
        {
            bool disposedSignal = false;
            try
            {
                using (WaitHandle prematureOwner = pending)
                    throw new ObjectDisposedException("fake EndWaitForConnection");
            }
            catch (ObjectDisposedException) { }
            try { pending.Set(); }
            catch (ObjectDisposedException) { disposedSignal = true; }
            Check(disposedSignal);
        }
        // All three operation kinds share exactly this helper. Model successful,
        // canceled and faulted End* after signaling, including a late callback.
        foreach (string operation in new[] { "connect", "read", "write" })
        {
            Check(operation.Length > 0);
            for (int mode = 0; mode < 3; mode++)
            using (var result = new Result())
            {
                int ends = 0;
                Exception expected = mode == 1 ? (Exception)new ObjectDisposedException("fake") : new IOException("fake");
                int selected = mode;
                object owner = New(delegate(IAsyncResult ar) {
                    Check(ar == result && result.Signaled && !result.Event.SafeWaitHandle.IsClosed);
                    Interlocked.Increment(ref ends);
                    if (selected != 0) throw expected;
                    return 7;
                });
                // Waiter expiration/cancellation cannot acquire or close an event
                // which the Framework has not finished signaling.
                Timeout(owner);
                Check(ends == 0 && result.Requests == 0 && !result.Event.SafeWaitHandle.IsClosed);
                result.Signal(); Callback(owner, result);
                Check(ends == 1 && result.Requests == 1 && result.Event.SafeWaitHandle.IsClosed);
                if (mode == 0) Check(Wait(owner, Stopwatch.StartNew(), 1000) == 7);
                else
                {
                    Exception observed = null;
                    try { Wait(owner, Stopwatch.StartNew(), 1000); }
                    catch (Exception error) { observed = error; }
                    Check(Object.ReferenceEquals(observed, expected));
                }
            }
        }
        // Completion before the caller begins waiting (also synchronous Begin).
        for (int i = 0; i < 256; i++)
        using (var result = new Result())
        {
            int ends = 0;
            object owner = New(delegate(IAsyncResult ar) { Interlocked.Increment(ref ends); return 1; });
            result.Signal(); Callback(owner, result);
            Check(Wait(owner, Stopwatch.StartNew(), 1000) == 1 && ends == 1 && result.Event.SafeWaitHandle.IsClosed);
        }
        // The publication barrier follows End*, not merely callback entry. The
        // waiter may time out while End is stalled without closing its event.
        using (var entered = new ManualResetEvent(false))
        using (var release = new ManualResetEvent(false))
        using (var result = new Result())
        {
            object owner = New(delegate(IAsyncResult ar) {
                entered.Set(); Check(release.WaitOne(5000)); return 2;
            });
            result.Signal(); Exception callbackError = null;
            var thread = new Thread(delegate() { try { Callback(owner, result); } catch (Exception e) { callbackError = e; } });
            thread.IsBackground = true; thread.Start();
            try
            {
                Check(entered.WaitOne(5000)); Timeout(owner);
                Check(!result.Event.SafeWaitHandle.IsClosed);
            }
            finally { release.Set(); Check(thread.Join(5000)); }
            Check(callbackError == null && result.Event.SafeWaitHandle.IsClosed);
            Check(Wait(owner, Stopwatch.StartNew(), 1000) == 2);
        }
    }
    private static string Mask(string text, string begin, string end, string marker)
    {
        int start = text.IndexOf(begin, StringComparison.Ordinal);
        int finish = text.IndexOf(end, start + begin.Length, StringComparison.Ordinal);
        Check(start >= 0 && finish > start);
        return text.Substring(0, start) + marker + "\n" + text.Substring(finish);
    }
    private static string Normalize(string text, bool successor)
    {
        text = text.Replace("\r\n", "\n");
        const string guard = "#if !DEBUG || RELEASE || !C1_P286_ASYNC_PIPE_REVIEW_ONLY\n#error P286_TEST_ONLY_DEBUG_AND_OPT_IN_REQUIRED\n#endif\n";
        if (successor) { Check(text.StartsWith(guard, StringComparison.Ordinal)); text = text.Substring(guard.Length); }
        text = Mask(text, successor ? "        // TEST ONLY source substitution" : "        // The caller owns the wait handle",
            "        // Fixed little-endian", "ASYNC_HELPER");
        text = Mask(text, successor ? "                var connect =" : "                IAsyncResult connect =",
            "                Guid requestId;", "CONNECT");
        return Mask(text, successor ? "                var write =" : "                IAsyncResult write =",
            "                Remaining(elapsed, timeoutMs);", "WRITE");
    }
    private static void FrozenSource()
    {
        const string path = "native_c1_successor/P265DevelopmentPipeAdapter.cs";
        using (SHA256 sha = SHA256.Create())
            Check(BitConverter.ToString(sha.ComputeHash(File.ReadAllBytes(path))).Replace("-", "") ==
                "CC4065A40E8F7C8DD296EE913533E5AA611EDD2BBBE0D830DA8196A74A440636");
        string original = File.ReadAllText(path);
        string next = File.ReadAllText("native_c1_successor/P286SafeDevelopmentPipeAdapter.cs");
        foreach (string operation in new[] { "connect", "read", "write" })
            Check(original.Contains("using (WaitHandle handle = " + operation + ".AsyncWaitHandle)"));
        Check(Normalize(original, false) == Normalize(next, true));
        // Canary: the comparison must reject a change outside async ownership.
        Check(Normalize(original, false) != Normalize(next.Replace("BodyLength = 24", "BodyLength = 25"), true));
        Check(next.Split(new[] { ".AsyncWaitHandle" }, StringSplitOptions.None).Length == 2);
        Check(next.Contains("pipe.BeginWaitForConnection(connect.Callback, null)") &&
            next.Contains("pipe.BeginRead(buffer, offset, buffer.Length - offset, read.Callback, null)") &&
            next.Contains("pipe.BeginWrite(denial, 0, denial.Length, write.Callback, null)"));
    }
    public static int Main()
    {
        // Accident barrier: this generated test is never authorized on Kristian.
        if (Environment.GetEnvironmentVariable("GITHUB_ACTIONS") != "true" ||
            Environment.GetEnvironmentVariable("RUNNER_ENVIRONMENT") != "github-hosted" ||
            Environment.GetEnvironmentVariable("RUNNER_OS") != "Windows" ||
            String.Equals(Environment.UserName, "krist", StringComparison.OrdinalIgnoreCase) ||
            String.Equals(Environment.UserName, "Kristian", StringComparison.OrdinalIgnoreCase)) return 2;
        try { FrozenSource(); CompletionSchedules(); Console.WriteLine("P286_FOCUSED=PASS"); return 0; }
        catch (Exception) { Console.WriteLine("P286_FOCUSED=HOLD"); return 1; }
    }
}
