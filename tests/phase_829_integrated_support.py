"""B1 test-only composition foundation; no GUI, startup or recovery actions.

Only the sealed A02 fixture creates credential wiring. Metadata and read-only
status follow, with no production fallback. Checks cover miswired dependencies,
not malicious in-process Python, filesystem races, or universal I/O isolation.
"""
from pathlib import Path

from nayeon.brain import onboarding_recovery as recovery
from nayeon.brain.connection_reconciliation import observe_connection
from nayeon.brain.first_run_refresh import FirstRunReadOnlyController
from nayeon.brain.onboarding_metadata_commit import TrustedMetadataCommitHost
from tests.a02_fake_isolation_support import (
    FakeBackend, FakeComposition, FakeMutex, FakeObserver, FakeTempRoot,
    FakeValidator, compose_fake_only_onboarding,
)


# Definition snapshots only: import constructs no fake or production services.
_FAKE_TYPES = (FakeBackend, FakeValidator, FakeObserver, FakeMutex, FakeTempRoot,
               type(Path()))
_FAKE_METHODS = tuple(
    (cls, name, cls.__dict__[name])
    for cls, names in (
        (FakeBackend, ("__init__", "is_available", "get", "put", "delete")),
        (FakeValidator, ("__init__", "validate")),
        (FakeObserver, ("__init__", "backend", "is_available", "__setattr__")),
        (FakeMutex, ("__init__", "hold")),
        (FakeTempRoot, ("__init__", "path", "__setattr__")),
    )
    for name in names
)
_METADATA_TYPE = TrustedMetadataCommitHost
_STATUS_TYPE = FirstRunReadOnlyController


def _check_dependencies(backend, validator, observer, mutex, temp_root, path):
    if any(type(value) is not cls for value, cls in zip(
            (backend, validator, observer, mutex, temp_root, path), _FAKE_TYPES)):
        raise TypeError("Exact sealed A02 dependencies required")
    # Inspect descriptors BEFORE properties, including potentially poisoned ones.
    if any(cls.__dict__.get(name) is not original
           for cls, name, original in _FAKE_METHODS):
        raise TypeError("Sealed fake dependency definition changed")
    if observer.backend is not backend:
        raise ValueError("Fake observer/backend mismatch")
    if (path.parent != temp_root.path or path.name != "provider.json" or
            path != path.resolve()):
        raise ValueError("One canonical test-owned metadata path required")


