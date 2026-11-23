using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Reflection.Emit;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;
using System.Threading;
using System.Web.Script.Serialization;
using System.Xml;
using Nayeon.ByokC1.Service;

internal static class P312ProductVaultTests
{
    private static int count;
    private static void Check(bool value) { if (!value) throw new Exception("P312 assertion; HOLD."); count++; }
    private static void Refuse(Action action)
    {
        bool refused = false;
        try { action(); } catch (InvalidOperationException) { refused = true; }
        Check(refused);
    }
    private static string Fresh() { return Guid.NewGuid().ToString("N"); }
    private static readonly Type Adapter = typeof(HostedDisposableWinCred);
    private static bool AdapterType(Type type)
    { while (type != null) { if (type == Adapter) return true; type = type.DeclaringType; } return false; }

    // Decode actual product IL operands, rather than matching an inherited compile count.
    private static void Topology()
    {
        Assembly product = Adapter.Assembly;
        Check(product != Assembly.GetExecutingAssembly());
        Check(product.GetName().Name == "Nayeon.ByokC1.Service");
        Check(Assembly.GetExecutingAssembly().GetName().Name == "P312.ProductVault.Tests");
        Check(!Adapter.IsPublic && Adapter.GetConstructors().Length == 0);
        Check(product.GetCustomAttributes(typeof(InternalsVisibleToAttribute), false)
            .Cast<InternalsVisibleToAttribute>().Count(a => a.AssemblyName == "P312.ProductVault.Tests") == 1);
        var codes = typeof(OpCodes).GetFields(BindingFlags.Static | BindingFlags.Public)
            .Where(f => f.FieldType == typeof(OpCode)).Select(f => (OpCode)f.GetValue(null))
            .ToDictionary(c => unchecked((ushort)c.Value));
        foreach (Type type in product.GetTypes().Where(t => !AdapterType(t)))
        {
            foreach (FieldInfo field in type.GetFields(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.Static))
                Check(!AdapterType(field.FieldType));
            var methods = type.GetMethods(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.Static | BindingFlags.DeclaredOnly)
                .Cast<MethodBase>().Concat(type.GetConstructors(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.Static));
            foreach (MethodBase method in methods)
            {
                var body = method.GetMethodBody(); if (body == null) continue;
                byte[] il = body.GetILAsByteArray();
                for (int i = 0; i < il.Length; )
                {
                    ushort key = il[i++]; if (key == 0xfe) key = (ushort)(0xfe00 | il[i++]);
                    OpCode code = codes[key]; int size;
                    switch (code.OperandType)
                    {
                        case OperandType.InlineNone: size = 0; break;
                        case OperandType.ShortInlineBrTarget: case OperandType.ShortInlineI: case OperandType.ShortInlineVar: size = 1; break;
                        case OperandType.InlineVar: size = 2; break;
                        case OperandType.InlineI8: case OperandType.InlineR: size = 8; break;
                        case OperandType.InlineSwitch: size = 4 + 4 * BitConverter.ToInt32(il, i); break;
                        default: size = 4; break;
                    }
                    if (code.OperandType == OperandType.InlineMethod || code.OperandType == OperandType.InlineField ||
                        code.OperandType == OperandType.InlineType || code.OperandType == OperandType.InlineTok)
                    {
                        MemberInfo member = method.Module.ResolveMember(BitConverter.ToInt32(il, i));
                        Check(!AdapterType(member as Type) && !AdapterType(member.DeclaringType));
                    }
                    i += size; Check(i <= il.Length);
                }
            }
        }
        string root = Environment.GetEnvironmentVariable("GITHUB_WORKSPACE") ?? Directory.GetCurrentDirectory();
        string service = Path.Combine(root, "src", "Nayeon.ByokC1.Service");
        var project = new XmlDocument(); project.Load(Path.Combine(service, "Nayeon.ByokC1.Service.csproj"));
        var ns = new XmlNamespaceManager(project.NameTable); ns.AddNamespace("m", project.DocumentElement.NamespaceURI);
        Check(project.SelectNodes("//m:Compile[@Include='HostedDisposableWinCred.cs']", ns).Count == 1);
        Check(project.SelectNodes("//m:Reference[@Include='System.Web.Extensions']", ns).Count == 1);
        Check(project.SelectSingleNode("//m:TargetFrameworkVersion", ns).InnerText == "v4.8");
        foreach (XmlNode source in project.SelectNodes("//m:Compile", ns))
        {
            string name = source.Attributes["Include"].Value;
            if (name != "HostedDisposableWinCred.cs")
                Check(!File.ReadAllText(Path.Combine(service, name)).Contains("HostedDisposableWinCred"));
        }
        var imports = Adapter.GetMethods(BindingFlags.NonPublic | BindingFlags.Static)
            .Select(m => m.GetCustomAttributes(typeof(DllImportAttribute), false).Cast<DllImportAttribute>().SingleOrDefault())
            .Where(a => a != null).ToArray();
        Check(imports.Length == 4 && imports.All(a => a.Value == "advapi32.dll"));
        Check(imports.Select(a => a.EntryPoint).OrderBy(s => s).SequenceEqual(new[] { "CredDeleteW", "CredFree", "CredReadW", "CredWriteW" }));
    }

