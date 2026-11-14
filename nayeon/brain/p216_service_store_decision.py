"""P216 source-grounded Windows store-principal decision intake: ALWAYS HOLD.

A positive high-assurance service-store design requires a qualified
independent G0/R3 review and actual Windows service identity, deployed
signed protected image, owner-bound store, immutable approval and removal of
the original P132/P133 user-scope direct WinCred effect route. None exists.

This module is an executable *reviewer decision inventory*, not an
authoritative Windows security barrier, Credential Manager hook, installer,
key transfer, production UI, or real-key admission. It never imports the
credential implementation or invokes OS credential APIs. Static scanning
cannot prove absence of dynamic imports/native alternate effect paths.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import stat

from nayeon.brain.p211_high_assurance_package_quarantine import (
    inspect_current_source_tree,
)

# Explicit CURRENT proposal for independent assessment, not a configuration
# to install. Reviewer/Windows policy owner can REJECT or require alternatives.
CANDIDATE_SERVICE_ACCOUNT=r"NT SERVICE\NayeonByokCustody"
CANDIDATE_STORE_CRYPTO="User-scoped DPAPI under a distinct service token"
CANDIDATE_OS_BOUNDARY="Service-SID-restricted ACL and independent protected monotonic witness"
CANDIDATE_MIGRATION="none; never copy interactive-user P132 secret automatically"
CANDIDATE_USER_PRESENCE="not implemented; untrusted signed UI claims are not consent"
CANDIDATE_MACHINE_DPAPI_AS_IS="REJECT; CryptProtectData LOCAL_MACHINE is decryptable by other local users if they can read ciphertext"

SCAN_ROOTS=("nayeon", "core")
MAX_TRACKED_PY_FILES=4096
MAX_SOURCE_BYTES=1024*1024
KNOWN_DIRECT_EFFECT="nayeon/secrets/windows_credential.py"
KNOWN_CONSUMER="nayeon/brain/local_byok_user_scope.py"
KNOWN_LAUNCHER="nayeon/desktop_alpha/local_byok_launch_bridge.py"


class P216ReviewStatus(str,Enum):
    SOURCE_UNPROVEN="SOURCE_UNPROVEN"
    TRACKED_SOURCE_UNPROVEN="TRACKED_SOURCE_UNPROVEN"
    SOURCE_RISK_REQUIRES_OWNER_DECISION="SOURCE_RISK_REQUIRES_OWNER_DECISION"


@dataclass(frozen=True,slots=True)
class P216EffectSourceFinding:
    path:str
    wincred_native_adapter:bool
    wincred_backend_import:bool
    explicit_native_credential_call:bool
    dynamic_import_risk:bool

@dataclass(frozen=True,slots=True)
class P216StoreReview:
    status:P216ReviewStatus
    parsed_tracked_python:int
    direct_effect_source_reachable:bool
    local_user_controller_reachable:bool
    source_launcher_reachable:bool
    original_native_C1_host_denial_only:bool
    findings:tuple[P216EffectSourceFinding,...]
    outstanding_external_decisions:tuple[str,...]
    release_eligible:bool=False
    real_key_admissible:bool=False
    protected_service_store_installed:bool=False
    legacy_route_isolated_by_OS:bool=False
    trusted_user_presence_proven:bool=False
    machine_code_integrity_approved:bool=False
    user_scope_key_migration_authorized:bool=False

    def __post_init__(self)->None:
        if any((
            self.release_eligible,self.real_key_admissible,
            self.protected_service_store_installed,
            self.legacy_route_isolated_by_OS,
            self.trusted_user_presence_proven,
            self.machine_code_integrity_approved,
            self.user_scope_key_migration_authorized,
        )):
            raise ValueError("P216 cannot mint real-key, WinCred migration, or release authority")


G0_R3_UNRESOLVED=(
    "G0:independent_windows_native_security_review",
    "R3:actual_service_account_and_profile_token_semantics",
    "R3:service_owned_separate_target_and_secret_isolation",
    "R3:user_scoped_DPAPI_not_machine_scoped_and_acl_evidence",
    "R3:independently_protected_monotonic_rollback_witness",
    "R3:recovery_migration_deletion_and_backup_plan",
    "R0:approved_signed_source_and_install_tree",
    "R1:loaded_signed_UI_image_authenticated_pipe_and_user_presence",
    "R2:oneuse_atomic_original_service_owned_terminal_effect_actor",
    "P0:legacy_user_scope_P132_P133_effect_elimination_or_OS_isolation",
    "P1:GOV01_GOV02_SEC03_SEC04_REL05_REL06_REL07",
    "P2:three_unfiltered_native_Windows_product_regressions",
    "P3:Windows_Code_Integrity_WDAC_SAC_signing_policy_owner",
)


def _safe_tracked_path(root:Path, relative:str)->Path|None:
    try:
        if (not isinstance(root,Path) or not root.is_absolute()
            or type(relative) is not str or len(relative)>200
            or not relative.endswith(".py")
            or "\\" in relative or ":" in relative or relative.startswith("/")):
            return None
        parts=relative.split("/")
        if (not parts or parts[0] not in SCAN_ROOTS
            or any(not p or p in (".","..") or p.endswith(".") or p.endswith(" ")
                   for p in parts)):
            return None
        current=root
        for part in parts:
            if current.is_symlink() or getattr(current.lstat(),"st_file_attributes",0)&0x400:
                return None
            current=current/part
        meta=current.lstat()
        if (not stat.S_ISREG(meta.st_mode) or current.is_symlink()
            or getattr(meta,"st_file_attributes",0)&0x400
            or not 0<meta.st_size<=MAX_SOURCE_BYTES):
            return None
        return current
    except (OSError,ValueError):
        return None


def _finding(path:str,source:str)->P216EffectSourceFinding:
    tree=ast.parse(source,filename=path)
    imported=False
    native=False
    dynamic=False
    for n in ast.walk(tree):
        if isinstance(n,ast.ImportFrom):
            if n.module=="nayeon.secrets.windows_credential":
                imported=True
        elif isinstance(n,ast.Import):
            if any(a.name=="nayeon.secrets.windows_credential" for a in n.names):
                imported=True
        elif isinstance(n,ast.Call):
            fn=n.func
            if isinstance(fn,ast.Attribute):
                if fn.attr in ("CredWriteW","CredDeleteW","CredReadW"):
                    native=True
                if fn.attr in ("import_module", "WinDLL","CDLL","LoadLibrary"):
                    dynamic=True
            elif isinstance(fn,ast.Name):
                if fn.id in ("__import__","getattr","eval","exec"):
                    dynamic=True
    return P216EffectSourceFinding(
        path=path,
        wincred_native_adapter=(
            path==KNOWN_DIRECT_EFFECT and
            "CredWriteW" in source and "CredDeleteW" in source and
            "WindowsCredentialBackend" in source),
        wincred_backend_import=imported,
        explicit_native_credential_call=native,
        dynamic_import_risk=dynamic,
    )


def review_proposed_service_store(
    root:Path, tracked_python:tuple[str,...]
)->P216StoreReview:
    """Fail-closed actual source inventory, not an installed OS trust gate.

    tracked_python must be generated by 'git ls-files' from exact audited
    checkout. User-supplied paths do NOT create authority. Any absent,
    unparseable, duplicate, untracked or untrusted scan => UNKNOWN/HOLD.
    """
    source=inspect_current_source_tree(root)
    if not source.exact_legacy_source_readable:
        return P216StoreReview(
            P216ReviewStatus.SOURCE_UNPROVEN,0,False,False,False,False,
            tuple(),G0_R3_UNRESOLVED)
    if (type(tracked_python) is not tuple or not tracked_python
        or len(tracked_python)>MAX_TRACKED_PY_FILES
        or len({p.casefold() for p in tracked_python if type(p) is str})!=len(tracked_python)):
        return P216StoreReview(
            P216ReviewStatus.TRACKED_SOURCE_UNPROVEN,0,False,False,False,False,
            tuple(),G0_R3_UNRESOLVED)
    required={KNOWN_DIRECT_EFFECT,KNOWN_CONSUMER,KNOWN_LAUNCHER}
    if not required.issubset(set(tracked_python)):
        return P216StoreReview(
            P216ReviewStatus.TRACKED_SOURCE_UNPROVEN,0,False,False,False,False,
            tuple(),G0_R3_UNRESOLVED)
    findings=[]
    try:
        for path in sorted(tracked_python):
            f=_safe_tracked_path(root,path)
            if f is None:raise ValueError("untrusted Python tracked source")
            findings.append(_finding(path,f.read_text("utf8")))
    except (OSError,UnicodeError,ValueError,SyntaxError,TypeError):
        return P216StoreReview(
            P216ReviewStatus.TRACKED_SOURCE_UNPROVEN,0,False,False,False,False,
            tuple(),G0_R3_UNRESOLVED)

    return P216StoreReview(
        P216ReviewStatus.SOURCE_RISK_REQUIRES_OWNER_DECISION,
        len(findings),
        source.python_direct_native_credential_effect,
        source.p132_product_constructor_and_effect,
        source.p133_source_mode_launcher,
        source.native_c1_service_denial_only,
        tuple(
            f for f in findings if
            f.wincred_native_adapter or f.wincred_backend_import
            or f.explicit_native_credential_call or f.dynamic_import_risk
        ),
        G0_R3_UNRESOLVED,
    )


def proposed_service_store_admission(_receipt:P216StoreReview,**_claims:object)->bool:
    """No password, signer, claimed approval, review file or env can turn GO."""
    return False


def authorize_cross_principal_user_vault_migration(
    _receipt:P216StoreReview,**_claims:object
)->bool:
    """No automatic P132 -> service credential migration or deletion."""
    return False
