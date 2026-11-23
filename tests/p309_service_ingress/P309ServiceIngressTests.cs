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
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using System.Xml;
using Nayeon.ByokC1.Service;

internal static class P309ServiceIngressTests
{
    private const BindingFlags Hidden = BindingFlags.Instance | BindingFlags.NonPublic;
    private static int checks;
    private static void Check(bool value)
    { int n = Interlocked.Increment(ref checks); if (!value) throw new Exception("P309 assertion " + n); }
    private static string Name() { return "P309.Disposable." + Guid.NewGuid().ToString("N"); }
    private static void Done(Task task) { Check(task.Wait(5000)); }
    private static FieldInfo Field(Type type, string name)
    {
        FieldInfo field = type.GetField(name, Hidden);
        Check(field != null && field.IsPrivate);
        return field;
    }
    private static ulong HighWater(SyntheticTransactionOwner owner)
    { return (ulong)Field(typeof(SyntheticTransactionOwner), "highWater").GetValue(owner); }
    private static SyntheticTransactionRequest Request(SyntheticTransactionOwner owner, ulong id)
    {
        SyntheticTransactionResult state = owner.Observe();
        return new SyntheticTransactionRequest(state.Owner, state.Epoch, id, SyntheticOperation.Add);
    }
    private static byte[] Frame(ulong id, byte operation)
    {
        byte[] bytes = new byte[13];
        bytes[0] = 67; bytes[1] = 49; bytes[2] = 84; bytes[3] = 49;
        for (int i = 0; i < 8; i++) bytes[4 + i] = (byte)(id >> (8 * i));
        bytes[12] = operation;
        return bytes;
    }
    private static NamedPipeClientStream Client(string name)
    {
        var client = new NamedPipeClientStream(".", name, PipeDirection.InOut,
            PipeOptions.Asynchronous, TokenImpersonationLevel.Anonymous);
        try { client.Connect(1000); client.ReadMode = PipeTransmissionMode.Message; return client; }
        catch { client.Dispose(); throw; }
    }
    private static void Write(NamedPipeClientStream client, byte[] bytes)
    { Done(Bounded(client.WriteAsync(bytes, 0, bytes.Length), client)); }
    private static async Task Bounded(Task operation, IDisposable pipe)
    {
        using (var timer = new CancellationTokenSource())
        {
            try
            {
                if (await Task.WhenAny(operation, Task.Delay(2000, timer.Token)) != operation)
                {
                    pipe.Dispose();
                    try { await operation; }
                    catch (IOException) { }
                    catch (ObjectDisposedException) { }
                    catch (OperationCanceledException) { }
                    throw new TimeoutException("Test I/O deadline; HOLD.");
                }
                await operation;
            }
            finally { timer.Cancel(); }
        }
    }
    private static string Read(NamedPipeClientStream client)
    {
        byte[] bytes = new byte[128];
        Task<int> read = client.ReadAsync(bytes, 0, bytes.Length);
        Done(Bounded(read, client));
        Check(client.IsMessageComplete);
        return Encoding.ASCII.GetString(bytes, 0, read.Result);
    }
    private static void NoReply(NamedPipeClientStream client)
    {
        byte[] bytes = new byte[128];
        try
        {
            Task<int> read = client.ReadAsync(bytes, 0, bytes.Length);
            Done(Bounded(read, client));
            Check(read.Result == 0);
        }
        catch (IOException) { }
        catch (AggregateException error)
        {
            Check(error.InnerException is IOException || error.InnerException is ObjectDisposedException);
        }
        // A timeout is a test failure here: all callers first retire the server.
    }
    private static void Unavailable(string name)
    {
        using (var client = new NamedPipeClientStream(".", name, PipeDirection.InOut,
            PipeOptions.Asynchronous, TokenImpersonationLevel.Anonymous))
        {
            bool refused = false;
            try { client.Connect(100); }
            catch (TimeoutException) { refused = true; }
            catch (IOException) { refused = true; }
            Check(refused);
        }
    }
    private static void Acl(PipeSecurity security)
    {
        SecurityIdentifier sid = CustodyService.ReadProcessSid();
        Check(security.AreAccessRulesProtected && security.GetOwner(typeof(SecurityIdentifier)).Equals(sid));
        AuthorizationRuleCollection rules = security.GetAccessRules(true, true, typeof(SecurityIdentifier));
        Check(rules.Count == 2);
        int allow = 0, deny = 0;
        foreach (PipeAccessRule rule in rules)
        {
            Check(!rule.IsInherited);
            if (rule.AccessControlType == AccessControlType.Allow)
            {
                Check(rule.IdentityReference.Equals(sid) &&
                    (rule.PipeAccessRights & ~PipeAccessRights.Synchronize) == PipeAccessRights.ReadWrite);
                allow++;
            }
            else
            {
                Check(rule.IdentityReference.Equals(new SecurityIdentifier(WellKnownSidType.NetworkSid, null)) &&
                    rule.PipeAccessRights == PipeAccessRights.FullControl);
                deny++;
            }
        }
        Check(allow == 1 && deny == 1);
    }
    private static void Exact()
    {
        foreach (byte operation in new byte[] { 1, 2, 3 })
        using (var owner = new SyntheticTransactionOwner())
        {
            string name = Name();
            using (var server = new SyntheticIngressServer(owner, name))
            using (var client = Client(name))
            {
                Check(object.ReferenceEquals(Field(typeof(SyntheticIngressServer), "owner").GetValue(server), owner));
                Acl(client.GetAccessControl());
                // Explicit little-endian asymmetric bytes and the complete unsigned range.
                ulong id = operation == 3 ? ulong.MaxValue : 0x0102030405060708UL;
                Write(client, Frame(id, operation));
                Check(Read(client) == "C1|DENIED|HOLD|NO_CREDENTIALS");
                Done(server.Completion); Check(!server.Refused);
                Check(HighWater(owner) == id && owner.Observe().State == TransactionOwnerState.ActiveDenied);
                Check(owner.Deny(Request(owner, id)).Disposition == TransactionDisposition.Replay);
                Unavailable(name); // One connected instance; never a second listener.
                // A second frame on this connection has no consumer and no second reply.
                Write(client, Frame(id, operation));
                Check(HighWater(owner) == id);
                server.Dispose();
                NoReply(client);
                Check(owner.Observe().Epoch == 2 && owner.Observe().State == TransactionOwnerState.Stopped);
                server.Dispose();
            }
            Unavailable(name);
        }
    }
    private static void Malformed(byte[] frame)
    {
        string name = Name();
        using (var owner = new SyntheticTransactionOwner())
        using (var server = new SyntheticIngressServer(owner, name))
        {
            using (var client = Client(name))
            {
                Write(client, frame);
                Done(server.Completion); Check(server.Refused);
                Check(HighWater(owner) == 0 && owner.Observe().State == TransactionOwnerState.Faulted);
                NoReply(client);
            }
            Unavailable(name);
        }
    }
    private static void Negatives()
    {
        byte[] wrong = Frame(1, 1); wrong[3] = 48; Malformed(wrong);
        Malformed(Encoding.ASCII.GetBytes("C1T1"));
        byte[] partial = new byte[12]; Array.Copy(Frame(1, 1), partial, 12); Malformed(partial);
        Malformed(new byte[14]);
        byte[] oversize = new byte[256]; Array.Copy(Frame(1, 1), oversize, 13); Malformed(oversize);
        Malformed(Frame(0, 1));
        Malformed(Frame(1, 0)); Malformed(Frame(1, 4)); Malformed(Frame(1, 255));

        // Replay is refused by the exact supplied owner's existing high-water mark.
        using (var owner = new SyntheticTransactionOwner())
        {
            Check(owner.Cancel(Request(owner, 9)).Disposition == TransactionDisposition.Cancelled);
            string name = Name();
            using (var server = new SyntheticIngressServer(owner, name))
            using (var client = Client(name))
            {
                Write(client, Frame(9, 2)); Done(server.Completion);
                Check(server.Refused && HighWater(owner) == 9);
                Check(owner.Observe().State == TransactionOwnerState.Faulted); NoReply(client);
            }
        }
        for (int mode = 0; mode < 2; mode++)
        using (var owner = new SyntheticTransactionOwner())
        {
            string name = Name();
            using (var server = new SyntheticIngressServer(owner, name))
            {
                // Connected disconnect or empty/silent peer; absence is valid idle.
                using (var client = Client(name))
                {
                    if (mode == 0) client.Dispose();
                    else Write(client, new byte[0]);
                    Done(server.Completion); Check(server.Refused);
                    if (mode == 1) NoReply(client);
                }
                Check(HighWater(owner) == 0 && owner.Observe().State == TransactionOwnerState.Faulted);
            }
            Unavailable(name);
        }
        using (var owner = new SyntheticTransactionOwner())
        {
            owner.Stop();
            bool refused = false;
            try { using (var server = new SyntheticIngressServer(owner, Name())) { Check(false); } }
            catch (InvalidOperationException) { refused = true; }
            Check(refused && owner.Observe().State == TransactionOwnerState.Stopped && HighWater(owner) == 0);
        }
        foreach (string name in new[] { null, "", SyntheticIngressServer.Endpoint,
            "other", "P309.Disposable." + Guid.Empty.ToString("N"), "P309.Disposable.abc\\path" })
        using (var owner = new SyntheticTransactionOwner())
        {
            bool refused = false;
            try { using (var server = new SyntheticIngressServer(owner, name)) { Check(false); } }
            catch (ArgumentException) { refused = true; }
            Check(refused && HighWater(owner) == 0);
        }
        // Same-user thread impersonation is still refused; no privileged token required.
        using (var owner = new SyntheticTransactionOwner())
        using (WindowsIdentity identity = WindowsIdentity.GetCurrent())
        {
            string name = Name();
            bool refused = false;
            using (identity.Impersonate())
            {
                try { using (var server = new SyntheticIngressServer(owner, name)) { Check(false); } }
                catch (InvalidOperationException) { refused = true; }
            }
            Check(refused && owner.Observe().State == TransactionOwnerState.Faulted);
            Unavailable(name);
        }
        CustodyService.RequireNoImpersonation();
        using (var service = (CustodyService)Activator.CreateInstance(typeof(CustodyService), true))
        {
            Close(service, 0); // Stop before startup; terminal check precedes native access.
            try
            {
                typeof(CustodyService).GetMethod("OnStart", Hidden).Invoke(service,
                    new object[] { new string[0] }); Check(false);
            }
            catch (TargetInvocationException error) { Check(error.InnerException is InvalidOperationException); }
            Check(service.ExitCode == 1 && Field(typeof(CustodyService), "transactions").GetValue(service) == null &&
                Field(typeof(CustodyService), "syntheticIngress").GetValue(service) == null);
        }
    }

