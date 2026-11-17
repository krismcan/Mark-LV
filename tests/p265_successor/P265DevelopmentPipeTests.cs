#if !C1_P265_DEVELOPMENT_ONLY
#error P265_TESTS_REQUIRE_DEVELOPMENT_BUILD
#endif
#if !DEBUG
#error P265_TESTS_NO_RELEASE_BUILD
#endif
// Run ONLY on the explicitly permitted disposable Windows runner. No SCM/credential work.
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.IO.Pipes;
using System.Reflection;
using System.Reflection.Emit;
using System.Runtime.InteropServices;
using System.Security.AccessControl;
using System.Security.Principal;
using System.Threading;

internal static class P265DevelopmentPipeTests
{
    private const BindingFlags Hidden = BindingFlags.Instance | BindingFlags.NonPublic;
    private static Type adapterType;
    private static int assertions;
    private static void Need(bool condition)
    { assertions++; if (!condition) throw new InvalidOperationException("P265_TEST_FAILED_" + assertions); }
    private static object Field(object value, string name)
    { return value.GetType().GetField(name, Hidden).GetValue(value); }
    private static object NewAdapter()
    {
        using (WindowsIdentity expected = WindowsIdentity.GetCurrent())
            return Activator.CreateInstance(adapterType, Hidden, null, new object[] { expected }, null);
    }
    private static object Serve(object adapter, int timeout)
    { return adapterType.GetMethod("ServeOnce", Hidden).Invoke(adapter, new object[] { timeout }); }
    private static void Close(object adapter) { ((IDisposable)adapter).Dispose(); }
    private static string Reason(object result) { return Field(result, "Reason").ToString(); }
    private static void Denied(object result)
    {
        Need(result != null);
        foreach (string name in new[] { "CredentialAllowed", "StoreAllowed", "PrivilegedAllowed", "ProductionEligible" })
            Need(!(bool)result.GetType().GetProperty(name, Hidden).GetValue(result, null));
    }
    private static byte[] Frame(Guid id, byte operation)
    {
        byte[] frame = new byte[28];
        frame[0] = 24; frame[4] = 67; frame[5] = 49; frame[6] = 80; frame[7] = 53;
        frame[8] = 1; frame[9] = operation;
        Buffer.BlockCopy(id.ToByteArray(), 0, frame, 12, 16);
        return frame;
    }
    private static void Complete(IAsyncResult pending, Action finish)
    {
        using (WaitHandle wait = pending.AsyncWaitHandle) Need(wait.WaitOne(3000));
        finish();
    }
    private static NamedPipeClientStream Connect(object adapter, TokenImpersonationLevel level)
    {
        var client = new NamedPipeClientStream(".", (string)Field(adapter, "Endpoint"),
            PipeDirection.InOut, PipeOptions.Asynchronous, level);
        try { client.Connect(1000); return client; }
        catch { client.Dispose(); throw; }
    }
    private static void Write(NamedPipeClientStream client, byte[] frame)
    {
        IAsyncResult write = client.BeginWrite(frame, 0, frame.Length, null, null);
        Complete(write, delegate { client.EndWrite(write); });
    }
    private static byte[] Reply(NamedPipeClientStream client, byte[] delivery)
    {
        byte[] reply = new byte[8];
        int offset = 0;
        while (offset < reply.Length)
        {
            IAsyncResult read = client.BeginRead(reply, offset, reply.Length - offset, null, null);
            int count = 0;
            Complete(read, delegate { count = client.EndRead(read); });
            Need(count > 0); offset += count;
        }
        Need(BitConverter.ToString(reply) == "43-31-44-4E-01-01-00-00");
        if (delivery != null) Write(client, delivery); // bounded delivery marker, never consent
        return reply;
    }