    private static void ReadOnlyNegatives()
    {
        foreach (string id in new[] { null, "", Guid.Empty.ToString("N"), "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
            Guid.NewGuid().ToString("D"), "Nayeon.P312.Disposable." + Fresh(), "../" + Fresh() })
        { Refuse(delegate { HostedDisposableWinCred.ValidateId(id); }); Refuse(delegate { new HostedDisposableWinCred(id); }); }
        HostedDisposableWinCred.ValidateId(Fresh()); count++;
        string original = Environment.GetEnvironmentVariable("P312_SYNTHETIC_HOSTED_ONLY");
        try
        {
            Environment.SetEnvironmentVariable("P312_SYNTHETIC_HOSTED_ONLY", null);
            Refuse(HostedDisposableWinCred.RequireHosted);
            Refuse(delegate { new HostedDisposableWinCred(Fresh()); });
        }
        finally { Environment.SetEnvironmentVariable("P312_SYNTHETIC_HOSTED_ONLY", original); }
        var env = new Dictionary<string, string> {
            {"GITHUB_ACTIONS", "true"}, {"RUNNER_OS", "Windows"}, {"RUNNER_ENVIRONMENT", "github-hosted"},
            {"GITHUB_EVENT_NAME", "pull_request"}, {"GITHUB_REPOSITORY", "krismcan/Mark-LV"},
            {"GITHUB_HEAD_REF", "byok-c1-p312-service-hosted-windows-vault-20261123"},
            {"GITHUB_BASE_REF", "byok-c1-p311-crosslanguage-synthetic-20261123"}, {"P312_SYNTHETIC_HOSTED_ONLY", "1"} };
        string sha = new string('a', 40);
        var repo = new Dictionary<string, object> { {"full_name", "krismcan/Mark-LV"}, {"fork", true}, {"id", 1402212689} };
        var head = new Dictionary<string, object> { {"repo", new Dictionary<string, object>(repo)}, {"ref", env["GITHUB_HEAD_REF"]}, {"sha", sha} };
        var baseSide = new Dictionary<string, object> { {"repo", new Dictionary<string, object>(repo)}, {"ref", env["GITHUB_BASE_REF"]}, {"sha", "c430fafba1dc5890e59ade3f96c5cba13e5797c5"} };
        var pr = new Dictionary<string, object> { {"draft", true}, {"head", head}, {"base", baseSide} };
        var root = new Dictionary<string, object> { {"repository", repo}, {"pull_request", pr} };
        var serializer = new JavaScriptSerializer();
        Action validate = delegate { HostedDisposableWinCred.ValidateContext(env, serializer.Serialize(root), sha); };
        validate(); count++; // Pure predicate: no OS or native access.
        foreach (string key in env.Keys.ToArray())
        { string value = env[key]; env[key] = "denied"; Refuse(validate); env[key] = value; }
        pr["draft"] = false; Refuse(validate); pr["draft"] = true;
        repo["fork"] = false; Refuse(validate); repo["fork"] = true;
        repo["fork"] = "true"; Refuse(validate); repo["fork"] = true;
        foreach (var endpoint in new[] { head, baseSide })
        {
            var endpointRepo = (Dictionary<string, object>)endpoint["repo"];
            endpointRepo["id"] = 456; Refuse(validate); endpointRepo["id"] = 1402212689;
            endpointRepo["fork"] = false; Refuse(validate); endpointRepo["fork"] = true;
            endpointRepo["fork"] = "true"; Refuse(validate); endpointRepo["fork"] = true;
        }
        head["sha"] = new string('b', 40); Refuse(validate); head["sha"] = sha;
        baseSide["sha"] = sha; Refuse(validate); baseSide["sha"] = "c430fafba1dc5890e59ade3f96c5cba13e5797c5";
        head["repo"] = new Dictionary<string, object> { {"full_name", "other/repo"}, {"fork", false}, {"id", 456} };
        Refuse(validate); head["repo"] = repo;
        Refuse(delegate { HostedDisposableWinCred.ValidateContext(env, new string(' ', 65536), sha); });
    }