    private static void IdleAccept()
    {
        string name = Name();
        using (var owner = new SyntheticTransactionOwner())
        using (var server = new SyntheticIngressServer(owner, name))
        {
            var idle = Stopwatch.StartNew();
            Check(!server.Completion.Wait(3600));
            Check(idle.ElapsedMilliseconds >= 3500);
            Check(!server.Completion.IsCompleted && !server.Refused && HighWater(owner) == 0);
            Check(owner.Observe().State == TransactionOwnerState.ActiveDenied && owner.Observe().Epoch == 1);
            using (var client = Client(name))
            {
                Write(client, Frame(123, 1));
                Check(Read(client) == "C1|DENIED|HOLD|NO_CREDENTIALS");
                Done(server.Completion);
                Check(!server.Refused && HighWater(owner) == 123 &&
                    owner.Observe().State == TransactionOwnerState.ActiveDenied);
            }
        }
        Unavailable(name);

        // Separate no-client direct disposal: no connection can wake the accept.
        name = Name();
        using (var owner = new SyntheticTransactionOwner())
        using (var server = new SyntheticIngressServer(owner, name))
        {
            var handle = ((NamedPipeServerStream)Field(typeof(SyntheticIngressServer), "pipe").GetValue(server)).SafePipeHandle;
            Check(!server.Completion.IsCompleted && !handle.IsClosed);
            var elapsed = Stopwatch.StartNew();
            Task close = Task.Run(delegate { server.Dispose(); });
            Check(close.Wait(3000) && elapsed.ElapsedMilliseconds < 3000);
            Check(server.Completion.IsCompleted && handle.IsClosed && HighWater(owner) == 0 &&
                owner.Observe().State == TransactionOwnerState.Stopped);
            Unavailable(name);
        }
    }