    // Server failures propagate to the driver; all waits and joins have deadlines.
    private static object Exchange(object adapter, byte[] frame, TokenImpersonationLevel level, bool expectReply, bool waitForRefusal = false)
    {
        object result = null; Exception failure = null;
        var server = new Thread(delegate()
        { try { result = Serve(adapter, 2000); } catch (Exception error) { failure = error; } });
        server.IsBackground = true; server.Start();
        try
        {
            using (NamedPipeClientStream client = Connect(adapter, level))
            {
                try { Write(client, frame); }
                catch (IOException) { if (!waitForRefusal) throw; } // malformed-frame close may win the write
                if (expectReply) Reply(client, new byte[] { 165 });
                else if (waitForRefusal) Need(server.Join(4000));
            }
        }
        finally
        {
            if (!server.Join(4000)) { Close(adapter); throw new InvalidOperationException("P265_SERVER_TIMEOUT"); }
        }
        Need(failure == null); Denied(result);
        return result;
    }
    private static object Exchange(object adapter, byte[] frame)
    { return Exchange(adapter, frame, TokenImpersonationLevel.Impersonation, true); }
    private static object RejectFrame(object adapter, byte[] frame)
    { return Exchange(adapter, frame, TokenImpersonationLevel.Impersonation, false, true); }

    private static void SecurityAndProtocolTests()
    {
        object adapter = NewAdapter();
        try
        {
            string endpoint = (string)Field(adapter, "Endpoint");
            Need(endpoint.StartsWith("Nayeon-P265-dev-", StringComparison.Ordinal) && endpoint.Length == 48);
            var pipe = (NamedPipeServerStream)Field(adapter, "pipe");
            PipeSecurity acl = pipe.GetAccessControl(); // inspect the ACTUAL kernel object's descriptor
            Need(acl.AreAccessRulesProtected);
            using (WindowsIdentity current = WindowsIdentity.GetCurrent())
            {
                Need(acl.GetOwner(typeof(SecurityIdentifier)).Equals(current.User));
                AuthorizationRuleCollection rules = acl.GetAccessRules(true, true, typeof(SecurityIdentifier));
                Need(rules.Count == 2);
                int allows = 0, denies = 0;
                foreach (PipeAccessRule rule in rules)
                {
                    Need(!rule.IsInherited);
                    if (rule.AccessControlType == AccessControlType.Allow)
                    {
                        allows++; Need(rule.IdentityReference.Equals(current.User));
                        Need(rule.PipeAccessRights == (PipeAccessRights.ReadWrite |
                            PipeAccessRights.Synchronize)); // .NET's implicit allow-rule right only
                    }
                    else
                    {
                        denies++; Need(rule.IdentityReference.Equals(new SecurityIdentifier(WellKnownSidType.NetworkSid, null)));
                        Need(rule.PipeAccessRights == PipeAccessRights.FullControl);
                    }
                }
                Need(allows == 1 && denies == 1);
                MethodInfo sameSid = adapterType.GetMethod("SameSid", BindingFlags.Static | BindingFlags.NonPublic);
                Need((bool)sameSid.Invoke(null, new object[] { current.User, current.User }));
                Need(!(bool)sameSid.Invoke(null, new object[] { new SecurityIdentifier(WellKnownSidType.NullSid, null), current.User }));
                Need(!(bool)sameSid.Invoke(null, new object[] { null, current.User }));
            }
            foreach (byte operation in new byte[] { 1, 2, 3, 4 })
            {
                object evidence = Exchange(adapter, Frame(Guid.NewGuid(), operation));
                Need(Reason(evidence) == "DevelopmentHold");
                Need((bool)Field(evidence, "PeerObserved") && (bool)Field(evidence, "SidMatched"));
                Need((bool)Field(evidence, "ThreadRestored") && (bool)Field(evidence, "ReplyWritten"));
            }
            Guid replay = Guid.NewGuid();
            Need(Reason(Exchange(adapter, Frame(replay, 2))) == "DevelopmentHold");
            Need(Reason(Exchange(adapter, Frame(replay, 2))) == "Replay");
            Need(Reason(Exchange(adapter, Frame(replay, 3))) == "Replay"); // altered operation, same reserved ID
            byte[] valid = Frame(Guid.NewGuid(), 1);
            foreach (int offset in new[] { 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11 })
            {
                byte[] malformed = (byte[])valid.Clone(); malformed[offset] = 255;
                Need(Reason(RejectFrame(adapter, malformed)) == "InvalidFrame");
            }
            Need(Reason(RejectFrame(adapter, Frame(Guid.Empty, 1))) == "InvalidFrame");
            byte[] oversized = new byte[256]; Buffer.BlockCopy(valid, 0, oversized, 0, valid.Length);
            oversized[0] = 252; Need(Reason(RejectFrame(adapter, oversized)) == "InvalidFrame");
            // A valid frame plus claimed SID text is NOT an identity-bearing extension.
            byte[] spoof = new byte[64]; Buffer.BlockCopy(valid, 0, spoof, 0, valid.Length);
            byte[] text = System.Text.Encoding.ASCII.GetBytes("SID=S-1-5-18;approved=true");
            Buffer.BlockCopy(text, 0, spoof, valid.Length, text.Length);
            Need(Reason(RejectFrame(adapter, spoof)) == "InvalidFrame");
            byte[] duplicate = new byte[56]; Buffer.BlockCopy(valid, 0, duplicate, 0, 28);
            Buffer.BlockCopy(valid, 0, duplicate, 28, 28);
            Need(Reason(RejectFrame(adapter, duplicate)) == "InvalidFrame");
            for (int index = 0; index < 128; index++) Exchange(adapter, Frame(Guid.NewGuid(), 4));
            Need(Reason(Exchange(adapter, Frame(Guid.NewGuid(), 1))) == "Capacity");
            Need(Reason(Exchange(adapter, Frame(replay, 2))) == "Replay"); // no eviction at saturation
        }
        finally { Close(adapter); Close(adapter); }
        Denied(Serve(adapter, 100)); Need(Reason(Serve(adapter, 100)) == "Closed");
    }