class IntegratedComposition:
    """Strongly own the root, credential assembly and shared recovery controller.

    Only explicit checked status refresh is added in B1. The caller owns the
    FakeTempRoot lifetime and cleanup of any separately requested fake tenure.
    No windows, owner claim, admission, approval, or automatic recovery here.
    """
    __slots__ = ("temp_root", "metadata_path", "credential", "metadata_host",
                 "status", "observe", "controller", "backend", "validator",
                 "observer", "mutex")

    def __init__(self, *, temp_root, metadata_path, credential, metadata_host,
                 status, observe, backend, validator, observer, mutex):
        for name, value in (
            ("temp_root", temp_root), ("metadata_path", metadata_path),
            ("credential", credential), ("metadata_host", metadata_host),
            ("status", status), ("observe", observe),
            ("controller", credential.controller), ("backend", backend),
            ("validator", validator), ("observer", observer), ("mutex", mutex),
        ):
            object.__setattr__(self, name, value)

    def __setattr__(self, name, value):
        raise AttributeError("Integrated composition bindings are read-only")

    def __repr__(self):
        return "IntegratedComposition(<test-only>)"

    def check_bindings(self):
        """Read-only assertions; never repair, recompose or fall back."""
        _check_dependencies(self.backend, self.validator, self.observer,
                            self.mutex, self.temp_root, self.metadata_path)
        credential = self.credential
        if (type(credential) is not FakeComposition or
                type(self.metadata_host) is not _METADATA_TYPE or
                type(self.status) is not _STATUS_TYPE):
            raise TypeError("Unexpected integrated composition result")
        coordinator = credential.coordinator
        controller = self.controller
        lifecycle = (credential.host._TrustedCredentialOperationHost__onboarding
                     ._OpenAICredentialOnboarding__lifecycle)
        if not all((
            credential.backend is self.backend,
            credential.validator is self.validator,
            credential.observer is self.observer,
            credential.mutex is self.mutex,
            credential.metadata_path is self.metadata_path,
            lifecycle._BoundCredentialLifecycle__backend is self.backend,
            lifecycle._BoundCredentialLifecycle__validator is self.validator,
            coordinator._path is self.metadata_path,
            coordinator._availability is self.observer,
            coordinator._mutex is self.mutex,
            coordinator._host is credential.host,
            credential.controller is controller,
            coordinator.recovery_controller is controller,
            self.metadata_host.recovery_controller is controller,
            self.metadata_host._path is self.metadata_path,
            self.metadata_host._store._path is self.metadata_path,
            self.metadata_host._mutex is self.mutex,
            controller._path is self.metadata_path,
            controller._mutex is self.mutex,
            controller._availability is self.observer,
            self.status._observe is self.observe,
        )):
            raise ValueError("Integrated dependency identity changed")
        # Exactly two captured objects, never late-bound configuration lookups.
        bindings = dict(zip(self.observe.__code__.co_freevars,
                            (cell.cell_contents for cell in self.observe.__closure__)))
        if (set(bindings) != {"metadata_path", "observer"} or
                bindings["metadata_path"] is not self.metadata_path or
                bindings["observer"] is not self.observer):
            raise ValueError("Status observation bindings changed")
        with recovery._POOL_LOCK:
            pooled = recovery._POOL.get(str(self.metadata_path.absolute()).casefold())
        if pooled is not controller:
            raise ValueError("Shared recovery controller changed")

    def check_unstarted(self):
        """Check absence of tenure, owner, READY, permit and pending approvals."""
        self.check_bindings()
        ctrl = self.controller
        coord = self.credential.coordinator
        if (any(value is not None for value in (
                ctrl._ctx, ctrl._owner, ctrl._ui_window_owner, ctrl._epoch,
                ctrl._active, ctrl._review, ctrl._last, ctrl._baseline,
                coord._pending, coord._operation, coord._pending_epoch,
                coord._pending_generation, coord._pending_host_review,
                coord._ui_ticket, self.metadata_host._pending,
                self.metadata_host._ui_ticket, self.metadata_host._ui_owner)) or
                ctrl.ready or ctrl.epoch is not None or ctrl.generation is not None or
                ctrl._ready or ctrl._faulted or ctrl._release_uncertain or
                ctrl._generation != 0 or self.credential.host.has_pending or
                self.mutex.active or self.mutex.entries != 0 or self.mutex.exits != 0):
            raise ValueError("Composition has unexpected startup authority")

    def refresh(self):
        self.check_bindings()
        return self.status.refresh()


def compose_integrated_fake_only(*, backend, validator, observer, mutex,
                                 temp_root, metadata_path):
    """Credential FIRST, metadata SECOND, status THIRD; every input mandatory.

    Reject even an unowned pre-existing metadata/controller assembly. A02's
    unchanged factory enforces fresh-file/root/reservation checks. Never add an
    observer late, clear a pool, or adopt earlier authority. No race guarantee.
    """
    _check_dependencies(backend, validator, observer, mutex, temp_root, metadata_path)
    with recovery._POOL_LOCK:
        existing = recovery._POOL.get(str(metadata_path.absolute()).casefold())
    if existing is not None:
        raise ValueError("Credential-first composition requires an unused path")
    credential = compose_fake_only_onboarding(
        backend=backend, validator=validator, observer=observer, mutex=mutex,
        temp_root=temp_root, metadata_path=metadata_path,
    )
    if type(credential) is not FakeComposition:
        raise TypeError("Exact sealed A02 composition required; no fallback")
    metadata_host = TrustedMetadataCommitHost(metadata_path=metadata_path, mutex=mutex)

    def observe():
        return observe_connection(metadata_path, observer)

    status = FirstRunReadOnlyController(observe=observe)
    result = IntegratedComposition(
        temp_root=temp_root, metadata_path=metadata_path, credential=credential,
        metadata_host=metadata_host, status=status, observe=observe,
        backend=backend, validator=validator, observer=observer, mutex=mutex,
    )
    result.check_unstarted()
    return result