    private static void NativeCases()
    {
        HostedDisposableWinCred.RequireHosted(); // Actual environment, never predicate injection.
        string id = Fresh();
        using (var vault = new HostedDisposableWinCred(id))
        {
            Check(vault.State == HostedDisposableWinCred.VaultState.Uninitialized);
            Refuse(vault.Replace); Refuse(vault.Delete); Refuse(vault.Verify);
            vault.Add(); Check(vault.State == HostedDisposableWinCred.VaultState.Saved); vault.Verify();
            Refuse(delegate { new HostedDisposableWinCred(id); }); // Real existing-entry collision.
            Refuse(vault.Add); vault.Replace(); Check(vault.State == HostedDisposableWinCred.VaultState.Replaced); vault.Verify();
            Refuse(vault.Replace); vault.Delete(); Check(vault.State == HostedDisposableWinCred.VaultState.Deleted); vault.Verify();
            Refuse(vault.Delete); Refuse(vault.Add);
            vault.Dispose(); vault.Dispose(); Refuse(vault.Add); Refuse(vault.Verify);
        }
        // Fresh lifetime at the SAME id proves the deleted credential is absent.
        using (var absent = new HostedDisposableWinCred(id)) Check(absent.State == HostedDisposableWinCred.VaultState.Uninitialized);
        id = Fresh();
        using (var firstOwner = new HostedDisposableWinCred(id))
        using (var notOwner = new HostedDisposableWinCred(id))
        {
            firstOwner.Add();
            Refuse(notOwner.Add); // Late collision: failure never acquires deletion ownership.
            Check(notOwner.State == HostedDisposableWinCred.VaultState.Faulted);
            notOwner.Dispose(); firstOwner.Verify();
        }
        using (var absent = new HostedDisposableWinCred(id)) Check(absent.State == HostedDisposableWinCred.VaultState.Uninitialized);
        id = Fresh();
        using (var vault = new HostedDisposableWinCred(id))
        {
            vault.Add();
            string brake = Environment.GetEnvironmentVariable("P312_SYNTHETIC_HOSTED_ONLY");
            try
            {
                Environment.SetEnvironmentVariable("P312_SYNTHETIC_HOSTED_ONLY", null);
                Refuse(vault.Replace); // Actual gate failure: no native call, cleanup also refuses.
                Check(vault.State == HostedDisposableWinCred.VaultState.Faulted);
                Refuse(vault.Dispose); // Incident remains failed until original context is restored.
            }
            finally { Environment.SetEnvironmentVariable("P312_SYNTHETIC_HOSTED_ONLY", brake); }
            Refuse(vault.Add); Refuse(vault.Replace);
        }
        using (var absent = new HostedDisposableWinCred(id)) Check(absent.State == HostedDisposableWinCred.VaultState.Uninitialized);
        id = Fresh();
        using (var vault = new HostedDisposableWinCred(id))
        {
            int accepted = 0, refused = 0; Exception failure = null;
            ThreadStart add = delegate {
                try { vault.Add(); Interlocked.Increment(ref accepted); }
                catch (InvalidOperationException) { Interlocked.Increment(ref refused); }
                catch (Exception ex) { Interlocked.CompareExchange(ref failure, ex, null); }
            };
            var first = new Thread(add); var second = new Thread(add);
            first.Start(); second.Start(); Check(first.Join(15000) && second.Join(15000));
            Check(failure == null && accepted == 1 && refused == 1); vault.Verify();
            // Test-only reflection models an uncertain outcome, never injects an OS adapter or gate.
            Adapter.GetField("state", BindingFlags.NonPublic | BindingFlags.Instance)
                .SetValue(vault, HostedDisposableWinCred.VaultState.Faulted);
            Refuse(vault.Add); Refuse(vault.Replace); Refuse(vault.Verify);
        } // Faulted-state disposal must still delete our verified synthetic value.
        using (var absent = new HostedDisposableWinCred(id)) Check(absent.State == HostedDisposableWinCred.VaultState.Uninitialized);
        id = Fresh();
        var racing = new HostedDisposableWinCred(id);
        Exception raceFailure = null;
        var writer = new Thread(delegate() {
            try { racing.Add(); }
            catch (InvalidOperationException ex) { if (ex.Message != "P312 refused; HOLD.") raceFailure = ex; }
            catch (Exception ex) { raceFailure = ex; }
        });
        try { writer.Start(); racing.Dispose(); Check(writer.Join(15000)); Check(raceFailure == null); }
        finally { racing.Dispose(); }
        using (var absent = new HostedDisposableWinCred(id)) Check(absent.State == HostedDisposableWinCred.VaultState.Uninitialized);
    }

    private static int Main(string[] args)
    {
        try
        {
            Check(args.Length == 0 || (args.Length == 1 && args[0] == "--readonly"));
            ReadOnlyNegatives(); Topology();
            if (args.Length == 0) NativeCases();
            Console.WriteLine("P312 PRODUCT VAULT TESTS PASS count=" + count); return 0;
        }
        catch { Console.Error.WriteLine("P312 PRODUCT VAULT TESTS FAIL; HOLD; inspect cleanup incident if applicable."); return 1; }
    }
}