    private static void AdverseTransportTests()
    {
        // Idle connect and partial header/body are bounded and terminal. No disconnect can reopen.
        foreach (int partial in new[] { -1, 0, 2, 10 })
        {
            object adapter = NewAdapter(); object evidence = null; Exception failure = null;
            var server = new Thread(delegate()
            { try { evidence = Serve(adapter, 300); } catch (Exception error) { failure = error; } });
            server.IsBackground = true;
            Stopwatch elapsed = Stopwatch.StartNew(); server.Start();
            try
            {
                if (partial >= 0)
                {
                    using (NamedPipeClientStream client = Connect(adapter, TokenImpersonationLevel.Impersonation))
                    {
                        if (partial > 0)
                        {
                            byte[] bytes = new byte[partial];
                            Buffer.BlockCopy(Frame(Guid.NewGuid(), 1), 0, bytes, 0, partial); Write(client, bytes);
                        }
                        Need(server.Join(3000)); // client stays connected but never finishes the frame
                    }
                }
                else Need(server.Join(3000));
                Need(failure == null && elapsed.ElapsedMilliseconds < 3500);
                Denied(evidence); Need(Reason(evidence) == "Timeout");
                Need(Reason(Serve(adapter, 100)) == "Closed");
            }
            finally { Close(adapter); Need(server.Join(3000)); }
        }
        // Disconnection mid-frame and an Identification-only peer never gain authority.
        foreach (bool disconnect in new[] { true, false })
        {
            object adapter = NewAdapter();
            try
            {
                if (disconnect)
                {
                    object result = Exchange(adapter, new byte[] { 24, 0 }, TokenImpersonationLevel.Impersonation, false);
                    Need(Reason(result) == "Disconnected");
                }
                else
                {
                    object result = Exchange(adapter, Frame(Guid.NewGuid(), 2), TokenImpersonationLevel.Identification, true);
                    Need(Reason(result) == "PeerRejected" && !(bool)Field(result, "SidMatched"));
                    Need((bool)Field(result, "ThreadRestored"));
                }
            }
            finally { Close(adapter); }
        }
        // Concurrent ingress fails immediately, disposal interrupts the waiting OS operation.
        object waiting = NewAdapter(); object first = null; Exception errorFirst = null;
        var worker = new Thread(delegate()
        { try { first = Serve(waiting, 2000); } catch (Exception error) { errorFirst = error; } });
        worker.IsBackground = true; worker.Start();
        try
        {
            Need(SpinWait.SpinUntil(delegate { return (int)Field(waiting, "serving") == 1; }, 1000));
            object busy = Serve(waiting, 100); Denied(busy); Need(Reason(busy) == "Busy");
        }
        finally { Close(waiting); Need(worker.Join(3000)); }
        Need(errorFirst == null); Denied(first); Need(Reason(first) == "Closed" || Reason(first) == "Disconnected");
    }