    private static void Close(CustodyService service, int mode)
    {
        if (mode == 2) { service.Dispose(); return; }
        if (mode == 3)
        {
            typeof(CustodyService).GetMethod("Dispose", Hidden, null, new[] { typeof(bool) }, null)
                .Invoke(service, new object[] { false }); return;
        }
        if (mode == 4)
        {
            try
            {
                // Invalid args refuse before native identity/SCM access, as in P306/P307.
                typeof(CustodyService).GetMethod("OnStart", Hidden).Invoke(service,
                    new object[] { new[] { "synthetic-invalid" } }); Check(false);
            }
            catch (TargetInvocationException error) { Check(error.InnerException is InvalidOperationException); }
            Check(service.ExitCode == 1); return;
        }
        typeof(CustodyService).GetMethod(mode == 0 ? "OnStop" : "OnShutdown", Hidden).Invoke(service, null);
    }
    private static void Retirement()
    {
        for (int mode = 0; mode < 5; mode++)
        for (int connected = 0; connected < 2; connected++)
        {
            string name = Name(), statusName = "p309-status-" + Guid.NewGuid().ToString("N");
            using (var service = (CustodyService)Activator.CreateInstance(typeof(CustodyService), true))
            using (var owner = new SyntheticTransactionOwner())
            using (var server = new SyntheticIngressServer(owner, name))
            using (var status = new StatusPipeServer(statusName))
            {
                Check(Field(typeof(CustodyService), "transactions").GetValue(service) == null);
                Check(Field(typeof(CustodyService), "syntheticIngress").GetValue(service) == null);
                // UNSTARTED reflection fixture only; never represents valid service startup.
                Field(typeof(CustodyService), "transactions").SetValue(service, owner);
                Field(typeof(CustodyService), "syntheticIngress").SetValue(service, server);
                Field(typeof(CustodyService), "statusPipe").SetValue(service, status);
                var handle = ((NamedPipeServerStream)Field(typeof(SyntheticIngressServer), "pipe").GetValue(server)).SafePipeHandle;
                using (var client = connected == 1 ? Client(name) : null)
                {
                    Check(connected == 1 || !server.Completion.IsCompleted);
                    var elapsed = Stopwatch.StartNew();
                    Task close = Task.Run(delegate { Close(service, mode); });
                    Check(close.Wait(3000) && elapsed.ElapsedMilliseconds < 3000);
                    Check(server.Completion.IsCompleted && status.Completion.IsCompleted);
                    Check(server.Refused && HighWater(owner) == 0 && owner.Observe().Epoch == 2);
                    Check(owner.Observe().State == (mode == 0 ? TransactionOwnerState.Stopped :
                        mode == 1 ? TransactionOwnerState.Shutdown : mode == 4 ? TransactionOwnerState.Faulted :
                        TransactionOwnerState.Disposed));
                    if (client != null) NoReply(client);
                    Check(handle.IsClosed);
                    Unavailable(name); Unavailable(statusName);
                }
            }
            // Same unique endpoint is immediately reusable after disposal, with the same ACL.
            using (var owner = new SyntheticTransactionOwner())
            using (var replacement = new SyntheticIngressServer(owner, name)) { replacement.Dispose(); }
        }
    }
    private static void Races()
    {
        for (int round = 0; round < 8; round++)
        using (var owner = new SyntheticTransactionOwner())
        using (var start = new ManualResetEventSlim(false))
        {
            string name = Name();
            using (var server = new SyntheticIngressServer(owner, name))
            using (var client = Client(name))
            {
                SyntheticTransactionRequest request = Request(owner, 66);
                SyntheticTransactionResult cancel = null;
                Task write = Task.Run(delegate { Check(start.Wait(2000)); Write(client, Frame(66, 2)); });
                Task cancellation = Task.Run(delegate { Check(start.Wait(2000)); cancel = owner.Cancel(request); });
                start.Set(); Check(Task.WaitAll(new[] { write, cancellation }, 5000)); Done(server.Completion);
                Check(HighWater(owner) == 66 && cancel != null && !cancel.Allowed);
                if (server.Refused)
                {
                    Check(cancel.Disposition == TransactionDisposition.Cancelled &&
                        owner.Observe().State == TransactionOwnerState.Faulted); NoReply(client);
                }
                else
                {
                    Check(cancel.Disposition == TransactionDisposition.Replay);
                    Check(Read(client) == SyntheticIngressServer.Reply);
                }
            }
        }
        // Force processing while the real host lock is held, then close under that
        // same lock. A worker calling a host handler would deadlock this fixture.
        using (var service = (CustodyService)Activator.CreateInstance(typeof(CustodyService), true))
        using (var owner = new SyntheticTransactionOwner())
        {
            string name = Name();
            using (var server = new SyntheticIngressServer(owner, name))
            using (var client = Client(name))
            {
                Field(typeof(CustodyService), "transactions").SetValue(service, owner);
                Field(typeof(CustodyService), "syntheticIngress").SetValue(service, server);
                lock (Field(typeof(CustodyService), "lifecycle").GetValue(service))
                {
                    Write(client, Frame(88, 3));
                    Check(Read(client) == SyntheticIngressServer.Reply); Done(server.Completion);
                    Close(service, 0);
                }
                Check(HighWater(owner) == 88 && owner.Observe().State == TransactionOwnerState.Stopped);
            }
        }
        for (int round = 0; round < 16; round++)
        using (var owner = new SyntheticTransactionOwner())
        using (var start = new ManualResetEventSlim(false))
        {
            string name = Name();
            using (var server = new SyntheticIngressServer(owner, name))
            using (var client = Client(name))
            {
                SyntheticTransactionRequest request = Request(owner, 77);
                SyntheticTransactionResult cancel = null;
                Task write = Task.Run(delegate {
                    Check(start.Wait(2000));
                    try { Write(client, Frame(77, 1)); }
                    catch (IOException) { }
                    catch (AggregateException error) { Check(error.InnerException is IOException); }
                });
                Task cancellation = Task.Run(delegate { Check(start.Wait(2000)); cancel = owner.Cancel(request); });
                Task stop = Task.Run(delegate { Check(start.Wait(2000)); owner.Stop(); server.Dispose(); });
                Task dispose = Task.Run(delegate { Check(start.Wait(2000)); server.Dispose(); });
                start.Set(); Check(Task.WaitAll(new[] { write, cancellation, stop, dispose }, 5000));
                Done(server.Completion);
                Check(cancel != null && !cancel.Allowed && owner.Observe().Epoch == 2);
                Check(cancel.Disposition == TransactionDisposition.Cancelled || cancel.Disposition == TransactionDisposition.Replay ||
                    cancel.Disposition == TransactionDisposition.OwnerTerminated);
                Check(owner.Observe().State != TransactionOwnerState.ActiveDenied && HighWater(owner) <= 77);
                // A denial that won the race may have reached the client; it can only be
                // the fixed HOLD frame. Closure may discard buffered data, never promote it.
                try
                {
                    byte[] bytes = new byte[128]; Task<int> read = client.ReadAsync(bytes, 0, bytes.Length);
                    Done(Bounded(read, client));
                    Check(read.Result == 0 || (client.IsMessageComplete &&
                        Encoding.ASCII.GetString(bytes, 0, read.Result) == SyntheticIngressServer.Reply));
                }
                catch (IOException) { }
                catch (AggregateException error) { Check(error.InnerException is IOException); }
            }
            Unavailable(name);
        }
    }

