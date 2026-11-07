// BYOK C1 — native service-owned single-writer lock and recovery gate.
// Uninstalled service remains permanently FAULTED. A future independently
// reviewed privileged session-reconciliation mechanism is needed to arm it.
// NO credential effects, no protected file/registry mutation, no IPC here.
using System;
using System.Security.AccessControl;
using System.Security.Principal;
using System.Threading;

namespace Nayeon.ByokC1
{
    internal sealed class ServiceCustodyMutex : IExclusiveCustodyLock, IDisposable
    {
        private readonly object gate=new object();
        private string mutexName;
        private Mutex retained;
#if BYOK_TEST
        private static readonly string SyntheticName=
            @"Global\NayeonV1_BYOK_C1_Test_"+Guid.NewGuid().ToString("N");
#endif

        internal ServiceCustodyMutex()
        {
            try
            {
                // Installation provisions an unpredictable 128-bit name in
                // an admin-only HKLM key. Never accept caller-supplied names.
                mutexName=@"Global\NayeonV1_BYOK_C1_"+
                    new CustodyRegistryAnchor().ReadMutexNonce();
            }
            catch(Exception){mutexName=null;}
        }
        private bool faulted=true;
        private bool active;
        private bool failedNativeRelease;
#if BYOK_TEST
        private bool testAdmittedEver;
#endif

        public bool RecoveryFaulted
        {
            get {lock(gate){return faulted || failedNativeRelease;}}
        }

        private static MutexSecurity Security()
        {
            MutexSecurity acl=new MutexSecurity();
            SecurityIdentifier localSystem=new SecurityIdentifier(
                WellKnownSidType.LocalSystemSid,null);
            SecurityIdentifier admins=new SecurityIdentifier(
                WellKnownSidType.BuiltinAdministratorsSid,null);
            acl.AddAccessRule(new MutexAccessRule(localSystem,
                MutexRights.FullControl,AccessControlType.Allow));
            acl.AddAccessRule(new MutexAccessRule(admins,
                MutexRights.FullControl,AccessControlType.Allow));
            return acl;
        }

#if BYOK_TEST
        internal void AllowSyntheticTestTenure()
        {
            lock(gate)
            {
                if(active || failedNativeRelease || testAdmittedEver)
                    throw new LedgerBlocked();
                testAdmittedEver=true;
                mutexName=SyntheticName;
                faulted=false;
            }
        }
#endif

        public IContinuousCustodyLease Acquire()
        {
            lock(gate)
            {
                if(faulted || active || failedNativeRelease)
                    throw new LedgerBlocked();
                Mutex native=retained;
                bool held=false;
                bool newlyOpened=false;
                try
                {
                    if(String.IsNullOrEmpty(mutexName))
                        throw new LedgerBlocked();
                    if(native==null)
                    {
                        bool created=false;
                        native=new Mutex(false,mutexName,out created,Security());
                        newlyOpened=true; // close even when name was already owned
                        if(!created)throw new LedgerBlocked();
                    }
                    held=native.WaitOne(0,false);
                    if(!held)throw new LedgerBlocked();
                    active=true;
                    // Keep the named object HANDLE throughout service life.
                    // No between-tenure name-squatting window.
                    retained=native;
                    return new Tenure(this,native,Thread.CurrentThread.ManagedThreadId);
                }
                catch(AbandonedMutexException)
                {
                    faulted=true;failedNativeRelease=true;
                    try{if(native!=null)native.ReleaseMutex();}catch(Exception){}
                    if(newlyOpened && native!=null)native.Dispose();
                    throw new LedgerBlocked();
                }
                catch(Exception)
                {
                    if(held && native!=null)
                    {
                        try{native.ReleaseMutex();}
                        catch(Exception){faulted=true;failedNativeRelease=true;}
                    }
                    if(newlyOpened && native!=null)native.Dispose();
                    throw new LedgerBlocked();
                }
            }
        }

        public void Dispose()
        {
            lock(gate)
            {
                faulted=true;
                if(active)throw new LedgerBlocked();
                if(retained!=null)
                {
                    try{retained.Dispose();}
                    catch(Exception){failedNativeRelease=true;throw new LedgerBlocked();}
                    finally{retained=null;}
                }
            }
        }

        private sealed class Tenure : IContinuousCustodyLease
        {
            private readonly ServiceCustodyMutex manager;
            private readonly Mutex native;
            private readonly int ownerThread;
            private bool terminalVerified,disposed;

            internal Tenure(ServiceCustodyMutex manager,Mutex native,int ownerThread)
            {
                this.manager=manager;this.native=native;this.ownerThread=ownerThread;
            }

            public bool IsOwned
            {
                get
                {
                    lock(manager.gate)
                    {
                        return !disposed && manager.active &&
                            !manager.faulted &&
                            !manager.failedNativeRelease &&
                            Thread.CurrentThread.ManagedThreadId==ownerThread;
                    }
                }
            }

            public void MarkTerminalVerified()
            {
                lock(manager.gate)
                {
                    if(!IsOwned || terminalVerified)
                        throw new LedgerBlocked();
                    terminalVerified=true;
                }
            }

            public void Dispose()
            {
                // All other contenders wait for the SAME gate until both
                // fault publication and Win32 release have been evaluated.
                lock(manager.gate)
                {
                    if(disposed)return;
                    // A foreign thread cannot release an owned Windows
                    // mutex. Fault, but preserve active=true, disposed=false
                    // and the native handle so the ORIGINAL owner can clean
                    // up on its own thread. Never let manager shutdown close
                    // an unresolved native tenure.
                    if(Thread.CurrentThread.ManagedThreadId!=ownerThread)
                    {
                        manager.faulted=true;
                        manager.failedNativeRelease=true;
                        throw new LedgerBlocked();
                    }
                    if(!terminalVerified || !IsOwned)
                        manager.faulted=true;
                    try{native.ReleaseMutex();}
                    catch(Exception)
                    {
                        // Keep active and the handle: whether native custody
                        // was released is unknown, and it must not be reused.
                        manager.faulted=true;
                        manager.failedNativeRelease=true;
                        throw new LedgerBlocked();
                    }
                    // Only an actually successful ReleaseMutex retires the
                    // tenure. Failed/foreign attempts never retire it.
                    disposed=true;
                    manager.active=false;
                    // The manager retains the object handle until trusted
                    // service shutdown; no name recreation between tenures.
                }
            }
        }
    }
}