    private static void ProvisioningAndThreadTests()
    {
        try
        {
            Activator.CreateInstance(adapterType, Hidden, null, new object[] { null }, null); Need(false);
        }
        catch (TargetInvocationException error) { Need(error.InnerException is ArgumentException); }
        object first = NewAdapter(), second = NewAdapter();
        try { Need((string)Field(first, "Endpoint") != (string)Field(second, "Endpoint")); }
        finally { Close(first); Close(second); }
        object adapter = NewAdapter();
        try
        {
            using (WindowsIdentity current = WindowsIdentity.GetCurrent())
            using (WindowsImpersonationContext context = current.Impersonate())
            {
                using (WindowsIdentity thread = WindowsIdentity.GetCurrent(true)) Need(thread != null);
                try { NewAdapter(); Need(false); }
                catch (TargetInvocationException error) { Need(error.InnerException is System.Security.SecurityException); }
                object evidence = Serve(adapter, 100);
                Denied(evidence); Need(Reason(evidence) == "Fault");
                Need(!(bool)Field(evidence, "ReplyWritten"));
            }
            using (WindowsIdentity thread = WindowsIdentity.GetCurrent(true)) Need(thread == null);
            Need(Reason(Serve(adapter, 100)) == "Closed");
        }
        finally { Close(adapter); }
    }

    private static void DeliveryTests()
    {
        // No drain can wait forever; a second request can never serve as a delivery marker.
        foreach (byte[] marker in new[] { null, new byte[] { 0 }, new byte[] { 165, 165 }, Frame(Guid.NewGuid(), 2) })
        {
            object adapter = NewAdapter(); object evidence = null; Exception failure = null;
            var worker = new Thread(delegate()
            { try { evidence = Serve(adapter, 1000); } catch (Exception error) { failure = error; } });
            worker.IsBackground = true; worker.Start();
            try
            {
                using (NamedPipeClientStream client = Connect(adapter, TokenImpersonationLevel.Impersonation))
                {
                    Write(client, Frame(Guid.NewGuid(), 4)); Reply(client, marker);
                    Need(worker.Join(3000));
                }
                Need(failure == null); Denied(evidence);
                Need(Reason(evidence) == (marker == null ? "Timeout" : "InvalidFrame"));
            }
            finally { Close(adapter); Need(worker.Join(3000)); }
        }
    }