    // Decode real product IL rather than searching arbitrary token-looking bytes.
    private static List<MethodBase> Calls(MethodBase method)
    {
        var codes = new Dictionary<short, OpCode>();
        foreach (FieldInfo field in typeof(OpCodes).GetFields(BindingFlags.Public | BindingFlags.Static))
            if (field.FieldType == typeof(OpCode)) { OpCode code = (OpCode)field.GetValue(null); codes[code.Value] = code; }
        var calls = new List<MethodBase>();
        byte[] il = method.GetMethodBody().GetILAsByteArray();
        for (int offset = 0; offset < il.Length; )
        {
            short value = il[offset++];
            if (value == 0xfe) value = (short)(0xfe00 | il[offset++]);
            OpCode code = codes[value];
            int count;
            switch (code.OperandType)
            {
                case OperandType.InlineNone: count = 0; break;
                case OperandType.ShortInlineBrTarget: case OperandType.ShortInlineI:
                case OperandType.ShortInlineVar: count = 1; break;
                case OperandType.InlineVar: count = 2; break;
                case OperandType.InlineI8: case OperandType.InlineR: count = 8; break;
                case OperandType.InlineSwitch: count = 4 + 4 * BitConverter.ToInt32(il, offset); break;
                default: count = 4; break;
            }
            if (code == OpCodes.Call || code == OpCodes.Callvirt || code == OpCodes.Newobj)
                calls.Add(method.Module.ResolveMethod(BitConverter.ToInt32(il, offset)));
            offset += count;
        }
        return calls;
    }
    private static int Index(List<MethodBase> calls, Type type, string name)
    { return calls.FindIndex(delegate(MethodBase m) { return m.DeclaringType == type && m.Name == name; }); }
    private static void Before(List<MethodBase> calls, Type firstType, string first, Type secondType, string second)
    {
        int a = Index(calls, firstType, first), b = Index(calls, secondType, second);
        Check(a >= 0 && b >= 0 && a < b);
    }
    private static void Shape()
    {
        Type host = typeof(CustodyService), ingress = typeof(SyntheticIngressServer);
        Check(ingress.IsNotPublic && ingress.IsSealed);
        Check(ingress.GetConstructors(BindingFlags.Instance | BindingFlags.Public).Length == 0);
        Check(ingress.GetConstructor(Hidden, null, new[] { typeof(SyntheticTransactionOwner) }, null).IsAssembly);
        Check(ingress.GetConstructor(Hidden, null, new[] { typeof(SyntheticTransactionOwner), typeof(string) }, null).IsAssembly);
        Check(SyntheticIngressServer.Endpoint == "NayeonV1ByokCustody.SyntheticDenied.v1" &&
            SyntheticIngressServer.Endpoint != StatusPipeServer.Endpoint);
        Check(SyntheticIngressServer.Reply == "C1|DENIED|HOLD|NO_CREDENTIALS");
        List<MethodBase> calls = Calls(host.GetMethod("OnStart", Hidden));
        var identities = calls.FindAll(delegate(MethodBase m) { return m.DeclaringType == host && m.Name == "VerifyExecutingIdentity"; });
        Check(identities.Count == 2);
        int first = Index(calls, host, "VerifyExecutingIdentity");
        int second = calls.FindIndex(first + 1, delegate(MethodBase m) { return m.DeclaringType == host && m.Name == "VerifyExecutingIdentity"; });
        int owner = Index(calls, typeof(SyntheticTransactionOwner), ".ctor");
        int server = Index(calls, ingress, ".ctor");
        Check(first >= 0 && first < second && second < owner && owner < server &&
            server < Index(calls, typeof(LifecycleCoordinator), "CompleteStart"));
        Before(calls, typeof(SyntheticTransactionOwner), "Fault", host, "ClosePipes");
        foreach (string method in new[] { "OnStop", "OnShutdown" })
            Check(Index(Calls(host.GetMethod(method, Hidden)), host, "Close") >= 0);
        calls = Calls(host.GetMethod("Close", Hidden));
        foreach (string method in new[] { "Stop", "Shutdown", "Dispose" })
            Before(calls, typeof(SyntheticTransactionOwner), method, host, "ClosePipes");
        calls = Calls(host.GetMethod("Dispose", Hidden, null, new[] { typeof(bool) }, null));
        Before(calls, typeof(SyntheticTransactionOwner), "Dispose", host, "ClosePipes");
        calls = Calls(host.GetMethod("ClosePipes", Hidden));
        Check(Index(calls, ingress, "Dispose") >= 0 &&
            Index(calls, ingress, "Dispose") < Index(calls, typeof(StatusPipeServer), "Dispose"));

        string[] sources = { "CustodyService.cs", "LifecycleCoordinator.cs", "StatusPipeServer.cs",
            "StatusPipeClient.cs", "SyntheticTransactionOwner.cs", "SyntheticIngressServer.cs" };
        var xml = new XmlDocument();
        xml.Load("src/Nayeon.ByokC1.Service/Nayeon.ByokC1.Service.csproj");
        var ns = new XmlNamespaceManager(xml.NameTable); ns.AddNamespace("m", xml.DocumentElement.NamespaceURI);
        XmlNodeList compile = xml.SelectNodes("/m:Project/m:ItemGroup/m:Compile", ns);
        Check(compile.Count == sources.Length);
        var expected = new HashSet<string>(sources, StringComparer.Ordinal);
        foreach (XmlNode node in compile) Check(expected.Remove(node.Attributes["Include"].Value));
        Check(expected.Count == 0);
        Check(xml.SelectSingleNode("//m:TargetFrameworkVersion", ns).InnerText == "v4.8");
        Check(xml.SelectSingleNode("//m:TreatWarningsAsErrors", ns).InnerText == "true");
        // Exact native import allowlist across the ACTUAL compiled product; no secret API.
        var imports = new HashSet<string>(new[] { "kernel32.dll!GetCurrentProcess", "kernel32.dll!GetCurrentThread",
            "kernel32.dll!CloseHandle", "advapi32.dll!OpenProcessToken", "advapi32.dll!OpenThreadToken",
            "advapi32.dll!IsTokenRestricted", "advapi32.dll!GetTokenInformation" }, StringComparer.Ordinal);
        foreach (Type type in host.Assembly.GetTypes())
        foreach (MethodInfo method in type.GetMethods(BindingFlags.DeclaredOnly | BindingFlags.Static |
            BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic))
        {
            var native = (DllImportAttribute)Attribute.GetCustomAttribute(method, typeof(DllImportAttribute));
            if (native != null) Check(type == host && imports.Remove(native.Value + "!" + native.EntryPoint));
        }
        Check(imports.Count == 0);
        // The ingress has no service lifecycle lock, dispatcher or effect callback field.
        foreach (FieldInfo field in ingress.GetFields(Hidden))
            Check(field.FieldType == typeof(SyntheticTransactionOwner) || field.FieldType == typeof(NamedPipeServerStream) ||
                field.FieldType == typeof(Task) || field.FieldType == typeof(CancellationTokenSource) ||
                field.FieldType == typeof(int));
    }
    private static int Main(string[] args)
    {
        var elapsed = Stopwatch.StartNew();
        try
        {
            Check(Environment.OSVersion.Platform == PlatformID.Win32NT);
            Check(args.Length == 1 && IntPtr.Size * 8 == int.Parse(args[0]));
            Check(typeof(SyntheticIngressServer).Assembly != typeof(P309ServiceIngressTests).Assembly);
            Check(typeof(SyntheticIngressServer).Assembly.Location == Path.Combine(
                AppDomain.CurrentDomain.BaseDirectory, "Nayeon.ByokC1.Service.exe"));
            Shape(); Exact(); Negatives(); IdleAccept(); Retirement(); Races();
            Console.WriteLine("P309 PASS checks=" + checks + " bits=" + IntPtr.Size * 8 + " elapsed_ms=" +
                elapsed.ElapsedMilliseconds + "; actual disposable message ingress, synthetic denial only; HOLD");
            return 0;
        }
        catch (Exception error)
        {
            Console.Error.WriteLine("P309 FAIL " + error +
                " elapsed_ms=" + elapsed.ElapsedMilliseconds + "; HOLD"); return 1;
        }
    }
}