    private static void AuditAssembly(Assembly candidate)
    {
        Need(candidate.EntryPoint == null); // library adapter: no SCM or standalone production entrypoint
        foreach (AssemblyName reference in candidate.GetReferencedAssemblies())
            Need(reference.Name == "mscorlib" || reference.Name == "System" || reference.Name == "System.Core");
        var codes = new Dictionary<ushort, OpCode>();
        foreach (FieldInfo field in typeof(OpCodes).GetFields(BindingFlags.Public | BindingFlags.Static))
            if (field.FieldType == typeof(OpCode))
            { OpCode code = (OpCode)field.GetValue(null); codes[unchecked((ushort)code.Value)] = code; }
        var allowed = new HashSet<string>(new[] {
            "System.Object", "System.String", "System.Environment", "System.OperatingSystem", "System.Guid",
            "System.Buffer", "System.Diagnostics.Stopwatch", "System.Threading.Interlocked", "System.Threading.WaitHandle",
            "System.IAsyncResult", "System.IDisposable", "System.AsyncCallback", "System.IO.Stream",
            "System.IO.Pipes.NamedPipeServerStream", "System.IO.Pipes.PipeStream", "System.IO.Pipes.PipeStreamImpersonationWorker",
            "System.IO.Pipes.PipeSecurity", "System.IO.Pipes.PipeAccessRule", "System.Security.Principal.WindowsIdentity",
            "System.Security.Principal.SecurityIdentifier", "System.Security.AccessControl.ObjectSecurity",
            "System.Security.AccessControl.NativeObjectSecurity", "System.Security.AccessControl.CommonObjectSecurity",
            "System.ArgumentException", "System.ArgumentOutOfRangeException", "System.PlatformNotSupportedException",
            "System.TimeoutException", "System.IO.EndOfStreamException", "System.Security.SecurityException"
        });
        int runAsClient = 0, tokenReads = 0;
        foreach (Type type in candidate.GetTypes())
        {
            var methods = new List<MethodBase>(type.GetMethods(BindingFlags.DeclaredOnly | Hidden | BindingFlags.Public | BindingFlags.Static));
            methods.AddRange(type.GetConstructors(BindingFlags.DeclaredOnly | Hidden | BindingFlags.Public | BindingFlags.Static));
            foreach (MethodBase method in methods)
            {
                Need((method.Attributes & MethodAttributes.PinvokeImpl) == 0 && !method.IsDefined(typeof(DllImportAttribute), false));
                Need((method.GetMethodImplementationFlags() & (MethodImplAttributes.CodeTypeMask |
                    MethodImplAttributes.ManagedMask | MethodImplAttributes.InternalCall)) == MethodImplAttributes.IL);
                MethodBody body = method.GetMethodBody();
                if (body == null) { Need(type.IsEnum); continue; }
                byte[] il = body.GetILAsByteArray();
                for (int cursor = 0; cursor < il.Length; )
                {
                    ushort key = il[cursor++]; if (key == 0xfe) key = (ushort)(0xfe00 | il[cursor++]);
                    OpCode code = codes[key]; Need(code != OpCodes.Calli);
                    int size;
                    switch (code.OperandType)
                    {
                        case OperandType.InlineNone: size = 0; break;
                        case OperandType.ShortInlineBrTarget: case OperandType.ShortInlineI: case OperandType.ShortInlineVar: size = 1; break;
                        case OperandType.InlineVar: size = 2; break;
                        case OperandType.InlineI8: case OperandType.InlineR: size = 8; break;
                        case OperandType.InlineSwitch: size = 4 + 4 * BitConverter.ToInt32(il, cursor); break;
                        default: size = 4; break;
                    }
                    if (code.OperandType == OperandType.InlineMethod)
                    {
                        MethodBase called = candidate.ManifestModule.ResolveMethod(BitConverter.ToInt32(il, cursor));
                        Type declaring = called.DeclaringType;
                        if (declaring.Assembly != candidate)
                        {
                            bool guidSet = declaring.IsGenericType && declaring.GetGenericTypeDefinition() == typeof(HashSet<>) &&
                                declaring.GetGenericArguments()[0] == typeof(Guid);
                            bool arrayInitializer = declaring == typeof(System.Runtime.CompilerServices.RuntimeHelpers) &&
                                called.Name == "InitializeArray";
                            Need(allowed.Contains(declaring.FullName) || guidSet || arrayInitializer);
                            if (declaring == typeof(WindowsIdentity))
                            {
                                Need(called.Name == "GetCurrent" || called.Name == "get_User" || called.Name == "get_IsAnonymous" ||
                                    called.Name == "get_ImpersonationLevel" || called.Name == "Dispose");
                                if (called.Name == "GetCurrent") tokenReads++;
                            }
                            if (called.Name == "RunAsClient") runAsClient++;
                        }
                    }
                    cursor += size;
                }
            }
        }
        Need(runAsClient == 1 && tokenReads >= 3);
    }

    private static int Main(string[] arguments)
    {
        if (arguments.Length != 2 || arguments[0] != "--permitted-disposable-runner") return 64;
        // Do not use reflection/another loader to evade any blocked image. Both artifacts must be admitted.
        Assembly candidate = Assembly.LoadFrom(arguments[1]);
        AuditAssembly(candidate); // audit exact loaded dependency/effect closure BEFORE constructing a pipe
        adapterType = candidate.GetType("Nayeon.ByokC1.P265Development.DevelopmentPipeAdapter", true);
        SecurityAndProtocolTests(); AdverseTransportTests(); ProvisioningAndThreadTests(); DeliveryTests();
        Console.WriteLine("P265_NATIVE_TESTS=PASS ASSERTIONS=" + assertions + " BITS=" + (IntPtr.Size * 8));
        Console.WriteLine("P265_SAME_SID_APP_TRUST=UNTRUSTED P96=HOLD REAL_KEY=HOLD PRODUCTION=HOLD");
        return 0;
    }
}
